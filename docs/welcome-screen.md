# The welcome screen

The deck keeps exactly one image in its own flash memory, the one the vendor calls the boot or background image, and Token Deck puts its welcome screen there. The deck shows it when it powers up, whenever its firmware restarts (about a minute after the computer stops talking to it), and around the edges of the keys while Token Deck runs. Everything else the keys show lives in RAM and is gone when the deck loses power, and the buttons do nothing without an app. So the welcome screen is the only thing a deck can show on its own.

Token Deck's welcome screen has the Stigg logo on key 1, `io.stigg.io` / `/usage` on key 4, "The AI Usage Management Console" on key 6, and the After Tokens token explosion across keys 2, 3 and 5.

| File | What it is |
|---|---|
| `resources/welcome-320x240.png` | The welcome screen, upright, 320 × 240 |
| `resources/welcome-sent.jpg` | The exact bytes written to the deck: 18,887 bytes, rotated for the wire, sha256 `daea022363c85ef722c9c93bcd7f5379a995b726cb5240bc4ed92b12d15071fb` |
| `resources/welcome-tiles/key1-6.jpg` | The same image cut into the six keys, painted before a write, when Token Deck quits and when it's idle |

The welcome screen was rendered from the private design kit with Söhne, which can't be in this repository. Don't redraw or re-encode these files: another renderer changes the hinted type and the hash. The design history is in [PLAN.md](../PLAN.md), section 9.

## When Token Deck writes it

Flash wears out, so each deck gets written once:

- **Automatically**, the first time Token Deck sees a deck whose serial number is in neither its own record nor `resources/preburned.json` (the list of decks prepared for the event). It waits 8 seconds after the deck appears, writes, and records the serial, the image hash and the time. Decks without a serial number are skipped. After two failed attempts on one deck it stops trying. The About page has a switch to turn the automatic write off.
- **By hand**, from About → Write welcome screen again, after a confirmation. Use it after another tool replaced the welcome screen.
- **In bulk**, with `burn --watch` ([below](#preparing-many-decks)).

## How a write works

The sequence was worked out on the development deck (USB `5548:1001`, firmware `V3.VSDN3_PXL.02.010`) and every step is in `src/main/burn/sequence.ts`, with tests against a fake deck in `test/queue-burn.test.ts`:

1. Open a fresh connection and send the handshake.
2. Wait 0.5 s, then paint the six welcome tiles and refresh. Writes without tiles painted first always failed.
3. Wait 1 s, then send the `LOG` header and the image in one unbroken stream.
4. Send nothing, not even the heartbeat, until the deck answers with its write report, for up to 10 s.
5. Refresh, wait 1 s, repaint the current keys and hold the connection for 10 s.

No write report means the write failed. Token Deck then sends nothing else to that deck but the heartbeat, because the firmware ignores image writes until it's power-cycled and a refresh after a failed write can leave the screen black. The app says "The welcome screen was not written. Unplug the deck and plug it back in."

Token Deck never sends the vendor's "software disconnected" frame, which clears the screen, or its sleep frame. When it quits it paints the welcome tiles into the keys and closes the connection, so the deck looks the same before and after its firmware restarts.

## Preparing many decks

This is how the Stigg team wrote the welcome screen to the giveaway decks, on a Mac:

1. Quit Token Deck from its menu, and quit the StreamDock and VSD Craft apps. On macOS only one program can open the deck, and a running Token Deck would grab each deck and write it itself.
2. Run:

   ```bash
   "/Applications/Token Deck.app/Contents/MacOS/Token Deck" burn --watch
   ```

3. Plug in a deck. The tool waits 8 seconds, prints the deck's maker, serial number and firmware, writes the welcome screen, holds for 10 seconds and prints `done, unplug and plug the next`. A deck it already wrote prints `already burned, unplug`.
4. If a write fails, it prints `FAILED: this deck may now start black. Unplug it and plug it back in to retry.` in red and won't take another deck until that one has been replugged and written. A deck whose last write failed must not ship.
5. Press Ctrl-C to stop. It prints which serials were written and which failed.

Expect about 25 seconds per deck. Every write is appended to `~/.tokendeck/preburned.json`. Commit that file as `resources/preburned.json` before tagging the release, so attendees' copies of Token Deck never write those decks again.

Before a large batch, write one deck, replug it with nothing running and check the screen, and confirm that a second deck reports a different serial number (the records can't tell two decks with the same serial apart).

## If a deck starts black

Unplug it and plug it back in, then write the welcome screen again: let the automatic write retry, or use About → Write welcome screen again. Power-cycling and writing again is also the vendor's own recovery for a failed write. Partial image data can wedge the deck, which is why nothing else is sent after a failed write.

## Other firmware

`resources/panel-geometry.json` records where this firmware draws each 64 × 64 key image inside its window, measured on the development deck. A deck with other firmware may differ. `tokendeck calibrate` isn't implemented yet; the manual procedure, a ruler image written to the deck plus a test tile on every key, is in [PLAN.md](../PLAN.md), section 9, step 2, and the ruler is `resources/calib-ruler-240x320.jpg`.
