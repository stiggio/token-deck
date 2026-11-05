import fs from 'fs'
import os from 'os'
import path from 'path'
import { commandVersion, which } from '../system/which'
import { focusSession, launchInTerminal } from '../system/focus'
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
    this.major = this.version.startsWith('2') || /\b2\./.test(this.version) ? 2 : 1
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
    const password = process.env.OPENCODE_SERVER_PASSWORD
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
        this.sessions.clear()
        for (const row of sessions || []) {
          const id = String(row.id)
          const state = active?.[id]?.type
          this.sessions.set(id, sessionFrom(id, String(row.title || 'OPENCODE'), state === 'busy' ? 'working' : 'idle'))
        }
      } else {
        await getJson(`${base.url}/global/health`, base.headers)
        const sessions = await getJson<Array<Record<string, unknown>>>(`${base.url}/session`, base.headers)
        const status = await getJson<Record<string, { type?: string }>>(`${base.url}/session/status`, base.headers)
        this.sessions.clear()
        for (const row of sessions || []) {
          const id = String(row.id)
          const state = status?.[id]?.type
          const mapped = state === 'busy' || state === 'retry' ? 'working' : 'idle'
          this.sessions.set(id, sessionFrom(id, String(row.title || 'OPENCODE'), mapped))
        }
      }
      this.reachable = true
      this.readModels()
      this.onChange()
    } catch {
      this.reachable = false
    }
  }

  private readModels(): void {
    try {
      const file = path.join(os.homedir(), '.config/opencode/opencode.json')
      const json = JSON.parse(fs.readFileSync(file, 'utf8')) as { model?: string }
      this.models = json.model ? [json.model] : []
    } catch {
      this.models = []
    }
  }

  async setModel(model: string): Promise<void> {
    const file = path.join(os.homedir(), '.config/opencode/opencode.json')
    fs.mkdirSync(path.dirname(file), { recursive: true })
    const json = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {}
    json.model = model
    fs.writeFileSync(file, JSON.stringify(json, null, 2) + '\n')
  }

  async setPermission(mode: PermissionMode): Promise<void> {
    const file = path.join(os.homedir(), '.config/opencode/opencode.json')
    fs.mkdirSync(path.dirname(file), { recursive: true })
    const json = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {}
    if (this.major >= 2) json.permissions = [{ permission: mode.toLowerCase(), action: 'allow' }]
    else json.permission = { edit: mode === 'READ' ? 'ask' : 'allow', bash: mode === 'FULL' || mode === 'AUTO' ? 'allow' : 'ask' }
    fs.writeFileSync(file, JSON.stringify(json, null, 2) + '\n')
  }

  async launch(): Promise<void> {
    await launchInTerminal('opencode')
  }

  async focus(session: LiveSession): Promise<void> {
    await focusSession({ cwd: session.cwd, termProgram: 'opencode' })
  }
}

function sessionFrom(id: string, title: string, status: LiveSession['status']): LiveSession {
  return { id, agent: 'opencode', title: title.toUpperCase(), status, context: null, updatedAt: Date.now() }
}

async function getJson<T>(url: string, headers: Record<string, string>): Promise<T> {
  const response = await fetch(url, { headers })
  if (!response.ok) throw new Error(String(response.status))
  return response.json() as Promise<T>
}
