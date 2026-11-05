#!/usr/bin/env python3
"""Token Deck welcome v7, variant C (Gabriel's option 2): URL bottom left under the logo, slogan bottom
right, token art in keys 2, 3 and 5. Own code; imports only v7_common (and Pillow).

Layout   key 1 logo   | key 2 art (the stream)  | key 3 art (the dust)
         key 4 URL    | key 5 art (the source)  | key 6 slogan
Type     Soehne Buch through v7_common's v6 pipeline, white, sentence case.
         URL 'io.stigg.io' / '/usage': 10.5 px on 13 px leading, flush left, its ink box centred on
         window 4 (x 28-72, y 156-178; centre 50.5 / 167.5 against the window's 50.5 / 168). At 10.5 px
         the x-height steps from 5 to 6 px and the cap from 7 to 8 px; the URL is all lowercase, so
         that step is what makes it read.
         Slogan 'The AI Usage' / 'Management' / 'Console': 9.5 px on 12 px leading, flush left at pen
         x 235. This is the most key 6 allows: 'Management' (and 'The AI Usage') ink 57 px at 9.5 px and
         region 6 is 58 px wide (x 234-292, the tile's right edge); at 9.75 px they ink 59 px. 9.55-9.7 px
         ink exactly 58 px (9.6 / 9.7 only at some sub-pixel phases): edge to edge from the rim limit
         x 234, with the same 7 px cap and 5 px x-height, a 1-2% gain nobody would see, at the cost of
         1 px of centring and the rim margin. A block centred on window 6 could be only 50 px
         wide (x 242-292), i.e. about 8.3 px type, so the block sits flush against the tile's right
         edge: ink x 235-291, centre 263.5 against the window's 267 (3.5 px left). Cap top 153 (ink
         153-183, 0.5 px below the window centre); at 152 the two long lines' JPEG ringing reaches luma
         4.0 outside the tile, at 153 it is 3.0.
         Logo: the official file from v7_common.logo_image(), 60 x 17 at (20, 50), v6's position:
         centred on window 1 to 0.5 px, and only its left edge shares a JPEG block with a tile edge.
Tokens   One lattice for the whole panel: 3 px squares on a 5 px pitch (2 px gaps), cells at
         x = 4 + 5i, y = 4 + 5j. Each art key shows a 10 x 10 block of it (48 x 48 px), every cell an
         unlit #3C3E3A token unless lit. The origin is chosen so all three blocks are the same size and
         each sits within 1 px of its WINDOW centre: key 2 x 134-181 / y 34-81 (centre -1, -0.5),
         key 3 x 244-291 (+1, -0.5), key 5 x 134-181 / y 144-191 (-1, 0). Key 3's block ends on the
         tile's last column, x 291, the same column where the slogan below it ends.
         Lit tokens: lime #92E759 and white #FFFFFF, 40% white (21 of 52; the 17-token source block is all
         lime, so the flying tokens are 21 of 35 white, more of them toward the dust). Depth: a few #639840 tokens
         sit behind the bright ones in the plume (the stigg.io field's dim points). #436633 was tried
         and dropped: on the panel it is barely distinguishable from the unlit grid and only added noise.
Burst    A solid lime source block (4 x 6 cells, rounded corners) one cell in from key 5's lower-left
         corner erodes at its right and top edges (pixelmark erosion); debris blows up and to the right
         from its top-right corner; a plume rises through the bezel into key 2, crosses it on a
         diagonal, bends right through the bezel into key 3 and thins into dust. The density is a
         designed field (a near-field blast + a band along a curved spine + four clusters at fixed
         positions along it); the seed only decides individual cells. Exact counts per key are drawn by
         weighted sampling without replacement. White goes to an exact number of tokens per key (key 5's
         debris 4, key 2 9, key 3 8), weighted toward the far end and never next to the source; colour and
         depth use their own random streams, so changing them never moves a bright token.
Rules    Enforced while placing (a cell that would break one is skipped) and re-checked afterwards:
         no 3 marked cells in a straight row or column; no diagonal staircase of 3 marked cells; no 4
         bright tokens within 7 cells of one row or column; no 3 x 3 window with more than 4 bright tokens;
         no mark in a block's corner cells; at most 2 marks on a block's outer row or column; at most 3
         marks in any row or column of a block (2 in key 3's sparse dust); depth tokens never touch the
         source, and debris touches it only on its right and top; key 3's last column (x 289-291) stays
         unlit because it shares an 8 px JPEG block with the tile edge. Every token is on the lattice,
         one per cell. Text keys carry no tokens at all.

usage: make.py                      render seed 148 here, plus alt-shared-9.5/ (URL at the slogan's 9.5 px)
       make.py --seed N [--out DIR] [--url-size S --url-lead L]
       make.py --search N           list seeds 1..N that pass every art rule, best bezel continuity first
"""
import argparse, json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WELCOME = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WELCOME)
import v7_common as c                                   # noqa: E402
from PIL import Image, ImageDraw                        # noqa: E402

W, H = c.W, c.H
INK, LIME, WHITE, UNLIT = c.INK, c.LIME, c.WHITE, c.UNLIT
MID_LIME = (0x63, 0x98, 0x40)                           # After Tokens depth step
BRIGHT = (LIME, WHITE)
SEED = 148                                              # chosen by eye among seeds that pass every rule

# lattice and art blocks
PITCH, SQ = 5, 3
OX, OY = 4, 4                                           # cells at x = 4 + 5i, y = 4 + 5j
BLOCKS = {2: (26, 6), 3: (48, 6), 5: (26, 28)}          # (i0, j0) of each art key's 10 x 10 block
NB = 10
QUIET = {(57, j) for j in range(6, 16)}                 # key 3's last column: shares a JPEG block with the tile edge

# type and logo
LOGO_XY = (20, 50)
URL = ["io.stigg.io", "/usage"]
SLOGAN = ["The AI Usage", "Management", "Console"]
URL_SIZE, URL_LEAD = 10.5, 13
SLOGAN_SIZE, SLOGAN_LEAD = 9.5, 12
SLOGAN_PEN, SLOGAN_CAP = 235, 153


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


# ---------------------------------------------------------------- the burst
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
    spine=[(160, 160), (161, 122), (164, 76), (192, 50), (252, 54), (300, 66)],   # panel px, source to dust
    src=(27, 31, 4, 6),            # source block: i0, j0, cols, rows (key 5, one cell in from the block edges)
    erode=0.65,                    # pixelmark erosion of the source's right side and top
    lam_n=13.0, up=58.0, aim=2.0,  # near field: blast from the source's top-right corner (px decay, direction deg, focus)
    fringe=0.35,                   # extra weight for fragments right against the source's right and top edges
    band_w=(7.0, 0.07), soft=0.45, lam_f=170.0, band_lo=0.18,   # the plume between clusters
    # clusters along the plume, in spine coordinates: (s px, q px, sigma_s, sigma_q, amplitude)
    clusters=[(108, 2, 13, 6, 1.0),        # key 2: where the plume comes up through the bezel
              (142, -3, 11, 6, 0.85),      # key 2: where it bends right
              (214, 4, 13, 8, 0.75),       # key 3: where it arrives
              (252, -2, 12, 9, 0.4)],      # key 3: the last of it
    jitter=6.0,                    # seeded jitter of each cluster centre (px)
    target={5: 11, 2: 15, 3: 9},   # bright tokens per key (key 5: debris beyond the source)
    depth={5: 4, 2: 6, 3: 4},      # #639840 depth tokens per key
    edge=0.5,                      # weight on each block's outer ring: the plume fades at the matrix edge
    gap0=1.0, gap1=0.35,           # min centre distance between bright tokens, cells: gap0 + gap1 * s/S
    white={5: 4, 2: 9, 3: 8},      # white tokens per key: 21 of 52 bright = 40%; the source itself is lime
    white_base=0.30, white_min_r=1.5,   # within a key, white leans to the far end; never next to the source
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
    for di, dj in ((1, 0), (0, 1)):
        run = 1
        for sgn in (1, -1):
            n = 1
            while marked((i + sgn * n * di, j + sgn * n * dj)):
                run += 1; n += 1
        if run >= 3:
            return "run"
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
    cap = 2 if k == 3 else 3
    if col > cap or row > cap:
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
    # 2. clusters at designed positions along the plume, jittered by the seed
    clusters = [(s0 + rnd.uniform(-1, 1) * p["jitter"], q0 + rnd.uniform(-1, 1) * p["jitter"], ss, sq, a)
                for (s0, q0, ss, sq, a) in p["clusters"]]
    # 3. a weight per free cell: near-field blast + plume band + clusters, faded on the matrix edge
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

    # colour and depth draw from their own streams, one per key: changing them never moves a bright token,
    # and changing one key never reshuffles another
    rnd_colour = {k: random.Random(seed * 7919 + 17 * k) for k in BLOCKS}
    rnd_depth = {k: random.Random(seed * 104729 + 3 * k) for k in BLOCKS}

    # 4. bright tokens, exact counts per key: weighted sampling without replacement, spacing and rules
    for k in (5, 2, 3):
        placed = 0
        for (i, j) in es_order([c_ for c_ in weight if key_of(*c_) == k], lambda c_: weight[c_]):
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
    # 6. depth: dim tokens behind the bright ones, in the plume's volume
    for k in (5, 2, 3):
        placed = 0
        for c_ in es_order([c_ for c_ in weight if key_of(*c_) == k and c_ not in lit], lambda c_: weight[c_], rnd_depth[k]):
            if placed >= p["depth"][k]:
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
    if not (n[5] > n[2] > n[3] >= 8):
        fails.append("counts %s" % n)
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
    for k, (i0, j0) in BLOCKS.items():
        cap = 2 if k == 3 else 3
        for m_ in range(NB):
            col = sum(1 for t in range(NB) if (i0 + m_, j0 + t) in marks)
            row = sum(1 for t in range(NB) if (i0 + t, j0 + m_) in marks)
            if col > cap or row > cap:
                fails.append("row/column of dots, key %d" % k)
            if (m_ in (0, NB - 1)) and (col > 2 or row > 2):
                fails.append("marks along the matrix edge, key %d" % k)
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
    if not (0.36 <= wf <= 0.44):
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


# ---------------------------------------------------------------- compose
def lime_detail(img):
    """Lime purity as the deck decodes it, split into each token's 2 x 2 full-chroma core and its edge."""
    seen = c.v6.decode_box(c.v6.jpeg(img, c.QUALITY))
    s, d = img.load(), seen.load()
    core, edge = [], []
    for y in range(H):
        for x in range(W):
            if s[x, y] == LIME:
                dev = max(abs(a - b) for a, b in zip(d[x, y], LIME))
                x0, y0 = x - x % 2, y - y % 2
                full = all(s[x0 + a, y0 + b] == LIME for a in (0, 1) for b in (0, 1))
                (core if full else edge).append(dev)
    m = lambda v: round(sum(v) / len(v), 1) if v else 0
    return {"core_px": len(core), "core_mean_dev": m(core), "core_max_dev": max(core, default=0),
            "edge_px": len(edge), "edge_mean_dev": m(edge), "edge_max_dev": max(edge, default=0)}


def compose(seed=SEED, url_size=URL_SIZE, url_lead=URL_LEAD, p=P):
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    lit, src, info, S = plume(seed, p)
    for k in BLOCKS:
        for (i, j) in block_cells(k):
            x, y = cell_px(i, j)
            d.rectangle([x, y, x + SQ - 1, y + SQ - 1], fill=lit.get((i, j), UNLIT))
    logo, _ = c.logo_image()
    img.paste(logo, LOGO_XY)
    # URL, key 4: flush left, ink box centred on the window (pen on a half pixel)
    ub = c.measure(URL, url_size, url_lead)
    uw = max(b[2] for b in ub) - min(b[0] for b in ub)
    uh = max(b[3] for b in ub) - min(b[1] for b in ub)
    cx4, cy4 = c.window_centre(4)
    u_pen = round((cx4 - uw / 2.0 - min(b[0] for b in ub)) * 2) / 2.0
    u_cap = math.floor(cy4 - uh / 2.0 - min(b[1] for b in ub))
    boxes_u = c.text(img, [(u_pen, u_cap, URL)], url_size, url_lead)
    # slogan, key 6: flush left, as far right as region 6 allows
    s_size = min(SLOGAN_SIZE, url_size)
    boxes_s = c.text(img, [(SLOGAN_PEN, SLOGAN_CAP, SLOGAN)], s_size, SLOGAN_LEAD)
    fails, n, wf = art_checks(lit, src, info)

    def centre(boxes, key):
        x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes); x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
        wx, wy = c.window_centre(key)
        return {"ink": [x0, y0, x1, y1], "centre_offset_vs_window": [round((x0 + x1) / 2 - wx, 1), round((y0 + y1) / 2 - wy, 1)]}

    tokens = {}
    for k in BLOCKS:
        cells = block_cells(k)
        tokens["key%d" % k] = {
            "lime": sum(1 for c_ in cells if lit.get(c_) == LIME and c_ not in src),
            "white": sum(1 for c_ in cells if lit.get(c_) == WHITE),
            "source_lime": sum(1 for c_ in cells if c_ in src and c_ in lit),
            "depth_639840": sum(1 for c_ in cells if lit.get(c_) == MID_LIME),
            "unlit_3C3E3A": sum(1 for c_ in cells if c_ not in lit)}
    blocks = {}
    for k, (i0, j0) in BLOCKS.items():
        x0, y0 = cell_px(i0, j0); x1, y1 = x0 + PITCH * NB - (PITCH - SQ), y0 + PITCH * NB - (PITCH - SQ)
        wx, wy = c.window_centre(k)
        blocks["key%d" % k] = {"px": [x0, y0, x1, y1], "centre_offset_vs_window": [(x0 + x1) / 2 - wx, (y0 + y1) / 2 - wy]}
    lx, ly = LOGO_XY
    meta = {
        "variant": "c-url-left-slogan-right", "seed": seed,
        "layout": {"key1": "logo", "key2": "art: the plume rising on a diagonal", "key3": "art: the dust",
                   "key4": "URL", "key5": "art: the source block and its debris", "key6": "slogan"},
        "logo": {"xy": [lx, ly], "size": [60, 17], "centre_offset_vs_window": [lx + 30 - c.window_centre(1)[0], ly + 8.5 - c.window_centre(1)[1]]},
        "url": dict(size_px=url_size, leading_px=url_lead, pen_x=u_pen, cap_top=u_cap, lines=URL, cap_height=c.cap_height(url_size),
                    line_ink=boxes_u, **centre(boxes_u, 4)),
        "slogan": dict(size_px=s_size, leading_px=SLOGAN_LEAD, pen_x=SLOGAN_PEN, cap_top=SLOGAN_CAP, lines=SLOGAN, cap_height=c.cap_height(s_size),
                       line_ink=boxes_s, **centre(boxes_s, 6),
                       note="max size in key 6: 'Management' inks 57 px of region 6's 58 px at 9.5 px, 59 px at 9.75 px"),
        "lattice": {"pitch": PITCH, "square": SQ, "origin": [OX, OY], "blocks": blocks, "unlit": "#3C3E3A",
                    "lit": ["#92E759", "#FFFFFF"], "depth": ["#639840"]},
        "tokens": tokens,
        "white_share_of_bright": round(wf, 3),
        "art_fails": fails, "bezel_continuity_0_12": continuity(lit),
        "lime_core_vs_edge": lime_detail(img),
    }
    return img, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--url-size", type=float, default=URL_SIZE)
    ap.add_argument("--url-lead", type=int, default=URL_LEAD)
    ap.add_argument("--search", type=int, default=0)
    a = ap.parse_args()
    if a.search:
        ok = []
        for s in range(1, a.search + 1):
            lit, src, info, _ = plume(s)
            fails, n, wf = art_checks(lit, src, info)
            if not fails:
                ok.append((continuity(lit), s, n, round(wf, 3)))
        ok.sort(key=lambda o: (-o[0], o[1]))
        print(len(ok), "of", a.search, "seeds pass every art rule; best bezel continuity first")
        for o in ok[:40]:
            print(o)
        return
    runs = [(a.seed or SEED, a.out or HERE, a.url_size, a.url_lead)]
    if a.seed is None and a.out is None and a.url_size == URL_SIZE:
        runs.append((SEED, os.path.join(HERE, "alt-shared-9.5"), 9.5, 12))     # the alternative: one size for both
    for seed, out, us, ul in runs:
        img, meta = compose(seed, us, ul)
        assert not meta["art_fails"], meta["art_fails"]
        checks = c.render(img, out, extra={"layout": meta})
        print(out)
        print(json.dumps({k: v for k, v in checks.items() if k != "layout"}, indent=1))
    print(json.dumps(meta, indent=1, default=str) if len(runs) == 1 else "")


if __name__ == "__main__":
    main()
