import type { ModelPaint, TileSpec } from '../../shared/model'
import { AGENT_ORDER } from '../../shared/model'

const shared = (name: string, current: boolean): ModelPaint => ({
  name,
  current,
  fiveHour: 62,
  sevenDay: 41,
  fiveLabel: '5H',
  sevenLabel: '7D',
  shared: true,
  noQuota: false,
  stale: false
})

export const DEMO_MODELS: ModelPaint[] = [
  shared('Opus', true),
  shared('Sonnet', false),
  shared('Haiku', false),
  shared('Fable', false),
  {
    name: 'Astra',
    current: false,
    fiveHour: 24,
    sevenDay: 58,
    fiveLabel: '5H',
    sevenLabel: '7D',
    shared: false,
    noQuota: false,
    stale: false
  },
  {
    name: 'Grok',
    current: false,
    fiveHour: 9,
    sevenDay: 17,
    fiveLabel: '5H',
    sevenLabel: '7D',
    shared: false,
    noQuota: false,
    stale: false
  }
]

export function demoAgents(): TileSpec[] {
  const active = [4, 0, 3, 0, 0, 0]
  return AGENT_ORDER.map((agent, i) => ({
    kind: 'agents' as const,
    agent,
    active: active[i]!,
    installed: true
  }))
}

export function demoSessions(): TileSpec[] {
  const rows: Array<TileSpec> = [
    { kind: 'session', session: { agent: 'claude-code', title: 'my-app-3f', context: 62, status: 'working' } },
    { kind: 'session', session: { agent: 'cursor', title: 'token-deck', context: 41, status: 'needs-approval' } },
    { kind: 'session', session: { agent: 'codex', title: 'billing', context: 24, status: 'needs-input' } },
    { kind: 'session', session: { agent: 'opencode', title: 'notes', context: 10, status: 'idle' } },
    { kind: 'session', session: { agent: 'amp', title: 'site', context: 80, status: 'completed' } },
    { kind: 'session', session: { agent: 'devin', title: 'offline', context: null, status: 'disconnected' } }
  ]
  return rows
}

export function demoModelTiles(): TileSpec[] {
  return DEMO_MODELS.map((model) => ({ kind: 'model', model }))
}

export function demoIdle(): TileSpec[] {
  return [1, 2, 3, 4, 5, 6].map((key) => (key === 4 ? { kind: 'connect' as const } : { kind: 'welcome' as const }))
}
