# Marketing's speaker cards: design references

Files Gabriel shared on Nov 1, 2026, made by Stigg marketing. They are the reference for the
After Tokens *event collateral* language (attendee cards, social videos). Note from Gabriel:
"logos are broken" in these files, so never copy a company logo from them; take logos from
`../at-launch/logos/` or the Luma speaker assets.

| File | What it is |
|---|---|
| `speakers-banner-1920-a.webp`, `-b.webp` | 1920x1080 speaker lineup banners, two background variants (big faint squares placed differently) |
| `speakers-banner-1280.webp` | 1280x720 version of the same banner |
| `speaker-card-matan-paul-shetrit.mp4` | 1080x1080 square speaker card **video**, H.264, 60 fps, 7.2 s, loopable |
| `_work/contact.png`, `_work/f-*.png` | contact sheet (every 0.6 s) and single frames pulled with ffmpeg |

## The still language (banner + video frame)

- Canvas: near-black (#0c0f0b to #131512) with a soft dark-green radial glow behind the portrait
  (towards #1b2a17). A faint grid of 1 px lines (about 4% white, roughly 64 px pitch at 1080) sits
  under everything. This is marketing's After Tokens look; the Stigg DS "no grid-paper" rule is
  about product/print work, and event collateral follows marketing here.
- Tokens: large translucent lime squares (~130 px at 1080, 6-10% opacity) sitting on the grid,
  plus a few small solid lime squares (8-24 px) scattered near the portrait. Always axis-aligned,
  on the grid, never rotated.
- Three lime crosshair "+" marks across the top (x ≈ 90, 540, 990 at 1080; y ≈ 90).
- Two or three dotted sine waves in lime across the lower third, dots ~4 px, different phases;
  they pass behind and in front of the portrait's shoulders.
- Portrait: black-and-white cut-out, right-aligned, bleeding off the bottom edge, with the green
  glow behind the head. In the lineup banner every portrait sits in a panel topped by a 1 px
  hairline that ends in a small lime square (top-right).
- Type: eyebrow `SPEAKER` in lime Söhne Mono uppercase (+0.03em); name in white Söhne Buch, two
  lines, ~96 px at 1080; title in Söhne Mono white; a short lime rule (60 px); company logo in
  white. Everything left-aligned on a 60 px margin.
- Bottom band (from y ≈ 850 at 1080): 1 px hairline, the After Tokens lockup with the pixel
  explosion, `NOVEMBER 10, 2026 • SAN FRANCISCO` in lime Söhne Mono (lime bullet), a vertical
  hairline, then `by` + the Stigg logo (gradient mark + white wordmark) on the right.

## The motion language (video)

- Everything in the layout is static: no camera move, no text animation, no portrait motion.
- A soft horizontal lime "scan line" (a ~6 px bright core with a ~40 px glow, ~35% opacity)
  sweeps from the top of the frame to the bottom in about 5 s, then restarts. It passes over
  the portrait and text.
- Token squares fade in and out and drift very slowly; the small bright ones twinkle.
- The dotted waves undulate slowly (phase drift), as if breathing.
- The lockup's explosion pixels twinkle a little.
- Loop length 7.2 s; the first and last frames match closely enough to loop.

## How to use these

For attendee cards: keep the grid, the glow, the big faint squares, the crosshairs, the waves,
the bottom band, and the scan-line sweep. Replace the eyebrow with the attendee copy, drop title
and company logo, and keep the text light. The speaker cards in `../../speaker-cards-clean/`
(1:1) and `../../speaker-cards/` (4:5) show the older, token-dissolve portrait treatment; both
treatments are on brand.
