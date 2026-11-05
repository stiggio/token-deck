# Gabriel's Token Deck: verified device facts (Nov 1-3, 2026)

Later sections supersede earlier ones; the app's rules are the section "Rules for the Token Deck app"
(only "Files the scripts rewrite" follows it), and where they differ
from `plans/token-deck/PLAN.md` sections 3 and 9, the plan wins.

Probed with `probe_n3.py` (own code, hidapi + Pillow, venv `~/.venvs/at`). The vendor StreamDock app was not running.

- USB: vendor 0x5548 "HOTSPOTEKUSB", product 0x1001 "HOTSPOTEKUSB HID DEMO", serial 81D0DA782A24.
  Not the Mirabox ids (6603:1002 / 6603:1003); the firmware family is the same.
- Firmware string (GET_INPUT_REPORT id 0, 64 bytes): `V3.VSDN3_PXL.02.010`
  (Mirabox-branded units report `V3.293N3_PXL.02.010`).
- HID interfaces: interface 0 = vendor interface, usage page 0xFFA0, usages 1 and 2 (same path);
  interface 1 = a keyboard (usage page 1, usage 6) that macOS protects (open fails; not needed).
- Output reports: 1024 bytes (+ leading 0x00 report id in hidapi writes). Input reports: 512 bytes.
- Commands that worked: `CRT\0\0DIS` (wake), `CRT\0\0LIG\0\0<pct>` (brightness),
  `CRT\0\0QUCMD\x1f\x11\x00\x11\x00\x11\x00` (vendor connect config), `CRT\0\0CONNECT` (heartbeat),
  `CRT\0\0BAT<u32be jpeg len><key 1-6>` then the JPEG in 1024-byte chunks, `CRT\0\0STP` (refresh).
- Documented by the vendor binary, tested on Nov 1 where noted:
  - `CRT\0\0CLE\0\0\0<key|0xFF>` clear one key / all (the key byte sits at payload index 11, after THREE
    zero bytes; MelvinTo's four-zero layout is wrong). Not sent yet.
  - `CRT\0\0HAN` sleep. Not sent yet.
  - `CRT\0\0CLE\0\0DC` "software disconnected". **The vendor's Python API reference documents
    `disconnected()` as "Disconnects and clears all display."** Sent once, at 20:10 (test 1 below):
    the panel went black and stayed black, no logo, keys still reporting. Nothing documents a logo
    fallback for the N3 (the N4 Pro, a different device, shows its standby logo after it). Rule for
    the app: never send it; see "Rules" below.
  - `CRT\0\0LOG<u32be jpeg len>\x01` + a 320x240 JPEG rotated 90 degrees clockwise (240x320 on the
    wire) = the boot/background image, written to the device ROM per the vendor README ("writes to the
    device's ROM ... remains after restart"; flash wear, so write it once). Sent twice (tests below);
    persistence on this unit: see test 2.
- Key tiles: 64x64 JPEG (quality 100, baseline; 4:2:0 in these probes, and q100 4:4:4 renders too,
  test 14; the app ships 4:4:4), **pre-rotated 90 degrees clockwise**
  (`PIL rotate(-90)`). Gabriel confirmed the test tiles were visible on keys 1-3.
- **Input reports only arrive after the connect handshake** (DIS, LIG, QUCMD, LIG). A plain open
  with no handshake produced nothing for 150 s. With the handshake, every control reports:
  - frame: `ACK\0\0OK\0\0` (9 bytes: 41 43 4B 00 00 4F 4B 00 00) + code at byte 9 + state at
    byte 10 (key 1 press = `41434b00004f4b0000010100`); match `ACK` at 0-2, never a 10-byte literal;
  - LCD keys 1-6: codes 0x01-0x06, state 1 = press, 0 = release;
  - metal buttons: 0x25 = left, 0x30 = middle, 0x31 = right (press 1 / release 0). Verified:
    Gabriel pressed them left to right in a second round.
  - knob clicks: 0x33, 0x34, 0x35 (press 1 / release 0);
  - knob rotation: one report per detent, state 0.
    **Main (large, top) knob: 0x51 = clockwise, 0x50 = counter-clockwise, click 0x35** (verified:
    Gabriel turned it clockwise first in a second round and the log shows 0x51 x9 then 0x50 x8).
    The two small knobs, per the vendor SDK's own code table (MiraboxSpace/StreamDock-Device-SDK,
    streamdockN3V25.cpp `_readValueMap`): **bottom-left knob = click 0x33, clockwise 0x91,
    counter-clockwise 0x90; bottom-right knob = click 0x34, clockwise 0x61, counter-clockwise 0x60.**
    Both knob states arrive on this firmware (click = 0x3x/1 then 0x3x/0). The first round of the
    capture (events log lines 105-140) has all six small-knob codes: 0x61/0x60 then clicks 0x34, and
    0x91/0x90 then clicks 0x33, the vendor's pairing. Which physical knob and which direction were not
    noted (the second capture closed before the small knobs), so the app confirms them on first run.
  - vendor table for the record (same file): LCD keys 0x01-0x06 left-to-right, top-to-bottom; bottom
    buttons 0x25/0x30/0x31 left-to-right; a report with byte 9 = 0xFF is a write acknowledgement.
- **Writes are not acknowledged, with one exception**: BAT, STP and CLE DC never produce a report.
  Every accepted `LOG` write answered once after its last chunk (`ACK\0\0OK\0\0` + code 0x00 + state
  0; tests 3, 13, 14 and welcome v1-v4, v6-v8). Nothing was ever sent between the last chunk and that
  report. Tests 1 and 2, which sent `STP` at once, got none, but they also had no tiles first (see the
  correction after test 12). The input side otherwise carries key/knob events only.
- What the deck shows when the host just closes (no `CLE DC`): observed on every probe session before
  20:10 (handshake + tiles, then the handle closed): the panel went back to the stored boot image, the
  factory VSD logo. Consistent with a community report that this firmware restarts by itself about a
  minute after the host stops sending `CONNECT` (opendeck-akp03 issue 44); the restart shows the ROM
  image.
- Still not tested: `CLE` of one key / all. `HAN` is never sent (Gabriel's rule). The write report
  timing is measured: 0.12-0.26 s after the last chunk (tests 13, 14, welcome v1-v4, v7, v8).

Raw capture: `events-2026-11-01.log`.

## LOG test 1 (Nov 1, 2026, 20:10): token field, then `CLE DC`

`burn_logo.py` (as it was that evening) sent the token-field placeholder in `boot-image/` as the `LOG`
frame: handshake (brightness 70), `CRT\0\0LOG` + u32be 11139 + 0x01, 11 chunks of 1024 bytes, `STP`
immediately, 3 s listening, 2 s pause, then `CLE\0\0DC` (the first time that frame was ever sent),
close. Every write was accepted, no input report came back for any of it, and the device kept
enumerating and answering the firmware read afterwards. The JPEG was 240x320 (the 320x240 image
rotated 90 degrees clockwise, PIL `rotate(-90)`), q90, 4:2:0, baseline (`boot-image/boot-image-sent.jpg`,
`boot-image/boot-image-as-seen.png`).

**Result (Gabriel, by eye, about two hours later): the panel was black. No lime or white squares, no
VSD logo, "screens are 100% empty"; the keys still worked.** Whether he had power-cycled the deck
before looking is not known. Reading of it after the research pass (`research-black-screen-2026-11-01.md`):
the black is the `CLE DC` "clears all display" state, which this firmware does not leave by itself;
whether the LOG write also took is what test 2 decides. The factory VSD logo is gone from this unit
either way; it was never saved.

## LOG test 2 (Nov 1, 2026, 22:49): solid lime, no `CLE DC`

`log_test.py lime --hold 3` (as it was that night): handshake at brightness 100, `LOG` with a solid
`#92E759` 320x240 image (1830-byte JPEG, 240x320 on the wire, same encoding), `STP` immediately,
2 s listening (nothing), 3 s hold, handle closed without `CLE DC` (`boot-image/test-lime-sent.jpg`).

**Result (Gabriel, Nov 2, early morning): black both times. (a) Black with nothing running. (b) Black
after an unplug/replug, no VSD logo, no lime.** So the `LOG` write does reach the boot slot (the
factory logo is gone at power-on), but what is stored renders black, and nothing painted live either.
Bottom row of the table. Next: test 3 below. The table, kept for the record:

| (a) now | (b) after replug | Meaning |
|---|---|---|
| lime | lime | LOG paints the panel and persists in ROM; the Nov 1 20:10 black was the `CLE DC` clear. Burn path confirmed. |
| lime | VSD logo | LOG is a volatile background on this firmware; the boot logo is a separate slot we cannot write with LOG. No burn; the app paints the welcome tiles on quit. |
| lime | black | the panel paints LOG live, the ROM copy failed. Rewrite with the vendor rhythm (below); then q85, then 320x240 unrotated, one variable at a time, replug after each. |
| black | lime | LOG goes only to the boot slot. Burn works; the app must paint tiles on every connect. |
| black | VSD logo | LOG never took with this framing. |
| black | black | slot blank or the panel not painting: first prove painting with one bright `BAT` tile + `STP`, then LOG variants; if nothing paints, VSD/TreasLin support. |

## LOG test 3 (Nov 2, 2026, 05:55): six tiles, then solid lime in the vendor rhythm

`log_test.py lime --tiles --hold 180`: handshake at brightness 100; six solid tiles (keys 1, 3, 5
lime; 2, 4, 6 white) over `BAT` + `STP`, the path verified on Nov 1, so the eye can confirm the panel
paints; then `LOG` with the same 1830-byte lime JPEG, 3 s listening before `STP` (the vendor's read),
`STP`, 1 s quiet, then 180 s holding the handle open with `CONNECT` every 10 s, then closed without
any goodbye frame. Run log: `test3-run.log`.

**New fact from the run log: during the 3 s listen between the last `LOG` chunk and `STP`, one input
report arrived: `ACK\0\0OK\0\0\0` with code 0x00, state 0.** It is the first report any write has
ever produced on this unit. Tests 1 and 2 sent `STP` with no gap and never saw it (the listen there was
after the `STP`). Reading: the firmware answers a finished background write, and this is the report
libtransport's 3 s read is waiting for; an `STP` arriving before it appears to cut the write short
(tests 1 and 2 ended with a black slot). Timing of the report inside the 3 s window: not measured yet
(next run timestamps it).

**Result, live (Gabriel, during the hold): "It's now all bright lime."** The whole panel shows the
`LOG` image through all six windows; the six tiles painted just before it are gone, so the background
write replaces everything on the panel at `STP` (the app must repaint its tiles after a burn). The
`ACK` report with code 0x00 arrived in the 3 s window before `STP`. Gabriel unplugged the deck during
the hold (the script died on the next heartbeat: "Device is disconnected", as expected).
**After the replug, with nothing running: "it all still bright lime." Persistence verified.** The
`LOG` slot is the boot image, it survives a power cycle on this firmware, and the whole difference
between black and lime was waiting for the device's write report before the refresh.

## LOG tests 4 to 6 (Nov 2, 2026, 06:10 to 06:17): the 11 KB token field, and the report that stopped coming

After test 3's replug (deck booting lime), Gabriel asked for the token-field placeholder
(`burn_logo.py`, 11,139 bytes, 11 chunks). Sequence, all in the same power cycle, no replug between:

- 4a `burn_logo.py`: handshake, `LOG` field, wait 3 s → **no report**; the script stopped before `STP`
  by design (its log was overwritten by 4b's).
- 4b `burn_logo.py` with a 2 s settle after the handshake and a 20 s wait → **no report**, no `STP`
  (log `burn-2026-11-02.log`).
- `log_sweep.py lime` (the 1.8 KB lime that answered in test 3; 2 s settle, 8 s wait) → **no report**.
- 5 `log_test.py lime --tiles --hold 12`, test 3's exact frame sequence → **no report**; `STP` sent
  anyway (`test5-tiles-lime.log`).
- 6 `log_test.py field --wait-before-stp 6 --hold 12`: `LOG` field, 6 s wait (no report), `STP`, 1 s,
  12 s hold, silent close (`test6-field.log`). **Result: solid black (below).** Token-field
  dots on dark = 11 KB writes work and the report is simply not reliable; solid lime = the deck has
  not processed any `LOG` since 4a and needs a power cycle.

Superseded by the correction after test 12 (tiles first) and the rule after test 17. Reading at the
time: the code-0x00 report is not a dependable success signal (test 3 is the only time it
ever came). Two explanations are open until the test 6 result is in: (T1) a failed or oversize `LOG`
leaves the firmware ignoring further `LOG` frames until a power cycle; (T2) the writes succeed
silently and only the first `LOG` after power-up is acknowledged. Token-field JPEG sizes for the
record (4:2:0): q50 6.3 KB, q70 7.3 KB, q85 9.6 KB, q90 11.1 KB; 4:4:4 adds 25 to 35 %.

**Test 6 result (Gabriel): solid black.** The 11 KB field + 6 s wait + `STP` blanked the panel.

## LOG test 7 (Nov 2, 2026, 06:29): replug, then exactly one 11 KB write

`replug_write.py field --wait-before-stp 6 --hold 10`: waited for Gabriel's unplug/replug, fired 3 s
after the deck came back: handshake, `LOG` field (11,139 bytes, the first and only `LOG` of that power
cycle), 6 s wait (**no report**, so the code-0x00 report of test 3 is not "first write after power-up"
either; it remains a one-off), `STP`, 1 s, 10 s hold, silent close (`test7-replug-field.log`). **Result (Gabriel): solid black.** So "one `LOG` per power cycle" (T2)
is dead too; the 11 KB image fails even as the first and only write after power-up.

## LOG test 8 (Nov 2, 2026, 06:33): the 11 KB field with 40 ms between chunks

Same power cycle as test 7, no replug. `log_test.py field --chunk-gap 40 --wait-before-stp 6 --hold 10`:
the 11 chunks spread over 0.46 s instead of 10 ms, 6 s wait (no report), `STP`, hold, silent close
(`test8-field-paced.log`). Tests whether the firmware drops back-to-back chunks (a pacing problem)
rather than refusing the byte count. **Result (Gabriel): solid black, also after a replug.** Pacing is
not it.

## LOG test 9 (Nov 2, 2026, 06:37): the 1.8 KB lime padded after EOI to 11,139 bytes

`log_test.py lime --tail-pad 11139 --wait-before-stp 6 --hold 10`: the lime JPEG with zero bytes
appended after its `FF D9` end marker so the stream has exactly the token field's byte count; decoders
stop at EOI, so the picture is the known-good lime and only the byte count changed. 6 s wait (no
report), `STP`, hold, silent close (`test9-lime-padded.log`). Lime = the byte count is not the limit
and the token field fails on content; black = a byte limit between 1,830 and 11,139.
**Result (Gabriel): black. The limit is the byte count.**

## LOG size bracket (Nov 2, 2026, 06:38 to 06:44): VOID, see the correction below

Lime padded after EOI to 8,192 (test 10), 4,096 (test 11), and a clean, unpadded 6 KB lime with film
grain (test 12): all black. None of them was preceded by a power cycle.

## Correction (Nov 2, ~06:50): tests 8 and 10 to 12 measured nothing

A failed write appears to make the firmware ignore further image writes until the deck is power-cycled:
test 5, the exact frame sequence of test 3, got no write report when it ran in the same power cycle as
two failed 11 KB writes. Tests 8 (paced 11 KB), 10, 11 and 12 all ran in a power cycle that had already
seen a failed write, so their black results say nothing about size or pacing. Only the first image
write after a power-up counts:

| test | first write after power-up | tiles first | bytes | write report | panel |
|---|---|---|---|---|---|
| 3 | yes | yes | 1,830 | yes | lime, survived a replug |
| 4a | yes | no | 11,139 | no | not looked at |
| 7 | yes | no | 11,139 | no | black |
| 9 | yes | no | 11,139 (padded) | no | black |
| 2 | unknown (no replug known after test 1) | no | 1,830 | not listened for | black |

Size and "tiles painted first" are confounded: the one success had a small image and tiles first, every
clean failure had neither. Against a small size cap: the factory VSD image had gradients and logos, and
the vendor's own Python SDK sends this same call with Pillow's default q75 JPEG. For scale, the test
card below (hue gradient + 24 outlined numbers) is 21.8 KB at q75, 27.2 KB at q85, 32.1 KB at q90 and
fits 11,139 bytes only at q24.

## LOG test 13 (Nov 2, ran 06:57): replug, tiles first, 11 KB rich test card

`replug_write.py --settle 8 card --tiles --fit-bytes 11139 --wait-before-stp 10 --hold 20`: after the
replug and 8 s, handshake, six tiles + `STP`, then the test card (`boot-image/test-card-as-seen.png`;
hue gradient, 24 numbered cells, q24 = 11,093 bytes, the size of the failed writes), wait up to 10 s
for the write report, `STP`, hold 20 s, silent close (`test13-replug-tiles-card.log`). Against test 7
it adds tiles first and a longer settle; against test 3 it changes only size and content.
**Run log: the device answered the 11 KB write.** `ACK\0\0OK` + zeros (raw
`41434b00004f4b000000000000000000`, code 0x00, state 0) arrived 0.13 s after the last chunk, the first
write report since test 3; then `STP`, 20 s hold, silent close. **Panel result (Gabriel, with a photo,
`photos/test13-card-on-deck.webp`): the rainbow card, in order.** So an 11 KB rich image burns fine when
tiles are painted first; size was never the problem at this scale.

What the photo shows about the panel geometry (coarse; test 14 measures it):
- Each key window shows a 2 x 2 block of the card's 6 x 4 grid: key 1 (top left) cells 1, 2, 7, 8;
  key 2: 3, 4, 9, 10; key 3: 5, 6, 11, 12; key 4: 13, 14, 19, 20; key 5: 15, 16, 21, 22; key 6: 17, 18,
  23, 24. The six windows sit over the six thirds-by-halves of the 320 x 240 image.
- The windows crop (Gabriel: "not the whole numbers are in the screen"): each shows roughly 85 to 90
  panel pixels around its centre (estimated centres x 53/160/267, y 54/161), **not 64 x 64**. The
  bottom windows show little of cells 19 to 24, so the lowest ~35 px of the panel are probably hidden.
- Open consequence: how the firmware places a 64 x 64 key tile in a window that shows ~88 px (scaled,
  or 1:1 with background around it). Test 14 answers it.

## Working rule as of test 13 (two successes, three clean failures; superseded by the rule after test 17)

First image write after a power-up, after six tiles + `STP`: accepted (write report within 0.13 s),
shown at once, survives a power cycle (test 3 checked; test 13 is checked at the start of test 14).
Without tiles first: three failures (tests 4a, 7, 9). After a failed write the deck ignores image writes
until a power cycle (test 5). Not yet separated: whether the tiles + `STP` or simply ~1.5 s between the
handshake and the `LOG` is what matters; the app paints tiles first anyway.

## LOG test 14 (Nov 2, armed ~07:10, ran 07:34): replug, persistence look, 22 KB ruler, frame tiles

`replug_write.py --settle 15 ruler --tiles --quality 90 --wait-before-stp 10 --frame420 5 --frame444 6
--hold 180`: after Gabriel's replug the deck boots on its stored image for 15 s (**is the test 13 card
still there?**); then handshake, six tiles + `STP`, `LOG` with the calibration ruler (`calib_images.py`,
22,307 bytes at q90, twice the proven size), wait up to 10 s for the write report, `STP`; then the
64 x 64 frame tile (magenta/white/black border, grey checkerboard, "64") on key 5 at q100 4:2:0 and on
key 6 at q100 4:4:4, each + `STP`; hold 180 s with the heartbeat for a straight-on photo; silent close
(`test14-ruler.log`).

**Run log (replug at 07:34:16, probe at 07:34:31):** the 22,307-byte ruler got the write report
(`ACK\0\0OK` + zeros) **0.26 s** after the last chunk (11 KB took 0.13 s, so roughly 12 ms per KB);
`STP`; frame tile key 5 (4:2:0, 6,045 bytes) + `STP`; frame tile key 6 (4:4:4, 6,681 bytes) + `STP`; no
errors. The hold then ran with `CONNECT` every 10 s until **07:36:09, when macOS logged a transaction
error on the input endpoint and "hardware connection lost"**; the deck re-enumerated at 07:36:13 and the
next heartbeat failed ("Device is disconnected"). Either Gabriel unplugged it, or the deck reset itself
about 90 s after the 4:4:4 tile while the heartbeat was running (to confirm with him).
**Visual results (Gabriel, photo `photos/test14-ruler-on-deck.webp`):** "Time-wise, it behaves as you
mentioned" (the test 13 card at boot during the 15 s settle, then the probe); the ruler shows in all six
windows; both frame tiles render, **the q100 4:4:4 tile on key 6 as well as the 4:2:0 one on key 5**;
the tiles are drawn 1:1, not scaled, with the ruler visible around them. The USB drop at 07:36:09 was
Gabriel replugging; after it the ruler was still there without the squares, so **22 KB persists**.

Windows measured from the ruler (panel coordinates, +-2 px): x 13-88 / 120-198 / 228-306,
y 20-97 (top row) / 130-206 (bottom row), so each window shows about 76 x 77 px.

## Test 15 (Nov 2, 07:44): the frame tile on all six keys over the burned ruler

`paint_tiles.py` (RAM only, no flash write), photo `photos/test15-six-tiles-on-deck.webp`. **The firmware
draws each 64 x 64 key image at a fixed position: x 20 / 124 / 228, y 28 / 131 (+-1 px)**, pitch
104 x 103, independent of where the windows are. So the burned image shows around every tile while the
app runs: up to 7 px left / 4 px right on keys 1 and 4, 4 / 10 px on keys 2 and 5, 0 / 14 px on keys 3
and 6, 8 px above / 5 px below the top row, 1 px above / 11 px below the bottom row.
`panel_geometry.py` holds both rect sets.

## Test 16 (Nov 2, 07:51): welcome screen v1

`burn_logo.py welcome/welcome-320x240.png` (v1 is kept as `welcome/welcome-v1-320x240.png`): handshake,
the image's own six tile crops + `STP`, `LOG` 14,206 bytes, write report at **+0.18 s**, `STP`, silent
close (`burn-welcome-v1.log`). It was the first `LOG` of that power cycle. Gabriel's feedback on v1: add
the URL, and the alignment was off (content centred in the tile rects, which sit off-centre in the
windows; a left-aligned slogan under a centred logo).

## Test 17 (Nov 2, 07:57): welcome screen v2, second `LOG` in the same power cycle

Same command with v2 (every element centred in its window and kept inside its tile rect, URL added,
5 x 5 tokens): `LOG` 8,310 bytes, write report at **+0.12 s** (`burn-welcome-v2.log`). **A second
`LOG` in the same power cycle works** when the previous one succeeded and tiles are painted first.
Result on the panel and after a replug: not recorded.

## Tests 18 and 19 (Nov 2, 08:02 and 08:04): welcome screen v3 and v4

Gabriel's direction after v2: "top-left logo, bottom-right slogan, mostly tokens explode pattern, and the
URL somewhere with tokens in it"; tokens "a little smaller and more exploded"; after v3: "the slogan should
align left and the URL on bottom right". v3 (`welcome/welcome-v3-320x240.png`, 11,374 bytes, report at
+0.14 s, `burn-welcome-v3.log`) and v4 (`welcome/welcome-320x240.png`, the Z layout, 10,930 bytes, report
at +0.13 s, `burn-welcome-v4.log`) were the third and fourth `LOG` writes of the same power cycle; both
accepted. v4 was on the deck until v6. Result on the panel and after a replug: not recorded.

## Working rule as of test 17

Burn = handshake, paint six tiles + `STP`, `LOG`, wait for the write report (about 12 ms per KB), `STP`.
Accepted: 1.8, 8.3, 10.9, 11.1, 11.4, 14.2, 22.3 KB at the time (15.8, 15.9 and 18.9 KB since: v7, v6, v8);
up to four writes in one power cycle, each a separate run (its own connection). Failed: every write
without tiles first; every write after a failed one until a power cycle. Untested: above 22.3 KB.

## Welcome screen v6 (Nov 2, burned)

Final design after a four-critic review of v5 (`welcome/review-v5-2026-11-02.md`): `welcome/welcome_v6.py`,
seed 259, then `welcome/welcome-320x240.png` + `welcome/welcome-sent.jpg`, now kept as
`welcome/welcome-v6-320x240.png` + `welcome/welcome-v6-sent.jpg` (q97, 15,927 bytes). Burned on Nov 2
right after the deck was plugged in, vendor app not running: `burn_logo.py welcome/welcome-320x240.png`
(its JPEG was byte-identical to `welcome-sent.jpg`), six tile crops + `STP`, `LOG` in 16 chunks, write
report `ACK` code 0x00 state 0 at +0.18 s (about 11 ms per KB), `STP`, 10 s heartbeat hold, close. So the
deck takes q97 (q90 was the highest on record before). Photo (`photos/welcome-v6-on-deck.webp`): it
renders as designed, colours and type intact. Lime tokens near a window edge show as faint reflections
in the clear keycap's bevel (top of key 4, left and bottom of key 2, top of key 5), so keep bright
content well clear of the rims. Replug check: not reported. Gabriel's feedback on it (Nov 2): bring back
the white tokens and the dim "background" tokens of v1, make the tokens a little smaller like the
stigg.io hero particles, make the text slightly larger, and reconsider where the URL and slogan sit.

## Welcome screen v7 (Nov 2, burned)

Gabriel's notes on v6 went to a design panel: four designs, two per layout (`welcome/v7/a-*` to `d-*`, each
with its `make.py` and previews; side by side in `welcome/v7/compare.png`), judged by four critics
(typography, composition, brand, device). All four critics put the slogan under the logo and the URL at the
bottom right. A right-column key holds 58 px and centres only 50 px (its tile hugs the window's left edge),
and 'Management' inks 57 px at 9.5 px and 63 px at 10.5 px (62 px with v7's -0.06 px tracking), so a
bottom-right slogan cannot grow and sits
4 px off centre. The URL under the logo costs the logo its clear space and puts bright ink on all four
bevels of key 1. The final is `welcome/welcome_v7.py` (shared helpers in `welcome/v7_common.py`), seed 184:
a and b's text keys on c's burst, with the critics' must-fixes applied.
- Layout: key 1 logo alone at (20, 50); key 4 slogan flush on the logo's x = 20; key 6 URL; art in keys 2,
  3 and 5.
- Type: Söhne Buch 10.5 / 13 px, tracking -0.06 px, for both blocks. 10.5 px is the first size whose hinted
  cap height and x-height (8 and 6 px) beat v6's (7 and 5 px). Every size from 9.5 to 10.49 px renders v6's
  heights and only gets wider. The tracking makes 'Management' fit key 4's 62 px with nothing in the rim
  and nothing erased. Each 'i' is the dotless glyph on a whole pixel plus a crisp one-pixel dot: the hinted
  dot bled into the stem, and under bloom the URL read 'lo.stlgg.lo'.
- Tokens: 3 px squares on a 5 px lattice (x = 4 + 5i, y = 4 + 5j), with identical 10 x 10 boards (48 px)
  of unlit #2C2F2B tokens in keys 2, 3 and 5. #2C2F2B is Stigg neutral 800. #3C3E3A made the boards
  outweigh the burst (judged by the v7 critics on the `lcd()` preview, not seen on the deck), and v1's dimmer #242723 boards were visible on the deck, so the `lcd()` emulation is
  pessimistic about dim greys. 60 bright tokens: 38 lime (the 19-cell source block included) and 22
  white. Three #639840 depth tokens in key 3.
- Checks: rim 0, outside tiles 0, darker 0, halo 0 (worst 3.2), JPEG q97 15,830 bytes. Known cost: 3 px
  lime cannot cover whole 4:2:0 chroma blocks, so each lime token decodes with a paler edge (mean channel
  deviation 31, against v6's 3). If it reads mint on the deck, the fallback is 4 px squares at even
  coordinates.
Burned on Nov 2 with the vendor app not running: `burn_logo.py welcome/welcome-320x240.png`
(`burn-welcome-v7.log`). The JPEG was byte-identical to `welcome-sent.jpg`. Six tile crops + `STP`, `LOG`
in 16 chunks, write report `ACK` code 0x00 state 0 at +0.25 s, `STP`, 10 s heartbeat hold, close.
Accepted writes so far: 1.8, 8.3, 10.9, 11.1, 11.4, 14.2, 15.8, 15.9 and 22.3 KB. Photo (Gabriel, Nov 2,
`photos/welcome-v7-on-deck.webp`): it renders as designed. The unlit #2C2F2B board tokens read clearly,
about a third of the way to white in the photo (far brighter than `lcd()` draws them;
`v8_common.photo_emul()` is fitted to this photo). 3 px lime reads lime, so the 4 px fallback is not
needed. White reads white and the 10.5 px type is legible. The clear keycap's bevels mirror tokens that sit
14-20 px from a window edge, lit and unlit (key 5's top bevel, key 3's left bevel, key 2's bottom bevel).
Replug check: not reported. His notes on it are in v8 below.

## Welcome screen v8 (Nov 3, burned)

Gabriel's notes on v7 as burned: "Why no tokens in the tile where the URL is? It might be complimentary",
"Why is there that big gap in the tiles between the tokens and the tile boundaries", "I think we better do
the URL on bottom left and slogan in bottom right". They went to a design panel: the brief
`welcome/v8/BRIEF.md`, four designs (`welcome/v8/a-*` to `d-*`, each with its `make.py`, `design.md` and
previews; next to the photo in `welcome/v8/compare-photo-emul.png` and `compare-photo-lcd.png`) and four
critics (typography, composition, brand, device). Typography, brand and device picked c (v7's burst, a calm
board around the URL). Composition picked d (the URL set into the field, the burst cascading to it) and put
c second. The final is `welcome/welcome_v8.py` (shared helpers in `welcome/v8_common.py`), seed 7: c with
the critics' must-fixes and the grafts they agreed on.
- Layout: key 1 the logo, as in v7; key 4 the URL, set into its own token board; key 6 the slogan; art in
  keys 2, 3 and 5.
- Boards (note 2): each key gets the largest board of 3 px tokens on a 5 px pitch that stays inside its
  tile, centred on its window to 1.5 px (`v8_common.board_fit`), each on its own lattice phase. Sizes and
  positions:
  - key 2: 12 x 13, x 130-187 / y 28-90;
  - key 3: 11 x 13, x 239-291 / y 28-90;
  - key 4: 12 x 11, x 21-78 / y 141-193;
  - key 5: 12 x 11, x 130-187 / y 141-193.
  The window around each board is now 6-12 px against v7's 13-16 px, and 14 px on key 3's right, where the
  firmware's tile ends. A centred board cannot be wider there, and nothing may be drawn outside the tiles.
- Type: the URL is 10.5 / 13 px, flush left, ink x 28-71 / y 156-178, centred on window 4 (-0.5 / -0.5 px).
  The slogan is 9.5 / 12 px, flush right on x 291, cap top 152, ink x 235-291 / y 152-182; its box is
  -3.5 / -0.5 px off centre and its visual mass -1.0 / -1.4 px (flush left would put the mass at -7 px).
  It cannot be bigger in key 6: 'Management' inks 57 px at 9.5 px and 62 px at 10.5 px, and key 6 holds
  58 px. Cap top 153 rings 5 luma levels past x 291. New against v7: 'i', 'I' and 'l' are one crisp, fully
  lit column (no 33 % column beside the stem); each period sits in the middle of its gap (the second period
  of io.stigg.io moved from x 61, against the g, to x 62).
- Key 4 (note 1): no token within 4 px beside the URL or 7 px above and below it (the dome ghosts strokes
  about 1 px downward). Inner tokens keep 10 px after a line ends, so they never read as more characters,
  and the field steps back in after '/usage' (67 cells not drawn). Three lime tokens have landed there, at
  (a5, b9), (a9, b9) and (a7, b1). Key 4 has no white token: there, white is the type.
- Burst: v7's on the bigger boards. The source block in key 5 sits at x 140-157 / y 161-188 (17 lit), at
  least 17 px from the window edges. Bright tokens, with white leaning to the far end and 0.371 of all
  bright tokens white:
  - key 5: the 17 source tokens plus 11 debris (7 lime, 4 white);
  - key 2: 17 (7 lime, 10 white);
  - key 3: 14 (5 lime, 9 white), plus 3 #639840;
  - key 4: 3 lime.
- New device rules:
  - No lit token within 14 px of a window edge (v7's nearest, which the bevels mirrored).
  - No lime or #639840 token in a 16 x 16 JPEG chroma block that holds window pixels outside the tiles.
    That tint was v7's 6 levels of blue in window 2; v8 is at most 3 levels in every channel in windows
    2-6.
  - Key 2's side toward the logo and key 5's side toward the slogan stay dark.
- Checks: rim 0, outside tiles 0, darker 0, luma halo 3.2 (count 0), colour halo [5, 4, 7] in window 1
  only (the logo's left edge, as in v6 and v7), JPEG q97 18,887 bytes.
Burned on Nov 3 with the vendor app not running: `burn_logo.py welcome/welcome-320x240.png`
(`burn-welcome-v8.log`). The JPEG was byte-identical to `welcome-sent.jpg`. Six tile crops + `STP`, `LOG`
in 19 chunks, write report `ACK` code 0x00 state 0 at +0.26 s, `STP`, 10 s heartbeat hold, close.
Accepted writes so far: 1.8, 8.3, 10.9, 11.1, 11.4, 14.2, 15.8, 15.9, 18.9 and 22.3 KB. v7 is kept as
`welcome/welcome-v7-320x240.png` + `welcome-v7-sent.jpg`. Watch on the next photo:
- the board tokens 6-8 px from the window edges, in the bevels (fallback: 12 rows in keys 2 and 3, y 29-86);
- the frame columns 4 px beside the URL;
- the g of 'Management' 3 px above the C of 'Console'.
Photo and replug check: pending.

## Research, Nov 2: region drawing and the vendor's pre-LOG order (`research-display-architecture-2026-11-02.md`)

- `CRT\0\0BGPIC` + u32be JPEG length + u16be x, y, w, h + `00` + framebuffer layer, then the JPEG in 1024-byte
  reports, draws a JPEG at any panel position into RAM (no flash write); `CRT\0\0BGCLE` + `03` clears it. The
  vendor enables it only on N4 Pro / XL / M3; whether this N3 firmware accepts it is untested. If it does, the
  app can draw the whole ~76 px window at runtime instead of only the 64 px tile. One probe per power cycle.
- The vendor SDKs send `DIS`, then `CRT\0\0CLE\0\0\0\xff` (clear all) and `STP` before `LOG`, never tiles. Our
  rule (tiles + `STP` first) works; whether clear-all + `STP` works too is untested.

## What the vendor's own transport does for the same write (from the libtransport disassembly)

`setBackgroundImgFile()` → `CRT\0\0LOG` + u32be length + 0x01, the JPEG in 1024-byte chunks, then ONE
blocking input read with a 3 s timeout (the vendor default), and only after that read returns does the
queued `STP` from `refresh()` go out; the vendor's N3 test then sleeps 1 s. No other delay anywhere.
`disconnected()` sends exactly `CRT\0\0CLE\0\0DC` and nothing else; closing the transport sends nothing.
Both our Nov 1 writes sent `STP` with no gap; `burn_logo.py` now follows the vendor rhythm.

## Rules for the Token Deck app (Nov 3, 2026; PLAN.md sections 3 and 9 are authoritative)

- Heartbeat `CONNECT` every 10 s for the whole session; it waits while a frame group or a burn is on
  the wire (nothing at all goes out between a `LOG`'s last chunk and its write report).
- Burn = its own connection; after a plug-in, at least 8 s after the deck enumerated with nothing
  opened before (a later burn in the same power cycle after a successful one also works: v1 after test
  15's connection, v2-v4 after earlier runs):
  handshake, 0.5 s, the image's six tile crops + `STP` (`welcome/welcome-tiles/`, the bytes
  `burn_logo.py` sends), 1 s, `LOG` + chunks as one unbroken stream, wait for the write report
  (`ACK\0\0OK\0\0` + code 0x00 + state 0; 0.12-0.26 s seen; give up after 10 s) with nothing sent,
  `STP`, 1 s with nothing sent, repaint the tiles, hold the handle 10 s more with the heartbeat. The
  burned image replaces the whole panel, tiles included. Several burns per power cycle work, each as
  its own run after a successful one (four on Nov 2, v1-v4); two `LOG`s on one connection were never
  tried. Verified: tests 3, 13 and 14 (persisted after a power cycle) and welcome v1-v4, v6, v7 and v8
  (write reports).
- No report = failed burn: no `STP` (after an unanswered `LOG` an `STP` left the panel black: lime at
  boot after test 3, solid black after tests 5 and 6 each sent `STP` after an unanswered `LOG`), nothing to that deck but the heartbeat, no retry until it has been unplugged and plugged in
  again (the firmware ignores image writes until a power cycle). A write that fails mid-stream follows
  the same rule.
- Quit = paint the welcome tiles, `STP`, stop the heartbeat, close (after a failed burn: stop the
  heartbeat and close). Never `CLE DC`, never `HAN`, not even behind a debug flag (Gabriel's rule).
  `burn_logo.py --dc` / `--dc-only` and `log_test.py --dc` remain the only ways to send `CLE DC`, by
  hand, outside the app.
- Tiles: content inside tile ∩ window inset 6 px (keycap rim); bevel mirrors within about 20 px of a
  window edge are expected on tiles; unlit squares `#2C2F2B`.

## Files the scripts rewrite

`burn_logo.py` rewrites `boot-image/boot-image-sent.jpg` and `boot-image-as-seen.png` on every run, and
`log_test.py` rewrites `boot-image/test-<image>-sent.jpg`: in `_source` they now hold v8's bytes and
test 11's 4,096-byte padded lime. The kit's copies keep the bytes cited above for tests 1-3 (the
11,139-byte field and the 1,830-byte lime). `burn-2026-11-02.log` is test 4b's log (4a's was
overwritten). There is no `burn-welcome-v6.log`; v6's write report is recorded only in this file.
