import http from 'http'
import type { SettingsStore } from '../settings/store'
import { homeDir } from '../log'
import fs from 'fs'
import path from 'path'

export type HookBody = {
  source: 'claude' | 'codex' | 'statusline'
  body: unknown
  headers: Record<string, string>
}

export class HookServer {
  private server: http.Server | null = null
  url = ''

  constructor(
    private readonly store: SettingsStore,
    private readonly onEvent: (event: HookBody) => void,
    private readonly log: (line: string) => void
  ) {}

  start(): Promise<void> {
    const token = this.store.get('token')
    this.server = http.createServer((req, res) => {
      const host = req.headers.host || ''
      if (!host.startsWith('127.0.0.1') && host !== 'localhost') {
        res.writeHead(404)
        res.end()
        return
      }
      const url = new URL(req.url || '/', 'http://127.0.0.1')
      const prefix = `/t/${token}`
      if (!url.pathname.startsWith(prefix + '/')) {
        res.writeHead(404)
        res.end()
        return
      }
      const route = url.pathname.slice(prefix.length)
      if (req.method !== 'POST' || (route !== '/hooks/claude' && route !== '/hooks/codex' && route !== '/statusline')) {
        res.writeHead(404)
        res.end()
        return
      }
      const chunks: Buffer[] = []
      req.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
      req.on('end', () => {
        let body: unknown = {}
        const raw = Buffer.concat(chunks).toString('utf8')
        try {
          body = raw ? JSON.parse(raw) : {}
        } catch {
          body = { raw }
        }
        const headers: Record<string, string> = {}
        for (const [key, value] of Object.entries(req.headers)) {
          if (typeof value === 'string') headers[key.toLowerCase()] = value
        }
        const source = route === '/statusline' ? 'statusline' : route.endsWith('codex') ? 'codex' : 'claude'
        try {
          this.onEvent({ source, body, headers })
        } catch (err) {
          this.log(`hook handler ${err}`)
        }
        res.writeHead(204)
        res.end()
      })
    })
    return new Promise((resolve) => {
      this.server!.listen(0, '127.0.0.1', () => {
        const address = this.server!.address()
        const port = typeof address === 'object' && address ? address.port : 0
        this.url = `http://127.0.0.1:${port}/t/${token}`
        const file = path.join(homeDir(), 'url')
        fs.mkdirSync(homeDir(), { recursive: true })
        fs.writeFileSync(file, this.url)
        this.log(`hooks ${this.url}`)
        resolve()
      })
    })
  }

  async stop(): Promise<void> {
    const file = path.join(homeDir(), 'url')
    fs.rmSync(file, { force: true })
    await new Promise<void>((resolve) => {
      if (!this.server) return resolve()
      this.server.close(() => resolve())
    })
  }
}
