import fs from 'fs'
import { createCanvas, loadImage, type Canvas, type SKRSContext2D } from '@napi-rs/canvas'
import { APPROVAL, C4, C8, C9, HAIR, INK, LIME, LIMIT, STALE, UNLIT, WHITE, WORKING } from './colors'
import { disc, fill, ring, roundRect, strokeRect, text } from './draw'
import { AGENT_PLACEMENT, loadGlyph, loadSvgFile } from './glyphs'
import { hairlineColumns, layoutOffset, safeRect, windowCentreInTile, type LayoutName } from './geometry'
import { resource } from '../paths'
import { fitText, fitTitle, measure } from './pixelfont'
import type { AgentId, ModelPaint, SessionPaint, SessionStatus, TileSpec } from '../../shared/model'
import { LAUNCH_ONLY } from '../../shared/model'

const welcomeCache = new Map<number, Buffer>()

export function welcomeCrop(key: number): Buffer {
  const hit = welcomeCache.get(key)
  if (hit) return hit
  const buf = fs.readFileSync(resource('welcome-tiles', `key${key}.jpg`))
  welcomeCache.set(key, buf)
  return buf
}

function blank(): { canvas: Canvas; ctx: SKRSContext2D } {
  const canvas = createCanvas(64, 64) as Canvas
  const ctx = canvas.getContext('2d')
  ctx.imageSmoothingEnabled = false
  fill(ctx, INK, 0, 0, 64, 64)
  return { canvas, ctx }
}

/** dst(x, y) = src(y, 63 − x). 90° clockwise, pixel copy. */
export function toWireCanvas(source: Canvas): Canvas {
  const src = source.getContext('2d').getImageData(0, 0, 64, 64)
  const dest = createCanvas(64, 64) as Canvas
  const dctx = dest.getContext('2d')
  const image = dctx.getImageData(0, 0, 64, 64)
  for (let y = 0; y < 64; y++) {
    for (let x = 0; x < 64; x++) {
      const sx = y
      const sy = 63 - x
      const si = (sy * 64 + sx) * 4
      const di = (y * 64 + x) * 4
      image.data[di] = src.data[si]!
      image.data[di + 1] = src.data[si + 1]!
      image.data[di + 2] = src.data[si + 2]!
      image.data[di + 3] = 255
    }
  }
  dctx.putImageData(image, 0, 0)
  return dest
}

export async function encodeWire(source: Canvas): Promise<Buffer> {
  const wire = toWireCanvas(source)
  return Buffer.from(await wire.encode('jpeg', { quality: 100 }))
}

function shift(layout: LayoutName, key: number, enabled: boolean): { dx: number; dy: number } {
  if (!enabled) return { dx: 0, dy: 0 }
  return layoutOffset(key, layout)
}

async function drawAgentGlyph(
  ctx: SKRSContext2D,
  layout: 'agents' | 'sessions',
  agent: AgentId,
  dx: number,
  dy: number,
  dim: boolean
): Promise<void> {
  const place = AGENT_PLACEMENT[layout][agent]
  const image = await loadGlyph(place, WHITE, dim)
  ctx.imageSmoothingEnabled = false
  ctx.drawImage(image, place.x + dx, place.y + dy, place.w, place.h)
}

function emptySlot(ctx: SKRSContext2D, key: number, offset: boolean): void {
  const c = offset ? windowCentreInTile(key) : { x: 32, y: 32 }
  const ox = Math.round(c.x - 9)
  const oy = Math.round(c.y - 9)
  for (let row = 0; row < 4; row++) {
    for (let col = 0; col < 4; col++) {
      fill(ctx, UNLIT, ox + col * 5, oy + row * 5, 3, 3)
    }
  }
}

function meter(ctx: SKRSContext2D, active: number, dx: number, dy: number): void {
  for (let i = 0; i < 4; i++) {
    fill(ctx, i < active ? LIME : UNLIT, 13 + i * 10 + dx, 46 + dy, 8, 8)
  }
}

async function paintAgents(
  ctx: SKRSContext2D,
  spec: Extract<TileSpec, { kind: 'agents' }>,
  key: number,
  offset: boolean,
  clip: boolean
): Promise<number> {
  const { dx, dy } = shift('agents', key, offset)
  const launch = LAUNCH_ONLY.has(spec.agent)
  const dim = launch && !spec.installed
  await drawAgentGlyph(ctx, 'agents', spec.agent, dx, dy, dim)
  if (!clip) {
    if (launch) text(ctx, 'LAUNCH', 32 + dx, 47 + dy, dim ? STALE : C8, 'center')
    else meter(ctx, Math.max(0, Math.min(4, spec.active)), dx, dy)
  }
  return dy
}

function statusColor(status: SessionStatus): string {
  switch (status) {
    case 'working':
      return WORKING
    case 'needs-approval':
      return APPROVAL
    case 'needs-input':
      return WHITE
    case 'completed':
      return LIME
    case 'disconnected':
      return STALE
    default:
      return C8
  }
}

async function paintSession(
  ctx: SKRSContext2D,
  session: SessionPaint | null,
  key: number,
  offset: boolean,
  clip: boolean
): Promise<number> {
  const { dx, dy } = shift('sessions', key, offset)
  if (!session) {
    emptySlot(ctx, key, offset)
    return dy
  }
  const cx = 32 + dx
  const cy = 27 + dy
  const disconnected = session.status === 'disconnected'
  const unknown = session.context === null
  if (unknown) ring(ctx, cx, cy, 17, 4, disconnected ? STALE : C8, Math.PI * 2, true)
  else {
    ring(ctx, cx, cy, 17, 4, UNLIT, null)
    if (session.context !== null && session.context > 0) {
      const arc = disconnected ? STALE : session.context > 85 ? LIMIT : WHITE
      ring(ctx, cx, cy, 17, 4, arc, (session.context / 100) * Math.PI * 2)
    }
  }
  await drawAgentGlyph(ctx, 'sessions', session.agent, dx, dy, false)
  disc(ctx, 44 + dx, 15 + dy, 15, INK)
  if (disconnected) ring(ctx, 44 + dx, 15 + dy, 5, 3, STALE, null)
  else disc(ctx, 44 + dx, 15 + dy, 10, statusColor(session.status))
  if (session.status === 'needs-approval') {
    strokeRect(ctx, 3 + dx, 2 + dy, 58, 58, 3, APPROVAL)
  }
  if (!clip) {
    const title = fitTitle(session.title, 50)
    text(ctx, title, 32 + dx, 48 + dy, disconnected ? STALE : C4, 'center')
  }
  return dy
}

function squares(ctx: SKRSContext2D, x0: number, y: number, lit: number, color: string, unlit: string): void {
  for (let i = 0; i < 10; i++) {
    fill(ctx, i < lit ? color : unlit, x0 + dxOf(i), y, 4, 4)
  }
}

function dxOf(i: number): number {
  return i * 5
}

function paintModel(ctx: SKRSContext2D, model: ModelPaint | null, key: number, offset: boolean, clip: boolean): number {
  const { dx, dy } = shift('models', key, offset)
  if (!model) {
    emptySlot(ctx, key, offset)
    return dy
  }
  const name = model.name
  const shown = fitText(name, 49, 12)
  if (model.current) {
    roundRect(ctx, 2 + dx, 2 + dy, 57, 14, 2, LIME)
    text(ctx, shown, 6 + dx, 6 + dy, INK)
  } else {
    text(ctx, shown, 6 + dx, 6 + dy, WHITE)
  }
  if (model.noQuota) {
    text(ctx, 'NO QUOTA', 6 + dx, 20 + dy, C8)
    text(ctx, 'DATA', 6 + dx, 30 + dy, C8)
    return dy
  }
  const pctColor = model.stale ? C8 : WHITE
  const litColor = model.stale ? STALE : model.current ? LIME : C9
  const row = (label: string, pct: number | null, yText: number, ySq: number) => {
    text(ctx, label, 6 + dx, yText + dy, C8)
    const value = pct === null ? '--' : `${Math.round(pct)}%`
    text(ctx, value, 54 + dx, yText + dy, pct === null ? C8 : pctColor, 'right')
    const lit = pct === null ? 0 : Math.max(0, Math.min(10, Math.round(pct / 10)))
    squares(ctx, 6 + dx, ySq + dy, lit, litColor, UNLIT)
  }
  row(model.fiveLabel, model.fiveHour, 20, 28)
  if (!clip) {
    row(model.sevenLabel, model.sevenDay, 36, 44)
    if (model.stale) {
      fill(ctx, C8, 6 + dx, 53 + dy, 4, 4)
      text(ctx, 'STALE', 12 + dx, 52 + dy, C8)
    } else if (model.shared) {
      fill(ctx, model.current ? LIME : C8, 6 + dx, 53 + dy, 4, 4)
      text(ctx, 'SHARED', 12 + dx, 52 + dy, C8)
    }
  }
  return dy
}

async function paintCustom(
  ctx: SKRSContext2D,
  lines: string[] | null,
  iconFile: string | undefined,
  key: number,
  offset: boolean,
  clip: boolean
): Promise<number> {
  const { dx, dy } = shift('custom', key, offset)
  if (!lines) {
    emptySlot(ctx, key, offset)
    return dy
  }
  if (iconFile && fs.existsSync(iconFile)) {
    const image = iconFile.toLowerCase().endsWith('.svg') ? await loadSvgFile(iconFile, 28) : await loadImage(iconFile)
    ctx.imageSmoothingEnabled = false
    ctx.drawImage(image, 32 - 14 + dx, 21 - 14 + dy, 28, 28)
  }
  if (!clip) {
    const rows = lines.slice(0, 2)
    rows.forEach((line, i) => {
      const fitted = fitText(line.toUpperCase(), 50, 16)
      text(ctx, fitted, 32 + dx, 40 + i * 8 + dy, WHITE, 'center')
    })
  }
  return dy
}

async function paintConnect(ctx: SKRSContext2D, key: number, offset: boolean): Promise<number> {
  const { dx, dy } = shift('agents', key, offset)
  const image = await loadSvgFile(resource('glyphs', 'stigg-mark-white.svg'), 30)
  ctx.imageSmoothingEnabled = false
  ctx.drawImage(image, 17 + dx, 10 + dy, 30, 29)
  text(ctx, 'CONNECT', 12 + dx, 47 + dy, WHITE)
  return dy
}

function paintTest(ctx: SKRSContext2D): void {
  strokeRect(ctx, 0, 0, 64, 64, 1, APPROVAL)
  ring(ctx, 32, 24, 14, 2, LIME, null)
  text(ctx, 'LIME', 32, 8, LIME, 'center')
  text(ctx, 'Sonnet', 32, 40, WHITE, 'center')
  roundRect(ctx, 4, 50, 56, 12, 2, LIME)
  text(ctx, 'Opus', 32, 52, INK, 'center')
}

function paintOverlay(ctx: SKRSContext2D, key: number, dy: number, group: string | null): void {
  const top = 48 + dy
  if (top < 64) fill(ctx, INK, 0, top, 64, 64 - top)
  if (top >= 0 && top < 64) {
    const cols = hairlineColumns(key)
    fill(ctx, HAIR, cols.x0, top, cols.x1 - cols.x0 + 1, 1)
  }
  if (!group) return
  if (key > 3) return
  const centre = windowCentreInTile(key).x
  const y = 53 + dy
  const w = measure(group)
  let x = Math.round(centre - (w - 1) / 2)
  const safe = safeRect(key)
  if (x < safe.x0) x = safe.x0
  if (x + w - 1 > safe.x1) x = safe.x1 - w + 1
  text(ctx, group, x, y, WHITE)
}

export async function renderUpright(spec: TileSpec, key: number, offset = true, overlay: string | null = null): Promise<Canvas> {
  if (spec.kind === 'welcome') {
    throw new Error('welcome crops are pre-encoded')
  }
  const { canvas, ctx } = blank()
  let dy = 0
  const clip = overlay !== null
  if (spec.kind === 'agents') dy = await paintAgents(ctx, spec, key, offset, clip)
  else if (spec.kind === 'session') dy = await paintSession(ctx, spec.session, key, offset, clip)
  else if (spec.kind === 'model') dy = paintModel(ctx, spec.model, key, offset, clip)
  else if (spec.kind === 'custom') dy = await paintCustom(ctx, spec.custom?.lines ?? null, spec.custom?.iconFile, key, offset, clip)
  else if (spec.kind === 'connect') dy = await paintConnect(ctx, key, offset)
  else if (spec.kind === 'test') paintTest(ctx)
  if (overlay !== null) paintOverlay(ctx, key, dy, overlay.length ? overlay : null)
  return canvas
}

export async function renderTile(spec: TileSpec, key: number, offset = true, overlay: string | null = null): Promise<Buffer> {
  if (spec.kind === 'welcome') return welcomeCrop(key)
  const canvas = await renderUpright(spec, key, offset, overlay)
  return encodeWire(canvas)
}

export function litCount(pct: number): number {
  return Math.max(0, Math.min(10, Math.round(pct / 10)))
}
