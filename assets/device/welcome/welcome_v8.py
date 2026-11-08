"""Token Deck welcome screen v8 (the image burned into the deck's boot slot), own code.

v8 answers Gabriel's notes on v7 as burned (Nov 2, photos/welcome-v7-on-deck.webp): "Why no tokens in the
tile where the URL is? It might be complementary", "Why is there that big gap in the tiles between the
tokens and the tile boundaries", "I think we better do the URL on bottom left and slogan in bottom right".
Four designs (v8/a-d) went to four critics (typography, composition, brand, device; v8/BRIEF.md, the
comparison sheets in v8/). Three picked c (v7's burst, a calm board around the URL); composition picked d
(type set into the field). This is c with every critic's must-fix and the grafts they agreed on.

Layout key 1 logo     | key 2 the plume  | key 3 the dust
       key 4 URL      | key 5 the source | key 6 slogan
       Logo top left, URL under it bottom left (both flush on the left of the composition), slogan bottom
       right: Gabriel's layout since v2 ("top-left logo, bottom-right slogan ... the URL somewhere with
       tokens in it"). The burst stays v7's, the one he has seen on the deck: a crisp lime block breaks at
       its top right and the debris rises up and to the right, the way 'Tokens' scatters in the After
       Tokens wordmark. The bottom row reads URL, burst, slogan.
Boards Each token key shows the largest board of 3 px tokens on a 5 px pitch that stays inside its tile
       and is centred on its window to 1.5 px (v8_common.BOARDS: key 2 12 x 13 at x 130-187 / y 28-90,
       key 3 11 x 13 at x 239-291 / y 28-90, key 4 12 x 11 at x 21-78 / y 141-193, key 5 12 x 11 at
       x 130-187 / y 141-193). v7 used one 10 x 10 board (48 px) everywhere, so 13-16 px of every window
       stood empty around it (note 2); now 6-12 px do, and 14 px on key 3's right, where the firmware's
       tile ends (nothing may be drawn outside the tiles: the burned image stays on screen around the
       app's tiles). Each key has its own lattice phase; the bezels hide 32-40 px between keys.
       Every cell is an unlit #2C2F2B token unless lit. In the v7 photo the unlit tokens read at about a
       third of the way to white, so the boards themselves carry the "field".
Key 4  The URL sits on its board in a clean window: no token comes closer than 4 px beside the type or
       7 px above the i-dots and below the descenders (the dome adds a ~1 px ghost under every stroke),
       and inner tokens keep 10 px after the end of a line so they never read as more characters. The
       window follows the rag: after the short '/usage' the field steps in again (3 cells), so the board
       reads as a field the URL is set into, not a dotted box. Three lime tokens have landed on it, two on
       the floor under '/usage' and one above, leaning right where the flush-left block is light:
       complementary, on their own random stream, not part of the burst. No white token in key 4: there
       white is the type.
Type   Soehne Buch, white, tracking -0.06 px, v7's pipeline (sub-pixel x, gamma 1.5, the '/u' kern dropped).
       URL 10.5 px / 13 px leading, flush left, centred on window 4: 10.5 px is the first size with an 8 px
       cap and 6 px x-height (every size from 9.5 to 10.49 px renders 7 and 5), and the URL is the one
       all-lowercase string people read letter by letter. Slogan 9.5 px / 12 px, flush right on x 291:
       'Management' and 'The AI Usage' ink 57 px at 9.5 px and 62 px at 10.5 px, and key 6 holds 58 px
       (x 234-291, the tile ends at 291); a block centred on window 6 could be only 50 px wide. Flush right
       puts the slogan's visual mass 1 px from the window centre (flush left: 7 px), lines its edge up with
       key 3's board edge above it, and mirrors the flush-left URL: the bottom row's straight edges face
       the deck's sides. Both blocks centre on y 167.5. Cap top 152 (153 rings 5 luma levels past x 291).
       New against v7: single-stem glyphs ('i', 'I', 'l') are one crisp, fully lit column (no 33 % column
       beside the stem; under the panel's bloom those made 'io.stigg.io' read 'lo.stlgg.lo' in v6/v7 and
       touched the A of 'AI'); the i keeps its crisp dot on the cap-top row with an empty row under it; a
       period sits in the middle of the gap between its neighbours' ink (v7 put the second one against the
       g's anti-aliased edge, so 'stigg.io' could read 'stiggio').
Burst  v7's generator on the bigger boards: a solid lime source block (key 5, 4 x 6 cells with rounded
       corners, x 140-157 / y 161-188, at least 17 px from the window edges) erodes at its top and breaks
       off only at its top-right corner; the plume rises through the bezel into key 2, crosses it on a
       diagonal, bends right into key 3 and settles there as dust. The density is a designed field
       (near-field blast + a band along a curved spine + clusters at fixed points); the seed decides cells.
       Exact counts per key by weighted sampling without replacement; white leans to the far end, so the
       plume runs lime near the source and whiter further out; three #639840 depth tokens at the far end.
Rules  Enforced while placing and re-checked afterwards (art_checks): no 3 marks in a straight row or
       column; no diagonal staircase of 3; at most 2 marks in any 5 consecutive cells of a row or column
       beyond the near field; no 4 bright within 7 cells of a row or column; no 3 x 3 window with more than
       4 bright; at most 3 marks in any row or column; at least a third lime among each key's flying
       tokens; white 0.34-0.44 of all bright tokens; side-by-side pairs only inside the debris; no ledges;
       depth never on the source; no stray; nothing in the URL's window. Device rules (the v7 photo):
       no lit token on a board's outer ring or closer than 14 px to a window edge (the clear keycap's bevel
       mirrors what is near it; v7's nearest lit token was at 14 px); no lime or #639840 token in a 16 x 16
       JPEG chroma block that also holds window pixels outside the tiles (it tints them, and those pixels
       stay visible around the app's tiles); cells that share an 8 x 8 block with them stay unlit; the
       sides of key 2 and key 5 that face the logo and the slogan stay dark. Hard rules (v8_common.render):
       all content inside the six tile rects, nothing within 6 px of a window edge, nothing darker than
       #131512, on the JPEG as burned (q97, 4:2:0) no window pixel outside the tiles more than 4 luma
       levels or 10 levels in any channel off #131512, JPEG at most 22,300 bytes.

usage: welcome_v8.py                 render the final (seed SEED) into this folder
       welcome_v8.py --seed N --out DIR
       welcome_v8.py --search N      list seeds 1..N that pass every rule, best first
"""
import sys
sys.dont_write_bytecode = True
import argparse, itertools, json, math, os, random   # noqa: E402
from PIL import Image, ImageChops, ImageDraw, ImageFont   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v8_common as v8                              # noqa: E402

c = v8.c
w7 = v8.w7
W, H = v8.W, v8.H
INK, LIME, WHITE, UNLIT, MID_LIME = v8.INK, v8.LIME, v8.WHITE, v8.UNLIT, v8.MID_LIME
BRIGHT = (LIME, WHITE)
PITCH, SQ = v8.PITCH, v8.SQ
BOARDS = v8.BOARDS
ART = (5, 2, 3)                                     # the burst: source in 5, plume in 2, dust in 3
SEED = 7                                            # chosen by eye among the seeds 1-150 that pass every rule

# ---------------------------------------------------------------- type
URL = ["io.stigg.io", "/usage"]
SLOGAN = ["The AI Usage", "Management", "Console"]
TRACK, GAMMA = -0.06, 1.5
URL_SIZE, URL_LEAD = 10.5, 13
SLOGAN_SIZE, SLOGAN_LEAD = 9.5, 12
SLOGAN_RIGHT, SLOGAN_CAP = 291, 152                 # last ink column of every slogan line; cap top
INK_T = 64                                          # coverage (of 255) that counts as ink for stems and gaps
STEMS = "iIl"                                       # single-stem glyphs drawn as one crisp column

AIR_SIDE, AIR_V, AIR_END = 4, 7, 10                 # key 4: px of air beside, above / below, after a line end


def _font(size):
    return ImageFont.truetype(c.base.FONT, size)


def _glyph(f, ch, x, top):
    fx = math.floor(x); phi = x - fx
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).text((fx, top), ch, font=f, fill=255)
    if phi > 0.01:
        g = Image.blend(g, ImageChops.offset(g, 1, 0), phi)
    return g


def _crisp_stem(g):
    """A single-stem glyph as one fully lit column: the column with the most coverage, on every row where
    it is at least 40 % of its peak. Returns (mask, stem x)."""
    bb = g.getbbox()
    px = g.load()
    stem = max(range(bb[0], bb[2]), key=lambda x: sum(px[x, y] for y in range(bb[1], bb[3])))
    peak = max(px[stem, y] for y in range(bb[1], bb[3]))
    out = Image.new("L", (W, H), 0)
    for y in range(bb[1], bb[3]):
        if px[stem, y] >= 0.4 * peak:
            out.putpixel((stem, y), 255)
    return out, stem


def _ink_cols(g):
    px = g.load(); bb = g.getbbox()
    cols = [x for x in range(bb[0], bb[2]) if any(px[x, y] >= INK_T for y in range(bb[1], bb[3]))]
    return (min(cols), max(cols)) if cols else (bb[0], bb[2] - 1)


_LINES = {}


def line_mask(text, size):
    """One line drawn at pen x 100 and cap top 100 (whole-pixel pens make this exact under translation):
    coverage mask and ink box (exclusive right / bottom, any coverage)."""
    key = (text, size)
    if key not in _LINES:
        f = _font(size)
        asc, _ = f.getmetrics()
        cap_off = f.getbbox("H")[1]
        top = 100 - cap_off
        base_y = top + asc
        xs = [x + TRACK * j for j, x in enumerate(w7.v6.layout_line(f, text, 100.0))]
        cov = Image.new("L", (W, H), 0)
        spans, periods = [], []
        for j, (ch, x) in enumerate(zip(text, xs)):
            if ch == " ":
                continue
            if ch == ".":
                periods.append(j)
                continue
            if ch in STEMS:
                g, stem = _crisp_stem(_glyph(f, "ı" if ch == "i" else ch, round(x), top))
                if ch == "i":
                    g.putpixel((stem, 100), 255)                 # the dot on the cap-top row, a row of air under it
                spans.append((j, stem, stem))
            else:
                g = _glyph(f, ch, x, top)
                spans.append((j,) + _ink_cols(g))
            cov = ImageChops.lighter(cov, g)
        for j in periods:                                        # a period in the middle of its gap
            prev = [s for s in spans if s[0] < j]; nxt = [s for s in spans if s[0] > j]
            px = (prev[-1][2] + nxt[0][1] + 1) // 2 if prev and nxt else round(xs[j] + 0.51)
            cov.putpixel((px, base_y - 1), 255)
        _LINES[key] = (cov, cov.getbbox())
    return _LINES[key]


def set_type(lines, size, lead, x, cap_top, align):
    """Coverage mask of a block and each line's ink box (exclusive). align 'left': x is the first ink
    column of every line; 'right': x is the last ink column of every line."""
    cov = Image.new("L", (W, H), 0)
    boxes = []
    for n, t in enumerate(lines):
        m, (x0, y0, x1, y1) = line_mask(t, size)
        dx = x - x0 if align == "left" else x + 1 - x1
        dy = cap_top + n * lead - 100
        cov = ImageChops.lighter(cov, ImageChops.offset(m, dx, dy))
        boxes.append((x0 + dx, y0 + dy, x1 + dx, y1 + dy))
    return cov, boxes


def composite(img, cov):
    w7.v6.GAMMA = GAMMA
    w7.v6.composite_text(img, cov, WHITE)


def url_block():
    """The URL's mask and line boxes, its ink box centred on key 4's board (the board is centred on
    window 4 to 0.5 px), on whole pixels."""
    _, boxes = set_type(URL, URL_SIZE, URL_LEAD, 0, 100, "left")
    w = max(b[2] for b in boxes) - min(b[0] for b in boxes)
    h = boxes[-1][3] - boxes[0][1]
    bx0, by0, bx1, by1 = v8.board_px(4)
    left = int(math.floor((bx0 + bx1 + 1) / 2.0 - w / 2.0 + 0.5))
    top = int(math.floor((by0 + by1 + 1) / 2.0 - h / 2.0 + 0.5))
    return set_type(URL, URL_SIZE, URL_LEAD, left, top + (100 - boxes[0][1]), "left")


def slogan_block():
    return set_type(SLOGAN, SLOGAN_SIZE, SLOGAN_LEAD, SLOGAN_RIGHT, SLOGAN_CAP, "right")


# ---------------------------------------------------------------- cells: (key, a, b) on each key's own board
def key_cells(k):
    return [(k, a, b) for (a, b) in v8.board_cells(k)]


def cpx(cell):
    k, a, b = cell
    return v8.cell_px(k, a, b)


def centre(cell):
    x, y = cpx(cell)
    return x + SQ / 2.0, y + SQ / 2.0


def dims(k):
    return BOARDS[k][2], BOARDS[k][3]


def on_ring(cell):
    k, a, b = cell
    nc, nr = dims(k)
    return a in (0, nc - 1) or b in (0, nr - 1)


def is_corner(cell):
    k, a, b = cell
    nc, nr = dims(k)
    return a in (0, nc - 1) and b in (0, nr - 1)


QUIET, CHROMA = set(), set()
for _k in BOARDS:
    QUIET |= {(_k, a, b) for (a, b) in v8.quiet(_k)}                   # 8 x 8 luma blocks: never lit
    CHROMA |= {(_k, a, b) for (a, b) in v8.quiet(_k, n=16)}            # 16 x 16 chroma blocks: never lime / depth
CHROMA -= QUIET
EDGE_MIN = 14                                                          # px from a window edge to any lit token


def edge_distance(cell):
    k, a, b = cell
    x, y = cpx(cell)
    wx0, wy0, wx1, wy1 = v8.WINDOWS[k - 1]
    return min(x - wx0, wx1 - (x + SQ), y - wy0, wy1 - (y + SQ))


QUIET_SIDES = ({(2, a, b) for a in range(0, 4) for b in range(3, 9)}      # key 2's side toward the logo
               | {(5, a, b) for a in range(9, 12) for b in range(3, 10)})  # key 5's side toward the slogan


def lit_ok(cell, colour):
    """Device rules for one lit token, or the reason it may not be lit."""
    if cell in QUIET:
        return "quiet"
    if on_ring(cell):
        return "ring"
    if edge_distance(cell) < EDGE_MIN:
        return "near the window edge"
    if colour in (LIME, MID_LIME) and cell in CHROMA:
        return "chroma block"
    if cell in QUIET_SIDES:
        return "quiet side"
    return None


# ---------------------------------------------------------------- key 4: the URL's window in the field
def _ink_pixels(cov):
    px = cov.load()
    x0, y0, x1, y1 = cov.getbbox()
    return [(x, y) for y in range(y0, y1) for x in range(x0, x1) if px[x, y]]


def _gaps(cell, p):
    """Horizontal and vertical distance from a token's 3 x 3 square to an ink pixel (0 = overlapping)."""
    x, y = cpx(cell)
    return max(0, x - p[0], p[0] - (x + SQ - 1)), max(0, y - p[1], p[1] - (y + SQ - 1))


def too_close(cell, ink):
    """Why an unlit token here would crowd the URL: closer than AIR_SIDE px beside or AIR_V px above /
    below the ink, or (an inner cell) within AIR_END px after a line's end at the line's height."""
    inner = not on_ring(cell)
    x = cpx(cell)[0]
    for p in ink:
        dx, dy = _gaps(cell, p)
        if dx <= AIR_SIDE and dy <= AIR_V:
            return "air"
        if inner and p[0] < x and dx <= AIR_END and dy <= AIR_V:
            return "after a line"
    return None


def url_window(ink):
    return {cl for cl in key_cells(4) if too_close(cl, ink)}


# ---------------------------------------------------------------- the burst (v7's generator, per-key boards)
def catmull(points, n=400):
    """Dense polyline through the control points (Catmull-Rom), as in v7."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for s in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[s - 1], pts[s], pts[s + 1], pts[s + 2]
        for t in [k / n for k in range(n)]:
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[a]) + (-p0[a] + p2[a]) * t + (2 * p0[a] - 5 * p1[a] + 4 * p2[a] - p3[a]) * t2
                                    + (-p0[a] + 3 * p1[a] - 3 * p2[a] + p3[a]) * t3) for a in (0, 1)))
    out.append(points[-1])
    return out


def project(poly, cum, p):
    """Arc length s of the nearest spine point and the signed distance q from it."""
    best = (1e9, 0, 0.0)
    for k in range(len(poly) - 1):
        ax, ay = poly[k]; bx, by = poly[k + 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        qx, qy = p[0] - (ax + t * dx), p[1] - (ay + t * dy)
        d = math.hypot(qx, qy)
        if d < best[0]:
            side = 1.0 if (dx * qy - dy * qx) < 0 else -1.0
            best = (d, cum[k] + t * math.sqrt(L2), side * d)
    return best[1], best[2]


P = dict(
    # panel px, source to dust: up out of key 5, across key 2 on a diagonal, right into key 3, down to its floor
    spine=[(161, 160), (163, 122), (165, 78), (190, 50), (250, 50), (272, 64), (288, 80)],
    src=(2, 4, 4, 6),              # key 5 source block: a0, b0, cols, rows (x 140-157, y 161-188)
    erode=0.65,                    # pixelmark erosion of the source's right side and top ...
    erode_v=3.0, erode_vmin=0.5,   # ... in its top half only
    lam_n=13.0, up=58.0, aim=2.5,  # near field: blast from the source's top-right corner ...
    near_floor=0.02,               # ... with little off-axis spray
    fringe=0.35, fringe_fall=1.5,  # fragments against the source: strongest at its top-right corner
    band_w=(7.0, 0.07), soft=0.45, lam_f=170.0, band_lo=0.18,
    clusters=[(164, 74, 13, 6, 1.0),       # key 2: where the plume comes up through the bezel
              (177, 50, 11, 6, 0.85),      # key 2: where it bends right
              (256, 50, 12, 8, 0.8),       # key 3: where it arrives
              (272, 68, 12, 8, 0.6)],      # key 3: where it settles
    jitter=5.0,
    target={5: 11, 2: 17, 3: 14},  # bright flying tokens per key (v7 11 / 17 / 13); thins away from the source
    white={5: 4, 2: 10, 3: 9},     # white leans to the far end; at least a third of every key's flying tokens lime
    white_base=0.30, white_min_r=1.5,
    depth={3: 3}, depth_from=0.62,
    min_w=0.03,
    gap0=1.0, gap1=0.35,
)

L4 = dict(quota={9: 2, 1: 1},     # landed tokens per row of key 4: two on the floor (b9), one above (b1)
          gap=3.0,                 # min distance between them (cells): calm, never touching
          colgap=2,                # tokens on the two rows never share or neighbour a column
          cols={9: (3, 10), 1: (3, 10)},
          lean={9: 1.2, 1: 0.6},   # lean right, where the flush-left URL is light
          ink_air=7)               # px from a landed token to any URL ink pixel


def spine_poly(p=P):
    poly = catmull(p["spine"])
    cum = [0.0]
    for a, b in zip(poly, poly[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return poly, cum


def source_cells(p=P):
    a0, b0, nc, nr = p["src"]
    src = {(5, a, b) for a in range(a0, a0 + nc) for b in range(b0, b0 + nr)}
    for (a, b) in [(a0 + nc - 1, b0), (a0 + nc - 1, b0 + 1), (a0 + nc - 2, b0), (a0 + nc - 1, b0 + nr - 1), (a0, b0)]:
        src.discard((5, a, b))                                   # rounded corners, the right side rounder
    return src


_GEO = {}


def geometry(p=P):
    """Seed-independent: the spine, the source cells, and (s, q, r_src in cells) for every art cell."""
    key = (tuple(p["spine"]), tuple(p["src"]))
    if key not in _GEO:
        poly, cum = spine_poly(p)
        src = source_cells(p)
        pts = [centre(s_) for s_ in src]
        info = {}
        for k in ART:
            for cell in key_cells(k):
                if cell in src:
                    continue
                cx, cy = centre(cell)
                s, q = project(poly, cum, (cx, cy))
                r = min(math.hypot(cx - x, cy - y) for x, y in pts) - PITCH
                info[cell] = (s, q, r / PITCH)
        _GEO[key] = (poly, cum, src, info)
    return _GEO[key]


def violates(lit, src, cell, colour, r_src, rmap=None):
    """The reason marking `cell` would read as a mistake, or None. Source cells never count as marks."""
    k, a, b = cell
    nc, nr = dims(k)
    bright = colour in BRIGHT
    why = lit_ok(cell, colour)
    if why:
        return why
    if src and k == 5 and any((5, a + da, b + db) in src for da in (-1, 0, 1) for db in (-1, 0, 1)):
        if not bright:
            return "depth on the source"
        if a <= min(s_[1] for s_ in src) or b >= max(s_[2] for s_ in src):
            return "debris left of / below the source"
        if b > min(s_[2] for s_ in src) + 1:
            return "debris low on the source's side"             # it breaks off at the top-right only

    def marked(c_):
        return c_ == cell or (c_ in lit and c_ not in src)

    def is_bright(c_):
        return (c_ == cell and bright) or (c_ in lit and c_ not in src and lit[c_] in BRIGHT)

    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = (k, a + da, b + db)
        if nb != cell and marked(nb) and (r_src >= 1.0 or (rmap or {}).get(nb, 99.0) >= 1.0):
            return "pair"
    for da, db in ((1, 0), (0, 1)):
        run = 1
        for sgn in (1, -1):
            n = 1
            while marked((k, a + sgn * n * da, b + sgn * n * db)):
                run += 1; n += 1
        if run >= 3:
            return "run"
        line = [cell]
        for sgn in (1, -1):
            n = 1
            while (k, a + sgn * n * da, b + sgn * n * db) in lit:
                line.append((k, a + sgn * n * da, b + sgn * n * db)); n += 1
        if any(c_ in src for c_ in line) and sum(1 for c_ in line if c_ not in src) >= 2:
            return "ledge"
        if bright and r_src >= 2.5:
            for o in range(-6, 1):
                if sum(1 for n in range(7) if is_bright((k, a + (o + n) * da, b + (o + n) * db))) >= 4:
                    return "dotted"
        for o in range(-4, 1):                                   # at most 2 marks in any 5 cells of a line
            ms = [c_ for c_ in ((k, a + (o + n) * da, b + (o + n) * db) for n in range(5)) if marked(c_)]
            if len(ms) >= 3 and any((r_src if c_ == cell else (rmap or {}).get(c_, 99.0)) >= 2.5 for c_ in ms):
                return "three in five"
    for da, db in ((1, 1), (1, -1)):
        run = 1
        for sgn in (1, -1):
            n = 1
            while marked((k, a + sgn * n * da, b + sgn * n * db)):
                run += 1; n += 1
        if run >= 3:
            return "diagonal"
    if bright:
        for oa in (-2, -1, 0):
            for ob in (-2, -1, 0):
                if sum(1 for x in range(3) for y in range(3) if is_bright((k, a + oa + x, b + ob + y))) > 4:
                    return "clump"
    col = sum(1 for n in range(nr) if marked((k, a, n)))
    row = sum(1 for n in range(nc) if marked((k, n, b)))
    if col > 3 or row > 3:
        return "row"
    return None


def es_order(cells, wfun, r):
    """Weighted random order (Efraimidis-Spirakis): sampling without replacement."""
    return sorted(cells, key=lambda c_: -(r.random() ** (1.0 / max(wfun(c_), 1e-9))))


def plume(seed, p=P):
    """One seeded burst: {cell: colour}, the source cells, per-cell info, spine length."""
    rnd = random.Random(seed)
    poly, cum, src, info = geometry(p)
    S = cum[-1]
    a0, b0, nc, nr = p["src"]
    lit = {}
    rmap = {c_: v[2] for c_, v in info.items()}
    for cell in sorted(src, key=lambda c_: (c_[2], c_[1])):      # 1. erosion of the right side and top
        _, a, b = cell
        u = (a - a0 + 1) / nc
        v = (b0 + nr - b) / nr
        x = rnd.random()
        prob = p["erode"] * max(0.0, (u - 0.5) / 0.5) ** 1.6 * v ** p["erode_v"] if v > p["erode_vmin"] else 0.0
        if x >= prob:
            lit[cell] = LIME
    clusters = []                                                # 2. clusters, jittered by the seed
    for (x, y, ss, sq, amp) in p["clusters"]:
        s0, q0 = project(poly, cum, (x, y))
        clusters.append((s0 + rnd.uniform(-1, 1) * p["jitter"], q0 + rnd.uniform(-1, 1) * p["jitter"], ss, sq, amp))
    px0 = cpx((5, a0 + nc - 1, b0))[0] + SQ                      # 3. weights
    py0 = cpx((5, a0, b0))[1]
    th0 = math.radians(p["up"])
    sa_max = max(c_[1] for c_ in src); sb_min = min(c_[2] for c_ in src)
    weight = {}
    for cell, (s, q, r) in info.items():
        k, a, b = cell
        if lit_ok(cell, WHITE):                                  # never lightable at all
            continue
        cx, cy = centre(cell)
        dd = math.hypot(cx - px0, cy - py0)
        th = math.atan2(-(cy - py0), cx - px0)
        near = math.exp(-dd / p["lam_n"]) * (p["near_floor"] + (1 - p["near_floor"]) * max(0.0, math.cos(th - th0)) ** p["aim"])
        if k == 5 and (5, a - 1, b) in src and a > sa_max - 1:
            near += p["fringe"] * math.exp(-(b - sb_min) / p["fringe_fall"])
        elif k == 5 and (5, a, b + 1) in src and b < sb_min + 1:
            near += p["fringe"] * math.exp(-(sa_max - a) / p["fringe_fall"])
        w = p["band_w"][0] + p["band_w"][1] * s
        env = 1.0 / (1.0 + math.exp((abs(q) - w) / (p["soft"] * w)))
        cl = sum(amp * math.exp(-((s - s0) / ss) ** 2 / 2 - ((q - q0) / sq) ** 2 / 2) for s0, q0, ss, sq, amp in clusters)
        band = p["band_lo"] * math.exp(-s / p["lam_f"]) * env
        weight[cell] = near + band + cl
    rnd_colour = {k: random.Random(seed * 7919 + 17 * k) for k in ART}
    rnd_depth = {k: random.Random(seed * 104729 + 3 * k) for k in ART}
    for k in ART:                                                # 4. bright tokens, exact counts per key
        placed = 0
        wmax = max(weight[c_] for c_ in weight if c_[0] == k)
        cells = [c_ for c_ in weight if c_[0] == k and weight[c_] >= p["min_w"] * wmax]
        for cell in es_order(cells, lambda c_: weight[c_], rnd):
            if placed >= p["target"][k]:
                break
            g = p["gap0"] + p["gap1"] * info[cell][0] / S
            rr = int(math.ceil(g))
            kk, a, b = cell
            if any((kk, a + da, b + db) in lit and (kk, a + da, b + db) not in src
                   for da in range(-rr, rr + 1) for db in range(-rr, rr + 1)
                   if (da or db) and da * da + db * db < g * g):
                continue
            if violates(lit, src, cell, WHITE, info[cell][2], rmap):        # colour comes later: check as white
                continue
            lit[cell] = LIME
            placed += 1
    for k in ART:                                                # 5. white: exact count, leaning to the far end
        cand = [c_ for c_ in lit if c_[0] == k and c_ not in src and info[c_][2] >= p["white_min_r"]]
        must = [c_ for c_ in cand if c_ in CHROMA]               # in a chroma block a token can only be white
        rest = es_order([c_ for c_ in cand if c_ not in CHROMA], lambda c_: p["white_base"] + info[c_][0] / S, rnd_colour[k])
        for c_ in (must + rest)[:p["white"][k]]:
            lit[c_] = WHITE
    for k in ART:                                                # bright cells left in a chroma block: drop them
        for c_ in [c_ for c_ in lit if c_[0] == k and lit[c_] == LIME and c_ in CHROMA]:
            del lit[c_]
    for k, want in p["depth"].items():                           # 6. depth: dim tokens at the far end
        placed = 0
        far = [c_ for c_ in weight if c_[0] == k and c_ not in lit and info[c_][0] >= p["depth_from"] * S]
        for c_ in es_order(far, lambda c_: weight[c_], rnd_depth[k]):
            if placed >= want:
                break
            if c_ in lit or violates(lit, src, c_, MID_LIME, info[c_][2], rmap):
                continue
            lit[c_] = MID_LIME
            placed += 1
    return lit, src, info, S


# ---------------------------------------------------------------- key 4: the landed tokens
def landing(seed, window, ink, l=L4, lit=None):
    """A few lime tokens settled on key 4's board outside the URL's window: well apart, the floor first,
    leaning right, at least ink_air px from every ink pixel, on their own random stream. Each row's set
    is drawn whole from every set that keeps the rules (weighted), so a quota is never missed."""
    rnd = random.Random(seed * 31337 + 4)
    out = dict(lit or {})
    nc, nr = dims(4)
    placed = []
    mid = (nc - 1) / 2.0
    for row in sorted(l["quota"], reverse=True):
        lo, hi = l["cols"].get(row, (0, nc - 1))
        cand = [c_ for c_ in key_cells(4) if c_[2] == row and lo <= c_[1] <= hi and c_ not in window
                and not lit_ok(c_, LIME)
                and all(max(_gaps(c_, p_)) > l["ink_air"] for p_ in ink)]
        lean = l["lean"].get(row, 0.0)

        def fits(combo):
            trial, done = dict(out), list(placed)
            for cell in combo:
                if any(math.hypot(cell[1] - o[1], cell[2] - o[2]) < l["gap"] for o in done):
                    return False
                if any(o[2] != cell[2] and abs(cell[1] - o[1]) < l["colgap"] for o in done):
                    return False
                if violates(trial, set(), cell, LIME, 99.0):
                    return False
                trial[cell] = LIME; done.append(cell)
            return True
        sets = [cb for cb in itertools.combinations(cand, l["quota"][row]) if fits(cb)]
        if not sets:
            continue
        ws = [math.prod(math.exp(lean * (c_[1] - mid) / mid) for c_ in cb) for cb in sets]
        pick = rnd.random() * sum(ws)
        for cb, w_ in zip(sets, ws):
            pick -= w_
            if pick <= 0:
                break
        for cell in cb:
            out[cell] = LIME
            placed.append(cell)
    return out, placed


# ---------------------------------------------------------------- checks on the art (mirror the rules)
def art_checks(lit, src, info, window, ink):
    fails = []
    marks = {c_ for c_ in lit if c_ not in src}
    bright = {c_ for c_ in marks if lit[c_] in BRIGHT}
    n = {k: sum(1 for c_ in lit if c_[0] == k and lit[c_] in BRIGHT) for k in (2, 3, 4, 5)}
    if not (n[5] > n[2] > n[3] >= 12):
        fails.append("burst counts %s" % n)
    if not (3 <= n[4] <= 5):
        fails.append("key 4 is not a few: %d" % n[4])
    for k in (2, 3, 4, 5):
        flying = [c_ for c_ in bright if c_[0] == k]
        if flying and sum(1 for c_ in flying if lit[c_] == LIME) * 3 < len(flying):
            fails.append("key %d: less than a third lime" % k)
    r_of = lambda c_: info[c_][2] if c_ in info else 99.0
    for (k, a, b) in marks:
        for da, db in ((1, 0), (0, 1)):
            if (k, a + da, b + db) in marks and (k, a + 2 * da, b + 2 * db) in marks:
                fails.append("straight run of 3 at %s" % ((k, a, b),))
        for da, db in ((1, 1), (1, -1)):
            if (k, a + da, b + db) in marks and (k, a + 2 * da, b + 2 * db) in marks:
                fails.append("diagonal of 3 at %s" % ((k, a, b),))
        if (k, a, b) in bright:
            if sum(1 for x in range(3) for y in range(3) if (k, a + x, b + y) in bright) > 4:
                fails.append("clump at %s" % ((k, a, b),))
            if r_of((k, a, b)) >= 2.5:
                for da, db in ((1, 0), (0, 1)):
                    if sum(1 for m_ in range(7) if (k, a + m_ * da, b + m_ * db) in bright) >= 4:
                        fails.append("dotted line at %s" % ((k, a, b),))
        for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            o = (k, a + x, b + y)
            if o in marks and (r_of((k, a, b)) >= 1.0 or r_of(o) >= 1.0):
                fails.append("side-by-side pair at %s" % ((k, a, b),))
    for (k, a, b) in [c_ for c_ in src if c_ in lit]:            # ledges: a source row or column run on by debris
        for da, db in ((1, 0), (0, 1)):
            run = [(k, a, b)]
            for sgn in (1, -1):
                m_ = 1
                while (k, a + sgn * m_ * da, b + sgn * m_ * db) in lit:
                    run.append((k, a + sgn * m_ * da, b + sgn * m_ * db)); m_ += 1
            if sum(1 for c_ in run if c_ not in src) >= 2:
                fails.append("ledge at %s" % ((k, a, b),))
    for k in (2, 3, 4, 5):
        nc, nr = dims(k)
        for a in range(nc):
            if sum(1 for b in range(nr) if (k, a, b) in marks) > 3:
                fails.append("column of dots, key %d" % k)
        for b in range(nr):
            if sum(1 for a in range(nc) if (k, a, b) in marks) > 3:
                fails.append("row of dots, key %d" % k)
        lines = [[(k, a, b) for a in range(nc)] for b in range(nr)] + [[(k, a, b) for b in range(nr)] for a in range(nc)]
        for line in lines:
            for o in range(len(line) - 4):
                ms = [c_ for c_ in line[o:o + 5] if c_ in marks]
                if len(ms) >= 3 and any(r_of(c_) >= 2.5 for c_ in ms):
                    fails.append("three in five at %s" % (ms[0],))
    for c_ in lit:
        if c_ not in src:
            why = lit_ok(c_, lit[c_])
            if why:
                fails.append("%s: %s" % (why, c_))
        if is_corner(c_):
            fails.append("lit corner %s" % (c_,))
        if c_ in window:
            fails.append("token in the URL's window %s" % (c_,))
        if c_[0] == 4 and lit[c_] != LIME:
            fails.append("key 4 token not lime %s" % (c_,))
        if c_[0] == 4 and any(max(_gaps(c_, p_)) <= L4["ink_air"] for p_ in ink):
            fails.append("key 4 token within %d px of the URL %s" % (L4["ink_air"], c_))
    for c_ in src:
        if edge_distance(c_) < 17:
            fails.append("source cell within 17 px of the window edge %s" % (c_,))
    for c_ in marks:
        if c_[0] == 5 and any((5, c_[1] + x, c_[2] + y) in src for x in (-1, 0, 1) for y in (-1, 0, 1)):
            if lit[c_] == MID_LIME or c_[1] <= min(s_[1] for s_ in src) or c_[2] >= max(s_[2] for s_ in src):
                fails.append("mark against the source's left / bottom, or depth on it")
            if c_[2] > min(s_[2] for s_ in src) + 1:
                fails.append("mark against the source's side below its top two rows %s" % (c_,))
    for c_ in marks:                                             # no stray: every burst mark has company
        if c_[0] in ART:
            near = [o for o in lit if o != c_ and o[0] == c_[0] and math.hypot(o[1] - c_[1], o[2] - c_[2]) <= 3.2]
            if not near:
                fails.append("stray %s" % (c_,))
    for c_ in key_cells(4):                                      # the URL's air, measured on the drawn ink
        if c_ not in window and too_close(c_, ink):
            fails.append("unlit token crowds the URL %s" % (c_,))
    nl = sum(1 for v in lit.values() if v == LIME); nw = sum(1 for v in lit.values() if v == WHITE)
    wf = nw / max(1, nl + nw)
    if not (0.34 <= wf <= 0.44):
        fails.append("white %.2f" % wf)
    return sorted(set(fails)), n, round(wf, 3)


def continuity(lit):
    """Bezel continuity 0-12: key 5's top inner rows vs key 2's bottom inner rows (same x lattice), key 2's
    right inner columns vs key 3's left inner columns (same y lattice). Lit rows and columns start two in
    from the board edge now (the 14 px edge rule), so those are compared."""
    m = lambda c_: c_ in lit
    nc2, nr2 = dims(2); nc5, nr5 = dims(5)
    up5 = [a for a in range(nc5) for b in (1, 2) if m((5, a, b))]
    in2 = [a for a in range(nc2) for b in (nr2 - 4, nr2 - 3) if m((2, a, b))]
    out2 = [b for b in range(nr2) for a in (nc2 - 4, nc2 - 3, nc2 - 2) if m((2, a, b))]
    in3 = [b for b in range(dims(3)[1]) for a in (1, 2) if m((3, a, b))]
    near = lambda x_, y_: sum(1 for x in x_ if any(abs(x - y) <= 1 for y in y_))
    return min(near(up5, in2), 3) + min(near(in2, up5), 3) + min(near(out2, in3), 3) + min(near(in3, out2), 3)


def elongation(cells):
    pts = [centre(c_) for c_ in cells]
    if len(pts) < 3:
        return 0.0, 0.0
    mx = sum(p[0] for p in pts) / len(pts); my = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0] - mx) ** 2 for p in pts); syy = sum((p[1] - my) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    tr, det = sxx + syy, sxx * syy - sxy * sxy
    l1 = tr / 2 + math.sqrt(max(0.0, tr * tr / 4 - det)); l2 = tr / 2 - math.sqrt(max(0.0, tr * tr / 4 - det))
    ang = math.degrees(math.atan2(-(l1 - sxx), sxy)) if sxy else (0.0 if sxx >= syy else 90.0)
    return round(ang, 1), round(math.sqrt(l1 / max(l2, 1e-9)), 2)


# ---------------------------------------------------------------- compose
_TYPE = {}


def type_layer():
    """Both text blocks (seed-independent): masks, boxes, the URL's ink pixels and its window in key 4."""
    if not _TYPE:
        ucov, uboxes = url_block()
        scov, sboxes = slogan_block()
        ink = _ink_pixels(ucov)
        _TYPE.update(ucov=ucov, uboxes=uboxes, scov=scov, sboxes=sboxes, ink=ink, window=url_window(ink))
    return _TYPE


def art(seed, p=P, l=L4):
    t = type_layer()
    lit, src, info, S = plume(seed, p)
    lit, landed = landing(seed, t["window"], t["ink"], l, lit)
    fails, n, wf = art_checks(lit, src, info, t["window"], t["ink"])
    return lit, src, info, landed, fails, n, wf


def compose(seed=SEED, p=P, l=L4):
    t = type_layer()
    lit, src, info, landed, fails, n, wf = art(seed, p, l)
    img = Image.new("RGB", (W, H), INK)
    for k in (2, 3, 4, 5):
        v8.draw_board(img, k, {(a, b): col for (kk, a, b), col in lit.items() if kk == k},
                      skip={(a, b) for (kk, a, b) in t["window"] if kk == k})
    logo_box = v8.logo(img)
    composite(img, ImageChops.lighter(t["ucov"], t["scov"]))
    return img, dict(lit=lit, src=src, info=info, landed=landed, fails=fails, n=n, wf=wf, logo=logo_box, seed=seed)


def _luma(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def mass_centroid(img, key):
    """Visual mass of a key: the centroid of (luma - luma of #131512) over its window, unlit board tokens
    left out (they are symmetric about the board centre). Offset from the window centre (x, y), px."""
    px = img.load(); x0, y0, x1, y1 = v8.WINDOWS[key - 1]
    li = _luma(INK); sw = sx = sy = 0.0
    for y in range(y0, y1):
        for x in range(x0, x1):
            p_ = px[x, y]
            if p_ == UNLIT:
                continue
            w = max(0.0, _luma(p_) - li)
            sw += w; sx += w * (x + 0.5); sy += w * (y + 0.5)
    cx, cy = v8.window_centre(key)
    return round(sx / sw - cx, 1), round(sy / sw - cy, 1)


def search(n, start=1, p=P, l=L4):
    ok = []
    for s in range(start, start + n):
        lit, src, info, landed, fails, cnt, wf = art(s, p, l)
        if not fails:
            k2 = elongation([c_ for c_ in lit if c_[0] == 2 and lit[c_] in BRIGHT])
            ok.append(dict(seed=s, cont=continuity(lit), k2_axis=k2[0], k2_elong=k2[1], n=cnt, white=wf,
                           k4=sorted((c_[1], c_[2]) for c_ in landed)))
    ok.sort(key=lambda o: (-o["cont"], -o["k2_elong"], o["seed"]))
    return ok


def layout_meta(img, meta):
    """Every number that matters, for checks.json and NOTES.md."""
    t = type_layer()
    lit, src = meta["lit"], meta["src"]

    def block(boxes, key):
        b = v8.ink_box(boxes)
        return {"ink_inclusive": [b[0], b[1], b[2] - 1, b[3] - 1], "size": [b[2] - b[0], b[3] - b[1]],
                "box_centre_offset_vs_window": list(v8.centre_offset(b, key)),
                "ink_mass_offset_vs_window": list(mass_centroid(img, key))}
    ink = t["ink"]
    drawn4 = [c_ for c_ in key_cells(4) if c_ not in t["window"]]
    air = {}
    for name, test in (("left", lambda dx, dy, p_, x, y: p_[0] > x + SQ - 1 and dy == 0),
                       ("right", lambda dx, dy, p_, x, y: p_[0] < x and dy == 0),
                       ("above", lambda dx, dy, p_, x, y: p_[1] > y + SQ - 1 and dx == 0),
                       ("below", lambda dx, dy, p_, x, y: p_[1] < y and dx == 0)):
        best = 99
        for c_ in drawn4:
            x, y = cpx(c_)
            for p_ in ink:
                dx, dy = _gaps(c_, p_)
                if test(dx, dy, p_, x, y):
                    best = min(best, (dx if name in ("left", "right") else dy) - 1)
        air[name] = best
    tokens = {}
    for k in (2, 3, 4, 5):
        cells = key_cells(k)
        fly = [c_ for c_ in cells if c_ in lit and c_ not in src]
        tokens["key%d" % k] = {
            "lime": sum(1 for c_ in fly if lit[c_] == LIME), "white": sum(1 for c_ in fly if lit[c_] == WHITE),
            "depth_639840": sum(1 for c_ in fly if lit[c_] == MID_LIME),
            "source_lime": sum(1 for c_ in cells if c_ in src and c_ in lit),
            "unlit_2C2F2B": sum(1 for c_ in cells if c_ not in lit and c_ not in t["window"]),
            "not_drawn_url_window": sum(1 for c_ in cells if c_ in t["window"]),
            "nearest_lit_to_window_edge_px": min([edge_distance(c_) for c_ in fly] or [0]),
            "bright_axis_deg_elongation": list(elongation([c_ for c_ in fly if lit[c_] in BRIGHT]))}
    a0, b0, nc, nr = P["src"]
    sx0, sy0 = cpx((5, a0, b0)); sx1, sy1 = cpx((5, a0 + nc - 1, b0 + nr - 1))
    return {
        "version": "v8", "seed": meta["seed"],
        "layout": {"key1": "logo", "key2": "the plume", "key3": "the dust", "key4": "URL set into its board",
                   "key5": "the source block and its debris", "key6": "slogan"},
        "logo": {"xy": list(meta["logo"][:2]), "size": [meta["logo"][2] - meta["logo"][0], meta["logo"][3] - meta["logo"][1]],
                 "box_centre_offset_vs_window": list(v8.centre_offset(meta["logo"], 1))},
        "url": dict(size_px=URL_SIZE, leading_px=URL_LEAD, tracking_px=TRACK, align="left", lines=URL,
                    cap_height_px=c.cap_height(URL_SIZE), line_ink=t["uboxes"], **block(t["uboxes"], 4),
                    air_to_nearest_token_px=air),
        "slogan": dict(size_px=SLOGAN_SIZE, leading_px=SLOGAN_LEAD, tracking_px=TRACK, align="right",
                       right_ink_column=SLOGAN_RIGHT, cap_top=SLOGAN_CAP, cap_height_px=c.cap_height(SLOGAN_SIZE),
                       lines=SLOGAN, line_ink=t["sboxes"], **block(t["sboxes"], 6)),
        "boards": {"key%d" % k: {"x0_y0_cols_rows": list(BOARDS[k]), "px_inclusive": list(v8.board_px(k)),
                                 "centre_offset_vs_window": list(v8.board_offset(k))} for k in (2, 3, 4, 5)},
        "key4_window_cells": len(t["window"]),
        "key4_landed": sorted([[c_[1], c_[2]] for c_ in meta["landed"]]),
        "source_block": {"cells_a_b_cols_rows": [a0, b0, nc, nr], "px_inclusive": [sx0, sy0, sx1 + SQ - 1, sy1 + SQ - 1],
                         "lit_cells": sum(1 for c_ in src if c_ in lit),
                         "nearest_window_edge_px": min(edge_distance(c_) for c_ in src)},
        "tokens": tokens, "bright_per_key": meta["n"], "white_share_of_bright": meta["wf"],
        "bezel_continuity_0_12": continuity(lit), "art_fails": meta["fails"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--search", type=int, default=0)
    ap.add_argument("--start", type=int, default=1)
    a = ap.parse_args()
    if a.search:
        ok = search(a.search, a.start)
        print(len(ok), "of", a.search, "seeds pass every rule; best bezel continuity, then key 2 elongation, first")
        for o in ok[:60]:
            print(o)
        return
    img, meta = compose(a.seed)
    lay = layout_meta(img, meta)
    checks = v8.render(img, a.out, extra={"layout": lay})
    v8.photo_preview(a.out)
    print(json.dumps({k: v for k, v in checks.items() if k != "layout"}, indent=1, default=str))
    print(json.dumps(lay, indent=1, default=str))
    if meta["fails"]:
        raise SystemExit("art rules fail: %s" % meta["fails"])
    if not checks["hard_rules_pass"]:
        raise SystemExit("hard rules fail")


if __name__ == "__main__":
    main()
