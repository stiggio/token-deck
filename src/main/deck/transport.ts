import fs from 'fs'
import { devicesAsync, HIDAsync, type Device } from 'node-hid'
import { spawnSync } from 'child_process'
import { resource } from '../paths'
import { FrameQueue } from './queue'
import {
  USAGE,
  USAGE_PAGE,
  VENDOR_IDS,
  VENDOR_PROCESSES,
  brightness,
  clearKey,
  createDecoder,
  heartbeat,
  parseFirmware,
  refresh,
  type DeckEvent,
  type KnobMap
} from './protocol'
import { executeBurn } from '../burn/sequence'
import { DEFAULT_KNOB_MAP, handshake } from './protocol'

export type Phase = 'idle' | 'opening' | 'handshaking' | 'ready' | 'burning' | 'closing' | 'vendor' | 'unresponsive'

export type DeckInfo = {
  manufacturer: string
  product: string
  serial: string
  release: number
  firmware: string
  path: string
}

export type TransportSnapshot = {
  phase: Phase
  message: string
  info: DeckInfo | null
  burnFailed: boolean
}

type Handle = HIDAsync

const MESSAGES = {
  connected: 'Deck connected',
  missing: 'No deck found. Plug it in, or unplug it and plug it back in.',
  vendor: 'Quit the StreamDock or VSD Craft app to use Token Deck.',
  dead: 'Deck not responding. Unplug it and plug it back in.',
  burning: 'Writing the welcome screen. Keep the deck plugged in.',
  burnFailed: 'The welcome screen was not written. Unplug the deck and plug it back in.'
}

export function vendorRunning(): boolean {
  if (process.platform === 'darwin') {
    return VENDOR_PROCESSES.darwin.some((name) => spawnSync('pgrep', ['-x', name], { encoding: 'utf8' }).status === 0)
  }
  if (process.platform === 'win32') {
    return VENDOR_PROCESSES.win32.some((name) => {
      const out = spawnSync('tasklist', ['/FI', `IMAGENAME eq ${name}`, '/FO', 'CSV', '/NH'], { encoding: 'utf8' }).stdout || ''
      return out.toLowerCase().includes(name.toLowerCase())
    })
  }
  return false
}

export function matchDevice(device: Device): boolean {
  const id = VENDOR_IDS.some((row) => row.vendorId === device.vendorId && row.productId === device.productId)
  return id && device.usagePage === USAGE_PAGE && device.usage === USAGE && !!device.path
}

function exclusiveError(err: unknown): boolean {
  const text = String((err as Error)?.message || err)
  return text.includes('0xE00002C5') || text.toLowerCase().includes('exclusive')
}

export class DeckTransport {
  phase: Phase = 'idle'
  message = MESSAGES.missing
  info: DeckInfo | null = null
  burnFailed = false
  firmware = 'n/a'
  nonExclusive = false

  private handle: Handle | null = null
  private queue = new FrameQueue((packet) => this.rawWrite(packet))
  private decoder = createDecoder(DEFAULT_KNOB_MAP)
  private poll: NodeJS.Timeout | null = null
  private heart: NodeJS.Timeout | null = null
  private keep: NodeJS.Timeout | null = null
  private tiles = new Map<number, Buffer>()
  private logWaiter: (() => void) | null = null
  private opening = false
  private failStreak = 0
  private sawAbsence = true
  private appearedAt = 0
  private seenSerial = ''
  private burnedThisAppearance = false
  private reconnecting = false
  private closed = false
  private burnInFlight: Promise<void> | null = null
  brightness = 70
  keepalive = true
  onInput: (event: DeckEvent) => void = () => {}
  onState: () => void = () => {}
  log: (line: string) => void = () => {}
  shouldBurn: (serial: string) => boolean = () => false
  onBurned: (serial: string) => void = () => {}
  onBurnFailed: (serial: string) => void = () => {}
  currentTiles: () => Buffer[] = () => []

  snapshot(): TransportSnapshot {
    return { phase: this.phase, message: this.message, info: this.info, burnFailed: this.burnFailed }
  }

  setKnobMap(map: KnobMap): void {
    this.decoder = createDecoder(map)
  }

  start(): void {
    this.closed = false
    this.heart = setInterval(() => {
      if (!this.handle || this.burnFailed) {
        if (this.handle && this.burnFailed && this.phase !== 'burning') void this.queue.heartbeat()
        return
      }
      if (process.platform === 'win32' && vendorRunning()) {
        this.log('vendor app appeared')
        this.message = MESSAGES.vendor
        this.phase = 'vendor'
        void this.dropHandle()
        this.emit()
        return
      }
      void this.queue.heartbeat().catch((err) => this.onWriteError(err))
    }, 10000)
    this.keep = setInterval(() => {
      if (!this.keepalive || !this.handle || this.burnFailed || this.phase !== 'ready') return
      const jpeg = this.tiles.get(1)
      if (!jpeg) return
      void this.queue.keepalive(jpeg).catch((err) => this.onWriteError(err))
    }, 1000)
    this.poll = setInterval(() => void this.pollOnce(), 2000)
    void this.pollOnce()
  }

  async pollOnce(): Promise<void> {
    if (this.closed || this.handle || this.opening || this.phase === 'burning' || this.phase === 'closing') return
    let list: Device[] = []
    try {
      list = await devicesAsync()
    } catch (err) {
      this.log(`enumerate failed ${err}`)
      return
    }
    const found = list.filter(matchDevice)
    const device = found[0]
    if (!device) {
      this.sawAbsence = true
      this.seenSerial = ''
      this.burnedThisAppearance = false
      this.burnFailed = false
      if (this.phase !== 'vendor') {
        this.phase = 'idle'
        this.message = MESSAGES.missing
        this.info = null
        this.emit()
      }
      return
    }
    if (this.phase === 'unresponsive' && !this.sawAbsence) return
    if (this.phase === 'vendor' && vendorRunning()) return
    const serial = device.serialNumber || ''
    if (serial !== this.seenSerial) {
      this.seenSerial = serial
      this.appearedAt = Date.now()
      this.burnedThisAppearance = false
      this.sawAbsence = false
    }
    if (vendorRunning()) {
      this.phase = 'vendor'
      this.message = MESSAGES.vendor
      this.emit()
      return
    }
    const burn = this.shouldBurn(serial) && !this.burnedThisAppearance
    if (burn) {
      const wait = 8000 - (Date.now() - this.appearedAt)
      if (wait > 0) return
    }
    await this.openDevice(device, { burn })
  }

  private async openDevice(device: Device, opts: { burn: boolean }): Promise<void> {
    if (!device.path || this.opening || this.handle) return
    this.opening = true
    this.phase = 'opening'
    this.emit()
    try {
      const handle = this.nonExclusive ? await HIDAsync.open(device.path, { nonExclusive: true }) : await HIDAsync.open(device.path)
      this.handle = handle
      this.failStreak = 0
      this.queue.clearLastSent()
      handle.on('error', (err) => {
        this.log(`hid error ${err}`)
        this.onWriteError(err)
      })
      handle.on('data', (data: Buffer) => this.onData(data))
      this.info = {
        manufacturer: device.manufacturer || '',
        product: device.product || '',
        serial: device.serialNumber || '',
        release: device.release,
        firmware: 'n/a',
        path: device.path
      }
      this.phase = 'handshaking'
      this.emit()
      await this.readFirmware(handle)
      if (this.info) this.info.firmware = this.firmware
      if (opts.burn) {
        this.burnedThisAppearance = true
        await this.runBurn(this.currentTiles())
      } else {
        await this.handshake()
        this.burnFailed = false
        this.phase = 'ready'
        this.message = MESSAGES.connected
        this.emit()
        await this.replay()
      }
    } catch (err) {
      this.log(`open failed ${err}`)
      if (exclusiveError(err) && !this.handle) {
        this.phase = 'vendor'
        this.message = MESSAGES.vendor
      } else {
        this.failStreak++
        if (this.failStreak >= 3) {
          this.phase = 'unresponsive'
          this.message = MESSAGES.dead
          this.sawAbsence = false
        }
      }
      await this.dropHandle()
      this.emit()
    } finally {
      this.opening = false
    }
  }

  private async readFirmware(handle: Handle): Promise<void> {
    if (process.platform !== 'darwin') {
      this.firmware = 'n/a'
      return
    }
    let found: string | null = null
    for (const [id, len] of [
      [1, 20],
      [0, 513]
    ] as const) {
      try {
        const report = Buffer.from(await handle.getFeatureReport(id, len))
        found = parseFirmware(report) || found
        if (found) break
      } catch (err) {
        this.log(`firmware report ${id} ${err}`)
      }
    }
    this.firmware = found || 'n/a'
  }

  private async handshake(): Promise<void> {
    for (const frame of handshake(this.brightness)) await this.queue.command(frame)
  }

  private onData(data: Buffer): void {
    try {
      const buf = Buffer.isBuffer(data) ? data : Buffer.from(data)
      for (const event of this.decoder.push(buf)) {
        if (event.type === 'log-report') {
          this.logWaiter?.()
          this.logWaiter = null
          continue
        }
        if (this.phase === 'burning') continue
        this.onInput(event)
      }
    } catch (err) {
      this.log(`data handler ${err}`)
    }
  }

  private async rawWrite(packet: Buffer): Promise<void> {
    const handle = this.handle
    if (!handle) throw new Error('no device')
    let timer: NodeJS.Timeout | undefined
    try {
      await Promise.race([
        handle.write(packet),
        new Promise<never>((_, reject) => {
          timer = setTimeout(() => reject(new Error('write-timeout')), 5000)
        })
      ])
    } catch (err) {
      if (String(err).includes('write-timeout')) this.abandon()
      throw err
    } finally {
      if (timer) clearTimeout(timer)
    }
  }

  private onWriteError(err: unknown): void {
    this.log(`write error ${err}`)
    if (this.phase === 'burning') return
    void this.reconnect()
  }

  private abandon(): void {
    const handle = this.handle
    this.handle = null
    this.log('abandoned wedged handle')
    if (handle) {
      void handle.close().catch(() => undefined)
    }
  }

  private async dropHandle(): Promise<void> {
    const handle = this.handle
    this.handle = null
    if (!handle) return
    this.phase = 'closing'
    try {
      await handle.close()
    } catch (err) {
      this.log(`close ${err}`)
    }
  }

  async reconnect(): Promise<void> {
    if (this.reconnecting || this.phase === 'burning' || this.closed) return
    this.reconnecting = true
    try {
      await this.dropHandle()
      await sleep(1000)
      this.queue.clearLastSent()
      this.phase = 'idle'
      this.emit()
    } finally {
      this.reconnecting = false
    }
  }

  async paint(frames: Array<Buffer | null>, force = false): Promise<void> {
    frames.forEach((jpeg, index) => {
      if (jpeg) this.tiles.set(index + 1, jpeg)
    })
    if (!this.handle || this.burnFailed || this.phase === 'burning') return
    const map = new Map<number, Buffer>()
    frames.forEach((jpeg, index) => {
      if (jpeg) map.set(index + 1, jpeg)
    })
    const started = Date.now()
    await this.queue.paint(map, force)
    const bytes = [...map.values()].reduce((sum, buf) => sum + buf.length, 0)
    this.log(`paint ${bytes}B ${Date.now() - started}ms keys ${[...map.keys()].join(',')}`)
  }

  async replay(): Promise<void> {
    if (this.burnFailed || !this.handle) return
    this.queue.clearLastSent()
    const frames = [1, 2, 3, 4, 5, 6].map((key) => this.tiles.get(key) || null)
    if (frames.some(Boolean)) await this.paint(frames, true)
  }

  async setBrightness(percent: number): Promise<void> {
    this.brightness = percent
    if (!this.handle || this.phase === 'burning') return
    await this.queue.command(brightness(percent))
  }

  async clearKeys(key: number): Promise<void> {
    if (!this.handle || this.phase !== 'ready') return
    await this.queue.command(clearKey(key))
    await this.queue.command(refresh())
  }

  async runBurn(repaint: Buffer[]): Promise<'ok' | 'failed'> {
    if (!this.handle) return 'failed'
    if (process.platform === 'win32' && vendorRunning()) {
      this.phase = 'vendor'
      this.message = MESSAGES.vendor
      this.emit()
      return 'failed'
    }
    const run = (async () => {
      this.phase = 'burning'
      this.message = MESSAGES.burning
      this.burnFailed = false
      this.emit()
      this.queue.clearLastSent()
      const tiles = [1, 2, 3, 4, 5, 6].map((key) => fs.readFileSync(resource('welcome-tiles', `key${key}.jpg`)))
      const welcome = fs.readFileSync(resource('welcome-sent.jpg'))
      let result: 'ok' | 'failed' = 'failed'
      try {
        result = await this.queue.submit(() =>
          executeBurn(
            {
              write: (packet) => this.rawWrite(packet),
              sleep,
              waitForLogReport: (ms) => this.waitForLogReport(ms)
            },
            {
              brightness: this.brightness,
              tiles,
              welcome,
              repaint: repaint.length === 6 ? repaint : tiles,
              holdMs: 10000
            }
          )
        )
      } catch (err) {
        this.log(`burn write error ${err}`)
        result = 'failed'
        this.abandon()
      }
      const serial = this.info?.serial || ''
      if (result === 'ok') {
        this.burnFailed = false
        this.phase = 'ready'
        this.message = MESSAGES.connected
        this.queue.clearLastSent()
        repaint.forEach((jpeg, index) => this.tiles.set(index + 1, jpeg))
        this.log(`burn ok ${serial}`)
        if (serial) this.onBurned(serial)
      } else {
        this.burnFailed = true
        this.phase = this.handle ? 'ready' : 'idle'
        this.message = MESSAGES.burnFailed
        if (serial) this.onBurnFailed(serial)
        this.log(`burn failed ${serial}`)
      }
      this.emit()
      return result
    })()
    this.burnInFlight = run.then(() => undefined)
    return run
  }

  /** Burn-page and calibration rewrite: close, wait, reopen, then the burn. */
  async rewrite(): Promise<'ok' | 'failed'> {
    if (this.phase === 'burning') return 'failed'
    const serial = this.info?.serial || this.seenSerial
    await this.dropHandle()
    await sleep(1000)
    const list = await devicesAsync()
    const device = list.filter(matchDevice).find((row) => (row.serialNumber || '') === serial) || list.find(matchDevice)
    if (!device) return 'failed'
    this.opening = false
    await this.openDevice(device, { burn: true })
    return this.burnFailed ? 'failed' : 'ok'
  }

  private waitForLogReport(timeoutMs: number): Promise<boolean> {
    return new Promise((resolve) => {
      const timer = setTimeout(() => {
        this.logWaiter = null
        resolve(false)
      }, timeoutMs)
      this.logWaiter = () => {
        clearTimeout(timer)
        resolve(true)
      }
    })
  }

  async prepareQuit(opts: { paint: Buffer[] | null; capMs: number }): Promise<void> {
    this.closed = true
    if (this.poll) clearInterval(this.poll)
    if (this.keep) clearInterval(this.keep)
    if (this.burnInFlight) {
      await Promise.race([this.burnInFlight, sleep(opts.capMs)])
    }
    if (!this.burnFailed && opts.paint && this.handle && this.phase !== 'burning') {
      await Promise.race([this.paint(opts.paint, true), sleep(opts.capMs)])
    }
    if (this.heart) clearInterval(this.heart)
    await Promise.race([this.dropHandle(), sleep(Math.min(1000, opts.capMs))])
  }

  private emit(): void {
    this.onState()
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export { heartbeat }
