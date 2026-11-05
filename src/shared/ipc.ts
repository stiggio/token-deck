import type { AgentId, DeckMode } from './model'
import type { KnobMap } from '../main/deck/protocol'

export type DeviceSnapshot = {
  phase: string
  message: string
  manufacturer: string
  product: string
  serial: string
  release: string
  firmware: string
  burnFailed: boolean
}

export type AgentSnapshot = {
  id: AgentId
  installed: boolean
  signedIn: boolean
  hooks: boolean
  statusLine: boolean
  reachable: boolean
  detail: string
}

export type ModeFile = { name: string; file: string; errors: string[] }

export type BurnRow = { serial: string; imageHash: string; at: string }

export type Snapshot = {
  version: string
  device: DeviceSnapshot
  mode: DeckMode
  brightness: number
  keepalive: boolean
  autoBurn: boolean
  startAtLogin: boolean
  agents: AgentSnapshot[]
  favorites: { 'claude-code': string[]; codex: string[]; opencode: string[] }
  efforts: { 'claude-code': string[]; codex: string[]; opencode: string[] }
  modes: ModeFile[]
  example: string
  burned: BurnRow[]
  preburned: boolean
  burnMessage: string
  welcomePng: string
  tiles: string[]
  wizard: { step: number; open: boolean; notes: string[] } | null
  knobsCalibrated: boolean
  accessibility: boolean
  updateVersion: string | null
  log: string
  modelNamesUpper: boolean
}

export type IpcCall =
  | { method: 'snapshot' }
  | { method: 'brightness'; value: number }
  | { method: 'keepalive'; value: boolean }
  | { method: 'autoBurn'; value: boolean }
  | { method: 'login'; value: boolean }
  | { method: 'testPattern' }
  | { method: 'connect'; id: AgentId }
  | { method: 'disconnect'; id: AgentId }
  | { method: 'restore'; id: AgentId }
  | { method: 'favorites'; agent: 'claude-code' | 'codex' | 'opencode'; models: string[] }
  | { method: 'reloadModes' }
  | { method: 'openModes' }
  | { method: 'burn' }
  | { method: 'exportWelcome' }
  | { method: 'checkUpdates' }
  | { method: 'updateNow' }
  | { method: 'showLog' }
  | { method: 'wizard'; step: number; skip?: boolean }
  | { method: 'wizardAsk' }
  | { method: 'wizardKnobs' }
  | { method: 'simulator'; event: { type: string; key?: number; which?: string; action?: string; pressed?: boolean } }
  | { method: 'modeExample' }

export type SimulatorEvent = { type: 'key'; key: number } | { type: 'metal'; which: 'left' | 'middle' | 'right'; pressed: boolean } | { type: 'knob'; which: 'main' | 'left' | 'right'; action: 'cw' | 'ccw' | 'click' }

export type { KnobMap }
