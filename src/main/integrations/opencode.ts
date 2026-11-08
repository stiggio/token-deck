import fs from 'fs'
import os from 'os'
import path from 'path'
import { commandVersion, loginShellVar, which } from '../system/which'
import { focusSession, launchInTerminal } from '../system/focus'
import { findAgentTerminal } from '../system/terminal'
import { readIfExists, writeFileAtomic } from '../system/files'
import type { SettingsStore } from '../settings/store'
import type { LiveSession } from './claude-code'
import type { PermissionMode } from '../../shared/model'

export class OpenCodeIntegration {
  id = 'opencode' as const
  bin: string | null = null
  version = ''
  major = 1
  reachable = false
  sessions = new Map<string, LiveSession>()
  models: string[] = []
  private password = ''
  private timer: NodeJS.Timeout | null = null
  onChange: () => void = () => {}

  constructor(private readonly store: SettingsStore) {}

  capabilities() {
    return { launch: true, sessions: true, context: false, usage: false, model: true, effort: false, permission: true, ultracode: false }
  }

  async detect(): Promise<void> {
    this.bin = await which('opencode')
    if (!this.bin) return
    this.version = await commandVersion(this.bin)
    this.major = majorVersion(this.version)
    this.password = await loginShellVar('OPENCODE_SERVER_PASSWORD')
  }

  start(): void {
    if (this.timer) return
    void this.poll()
    this.timer = setInterval(() => void this.poll(), 2000)
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer)
    this.timer = null
  }

  private async authHeader(): Promise<Record<string, string>> {
    const password = this.password || process.env.OPENCODE_SERVER_PASSWORD
    if (!password) return {}
    return { authorization: `Basic ${Buffer.from(`opencode:${password}`).toString('base64')}` }
  }

  private async base(): Promise<{ url: string; headers: Record<string, string> } | null> {
    if (this.major >= 2) {
      try {
        const file = path.join(os.homedir(), '.local/state/opencode/service.json')
        const info = JSON.parse(fs.readFileSync(file, 'utf8')) as { url?: string; password?: string }
        if (!info.url) return null
        const headers: Record<string, string> = {}
        if (info.password) headers.authorization = `Basic ${Buffer.from(`opencode:${info.password}`).toString('base64')}`
        return { url: info.url.replace(/\/$/, ''), headers }
      } catch {
        return null
      }
    }
    return { url: this.store.get('opencodeUrl').replace(/\/$/, ''), headers: await this.authHeader() }
  }

  private async poll(): Promise<void> {
    const base = await this.base()
    if (!base) {
      this.reachable = false
      return
    }
    try {
      if (this.major >= 2) {
        const sessions = await getJson<Array<Record<string, unknown>>>(`${base.url}/api/session`, base.headers)
        const active = await getJson<Record<string, { type?: string }>>(`${base.url}/api/session/active`, base.headers)
        const next = new Map<string, LiveSession>()
        for (const row of sessions || []) {
          const id = String(row.id)
          const state = active?.[id]?.type
          next.set(id, sessionFrom(row, state === 'busy' ? 'working' : 'idle', this.sessions.get(id)))
        }
        this.sessions = next
      } else {
        await getJson(`${base.url}/global/health`, base.headers)
        const sessions = await getJson<Array<Record<string, unknown>>>(`${base.url}/session`, base.headers)
        const status = await getJson<Record<string, { type?: string }>>(`${base.url}/session/status`, base.headers)
        const next = new Map<string, LiveSession>()
        for (const row of sessions || []) {
          const id = String(row.id)
          const state = status?.[id]?.type
          const mapped = state === 'busy' || state === 'retry' ? 'working' : 'idle'
          next.set(id, sessionFrom(row, mapped, this.sessions.get(id)))
        }
        this.sessions = next
      }
      this.reachable = true
      await this.readModels(base)
      this.onChange()
    } catch {
      this.reachable = false
    }
  }

  /** The configured model first, then the providers' default models and the rest, from the server (1.x). */
  private async readModels(base: { url: string; headers: Record<string, string> }): Promise<void> {
    const configured = readConfig().model
    let offered: string[] = []
    if (this.major < 2) {
      try {
        offered = providerModels(await getJson<unknown>(`${base.url}/config/providers`, base.headers))
      } catch {
        /* older servers: just the configured model */
      }
    }
    const all = [...(typeof configured === 'string' && configured ? [configured] : []), ...offered]
    this.models = [...new Set(all)].slice(0, 6)
  }

  async setModel(model: string): Promise<void> {
    const json = readConfig(true)
    json.model = model
    writeConfig(json)
  }

  /**
   * 1.x: sets `edit` and the default bash rule, keeping per-command bash rules and every other key.
   * 2.x's permission list isn't mapped yet, so the deck says NOT AVAILABLE instead of guessing.
   */
  async setPermission(mode: PermissionMode): Promise<void> {
    if (this.major >= 2) throw new Error('NOT AVAILABLE')
    const json = readConfig(true)
    json.permission = mergePermission(json.permission, mode)
    writeConfig(json)
  }

  async launch(): Promise<void> {
    await launchInTerminal('opencode')
  }

  /** The terminal running OpenCode in the session's folder. */
  async focus(session: LiveSession): Promise<void> {
    const terminal = await findAgentTerminal(['opencode'], session.cwd)
    if (terminal) {
      await focusSession({ tty: terminal.tty, termProgram: terminal.termProgram, bundleId: terminal.bundleId, cwd: session.cwd })
      return
    }
    // macOS: no terminal runs OpenCode in that folder, so say so. Windows: bring the terminal app forward.
    if (process.platform === 'darwin') throw new Error('no terminal found for this OpenCode session')
    await focusSession({ cwd: session.cwd, termProgram: 'opencode' })
  }
}

/** `opencode --version` → its major version; "1.2.0" is 1, not 2. */
export function majorVersion(version: string): number {
  const major = Number(version.match(/(\d+)\.\d+/)?.[1])
  return Number.isFinite(major) && major > 0 ? major : 1
}

/** Sessions sort by their own last update, from the server, never by when Token Deck polled. */
export function sessionFrom(row: Record<string, unknown>, status: LiveSession['status'], prev?: LiveSession): LiveSession {
  const time = (row.time || {}) as { updated?: unknown; created?: unknown }
  const stamp = Number(time.updated ?? row.updatedAt ?? time.created ?? 0)
  const updatedAt = Number.isFinite(stamp) && stamp > 0 ? (stamp < 1e12 ? stamp * 1000 : stamp) : prev?.updatedAt || 0
  return {
    id: String(row.id),
    agent: 'opencode',
    title: String(row.title || 'OPENCODE').toUpperCase(),
    cwd: typeof row.directory === 'string' ? row.directory : typeof row.cwd === 'string' ? row.cwd : prev?.cwd,
    status,
    context: null,
    updatedAt,
    live: true
  }
}

/** "provider/model" ids from GET /config/providers, the providers' defaults first. */
export function providerModels(data: unknown): string[] {
  const body = (data || {}) as { providers?: Array<{ id?: unknown; models?: unknown }>; default?: Record<string, unknown> }
  const defaults = Object.entries(body.default || {}).filter(([, model]) => typeof model === 'string').map(([provider, model]) => `${provider}/${model}`)
  const rest: string[] = []
  for (const provider of Array.isArray(body.providers) ? body.providers : []) {
    if (typeof provider.id !== 'string') continue
    const ids = Array.isArray(provider.models)
      ? provider.models.map((model) => (model as { id?: unknown }).id).filter((id): id is string => typeof id === 'string')
      : Object.keys((provider.models as Record<string, unknown>) || {})
    for (const id of ids) rest.push(`${provider.id}/${id}`)
  }
  return [...new Set([...defaults, ...rest])]
}

/** OpenCode 1.x permission settings for a deck level, keeping the user's per-command bash rules and other keys. */
export function mergePermission(current: unknown, mode: PermissionMode): Record<string, unknown> {
  const next: Record<string, unknown> = current && typeof current === 'object' && !Array.isArray(current) ? { ...(current as Record<string, unknown>) } : {}
  next.edit = mode === 'READ' ? 'ask' : 'allow'
  const bash = mode === 'FULL' || mode === 'AUTO' ? 'allow' : 'ask'
  next.bash = next.bash && typeof next.bash === 'object' && !Array.isArray(next.bash) ? { ...(next.bash as Record<string, unknown>), '*': bash } : bash
  return next
}

function configFile(): string {
  return path.join(os.homedir(), '.config/opencode/opencode.json')
}

/**
 * opencode.json as an object. A missing file is an empty config. For a write, a file that can't be
 * read or isn't a JSON object stops the change, so Token Deck never replaces what it couldn't parse.
 */
function readConfig(forWrite = false): Record<string, unknown> {
  let text: string | null
  try {
    text = readIfExists(configFile())
  } catch (err) {
    if (forWrite) throw err
    return {}
  }
  if (text === null) return {}
  try {
    const parsed = JSON.parse(text) as unknown
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) return parsed as Record<string, unknown>
  } catch {
    /* falls through */
  }
  if (forWrite) throw new Error('opencode.json is not valid JSON')
  return {}
}

/** Writes opencode.json in one step, after keeping a copy of the user's original once. */
function writeConfig(json: Record<string, unknown>): void {
  const file = configFile()
  if (fs.existsSync(file) && !fs.existsSync(file + '.tokendeck-backup')) fs.copyFileSync(file, file + '.tokendeck-backup')
  writeFileAtomic(file, JSON.stringify(json, null, 2) + '\n')
}

async function getJson<T>(url: string, headers: Record<string, string>): Promise<T> {
  const response = await fetch(url, { headers })
  if (!response.ok) throw new Error(String(response.status))
  return response.json() as Promise<T>
}
