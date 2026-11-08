import { execFile } from 'child_process'

/**
 * Finds the terminal an agent runs in, from the process table, so a session can be focused even
 * when no hook has told Token Deck about it (a Claude Code session that started before the app, a
 * Codex or OpenCode session). macOS only: `ps` gives the tty and, with -E, the TERM_PROGRAM the
 * terminal set; `lsof` gives the working directory.
 */

export type AgentProcess = { pid: number; tty: string; command: string }
export type TerminalInfo = { pid: number; tty: string; termProgram?: string }

function run(cmd: string, args: string[]): Promise<string> {
  return new Promise((resolve) => {
    execFile(cmd, args, { timeout: 4000, encoding: 'utf8', maxBuffer: 8_000_000 }, (err, stdout) => resolve(err ? '' : String(stdout || '')))
  })
}

/** `ps -axo pid=,tty=,command=` lines for the given program names that run on a terminal. */
export function parseProcessList(text: string, names: string[]): AgentProcess[] {
  const wanted = new Set(names)
  const rows: AgentProcess[] = []
  for (const line of text.split('\n')) {
    const match = line.trim().match(/^(\d+)\s+(\S+)\s+(.+)$/)
    if (!match) continue
    const [, pid, tty, command] = match
    if (!tty || tty === '??' || tty === '-') continue
    const argv0 = command!.split(/\s+/)[0]!.split('/').pop()!
    // node-installed CLIs run as `node /path/to/bin/codex …`
    const script = command!.split(/\s+/)[1]?.split('/').pop() || ''
    if (!wanted.has(argv0) && !(argv0 === 'node' && wanted.has(script))) continue
    rows.push({ pid: Number(pid), tty: tty.startsWith('/dev/') ? tty : `/dev/${tty}`, command: command! })
  }
  return rows
}

/** The working directory from `lsof -a -p PID -d cwd -Fn`. */
export function parseLsofCwd(text: string): string | undefined {
  const line = text.split('\n').find((row) => row.startsWith('n'))
  return line ? line.slice(1).trim() || undefined : undefined
}

/** TERM_PROGRAM from `ps -Eww -o command= -p PID`, which appends the environment on macOS. */
export function parseTermProgram(text: string): string | undefined {
  return text.match(/(?:^|\s)TERM_PROGRAM=(\S+)/)?.[1]
}

function samePath(a?: string, b?: string): boolean {
  if (!a || !b) return false
  return a.replace(/\/+$/, '') === b.replace(/\/+$/, '')
}

/** The terminal a process runs in, by pid. */
export async function terminalOf(pid: number): Promise<TerminalInfo | null> {
  if (process.platform !== 'darwin' || !pid) return null
  const tty = (await run('ps', ['-o', 'tty=', '-p', String(pid)])).trim()
  if (!tty || tty === '??') return null
  const env = await run('ps', ['-Eww', '-o', 'command=', '-p', String(pid)])
  return { pid, tty: tty.startsWith('/dev/') ? tty : `/dev/${tty}`, termProgram: parseTermProgram(env) }
}

/** The terminal running one of `names` in `cwd`; the newest such process when several match. */
export async function findAgentTerminal(names: string[], cwd?: string): Promise<TerminalInfo | null> {
  if (process.platform !== 'darwin' || !cwd) return null
  const candidates = parseProcessList(await run('ps', ['-axo', 'pid=,tty=,command=']), names).sort((a, b) => b.pid - a.pid)
  for (const candidate of candidates) {
    const dir = parseLsofCwd(await run('lsof', ['-a', '-p', String(candidate.pid), '-d', 'cwd', '-Fn']))
    if (!samePath(dir, cwd)) continue
    return terminalOf(candidate.pid)
  }
  return null
}
