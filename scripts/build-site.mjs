/**
 * Builds site/index.html, the download page at usage.stigg.io.
 *
 * Static HTML, site/style.css and site/main.js; no framework and no network calls from the page.
 * Run `npx tsx scripts/export-site-tiles.ts` first: the device drawings use the tiles it renders.
 *
 * Fonts: Söhne is loaded from the URLs stigg.io's own stylesheet serves (they change if marketing
 * re-uploads the fonts in Webflow; Geist, served from this origin, keeps the page readable).
 * No Söhne file is ever committed or deployed (scripts/lint-fonts).
 */
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const version = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8')).version
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8')

const SITE = 'https://usage.stigg.io'
const REPO = 'https://github.com/stiggio/token-deck'
const DOWNLOAD = `${REPO}/releases/latest/download`
const INSTALL = `/bin/bash -c "$(curl -fsSL ${SITE}/install.sh)"`

const fonts = {
  buch: 'https://cdn.prod.website-files.com/6a2ff0758d0f9f6abcd082f0/6a2ff738fe0dab30dc7d8faa_soehne-buch.woff2',
  leicht: 'https://cdn.prod.website-files.com/6a2ff0758d0f9f6abcd082f0/6a2ff738fe713781beb04518_soehne-leicht.woff2',
  mono: 'https://cdn.prod.website-files.com/6a2ff0758d0f9f6abcd082f0/6a2ff7385d9084e037c340d7_soehne-mono-buch.woff2',
  monoLight: 'https://cdn.prod.website-files.com/6a2ff0758d0f9f6abcd082f0/6a2ff738aaffb29b8ccee03b_soehne-mono-leicht.woff2'
}

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

/** An SVG file's markup without its XML prolog, comments and ids, with its root attributes replaced. */
function svg(file, attrs) {
  let text = read(file)
    .replace(/<\?xml[^>]*>/, '')
    .replace(/<!DOCTYPE[^>]*>/, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/(<g\b[^>]*?)\s+id="[^"]*"/g, '$1')
    .replace(/\sdata-screen="[^"]*"/g, '')
    .replace(/<title>[\s\S]*?<\/title>/g, '')
    .trim()
  const viewBox = text.match(/viewBox="([^"]*)"/)[1]
  text = text.replace(/^<svg[^>]*>/, `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" ${attrs}>`)
  return text
}

// ---- The device drawing --------------------------------------------------------------------------
// brand-kit/design/n3-line.svg is the face at 1:1 in millimetres (129 x 78). It is defined once as a
// symbol with 1px non-scaling hairlines, and every drawing on the page uses it.

const n3 = read('brand-kit/design/n3-line.svg')
const n3Body = n3
  .replace(/^[\s\S]*?<svg[^>]*>/, '')
  .replace(/<\/svg>\s*$/, '')
  .replace(/<!--[\s\S]*?-->/g, '')
  .replace(/\s(id)="[^"]*"/g, '')
  .replace(/stroke-width="0\.265"/g, 'stroke-width="1" vector-effect="non-scaling-stroke"')
  .trim()

const KEYS = [
  [14.7, 12.2], [33.5, 12.2], [52.3, 12.2],
  [14.7, 30.7], [33.5, 30.7], [52.3, 30.7]
]
const BUTTONS = { agents: 22.7, sessions: 41.5, models: 60.3 }
const CALLOUTS = { keys: [7, 29.2], main: [96.1, 26.7], left: [85, 59.1], right: [110.6, 59.1], buttons: [7, 62.9] }

const defs = `<svg class="visually-hidden" aria-hidden="true" focusable="false"><defs>
<symbol id="n3" viewBox="0 0 129 78">${n3Body}</symbol>
${KEYS.map(([x, y], i) => `<clipPath id="key-${i + 1}"><rect x="${x}" y="${y}" width="16" height="15.5" rx="1"/></clipPath>`).join('\n')}
</defs></svg>`

function tiles(screen, extra = '') {
  return KEYS.map(([x, y], i) => `<image class="tile" style="--k:${i}" href="tiles/${screen}-${i + 1}.png" x="${(x + 0.25).toFixed(2)}" y="${y}" width="15.5" height="15.5" clip-path="url(#key-${i + 1})" preserveAspectRatio="none"${extra}/>`).join('')
}

function lit(mode) {
  const cx = BUTTONS[mode]
  return `<g class="lit-group" data-for="${mode}"><circle class="lit" cx="${cx}" cy="62.9" r="6.317"/><circle class="lit" cx="${cx}" cy="62.9" r="5.25"/></g>`
}

function callouts(list) {
  return list.map(([n, part]) => {
    const [x, y] = CALLOUTS[part]
    return `<span class="callout" style="left:${((x / 129) * 100).toFixed(2)}%;top:${((y / 78) * 100).toFixed(2)}%" aria-hidden="true">${n}</span>`
  }).join('')
}

/** A static drawing of the deck on one screen. */
function deck(screen, mode, label, marks = []) {
  return `<div class="deck-fig">
<svg class="deck" viewBox="0 0 129 78" role="img" aria-label="${esc(label)}">${tiles(screen)}<use href="#n3" width="129" height="78"/>${mode ? lit(mode) : ''}</svg>
${callouts(marks)}
</div>`
}

const heroLabels = {
  welcome: 'Token Deck before the app runs: the welcome screen with the Stigg logo and io.stigg.io/usage',
  agents: 'Token Deck in Agents mode: keys for Claude Code, Cursor, Codex, OpenCode, Amp and Devin',
  sessions: 'Token Deck in Sessions mode: six live sessions, one of them waiting for approval',
  models: 'Token Deck in Models & Usage mode: the usage key at 62% of the 5-hour limit and 41% of the week, then Opus, Sonnet, Haiku and Fable'
}

const heroDeck = `<svg class="deck" viewBox="0 0 129 78" role="img" aria-label="${esc(heroLabels.sessions)}" ${Object.entries(heroLabels).map(([k, v]) => `data-label-${k}="${esc(v)}"`).join(' ')}>
${['welcome', 'agents', 'sessions', 'models'].map((screen) => `<g class="layer" data-screen="${screen}">${tiles(screen)}</g>`).join('\n')}
<use href="#n3" width="129" height="78"/>
${Object.keys(BUTTONS).map(lit).join('')}
${Object.entries(BUTTONS).map(([mode, cx]) => `<g data-mode-button="${mode}" aria-hidden="true"><title>${mode === 'models' ? 'Models &amp; Usage' : mode[0].toUpperCase() + mode.slice(1)}</title><circle class="hit" cx="${cx}" cy="62.9" r="6.8"/><circle class="ring" cx="${cx}" cy="62.9" r="6.317"/></g>`).join('')}
</svg>`

// ---- Program it yourself ----------------------------------------------------------------------------

const example = `{
  "name": "Deploy",
  "tiles": [
    { "label": "BUILD", "icon": "~/icons/hammer.svg",
      "action": { "type": "shell", "command": "npm run build",
                  "cwd": "~/dev/app" } },
    { "label": "LOGS",
      "action": { "type": "url",
                  "url": "https://grafana.example.com/d/abc" } },
    { "label": "EDITOR",
      "action": { "type": "open", "app": "Cursor" } },
    { "label": "PALETTE",
      "action": { "type": "keys", "keys": "cmd+shift+p" } },
    { "label": "AGENTS",
      "action": { "type": "mode", "mode": "agents" } },
    null
  ],
  "knobs": {
    "main": {
      "cw":    { "type": "keys", "keys": "cmd+=" },
      "ccw":   { "type": "keys", "keys": "cmd+-" },
      "click": { "type": "shell", "command": "say done" }
    },
    "left": null,
    "right": null
  }
}`

// The example must stay valid JSON with the same content as the app's own (src/main/modes/custom.ts).
JSON.parse(example)

function highlight(json) {
  return esc(json).replace(/(&quot;(?:[^&]|&(?!quot;))*?&quot;)(\s*:)?|\b(null|true|false|-?\d+(?:\.\d+)?)\b|([{}[\],])/g, (m, str, colon, lit, punct) => {
    if (str) return colon ? `<span class="k">${str}</span>${colon}` : `<span class="s">${str}</span>`
    if (lit) return `<span class="v">${lit}</span>`
    return `<span class="p">${punct}</span>`
  })
}

// ---- Icons (Lucide, 1px) ------------------------------------------------------------------------------

const icon = {
  copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>',
  download: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 15V3"/><path d="m7 10 5 5 5-5"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/></svg>'
}

// ---- The page -----------------------------------------------------------------------------------------

const description = 'Token Deck is the free app for the deck in your After Tokens box. It puts your Claude Code, Codex and OpenCode sessions on the keys, takes you to the one that needs you, and shows how much of your 5-hour and weekly limits you have used. For macOS and Windows.'

const legend = (rows) => `<dl class="legend">${rows.map(([n, term, text]) => `<div><dt><span class="num" aria-hidden="true">${n}</span>${term}</dt><dd>${text}</dd></div>`).join('')}</dl>`

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Token Deck by Stigg</title>
<meta name="description" content="${esc(description)}">
<meta name="theme-color" content="#131512">
<link rel="canonical" href="${SITE}/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Stigg">
<meta property="og:url" content="${SITE}/">
<meta property="og:title" content="Token Deck">
<meta property="og:description" content="${esc(description)}">
<meta property="og:image" content="${SITE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The Token Deck logo next to a drawing of the deck showing six coding sessions">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="preconnect" href="https://cdn.prod.website-files.com" crossorigin>
<link rel="preload" href="${fonts.buch}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="${fonts.leicht}" as="font" type="font/woff2" crossorigin>
<style>
@font-face { font-family: "Soehne Buch"; src: url("${fonts.buch}") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Soehne Leicht"; src: url("${fonts.leicht}") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Soehne Mono Buch"; src: url("${fonts.mono}") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Soehne Mono Leicht"; src: url("${fonts.monoLight}") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: Geist; src: url("fonts/Geist-Regular.woff2") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Geist Light"; src: url("fonts/Geist-Light.woff2") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Geist Mono"; src: url("fonts/GeistMono-Regular.woff2") format("woff2"); font-weight: 400; font-display: swap; }
</style>
<link rel="stylesheet" href="style.css?v=${version}">
</head>
<body>
<a class="skip" href="#install">Skip to the download</a>
${defs}
<div class="frame">

<header class="top wrap">
  <a class="brand" href="${SITE}/" aria-label="Token Deck by Stigg, home">
    ${svg('brand-kit/brand/stigg-logo-on-dark.svg', 'class="stigg" aria-hidden="true" focusable="false"')}
    <span class="sep" aria-hidden="true"></span>
    <span class="name">Token Deck</span>
  </a>
  <nav class="nav" aria-label="Page">
    <a href="#modes">How it works</a>
    <a href="#program">Your own modes</a>
    <a href="#help">Help</a>
    <a class="ext" href="${REPO}">GitHub</a>
    <a class="btn btn-sm" href="#install">Install</a>
  </nav>
</header>

<main id="main">
<section class="hero wrap rule" aria-labelledby="title">
  <p class="eyebrow">The AI Usage Management Console</p>
  <div class="hero-intro">
    <h1 id="title" class="lockup"><span class="visually-hidden">Token Deck</span>${svg('brand-kit/design/token-deck-d-stacked-pixel-token.svg', 'aria-hidden="true" focusable="false"')}</h1>
    <div class="hero-copy">
      <p class="display">Your coding agents, on six keys and three knobs<span class="dot">.</span></p>
      <p class="lead">Token Deck is the free app for the deck in your After Tokens box. It puts your Claude Code, Codex and OpenCode sessions on the keys, takes you to the one that needs you, and shows how much of your 5&#8209;hour and weekly limits you’ve used.</p>
      <div class="away" hidden>
        <p>Token Deck runs on macOS and Windows. Open <span class="mono">usage.stigg.io</span> on your Mac or PC to install it.</p>
        <button class="btn btn-sm btn-ghost" type="button" data-copy="site-url" aria-label="Copy the link to this page">${icon.copy}${icon.check}<span class="idle">Copy link</span><span class="done">Copied</span></button>
        <span id="site-url" hidden>${SITE}</span>
      </div>
    </div>
  </div>
  <div class="hero-main">
    <div class="install" id="install">
      <h2 class="visually-hidden">Install Token Deck</h2>
      <div class="install-row" data-os-row="mac">
        <div class="install-head">
          <p class="eyebrow">Mac <span class="sub"></span></p>
          <p class="req">macOS 12 or later · Apple silicon and Intel</p>
        </div>
        <div class="cmd">
          <code id="install-cmd">${esc(INSTALL).replace('usage.stigg.io/', 'usage.stigg.io/<wbr>')}</code>
          <button class="copy" type="button" data-copy="install-cmd" aria-label="Copy the install command">${icon.copy}${icon.check}<span class="idle">Copy</span><span class="done">Copied</span></button>
        </div>
        <p class="small">Paste it into Terminal. It downloads the build for your Mac, verifies its SHA-256 checksum and puts Token Deck in Applications. <a class="link" href="${SITE}/install.sh">Read the script</a> before you run it.</p>
      </div>
      <div class="install-row" data-os-row="windows">
        <div class="install-head">
          <p class="eyebrow">Windows <span class="sub"></span></p>
          <p class="req">Windows 10 or 11 · 64-bit</p>
        </div>
        <div class="install-actions">
          <a class="btn" href="${DOWNLOAD}/TokenDeck-win-x64.exe">${icon.download}Download for Windows</a>
          <span class="file">TokenDeck-win-x64.exe</span>
        </div>
        <p class="small">If Windows says it protected your PC, choose More info, then Run anyway. The installer isn’t code-signed yet.</p>
      </div>
      <div class="install-more"><p>Mac disk images: <a id="dmg-arm" href="${DOWNLOAD}/TokenDeck-mac-arm64.dmg">Apple silicon<span class="badge-rec">Your Mac</span></a><span class="sep">·</span><a id="dmg-intel" href="${DOWNLOAD}/TokenDeck-mac-x64.dmg">Intel<span class="badge-rec">Your Mac</span></a><span class="sep">·</span><a href="#damaged">If macOS won’t open one</a></p><a class="ext" href="${REPO}/releases">All releases</a></div>
    </div>
    <figure class="hero-device" data-screen="sessions">
      <div class="deck-fig">${heroDeck}</div>
      <script>if (!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)) document.currentScript.parentNode.setAttribute('data-screen', 'welcome')</script>
      <div class="modes-switch" role="group" aria-label="Show a mode">
        <button type="button" data-show="agents" aria-pressed="false">Agents</button>
        <button type="button" data-show="sessions" aria-pressed="true">Sessions</button>
        <button type="button" data-show="models" aria-pressed="false">Models &amp; Usage</button>
      </div>
      <figcaption class="fig-note">These are the app’s real key images. Pick a mode to switch them.</figcaption>
    </figure>
  </div>
</section>

<section class="section wrap rule" id="modes" aria-labelledby="modes-title">
  <div class="section-head">
    <p class="eyebrow">How it works</p>
    <h2 class="h2" id="modes-title">The metal buttons pick the mode. <span class="dim">The mode sets what the keys show and what the knobs do.</span></h2>
  </div>

  <article class="mode" aria-labelledby="agents-title">
    <div class="mode-head">
      <p class="eyebrow">01 Agents <span class="sub">· Left button</span></p>
      <h3 class="h3" id="agents-title">Jump to any coding agent. <span class="dim">Turn the dial to hop windows.</span></h3>
      <p class="body">Each key is an agent: Claude Code, Cursor and Codex on top; OpenCode, Amp and Devin below. The knobs set the model and effort your next session starts with.</p>
    </div>
    <figure class="mode-fig">${deck('agents', 'agents', heroLabels.agents, [[1, 'keys'], [2, 'main'], [3, 'left'], [4, 'right']])}</figure>
    <div class="mode-legend">
      ${legend([
        [1, 'Keys', '<b>Press:</b> bring that agent’s latest window to the front, or open it. A dim key means the agent isn’t installed.'],
        [2, 'Big knob', '<b>Turn:</b> hop between open agent windows. <b>Press:</b> back to the previous window.'],
        [3, 'Left knob', '<b>Turn:</b> the model your next session starts with.'],
        [4, 'Right knob', '<b>Turn:</b> the effort your next session starts with.']
      ])}
    </div>
  </article>

  <article class="mode" aria-labelledby="sessions-title">
    <div class="mode-head">
      <p class="eyebrow">02 Sessions <span class="sub">· Middle button</span></p>
      <h3 class="h3" id="sessions-title">Every session and its context. <span class="dim">See which one needs you.</span></h3>
      <p class="body">Each key is one recent session from Claude Code, Codex or OpenCode, newest first. The dot says what it’s doing, and the ring shows how full its context window is.</p>
      <ul class="states">
        <li><i style="background:var(--blue)"></i>Working</li>
        <li><i class="framed" style="background:var(--coral)"></i>Needs your approval</li>
        <li><i style="background:var(--ink)"></i>Waiting for your reply</li>
        <li><i style="background:var(--n500)"></i>Idle</li>
        <li><i style="background:var(--lime)"></i>Done</li>
      </ul>
    </div>
    <figure class="mode-fig">${deck('sessions', 'sessions', heroLabels.sessions, [[1, 'keys'], [2, 'main'], [3, 'left'], [4, 'right']])}</figure>
    <div class="mode-legend">
      ${legend([
        [1, 'Keys', '<b>Press:</b> jump to that session’s window.'],
        [2, 'Big knob', '<b>Turn:</b> page through sessions, six at a time. <b>Press:</b> go to the page with the latest session that needs you.'],
        [3, 'Left knob', '<b>Turn:</b> filter by agent. <b>Press:</b> all agents.'],
        [4, 'Right knob', '<b>Turn:</b> filter by status. <b>Press:</b> all statuses.']
      ])}
      <p class="note">Only Claude Code reports context, so Codex and OpenCode sessions get a dashed ring. OpenCode sessions show up while <code class="inline">opencode serve</code> is running.</p>
      <p class="note">The deck never approves anything. It takes you to the window where you decide.</p>
    </div>
  </article>

  <article class="mode" aria-labelledby="models-title">
    <div class="mode-head">
      <p class="eyebrow">03 Models &amp; Usage <span class="sub">· Right button</span></p>
      <h3 class="h3" id="models-title">Pick the next model. <span class="dim">Live 5H and 7D limits.</span></h3>
      <p class="body">This mode shows one agent at a time: Claude Code, Codex or OpenCode. The first key shows how much of that agent’s 5&#8209;hour and weekly limits you’ve used, and the other keys are its models, with the current one in lime.</p>
    </div>
    <figure class="mode-fig">${deck('models', 'models', heroLabels.models, [[1, 'keys'], [2, 'main'], [3, 'left'], [4, 'right'], [5, 'buttons']])}</figure>
    <div class="mode-legend">
      ${legend([
        [1, 'Keys', '<b>Press</b> a model and your next session starts on it. <b>Press</b> the usage key for exact numbers and reset times.'],
        [2, 'Big knob', '<b>Turn:</b> effort. <b>Press:</b> Ultracode.'],
        [3, 'Left knob', '<b>Turn:</b> agent. <b>Press:</b> last agent, the one whose session you opened last.'],
        [4, 'Right knob', '<b>Turn:</b> permission. <b>Press:</b> apply.'],
        [5, 'Metal buttons', 'Select the mode, one per button.']
      ])}
      <p class="note">Turning the right knob only previews <span class="mono">READ</span>, <span class="mono">ASK</span>, <span class="mono">AUTO</span> or <span class="mono">FULL</span>; nothing changes until you press it, and <span class="mono">FULL</span> also asks you to confirm on the computer. Every change applies from your next session, and the deck confirms it, like <span class="mono">SONNET NEXT SESSION</span>. Sessions that are already running keep their settings.</p>
      <p class="note">Claude Code reports limits on Pro and Max plans, after a session’s first reply. Codex reports them when you sign in with ChatGPT. OpenCode doesn’t report limits, and on Windows Claude Code’s don’t show yet.</p>
    </div>
  </article>
</section>

<section class="section wrap rule" id="program" aria-labelledby="program-title">
  <div class="section-head">
      <p class="eyebrow">Program it yourself</p>
      <h2 class="h2" id="program-title">Write your own modes for any screen, button or knob. <span class="dim">Hold the middle button to open them.</span></h2>
      <p class="body">A mode is a JSON file in <code class="inline">~/.tokendeck/modes</code>: up to six keys and the three knobs, each tied to an action. The keys list your modes; press one to open it. The metal buttons still switch modes, and an edited file takes effect the next time you open it.</p>
    </div>
  <div class="program-grid">
    <div class="program-code">
      <div class="code">
        <div class="code-bar"><span>~/.tokendeck/modes/deploy.json</span><span>JSON</span></div>
        <pre tabindex="0" aria-label="Example mode file, deploy.json"><code>${highlight(example)}</code></pre>
      </div>
    </div>
    <div class="program-side">
      <figure class="program-fig">${deck('custom', 'sessions', 'Token Deck showing a custom mode with BUILD, LOGS, EDITOR, PALETTE and AGENTS keys')}</figure>
      <div class="program-actions">
      <table class="actions">
        <caption class="visually-hidden">Actions a key or knob can run</caption>
        <thead><tr><th scope="col">Action</th><th scope="col">What it does</th></tr></thead>
        <tbody>
        <tr><th scope="row">shell</th><td>Runs a command with zsh (cmd on Windows) for up to 10 seconds. The deck shows OK or FAILED.</td></tr>
        <tr><th scope="row">open</th><td>Opens an app, like Cursor.</td></tr>
        <tr><th scope="row">url</th><td>Opens a link in your browser.</td></tr>
        <tr><th scope="row">keys</th><td>Sends a shortcut, like <span class="mono">cmd+shift+p</span>, to the app in front.</td></tr>
        <tr><th scope="row">mode</th><td>From a key, switches the deck to <span class="mono">agents</span>, <span class="mono">sessions</span> or <span class="mono">models</span>.</td></tr>
        </tbody>
      </table>
      <p class="note">A key can also show an icon: a PNG or SVG file, drawn at 28 pixels.</p>
    </div>
    </div>
  </div>
</section>

<section class="section wrap rule" id="privacy" aria-labelledby="privacy-title">
  <div class="section-head">
    <p class="eyebrow">On your computer</p>
    <h2 class="h2" id="privacy-title">No account, no telemetry. <span class="dim">Here’s what Token Deck reads and changes.</span></h2>
  </div>
  <div class="facts">
    <div class="fact"><h3>Claude Code</h3><p>With your OK, Token Deck writes its hooks and status line into <code class="inline">~/.claude/settings.json</code>, so the deck sees a session change the moment it does. Its hooks replace any you have on the same seven events. It backs up the file first, and Stop watching, on the app’s This Mac page, puts that copy back.</p></div>
    <div class="fact"><h3>Codex and OpenCode</h3><p>Token Deck runs <code class="inline">codex app-server</code> to read your Codex sessions and limits, and asks OpenCode’s local server for its sessions. It never answers an approval request.</p></div>
    <div class="fact"><h3>Defaults</h3><p>Turning a knob writes your default model, effort or permission to the agent’s own config file. Nothing is typed into a running session.</p></div>
    <div class="fact"><h3>Credentials</h3><p>Token Deck never reads your Claude Code or Codex sign-in. The limits come from what those tools already report.</p></div>
    <div class="fact"><h3>Network</h3><p>Hooks reach the app on 127.0.0.1 only. Token Deck goes online only to check for and download new versions.</p></div>
    <div class="fact"><h3>Open source</h3><p>MIT licensed. <a class="link" href="${REPO}">Read the code</a> and <a class="link" href="${SITE}/install.sh">the install script</a>.</p></div>
  </div>
</section>

<section class="section wrap rule" id="help" aria-labelledby="help-title">
  <div class="help-grid">
    <div class="section-head">
      <p class="eyebrow">Help</p>
      <h2 class="h2" id="help-title">Questions and fixes. <span class="dim">Setup, updates and removal.</span></h2>
      <p class="body">Something else? <a class="link" href="${REPO}/issues">Open an issue on GitHub</a>.</p>
    </div>
    <div class="faq">
      <details id="agents">
        <summary>Which coding agents does it work with?</summary>
        <div class="answer">
          <table class="support">
            <thead><tr><th scope="col">Agent</th><th scope="col">What the deck does</th></tr></thead>
            <tbody>
              <tr><th scope="row">Claude Code</th><td>Sessions, context and usage limits (macOS), model, effort, permission, Ultracode</td></tr>
              <tr><th scope="row">Codex</th><td>Sessions, usage limits, model, effort, permission</td></tr>
              <tr><th scope="row">OpenCode</th><td>Sessions while <span class="mono">opencode serve</span> runs, and its permission setting</td></tr>
              <tr><th scope="row">Cursor, Amp, Devin</th><td>A key that opens or focuses the app</td></tr>
            </tbody>
          </table>
          <p>Amp’s key opens VS Code. Devin’s opens app.devin.ai in your browser.</p>
        </div>
      </details>
      <details id="no-change">
        <summary>The deck still shows the welcome screen.</summary>
        <div class="answer">
          <p>Check that Token Deck is running: it lives in the menu bar on a Mac and in the system tray on Windows. If the deck maker’s StreamDock or VSD Craft app is running, quit it, because only one program can use the deck at a time. Then unplug the deck and plug it back in.</p>
        </div>
      </details>
      <details id="damaged">
        <summary>macOS says Token Deck is damaged, or won’t open it.</summary>
        <div class="answer">
          <p>That happens with the disk images, because Token Deck isn’t notarized by Apple yet. The install command doesn’t have this problem. If you used a disk image, run this in Terminal and open the app again:</p>
          <div class="cmd"><code id="xattr-cmd">xattr -d com.apple.quarantine "/Applications/Token Deck.app"</code><button class="copy" type="button" data-copy="xattr-cmd" aria-label="Copy the command">${icon.copy}${icon.check}<span class="idle">Copy</span><span class="done">Copied</span></button></div>
          <p>If System Settings → Privacy &amp; Security shows Open Anyway for Token Deck, that works too.</p>
        </div>
      </details>
      <details id="smartscreen">
        <summary>Windows says it protected my PC.</summary>
        <div class="answer"><p>The installer isn’t code-signed yet. Choose More info, then Run anyway.</p></div>
      </details>
      <details id="permissions">
        <summary>Why does macOS ask for Automation and Accessibility?</summary>
        <div class="answer"><p>So a key can bring the right window to the front. macOS asks once for each app Token Deck switches to, like Terminal, iTerm2 or Cursor, and once for Accessibility under System Settings → Privacy &amp; Security.</p></div>
      </details>
      <details id="update">
        <summary>How do I update?</summary>
        <div class="answer"><p>Token Deck checks GitHub for a new version when it starts. On a Mac, click Update now on the app’s About page, which runs the install command for you, or run it yourself. On Windows, the app downloads the update in the background and asks before it installs.</p></div>
      </details>
      <details id="simulator">
        <summary>Can I try it without the deck?</summary>
        <div class="answer"><p>Yes. Open Token Deck’s window from its menu bar or tray icon: the deck drawn at the bottom is a simulator that shows the same key images. Click the drawing, or use your keyboard: 1 to 6 for the screen keys, Q, W and E for the metal buttons, the arrow keys for the big and left knobs, and comma and period for the right knob.</p></div>
      </details>
      <details id="remove">
        <summary>How do I remove it?</summary>
        <div class="answer">
          <p>Open Token Deck’s window from its menu bar or tray icon, go to This Mac and click Stop watching. That puts back the <code class="inline">settings.json</code> you had when you connected Claude Code. Then quit Token Deck and delete it: drag it out of Applications on a Mac, or use Settings → Apps on Windows.</p>
          <p>To remove its settings and log, delete <code class="inline">~/.tokendeck</code>. If you changed Codex defaults from the deck, copy <code class="inline">~/.codex/config.toml.tokendeck-backup</code> back over <code class="inline">config.toml</code>.</p>
        </div>
      </details>
      <details id="welcome">
        <summary>What does the deck show when the app isn’t running?</summary>
        <div class="answer"><p>The welcome screen, with the Stigg logo and io.stigg.io/usage. The deck stores it in its own memory, so it shows on any computer, with or without the app. Decks from the After Tokens box already have it, and Token Deck writes it once to any deck it hasn’t seen before.</p></div>
      </details>
    </div>
  </div>
</section>
</main>

<footer>
  <div class="foot-art wrap rule" aria-hidden="true">${svg('brand-kit/design/explosion-b-rise.svg', 'focusable="false" preserveAspectRatio="xMinYMid meet"').replace('viewBox="0 0 162 65"', 'viewBox="9.2 9.7 139.6 45.6"')}</div>
  <div class="footer wrap">
    <div class="event">
      <a class="at" href="https://www.stigg.io/after-tokens" aria-label="After Tokens">${svg('brand-kit/design/at-logo.svg', 'aria-hidden="true" focusable="false"')}</a>
      <p class="date">Nov 10, 2026 <span>·</span> Terra, San Francisco</p>
      <p class="blurb">Made by Stigg for everyone at After Tokens.</p>
    </div>
    <div class="foot-links">
    <nav class="links" aria-label="Token Deck">
      <h2>Token Deck</h2>
      <ul>
        <li><a href="#install">Install</a></li>
        <li><a href="${REPO}">Source on GitHub</a></li>
        <li><a href="${REPO}/releases">Releases</a></li>
        <li><a href="${SITE}/install.sh">Install script</a></li>
      </ul>
    </nav>
    <nav class="links" aria-label="Stigg">
      <h2>Stigg</h2>
      <ul>
        <li><a href="https://stigg.io">stigg.io</a></li>
        <li><a href="https://www.stigg.io/after-tokens">After Tokens</a></li>
      </ul>
    </nav>
    </div>
  </div>
  <div class="legal wrap rule">
    <span>© 2026 Stigg. The app is MIT licensed; the logos belong to their owners. Version ${version}.</span>
    <a class="chip" href="${SITE}/">io.stigg.io/usage <span aria-hidden="true">↗</span></a>
  </div>
</footer>
</div>
<p id="live" class="visually-hidden" aria-live="polite"></p>
<script src="main.js?v=${version}" defer></script>
</body>
</html>
`

fs.mkdirSync(path.join(root, 'site/fonts'), { recursive: true })
for (const name of ['Geist-Regular.woff2', 'GeistMono-Regular.woff2', 'Geist-Light.woff2']) {
  fs.copyFileSync(path.join(root, 'brand-kit/brand/geist', name), path.join(root, 'site/fonts', name))
}
fs.writeFileSync(path.join(root, 'site/favicon.svg'), svg('brand-kit/brand/stigg-app-icon.svg', 'width="512" height="512"') + '\n')
fs.writeFileSync(path.join(root, 'site/index.html'), html)
console.log(`site/index.html ${(html.length / 1024).toFixed(1)} KB`)
