import type { SKRSContext2D } from '@napi-rs/canvas'
import { textRects, measure, inkWidth } from './pixelfont'

export function fill(ctx: SKRSContext2D, color: string, x: number, y: number, w: number, h: number): void {
  ctx.fillStyle = color
  ctx.fillRect(x, y, w, h)
}

/** Pixel rounded rect. Radius 2 skips two edge pixels on the first row and one on the second. */
export function roundRect(
  ctx: SKRSContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
  color: string
): void {
  ctx.fillStyle = color
  for (let row = 0; row < h; row++) {
    let inset = 0
    if (r > 0) {
      const fromEdge = Math.min(row, h - 1 - row)
      if (fromEdge === 0) inset = r
      else if (fromEdge < r) inset = r - fromEdge
    }
    if (w - inset * 2 > 0) ctx.fillRect(x + inset, y + row, w - inset * 2, 1)
  }
}

export function strokeRect(
  ctx: SKRSContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  thickness: number,
  color: string
): void {
  fill(ctx, color, x, y, w, thickness)
  fill(ctx, color, x, y + h - thickness, w, thickness)
  fill(ctx, color, x, y, thickness, h)
  fill(ctx, color, x + w - thickness, y, thickness, h)
}

export function disc(ctx: SKRSContext2D, cx: number, cy: number, diameter: number, color: string): void {
  const r = diameter / 2
  const x0 = Math.floor(cx - r - 1)
  const y0 = Math.floor(cy - r - 1)
  const x1 = Math.ceil(cx + r + 1)
  const y1 = Math.ceil(cy + r + 1)
  ctx.fillStyle = color
  for (let y = y0; y <= y1; y++) {
    for (let x = x0; x <= x1; x++) {
      if (Math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r) ctx.fillRect(x, y, 1, 1)
    }
  }
}

export function ring(
  ctx: SKRSContext2D,
  cx: number,
  cy: number,
  radius: number,
  stroke: number,
  color: string,
  sweep: number | null,
  dashed = false
): void {
  const outer = radius + stroke / 2
  const inner = Math.max(0, radius - stroke / 2)
  const x0 = Math.floor(cx - outer - 1)
  const y0 = Math.floor(cy - outer - 1)
  const x1 = Math.ceil(cx + outer + 1)
  const y1 = Math.ceil(cy + outer + 1)
  ctx.fillStyle = color
  for (let y = y0; y <= y1; y++) {
    for (let x = x0; x <= x1; x++) {
      const dx = x + 0.5 - cx
      const dy = y + 0.5 - cy
      const d = Math.hypot(dx, dy)
      if (d > outer || d < inner) continue
      if (sweep !== null) {
        let ang = Math.atan2(dx, -dy)
        if (ang < 0) ang += Math.PI * 2
        if (sweep <= 0 || ang > sweep) continue
        if (dashed) {
          const along = ang * radius
          if (Math.floor(along / 4) % 2 === 1) continue
        }
      }
      ctx.fillRect(x, y, 1, 1)
    }
  }
}

export function text(
  ctx: SKRSContext2D,
  value: string,
  x: number,
  y: number,
  color: string,
  align: 'left' | 'right' | 'center' = 'left'
): void {
  if (!value) return
  const w = measure(value)
  let ox = x
  if (align === 'right') ox = x - w + 1
  else if (align === 'center') ox = Math.round(x - (w - 1) / 2)
  ctx.fillStyle = color
  for (const rect of textRects(value, ox, y)) {
    if (rect.x < 0 || rect.y < 0 || rect.x > 63 || rect.y > 63) continue
    ctx.fillRect(rect.x, rect.y, rect.w, rect.h)
  }
}

/** 2× pixel font. Tight drops the letter gap when the word would otherwise run off the key. */
export function textScaled(
  ctx: SKRSContext2D,
  value: string,
  x: number,
  y: number,
  color: string,
  align: 'left' | 'right' | 'center' = 'left',
  scale = 2,
  tight = false
): void {
  if (!value) return
  const w = inkWidth(value, tight) * scale
  let ox = x
  if (align === 'right') ox = x - w
  else if (align === 'center') ox = Math.round(x - w / 2)
  ctx.fillStyle = color
  for (const rect of textRects(value, ox, y, scale, tight)) {
    if (rect.x > 63 || rect.y > 63 || rect.x + rect.w < 0 || rect.y + rect.h < 0) continue
    ctx.fillRect(rect.x, rect.y, rect.w, rect.h)
  }
}
