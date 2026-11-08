import { execFile } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'

const cache = new Map<string, string | null>()

function exec(cmd: string, args: string[]): Promise<string> {
  return new Promise((resolve) => {
    execFile(cmd, args, { timeout: 8000, encoding: 'utf8' }, (err, stdout) => {
      if (err) return resolve('')
      resolve(String(stdout || '').trim())
    })
  })
}

/** `zsh -lic` prints startup noise, and `command -v` prints `alias name=/path` for an alias. */
export function executableFromWhich(text: string): string {
  for (const raw of text.split('\n')) {
    const line = raw.replace(/\u001b\[[0-9;]*m/g, '').trim()
    if (!line) continue
    const alias = /^alias\s+[^=]+=\s*(.+)$/.exec(line)
    if (alias) return alias[1].trim().replace(/^['"]|['"]$/g, '').replace(/^~/, os.homedir())
    if (line.startsWith('/')) return line.split(/\s/)[0] || ''
  }
  return ''
}

function knownBins(name: string): string[] {
  const home = os.homedir()
  if (name === 'claude') return [path.join(home, '.claude/local/claude'), path.join(home, '.local/bin/claude')]
  if (name === 'codex') return [path.join(home, '.local/bin/codex'), '/opt/homebrew/bin/codex', '/usr/local/bin/codex']
  if (name === 'opencode') return [path.join(home, '.local/bin/opencode'), '/opt/homebrew/bin/opencode']
  return []
}

export async function which(name: string): Promise<string | null> {
  if (cache.has(name)) return cache.get(name) || null
  const direct = knownBins(name).find((file) => fs.existsSync(file))
  if (direct) {
    cache.set(name, direct)
    return direct
  }
  let found = ''
  if (process.platform === 'win32') found = (await exec('cmd', ['/c', 'where', name])).split(/\r?\n/)[0] || ''
  else found = executableFromWhich(await exec('/bin/zsh', ['-lic', `command -v ${name}`]))
  if (!found && name === 'claude') {
    const root = path.join(os.homedir(), 'Library/Application Support/Claude/claude-code')
    if (fs.existsSync(root)) {
      const versions = fs.readdirSync(root).sort()
      for (const version of versions.reverse()) {
        const hit = findFile(path.join(root, version), 'claude')
        if (hit) {
          found = hit
          break
        }
      }
    }
  }
  const value = found && fs.existsSync(found) ? found : null
  cache.set(name, value)
  return value
}

function findFile(dir: string, name: string, depth = 0): string | null {
  if (depth > 4 || !fs.existsSync(dir)) return null
  for (const entry of fs.readdirSync(dir)) {
    const full = path.join(dir, entry)
    let stat: fs.Stats
    try {
      stat = fs.statSync(full)
    } catch {
      continue
    }
    if (stat.isDirectory()) {
      const nested = findFile(full, name, depth + 1)
      if (nested) return nested
    } else if (entry === name && (stat.mode & 0o111)) return full
  }
  return null
}

export function commandVersion(bin: string): Promise<string> {
  return exec(bin, ['--version'])
}

/**
 * A variable from the user's login shell. A GUI app started from Finder or at login doesn't get
 * what ~/.zshrc exports, so read it the way a terminal would. Sentinels skip startup noise.
 */
export async function loginShellVar(name: string): Promise<string> {
  if (process.env[name]) return process.env[name]!
  if (process.platform === 'win32' || !/^[A-Z_][A-Z0-9_]*$/.test(name)) return ''
  const out = await exec('/bin/zsh', ['-lic', `printf '__TD__%s__TD__' "$${name}"`])
  return out.match(/__TD__([\s\S]*?)__TD__/)?.[1] || ''
}
