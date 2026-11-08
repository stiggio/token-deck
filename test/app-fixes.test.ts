import fs from 'fs'
import os from 'os'
import path from 'path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { isAppUrl, isExternalLink } from '../src/main/system/navigation'
import { parseBundleId, parseLsofCwd, parseProcessList, parseTermProgram } from '../src/main/system/terminal'
import { readIfExists, writeFileAtomic } from '../src/main/system/files'
import { ClaudeCode, readOriginalStatusLine, resumeCommand, transcriptCwd, withoutTokenDeckHooks } from '../src/main/integrations/claude-code'
import { editConfig, removeConfigKeys, setTopLevel, topLevelValue, trailingComment, withoutTopLevel } from '../src/main/integrations/codex'
import { majorVersion, mergePermission, providerModels, sessionFrom } from '../src/main/integrations/opencode'
import { Controller, current, isLive, nextPageNeedingYou } from '../src/main/modes/controller'
import { loadMode } from '../src/main/modes/custom'
import { OVERLAY_GROUPS, groupOk } from '../src/shared/overlays'
import type { SettingsStore } from '../src/main/settings/store'

vi.mock('../src/main/system/which', () => ({
  which: async () => '/nonexistent/claude',
  commandVersion: async () => '2.1.319',
  loginShellVar: async () => ''
}))

let home = ''
const realEnv = { HOME: process.env.HOME, USERPROFILE: process.env.USERPROFILE }

beforeEach(() => {
  home = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tokendeck-fixes-')))
  process.env.HOME = home
  process.env.USERPROFILE = home
  if (os.homedir() !== home) throw new Error('os.homedir() is not the temp HOME')
})

afterEach(() => {
  process.env.HOME = realEnv.HOME
  process.env.USERPROFILE = realEnv.USERPROFILE
  fs.rmSync(home, { recursive: true, force: true })
})

function store(): SettingsStore {
  const data: Record<string, unknown> = { favorites: { 'claude-code': [], codex: [], opencode: [] }, usage: {} }
  return { get: (key: string) => data[key], set: (key: string, value: unknown) => { data[key] = value } } as unknown as SettingsStore
}

const settingsFile = () => path.join(home, '.claude', 'settings.json')
const writeSettings = (value: unknown) => {
  fs.mkdirSync(path.dirname(settingsFile()), { recursive: true })
  fs.writeFileSync(settingsFile(), typeof value === 'string' ? value : JSON.stringify(value, null, 2))
}
const readSettings = () => JSON.parse(fs.readFileSync(settingsFile(), 'utf8'))

describe('the settings window only ever loads the app', () => {
  it('accepts the bundled page and the dev server, nothing else', () => {
    const page = 'file:///Applications/Token%20Deck.app/Contents/Resources/app.asar/out/renderer/index.html'
    expect(isAppUrl(page, page)).toBe(true)
    expect(isAppUrl(page + '#about', page)).toBe(true)
    expect(isAppUrl('file:///Applications/Token Deck.app/Contents/Resources/app.asar/out/renderer/index.html', page)).toBe(true)
    expect(isAppUrl('file:///tmp/out/renderer/index.html', page)).toBe(false)
    expect(isAppUrl('file://evil-share/out/renderer/index.html', 'file:///out/renderer/index.html')).toBe(false)
    expect(isAppUrl('file:///tmp/evil.html', page)).toBe(false)
    expect(isAppUrl('https://usage.stigg.io/', page)).toBe(false)
    expect(isAppUrl('', page)).toBe(false)
    const win = 'file:///C:/Users/Ada/AppData/Local/Programs/token-deck/resources/app.asar/out/renderer/index.html'
    expect(isAppUrl(win.replace('C:/Users/Ada', 'c:/users/ada'), win, true)).toBe(true)
    expect(isAppUrl(win.replace('C:/Users/Ada', 'c:/users/ada'), win, false)).toBe(false)

    expect(isAppUrl('http://localhost:5173/', 'http://localhost:5173')).toBe(true)
    expect(isAppUrl('http://localhost:5173/#about', 'http://localhost:5173')).toBe(true)
    expect(isAppUrl('http://localhost:5173.evil.com/', 'http://localhost:5173')).toBe(false)
    expect(isAppUrl(page, 'http://localhost:5173')).toBe(false)
  })

  it('opens only https links outside the app', () => {
    expect(isExternalLink('https://github.com/stiggio/token-deck')).toBe(true)
    expect(isExternalLink('file:///etc/passwd')).toBe(false)
    expect(isExternalLink('javascript:alert(1)')).toBe(false)
  })
})

describe('finding the terminal an agent runs in', () => {
  it('keeps agent processes that have a terminal', () => {
    const ps = [
      '  501 ttys003  /opt/homebrew/bin/codex',
      '  502 ??       /opt/homebrew/bin/codex app-server',
      '  503 ttys004  node /Users/ada/.npm/bin/opencode',
      '  504 ttys005  /bin/zsh -l',
      '  505 ttys006  /opt/homebrew/bin/codex app-server --listen stdio://',
      '  506 ttys007  node /Users/ada/.npm/bin/opencode serve --port 4096'
    ].join('\n')
    expect(parseProcessList(ps, ['codex', 'opencode'])).toEqual([
      { pid: 501, tty: '/dev/ttys003', command: '/opt/homebrew/bin/codex' },
      { pid: 503, tty: '/dev/ttys004', command: 'node /Users/ada/.npm/bin/opencode' }
    ])
  })

  it('reads the folder from lsof and TERM_PROGRAM from ps -E', () => {
    expect(parseLsofCwd('p501\nfcwd\nn/Users/ada/dev/app\n')).toBe('/Users/ada/dev/app')
    expect(parseTermProgram('/opt/homebrew/bin/codex TERM=xterm TERM_PROGRAM=iTerm.app HOME=/Users/ada')).toBe('iTerm.app')
    expect(parseTermProgram('/opt/homebrew/bin/codex HOME=/Users/ada')).toBeUndefined()
    expect(parseBundleId('/opt/homebrew/bin/codex TERM_PROGRAM=tmux __CFBundleIdentifier=com.github.wez.wezterm HOME=/Users/ada')).toBe('com.github.wez.wezterm')
    expect(parseBundleId('/opt/homebrew/bin/codex HOME=/Users/ada')).toBeUndefined()
  })
})

describe('writing a user’s config file', () => {
  it.skipIf(process.platform === 'win32')('replaces the file in one step and keeps a dotfiles symlink', () => {
    const real = path.join(home, 'dotfiles', 'settings.json')
    const link = path.join(home, '.claude', 'settings.json')
    fs.mkdirSync(path.dirname(real), { recursive: true })
    fs.mkdirSync(path.dirname(link), { recursive: true })
    fs.writeFileSync(real, '{"model":"opus"}')
    fs.symlinkSync(real, link)
    writeFileAtomic(link, '{"model":"sonnet"}\n')
    expect(fs.lstatSync(link).isSymbolicLink()).toBe(true)
    expect(fs.readFileSync(real, 'utf8')).toBe('{"model":"sonnet"}\n')
    // No temp file left behind.
    expect(fs.readdirSync(path.dirname(real))).toEqual(['settings.json'])
  })

  it('creates a missing file and its folder', () => {
    const file = path.join(home, '.codex', 'config.toml')
    writeFileAtomic(file, 'model = "x"\n')
    expect(fs.readFileSync(file, 'utf8')).toBe('model = "x"\n')
  })

  it('takes only a missing file for empty; any other read error is thrown', () => {
    expect(readIfExists(path.join(home, 'nope.json'))).toBeNull()
    expect(() => readIfExists(home)).toThrow()
  })
})

describe('Claude Code settings', () => {
  const claude = () => new ClaudeCode(store(), () => undefined)

  it('Stop watching takes out only Token Deck and puts the status line back with its other fields', async () => {
    const userHook = { hooks: [{ type: 'command', command: '~/.claude/hooks/log.sh' }] }
    writeSettings({
      model: 'opus',
      hooks: { UserPromptSubmit: [userHook] },
      statusLine: { type: 'command', command: 'bash "$HOME/.claude/statusline.sh"', padding: 2 }
    })
    const c = claude()
    await c.install()
    const connected = readSettings()
    expect(connected.statusLine).toEqual({ type: 'command', command: 'sh ~/.tokendeck/bin/statusline', padding: 2 })
    // The shim runs the original command exactly, quotes and all.
    expect(fs.readFileSync(path.join(home, '.tokendeck', 'statusline-original'), 'utf8')).toBe('bash "$HOME/.claude/statusline.sh"')
    // Something else changes the file after connecting; Stop watching must keep it.
    writeSettings({ ...connected, theme: 'dark' })
    c.uninstall()
    expect(readSettings()).toEqual({
      model: 'opus',
      theme: 'dark',
      hooks: { UserPromptSubmit: [userHook] },
      statusLine: { type: 'command', command: 'bash "$HOME/.claude/statusline.sh"', padding: 2 }
    })
  })

  it('forgets a status line you deleted, so Stop watching never brings it back', async () => {
    writeSettings({ statusLine: { type: 'command', command: '~/.claude/old-statusline.sh' } })
    const c = claude()
    await c.install()
    c.uninstall()
    // You remove your status line, then connect and stop watching again.
    writeSettings({})
    await c.install()
    expect(fs.existsSync(path.join(home, '.tokendeck', 'statusline-original'))).toBe(false)
    c.uninstall()
    expect(readSettings()).toEqual({})
  })

  it('takes a session that ended for finished, and a running one for running', () => {
    const c = claude()
    const hook = (name: string, headers: Record<string, string> = {}) =>
      c.ingest({ source: 'claude', headers, body: { session_id: 's1', hook_event_name: name, cwd: '/Users/ada/app' } })
    hook('UserPromptSubmit', { 'x-td-tty': 'ttys004', 'x-td-term': 'iTerm.app' })
    expect(c.sessions.get('s1')).toMatchObject({ live: true, tty: '/dev/ttys004', status: 'working' })
    hook('SessionEnd')
    expect(c.sessions.get('s1')).toMatchObject({ live: false, ended: true, tty: undefined, status: 'completed' })
    // A status line that arrives late doesn't bring it back.
    c.ingest({ source: 'statusline', headers: {}, body: { session_id: 's1' } })
    expect(c.sessions.get('s1')?.live).toBe(false)
    // Resuming it does.
    hook('SessionStart', { 'x-td-tty': 'ttys009' })
    expect(c.sessions.get('s1')).toMatchObject({ live: true, ended: false, tty: '/dev/ttys009' })
  })

  it('Stop watching removes the status line when there was none before', async () => {
    writeSettings({})
    const c = claude()
    await c.install()
    c.uninstall()
    expect(readSettings()).toEqual({})
  })

  it('reads a status line saved by an older version as a bare command', () => {
    fs.mkdirSync(path.join(home, '.tokendeck'), { recursive: true })
    fs.writeFileSync(path.join(home, '.tokendeck', 'statusline-original.json'), JSON.stringify('~/.claude/statusline-command.sh'))
    expect(readOriginalStatusLine()).toEqual({ type: 'command', command: '~/.claude/statusline-command.sh' })
  })

  it('never overwrites a settings.json that is not valid JSON', async () => {
    const broken = '{ "model": "opus", // a comment\n }'
    writeSettings(broken)
    const c = claude()
    await expect(c.setModel('sonnet')).rejects.toThrow()
    await expect(c.install()).rejects.toThrow()
    expect(() => c.uninstall()).toThrow()
    expect(fs.readFileSync(settingsFile(), 'utf8')).toBe(broken)
  })

  it('restores the default effort and keeps other per-model settings', async () => {
    writeSettings({ model: 'opus', effortLevel: 'high', modelSettings: { opus: { effortLevel: 'xhigh', other: 1 }, sonnet: { effortLevel: 'low' } } })
    await claude().clearEffort()
    expect(readSettings()).toEqual({ model: 'opus', modelSettings: { opus: { other: 1 }, sonnet: { effortLevel: 'low' } } })
  })

  it('reads Ultracode from the file instead of guessing', () => {
    writeSettings({ ultracode: true })
    expect(claude().readUltracode()).toBe(true)
  })

  it('drops events that held only Token Deck hooks', () => {
    const ours = { hooks: [{ type: 'command', command: 'sh ~/.tokendeck/bin/hook 2>/dev/null || true' }] }
    const theirs = { hooks: [{ type: 'command', command: 'echo hi' }] }
    expect(withoutTokenDeckHooks({ Stop: [ours], SessionEnd: [theirs, ours] })).toEqual({ SessionEnd: [theirs] })
    expect(withoutTokenDeckHooks({ Stop: [ours] })).toBeUndefined()
  })

  it('reopens a finished session in its own folder', () => {
    const file = path.join(home, 'session.jsonl')
    fs.writeFileSync(file, '{"type":"summary"}\n{"cwd":"/Users/ada/dev/my app","type":"user"}\n')
    expect(transcriptCwd(file)).toBe('/Users/ada/dev/my app')
    expect(resumeCommand('/opt/homebrew/bin/claude', '3f2a-9c', '/Users/ada/dev/my app')).toBe('cd "/Users/ada/dev/my app" && "/opt/homebrew/bin/claude" --resume 3f2a-9c')
    expect(resumeCommand('/opt/homebrew/bin/claude', 'id;rm -rf ~', '/tmp/$(boom)')).toBe('"/opt/homebrew/bin/claude" --resume idrm-rf')
  })
})

describe('Codex config.toml', () => {
  const file = () => path.join(home, '.codex', 'config.toml')

  it('keeps a comment on the line it changes, and backs the file up once', () => {
    fs.mkdirSync(path.dirname(file()), { recursive: true })
    const original = 'model = "gpt-5" # the default\nnotify = ["say"]\n\n[profiles.fast]\nmodel = "mini"\n'
    fs.writeFileSync(file(), original)
    editConfig({ model: 'gpt-5-codex', model_reasoning_effort: 'high' })
    expect(fs.readFileSync(file(), 'utf8')).toBe('model_reasoning_effort = "high"\nmodel = "gpt-5-codex" # the default\nnotify = ["say"]\n\n[profiles.fast]\nmodel = "mini"\n')
    expect(fs.readFileSync(file() + '.tokendeck-backup', 'utf8')).toBe(original)
  })

  it('removes a top-level key to restore the default, never one inside a table', () => {
    fs.mkdirSync(path.dirname(file()), { recursive: true })
    fs.writeFileSync(file(), 'model = "gpt-5"\nmodel_reasoning_effort = "low"\n[profiles.fast]\nmodel = "mini"\n')
    removeConfigKeys(['model'])
    expect(fs.readFileSync(file(), 'utf8')).toBe('model_reasoning_effort = "low"\n[profiles.fast]\nmodel = "mini"\n')
  })

  it('finds a trailing comment only outside the value', () => {
    expect(trailingComment('model = "a#b" # note')).toBe(' # note')
    expect(trailingComment('model = "a#b"')).toBe('')
    expect(trailingComment('model = "a" # note\r')).toBe(' # note')
  })

  it('keeps a Windows file’s CRLF line endings and its comments', () => {
    const crlf = 'model = "gpt-5" # mine\r\napproval_policy = "on-request"\r\n\r\n[profiles.fast]\r\nmodel = "mini"\r\n'
    expect(setTopLevel(crlf, { model: 'gpt-5-codex' })).toBe(crlf.replace('"gpt-5"', '"gpt-5-codex"'))
    expect(withoutTopLevel(crlf, ['model'])).toBe('approval_policy = "on-request"\r\n\r\n[profiles.fast]\r\nmodel = "mini"\r\n')
  })

  it('reads past multi-line arrays and strings at the top', () => {
    const text = [
      'notify = [',
      '  ["terminal-notifier", "-title", "Codex"],',
      ']',
      'instructions = """',
      'model = "not a key"',
      '[not a table]',
      '"""',
      'model = "gpt-5"',
      '',
      '[mcp_servers.docs]',
      'command = "npx"',
      ''
    ].join('\n')
    expect(topLevelValue(text, 'model')).toBe('gpt-5')
    // The real top-level key changes; nothing is added at the top, which TOML would reject as a duplicate.
    expect(setTopLevel(text, { model: 'o3' })).toBe(text.replace('model = "gpt-5"', 'model = "o3"'))
    expect(withoutTopLevel(text, ['model'])).toBe(text.replace('model = "gpt-5"\n', ''))
    expect(withoutTopLevel(text, ['model_reasoning_effort'])).toBe(text)
  })

  it('never reads a key from a [table] as the top-level one', () => {
    expect(topLevelValue('[profiles.fast]\nmodel = "mini"\n', 'model')).toBe('')
    expect(topLevelValue("model = 'gpt-5' # literal", 'model')).toBe('gpt-5')
  })
})

describe('OpenCode', () => {
  it('reads the major version correctly', () => {
    expect(majorVersion('1.2.3')).toBe(1)
    expect(majorVersion('opencode 2.0.1')).toBe(2)
    expect(majorVersion('')).toBe(1)
  })

  it('sorts sessions by their own update time, not by when Token Deck polled', () => {
    const row = sessionFrom({ id: 's1', title: 'notes', directory: '/Users/ada/notes', time: { created: 1, updated: 1_700_000_000_000 } }, 'idle')
    expect(row.updatedAt).toBe(1_700_000_000_000)
    expect(row.cwd).toBe('/Users/ada/notes')
    expect(row.title).toBe('NOTES')
  })

  it('offers the providers models, defaults first', () => {
    const data = { providers: [{ id: 'opencode', models: { 'big-pickle': {}, 'grok-code': {} } }, { id: 'anthropic', models: [{ id: 'claude-sonnet' }] }], default: { anthropic: 'claude-sonnet' } }
    expect(providerModels(data)).toEqual(['anthropic/claude-sonnet', 'opencode/big-pickle', 'opencode/grok-code'])
  })

  it('keeps per-command bash rules and other permission keys', () => {
    expect(mergePermission({ bash: { 'git push': 'ask', '*': 'allow' }, webfetch: 'deny' }, 'ASK')).toEqual({ bash: { 'git push': 'ask', '*': 'ask' }, webfetch: 'deny', edit: 'allow' })
    expect(mergePermission(undefined, 'READ')).toEqual({ edit: 'ask', bash: 'ask' })
  })
})

describe('the deck', () => {
  it('cycles through the pages with a session that needs you', () => {
    const rows = Array.from({ length: 14 }, (_, i) => ({ status: i === 2 || i === 9 ? 'needs-approval' : 'idle' }))
    expect(nextPageNeedingYou(rows, 0)).toBe(1)
    expect(nextPageNeedingYou(rows, 1)).toBe(0)
    expect(nextPageNeedingYou(rows.map(() => ({ status: 'idle' })), 2)).toBe(0)
  })

  it('stops showing a usage window once it has reset', () => {
    expect(current({ pct: 40, resetsAt: Math.floor(Date.now() / 1000) - 60 })).toBeUndefined()
    expect(current({ pct: 40, resetsAt: Math.floor(Date.now() / 1000) + 600 })?.pct).toBe(40)
    expect(current({ pct: 40 })?.pct).toBe(40)
  })

  it('counts only busy Codex and OpenCode threads as live, since they list their whole history', () => {
    expect(isLive({ agent: 'codex', status: 'idle', live: undefined })).toBe(false)
    expect(isLive({ agent: 'opencode', status: 'idle', live: true })).toBe(false)
    expect(isLive({ agent: 'codex', status: 'needs-approval', live: undefined })).toBe(true)
    expect(isLive({ agent: 'claude-code', status: 'idle', live: true })).toBe(true)
    expect(isLive({ agent: 'claude-code', status: 'completed', live: false })).toBe(false)
  })

  it('applies a permission level only while its preview is on the deck', async () => {
    vi.useFakeTimers()
    try {
      const setPermission = vi.fn(async () => undefined)
      const data: Record<string, unknown> = { mode: 'models', favorites: { 'claude-code': [], codex: [], opencode: [] }, usage: {} }
      const deckStore = { get: (key: string) => data[key], set: (key: string, value: unknown) => { data[key] = value } } as unknown as SettingsStore
      const claudeStub = { bin: '/usr/local/bin/claude', desktop: false, sessions: new Map(), setPermission }
      const none = { bin: null, sessions: new Map() }
      const launch = { cursor: { installed: false }, amp: { installed: false }, devin: { installed: false } }
      const deck = new Controller(deckStore, claudeStub as never, none as never, none as never, launch as never, async () => undefined, () => undefined, async () => true)
      const right = (action: 'cw' | 'click') => deck.handle({ type: 'knob', which: 'right', action })

      await right('click')
      expect(deck.overlay).toEqual(['TURN', 'FIRST'])
      expect(setPermission).not.toHaveBeenCalled()

      await right('cw')
      expect(deck.permissionPending).toBe(true)
      await right('click')
      expect(setPermission).toHaveBeenCalledTimes(1)

      // Turn, walk away until the preview is gone, then press: nothing is applied.
      await right('cw')
      vi.advanceTimersByTime(6000)
      expect(deck.permissionPending).toBe(false)
      await right('click')
      expect(setPermission).toHaveBeenCalledTimes(1)
    } finally {
      vi.useRealTimers()
    }
  })

  it('keeps a mode file with a mistake on six keys and marks it', () => {
    const dir = path.join(home, '.tokendeck', 'modes')
    fs.mkdirSync(dir, { recursive: true })
    const broken = path.join(dir, 'build.json')
    fs.writeFileSync(broken, '{ "name": "Build", "tiles": [ { "label": "TEST" } ')
    expect(loadMode(broken)).toMatchObject({ name: 'build', invalid: true, tiles: [null, null, null, null, null, null] })
    fs.writeFileSync(broken, '[]')
    expect(loadMode(broken).invalid).toBe(true)
    fs.writeFileSync(broken, JSON.stringify({ name: 'Build', tiles: [{ label: 42 }, 'junk', { label: 'LOGS' }] }))
    const mode = loadMode(broken)
    expect(mode.invalid).toBeUndefined()
    expect(mode.tiles.map((tile) => tile?.label ?? null)).toEqual(['42', null, 'LOGS', null, null, null])
    expect(mode.errors).toEqual(["Tile 1 label isn't text."])
  })

  it('keeps the new deck messages short enough for a key', () => {
    for (const group of ['DEFAULT', 'TURN', 'FIRST', 'MODE FILE', 'ERROR']) {
      expect(OVERLAY_GROUPS).toContain(group)
      expect(groupOk(group)).toBe(true)
    }
  })
})
