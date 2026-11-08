# Token Deck box: design brief

This is the single source of truth for everyone working on the box. Read all of it before you draw anything.

`BOX` = `/Users/gemanor/Library/Application Support/Claude/scratch-workspaces/87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f/50b75cba-044a-4773-8b68-1ef7e8621cea/scratch-2026-10-06-95ecc8/after-tokens-launch/box`. Paths below are relative to it unless absolute.

## 1. What this is

Stigg is giving every After Tokens attendee a swag device. After Tokens is Stigg's conference on the AI economy (Tue Nov 10, 2026, Terra, San Francisco). The device is a MiraBox N3 console with the Stigg logo on its face, and it is called **Token Deck**. It controls coding agents (Claude Code, Cursor, Codex, OpenCode, Amp, Devin) from the desk. This brief covers the printed mailer box it ships in.

Audience: engineers (engineering directors, billing and pricing engineers, AI builders). They expect craft.

The client, Gabriel, gave this direction in his own words:
- "very clean lines. Somewhere between Apple to fancy gaming stuff."
- "There should be a 100% match with the Stigg and After Tokens brand."
- "we shouldn't show the device picture itself on the box, it's very anti-pattern for clean design. We should show silhouettes."
- Colors: "black background, and except of the button screen in the demo only white, silver/grey, and Stigg's Pantone green 7487C".
- Printing: "We can't have foil, we need to use pure Pantone/CMYK".
- Third parties: real agent and model names are OK as text (models without version numbers). Agents appear as one-color glyphs of their **real logos** (Gabriel, Oct 28: "why not use glyphs of the real logo?").

## 2. Panel content (Gabriel's layout, final)

| Panel | Content |
|---|---|
| **Top (lid)** | "Token Deck", in the same design language as the After Tokens logo (pixel-token lockup). Nothing else. **Gabriel's feedback (Oct 28):** he likes lockup D (stacked, pixel "Token" over white "Deck") "because the word Token is literally tokens", but is "not sure it will look nice in the center of the lid" — so either D in a better layout composition, or lockup A (inline, centered) as the fallback. Explore stronger compositions for D (for example anchored to the lower-left or upper-left on the panel grid with intentional negative space, the explosion flying toward the open area, sized with confidence), and A centered; show them on folded mockups and recommend one. |
| **Front wall** | The slogan "The AI Usage Management Console". |
| **Left wall** | The After Tokens logo in the middle. The date and location go in the top-right corner, which is the corner nearest the front: "Nov 10, 2026" and "Terra, San Francisco". |
| **Right wall** | The Stigg logo in silver with Stigg's tagline "Infrastructure for the AI Economy". |
| **Back wall** | "Just the exploding tokens": the After Tokens token-explosion motif as the only graphic. |
| **Bottom** | The demonstrations. One large demo of Mode 3 "Models & Usage", spec-like: every screen, knob and button with short descriptions. Below it, three small demos: Mode 1 "Agents", Mode 2 "Sessions", and a "Program it yourself" window. The small demos are sketch graphics with no text inside, each with a short description under it. |

"Left" and "right" are as seen by someone facing the front wall.

## 3. The dieline (printer's file `_source/dieline-293.pdf`, converted to `_source/dieline.svg` and `_source/dieline.json`)

- Mailer box, inner size 165 × 123 × 65 mm. The page is 474.585 × 495.988 mm.
- Coordinates are in mm on the flat sheet: origin top-left, y down, viewed from the printed (outside) side.
- Layers: `/MC0` 压痕 = creases (fold lines), `/MC1` 齿刀 = cut lines, `/MC2` = dimension notes. The dimension notes never print.

Visible panels and where they sit on the flat sheet (crease to crease, in mm):

| Panel | Flat-sheet rect (x0, y0, x1, y1) | Visible size W × H (art upright) | Rotation to apply when placing upright art |
|---|---|---|---|
| Lid (top face) | 157.57, 272.29, 313.57, 396.79 | 156.0 × 124.5 | 0°. The art's top edge is toward the hinge, which is the back. |
| Bottom (base) | 153.07, 84.29, 318.07, 207.29 | 165.0 × 123.0 | 0°. The art's top edge is toward the front wall. It reads upright when the box is flipped end over end. |
| Front wall | 156.57, 20.29, 314.57, 84.29 | 158.0 × 64.0 | 0° |
| Back wall | 154.57, 207.29, 316.57, 272.29 | 162.0 × 65.0 | 180° |
| Left wall (outer) | 88.07, 84.29, 153.07, 207.29 | 123.0 × 65.0 | −90° (the art's top points to sheet −x) |
| Right wall (outer) | 318.07, 84.29, 383.07, 207.29 | 123.0 × 65.0 | +90° (the art's top points to sheet +x) |

The rest of the sheet is hidden or inside the box: inner side walls, dust flaps, lid ears and the front tuck flap. It is still flooded black.

Hazards. Keep every element at least **5 mm clear** of each:
- Front wall: lock slot, x 218.7–252.4, y 81.2–84.3. That is the bottom-center of the front wall.
- Bottom: thumb notch cut, x 229.7–241.5, y 84.3–89.9. That is the top-center of the bottom.
- Bottom: side lock slots, x 153.1–157.1 and 314.1–318.1, y 125.8–165.8.
- All creases and cut edges. Use a **5 mm safe margin** inside every visible panel.

Bleed: the black flood covers the whole page, so panels need no bleed of their own. Composition draws the flood first.

## 4. Color system — strict (UPDATED Oct 28 to Stigg's official design system)

> **Update:** Gabriel shared Stigg's official brand package (`_source/stigg-brand/plugins/stigg-design/skills/stigg-ds-master/`, rules in its `SKILL.md` and `references/brand.md`). It governs. Changes vs the first version of this brief: the canvas is the brand near-black `#131512` (never `#000`), greys come from Stigg's neutral ramp, every line is 0.75 pt, mono labels track +0.03em, screen status colors use the brand status set, and the Stigg logo comes from the official mono SVG. If something you made earlier uses the old values, convert it.

Outside the LCD screen images, only these values may appear (enforced by `tools/palette_check.py`):

| Role | Preview hex (use exactly in SVG) | Press output |
|---|---|---|
| Canvas / background flood (the brand's "black") | `#131512` | rich black C60 M45 Y55 K100 (set in the press tool) |
| White (primary text, marks) | `#ffffff` | knockout (paper white) |
| Brand lime | `#92e759` | Spot **PANTONE 7487 C** 100% |
| Silver (Stigg logo only) | `#a9acaf` | Spot **PANTONE 877 C** (metallic silver ink) 100% |
| Grey n300 | `#c4c7c3` | K 25 |
| Grey n400 (secondary text) | `#9ea19d` | K 42 |
| Grey n500 (tertiary text, labels) | `#838682` | K 55 |
| Grey n600 | `#5b5d59` | K 73 |
| Grey n700 (default hairline) | `#3c3e3a` | K 85 |
| Grey n800 (subtle hairline) | `#2c2f2b` | K 90 |

Rules:
- Never `#000000` (use `#131512` for anything "black", including occluding fills inside silhouettes). No other colors, no gradients, no opacity < 1, no blur/glow. Lime at 100%, never tinted.
- **Lime is a scalpel** (Stigg: about 5% of a composition, the signal: active state, eyebrows, one accent). The After Tokens marks are the exception where lime carries the mark (the pixel lockups and the token explosion); keep the explosion airy and consider mixing white squares in, like the stigg.io particle field (about 60% lime / 40% white points).
- Avoid large dark-grey fills (they barely separate from the rich-black flood in print); group with hairlines instead ("a 1px line is preferred over a filled card").
- **LCD screen exception:** only inside a `<g data-screen="1">` group (a device screen's pixels) may other colors appear. Screens are the one "live", colorful thing on the box — make them look like real UI on a tiny LCD, using Stigg's status set: success/active lime `#92e759`, working/info blue `#7da2ff`, needs approval/warning coral `#ff8e6d`, limit/danger red `#ea384c`, mint `#6bf8c2` (series), neutral `#838682`; screen glass `#0b0c0a` or `#131512`; text white/greys from the ramp.

## 5. Typography (Stigg Design System: Söhne, one weight per cut)

Fonts: Stigg's brand package, `_source/stigg-brand/plugins/stigg-design/skills/stigg-ds-master/assets/fonts/` — `.otf` desktop files (use these for print outlines) and identical `.woff2` web files (the copies in `../_source/at-launch/assets/fonts/` are byte-identical). Font license: internal Stigg use; never ship the font files to anyone — the press file outlines all text. Use exactly these SVG family names:
- `Soehne Buch` — headings, names, UI text, buttons.
- `Soehne Leicht` — descriptions, captions, longer copy.
- `Soehne Mono Buch` — labels, eyebrows, numbers, table heads. `Soehne Mono Leicht` only if really needed.
- **Never bold, never italic, never faux styles.** Hierarchy comes from size, color (white vs greys) and Buch/Leicht contrast.
- **Mono labels are UPPERCASE with +0.03em tracking.** The Stigg **eyebrow** = lime Mono uppercase label with a small square bullet before it (like "■ USAGE STARTS HERE" on the device sticker).
- Copy is **sentence case** (headings included); labels may be uppercase mono by style. "Stigg", never "STIGG"/"stigg" in text.

Units: every SVG uses a **millimetre viewBox**. 1 pt = 0.3528 mm → 6 pt = 2.117 mm, 7 pt = 2.469 mm, 8 pt = 2.822 mm, 10 pt = 3.528 mm, 12 pt = 4.233 mm.
Minimums for reversed (light-on-black) print: text ≥ 6 pt in Buch/Mono Buch, ≥ 7 pt in Leicht (screen micro-labels inside data-screen groups may go to 5 pt in Mono Buch); squares ≥ 0.6 mm.
Tracking: After Tokens wordmark −0.073em (as in pixelmark.js); display type about −0.01em to −0.02em; mono labels +0.03em.

## 6. Brand rules (After Tokens + Stigg)

Stigg Design System rules (from the official package — they apply to every face):
- **The hairline rule: every line is exactly 0.75 pt = 0.265 mm at final printed size, everywhere, no exceptions** — outlines, leaders, rules, rings, ticks, icons. Never thicker "for emphasis", never thinner. Emphasize with color, a small dot, a dash pattern or a fill. Inside a scaled group, set stroke-width = 0.265 / scale so it prints at 0.265 mm (`palette_check.py` checks the effective width). Patterns: solid; dashed 1.06 mm / 0.79 mm; dotted = round-cap dots every 1.6 mm. A dashed lime line marks the "focus / our answer" element.
- Radii (scaled to print): 0.5 mm chips · 1 mm small controls · 2 mm cards/tiles · 4 mm outer frames. Round only for dots, knobs, buttons.
- No grid-paper or dot-grid backgrounds behind content. Structure comes from real hairlines. Stigg's print/one-pager signature is a **registration frame**: hairlines inset from the edges that run edge to edge and cross at the corners (worth considering for the bottom "spec sheet").
- Depth from hairlines and surface steps, never shadows. Generous negative space; "when in doubt, remove a box, not add one". Left-aligned text by default; centered only for short hero statements.
- Voice: clear over clever, confident not hype, technical nouns, short.

- **The After Tokens logo:** "After" is white Söhne Buch. "Tokens" is built from lime `#92e759` squares sampled on a strict grid from the same text, and the "ns" breaks apart into an explosion of squares blowing right, up and down.
  - The reference implementation is `/Users/gemanor/Library/Application Support/Claude/scratch-workspaces/87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f/50b75cba-044a-4773-8b68-1ef7e8621cea/scratch-2026-10-06-95ecc8/after-tokens-launch/_source/at-launch/pixelmark/pixelmark.js`, a canvas implementation. The approved use, on the Luma banner, is `PixelMark.draw(canvas, {cap: 84, layout: 'inline', rows: 22, seed: 11, reachX: 0.6, reachUp: 0.45, reachDown: 0.45, spray: 1.1})`.
  - A rendered reference is in `/Users/gemanor/Library/Application Support/Claude/scratch-workspaces/87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f/50b75cba-044a-4773-8b68-1ef7e8621cea/scratch-2026-10-06-95ecc8/after-tokens-launch/luma/after-tokens-luma-speakers.png`, top-left header, about 760 × 170 px.
  - The stacked logo is `/Users/gemanor/Library/Application Support/Claude/scratch-workspaces/87e2a23b-6eb1-4ed2-8f16-42d28c93ad7f/50b75cba-044a-4773-8b68-1ef7e8621cea/scratch-2026-10-06-95ecc8/after-tokens-launch/after-tokens-wordmark.png`, where "After" is white on transparent.
- **The token grid:** tokens always sit on a strict grid, with even pitch and square size. Never use random, jittered or overlapping squares. An earlier attempt with loose dots was rejected as "looks broken". Explosion squares snap to the same grid as the letters, one square per cell (`snap: true` in pixelmark.js).
- **Stigg logo:** use the official single-color file `assets/stigg-logo-mono.svg` (from the brand package; `currentColor`) colored silver `#a9acaf` — mark and wordmark both silver, no gradient (the gradient version is for screens only). Never rebuild, retype, recolor to lime, stretch, outline or add effects. Clear space ≥ the mark's height on all sides.
- **Look and feel:** precise, quiet, engineered. Use thin rules, mono uppercase micro-labels, generous black space and exact alignment on a grid. The gaming edge comes from the lit LCD screens and the lime tokens, not from glows, bevels, angles or gradients. The device never appears as a photo or a realistic render: only clean line silhouettes, with no shading.
- **Copy voice:** plain and specific, with no hype words, emoji or exclamation marks.

## 7. The device (for silhouettes)

The MiraBox N3 face is 129 × 78 mm in landscape. It has rounded corners (r ≈ 4 mm), a USB-C port on the back, and a body depth of about 25 mm. Face layout, measured from Gabriel's photo (x from the left edge, y from the top edge, in mm, ±1):
- **6 LCD screen buttons** in 3 columns × 2 rows, each about 16 × 15.5 mm. Their left edges are at x ≈ 14.7, 33.7, 52.2 and their top edges at y ≈ 12.2, 30.7. Each sits in a thin dark bezel.
- **3 metal buttons**, round, about 12.9 mm across, in a row under the screens. Their centers are at x ≈ 22.7, 41.5, 60.3 (aligned to the screen columns), y ≈ 62.9.
- **Main knob**, large: center (96.1, 26.7), about 29.3 mm across, with radial machined texture.
- **Left knob and right knob**, small: centers (85.0, 59.1) and (110.6, 59.1), about 15.2 mm across.
- **Stigg logo** on the face, top right: x ≈ 100–122, y ≈ 4–10.

Names in the product spec: the 3 metal buttons select the mode (Left = Agents, Middle = Sessions, Right = Models & Usage); the main knob, the left knob and the right knob; the 6 LCD buttons. Knob clicks give additional actions.

## 8. The three modes (from Gabriel's spec, "Coding Agent Control Deck v0.1")

The three metal buttons always select the same modes. Switching modes never interrupts active agents. All modes share one "selected session".

**Mode 1, Agents (left metal button).** Open coding tools, switch between their windows, adjust the current model.
- LCD screens are fixed: top row Claude Code, Cursor, Codex; bottom row OpenCode, Amp, Devin. Each shows the agent's glyph and a small activity indicator. Pressing one focuses that agent's latest window, or launches the app.
- Main knob: turn to cycle open coding-agent windows; click to go back to the previous window.
- Left knob: turn to change the model in the active session; click to restore the default.
- Right knob: turn to change reasoning effort; click to restore the default.

**Mode 2, Sessions (middle metal button).** Monitor every agent session and open the ones that need attention.
- Each LCD screen is one session and shows four things: the agent glyph, a colored status indicator (Working, Needs approval, Needs input, Idle, Completed, Disconnected), a **circular ring of context-window usage**, and a task title of up to 3 words (e.g. "Fix login bug").
- "Needs approval" must look different from "Completed". Pressing a session opens it; pressing one that needs approval opens its approval prompt but never approves it.
- Main knob: browse older and newer sessions, six at a time; click to jump to the next one that needs attention.
- Left knob: filter by agent. Right knob: filter by status.

**Mode 3, Models & Usage (right metal button). This is the large demo.** Select models, monitor limits, change the selected session's settings.
- Each LCD screen is a model available to the selected coding agent (up to 6 favorites). Each shows the **model name**, a **short-window usage bar**, a **long-window usage bar**, and **whether it is the current model**.
- Time labels use the real windows the provider reports, for example "5H" and "7D", never "hourly". Models that share one quota must show that they use a **shared pool**.
- Pressing a model sets it as the selected session's model.
- **Main knob:** turn to change **reasoning effort**: Low, Medium, High, Extra High, Max (only the levels the model supports). Click to toggle **Ultracode** (Claude Code), which is separate from effort.
- **Left knob:** turn to switch the selected coding agent; click to return to the agent of the last selected session.
- **Right knob:** turn to preview a **permission level**: Read-only, Ask, Auto, Full. Click to apply. Full needs confirmation on the computer; the deck never bypasses security prompts.
- Temporary feedback: turning a knob shows a short overlay such as "HIGH EFFORT" for 5 seconds.

Content for the large demo (UPDATED Oct 28 after Gabriel's feedback; use exactly this):
- **No version numbers on model names** (Gabriel: versions make it "a little too much of a vendor lookup").
- **Selected agent: OpenCode** (it runs models from several providers, so a mixed model list is truthful).
- **Screens, left to right then top to bottom:** "Opus" (current model, highlighted), "Sonnet", "Haiku", "Fable", "Astra", "Grok".
- **Usage, by provider pool** (the spec: shared quotas must show they are a shared pool; never present a quota as model-specific unless it is):
  - Opus, Sonnet, Haiku and Fable share one pool: 5H at 62% and 7D at 41%, marked shared.
  - Astra has its own pool: 5H at 24% and 7D at 58%.
  - Grok has its own pool: 5H at 9% and 7D at 17%.
- **Main knob effort scale:** LOW · MED · HIGH · XHIGH · MAX with HIGH active. Ultracode is OFF (a Claude Code feature, toggled by pressing the main knob where supported).
- **Right knob permission scale:** READ · ASK · AUTO · FULL with ASK active. The left knob shows the agent: OPENCODE.
- **Agent glyphs** (Mode 1 and Mode 2 screens): Gabriel now wants **glyphs of the real logos** — simplified, one-color (white on the LCD) versions of the real Claude Code, Cursor, Codex, OpenCode, Amp and Devin marks, taken from official sources (`assets/logos-3p/`), not invented shapes.

**Program it yourself** (small demo 3). A desktop window, sketch only, showing that you can build your own modes and map screens, buttons and knobs. Suggested sketch: a minimal editor window (3 traffic-light dots, a sidebar, code as abstract bars with a few lime accents) beside or overlapping a tiny device outline.

Small-demo captions: title plus one line each, in Gabriel's voice: short, plain, engineer-to-engineer. Starting points to refine:
- "Agents": "Six coding agents, one press away. Turn the dial to hop between their windows."
- "Sessions": "Every session, its status and its context. See which one needs you."
- "Program it yourself": "Write your own modes for any screen, button or knob."

## 9. SVG authoring rules

Every file must follow these rules, because the press tool parses them.

- One `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H">` in **mm**. No width or height attributes are needed.
- Allowed elements:
  - `g` with `transform` (`translate`, `rotate`, `scale` or `matrix`);
  - `rect` (with x, y, width, height, rx, ry);
  - `circle`, `ellipse`, `line`, `polyline` and `polygon`;
  - `path`, using absolute or relative M, L, H, V, C, S, Q, T, A and Z;
  - `text`, with `x`, `y`, `font-family`, `font-size`, `letter-spacing` (user units), `text-anchor` (start, middle or end) and `fill`. Text is one line, with no `tspan` and no `textPath`.
- Allowed attributes: `fill`, `stroke`, `stroke-width`, `stroke-linecap`, `stroke-linejoin`, `stroke-dasharray`, `fill-rule`, `data-screen`, `id` and `class`.
- **Not allowed:** CSS `<style>`, gradients, patterns, filters, masks, clip paths, `<use>`, images, opacity or fill-opacity below 1, and `transform` on `<text>` other than plain translate or rotate on a parent `<g>`.
- Colors come only from the palette in section 4, written as lowercase hex, except inside `data-screen` groups.
- Panel art is upright, as a viewer standing in front of that face would read it, with a transparent background. Composition adds the black flood and rotates each panel into place.
- Rendering cannot use kerning or ligatures. The render tool turns them off, so design with that look.

## 10. Tools and files

- `node tools/render.mjs <in.svg> <out.png> [px_per_mm=12]` renders an SVG on black with the Söhne fonts loaded. Use it to look at your work. Zoom in on crops too: view the PNG and crop details with Python/PIL.
- `python3 tools/palette_check.py <file.svg>` lists any color outside the palette, outside screen groups.
- Assets go in `assets/`, panels in `panels/`, build outputs in `build/`.
- Playwright: `/Users/gemanor/.npm/_npx/e41f203b7505f1fb/node_modules/playwright-core/index.mjs`. Headless Chrome: `~/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell`.

## 11. Quality bar

Hold the work to the standard of a premium hardware package (Apple, Teenage Engineering, Nothing) made for the After Tokens brand.
- Every element sits on a grid.
- Spacing is consistent: multiples of 1 mm, with 2, 3, 4, 6 and 8 mm as the main steps.
- No element is cramped against a margin or crease.
- Line weights are consistent: one hairline weight and one emphasis weight.
- Labels are aligned and readable at arm's length.

Look at every render at 100% and in zoomed crops before calling anything done.
