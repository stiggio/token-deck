import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const version = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8')).version
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8')
const inline = (file) => read(file).replace(/<\?xml[^>]*>/, '').replace(/<!DOCTYPE[^>]*>/, '')

const fonts = {
  buch: 'https://cdn.prod.website-files.com/6a2ff0758d0f9f6abcd082f0/6a2ff738fe0dab30dc7d8faa_soehne-buch.woff2',
  leicht: 'https://cdn.prod.website-files.com/6a2ff0758d0f9f6abcd082f0/6a2ff738fe713781beb04518_soehne-leicht.woff2',
  mono: 'https://cdn.prod.website-files.com/6a2ff0758d0f9f6abcd082f0/6a2ff7385d9084e037c340d7_soehne-mono-buch.woff2',
  monoLight: 'https://cdn.prod.website-files.com/6a2ff0758d0f9f6abcd082f0/6a2ff738aaffb29b8ccee03b_soehne-mono-leicht.woff2'
}

const screens = [
  ['14.7', '12.2'],
  ['33.5', '12.2'],
  ['52.3', '12.2'],
  ['14.7', '30.7'],
  ['33.5', '30.7'],
  ['52.3', '30.7']
].map(([x, y], index) => `<img class="tile" style="left:${(Number(x) / 129) * 100}%;top:${(Number(y) / 78) * 100}%;width:${(16 / 129) * 100}%;height:${(15.5 / 78) * 100}%" src="tiles/key${index + 1}.png" alt="">`).join('\n')

const example = `{
  "name": "Deploy",
  "tiles": [
    { "label": "BUILD", "icon": "~/icons/hammer.svg", "action": { "type": "shell", "command": "npm run build", "cwd": "~/dev/app" } },
    { "label": "LOGS", "action": { "type": "url", "url": "https://grafana.example.com/d/abc" } },
    { "label": "EDITOR", "action": { "type": "open", "app": "Cursor" } },
    { "label": "PALETTE", "action": { "type": "keys", "keys": "cmd+shift+p" } },
    { "label": "AGENTS", "action": { "type": "mode", "mode": "agents" } },
    null
  ],
  "knobs": {
    "main": { "cw": { "type": "keys", "keys": "cmd+=" }, "ccw": { "type": "keys", "keys": "cmd+-" }, "click": { "type": "shell", "command": "say done" } },
    "left": null,
    "right": null
  }
}`

const html = `<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Token Deck</title>
<link rel="icon" href="data:image/svg+xml,${encodeURIComponent(read('brand-kit/brand/stigg-mark-white.svg'))}">
<style>
@font-face { font-family: "Soehne Buch"; src: url("${fonts.buch}") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Soehne Leicht"; src: url("${fonts.leicht}") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Soehne Mono Buch"; src: url("${fonts.mono}") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Soehne Mono Leicht"; src: url("${fonts.monoLight}") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: Geist; src: url("fonts/Geist-Regular.woff2") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Geist Mono"; src: url("fonts/GeistMono-Regular.woff2") format("woff2"); font-weight: 400; font-display: swap; }
:root { color-scheme: dark; --bg:#131512; --ink:#fff; --muted:#9ea19d; --dim:#838682; --line:#3c3e3a; --lime:#92e759; }
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--bg); color: var(--ink); }
body { font-family: "Soehne Buch", Geist, sans-serif; font-weight: 400; font-synthesis: none; }
h1, h2, h3, strong, b { font-weight: 400; }
a { color: inherit; }
.wrap { width: min(960px, calc(100% - 48px)); margin: 0 auto; }
.eyebrow { font-family: "Soehne Mono Buch", "Geist Mono", monospace; font-size: 12px; letter-spacing: .03em; text-transform: uppercase; color: var(--lime); }
.eyebrow::before { content: ""; display: inline-block; width: 6px; height: 6px; background: var(--lime); margin-right: 8px; vertical-align: 1px; }
.hero { padding: 72px 0 32px; border-bottom: 1px solid var(--line); }
.lockup svg { width: min(420px, 100%); height: auto; }
.tag { font-family: "Soehne Leicht", Geist, sans-serif; font-size: 22px; margin: 18px 0 28px; }
.installs { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
@media (max-width: 800px) { .installs { grid-template-columns: 1fr; } }
.cmd { display: flex; gap: 8px; align-items: stretch; }
.cmd code, .note, pre { font-family: "Soehne Mono Buch", "Geist Mono", monospace; font-size: 13px; }
.cmd code { display: block; border: 1px solid var(--line); border-radius: 4px; padding: 12px; overflow: auto; flex: 1; }
.btn { height: 44px; padding: 0 16px; border-radius: 4px; border: 1px solid transparent; background: #fff; color: #131512; font-family: inherit; font-size: 16px; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; }
.btn:hover { background: var(--lime); }
.plain { color: var(--muted); line-height: 1.5; }
.device { position: relative; margin: 48px 0 8px; }
.device svg { width: 100%; height: auto; display: block; }
.device svg [stroke] { stroke-width: 1px; vector-effect: non-scaling-stroke; }
.tile { position: absolute; image-rendering: pixelated; object-fit: fill; }
.block { padding: 48px 0; border-bottom: 1px solid var(--line); display: grid; grid-template-columns: 1fr 1fr; gap: 32px; align-items: center; }
@media (max-width: 800px) { .block { grid-template-columns: 1fr; } }
.block svg { width: 100%; height: auto; }
.legend { font-family: "Soehne Mono Buch", "Geist Mono", monospace; font-size: 13px; color: var(--muted); line-height: 1.7; }
pre { border: 1px solid var(--line); border-radius: 8px; padding: 16px; overflow: auto; color: var(--muted); }
footer { padding: 40px 0 64px; display: flex; justify-content: space-between; gap: 24px; flex-wrap: wrap; }
.mono { font-family: "Soehne Mono Buch", "Geist Mono", monospace; letter-spacing: .03em; }
.version { color: var(--dim); font-family: "Soehne Mono Buch", "Geist Mono", monospace; font-size: 12px; }
</style>
</head>
<body>
<main class="wrap">
  <header class="hero">
    <div class="lockup">${inline('brand-kit/design/token-deck-d-stacked-pixel-token.svg')}</div>
    <p class="tag">The AI Usage Management Console</p>
    <div class="installs">
      <div>
        <p class="eyebrow">Mac</p>
        <div class="cmd">
          <code id="cmd">/bin/bash -c "$(curl -fsSL https://usage.stigg.io/install.sh)"</code>
          <button class="btn" id="copy" type="button">Copy</button>
        </div>
        <p class="plain">Paste it in Terminal. It picks the build for your Mac (Apple Silicon or Intel), checks it and puts Token Deck in Applications. Read the script first: <a href="https://usage.stigg.io/install.sh">usage.stigg.io/install.sh</a></p>
      </div>
      <div>
        <p class="eyebrow">Windows</p>
        <p><a class="btn" href="https://github.com/stiggio/token-deck/releases/latest/download/TokenDeck-win-x64.exe">Download for Windows</a></p>
      </div>
    </div>
    <p class="plain">Other downloads: <a id="arm" href="https://github.com/stiggio/token-deck/releases/latest/download/TokenDeck-mac-arm64.dmg">Mac (Apple Silicon)</a> · <a id="intel" href="https://github.com/stiggio/token-deck/releases/latest/download/TokenDeck-mac-x64.dmg">Mac (Intel)</a> · <a href="https://github.com/stiggio/token-deck/releases">All releases</a></p>
    <p class="plain">Not sure which Mac? Apple menu → About This Mac shows an Apple chip or an Intel processor.</p>
    <p class="plain">macOS will refuse to open Token Deck because it is not notarized (on macOS 15 and later Control-click → Open no longer works, and an unsigned build may be reported as 'damaged'). In Terminal run: <span class="mono">xattr -d com.apple.quarantine "/Applications/Token Deck.app"</span> and open it again, or use the install command above. If System Settings → Privacy &amp; Security shows an Open Anyway button for Token Deck, that works too.</p>
    <p class="version">Version ${version}</p>
    <div class="device">
      ${inline('brand-kit/design/n3-line.svg')}
      ${screens}
    </div>
  </header>
  <section class="block">
    <div>
      <p class="eyebrow">Agents</p>
      <h2>Jump to any coding agent. Turn the dial to hop windows.</h2>
    </div>
    ${inline('brand-kit/design/screens-v2/screens-mode1.svg')}
  </section>
  <section class="block">
    <div>
      <p class="eyebrow">Sessions</p>
      <h2>Every session and its context. See which one needs you.</h2>
    </div>
    ${inline('brand-kit/design/screens-v2/screens-mode2.svg')}
  </section>
  <section class="block">
    <div>
      <p class="eyebrow">Models &amp; usage</p>
      <h2>Six models, live 5H and 7D limits.</h2>
      <div class="legend">
        <div>Turn: effort. Press: Ultracode.</div>
        <div>Turn: agent. Press: last agent.</div>
        <div>Turn: permission. Press: apply.</div>
        <div>Select the mode, one per button.</div>
      </div>
    </div>
    ${inline('brand-kit/design/screens-v2/screens-mode3.svg')}
  </section>
  <section class="block">
    <div>
      <p class="eyebrow">Program it yourself</p>
      <h2>Write your own modes for any screen, button or knob.</h2>
      <pre>${example.replace(/</g, '&lt;')}</pre>
    </div>
    ${inline('brand-kit/design/program-window.svg')}
  </section>
  <section class="block">
    <div>
      <p class="eyebrow">Setup</p>
      <p class="plain">Quit the StreamDock or VSD Craft app before Token Deck opens the deck. macOS asks for Automation, once per app, and for Accessibility, so a tile press can bring that window to the front. The install command does not need the quarantine note above. On Windows, SmartScreen says "Windows protected your PC": choose More info, then Run anyway.</p>
    </div>
  </section>
  <footer>
    <div>
      <canvas id="after" width="320" height="80"></canvas>
      <p class="mono">Nov 10, 2026 · Terra, San Francisco</p>
      <p>by Stigg</p>
    </div>
    <p class="mono"><a href="https://github.com/stiggio/token-deck">github.com/stiggio/token-deck</a><br><a href="https://stigg.io">stigg.io</a><br>io.stigg.io/usage</p>
  </footer>
</main>
<script src="pixelmark.js"></script>
<script>
document.getElementById('copy').addEventListener('click', () => navigator.clipboard.writeText(document.getElementById('cmd').textContent))
if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {
  navigator.userAgentData.getHighEntropyValues(['architecture']).then((v) => {
    const id = v.architecture === 'arm' ? 'arm' : 'intel'
    const link = document.getElementById(id)
    if (link) link.insertAdjacentText('beforeend', ' (recommended)')
  }).catch(() => {})
}
if (window.PixelMark) PixelMark.ready().then(() => PixelMark.draw(document.getElementById('after'), { cap: 22, layout: 'inline', rows: 16, dpr: 2, explode: 0.8 }))
</script>
</body>
</html>
`
fs.mkdirSync(path.join(root, 'site/fonts'), { recursive: true })
for (const name of ['Geist-Regular.woff2', 'GeistMono-Regular.woff2', 'Geist-Light.woff2']) {
  fs.copyFileSync(path.join(root, 'brand-kit/brand/geist', name), path.join(root, 'site/fonts', name))
}
fs.copyFileSync(path.join(root, 'brand-kit/design/pixelmark.js'), path.join(root, 'site/pixelmark.js'))
fs.writeFileSync(path.join(root, 'site/index.html'), html)
console.log('site/index.html', html.length)
