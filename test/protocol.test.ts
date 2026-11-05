import fs from 'fs'
import path from 'path'
import { describe, expect, it } from 'vitest'
import {
  batHeader,
  brightness,
  clearKey,
  createDecoder,
  DEFAULT_KNOB_MAP,
  logHeader,
  parseFirmware,
  sampleFrames
} from '../src/main/deck/protocol'

const FORBIDDEN = [Buffer.from('CRT\0\0CLE\0\0DC'), Buffer.from('CRT\0\0HAN')]

describe('protocol frames', () => {
  it('never produces the disconnect or sleep frame', () => {
    for (const frame of sampleFrames()) {
      for (const bad of FORBIDDEN) {
        expect(frame.subarray(0, bad.length).equals(bad)).toBe(false)
      }
    }
  })

  it('puts brightness at index 10 and the clear key at index 11', () => {
    const lig = brightness(70)
    expect(lig.subarray(0, 8).toString('ascii')).toBe('CRT\0\0LIG')
    expect(lig[8]).toBe(0)
    expect(lig[9]).toBe(0)
    expect(lig[10]).toBe(70)
    const cle = clearKey(3)
    expect(cle.subarray(0, 8).toString('ascii')).toBe('CRT\0\0CLE')
    expect(cle[8]).toBe(0)
    expect(cle[9]).toBe(0)
    expect(cle[10]).toBe(0)
    expect(cle[11]).toBe(3)
    const all = clearKey(0xff)
    expect(all[11]).toBe(0xff)
  })

  it('encodes BAT and LOG lengths big-endian', () => {
    const bat = batHeader(6681, 6)
    expect(bat.readUInt32BE(8)).toBe(6681)
    expect(bat[12]).toBe(6)
    const log = logHeader(18887)
    expect(log.readUInt32BE(8)).toBe(18887)
    expect(log[12]).toBe(0x01)
  })

  it('reads a V3 firmware string and rejects anything else', () => {
    const raw = Buffer.alloc(20)
    raw.write('V3.VSDN3_PXL.02.010', 1)
    expect(parseFirmware(raw)).toBe('V3.VSDN3_PXL.02.010')
    expect(parseFirmware(Buffer.from('hello'))).toBeNull()
    expect(parseFirmware(Buffer.from([0, 0x41, 0]))).toBeNull()
  })
})

describe('decoder', () => {
  const lines = fs.readFileSync(path.join(__dirname, 'fixtures/events-2026-11-01.log'), 'utf8').split('\n')

  function rawLine(n: number): Buffer {
    const line = lines[n - 1]!
    const match = line.match(/'raw': '([0-9a-f]+)'/)
    if (!match) throw new Error(`no raw on line ${n}`)
    return Buffer.from(match[1]!, 'hex')
  }

  it('turns one main-knob press and release into one click, and two pairs into two', () => {
    const decoder = createDecoder(DEFAULT_KNOB_MAP)
    const one = [rawLine(101), rawLine(102)].flatMap((buf) => decoder.push(buf))
    expect(one).toEqual([{ type: 'knob', which: 'main', action: 'click' }])
    const two = [rawLine(101), rawLine(102), rawLine(103), rawLine(104)].flatMap((buf) => decoder.push(buf))
    expect(two.filter((e) => e.type === 'knob' && e.action === 'click')).toHaveLength(2)
  })

  it('maps the captured small-knob codes and ignores a non-ACK report', () => {
    const decoder = createDecoder()
    const cw = decoder.push(rawLine(105))
    expect(cw).toEqual([{ type: 'knob', which: 'right', action: 'cw' }])
    const ccw = decoder.push(rawLine(130))
    expect(ccw[0]).toMatchObject({ which: 'left', action: 'ccw' })
    expect(decoder.push(Buffer.from('hello world!!'))).toEqual([])
    const ack = Buffer.from('41434b00004f4b0000ff0000', 'hex')
    expect(decoder.push(ack)).toEqual([])
    const log = Buffer.from('41434b00004f4b0000000000', 'hex')
    expect(decoder.push(log)).toEqual([{ type: 'log-report' }])
  })

  it('emits a key only on press', () => {
    const decoder = createDecoder()
    expect(decoder.push(rawLine(4))).toEqual([{ type: 'key', key: 1 }])
    expect(decoder.push(rawLine(5))).toEqual([])
  })
})
