"""Token Deck welcome screen v7 (the image burned into the deck's boot slot), own code.

v7 answers Gabriel's notes on v6 as burned (Nov 2, photos/welcome-v6-on-deck.webp): bring back v1's
white tokens and its dim "background" tokens, make the tokens a little smaller like the stigg.io hero's
particles, make the text slightly larger, and rethink where the URL and the slogan sit. Four designs
(v7/a-d, two per layout) went through a four-critic review (typography, composition, brand, device);
this is the synthesis: a and b's text keys on c's burst, with every critic's must-fix applied.

Layout key 1 logo     | key 2 the plume  | key 3 the dust
       key 4 slogan   | key 5 the source | key 6 URL
       The slogan sits under the logo, flush on the logo's left edge (x = 20), so the left column reads
       as one lockup, the mark and then what it is; the URL is alone at the bottom right, read last.
       Why not the slogan on the right: a right-column tile hugs its window's left edge, so those keys
       hold 58 px at most and centre only 50 px, and 'Management' inks 57 px at v6's 9.5 px. There the
       slogan cannot grow, and it sits 4 px off centre (the left-heavy key the v6 photo shows). Why not
       the URL under the logo: it costs the logo its clear space and centring, and bright ink on all
       four bevels of the brand key.
Type   Soehne Buch 10.5 px on 13 px leading, white, both blocks. 10.5 px is the first size whose hinted
       cap height (8 px) and x-height (6 px) are larger than v6's: every size from 9.5 to 10.49 px
       renders v6's 7 and 5 px and only gets wider. Tracking -0.06 px (-0.6 % of the em) is what lets
       'The AI Usage' and 'Management' fit key 4's 62 px (x 20-81) with nothing in the rim; nothing is
       erased after rendering. Otherwise v6's pipeline: sub-pixel glyph x, gamma 1.5, periods as single
       crisp pixels, the '/u' kern dropped. New: each 'i' is the dotless glyph on a whole pixel with a
       crisp one-pixel dot on the cap-top row and an empty row under it. The hinted dot bleeds into the
       stem at this size, and under the panel's bloom 'io.stigg.io' read as 'lo.stlgg.lo'.
       Slogan pen x 20, cap top 151, centred on window 4. URL pen x 244 (whole pixel, the left edge of
       key 3's board above it), cap top 157, centred on window 6.
Logo   The official file, 60 x 17 at (20, 50), alone in key 1, centred, 30 px clear above and below.
Tokens One lattice for the whole panel: 3 px squares on a 5 px pitch (2 px gaps), cells at x = 4 + 5i,
       y = 4 + 5j, smaller than v1 and v6's 4 px. Each art key shows the same 10 x 10 board (48 x 48 px),
       centred on its window to 1 px: key 2 x 134-181 / y 34-81, key 3 x 244-291, key 5 x 134-181 /
       y 144-191. Every cell is an unlit #2C2F2B token unless lit (Stigg neutral 800: the boards carry
       the visual weight of v1's #242723 boards, which Gabriel saw on the deck, while 3 px tokens get a
       little more contrast; #3C3E3A made the boards outweigh the burst). Key 3's last column (x 289-291)
       shares an 8 px JPEG block with the tile edge and stays unlit. Text keys carry no tokens.
       Lit: lime #92E759 and white #FFFFFF, about 60 / 40 over all bright tokens, at least a third lime
       in every key; a few #639840 depth tokens at the plume's far end only (the hero's dim points).
       No #436633, no grey "dim whites".
Burst  The After Tokens explosion: a solid lime source block one cell in from key 5's lower-left corner
       erodes at its right and top (pixelmark erosion), debris blows up and to the right from its top-right
       corner, the plume rises through the bezel into key 2, crosses it on a diagonal, bends right through
       the bezel into key 3 and lands there as dust trending down toward the URL. The density is a designed
       field (near-field blast + a band along a curved spine + clusters at fixed points of it); the seed
       only decides individual cells. Exact counts per key come from weighted sampling without replacement.
Rules  Enforced while placing and re-checked afterwards: no 3 marks in a straight row or column; no
       diagonal staircase of 3; no 4 bright tokens within 7 cells of one row or column; no 3 x 3 window
       with more than 4 bright tokens; no mark in a board's corner; at most 2 marks on a board's outer
       row or column; at most 3 marks in any row or column of a board; debris touches the source only
       on its right and top and never extends one of its rows or columns into a ledge; depth tokens never
       touch the source; beyond the debris tokens touch only at corners; cells far off the field never
       light. Every token is on the lattice, one per cell. Hard rules (v7_common.render): all
       content inside the six tile rects, at least 6 px from every window edge, nothing darker than
       #131512, luma within 4 levels of #131512 outside the tiles in the JPEG as burned (q97, 4:2:0),
       JPEG at most 22,300 bytes.

usage: welcome_v7.py                 render the final (seed SEED) into this folder
       welcome_v7.py --seed N --out DIR
       welcome_v7.py --search N      list seeds 1..N that pass every art rule, best bezel continuity first
"""
import argparse, json, math, os, random, sys
from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v7_common as c                                   # noqa: E402

v6 = c.v6
W, H = c.W, c.H
INK, LIME, WHITE = c.INK, c.LIME, c.WHITE
UNLIT = (0x2C, 0x2F, 0x2B)                              # Stigg neutral 800 ("subtle")
MID_LIME = (0x63, 0x98, 0x40)                           # After Tokens depth step
BRIGHT = (LIME, WHITE)
SEED = 184                                              # chosen by eye among the seeds 1-300 that pass every art rule

# ---------------------------------------------------------------- type
SIZE, LEADING, TRACK, GAMMA = 10.5, 13, -0.06, 1.5
LOGO_XY = (20, 50)
SLOGAN = ["The AI Usage", "Management", "Console"]
URL = ["io.stigg.io", "/usage"]
SLOGAN_PEN, SLOGAN_CAP = 20.0, 151                      # key 4, flush on the logo's left edge
URL_PEN, URL_CAP = 244.0, 157                           # key 6, on key 3's board edge


def font():
    return ImageFont.truetype(c.base.FONT, SIZE)


def layout_line(f, text, pen):
    """v6's shaped x of every glyph (pair kerning, '/u' kern dropped) plus TRACK after each glyph."""
    return [x + TRACK * j for j, x in enumerate(v6.layout_line(f, text, pen))]


def _glyph(f, ch, x, top):
    fx = math.floor(x); phi = x - fx
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).text((fx, top), ch, font=f, fill=255)
    if phi > 0.01:
        g = Image.blend(g, ImageChops.offset(g, 1, 0), phi)
    return g


def text_mask(blocks):
    """blocks: [(pen_x, cap_top_y, [lines])] -> L coverage mask for the panel and each line's ink box.
    Periods are one crisp pixel on the baseline row; an 'i' is the dotless glyph on a whole pixel with a
    crisp one-pixel dot on the cap-top row, above its stem."""
    f = font()
    asc, _ = f.getmetrics()
    cap_off = f.getbbox("H")[1]
    cov = Image.new("L", (W, H), 0)
    dots, boxes = [], []
    for pen, cap_top, lines in blocks:
        for n, t in enumerate(lines):
            top = cap_top - cap_off + n * LEADING
            base_y = top + asc
            lb = [W, H, 0, 0]

            def grow(x0, y0, x1, y1):
                lb[:] = [min(lb[0], x0), min(lb[1], y0), max(lb[2], x1), max(lb[3], y1)]

            for ch, x in zip(t, layout_line(f, t, pen)):
                if ch == " ":
                    continue
                if ch == ".":
                    px, py = round(x + 0.51), base_y - 1
                    dots.append((px, py)); grow(px, py, px + 1, py + 1)
                    continue
                if ch == "i":
                    g = _glyph(f, "ı", round(x), top)
                    bb = g.getbbox()
                    stem = max(range(bb[0], bb[2]), key=lambda cx: sum(g.getpixel((cx, y)) for y in range(bb[1], bb[3])))
                    dots.append((stem, cap_top + n * LEADING)); grow(stem, cap_top + n * LEADING, stem + 1, bb[3])
                else:
                    g = _glyph(f, ch, x, top)
                    bb = g.getbbox()
                    if bb:
                        grow(*bb)
                cov = ImageChops.lighter(cov, g)
            boxes.append(tuple(lb))
    for p in dots:
        cov.putpixel(p, 255)
    return cov, boxes


def draw_text(img, blocks):
    v6.GAMMA = GAMMA
    cov, boxes = text_mask(blocks)
    v6.composite_text(img, cov, WHITE)
    return boxes


# ---------------------------------------------------------------- lattice and boards
PITCH, SQ = 5, 3
OX, OY = 4, 4                                           # cells at x = 4 + 5i, y = 4 + 5j
BLOCKS = {2: (26, 6), 3: (48, 6), 5: (26, 28)}          # (i0, j0) of each art key's 10 x 10 board
NB = 10
QUIET = {(57, j) for j in range(6, 16)}                 # key 3's last column: shares a JPEG block with the tile edge


def cell_px(i, j):
    return OX + PITCH * i, OY + PITCH * j


def cell_centre(i, j):
    x, y = cell_px(i, j)
    return x + SQ / 2.0, y + SQ / 2.0


def block_cells(k):
    i0, j0 = BLOCKS[k]
    return [(i, j) for j in range(j0, j0 + NB) for i in range(i0, i0 + NB)]


def key_of(i, j):
    for k, (i0, j0) in BLOCKS.items():
        if i0 <= i < i0 + NB and j0 <= j < j0 + NB:
            return k
    return None


# ---------------------------------------------------------------- the burst (after v7/c's generator)
def catmull(points, n=400):
    """Dense polyline through the control points (Catmull-Rom)."""
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
    # panel px, source to dust: up out of key 5, across key 2 on a diagonal, right into key 3, down toward the URL
    spine=[(160, 160), (161, 122), (164, 76), (192, 50), (250, 50), (276, 66), (294, 84)],
    src=(27, 31, 4, 6),            # source block: i0, j0, cols, rows (key 5, one cell in from the board edges)
    erode=0.65,                    # pixelmark erosion of the source's right side and top
    lam_n=13.0, up=58.0, aim=2.0,  # near field: blast from the source's top-right corner (px decay, direction deg, focus)
    fringe=0.35,                   # extra weight for fragments right against the source's right and top edges
    band_w=(7.0, 0.07), soft=0.45, lam_f=170.0, band_lo=0.18,   # the plume between clusters
    # clusters at fixed panel points (x, y, sigma along the spine, sigma across it, amplitude)
    clusters=[(163, 72, 13, 6, 1.0),       # key 2: where the plume comes up through the bezel
              (176, 47, 11, 6, 0.85),      # key 2: where it bends right
              (256, 50, 12, 8, 0.8),       # key 3: where it arrives
              (274, 68, 12, 8, 0.6)],      # key 3: where it lands, toward the URL below
    jitter=5.0,                    # seeded jitter of each cluster centre (px)
    target={5: 11, 2: 17, 3: 13},  # bright tokens per key (key 5: debris beyond the source)
    white={5: 4, 2: 10, 3: 8},     # white tokens per key: 22 of 58 bright (38 %), at least a third lime per key
    white_base=0.30, white_min_r=1.5,   # within a key, white leans to the far end; never next to the source
    depth={3: 3},                  # #639840 depth tokens, far end of the spine only (key 3)
    depth_from=0.62,               # ... from this fraction of the spine length on
    edge=0.5,                      # weight on each board's outer ring: the plume fades at the board edge
    min_w=0.03,                    # cells under this fraction of their key's heaviest weight never light: no strays
    gap0=1.0, gap1=0.35,           # min centre distance between bright tokens, cells: gap0 + gap1 * s/S
)


def spine_poly(p=P):
    poly = catmull(p["spine"])
    cum = [0.0]
    for a, b in zip(poly, poly[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return poly, cum


def source_cells(p=P):
    i0, j0, nc, nr = p["src"]
    src = {(i, j) for i in range(i0, i0 + nc) for j in range(j0, j0 + nr)}
    for corner in [(i0 + nc - 1, j0), (i0 + nc - 1, j0 + 1), (i0 + nc - 2, j0), (i0 + nc - 1, j0 + nr - 1), (i0, j0)]:
        src.discard(corner)                                          # rounded corners, the right side rounder
    return src


def violates(lit, src, cell, bright, r_src):
    """The reason marking `cell` would read as a mistake, or None. Source cells never count as marks."""
    i, j = cell
    if cell in QUIET:
        return "quiet"
    if any((i + a, j + b) in src for a in (-1, 0, 1) for b in (-1, 0, 1)):
        if not bright:
            return "depth on the source"                       # the source keeps a crisp edge
        if i <= min(c_[0] for c_ in src) or j >= max(c_[1] for c_ in src):
            return "debris left of / below the source"          # fragments break off its right and top only
    marked = lambda c_: c_ == cell or (c_ in lit and c_ not in src)
    is_bright = lambda c_: (c_ == cell and bright) or (c_ in lit and c_ not in src and lit[c_] in BRIGHT)
    if r_src >= 1.0 and any(marked((i + a, j + b)) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        return "pair"                                           # beyond the debris, tokens touch only at corners
    for di, dj in ((1, 0), (0, 1)):
        run = 1
        for sgn in (1, -1):
            n = 1
            while marked((i + sgn * n * di, j + sgn * n * dj)):
                run += 1; n += 1
        if run >= 3:
            return "run"
        # a ledge: debris that continues one of the source's rows or columns by more than one cell
        on = lambda c_: c_ == cell or c_ in lit                  # lit includes the source's surviving cells
        line, touches = [cell], False
        for sgn in (1, -1):
            n = 1
            while on((i + sgn * n * di, j + sgn * n * dj)):
                line.append((i + sgn * n * di, j + sgn * n * dj)); n += 1
        if any(c_ in src for c_ in line) and sum(1 for c_ in line if c_ not in src) >= 2:
            return "ledge"
        if bright and r_src >= 2.5:
            for o in range(-6, 1):
                if sum(1 for n in range(7) if is_bright((i + (o + n) * di, j + (o + n) * dj))) >= 4:
                    return "dotted"
    for di, dj in ((1, 1), (1, -1)):                              # no diagonal staircase of 3 marks
        run = 1
        for sgn in (1, -1):
            n = 1
            while marked((i + sgn * n * di, j + sgn * n * dj)):
                run += 1; n += 1
        if run >= 3:
            return "diagonal"
    if bright:
        for oi in (-2, -1, 0):
            for oj in (-2, -1, 0):
                if sum(1 for a in range(3) for b in range(3) if is_bright((i + oi + a, j + oj + b))) > 4:
                    return "clump"
    k = key_of(i, j)
    i0, j0 = BLOCKS[k]
    if i in (i0, i0 + NB - 1) and j in (j0, j0 + NB - 1):
        return "corner"
    col = sum(1 for n in range(NB) if marked((i, j0 + n)))
    row = sum(1 for n in range(NB) if marked((i0 + n, j)))
    if (i in (i0, i0 + NB - 1) and col > 2) or (j in (j0, j0 + NB - 1) and row > 2):
        return "edge"
    if col > 3 or row > 3:
        return "row"
    return None


def plume(seed, p=P):
    """One seeded burst: {cell: colour}, the source cells, per-cell (s, q, r_src in cells), spine length."""
    rnd = random.Random(seed)
    poly, cum = spine_poly(p)
    S = cum[-1]
    i0, j0, nc, nr = p["src"]
    src = source_cells(p)
    lit = {}
    # 1. erosion: the source's right columns and top rows break off (pixelmark: u > 0.5 erodes)
    for (i, j) in sorted(src, key=lambda c_: (c_[1], c_[0])):
        u = (i - i0 + 1) / nc
        v = (j0 + nr - j) / nr
        if rnd.random() >= p["erode"] * max(0.0, (u - 0.5) / 0.5) ** 1.6 * (0.3 + 0.7 * v):
            lit[(i, j)] = LIME
    # 2. clusters at designed points along the plume, jittered by the seed, in spine coordinates
    clusters = []
    for (x, y, ss, sq, a) in p["clusters"]:
        s0, q0 = project(poly, cum, (x, y))
        clusters.append((s0 + rnd.uniform(-1, 1) * p["jitter"], q0 + rnd.uniform(-1, 1) * p["jitter"], ss, sq, a))
    # 3. a weight per free cell: near-field blast + plume band + clusters, faded on the board edge
    src_pts = [cell_centre(*c_) for c_ in src]
    px0 = cell_px(i0 + nc - 1, j0)[0] + SQ; py0 = cell_px(i0, j0)[1]          # the eroding top-right corner
    th0 = math.radians(p["up"])
    si_max = max(c_[0] for c_ in src); sj_min = min(c_[1] for c_ in src)
    info, weight = {}, {}
    for k in BLOCKS:
        bi, bj = BLOCKS[k]
        for (i, j) in block_cells(k):
            if (i, j) in src:
                continue
            cx_, cy_ = cell_centre(i, j)
            s, q = project(poly, cum, (cx_, cy_))
            r = min(math.hypot(cx_ - x, cy_ - y) for x, y in src_pts) - PITCH
            info[(i, j)] = (s, q, r / PITCH)
            dd = math.hypot(cx_ - px0, cy_ - py0)
            th = math.atan2(-(cy_ - py0), cx_ - px0)
            near = math.exp(-dd / p["lam_n"]) * (0.08 + 0.92 * max(0.0, math.cos(th - th0)) ** p["aim"])
            if any((i + a, j + b) in src for a, b in ((-1, 0), (0, 1))) and (i > si_max - 1 or j < sj_min + 1):
                near += p["fringe"]
            w = p["band_w"][0] + p["band_w"][1] * s
            env = 1.0 / (1.0 + math.exp((abs(q) - w) / (p["soft"] * w)))
            cl = sum(a * math.exp(-((s - s0) / ss) ** 2 / 2 - ((q - q0) / sq) ** 2 / 2) for s0, q0, ss, sq, a in clusters)
            band = p["band_lo"] * math.exp(-s / p["lam_f"]) * env
            ring = i in (bi, bi + NB - 1) or j in (bj, bj + NB - 1)
            weight[(i, j)] = (near + band + cl) * (p["edge"] if ring else 1.0)

    def es_order(cells, wfun, r=rnd):
        return sorted(cells, key=lambda c_: -(r.random() ** (1.0 / max(wfun(c_), 1e-9))))

    # colour and depth draw from their own streams, one per key: changing them never moves a bright token
    rnd_colour = {k: random.Random(seed * 7919 + 17 * k) for k in BLOCKS}
    rnd_depth = {k: random.Random(seed * 104729 + 3 * k) for k in BLOCKS}

    # 4. bright tokens, exact counts per key: weighted sampling without replacement, spacing and rules
    for k in (5, 2, 3):
        placed = 0
        wmax = max(weight[c_] for c_ in weight if key_of(*c_) == k)
        cells = [c_ for c_ in weight if key_of(*c_) == k and weight[c_] >= p["min_w"] * wmax]
        for (i, j) in es_order(cells, lambda c_: weight[c_]):
            if placed >= p["target"][k]:
                break
            g = p["gap0"] + p["gap1"] * info[(i, j)][0] / S
            rr = int(math.ceil(g))
            if any((i + di, j + dj) in lit and (i + di, j + dj) not in src
                   for di in range(-rr, rr + 1) for dj in range(-rr, rr + 1)
                   if (di or dj) and di * di + dj * dj < g * g):
                continue
            if violates(lit, src, (i, j), True, info[(i, j)][2]):
                continue
            lit[(i, j)] = LIME
            placed += 1
    # 5. colour: an exact number of white tokens per key, leaning to the far end, never next to the source
    for k in (5, 2, 3):
        cand = [c_ for c_ in lit if key_of(*c_) == k and c_ not in src and info[c_][2] >= p["white_min_r"]]
        for c_ in es_order(cand, lambda c_: p["white_base"] + info[c_][0] / S, rnd_colour[k])[:p["white"][k]]:
            lit[c_] = WHITE
    # 6. depth: a few dim tokens behind the bright ones, at the plume's far end only
    for k, want in p["depth"].items():
        placed = 0
        far = [c_ for c_ in weight if key_of(*c_) == k and c_ not in lit and info[c_][0] >= p["depth_from"] * S]
        for c_ in es_order(far, lambda c_: weight[c_], rnd_depth[k]):
            if placed >= want:
                break
            if c_ in lit or violates(lit, src, c_, False, info[c_][2]):
                continue
            lit[c_] = MID_LIME
            placed += 1
    return lit, src, info, S


# ---------------------------------------------------------------- checks on the art (mirror the rules)
def art_checks(lit, src, info):
    fails = []
    marks = {c_ for c_ in lit if c_ not in src}
    bright = {c_ for c_ in marks if lit[c_] in BRIGHT}
    n = {k: sum(1 for c_ in lit if key_of(*c_) == k and lit[c_] in BRIGHT) for k in BLOCKS}
    if not (n[5] > n[2] > n[3] >= 12):
        fails.append("counts %s" % n)
    for k in BLOCKS:
        flying = [c_ for c_ in bright if key_of(*c_) == k]
        if flying and sum(1 for c_ in flying if lit[c_] == LIME) * 3 < len(flying):
            fails.append("key %d: less than a third lime" % k)
    for (i, j) in marks:
        for di, dj in ((1, 0), (0, 1)):
            if (i + di, j + dj) in marks and (i + 2 * di, j + 2 * dj) in marks:
                fails.append("straight run of 3 at %s" % ((i, j),))
        for di, dj in ((1, 1), (1, -1)):
            if (i + di, j + dj) in marks and (i + 2 * di, j + 2 * dj) in marks:
                fails.append("diagonal of 3 at %s" % ((i, j),))
        if (i, j) in bright:
            if sum(1 for a in range(3) for b in range(3) if (i + a, j + b) in bright) > 4:
                fails.append("clump at %s" % ((i, j),))
            if info[(i, j)][2] >= 2.5:
                for di, dj in ((1, 0), (0, 1)):
                    if sum(1 for m_ in range(7) if (i + m_ * di, j + m_ * dj) in bright) >= 4:
                        fails.append("dotted line at %s" % ((i, j),))
    for (i, j) in marks:
        if info[(i, j)][2] >= 1.0 and any((i + a, j + b) in marks for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            fails.append("side-by-side pair at %s" % ((i, j),))
    for (i, j) in [c_ for c_ in src if c_ in lit]:               # ledges: a source row or column run on by debris
        for di, dj in ((1, 0), (0, 1)):
            run = [(i, j)]
            for sgn in (1, -1):
                m_ = 1
                while (i + sgn * m_ * di, j + sgn * m_ * dj) in lit:
                    run.append((i + sgn * m_ * di, j + sgn * m_ * dj)); m_ += 1
            if sum(1 for c_ in run if c_ not in src) >= 2:
                fails.append("ledge at %s" % ((i, j),))
    for k, (i0, j0) in BLOCKS.items():
        for m_ in range(NB):
            col = sum(1 for t in range(NB) if (i0 + m_, j0 + t) in marks)
            row = sum(1 for t in range(NB) if (i0 + t, j0 + m_) in marks)
            if col > 3 or row > 3:
                fails.append("row/column of dots, key %d" % k)
            if (m_ in (0, NB - 1)) and (col > 2 or row > 2):
                fails.append("marks along the board edge, key %d" % k)
        if any((i0 + a, j0 + b) in marks for a in (0, NB - 1) for b in (0, NB - 1)):
            fails.append("corner, key %d" % k)
    if any(c_ in marks for c_ in QUIET):
        fails.append("key 3 last column lit")
    for c_ in marks:
        if any((c_[0] + a, c_[1] + b) in src for a in (-1, 0, 1) for b in (-1, 0, 1)):
            if lit[c_] == MID_LIME or c_[0] <= min(s[0] for s in src) or c_[1] >= max(s[1] for s in src):
                fails.append("mark against the source's left / bottom, or depth on it")
    nl = sum(1 for v in lit.values() if v == LIME); nw = sum(1 for v in lit.values() if v == WHITE)
    wf = nw / max(1, nl + nw)
    if not (0.34 <= wf <= 0.44):
        fails.append("white %.2f" % wf)
    return sorted(set(fails)), n, wf


def continuity(lit):
    """Tokens leaving key 5's top rows meet tokens entering key 2's bottom rows near the same columns,
    and key 2's right columns meet key 3's left columns near the same rows (0-12)."""
    m = lambda c_: c_ in lit
    i5, j5 = BLOCKS[5]; i2, j2 = BLOCKS[2]; i3, j3 = BLOCKS[3]
    up5 = [i - i5 for i in range(i5, i5 + NB) for j in (j5, j5 + 1) if m((i, j))]
    in2 = [i - i2 for i in range(i2, i2 + NB) for j in (j2 + NB - 2, j2 + NB - 1) if m((i, j))]
    out2 = [j - j2 for j in range(j2, j2 + NB) for i in (i2 + NB - 2, i2 + NB - 1) if m((i, j))]
    in3 = [j - j3 for j in range(j3, j3 + NB) for i in (i3, i3 + 1) if m((i, j))]
    near = lambda a, b: sum(1 for x in a if any(abs(x - y) <= 1 for y in b))
    return min(near(up5, in2), 3) + min(near(in2, up5), 3) + min(near(out2, in3), 3) + min(near(in3, out2), 3)


def elongation(cells):
    """Bright-token PCA: (axis angle in degrees, panel y up; elongation = sqrt of the eigenvalue ratio)."""
    pts = [cell_centre(*c_) for c_ in cells]
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
def compose(seed=SEED, p=P):
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    lit, src, info, S = plume(seed, p)
    for k in BLOCKS:
        for (i, j) in block_cells(k):
            x, y = cell_px(i, j)
            d.rectangle([x, y, x + SQ - 1, y + SQ - 1], fill=lit.get((i, j), UNLIT))
    logo, _ = c.logo_image()
    img.paste(logo, LOGO_XY)
    boxes_s = draw_text(img, [(SLOGAN_PEN, SLOGAN_CAP, SLOGAN)])
    boxes_u = draw_text(img, [(URL_PEN, URL_CAP, URL)])
    fails, n, wf = art_checks(lit, src, info)

    def centre(boxes, key):
        x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes); x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
        wx, wy = c.window_centre(key)
        return {"ink": [x0, y0, x1 - 1, y1 - 1], "centre_offset_vs_window": [round((x0 + x1) / 2 - wx, 1), round((y0 + y1) / 2 - wy, 1)]}

    tokens = {}
    for k in BLOCKS:
        cells = block_cells(k)
        flying = [c_ for c_ in cells if lit.get(c_) in BRIGHT and c_ not in src]
        tokens["key%d" % k] = {
            "lime": sum(1 for c_ in flying if lit[c_] == LIME),
            "white": sum(1 for c_ in flying if lit[c_] == WHITE),
            "source_lime": sum(1 for c_ in cells if c_ in src and c_ in lit),
            "depth_639840": sum(1 for c_ in cells if lit.get(c_) == MID_LIME),
            "unlit_2C2F2B": sum(1 for c_ in cells if c_ not in lit),
            "bright_axis_deg_elongation": elongation(flying)}
    boards = {}
    for k, (i0, j0) in BLOCKS.items():
        x0, y0 = cell_px(i0, j0); x1, y1 = x0 + PITCH * NB - (PITCH - SQ), y0 + PITCH * NB - (PITCH - SQ)
        wx, wy = c.window_centre(k)
        boards["key%d" % k] = {"px": [x0, y0, x1 - 1, y1 - 1], "centre_offset_vs_window": [(x0 + x1) / 2 - wx, (y0 + y1) / 2 - wy]}
    lx, ly = LOGO_XY
    meta = {
        "version": "v7", "seed": seed,
        "layout": {"key1": "logo", "key2": "art: the plume", "key3": "art: the dust", "key4": "slogan",
                   "key5": "art: the source block and its debris", "key6": "URL"},
        "logo": {"xy": [lx, ly], "size": [60, 17], "centre_offset_vs_window": [lx + 30 - c.window_centre(1)[0], ly + 8.5 - c.window_centre(1)[1]]},
        "type": {"font": "Soehne Buch", "size_px": SIZE, "leading_px": LEADING, "tracking_px": TRACK,
                 "cap_height_px": c.cap_height(SIZE), "colour": "#FFFFFF"},
        "slogan": dict(pen_x=SLOGAN_PEN, cap_top=SLOGAN_CAP, lines=SLOGAN, line_ink=boxes_s, **centre(boxes_s, 4)),
        "url": dict(pen_x=URL_PEN, cap_top=URL_CAP, lines=URL, line_ink=boxes_u, **centre(boxes_u, 6)),
        "lattice": {"pitch": PITCH, "square": SQ, "origin": [OX, OY], "boards": boards, "unlit": "#2C2F2B",
                    "lit": ["#92E759", "#FFFFFF"], "depth": ["#639840"]},
        "tokens": tokens,
        "bright_total": sum(n.values()), "white_share_of_bright": round(wf, 3),
        "art_fails": fails, "bezel_continuity_0_12": continuity(lit),
    }
    return img, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--search", type=int, default=0)
    a = ap.parse_args()
    if a.search:
        ok = []
        for s in range(1, a.search + 1):
            lit, src, info, _ = plume(s)
            fails, n, wf = art_checks(lit, src, info)
            if not fails:
                k2 = elongation([c_ for c_ in lit if key_of(*c_) == 2 and lit[c_] in BRIGHT])
                ok.append((continuity(lit), k2[1], s, n, round(wf, 3)))
        ok.sort(key=lambda o: (-o[0], -o[1], o[2]))
        print(len(ok), "of", a.search, "seeds pass every art rule; best bezel continuity, then key 2 elongation, first")
        for o in ok[:40]:
            print(o)
        return
    img, meta = compose(a.seed)
    assert not meta["art_fails"], meta["art_fails"]
    checks = c.render(img, a.out, extra={"layout": meta})
    print(json.dumps({k: v for k, v in checks.items() if k != "layout"}, indent=1))
    print(json.dumps(meta, indent=1, default=str))
    if not checks["hard_rules_pass"]:
        raise SystemExit("hard rules fail")


if __name__ == "__main__":
    main()
