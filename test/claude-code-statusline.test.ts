import { spawnSync } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ClaudeCode, writeStatusline } from '../src/main/integrations/claude-code'
import type { SettingsStore } from '../src/main/settings/store'

// No claude binary, so install() never runs one.
vi.mock('../src/main/system/which', () => ({ which: async () => null, commandVersion: async () => '' }))

/** What Claude Code sends a status line on stdin, cut down. */
const SESSION = '{"model":{"display_name":"Opus"},"context_window":{"used_percentage":42}}'
const ESC = '\u001b'

/**
 * Status line commands and what they print. statusline-original.json holds JSON.stringify(command), which
 * escapes their quotes, backslashes and control characters, and the shim has to undo every one.
 */
const STATUS_LINES = [
  { name: 'double quotes', command: 'echo "quoted"', prints: 'quoted\n' },
  {
    name: 'backslashes',
    command: String.raw`printf '%s\n' 'C:\temp\new' "back\\slash" \"escaped\" 'trailing\'`,
    prints: 'C:\\temp\\new\nback\\slash\n"escaped"\ntrailing\\\n'
  },
  { name: 'dollar signs', command: String.raw`x=deck; printf '%s\n' "$x" '$x' "\$x" "$((6 * 7))" "*"`, prints: 'deck\n$x\n$x\n42\n*\n' },
  { name: 'single quotes', command: `echo 'it'"'"'s'`, prints: "it's\n" },
  { name: 'a quote at each end', command: `"printf" '%s\\n' "hi"`, prints: 'hi\n' },
  { name: 'colours from printf', command: String.raw`printf '\033[2m%s\033[0m\n' dim`, prints: `${ESC}[2mdim${ESC}[0m\n` },
  {
    name: 'a newline, a tab and other control characters',
    command: `echo one\nprintf '%s\\n' '\ttwo' '${ESC}[1mbold${ESC}[0m' 'cr\r bs\b ff\f'`,
    prints: `one\n\ttwo\n${ESC}[1mbold${ESC}[0m\ncr\r bs\b ff\f\n`
  },
  { name: 'text that is not ASCII', command: `printf '%s\\n' "שלום 📁"`, prints: 'שלום 📁\n' },
  {
    name: 'a one-liner that reads the session',
    command: String.raw`input=$(cat); printf '[%s] %s%%\n' "$(printf '%s' "$input" | sed 's/.*"display_name":"\([^"]*\)".*/\1/')" "$(printf '%s' "$input" | sed 's/.*"used_percentage":\([0-9]*\).*/\1/')"`,
    prints: '[Opus] 42%\n'
  }
]

let home = ''
const realEnv = { HOME: process.env.HOME, USERPROFILE: process.env.USERPROFILE }

beforeEach(() => {
  home = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tokendeck-home-')))
  process.env.HOME = home
  process.env.USERPROFILE = home
  // Never let these tests reach the real ~/.claude or ~/.tokendeck.
  if (os.homedir() !== home) throw new Error(`os.homedir() is ${os.homedir()}, not the temp HOME`)
})

afterEach(() => {
  for (const [key, value] of Object.entries(realEnv)) {
    if (value === undefined) delete process.env[key]
    else process.env[key] = value
  }
  fs.rmSync(home, { recursive: true, force: true })
})

function tokendeck(...parts: string[]): string {
  return path.join(home, '.tokendeck', ...parts)
}

/** Runs sh the way Claude Code runs a status line: the session on stdin, in the session's directory. */
function sh(...args: string[]): { stdout: string; stderr: string } {
  const { stdout, stderr } = spawnSync('sh', args, { input: SESSION, cwd: home, env: { ...process.env, HOME: home }, encoding: 'utf8' })
  return { stdout, stderr }
}

describe.skipIf(process.platform === 'win32')('the status line shim', () => {
  it.each(STATUS_LINES)('prints what the status line prints by itself, with $name', async ({ command, prints }) => {
    fs.mkdirSync(path.join(home, '.claude'))
    fs.writeFileSync(path.join(home, '.claude', 'settings.json'), JSON.stringify({ statusLine: { type: 'command', command } }))
    await new ClaudeCode({} as SettingsStore, () => {}).install()

    const direct = sh('-c', command)
    expect(direct.stdout).toBe(prints)
    expect(sh(tokendeck('bin', 'statusline'))).toEqual(direct)
    // Token Deck still gets the session.
    expect(fs.readFileSync(tokendeck('last-statusline.json'), 'utf8')).toBe(SESSION)
  })

  it('runs a status line that an older Token Deck saved, once the app restarts', () => {
    // Every version has saved JSON.stringify(command), and only install() writes it. start() rewrites the shim.
    writeStatusline()
    for (const { command, prints } of STATUS_LINES) {
      fs.writeFileSync(tokendeck('statusline-original.json'), JSON.stringify(command))
      expect(sh(tokendeck('bin', 'statusline')).stdout, command).toBe(prints)
    }
  })

  it('runs nothing when no status line was saved', () => {
    writeStatusline()
    expect(sh(tokendeck('bin', 'statusline')).stdout).toBe('')
    fs.writeFileSync(tokendeck('statusline-original.json'), 'null')
    expect(sh(tokendeck('bin', 'statusline')).stdout).toBe('')
    expect(fs.readFileSync(tokendeck('last-statusline.json'), 'utf8')).toBe(SESSION)
  })
})
