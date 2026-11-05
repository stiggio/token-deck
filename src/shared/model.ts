export type AgentId = 'claude-code' | 'cursor' | 'codex' | 'opencode' | 'amp' | 'devin'

export const AGENT_ORDER: AgentId[] = ['claude-code', 'cursor', 'codex', 'opencode', 'amp', 'devin']

export const LAUNCH_ONLY: ReadonlySet<AgentId> = new Set(['cursor', 'amp', 'devin'])

export type SessionStatus = 'working' | 'needs-approval' | 'needs-input' | 'idle' | 'completed' | 'disconnected'

export type SessionPaint = {
  agent: AgentId
  title: string
  context: number | null
  status: SessionStatus
}

export type ModelPaint = {
  name: string
  current: boolean
  fiveHour: number | null
  sevenDay: number | null
  fiveLabel: string
  sevenLabel: string
  shared: boolean
  noQuota: boolean
  stale: boolean
}

export type CustomPaint = {
  lines: string[]
  iconFile?: string
}

export type TileSpec =
  | { kind: 'agents'; agent: AgentId; active: number; installed: boolean }
  | { kind: 'session'; session: SessionPaint | null }
  | { kind: 'model'; model: ModelPaint | null }
  | { kind: 'custom'; custom: CustomPaint | null }
  | { kind: 'welcome' }
  | { kind: 'connect' }
  | { kind: 'test' }

export type DeckMode = 'agents' | 'sessions' | 'models' | 'custom' | 'picker' | 'idle'

export type PermissionMode = 'READ' | 'ASK' | 'AUTO' | 'FULL'
