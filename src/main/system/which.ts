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

export async function which(name: string): Promise<string | null> {
  if (cache.has(name)) return cache.get(name) || null
  let found = ''
  if (process.platform === 'win32') found = (await exec('cmd', ['/c', 'where', name])).split(/\r?\n/)[0] || ''
  else found = await exec('/bin/zsh', ['-lic', `command -v ${name}`])
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
