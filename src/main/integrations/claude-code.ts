import { execFile } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'
import chokidar from 'chokidar'
import type { SettingsStore } from '../settings/store'
import { commandVersion, which } from '../system/which'
import { focusSession, launchInTerminal } from '../system/focus'
import type { AgentId, PermissionMode, SessionStatus } from '../../shared/model'
import type { HookBody } from '../hooks/server'

export type LiveSession = {
  id: string
  agent: AgentId
  title: string
  cwd?: string
  status: SessionStatus
  context: number | null
  updatedAt: number
  pid?: number
  tty?: string
  termProgram?: string
  entrypoint?: string
  model?: string
}

const HOOK = `#!/bin/sh
u=$(cat "$HOME/.tokendeck/url" 2>/dev/null) || exit 0
[ -n "$u" ] || exit 0
curl -s --connect-timeout 1 --max-time 2 -o /dev/null -X POST "$u/hooks/claude" \\
  -H 'content-type: application/json' --data-binary @- \\
  -H "x-td-pid: \${CLAUDE_PID:-}" -H "x-td-entrypoint: \${CLAUDE_CODE_ENTRYPOINT:-}" \\
  -H "x-td-term: \${TERM_PROGRAM:-}" -H "x-td-term-session: \${TERM_SESSION_ID:-}\${ITERM_SESSION_ID:-}\${WT_SESSION:-}" \\
  -H "x-td-tty: $(ps -o tty= -p "\${CLAUDE_PID:-$PPID}" 2>/dev/null)" \\
  >/dev/null 2>&1
exit 0
`

const STATUSLINE = `#!/bin/sh
in=$(cat)
u=$(cat "$HOME/.tokendeck/url" 2>/dev/null || true)
if [ -n "$u" ]; then
  printf '%s' "$in" | curl -s -m 1 -o /dev/null -X POST "$u/statusline" -H 'content-type: application/json' --data-binary @- >/dev/null 2>&1 &
fi
orig=$(cat "$HOME/.tokendeck/statusline-original.json" 2>/dev/null || true)
orig=\${orig#\\"}
orig=\${orig%\\"}
if [ -n "$orig" ] && [ "$orig" != "null" ]; then
  printf '%s' "$in" | sh -c "$orig"
fi
exit 0
`

const HOOK_PS = `try { $u = Get-Content "$env:USERPROFILE\\.tokendeck\\url" -ErrorAction Stop; $b = [Console]::In.ReadToEnd(); Invoke-RestMethod -Method Post -Uri "$u/hooks/claude" -ContentType 'application/json' -TimeoutSec 2 -Body $b | Out-Null } catch {}; exit 0
`

type ClaudeAgent = {
  cwd?: string
  kind?: string
  startedAt?: string
  sessionId?: string
  name?: string
  pid?: number
  status?: string
  waitingFor?: string
  state?: string
}

export class ClaudeCode {
  id = 'claude-code' as const
  bin: string | null = null
  version = ''
  signedIn = false
  plan = ''
  hooksInstalled = false
  statusChained = false
  sessions = new Map<string, LiveSession>()
  private timer: NodeJS.Timeout | null = null
  private watcher: chokidar.FSWatcher | null = null
  onChange: () => void = () => {}

  constructor(private readonly store: SettingsStore, private readonly log: (line: string) => void) {}

  capabilities() {
    return {
      launch: true,
      sessions: true,
      context: true,
      usage: true,
      model: true,
      effort: true,
      permission: true,
      ultracode: true
    }
  }

  private settingsPath(): string {
    return path.join(os.homedir(), '.claude', 'settings.json')
  }

  async detect(): Promise<void> {
    this.bin = await which('claude')
    if (!this.bin) return
    this.version = await commandVersion(this.bin)
    const status = await this.execJson(['auth', 'status', '--json'])
    this.signedIn = !!(status && (status.loggedIn || status.authenticated || status.authMethod))
    this.plan = String(status?.subscriptionType || status?.plan || status?.account || '')
    const settings = this.readSettings()
    const blob = JSON.stringify(settings.hooks || {})
    this.hooksInstalled = blob.includes('.tokendeck/bin/hook') || blob.includes('.tokendeck\\bin\\hook')
    const command = settings.statusLine?.command
    this.statusChained = typeof command === 'string' && command.includes('.tokendeck/bin/statusline')
  }

  start(): void {
    if (this.timer) return
    void this.poll()
    this.timer = setInterval(() => void this.poll(), 2000)
    this.watcher = chokidar.watch(this.settingsPath(), { ignoreInitial: true }).on('change', () => this.onChange())
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer)
    this.timer = null
    void this.watcher?.close()
  }

  private execJson(args: string[]): Promise<Record<string, unknown> | null> {
    return new Promise((resolve) => {
      if (!this.bin) return resolve(null)
      execFile(this.bin, args, { timeout: 8000, encoding: 'utf8' }, (err, stdout) => {
        if (err) return resolve(null)
        try {
          resolve(JSON.parse(String(stdout)))
        } catch {
          resolve(null)
        }
      })
    })
  }

  private async poll(): Promise<void> {
    if (!this.bin) return
    const raw = await new Promise<string>((resolve) => {
      execFile(this.bin!, ['agents', '--json', '--all'], { timeout: 8000, encoding: 'utf8' }, (err, stdout) => {
        resolve(err ? '' : String(stdout || ''))
      })
    })
    if (!raw) return
    let rows: ClaudeAgent[] = []
    try {
      const parsed = JSON.parse(raw) as ClaudeAgent[] | { agents?: ClaudeAgent[] }
      rows = Array.isArray(parsed) ? parsed : parsed.agents || []
    } catch {
      return
    }
    const seen = new Set<string>()
    for (const row of rows) {
      const id = row.sessionId || `${row.pid || row.cwd}`
      if (!id) continue
      seen.add(id)
      const prev = this.sessions.get(id)
      const title = (row.name || prev?.title || path.basename(row.cwd || 'session')).toUpperCase()
      this.sessions.set(id, {
        id,
        agent: 'claude-code',
        title,
        cwd: row.cwd,
        status: mapStatus(row),
        context: prev?.context ?? null,
        updatedAt: Date.parse(row.startedAt || '') || prev?.updatedAt || Date.now(),
        pid: row.pid,
        tty: prev?.tty,
        termProgram: prev?.termProgram,
        entrypoint: prev?.entrypoint,
        model: prev?.model
      })
    }
    for (const id of [...this.sessions.keys()]) {
      if (!seen.has(id) && this.sessions.get(id)?.status !== 'completed') this.sessions.delete(id)
    }
    this.onChange()
  }

  ingest(event: HookBody): void {
    const body = (event.body || {}) as Record<string, unknown>
    const id = String(body.session_id || body.sessionId || '')
    if (event.source === 'statusline') {
      this.ingestStatus(body)
      return
    }
    if (!id) return
    const prev = this.sessions.get(id)
    const hook = String(body.hook_event_name || body.hookEventName || '')
    let status = prev?.status || 'idle'
    if (hook === 'UserPromptSubmit') status = 'working'
    if (hook === 'PermissionRequest') status = 'needs-approval'
    if (hook === 'Stop') status = 'completed'
    if (hook === 'Notification') {
      const note = String(body.notification_type || body.notificationType || body.message || '')
      if (note.includes('permission')) status = 'needs-approval'
      else if (note.includes('input')) status = 'needs-input'
      else if (note.includes('completed')) status = 'completed'
      else if (note.includes('idle')) status = 'idle'
    }
    const prompt = typeof body.prompt === 'string' ? body.prompt : ''
    const ttyHeader = event.headers['x-td-tty'] || ''
    const tty = ttyHeader.trim() ? (ttyHeader.trim().startsWith('/dev/') ? ttyHeader.trim() : `/dev/${ttyHeader.trim()}`) : prev?.tty
    this.sessions.set(id, {
      id,
      agent: 'claude-code',
      title: prev?.title || (prompt ? prompt.slice(0, 24).toUpperCase() : 'SESSION'),
      cwd: String(body.cwd || prev?.cwd || ''),
      status,
      context: prev?.context ?? null,
      updatedAt: Date.now(),
      pid: Number(event.headers['x-td-pid'] || prev?.pid || 0) || prev?.pid,
      tty,
      termProgram: event.headers['x-td-term'] || prev?.termProgram,
      entrypoint: event.headers['x-td-entrypoint'] || prev?.entrypoint,
      model: prev?.model
    })
    this.onChange()
  }

  private ingestStatus(body: Record<string, unknown>): void {
    const id = String(body.session_id || '')
    const model = body.model as { id?: string; display_name?: string } | undefined
    const context = body.context_window as { used_percentage?: number | null } | undefined
    const limits = body.rate_limits as {
      five_hour?: { used_percentage?: number; resets_at?: number }
      seven_day?: { used_percentage?: number; resets_at?: number }
    }
    if (limits) {
      const now = Date.now()
      const five = windowOf(limits.five_hour)
      const seven = windowOf(limits.seven_day)
      this.store.set('usage', { ...this.store.get('usage'), 'claude-code': { five, seven, at: now, labels: { five: '5H', seven: '7D' } } })
    }
    if (!id) return
    const prev = this.sessions.get(id)
    this.sessions.set(id, {
      id,
      agent: 'claude-code',
      title: prev?.title || 'SESSION',
      cwd: String(body.cwd || prev?.cwd || ''),
      status: prev?.status || 'working',
      context: context?.used_percentage ?? prev?.context ?? null,
      updatedAt: Date.now(),
      pid: prev?.pid,
      tty: prev?.tty,
      termProgram: prev?.termProgram,
      entrypoint: prev?.entrypoint,
      model: model?.display_name || model?.id || prev?.model
    })
    this.onChange()
  }

  async install(): Promise<string[]> {
    await this.detect()
    const notes: string[] = []
    const bin = path.join(os.homedir(), '.tokendeck', 'bin')
    fs.mkdirSync(bin, { recursive: true })
    if (process.platform === 'win32') {
      fs.writeFileSync(path.join(bin, 'hook.ps1'), HOOK_PS)
      notes.push('Writes %USERPROFILE%\\.tokendeck\\bin\\hook.ps1 and registers it in .claude/settings.json.')
    } else {
      fs.writeFileSync(path.join(bin, 'hook'), HOOK, { mode: 0o755 })
      fs.chmodSync(path.join(bin, 'hook'), 0o755)
      fs.writeFileSync(path.join(bin, 'statusline'), STATUSLINE, { mode: 0o755 })
      notes.push('Writes ~/.tokendeck/bin/hook and ~/.tokendeck/bin/statusline.')
    }
    const file = this.settingsPath()
    fs.mkdirSync(path.dirname(file), { recursive: true })
    if (!fs.existsSync(file + '.tokendeck-backup') && fs.existsSync(file)) {
      fs.copyFileSync(file, file + '.tokendeck-backup')
      notes.push('Backs up ~/.claude/settings.json to settings.json.tokendeck-backup once.')
    }
    const settings = this.readSettings()
    const command = process.platform === 'win32'
      ? undefined
      : 'sh ~/.tokendeck/bin/hook 2>/dev/null || true'
    const hook = (extra: Record<string, unknown> = {}, matcher?: string) => {
      if (process.platform === 'win32') {
        return {
          matcher,
          hooks: [{
            type: 'command',
            command: 'powershell.exe',
            args: ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(bin, 'hook.ps1')],
            ...extra
          }]
        }
      }
      return { matcher, hooks: [{ type: 'command', command, ...extra }] }
    }
    settings.hooks = settings.hooks || {}
    const hooks = settings.hooks as Record<string, unknown[]>
    const asyncHook = hook({ async: true })
    const notify = hook({ async: true }, 'permission_prompt|idle_prompt|agent_needs_input|agent_completed')
    const syncHook = hook({ timeout: 2 })
    hooks.UserPromptSubmit = [asyncHook]
    hooks.Stop = [asyncHook]
    hooks.Notification = [notify]
    hooks.PermissionRequest = [asyncHook]
    hooks.PostModelSwitch = [asyncHook]
    hooks.SessionStart = [syncHook]
    hooks.SessionEnd = [syncHook]
    if (process.platform !== 'win32') {
      const existing = settings.statusLine?.command
      if (existing && !String(existing).includes('statusline')) {
        fs.writeFileSync(path.join(os.homedir(), '.tokendeck', 'statusline-original.json'), JSON.stringify(existing))
      }
      settings.statusLine = { type: 'command', command: 'sh ~/.tokendeck/bin/statusline' }
      notes.push('Chains the status line through ~/.tokendeck/bin/statusline.')
    } else {
      notes.push('Windows status line is skipped unless Git Bash is present; sessions come from the poll.')
    }
    this.writeSettings(settings)
    notes.push('Edits ~/.claude/settings.json hooks, and model, effort, permission or ultracode only when you change them on the deck.')
    await this.detect()
    return notes
  }

  restore(): void {
    const file = this.settingsPath()
    const backup = file + '.tokendeck-backup'
    if (fs.existsSync(backup)) fs.copyFileSync(backup, file)
  }

  async setModel(model: string): Promise<void> {
    const settings = this.readSettings()
    settings.model = model.toLowerCase()
    this.writeSettings(settings)
  }

  async clearModel(): Promise<void> {
    const settings = this.readSettings()
    delete settings.model
    this.writeSettings(settings)
  }

  async setEffort(level: string): Promise<void> {
    const settings = this.readSettings()
    const modern = versionAtLeast(this.version, '2.1.251')
    if (modern) {
      const id = canonicalModel(String(settings.model || 'opus'))
      settings.modelSettings = settings.modelSettings || {}
      const table = settings.modelSettings as Record<string, { effortLevel?: string }>
      table[id] = { ...(table[id] || {}), effortLevel: level }
    } else {
      settings.effortLevel = level
    }
    this.writeSettings(settings)
  }

  async setPermission(mode: PermissionMode): Promise<void> {
    const settings = this.readSettings()
    const perms = (settings.permissions || {}) as { defaultMode?: string; disableBypassPermissionsMode?: boolean }
    if (mode === 'FULL' && perms.disableBypassPermissionsMode) throw new Error('NOT AVAILABLE')
    const map = { READ: 'plan', ASK: 'default', AUTO: 'auto', FULL: 'bypassPermissions' } as const
    perms.defaultMode = map[mode]
    settings.permissions = perms
    this.writeSettings(settings)
  }

  async setUltracode(on: boolean): Promise<void> {
    const settings = this.readSettings()
    settings.ultracode = on
    this.writeSettings(settings)
  }

  async launch(): Promise<void> {
    await launchInTerminal('claude')
  }

  async focus(session: LiveSession): Promise<void> {
    await focusSession({
      termProgram: session.entrypoint === 'claude-desktop' ? 'claude-desktop' : session.termProgram,
      tty: session.tty,
      cwd: session.cwd,
      sessionId: session.id
    })
  }

  readModel(): string {
    return String(this.readSettings().model || '')
  }

  private readSettings(): Record<string, any> {
    try {
      return JSON.parse(fs.readFileSync(this.settingsPath(), 'utf8'))
    } catch {
      return {}
    }
  }

  private writeSettings(settings: Record<string, unknown>): void {
    const file = this.settingsPath()
    fs.mkdirSync(path.dirname(file), { recursive: true })
    fs.writeFileSync(file, JSON.stringify(settings, null, 2) + '\n')
  }
}

function mapStatus(row: ClaudeAgent): SessionStatus {
  if (row.status === 'busy') return 'working'
  if (row.status === 'waiting' && String(row.waitingFor || '').includes('permission')) return 'needs-approval'
  if (row.status === 'waiting') return 'needs-input'
  if (row.status === 'idle') return 'idle'
  return 'idle'
}

function windowOf(row?: { used_percentage?: number; resets_at?: number }): { pct: number; resetsAt?: number } | undefined {
  if (!row || typeof row.used_percentage !== 'number') return undefined
  if (row.resets_at && row.resets_at * 1000 < Date.now()) return undefined
  return { pct: row.used_percentage, resetsAt: row.resets_at }
}

function versionAtLeast(version: string, min: string): boolean {
  const parse = (value: string) => value.replace(/^[^\d]*/, '').split(/[^\d]+/).map((n) => Number(n) || 0)
  const a = parse(version)
  const b = parse(min)
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    if ((a[i] || 0) > (b[i] || 0)) return true
    if ((a[i] || 0) < (b[i] || 0)) return false
  }
  return true
}

function canonicalModel(alias: string): string {
  const map: Record<string, string> = {
    opus: 'opus',
    sonnet: 'sonnet',
    haiku: 'haiku',
    fable: 'fable'
  }
  return map[alias.toLowerCase()] || alias
}

export const CLAUDE_EFFORTS = ['low', 'medium', 'high', 'xhigh']
export const CLAUDE_MODELS = ['opus', 'sonnet', 'haiku', 'fable']
