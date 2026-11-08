import { useEffect, useRef, useState } from 'react'
import { Info, LayoutGrid, Monitor, SlidersHorizontal } from 'lucide-react'
import type { AgentId } from '../shared/model'
import type { Snapshot } from '../shared/ipc'

const PAGES = ['Deck', 'This Mac', 'Models', 'About'] as const

export function App() {
  const [page, setPage] = useState<(typeof PAGES)[number]>('Deck')
  const [snap, setSnap] = useState<Snapshot | null>(null)
  useEffect(() => {
    const off = window.tokenDeck.onState(setSnap)
    void window.tokenDeck.invoke({ method: 'snapshot' }).then((value) => {
      if (value && typeof value === 'object') setSnap(value as Snapshot)
    })
    return off
  }, [])
  if (!snap) return null
  return (
    <div className="shell">
      <nav>
        {PAGES.map((item) => (
          <button key={item} className={page === item ? 'active' : ''} onClick={() => setPage(item)}>
            <Icon name={item} /> {item}
          </button>
        ))}
      </nav>
      <main>
        <section className="page">
          {page === 'Deck' && <Deck snap={snap} />}
          {page === 'This Mac' && <ThisMac snap={snap} />}
          {page === 'Models' && <Models snap={snap} />}
          {page === 'About' && <About snap={snap} />}
        </section>
        <Simulator snap={snap} />
      </main>
      {snap.wizard?.open && <Wizard snap={snap} />}
      {snap.usageOpen && <UsagePopup snap={snap} />}
    </div>
  )
}

function Icon({ name }: { name: (typeof PAGES)[number] }) {
  const props = { size: 16, strokeWidth: 1, absoluteStrokeWidth: true }
  if (name === 'Deck') return <LayoutGrid {...props} />
  if (name === 'This Mac') return <Monitor {...props} />
  if (name === 'Models') return <SlidersHorizontal {...props} />
  return <Info {...props} />
}

function Deck({ snap }: { snap: Snapshot }) {
  const mode = snap.mode === 'sessions' || snap.mode === 'models' ? snap.mode : 'agents'
  return (
    <div className="guide">
      <div className="guide-head">
        <div>
          <h1>{GUIDE[mode].title}</h1>
          <p className="blurb">{GUIDE[mode].blurb}</p>
        </div>
        <span className={snap.device.phase === 'ready' ? 'live' : ''}>{snap.device.message}</span>
      </div>
      <DeckMap mode={mode} onMode={selectMode} />
      <div className="guide-foot">
        <span>Hold the middle button for a screen of your own.</span>
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'openModes' })}>Open folder</button>
      </div>
      {snap.modes.some((item) => item.errors.length > 0) && snap.modes.map((item) => item.errors.map((error) => <div className="warn" key={item.file + error}>{item.name}: {error}</div>))}
    </div>
  )
}

const GUIDE = {
  agents: {
    title: 'Agents',
    blurb: 'The coding apps on this computer. Open one, move to one that is already running, and set what the next session will use.',
    left: 'Set model',
    main: 'Switch app',
    right: 'Set effort',
    keys: 'Open app'
  },
  sessions: {
    title: 'Sessions',
    blurb: 'The chats already going. See which Claude Code or Codex conversation needs you, and jump to it.',
    left: 'Pick app',
    main: 'More chats',
    right: 'Pick status',
    keys: 'Open chat'
  },
  models: {
    title: 'Models & usage',
    blurb: 'Pick the model the next session will use. The first key is the shared allowance. Press it to open the details.',
    left: 'Pick app',
    main: 'Set effort',
    right: 'Ask first',
    keys: 'Usage, models'
  }
} as const

function selectMode(which: 'left' | 'middle' | 'right') {
  void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'metal', which, pressed: true } })
  window.setTimeout(() => void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'metal', which, pressed: false } }), 80)
}

const SCREENS = [
  [14.7, 12.2], [33.5, 12.2], [52.3, 12.2],
  [14.7, 30.7], [33.5, 30.7], [52.3, 30.7]
] as const

const FACE_BUTTONS = [
  { which: 'left' as const, cx: 22.7, label: 'Agents', mode: 'agents' },
  { which: 'middle' as const, cx: 41.5, label: 'Sessions', mode: 'sessions' },
  { which: 'right' as const, cx: 60.3, label: 'Models', mode: 'models' }
]

function DeckMap({ mode, onMode }: { mode: keyof typeof GUIDE; onMode: (which: 'left' | 'middle' | 'right') => void }) {
  const cap = GUIDE[mode]
  return (
    <svg className="guide-svg" viewBox="-62 -18 214 132" role="img" aria-label={`${cap.title}. Six keys ${cap.keys}. Large knob ${cap.main}. Left small knob ${cap.left}. Right small knob ${cap.right}.`}>
      <rect x="0" y="0" width="129" height="78" rx="3.9" fill="#1a1c19" stroke="#3c3e3a" strokeWidth="0.4" />
      {SCREENS.map(([x, y]) => (
        <rect key={`${x}-${y}`} x={x} y={y} width="16" height="15.5" rx="1" fill="#131512" stroke="#3c3e3a" strokeWidth="0.35" />
      ))}
      <circle cx="96.1" cy="26.7" r="14.5" fill="#131512" stroke="#92e759" strokeWidth="0.45" />
      <circle cx="96.1" cy="26.7" r="11" fill="none" stroke="#3c3e3a" strokeWidth="0.3" />
      <circle cx="85" cy="59.1" r="7.5" fill="#131512" stroke="#92e759" strokeWidth="0.45" />
      <circle cx="110.6" cy="59.1" r="7.5" fill="#131512" stroke="#92e759" strokeWidth="0.45" />
      <FaceLead x1={-6} y1={24} x2={14.7} y2={20} text={cap.keys} anchor="end" />
      <FaceLead x1={96.1} y1={-8} x2={96.1} y2={12.2} text={cap.main} anchor="middle" />
      <FaceLead x1={85} y1={104} x2={85} y2={66.6} text={cap.left} anchor="middle" />
      <FaceLead x1={110.6} y1={104} x2={110.6} y2={66.6} text={cap.right} anchor="middle" />
      {FACE_BUTTONS.map((button) => {
        const on = mode === button.mode
        return (
          <g key={button.which} className="hit" onClick={() => onMode(button.which)}>
            <circle cx={button.cx} cy="62.9" r="6.3" fill={on ? '#92e759' : '#131512'} stroke={on ? '#92e759' : '#5b5d59'} strokeWidth="0.4" />
            <text x={button.cx} y="88" textAnchor="middle" fill={on ? '#92e759' : '#ffffff'} fontSize="3.6">{button.label}</text>
          </g>
        )
      })}
    </svg>
  )
}

function FaceLead({ x1, y1, x2, y2, text, anchor }: { x1: number; y1: number; x2: number; y2: number; text: string; anchor: 'start' | 'middle' | 'end' }) {
  const labelX = anchor === 'middle' ? x1 : anchor === 'end' ? x1 - 2 : x1 + 2
  const labelY = anchor === 'middle' ? (y1 < y2 ? y1 - 1.5 : y1 + 1.2) : y1 + 1
  return (
    <g>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#92e759" strokeWidth="0.4" />
      <circle cx={x2} cy={y2} r="0.9" fill="#92e759" />
      <text x={labelX} y={labelY} textAnchor={anchor} fill="#ffffff" fontSize="3.8">{text}</text>
    </g>
  )
}

function ThisMac({ snap }: { snap: Snapshot }) {
  return (
    <>
      <h1>This Mac</h1>
      {snap.agents.map((agent) => (
        <div className="row" key={agent.id}>
          <div>
            <strong>{label(agent.id)}</strong>
            <div>{macLine(agent)}</div>
          </div>
          {agent.id === 'claude-code' && agent.installed && (
            <div className="actions">
              {agent.hooks
                ? <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'restore', id: 'claude-code' })}>Stop watching</button>
                : <button className="btn accent" onClick={() => void window.tokenDeck.invoke({ method: 'connect', id: 'claude-code' })}>Let Token Deck see Claude sessions</button>}
            </div>
          )}
        </div>
      ))}
      {!snap.accessibility && (
        <>
          <p>To bring a window to the front, macOS needs Accessibility for Token Deck. It asks once.</p>
          <div className="actions">
            <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'wizardAsk' })}>Allow Accessibility</button>
          </div>
        </>
      )}
    </>
  )
}

function macLine(agent: Snapshot['agents'][number]): string {
  if (agent.id === 'devin') return 'Opens in the browser'
  if (!agent.installed) return 'Not installed'
  if (agent.id === 'claude-code') return agent.hooks ? 'Watching sessions' : 'Not watching sessions'
  if (agent.id === 'codex') return agent.signedIn ? 'Signed in' : 'Sign in to Codex on this Mac'
  if (agent.id === 'opencode') return agent.reachable ? 'Sessions showing' : 'Run opencode serve'
  return 'Opens from its key'
}

function Models({ snap }: { snap: Snapshot }) {
  const agents = (['claude-code', 'codex', 'opencode'] as const).filter((id) => snap.agents.find((agent) => agent.id === id)?.installed)
  return (
    <>
      <h1>Next session</h1>
      {!agents.length && <p>Claude Code, Codex, and OpenCode are not installed.</p>}
      {agents.map((agent) => (
        <div key={agent} className="models-block">
          <strong>{label(agent)}</strong>
          {!snap.favorites[agent].length && <p>Waiting for models</p>}
          <ol className="model-list">
            {snap.favorites[agent].map((name, index, list) => (
              <li key={name}>
                <span className="chip">{name}</span>
                <span className="actions">
                  <button className="btn ghost" disabled={index === 0} onClick={() => move(snap, agent, index, -1)}>Move up</button>
                  <button className="btn ghost" disabled={index === list.length - 1} onClick={() => move(snap, agent, index, 1)}>Move down</button>
                </span>
              </li>
            ))}
          </ol>
        </div>
      ))}
    </>
  )
}

/** Moves one model up or down the list; the deck shows the first five after the usage key. */
function move(snap: Snapshot, agent: 'claude-code' | 'codex' | 'opencode', index: number, dir: -1 | 1) {
  const models = [...snap.favorites[agent]]
  const target = index + dir
  if (target < 0 || target >= models.length) return
  ;[models[index], models[target]] = [models[target]!, models[index]!]
  void window.tokenDeck.invoke({ method: 'favorites', agent, models })
}

function About({ snap }: { snap: Snapshot }) {
  return (
    <>
      <h1>Token Deck {snap.version}</h1>
      <div className="row">
        <label className="slider">Brightness {snap.brightness}
          <input type="range" min={0} max={100} value={snap.brightness} onChange={(event) => void window.tokenDeck.invoke({ method: 'brightness', value: Number(event.target.value) })} />
        </label>
      </div>
      <div className="actions">
        <button className="btn primary" onClick={() => void window.tokenDeck.invoke({ method: 'checkUpdates' })}>Check for updates</button>
        {snap.updateVersion && <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'updateNow' })}>Update now</button>}
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'showLog' })}>Show log</button>
      </div>
      {snap.updateVersion && <p>Token Deck {snap.updateVersion} is available.</p>}
      <h2>Welcome screen</h2>
      <p>Shown when the deck has power and Token Deck is not running.</p>
      {snap.welcomePng && <img src={snap.welcomePng} alt="Welcome screen" width={320} height={240} />}
      {snap.burnMessage && <p className="warn">{snap.burnMessage}</p>}
      <div className="row">
        <span>Open Token Deck when you log in</span>
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'login', value: !snap.startAtLogin })}>{snap.startAtLogin ? 'On' : 'Off'}</button>
      </div>
      <div className="row">
        <span>Write the welcome screen on a new deck</span>
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'autoBurn', value: !snap.autoBurn })}>{snap.autoBurn ? 'On' : 'Off'}</button>
      </div>
      <div className="actions">
        <button className="btn accent" disabled={snap.device.phase === 'burning' || snap.device.burnFailed} onClick={() => void window.tokenDeck.invoke({ method: 'burn' })}>Write welcome screen again</button>
      </div>
      <p><a href="https://usage.stigg.io" target="_blank" rel="noreferrer">usage.stigg.io</a> · <a href="https://github.com/stiggio/token-deck" target="_blank" rel="noreferrer">repository</a></p>
    </>
  )
}

function Simulator({ snap }: { snap: Snapshot }) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return
      const key = Number(event.key)
      if (key >= 1 && key <= 6) void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'key', key } })
      // Shift makes the key upper case, so match it lower case; Shift + W holds the middle button.
      const metal: Record<string, 'left' | 'middle' | 'right'> = { q: 'left', w: 'middle', e: 'right' }
      const which = metal[event.key.toLowerCase()]
      if (which && !event.metaKey && !event.ctrlKey && !event.altKey) {
        void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'metal', which, pressed: true } })
        window.setTimeout(() => void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'metal', which, pressed: false } }), event.shiftKey ? 900 : 100)
      }
      if (event.key === 'ArrowRight') void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'knob', which: 'main', action: 'cw' } })
      if (event.key === 'ArrowLeft') void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'knob', which: 'main', action: 'ccw' } })
      if (event.key === 'ArrowUp') void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'knob', which: 'left', action: 'cw' } })
      if (event.key === 'ArrowDown') void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'knob', which: 'left', action: 'ccw' } })
      if (event.key === ',') void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'knob', which: 'right', action: 'ccw' } })
      if (event.key === '.') void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'knob', which: 'right', action: 'cw' } })
      if (event.key === 'Enter') void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'knob', which: event.altKey ? 'right' : event.shiftKey ? 'left' : 'main', action: 'click' } })
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  return (
    <div className="drawer">
      <div className="deck">
        {snap.tiles.slice(0, 6).map((tile, index) => (
          <button key={index} className="key" onClick={() => void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'key', key: index + 1 } })}>
            {tile && <WireTile jpeg={tile} />}
          </button>
        ))}
      </div>
      <p className="hint">Keys 1–6 · Q W E metal (Shift holds) · arrows main and left knobs · comma period right knob · enter click</p>
    </div>
  )
}

function UsagePopup({ snap }: { snap: Snapshot }) {
  const row = snap.allowance
  const close = () => void window.tokenDeck.invoke({ method: 'usageClose' })
  return (
    <div className="wizard">
      <div className="card">
        <h1>{row.agent}</h1>
        <p>How much of the allowance is already used. Every model of this app shares it.</p>
        <UsageLine name="5-hour window" pct={row.fiveHour} resets={row.fiveResets} />
        <UsageLine name="7-day window" pct={row.sevenDay} resets={row.sevenResets} />
        {!row.known && <p>No reading yet. Claude sends this after one of its sessions replies. Codex sends it from the app on this Mac.</p>}
        <div className="actions">
          <button className="btn primary" onClick={close}>Close</button>
        </div>
      </div>
    </div>
  )
}

function UsageLine({ name, pct, resets }: { name: string; pct: number | null; resets: number | null }) {
  const width = pct === null ? 0 : Math.max(0, Math.min(100, pct))
  const when = resets ? new Date(resets > 1e12 ? resets : resets * 1000).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : ''
  return (
    <div className="usage-line">
      <div className="usage-top"><span>{name}</span><strong>{pct === null ? '--' : `${Math.round(pct)}%`}</strong></div>
      <div className="usage-track"><div className="usage-fill" style={{ width: `${width}%` }} /></div>
      {when && <div className="usage-reset">Resets {when}</div>}
    </div>
  )
}

function Wizard({ snap }: { snap: Snapshot }) {
  const step = snap.wizard?.step || 0
  const next = () => void window.tokenDeck.invoke({ method: 'wizard', step: step + 1 })
  const copy = [
    'The deck is on Agents.',
    'See Claude sessions',
    'Bring the right window forward',
    'Open Token Deck when you log in?'
  ][Math.min(step, 3)]
  return (
    <div className="wizard">
      <div className="card">
        <h1>{copy}</h1>
        {step === 0 && <DeckMap mode="agents" onMode={() => undefined} />}
        {step === 0 && snap.device.phase === 'burning' && <p>Writing the welcome screen. Keep the deck plugged in.</p>}
        {step === 1 && <p>This edits ~/.claude/settings.json and keeps one backup beside it.</p>}
        {step === 2 && <p>macOS asks once, under Privacy &amp; Security, Accessibility.</p>}
        <div className="actions">
          {step === 1 && <button className="btn accent" onClick={() => void window.tokenDeck.invoke({ method: 'connect', id: 'claude-code' })}>Let Token Deck see Claude sessions</button>}
          {step === 2 && <button className="btn accent" onClick={() => void window.tokenDeck.invoke({ method: 'wizardAsk' })}>Allow Accessibility</button>}
          {step === 3 && <button className="btn primary" onClick={() => void window.tokenDeck.invoke({ method: 'login', value: true })}>Start at login</button>}
          <button className="btn ghost" onClick={next}>{step >= 3 ? 'Done' : 'Continue'}</button>
          <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'wizard', step, skip: true })}>Skip</button>
        </div>
      </div>
    </div>
  )
}

function WireTile({ jpeg }: { jpeg: string }) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const image = new Image()
    image.onload = () => {
      const wire = document.createElement('canvas')
      wire.width = 64
      wire.height = 64
      const source = wire.getContext('2d')
      const dest = canvas.getContext('2d')
      if (!source || !dest) return
      source.drawImage(image, 0, 0, 64, 64)
      const pixels = source.getImageData(0, 0, 64, 64)
      const out = dest.createImageData(64, 64)
      for (let y = 0; y < 64; y++) {
        for (let x = 0; x < 64; x++) {
          const si = (x * 64 + (63 - y)) * 4
          const di = (y * 64 + x) * 4
          out.data[di] = pixels.data[si]!
          out.data[di + 1] = pixels.data[si + 1]!
          out.data[di + 2] = pixels.data[si + 2]!
          out.data[di + 3] = 255
        }
      }
      dest.putImageData(out, 0, 0)
    }
    image.src = jpeg
  }, [jpeg])
  return <canvas ref={ref} width={64} height={64} />
}

function label(id: AgentId | string): string {
  if (id === 'claude-code') return 'Claude Code'
  if (id === 'opencode') return 'OpenCode'
  return id[0]!.toUpperCase() + id.slice(1)
}
