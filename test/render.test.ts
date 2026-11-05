import { describe, expect, it } from 'vitest'
import { createCanvas } from '@napi-rs/canvas'
import { encodeWire, renderTile, toWireCanvas } from '../src/main/deck/render'
import { is444, jpegInfo } from '../src/main/deck/jpeg'
import { demoAgents, demoIdle, demoModelTiles, demoSessions } from '../src/main/deck/demo'
import { welcomeCrop } from '../src/main/deck/render'
import type { TileSpec } from '../src/shared/model'
import { splitGroups } from '../src/shared/overlays'

describe('rotation and jpeg', () => {
  it('moves a pixel at (0, 0) to (63, 0)', () => {
    const canvas = createCanvas(64, 64)
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#000000'
    ctx.fillRect(0, 0, 64, 64)
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, 1, 1)
    const wire = toWireCanvas(canvas)
    const data = wire.getContext('2d').getImageData(0, 0, 64, 64).data
    const at = (x: number, y: number) => data[(y * 64 + x) * 4]
    expect(at(63, 0)).toBe(255)
    expect(at(0, 0)).toBe(0)
  })

  it('encodes 4:4:4 at quality 100', async () => {
    const canvas = createCanvas(64, 64)
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#131512'
    ctx.fillRect(0, 0, 64, 64)
    ctx.fillStyle = '#92E759'
    ctx.fillRect(8, 8, 4, 4)
    const jpeg = await encodeWire(canvas)
    const info = jpegInfo(jpeg)
    expect(info.baseline).toBe(true)
    expect(is444(info)).toBe(true)
  })
})

describe('built-in tiles stay under 10 KB', () => {
  it('renders demo, idle, overlays and welcome crops', async () => {
    const specs: Array<{ spec: TileSpec; key: number; overlay?: string | null }> = []
    demoAgents().forEach((spec, i) => specs.push({ spec, key: i + 1 }))
    demoSessions().forEach((spec, i) => specs.push({ spec, key: i + 1 }))
    demoModelTiles().forEach((spec, i) => specs.push({ spec, key: i + 1 }))
    demoIdle().forEach((spec, i) => specs.push({ spec, key: i + 1 }))
    specs.push({ spec: { kind: 'test' }, key: 1 })
    specs.push({ spec: { kind: 'session', session: null }, key: 3 })
    specs.push({ spec: { kind: 'custom', custom: { lines: ['BUILD', 'NOW'] } }, key: 6 })
    const overlay = splitGroups('ASK | PRESS TO | APPLY')
    demoAgents().forEach((spec, i) => specs.push({ spec, key: i + 1, overlay: overlay[i] ?? '' }))
    for (const item of specs) {
      const jpeg = await renderTile(item.spec, item.key, true, item.overlay ?? null)
      expect(jpeg.length).toBeLessThan(10000)
    }
    for (let key = 1; key <= 6; key++) expect(welcomeCrop(key).length).toBeLessThan(10000)
  })
})
