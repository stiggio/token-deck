import fs from 'fs'
import os from 'os'
import path from 'path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ClaudeCode, hasTokenDeckHook, isTokenDeckHook, withTokenDeckHooks } from '../src/main/integrations/claude-code'
import type { SettingsStore } from '../src/main/settings/store'

// detect() returns before it reads settings.json when there is no claude binary, so pretend there is one.
vi.mock('../src/main/system/which', () => ({
  which: async () => '/nonexistent/claude',
  commandVersion: async () => '2.1.319'
}))

type Entry = { matcher?: string; hooks: Array<Record<string, unknown>> }

const HOOK = 'sh ~/.tokendeck/bin/hook 2>/dev/null || true'
const WINDOWS_HOOK = {
  type: 'command',
  command: 'powershell.exe',
  args: ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\Users\\ada\\.tokendeck\\bin\\hook.ps1'],
  async: true
}

/** What install() puts on each event on macOS. */
const OURS: Record<string, Entry> = {
  UserPromptSubmit: { hooks: [{ type: 'command', command: HOOK, async: true }] },
  Stop: { hooks: [{ type: 'command', command: HOOK, async: true }] },
  Notification: { matcher: 'permission_prompt|idle_prompt|agent_needs_input|agent_completed', hooks: [{ type: 'command', command: HOOK, async: true }] },
  PermissionRequest: { hooks: [{ type: 'command', command: HOOK, async: true }] },
  PostModelSwitch: { hooks: [{ type: 'command', command: HOOK, async: true }] },
  SessionStart: { hooks: [{ type: 'command', command: HOOK, timeout: 2 }] },
  SessionEnd: { hooks: [{ type: 'command', command: HOOK, timeout: 2 }] }
}

/** Hooks a user already had, on every event Token Deck uses and one it doesn't. */
const USER_HOOKS: Record<string, Entry[]> = {
  UserPromptSubmit: [{ hooks: [{ type: 'command', command: '~/.claude/hooks/log-prompt.sh' }] }],
  Stop: [{ hooks: [{ type: 'command', command: 'afplay /System/Library/Sounds/Glass.aiff' }] }],
  Notification: [{ matcher: 'permission_prompt', hooks: [{ type: 'command', command: 'terminal-notifier -message "Claude needs you"' }] }],
  PermissionRequest: [{ matcher: 'Bash', hooks: [{ type: 'command', command: '~/.claude/hooks/approve.sh', timeout: 5 }] }],
  PostModelSwitch: [{ hooks: [{ type: 'command', command: 'echo switched >> ~/claude.log' }] }],
  SessionStart: [{ matcher: 'startup', hooks: [{ type: 'command', command: 'cat ~/notes/context.md' }] }],
  SessionEnd: [
    { hooks: [{ type: 'command', command: '~/.claude/hooks/backup.sh' }] },
    { hooks: [{ type: 'command', command: '~/.claude/hooks/cleanup.sh' }] }
  ],
  PreToolUse: [{ matcher: 'Bash', hooks: [{ type: 'command', command: '~/.claude/hooks/guard.sh' }] }]
}

let home = ''
const realEnv = { HOME: process.env.HOME, USERPROFILE: process.env.USERPROFILE }

beforeEach(() => {
  home = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tokendeck-home-')))
  process.env.HOME = home
  process.env.USERPROFILE = home
  // Never let these tests reach the real ~/.claude/settings.json.
  if (os.homedir() !== home) throw new Error(`os.homedir() is ${os.homedir()}, not the temp HOME`)
})

afterEach(() => {
  for (const [key, value] of Object.entries(realEnv)) {
    if (value === undefined) delete process.env[key]
    else process.env[key] = value
  }
  fs.rmSync(home, { recursive: true, force: true })
})

function settingsFile(): string {
  return path.join(home, '.claude', 'settings.json')
}

function writeSettings(bytes: Buffer | string): void {
  fs.mkdirSync(path.dirname(settingsFile()), { recursive: true })
  fs.writeFileSync(settingsFile(), bytes)
}

function readSettings() {
  return JSON.parse(fs.readFileSync(settingsFile(), 'utf8'))
}

/** The command the status line shim runs, saved verbatim. */
function savedStatusline(): unknown {
  return fs.readFileSync(path.join(home, '.tokendeck', 'statusline-original'), 'utf8')
}

function claude(): ClaudeCode {
  return new ClaudeCode({} as SettingsStore, () => {})
}

describe.skipIf(process.platform === 'win32')('connecting Claude Code', () => {
  it('keeps your hooks and status line, adds Token Deck once, and Stop watching restores the file', async () => {
    const original = {
      model: 'opus',
      env: { GREETING: 'שלום' },
      hooks: USER_HOOKS,
      statusLine: { type: 'command', command: '~/.claude/statusline-command.sh' }
    }
    // Four spaces, CRLF and no final newline. Token Deck writes two spaces and LF, so only a byte copy gets this back.
    const bytes = Buffer.from(JSON.stringify(original, null, 4).replace(/\n/g, '\r\n'))
    writeSettings(bytes)
    const app = claude()

    await app.install()
    await app.install()

    const after = readSettings()
    for (const event of Object.keys(OURS)) {
      // Your entries first, unchanged, then Token Deck's, once.
      expect(after.hooks[event], event).toEqual([...USER_HOOKS[event]!, OURS[event]])
    }
    expect(after.hooks.PreToolUse).toEqual(USER_HOOKS.PreToolUse)
    expect(after.model).toBe('opus')
    expect(after.env).toEqual({ GREETING: 'שלום' })
    expect(after.statusLine).toEqual({ type: 'command', command: 'sh ~/.tokendeck/bin/statusline' })
    expect(savedStatusline()).toBe('~/.claude/statusline-command.sh')
    expect(app.hooksInstalled).toBe(true)
    expect(app.statusChained).toBe(true)

    expect(fs.readFileSync(settingsFile() + '.tokendeck-backup')).toEqual(bytes)
    app.restore()
    expect(fs.readFileSync(settingsFile())).toEqual(bytes)
    await app.detect()
    expect(app.hooksInstalled).toBe(false)
    expect(app.statusChained).toBe(false)
  })

  it.each(['~/.claude/statusline.sh', 'npx -y ccstatusline@latest', 'bunx ccusage statusline'])('saves the status line %s for the shim to run', async (command) => {
    writeSettings(JSON.stringify({ statusLine: { type: 'command', command } }))
    await claude().install()
    expect(savedStatusline()).toBe(command)
  })
})

describe('Token Deck hook entries', () => {
  const say = { type: 'command', command: 'say done' }

  it('are recognised by their command, or on Windows by their args', () => {
    expect(isTokenDeckHook({ type: 'command', command: HOOK })).toBe(true)
    expect(isTokenDeckHook(WINDOWS_HOOK)).toBe(true)
    expect(isTokenDeckHook({ ...WINDOWS_HOOK, args: ['-File', 'C:/Users/ada/.tokendeck/bin/hook.ps1'] })).toBe(true)
    expect(isTokenDeckHook(say)).toBe(false)
    expect(isTokenDeckHook({ type: 'command', command: 'sh ~/.tokendeck/bin/statusline' })).toBe(false)
    expect(isTokenDeckHook(null)).toBe(false)
    expect(isTokenDeckHook('sh ~/.tokendeck/bin/hook')).toBe(false)
  })

  it('replace only Token Deck’s own entry when you connect again on Windows', () => {
    const yours = { matcher: 'startup', hooks: [say] }
    const ours = { hooks: [WINDOWS_HOOK] }
    const once = withTokenDeckHooks({ SessionStart: [yours] }, { SessionStart: ours })
    expect(withTokenDeckHooks(once, { SessionStart: ours })).toEqual({ SessionStart: [yours, ours] })
  })

  it('keep your hook when it shares an entry with Token Deck’s', () => {
    const ours = OURS.Stop!
    const shared = { hooks: [say, { type: 'command', command: HOOK, async: true }] }
    expect(withTokenDeckHooks({ Stop: [shared] }, { Stop: ours })).toEqual({ Stop: [{ hooks: [say] }, ours] })
  })

  it('leave other events alone, keep an entry written without its list, and do not change their input', () => {
    const input = { PreToolUse: [{ matcher: 'Bash', hooks: [say] }], Stop: { hooks: [say] } }
    const copy = structuredClone(input)
    expect(withTokenDeckHooks(input, { Stop: OURS.Stop!, SessionEnd: OURS.SessionEnd! })).toEqual({
      PreToolUse: [{ matcher: 'Bash', hooks: [say] }],
      Stop: [{ hooks: [say] }, OURS.Stop],
      SessionEnd: [OURS.SessionEnd]
    })
    expect(input).toEqual(copy)
    expect(withTokenDeckHooks(undefined, { Stop: OURS.Stop! })).toEqual({ Stop: [OURS.Stop] })
  })

  it('are found by detect(), including the Windows hook', async () => {
    expect(hasTokenDeckHook({ Stop: [{ hooks: [say] }] })).toBe(false)
    expect(hasTokenDeckHook(undefined)).toBe(false)
    writeSettings(JSON.stringify({ hooks: { Stop: [{ hooks: [say] }, { hooks: [WINDOWS_HOOK] }] } }, null, 2))
    const app = claude()
    await app.detect()
    expect(app.hooksInstalled).toBe(true)
  })
})
