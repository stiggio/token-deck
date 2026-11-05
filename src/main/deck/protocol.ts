/** HID frames for the Stream Dock N3. There is no encoder for the vendor sleep
 * frame or the vendor disconnect frame. */

export const VENDOR_IDS: ReadonlyArray<{ vendorId: number; productId: number }> = [
  { vendorId: 0x5548, productId: 0x1001 },
  { vendorId: 0x6603, productId: 0x1002 },
  { vendorId: 0x6603, productId: 0x1003 }
]

export const USAGE_PAGE = 0xffa0
export const USAGE = 1
export const PAYLOAD = 1024
export const REPORT = 1025

export const VENDOR_PROCESSES = {
  darwin: ['StreamDock', 'VSD Craft'],
  win32: ['StreamDock.exe', 'VSD Craft.exe']
} as const

const PREFIX = Buffer.from([0x43, 0x52, 0x54, 0x00, 0x00])

export function command(tag: string, tail: Buffer = Buffer.alloc(0)): Buffer {
  const payload = Buffer.alloc(PAYLOAD)
  PREFIX.copy(payload, 0)
  const t = Buffer.from(tag, 'ascii')
  t.copy(payload, 5)
  if (tail.length) tail.copy(payload, 5 + t.length)
  return payload
}

export function withReportId(payload: Buffer): Buffer {
  const pkt = Buffer.alloc(REPORT)
  payload.copy(pkt, 1, 0, PAYLOAD)
  return pkt
}

export function wake(): Buffer {
  return command('DIS')
}

export function refresh(): Buffer {
  return command('STP')
}

export function brightness(percent: number): Buffer {
  const p = Math.max(0, Math.min(100, percent | 0))
  return command('LIG', Buffer.from([0x00, 0x00, p]))
}

/** Clear one key (1–6) or all keys (0xFF). Key byte sits at payload index 11. */
export function clearKey(key: number): Buffer {
  return command('CLE', Buffer.from([0x00, 0x00, 0x00, key & 0xff]))
}

export function heartbeat(): Buffer {
  return command('CONNECT')
}

export function qucmd(): Buffer {
  return command('QUCMD', Buffer.from([0x1f, 0x11, 0x00, 0x11, 0x00, 0x11, 0x00]))
}

export function batHeader(jpegLength: number, key: number): Buffer {
  const tail = Buffer.alloc(5)
  tail.writeUInt32BE(jpegLength >>> 0, 0)
  tail[4] = key & 0xff
  return command('BAT', tail)
}

export function logHeader(jpegLength: number): Buffer {
  const tail = Buffer.alloc(5)
  tail.writeUInt32BE(jpegLength >>> 0, 0)
  tail[4] = 0x01
  return command('LOG', tail)
}

export function jpegChunk(jpeg: Buffer, offset: number): Buffer {
  const payload = Buffer.alloc(PAYLOAD)
  jpeg.copy(payload, 0, offset, Math.min(jpeg.length, offset + PAYLOAD))
  return payload
}

export function handshake(percent: number): Buffer[] {
  return [wake(), brightness(percent), qucmd(), brightness(percent)]
}

/** Every command frame this module can build, for the forbidden-frame test. */
export function sampleFrames(): Buffer[] {
  const frames = [
    wake(),
    refresh(),
    heartbeat(),
    qucmd(),
    ...handshake(70),
    ...handshake(0),
    ...handshake(100)
  ]
  for (let p = 0; p <= 100; p += 10) frames.push(brightness(p))
  for (const key of [1, 2, 3, 4, 5, 6, 0xff]) frames.push(clearKey(key))
  for (const key of [1, 2, 3, 4, 5, 6]) {
    frames.push(batHeader(1000, key))
    frames.push(batHeader(6681, key))
  }
  frames.push(logHeader(18887))
  frames.push(logHeader(22307))
  frames.push(jpegChunk(Buffer.from([0xff, 0xd8, 0xff, 0xd9]), 0))
  return frames
}

export type KnobId = 'main' | 'left' | 'right'

export type KnobMap = Record<KnobId, { cw: number; ccw: number; click: number }>

export const DEFAULT_KNOB_MAP: KnobMap = {
  main: { cw: 0x51, ccw: 0x50, click: 0x35 },
  left: { cw: 0x91, ccw: 0x90, click: 0x33 },
  right: { cw: 0x61, ccw: 0x60, click: 0x34 }
}

export type DeckEvent =
  | { type: 'key'; key: 1 | 2 | 3 | 4 | 5 | 6 }
  | { type: 'metal'; which: 'left' | 'middle' | 'right'; pressed: boolean }
  | { type: 'knob'; which: KnobId; action: 'cw' | 'ccw' | 'click' }
  | { type: 'log-report' }

const KEYS = new Set([0x01, 0x02, 0x03, 0x04, 0x05, 0x06])

export function knownCodes(map: KnobMap = DEFAULT_KNOB_MAP): Set<number> {
  const s = new Set<number>([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x25, 0x30, 0x31])
  for (const knob of Object.values(map)) {
    s.add(knob.cw)
    s.add(knob.ccw)
    s.add(knob.click)
  }
  return s
}

export type RawInput = { code: number; pressed: boolean } | { kind: 'log' } | { kind: 'drop' }

/** Match ACK at bytes 0–2 and OK at 5–6. Code 0x00 is the LOG write report. */
export function decodeRaw(buf: Buffer): RawInput {
  if (buf.length < 11) return { kind: 'drop' }
  if (buf[0] !== 0x41 || buf[1] !== 0x43 || buf[2] !== 0x4b) return { kind: 'drop' }
  if (buf[5] !== 0x4f || buf[6] !== 0x4b) return { kind: 'drop' }
  const code = buf[9]!
  const state = buf[10]!
  if (code === 0x00) return { kind: 'log' }
  if (code === 0xff) return { kind: 'drop' }
  return { code, pressed: state === 1 }
}

export function createDecoder(map: KnobMap = DEFAULT_KNOB_MAP): {
  push(buf: Buffer): DeckEvent[]
  map: KnobMap
} {
  const known = knownCodes(map)
  const clickOf = new Map<number, KnobId>()
  const rotOf = new Map<number, { which: KnobId; action: 'cw' | 'ccw' }>()
  for (const which of ['main', 'left', 'right'] as const) {
    clickOf.set(map[which].click, which)
    rotOf.set(map[which].cw, { which, action: 'cw' })
    rotOf.set(map[which].ccw, { which, action: 'ccw' })
  }
  return {
    map,
    push(buf: Buffer): DeckEvent[] {
      const raw = decodeRaw(buf)
      if ('kind' in raw && raw.kind === 'log') return [{ type: 'log-report' }]
      if ('kind' in raw) return []
      if (!known.has(raw.code)) return []
      if (KEYS.has(raw.code)) {
        if (!raw.pressed) return []
        return [{ type: 'key', key: raw.code as 1 | 2 | 3 | 4 | 5 | 6 }]
      }
      if (raw.code === 0x25) {
        if (!raw.pressed) return []
        return [{ type: 'metal', which: 'left', pressed: true }]
      }
      if (raw.code === 0x31) {
        if (!raw.pressed) return []
        return [{ type: 'metal', which: 'right', pressed: true }]
      }
      if (raw.code === 0x30) {
        return [{ type: 'metal', which: 'middle', pressed: raw.pressed }]
      }
      const click = clickOf.get(raw.code)
      if (click) {
        if (!raw.pressed) return []
        return [{ type: 'knob', which: click, action: 'click' }]
      }
      const rot = rotOf.get(raw.code)
      if (rot) return [{ type: 'knob', which: rot.which, action: rot.action }]
      return []
    }
  }
}

export function parseFirmware(report: Buffer): string | null {
  let bytes = Buffer.from(report)
  let start = 0
  let end = bytes.length
  while (start < end && bytes[start] === 0) start++
  while (end > start && bytes[end - 1] === 0) end--
  bytes = bytes.subarray(start, end)
  const cut = bytes.indexOf(0)
  if (cut >= 0) bytes = bytes.subarray(0, cut)
  const text = bytes.toString('ascii')
  if (!text.startsWith('V3.')) return null
  if (![...text].every((c) => c.charCodeAt(0) >= 32 && c.charCodeAt(0) < 127)) return null
  return text
}

export function chunkCount(byteLength: number): number {
  return Math.ceil(byteLength / PAYLOAD)
}
