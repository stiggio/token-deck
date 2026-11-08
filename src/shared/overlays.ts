import { fitText, measure } from '../main/deck/pixelfont'

/** Static overlay groups. Dynamic names go through fitOverlayGroup. */
export const OVERLAY_GROUPS = [
  'HIGH',
  'EFFORT',
  'ULTRACODE',
  'ON',
  'OFF',
  'ASK',
  'PRESS TO',
  'APPLY',
  'READ',
  'AUTO',
  'FULL',
  'NEXT',
  'SESSION',
  'CONFIRM ON',
  'COMPUTER',
  'NOT',
  'AVAILABLE',
  'NO SESSION',
  'APPLIED',
  'FAILED',
  'OK',
  'ALL',
  'WORKING',
  'NEEDS YOU',
  'IDLE',
  'DONE',
  'CLAUDE',
  'CODE',
  'CODEX',
  'OPENCODE',
  'CURSOR',
  'AMP',
  'DEVIN',
  'AGENTS',
  'SESSIONS',
  'MODELS &',
  'USAGE',
  'LOW',
  'MED',
  'XHIGH',
  'SONNET',
  'OPUS',
  'HAIKU',
  'FABLE',
  'CONNECT',
  'ONLY',
  'NONE',
  'INSTALLED',
  'NOTHING',
  'OPEN',
  'DEFAULT',
  'TURN',
  'FIRST',
  'MODE FILE',
  'ERROR'
] as const

export function splitGroups(message: string): string[] {
  return message.split('|').map((s) => s.trim()).filter((s) => s.length > 0)
}

export function fitOverlayGroup(text: string): string {
  const upper = text.toUpperCase() === 'MEDIUM' ? 'MED' : text.toUpperCase()
  return fitText(upper, 58, 10)
}

export function groupOk(text: string): boolean {
  return text.length <= 10 && measure(text) <= 58
}

export function effortLabel(level: string): string {
  const l = level.toLowerCase()
  if (l === 'medium' || l === 'med') return 'MED'
  if (l === 'xhigh' || l === 'x-high' || l === 'extra-high') return 'XHIGH'
  return fitOverlayGroup(level)
}
