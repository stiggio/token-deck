import fs from 'fs'
import path from 'path'
import { createCanvas, loadImage } from '@napi-rs/canvas'

const root = path.resolve(import.meta.dirname, '..')

async function mark(size, color) {
  let svg = fs.readFileSync(path.join(root, 'resources/glyphs/stigg-mark-white.svg'), 'utf8')
  svg = svg.replace(/#FFFFFF/gi, color)
  svg = svg.replace(/\s(width|height)="[^"]*"/g, '')
  svg = svg.replace('<svg', `<svg width="${size}" height="${size}"`)
  return loadImage(Buffer.from(svg))
}

async function tray(file, size) {
  const canvas = createCanvas(size, size)
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, size, size)
  const image = await mark(size, '#000000')
  const pad = Math.round(size * 0.12)
  ctx.drawImage(image, pad, pad, size - pad * 2, size - pad * 2)
  fs.writeFileSync(path.join(root, 'resources', file), await canvas.encode('png'))
}

await tray('trayTemplate.png', 16)
await tray('trayTemplate@2x.png', 32)

const iconSvg = fs.readFileSync(path.join(root, 'brand-kit/brand/stigg-app-icon.svg'), 'utf8')
const icon = await loadImage(Buffer.from(iconSvg))
const canvas = createCanvas(1024, 1024)
canvas.getContext('2d').drawImage(icon, 0, 0, 1024, 1024)
fs.mkdirSync(path.join(root, 'build'), { recursive: true })
fs.writeFileSync(path.join(root, 'build/icon.png'), await canvas.encode('png'))
console.log('icons ok')
