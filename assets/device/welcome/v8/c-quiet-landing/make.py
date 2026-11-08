#!/usr/bin/env python3
"""Token Deck welcome v8, candidate c-quiet-landing: v7's burst, a quiet landing in key 4. Own code.

Answers Gabriel's notes on v7 (BRIEF.md): tokens in the URL's key, boards that fill each window, URL
bottom left and slogan bottom right. Imports v8_common only (boards, quiet cells, type, logo, render).

Layout   key 1 logo   | key 2 the plume    | key 3 the dust
         key 4 URL    | key 5 the source   | key 6 slogan
Key 4    The URL on a full 12 x 11 board (the same footprint as keys 2, 3 and 5), with a window cut in it:
         cells a1-a10 x b2-b8 (every cell within 4 px of the URL's ink) are not drawn, so the URL sits on
         clean #131512 with 4 px of air to the frame's side columns and 7 px above and below. Three tokens
         have landed: two lime on the floor row (b9, columns a6-a10, under the gap the short '/usage' line
         leaves) and one white still in the air (b1, columns a3-a8), never touching, never sharing a column.
         The flush-left URL is left-heavy (its ink mass is 2.6 px left of the window centre); the landed
         tokens sit where it is light and bring the key's mass to 1.4 px. Not part of the burst: own stream.
Type     Soehne Buch through v8_common.text, white, tracking -0.06 px. URL 10.5 px / 13 px leading, flush
         left, pen x 28, cap top 156: ink x 28-71, y 156-178, centred on the board (and window 4) to 0.5 px.
         Slogan 9.5 px / 12 px, flush right on x 291 (the tile's last column), cap top 152: ink x 235-291,
         y 152-182; its box is 3.5 px left of window 6's centre (the tile ends there), its ink mass 1.0 px
         (the short 'Console' sits right). Cap top 153 rings 5.0 luma at x 292; 152 rings 3.2.
         alt/: the URL at 9.5 px / 12 px too (pen x 30, cap top 157, ink x 30-69, y 157-177).
Tokens   3 px squares on each key's own 5 px lattice (v8_common.BOARDS, 13 rows in keys 2 and 3). Every cell
         an unlit #2C2F2B token unless lit; lime #92E759, white #FFFFFF, three #639840 depth tokens in key 3.
         No lit token on any board's outer ring (the keycap bevel mirrors it; v8_common.quiet() cells are
         all on it), and a lighter weight on the next ring where the flow does not cross a bezel.
Burst    v7's generator per key: a lime source block (key 5, a1-a4 x b4-b9, rounded corners) erodes only in
         its top half; debris breaks off its top-right corner only (a near-field blast at 58 degrees with
         little off-axis spray, fragments against the block only in its top two rows), rises through key 2
         on a diagonal, bends right into key 3 and drifts down as dust. Density is a designed field (near
         field + a band along a curved spine + four clusters); the seed decides cells. Exact counts per key
         by weighted sampling without replacement: debris 11 / 19 / 14, white 4 / 11 / 9.
Rules    Enforced while placing and re-checked afterwards (art_checks): no 3 marks in a straight row or
         column; no diagonal staircase of 3; no 4 bright within 7 cells of a row or column; v8: no 3 marks
         within 5 cells of a row or column (the lattice packs a dense plume into ruled X.X.X lines) beyond
         the near field; no 3 x 3 window with more than 4 bright; nothing lit on an outer ring (so no lit
         corner and no marks along an edge); at most 3 marks per row or column; a third of every key's
         flying tokens lime; white 0.34-0.44 of all bright; side-by-side pairs only within the debris (v8:
         refused when EITHER token is beyond it; v7 looked only at the new one); no ledges; depth never on
         the source; no stray (every burst mark has company within 3.2 cells); nothing in the URL's window.
         Hard rules: v8_common.render (hard_rules_pass).

usage: make.py                      render seed SEED here and alt/ (URL at 9.5 px), print the checks
       make.py --seed N [--type main|alt] [--out DIR] [--shape frame|band|hug]
       make.py --search N           list seeds 1..N that pass every art rule
"""
import sys
sys.dont_write_bytecode = True                      # never drop .pyc files next to the shared modules
import argparse, itertools, json, math, os, random   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WELCOME = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WELCOME)
import v8_common as v8                              # noqa: E402
from PIL import Image, ImageDraw                    # noqa: E402

c = v8.c
W, H = v8.W, v8.H
INK, LIME, WHITE, UNLIT, MID_LIME = v8.INK, v8.LIME, v8.WHITE, v8.UNLIT, v8.MID_LIME
BRIGHT = (LIME, WHITE)
PITCH, SQ = v8.PITCH, v8.SQ
BOARDS = v8.BOARDS
ART = (5, 2, 3)                                     # the burst: source in 5, plume in 2, dust in 3
SEED = 995                                          # chosen by eye among seeds 1-1000 that pass every rule

URL = ["io.stigg.io", "/usage"]
SLOGAN = ["The AI Usage", "Management", "Console"]
TRACK = -0.06
TYPE = {"main": {"url": (10.5, 13), "slogan": (9.5, 12)},
        "alt": {"url": (9.5, 12), "slogan": (9.5, 12)}}
SLOGAN_RIGHT = 292                                  # exclusive: every slogan line ends on x 291, the tile's last column
SLOGAN_CAP = 152
CLEAR_MARGIN = 4                                    # px: board cells this close to the URL's ink are not drawn


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


QUIET = set()
for _k in BOARDS:
    QUIET |= {(_k, a, b) for (a, b) in v8.quiet(_k)}


# ---------------------------------------------------------------- key 4: the URL's clearing
def url_place(size, lead):
    """Pen x (left ink edge) and cap top that centre the URL's ink box on key 4's board (the board is
    centred on window 4 to 0.5 px), and the expected ink box (exclusive right / bottom)."""
    boxes = v8.measure(URL, size, TRACK, lead)
    w = max(b[2] - b[0] for b in boxes)
    h = boxes[-1][3] - boxes[0][1]
    x0, y0, x1, y1 = v8.board_px(4)
    bcx, bcy = (x0 + x1 + 1) / 2.0, (y0 + y1 + 1) / 2.0
    pen = int(math.floor(bcx - w / 2.0 + 0.5))
    top = int(math.floor(bcy - h / 2.0 + 0.5))
    return pen, top - boxes[0][1], (pen, top, pen + w, top + h), [
        (pen, top + b[1] - boxes[0][1], pen + (b[2] - b[0]), top + b[3] - boxes[0][1]) for b in boxes]


def clearing(box, lines, shape="frame", m=CLEAR_MARGIN):
    """Key 4 cells not drawn at all, so the URL sits on clean #131512. frame: every cell within m px of
    the URL's ink box (the board stays a frame around it); band: those rows across the whole board;
    hug: within m px of each line's own ink box (tokens fill in beside the short second line)."""
    def near(bx, cell):
        x, y = cpx(cell)
        return x + SQ - 1 >= bx[0] - m and x <= bx[2] - 1 + m and y + SQ - 1 >= bx[1] - m and y <= bx[3] - 1 + m
    if shape == "hug":
        out = {cl for cl in key_cells(4) if any(near(lb, cl) for lb in lines)}
    else:
        out = {cl for cl in key_cells(4) if near(box, cl)}
    if shape == "band":
        rows = {b for (_, _, b) in out}
        out |= {cl for cl in key_cells(4) if cl[2] in rows}
    return out


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
    spine=[(156, 160), (160, 122), (164, 78), (190, 48), (250, 48), (274, 66), (292, 86)],
    src=(1, 4, 4, 6),              # key 5 source block: a0, b0, cols, rows (one cell in from the lower-left corner)
    erode=0.65,                    # pixelmark erosion of the source's right side and top ...
    erode_v=3.0, erode_vmin=0.5,   # ... at the top only (v7: 0.3 + 0.7 v, which notched the lower right side)
    lam_n=13.0, up=58.0, aim=2.5,  # near field: blast from the source's top-right corner ...
    near_floor=0.02,               # ... with little off-axis spray (v7 0.08 put debris over the block's left side)
    fringe=0.35, fringe_fall=1.5,  # fragments against the source: strongest at its top-right corner, where the burst goes
    band_w=(7.0, 0.07), soft=0.45, lam_f=170.0, band_lo=0.18,
    clusters=[(163, 74, 13, 6, 1.0),       # key 2: where the plume comes up through the bezel
              (177, 45, 11, 6, 0.85),      # key 2: where it bends right
              (256, 48, 12, 8, 0.8),       # key 3: where it arrives
              (274, 70, 12, 8, 0.6)],      # key 3: where it settles
    jitter=5.0,
    target={5: 11, 2: 19, 3: 14},  # bright flying tokens per key (v7: 11 / 17 / 13; keys 2 and 3 are bigger boards now)
    white={5: 4, 2: 11, 3: 9},     # white leans to the far end; at least a third of every key's flying tokens stay lime
    white_base=0.30, white_min_r=1.5,
    depth={3: 3}, depth_from=0.62,
    # weight on the ring just inside the dark outer ring, per side, where the flow does not cross a bezel
    # (fewer bright reflections in the keycap bevel; the burst stays whole across 5 -> 2 -> 3)
    inner={2: {"top": 0.6, "left": 0.6}, 3: {"top": 0.6, "right": 0.6, "bottom": 0.6},
           5: {"right": 0.6}},
    min_w=0.03,
    gap0=1.0, gap1=0.35,
)

L4 = dict(quota={9: 2, 1: 1},     # settled tokens per row: two landed on the floor (b9), one above (b1)
          white_rows=(1,),         # the one still in the air is white; the landed ones are lime
          depth=0,
          gap=3.0,                 # min distance between settled tokens (cells): calm, never touching
          colgap=2,                # tokens on the two strips never share or neighbour a column
          cols={9: (6, 10),        # the landed pair: under the end of the URL, right of the window centre
                1: (3, 8)},        # the airborne one: over the URL's middle, never over its first letters
          lean={9: 0.0, 1: 0.0},   # horizontal lean per row (>0 right)
          focus={1: 2.5})          # the airborne one stays over the middle of the URL (sigma, cells)


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


def violates(lit, src, cell, bright, r_src, rmap=None):
    """The reason marking `cell` would read as a mistake, or None. Source cells never count as marks.
    rmap gives every cell's distance from the source (cells): a side-by-side pair is refused when EITHER
    token is beyond the debris (v7 only looked at the new one, so a later check could still fail)."""
    k, a, b = cell
    nc, nr = dims(k)
    if cell in QUIET:
        return "quiet"
    if on_ring(cell):
        return "ring"                                            # the bevel mirrors the outer ring
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
        # v8: at most 2 marks in any 5 consecutive cells of a row or column (X.X.X reads as a ruled line;
        # the lattice packs a dense plume into exactly that), unless every one of them is in the near field
        for o in range(-4, 1):
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
    """One seeded burst: {cell: colour}, the source cells, per-cell info, spine length, weights."""
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
        x = rnd.random()                                         # one draw per cell, eroded or not
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
        if on_ring(cell) or cell in QUIET:
            continue
        cx, cy = centre(cell)
        dd = math.hypot(cx - px0, cy - py0)
        th = math.atan2(-(cy - py0), cx - px0)
        near = math.exp(-dd / p["lam_n"]) * (p["near_floor"] + (1 - p["near_floor"]) * max(0.0, math.cos(th - th0)) ** p["aim"])
        if k == 5 and (5, a - 1, b) in src and a > sa_max - 1:   # against the right side: strongest at the top
            near += p["fringe"] * math.exp(-(b - sb_min) / p["fringe_fall"])
        elif k == 5 and (5, a, b + 1) in src and b < sb_min + 1:  # on the top edge: strongest at the right
            near += p["fringe"] * math.exp(-(sa_max - a) / p["fringe_fall"])
        w = p["band_w"][0] + p["band_w"][1] * s
        env = 1.0 / (1.0 + math.exp((abs(q) - w) / (p["soft"] * w)))
        cl = sum(amp * math.exp(-((s - s0) / ss) ** 2 / 2 - ((q - q0) / sq) ** 2 / 2) for s0, q0, ss, sq, amp in clusters)
        band = p["band_lo"] * math.exp(-s / p["lam_f"]) * env
        knc, knr = dims(k)
        side = p["inner"].get(k, {})
        f = 1.0
        for name, hit in (("top", b == 1), ("bottom", b == knr - 2), ("left", a == 1), ("right", a == knc - 2)):
            if hit:
                f = min(f, side.get(name, 1.0))
        weight[cell] = (near + band + cl) * f
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
            if violates(lit, src, cell, True, info[cell][2], rmap):
                continue
            lit[cell] = LIME
            placed += 1
    for k in ART:                                                # 5. white: exact count, leaning to the far end
        cand = [c_ for c_ in lit if c_[0] == k and c_ not in src and info[c_][2] >= p["white_min_r"]]
        for c_ in es_order(cand, lambda c_: p["white_base"] + info[c_][0] / S, rnd_colour[k])[:p["white"][k]]:
            lit[c_] = WHITE
    for k, want in p["depth"].items():                           # 6. depth: dim tokens at the far end
        placed = 0
        far = [c_ for c_ in weight if c_[0] == k and c_ not in lit and info[c_][0] >= p["depth_from"] * S]
        for c_ in es_order(far, lambda c_: weight[c_], rnd_depth[k]):
            if placed >= want:
                break
            if c_ in lit or violates(lit, src, c_, False, info[c_][2], rmap):
                continue
            lit[c_] = MID_LIME
            placed += 1
    return lit, src, info, S, weight


# ---------------------------------------------------------------- key 4: the quiet landing
def landing(seed, clear, l=L4, lit=None):
    """A handful of settled tokens on key 4's board, outside the URL's clearing: well apart (calm, never
    touching), the floor first, seeded on their own stream. Each row's set is drawn whole from every set
    that keeps the rules (weighted by the product of its cells' weights), so a quota is never missed."""
    rnd = random.Random(seed * 31337 + 4)
    out = dict(lit or {})
    nc, nr = dims(4)
    placed = []
    for row in sorted(l["quota"], reverse=True):                 # the floor first
        lo, hi = l["cols"].get(row, (0, nc - 1))
        cand = [c_ for c_ in key_cells(4) if c_[2] == row and lo <= c_[1] <= hi
                and c_ not in clear and not on_ring(c_) and c_ not in QUIET]
        lean = l["lean"].get(row, 0.0)
        sig = l["focus"].get(row)
        mid = (nc - 1) / 2.0

        def wt(c_, lean=lean, sig=sig, mid=mid):
            w = math.exp(lean * (c_[1] - mid) / mid)
            return w * math.exp(-((c_[1] - mid) / sig) ** 2 / 2) if sig else w

        def fits(combo):
            trial, done = dict(out), list(placed)
            for cell in combo:
                if any(math.hypot(cell[1] - o[1], cell[2] - o[2]) < l["gap"] for o in done):
                    return False
                if any(o[2] != cell[2] and abs(cell[1] - o[1]) < l["colgap"] for o in done):
                    return False
                if violates(trial, set(), cell, True, 99.0):
                    return False
                trial[cell] = LIME; done.append(cell)
            return True
        sets = [cb for cb in itertools.combinations(cand, l["quota"][row]) if fits(cb)]
        if not sets:
            continue
        ws = [math.prod(wt(c_) for c_ in cb) for cb in sets]
        pick = rnd.random() * sum(ws)
        for cb, w_ in zip(sets, ws):
            pick -= w_
            if pick <= 0:
                break
        for cell in cb:
            out[cell] = LIME
            placed.append(cell)
    for c_ in placed:
        if c_[2] in l["white_rows"]:
            out[c_] = WHITE
    rc = random.Random(seed * 7919 + 17 * 4)
    for c_ in es_order([c_ for c_ in placed if out[c_] == LIME], lambda c_: 1.0, rc)[:l["depth"]]:
        out[c_] = MID_LIME
    return out, placed


# ---------------------------------------------------------------- checks on the art (mirror the rules)
def art_checks(lit, src, info, clear, l=L4):
    fails = []
    marks = {c_ for c_ in lit if c_ not in src}
    bright = {c_ for c_ in marks if lit[c_] in BRIGHT}
    n = {k: sum(1 for c_ in lit if c_[0] == k and lit[c_] in BRIGHT) for k in (2, 3, 4, 5)}
    if not (n[5] > n[2] > n[3] >= 12):
        fails.append("burst counts %s" % n)
    if not (3 <= n[4] <= 7):
        fails.append("key 4 is not a handful: %d" % n[4])
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
        if r_of((k, a, b)) >= 1.0 and any((k, a + x, b + y) in marks for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1))):
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
        for line in lines:                                       # at most 2 marks in any 5 consecutive cells
            for o in range(len(line) - 4):
                ms = [c_ for c_ in line[o:o + 5] if c_ in marks]
                if len(ms) >= 3 and any(r_of(c_) >= 2.5 for c_ in ms):
                    fails.append("three in five at %s" % (ms[0],))
    for c_ in lit:
        if on_ring(c_):
            fails.append("lit on the outer ring %s" % (c_,))
        if is_corner(c_):
            fails.append("lit corner %s" % (c_,))
        if c_ in QUIET:
            fails.append("lit quiet cell %s" % (c_,))
        if c_ in clear:
            fails.append("token in the URL's clearing %s" % (c_,))
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
    nl = sum(1 for v in lit.values() if v == LIME); nw = sum(1 for v in lit.values() if v == WHITE)
    wf = nw / max(1, nl + nw)
    if not (0.34 <= wf <= 0.44):
        fails.append("white %.2f" % wf)
    return sorted(set(fails)), n, round(wf, 3)


def continuity(lit):
    """Bezel continuity 0-12: key 5's top inner rows vs key 2's bottom inner rows (same x lattice), key 2's
    right inner columns vs key 3's left inner columns (same y lattice)."""
    m = lambda c_: c_ in lit
    nc2, nr2 = dims(2); nc3, nr3 = dims(3); nc5, nr5 = dims(5)
    up5 = [a for a in range(nc5) for b in (1, 2) if m((5, a, b))]
    in2 = [a for a in range(nc2) for b in (nr2 - 3, nr2 - 2) if m((2, a, b))]
    out2 = [b for b in range(nr2) for a in (nc2 - 3, nc2 - 2) if m((2, a, b))]
    in3 = [b for b in range(nr3) for a in (1, 2) if m((3, a, b))]
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
def compose(seed=SEED, sizes=None, shape="frame", p=P, l=L4, slogan_cap=SLOGAN_CAP):
    sizes = sizes or TYPE["main"]
    us, ul = sizes["url"]
    ss, sl = sizes["slogan"]
    url_pen, url_cap, url_box, url_lines = url_place(us, ul)
    clear = clearing(url_box, url_lines, shape)
    lit, src, info, S, weight = plume(seed, p)
    lit, settled = landing(seed, clear, l, lit)
    img = Image.new("RGB", (W, H), INK)
    for k in (2, 3, 4, 5):
        v8.draw_board(img, k, {(a, b): col for (kk, a, b), col in lit.items() if kk == k},
                      skip={(a, b) for (kk, a, b) in clear if kk == k})
    logo_box = v8.logo(img)
    boxes_u = v8.text(img, url_pen, url_cap, URL, us, TRACK, ul, "left")
    boxes_s = v8.text(img, SLOGAN_RIGHT, slogan_cap, SLOGAN, ss, TRACK, sl, "right")
    fails, n, wf = art_checks(lit, src, info, clear, l)
    return img, dict(lit=lit, src=src, info=info, clear=clear, settled=settled, fails=fails, n=n, wf=wf,
                     url=(url_pen, url_cap, boxes_u, us, ul), slogan=(SLOGAN_RIGHT, slogan_cap, boxes_s, ss, sl),
                     logo=logo_box, seed=seed, shape=shape)


def _luma(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def mass_centroid(img, key, skip_unlit=True):
    """Visual mass of a key: the centroid of (luma - luma of #131512) over its window, the unlit board
    tokens left out (they are symmetric about the board centre). Returns the offset from the window
    centre (x, y) in px."""
    px = img.load(); x0, y0, x1, y1 = v8.WINDOWS[key - 1]
    li = _luma(INK); sw = sx = sy = 0.0
    for y in range(y0, y1):
        for x in range(x0, x1):
            p_ = px[x, y]
            if skip_unlit and p_ == UNLIT:
                continue
            w = max(0.0, _luma(p_) - li)
            sw += w; sx += w * (x + 0.5); sy += w * (y + 0.5)
    cx, cy = v8.window_centre(key)
    return round(sx / sw - cx, 1), round(sy / sw - cy, 1)


_URL_MASS = {}


def k4_balance(lit, sizes=None):
    """Fast key 4 mass offset (x, y) for the search: the URL's ink mass (rendered once) plus the settled tokens."""
    sizes = sizes or TYPE["main"]
    key = tuple(sizes["url"])
    if key not in _URL_MASS:
        im = Image.new("RGB", (W, H), INK)
        us, ul = sizes["url"]
        pen, cap, _, _ = url_place(us, ul)
        v8.text(im, pen, cap, URL, us, TRACK, ul, "left")
        px = im.load(); li = _luma(INK); sw = sx = sy = 0.0
        for y in range(130, 206):
            for x in range(13, 88):
                w = max(0.0, _luma(px[x, y]) - li); sw += w; sx += w * (x + 0.5); sy += w * (y + 0.5)
        _URL_MASS[key] = (sw, sx, sy)
    sw, sx, sy = _URL_MASS[key]
    li = _luma(INK)
    for cell, col in lit.items():
        if cell[0] == 4:
            x, y = centre(cell); w = (_luma(col) - li) * SQ * SQ
            sw += w; sx += w * x; sy += w * y
    cx, cy = v8.window_centre(4)
    return round(sx / sw - cx, 1), round(sy / sw - cy, 1)


def search(n, p=P, l=L4, start=1):
    ok = []
    box, lines = url_place(*TYPE["main"]["url"])[2:]
    clear = clearing(box, lines, "frame")
    for s in range(start, start + n):
        lit, src, info, S, _ = plume(s, p)
        lit, settled = landing(s, clear, l, lit)
        fails, cnt, wf = art_checks(lit, src, info, clear, l)
        if not fails:
            k2 = elongation([c_ for c_ in lit if c_[0] == 2 and lit[c_] in BRIGHT])
            ok.append(dict(seed=s, cont=continuity(lit), k2_axis=k2[0], k2_elong=k2[1], k4=k4_balance(lit),
                           n=cnt, white=wf))
    ok.sort(key=lambda o: (-o["cont"], abs(o["k4"][0]) + abs(o["k4"][1]), -o["k2_elong"], o["seed"]))
    return ok


def layout_meta(img, meta):
    """Every number that matters, for checks.json and design.md."""
    def block(boxes, key):
        b = v8.ink_box(boxes)
        return {"ink_inclusive": [b[0], b[1], b[2] - 1, b[3] - 1], "size": [b[2] - b[0], b[3] - b[1]],
                "box_centre_offset_vs_window": list(v8.centre_offset(b, key)),
                "ink_mass_offset_vs_window": list(mass_centroid(img, key))}
    lit, src, clear = meta["lit"], meta["src"], meta["clear"]
    url_pen, url_cap, boxes_u, us, ul = meta["url"]
    sl_right, sl_cap, boxes_s, ss, sl = meta["slogan"]
    ub = v8.ink_box(boxes_u)
    ca = sorted({a for (_, a, _) in clear}); cb = sorted({b for (_, _, b) in clear})
    clean = (cpx((4, ca[0] - 1, 0))[0] + SQ, cpx((4, 0, cb[0] - 1))[1] + SQ,      # inclusive clean rect around the URL
             cpx((4, ca[-1] + 1, 0))[0] - 1, cpx((4, 0, cb[-1] + 1))[1] - 1)
    tokens = {}
    for k in (2, 3, 4, 5):
        cells = key_cells(k)
        fly = [c_ for c_ in cells if c_ in lit and c_ not in src]
        tokens["key%d" % k] = {
            "lime": sum(1 for c_ in fly if lit[c_] == LIME), "white": sum(1 for c_ in fly if lit[c_] == WHITE),
            "depth_639840": sum(1 for c_ in fly if lit[c_] == MID_LIME),
            "source_lime": sum(1 for c_ in cells if c_ in src and c_ in lit),
            "unlit_2C2F2B": sum(1 for c_ in cells if c_ not in lit and c_ not in clear),
            "not_drawn_clearing": sum(1 for c_ in cells if c_ in clear),
            "bright_axis_deg_elongation": list(elongation([c_ for c_ in fly if lit[c_] in BRIGHT]))}
    a0, b0, nc, nr = P["src"]
    sx0, sy0 = cpx((5, a0, b0)); sx1, sy1 = cpx((5, a0 + nc - 1, b0 + nr - 1))
    return {
        "candidate": "c-quiet-landing", "seed": meta["seed"],
        "layout": {"key1": "logo", "key2": "the plume", "key3": "the dust", "key4": "URL on a calm board",
                   "key5": "the source block and its debris", "key6": "slogan"},
        "logo": {"xy": list(meta["logo"][:2]), "size": [meta["logo"][2] - meta["logo"][0], meta["logo"][3] - meta["logo"][1]],
                 "box_centre_offset_vs_window": list(v8.centre_offset(meta["logo"], 1))},
        "url": dict(size_px=us, leading_px=ul, tracking_px=TRACK, align="left", pen_x=url_pen, cap_top=url_cap,
                    cap_height_px=c.cap_height(us), lines=URL, line_ink=boxes_u, **block(boxes_u, 4),
                    clean_rect_inclusive=list(clean),
                    margins_ink_to_tokens_lrtb=[ub[0] - clean[0], clean[2] - (ub[2] - 1), ub[1] - clean[1], clean[3] - (ub[3] - 1)]),
        "slogan": dict(size_px=ss, leading_px=sl, tracking_px=TRACK, align="right", right_ink_edge=sl_right - 1,
                       cap_top=sl_cap, cap_height_px=c.cap_height(ss), lines=SLOGAN, line_ink=boxes_s, **block(boxes_s, 6)),
        "boards": {"key%d" % k: {"x0_y0_cols_rows": list(BOARDS[k]), "px_inclusive": list(v8.board_px(k)),
                                 "centre_offset_vs_window": list(v8.board_offset(k))} for k in (2, 3, 4, 5)},
        "key4_clearing": {"cols": [ca[0], ca[-1]], "rows": [cb[0], cb[-1]], "cells": len(clear), "shape": meta["shape"]},
        "key4_settled": sorted([[c_[1], c_[2], {LIME: "lime", WHITE: "white", MID_LIME: "depth"}[lit[c_]]]
                                for c_ in meta["settled"]]),
        "source_block": {"cells_a_b_cols_rows": [a0, b0, nc, nr], "px_inclusive": [sx0, sy0, sx1 + SQ - 1, sy1 + SQ - 1],
                         "lit_cells": sum(1 for c_ in src if c_ in lit)},
        "tokens": tokens, "bright_per_key": meta["n"], "white_share_of_bright": meta["wf"],
        "bezel_continuity_0_12": continuity(lit), "art_fails": meta["fails"],
    }


def build(seed, sizes, outdir, shape="frame"):
    img, meta = compose(seed, sizes, shape)
    lay = layout_meta(img, meta)
    checks = v8.render(img, outdir, extra={"layout": lay})
    return checks, lay


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=None)
    ap.add_argument("--search", type=int, default=0)
    ap.add_argument("--shape", default="frame")
    ap.add_argument("--type", default=None, help="main or alt; default renders both (main here, alt in alt/)")
    a = ap.parse_args()
    if a.search:
        ok = search(a.search)
        print(len(ok), "of", a.search, "seeds pass every art rule; best bezel continuity, then key 4 balance first")
        for o in ok[:40]:
            print(o)
        return
    runs = [(a.type, a.out or HERE)] if a.type else [("main", HERE), ("alt", os.path.join(HERE, "alt"))]
    bad = []
    for kind, out in runs:
        checks, lay = build(a.seed, TYPE[kind], out, a.shape)
        print("==", kind, "->", out)
        print(json.dumps({k: v for k, v in checks.items() if k != "layout"}, indent=1, default=str))
        print(json.dumps({k: lay[k] for k in ("url", "slogan", "key4_settled", "bright_per_key",
                                              "white_share_of_bright", "art_fails")}, default=str))
        if not checks["hard_rules_pass"]:
            bad.append("%s: hard rules fail" % kind)
        if lay["art_fails"]:
            bad.append("%s: art rules fail %s" % (kind, lay["art_fails"]))
    if bad:
        raise SystemExit("; ".join(bad))


if __name__ == "__main__":
    main()
