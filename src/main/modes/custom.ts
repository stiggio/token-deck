import fs from 'fs'
import os from 'os'
import path from 'path'
import chokidar from 'chokidar'
import { openApp, openUrl, runShell, sendKeys } from '../system/focus'

export type Action =
  | { type: 'shell'; command: string; cwd?: string }
  | { type: 'url'; url: string }
  | { type: 'open'; app: string }
  | { type: 'keys'; keys: string }
  | { type: 'mode'; mode: 'agents' | 'sessions' | 'models' }

export type CustomTile = { label?: string; icon?: string; action?: Action } | null

export type CustomMode = {
  file: string
  name: string
  tiles: CustomTile[]
  knobs: { main?: KnobActions | null; left?: KnobActions | null; right?: KnobActions | null }
  errors: string[]
  /** The file couldn't be read as a mode at all, so it has no keys. */
  invalid?: boolean
}

type KnobActions = { cw?: Action | null; ccw?: Action | null; click?: Action | null }

export function modesDir(): string {
  return path.join(os.homedir(), '.tokendeck', 'modes')
}

export function loadModes(): CustomMode[] {
  const dir = modesDir()
  fs.mkdirSync(dir, { recursive: true })
  return fs
    .readdirSync(dir)
    .filter((name) => name.endsWith('.json'))
    .map((name) => loadMode(path.join(dir, name)))
}

export function loadMode(file: string): CustomMode {
  const errors: string[] = []
  let json: Record<string, unknown>
  try {
    const parsed = JSON.parse(fs.readFileSync(file, 'utf8')) as unknown
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('a mode file holds one JSON object')
    json = parsed as Record<string, unknown>
  } catch (err) {
    // Six empty keys rather than none, so the deck still draws and says what's wrong.
    return { file, name: path.basename(file, '.json'), tiles: [null, null, null, null, null, null], knobs: {}, errors: [String(err)], invalid: true }
  }
  const tiles = (Array.isArray(json.tiles) ? json.tiles.slice(0, 6) : []).map((tile): CustomTile =>
    tile && typeof tile === 'object' && !Array.isArray(tile) ? { ...(tile as Record<string, unknown>) } as CustomTile : null
  )
  while (tiles.length < 6) tiles.push(null)
  tiles.forEach((tile, index) => {
    if (!tile || tile.label == null) return
    if (typeof tile.label !== 'string') {
      errors.push(`Tile ${index + 1} label isn't text.`)
      tile.label = String(tile.label)
    }
    const lines = tile.label.split('\n').slice(0, 2)
    if (tile.label.length > 24) errors.push(`Tile ${index + 1} label was cut to 50px.`)
    tile.label = lines.join('\n')
  })
  const knobs = (json.knobs && typeof json.knobs === 'object' && !Array.isArray(json.knobs) ? json.knobs : {}) as CustomMode['knobs']
  return { file, name: String(json.name || path.basename(file, '.json')), tiles, knobs, errors }
}

export function watchModes(onChange: () => void): chokidar.FSWatcher {
  fs.mkdirSync(modesDir(), { recursive: true })
  return chokidar.watch(modesDir(), { ignoreInitial: true }).on('all', () => onChange())
}

export async function runAction(action: Action | null | undefined): Promise<'ok' | 'failed' | 'mode'> {
  if (!action) return 'failed'
  try {
    if (action.type === 'shell') {
      const cwd = action.cwd?.replace(/^~/, os.homedir())
      await runShell(action.command, cwd)
      return 'ok'
    }
    if (action.type === 'url') {
      await openUrl(action.url)
      return 'ok'
    }
    if (action.type === 'open') {
      await openApp(action.app)
      return 'ok'
    }
    if (action.type === 'keys') {
      await sendKeys(action.keys)
      return 'ok'
    }
    return 'mode'
  } catch {
    return 'failed'
  }
}

export const MODE_EXAMPLE = {
  name: 'Deploy',
  tiles: [
    { label: 'BUILD', icon: '~/icons/hammer.svg', action: { type: 'shell', command: 'npm run build', cwd: '~/dev/app' } },
    { label: 'LOGS', action: { type: 'url', url: 'https://grafana.example.com/d/abc' } },
    { label: 'EDITOR', action: { type: 'open', app: 'Cursor' } },
    { label: 'PALETTE', action: { type: 'keys', keys: 'cmd+shift+p' } },
    { label: 'AGENTS', action: { type: 'mode', mode: 'agents' } },
    null
  ],
  knobs: {
    main: { cw: { type: 'keys', keys: 'cmd+=' }, ccw: { type: 'keys', keys: 'cmd+-' }, click: { type: 'shell', command: 'say done' } },
    left: null,
    right: null
  }
}
