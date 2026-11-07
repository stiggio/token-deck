# Token Deck

The AI Usage Management Console. Token Deck is the menu-bar app for the Stream Dock N3 that ships with After Tokens: six LCD keys, three metal buttons, three knobs. Plug the deck in, install the app, and the keys become a control surface for Claude Code, Codex and OpenCode.

The download page is [usage.stigg.io](https://usage.stigg.io). The address printed on the box and burned onto the deck is `io.stigg.io/usage`.

## Install

macOS 12 or later, Apple Silicon or Intel:

```sh
/bin/bash -c "$(curl -fsSL https://usage.stigg.io/install.sh)"
```

Paste that in Terminal. The script picks the build, checks its checksum, and puts Token Deck in Applications. Read it first at [usage.stigg.io/install.sh](https://usage.stigg.io/install.sh). There is no Apple Developer ID, so there is no built-in macOS updater. "Update now" runs the installer again. macOS may ask for Automation and Accessibility again after an update.

A browser download of the dmg is unsigned. macOS will refuse to open Token Deck because it is not notarized (on macOS 15 and later Control-click → Open no longer works, and an unsigned build may be reported as 'damaged'). In Terminal run `xattr -d com.apple.quarantine "/Applications/Token Deck.app"` and open it again, or use the install command above. If System Settings → Privacy & Security shows an Open Anyway button for Token Deck, that works too.

Windows: download `TokenDeck-win-x64.exe` from the [releases](https://github.com/stiggio/token-deck/releases). SmartScreen says "Windows protected your PC". Choose More info, then Run anyway.

Quit the StreamDock or VSD Craft app before Token Deck. Only one program can open the deck on macOS.

A shell alias for the commands below:

```sh
alias tokendeck='"/Applications/Token Deck.app/Contents/MacOS/Token Deck"'
```

On Windows the binary is `Token Deck.exe`.

## What the deck does

Three metal buttons select Agents, Sessions, and Models & Usage. Hold the middle button to open a custom mode. The current mode is remembered.

The deck opens on Agents. The left metal button is Agents, the middle is Sessions, the right is Models & Usage.

Agents shows Claude Code, Cursor, Codex, OpenCode, Amp, and Devin as the same kind of key. A dim key is not installed. Press a key to go to that app. If it is not already open, the key opens it. Claude opens the desktop app when it is installed, and Terminal otherwise. The large knob moves between apps that are already open. It does not open a new one. The left knob sets the model for the next session, and the right knob sets its effort. Those two knobs only list Claude Code, Codex, and OpenCode, and only when that app is installed. One installed app does not pretend to switch. None installed says so.

Sessions lists Claude Code and Codex sessions, newest activity first, and OpenCode while `opencode serve` is running. Press a key to bring that window forward. The large knob pages. The left knob filters by installed app. The right knob filters by status.

Models & Usage shows up to six favourite models and the real 5-hour and weekly limits for Claude Code and Codex. The same limits are shared across that app's model keys. Press a key to set that model for the next session. A session that is already running keeps its model. Every default change says `NEXT SESSION`. Full access is saved only after you confirm it in the Token Deck window. There is no credit balance on the deck.

None of this is done with simulated keystrokes. Claude Code, Codex and OpenCode defaults are written to their own config files.

## Claude Code

Token Deck polls `claude agents --json --all` and, with your consent, installs a command hook (never an HTTP hook) plus a status line that chains whatever you already had. The shim is `~/.tokendeck/bin/hook`. It exits immediately when Token Deck is not running, so a quit or a crash does not print hook errors into your transcript.

Context and the 5H / 7D windows come from the status line, for Pro and Max accounts, after the first response of a session. The last values are kept. After 10 minutes the tile says `STALE`. After 24 hours, or when a window's reset time has passed, the row shows `--`. Claude Code credentials are never read.

`model` is `opus`, `sonnet`, `haiku` or `fable`. Effort is `modelSettings.<model>.effortLevel` on Claude Code 2.1.251 and later, and the top-level `effortLevel` on older versions. Permission maps READ → `plan`, ASK → `default`, AUTO → `auto`, FULL → `bypassPermissions`. Ultracode is the boolean in `~/.claude/settings.json`.

The first edit copies `~/.claude/settings.json` to `settings.json.tokendeck-backup`. Stop watching puts that file back byte for byte. The button is on This Mac, and only for Claude Code.

Focus uses AppleScript and needs Automation (once per terminal) and Accessibility. The wizard asks on purpose. On Windows, focus is best-effort and the status line is chained only when Git Bash is present.

## Codex

Token Deck talks to `codex app-server` for threads, models and `account/rateLimits/read`. It does not answer approval requests. If a running TUI's threads do not show as active, the README note from the day-one check applies and hooks plus rollout files are the fallback. `notify` in `~/.codex/config.toml` is never rewritten. Edits are line-wise, so comments survive. The first edit copies the file to `config.toml.tokendeck-backup`.

Permission maps READ → `read-only` + `on-request`, ASK → `workspace-write` + `on-request`, AUTO → `workspace-write` + `never`, FULL → `danger-full-access` + `never`.

## OpenCode

Installed on this Mac with `npm i -g opencode-ai` when that check is run. Sessions appear while `opencode serve` is running (default `http://127.0.0.1:4096`). There is no quota API. The tile says `NO QUOTA DATA`. The model default is `model` in `~/.config/opencode/opencode.json`. v1 and v2 are both implemented. OpenCode is not signed into a Claude subscription.

## Custom modes

JSON files in `~/.tokendeck/modes/`, reloaded when they change. Hold the middle metal button for 800 ms. With no files, that hold selects Sessions. A key is a label, an optional PNG or SVG icon, and an action: `shell`, `url`, `open`, `keys`, or `mode`. Shell actions run in your login shell with a 10 second timeout. The example is on the Deck page and on the download site.

## The welcome screen

The deck stores one image in ROM: the boot background. Tiles are RAM. Token Deck writes the welcome screen once per deck, the first time a deck connects whose serial is in neither this computer's record nor `resources/preburned.json`. About can write it again after a confirmation. Quit paints the same picture into the six tiles and closes. The app never sends the vendor disconnect or sleep frames.

The image is welcome screen v8 (18,887 bytes, sha256 `daea022363c85ef722c9c93bcd7f5379a995b726cb5240bc4ed92b12d15071fb`). Its power-on photo and replug check were still pending when this repository was built. Do not redraw it. The bytes in `resources/` are the bytes that were burned.

Batch, on a Mac, with Token Deck and the vendor apps quit:

```sh
"/Applications/Token Deck.app/Contents/MacOS/Token Deck" burn --watch
```

It waits 8 seconds, prints the deck's identity, and prints `done` only after the 10 second hold. A deck already in the record prints `already burned, unplug`. After the run, commit `~/.tokendeck/preburned.json` as `resources/preburned.json` and tag the event release. `tokendeck calibrate` replaces the welcome screen with a ruler and is only for a deck whose firmware is not this one. It is not in the settings window.

`tokendeck probe` prints whatever vendor interfaces are plugged in, without writing the boot image.

## Tiles

Tiles are 64×64 JPEGs at quality 100, 4:4:4, rotated 90° clockwise as a pixel copy before they go on the wire. 4:2:0 at q99 halves the saturation of a 1 px lime or coral feature. q100 was checked on this unit with a Pillow tile on 2 Nov 2026. The first Skia tile is the test pattern from the Device page (1 px lime text, a 2 px lime ring, a 1 px coral border, Sonnet in white, Opus in ink on a lime band).

The firmware draws each tile at a fixed spot that is off-centre in the key window, so every layout is shifted per key from `resources/panel-geometry.json`. Unlit squares are `#2C2F2B`, one step darker than the box, because the panel lifts dark greys. Content stays 6 px inside the window. The keycap bevel still mirrors bright pixels near the edge. That is expected on a 64 px tile.

If model names in mixed case do not read at arm's length on the lime band, set them to uppercase. The settings store key is `modelNamesUpper`. The default follows the provider's spelling.

## Develop

```sh
npm install
npm test
npm run dev
```

`npm test` is vitest. It checks that no frame the protocol can build is the vendor disconnect or sleep frame, the decoder against `test/fixtures/events-2026-11-01.log`, the write queue, the burn rhythm, JPEG 4:4:4, and that every built-in tile is under 10,000 bytes.

`node scripts/lint-fonts` fails if a Söhne file is tracked or packaged. Söhne is not in this repository. The site loads it from the same Webflow CDN URLs stigg.io already serves. If marketing re-uploads those fonts, the four URLs in `scripts/build-site.mjs` have to change. Geist is the fallback and the app UI face.

Logs: `~/.tokendeck/log/tokendeck.log`, rotated at 5 MB. No telemetry.

## Device observations

Gabriel's unit is USB `5548:1001`, firmware `V3.VSDN3_PXL.02.010`, serial `81D0DA782A24`. On 5 Nov 2026, from this Mac:

- Opening the vendor interface exclusively works. A second open from another process fails with IOKit `0xE00002C5`. Token Deck keeps the exclusive open.
- `getFeatureReport` returned `V3.VSDN3_PXL.02.010`. Keys were still writable after that read.
- The first Skia q100 tile was 6,620 bytes and was accepted by the device (the write did not error). A clear of key 1 used the three-zero layout and did not error. Nobody was at the deck to press keys during that listen, so the small-knob direction check is still the first-run wizard's job. The Nov 1 capture already contains all six small-knob codes.
- The first burn through the app, on a fresh settings store, waited out the settle, wrote v8, and got the device's write report. The record is serial `81D0DA782A24` at `2026-11-05T10:11:26Z`, image hash `daea0223…`. The log line `burn ok 81D0DA782A24` is `2026-11-05T10:14:00Z`. A relaunch must not write again. The power-on photo and the replug check still need someone at the deck: this session could not see the panel. Codex `account/rateLimits/read` returned a 5H window at 84% and a 7D window at 15% over app-server. No Codex TUI was running, so TUI visibility is still unchecked. OpenCode was not installed in this session.
- Brightness default is 70. The boot brightness versus the app's level still needs a photo of the welcome screen at power-on with nothing running, and another after the app connects.
- The 15 minute keepalive, the sleep/wake reconnect, the quit and `kill -9` timings, and the five minute enumeration log are recorded below when they have been run. A second computer and a Windows VM were not available in this build session.
- `BGPIC` was not probed. There is no spare deck, and this unit holds v8.

Small-knob map until the wizard says otherwise, from the vendor table and the Nov 1 capture: bottom-left click `0x33`, clockwise `0x91`, counter-clockwise `0x90`. Bottom-right click `0x34`, clockwise `0x61`, counter-clockwise `0x60`. Main knob click `0x35`, clockwise `0x51`, counter-clockwise `0x50`.

## Licence

MIT, © Stigg. The Stigg logos, marks and app icon are excluded. See `BRAND-ASSETS.md`.
