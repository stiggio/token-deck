import { execFile, spawn } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'
import chokidar from 'chokidar'
import type { SettingsStore } from '../settings/store'
import { commandVersion, which } from '../system/which'
import { focusSession, launchInTerminal, openApp } from '../system/focus'
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
mkdir -p "$HOME/.tokendeck"
printf '%s' "$in" > "$HOME/.tokendeck/last-statusline.json"
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

/** How a hook names Token Deck's shim: in `command` on macOS, in `args` (as hook.ps1) on Windows. */
const HOOK_SHIMS = ['.tokendeck/bin/hook', '.tokendeck\\bin\\hook']
const STATUSLINE_SHIM = '.tokendeck/bin/statusline'

type HookEntry = { matcher?: string; hooks: unknown[] }

type ClaudeAgent = {
  cwd?: string
  kind?: string
  startedAt?: string | number
  updatedAt?: number
  sessionId?: string
  name?: string
  pid?: number
  entrypoint?: string
  status?: string
  waitingFor?: string
  state?: string
}

export class ClaudeCode {
  id = 'claude-code' as const
  bin: string | null = null
  desktop = false
  version = ''
  signedIn = false
  plan = ''
  hooksInstalled = false
  statusChained = false
  sessions = new Map<string, LiveSession>()
  /** Model id of the Claude Code session that was active most recently. */
  activeModelId: string | null = null
  private sessionSig = ''
  private statuslineMtime = 0
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
    const desktopApps = ['/Applications/Claude.app', path.join(os.homedir(), 'Applications/Claude.app')]
    this.desktop = desktopApps.some((folder) => fs.existsSync(folder))
    this.bin = await which('claude')
    if (!this.bin) return
    this.version = await commandVersion(this.bin)
    const status = await this.execJson(['auth', 'status', '--json'])
    this.signedIn = !!(status && (status.loggedIn || status.authenticated || status.authMethod))
    this.plan = String(status?.subscriptionType || status?.plan || status?.account || '')
    const settings = this.readSettings()
    this.hooksInstalled = hasTokenDeckHook(settings.hooks)
    const command = settings.statusLine?.command
    this.statusChained = typeof command === 'string' && command.includes(STATUSLINE_SHIM)
    this.refreshModelFavorites()
  }

  start(): void {
    if (this.timer) return
    writeStatusline()
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
    await this.refreshActiveModel()
    this.readSavedStatusline()
    const rows = new Map<string, ClaudeAgent>()
    for (const row of readSessionFiles()) rows.set(row.sessionId || '', row)
    rows.delete('')
    for (const row of recentSessionFiles()) {
      if (row.sessionId && !rows.has(row.sessionId)) rows.set(row.sessionId, row)
    }
    if (this.bin) {
      const raw = await new Promise<string>((resolve) => {
        execFile(this.bin!, ['agents', '--json', '--all'], { timeout: 8000, encoding: 'utf8' }, (err, stdout) => {
          resolve(err ? '' : String(stdout || ''))
        })
      })
      const parsed = parseAgents(raw)
      if (raw && !parsed) this.log('claude agents was not JSON')
      for (const row of parsed || []) {
        const id = row.sessionId || ''
        if (!id) continue
        rows.set(id, { ...rows.get(id), ...row, sessionId: id })
      }
    }
    const next = new Map<string, LiveSession>()
    const ordered = [...rows.values()].sort((a, b) => (b.updatedAt || startedAt(b.startedAt) || 0) - (a.updatedAt || startedAt(a.startedAt) || 0))
    for (const row of ordered) {
      const id = row.sessionId || ''
      if (!id || next.has(id)) continue
      const prev = this.sessions.get(id)
      const desktop = row.entrypoint === 'claude-desktop' || String(row.cwd || '').includes('Application Support/Claude')
      next.set(id, {
        id,
        agent: 'claude-code',
        title: (row.name || prev?.title || 'SESSION').toUpperCase(),
        cwd: row.cwd,
        status: mapStatus(row),
        context: prev?.context ?? null,
        updatedAt: startedAt(row.startedAt) || prev?.updatedAt || Date.now(),
        pid: row.pid,
        tty: prev?.tty,
        termProgram: prev?.termProgram,
        entrypoint: row.entrypoint || (desktop ? 'claude-desktop' : prev?.entrypoint),
        model: prev?.model
      })
    }
    for (const [id, prev] of this.sessions) {
      if (!next.has(id) && prev.tty && Date.now() - prev.updatedAt < 20000) next.set(id, prev)
    }
    const sig = [...next.values()].map((row) => `${row.id}:${row.status}:${row.title}`).join('|')
    this.sessions = next
    if (sig === this.sessionSig) return
    this.sessionSig = sig
    this.log(`claude sessions ${next.size}`)
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
    const limits = (body.rate_limits || body.rateLimits) as {
      five_hour?: { used_percentage?: number; utilization?: number; resets_at?: number; resetsAt?: number }
      seven_day?: { used_percentage?: number; utilization?: number; resets_at?: number; resetsAt?: number }
    } | undefined
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
    const asyncHook = hook({ async: true })
    const notify = hook({ async: true }, 'permission_prompt|idle_prompt|agent_needs_input|agent_completed')
    const syncHook = hook({ timeout: 2 })
    settings.hooks = withTokenDeckHooks(settings.hooks, {
      UserPromptSubmit: asyncHook,
      Stop: asyncHook,
      Notification: notify,
      PermissionRequest: asyncHook,
      PostModelSwitch: asyncHook,
      SessionStart: syncHook,
      SessionEnd: syncHook
    })
    if (process.platform !== 'win32') {
      const existing = settings.statusLine?.command
      // Save what the shim should run, unless it is the shim itself, which would then call itself.
      if (existing && !String(existing).includes(STATUSLINE_SHIM)) {
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

  catalogModels(): Array<{ id: string; name: string }> {
    return readClaudeCatalog()
  }

  displayModel(): string {
    const current = this.activeModelId || String(this.readSettings().model || '')
    if (!current) return ''
    const models = this.catalogModels()
    const exact = models.find((model) => model.id === current || model.name.toLowerCase() === current.toLowerCase())
    if (exact) return exact.name
    const family = models.find((model) => model.id.startsWith(`claude-${current.toLowerCase()}`))
    return family?.name || ''
  }

  private async refreshActiveModel(): Promise<void> {
    const running = await runningClaudeModels()
    let best: { id: string; at: number } | null = null
    for (const row of readSessionFiles()) {
      const id = running.get(String(row.pid || ''))
      const at = row.updatedAt || 0
      if (id && (!best || at > best.at)) best = { id, at }
    }
    if (!best) {
      for (const id of running.values()) {
        best = { id, at: 0 }
        break
      }
    }
    if (best?.id === this.activeModelId) return
    this.activeModelId = best?.id || null
    const settings = this.readSettings()
    if (this.activeModelId && settings.model && settings.model !== this.activeModelId && ![...running.values()].includes(String(settings.model))) {
      delete settings.model
      this.writeSettings(settings)
      this.log('cleared a Claude model setting that no running session uses')
    }
    this.onChange()
  }

  private readSavedStatusline(): void {
    try {
      const file = path.join(os.homedir(), '.tokendeck', 'last-statusline.json')
      const mtime = fs.statSync(file).mtimeMs
      if (mtime === this.statuslineMtime) return
      this.statuslineMtime = mtime
      this.ingestStatus(JSON.parse(fs.readFileSync(file, 'utf8')) as Record<string, unknown>)
    } catch {
      /* no status line has reported yet */
    }
  }

  private refreshModelFavorites(): void {
    const names = this.catalogModels().map((model) => model.name)
    if (names.length < 6) return
    const favorites = this.store.get('favorites')
    const saved = favorites['claude-code']
    const same = saved.length === names.length && saved.every((name) => names.includes(name))
    if (same) return
    this.store.set('favorites', { ...favorites, 'claude-code': names })
  }

  async setModel(model: string): Promise<void> {
    const row = this.catalogModels().find((item) => item.id === model || item.name.toLowerCase() === model.toLowerCase())
    const settings = this.readSettings()
    settings.model = row?.id || model
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
    if (this.bin && this.desktop) {
      const where = await openClaude(this.bin, ['--desktop'])
      if (where === 'already') await openApp('Claude')
      return
    }
    if (this.bin) {
      await launchInTerminal(this.bin)
      return
    }
    if (this.desktop) await openApp('Claude')
  }

  async focus(session: LiveSession): Promise<void> {
    const desktopSession = session.entrypoint === 'claude-desktop' || (!session.tty && !session.termProgram && this.desktop)
    if (desktopSession && this.bin && session.id) {
      const where = await openClaude(this.bin, ['--desktop', '--resume', session.id])
      if (where === 'already') await openApp('Claude')
      return
    }
    await focusSession({
      termProgram: session.termProgram,
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

/** A hook whose command or args run Token Deck's hook shim. */
export function isTokenDeckHook(hook: unknown): boolean {
  if (!isRecord(hook)) return false
  const words = [hook.command, ...(Array.isArray(hook.args) ? hook.args : [])]
  return words.some((word) => typeof word === 'string' && HOOK_SHIMS.some((shim) => word.includes(shim)))
}

/** Whether any event in settings.json `hooks` runs Token Deck's hook. */
export function hasTokenDeckHook(hooks: unknown): boolean {
  if (!isRecord(hooks)) return false
  const entries = Object.values(hooks).flatMap((list) => (Array.isArray(list) ? list : []))
  return entries.some((entry) => isRecord(entry) && Array.isArray(entry.hooks) && entry.hooks.some(isTokenDeckHook))
}

/**
 * Adds Token Deck's entry to each event, after the hooks already there. Token Deck's hooks from an
 * earlier connect are taken out first, so connecting again leaves one Token Deck entry per event.
 * Nothing else is removed. An entry written without its list is kept, in a list.
 */
export function withTokenDeckHooks(hooks: unknown, ours: Record<string, HookEntry>): Record<string, unknown> {
  const next: Record<string, unknown> = isRecord(hooks) ? { ...hooks } : {}
  for (const [event, entry] of Object.entries(ours)) {
    const current = next[event]
    const entries: unknown[] = Array.isArray(current) ? current : current == null ? [] : [current]
    next[event] = [...entries.flatMap(withoutTokenDeckHook), entry]
  }
  return next
}

/** The entry without Token Deck's hooks, or nothing when they were all it had. */
function withoutTokenDeckHook(entry: unknown): unknown[] {
  if (!isRecord(entry) || !Array.isArray(entry.hooks) || !entry.hooks.some(isTokenDeckHook)) return [entry]
  const rest = entry.hooks.filter((hook) => !isTokenDeckHook(hook))
  return rest.length ? [{ ...entry, hooks: rest }] : []
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}

function readSessionFiles(): ClaudeAgent[] {
  const dir = path.join(os.homedir(), '.claude', 'sessions')
  let names: string[] = []
  try {
    names = fs.readdirSync(dir)
  } catch {
    return []
  }
  const rows: ClaudeAgent[] = []
  for (const name of names) {
    if (!name.endsWith('.json')) continue
    try {
      const row = JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8')) as ClaudeAgent
      if (row.sessionId) rows.push(row)
    } catch {
      /* a live session file can be mid-write */
    }
  }
  return rows
}

function recentSessionFiles(): ClaudeAgent[] {
  const root = path.join(os.homedir(), '.claude', 'projects')
  let projects: string[] = []
  try {
    projects = fs.readdirSync(root)
  } catch {
    return []
  }
  const found: Array<{ mtime: number; id: string; dir: string; project: string }> = []
  for (const project of projects) {
    const dir = path.join(root, project)
    let names: string[] = []
    try {
      names = fs.readdirSync(dir)
    } catch {
      continue
    }
    for (const name of names) {
      if (!name.endsWith('.jsonl')) continue
      try {
        const stat = fs.statSync(path.join(dir, name))
        if (stat.size < 32) continue
        found.push({ mtime: stat.mtimeMs, id: name.slice(0, -6), dir, project })
      } catch {
        /* gone */
      }
    }
  }
  found.sort((a, b) => b.mtime - a.mtime)
  return found.slice(0, 12).map((row) => ({
    sessionId: row.id,
    name: customTitle(row.dir, row.id) || 'SESSION',
    status: 'idle',
    startedAt: row.mtime,
    updatedAt: row.mtime
  }))
}

function customTitle(dir: string, id: string): string {
  try {
    const parsed = JSON.parse(fs.readFileSync(path.join(dir, id, 'custom-title.json'), 'utf8')) as { customTitle?: string }
    return parsed.customTitle || ''
  } catch {
    return ''
  }
}

function parseAgents(raw: string): ClaudeAgent[] | null {
  if (!raw.trim()) return []
  try {
    const parsed = JSON.parse(raw) as ClaudeAgent[] | { agents?: ClaudeAgent[] }
    return Array.isArray(parsed) ? parsed : parsed.agents || []
  } catch {
    return null
  }
}

function startedAt(value: ClaudeAgent['startedAt']): number {
  if (typeof value === 'number') return value
  const parsed = Date.parse(value || '')
  return Number.isNaN(parsed) ? 0 : parsed
}

/**
 * `claude --desktop` refuses a redirected stdout, so it runs under `script`, which gives it a tty.
 * A session that is already open returns `already` and the caller brings Claude forward.
 */
function openClaude(bin: string, args: string[]): Promise<'opened' | 'already'> {
  return new Promise((resolve, reject) => {
    const child = spawn('/usr/bin/script', ['-q', '/dev/null', bin, ...args], { detached: true, stdio: ['ignore', 'pipe', 'pipe'] })
    let text = ''
    let settled = false
    const done = (error?: Error, result: 'opened' | 'already' = 'opened') => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      child.unref()
      if (error) reject(error)
      else resolve(result)
    }
    const take = (chunk: Buffer | string) => {
      text += String(chunk)
      if (/another terminal|already open|can't run non-interactively/i.test(text) && /another terminal|already open/i.test(text)) done(undefined, 'already')
    }
    const timer = setTimeout(() => done(), 1800)
    child.stdout?.on('data', take)
    child.stderr?.on('data', take)
    child.on('error', (error) => done(error))
    child.on('exit', (code) => {
      if (/another terminal|already open/i.test(text)) done(undefined, 'already')
      else if (code && code !== 0) done(new Error(text.trim() || `claude exited ${code}`))
      else done()
    })
  })
}

function mapStatus(row: ClaudeAgent): SessionStatus {
  if (row.status === 'busy') return 'working'
  if (row.status === 'waiting' && String(row.waitingFor || '').includes('permission')) return 'needs-approval'
  if (row.status === 'waiting') return 'needs-input'
  if (row.status === 'idle') return 'idle'
  return 'idle'
}

function windowOf(row?: { used_percentage?: number; utilization?: number; resets_at?: number; resetsAt?: number }): { pct: number; resetsAt?: number } | undefined {
  if (!row) return undefined
  let pct = row.used_percentage
  if (typeof pct !== 'number' && typeof row.utilization === 'number') pct = row.utilization <= 1 ? row.utilization * 100 : row.utilization
  if (typeof pct !== 'number') return undefined
  const resetsAt = row.resets_at || row.resetsAt
  if (resetsAt && resetsAt * 1000 < Date.now()) return undefined
  return { pct, resetsAt }
}

function writeStatusline(): void {
  const file = path.join(os.homedir(), '.tokendeck', 'bin', 'statusline')
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, STATUSLINE, { mode: 0o755 })
}

function runningClaudeModels(): Promise<Map<string, string>> {
  return new Promise((resolve) => {
    execFile('ps', ['-ax', '-o', 'pid=,command='], { timeout: 4000, encoding: 'utf8', maxBuffer: 4_000_000 }, (err, stdout) => {
      const found = new Map<string, string>()
      if (err) return resolve(found)
      for (const line of String(stdout).split('\n')) {
        if (!line.includes('--model=')) continue
        if (!line.includes('claude')) continue
        const pid = line.trim().split(/\s+/)[0]
        const model = line.split('--model=')[1]?.split(/\s+/)[0]
        if (pid && model) found.set(pid, model)
      }
      resolve(found)
    })
  })
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

function readClaudeCatalog(): Array<{ id: string; name: string }> {
  const dir = path.join(os.homedir(), '.claude', 'cache', 'model-catalog')
  let files: string[] = []
  try {
    files = fs.readdirSync(dir).filter((name) => name.endsWith('.json')).map((name) => path.join(dir, name))
  } catch {
    return []
  }
  files.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)
  for (const file of files) {
    try {
      const parsed = JSON.parse(fs.readFileSync(file, 'utf8')) as { catalog?: { config?: { models?: Array<{ id?: string; name?: string }> } } }
      const rows = parsed.catalog?.config?.models || []
      const models = rows
        .map((row) => ({ id: String(row.id || ''), name: String(row.name || '') }))
        .filter((row) => row.id && row.name)
      if (models.length) return models.slice(0, 6)
    } catch {
      /* try the next catalog file */
    }
  }
  return []
}
