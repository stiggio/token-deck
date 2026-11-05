import { randomBytes } from 'crypto'
import Store from 'electron-store'
import { DEFAULT_KNOB_MAP, type KnobMap } from '../deck/protocol'
import type { BurnRecord } from '../burn/records'
import { homeDir } from '../log'
import type { DeckMode } from '../../shared/model'

export type UsageWindow = { pct: number; resetsAt?: number }
export type UsageSnapshot = { five?: UsageWindow; seven?: UsageWindow; at: number; labels?: { five: string; seven: string } }

export type Schema = {
  brightness: number
  repaintKeepalive: boolean
  autoBurn: boolean
  startAtLogin: boolean
  wizardDone: boolean
  wizardStep: number
  mode: Exclude<DeckMode, 'custom' | 'picker' | 'idle'>
  knobMap: KnobMap
  knobsCalibrated: boolean
  burnedSerials: BurnRecord[]
  burnFailures: Record<string, number>
  token: string
  favorites: { 'claude-code': string[]; codex: string[]; opencode: string[] }
  opencodeUrl: string
  codexUseHooks: boolean
  modelNamesUpper: boolean
  usage: Record<string, UsageSnapshot>
  fullConfirmed: boolean
}

const defaults: Schema = {
  brightness: 70,
  repaintKeepalive: true,
  autoBurn: true,
  startAtLogin: false,
  wizardDone: false,
  wizardStep: 0,
  mode: 'agents',
  knobMap: DEFAULT_KNOB_MAP,
  knobsCalibrated: false,
  burnedSerials: [],
  burnFailures: {},
  token: randomBytes(16).toString('hex'),
  favorites: {
    'claude-code': ['Opus', 'Sonnet', 'Haiku', 'Fable'],
    codex: [],
    opencode: []
  },
  opencodeUrl: 'http://127.0.0.1:4096',
  codexUseHooks: false,
  modelNamesUpper: false,
  usage: {},
  fullConfirmed: false
}

export function openStore(): Store<Schema> {
  return new Store<Schema>({
    name: 'settings',
    cwd: homeDir(),
    defaults
  })
}

export type SettingsStore = Store<Schema>
