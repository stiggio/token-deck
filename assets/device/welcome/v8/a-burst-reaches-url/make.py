#!/usr/bin/env python3
"""Token Deck welcome v8, candidate a: THE BURST REACHES THE URL. Own code; imports v8_common.

Layout   key 1 logo          | key 2 the plume          | key 3 the dust
         key 4 URL + landing | key 5 the source + blast | key 6 slogan
Idea     The lime source block (5 x 6 cells, rounded, one cell in from key 5's lower-right corner) blows
         out radially from its top-left corner: a near-field fan fills key 5's upper left; one branch
         rises through key 2 on a diagonal and falls into key 3 as dust (v7's plume); the other flies
         left across key 5, crosses the bezel and lands around the URL in key 4. Key 4 carries a full
         board like the art keys, with the cells within 3 px of each URL line's ink not drawn, so the
         URL reads on plain #131512; the debris lands in the notch beside '/usage' and on the rows above
         and below it, densest on the right where it arrives (lime next to the type, white kept 6 px off
         so it never reads as punctuation).
Type     URL 10.5 px / 13 px leading, flush left at x 28, ink x 28-71 / y 157-179, its box centred on
         window 4 (-0.5, +0.5). Slogan 9.5 px / 12 px, flush right on x 291, cap top 152, ink x 235-291 /
         y 152-182: box (-3.5, -0.5) and ink centroid (-1.0, -1.5) from window 6's centre; flush left at
         x 234 puts the centroid 7.0 px left (alt-slogan-flush-left/). Cap top 153 rings to luma 5.0
         beside the tile's right edge, 152 to 3.0.
Rules    v8 BRIEF's art rules on per-key boards (cells (k, a, b), adjacency only inside one board), plus
         this design's own: no lit token on any board's outermost ring (every ring is 6-14 px from a
         window edge and the v7 photo shows the bevel reflecting the ring) or in v8_common.quiet(k); no
         three marks every other cell in a row or column; corner-touching debris at most 3 to a group;
         key 4: at most 2 marks per row, no lit token over an i-dot. Hard rules: v8_common.render.

usage: make.py                    render the final here (+ alt-slogan-flush-left/)
       make.py --seed N --out DIR [--slogan left|right]
       make.py --search N         seeds 1..N that pass every art rule, best score first
       make.py --seed N --ascii   the boards and the weights as text
"""
import argparse, json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WELCOME = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WELCOME)
import v8_common as v                                   # noqa: E402
from PIL import Image, ImageDraw                        # noqa: E402

W, H = v.W, v.H
INK, LIME, WHITE, UNLIT, MID = v.INK, v.LIME, v.WHITE, v.UNLIT, v.MID_LIME
BRIGHT = (LIME, WHITE)
PITCH, SQ = v.PITCH, v.SQ
ART = (5, 2, 3, 4)                     # placement order: the blast, the plume, the dust, the landing
SEED = 309                              # chosen by eye among the top-ranked seeds of 1-400 (see search())

# ---------------------------------------------------------------- type and logo
LOGO_XY = (20, 50)
TRACK = -0.06
URL = ["io.stigg.io", "/usage"]
URL_SIZE, URL_LEAD = 10.5, 13
URL_PEN, URL_CAP = 28, 157             # flush left, ink box x 28-71 / y 157-179: centred on window 4
SLOGAN = ["The AI Usage", "Management", "Console"]
SLOGAN_SIZE, SLOGAN_LEAD = 9.5, 12
SLOGANS = {"right": ("right", 292, 152),   # every line's last ink column on x 291
           "left": ("left", 234, 152)}     # every line's first ink column on x 234
M_CLEAR = 3                            # no token within 3 px of a URL line's ink box (2 px = the token gap)
M_LIT = 3                              # lit tokens may sit on any drawn cell (lime only within 6 px)
M_WHITE = 6                            # white tokens keep 6 px: beside the URL a white square reads as a full stop
ROW4 = 2                               # key 4: at most 2 marks on a row (3 parallel to the URL read as a dotted rule)


def dims(k):
    return v.BOARDS[k][2], v.BOARDS[k][3]


def cells(k):
    return [(k, a, b) for (a, b) in v.board_cells(k)]


def cpx(c):
    return v.cell_px(c[0], c[1], c[2])


def ctr(c):
    x, y = cpx(c)
    return x + SQ / 2.0, y + SQ / 2.0


def ring(c):
    nc, nr = dims(c[0])
    return c[1] in (0, nc - 1) or c[2] in (0, nr - 1)


QUIET = {(k, a, b) for k in ART for (a, b) in v.quiet(k)}


def url_boxes():
    """Each URL line's ink box (exclusive right / bottom), as v8_common.text draws it."""
    scratch = Image.new("RGB", (W, H), INK)
    return v.text(scratch, URL_PEN, URL_CAP, URL, URL_SIZE, TRACK, URL_LEAD, "left")


def near_boxes(c, boxes, m):
    x, y = cpx(c)
    return any(x <= bx1 - 1 + m and x + SQ - 1 >= bx0 - m and y <= by1 - 1 + m and y + SQ - 1 >= by0 - m
               for (bx0, by0, bx1, by1) in boxes)


def i_dots():
    """The URL's crisp i-dots: isolated lit pixels on a line's cap-top row (empty left, right and below)."""
    scratch = Image.new("RGB", (W, H), INK)
    boxes = v.text(scratch, URL_PEN, URL_CAP, URL, URL_SIZE, TRACK, URL_LEAD, "left")
    px = scratch.load()
    return [(x, b[1]) for b in boxes for x in range(b[0], b[2]) if px[x, b[1]] != INK
            and px[x - 1, b[1]] == INK and px[x + 1, b[1]] == INK and px[x, b[1] + 1] == INK]


UB = url_boxes()
DOTS = i_dots()
CLEAR = {c for c in cells(4) if near_boxes(c, UB, M_CLEAR)}       # not drawn: the URL's clearing
NOLIT = {c for c in cells(4) if near_boxes(c, UB, M_LIT)          # drawn unlit at most: near the type, or
         or any(cpx(c)[0] - 1 <= dx <= cpx(c)[0] + SQ and dy - 7 <= cpx(c)[1] < dy for dx, dy in DOTS)}  # over an i-dot


# ---------------------------------------------------------------- spines (after welcome_v7)
def catmull(points, n=300):
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for s in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[s - 1], pts[s], pts[s + 1], pts[s + 2]
        for t in [q / n for q in range(n)]:
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2
                                    + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3) for i in (0, 1)))
    out.append(points[-1])
    return out


def spine(points):
    poly = catmull(points)
    cum = [0.0]
    for p, q in zip(poly, poly[1:]):
        cum.append(cum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    return poly, cum


def project(sp, p):
    """(s, q): arc length of the nearest spine point and the signed distance from it."""
    poly, cum = sp
    best = (1e9, 0.0, 0.0)
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
    src=(6, 4, 5, 6),              # key 5: a0, b0, cols, rows (one cell in from the right and bottom edges)
    erode=0.45, bites=1,           # boundary erosion of the top-left edge: chance scale, most cells taken
    # near field: a fan from the source's top-left corner, aimed up-left, covering up to left
    lam_n=11.0, fan=135.0, aim=1.2, fan_base=0.06, fringe=0.3,
    # the plume (up through key 2, right into key 3) and the left branch (across key 5 into key 4), panel px
    U=[(172, 158), (170, 130), (166, 88), (160, 62), (168, 40), (196, 32), (247, 40), (268, 54), (283, 74)],
    L=[(163, 171), (146, 169), (104, 166), (80, 168), (70, 176)],
    band={"U": (7.0, 0.06, 0.45, 0.18, 180.0), "L": (6.0, 0.05, 0.45, 0.22, 120.0)},   # w0, w1, soft, lo, lambda
    # clusters: (spine or "P", x, y, sigma along, sigma across, amplitude); "P" = panel axes (sigma x, sigma y)
    clusters=[("U", 170, 148, 8, 7, 0.6),       # key 5: the plume's base, straight above the source
              ("U", 161, 82, 12, 7, 1.0),       # key 2: where the plume comes up through the bezel
              ("U", 168, 46, 11, 6, 0.85),      # key 2: where it bends right
              ("U", 252, 44, 12, 8, 0.8),       # key 3: where it arrives
              ("U", 272, 66, 12, 9, 0.6),       # key 3: where it settles
              ("L", 142, 170, 9, 7, 0.45),      # key 5: the left branch leaving
              ("P", 70, 177, 6, 7, 1.0),        # key 4: the notch beside '/usage', where it lands
              ("P", 62, 148, 12, 4, 0.7),       # key 4: above the URL, right half
              ("P", 60, 187, 12, 3, 0.6)],      # key 4: below the URL, right half
    jitter=4.0,
    land=(0.35, 28.0),             # key 4: frame weight a * exp(-(78 - x) / lambda), the arrival side heavier
    target={5: 11, 2: 16, 3: 12, 4: 8},   # bright flying tokens per key (key 5: beyond the source)
    white={5: 4, 2: 10, 3: 8, 4: 3},      # white among them: 25 of 71 bright with the source's 24 lime
    white_base=0.30, white_min_r=1.5,     # white leans to the far end of its spine, never next to the source
    depth={3: 2}, depth_from=0.55,        # #639840 at the dust's far end (key 4's rows are full at 2 marks)
    min_w={5: 0.05, 2: 0.12, 3: 0.10, 4: 0.10},   # cells under this share of the key's heaviest never light
    gamma={5: 1.0, 2: 1.6, 3: 1.4, 4: 1.6},        # contrast of the weights inside each key
    gap0=1.0, gap1=0.35,
)


def source_cells(p=P):
    a0, b0, nc, nr = p["src"]
    src = {(5, a, b) for a in range(a0, a0 + nc) for b in range(b0, b0 + nr)}
    for a, b in [(a0, b0), (a0, b0 + 1), (a0 + 1, b0), (a0, b0 + nr - 1), (a0 + nc - 1, b0)]:
        src.discard((5, a, b))                                  # rounded corners, the eroding left side rounder
    return src


def _nbrs(c, cs):
    return sum((c[0], c[1] + i, c[2] + j) in cs for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def _one_piece(cs):
    cs = set(cs)
    if not cs:
        return True
    seen, todo = set(), [next(iter(cs))]
    while todo:
        c = todo.pop()
        if c in seen:
            continue
        seen.add(c)
        todo += [(c[0], c[1] + i, c[2] + j) for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (c[0], c[1] + i, c[2] + j) in cs]
    return seen == cs


def _chain(cell, marked):
    """The 8-connected group of marked cells (same key) that contains `cell`."""
    seen, todo = set(), [cell]
    while todo:
        c = todo.pop()
        if c in seen or not marked(c):
            continue
        seen.add(c)
        todo += [(c[0], c[1] + i, c[2] + j) for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j]
    return seen


def src_bounds(src):
    return (min(c[1] for c in src), min(c[2] for c in src), max(c[1] for c in src), max(c[2] for c in src))


def violates(lit, src, cell, bright, r_src):
    """The reason marking `cell` would read as a mistake, or None. Source cells never count as marks."""
    k, a, b = cell
    nc, nr = dims(k)
    if cell in QUIET:
        return "quiet"
    if ring(cell):
        return "ring"
    if cell in NOLIT:
        return "clearing"
    if k == 5 and any((5, a + i, b + j) in src for i in (-1, 0, 1) for j in (-1, 0, 1)):
        if not bright:
            return "depth on the source"
        _, _, sa1, sb1 = src_bounds(src)
        if a >= sa1 or b >= sb1:
            return "debris right of / below the source"        # fragments break off its top and left only
    marked = lambda c: c == cell or (c in lit and c not in src)
    is_bright = lambda c: (c == cell and bright) or (c in lit and c not in src and lit[c] in BRIGHT)
    if r_src >= 1.0 and any(marked((k, a + i, b + j)) for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        return "pair"
    for i, j in ((1, 0), (0, 1)):
        run = 1
        for sg in (1, -1):
            n = 1
            while marked((k, a + sg * n * i, b + sg * n * j)):
                run += 1; n += 1
        if run >= 3:
            return "run"
        on = lambda c: c == cell or c in lit
        line = [cell]
        for sg in (1, -1):
            n = 1
            while on((k, a + sg * n * i, b + sg * n * j)):
                line.append((k, a + sg * n * i, b + sg * n * j)); n += 1
        if any(c in src for c in line) and sum(1 for c in line if c not in src) >= 2:
            return "ledge"
        if bright and r_src >= 2.5:
            for o in range(-6, 1):
                if sum(1 for n in range(7) if is_bright((k, a + (o + n) * i, b + (o + n) * j))) >= 4:
                    return "dotted"
        for o in (-4, -2, 0):                                    # three marks every other cell: a short dotted line
            if all(marked((k, a + (o + n) * i, b + (o + n) * j)) for n in (0, 2, 4)):
                return "every other"
    for i, j in ((1, 1), (1, -1)):
        run = 1
        for sg in (1, -1):
            n = 1
            while marked((k, a + sg * n * i, b + sg * n * j)):
                run += 1; n += 1
        if run >= 3:
            return "diagonal"
    if bright:
        for oa in (-2, -1, 0):
            for ob in (-2, -1, 0):
                if sum(1 for x in range(3) for y in range(3) if is_bright((k, a + oa + x, b + ob + y))) > 4:
                    return "clump"
    if r_src >= 2.5 and len(_chain(cell, lambda c: marked(c))) > 3:
        return "chain"                                          # corner-touching debris: at most 3 in a cluster
    col = sum(1 for n in range(nr) if marked((k, a, n)))
    row = sum(1 for n in range(nc) if marked((k, n, b)))
    if col > 3 or row > 3:
        return "row"
    if k == 4 and row > ROW4:
        return "key 4 row"                                      # 3 on a row parallel to the URL read as a rule
    return None


_PROJ = {}


def projections(p):
    key = (tuple(p["U"]), tuple(p["L"]))
    if key not in _PROJ:
        sp = {"U": spine(p["U"]), "L": spine(p["L"])}
        _PROJ[key] = (sp, {c: {n: project(sp[n], ctr(c)) for n in sp} for k in ART for c in cells(k)})
    return _PROJ[key]


def plume(seed, p=P):
    """One seeded burst: {cell: colour}, the source cells, per-cell info (s/S, q, r_src cells, spine)."""
    rnd = random.Random(seed)
    sp, proj = projections(p)
    S = {n: sp[n][1][-1] for n in sp}
    a0, b0, nc, nr = p["src"]
    src = source_cells(p)
    lit = {c: LIME for c in src}
    # 1. erosion: at most p["bites"] cells break off the block's exposed top / left edge, likelier near the
    #    top-left corner; the right column and the bottom row stay crisp, the block stays one piece and no
    #    cell is left hanging by a corner
    alive = set(src)
    bites = 0
    for c in sorted(src, key=lambda c: (c[1] - a0) + (c[2] - b0)):
        u = (a0 + nc - 1 - c[1]) / (nc - 1.0)             # 1 on the left column, 0 on the right
        w = (b0 + nr - 1 - c[2]) / (nr - 1.0)             # 1 on the top row, 0 on the bottom
        exposed = (5, c[1] - 1, c[2]) not in alive or (5, c[1], c[2] - 1) not in alive
        roll = rnd.random()
        if bites >= p["bites"] or not exposed or u == 0 or w == 0:
            continue
        if roll < p["erode"] * (u * w) ** 0.6:
            trial = alive - {c}
            if _one_piece(trial) and all(_nbrs(x, trial) >= min(2, _nbrs(x, alive)) for x in trial):
                alive = trial
                bites += 1
    lit = {c: LIME for c in alive}
    # 2. clusters, jittered by the seed
    cl = []
    for (name, x, y, sa, sq, amp) in p["clusters"]:
        jx, jy = rnd.uniform(-1, 1) * p["jitter"], rnd.uniform(-1, 1) * p["jitter"]
        if name == "P":
            cl.append(("P", x + jx, y + jy, sa, sq, amp))
        else:
            s0, q0 = project(sp[name], (x + jx, y + jy))
            cl.append((name, s0, q0, sa, sq, amp))
    # 3. a weight per free cell
    src_pts = [ctr(c) for c in src]
    ox = v.cell_px(5, a0, b0)[0] - 1; oy = v.cell_px(5, a0, b0)[1] - 1        # the eroding top-left corner
    _, _, sa1, sb1 = src_bounds(src)
    info, weight = {}, {}
    for k in ART:
        for c in cells(k):
            if c in src:
                continue
            x, y = ctr(c)
            r = (min(math.hypot(x - px, y - py) for px, py in src_pts) - PITCH) / PITCH
            sq = proj[c]
            near_spine = {4: "L", 2: "U", 3: "U"}.get(k) or min(sq, key=lambda n: abs(sq[n][1]))
            s, q = sq[near_spine]
            info[c] = (s / S[near_spine], q, r, near_spine)
            dd = math.hypot(x - ox, y - oy)
            th = math.degrees(math.atan2(-(y - oy), x - ox))
            near = 0.0
            if k == 5:
                near = math.exp(-dd / p["lam_n"]) * (p["fan_base"] + (1 - p["fan_base"]) *
                                                     max(0.0, math.cos(math.radians(th - p["fan"]))) ** p["aim"])
                if any((5, c[1] + i, c[2] + j) in src for i, j in ((1, 0), (0, 1))) and c[1] < sa1 and c[2] < sb1:
                    near += p["fringe"]
            band = 0.0
            for n in sp:
                w0, w1, soft, lo, lam = p["band"][n]
                s_n, q_n = sq[n]
                wd = w0 + w1 * s_n
                env = 1.0 / (1.0 + math.exp((abs(q_n) - wd) / (soft * wd)))
                band += lo * math.exp(-s_n / lam) * env
            clu = 0.0
            for (name, s0, q0, sa, sqq, amp) in cl:
                if name == "P":
                    clu += amp * math.exp(-((x - s0) / sa) ** 2 / 2 - ((y - q0) / sqq) ** 2 / 2)
                else:
                    s_n, q_n = sq[name]
                    clu += amp * math.exp(-((s_n - s0) / sa) ** 2 / 2 - ((q_n - q0) / sqq) ** 2 / 2)
            land = 0.0
            if k == 4:
                land = p["land"][0] * math.exp(-(78 - x) / p["land"][1])
            weight[c] = near + band + clu + land

    def es_order(cs, wf, r=rnd):
        return sorted(cs, key=lambda c: -(r.random() ** (1.0 / max(wf(c), 1e-9))))

    rnd_colour = {k: random.Random(seed * 7919 + 17 * k) for k in ART}
    rnd_depth = {k: random.Random(seed * 104729 + 3 * k) for k in ART}
    # 4. bright tokens, exact counts per key
    for k in ART:
        placed = 0
        pool = [c for c in weight if c[0] == k and not ring(c) and c not in QUIET and c not in NOLIT]
        wmax = max(weight[c] for c in pool)
        mw = p["min_w"][k] if isinstance(p["min_w"], dict) else p["min_w"]
        pool = [c for c in pool if weight[c] >= mw * wmax]
        gam = p["gamma"][k]
        for c in es_order(pool, lambda c: (weight[c] / wmax) ** gam):
            if placed >= p["target"][k]:
                break
            g = p["gap0"] + p["gap1"] * min(1.0, info[c][0])
            rr = int(math.ceil(g))
            if any((k, c[1] + i, c[2] + j) in lit and (k, c[1] + i, c[2] + j) not in src
                   for i in range(-rr, rr + 1) for j in range(-rr, rr + 1) if (i or j) and i * i + j * j < g * g):
                continue
            if violates(lit, src, c, True, info[c][2]):
                continue
            lit[c] = LIME
            placed += 1
    # 5. colour: an exact number of white tokens per key, leaning to the far end, never next to the source
    for k in ART:
        cand = [c for c in lit if c[0] == k and c not in src and info[c][2] >= p["white_min_r"]
                and not (k == 4 and near_boxes(c, UB, M_WHITE))]
        for c in es_order(cand, lambda c: p["white_base"] + min(1.0, info[c][0]), rnd_colour[k])[:p["white"][k]]:
            lit[c] = WHITE
    # 6. depth: a few dim tokens at the far ends
    for k, want in p["depth"].items():
        placed = 0
        far = [c for c in weight if c[0] == k and c not in lit and info[c][0] >= p["depth_from"]
               and not (k == 4 and near_boxes(c, UB, M_WHITE))]
        for c in es_order(far, lambda c: weight[c], rnd_depth[k]):
            if placed >= want:
                break
            if c in lit or violates(lit, src, c, False, info[c][2]):
                continue
            lit[c] = MID
            placed += 1
    return lit, src, info, weight


# ---------------------------------------------------------------- checks on the art (mirror the rules)
def art_checks(lit, src, info):
    fails = []
    marks = {c for c in lit if c not in src}
    bright = {c for c in marks if lit[c] in BRIGHT}
    n = {k: sum(1 for c in bright if c[0] == k) for k in ART}
    for k in ART:
        fl = [c for c in bright if c[0] == k]
        if fl and sum(1 for c in fl if lit[c] == LIME) * 3 < len(fl):
            fails.append("key %d: less than a third lime" % k)
    for c in marks:
        k, a, b = c
        if c in QUIET:
            fails.append("quiet cell lit %s" % (c,))
        if ring(c):
            fails.append("ring cell lit %s" % (c,))
        if c in NOLIT or c in CLEAR:
            fails.append("lit in the URL clearing %s" % (c,))
        for i, j in ((1, 0), (0, 1)):
            if (k, a + i, b + j) in marks and (k, a + 2 * i, b + 2 * j) in marks:
                fails.append("straight run of 3 at %s" % (c,))
        for i, j in ((1, 1), (1, -1)):
            if (k, a + i, b + j) in marks and (k, a + 2 * i, b + 2 * j) in marks:
                fails.append("diagonal of 3 at %s" % (c,))
        if c in bright:
            for oa in (-2, -1, 0):
                for ob in (-2, -1, 0):
                    if sum(1 for x in range(3) for y in range(3) if (k, a + oa + x, b + ob + y) in bright) > 4:
                        fails.append("clump at %s" % (c,))
            if info[c][2] >= 2.5:
                for i, j in ((1, 0), (0, 1)):
                    if sum(1 for m in range(7) if (k, a + m * i, b + m * j) in bright) >= 4:
                        fails.append("dotted line at %s" % (c,))
        if info[c][2] >= 1.0 and any((k, a + i, b + j) in marks for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            fails.append("side-by-side pair at %s" % (c,))
        for i, j in ((1, 0), (0, 1)):
            if (k, a + 2 * i, b + 2 * j) in marks and (k, a + 4 * i, b + 4 * j) in marks:
                fails.append("three every other cell at %s" % (c,))
        if info[c][2] >= 2.5 and len(_chain(c, lambda x: x in marks)) > 3:
            fails.append("chain of more than 3 corner-touching marks at %s" % (c,))
        if k == 4 and lit[c] != LIME and near_boxes(c, UB, M_WHITE):
            fails.append("white or depth within %d px of the URL at %s" % (M_WHITE, c))
    for c in [c for c in src if c in lit]:                       # ledges: a source row or column run on by debris
        k, a, b = c
        for i, j in ((1, 0), (0, 1)):
            run = [c]
            for sg in (1, -1):
                m = 1
                while (k, a + sg * m * i, b + sg * m * j) in lit:
                    run.append((k, a + sg * m * i, b + sg * m * j)); m += 1
            if sum(1 for x in run if x not in src) >= 2:
                fails.append("ledge at %s" % (c,))
    for k in ART:
        nc, nr = dims(k)
        for m in range(max(nc, nr)):
            col = sum(1 for t in range(nr) if (k, m, t) in marks)
            row = sum(1 for t in range(nc) if (k, t, m) in marks)
            if col > 3 or row > 3:
                fails.append("row/column of dots, key %d" % k)
            if (m in (0, nc - 1) and col > 2) or (m in (0, nr - 1) and row > 2):
                fails.append("marks along the board edge, key %d" % k)
            if k == 4 and row > ROW4:
                fails.append("key 4: more than %d marks on row %d" % (ROW4, m))
        if any((k, a, b) in marks for a in (0, nc - 1) for b in (0, nr - 1)):
            fails.append("corner, key %d" % k)
    _, _, sa1, sb1 = src_bounds(src)
    for c in marks:
        if c[0] == 5 and any((5, c[1] + i, c[2] + j) in src for i in (-1, 0, 1) for j in (-1, 0, 1)):
            if lit[c] == MID or c[1] >= sa1 or c[2] >= sb1:
                fails.append("mark against the source's right / bottom, or depth on it")
    nl = sum(1 for x in lit.values() if x == LIME); nw = sum(1 for x in lit.values() if x == WHITE)
    wf = nw / max(1, nl + nw)
    if not (0.34 <= wf <= 0.44):
        fails.append("white %.2f" % wf)
    return sorted(set(fails)), n, wf


# ---------------------------------------------------------------- scores used to rank seeds (by eye after)
def continuity(lit, src):
    """Tokens leaving one key meet tokens entering the next near the same panel line (0-15):
    key 5 top <-> key 2 bottom (x), key 2 right <-> key 3 left (y), key 5 left <-> key 4 right (y)."""
    m = {c for c in lit if c not in src}
    def xs(k, rows):
        return [ctr(c)[0] for c in m if c[0] == k and c[2] in rows]
    def ys(k, colsel):
        return [ctr(c)[1] for c in m if c[0] == k and colsel(c[1])]
    near = lambda A, B, tol: sum(1 for p in A if any(abs(p - q) <= tol for q in B))
    up5, in2 = xs(5, (1, 2)), xs(2, (10, 11))
    out2, in3 = ys(2, lambda a: a >= 9), ys(3, lambda a: a <= 2)
    out5, in4 = ys(5, lambda a: a <= 2), ys(4, lambda a: a >= 8)
    sc = 0
    for A, B in ((up5, in2), (out2, in3), (out5, in4)):
        sc += min(near(A, B, 6.0), 3) + min(near(B, A, 6.0), 2)
    return sc


def frame_balance(lit):
    """Key 4: lit tokens above the URL, beside '/usage' and below it; and the share on the right half."""
    m = [c for c in lit if c[0] == 4]
    above = sum(1 for c in m if cpx(c)[1] < UB[0][1])
    below = sum(1 for c in m if cpx(c)[1] >= UB[1][3])
    beside = len(m) - above - below
    right = sum(1 for c in m if ctr(c)[0] > v.window_centre(4)[0])
    return above, beside, below, right


# ---------------------------------------------------------------- compose
def compose(seed=SEED, slogan="right", p=P):
    img = Image.new("RGB", (W, H), INK)
    lit, src, info, weight = plume(seed, p)
    for k in ART:
        v.draw_board(img, k, {(a, b): col for (kk, a, b), col in lit.items() if kk == k},
                     skip={(a, b) for (kk, a, b) in CLEAR if kk == k} if k == 4 else ())
    logo_box = v.logo(img, LOGO_XY)
    ub = v.text(img, URL_PEN, URL_CAP, URL, URL_SIZE, TRACK, URL_LEAD, "left")
    al, pen, cap = SLOGANS[slogan]
    sb = v.text(img, pen, cap, SLOGAN, SLOGAN_SIZE, TRACK, SLOGAN_LEAD, al)
    fails, n, wf = art_checks(lit, src, info)
    assert ub == UB, (ub, UB)

    text_only = Image.new("RGB", (W, H), INK)
    v.text(text_only, URL_PEN, URL_CAP, URL, URL_SIZE, TRACK, URL_LEAD, "left")
    v.text(text_only, pen, cap, SLOGAN, SLOGAN_SIZE, TRACK, SLOGAN_LEAD, al)

    def ink_centroid(win):
        """Coverage-weighted centre of the type alone (tokens excluded) inside a window."""
        x0, y0, x1, y1 = win
        px = text_only.load(); sx = sy = sw = 0.0
        for y in range(y0, y1):
            for x in range(x0, x1):
                w = max(0.0, (sum(px[x, y]) - sum(INK)) / (765.0 - sum(INK)))
                sx += w * (x + 0.5); sy += w * (y + 0.5); sw += w
        return sx / sw, sy / sw

    def block(boxes, key):
        bx = v.ink_box(boxes)
        cx, cy = v.window_centre(key)
        gx, gy = ink_centroid(v.WINDOWS[key - 1])
        return {"ink": [bx[0], bx[1], bx[2] - 1, bx[3] - 1], "line_ink": boxes,
                "bbox_offset_vs_window": list(v.centre_offset(bx, key)),
                "ink_centroid_offset_vs_window": [round(gx - cx, 1), round(gy - cy, 1)]}

    tokens = {}
    for k in ART:
        cs = cells(k)
        fl = [c for c in cs if lit.get(c) in BRIGHT and c not in src]
        tokens["key%d" % k] = {"lime": sum(1 for c in fl if lit[c] == LIME), "white": sum(1 for c in fl if lit[c] == WHITE),
                               "source_lime": sum(1 for c in cs if c in src and c in lit),
                               "depth_639840": sum(1 for c in cs if lit.get(c) == MID),
                               "drawn": len(cs) - (len(CLEAR) if k == 4 else 0),
                               "unlit_2C2F2B": sum(1 for c in cs if c not in lit and not (k == 4 and c in CLEAR))}
    a0, b0, nc, nr = p["src"]
    sx0, sy0 = v.cell_px(5, a0, b0)
    meta = {
        "version": "v8a burst reaches url", "seed": seed,
        "layout": {"key1": "logo", "key2": "the plume", "key3": "the dust", "key4": "URL + landed debris",
                   "key5": "the source block and the radial blast", "key6": "slogan"},
        "logo": {"xy": list(LOGO_XY), "size": [logo_box[2] - logo_box[0], logo_box[3] - logo_box[1]],
                 "bbox_offset_vs_window": list(v.centre_offset(logo_box, 1))},
        "boards": {"key%d" % k: {"board": v.BOARDS[k], "px": v.board_px(k), "offset_vs_window": v.board_offset(k)}
                   for k in ART},
        "url": dict(size=URL_SIZE, leading=URL_LEAD, tracking=TRACK, pen_x=URL_PEN, cap_top=URL_CAP, align="left",
                    clearing_cells=len(CLEAR), clear_margin_px=M_CLEAR, lit_margin_px=M_LIT, **block(ub, 4)),
        "slogan": dict(size=SLOGAN_SIZE, leading=SLOGAN_LEAD, tracking=TRACK, align=al, pen_x=pen, cap_top=cap,
                       **block(sb, 6)),
        "source": {"cells": [a0, b0, nc, nr], "px": [sx0, sy0, sx0 + PITCH * nc - 3, sy0 + PITCH * nr - 3],
                   "lit": sum(1 for c in src if c in lit)},
        "tokens": tokens, "bright_flying": n, "white_share_of_bright": round(wf, 3),
        "frame_above_beside_below_right": frame_balance(lit), "continuity_0_15": continuity(lit, src),
        "art_fails": fails,
    }
    return img, meta, (lit, src, info)


def ascii(lit, src):
    """Each art board as text: . unlit, L lime, W white, d depth, S source, s eroded source, q quiet, space cleared."""
    out = []
    for k in (2, 3, 5, 4):
        nc, nr = dims(k)
        out.append("key %d" % k)
        for b in range(nr):
            row = ""
            for a in range(nc):
                c = (k, a, b)
                if c in CLEAR:
                    ch = " "
                elif c in src:
                    ch = "S" if c in lit else "s"
                elif c in lit:
                    ch = {LIME: "L", WHITE: "W", MID: "d"}[lit[c]]
                else:
                    ch = "q" if c in QUIET else "."
                row += ch + " "
            out.append("  " + row)
    return "\n".join(out)


def weight_map(lit, src, weight):
    """Weights per board as digits 0-9 of the key's maximum; S source, ' ' cleared, x not eligible for lit."""
    out = []
    for k in (2, 3, 5, 4):
        nc, nr = dims(k)
        pool = [c for c in weight if c[0] == k and not ring(c) and c not in QUIET and c not in NOLIT]
        wmax = max(weight[c] for c in pool)
        out.append("key %d (max %.3f)" % (k, wmax))
        for b in range(nr):
            row = ""
            for a in range(nc):
                c = (k, a, b)
                if c in CLEAR:
                    ch = " "
                elif c in src:
                    ch = "S"
                elif c not in pool:
                    ch = "x"
                else:
                    ch = str(min(9, int(10 * weight[c] / wmax)))
                    if c in lit:
                        ch = {LIME: "L", WHITE: "W", MID: "d"}[lit[c]] if weight[c] / wmax < 0.1 else ch + "*"
                        ch = ch[-2:]
                row += ch.ljust(3)
            out.append("  " + row)
    return "\n".join(out)


def elongation(cs):
    """Bright-token PCA: (axis angle in degrees, y up, folded to -90..90; sqrt of the eigenvalue ratio)."""
    pts = [ctr(c) for c in cs]
    if len(pts) < 3:
        return 0.0, 0.0
    mx = sum(q[0] for q in pts) / len(pts); my = sum(q[1] for q in pts) / len(pts)
    sxx = sum((q[0] - mx) ** 2 for q in pts); syy = sum((q[1] - my) ** 2 for q in pts)
    sxy = sum((q[0] - mx) * (q[1] - my) for q in pts)
    ang = 0.5 * math.degrees(math.atan2(2 * sxy, sxx - syy))         # image y down
    tr, det = sxx + syy, sxx * syy - sxy * sxy
    disc = math.sqrt(max(0.0, tr * tr / 4 - det))
    l1, l2 = tr / 2 + disc, tr / 2 - disc
    return round(-ang, 1), round(math.sqrt(l1 / max(l2, 1e-9)), 2)


def shapes(lit, src):
    return {k: elongation([c for c in lit if c[0] == k and c not in src and lit[c] in BRIGHT]) for k in ART}


def burned_halos(img):
    """(luma halo worst, rgb halo worst, jpeg bytes) of the image as burned (q97, decoded like the deck)."""
    data = v.c.v6.jpeg(img, v.c.QUALITY)
    seen = v.c.v6.decode_box(data)
    return v.c.v6.halo(seen)[1], max(v.rgb_halo(seen)[0]), len(data)


def score(lit, src):
    fb = frame_balance(lit)
    return continuity(lit, src) + min(fb[0], 2) + min(fb[1], 2) + min(fb[2], 2) + min(fb[3], 6) - 4


def search(N, top=40):
    ok = []
    for s in range(1, N + 1):
        lit, src, info, _ = plume(s)
        fails, n, wf = art_checks(lit, src, info)
        if fails:
            continue
        sh = shapes(lit, src)
        ok.append((score(lit, src), s, round(wf, 3), frame_balance(lit), continuity(lit, src), sh[2], sh[3]))
    ok.sort(key=lambda o: (-o[0] - min(o[5][1], 2.5) - min(o[6][1], 2.0), o[1]))
    print(len(ok), "of", N, "seeds pass every art rule; best score (continuity + key 4 frame) first")
    rows = []
    for o in ok[:top]:
        img, meta, _ = compose(o[1])
        lh, ch, nb = burned_halos(img)
        rows.append(o + (lh, ch, nb))
        print("score %d seed %d white %.3f frame %s cont %d key2 %s key3 %s | luma %.1f rgb %d jpeg %d" % (o + (lh, ch, nb)))
    return rows


def run(seed, out, slogan):
    img, meta, _ = compose(seed, slogan)
    checks = v.render(img, out, extra={"layout": meta})
    show = {k: x for k, x in checks.items() if k != "layout"}
    print(json.dumps(show, indent=1, default=str))
    print(json.dumps(meta, indent=1, default=str))
    return checks, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=None)
    ap.add_argument("--slogan", default="right", choices=("right", "left"))
    ap.add_argument("--search", type=int, default=0)
    ap.add_argument("--ascii", action="store_true")
    a = ap.parse_args()
    if a.search:
        search(a.search)
        return
    if a.ascii:
        lit, src, info, weight = plume(a.seed)
        print(ascii(lit, src))
        print(weight_map(lit, src, weight))
        print(art_checks(lit, src, info))
        return
    if a.out:
        results = [run(a.seed, a.out, a.slogan)]
    else:
        results = [run(SEED, HERE, "right"),                                         # the final
                   run(SEED, os.path.join(HERE, "alt-slogan-flush-left"), "left")]   # the alternative alignment
    for checks, meta in results:
        print("hard_rules_pass %s | art_fails %s | luma halo %.1f | rgb halo %s | jpeg %d bytes"
              % (checks["hard_rules_pass"], meta["art_fails"], checks["halo_worst"], checks["rgb_halo_worst"],
                 checks["jpeg_bytes"]))
    if any(not ch["hard_rules_pass"] or m["art_fails"] for ch, m in results):
        raise SystemExit("FAIL: a hard rule or an art rule does not hold")


if __name__ == "__main__":
    main()
