import type { DeckEvent } from '../deck/protocol'
import type { SettingsStore } from '../settings/store'
import { renderTile } from '../deck/render'
import { demoAgents, demoModelTiles, demoSessions } from '../deck/demo'
import type { UsageAllowance } from '../../shared/ipc'
import type { AgentId, DeckMode, ModelPaint, PermissionMode, TileSpec } from '../../shared/model'
import { AGENT_ORDER } from '../../shared/model'
import { effortLabel, fitOverlayGroup, splitGroups } from '../../shared/overlays'
import type { ClaudeCode, LiveSession } from '../integrations/claude-code'
import { CLAUDE_EFFORTS, CLAUDE_MODELS } from '../integrations/claude-code'
import type { CodexIntegration } from '../integrations/codex'
import type { OpenCodeIntegration } from '../integrations/opencode'
import type { LaunchOnly } from '../integrations/launch'
import { loadModes, runAction, type CustomMode } from './custom'
import { raiseBundle, runningBundles } from '../system/focus'

const PERMS: PermissionMode[] = ['READ', 'ASK', 'AUTO', 'FULL']

export class Controller {
  mode: DeckMode = 'idle'
  overlay: string[] | null = null
  overlayUntil = 0
  selectedId: string | null = null
  page = 0
  agentFilter: AgentId | 'all' = 'all'
  statusFilter = 'ALL'
  custom: CustomMode | null = null
  picker = false
  permissionPreview = 0
  effortIndex = 2
  modelIndex = 0
  selectedAgent: AgentId = 'claude-code'
  windowIndex = 0
  private hold: NodeJS.Timeout | null = null
  private overlayTimer: NodeJS.Timeout | null = null
  private painting = false
  private pending = false
  ultracodeOn = false

  constructor(
    private readonly store: SettingsStore,
    private readonly claude: ClaudeCode,
    private readonly codex: CodexIntegration,
    private readonly opencode: OpenCodeIntegration,
    private readonly launch: Record<'cursor' | 'amp' | 'devin', LaunchOnly>,
    private readonly paint: (frames: Array<Buffer | null>, force?: boolean) => Promise<void>,
    private readonly log: (line: string) => void,
    private readonly confirmFull: () => Promise<boolean>
  ) {
    const saved = store.get('mode')
    this.mode = saved === 'sessions' || saved === 'models' ? saved : 'agents'
    const installed = this.readableInstalled()
    if (installed.length === 1) {
      this.selectedAgent = installed[0]!
      this.agentFilter = installed[0]!
    } else if (installed.length && !installed.includes(this.selectedAgent)) this.selectedAgent = installed[0]!
  }

  modes(): CustomMode[] {
    return loadModes()
  }

  sessions(): LiveSession[] {
    if (process.env.TOKENDECK_DEMO === '1') return []
    const rows = [...this.claude.sessions.values(), ...this.codex.sessions.values(), ...this.opencode.sessions.values()]
    return rows
      .filter((row) => this.agentFilter === 'all' || row.agent === this.agentFilter)
      .filter((row) => this.statusFilter === 'ALL' || statusGroup(row.status) === this.statusFilter)
      .sort((a, b) => b.updatedAt - a.updatedAt)
  }

  async handle(event: DeckEvent): Promise<void> {
    if (event.type === 'log-report') return
    if (this.overlay && event.type === 'key') return
    if (event.type === 'knob') this.restartOverlay()
    if (event.type === 'metal') return this.metal(event.which, event.pressed)
    if (event.type === 'key') return this.key(event.key)
    if (event.type === 'knob') return this.knob(event.which, event.action)
  }

  private async metal(which: 'left' | 'middle' | 'right', pressed: boolean): Promise<void> {
    if (this.picker && pressed) {
      this.picker = false
      this.custom = null
      this.mode = this.store.get('mode')
      this.flash(this.mode === 'models' ? ['MODELS &', 'USAGE'] : [this.mode.toUpperCase()])
      await this.render(true)
      return
    }
    if (which === 'middle') {
      if (pressed) {
        this.hold = setTimeout(() => {
          this.hold = null
          const modes = this.modes()
          if (modes.length === 0) {
            void this.enter('sessions')
            return
          }
          this.picker = true
          this.mode = 'picker'
          void this.render(true)
        }, 800)
        return
      }
      if (this.hold) {
        clearTimeout(this.hold)
        this.hold = null
        await this.enter('sessions')
      }
      return
    }
    if (!pressed) return
    await this.enter(which === 'left' ? 'agents' : 'models')
  }

  private async enter(mode: 'agents' | 'sessions' | 'models'): Promise<void> {
    this.mode = mode
    this.picker = false
    this.custom = null
    this.store.set('mode', mode)
    this.flash(mode === 'models' ? ['MODELS &', 'USAGE'] : [mode.toUpperCase()], 1000)
    await this.render(true)
  }

  private async key(key: number): Promise<void> {
    if (this.mode === 'idle') {
      this.mode = 'agents'
      this.onConnect?.()
      await this.render(true)
      return
    }
    if (this.picker) {
      const mode = this.modes()[key - 1]
      if (!mode) return
      this.custom = mode
      this.picker = false
      this.mode = 'custom'
      await this.render(true)
      return
    }
    if (this.mode === 'custom' && this.custom) {
      const tile = this.custom.tiles[key - 1]
      const result = await runAction(tile && 'action' in tile ? tile.action : undefined)
      if (result === 'mode' && tile && tile.action && tile.action.type === 'mode') await this.enter(tile.action.mode === 'models' ? 'models' : tile.action.mode)
      else this.flash([result === 'ok' ? 'OK' : 'FAILED'])
      return
    }
    if (this.mode === 'agents') {
      const agent = AGENT_ORDER[key - 1]!
      if (this.readableInstalled().includes(agent)) this.selectedAgent = agent
      const session = this.latest(agent)
      if (session) {
        this.selectedId = session.id
        await this.focus(session)
        return
      }
      if (agent !== 'claude-code' && (await this.appIsOpen(agent))) {
        const bundle = bundleFor(agent)
        if (bundle) {
          try {
            await raiseBundle(bundle)
          } catch {
            this.flash(['FAILED'])
          }
        }
        return
      }
      if (!this.installed(agent)) {
        this.flash(['NOT', 'INSTALLED'])
        return
      }
      await this.launchAgent(agent)
      return
    }
    if (this.mode === 'sessions') {
      const session = this.sessions()[this.page * 6 + key - 1]
      if (!session) return
      this.selectedId = session.id
      this.selectedAgent = session.agent
      await this.focus(session)
      return
    }
    if (this.mode === 'models') {
      const tile = this.modelTiles()[key - 1]
      if (tile?.kind === 'usage') {
        const allowance = this.allowance()
        const five = allowance.fiveHour === null ? '--' : `${Math.round(allowance.fiveHour)}%`
        const seven = allowance.sevenDay === null ? '--' : `${Math.round(allowance.sevenDay)}%`
        this.flash(allowance.known ? [`${allowance.fiveLabel} ${five}`, `${allowance.sevenLabel} ${seven}`] : ['NO', 'READING'])
        this.onUsage?.()
        return
      }
      if (!tile || tile.kind !== 'model' || !tile.model) return
      await this.applyModel(tile.model.name)
    }
  }

  onConnect: (() => void) | null = null
  onUsage: (() => void) | null = null

  private async knob(which: 'main' | 'left' | 'right', action: 'cw' | 'ccw' | 'click'): Promise<void> {
    if (this.mode === 'custom' && this.custom) {
      const knob = this.custom.knobs[which]
      const step = action === 'cw' ? knob?.cw : action === 'ccw' ? knob?.ccw : knob?.click
      const result = await runAction(step)
      this.flash([result === 'failed' ? 'FAILED' : 'OK'])
      return
    }
    if (this.mode === 'idle') return
    if (this.mode === 'agents') return this.agentKnob(which, action)
    if (this.mode === 'sessions') return this.sessionKnob(which, action)
    if (this.mode === 'models') return this.modelKnob(which, action)
  }

  private async agentKnob(which: 'main' | 'left' | 'right', action: 'cw' | 'ccw' | 'click'): Promise<void> {
    if (which === 'main') {
      const open = await this.openTargets()
      if (open.length === 0) {
        this.flash(['NOTHING', 'OPEN'])
        return
      }
      if (action === 'click') this.windowIndex -= 1
      else this.windowIndex += action === 'cw' ? 1 : -1
      const index = wrap(this.windowIndex, open.length)
      this.windowIndex = index
      const target = open[index]!
      try {
        if (target.session) await this.focus(target.session)
        else if (target.bundleId) await raiseBundle(target.bundleId)
      } catch {
        this.flash(['FAILED'])
      }
      return
    }
    const agent = this.configAgent()
    if (!agent) {
      this.flash(['NONE', 'INSTALLED'])
      return
    }
    if (which === 'left') {
      const models = this.modelsFor(agent)
      if (!models.length) return this.flash(['NOT', 'AVAILABLE'])
      if (action === 'click') {
        if (agent === 'claude-code') await this.claude.clearModel()
        this.flash(['NEXT', 'SESSION'])
        return
      }
      this.modelIndex = wrap(this.modelIndex + (action === 'cw' ? 1 : -1), models.length)
      this.selectedAgent = agent
      await this.applyModel(models[this.modelIndex] || models[0]!)
      return
    }
    const levels = this.effortsFor(agent)
    if (!levels.length) return this.flash(['NOT', 'AVAILABLE'])
    this.effortIndex = wrap(this.effortIndex + (action === 'cw' ? 1 : action === 'ccw' ? -1 : 0), levels.length)
    if (action === 'click') this.effortIndex = 0
    this.selectedAgent = agent
    await this.applyEffort(levels[this.effortIndex] || levels[0]!)
  }

  private async sessionKnob(which: 'main' | 'left' | 'right', action: 'cw' | 'ccw' | 'click'): Promise<void> {
    const rows = this.sessions()
    if (which === 'main') {
      const last = Math.max(0, Math.ceil(rows.length / 6) - 1)
      if (action === 'click') {
        const next = rows.find((row) => row.status === 'needs-approval' || row.status === 'needs-input')
        this.page = next ? Math.floor(rows.indexOf(next) / 6) : 0
      } else this.page = Math.min(last, Math.max(0, this.page + (action === 'cw' ? 1 : -1)))
      await this.render(true)
      return
    }
    if (action === 'click') {
      if (which === 'left') {
        const installed = this.readableInstalled()
        if (installed.length === 0) {
          this.flash(['NONE', 'INSTALLED'])
          return
        }
        if (installed.length === 1) {
          this.agentFilter = installed[0]!
          this.flash(['ONLY', shortAgent(installed[0]!)])
          return
        }
        this.agentFilter = 'all'
        this.flash(['ALL'])
      } else this.statusFilter = 'ALL'
    } else if (which === 'left') {
      if (!this.turnInstalledAgent(action)) return
    } else {
      const order = ['ALL', 'WORKING', 'NEEDS YOU', 'IDLE', 'DONE']
      const index = order.indexOf(this.statusFilter)
      this.statusFilter = order[wrap(index + (action === 'cw' ? 1 : -1), order.length)]!
      this.flash(splitGroups(this.statusFilter))
    }
    this.page = 0
    await this.render(true)
  }

  private async modelKnob(which: 'main' | 'left' | 'right', action: 'cw' | 'ccw' | 'click'): Promise<void> {
    if (which === 'left') {
      if (action === 'click') {
        const fromSession = this.selected()?.agent
        if (fromSession && this.readableInstalled().includes(fromSession)) this.selectedAgent = fromSession
      } else if (!this.turnInstalledAgent(action)) return
      this.flash(splitGroups(agentGroup(this.selectedAgent)))
      await this.render(true)
      return
    }
    if (which === 'main') {
      if (action === 'click') {
        if (this.configAgent() !== 'claude-code') return this.flash(['NOT', 'AVAILABLE'])
        this.ultracodeOn = !this.ultracodeOn
        await this.claude.setUltracode(this.ultracodeOn)
        this.flash(['ULTRACODE', this.ultracodeOn ? 'ON' : 'OFF'])
        return
      }
      const levels = this.effortsFor(this.configAgent() || this.selectedAgent)
      if (!levels.length) return this.flash(['NOT', 'AVAILABLE'])
      this.effortIndex = wrap(this.effortIndex + (action === 'cw' ? 1 : -1), levels.length)
      await this.applyEffort(levels[this.effortIndex]!)
      return
    }
    if (action === 'click') {
      const mode = PERMS[this.permissionPreview]!
      if (mode === 'FULL') {
        this.flash(['CONFIRM ON', 'COMPUTER'])
        const ok = await this.confirmFull()
        if (!ok) return
      }
      await this.applyPermission(mode)
      this.flash([mode, 'NEXT', 'SESSION'])
      return
    }
    this.permissionPreview = wrap(this.permissionPreview + (action === 'cw' ? 1 : -1), PERMS.length)
    const mode = PERMS[this.permissionPreview]!
    this.flash(mode === 'ASK' ? ['ASK', 'PRESS TO', 'APPLY'] : [mode, 'PRESS TO', 'APPLY'])
  }

  private async applyModel(name: string): Promise<void> {
    const agent = this.configAgent()
    if (!agent) {
      this.flash(['NONE', 'INSTALLED'])
      return
    }
    try {
      if (agent === 'claude-code') await this.claude.setModel(name)
      else if (agent === 'codex') await this.codex.setModel(name)
      else if (agent === 'opencode') await this.opencode.setModel(name)
      else return this.flash(['NOT', 'AVAILABLE'])
      this.flash([fitOverlayGroup(name), 'NEXT', 'SESSION'])
    } catch {
      this.flash(['NOT', 'AVAILABLE'])
    }
  }

  private async applyEffort(level: string): Promise<void> {
    const agent = this.configAgent()
    if (!agent) {
      this.flash(['NONE', 'INSTALLED'])
      return
    }
    try {
      if (agent === 'codex') await this.codex.setEffort(level)
      else if (agent === 'claude-code') await this.claude.setEffort(level)
      else {
        this.flash(['NOT', 'AVAILABLE'])
        return
      }
      this.flash([effortLabel(level), 'EFFORT'])
    } catch {
      this.flash(['NOT', 'AVAILABLE'])
    }
  }

  private async applyPermission(mode: PermissionMode): Promise<void> {
    const agent = this.selectedAgent
    if (agent === 'codex') await this.codex.setPermission(mode)
    else if (agent === 'opencode') await this.opencode.setPermission(mode)
    else await this.claude.setPermission(mode)
  }

  private flash(groups: string[], ms = 5000): void {
    this.overlay = groups.map((group) => fitOverlayGroup(group))
    this.overlayUntil = Date.now() + ms
    if (this.overlayTimer) clearTimeout(this.overlayTimer)
    this.overlayTimer = setTimeout(() => {
      this.overlay = null
      void this.render(false)
    }, ms)
    void this.render(true)
  }

  private restartOverlay(): void {
    if (!this.overlay) return
    const left = Math.max(1000, this.overlayUntil - Date.now())
    this.overlayUntil = Date.now() + Math.max(left, 5000)
  }

  async render(force = false): Promise<void> {
    if (this.painting) {
      this.pending = true
      return
    }
    this.painting = true
    try {
      const specs = this.specs()
      const groups = this.overlay
      const frames = await Promise.all(
        specs.map((spec, index) => {
          if (spec.kind === 'welcome') return Promise.resolve(null)
          const group = groups && index < 3 ? groups[index] || '' : groups ? '' : null
          return renderTile(spec, index + 1, true, group).then((buf) => buf)
        })
      )
      const resolved = await Promise.all(
        specs.map(async (spec, index) => (spec.kind === 'welcome' ? renderTile(spec, index + 1) : frames[index]!))
      )
      await this.paint(resolved, force)
    } catch (err) {
      this.log(`render ${err}`)
    } finally {
      this.painting = false
      if (this.pending) {
        this.pending = false
        void this.render(false)
      }
    }
  }

  private specs(): TileSpec[] {
    if (process.env.TOKENDECK_DEMO === '1' && this.mode === 'agents') return demoAgents()
    if (process.env.TOKENDECK_DEMO === '1' && this.mode === 'sessions') return demoSessions()
    if (process.env.TOKENDECK_DEMO === '1' && this.mode === 'models') return demoModelTiles()
    if (this.mode === 'idle') return [1, 2, 3, 4, 5, 6].map((key) => (key === 4 ? { kind: 'connect' as const } : { kind: 'welcome' as const }))
    if (this.picker) {
      return [0, 1, 2, 3, 4, 5].map((index) => {
        const mode = this.modes()[index]
        return mode ? { kind: 'custom' as const, custom: { lines: [mode.name] } } : { kind: 'custom' as const, custom: null }
      })
    }
    if (this.mode === 'custom' && this.custom) {
      return this.custom.tiles.map((tile) => ({
        kind: 'custom' as const,
        custom: tile ? { lines: (tile.label || '').split(' '), iconFile: tile.icon?.replace(/^~/, process.env.HOME || '') } : null
      }))
    }
    if (this.mode === 'agents') {
      return AGENT_ORDER.map((agent) => ({
        kind: 'agents' as const,
        agent,
        active: this.count(agent),
        installed: this.installed(agent)
      }))
    }
    if (this.mode === 'sessions') {
      const all = this.sessions()
      const last = Math.max(0, Math.ceil(all.length / 6) - 1)
      if (this.page > last) this.page = last
      const rows = all.slice(this.page * 6, this.page * 6 + 6)
      return [0, 1, 2, 3, 4, 5].map((index) => {
        const row = rows[index]
        return row
          ? { kind: 'session' as const, session: { agent: row.agent, title: row.title, context: row.context, status: row.status } }
          : { kind: 'session' as const, session: null }
      })
    }
    return this.modelTiles()
  }

  allowance(): UsageAllowance {
    const agent = this.configAgent()
    const usage = agent ? this.store.get('usage')[agent] : undefined
    const expired = !usage || Date.now() - usage.at > 24 * 60 * 60 * 1000
    return {
      agent: agent === 'codex' ? 'Codex' : agent === 'opencode' ? 'OpenCode' : 'Claude Code',
      fiveHour: !usage || expired ? null : usage.five?.pct ?? null,
      sevenDay: !usage || expired ? null : usage.seven?.pct ?? null,
      fiveLabel: usage?.labels?.five || '5H',
      sevenLabel: usage?.labels?.seven || '7D',
      fiveResets: usage?.five?.resetsAt ?? null,
      sevenResets: usage?.seven?.resetsAt ?? null,
      known: !!usage && !expired && (usage.five?.pct != null || usage.seven?.pct != null)
    }
  }

  private modelTiles(): TileSpec[] {
    const agent = this.configAgent()
    const allowance = this.allowance()
    const usage: TileSpec = {
      kind: 'usage',
      agent: allowance.agent === 'Claude Code' ? 'CLAUDE' : allowance.agent === 'OpenCode' ? 'OPENCODE' : 'CODEX',
      fiveHour: agent === 'opencode' ? null : allowance.fiveHour,
      sevenDay: agent === 'opencode' ? null : allowance.sevenDay,
      fiveLabel: allowance.fiveLabel,
      sevenLabel: allowance.sevenLabel
    }
    if (!agent) return [usage, ...[0, 1, 2, 3, 4].map(() => ({ kind: 'model' as const, model: null }))]
    const names = this.modelNames(agent).slice(0, 5)
    const current = this.currentModelName(agent)
    const models = [0, 1, 2, 3, 4].map((index) => {
      const name = names[index]
      if (!name) return { kind: 'model' as const, model: null }
      const model: ModelPaint = {
        name: this.store.get('modelNamesUpper') ? name.toUpperCase() : name,
        current: name.toLowerCase() === current.toLowerCase(),
        fiveHour: null,
        sevenDay: null,
        fiveLabel: '5H',
        sevenLabel: '7D',
        shared: false,
        noQuota: agent === 'opencode',
        stale: false
      }
      return { kind: 'model' as const, model }
    })
    return [usage, ...models]
  }

  private modelNames(agent: AgentId): string[] {
    const key = agent === 'claude-code' ? 'claude-code' : agent === 'codex' ? 'codex' : 'opencode'
    const saved = this.store.get('favorites')[key] || []
    if (saved.length) return saved.slice(0, 6)
    if (agent === 'codex') return this.codex.models.slice(0, 6).map((model) => model.name)
    if (agent === 'opencode') return this.opencode.models.slice(0, 6)
    return []
  }

  private currentModelName(agent: AgentId): string {
    if (agent === 'claude-code') return this.claude.displayModel()
    if (agent === 'codex') return this.codex.currentName()
    return this.opencode.models[0] || ''
  }

  private modelsFor(agent: AgentId): string[] {
    if (agent === 'claude-code') {
      const names = this.modelNames(agent)
      return names.length ? names : CLAUDE_MODELS.map((name) => name[0]!.toUpperCase() + name.slice(1))
    }
    if (agent === 'codex') return this.codex.models.map((model) => model.name)
    return this.opencode.models
  }

  private effortsFor(agent: AgentId): string[] {
    if (agent === 'codex') {
      const model = this.codex.models.find((row) => row.isDefault) || this.codex.models[0]
      return model?.efforts || []
    }
    if (agent === 'opencode') return []
    return CLAUDE_EFFORTS
  }

  private count(agent: AgentId): number {
    if (agent === 'claude-code') return [...this.claude.sessions.values()].filter((row) => row.status === 'working').length
    if (agent === 'codex') return [...this.codex.sessions.values()].filter((row) => row.status === 'working').length
    if (agent === 'opencode') return [...this.opencode.sessions.values()].filter((row) => row.status === 'working').length
    return 0
  }

  private installed(agent: AgentId): boolean {
    if (agent === 'claude-code') return !!this.claude.bin || this.claude.desktop
    if (agent === 'codex') return !!this.codex.bin
    if (agent === 'opencode') return !!this.opencode.bin
    if (agent === 'devin') return true
    return this.launch[agent as 'cursor' | 'amp'].installed
  }

  /** Agents whose sessions or model settings Token Deck can read. */
  private readableInstalled(): AgentId[] {
    return (['claude-code', 'codex', 'opencode'] as const).filter((agent) => this.installed(agent))
  }

  private configAgent(): AgentId | null {
    const installed = this.readableInstalled()
    if (installed.includes(this.selectedAgent)) return this.selectedAgent
    return installed[0] || null
  }

  /** Left-knob agent list. One installed agent does not pretend to switch. */
  private turnInstalledAgent(action: 'cw' | 'ccw' | 'click'): boolean {
    const installed = this.readableInstalled()
    if (installed.length === 0) {
      this.flash(['NONE', 'INSTALLED'])
      return false
    }
    if (installed.length === 1) {
      this.selectedAgent = installed[0]!
      this.agentFilter = installed[0]!
      this.flash(['ONLY', shortAgent(installed[0]!)])
      return false
    }
    const order: Array<AgentId | 'all'> = this.mode === 'sessions' ? ['all', ...installed] : installed
    const current = this.mode === 'sessions' ? this.agentFilter : this.selectedAgent
    const index = Math.max(0, order.indexOf(current as AgentId | 'all'))
    const next = order[wrap(index + (action === 'cw' ? 1 : -1), order.length)]!
    if (this.mode === 'sessions') this.agentFilter = next
    else if (next !== 'all') this.selectedAgent = next
    this.flash(next === 'all' ? ['ALL'] : splitGroups(agentGroup(next)))
    return true
  }

  private async appIsOpen(agent: AgentId): Promise<boolean> {
    const bundle = bundleFor(agent)
    if (!bundle) return false
    const running = await runningBundles([bundle])
    return running.includes(bundle)
  }

  private async openTargets(): Promise<Array<{ session?: LiveSession; bundleId?: string }>> {
    const pairs: Array<[string, AgentId]> = [
      ['com.anthropic.claudefordesktop', 'claude-code'],
      ['com.todesktop.230313mzl4w4u92', 'cursor'],
      ['com.openai.codex', 'codex']
    ]
    if (this.launch.amp.installed) pairs.push(['com.microsoft.VSCode', 'amp'])
    const running = new Set(await runningBundles(pairs.map(([id]) => id)))
    const targets: Array<{ session?: LiveSession; bundleId?: string }> = []
    const seen = new Set<AgentId>()
    for (const [id, agent] of pairs) {
      if (!running.has(id)) continue
      const session = this.latest(agent)
      if (session) targets.push({ session })
      else targets.push({ bundleId: id })
      seen.add(agent)
    }
    for (const agent of ['claude-code', 'codex', 'opencode'] as const) {
      if (seen.has(agent)) continue
      const session = this.latest(agent)
      if (session) targets.push({ session })
    }
    return targets
  }

  private latest(agent: AgentId): LiveSession | undefined {
    return [...this.claude.sessions.values(), ...this.codex.sessions.values(), ...this.opencode.sessions.values()]
      .filter((row) => row.agent === agent)
      .sort((a, b) => b.updatedAt - a.updatedAt)[0]
  }

  private selected(): LiveSession | undefined {
    return [...this.claude.sessions.values(), ...this.codex.sessions.values(), ...this.opencode.sessions.values()].find((row) => row.id === this.selectedId)
  }

  private async focus(session: LiveSession): Promise<void> {
    try {
      if (session.agent === 'claude-code') await this.claude.focus(session)
      else if (session.agent === 'codex') await this.codex.focus(session)
      else await this.opencode.focus(session)
    } catch (err) {
      this.log(`focus ${err}`)
      if (session.agent === 'claude-code') await this.claude.launch()
      else this.flash(['FAILED'])
    }
  }

  private async launchAgent(agent: AgentId): Promise<void> {
    if (agent === 'claude-code') await this.claude.launch()
    else if (agent === 'codex') await this.codex.launch()
    else if (agent === 'opencode') await this.opencode.launch()
    else await this.launch[agent].launch()
  }
}

function wrap(index: number, length: number): number {
  if (length <= 0) return 0
  return ((index % length) + length) % length
}

function statusGroup(status: LiveSession['status']): string {
  if (status === 'working') return 'WORKING'
  if (status === 'needs-approval' || status === 'needs-input') return 'NEEDS YOU'
  if (status === 'completed') return 'DONE'
  if (status === 'idle') return 'IDLE'
  return 'ALL'
}

function shortAgent(agent: AgentId): string {
  if (agent === 'claude-code') return 'CLAUDE'
  if (agent === 'opencode') return 'OPENCODE'
  return agent.toUpperCase()
}

function bundleFor(agent: AgentId): string | undefined {
  if (agent === 'claude-code') return 'com.anthropic.claudefordesktop'
  if (agent === 'cursor') return 'com.todesktop.230313mzl4w4u92'
  if (agent === 'amp') return 'com.microsoft.VSCode'
  if (agent === 'codex') return 'com.openai.codex'
  return undefined
}

function agentGroup(agent: AgentId): string {
  if (agent === 'claude-code') return 'CLAUDE | CODE'
  if (agent === 'opencode') return 'OPENCODE'
  return agent.toUpperCase()
}
