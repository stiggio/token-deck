#!/usr/bin/env python3
"""Token Deck welcome v8, candidate b: THE URL IS THE SOURCE. Own code; imports v8_common only.

Layout key 1 logo        | key 2 the rise    | key 3 the dust
       key 4 URL+source  | key 5 the run     | key 6 slogan
       The solid lime source block sits in key 4 under the URL, so the burst starts where the URL is.
       Its debris breaks off the block's right side and runs right through key 5 (the plume's lower
       stretch), rises through key 2, bends right over its top and lands in key 3 as dust drifting
       down toward the slogan: one arc from the bottom-left key to the top-right key.
Key 4  URL 'io.stigg.io' / '/usage', Soehne Buch 10.5 px / 13 px leading, flush left on the board's left
       edge (x 21, one px right of the logo's x 20), cap top on the board's top row (y 141). The board
       cells under the URL's ink box plus a 2 px margin are knocked out (drawn as ink), so the URL sits in
       a clearing cut into the token board; the cells around the clearing never light, so nothing bright
       comes within 7 px of the type. The source block (5 x 4 cells, right corners cut) sits one cell in
       from the board's left and bottom edges, under the URL's first letters.
Key 6  Slogan 9.5 px / 12 px, flush right on the tile's last column (x 291): the long lines fill the
       58 px key, and 'Console' on the right puts the block's visual mass 0.9 px from the window centre.
       Cap top 152 (153 rings 5 luma levels outside the tile).
Tokens v8_common boards (3 px squares, 5 px pitch, every cell an unlit #2C2F2B token unless lit). Lit:
       lime #92E759, white #FFFFFF, a few #639840 depth tokens in the dust. The outer ring of every art
       board stays unlit: the quiet cells, and the sides 6-11 px from a window edge, which the bevel
       reflects (the v7 photo shows reflections from boards 14-16 px in). In keys 2 and 5 the last two
       inner columns share a 16 px chroma block with the window outside the tile: tokens there are white
       (lime there raised the colour halo to v8_common's limit of 10); v8_common.quiet() covers only the
       8 px luma blocks.
Burst  Pixelmark erosion of the block's right column; each eroded cell lands as a fragment just past the
       block's edge. Then a density field per key: a near-field blast from the source's right edge (key 4),
       a band along each key's own spine segment (the bezels hide 32-40 px, so each key gets the stretch of
       the arc it shows), clusters at fixed points jittered by the seed. Exact counts per key by weighted
       sampling without replacement; colour (white leaning to each key's far end, none in key 4) and depth
       from their own random streams, so recolouring never moves a token.
Rules  Enforced while placing and re-checked: no 3 marks in a straight row or column; no diagonal
       staircase of 3; no 4 bright tokens within 7 cells of one row, column or diagonal beyond the near
       field, and no 3 marks within 5 cells of one row or column; no 3 x 3 window with more than 4 bright
       tokens; no four marks on the corners of a 3 x 3 square; no lit corner; at most 2 marks on an outer
       row or column; at most 3 marks in any row or column; at least a third lime per key; white share of
       all bright tokens 0.34-0.44; density falls along the plume (key 5 >= key 2 > key 3); debris touches
       the source only on its right and never runs a source row on (a ledge, or more than one mark in the
       four cells after the row's end); key 4's sparks never touch anything; depth tokens never touch the
       source; beyond the debris tokens touch only at corners; cells far from the field never light.
Alts   alt-url-9.5: the URL at the slogan's 9.5 px / 12 px (cap top 142), same tokens. alt-seed-361: the
       runner-up burst.

usage: make.py                       render the final (seed SEED) here and the alternatives in alt-*/;
                                     exits non-zero if any render fails a hard or an art rule
       make.py --variant V [--seed N] [--out DIR]
       make.py --search N           seeds 1..N that pass every art rule and the hard rules with a margin
"""
import argparse, copy, json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WELCOME = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WELCOME)
import v8_common as v8                                   # noqa: E402
from PIL import Image                                    # noqa: E402

W, H = v8.W, v8.H
INK, LIME, WHITE, UNLIT, DEPTH = v8.INK, v8.LIME, v8.WHITE, v8.UNLIT, v8.MID_LIME
BRIGHT = (LIME, WHITE)
PITCH, SQ = v8.PITCH, v8.SQ
SEED = 467                                               # chosen by eye among the top-scoring seeds of 1-600

ART = (4, 5, 2, 3)                                       # along the plume: source, run, rise, dust
LOGO_XY = (20, 50)
URL = ["io.stigg.io", "/usage"]
SLOGAN = ["The AI Usage", "Management", "Console"]

T = dict(
    url_size=10.5, url_lead=13, url_track=-0.06,
    url_x=21, url_cap=141,                               # left ink edge, cap top (key 4)
    clear_mode="block", clear_margin=2,                  # knockout: the URL's ink box + margin
    slogan_size=9.5, slogan_lead=12, slogan_track=-0.06,
    slogan_align="right", slogan_x=292, slogan_cap=152,  # right: pen x is the exclusive right ink edge
)

P = dict(
    # each key's stretch of the arc, panel px, in flow order
    segs={4: [(44, 180), (60, 177), (80, 172)],
          5: [(128, 179), (148, 174), (164, 165), (175, 152), (181, 140)],
          2: [(152, 93), (157, 74), (166, 57), (180, 45), (193, 38)],
          3: [(237, 37), (255, 43), (271, 57), (285, 80)]},
    src=(1, 6, 5, 4),              # key 4 source block: a0, b0, cols, rows (one cell in from left and bottom)
    cut=((4, 0), (4, 3)),          # corners removed (relative a, b): top-right, bottom-right
    erode=0.5, erode_u0=0.6,       # pixelmark erosion of the source's right side (from u0 across the block)
    lam_n=9.0, up=15.0, aim=2.0,   # near field: blast from the source's right edge (decay px, direction deg, focus)
    fringe=0.6,                    # extra weight right against the source's right edge
    band_w=(6.0, 0.035), soft=0.45, lam_f=260.0, band_lo=0.25,
    band_k={4: 0.25, 5: 1.0, 2: 1.0, 3: 1.0},   # the band's share per key (key 4 is mostly the near field)
    # clusters at fixed panel points (key, x, y, sigma along, sigma across, amplitude)
    clusters=[(5, 142, 176, 11, 6, 0.9),     # key 5: where the run comes in, low
              (5, 170, 160, 11, 6, 0.8),     # key 5: where it turns up
              (2, 157, 78, 11, 7, 0.85),     # key 2: rising
              (2, 175, 48, 11, 7, 0.8),      # key 2: bending right
              (3, 252, 44, 12, 9, 0.7),      # key 3: where it arrives
              (3, 274, 66, 13, 10, 0.5)],    # key 3: where it lands
    jitter=4.0,
    target={4: 4, 5: 15, 2: 14, 3: 12},      # bright flying tokens per key (key 4: fragments + sparks)
    white={4: 0, 5: 6, 2: 9, 3: 8},          # white per key (the rest lime): none by the source, more further out
    white_base=0.15, white_pow=1.5, white_min_r=1.5, white_text_px=9,   # white leans to each key's far end
    depth={3: 3}, depth_from=0.80,
    min_w=0.03,
    gap0=1.0, gap1=0.4,
    spark_gap=1.5,                 # key 4 beyond the fragments: sparks keep 1.5 cells apart (no diagonal touching)
    fly_max=2,                     # at most this many eroded cells land as fragments next to the block
)

# name: (P overrides, T overrides, seed). Alternatives keep the final's tokens (placed against the final's URL
# clearing) unless they change the seed, so each one differs from the final in one thing only.
VARIANTS = {
    "final": ({}, {}, SEED),
    "url-9.5": ({}, {"url_size": 9.5, "url_lead": 12, "url_cap": 142}, SEED),   # one type size for both texts
    "seed-361": ({}, {}, 361),                                                 # the runner-up burst
}


# ---------------------------------------------------------------- geometry
def dims(k):
    return v8.BOARDS[k][2], v8.BOARDS[k][3]


def cells(k):
    return [(k, a, b) for (a, b) in v8.board_cells(k)]


def cxy(cell):
    k, a, b = cell
    x, y = v8.cell_px(k, a, b)
    return x + SQ / 2.0, y + SQ / 2.0


QUIET = {k: {(k, a, b) for (a, b) in v8.quiet(k)} for k in ART}
# Lime next to a tile edge bleeds colour outside the tile through JPEG's 16 x 16 chroma blocks (4:2:0): measured
# on the burned JPEG, key 5's lime in its last two inner columns tinted the window's right margin by 10 blue levels.
# In the columns whose chroma block straddles the right-hand tile edge of keys 2 and 5, tokens are white only.
CHROMA = {c_ for k in (2, 5) for c_ in {(k, a, b) for (a, b) in v8.quiet(k, n=16)} - QUIET[k]
          if c_[1] >= v8.BOARDS[k][2] - 3}


def ring(cell):
    k, a, b = cell
    nc, nr = dims(k)
    return a in (0, nc - 1) or b in (0, nr - 1)


def url_boxes(t):
    rel = v8.measure(URL, t["url_size"], t["url_track"], t["url_lead"])
    return [(t["url_x"], t["url_cap"] + y0, t["url_x"] + (x1 - x0), t["url_cap"] + y1) for (x0, y0, x1, y1) in rel]


def clearing(t):
    m = t["clear_margin"]
    boxes = url_boxes(t)
    if t["clear_mode"] in ("block", "band"):
        boxes = [v8.ink_box(boxes)]
    out = set()
    for c_ in cells(4):
        x, y = v8.cell_px(*c_)
        for (x0, y0, x1, y1) in boxes:
            if t["clear_mode"] == "band":
                x0, x1 = 0, W
            if x < x1 + m and x + SQ > x0 - m and y < y1 + m and y + SQ > y0 - m:
                out.add(c_)
    return out


def blocked(t, p=None):
    """Cells that never light: quiet cells, every art board's outer ring, the URL clearing and its ring,
    and the source block's cut corners (debris flies away from the block, it never squares it off)."""
    p = p or P
    out = set()
    a0, b0, nc, nr = p["src"]
    out |= {(4, a0 + a, b0 + b) for (a, b) in p["cut"]}
    for k in ART:
        out |= QUIET[k]
        out |= {c_ for c_ in cells(k) if ring(c_)}
    clr = clearing(t)
    out |= clr
    for (k, a, b) in clr:
        out |= {(k, a + da, b + db) for da in (-1, 0, 1) for db in (-1, 0, 1)}
    return out


# ---------------------------------------------------------------- spine
def catmull(points, n=60):
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


def spines(p):
    """{key: (poly, cum, s_offset)}; s runs along the whole arc, the bezel gaps counted as straight lines."""
    out, off, prev = {}, 0.0, None
    for k in ART:
        pts = p["segs"][k]
        if prev is not None:
            off += math.hypot(pts[0][0] - prev[0], pts[0][1] - prev[1])
        poly = catmull(pts)
        cum = [0.0]
        for a, b in zip(poly, poly[1:]):
            cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        out[k] = (poly, cum, off)
        off += cum[-1]
        prev = pts[-1]
    return out, off


def source_cells(p):
    a0, b0, nc, nr = p["src"]
    src = {(4, a0 + a, b0 + b) for a in range(nc) for b in range(nr)}
    for (a, b) in p["cut"]:
        src.discard((4, a0 + a, b0 + b))
    return src


# ---------------------------------------------------------------- rules
def _side_ok(cell, src):
    """Debris may touch the source only on its right (and over its right column), where the burst goes."""
    k, a, b = cell
    if k != 4:
        return True
    lo = min(y for (_, x, y) in src); hi = max(y for (_, x, y) in src)
    for (sk, sa, sb) in src:
        if max(abs(sa - a), abs(sb - b)) == 1:
            row_max = max(x for (_, x, y) in src if y == sb)
            if not (a > row_max or (a == row_max and b != sb)):
                return False
            if b > hi:
                return False
    return True


def row_ledge(marks, src, cell=None):
    """A source row run on by debris: more than one mark in the four cells after the row's right end."""
    rows = {}
    for (_, x, y) in src:
        rows[y] = max(rows.get(y, -1), x)
    for y, xm in rows.items():
        n = sum(1 for x in range(xm + 1, xm + 5) if (4, x, y) in marks or (4, x, y) == cell)
        if n > 1:
            return y
    return None


def violates(lit, src, cell, bright, r_src, blk):
    k, a, b = cell
    nc, nr = dims(k)
    if cell in blk:
        return "blocked"
    if k == 4 and row_ledge({c_ for c_ in lit if c_ not in src}, src, cell) is not None:
        return "row ledge"
    near_src = any((k, a + da, b + db) in src for da in (-1, 0, 1) for db in (-1, 0, 1))
    if near_src:
        if not bright:
            return "depth on the source"
        if not _side_ok(cell, src):
            return "debris off the burst side"
    marked = lambda c_: c_ == cell or (c_ in lit and c_ not in src)
    is_bright = lambda c_: (c_ == cell and bright) or (c_ in lit and c_ not in src and lit[c_] in BRIGHT)
    if r_src >= 1.0 and any(marked((k, a + da, b + db)) for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        return "pair"
    for da, db in ((1, 0), (0, 1)):
        run = 1
        for sgn in (1, -1):
            n = 1
            while marked((k, a + sgn * n * da, b + sgn * n * db)):
                run += 1; n += 1
        if run >= 3:
            return "run"
        on = lambda c_: c_ == cell or c_ in lit
        line = [cell]
        for sgn in (1, -1):
            n = 1
            while on((k, a + sgn * n * da, b + sgn * n * db)):
                line.append((k, a + sgn * n * da, b + sgn * n * db)); n += 1
        if any(c_ in src for c_ in line) and sum(1 for c_ in line if c_ not in src) >= 2:
            return "ledge"
        if bright and r_src >= 2.5:
            for o in range(-6, 1):
                if sum(1 for n in range(7) if is_bright((k, a + (o + n) * da, b + (o + n) * db))) >= 4:
                    return "dotted"
        if r_src >= 2.5:                                         # a short dotted row or column
            for o in range(-4, 1):
                if sum(1 for n in range(5) if marked((k, a + (o + n) * da, b + (o + n) * db))) >= 3:
                    return "dotted short"
    if bright and r_src >= 2.5:                                  # a dotted diagonal
        for da, db in ((1, 1), (1, -1)):
            for o in range(-6, 1):
                if sum(1 for n in range(7) if is_bright((k, a + (o + n) * da, b + (o + n) * db))) >= 4:
                    return "dotted diagonal"
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
    for d in (2,):                                               # four marks on the corners of a square
        for sa in (0, -d):
            for sb in (0, -d):
                if all(marked((k, a + sa + x, b + sb + y)) for x in (0, d) for y in (0, d)):
                    return "lattice square"
    if a in (0, nc - 1) and b in (0, nr - 1):
        return "corner"
    col = sum(1 for n in range(nr) if marked((k, a, n)))
    row = sum(1 for n in range(nc) if marked((k, n, b)))
    if (a in (0, nc - 1) and col > 2) or (b in (0, nr - 1) and row > 2):
        return "edge"
    if col > 3 or row > 3:
        return "row"
    return None


# ---------------------------------------------------------------- the burst
def field(seed, p, t):
    """Per-cell (s, q, r_src) and weight; the seed only jitters the clusters."""
    rnd = random.Random(seed)
    sp, S = spines(p)
    src = source_cells(p)
    erode_draws = [rnd.random() for _ in range(64)]
    clusters = []
    for (k, x, y, ss, sq, amp) in p["clusters"]:
        poly, cum, off = sp[k]
        s0, q0 = project(poly, cum, (x, y))
        clusters.append((k, off + s0 + rnd.uniform(-1, 1) * p["jitter"], q0 + rnd.uniform(-1, 1) * p["jitter"], ss, sq, amp))
    src_pts = [cxy(c_) for c_ in src]
    xs = [v8.cell_px(*c_)[0] for c_ in src]; ys = [v8.cell_px(*c_)[1] for c_ in src]
    px0 = max(xs) + SQ; py0 = (min(ys) + max(ys) + SQ) / 2.0
    th0 = math.radians(p["up"])
    info, weight = {}, {}
    for k in ART:
        poly, cum, off = sp[k]
        for c_ in cells(k):
            if c_ in src:
                continue
            x_, y_ = cxy(c_)
            sl, q = project(poly, cum, (x_, y_))
            s = off + sl
            r = min(math.hypot(x_ - x, y_ - y) for x, y in src_pts) - PITCH
            info[c_] = (s, q, r / PITCH)
            near = 0.0
            if k == 4:
                dd = math.hypot(x_ - px0, y_ - py0)
                th = math.atan2(-(y_ - py0), x_ - px0)
                near = math.exp(-dd / p["lam_n"]) * (0.08 + 0.92 * max(0.0, math.cos(th - th0)) ** p["aim"])
                _, a, b = c_
                if any((4, a - 1, b + db) in src for db in (-1, 0, 1)):
                    near += p["fringe"]
            w = p["band_w"][0] + p["band_w"][1] * s
            env = 1.0 / (1.0 + math.exp((abs(q) - w) / (p["soft"] * w)))
            cl = sum(amp * math.exp(-((s - s0) / ss) ** 2 / 2 - ((q - q0) / sq) ** 2 / 2)
                     for kk, s0, q0, ss, sq, amp in clusters if kk == k)
            band = p["band_lo"] * p["band_k"][k] * math.exp(-s / p["lam_f"]) * env
            weight[c_] = near + band + cl
    return src, info, weight, S, erode_draws, rnd


def plume(seed, p, t):
    src, info, weight, S, erode_draws, rnd = field(seed, p, t)
    a0, b0, nc, nr = p["src"]
    blk = blocked(t, p)
    lit = {}
    # 1. erosion: the source's right columns break off (pixelmark: u > u0 erodes; pixelmark's u0 is 0.5, 0.6
    #    here because the block is only five cells wide), a little more at the top
    for n, (k, a, b) in enumerate(sorted(src, key=lambda c_: (c_[2], c_[1]))):
        u = (a - a0 + 1) / nc
        v = (b0 + nr - b) / nr
        u0 = p["erode_u0"]
        if erode_draws[n] >= p["erode"] * max(0.0, (u - u0) / (1.0 - u0)) ** 1.6 * (0.45 + 0.55 * v):
            lit[(k, a, b)] = LIME

    def es_order(cs, wfun, r=rnd):
        return sorted(cs, key=lambda c_: -(r.random() ** (1.0 / max(wfun(c_), 1e-9))))

    rnd_colour = {k: random.Random(seed * 7919 + 17 * k) for k in ART}
    rnd_depth = {k: random.Random(seed * 104729 + 3 * k) for k in ART}
    rnd_fly = random.Random(seed * 3571 + 11)
    wmax = {k: max(weight[c_] for c_ in weight if c_[0] == k and c_ not in blk) for k in ART}
    # 2a. flying fragments (pixelmark): each eroded source cell lands a little to the right of where it was,
    #     just past the block's edge in its own row or the next, if the rules allow it
    rows_end = {}
    for (_, x, y) in src:
        rows_end[y] = max(rows_end.get(y, -1), x)
    flown = 0
    for (k, a, b) in sorted(src - set(lit), key=lambda c_: (c_[2], c_[1])):
        if flown >= p["fly_max"]:
            break
        tries = []
        for _ in range(6):
            dx = 1
            r_ = rnd_fly.random()
            dy = -1 if r_ < 0.3 else (1 if r_ > 0.75 else 0)
            yb = min(max(b + dy, b0), b0 + nr - 1)
            tries.append((4, rows_end[yb] + dx, yb))
        for c_ in tries:
            if c_ in lit or c_ in src or c_ not in info:
                continue
            if violates(lit, src, c_, True, info[c_][2], blk):
                continue
            lit[c_] = LIME
            flown += 1
            break
    # 2b. bright tokens, exact counts per key (key 4's count includes the flying fragments)
    for k in ART:
        placed = flown if k == 4 else 0
        cand = [c_ for c_ in weight if c_[0] == k and c_ not in blk and c_ not in lit
                and weight[c_] >= p["min_w"] * wmax[k]]
        for c_ in es_order(cand, lambda c_: weight[c_]):
            if placed >= p["target"][k]:
                break
            g = p["gap0"] + p["gap1"] * info[c_][0] / S
            if k == 4 and info[c_][2] >= 1.0:
                g = max(g, p["spark_gap"])
            rr = int(math.ceil(g))
            _, a, b = c_
            if any((k, a + da, b + db) in lit and (k, a + da, b + db) not in src
                   for da in range(-rr, rr + 1) for db in range(-rr, rr + 1)
                   if (da or db) and da * da + db * db < g * g):
                continue
            if k == 4 and any((4, a + da, b + db) in lit and (4, a + da, b + db) not in src
                              and max(info[c_][2], info[(4, a + da, b + db)][2]) >= 1.0
                              for da in (-1, 1) for db in (-1, 1)):
                continue                                         # a spark never touches anything
            if c_ in CHROMA and sum(1 for x in lit if x in CHROMA and x[0] == k) >= p["white"][k]:
                continue                                         # there would not be enough whites for them
            if violates(lit, src, c_, True, info[c_][2], blk):
                continue
            lit[c_] = LIME
            placed += 1
    # 3. colour: an exact number of whites per key, leaning to the far end, never next to the source or the URL
    ubox = v8.ink_box(url_boxes(t))

    def far_from_text(c_):
        x, y = v8.cell_px(*c_)
        dx = max(ubox[0] - (x + SQ), x - ubox[2], 0); dy = max(ubox[1] - (y + SQ), y - ubox[3], 0)
        return c_[0] != 4 or math.hypot(dx, dy) >= p["white_text_px"]
    for k in ART:
        cand = [c_ for c_ in lit if c_[0] == k and c_ not in src and info[c_][2] >= p["white_min_r"] and far_from_text(c_)]
        if not cand:
            continue
        s_lo = min(info[c_][0] for c_ in cand); s_hi = max(info[c_][0] for c_ in cand)
        lean = lambda c_: p["white_base"] + ((info[c_][0] - s_lo) / max(1e-9, s_hi - s_lo)) ** p["white_pow"]
        forced = [c_ for c_ in cand if c_ in CHROMA]
        rest = [c_ for c_ in es_order(cand, lean, rnd_colour[k]) if c_ not in CHROMA]
        for c_ in (forced + rest)[:p["white"][k]]:
            lit[c_] = WHITE
    # 4. depth: a few dim tokens at the far end of the dust
    for k, want in p["depth"].items():
        placed = 0
        far = [c_ for c_ in weight if c_[0] == k and c_ not in lit and c_ not in blk and c_ not in CHROMA
               and info[c_][0] >= p["depth_from"] * S and weight[c_] >= p["min_w"] * wmax[k]]
        for c_ in es_order(far, lambda c_: weight[c_], rnd_depth[k]):
            if placed >= want:
                break
            if violates(lit, src, c_, False, info[c_][2], blk):
                continue
            lit[c_] = DEPTH
            placed += 1
    return lit, src, info, weight, wmax, S


# ---------------------------------------------------------------- checks on the art (mirror the rules)
def art_checks(lit, src, info, weight, wmax, p, t):
    fails = []
    blk = blocked(t, p)
    marks = {c_ for c_ in lit if c_ not in src}
    if row_ledge(marks, src) is not None:
        fails.append("debris runs on source row %s" % row_ledge(marks, src))
    bright = {c_ for c_ in marks if lit[c_] in BRIGHT}
    n = {k: sum(1 for c_ in bright if c_[0] == k) for k in ART}
    if any(n[k] != p["target"][k] for k in ART):
        fails.append("counts %s (wanted %s)" % (n, p["target"]))
    if not (n[5] >= n[2] > n[3] >= 10):
        fails.append("density does not fall along the plume: %s" % n)
    for k in ART:
        fl = [c_ for c_ in bright if c_[0] == k]
        if fl and sum(1 for c_ in fl if lit[c_] == LIME) * 3 < len(fl):
            fails.append("key %d: less than a third lime" % k)
    for c_ in marks:
        if c_ in blk:
            fails.append("lit blocked cell %s" % (c_,))
        if c_ in CHROMA and lit[c_] != WHITE:
            fails.append("colour by the tile edge (chroma block) %s" % (c_,))
        if weight.get(c_, 0) < p["min_w"] * wmax[c_[0]]:
            fails.append("stray %s" % (c_,))
    for (k, a, b) in marks:
        for da, db in ((1, 0), (0, 1)):
            if (k, a + da, b + db) in marks and (k, a + 2 * da, b + 2 * db) in marks:
                fails.append("straight run of 3 at %s" % ((k, a, b),))
        for da, db in ((1, 1), (1, -1)):
            if (k, a + da, b + db) in marks and (k, a + 2 * da, b + 2 * db) in marks:
                fails.append("diagonal of 3 at %s" % ((k, a, b),))
        if (k, a, b) in bright:
            for x0 in range(a - 2, a + 1):
                for y0 in range(b - 2, b + 1):
                    if sum(1 for x in range(3) for y in range(3) if (k, x0 + x, y0 + y) in bright) > 4:
                        fails.append("clump near %s" % ((k, a, b),))
            if info[(k, a, b)][2] >= 2.5:
                for da, db in ((1, 0), (0, 1), (1, 1), (1, -1)):
                    for o in range(-6, 1):
                        if sum(1 for m_ in range(7) if (k, a + (o + m_) * da, b + (o + m_) * db) in bright) >= 4:
                            fails.append("dotted line at %s" % ((k, a, b),))
        if info[(k, a, b)][2] >= 2.5:
            for da, db in ((1, 0), (0, 1)):
                if sum(1 for m_ in range(5) if (k, a + m_ * da, b + m_ * db) in marks) >= 3:
                    fails.append("short dotted row or column at %s" % ((k, a, b),))
        if info[(k, a, b)][2] >= 1.0 and any((k, a + x, b + y) in marks for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            fails.append("side-by-side pair at %s" % ((k, a, b),))
    for (k, a, b) in marks:
        if all((k, a + x, b + y) in marks for x in (0, 2) for y in (0, 2)):
            fails.append("lattice square at %s" % ((k, a, b),))
        if k == 4 and (k, a, b) in bright:
            if any((k, a + x, b + y) in bright and max(info[(k, a, b)][2], info[(k, a + x, b + y)][2]) >= 1.0
                   for x in (-1, 1) for y in (-1, 1)):
                fails.append("key 4 spark touching at %s" % ((k, a, b),))
    for c_ in [c_ for c_ in src if c_ in lit]:
        k, a, b = c_
        for da, db in ((1, 0), (0, 1)):
            run = [c_]
            for sgn in (1, -1):
                m_ = 1
                while (k, a + sgn * m_ * da, b + sgn * m_ * db) in lit:
                    run.append((k, a + sgn * m_ * da, b + sgn * m_ * db)); m_ += 1
            if sum(1 for x in run if x not in src) >= 2:
                fails.append("ledge at %s" % (c_,))
    for k in ART:
        nc, nr = dims(k)
        for m_ in range(nc):
            col = sum(1 for y in range(nr) if (k, m_, y) in marks)
            if col > 3 or (m_ in (0, nc - 1) and col > 2):
                fails.append("column of marks, key %d" % k)
        for m_ in range(nr):
            row = sum(1 for x in range(nc) if (k, x, m_) in marks)
            if row > 3 or (m_ in (0, nr - 1) and row > 2):
                fails.append("row of marks, key %d" % k)
        if any((k, a, b) in marks for a in (0, nc - 1) for b in (0, nr - 1)):
            fails.append("corner, key %d" % k)
    for c_ in marks:
        k, a, b = c_
        if any((k, a + x, b + y) in src for x in (-1, 0, 1) for y in (-1, 0, 1)):
            if lit[c_] == DEPTH or not _side_ok(c_, src):
                fails.append("mark against the source off the burst side, or depth on it: %s" % (c_,))
    nl = sum(1 for v in lit.values() if v == LIME); nw = sum(1 for v in lit.values() if v == WHITE)
    wf = nw / max(1, nl + nw)
    if not (0.34 <= wf <= 0.44):
        fails.append("white %.2f" % wf)
    return sorted(set(fails)), n, wf


# ---------------------------------------------------------------- seed metrics
def elongation(cs):
    pts = [cxy(c_) for c_ in cs]
    if len(pts) < 3:
        return 0.0, 0.0
    mx = sum(p[0] for p in pts) / len(pts); my = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0] - mx) ** 2 for p in pts); syy = sum((p[1] - my) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    tr, det = sxx + syy, sxx * syy - sxy * sxy
    l1 = tr / 2 + math.sqrt(max(0.0, tr * tr / 4 - det)); l2 = tr / 2 - math.sqrt(max(0.0, tr * tr / 4 - det))
    ang = math.degrees(math.atan2(-(l1 - sxx), sxy)) if sxy else (0.0 if sxx >= syy else 90.0)
    return round(ang % 180.0, 1), round(math.sqrt(l1 / max(l2, 1e-9)), 2)


def seed_score(lit, info, p):
    """Higher is better: bright tokens hug their key's spine (mean |q| small), each key's plume is
    elongated along its spine's chord, the source stays solid and sheds a few fragments on its right."""
    sp, S = spines(p)
    src = source_cells(p)
    kept = sum(1 for c_ in src if c_ in lit)
    frag = sum(1 for c_ in lit if c_[0] == 4 and c_ not in src and info[c_][2] < 1.0)
    score, parts = 0.4 * min(kept, len(src) - 1) + 0.5 * min(frag, 3), {"src": kept, "frag": frag}
    for k in (5, 2, 3):
        fl = [c_ for c_ in lit if c_[0] == k and lit[c_] in BRIGHT]
        ang, el = elongation(fl)
        (x0, y0), (x1, y1) = p["segs"][k][0], p["segs"][k][-1]
        want = math.degrees(math.atan2(-(y1 - y0), x1 - x0)) % 180.0
        dang = min(abs(ang - want), 180 - abs(ang - want))
        mq = sum(abs(info[c_][1]) for c_ in fl) / max(1, len(fl))
        parts[k] = (round(dang, 1), el, round(mq, 1))
        score += el * math.cos(math.radians(min(dang, 90))) - 0.05 * mq
    # aligned triples read as drawn lines: 3 marks in one row, column or diagonal within 5 cells
    marks = [c_ for c_ in lit if c_ not in src]
    ms = set(marks)
    tri = 0
    for (k, a, b) in marks:
        for da, db in ((1, 0), (0, 1), (1, 1), (1, -1)):
            for j in range(1, 4):
                for i in range(j + 1, 5):
                    if (k, a + j * da, b + j * db) in ms and (k, a + i * da, b + i * db) in ms:
                        tri += 1
    parts["triples"] = tri
    score -= 0.35 * tri
    # chevrons chained into a zig-zag read as a pattern: (a, b), (a +- 1, b + 1), (a, b + 2) and the row version
    chev = 0
    for (k, a, b) in marks:
        for d in (1, -1):
            if (k, a + d, b + 1) in ms and (k, a, b + 2) in ms:
                chev += 1
            if (k, a + 1, b + d) in ms and (k, a + 2, b) in ms:
                chev += 1
    parts["chevrons"] = chev
    score -= 0.25 * chev
    return round(score, 3), parts


# ---------------------------------------------------------------- compose
def compose(seed, p, t, t_art=None):
    """t draws the type; t_art (default t) is the layout the tokens are placed against."""
    t_art = t_art or t
    img = Image.new("RGB", (W, H), INK)
    lit, src, info, weight, wmax, S = plume(seed, p, t_art)
    clr = clearing(t)
    for k in ART:
        v8.draw_board(img, k, {(a, b): col for (kk, a, b), col in lit.items() if kk == k},
                      skip={(a, b) for (kk, a, b) in clr if kk == k})
    logo_box = v8.logo(img, LOGO_XY)
    url_ink = v8.text(img, t["url_x"], t["url_cap"], URL, t["url_size"], t["url_track"], t["url_lead"], "left")
    slo_ink = v8.text(img, t["slogan_x"], t["slogan_cap"], SLOGAN, t["slogan_size"], t["slogan_track"],
                      t["slogan_lead"], t["slogan_align"])
    fails, n, wf = art_checks(lit, src, info, weight, wmax, p, t_art)
    if any(c_ in lit for c_ in clr) or any(c_ in lit and c_ not in src for c_ in blocked(t, p)):
        fails.append("a lit token in this layout's URL clearing or its ring")

    def block(boxes, key):
        b = v8.ink_box(boxes)
        return {"ink": [b[0], b[1], b[2] - 1, b[3] - 1], "centre_offset_vs_window": list(v8.centre_offset(b, key))}

    def mass(boxes, key):
        """Ink-width-weighted centre of the lines (where the block's visual mass sits)."""
        wsum = sum(b[2] - b[0] for b in boxes)
        mx = sum((b[2] - b[0]) * (b[0] + b[2]) / 2.0 for b in boxes) / wsum
        return round(mx - v8.window_centre(key)[0], 1)

    tokens = {}
    for k in ART:
        cs = cells(k)
        fl = [c_ for c_ in cs if lit.get(c_) in BRIGHT and c_ not in src]
        tokens["key%d" % k] = {
            "lime": sum(1 for c_ in fl if lit[c_] == LIME), "white": sum(1 for c_ in fl if lit[c_] == WHITE),
            "source_lime": sum(1 for c_ in cs if c_ in src and c_ in lit),
            "depth_639840": sum(1 for c_ in cs if lit.get(c_) == DEPTH),
            "knocked_out": sum(1 for c_ in cs if c_ in clr),
            "unlit_2C2F2B": sum(1 for c_ in cs if c_ not in lit and c_ not in clr),
            "bright_axis_deg_elongation": elongation(fl)}
    boards = {"key%d" % k: {"board": v8.BOARDS[k], "px": v8.board_px(k), "centre_offset_vs_window": v8.board_offset(k)}
              for k in ART}
    a0, b0, nc, nr = p["src"]
    sx0, sy0 = v8.cell_px(4, a0, b0)
    meta = {
        "version": "v8/b-url-is-source", "seed": seed,
        "layout": {"key1": "logo", "key2": "art: the rise", "key3": "art: the dust", "key4": "URL + source block",
                   "key5": "art: the run (the plume's lower stretch)", "key6": "slogan"},
        "logo": {"xy": list(LOGO_XY), "box": logo_box, "centre_offset_vs_window": list(v8.centre_offset(logo_box, 1))},
        "url": dict(size=t["url_size"], leading=t["url_lead"], track=t["url_track"], align="left", pen_x=t["url_x"],
                    cap_top=t["url_cap"], line_ink=url_ink, clearing=t["clear_mode"], margin_px=t["clear_margin"],
                    **block(url_ink, 4)),
        "slogan": dict(size=t["slogan_size"], leading=t["slogan_lead"], track=t["slogan_track"], align=t["slogan_align"],
                       pen_x=t["slogan_x"], cap_top=t["slogan_cap"], line_ink=slo_ink,
                       mass_x_offset_vs_window=mass(slo_ink, 6), **block(slo_ink, 6)),
        "source": {"cells_a_b_cols_rows": p["src"], "px": [sx0, sy0, sx0 + PITCH * nc - 3, sy0 + PITCH * nr - 3],
                   "lit_cells": sum(1 for c_ in src if c_ in lit)},
        "boards": boards, "tokens": tokens,
        "bright_total": sum(1 for v in lit.values() if v in BRIGHT), "white_share_of_bright": round(wf, 3),
        "art_fails": fails, "seed_score": seed_score(lit, info, p),
    }
    return img, meta


def variant(name):
    po, to, seed = VARIANTS[name]
    p = copy.deepcopy(P); p.update(copy.deepcopy(po))
    t = dict(T); t.update(to)
    return p, t, seed


def burn_check(img):
    """The hard rules' JPEG half, without writing files: bytes, luma halo (count > 4, worst), colour halo."""
    data = v8.c.v6.jpeg(img, v8.c.QUALITY)
    seen = v8.c.v6.decode_box(data)
    cnt, worst = v8.c.v6.halo(seen)
    rgb, _ = v8.rgb_halo(seen)
    return len(data), cnt, worst, rgb


def search(n_seeds, p, t, rgb_max=8):
    """Seeds 1..n that pass every art rule and the hard rules with a margin (colour halo <= rgb_max, two
    levels under v8_common's limit of 10), best score first."""
    ok = []
    for s in range(1, n_seeds + 1):
        lit, src, info, weight, wmax, S = plume(s, p, t)
        fails, n, wf = art_checks(lit, src, info, weight, wmax, p, t)
        if fails:
            continue
        img, meta = compose(s, p, t)
        nbytes, cnt, worst, rgb = burn_check(img)
        if cnt or max(rgb) > rgb_max or nbytes > v8.c.MAX_JPEG:
            continue
        sc, parts = seed_score(lit, info, p)
        ok.append((sc, s, parts, round(wf, 3), worst, rgb, nbytes))
    ok.sort(key=lambda o: (-o[0], o[1]))
    return ok


def run(seed, out, p, t, verbose=True, t_art=None):
    img, meta = compose(seed, p, t, t_art)
    checks = v8.render(img, out, extra={"layout": meta})
    if verbose:
        print(json.dumps({k: v for k, v in checks.items() if k != "layout"}, indent=1, default=str))
        print(json.dumps(meta, indent=1, default=str))
    return checks, meta


def verdict(name, checks, meta):
    bad = []
    if not checks["hard_rules_pass"]:
        bad.append("%s: hard rules fail" % name)
    if meta["art_fails"]:
        bad.append("%s: art rules fail: %s" % (name, meta["art_fails"]))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--variant", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--search", type=int, default=0)
    a = ap.parse_args()
    if a.search:
        p, t, _ = variant(a.variant or "final")
        ok = search(a.search, p, t)
        print(len(ok), "of", a.search, "seeds pass every art rule and the hard rules with a margin; best score first")
        for o in ok[:30]:
            print(o)
        return
    names = [a.variant] if a.variant else list(VARIANTS)
    bad = []
    _, t_final, _ = variant("final")
    for name in names:
        p, t, seed = variant(name)
        seed = a.seed if a.seed is not None else seed
        out = a.out or (HERE if name == "final" else os.path.join(HERE, "alt-" + name))
        print("==== %s (seed %d) -> %s" % (name, seed, out))
        checks, meta = run(seed, out, p, t, verbose=(name == "final"), t_art=t_final)
        if name != "final":
            print(json.dumps({k: v for k, v in checks.items() if k != "layout"}, default=str))
            print(json.dumps({"art_fails": meta["art_fails"], "url": meta["url"]["ink"], "tokens": meta["tokens"]},
                             default=str))
        bad += verdict(name, checks, meta)
    if bad:
        raise SystemExit("; ".join(bad))


if __name__ == "__main__":
    main()
