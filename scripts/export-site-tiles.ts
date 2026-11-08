/**
 * Renders the tiles the download page shows, with the app's own tile renderer.
 *
 * Each screen is six PNGs, site/tiles/<screen>-<key>.png, drawn upright in tile space with no
 * per-key window offset (the site's device drawing centres every tile in its key) and scaled up
 * 4x with nearest-neighbour, so the browser only ever scales them down and the pixel type stays
 * even at any size. The welcome screen is cropped from the burned image instead of rendered.
 *
 * The data is what a typical Claude Code + Codex + OpenCode setup shows, not the box's demo set:
 * the app only lists sessions from those three agents, and Models & Usage starts with the usage key.
 */
import fs from 'fs'
import os from 'os'
import path from 'path'
import { createCanvas, loadImage, type Canvas, type Image } from '@napi-rs/canvas'
import { AGENT_ORDER, type TileSpec } from '../src/shared/model'
import { renderUpright } from '../src/main/deck/render'
import panel from '../resources/panel-geometry.json'

const SCALE = 4
const dir = path.resolve('site/tiles')

const model = (name: string, current = false): TileSpec => ({
  kind: 'model',
  model: { name, current, fiveHour: null, sevenDay: null, fiveLabel: '5H', sevenLabel: '7D', shared: false, noQuota: false, stale: false }
})

// The example mode on the page gives BUILD "~/icons/hammer.svg"; draw it with Lucide's hammer (ISC).
const hammer = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'td-site-')), 'hammer.svg')
fs.writeFileSync(hammer, '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 12-8.373 8.373a1 1 0 1 1-3-3L12 9"/><path d="m18 15 4-4"/><path d="m21.5 11.5-1.914-1.914A2 2 0 0 1 19 8.172V7l-2.26-2.26a6 6 0 0 0-4.202-1.756L9 2.96l.92.82A6.18 6.18 0 0 1 12 8.4V10l2 2h1.172a2 2 0 0 1 1.414.586L18.5 14.5"/></svg>')

const screens: Record<string, TileSpec[]> = {
  agents: AGENT_ORDER.map((agent) => ({ kind: 'agents', agent, active: 0, installed: true })),
  sessions: [
    { kind: 'session', session: { agent: 'claude-code', title: 'my-app-3f', context: 62, status: 'working' } },
    { kind: 'session', session: { agent: 'claude-code', title: 'billing', context: 41, status: 'needs-approval' } },
    { kind: 'session', session: { agent: 'codex', title: 'flaky-tests', context: null, status: 'working' } },
    { kind: 'session', session: { agent: 'claude-code', title: 'docs', context: 24, status: 'completed' } },
    { kind: 'session', session: { agent: 'codex', title: 'migration', context: null, status: 'needs-input' } },
    { kind: 'session', session: { agent: 'opencode', title: 'notes', context: null, status: 'idle' } }
  ],
  models: [
    { kind: 'usage', agent: 'CLAUDE', fiveHour: 62, sevenDay: 41, fiveLabel: '5H', sevenLabel: '7D' },
    model('Opus', true),
    model('Sonnet'),
    model('Haiku'),
    model('Fable'),
    { kind: 'model', model: null }
  ],
  custom: [
    { kind: 'custom', custom: { lines: ['BUILD'], iconFile: hammer } },
    { kind: 'custom', custom: { lines: ['LOGS'] } },
    { kind: 'custom', custom: { lines: ['EDITOR'] } },
    { kind: 'custom', custom: { lines: ['PALETTE'] } },
    { kind: 'custom', custom: { lines: ['AGENTS'] } },
    { kind: 'custom', custom: null }
  ]
}

function upscale(source: Canvas | Image, sx: number, sy: number, size: number): Canvas {
  const out = createCanvas(size * SCALE, size * SCALE) as Canvas
  const ctx = out.getContext('2d')
  ctx.imageSmoothingEnabled = false
  ctx.drawImage(source, sx, sy, size, size, 0, 0, size * SCALE, size * SCALE)
  return out
}

async function main(): Promise<void> {
  fs.mkdirSync(dir, { recursive: true })
  for (const name of fs.readdirSync(dir)) if (name.endsWith('.png')) fs.unlinkSync(path.join(dir, name))

  for (const [screen, specs] of Object.entries(screens)) {
    for (let i = 0; i < 6; i++) {
      const tile = await renderUpright(specs[i]!, i + 1, false)
      fs.writeFileSync(path.join(dir, `${screen}-${i + 1}.png`), await upscale(tile, 0, 0, 64).encode('png'))
    }
  }

  // The welcome screen as each key's window shows it: a square centred on the window, so the
  // composition matches the deck even though the app's tiles sit off-centre in their windows.
  const welcome = await loadImage(fs.readFileSync(path.resolve('resources/welcome-320x240.png')))
  for (let i = 0; i < 6; i++) {
    const [x0, y0, x1, y1] = panel.windows[i]!
    const size = Math.min(x1! - x0!, y1! - y0!)
    const sx = Math.round((x0! + x1! - size) / 2)
    const sy = Math.round((y0! + y1! - size) / 2)
    fs.writeFileSync(path.join(dir, `welcome-${i + 1}.png`), await upscale(welcome, sx, sy, size).encode('png'))
  }
  console.log(`exported ${Object.keys(screens).length + 1} screens to site/tiles`)
}

void main()
