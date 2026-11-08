import { execFile } from 'child_process'

/**
 * Finds the terminal an agent runs in, from the process table, so a session can be focused even
 * when no hook has told Token Deck about it (a Claude Code session that started before the app, a
 * Codex or OpenCode session). macOS only: `ps` gives the tty and, with -E, the TERM_PROGRAM the
 * terminal set; `lsof` gives the working directory.
 */

export type AgentProcess = { pid: number; tty: string; command: string }
/** termProgram is the terminal's TERM_PROGRAM; bundleId is the app it runs in, from macOS's __CFBundleIdentifier. */
export type TerminalInfo = { pid: number; tty: string; termProgram?: string; bundleId?: string }

function run(cmd: string, args: string[]): Promise<string> {
  return new Promise((resolve) => {
    execFile(cmd, args, { timeout: 4000, encoding: 'utf8', maxBuffer: 8_000_000 }, (err, stdout) => resolve(err ? '' : String(stdout || '')))
  })
}

/** Subcommands that run a server, not a session someone types into (Token Deck runs `codex app-server` itself). */
const SERVER_COMMANDS = new Set(['app-server', 'mcp-server', 'serve', 'acp', 'mcp'])

/** `ps -axo pid=,tty=,command=` lines for the given program names that run on a terminal. */
export function parseProcessList(text: string, names: string[]): AgentProcess[] {
  const wanted = new Set(names)
  const rows: AgentProcess[] = []
  for (const line of text.split('\n')) {
    const match = line.trim().match(/^(\d+)\s+(\S+)\s+(.+)$/)
    if (!match) continue
    const [, pid, tty, command] = match
    if (!tty || tty === '??' || tty === '-') continue
    const argv = command!.split(/\s+/)
    const argv0 = argv[0]!.split('/').pop()!
    // node-installed CLIs run as `node /path/to/bin/codex …`
    const script = argv[1]?.split('/').pop() || ''
    const viaNode = argv0 === 'node' && wanted.has(script)
    if (!wanted.has(argv0) && !viaNode) continue
    if (SERVER_COMMANDS.has(argv[viaNode ? 2 : 1] || '')) continue
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

/**
 * The app a process was started from, from the same `ps -Eww` output: macOS sets __CFBundleIdentifier
 * for every app it launches and the shells inside inherit it, so this names WezTerm, Zed or the
 * terminal behind tmux when TERM_PROGRAM doesn't.
 */
export function parseBundleId(text: string): string | undefined {
  return text.match(/(?:^|\s)__CFBundleIdentifier=([\w.-]+)/)?.[1]
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
  return { pid, tty: tty.startsWith('/dev/') ? tty : `/dev/${tty}`, termProgram: parseTermProgram(env), bundleId: parseBundleId(env) }
}

/** The terminal of the newest process running one of `names` that `accept` takes. */
async function newestTerminal(names: string[], accept: (pid: number) => Promise<boolean>): Promise<TerminalInfo | null> {
  if (process.platform !== 'darwin') return null
  const candidates = parseProcessList(await run('ps', ['-axo', 'pid=,tty=,command=']), names).sort((a, b) => b.pid - a.pid)
  for (const candidate of candidates) {
    if (!(await accept(candidate.pid))) continue
    const info = await terminalOf(candidate.pid)
    if (info) return info
  }
  return null
}

/** The terminal running one of `names` in `cwd`; the newest such process when several match. */
export async function findAgentTerminal(names: string[], cwd?: string): Promise<TerminalInfo | null> {
  if (!cwd) return null
  return newestTerminal(names, async (pid) => samePath(parseLsofCwd(await run('lsof', ['-a', '-p', String(pid), '-d', 'cwd', '-Fn'])), cwd))
}

/** The terminal running one of `names` in any folder, the newest first. */
export function anyAgentTerminal(names: string[]): Promise<TerminalInfo | null> {
  return newestTerminal(names, async () => true)
}

/** Whether a process is still running. Signal 0 checks without touching it; EPERM means it runs as someone else. */
export function pidAlive(pid?: number): boolean {
  if (!pid || pid <= 0) return false
  try {
    process.kill(pid, 0)
    return true
  } catch (err) {
    return (err as NodeJS.ErrnoException).code === 'EPERM'
  }
}
