# Token Deck — build plan

You are starting in an empty repository. This plan and the `assets/` folder next to it are everything
you need to build and ship **Token Deck**, Stigg's desktop software for the swag device every After
Tokens attendee receives on Nov 10, 2026: a Stream Dock N3 (6 LCD keys, 3 metal buttons, 3 knobs)
with the Stigg logo, named Token Deck, slogan "The AI Usage Management Console". The device is in the
box with a printed demo of the three modes and the address **io.stigg.io/usage**, which will point at
the download page you also build. People plug the deck in, see the burned welcome screen, install the
app from that page, and the deck becomes a control surface for their coding agents.

Build it in one pass, verify it on the real device (it is plugged into this computer) the way
section 15 says, and ship. Prefer the simple, proven option every time; do not add anything this plan
does not ask for. The deadline is real: installers and the site must be live before Nov 10. Every
external fact below was checked against primary sources (vendor SDK source, product docs, npm) on
Nov 1, 2026, and the plan was then reviewed by eight independent reviewers whose corrections are
folded in; where only hardware can settle something, the plan says "verify" and how.

## 0. What Gabriel sets up (everything else is yours)

Ask for these once, at the start, as a single list.

1. **GitHub repository** `stiggio/token-deck`, **public** (the box says "Program it yourself"), MIT
   licence with the brand assets excluded (section 2). Releases are published there by the CI
   workflow you write.
2. **No Apple Developer ID.** macOS installs with one Terminal command from the site, Homebrew-style:
   `/bin/bash -c "$(curl -fsSL https://usage.stigg.io/install.sh)"` (section 12). curl sets no `com.apple.quarantine` attribute (checked on macOS 26.5), and
   Gatekeeper only assesses quarantined downloads, so the unsigned app opens with no dialog. The costs:
   no built-in macOS updater (Squirrel.Mac needs a Developer ID signature; the app's "Update now" reruns
   the installer, section 12), macOS may ask for Automation and Accessibility again after an update,
   and a browser download of the dmg needs the note below. If Stigg ever adds a Developer ID, the repo
   secrets `CSC_LINK` (base64 of the Developer ID Application .p12), `CSC_KEY_PASSWORD`, `APPLE_ID`,
   `APPLE_APP_SPECIFIC_PASSWORD` and `APPLE_TEAM_ID` turn on signing, notarization and the built-in
   updater with no other change: CI bakes `__SIGNED__ = !!process.env.CSC_LINK` through electron-vite
   `define`, and `index.ts` calls `autoUpdater` on macOS only when it is true. The site's note for the
   dmg downloads (section 11) reads: "macOS will refuse to open Token Deck because it is not notarized
   (on macOS 15 and later Control-click → Open no longer works, and an unsigned build may be reported as
   'damaged'). In Terminal run: `xattr -d com.apple.quarantine "/Applications/Token Deck.app"` and open
   it again, or use the install command above. If System Settings → Privacy & Security shows an Open
   Anyway button for Token Deck, that works too." Do not ad-hoc sign under the hardened runtime with
   custom entitlements (launch crashes); section 12 has the one ad-hoc case.
3. **DNS only**: a CNAME `usage.stigg.io` → `stiggio.github.io` (the site in `site/` is published by
   GitHub Pages from the same public repo, free, with HTTPS; the workflow writes the `CNAME` file), and
   the short link `io.stigg.io/usage` pointed at `https://usage.stigg.io`. No Vercel, no other host.
4. This Mac, with the deck plugged in and the vendor "StreamDock" app quit (it holds the USB
   interface). Already here on Nov 1: Claude Code (signed in via claude.ai), Codex CLI (signed in,
   `~/.codex/auth.json`), Cursor.app, Visual Studio Code.app. Not here: OpenCode and Amp. You install
   OpenCode yourself (section 7); Amp needs nothing (its tile opens VS Code).

No API keys. Nothing else.

## 1. Decisions already made (do not reopen)

| Topic | Decision |
|---|---|
| App | One Electron app (TypeScript, electron-vite, React for the settings window), tray/menu-bar only (no Dock icon), starts at login (opt-in on first run). Name "Token Deck", bundle/app id `io.stigg.tokendeck` (never change it; NSIS upgrades key on it). macOS arm64 + x64 and Windows x64 installers from one codebase. Linux is not a target. |
| Device I/O | `node-hid` ^3.4.0 in the main process on the vendor HID interface (usage page `0xFFA0`, usage 1), matched by VID/PID only. Protocol implemented from section 3, which matches the vendor's own SDK byte for byte. No vendor SDK, no vendor app. |
| Tiles | 64 × 64 px JPEGs rendered with `@napi-rs/canvas` ^1.1.0 in the main process, pixel-exact: a code-authored 5 × 7 bitmap font (upper and lower case, proportional advances) on the token grid, the official one-color agent glyphs (OpenCode keeps its dim inner square), Stigg's colors. No anti-aliased body text on tiles. Geometry comes from the approved kit SVGs at 4 px per mm (section 5). |
| Fonts | Söhne cannot ship inside a downloadable app or a public repository (its licence covers Stigg desktops and the stigg.io web; the files must never be downloadable by third parties). The app UI uses **Geist** and **Geist Mono** (OFL, in `assets/brand/geist`, also Stigg's own fallback). The download site lives on `usage.stigg.io`, a sub-domain of the licensed domain, and uses Söhne through `@font-face` rules that point at the four woff2 URLs stigg.io's own stylesheet already serves from Webflow's CDN (section 11), with Geist as the fallback stack; no font file in the repo or in the deployed site. Tiles use the bitmap font. |
| Agents in v1 | Claude Code (sessions, context, usage, defaults), Codex (sessions + approvals via app-server, usage, defaults), OpenCode (sessions when its server runs, model default). Cursor, Amp, Devin: launch and focus only, shown honestly (section 5, Agents tile). |
| What "change model / effort / permission" means | None of the three agents has an API for changing a running session. The deck changes the agent's **defaults** (its config file) and shows `NEXT SESSION` on the tiles. Ultracode toggles the Claude Code setting. Nothing is simulated with keystrokes. |
| Sessions data | Claude Code: `claude agents --json --all` (supported, live) polled every 2 s, plus command hooks for instant transitions and the status line for context. Codex: `codex app-server` thread status. OpenCode: its local server. |
| Usage data | Claude Code: `rate_limits.five_hour` / `seven_day` (`used_percentage`, `resets_at`) from the chained status line (present for Pro/Max accounts after the first API response of a session; a window disappears once its `resets_at` passes). **No other source in v1**: Claude Code's credentials are never read (section 7). Codex: `account/rateLimits/read`. OpenCode: none (`NO QUOTA DATA`). |
| No-software state | The deck stores exactly one image in ROM: the boot/background image, shown at power-on and whenever the firmware restarts (it restarts by itself about a minute after a host goes silent), and the background behind the tiles while a host runs. Nothing else survives a power cycle (tiles are RAM), buttons do nothing without a host, there is no firmware menu. So "keeping a basic state without the app" means exactly this picture: the welcome screen. Token Deck writes it the first time it connects to a deck it has not burned yet (one flash write per deck, remembered by serial), the team pre-burns the giveaway decks with the batch tool, and the Burn page can rewrite it by hand (section 9). On quit the app paints the same welcome screen into the six tiles and closes; it never sends the vendor's `CLE DC` "software disconnected" frame, which the vendor documents as "clears all display" and which left Gabriel's unit black on Nov 1. With the app running but nothing connected, the tiles show one static on-brand idle screen with a `CONNECT` tile. |
| Program it yourself | Custom modes are JSON files in `~/.tokendeck/modes/`, hot-reloaded, entered by holding the middle metal button. Actions: shell command, open app, open URL, keystroke, switch mode. |
| Simulator | The settings window has a drawn deck that renders the same tiles and emits the same events, so everything is testable without hardware and on Windows. |
| Releases | GitHub Actions builds mac (zip + dmg, arm64 and x64 in one job) and Windows (nsis) on a tag, with fixed artifact names (`TokenDeck-mac-arm64.zip`, `TokenDeck-mac-x64.zip`, the matching `.dmg` files, `TokenDeck-win-x64.exe`) so the site links never change. macOS installs unsigned through the site's one-line `curl` installer (`/bin/bash -c "$(curl -fsSL https://usage.stigg.io/install.sh)"`; no Apple Developer ID, section 0). `electron-updater` checks GitHub releases on launch on Windows (and on macOS only if a Developer ID is ever added) and offers updates; unsigned macOS offers "Update now", which reruns the installer. Never silent restarts. |

## 2. Assets (the kit is committed as `/assets` except two private folders; the app's public brand files are copied into `/brand-kit`)

Since Nov 8 (Gabriel's call, so cloud sessions can work from the repository), `PLAN.md` and the kit
are committed at the repository root, the kit as `assets/`, except `assets/site-fonts/` (Klim licence
§3d: no third-party download) and `assets/brand/stigg-ds/` (proprietary, internal Stigg use only),
which stay untracked on the machine that has them. Where the rest of this section says "never
commit" or "read from the kit on disk", it now means only those two folders.

The repository is public, so the kit is split. Copy into `brand-kit/`, keeping the kit's sub-paths:
`design/agent-glyphs/` (with `SOURCES.md`), `design/screens-v2/`, `design/screens-kit-v2.png`,
`design/token-deck-*.{svg,json}`, `design/at-logo.{svg,json}`, `design/pixelmark.js` (font-name
references only, no font data), `design/explosion-*.svg`, `design/n3-line.svg`, `design/n3-mini.svg`,
`design/program-window.svg`, `design/stigg-*.svg`, `brand/geist/` (with `OFL-LICENSE.txt`),
`brand/stigg-*.svg` (includes `stigg-app-icon.svg`), `device/` (without its `*.log` files, `research-black-screen-2026-11-01.md`,
`research-display-architecture-2026-11-02.md` and `welcome/review-v5-2026-11-02.md`, which carry this
machine's paths; read those from the kit on disk; `device/NOTES.md` quotes what matters). **Never commit:** `site-fonts/` (Klim
licence §3d: no third-party download), `brand/stigg-ds/` (proprietary, internal Stigg use only),
`spec/`, `design/BOX-BRIEF.md`, `design/MARKETING-REFS.md`, `design/Token-Deck-box-*.png`. Read those
from the kit folder on disk when you need them. First commit a `.gitignore` with `/assets/site-fonts/`
and `/assets/brand/stigg-ds/` (the two private kit folders), `brand-kit/site-fonts/`,
`brand-kit/brand/stigg-ds/`, `site/fonts/`, `*.otf`. Add `LICENSE` (MIT, © Stigg) and
`BRAND-ASSETS.md` stating that the Stigg logos, marks and app icon are © Stigg, all rights reserved
and excluded from the MIT grant, and that the agent glyphs are their owners' trademarks used only to
name the integrations (sources in `brand-kit/design/agent-glyphs/SOURCES.md`). Font lint
(`scripts/lint-fonts`, run in `ci.yml` and before packaging) fails on: any tracked path matching
`soehne|söhne` case-insensitively (`git ls-files`); any tracked `.woff`/`.woff2`/`.otf`/`.ttf`
outside `brand-kit/brand/geist/` and the Geist copies under `resources/`; the string `soehne` in any
file under `src/` or `resources/`; any font file other than Geist inside the packaged app (`dist/`).

- `device/NOTES.md` — **read first**: every probe and test on Gabriel's deck, Nov 1-3, 2026 (USB ids,
  firmware string, HID interfaces, commands, input codes, the vendor code table, the `LOG` burn tests,
  the welcome screens v1-v8). Later sections supersede earlier ones; where NOTES and sections 3 and 9
  of this plan differ, this plan wins. `device/probe_n3.py` (about 120 lines) is the first probe
  (hidapi + Pillow; a Python venv with both exists at `~/.venvs/at`); `device/events-2026-11-01.log`
  is the raw input capture, and `device/burn_logo.py` is the reference burn (section 9).
- `spec/SPEC-v0.1.md` — Gabriel's product spec (reference only, not committed). It defines the three
  modes, the knob semantics, the session states, the safety rules and the acceptance tests. Section 6
  of this plan restates it with the engineering decisions; where the two differ, this plan wins.
- `design/BOX-BRIEF.md` — the box design brief (reference only). Sections 4–8 are the visual spec for
  the screens (colors, type, the kit of Mode 3 content); its section 8 copy lines are **drafts**, not
  the printed captions (section 11 has the printed ones). `design/screens-v2/screens-mode{1,2,3}.svg`
  and `design/screens-kit-v2.png` are the approved screen designs printed on the box: **the tiles
  must look like these**; section 5 converts them to pixels (the box draws each 16 mm screen as the
  64 px tile, so 1 mm of the box = 4 px; that is the design mapping, not the deck's scale: the panel
  has about 5.5 px per mm, so on the deck the tile is about 11.5 mm across inside a window of about
  14 mm, with the burned `#131512` around it). `design/Token-Deck-box-4-bottom.png` shows the printed demo and the printed captions
  people will compare the device and the site against.
- `design/agent-glyphs/*.svg` — one-color glyphs of the real Claude Code, Cursor, Codex, OpenCode,
  Amp and Devin marks (sources in `SOURCES.md`; OpenCode has a `#5b5d59` inner square). Use these,
  never redraw them.
- `design/token-deck-*.svg` — the "Token Deck" lockups (pixel "Token" + white "Deck"); `d-stacked`
  is the lid version. They are print and site assets: their pixel word is about 84 grid columns wide,
  so they can never be drawn on a 64 px tile (the welcome screen, section 9, is a burned image with
  the official logo and Söhne type), and their
  "Deck" is live Söhne `<text>`, so on the site they are inlined, never loaded through `<img>`.
  `design/at-logo.svg` + `pixelmark.js` — the After Tokens lockup (canvas implementation; the site
  uses it). `design/explosion-*.svg` — the token explosion motif. `design/n3-line.svg`, `n3-mini.svg`
  — line silhouettes of the device (for the simulator and the site). `design/program-window.svg` —
  the "Program it yourself" sketch from the box.
- `design/stigg-mark-mono.svg`, `stigg-logo-mono.svg` (both `currentColor`: they rasterize **black**
  through `@napi-rs/canvas`, so never on a tile), `brand/stigg-logo-on-dark.svg`,
  `brand/stigg-mark-white.svg` (explicit `#FFFFFF`; the one for the idle tile), `brand/stigg-app-icon.svg`
  (the app icon source).
- `brand/stigg-ds/SKILL.md` — Stigg's design system rules; `tokens.css` (every `--sg-*` variable;
  this copy's font stacks already lead with Geist), `components.css` (consumes those variables) and
  `geist-embedded.css` are the DS's own CSS. Reference only, never committed: for the settings window
  write the values you use (colors, hairline, radii, type scale, the button rules in section 10) into
  `src/renderer/styles/tokens.css` by hand, and set `<html data-theme="dark">` so the window keeps the
  `#131512` canvas whatever the OS appearance. `particles.js` the stigg.io particle field;
  `stigg-remotion-theme.ts` the motion tokens (one easing, `cubic-bezier(.2,.7,.2,1)`).
- `brand/geist/` — Geist and Geist Mono woff2 + OFL license (for the app UI; the site's fallback).
- `site-fonts/` — Söhne woff2, kept on disk only; the site does not load from them (section 11).
- `design/MARKETING-REFS.md` — marketing's speaker-card language (grid paper, glow, scan line, waves).
  Context only; **not a reference for the site**, which follows the DS and the box (section 11).

## 3. The device, as verified (Gabriel's unit + the vendor SDK source)

- USB `5548:1001`, manufacturer `HOTSPOTEKUSB`, product `HOTSPOTEKUSB HID DEMO` (a VSD-branded N3,
  "TreasLin N3" in community tables). Mirabox-branded N3s are `6603:1002` / `6603:1003`; older
  `6602:xxxx` units take a raw RGB565 background and no key rotation, so **do not** support them.
  Match only `5548:1001`, `6603:1002`, `6603:1003`: filter `HID.devices()` on those ids plus
  `usagePage === 0xFFA0 && usage === 1` and open by `path` (the same filter as `device/probe_n3.py`;
  the probes opened non-exclusively, while Token Deck keeps node-hid's default exclusive open, so
  section 13 step 2 confirms on day one that input still arrives after the handshake and that a second
  open from another process fails with `0xE00002C5`; if either does not hold, open with
  `{ nonExclusive: true }` and rely on the process check below). Never open a device to identify it.
  Token Deck drives one deck at a time: the first matching entry, kept until it disappears; other
  matching decks are left alone and keep showing their burned screen. The firmware string
  (`V3.VSDN3_PXL.02.010` here; Mirabox units report `V3.293N3_PXL.02.010`, same protocol) is
  informational: the vendor reads it with a GET_REPORT of input report id 0, which node-hid cannot do.
  After a matched open, on macOS only, try `getFeatureReport(1, 20)` and then `getFeatureReport(0, 513)`,
  each once inside try/catch; strip NUL bytes from both ends (hidapi returns the report id as the first
  byte), cut at the first remaining NUL, and accept only ASCII starting with `V3.`, otherwise show
  "n/a". On Windows show "n/a" without reading. Section 15 confirms keys still report after the read.
  The Device page, the log and the batch-burn printout show manufacturer, product, `serialNumber` and
  `release` from `HID.devices()` plus that string when it reads. An unlisted rebrand is diagnosed
  with `tokendeck probe` and added to the id constant.
- HID interfaces: interface 0 = vendor (usage page `0xFFA0`, usages 1 and 2 on one path → open the
  usage-1 entry); interface 1 = a keyboard interface (usage page 1, usage 6) that the OS owns (opening
  it fails on macOS); ignore it.
- Reports: output 1025 bytes in node-hid terms (report id `0x00` + 1024 payload bytes, zero-padded);
  input 512 bytes.
- Command frames (payload, after the report id; all verified in the vendor `libtransport` binary and
  on the device unless marked):
  - `CRT\0\0DIS` wake · `CRT\0\0STP` refresh (commits queued images and clears) · `CRT\0\0HAN` sleep
    (documented by the vendor; Token Deck never sends it)
  - `CRT\0\0LIG\0\0<pct>` brightness 0–100 (percent at payload index 10)
  - `CRT\0\0CLE\0\0\0<key 1–6 | 0xFF>` clear one key / all (key at payload index 11, after **three**
    zero bytes; a popular Python tool uses four, which is wrong), then `STP` (vendor binary only; not
    yet sent to this unit; section 15 checks it)
  - `CRT\0\0CONNECT` heartbeat, every 10 s, mandatory (units reboot about every minute without it:
    community report, opendeck-akp03 issue 44; not yet timed on this unit, section 15 measures it)
  - `CRT\0\0CLE\0\0DC` "software disconnected": **never send it.** The vendor's Python API reference
    documents `disconnected()` as "Disconnects and clears all display", and that is what it did on
    Gabriel's unit on Nov 1 (sent once, after the first LOG test): the panel went black, no logo, no
    fallback, keys still reporting. The only sources that show a standby logo after it are about other
    models (N4 Pro). Token Deck has no code path that builds it or `HAN`, not even behind a debug flag
    (Gabriel's rule): `protocol.ts` has no encoder for either, a vitest asserts that no frame the
    protocol module can produce starts with `CRT\0\0CLE\0\0DC` or `CRT\0\0HAN`, and the `--dc` /
    `--dc-only` options of `device/burn_logo.py` and `device/log_test.py` are never ported. The quit
    path is in the "On quit" bullet below.
  - `CRT\0\0QUCMD\x1f\x11\x00\x11\x00\x11\x00` what the vendor app sends on connect (meaning
    undocumented; harmless; the vendor SDK itself does not send it to the N3)
  - `CRT\0\0BAT<u32be jpegLength><key 1–6>` (length at payload 8–11, key at 12) then the JPEG bytes in
    1024-byte payload chunks (each its own 1025-byte report), then `STP`
  - `CRT\0\0LOG<u32be jpegLength>\x01` then a 320 × 240 JPEG (rotated like the tiles, so 240 × 320 on
    the wire) in chunks = the boot / background image, **written to the device ROM** (vendor README:
    "writes to the device's ROM … remains after restart"; key images are RAM and vanish at power-off).
    The vendor's `libtransport` sends the header and chunks, then blocks on one input read with a 3 s
    timeout, and only then lets the `STP` out; its N3 test sleeps 1 s after the refresh. The device
    answers a successful write with one report (`ACK\0\0OK\0\0` + code `0x00` + state `0x00`), the only
    write acknowledgement this unit sends; every write that got no report failed and left the slot
    blank (black panel at power-on, the factory logo gone). Status on Nov 3: ten writes accepted, 1.8 to
    22.3 KB (tests 3, 13 and 14, welcome v1-v4 and v6-v8; four in one power cycle, v1-v4), each the only
    `LOG` of a fresh connection, each after six tiles + `STP` in the same session, and each answered by
    the write report (0.12-0.26 s after the last chunk where it was timed; test 3's came inside its 3 s
    listen, untimed). The three checked after a power cycle (1.8, 11.1 and 22.3 KB) persisted. Every
    write without tiles first failed (tests 4a, 7 and 9), and after a failed write the firmware ignores
    image writes until a power cycle. Size is not the limit up to 22.3 KB; above that is untested.
    Section 9 step 4 is the verified rhythm. `device/NOTES.md` has the test record and
    `device/research-black-screen-2026-11-01.md` the sources. Flash wears: write it once per device
    (section 9), never on every launch.
- Key tiles: 64 × 64 baseline JPEG, **rotated 90° clockwise before encoding** (vendor:
  `key_rotate_angle = 90` = `ROTATE_90_CLOCKWISE`; PIL `rotate(-90)`). The background image is
  rotated the same way. Verified: upright test tiles showed upright. Encode with
  `canvas.encode('jpeg', { quality: 100 })`: `@napi-rs/canvas` writes 4:4:4 at exactly q100 and 4:2:0
  at q99 and below (no subsampling option exists), and 4:4:4 keeps 1 px color exact, whereas 4:2:0
  halves the saturation of every thin lime or coral feature. **Verified Nov 2: a q100 4:4:4 tile renders
  correctly on Gabriel's unit** (`device/NOTES.md`, test 14), so ship q100. That tile was encoded by
  Pillow; the first Skia-encoded tile the deck decodes is section 13 step 2's test tile. One vitest
  encodes a tile and asserts the JPEG SOF0 sampling factors (1×1 for all components) so a dependency
  bump cannot silently switch to 4:2:0. The largest tile sent to this unit is 6,681 bytes (test 14);
  other drivers for this family keep tiles under 10 KB. The headless renderer test asserts every
  built-in tile (demo data, idle, overlays, the welcome crops) is under 10,000 bytes, and a custom-mode
  tile over 10,000 bytes is a validation error on the Modes page.
- **Where tiles land (measured Nov 2, `device/panel_geometry.py`; tiles ±1 px, windows ±2 px):** the
  firmware draws each 64 × 64 key image 1:1 (never scaled) at a fixed panel position: x = 20 / 124 /
  228, y = 28 / 131 for keys 1–3 / 4–6. Each key's window shows more than the tile, about 76 × 77 px of
  the panel: x 13–88, 120–198, 228–306 and y 20–97, 130–206, as half-open rects (x1 and y1 exclusive,
  as the welcome generator uses them). So **the burned background is visible around every tile while
  the app runs** (7 / 4 px left / right on keys 1 and 4, 4 / 10 on keys 2 and 5, 0 / 14 on keys 3 and
  6; 8 / 5 px above / below the top row, 1 / 11 for the bottom row), and the app cannot draw there
  without a flash write. Section 9 keeps that band `#131512`. Optics (photos of v6, v7 and test 15):
  the tile's outer pixel is visible at the left edge of keys 3 and 6 and 1 px below the top of keys
  4–6, and the clear keycap's bevel mirrors bright content near a window edge, up to about 20 px in
  (v7, lit and unlit tokens alike). Section 5's safe rect keeps tile content 6 px inside the window;
  runtime tiles cannot avoid the bevel mirror.
- **Region drawing (candidate, untested on this firmware):** the vendor transport also has
  `CRT\0\0BGPIC` + u32be JPEG length + u16be x, y, w, h + `00` + framebuffer layer, then the JPEG in
  1024-byte reports, which draws into RAM at any panel position (no flash write), and `CRT\0\0BGCLE` +
  `03` to clear it (`device/research-display-architecture-2026-11-02.md`). The vendor enables it only on
  bigger models. If this N3 accepts it, the app could fill each ~76 px window at runtime instead of only
  the 64 px tile. v1 does not depend on it; a probe for it is in section 15.
- **Input reports only arrive after the handshake** (`DIS`, `LIG`, `QUCMD`, `LIG`; verified: a plain
  open produced nothing for 150 s). Frame: bytes 0-8 are `ACK\0\0OK\0\0` (41 43 4B 00 00 4F 4B 00 00),
  the code is byte 9 and the state byte 10 (key 1 press = `41434b00004f4b0000010100`). Match `ACK` at
  bytes 0-2 and `OK` at 5-6, never a 10-byte `ACK\0\0OK\0\0\0` literal (its last zero is the code), and
  ignore everything after byte 10 (only bytes 0-15 were ever logged); the decoder fixtures are the raw
  hex lines of `device/events-2026-11-01.log`. Code `0x00` is the `LOG` write report: it goes to the
  burn's wait and never to the mode controller (section 9). Drop reports that do not start with `ACK`,
  byte 9 = `0xFF` (a write acknowledgement per the vendor table, never seen on this unit), unknown
  codes, and every input event while a burn is running. Decode state 1 as press and any other value as
  release (this unit sends 0; the vendor's Python SDK also handles 2). The code table (vendor
  `streamdockN3V25.cpp`, confirmed on the deck where noted):
  - LCD keys 1–6: `0x01`–`0x06`, left to right then top to bottom, state 1 = press, 0 = release
    (verified).
  - Metal buttons: `0x25` left, `0x30` middle, `0x31` right (verified left → right).
  - Top (main, large) knob: click `0x35`; `0x51` clockwise, `0x50` counter-clockwise (verified).
  - Bottom-left knob: click `0x33`; `0x91` clockwise, `0x90` counter-clockwise.
  - Bottom-right knob: click `0x34`; `0x61` clockwise, `0x60` counter-clockwise.
  - Rotation = one report per detent with state 0. Knob clicks send both states (1 then 0) on this
    firmware (verified).
  Keys, the left and right metal buttons and knob clicks act on state 1 (press) and ignore the
  release; the middle metal button acts on release or after an 800 ms hold (section 5, Custom modes).
  A decoder test feeds the `0x35` press/release pair from `device/events-2026-11-01.log` lines 101-102
  and expects one click (lines 101-104, two pairs, give two). All six small-knob codes are in the Nov 1 capture (`device/events-2026-11-01.log` lines
  105-140): `0x61`/`0x60` followed by clicks `0x34`, and `0x91`/`0x90` followed by clicks `0x33`, the
  vendor's pairing. Which physical knob is which, and which code is clockwise, were not recorded for
  that round: section 15's input check settles them on this unit, and the first-run wizard confirms
  them (section 10) and stores the result.
- Keepalive: the vendor app also re-uploads a key image about once a second; one community tool
  reports the panel stops repainting after silence on this firmware family. Implement `CONNECT` every
  10 s for the whole session (deferred, never dropped, while a frame group or a burn is on the wire:
  a burn holds it until its hold starts, so the longest gap is about 23 s, inside the ~1 min the
  firmware tolerates), and a setting "repaint
  keepalive" (re-send key 1's tile every second when idle) that defaults to on; test 15 minutes with
  it off on a static screen (section 15) and keep the default that works.
- **Write queue** (`transport.ts`, the only caller of `device.write`): it runs one item at a time to
  completion, and an item is a whole frame group, never a single report: one command; one tile (`BAT`
  header + all its 1024-byte chunks, back to back); a paint (the changed tiles + one `STP`); a burn
  (section 9 step 4, from its handshake to the end of its hold, the pauses and the wait for the write
  report included). The heartbeat and the repaint keepalive are queue items like any other, so they
  never land inside a group, and during a burn they wait. The queue holds at most one pending image
  per key: a newer render replaces a queued one that has not started, so a fast knob never builds a
  backlog in front of the heartbeat. A key whose JPEG bytes equal the last sent is skipped (except the
  keepalive repaint); the last-sent record is cleared on every open, reopen, resume, replay and burn,
  and the burn's tile pre-paint, the quit paint and a replay always send all six tiles. Log bytes and
  milliseconds per paint. A vitest drives the queue against a fake device with the keepalive and
  heartbeat timers armed and asserts that no foreign report appears inside a tile or burn group and
  that nothing at all is written between the last `LOG` chunk and the write report.
- On quit (tray Quit, logout or shutdown, the updater's install on quit) `before-quit` calls
  `event.preventDefault()` once and runs the quit sequence: wait for an in-flight burn to end its hold
  or fail (about 13 s with the reports on record, up to about 23 s if a report comes near the 10 s limit;
  never close inside a burn), stop the repaint keepalive, queue the six
  welcome crops (`resources/welcome-tiles/`, the same bytes the burn paints, section 9) + `STP` and
  await them, stop the heartbeat, await `device.close()`, then `app.exit(0)`. Cap the paint and close
  at 3 s (1 s after `powerMonitor` `shutdown`); past the cap exit anyway, which ends like a crash. After
  a failed burn (section 9 step 4) the quit paints nothing: it stops the heartbeat and closes. Send
  **no `CLE\0\0DC` and no `HAN`**: the vendor documents `CLE DC` as "clears all display" and it left
  Gabriel's unit black; `HAN` is sleep (dark panel). The deck keeps the last tiles until the firmware
  restarts on host silence (about a minute, per the community report above), then shows the ROM
  image: the same picture when the deck is burned. A crash sends nothing and ends the same way;
  section 15 times both on this unit.
- Connection (`transport.ts` is the only code that opens or closes a handle): a state machine idle →
  opening → handshaking → ready (→ burning, section 9) → closing → idle. At most one open is in flight,
  and the previous handle's `close()` is awaited before any open. node-hid has no hotplug events, so
  poll `HID.devicesAsync()` every 2 s while no deck is open. The poll, a write error, a node-hid
  `error` event and `powerMonitor` `resume` all request a reconnect, and requests coalesce: close,
  wait 1 s, enumerate again (never reuse a stored path: it changes whenever the deck re-enumerates,
  after a replug or its own firmware restart), open, replay the handshake and the current tiles (these
  units often fail to recover from USB selective suspend without that). Register `device.on('error')`
  on every handle before adding the `data` listener (node-hid emits a read error once and stops
  reading; with no listener it is an uncaught exception in the main process), and wrap the decoder and
  controller call inside the `data` handler in try/catch and log, because node-hid re-emits exceptions
  thrown from a `data` handler as `error`. A write still unresolved after 5 s means the deck is wedged:
  abandon that handle without awaiting its close (the close would queue behind the stuck write). After
  that, or after 3 failed opens or handshakes in a row on a deck that is still listed, stop and show
  "Deck not responding. Unplug it and plug it back in."; resume when the deck has left
  `HID.devices()` and come back. During a burn, and after a failed one, section 9 step 4 decides
  instead of this bullet.
- Only one process can own the interface on macOS (hidapi opens exclusively; a second open fails with
  IOKit `0xE00002C5`). Keep the default exclusive open (it is the guard; section 13 step 2 confirms it
  on this unit). Detect the vendor apps before opening: StreamDock and the VSD-branded VSD Craft
  (`pgrep -x StreamDock`, `pgrep -x 'VSD Craft'` on macOS; `tasklist /FI "IMAGENAME eq StreamDock.exe"
  /FO CSV /NH` and the same for `VSD Craft.exe` on Windows; names are the best available guess, keep
  them in a config constant). Treat an open failure whose message contains `0xE00002C5` or "exclusive"
  as the same case regardless of the process check, but only while no Token Deck handle is open or
  closing: show "Quit the StreamDock or VSD Craft app to use Token Deck." Any other open failure logs
  and falls back to the 2 s poll. On Windows two apps can open the device at once and fight over the
  display, so the process check is the only guard there: repeat it with every heartbeat and right
  before any burn, and when a vendor app appears, stop writing, close the deck and show the same
  message.

## 4. Repository layout

```
src/main/
  index.ts                     app lifecycle, tray, single instance, autostart, updater (gated), --smoke flag (section 12)
  deck/transport.ts            node-hid (HIDAsync): the connection state machine, hot-plug by 2 s polling, the write queue of whole frame groups (section 3)
  deck/protocol.ts             frames from section 3 (no encoder for CLE DC or HAN), handshake, keepalive, event decoding, knob map
  deck/tiles.ts                64x64 renderer (@napi-rs/canvas): renders each tile upright (RGBA, tile space); toWire() turns it 90° clockwise as a pixel copy, dst(x, y) = src(y, 63 − x), never ctx.rotate, then encodes JPEG q100 (4:4:4)
  deck/pixelfont.ts            the 5x7 bitmap font (section 5): A–Z, a–z, digits, space, % - . : / + , ' & ■ ● ○ ▲ ▼ ✓; proportional advances; measure(text); unknown glyph = outlined box
  deck/glyphs.ts               agent glyphs rasterized once per size from brand-kit SVGs (color by text replacement, section 5)
  deck/screens/*.ts            tile layouts: agents, sessions, models, overlay, idle, custom (the welcome tiles are not a layout: they are the six committed crops in resources/welcome-tiles/, painted before a burn, on quit and on the idle screen)
  modes/controller.ts          mode state machine, selected session, overlays, custom-mode picker
  integrations/types.ts        Integration interface + capability declaration
  integrations/claude-code.ts  agents --json, hook/status-line receiver, settings.json, focus
  integrations/codex.ts        app-server rpc, config.toml, rollouts fallback
  integrations/opencode.ts     server api (v1 and v2), opencode.json
  integrations/{cursor,amp,devin}.ts   launch/focus only
  sessions/store.ts            unified session list, ordering, filters, staleness
  usage/store.ts               per-agent quota windows, last-seen timestamps, staleness (STALE after 10 min, -- after 24 h)
  hooks/server.ts              http://127.0.0.1:<port>/t/<token>/… for the hook and status-line shims; base URL written to ~/.tokendeck/url
  system/focus.ts              window focusing (AppleScript / PowerShell), app launching
  settings/store.ts            electron-store schema (section 10)
  burn/burn.ts                 the burn (section 9 step 4); burn/records.ts: burnedSerials + resources/preburned.json; burn/calibrate.ts (CLI only, section 9 step 2)
  cli.ts                       `burn --watch`, `probe` and `calibrate`, run as the packaged app binary with that first argument (macOS `"/Applications/Token Deck.app/Contents/MacOS/Token Deck" burn --watch`, Windows `"Token Deck.exe" burn --watch`; the README gives both and a `tokendeck` shell alias, the name this plan uses). index.ts handles them right after `--smoke`, before anything opens a deck; the CLI takes the single-instance lock itself and, if the tray app holds it, prints "Quit Token Deck first: the tray app owns the deck." and exits 1
src/renderer/                  React settings window + simulator (Geist, hand-written DS tokens in styles/tokens.css)
src/shared/                    types shared by main and renderer
resources/                     icons (Template tray icons 16/32@2x, .ico), glyph SVGs, hook shim scripts (sh + ps1), panel-geometry.json, welcome-320x240.png + welcome-sent.jpg + welcome-tiles/key1-6.jpg (section 9 step 3), calib-ruler-240x320.jpg (section 9 step 2), preburned.json (committed as `[]`; the batch's list replaces it before the event tag, section 9 step 5)
scripts/                       build, lint-fonts, release, export-site-tiles (Node script importing the tile renderer)
site/                          the static download page (usage.stigg.io)
test/                          vitest only: protocol (no frame starts with CRT\0\0CLE\0\0DC or CRT\0\0HAN), decoder (fixtures: the raw hex lines of device/events-2026-11-01.log), the write queue (no foreign report inside a tile or burn group; nothing between the last LOG chunk and the report), the burn sequence (section 9 step 4 against a fake transport and clock), the once-per-serial records, rotation (a lone white pixel at (0, 0) decodes at (63, 0)), pixelfont widths, overlay string lengths, JPEG sampling, tile byte sizes (every built-in tile under 10,000 bytes), tile renderers (headless: loads @napi-rs/canvas and renders the six demo tiles), integrations with fixtures. No Playwright; the settings window and simulator are checked by hand.
```

## 5. Tile design system (64 × 64)

The box printed these screens; people will hold the device next to the box. Match
`design/screens-v2/*.svg` at 4 px per mm (their 16 mm screen is the 64 px tile; all coordinates below
are 64 px tile space before the 90° rotation), with these rules:

- Grid: 4 px cells (16 × 16 cells). Everything snaps to it, except the kit's own text rows and token
  pitches noted below. Background `#131512`. Never `#000`.
- **Centre on the window, not the tile.** The firmware draws each tile at a fixed spot that is off-centre
  in its key's window (section 3; measured Nov 2): in tile coordinates the window's centre is at
  x = 30.5 / 35 / 39 (left / middle / right column) and y = 30.5 / 37 (top / bottom row), not at
  (32, 32) (`panel-geometry.json` rects are half-open: x1 and y1 are exclusive). A layout centred in the
  tile would sit 7 px left in keys 3 and 6 and 5 px high in the bottom row, the composition fault
  Gabriel rejected in welcome screen v1. Every layout therefore declares a fixed design box, the
  largest area it draws in any state: Agents x 13–50, y 9–53 (the meter and the largest glyph extents,
  Amp 38 px wide and Devin 32 px tall, centred on (32, 25)); Sessions the approval frame's outer rect,
  x 3–60, y 2–59; Models the band and rows, x 2–58, y 2–58; a custom tile x 7–56, y 7–54. Each key gets
  one offset per layout, computed from `panel-geometry.json` and never from what is drawn: (dx, dy) =
  `Math.round`(window centre − design-box centre), then clamped so the design box stays inside the
  key's safe rect (next bullet; every design box is at most 58 × 59 px). A glyph, ring or token row
  therefore lands on the same pixels whatever the title, percent, model or state; rows of keys line
  up, and nothing moves when a model becomes current, a frame appears or an overlay shows. Result:
  Agents centred to 1 px on every key; Models 3.5 px left of centre on keys 3 and 6 and 1.5 px high on
  the bottom row; Sessions 4 px left on keys 3 and 6 and 2 px high on the bottom row. That residue is
  the device's: on keys 3 and 6 the tile starts at the window's left edge, so nothing wider than 50 px
  can be centred there. The welcome crops (pre-burn paint, quit, idle) are composed in panel space and
  are never offset. The simulator draws the decoded wire JPEG turned back 90° counter-clockwise at its
  `panel-geometry.json` tile rect inside the window rect, over that window's crop of
  `resources/welcome-320x240.png`, so a rotation, offset or encoder fault shows there first. It checks
  layout, not tone: the panel lifts dark greys far more than a monitor (section 15 judges colours on a
  photo of the deck).
- **Safe rect per key.** Where the tile reaches the window edge, content stays 6 px inside the window,
  the welcome screen's rim: the clear keycap's wall mirrors what is close to it, and a seated viewer's
  parallax hides a few px. Safe rect = tile ∩ window inset 6 px, in tile coordinates, inclusive: key 1
  x 0–61, y 0–62; key 2 x 2–63, y 0–62; key 3 x 6–63, y 0–62; key 4 x 0–61, y 5–63; key 5 x 2–63,
  y 5–63; key 6 x 6–63, y 5–63. Content may touch the tile edge where the window continues past it
  (left of keys 1 and 4, right of keys 2, 3, 5 and 6, above keys 1–3 and below keys 4–6, where the
  burned image is `#131512`). The bevel
  mirrors whatever sits within about 20 px of a window edge (v7 photo: tokens 14–20 px in); a 64 px
  tile cannot keep its content that far in, so tiles accept it, unlike the welcome screen, and the
  section 15 photo checks that no reflection reads as content.
- Colors: white `#FFFFFF`, greys `#C4C7C3`, `#9EA19D`, `#838682`, `#5B5D59` (disconnected, stale),
  `#3C3E3A` (hairline, dim glyph), `#2C2F2B` (unlit: every unlit token square, the Agents meter's off
  squares, the ring track and the empty slot; also the welcome screen's unlit token); lime `#92E759` as
  the signal (the current model's band and squares, the eyebrow, active meter squares); status set:
  working `#7DA2FF`, needs approval `#FF8E6D` (with frame), needs input `#FFFFFF`, limit or error
  `#EA384C`, series `#6BF8C2`, neutral `#838682`. The panel lifts dark greys (v7 photo: `#2C2F2B`
  tokens a third of the way to white; `v8_common.photo_emul` puts `#3C3E3A` at 38 %), so the box's
  `#3C3E3A` off squares and track are drawn one step darker on the deck to keep the box's contrast;
  section 15 checks it against the box.
- Type: the bitmap font only, drawn as filled rectangles (canvas text is anti-aliased; rectangles are
  not). 1× = 5 × 7 px glyphs with proportional advances: `.` `:` `,` `'` are 2 px wide (3 px advance;
  a 2 px dot stays JPEG-safe), `/` `-` `I` `1` are 3 px wide (4 px advance), space is 3 px, every
  other glyph 5 px + 1 px = 6 px; lowercase a–z with `g j p q y` descending 2 px; `measure(text)` is
  used by every layout and numbers are right-aligned by measured width. "About 10 letters per tile" is
  the worst case (59 px), not a rule. All tile text is 1× (the welcome screen is a burned image,
  section 9, not tile text). Case: model names as the provider spells them (`Opus`, `Sonnet`, `Haiku`,
  `Fable`), everything else uppercase (mono-label rule),
  including session titles. The six welcome crops (section 9 step 3) are not rendered tiles: they are
  the burned welcome image itself (Pillow q100 4:2:0 with its Söhne type), painted unchanged before a
  burn, on quit and on the idle screen. If section 13 step 2's test photo shows lowercase names or dark names on
  the lime band illegible at arm's length, model names follow the uppercase rule too (`OPUS`,
  `SONNET`), and the README records it.
- Lines are 1 px. Rings are 4 px (the kit's 1.1 mm stroke). Usage meters are rows of ten 4 × 4 token
  squares (Models & Usage below); there are no continuous bars.
- JPEG at quality 100 (4:4:4, section 3). Text is white or grey; lime is for fills, bands and squares.
  `ctx.imageSmoothingEnabled = false` when scaling glyph bitmaps.
- Glyph rasterizer (`deck/glyphs.ts`): load each brand-kit SVG as text, replace `fill="#ffffff"` with
  the requested color, leave `#5b5d59` (OpenCode's inner square) as is, use `#3C3E3A` for both when
  the whole glyph is dim, then `loadImage` at the target size; never tint through a mask. For any
  other SVG (custom-mode icons) replace `currentColor` with `#ffffff` before `loadImage`, because
  resvg resolves `currentColor` to black.

Tile layouts:

**Agents (mode 1)** — fixed positions: Claude Code, Cursor, Codex / OpenCode, Amp, Devin. Each mark
placed exactly as `screens-mode1.svg` places it, times 4: rasterize the glyph SVG at its viewBox size ×
the kit's scale × 4 (Claude 30 × 30, Cursor 26 × 29, Codex 27 × 27, OpenCode 25 × 27, Amp 38 × 20,
Devin 29 × 32, padding included) at (kit translate + kit scale × viewBox origin) × 4; never re-fit a
mark to a box (they are optically sized; Amp's ink is 37 × 16). White. Under it the meter: four 8 × 8
squares at x = 13, 23, 33, 43, y = 46 (the kit's 2 mm squares on a 2.6 mm pitch), lime = that many
sessions active (capped at 4), `#2C2F2B` otherwise. Launch-only agents (Cursor, Amp, Devin) never draw the
meter: white glyph plus `LAUNCH` (1×, `#838682`, centred in the meter band at y 47–53) when
installed; glyph `#3C3E3A` plus `LAUNCH` only when `detect()` finds nothing (Devin counts as always
installed; it is a URL). No running-state detection, no third state. Pressing a tile focuses the
agent's most recent window or launches it (section 7).

**Sessions (mode 2)** — one session per tile: ring centre (32, 27), radius 17, stroke 4 px; track
`#2C2F2B`; used arc from 12 o'clock clockwise, white (`#EA384C` above 85%, dashed `#838682` when
unknown, `#5B5D59` when disconnected). Agent glyph white, placed the same way from `screens-mode2.svg`
(rasters Claude 18 × 18, Cursor 15 × 18, Codex 16 × 16, OpenCode 15 × 16, Amp 23 × 12, Devin 17 × 19),
so it sits in the ring as the kit draws it. Status dot on the ring's upper right: first a 15 px
`#131512` knockout circle, then a 10 px dot, both centred at (44, 15). Dot colors: working `#7DA2FF`;
needs approval `#FF8E6D` plus a 3 px `#FF8E6D` rounded frame (radius 2) on the Sessions design box:
outer edge on columns 3 and 60 and rows 2 and 59, strokes on columns 3–5 and 58–60 and rows 2–4 and
57–59 (the kit's frame is 60 × 58; trimmed to 58 px wide to fit keys 3 and 6); needs input white; idle
`#838682`; completed lime; disconnected = a 3 px `#5B5D59` ring outline 10 px across (the kit's
0.777 mm stroke), no fill, with arc and title in `#5B5D59`. Title: one line, 1×, `#C4C7C3` (the kit's
title bars), glyph rows 48–54, centred, at most 50 px measured (about 8 characters, so it clears the
frame's strokes), uppercase, truncated without ellipsis; break at `-`, `_` or space where possible so
a suffix survives (`MY-APP-3F`). Empty slot (Sessions; Models when the agent has fewer than six
favourites, as with Claude Code's four defaults; a custom `null` tile): a 4 × 4 board of 3 × 3 px
`#2C2F2B` tokens on a 5 px pitch (18 × 18 px, the welcome screen's unlit token), centred on the window
(it fits every key exactly); nothing else is drawn.

**Models & Usage (mode 3)** — `screens-mode3.svg` at 4 px per mm, all type 1×:
- Name row: name at (6, 6), white (glyph rows 6–12; descenders to 14), truncated to fit x 6–54.
  Current model instead gets a lime band rect (2, 2, 57 × 14), radius 2 (4 px of lime on both sides of
  the 49 px rows), with the name in `#131512`.
- Row `5H`: label `#838682` at (6, 20); percent white, right-aligned with its last pixel at x = 54,
  over the last square.
- Token row: ten 4 × 4 squares on an even 5 px pitch at x = 6, 11, 16, 21, 26, 31, 36, 41, 46, 51 (last
  pixel 54), y = 28. The kit's 1.33 mm pitch is 5.33 px; rounded to pixels it gives 1 and 2 px gaps,
  and tokens keep an even pitch (box brief, the token grid). Lit count = `Math.round(pct / 10)` (kit:
  62 → 6, 41 → 4, 24 → 2, 58 → 6, 9 → 1, 17 → 2). Lit color lime on the current model's tile,
  `#9EA19D` on every other tile; unlit `#2C2F2B`.
- Row `7D`: label at (6, 36), percent to x = 54, squares at y = 44.
- Bottom row, only when the model's quota is a shared pool: a 4 × 4 square at (6, 53), lime on the
  current model else `#838682`, then `SHARED` 1× `#838682` at (12, 52). Own-pool tiles draw nothing
  here (the kit's Astra and Grok tiles carry no label). `SHARED` text is never lime.
- Unknown window: all ten squares unlit and `--` in place of the percent. Provider reports no quota:
  `NO QUOTA` at (6, 20) and `DATA` at (6, 30) in `#838682`, no squares, no bottom row.
Row budget: band 2–15, name 6–12(14), 5H text 20–26, squares 28–31, 7D text 36–42, squares 44–47,
bottom 52–58; the widest percent `100%` (21 px with the 3 px `1`) spans x 34–54 and never meets the
label.

**Overlay** — a band across the bottom of every tile that moves with the layout's dy and is clipped to
the tile: rows 48 + dy to 63 filled `#131512`; a 1 px `#3C3E3A` hairline on row 48 + dy, 50 px long and
centred on the window (columns 6–55 on keys 1 and 4, 10–59 on keys 2 and 5, 14–63 on keys 3 and 6).
Text appears only on the top row: 1× white, glyph rows 53 + dy to 59 + dy, centred on the window's x
centre (30.5 / 35 / 39) and clamped into the key's safe rect. While an overlay shows, a tile draws only
the parts of its layout that end at least 2 px above the hairline: Agents the glyph, Sessions the ring
with its glyph and status dot, Models the name row and the 5H row, custom tiles the icon; meters,
titles, the 7D row and the bottom row are left out, never cut by the band. A message is a list of tile
groups written below with `|`; render them literally, one group per tile, tiles 1 → 3 (the top row) in
order; every other tile shows the empty band. No group exceeds 10 characters or 58 px measured (the
safe width of keys 3 and 6); a unit test asserts this for every string in the list. Messages:
`HIGH | EFFORT` (any level the agent advertises, uppercased, `medium` as `MED`, cut to 10 characters
and 58 px); `ULTRACODE | ON`; `ULTRACODE | OFF`;
`ASK | PRESS TO | APPLY` (`READ`, `AUTO`, `FULL` the same); after apply, since every default change
shows next-session semantics: `ASK | NEXT | SESSION`; `CONFIRM ON | COMPUTER`;
`SONNET | NEXT | SESSION` (any model name, cut to 10 characters and 58 px measured); `NEXT | SESSION`; `NOT | AVAILABLE`;
`NO SESSION`; `APPLIED`; `FAILED`; `OK`; the Sessions filters as their value, one group: `ALL`,
`WORKING`, `NEEDS YOU`, `IDLE`, `DONE`, and the agent as `CLAUDE | CODE`, `CODEX`, `OPENCODE`,
`CURSOR`, `AMP`, `DEVIN` (also the Models left knob). Mode switch: `AGENTS`,
`SESSIONS`, `MODELS & | USAGE`, same band and text, for 1 s. Shown for 5 s; any knob turn restarts
the timer; key presses under an overlay are ignored (the spec's rule).

**Idle screen** (section 1: app running, no integration connected; shown from start while no
integration is connected; a metal button press leaves it for that mode, since Agents works without any
integration, and connecting an integration leaves it for the current mode): the welcome
screen itself, so the deck looks the same at power-on, while idle and after quit. Keys 1, 2, 3, 5 and 6
are the welcome image's own tile crops (`resources/welcome-tiles/`, the bytes the quit and pre-burn
paints use), drawn as they are, never offset. Key 4 is the CONNECT tile, laid out as an Agents tile
with key 4's Agents offset: the Stigg mark rasterized from `brand/stigg-mark-white.svg` (never the
`design/*-mono.svg` files) in the glyph box and `CONNECT` 1× white in the meter band (41 px, x 12–52
before key 4's dx of −1: the one element wider than the Agents box, still inside key 4's safe rect
x 0–61); pressing it
opens the settings window. No other token field is composed: the tiles are 40 px apart horizontally
and 39 px vertically behind the bezels (pitch 104 × 103), so a burst drawn on one 192 × 128 canvas
would break at every bezel, and the welcome screen already follows the device rules (3 px tokens on a
5 px pitch, unlit `#2C2F2B`, no lit token within 14 px of a window edge, nothing in the 6 px rim). No
animation: when idle, the only periodic writes are `CONNECT` and the repaint keepalive from section 3.

**Custom modes** — tile = optional icon (PNG/SVG from the mode file, rasterized to 28 px) centred at
(32, 21) + label 1× white, at most two lines broken at spaces, glyph rows 40–46 and 48–54, each line
centred and cut to 50 px measured (the widest a layout can be and still be centred on keys 3 and 6);
design box x 7–56, y 7–54, offset per key like every layout; a `null` tile is the empty slot. The
schema validation reports any label line it had to cut. The middle metal button acts on release:
released within 800 ms it selects Sessions; held 800 ms it opens the picker instead, without showing
Sessions first. With no files in `~/.tokendeck/modes/` a hold just selects Sessions. The picker lists
custom modes one per tile; any metal button leaves it.

## 6. The three modes (spec restated with decisions)

Shared: the three metal buttons always select Agents / Sessions / Models & Usage; the current mode
persists across restarts; one **selected session** is shared by all modes; knob actions never apply
to an unknown session (overlay `NO SESSION`); unsupported actions show `NOT | AVAILABLE`.

**Agents.** Tiles as above. Main knob: cycle through the registered coding-agent windows (the
terminal windows/tabs of known sessions, Cursor, VS Code with Amp; Devin's browser tab is not
tracked), click = back to the previous window. Left knob: change the default model of the selected
session's agent (overlay `SONNET | NEXT | SESSION`), click = restore the agent's default. Right
knob: effort the same way (`HIGH | EFFORT` then `NEXT | SESSION`).

**Sessions.** Tiles as above, newest activity first, positions stable while the page is shown;
status and ring update in place. Main knob pages six at a time; click jumps to the next session that
needs you (approval or input), or back to page 1 when none. Left knob filters by agent, right knob by
status (ALL, WORKING, NEEDS YOU, IDLE, DONE), clicks clear. Pressing a session focuses its window
and selects it; if it needs approval, focusing is all we do (the prompt is in that window). Filters
and page survive mode switches.

**Models & Usage.** Tiles = favorite models of the selected agent (defaults: Claude Code → Opus,
Sonnet, Haiku, Fable; Codex → `model/list` from its app-server, whose default response is already the
non-hidden models: the first six are the tiles and the `isDefault` model is the restore target;
OpenCode → the models in its config, first six). Press = set as the agent's default model
(`NEXT | SESSION`). Main knob: effort (only the levels the agent supports; Claude Code
`LOW MED HIGH XHIGH`; Codex exactly the selected model's `supportedReasoningEfforts[].reasoningEffort`
from `model/list` (it differs per model), knob click = that model's `defaultReasoningEffort`;
OpenCode none), click = toggle Ultracode (Claude Code only). Left knob: selected agent (click = back
to the agent of the last selected session). Right knob: preview `READ ASK AUTO FULL`, click = apply;
FULL opens a confirmation dialog in the desktop app and applies only when confirmed there (and shows
`CONFIRM ON | COMPUTER` on the deck). When the Codex app-server is not reachable or not signed in,
the Codex model and effort tiles show `NOT | AVAILABLE`; there is no static fallback list.

Usage windows use the provider's real windows: Claude Code `5H` and `7D` (one shared pool across all
its models, so every tile says `■ SHARED`); Codex `primary`/`secondary` windows labelled by their
`windowDurationMins` (300 → `5H`, 10080 → `7D`, otherwise `15M`-style; never "hourly"), shared across
its models.

## 7. Integrations

Each integration implements `Integration { id, capabilities(), detect(), sessions(), usage(),
setModel(), setEffort(), setPermission(), setUltracode?(), launch(), focus(session) }` and declares
what it supports; the controller disables the rest. Capability matrix for v1:

| | Launch/focus | Sessions + status | Context ring | Usage windows | Model default | Effort default | Permission default | Ultracode |
|---|---|---|---|---|---|---|---|---|
| Claude Code | yes | yes (`claude agents` + hooks) | yes (status line) | yes (status line, while a session runs) | yes | yes | yes | yes |
| Codex | yes | yes (app-server status; verify TUI visibility) | no (unknown ring) | yes | yes | yes | yes | no |
| OpenCode | yes | yes when its server runs | no | no | yes | no | yes (permission config) | no |
| Cursor | yes | no | no | no | no | no | no | no |
| Amp | yes (VS Code / terminal) | no | no | no | no | no | no | no |
| Devin | opens app.devin.ai | no | no | no | no | no | no | no |

**Claude Code.** Docs: https://code.claude.com/docs/en/agent-view.md (`claude agents --json`),
hooks.md, statusline.md, settings-reference.md, settings.md, env-vars.md. Read them before coding;
the names below come from them.
- **Live sessions, the supported way:** `claude agents --json --all` every 2 s. Each entry:
  `cwd`, `kind` (interactive | background), `startedAt`, `sessionId`, `name` (by default
  `<cwd basename>-<2 chars>`, e.g. `my-app-3f`; the user's `/rename` or `-n` name when set), `pid`
  and `status` (busy | waiting | idle) while the process lives, `waitingFor` ("permission prompt",
  "input needed", …), `state` for background sessions. Map: busy → Working; waiting + "permission
  prompt" → Needs approval; waiting + other → Needs input; idle → Idle; gone from the list → remove.
  **Tile title = `name`** (uppercased per section 5); the first words of the `UserPromptSubmit`
  prompt are used only until the first poll returns or when `name` is absent (older Claude Code).
- **Hooks for instant transitions and extra data** (installed by the first-run wizard, with consent,
  after backing up `~/.claude/settings.json` once to `settings.json.tokendeck-backup`). Every hook is
  `type: "command"`, **never `type: "http"`**: an HTTP hook that cannot connect is a non-blocking
  error that prints a hook-error notice in the user's transcript on every prompt, Stop, permission
  prompt and notification while Token Deck is quit, crashed or not yet started at login, and
  `SessionStart` does not support `http` at all. One shim, `~/.tokendeck/bin/hook` (mode 755), which
  never prints and always exits 0:

  ```sh
  #!/bin/sh
  u=$(cat "$HOME/.tokendeck/url" 2>/dev/null) || exit 0
  [ -n "$u" ] || exit 0
  curl -s --connect-timeout 1 --max-time 2 -o /dev/null -X POST "$u/hooks/claude" \
    -H 'content-type: application/json' --data-binary @- \
    -H "x-td-pid: ${CLAUDE_PID:-}" -H "x-td-entrypoint: ${CLAUDE_CODE_ENTRYPOINT:-}" \
    -H "x-td-term: ${TERM_PROGRAM:-}" -H "x-td-term-session: ${TERM_SESSION_ID:-}${ITERM_SESSION_ID:-}${WT_SESSION:-}" \
    -H "x-td-tty: $(ps -o tty= -p "${CLAUDE_PID:-$PPID}" 2>/dev/null)" \
    >/dev/null 2>&1
  exit 0
  ```

  The app writes its base URL `http://127.0.0.1:<port>/t/<token>` (the per-install token from
  housekeeping (b)) to `~/.tokendeck/url` at start and deletes the file on quit, so while Token Deck
  is not running the shim exits before spawning curl; after a crash the file remains, curl gets an
  instant connection-refused, and the shim still exits 0. The stdin JSON is posted untouched as the
  body; the terminal identity used for focusing travels in headers (no jq). The settings entry is
  `"command": "sh ~/.tokendeck/bin/hook 2>/dev/null || true"`. Install it with `"async": true` on
  `UserPromptSubmit`, `Stop`, `Notification` (matcher
  `permission_prompt|idle_prompt|agent_needs_input|agent_completed`), `PermissionRequest` and
  `PostModelSwitch` (async hooks are fire-and-forget), and synchronously with `"timeout": 2` on
  `SessionStart` and `SessionEnd` (SessionEnd's default budget is 1.5 s; the shim's `--max-time 2`
  fits either way). Do not install `PreToolUse` or `PostToolUse`: `UserPromptSubmit` plus the 2 s
  poll already give Working. Hook inputs carry `session_id`, `cwd`, `permission_mode`,
  `effort.level`; `Stop` carries `last_assistant_message`; `UserPromptSubmit` carries `prompt`;
  `PermissionRequest` fires immediately when a prompt appears (the `permission_prompt` notification
  waits ~6 s).
- **Status line** (for the context ring and rate limits): the status line must be a `command`, and
  it must **chain** the user's existing one: the shim `~/.tokendeck/bin/statusline` reads stdin once
  (`in=$(cat)`), fires the POST in the background without waiting
  (`u=$(cat ~/.tokendeck/url 2>/dev/null) && [ -n "$u" ] && { printf '%s' "$in" | curl -s -m 1 -o
  /dev/null -X POST "$u/statusline" -H 'content-type: application/json' --data-binary @- >/dev/null
  2>&1 & }`), then `printf '%s' "$in" | exec <original command>` (saved in
  `~/.tokendeck/statusline-original.json`), so their display is unchanged and never waits on Token
  Deck; with no original command it prints nothing and exits 0. Fields: `session_id`, `model.id`,
  `model.display_name`, `cwd`, `context_window.used_percentage` (null early in a session → dashed
  ring), `effort.level`, `rate_limits.five_hour.used_percentage`,
  `rate_limits.seven_day.used_percentage`, each with `resets_at` (Unix epoch seconds; present only
  for claude.ai subscribers after the first API response; a window is dropped once it passes). The
  Desktop app may not run a custom status line; hooks and `claude agents` still work there.
- **Terminal identity for focusing:** the SessionStart shim's headers carry `CLAUDE_PID`,
  `CLAUDE_CODE_ENTRYPOINT` (`claude-desktop` in the Desktop app), `TERM_PROGRAM`, `TERM_SESSION_ID`
  (Terminal.app), `ITERM_SESSION_ID`, `WT_SESSION` (Windows Terminal) and the tty
  (`ps -o tty= -p $CLAUDE_PID` prints `ttys003` without `/dev/`; prefix it). For sessions found only
  through `claude agents --json` (no hook yet), derive the same from the `pid`: `ps -o tty= -p PID`
  and `ps -Eww -o command= -p PID` for `TERM_PROGRAM`. Focus, by `TERM_PROGRAM` (all AppleScript via
  `osascript` with the tty passed as an argument):
  - `Apple_Terminal`: loop `windows` → `tabs`, `if tty of t is theTTY then set selected of t to true,
    set frontmost of w to true, activate`.
  - `iTerm.app`: loop windows → tabs → sessions, match `tty of s` (or `id of s` = the UUID after the
    colon in `ITERM_SESSION_ID`), then `select s`, `select t`, `select w`, `activate` (all three
    levels are needed).
  - `ghostty` 1.4+: `focus (first terminal whose tty is theTTY)`; on 1.3.x match `working directory`.
  - `WarpTerminal`, Kitty and unknown terminals: activate the app (`open -b <bundle id>`).
  - `vscode` / Cursor terminals: `code -r <a file in cwd>` / `cursor -r <file>` focuses the owning
    window; fallback System Events `AXRaise` on the window whose name contains the folder name.
  - Desktop app sessions (`CLAUDE_CODE_ENTRYPOINT=claude-desktop`, no tty): run
    `claude --desktop --resume <sessionId>` (v2.1.285+), which opens that session in the Desktop
    app; check whether it focuses an already-open session or duplicates it, and fall back to
    activating Claude.app.
  Window cycling (Agents mode main knob): System Events over an allowlist of bundle ids (the
  terminals above, Cursor `com.todesktop.230313mzl4w4u92`, VS Code `com.microsoft.VSCode`, Codex
  `com.openai.codex`, Claude `com.anthropic.claudefordesktop`), `set frontmost` + `perform action
  "AXRaise"`; needs the Accessibility permission. Launch when nothing runs: open a new window in the
  user's default terminal running `claude`. macOS asks for Automation (per target app) and
  Accessibility once; put `NSAppleEventsUsageDescription` in the app's Info.plist (section 12) or the
  prompts never appear, and let the wizard trigger them on purpose. Windows: best effort only —
  `SetForegroundWindow` on the terminal process's main window (it may only flash the taskbar);
  no tab-level focus in v1.
- **Usage:** keep the last `rate_limits` object received with the time it arrived, persisted in
  electron-store so it survives restarts. Tiles show those values; when older than 10 minutes the
  lit squares switch to `#5B5D59`, the percents to `#838682`, and the bottom label becomes `STALE`
  (`#838682`, in place of `SHARED`; a tile label, not an overlay) (spec: a disconnected
  integration shows its last known data as stale); after 24 h, or when a window's `resets_at` has
  passed, show the unlit row and `--`. **Never read Claude Code's credentials** (the Keychain item
  `Claude Code-credentials` or `.credentials.json`) and never call Anthropic's undocumented OAuth
  usage endpoint: Claude Code's legal-and-compliance doc says developers may not collect, store or
  intermediate Claude.ai credentials or session tokens, and Claude Code's own token refresh rewrites
  the Keychain item's ACL so a `security` read would prompt for the login password on every poll.
  `claude auth status --json` (supported) tells login state and plan for the Agents page.
- **Defaults** (read-modify-write `~/.claude/settings.json` as strict JSON, preserving unknown keys;
  running sessions hot-reload hooks and the status line but read `model`/effort only at start):
  `model` (`opus` | `sonnet` | `haiku` | `fable`), effort as
  `modelSettings.<canonical model id>.effortLevel` (`low` | `medium` | `high` | `xhigh`; a top-level
  `effortLevel` is ignored by Opus 5.5+ in user settings), `ultracode` (boolean),
  `permissions.defaultMode` (READ → `plan`, ASK → `default`, AUTO → `auto`, FULL →
  `bypassPermissions` after the desktop confirmation, refused with `NOT | AVAILABLE` when
  `permissions.disableBypassPermissionsMode` is set; `auto` and `bypassPermissions` only work from
  user-scope settings, which is where we write). Show `NEXT | SESSION` after every change. "Restore my
  settings" puts the backup back byte for byte. Watch the file with chokidar: `/model` and
  `/effort` write it too, and the deck must show what is really there.
- **Housekeeping that bites:** (a) a GUI app launched from Finder or login items does not get the
  shell PATH — resolve `claude`, `codex`, `opencode`, `code`, `cursor` once through the login shell
  (`/bin/zsh -lic 'command -v claude'`, `cmd /c where claude` on Windows) and known locations,
  including Claude Desktop's bundled binary under `~/Library/Application Support/Claude/claude-code/<version>/…/claude`;
  (b) the listener binds `127.0.0.1` only, its base URL carries a per-install random token
  (`http://127.0.0.1:<port>/t/<token>`; the port may change per launch, nothing in settings.json
  carries it), and it rejects any other path; (c) feature-detect the installed Claude Code version
  (`claude --version`): `modelSettings` needs 2.1.251+; on older versions use the top-level
  `effortLevel`.
- **Windows:** install `%USERPROFILE%\.tokendeck\bin\hook.ps1`
  (`try { $u = Get-Content "$env:USERPROFILE\.tokendeck\url" -ErrorAction Stop; $b = [Console]::In.ReadToEnd(); Invoke-RestMethod -Method Post -Uri "$u/hooks/claude" -ContentType 'application/json' -TimeoutSec 2 -Body $b | Out-Null } catch {}; exit 0`)
  and register it in exec form with the absolute path the installer knows:
  `{"type":"command","command":"powershell.exe","args":["-NoProfile","-ExecutionPolicy","Bypass","-File","C:\\Users\\<user>\\.tokendeck\\bin\\hook.ps1"]}`
  (the docs' own Windows pattern; works with or without Git Bash). The status line on Windows is
  chained only when Git Bash is present (`CLAUDE_CODE_GIT_BASH_PATH` or
  `C:/Program Files/Git/bin/bash.exe`); otherwise skip it and rely on the poll, and say so on the
  Agents page.

**Codex.** Docs: https://developers.openai.com/codex/app-server.md, config-reference.md,
config-advanced.md, hooks.md. Current CLI 0.166.x.
- Spawn `codex app-server` (stdio, newline-delimited JSON-RPC without the `jsonrpc` field). Send
  `initialize` `{clientInfo: {name: "token-deck", version}}` then the `initialized` notification.
  Sessions: `thread/list` (`sortKey: "recency_at"`, page by `nextCursor`) → `Thread` with `id`,
  `name` (title when non-null, else `preview`), `cwd`, `model`, `reasoningEffort`, `updatedAt`, and
  `status` ∈ `{type: "notLoaded"}` | `idle` | `systemError` | `{type: "active", activeFlags:
  ["waitingOnApproval" | "waitingOnUserInput"]}`; live changes arrive as `thread/status/changed`,
  `turn/started`, `turn/completed`, `item/*`. Never answer `item/*/requestApproval` server requests
  (the deck is not the approving client). Models and efforts: `model/list` → `Model { id,
  displayName, hidden, supportedReasoningEfforts, defaultReasoningEffort, isDefault }` (section 6).
  **Verify on day one** whether threads driven by a running `codex` TUI show as `active` to our
  separate app-server; if not, use Codex's hooks (`~/.codex/hooks.json`, events `SessionStart`,
  `UserPromptSubmit`, `PermissionRequest`, `Stop`, `SessionEnd`, command handlers with stdin JSON like
  Claude Code's) plus the rollout files under `~/.codex/sessions/YYYY/MM/DD/` for titles and activity.
  **Never write `notify`**: it is a single program slot, the hooks carry the same data, and on
  Gabriel's own machine the slot is already taken; if a line starting with `notify` exists, leave it
  byte for byte.
- Usage: `account/rateLimits/read` → `rateLimits.primary` / `secondary` =
  `{usedPercent, windowDurationMins, resetsAt}` (ChatGPT sign-in only), updates via
  `account/rateLimits/updated`. `usedPercent` is used, not remaining.
- Defaults in `~/.codex/config.toml`: `model`, `model_reasoning_effort` (free string; valid values are
  the selected model's `supportedReasoningEfforts` from `model/list`; never write a value the model
  does not advertise), and the permission pair `approval_policy` (`on-request` default | `never`;
  `on-failure` is deprecated, never write it) + `sandbox_mode` (`read-only` default |
  `workspace-write` | `danger-full-access`): READ → `read-only` + `on-request`; ASK →
  `workspace-write` + `on-request`; AUTO → `workspace-write` + `never`; FULL → `danger-full-access` +
  `never` after the desktop confirmation. Before the first edit copy `~/.codex/config.toml` once to
  `config.toml.tokendeck-backup`; "Restore my settings" (section 10) puts it back byte for byte, same
  as `settings.json`. Edit `config.toml` line-wise (replace the top-level `model = …`,
  `model_reasoning_effort = …`, `approval_policy = …`, `sandbox_mode = …` lines in place, insert
  missing ones before the first `[table]` header; "top-level" means the region before the first `[`
  header, a `model =` inside `[profiles.*]` is never touched) so comments and everything else survive;
  JS TOML libraries do not preserve comments. Codex asks the user to trust non-managed hooks the first
  time; the wizard says so.
- Focus/launch like Claude Code (process name `codex`, same tty logic via the SessionStart hook).

**OpenCode.** Docs: https://opencode.ai/docs/server/, /docs/config/, and for v2
https://opencode.ai/v2/docs/. Detect the major version with `opencode --version`.
- Not installed on this Mac; install it yourself at build step 6: `npm i -g opencode-ai` (today
  1.19.x, the v1 branch below; `brew install opencode` would install 2.x and exercise the v2 branch).
  No sign-in needed: OpenCode ships free Zen models (e.g. `opencode/big-pickle`; the live list is
  `/models` in the TUI; per-IP rate limits). Do not try to sign OpenCode into Gabriel's Claude
  subscription (Anthropic blocks third-party OAuth there and accounts have been suspended for it). For
  the section 15 check run `opencode serve --port 4096`, then in another terminal
  `opencode run --model opencode/big-pickle 'list the files in this folder'` so a real session with a
  tool call exists. Only if no free model is listed that day: build v1 against the documented shapes
  with recorded fixtures and label OpenCode "built from docs, untested on this Mac" in the README and
  on the Agents settings page.
- v1 (1.19.x, current npm `latest`): sessions only when a server is reachable: the URL from settings
  (default `http://127.0.0.1:4096`, basic auth `opencode:$OPENCODE_SERVER_PASSWORD` when set).
  `GET /global/health`, `GET /session` (`id`, `title`, `time.updated`), `GET /session/status`
  (non-idle sessions: `busy` | `retry`), SSE `GET /event` for `session.status`, `session.idle`,
  `permission.updated` (→ Needs approval) and `permission.replied`. A TUI started without `--port`
  listens on a random port and cannot be discovered; the Agents page says "Run `opencode serve` to
  show sessions".
- v2 (when installed): read `~/.local/state/opencode/service.json` (`url`, `password`), then
  `GET /api/info`, `GET /api/session`, `GET /api/session/active`, SSE
  `GET /api/event?types=session.status&types=permission.asked&types=permission.replied`.
- Model default: `model` ("provider/model") in `~/.config/opencode/opencode.json`; permission via its
  `permission` map (v1) / `permissions` array (v2); no quota API. Focus/launch via the terminal.
  Tile title: `title`.

**Cursor / Amp / Devin.** `focus()` activates the app (Cursor.app, VS Code for Amp, the browser for
Devin at https://app.devin.ai); `launch()` opens it. Their tiles show the white glyph with `LAUNCH`
when installed (section 5) and never a session meter; nothing else is claimed.

## 8. Program it yourself

`~/.tokendeck/modes/<name>.json`, watched with chokidar, validated with a JSON schema that the
settings window shows errors for:

```json
{
  "name": "Deploy",
  "tiles": [
    { "label": "BUILD",  "icon": "~/icons/hammer.svg", "action": { "type": "shell", "command": "npm run build", "cwd": "~/dev/app" } },
    { "label": "LOGS",   "action": { "type": "url", "url": "https://grafana.example.com/d/abc" } },
    { "label": "EDITOR", "action": { "type": "open", "app": "Cursor" } },
    { "label": "PALETTE","action": { "type": "keys", "keys": "cmd+shift+p" } },
    { "label": "AGENTS", "action": { "type": "mode", "mode": "agents" } },
    null
  ],
  "knobs": {
    "main":  { "cw": { "type": "keys", "keys": "cmd+=" }, "ccw": { "type": "keys", "keys": "cmd+-" }, "click": { "type": "shell", "command": "say done" } },
    "left":  null,
    "right": null
  }
}
```

Shell actions run in the user's login shell with a 10 s timeout and show `OK`/`FAILED` as an
overlay; keystrokes go through AppleScript `System Events` on macOS and PowerShell `SendKeys` on
Windows. Entering: hold the middle metal button 800 ms → picker (section 5, Custom modes: the button
acts on release, so a hold never shows Sessions first). Files are hot-reloaded by the
watcher; the Modes page's Reload button calls the same loader by hand if a save is missed. The site
documents this format.

## 9. Burn (the welcome screen)

The `LOG` frame carries a 320 × 240 JPEG for the whole panel; the six key windows are regions of it.
The vendor documents it as the startup background written to ROM; the device shows it at power-on and
after every firmware restart, and as the background behind the tiles while the host runs. It is the
only thing the deck keeps without Token Deck: a deck that was burned once shows the welcome screen on
any computer, with nothing installed, until something overwrites it (a new unit shows the vendor's
VSD/Mirabox logo until then). On Gabriel's unit it holds the final welcome screen, v8 (step 3,
`device/welcome/`), burned on Nov 3 (18.9 KB, q97; write report received, photo and replug check
pending, step 3). Ten writes have been accepted so far (1.8, 8.3, 10.9, 11.1, 11.4, 14.2, 15.8, 15.9,
18.9 and 22.3 KB), each confirmed by the device's write report, three of them checked after a power
cycle, four in one power cycle; writes failed only when no tiles had been painted first in that
session, or after a failed write (`device/NOTES.md`). `device/burn_logo.py` is the reference implementation of the whole burn, without its `--dc` and `--dc-only`
options, which the app never has; `device/welcome/welcome_v8.py` is the reference for the image.

**When the app writes it.** Three paths, one code path (`burn/burn.ts`, step 4):

- On first connect: when Token Deck sees a deck whose serial is in neither electron-store
  `burnedSerials` nor the shipped `resources/preburned.json` (the list the batch writes for the
  giveaway decks, step 5), whatever image it was written with, it waits until 8 s after the deck
  appeared in `HID.devices()` without opening it (the deck shows its boot image meanwhile), then writes
  the welcome screen once (step 4), records `{serial, imageHash, at}` once the burn's hold has ended
  without an error, logs it and shows a tray notification. There is no read-back, so these two records
  are the only way to know a deck already has the picture. One flash write per deck (section 1): a deck
  in either record is never rewritten automatically, also after an update changes the picture; the
  record keeps the image hash so the Burn page can list which picture each deck has. An empty
  `serialNumber` is never recorded: the automatic path skips such a deck and logs it (the Burn page
  button still works). A giveaway deck missing from `resources/preburned.json` (a release tagged before
  the batch) gets one more, identical write from the attendee's app. Burn page toggle "Write the
  welcome screen to new decks automatically", default on.
- The Burn page button: always writes, after one confirmation ("Write the welcome screen to this deck
  again?", naming when this computer last wrote that deck), because it is the only way back after
  another tool replaced the boot image, or to give a deck a newer picture; then it updates the record.
  It is disabled while a burn runs, and after a failed burn until the deck has been replugged.
- The batch CLI (step 5) for the giveaway decks, so attendees see the welcome screen before they
  install anything.

Steps:

1. **Resolution: done.** 320 × 240 as seen, 240 × 320 on the wire, verified on this firmware: the
   test 13 card showed one sixth of the image in each window (coarse), the test 14 ruler gave the window
   rects (±2 px) and test 15's frame tiles the tile rects (±1 px) that `device/panel_geometry.py`
   records, and Gabriel's photos of the burned v6 and v7
   show them as designed. No vendor-app check (the vendor app is an untested writer on this deck).
2. **Panel geometry: done for this firmware.** `device/panel_geometry.py` has the measured tile rects
   and window rects (section 3); copy them into `resources/panel-geometry.json` as half-open rects
   [x0, x1) × [y0, y1), as the welcome generator uses them (centres are pixel-edge coordinates, so a
   box with inclusive pixels x0..x1 has its centre at (x0 + x1 + 1) / 2). How they were measured, for
   a deck with other firmware only (`burn/calibrate.ts`, run as `tokendeck calibrate`; never in the
   settings window or the wizard, and not re-run on Gabriel's unit): burn the verified ruler (ship
   `device/boot-image/test-ruler-sent.jpg`, 22,307 bytes, as `resources/calib-ruler-240x320.jpg`;
   `device/calib_images.py` made it: an x and a y ruler with coordinates crossing in each window), then
   paint the 64 × 64 frame tile (magenta border, checkerboard) on all six keys (`device/paint_tiles.py`,
   RAM only) and photograph the deck straight on: each window's edges and each tile's position read
   directly off the rulers. Calibration asks once ("This replaces the welcome screen until calibration
   ends"), removes the deck from `burnedSerials`, and when the user finishes or cancels it writes the
   welcome screen back with the step 4 sequence (in the same power cycle when the ruler got its report,
   otherwise after a replug): two flash writes per calibration.
3. **The welcome screen (final: v8, Nov 3).** Gabriel's brief: the tokens pattern on black, the Stigg logo,
   the slogan "The AI Usage Management Console" and the URL, mostly the token explosion; "think as an
   expert and make it perfect". His notes on v6 as burned: bring back v1's white tokens and its dim
   "background" tokens, make the tokens a little smaller like the stigg.io hero's particles, make the text
   slightly larger. His notes on v7: tokens in the URL's key too ("it might be complementary"), no big gap
   between the tokens and the window edges, URL bottom left and slogan bottom right. v8 is
   `device/welcome/welcome-320x240.png` (and `welcome-sent.jpg`, the exact bytes to burn), made by
   `device/welcome/welcome_v8.py` (helpers in `v8_common.py`, which builds on `v7_common.py` and
   `welcome_v7.py`) after a design panel of four designs and four critics (`device/NOTES.md`, "Welcome
   screen v8"; the brief and every candidate in `device/welcome/v8/`). v1 to v7 are kept next to it as
   earlier directions.
   - Key 1: the official `stigg-logo-on-dark.svg`, rasterized at 20× by headless Chrome, 60 × 17 px at
     its exact aspect, at (20, 50), alone and centred, clamped so no pixel is darker than `#131512`.
   - Key 4, under the logo: `io.stigg.io` / `/usage`, Söhne Buch 10.5 px on 13 px leading, tracking
     -0.06 px, white, flush left, ink x 28-71 / y 156-178, centred on its window. 10.5 px is the first size
     whose hinted cap height and x-height (8 and 6 px) are larger than 9.5 px's (7 and 5 px).
   - Key 6: `The AI Usage` / `Management` / `Console`, Söhne Buch 9.5 px on 12 px leading, tracking
     -0.06 px, white, flush right on x 291 (the tile's last column), cap top 152. That is as large as key 6
     allows: a right-column tile hugs its window's left edge, so the key holds 58 px (x 234-291) and centres
     only 50 px, and `Management` inks 57 px at 9.5 px and 62 px at 10.5 px. Flush right puts the slogan's
     visual mass 1 px from the window centre (flush left: 7 px) and mirrors the flush-left URL.
   - Type pipeline: every glyph sits at its exact shaped x (sub-pixel), composited with gamma 1.5. `i`,
     `I` and `l` are one crisp, fully lit column; each `i` has a crisp one-pixel dot on the cap-top row
     with an empty row under it; each period is one crisp pixel in the middle of the gap between its
     neighbours' ink. The `/u` kern is dropped.
   - Boards: each of keys 2-5 shows the largest board of 3 px tokens on a 5 px pitch that stays inside its
     tile and is centred on its window to 1.5 px (`v8_common.BOARDS`):
     - key 2: 12 × 13, x 130-187 / y 28-90;
     - key 3: 11 × 13, x 239-291 / y 28-90;
     - key 4: 12 × 11, x 21-78 / y 141-193;
     - key 5: 12 × 11, x 130-187 / y 141-193.
     Each board is on its own lattice phase, and every cell is an unlit `#2C2F2B` token unless lit.
   - Key 4's board leaves a clean window for the URL: no token within 4 px beside it or 7 px above and
     below it, and inner tokens keep 10 px after a line's end. The field steps back in after `/usage`.
     Three lime tokens have landed on it (two on the floor, one above); key 4 has no white token, because
     there white is the type.
   - Lit tokens are lime `#92E759` and white `#FFFFFF` (white 0.371 of all bright), plus three `#639840`
     depth tokens at the far end. The After Tokens explosion: a solid lime source block in key 5 (x 140-157,
     y 161-188) frays at its top, and its debris breaks off the top-right corner. It rises through key 2 on
     a diagonal and settles in key 3 as dust. The seed (7) was chosen by eye among the seeds that pass
     every rule.

   The rules the generator enforces, the reason for every number:
   - All content inside the six tile rects (the app's tiles cover it exactly at runtime).
   - Nothing within 6 px of a window edge (the keycap rim). No lit token closer than 14 px to a window
     edge: v7's nearest lit token sat at 14 px and was mirrored in the bevel (the v7 photo shows tokens
     14-20 px in mirrored, lit and unlit); v8's nearest lit tokens are at 15-16 px and its dim boards at
     6-12 px, so bevel ghosts remain possible. That is the price of Gabriel's "no big gap" note.
   - No pixel darker than `#131512`.
   - The art rules: no runs, dotted lines, clumps or side-by-side pairs; nothing lit on a board's outer
     ring; at least a third lime in every key; debris only off the source's top-right corner, and no
     ledges; the sides of key 2 and key 5 that face the logo and the slogan stay dark.
   - Cells that share an 8 × 8 JPEG block with window pixels outside the tiles stay unlit. No lime or
     depth token in a 16 × 16 chroma block that holds such pixels, because it tints them.
   - On the JPEG as burned (q97, 4:2:0, 18.9 KB; the deck accepted it on Nov 3, write report after 0.26 s),
     no window pixel outside the tiles more than 4 luma levels (worst 3.2) or 10 levels in any channel
     (worst 7, at the logo's left edge as in v7) off `#131512`, so no halo frames the app's tiles.

   Status (Nov 3): the deck accepted v8 (write report at 0.26 s), but its photo and replug check are
   pending (`device/NOTES.md`, end of "Welcome screen v8"; no replug check is recorded for v6 or v7
   either). Three items are on watch: the board tokens 6-8 px from the window edges, in the bevels
   (fallback: 12 rows in keys 2 and 3, y 29-86); the frame columns 4 px beside the URL; and the g of
   "Management" 3 px above the C of "Console". Before committing `resources/welcome-*`, before the
   giveaway batch and before the release tag, get Gabriel's photo of v8 at power-on with nothing running
   (the unboxing view) and a replug check. Any change is his call and goes back through `welcome_v8.py`
   on this Mac (the kit's `site-fonts/` is here); the app never redraws it. The automatic path writes
   each deck once (section 1), so a picture changed after the batch would leave every giveaway deck on
   v8 unless it is rewritten by hand.

   The image is rendered from the private kit on this Mac (Söhne never enters the public repo; the logo
   is committed under section 2's brand terms) and committed as `resources/welcome-320x240.png`,
   `resources/welcome-sent.jpg` (the exact burn bytes: 18,887 bytes, 240 × 320, baseline, 4:2:0, sha256
   `daea022363c85ef722c9c93bcd7f5379a995b726cb5240bc4ed92b12d15071fb`) and
   `resources/welcome-tiles/key1.jpg` to `key6.jpg` (`device/welcome/welcome_tiles.py`: the six crops
   exactly as `burn_logo.py` sends them, Pillow q100 4:2:0, 2.7-5.2 KB each; they are the pre-burn paint,
   the quit paint and the idle screen). Copy these bytes from `device/welcome/` (`welcome-tiles/`);
   never re-render or re-encode them (another FreeType or Pillow changes the hinted type and the hash).
   `imageHash` is the sha256 of `welcome-sent.jpg`. The app burns those bytes and shows the PNG on the
   Burn page; "Export image" saves an upright 320 × 240 JPEG encoded from the PNG (q97, 4:2:0), never the
   sideways burn bytes. The smoke step (section 12) fails if these resources are missing from the
   packaged app.
4. **Burn**, in the rhythm verified on this unit (`device/burn_logo.py`: libtransport's `LOG` → read →
   `STP` → 1 s, plus the tile paint this firmware needs). The vendor SDKs' `DIS` + clear-all + `STP`
   before `LOG` is untested here; do not substitute it. A burn is one item of the write queue (section 3):
   from its handshake to the end of its hold nothing else goes out (no mode tiles, overlays, repaint
   keepalive or replay; the heartbeat waits until the hold starts), deck input is ignored, and quit
   waits for it. A write still unresolved after 5 s is a write error: the burn has failed; abandon the
   handle as section 3 says, without awaiting its close, and end the burn item so the queue and quit
   move on. The sequence:
   1. Validate `resources/welcome-sent.jpg`: 240 × 320, baseline, at most 22,307 bytes (the largest
      verified write). On Windows, re-run the vendor-app process check (section 3) right before the
      burn and wait while one runs.
   2. On the first-connect and batch paths, start no sooner than 8 s after the deck appeared in
      `HID.devices()`, with nothing opened in between; the Burn page button and calibration's
      write-back start at sub-step 3 on the deck the app already holds (v1 followed test 15's connection
      in its power cycle, and v2-v4 each followed an earlier successful run). The post-replug successes with a recorded wait had waited 8 s (test 13) and 15 s
      (test 14); v6 was burned "right after the deck was plugged in" with no time recorded; the 3 s
      attempt (test 7) failed, though without tiles, and test 13 changed both against test 7 (it added
      tiles first and a longer settle), so tiles and settle were never separated. Shorten the wait only after a bench test on Gabriel's deck passes three times in a
      row (plug in, burn at the shorter wait, replug, look).
   3. A fresh handle: if the app holds the deck, close it, wait 1 s and reopen (every accepted write
      was the only `LOG` of its connection; two `LOG`s on one handle were never tried). Handshake. The
      burn's handle skips section 3's `getFeatureReport` reads (the batch reads the firmware string
      after the hold, before it closes).
   4. 0.5 s with nothing sent.
   5. The six crops `resources/welcome-tiles/key1-6.jpg`, each as a `BAT` header + its chunks, then
      `STP`.
   6. 1 s with nothing sent.
   7. The `LOG` header and all its chunks as one unbroken stream.
   8. Wait for the write report (`ACK\0\0OK\0\0` + code `0x00` + state `0x00`; 0.12-0.26 s after the
      last chunk for 8-22 KB on record), sending nothing at all, the heartbeat included; give up after
      10 s.
   9. `STP`. **The burned image replaces the whole panel at once, tiles included.**
   10. 1 s with nothing sent. Then repaint the current tiles (test 14 painted tiles 1 s after its `STP`
       and its 22 KB image persisted; the first-connect burn runs before the first tile paint anyway) and
       keep the handle open 10 s more, sending `CONNECT` at the start of the hold and every 10 s and no
       `CLE`, `HAN` or other `LOG` (the
       batch closes after that).

   **Failed burn.** No report within 10 s, or a write error anywhere in the burn, is a failed burn.
   Send no `STP` (after an unanswered `LOG`, an `STP` left the panel black before any replug: the deck
   had booted lime after test 3, and tests 5 and 6 each sent `STP` after an unanswered `LOG`) and nothing else to that deck but the heartbeat: no tiles, no replay after a transport reopen
   or a resume, and on quit no welcome tiles (stop the heartbeat, close). Leave the serial unrecorded,
   log it, and show "The welcome screen was not written. Unplug the deck and plug it back in." on the
   Device and Burn pages, in the wizard and as a tray notification (section 14). The slot may now be
   blank (the deck may boot black) and the firmware ignores image writes until a power cycle, so only a
   replug re-arms the burn: after the deck has left `HID.devices()` and come back, the automatic path
   runs this step once more (one attempt per appearance, never after a reopen or a resume). After two
   failed automatic attempts on one serial it stops for that serial, and the Burn page says "Token Deck
   could not write the welcome screen to this deck."; its button still writes, after a replug. A write
   that fails mid-stream follows the same rule (the vendor warns that partial or out-of-bounds image
   data can deadlock the device).

   **Persistence.** Nothing on the panel tells a good burn from a bad one while a host has painted
   tiles: v8 is `#131512` outside the tiles, and the crops painted before the burn and on quit are the
   same picture. The write report is the app's only signal. Persistence is a QA step for this build
   (section 15), not an app step (the app never asks for a replug after a report): power-cycle the deck
   with Token Deck quit and look before anything opens it.

   This rhythm is verified only on `5548:1001` with firmware `V3.VSDN3_PXL.02.010`, through Python
   hidapi. The app's own path differs in ways no test separated: no GET_INPUT_REPORT firmware read
   first (node-hid cannot send one), each report started from the main event loop, an exclusive open.
   Section 15's first app burn on Gabriel's deck is the check; if it gets no report, ask Gabriel to
   replug and restore v8 as section 15 says before changing anything.
5. **Batch mode** for the team, on a Mac. Quit the Token Deck tray app and the vendor apps first (on
   macOS the open is exclusive, and a running Token Deck would grab each deck and burn it itself), then
   run `tokendeck burn --watch` (section 4: the packaged binary with that argument; it exits with "Quit
   Token Deck first: the tray app owns the deck." while the tray app runs). For each newly attached deck
   it runs step 4 (the 8 s settle included), prints manufacturer, product, `serialNumber`, `release` and
   the firmware string when it reads, and appends `{serial, imageHash, at}` to
   `~/.tokendeck/preburned.json`. It prints "done, unplug and plug the next" only after the 10 s hold. A
   deck listed in `~/.tokendeck/preburned.json` or the shipped `resources/preburned.json` with the
   current image prints "already burned, unplug" and is not written. A
   serial seen twice in one run prints a red warning (the per-serial records cannot tell those decks
   apart) and the batch goes on; an empty `serialNumber` prints "no serial". A failure prints in red
   "FAILED: this deck may now start black. Unplug it and plug it back in to retry." and the batch takes
   no new deck until that one has come back and been written: a deck whose last write failed must never
   ship, and whatever made it fail would blank the next deck too. Before the run: burn one deck from the
   giveaway stock, replug it with nothing running and look; confirm a second deck reports a different
   `serialNumber`; read one stock deck's firmware string with `device/probe_n3.py` (hidapi's input
   report; node-hid usually shows "n/a") and compare it with `V3.VSDN3_PXL.02.010`. The first deck of
   any other id or firmware string is burned alone and checked after a replug (boot image, tile
   alignment) before the batch continues with it. Ctrl-C prints the run's summary (burned and failed
   serials). To inspect a burned deck, stop the batch first (it would see the deck again), then replug
   it and look. Expect about 25 s per deck (the 2 s poll, the 8 s settle, the burn and its 10 s hold,
   the swap). After the run, commit the file as `resources/preburned.json`, then tag the event release
   (section 13). The Burn page's batch instructions are this paragraph.
6. `LOG` persists on this firmware (tests 3, 13, 14). For a deck whose firmware turns out not to keep
   it, the Burn page's "Export image" saves the upright 320 × 240 JPEG for the vendor app's Settings →
   Device → "Replace the boot logo" (the vendor's tutorial: restart or reconnect the device to see the
   new logo; a wrong resolution makes the upload fail; a reset does not restore the default logo). If a
   burn leaves the panel black, power the deck off and on and write the image again: that is the
   vendor's own recovery for a failed boot-logo write, and the only one that exists for the N3.

## 10. Settings window and first run

Window 960 × 640, Geist, DS values hand-written into `src/renderer/styles/tokens.css` (`#131512`
canvas, hairlines, mono uppercase labels in Geist Mono +0.03em, radii 4/8 px). Buttons follow the DS:
primary is white with ink text and turns lime on hover; the lime-filled accent button appears at most
once per page for its main action (Connect on Agents, Write welcome screen on Burn); ghost buttons for
the rest; lime otherwise only in the active nav item, eyebrows and status dots; icons are Lucide via
`lucide-react` with `strokeWidth={1} absoluteStrokeWidth`, sizes 16/20. Left nav: Device, Agents,
Models, Modes, Burn, About. The simulator sits in a bottom drawer on every page.

- **Device**: connection state (the device states of section 14, including a burn in progress and a
  failed burn, since notifications can be turned off), manufacturer/product/serial/release and the
  firmware string when it reads, brightness slider (default 70, the level `device/burn_logo.py`
  sets in its handshake for every welcome burn; the test photos were taken at 100 and the boot level is
  unmeasured; the user's choice persists; section 15 checks the
  boot brightness against it), keepalive toggle, "Send test pattern", "Calibrate knobs". No panel
  calibration here: it burns a ruler over the welcome screen, so it is the `tokendeck calibrate` CLI
  only (section 9 step 2).
- **Agents**: one row per integration with detection (installed? signed in? hooks installed?
  status line chained?), Connect/Disconnect buttons, the exact file edits listed before they are
  made, and a "Restore my settings" button that puts the backups (`settings.json`, `config.toml`)
  back.
- **Models**: favorites per agent (up to six, an ordered list with move up/down buttons), the effort
  levels per agent (read only), the permission mapping table (read only).
- **Modes**: the custom mode files, validation errors, "Open folder", "Reload", a JSON example
  button.
- **Burn**: preview, "Write welcome screen to deck" (section 9: always writes, after a confirmation),
  the "Write the welcome screen to new decks automatically" toggle, the list of decks this computer
  wrote (serial, date, image hash) and whether the connected deck is in `resources/preburned.json`,
  "Export image", batch mode instructions (section 9 step 5).
- **About**: version, "Check for updates" (on unsigned macOS it reads the latest version and offers
  "Update now", which reruns the installer, section 12), links to
  usage.stigg.io and the repo, licenses (MIT for the app, Geist OFL, agent logo sources, the MIT
  protocol references), "Show log" (the app logs to `~/.tokendeck/log/tokendeck.log`, rotated at
  5 MB; no telemetry).

Windows in v1 ships the device, the three modes with demo data, custom modes, burn, and the Claude
Code integration with Windows paths (`%USERPROFILE%\.claude`, `%USERPROFILE%\.codex`) and the
PowerShell hook shim (section 7); Codex and OpenCode on Windows are "detected, not connected" unless
they test clean in the Windows VM.

First run (a 6-step wizard): 1) plug in / quit StreamDock or VSD Craft, the idle screen lights up
(and, if this deck is in neither burn record, the welcome screen is written now and the step says so,
with the section 14 strings for a burn in progress, done and failed); 2) knob calibration: "turn the
left knob clockwise" → confirms the `0x90/0x91` vs `0x60/0x61` assignment and direction (section 3),
then the right knob, then "click the left knob"; 3) Claude Code: show the edits, Install; 4) macOS
only, permissions: "Token Deck brings the window of the session you pick to the front. macOS asks you
to allow that once for each app, and once in Privacy & Security → Accessibility." Button "Ask now":
run one no-op AppleScript against System Events and each running terminal or editor (the Automation
prompts) and call `systemPreferences.isTrustedAccessibilityClient(true)` (the Accessibility prompt);
the step shows whether Accessibility is granted, and the Agents page names a missing permission;
5) Codex and OpenCode detection, optional; 6) start at login (opt-in), done. Every step is skippable.

## 11. The download site (`site/`, usage.stigg.io)

Static HTML + CSS + one script, no framework. The site follows the Stigg DS (`brand/stigg-ds/SKILL.md`
rules 1, 2, 5, 8, 10) and the box brief §4–6, exactly like the box it ships with: `#131512` canvas,
1 px hairlines (a registration frame around the hero is fine), weight 400 only, sentence-case
headings, mono uppercase eyebrows with the 6 px square bullet, radii 4/8 px, no grid-paper, no glow or
blur, no scan line, no waves, no shadows. `design/MARKETING-REFS.md` is speaker-card collateral and is
not a reference for this page.

Fonts: Söhne through `@font-face` rules whose `src` are the four URLs stigg.io's own stylesheet serves
today (verified Nov 1: `font/woff2`, `access-control-allow-origin: *`, `cache-control: max-age=31536000`):
`https://cdn.prod.website-files.com/6a2ff0758d0f9f6abcd082f0/6a2ff738fe0dab30dc7d8faa_soehne-buch.woff2`,
`…/6a2ff738fe713781beb04518_soehne-leicht.woff2`, `…/6a2ff7385d9084e037c340d7_soehne-mono-buch.woff2`,
`…/6a2ff738aaffb29b8ccee03b_soehne-mono-leicht.woff2`. Declare the families exactly as `Soehne Buch`,
`Soehne Leicht`, `Soehne Mono Buch`, `Soehne Mono Leicht` (one family per cut, weight 400), because
the lockup SVGs' `<text>`, `screens-v2/*.svg` and `pixelmark.js` reference those names and fall back
silently otherwise; stacks `"Soehne Buch", Geist, sans-serif` and `"Soehne Mono Buch", "Geist Mono",
monospace`, with Geist served from the site's own origin (`brand-kit/brand/geist/`, committed, OFL).
Keep the four URLs as constants in one place and note in the README that a marketing font re-upload
in Webflow changes them (Geist keeps the page readable). No font file in the repo or in the deployed
site. Hosting: GitHub Pages from this repo (`pages.yml` on pushes to `main` that touch `site/` or a
tag: build the six tile PNGs with `scripts/export-site-tiles`, upload `site/` as the Pages artifact,
deploy; `site/CNAME` contains `usage.stigg.io`; enforce HTTPS in the repo's Pages settings). Inline every SVG that contains `<text>` (the lockups, at-logo, screens-v2) into the HTML; an
`<img>` SVG cannot use the page's fonts. Inline `n3-line.svg` too and set `stroke-width: 1;
vector-effect: non-scaling-stroke` on its strokes so the silhouette keeps the 1 px hairline at hero
size. Sections, in order:

1. Hero: the `Token Deck` pixel lockup (stacked, as on the lid), "The AI Usage Management Console",
   then the two installs, with no fetch and no GitHub API call (unauthenticated API calls are limited to
   60 per hour per IP, which the venue's NAT would exhaust in minutes). Mac: a mono eyebrow `MAC`, the
   command `/bin/bash -c "$(curl -fsSL https://usage.stigg.io/install.sh)"` in a mono block with a Copy button (a DS primary button), and one plain line:
   "Paste it in Terminal. It picks the build for your Mac (Apple Silicon or Intel), checks it and puts
   Token Deck in Applications. Read the script first: usage.stigg.io/install.sh" (linked). Windows:
   `Download for Windows` → `https://github.com/stiggio/token-deck/releases/latest/download/TokenDeck-win-x64.exe`,
   a DS primary button (white, hover lime); never two lime buttons. Under them, "Other downloads":
   `Mac (Apple Silicon)` → `…/TokenDeck-mac-arm64.dmg` and `Mac (Intel)` → `…/TokenDeck-mac-x64.dmg`, both
   always visible (Safari and Firefox expose no architecture hint), with "Not sure which Mac? Apple menu
   → About This Mac shows an Apple chip or an Intel processor.", section 0's dmg note, and a link to
   `https://github.com/stiggio/token-deck/releases`. Optional progressive enhancement only: if
   `navigator.userAgentData` exists, `getHighEntropyValues(['architecture'])` returns `arm` on Apple
   Silicon in Chromium; use it to add a "recommended" badge to the matching dmg link, never to hide a
   link. Then the device line silhouette with six PNG tiles exported at build time by
   `scripts/export-site-tiles` (a Node script that imports the tile renderer and renders the layouts
   in tile space with no per-key window offset, because the silhouette's keys have no off-centre tile; nothing from `src/main` is ever bundled for the browser). The version shown comes from `package.json` at build time (the
   Pages workflow also runs on release tags, so the site redeploys with each release).
2. The three modes, each a block with a mono eyebrow, its screen illustration from `design/screens-v2`
   (inlined), and the printed caption verbatim (source of truth:
   `design/Token-Deck-box-4-bottom.png`, the press version): AGENTS "Jump to any coding agent. Turn
   the dial to hop windows." / SESSIONS "Every session and its context. See which one needs you." /
   MODELS & USAGE "Six models, live 5H and 7D limits." Under the Models block, a four-line mono knob
   legend as printed: "Turn: effort. Press: Ultracode." (main knob) / "Turn: agent. Press: last
   agent." (left knob) / "Turn: permission. Press: apply." (right knob) / "Select the mode, one per
   button." (metal buttons). The brief's section 8 lines are drafts and are never used as copy.
3. PROGRAM IT YOURSELF: caption "Write your own modes for any screen, button or knob.", then the JSON
   example from section 8 and `design/program-window.svg`.
4. Setup notes: quit the StreamDock or VSD Craft app; macOS asks for Automation and Accessibility and why; the
   section 0's dmg note (the install command needs none); the Windows SmartScreen
   note ("Windows protected your PC" → More info → Run anyway).
5. Footer: After Tokens lockup, "Nov 10, 2026 · Terra, San Francisco", "by Stigg", links to the
   repo and stigg.io. The short link is written `io.stigg.io/usage` in lowercase mono, as printed.

Copy voice: plain, engineer to engineer, no hype, no exclamation marks.

## 12. Packaging and release (versions current on Nov 1, 2026)

- Electron ^45.2.1, electron-vite, `node-hid` ^3.4.0, `@napi-rs/canvas` ^1.1.0, `electron-builder`
  ^26.18, `electron-updater` ^6.8. All three native modules ship N-API prebuilds, so set
  `npmRebuild: false` in the builder config (otherwise `@electron/rebuild` tries to compile node-hid
  with node-gyp) and keep `node-hid` external in the bundler. The CI smoke step below must pass for the
  x64 app, the arm64 app and the Windows exe before anything is published.
- Root-level `artifactName: "TokenDeck-${os}-${arch}.${ext}"` (no version in the name, so the site's
  `releases/latest/download/…` links never change; with no pattern electron-builder drops the arch
  suffix for the default arch). electron-updater is unaffected: it reads file names from
  `latest-mac.yml` / `latest.yml`. Keep `publish: { provider: "github", releaseType: "release" }`
  (the default is a draft, which never becomes `latest`).
- macOS: targets `dmg` + `zip` for `arm64` and `x64`, **both in one electron-builder invocation** so
  one `latest-mac.yml` lists both zips (two mac jobs overwrite each other's yml and break the updater
  on one arch); never `universal` (`@napi-rs/canvas` and `node-hid` ship per-arch packages).
  `@napi-rs/canvas` installs only the host platform's binary package, so before packaging on the
  arm64 runner run `npm install --no-save --force @napi-rs/canvas-darwin-x64@$(node -p
  "require('@napi-rs/canvas/package.json').version")`; each mac app then carries both skia binaries
  (about 33 MB extra; the napi loader picks by `process.arch`). `mac.extendInfo: { LSUIElement: true,
  NSAppleEventsUsageDescription: "Token Deck focuses the terminal window of the session you pick on
  the deck." }` for the tray-only app (`app.dock?.hide()` in dev), plus the
  `com.apple.security.automation.apple-events` entitlement so AppleScript works under the hardened
  runtime; otherwise `hardenedRuntime` default on with the default allow-jit entitlements (no USB/HID
  entitlement exists or is needed), signing through `CSC_LINK`/`CSC_KEY_PASSWORD`, notarization
  through `APPLE_ID`/`APPLE_APP_SPECIFIC_PASSWORD`/`APPLE_TEAM_ID` (leave `notarize` unset so the
  build skips it with a warning when the secrets are absent; with no secrets, v1's case, the build is
  unsigned). The built-in updater requires the zip target and a signed app:
  `if (process.platform !== 'darwin' || __SIGNED__) autoUpdater.checkForUpdatesAndNotify()`.
- **macOS installer** (`site/install.sh`, served by Pages at `https://usage.stigg.io/install.sh`; the
  site's command is `/bin/bash -c "$(curl -fsSL https://usage.stigg.io/install.sh)"`). A short, readable bash script with `set -euo pipefail`, no `sudo`, and
  nothing sent to the deck: refuse anything but macOS 12 or later; pick `arm64` when
  `sysctl -in hw.optional.arm64` is 1, else `x64` (`TOKENDECK_ARCH` overrides, for tests); download
  `https://github.com/stiggio/token-deck/releases/latest/download/TokenDeck-mac-<arch>.zip` and its
  `.zip.sha256` into a temp dir with `curl -fL`; stop with "Checksum mismatch: nothing was changed. Run
  the command again." unless `shasum -a 256` matches; quit a running Token Deck
  (`osascript -e 'tell application "Token Deck" to quit'`, then wait up to 30 s for `pgrep -x "Token Deck"`
  to end, since quit waits for a burn, section 3); unpack with `ditto -x -k`; replace
  `/Applications/Token Deck.app` (or `~/Applications/Token Deck.app` when `/Applications` is not
  writable); `xattr -dr com.apple.quarantine` on it (normally a no-op); `open` it; print what it did.
  The mac release job uploads `TokenDeck-mac-arm64.zip.sha256` and `TokenDeck-mac-x64.zip.sha256` (the
  hash alone, from `shasum -a 256`) with `gh release upload` after electron-builder publishes.
- Unsigned macOS launch: an arm64 executable needs a valid signature, and electron-builder's edits to
  Electron's bundle can invalidate the one Electron ships. Section 15 checks that the unsigned arm64 app
  installed by the script launches; if macOS kills it, sign the app ad hoc in CI (`mac.identity: "-"`
  with `hardenedRuntime: false`; without the hardened runtime the AppleScript entitlement is not needed)
  and test again.
- Unsigned macOS updates: at launch and on "Check for updates", fetch
  `https://github.com/stiggio/token-deck/releases/latest/download/latest-mac.yml` (a release asset, not
  the GitHub API) and compare its `version`; when newer, show the notification "Token Deck <version> is
  available." with the button "Update now", which spawns the site's command detached
  (`detached: true`, `stdio: 'ignore'`, `unref()`): the script quits Token Deck through its normal quit
  sequence, replaces it and opens the new one. Nothing updates without that click. macOS ties an
  unsigned app's Automation and Accessibility grants to that exact build, so after an update the app
  checks `systemPreferences.isTrustedAccessibilityClient(false)` and, when access is gone, opens the
  wizard's permission step again (section 15 records what macOS actually does).
- Windows: `nsis` x64, one-click installer, unsigned: `win.sign: false` and
  `win.verifyUpdateCodeSignature: false` (otherwise the updater rejects unsigned updates). Document
  the SmartScreen dialog on the site.
- Smoke flag: `--smoke`, handled first in `src/main/index.ts`: on `app.whenReady`,
  `require('node-hid').getHidapiVersion()` (node-hid loads its native binding lazily; this call loads
  it and returns the hidapi version without touching any device; print it),
  `require('@napi-rs/canvas').createCanvas(64, 64).toBuffer('image/jpeg')`, a check that
  `resources/welcome-320x240.png`, `resources/welcome-sent.jpg`, `resources/welcome-tiles/key1.jpg` to `key6.jpg`,
  `resources/panel-geometry.json` and `resources/preburned.json` are in the package (and that
  `welcome-sent.jpg` has section 9's sha256), `app.exit(0)`; any throw → print it, `app.exit(2)`. The
  `burn`, `probe` and `calibrate` arguments (section 4, `cli.ts`) are handled right after it.
- Tray: Template icons (`trayTemplate.png` 16 px and `@2x` 32 px, black + alpha) on macOS, `.ico`
  on Windows; keep a global reference; `app.requestSingleInstanceLock()`; a no-op
  `window-all-closed`; the settings `BrowserWindow` hides on close. Start at login via
  `app.setLoginItemSettings({ openAtLogin })`.
- App icon from `brand/stigg-app-icon.svg`.
- GitHub Actions: `release.yml` on tags `v*` runs two jobs with `permissions: { contents: write }` and
  `env: GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` on the build steps (electron-builder reads it from the
  env and nothing sets it otherwise): **`macos-15`** (arm64; `macos-14` is retired on Nov 2, 2026 and
  `macos-latest` now means macOS 26) and `windows-latest`. Mac job: `npm ci`; the x64 canvas install
  above; `npx electron-builder --mac dir --arm64 --x64`; smoke-run
  `"dist/mac/Token Deck.app/Contents/MacOS/Token Deck" --smoke` (x64, under Rosetta, which the runner
  image preinstalls) and `"dist/mac-arm64/Token Deck.app/Contents/MacOS/Token Deck" --smoke`; then
  `npx electron-builder --mac dmg zip --arm64 --x64 --publish always`. Windows job: `npm ci`,
  `npx electron-builder --win dir --x64`, `dist\win-unpacked\Token Deck.exe --smoke`, then
  `npx electron-builder --win nsis --x64 --publish always`. `ci.yml` runs lint, the font lint
  (section 2), the unit tests and the headless tile-renderer test (this also catches a native module
  that fails to load) on every push.
- Version 1.0.0 for the event. The About page and the site show the version.

## 13. Build order

1. Scaffold (electron-vite, TypeScript strict, React, electron-store, vitest). Tray app shell,
   settings window with the nav, the lint-fonts script, `.gitignore`, `LICENSE`, `BRAND-ASSETS.md`.
2. Device: transport (the connection state machine and the write queue, section 3) + protocol +
   handshake + decoder with fixtures from `device/events-2026-11-01.log`. On day one, confirm the
   exclusive open on this unit (input arrives after the handshake; a second open from another process
   fails with `0xE00002C5`; otherwise `{ nonExclusive: true }`, section 3). Test tiles on the real deck,
   the first one at q100 with 1 px lime text, a 2 px lime ring, a 1 px coral border, and `Sonnet` in
   white and `Opus` in `#131512` on a lime band, 1× (section 3; photograph at 4×: this is the first
   Skia-encoded JPEG the deck decodes, since test 14's 4:4:4 tile came from Pillow, so it gates the
   renderer; q100 is decided); the CLE layout, every input and the keepalive experiment (section 15).
   Copy `device/panel_geometry.py` into `resources/panel-geometry.json` and the kit's v8
   `welcome-320x240.png`, `welcome-sent.jpg` and `welcome-tiles/` into `resources/` now (later steps
   use them), and commit `resources/preburned.json` as `[]`.
3. Tile renderer: bitmap font (widths tested), glyphs, the per-key design-box offsets and safe rects,
   the three mode layouts with the box kit's demo data, the overlay groups (lengths tested), the idle
   screen (the welcome crops + the CONNECT tile). Compare against `design/screens-kit-v2.png` on the
   device and in 4× captures.
4. Simulator in the settings window (same renderer, the decoded wire JPEG drawn in panel geometry, same
   event bus, keyboard shortcuts 1–6, Q/W/E for the metal buttons, arrows and Enter for knobs).
5. Mode controller with demo data (all three modes, selected session, overlays, custom-mode picker).
6. Claude Code integration end to end on this Mac (`claude agents --json`, hook shim, status line
   shim, defaults, usage from the status line, focus); then Codex (with the TUI-visibility check);
   then install OpenCode and do its check; then the three launch-only agents. Focus/launch on macOS,
   then Windows.
7. Custom modes (schema, watcher, actions).
8. Burn: freeze the welcome image first (the v8 power-on photo and replug check, section 9 step 3) and
   commit the welcome files in `resources/` once they are in; then the burn through the app path (section 9 step 4, with its tests
   against a fake transport), the persistence test, the first-connect auto-burn with the two records,
   and the batch CLI.
9. Settings pages and the first-run wizard.
10. Site, packaging (with the `--smoke` flag and the CI smoke steps), CI, a tagged pre-release,
    install with the site's command on a clean macOS user account and, if available, a Windows VM. Tag the event
    release only after the giveaway batch has run (a 1.0.x before Nov 10 is fine), so
    `resources/preburned.json` lists every giveaway deck.
11. QA (section 15), README (setup, how each integration works, the burn and batch procedures, the
    custom-mode format, troubleshooting, why q100 4:4:4, the device observations section 15 records),
    hand over.

## 14. Microcopy (use verbatim)

Tray menu: `Token Deck`, `Mode: Agents / Sessions / Models & Usage`, `Open settings…`, `Check for
updates`, `Quit` (burning lives on the Burn settings page only; attendees never need it). Device
states: "Deck connected", "No deck found. Plug it in, or unplug it and plug it back in.", "Quit the
StreamDock or VSD Craft app to use Token Deck.", "Deck not responding. Unplug it and plug it back
in.", "Writing the welcome screen. Keep the deck plugged in." (from the burn's tile paint until the end
of its hold), "The welcome screen was not written. Unplug the deck and plug it back in." (after a
failed burn, until the replug). Wizard: "Plug in your Token Deck." / "Writing the welcome screen to
this deck. Keep it plugged in." / "Done. The deck shows this screen whenever no app is driving it." /
on failure, the failed-burn device state / "Turn the left knob clockwise." / "Now the right knob." /
"Click the left knob." / "Token Deck adds a status line and hooks to Claude Code so the deck can see
your sessions. Here is exactly what changes:" / "Restore my settings" / "Token Deck brings the window
of the session you pick to the front. macOS asks you to allow that once for each app, and once in
Privacy & Security → Accessibility." / "Ask now". Burn page: "Token Deck writes its welcome screen
into a deck's memory the first time the deck connects to this computer, unless the deck already has it
(the giveaway decks come with it). The deck shows that screen whenever it has power and no app is
driving it, on any computer. The button below writes it again." Toggle: "Write the welcome screen to
new decks automatically". Button: "Write welcome screen to deck". Confirmation: "Write the welcome
screen to this deck again?". After two failed automatic writes: "Token Deck could not write the welcome
screen to this deck." Tray notification after an automatic write: "Welcome screen written to the
deck."; after a failed one: "The welcome screen was not written. Unplug the deck and plug it back in."
Calibration (CLI only): "This replaces the welcome screen until calibration ends". Unsigned macOS
update: "Token Deck <version> is available." / "Update now". Installer: "Checksum mismatch: nothing
was changed. Run the command again." Overlays: section 5.

## 15. Verification before you call it done

Device in the loop (the deck is on this desk):
- Handshake, tiles on all six keys, brightness, `CLE` of one key and of all (confirms the three-zero
  layout), computer sleep and wake (sleep the Mac for 2 minutes with the deck attached, then wake it:
  the deck returns to the current tiles through the `powerMonitor` `resume` path and the log shows one
  reconnect; the deck's own `HAN` frame is never sent), unplug and replug while the app runs (one
  reconnect, no crash dialog), keepalive for 15 minutes with the app idle on a static screen (Agents
  mode, no session changes, so the soak measures the keepalive and nothing else; tiles must still be
  there; run it with the settings window closed and another app frontmost, log each `CONNECT` with a
  timestamp and fail it if any gap outside a burn exceeds 15 s; if one does, add
  `LSAppNapIsDisabled: true` to `mac.extendInfo` and repeat; try with the repaint keepalive off; film
  key 1 for 10 s with the repaint keepalive on and look for a blink at each repaint), the
  firmware-string read leaves keys reporting, quit the normal way (welcome tiles painted, no goodbye
  frame) and `kill -9` the app: after each, record with timestamps how long the last tiles stay up and
  when the deck switches to its ROM image. Then leave it plugged in 5 minutes with Token Deck quit while
  a script logs `HID.devices()` once a second without opening the deck, and record whether and when the
  firmware restart re-enumerates it, once or every minute.
- Brightness: photograph the welcome screen at power-on with nothing running and again after the app
  connects at the default (70); if the panel steps, set the default to the boot level, and record it,
  and whether the app's level survives a replug, in the README and `device/NOTES.md`.
- With nothing driving the deck (Token Deck quit, and on a second computer without it), turn each knob
  both ways, click it, press every key and metal button: the computer shows no volume or media HUD and
  receives no keystrokes. Plug the burned deck into a second computer without Token Deck (or a USB
  charger) and confirm the welcome screen stays for 5 minutes. Record both in the README; if the deck
  sends keys, tell Gabriel before the event.
- The q100 tiles (4:4:4): 1 px lime text, the 2 px lime ring, the 1 px coral border and the model names,
  including the current model's on its band, appear with their colors and read at arm's length in a
  4× photograph (compare with the simulator); the sampling-factor unit test passes. Each tile lands at
  its `panel-geometry.json` rect, with only `#131512` from the burned image showing around it; with an
  app tile on key 1, the strip left of it (window 1, x 13–19, v8's 7-level colour halo) shows no tinted
  line. On keys 3 and 6 (left edge) and 4–6 (top edge) nothing bright sits within 6 px of the window
  edge, the approval frame shows all four sides, and bevel reflections do not read as extra squares or
  lines: photograph, straight on and from a seated angle, a needs-approval tile on keys 3, 4 and 6 and
  the current-model band on a bottom-row key.
- Layout: each Agents glyph and meter is centred in its window to 1 px, the meters of keys 4–6 are on
  one line, and a ring does not move when its session starts needing approval. With an overlay up, the
  third group on key 3 is centred in its window and no sliver of a meter square shows above the
  hairline. The Models token rows are evenly spaced on the 4× crops. Next to the box and the welcome
  boards, unlit squares and ring tracks read as dark as the box's and the same as the welcome screen's
  unlit tokens (if they vanish, go back to `#3C3E3A`). Turn the main knob 20 detents fast in Sessions
  and in Models: the deck lands on the final state without replaying intermediate screens.
- Optional, only on a spare deck (never Gabriel's development unit, which holds v8), after everything
  else passes and in its own power cycle: one `BGPIC` probe; skip it if no spare exists before Nov 10.
  After the usual handshake and tile paint, send `CRT\0\0BGPIC` + u32be length + x 12, y 18, w 80, h 80
  (u16be) + `00` + layer `00`, then an 80 × 80 baseline JPEG of an asymmetric glyph (an "F" with a
  magenta border), pre-rotated like the tiles; `STP`; read 2 s. Upright over key 1 = it draws in panel
  coordinates (usable); near key 4 = native coordinates; nothing = send one `BAT` + `STP`: if that tile
  draws, the firmware ignores `BGPIC`; if not, the deck is wedged and needs a power cycle. Clean up with
  `CRT\0\0BGCLE` + `03` + `STP` and a power cycle, then check that the boot image is unchanged (it is
  RAM only). Do not build on it unless it draws where expected.
- Every input: keys 1–6, three metal buttons, three knob clicks (one click per press, both states
  logged), both directions on all three knobs → the right event names after calibration (this settles
  which small knob is left and which code is clockwise; record it in `device/NOTES.md`); hold the
  middle metal button 2 s: exactly one `0x30` state 1 and one `0x30` state 0, nothing between; a
  2-minute soak turning a knob fast with no dropped mode switches.
- All three modes with demo data compared side by side with `design/screens-kit-v2.png` and the box
  bottom panel: same layout (Cursor, Amp and Devin show `LAUNCH` where the box shows meters, by section
  1), colours judged on the photo next to the box (the panel lifts dark greys), readable at arm's
  length; the Opus tile is the only one with lime squares. Photograph the deck and crop each tile at 4×
  to check pixel crispness and JPEG bleed.
- Burn:
  - The burn sequence and the burn records are unit-tested against a fake transport, clock and store:
    the frames and gaps of section 9 step 4 (handshake; at least 0.5 s; six `BAT` headers with u32be
    length and keys 1–6, each followed by its zero-padded chunks; `STP`; at least 1 s with nothing sent;
    `CRT\0\0LOG` + u32be 18,887 + `0x01` and its 19 chunks; nothing until the fake report; `STP`; at
    least 1 s; then the repaint); a serial already recorded or in `resources/preburned.json` → no `LOG`;
    an empty serial → no `LOG`; no report → no `STP`, nothing but `CONNECT` afterwards, no record; the
    deck's next appearance → one retry; two failures → the automatic path stops for that serial.
  - The first app burn on Gabriel's deck, through the app path: fresh electron-store, his serial not in
    `resources/preburned.json`, plug the deck in with the app running. The app waits 8 s; the log shows
    the frames and gaps of section 9 step 4 and no frame between the last `LOG` chunk and the report;
    the write report arrives. Then quit Token Deck, power-cycle the deck and photograph the boot image
    (not the app's tiles) straight on, cropping each window at 4×: the logo, `io.stigg.io` / `/usage`
    (not misread as `lo.stlgg.lo`) and the slogan crisp, no ring or tint around the tiles, the three
    watch items of section 9 step 3 checked. Then relaunch and reconnect → no `LOG`. Then quit, clear
    `burnedSerials` again, relaunch and plug the deck in; after the automatic write's hold, in that same
    app session, do one Burn-page rewrite (with the repaint keepalive on and a Claude Code session
    changing state): its write report in the log, then the boot image after a power cycle with Token
    Deck quit.
  - If an app burn on Gabriel's deck gets no report or leaves the wrong boot image: ask Gabriel to
    replug; then, with Token Deck quit, restore v8 with the reference writer, run from a scratch copy of
    the kit's `device/` folder (it rewrites `boot-image/` in its own folder):
    `~/.venvs/at/bin/python burn_logo.py welcome/welcome-320x240.png` (its JPEG is byte-identical to
    `welcome-sent.jpg`). Replug and look before continuing.
  - The batch, run the way the team will run it: with the tray app running, `burn --watch` exits with
    "Quit Token Deck first: the tray app owns the deck."; with the tray app and the vendor apps quit,
    plug Gabriel's deck (his serial in neither list): it waits 8 s, gets the write report, prints "done"
    only after the 10 s hold and appends the entry; unplug and plug it again: it prints the identity and
    "already burned, unplug"; stop the batch, replug with nothing running → welcome screen.
  - Windows: one burn on real hardware through the Windows build (a Windows PC, or a VM with the deck
    passed through): fresh store, connect, write report in the log, then power-cycle with Token Deck
    quit and the welcome screen is at boot. Record the result in the README; if it cannot be run before
    release, say so to Gabriel at hand-over.
  - Each burn's write report and boot image after the power cycle, the quit and kill timings, the
    re-enumeration log and the brightness go into the README and `device/NOTES.md`.
Integrations, for real:
- Claude Code: start a session in Terminal.app; `claude agents --json` shows it; the tile shows it
  Working, then Idle, titled with its `name`; trigger a permission prompt (a Bash call in default
  mode) → Needs approval with the frame within a second (hook), confirmed by `waitingFor` on the next
  poll; press the tile → that Terminal tab is focused; `Stop` → Completed; the context ring moves
  after a long prompt; usage squares match `/usage` inside Claude Code; quit every session: tiles go
  `STALE` after 10 min and `--` after 24 h; change model/effort/permission/ultracode → the settings
  file shows the change and the next session uses it (`/status` or `/model` to confirm). Restore my
  settings → the backup is back byte for byte. Also one Desktop-app session: it appears through
  `claude agents` and hooks even if the status line never runs there. Then quit Token Deck, start a new
  Claude Code session, run three prompts including one permission prompt: no hook error appears
  anywhere and the status line is unchanged; relaunch Token Deck: sessions appear without re-running
  the wizard.
- Codex: the TUI-visibility check recorded; a session appears with the right status and title; usage
  matches `/status` in Codex; `config.toml` changes apply, comments and `notify` survive, and the
  backup restores.
- OpenCode (installed by you, free Zen model): with `opencode serve` running, sessions and status
  appear; a permission prompt shows as Needs approval; model default changes. If no free model was
  available, the README says so instead of claiming this check.
- Cursor/Amp/Devin tiles show `LAUNCH`, launch and focus the right thing and never claim more.
Simulator, site and packaging:
- Every mode and the wizard work with no device attached; the simulator emits the same events.
- Packaged app launches on a clean macOS user account (and in a Windows VM if available): tray icon,
  settings window, device access, no missing native module; open the x64 dmg on this Mac too and
  launch it under Rosetta (a missing x64 canvas binary shows as "Cannot find native binding");
  on Windows `electron-updater` finds the pre-release.
- The macOS installer on a clean user account on this Apple Silicon Mac: paste the site's command; it
  installs the arm64 build into `/Applications` with no Gatekeeper dialog, `xattr -l` shows no
  `com.apple.quarantine`, and the app launches (if macOS kills the unsigned arm64 app, apply section
  12's ad-hoc fallback and test again). Run the command again: it quits the running app, replaces it
  and opens it. With `TOKENDECK_ARCH=x64` it installs the Intel build, which runs under Rosetta. A
  wrong `.sha256` makes it stop without touching the installed app. "Update now" from a lower version
  updates and relaunches; record whether macOS kept Automation and Accessibility across the update.
- First run on that clean account: the wizard's permission step raises the Automation prompts and the
  Accessibility entry; after granting, a tile press focuses Terminal and the main knob cycles windows;
  with Accessibility off, the knob shows `FAILED` and the Agents page names the missing permission.
- After the first full (non-prerelease) tag, `curl -sIL` each of the three download permalinks and
  expect a 302 chain ending in 200, and confirm the three asset names match byte for byte.
- The printed address: `curl -sIL io.stigg.io/usage` (no scheme, typed as printed on the box and the
  deck) and `curl -sIL https://io.stigg.io/usage` both end at `https://usage.stigg.io/` with 200, and
  `curl -sI http://usage.stigg.io` redirects to HTTPS. It is the only address on the box and on every
  burned deck. At hand-over, ask Gabriel to open `io.stigg.io/usage` on his phone over cellular.
- Site: `document.fonts.check('16px "Soehne Buch"')` and `'16px "Soehne Mono Buch"'` are true after
  load, the hero "Deck" and the canvas "After" match the lid lockup, every line measures 1 px at 1×,
  at most one lime button, no grid or glow anywhere, the captions match the printed box.
- Fonts lint: no Söhne file anywhere in the repository (`git ls-files`), the app bundle or the
  deployed Pages site. Licenses listed in About.

## 16. Assumptions Gabriel still has to confirm (defaults applied)

1. No Stigg account; "connect" means the coding-agent accounts already on the machine.
2. Electron/TypeScript, mac + Windows, open-source repo `stiggio/token-deck` under the MIT licence
   with the brand assets excluded (`BRAND-ASSETS.md`), site at `usage.stigg.io` on GitHub Pages
   (free) behind `io.stigg.io/usage`. macOS installs with a one-line `curl` command, unsigned (no
   Apple Developer ID): no built-in macOS updater ("Update now" reruns the installer), and macOS may ask
   for Automation and Accessibility again after an update.
3. Geist in the app UI and a bitmap font on the tiles because Söhne cannot ship in an app or a public
   repo; the site keeps Söhne by loading stigg.io's own CDN files.
4. Model/effort/permission/Ultracode change the agent's defaults (`NEXT | SESSION`); FULL maps to
   Claude Code's `bypassPermissions` only after the desktop confirmation; Cursor/Amp/Devin are
   launch-only.
5. The burned welcome screen is static (the device cannot react to buttons without a host): welcome
   screen v8 (section 9 step 3), the Stigg logo on key 1, `io.stigg.io` / `/usage` set into a dim token
   board on key 4, the slogan on key 6 and the token explosion across keys 2, 3 and 5, its type in Söhne
   rendered from the private kit. Its power-on photo and replug check are pending.
6. Small-knob mapping is the vendor table's (all six codes seen on Nov 1; which knob and which direction
   is settled in section 15) and confirmed on first run.
7. Custom modes = JSON files, entered by holding the middle metal button.
8. Number of devices to burn and whether they all share this firmware: unknown; the batch tool
   handles any count and prints the identity of each one.
9. Usage without a running Claude Code session is deferred past the event: the deck shows the last
   status-line values as `STALE`, and an always-on source is added only if Anthropic documents one.
10. Tiles the app renders are encoded at JPEG q100 (4:4:4); verified on Gabriel's unit on Nov 2 with a Pillow-encoded
    tile (the first Skia tile is section 13 step 2's test). Each layout sits on its key's window by a
    fixed per-key offset (section 5): Agents to 1 px, Models and Sessions within 4 px (nothing wider than
    50 px can be centred on keys 3 and 6). Tile content stays 6 px inside the window; the keycap bevel's
    mirror of bright content near the edges cannot be avoided on 64 px tiles. Unlit squares and ring
    tracks use `#2C2F2B`, one step darker than the box's `#3C3E3A`, because the panel lifts dark greys.
11. Token Deck writes the welcome screen by itself the first time it connects to a deck that neither
    this computer's record nor the shipped `resources/preburned.json` lists (one flash write per deck,
    Burn page toggle, default on), on top of the batch pre-burn of the giveaway decks, whose serials
    ship in `resources/preburned.json` so attendees' computers never write them again; the vendor's
    stock logo is overwritten and not kept anywhere. The app never sends the vendor's `CLE DC` goodbye
    or `HAN`, not even behind a debug flag; it paints the welcome tiles on quit instead. The burn is
    verified on Gabriel's unit (Nov 2-3: ten writes up to 22.3 KB, tiles first, write report, three
    checked after a power cycle, up to four per power cycle, each as its own connection); welcome screen
    v8 is on it (write report received; photo and replug check pending). Untested: images above
    22.3 KB; a burn started less than 8 s after the deck powers up; two `LOG`s on one connection; a burn
    through the app's own node-hid path and from Windows; decks from the giveaway stock (firmware string,
    and whether serials differ); Mirabox-branded `6603:1002` / `6603:1003` units, which the app matches
    and would burn on first connect (the `LOG` rhythm and the panel geometry the welcome image is cut to
    are verified only on this `5548:1001` unit).
