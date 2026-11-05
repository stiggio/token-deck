import fs from 'fs'
import path from 'path'
import { describe, expect, it } from 'vitest'
import { FrameQueue } from '../src/main/deck/queue'
import { heartbeat, refresh } from '../src/main/deck/protocol'
import { executeBurn } from '../src/main/burn/sequence'
import { jpegInfo } from '../src/main/deck/jpeg'
import { WELCOME_BYTES } from '../src/main/deck/geometry'

const root = path.resolve(__dirname, '..')

function payload(packet: Buffer): Buffer {
  return packet.subarray(1, 1025)
}

function tag(packet: Buffer): string {
  return payload(packet).subarray(0, 16).toString('latin1').replace(/\0/g, '·')
}

describe('write queue', () => {
  it('does not let a heartbeat inside a tile group', async () => {
    const writes: Buffer[] = []
    let release: () => void = () => {}
    const gate = new Promise<void>((r) => {
      release = r
    })
    let blocked = false
    const queue = new FrameQueue(async (packet) => {
      writes.push(packet)
      if (!blocked) {
        blocked = true
        await gate
      }
    })
    const jpeg = Buffer.from([0xff, 0xd8, 0xff, 0xd9])
    const paint = queue.paint(new Map([[1, jpeg]]))
    await new Promise((r) => setTimeout(r, 10))
    const beat = queue.heartbeat()
    release()
    await paint
    await beat
    const bodies = writes.map(tag)
    const stp = bodies.findIndex((b) => b.startsWith('CRT··STP'))
    const connect = bodies.findIndex((b) => b.startsWith('CRT··CONNECT'))
    expect(stp).toBeGreaterThan(0)
    expect(connect).toBe(stp + 1)
  })

  it('writes nothing between the last LOG chunk and the write report', async () => {
    const writes: string[] = []
    let report: (ok: boolean) => void = () => {}
    const waiting = new Promise<boolean>((r) => {
      report = r
    })
    const queue = new FrameQueue(async (packet) => {
      writes.push(tag(packet))
    })
    const welcome = fs.readFileSync(path.join(root, 'resources/welcome-sent.jpg'))
    const tile = Buffer.from([0xff, 0xd8, 0xff, 0xd9])
    const burn = queue.submit(() =>
      executeBurn(
        {
          write: async (packet) => {
            writes.push(tag(packet))
          },
          sleep: async () => undefined,
          waitForLogReport: () => waiting
        },
        { brightness: 70, tiles: [tile, tile, tile, tile, tile, tile], welcome, holdMs: 10000 }
      )
    )
    await new Promise((r) => setTimeout(r, 20))
    const before = writes.length
    const beat = queue.heartbeat()
    await new Promise((r) => setTimeout(r, 20))
    expect(writes.length).toBe(before)
    expect(writes[writes.length - 1]!.startsWith('CRT··')).toBe(false)
    report(true)
    await burn
    await beat
    const logAt = writes.findIndex((w) => w.startsWith('CRT··LOG'))
    expect(logAt).toBeGreaterThan(0)
    const stpAfter = writes.findIndex((w, i) => i > logAt && w.startsWith('CRT··STP'))
    expect(stpAfter).toBeGreaterThan(logAt)
    expect(writes.slice(logAt + 1, stpAfter).some((w) => w.startsWith('CRT··CONNECT'))).toBe(false)
    expect(writes[writes.length - 1]).toBe(tag(Buffer.concat([Buffer.from([0]), heartbeat().subarray(0, 1024)])))
  })

  it('replaces a queued tile that has not started', async () => {
    const seen: number[] = []
    let release: () => void = () => {}
    const gate = new Promise<void>((r) => {
      release = r
    })
    let held = false
    const queue = new FrameQueue(async (packet) => {
      const body = payload(packet)
      if (body[0] === 0xff) seen.push(body[3]!)
      if (!held) {
        held = true
        await gate
      }
    })
    const blocker = queue.heartbeat()
    await new Promise((r) => setTimeout(r, 10))
    const a = Buffer.from([0xff, 0xd8, 0x00, 1, 0xff, 0xd9])
    const b = Buffer.from([0xff, 0xd8, 0x00, 2, 0xff, 0xd9])
    const first = queue.paint(new Map([[2, a]]))
    const second = queue.paint(new Map([[2, b]]))
    release()
    await blocker
    await first
    await second
    expect(seen).toContain(2)
    expect(seen.filter((n) => n === 1)).toHaveLength(0)
  })

  it('skips an unchanged tile and still forces a keepalive', async () => {
    const kinds: string[] = []
    const queue = new FrameQueue(async (packet) => {
      kinds.push(tag(packet))
    })
    const jpeg = Buffer.from([0xff, 0xd8, 0xff, 0xd9])
    await queue.paint(new Map([[1, jpeg]]))
    const before = kinds.length
    await queue.paint(new Map([[1, jpeg]]))
    expect(kinds.length).toBe(before)
    await queue.keepalive(jpeg)
    expect(kinds.length).toBeGreaterThan(before)
    expect(kinds.at(-1)).toContain('STP')
    expect(refresh()[5]).toBe('S'.charCodeAt(0))
  })
})

describe('burn bytes', () => {
  it('accepts the committed welcome image', () => {
    const jpeg = fs.readFileSync(path.join(root, 'resources/welcome-sent.jpg'))
    expect(jpeg.length).toBe(WELCOME_BYTES)
    const info = jpegInfo(jpeg)
    expect(info.baseline).toBe(true)
    expect(info.width).toBe(240)
    expect(info.height).toBe(320)
    const chunks = Math.ceil(jpeg.length / 1024)
    expect(chunks).toBe(19)
  })

  it('does not refresh when the report never comes', async () => {
    const writes: string[] = []
    const welcome = fs.readFileSync(path.join(root, 'resources/welcome-sent.jpg'))
    const tile = Buffer.from([0xff, 0xd8, 0xff, 0xd9])
    const result = await executeBurn(
      {
        write: async (packet) => {
          writes.push(tag(packet))
        },
        sleep: async () => undefined,
        waitForLogReport: async () => false
      },
      { brightness: 70, tiles: Array(6).fill(tile), welcome }
    )
    expect(result).toBe('failed')
    const logAt = writes.findIndex((w) => w.startsWith('CRT··LOG'))
    expect(writes.slice(logAt + 1).some((w) => w.startsWith('CRT··STP'))).toBe(false)
    expect(writes.slice(logAt + 1).some((w) => w.startsWith('CRT··CONNECT'))).toBe(false)
  })
})
