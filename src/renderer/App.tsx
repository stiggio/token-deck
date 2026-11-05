import { useEffect, useRef, useState } from 'react'
import { Cable, Cpu, Info, Layers, SlidersHorizontal, Sparkles } from 'lucide-react'
import type { AgentId } from '../shared/model'
import type { Snapshot } from '../shared/ipc'

const PAGES = ['Device', 'Agents', 'Models', 'Modes', 'Burn', 'About'] as const

export function App() {
  const [page, setPage] = useState<(typeof PAGES)[number]>('Device')
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
          {page === 'Device' && <Device snap={snap} />}
          {page === 'Agents' && <Agents snap={snap} />}
          {page === 'Models' && <Models snap={snap} />}
          {page === 'Modes' && <Modes snap={snap} />}
          {page === 'Burn' && <Burn snap={snap} />}
          {page === 'About' && <About snap={snap} />}
        </section>
        <Simulator snap={snap} />
      </main>
      {snap.wizard?.open && <Wizard snap={snap} />}
    </div>
  )
}

function Icon({ name }: { name: (typeof PAGES)[number] }) {
  const props = { size: 16, strokeWidth: 1, absoluteStrokeWidth: true }
  if (name === 'Device') return <Cable {...props} />
  if (name === 'Agents') return <Sparkles {...props} />
  if (name === 'Models') return <SlidersHorizontal {...props} />
  if (name === 'Modes') return <Layers {...props} />
  if (name === 'Burn') return <Cpu {...props} />
  return <Info {...props} />
}

function Device({ snap }: { snap: Snapshot }) {
  return (
    <>
      <p className="eyebrow">Device</p>
      <h1>{snap.device.message}</h1>
      <div className="row"><span>Manufacturer</span><span>{snap.device.manufacturer || '—'}</span></div>
      <div className="row"><span>Product</span><span>{snap.device.product || '—'}</span></div>
      <div className="row"><span>Serial</span><span>{snap.device.serial || '—'}</span></div>
      <div className="row"><span>Release</span><span>{snap.device.release || '—'}</span></div>
      <div className="row"><span>Firmware</span><span>{snap.device.firmware || 'n/a'}</span></div>
      <div className="row">
        <label className="slider">Brightness {snap.brightness}
          <input type="range" min={0} max={100} value={snap.brightness} onChange={(event) => void window.tokenDeck.invoke({ method: 'brightness', value: Number(event.target.value) })} />
        </label>
      </div>
      <div className="row">
        <span>Repaint keepalive</span>
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'keepalive', value: !snap.keepalive })}>{snap.keepalive ? 'On' : 'Off'}</button>
      </div>
      <div className="actions">
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'testPattern' })}>Send test pattern</button>
      </div>
    </>
  )
}

function Agents({ snap }: { snap: Snapshot }) {
  return (
    <>
      <p className="eyebrow">Agents</p>
      <h1>Connect the agents on this computer</h1>
      {snap.agents.map((agent, index) => (
        <div className="row" key={agent.id}>
          <div>
            <strong>{label(agent.id)}</strong>
            <div>{agent.installed ? 'Installed' : 'Not installed'}{agent.signedIn ? ' · signed in' : ''}{agent.hooks ? ' · hooks installed' : ''}{agent.statusLine ? ' · status line chained' : ''}{agent.detail ? ` · ${agent.detail}` : ''}</div>
            {agent.id === 'opencode' && !agent.reachable && <div>Run `opencode serve` to show sessions</div>}
            {!snap.accessibility && agent.id === 'claude-code' && <div>Accessibility permission is missing. Window focus needs it.</div>}
          </div>
          <div className="actions">
            {index === 0 && <button className="btn accent" onClick={() => void window.tokenDeck.invoke({ method: 'connect', id: agent.id })}>Connect</button>}
            {index !== 0 && <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'connect', id: agent.id })}>Connect</button>}
            <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'disconnect', id: agent.id })}>Disconnect</button>
            {(agent.id === 'claude-code' || agent.id === 'codex') && (
              <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'restore', id: agent.id })}>Restore my settings</button>
            )}
          </div>
        </div>
      ))}
      <p>Token Deck adds a status line and hooks to Claude Code so the deck can see your sessions. Here is exactly what changes: a command hook shim and a chained status line. Nothing reads Claude credentials.</p>
    </>
  )
}

function Models({ snap }: { snap: Snapshot }) {
  const agents = ['claude-code', 'codex', 'opencode'] as const
  return (
    <>
      <p className="eyebrow">Models</p>
      <h1>Favorites</h1>
      {agents.map((agent) => (
        <div key={agent} className="row">
          <div>
            <strong>{label(agent)}</strong>
            <div>{snap.favorites[agent].join(', ') || 'None yet'}</div>
            <div>Effort {snap.efforts[agent].join(' ') || 'Not available'}</div>
          </div>
          <div className="actions">
            <button className="btn ghost" onClick={() => move(snap, agent, -1)}>Move up</button>
            <button className="btn ghost" onClick={() => move(snap, agent, 1)}>Move down</button>
          </div>
        </div>
      ))}
      <p>READ plan / read-only. ASK default / workspace-write. AUTO auto / never. FULL bypass / danger-full-access, only after you confirm on this computer.</p>
    </>
  )
}

function move(snap: Snapshot, agent: 'claude-code' | 'codex' | 'opencode', dir: number) {
  const models = [...snap.favorites[agent]]
  if (models.length < 2) return
  const next = models.slice(1).concat(models[0]!)
  const ordered = dir < 0 ? models.slice(-1).concat(models.slice(0, -1)) : next
  void window.tokenDeck.invoke({ method: 'favorites', agent, models: ordered })
}

function Modes({ snap }: { snap: Snapshot }) {
  return (
    <>
      <p className="eyebrow">Modes</p>
      <h1>Program it yourself</h1>
      {snap.modes.map((mode) => (
        <div className="row" key={mode.file}>
          <div>
            <strong>{mode.name}</strong>
            {mode.errors.map((error) => <div className="warn" key={error}>{error}</div>)}
          </div>
        </div>
      ))}
      {!snap.modes.length && <p>No files in ~/.tokendeck/modes yet.</p>}
      <div className="actions">
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'openModes' })}>Open folder</button>
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'reloadModes' })}>Reload</button>
      </div>
      <pre>{snap.example}</pre>
    </>
  )
}

function Burn({ snap }: { snap: Snapshot }) {
  return (
    <>
      <p className="eyebrow">Burn</p>
      <h1>Welcome screen</h1>
      <p>Token Deck writes its welcome screen into a deck's memory the first time the deck connects to this computer, unless the deck already has it (the giveaway decks come with it). The deck shows that screen whenever it has power and no app is driving it, on any computer. The button below writes it again.</p>
      {snap.welcomePng && <img src={snap.welcomePng} alt="Welcome screen" width={320} height={240} />}
      {snap.burnMessage && <p className="warn">{snap.burnMessage}</p>}
      <div className="row">
        <span>Write the welcome screen to new decks automatically</span>
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'autoBurn', value: !snap.autoBurn })}>{snap.autoBurn ? 'On' : 'Off'}</button>
      </div>
      <div className="actions">
        <button className="btn accent" disabled={snap.device.phase === 'burning' || snap.device.burnFailed} onClick={() => void window.tokenDeck.invoke({ method: 'burn' })}>Write welcome screen to deck</button>
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'exportWelcome' })}>Export image</button>
      </div>
      <p>This deck is {snap.preburned ? 'listed' : 'not listed'} in the shipped giveaway record.</p>
      {snap.burned.map((row) => <div className="row" key={row.serial + row.at}><span>{row.serial}</span><span>{row.at} · {row.imageHash.slice(0, 12)}</span></div>)}
      <p>Batch: quit Token Deck and the vendor apps, then run the packaged binary with `burn --watch`. It waits 8 seconds, prints the deck identity, and says done only after the 10 second hold.</p>
    </>
  )
}

function About({ snap }: { snap: Snapshot }) {
  return (
    <>
      <p className="eyebrow">About</p>
      <h1>Token Deck {snap.version}</h1>
      <div className="actions">
        <button className="btn primary" onClick={() => void window.tokenDeck.invoke({ method: 'checkUpdates' })}>Check for updates</button>
        {snap.updateVersion && <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'updateNow' })}>Update now</button>}
        <button className="btn ghost" onClick={() => void window.tokenDeck.invoke({ method: 'showLog' })}>Show log</button>
      </div>
      {snap.updateVersion && <p>Token Deck {snap.updateVersion} is available.</p>}
      <p><a href="https://usage.stigg.io">usage.stigg.io</a> · <a href="https://github.com/stiggio/token-deck">repository</a></p>
      <p>MIT for the app. Geist is OFL. Agent marks belong to their owners and are used only to name the integrations. The HID protocol notes are from public vendor material.</p>
      <pre>{snap.log}</pre>
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
      const metal: Record<string, 'left' | 'middle' | 'right'> = { q: 'left', w: 'middle', e: 'right' }
      if (metal[event.key]) {
        void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'metal', which: metal[event.key], pressed: true } })
        window.setTimeout(() => void window.tokenDeck.invoke({ method: 'simulator', event: { type: 'metal', which: metal[event.key], pressed: false } }), event.shiftKey ? 900 : 100)
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
      <p className="hint">Keys 1–6 · Q W E metal · arrows main and left knobs · comma period right knob · enter click</p>
    </div>
  )
}

function Wizard({ snap }: { snap: Snapshot }) {
  const step = snap.wizard?.step || 0
  const next = () => void window.tokenDeck.invoke({ method: 'wizard', step: step + 1 })
  const copy = [
    'Plug in your Token Deck.',
    'Turn the left knob clockwise.',
    'Token Deck adds a status line and hooks to Claude Code so the deck can see your sessions. Here is exactly what changes:',
    'Token Deck brings the window of the session you pick to the front. macOS asks you to allow that once for each app, and once in Privacy & Security → Accessibility.',
    'Codex and OpenCode are optional.',
    'Start Token Deck at login?'
  ][Math.min(step, 5)]
  return (
    <div className="wizard">
      <div className="card">
        <p className="eyebrow">Setup</p>
        <h1>{copy}</h1>
        {step === 1 && <p>Now the right knob. Click the left knob.</p>}
        {step === 0 && snap.device.phase === 'burning' && <p>Writing the welcome screen to this deck. Keep it plugged in.</p>}
        {step === 0 && snap.device.message.startsWith('Deck connected') && <p>Done. The deck shows this screen whenever no app is driving it.</p>}
        <div className="actions">
          {step === 2 && <button className="btn accent" onClick={() => void window.tokenDeck.invoke({ method: 'connect', id: 'claude-code' })}>Install</button>}
          {step === 3 && <button className="btn accent" onClick={() => void window.tokenDeck.invoke({ method: 'wizardAsk' })}>Ask now</button>}
          {step === 5 && <button className="btn primary" onClick={() => void window.tokenDeck.invoke({ method: 'login', value: true })}>Start at login</button>}
          <button className="btn ghost" onClick={next}>{step >= 5 ? 'Done' : 'Continue'}</button>
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
