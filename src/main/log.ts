import fs from 'fs'
import os from 'os'
import path from 'path'

export function homeDir(): string {
  return path.join(os.homedir(), '.tokendeck')
}

export class Log {
  readonly file: string
  private stream: fs.WriteStream

  constructor() {
    const dir = path.join(homeDir(), 'log')
    fs.mkdirSync(dir, { recursive: true })
    this.file = path.join(dir, 'tokendeck.log')
    this.stream = this.open()
  }

  private open(): fs.WriteStream {
    try {
      if (fs.existsSync(this.file) && fs.statSync(this.file).size > 5 * 1024 * 1024) {
        fs.renameSync(this.file, `${this.file}.1`)
      }
    } catch {
      /* a rotation failure still leaves the current file usable */
    }
    return fs.createWriteStream(this.file, { flags: 'a' })
  }

  write(line: string): void {
    try {
      if (fs.existsSync(this.file) && fs.statSync(this.file).size > 5 * 1024 * 1024) {
        this.stream.end()
        this.stream = this.open()
      }
    } catch {
      /* keep the current stream */
    }
    const text = `${new Date().toISOString()} ${line}\n`
    fs.appendFileSync(this.file, text)
  }

  tail(max = 8000): string {
    try {
      const text = fs.readFileSync(this.file, 'utf8')
      return text.slice(-max)
    } catch {
      return ''
    }
  }
}
