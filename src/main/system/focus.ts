import { execFile } from 'child_process'
import { which } from './which'

export type FocusTarget = {
  termProgram?: string
  tty?: string
  cwd?: string
  sessionId?: string
  bundleId?: string
  app?: string
}

const BUNDLES: Record<string, string> = {
  Apple_Terminal: 'com.apple.Terminal',
  'iTerm.app': 'com.googlecode.iterm2',
  ghostty: 'com.mitchellh.ghostty',
  WarpTerminal: 'dev.warp.Warp-Stable',
  kitty: 'net.kovidgoyal.kitty',
  vscode: 'com.microsoft.VSCode',
  Cursor: 'com.todesktop.230313mzl4w4u92',
  claude: 'com.anthropic.claudefordesktop',
  codex: 'com.openai.codex'
}

function osa(script: string, args: string[] = []): Promise<void> {
  return new Promise((resolve, reject) => {
    execFile('osascript', ['-e', script, ...args], { timeout: 8000 }, (err) => {
      if (err) reject(err)
      else resolve()
    })
  })
}

export async function focusSession(target: FocusTarget): Promise<void> {
  if (process.platform !== 'darwin') {
    await focusWindows(target)
    return
  }
  const term = target.termProgram || ''
  const tty = target.tty || ''
  if (term === 'Apple_Terminal' && tty) {
    await osa(
      `on run argv
        set theTTY to item 1 of argv
        tell application "Terminal"
          repeat with w in windows
            repeat with t in tabs of w
              if tty of t is theTTY then
                set selected of t to true
                set frontmost of w to true
                activate
                return
              end if
            end repeat
          end repeat
          activate
        end tell
      end run`,
      [tty]
    )
    return
  }
  if (term === 'iTerm.app' && (tty || target.sessionId)) {
    await osa(
      `on run argv
        set theTTY to item 1 of argv
        set theID to item 2 of argv
        tell application "iTerm"
          repeat with w in windows
            repeat with t in tabs of w
              repeat with s in sessions of t
                if tty of s is theTTY or id of s is theID then
                  select s
                  select t
                  select w
                  activate
                  return
                end if
              end repeat
            end repeat
          end repeat
          activate
        end tell
      end run`,
      [tty, target.sessionId || '']
    )
    return
  }
  if (term === 'ghostty' && tty) {
    try {
      await osa(`tell application "Ghostty" to focus (first terminal whose tty is "${tty.replace(/"/g, '')}")`)
      return
    } catch {
      /* 1.3 falls through */
    }
  }
  if ((term === 'vscode' || term === 'Cursor') && target.cwd) {
    const bin = await which(term === 'Cursor' ? 'cursor' : 'code')
    if (bin) {
      await new Promise<void>((resolve) => {
        execFile(bin, ['-r', target.cwd!], () => resolve())
      })
      return
    }
  }
  if (target.termProgram === 'claude-desktop' && target.sessionId) {
    const bin = await which('claude')
    if (bin) {
      await new Promise<void>((resolve) => {
        execFile(bin, ['--desktop', '--resume', target.sessionId!], () => resolve())
      })
      return
    }
  }
  const bundle = target.bundleId || BUNDLES[term] || target.app
  if (bundle) await osa(`tell application id "${bundle}" to activate`)
}

export async function raiseBundle(bundleId: string): Promise<void> {
  if (process.platform !== 'darwin') return
  await osa(
    `tell application "System Events"
      set frontmost of (first process whose bundle identifier is "${bundleId}") to true
      try
        perform action "AXRaise" of window 1 of (first process whose bundle identifier is "${bundleId}")
      end try
    end tell`
  )
}

export async function cycleBundles(bundleIds: string[], index: number): Promise<number> {
  if (bundleIds.length === 0) return 0
  const next = ((index % bundleIds.length) + bundleIds.length) % bundleIds.length
  await raiseBundle(bundleIds[next]!)
  return next
}

async function focusWindows(target: FocusTarget): Promise<void> {
  const name = target.app || 'WindowsTerminal'
  await new Promise<void>((resolve) => {
    execFile(
      'powershell.exe',
      ['-NoProfile', '-Command', `$p = Get-Process ${name} -ErrorAction SilentlyContinue | Select-Object -First 1; if ($p) { (New-Object -ComObject WScript.Shell).AppActivate($p.Id) | Out-Null }`],
      () => resolve()
    )
  })
}

export async function askAutomation(): Promise<void> {
  if (process.platform !== 'darwin') return
  const scripts = [
    'tell application "System Events" to get name of first process',
    'tell application "Terminal" to get name',
    'tell application "System Events" to get name of processes'
  ]
  for (const script of scripts) {
    await osa(script).catch(() => undefined)
  }
}

export function accessibilityTrusted(prompt: boolean): boolean {
  if (process.platform !== 'darwin') return true
  try {
    const { systemPreferences } = require('electron') as typeof import('electron')
    return systemPreferences.isTrustedAccessibilityClient(prompt)
  } catch {
    return false
  }
}

export async function sendKeys(keys: string): Promise<void> {
  if (process.platform === 'darwin') {
    const parts = keys.toLowerCase().split('+')
    const key = parts.pop() || ''
    const mods = parts.map((part) => (part === 'cmd' ? 'command' : part === 'ctrl' ? 'control' : part === 'opt' || part === 'alt' ? 'option' : part))
    const using = mods.length ? ` using {${mods.map((m) => `${m} down`).join(', ')}}` : ''
    await osa(`tell application "System Events" to keystroke "${key.replace(/"/g, '')}"${using}`)
    return
  }
  await new Promise<void>((resolve, reject) => {
    execFile(
      'powershell.exe',
      ['-NoProfile', '-Command', `(New-Object -ComObject WScript.Shell).SendKeys('${keys.replace(/'/g, "''")}')`],
      (err) => (err ? reject(err) : resolve())
    )
  })
}

export async function openApp(app: string): Promise<void> {
  if (process.platform === 'darwin') {
    await new Promise<void>((resolve, reject) => {
      execFile('open', ['-a', app], (err) => (err ? reject(err) : resolve()))
    })
    return
  }
  await new Promise<void>((resolve, reject) => {
    execFile('cmd', ['/c', 'start', '', app], (err) => (err ? reject(err) : resolve()))
  })
}

export async function openUrl(url: string): Promise<void> {
  const cmd = process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'cmd' : 'xdg-open'
  const args = process.platform === 'win32' ? ['/c', 'start', '', url] : [url]
  await new Promise<void>((resolve, reject) => {
    execFile(cmd, args, (err) => (err ? reject(err) : resolve()))
  })
}

export function runShell(command: string, cwd?: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const shell = process.platform === 'win32' ? 'cmd' : '/bin/zsh'
    const args = process.platform === 'win32' ? ['/c', command] : ['-lic', command]
    execFile(shell, args, { timeout: 10000, cwd }, (err) => (err ? reject(err) : resolve()))
  })
}

export async function launchInTerminal(command: string): Promise<void> {
  if (process.platform === 'darwin') {
    await osa(`tell application "Terminal" to do script "${command.replace(/"/g, '\\"')}"`)
    return
  }
  await new Promise<void>((resolve, reject) => {
    execFile('cmd', ['/c', 'start', '', 'cmd', '/k', command], (err) => (err ? reject(err) : resolve()))
  })
}
