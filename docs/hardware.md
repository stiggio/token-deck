# How Token Deck talks to the deck

Token Deck drives the deck directly over USB HID with `node-hid`. It doesn't use the vendor's SDK or app. The protocol below matches the vendor's own SDK byte for byte and was checked on the development deck in November 2026. The full reasoning, with sources, is in [PLAN.md](../PLAN.md), section 3.

## The device

The deck is a Stream Dock N3 with the Stigg logo: six 64 × 64 screen keys, three metal buttons, a big knob and two small knobs, each knob clickable.

| | |
|---|---|
| USB ids matched | `5548:1001` (the VSD-branded N3 in the After Tokens box), `6603:1002` and `6603:1003` (Mirabox-branded N3s, same protocol, untested) |
| Interface | The vendor HID interface, usage page `0xFFA0`, usage 1. The keyboard interface next to it belongs to the OS and is ignored. |
| Reports | Output: 1,025 bytes (report id `0x00` and a 1,024-byte payload). Input: 512 bytes. |
| Firmware on the development deck | `V3.VSDN3_PXL.02.010` |

On macOS only one program can open the interface; a second open fails with IOKit error `0xE00002C5`. Token Deck keeps that exclusive open, checks for the StreamDock and VSD Craft apps before opening, and asks you to quit them. On Windows two programs can open the deck at once and fight over the screen, so Token Deck repeats the check with every heartbeat.

## Frames

Every command payload starts with `CRT\0\0`. Images go as a header frame, then the JPEG in 1,024-byte chunks, each its own report. All of them are in `src/main/deck/protocol.ts`.

| Frame | Does |
|---|---|
| `DIS` | Wake |
| `LIG\0\0<percent>` | Brightness, 0 to 100 (Token Deck defaults to 70) |
| `QUCMD` + 7 bytes | Sent during the handshake, as the vendor app does |
| `CONNECT` | Heartbeat. Sent every 10 seconds; without it the deck restarts after about a minute |
| `BAT<u32 length><key>` + chunks | One key image, keys 1 to 6 |
| `STP` | Refresh: shows the images sent so far |
| `CLE\0\0\0<key or 0xFF>` | Clear one key, or all of them |
| `LOG<u32 length>\x01` + chunks | The welcome screen, written to flash ([how](welcome-screen.md#how-a-write-works)) |

The handshake is `DIS`, `LIG`, `QUCMD`, `LIG`. The deck sends no input until it has seen it.

Two vendor frames are never sent, and no code path can build them: `CLE\0\0DC` ("software disconnected"), which blanked the development deck's screen, and `HAN`, which puts the screen to sleep. A unit test checks that nothing the protocol module produces starts with either.

## Input

Every input report starts `ACK\0\0OK\0\0`, followed by a code and a state byte (1 is press, anything else release). Token Deck matches `ACK` at bytes 0 to 2 and `OK` at bytes 5 and 6, and drops anything else.

| Control | Codes |
|---|---|
| Screen keys 1 to 6 | `0x01` to `0x06`, left to right, then top to bottom |
| Metal buttons | `0x25` left, `0x30` middle, `0x31` right |
| Big knob | `0x51` clockwise, `0x50` counter-clockwise, `0x35` press |
| Left knob | `0x91` clockwise, `0x90` counter-clockwise, `0x33` press |
| Right knob | `0x61` clockwise, `0x60` counter-clockwise, `0x34` press |
| Write report | `0x00`, the deck's answer to a successful `LOG` |

A knob sends one report per detent. Keys, the left and right buttons and knob presses act on press. The middle button acts on release, or after an 800 ms hold, which opens your own modes. The decoder's tests replay a real capture from the development deck, `test/fixtures/events-2026-11-01.log`.

## Tiles

Each tile is drawn upright on a 64 × 64 canvas with `@napi-rs/canvas`, turned 90° clockwise as a pixel copy (the firmware expects it sideways) and encoded as a baseline JPEG at quality 100.

- **Quality 100 on purpose.** At 100 the encoder keeps full colour resolution (4:4:4). At 99 and below it halves it (4:2:0), and a 1-pixel lime or coral line loses half its saturation. A test checks the sampling factors, so a dependency update can't switch it silently.
- **No anti-aliased text.** Tile text uses a 5 × 7 bitmap font drawn in code as filled rectangles (`src/main/deck/pixelfont.ts`). The agent logos are their owners' one-colour marks from `brand-kit/design/agent-glyphs/`.
- **Size.** Every built-in tile is under 10,000 bytes; a test checks that too.
- **Position.** The firmware draws each tile at a fixed spot that sits off-centre in its key's window, and the window shows a few pixels of the welcome screen around it. `resources/panel-geometry.json` holds the measured positions, and each layout is shifted per key so it's centred in the window.

## Writing to the deck

`src/main/deck/transport.ts` is the only code that writes. It sends one group of frames at a time, start to finish: a command, a key image with all its chunks, a whole repaint, or a whole welcome-screen write. The heartbeat and the keepalive wait their turn, so they never land in the middle of an image. Only the newest image per key is queued, so turning a knob fast never builds a backlog. By default the app also re-sends key 1 every second while idle (the `repaintKeepalive` setting), because this firmware family has been reported to stop repainting after a silence.

`node-hid` has no hot-plug events, so while no deck is open Token Deck lists devices every two seconds. A write error, a read error, or the computer waking from sleep closes the connection and opens it again with a fresh handshake and the current keys. A write that hangs for 5 seconds, or three failed opens in a row, shows "Deck not responding. Unplug it and plug it back in."

When Token Deck quits, it paints the welcome tiles into the keys, stops the heartbeat and closes. About a minute later the firmware restarts and shows the welcome screen from flash, which looks the same.

## What was measured on the development deck

The development deck is USB `5548:1001`, firmware `V3.VSDN3_PXL.02.010`, serial `81D0DA782A24`. Between November 1 and 5, 2026:

- The exclusive open works, and a second open from another process fails with `0xE00002C5`.
- `getFeatureReport` returned the firmware string, and the keys kept working after the read.
- The first tile encoded by `@napi-rs/canvas` at quality 100 (6,620 bytes) was accepted. Clearing a key with the three-zero layout worked.
- Ten welcome-screen writes from 1.8 to 22.3 KB were accepted, each answered by the write report 0.12 to 0.26 s after the last chunk. Three of them were checked after a power cycle and had persisted. Writes without tiles painted first always failed.
- The first write through the app itself, on a fresh settings store, waited out the settle, wrote the welcome screen and got the write report (recorded at `2026-11-05T10:11:26Z`).
- Codex's `account/rateLimits/read` returned a 5-hour and a 7-day window over `codex app-server`.

Not yet checked on hardware: the power-on photo and replug check of the final welcome screen, the boot brightness against the app's default of 70, a 15-minute keepalive soak, reconnecting after sleep, how long the last tiles stay up after a quit or a crash, a write from Windows, decks from the giveaway stock, and the Mirabox-branded units. The small knobs' codes come from the vendor table and the November 1 capture; which physical knob is which hasn't been confirmed by hand.
