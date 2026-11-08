# Research record: N3 display architecture, key-image placement, boot-logo flow, region drawing (Nov 2, 2026)

Re-run after a network failure: three research agents, one checker per angle (all checked this time), one
synthesis that also read this unit's own measurements (NOTES.md, panel_geometry.py). Nothing touched the device.

---

# VSD N3 display synthesis

D documented, O observed by others, I inferred, U unknown, GT this unit [S1].

## 1. Answers

**Q1.** One 320x240 framebuffer spans all six windows (GT [S1:209-216]; one vendor background [S2], D); one LCD or six, inches: U. Tiles: 64x64 JPEG, 90° CW [S2] (D); 60x60 smears edges [S3] (O). GT, calibration done [S1:250-262][S4]: tiles are drawn **1:1, not scaled**, top-left at x 20/124/228, y 28/131; windows show ~76x77 px (x 13-88/120-198/228-306, y 20-97/130-206), a 0-14 px boot-image ring per tile. No official coordinates; ajazz-sdk's 84 px template boxes fit these windows [S5] (I).

**Q2.** App: "Replace the boot logo (Resolution W*H)"; wrong resolution fails; no size rule; N3 label U [S6] (D); its connect adds `QUCMD 1f110011001100` [S14] (O). SDK wire: `CRT\0\0LOG` + u32be length + `01`, 240x320 JPEG (CW) in 1024-byte reports, one unchecked reply wait (3 s), STP; ROM [S7][S8] (D). SDK pre-LOG: DIS, `CLE 000000FF`, no tiles [S9] (D). Why tiles first: U (maybe a host draw ends a logo mode; I [S10]). Cap: none in the C API (D); firmware U. GT: 1.8-22.3 KB accepted, ACK ~12 ms/KB, up to four LOGs per power cycle [S1:289-293].

**Q3.** Frames follow report ID `00`, zero-padded to 1024 [S7] (D):
- BGPIC (`transport_set_background_frame_stream`): `CRT\0\0BGPIC`, u32be JPEG length, u16be **x, y, w, h**, `00`, layer, then JPEG chunks; no STP or read.
- BGCLE (`transport_clear_background_frame_stream`): `CRT\0\0BGCLE` + byte, default `03` = all [S11].
- SETLB (`transport_set_led_color`: `CRT\0\0SETLB` + RGB×count) and MOD (`transport_change_mode`: `CRT\0\0MOD\0\0` + 0x31+mode, N1) never draw [S7][S12].

N3 classes disable frame streaming (`supportBackGroundGif=false`) and no SDK or N3/AKP03 driver sends BGPIC [S2] (D); N3 firmware support U. crusardri drops the `00` pad [S13]; identical at layer 0.

## 2. Implications

**(a) Burn:** power-up, reader + CONNECT every 10 s, handshake, six tiles + STP, LOG, wait for `ACK\0\0OK`, STP, repaint tiles [S1:291-293,324-330]. No ACK: no STP, power-cycle. v6 (15.9 KB) is in the proven range; above 22 KB, one step per power cycle; baseline JPEG, no metadata. At runtime only the rings show: boot art frames each key.

**(b) Runtime:** tiles 64x64, CW, BAT + STP, ≤10 KB [S10] (O); to centre art in its window, offset it x −1/+4/+8, y −1/+6 px inside the tile (as seen; I). Full 76x77 windows need BGPIC; LOG also works at runtime (MelvinTo [S14]) but writes flash and wipes tiles.

**(c) Next probe: BGPIC**, own power cycle, after v6 is confirmed. Recipe through tiles + STP, then report `00`, `CRT\0\0BGPIC`, `<u32be len>`, `000C 0012 0050 0050 00 00` (x 12, y 18, 80x80, layer 0), zero pad; an 80x80 baseline JPEG (asymmetric "F", magenta border), pre-rotated CW; STP; read 2 s. Upright on key 1: logical coordinates, works (tile hidden = drawn on top). Near key 4: native coordinates. Nothing: one BAT + STP; drawn = unsupported, ignored = wedged. Clean up: BGCLE `03` + STP, power cycle; unchanged boot image = RAM only.

## 3. Open risks
- No vendor class matches 5548:1001 [S2] (I); BGPIC may wedge the deck.
- A same-identity N3 wedged until reseated [S15] (O): heartbeat, one experiment per power cycle.
- U: LOG above 22 KB, flash wear; whether tiles or just delay unlock LOG [S1:226-228]; LOG byte 12 = `00`.

## Sources
S1 /Users/gemanor/Library/Application Support/Claude/scratch-workspaces/87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f/50b75cba-044a-4773-8b68-1ef7e8621cea/scratch-2026-10-06-95ecc8/after-tokens-launch/plans/token-deck/assets/device/NOTES.md
S2 /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/n3research/sdkpy/StreamDockN3.py:184-198; /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/n3research/sdk/streamdockN3V25.cpp:45-52,95,101; /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/n3research/sdkpy/GifController.py:88-90
S3 https://github.com/4ndv/opendeck-akp03/pull/37
S4 /Users/gemanor/Library/Application Support/Claude/scratch-workspaces/87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f/50b75cba-044a-4773-8b68-1ef7e8621cea/scratch-2026-10-06-95ecc8/after-tokens-launch/plans/token-deck/assets/device/panel_geometry.py
S5 /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/n3research/ajazz_sdk_testdata/bootlogo_layout.jpg
S6 https://mirabox.net/blogs/tutorial/how-to-replace-the-boot-logo-on-streamdock
S7 /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/n3research/libtransport_bin/full.asm: LOG 12861, BGPIC 13532, BGCLE 13863, SETLB 14017, MOD 14279; HEAD same: /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/so_head_x/head.asm
S8 https://github.com/MiraboxSpace/StreamDock-Device-SDK/blob/main/CPP-SDK/README.md#L300-L323
S9 /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/n3research/sdk/test.h:272-282
S10 https://github.com/superdeee/pyajazz/blob/main/README.md; https://github.com/bitfocus/companion-surface-mirabox-stream-dock/blob/main/src/streamdock.ts
S11 /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/n3research/sdk/TransportCWrapper.h:153-161
S12 /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/n3research/sdk/transport_c.h:128-141
S13 /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/n3research/crusardri/MiraboxN4Pro.py:115-117,153
S14 /private/tmp/claude-501/-Users-gemanor-Library-Application-Support-Claude-scratch-workspaces-87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f-50b75cba-044a-4773-8b68-1ef7e8621cea-scratch-2026-10-06-95ecc8/8f0606f4-503d-4ab8-a87b-e41cd8bb2294/scratchpad/n3research/melvin_n3.py:198-209,228-240
S15 https://github.com/MiraboxSpace/StreamDock-Device-SDK/issues/103; https://github.com/4ndv/opendeck-akp03/pull/45
