import { spawn, type ChildProcessWithoutNullStreams } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'
import readline from 'readline'
import { which } from '../system/which'
import { focusSession, launchInTerminal } from '../system/focus'
import type { SettingsStore } from '../settings/store'
import type { LiveSession } from './claude-code'
import type { PermissionMode } from '../../shared/model'

type Rpc = { id?: number; method?: string; params?: unknown; result?: unknown; error?: unknown }

export class CodexIntegration {
  id = 'codex' as const
  bin: string | null = null
  signedIn = false
  sessions = new Map<string, LiveSession>()
  models: Array<{ id: string; name: string; efforts: string[]; defaultEffort?: string; isDefault?: boolean }> = []
  private child: ChildProcessWithoutNullStreams | null = null
  private nextId = 1
  private pending = new Map<number, (msg: Rpc) => void>()
  onChange: () => void = () => {}

  constructor(private readonly store: SettingsStore, private readonly log: (line: string) => void) {}

  capabilities() {
    return { launch: true, sessions: true, context: false, usage: true, model: true, effort: true, permission: true, ultracode: false }
  }

  async detect(): Promise<void> {
    this.bin = await which('codex')
  }

  async start(): Promise<void> {
    if (this.child || !this.bin) return
    this.child = spawn(this.bin, ['app-server'], { stdio: ['pipe', 'pipe', 'pipe'] })
    const rl = readline.createInterface({ input: this.child.stdout })
    rl.on('line', (line) => {
      let msg: Rpc
      try {
        msg = JSON.parse(line)
      } catch {
        return
      }
      if (msg.id && this.pending.has(msg.id)) {
        this.pending.get(msg.id)!(msg)
        this.pending.delete(msg.id)
        return
      }
      this.onNotify(msg)
    })
    this.child.on('exit', () => {
      this.child = null
      this.log('codex app-server exited')
    })
    await this.request('initialize', { clientInfo: { name: 'token-deck', version: '1.0.0' } })
    this.notify('initialized', {})
    await this.refresh()
  }

  stop(): void {
    this.child?.kill()
    this.child = null
  }

  private request(method: string, params: unknown): Promise<unknown> {
    const id = this.nextId++
    return new Promise((resolve, reject) => {
      if (!this.child) return reject(new Error('codex app-server is not running'))
      this.pending.set(id, (msg) => (msg.error ? reject(msg.error) : resolve(msg.result)))
      this.child.stdin.write(JSON.stringify({ id, method, params }) + '\n')
      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id)
          reject(new Error(`codex ${method} timed out`))
        }
      }, 8000)
    })
  }

  private notify(method: string, params: unknown): void {
    this.child?.stdin.write(JSON.stringify({ method, params }) + '\n')
  }

  private onNotify(msg: Rpc): void {
    if (msg.method === 'thread/status/changed' || msg.method === 'turn/started' || msg.method === 'turn/completed') {
      void this.refresh()
    }
    if (msg.method === 'account/rateLimits/updated') this.readLimits(msg.params)
  }

  async refresh(): Promise<void> {
    try {
      const listed = (await this.request('thread/list', { sortKey: 'recency_at', limit: 30 })) as {
        threads?: Array<Record<string, unknown>>
        data?: Array<Record<string, unknown>>
      }
      const threads = listed.threads || listed.data || []
      this.sessions.clear()
      for (const thread of threads) {
        const id = String(thread.id || '')
        if (!id) continue
        const status = thread.status as { type?: string; activeFlags?: string[] } | string
        this.sessions.set(id, {
          id,
          agent: 'codex',
          title: String(thread.name || thread.preview || 'CODEX').toUpperCase(),
          cwd: String(thread.cwd || ''),
          status: mapCodex(status),
          context: null,
          updatedAt: Date.parse(String(thread.updatedAt || '')) || Date.now(),
          model: String(thread.model || '')
        })
      }
      const models = (await this.request('model/list', {})) as { models?: Array<Record<string, unknown>>; data?: Array<Record<string, unknown>> }
      const rows = models.models || models.data || []
      this.models = rows
        .filter((row) => !row.hidden)
        .slice(0, 12)
        .map((row) => ({
          id: String(row.id),
          name: String(row.displayName || row.id),
          efforts: ((row.supportedReasoningEfforts as Array<{ reasoningEffort?: string }>) || []).map((item) => item.reasoningEffort || '').filter(Boolean),
          defaultEffort: String(row.defaultReasoningEffort || ''),
          isDefault: !!row.isDefault
        }))
      const limits = await this.request('account/rateLimits/read', {})
      this.readLimits(limits)
      this.signedIn = true
      this.onChange()
    } catch (err) {
      this.log(`codex refresh ${err}`)
      this.signedIn = false
    }
  }

  private readLimits(payload: unknown): void {
    const limits = (payload as { rateLimits?: { primary?: Limit; secondary?: Limit } })?.rateLimits || (payload as { primary?: Limit; secondary?: Limit })
    if (!limits) return
    const five = asWindow(limits.primary)
    const seven = asWindow(limits.secondary)
    this.store.set('usage', {
      ...this.store.get('usage'),
      codex: {
        five,
        seven,
        at: Date.now(),
        labels: { five: labelFor(limits.primary?.windowDurationMins), seven: labelFor(limits.secondary?.windowDurationMins) }
      }
    })
  }

  async setModel(model: string): Promise<void> {
    editConfig({ model })
  }

  async setEffort(level: string): Promise<void> {
    const current = this.models.find((model) => model.id === readConfigValue('model')) || this.models.find((model) => model.isDefault)
    if (current && current.efforts.length && !current.efforts.includes(level)) throw new Error('NOT AVAILABLE')
    editConfig({ model_reasoning_effort: level })
  }

  async setPermission(mode: PermissionMode): Promise<void> {
    const map = {
      READ: ['read-only', 'on-request'],
      ASK: ['workspace-write', 'on-request'],
      AUTO: ['workspace-write', 'never'],
      FULL: ['danger-full-access', 'never']
    } as const
    const [sandbox, approval] = map[mode]
    editConfig({ sandbox_mode: sandbox, approval_policy: approval })
  }

  async launch(): Promise<void> {
    await launchInTerminal('codex')
  }

  async focus(session: LiveSession): Promise<void> {
    await focusSession({ cwd: session.cwd, termProgram: 'codex', bundleId: 'com.openai.codex' })
  }
}

type Limit = { usedPercent?: number; windowDurationMins?: number; resetsAt?: number }

function asWindow(row?: Limit): { pct: number; resetsAt?: number } | undefined {
  if (!row || typeof row.usedPercent !== 'number') return undefined
  return { pct: row.usedPercent, resetsAt: row.resetsAt }
}

function labelFor(mins?: number): string {
  if (mins === 300) return '5H'
  if (mins === 10080) return '7D'
  if (!mins) return '5H'
  if (mins % 60 === 0 && mins < 48 * 60) return `${mins / 60}H`
  return `${mins}M`
}

function mapCodex(status: { type?: string; activeFlags?: string[] } | string): LiveSession['status'] {
  const type = typeof status === 'string' ? status : status?.type || ''
  const flags = typeof status === 'object' && status ? status.activeFlags || [] : []
  if (flags.includes('waitingOnApproval')) return 'needs-approval'
  if (flags.includes('waitingOnUserInput')) return 'needs-input'
  if (type === 'active') return 'working'
  if (type === 'systemError') return 'disconnected'
  return 'idle'
}

function configPath(): string {
  return path.join(os.homedir(), '.codex', 'config.toml')
}

function readConfigValue(key: string): string {
  try {
    const text = fs.readFileSync(configPath(), 'utf8')
    const line = text.split('\n').find((row) => row.startsWith(`${key} =`) && !row.trim().startsWith('#'))
    return line ? line.split('=').slice(1).join('=').trim().replace(/^"|"$/g, '') : ''
  } catch {
    return ''
  }
}

export function editConfig(values: Record<string, string>): void {
  const file = configPath()
  fs.mkdirSync(path.dirname(file), { recursive: true })
  if (!fs.existsSync(file + '.tokendeck-backup') && fs.existsSync(file)) fs.copyFileSync(file, file + '.tokendeck-backup')
  const text = fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : ''
  const lines = text.split('\n')
  const header = lines.findIndex((line) => /^\s*\[/.test(line))
  const head = header === -1 ? lines : lines.slice(0, header)
  const tail = header === -1 ? [] : lines.slice(header)
  for (const [key, value] of Object.entries(values)) {
    const rendered = `${key} = "${value}"`
    const index = head.findIndex((line) => line.trim().startsWith(`${key} =`) || line.trim().startsWith(`${key}=`))
    if (index >= 0) head[index] = rendered
    else head.unshift(rendered)
  }
  fs.writeFileSync(file, [...head, ...tail].join('\n').replace(/\n+$/, '\n'))
}

export function restoreCodex(): void {
  const file = configPath()
  if (fs.existsSync(file + '.tokendeck-backup')) fs.copyFileSync(file + '.tokendeck-backup', file)
}
