import fs from 'fs'
import path from 'path'

/**
 * Replaces a user's config file in one step: write a temp file beside it, then rename it over the
 * original, so a crash or a reader never sees half a file. A symlinked file (dotfiles) keeps its
 * link: the write goes to the real file the link points at.
 */
export function writeFileAtomic(file: string, data: string): void {
  let target = file
  try {
    target = fs.realpathSync(file)
  } catch {
    /* doesn't exist yet */
  }
  fs.mkdirSync(path.dirname(target), { recursive: true })
  const temp = path.join(path.dirname(target), `.${path.basename(target)}.tokendeck-${process.pid}-${Date.now()}`)
  fs.writeFileSync(temp, data)
  try {
    fs.renameSync(temp, target)
  } catch {
    // Windows can refuse to rename over a file another program holds open; write in place instead.
    try {
      fs.writeFileSync(target, data)
    } finally {
      fs.rmSync(temp, { force: true })
    }
  }
}

/** A file's text, or null when it doesn't exist. Any other read error is thrown, never taken for "empty". */
export function readIfExists(file: string): string | null {
  try {
    return fs.readFileSync(file, 'utf8')
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') return null
    throw err
  }
}
