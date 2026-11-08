# Welcome screen v8: design brief (Nov 2, 2026)

The Token Deck is a Stigg giveaway for the After Tokens event: a Mirabox Stream Dock N3 (six 64 x 64 LCD keys
behind clear domed keycaps). The welcome screen is one 320 x 240 JPEG burned into the deck's boot slot. It
shows at power-on, and while the Token Deck app runs it stays visible around the app's key tiles. Gabriel
(Stigg, the client) photographs every version on his deck and gives notes. v7 is on the deck now.

Work in `after-tokens-launch/_source/n3-probe/welcome/` (below: `welcome/`).

## Gabriel's notes on v7 (verbatim, with his photo `photos/welcome-v7-on-deck.webp`)

1. "Why no tokens in the tile where the URL is? It might be complimentary" (complementary)
2. "Why is there that big gap in the tiles between the tokens and the tile boundaries"
3. "I think we better do the URL on bottom left and slogan in bottom right"

Earlier directions that still hold: after v2, "top-left logo, bottom-right slogan, mostly tokens explode
pattern, and the URL somewhere with tokens in it"; on v1, the alignment was off (content centred in the tile
rects, which sit off-centre in the windows); on v6, bring back v1's white tokens and its dim "background"
tokens, make the tokens a little smaller like the stigg.io hero's particles, make the text slightly larger.
He wants it perfect, centred on what each window shows, no hand-waving. v6 (`welcome-v6-320x240.png`) had lit
tokens above the URL; v7 (`welcome-320x240.png`, `welcome_v7.py`) had none there, which is note 1.

## What his v7 photo shows

The dim #2C2F2B board tokens read clearly (brighter than `v7_common.lcd()` predicts), lime reads lime, white
reads white, the 10.5 px text is legible. Each 48 px board sits in a window that shows about 73-78 px, so
13-16 px of empty window on every side: note 2. The clear keycap's bevel reflects tokens near the window
edge (a column of reflected dots in key 3's left bevel).

## Decided (not open; reasons in `v8_common.py`)

- Layout: key 1 the logo, alone, as in v7 (60 x 17 at (20, 50)); key 4 the URL `io.stigg.io` / `/usage` WITH
  tokens; key 6 the slogan `The AI Usage` / `Management` / `Console`; the explosion art in keys 2, 3 and 5.
  Text strings and line breaks do not change.
- Boards: `v8_common.BOARDS`, each key fitted on its own and centred on its window within 1.5 px:
  key 2 12 x 13 (x 130-187, y 28-90), key 3 11 x 13 (x 239-291, y 28-90), key 4 12 x 11 (x 21-78, y 141-193),
  key 5 12 x 11 (x 130-187, y 141-193). That is as large as a centred board can get: the firmware's tile
  hugs the left edge of the right-column windows and sits high in the bottom-row windows, and nothing may be
  drawn outside the tiles. You may use 12 rows in keys 2 and 3 instead of 13 if your composition needs it;
  say why.
- Tokens: 3 px squares on a 5 px pitch; every board cell is an unlit #2C2F2B token unless lit. Lit: lime
  #92E759 and white #FFFFFF, a few #639840 depth tokens allowed. No other colours, no gradients, no blur.
- Type: Soehne Buch only, through `v8_common.text` (v7's pipeline: sub-pixel x, gamma 1.5, crisp periods and
  i-dots). The URL may stay 10.5 px / 13 px leading. The slogan in key 6 can be at most 9.5 px / 12 px:
  'Management' and 'The AI Usage' ink 57 px at 9.5 px and 62 px at 10.5 px, and key 6 holds 58 px (x
  234-291); a block centred on window 6 could be only 50 px wide. Every size from 9.5 to 10.49 px renders the
  same cap height (7 px) and x-height (5 px), so 9.5 px loses nothing to the bigger sizes but width.
- Hard rules, all checked by `v8_common.render` (`hard_rules_pass` must be true): all content inside the six
  tile rects; nothing within 6 px of a window edge; no pixel darker than #131512; on the q97 JPEG as burned,
  no window pixel outside the tiles more than 4 luma levels off #131512 and no channel more than 10 off; JPEG
  at most 22,300 bytes. Cells in `v8_common.quiet(key)` stay unlit (they share a JPEG block with the tile
  edge). Text near a tile edge rings too: check the halo numbers.

## Open (your design job)

- Key 4: how the URL and the tokens live together so they complement each other and the URL stays easy to
  read at arm's length (clearing, knockout, band, landed debris, source block, ...). Where the URL sits
  (flush on the logo's x = 20, centred on window 4, ...).
- The burst across the new layout: where the source block is, which way the debris flows, how keys 2, 3, 4
  and 5 relate. v7's flow (source in key 5, rising through key 2, landing in key 3 "toward the URL") pointed
  at key 6, which is now the slogan.
- Key 6: the slogan's alignment (flush left at x 234 is 3.5-4.5 px left of centre; flush right on x 291
  puts the visual mass near the centre; centred lines; ...) and its exact position.
- Type consistency: URL 10.5 px with the slogan at 9.5 px, or both 9.5 px.
- How many lit tokens per key, the lime / white balance, and the seed.

## Art rules (from v7; adapt to per-key boards, all must hold)

No 3 marks in a straight row or column; no diagonal staircase of 3; no 4 bright tokens within 7 cells of one
row or column (beyond the source's near field); no 3 x 3 window with more than 4 bright tokens; no lit
board corner; at most 2 marks on a board's outer row or column; at most 3 marks in any row or column; at
least a third lime among each key's flying tokens; overall white share of bright tokens 0.34-0.44 unless your
design argues otherwise; the source block keeps a crisp edge (debris only breaks off where the burst goes,
no ledges extending a source row or column); beyond the debris, tokens touch only at corners; no stray far
from the field. Keep lit tokens off the board's outermost ring on sides that face a window edge closely (the
bevel reflects them).

## Deliverables (in `welcome/v8/<your-id>/` only)

- `make.py`: own code, imports `v8_common` (and `welcome_v7` / `v7_common` if useful; do not edit them),
  renders into its own folder with `v8_common.render(img, HERE, extra={...})`, prints the checks, exits
  non-zero if `hard_rules_pass` is false or an art rule fails. Run it.
- `design.md`: at most 300 words: the idea, every number that matters (positions, sizes, counts, offsets
  from window centres), and what you traded away.
- Look at your own `preview-lcd-3x.png`, `preview-face-3x.png` and `preview-runtime-3x.png` before you finish,
  and compare with the v7 photo.

## Never

Never touch the deck: do not import hid, never run `burn_logo.py`, `replug_write.py`, `paint_tiles.py` or
anything that opens a USB device. No network. Write nothing outside your folder. No fonts other than Soehne
Buch. Do not change the URL or slogan text.
