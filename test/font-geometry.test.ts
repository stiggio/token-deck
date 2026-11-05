import { describe, expect, it } from 'vitest'
import { advance, glyphWidth, measure } from '../src/main/deck/pixelfont'
import { layoutOffset, safeRect } from '../src/main/deck/geometry'
import { groupOk, OVERLAY_GROUPS } from '../src/shared/overlays'

describe('pixelfont', () => {
  it('uses the specified advances', () => {
    expect(glyphWidth('.')).toBe(2)
    expect(advance('.')).toBe(3)
    expect(glyphWidth('1')).toBe(3)
    expect(advance('I')).toBe(4)
    expect(advance(' ')).toBe(3)
    expect(advance('A')).toBe(6)
    expect(measure('1')).toBe(3)
    expect(measure('100%')).toBe(21)
  })
})

describe('geometry', () => {
  it('matches the safe rects', () => {
    expect(safeRect(1)).toEqual({ x0: 0, y0: 0, x1: 61, y1: 62 })
    expect(safeRect(2)).toEqual({ x0: 2, y0: 0, x1: 63, y1: 62 })
    expect(safeRect(3)).toEqual({ x0: 6, y0: 0, x1: 63, y1: 62 })
    expect(safeRect(4)).toEqual({ x0: 0, y0: 5, x1: 61, y1: 63 })
    expect(safeRect(5)).toEqual({ x0: 2, y0: 5, x1: 63, y1: 63 })
    expect(safeRect(6)).toEqual({ x0: 6, y0: 5, x1: 63, y1: 63 })
  })

  it('centres Agents to 1px and leaves the documented residue on Models and Sessions', () => {
    expect(layoutOffset(4, 'agents').dx).toBe(-1)
    for (const key of [1, 2, 3, 4, 5, 6]) {
      const o = layoutOffset(key, 'agents')
      expect(Math.abs(o.dx)).toBeLessThanOrEqual(8)
    }
    expect(layoutOffset(3, 'models').dx).toBe(5)
    expect(layoutOffset(6, 'models').dy).toBe(5)
    expect(layoutOffset(3, 'sessions').dx).toBe(3)
    expect(layoutOffset(6, 'sessions').dy).toBe(4)
  })
})

describe('overlay groups', () => {
  it('keeps every static group inside 10 characters and 58px', () => {
    for (const group of OVERLAY_GROUPS) expect(groupOk(group)).toBe(true)
  })
})
