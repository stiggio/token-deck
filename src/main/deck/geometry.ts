import panel from '../../../resources/panel-geometry.json'

export type Box = { x0: number; y0: number; x1: number; y1: number }

type PanelFile = {
  tile: number
  tiles: Array<{ key: number; x: number; y: number }>
  windows: number[][]
}

const file = panel as PanelFile

export const TILE = file.tile

export type Half = { x0: number; y0: number; x1: number; y1: number }

export function tileOrigin(key: number): { x: number; y: number } {
  const t = file.tiles[key - 1]
  if (!t) throw new Error(`bad key ${key}`)
  return { x: t.x, y: t.y }
}

export function windowHalf(key: number): Half {
  const w = file.windows[key - 1]
  if (!w) throw new Error(`bad key ${key}`)
  return { x0: w[0]!, y0: w[1]!, x1: w[2]!, y1: w[3]! }
}

export function windowCentreInTile(key: number): { x: number; y: number } {
  const origin = tileOrigin(key)
  const w = windowHalf(key)
  return { x: (w.x0 + w.x1) / 2 - origin.x, y: (w.y0 + w.y1) / 2 - origin.y }
}

/** Tile ∩ window inset 6px, in tile coordinates, inclusive. */
export function safeRect(key: number): Box {
  const origin = tileOrigin(key)
  const tile: Half = { x0: origin.x, y0: origin.y, x1: origin.x + TILE, y1: origin.y + TILE }
  const w = windowHalf(key)
  const inner: Half = { x0: w.x0 + 6, y0: w.y0 + 6, x1: w.x1 - 6, y1: w.y1 - 6 }
  const x0 = Math.max(tile.x0, inner.x0) - origin.x
  const x1 = Math.min(tile.x1, inner.x1) - origin.x - 1
  const y0 = Math.max(tile.y0, inner.y0) - origin.y
  const y1 = Math.min(tile.y1, inner.y1) - origin.y - 1
  return { x0, y0, x1, y1 }
}

export function boxCentre(box: Box): { x: number; y: number } {
  return { x: (box.x0 + box.x1 + 1) / 2, y: (box.y0 + box.y1 + 1) / 2 }
}

export const DESIGN_BOXES = {
  agents: { x0: 13, y0: 9, x1: 50, y1: 53 },
  sessions: { x0: 3, y0: 2, x1: 60, y1: 59 },
  models: { x0: 2, y0: 2, x1: 58, y1: 58 },
  custom: { x0: 7, y0: 7, x1: 56, y1: 54 }
} as const

export type LayoutName = keyof typeof DESIGN_BOXES

export function layoutOffset(key: number, layout: LayoutName): { dx: number; dy: number } {
  const box = DESIGN_BOXES[layout]
  const c = windowCentreInTile(key)
  const b = boxCentre(box)
  let dx = Math.round(c.x - b.x)
  let dy = Math.round(c.y - b.y)
  const safe = safeRect(key)
  if (box.x0 + dx < safe.x0) dx = safe.x0 - box.x0
  if (box.x1 + dx > safe.x1) dx = safe.x1 - box.x1
  if (box.y0 + dy < safe.y0) dy = safe.y0 - box.y0
  if (box.y1 + dy > safe.y1) dy = safe.y1 - box.y1
  return { dx, dy }
}

export function hairlineColumns(key: number): { x0: number; x1: number } {
  const c = windowCentreInTile(key).x
  const x0 = Math.round(c - 25)
  return { x0, x1: x0 + 49 }
}

export const WELCOME_HASH = 'daea022363c85ef722c9c93bcd7f5379a995b726cb5240bc4ed92b12d15071fb'
export const WELCOME_BYTES = 18887
