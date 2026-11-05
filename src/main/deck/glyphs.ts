import fs from 'fs'
import path from 'path'
import { loadImage, type Image } from '@napi-rs/canvas'
import { resource } from '../paths'
import type { AgentId } from '../../shared/model'

type Place = { file: string; w: number; h: number; x: number; y: number }

export const AGENT_PLACEMENT: Record<'agents' | 'sessions', Record<AgentId, Place>> = {
  agents: {
    'claude-code': { file: 'claude-code.svg', w: 30, h: 30, x: 17, y: 10 },
    cursor: { file: 'cursor.svg', w: 26, h: 29, x: 20, y: 10 },
    codex: { file: 'codex.svg', w: 27, h: 27, x: 19, y: 11 },
    opencode: { file: 'opencode.svg', w: 25, h: 27, x: 20, y: 11 },
    amp: { file: 'amp.svg', w: 38, h: 20, x: 13, y: 15 },
    devin: { file: 'devin.svg', w: 29, h: 32, x: 19, y: 9 }
  },
  sessions: {
    'claude-code': { file: 'claude-code.svg', w: 18, h: 18, x: 23, y: 18 },
    cursor: { file: 'cursor.svg', w: 15, h: 18, x: 25, y: 18 },
    codex: { file: 'codex.svg', w: 16, h: 16, x: 24, y: 19 },
    opencode: { file: 'opencode.svg', w: 15, h: 16, x: 24, y: 19 },
    amp: { file: 'amp.svg', w: 23, h: 12, x: 21, y: 21 },
    devin: { file: 'devin.svg', w: 17, h: 19, x: 24, y: 17 }
  }
}

const cache = new Map<string, Promise<Image>>()

function prepareSvg(file: string, w: number, h: number, color: string, dim: boolean): string {
  let svg = fs.readFileSync(file, 'utf8')
  if (dim) {
    svg = svg.replace(/fill="#ffffff"/gi, 'fill="#3C3E3A"').replace(/fill="#5b5d59"/gi, 'fill="#3C3E3A"')
  } else {
    svg = svg.replace(/fill="#ffffff"/gi, `fill="${color}"`)
  }
  svg = svg.replace(/currentColor/g, '#ffffff')
  svg = svg.replace(/\s(width|height)="[^"]*"/g, '')
  svg = svg.replace('<svg', `<svg width="${w}" height="${h}"`)
  return svg
}

export function loadGlyph(place: Place, color: string, dim: boolean): Promise<Image> {
  const key = `${place.file}|${place.w}x${place.h}|${color}|${dim ? 1 : 0}`
  const hit = cache.get(key)
  if (hit) return hit
  const pending = loadImage(Buffer.from(prepareSvg(path.join(resource('glyphs'), place.file), place.w, place.h, color, dim)))
  cache.set(key, pending)
  return pending
}

export function loadSvgFile(file: string, size: number, color = '#ffffff'): Promise<Image> {
  const place = { file: path.basename(file), w: size, h: size, x: 0, y: 0 }
  const key = `file|${file}|${size}|${color}`
  const hit = cache.get(key)
  if (hit) return hit
  const pending = loadImage(Buffer.from(prepareSvg(file, size, size, color, false)))
  cache.set(key, pending)
  return pending
}
