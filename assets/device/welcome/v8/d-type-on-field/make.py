#!/usr/bin/env python3
"""Token Deck welcome v8, candidate d: TYPE ON THE FIELD. Own code; imports v8_common (and through it
v7_common / welcome_v7, all unchanged).

Layout   key 1 logo                 | key 2 art: the stream falls  | key 3 art: the source
         key 4 URL printed on field | key 5 art: the stream turns  | key 6 slogan
Idea     Every key 2-5 shows its full v8_common board of unlit #2C2F2B tokens, key 4 included. The URL is
         printed over key 4's field the way a headline sits on the stigg.io hero's particle field: the only
         cells left out are those whose 3 x 3 token comes within 1 px of the URL's ink sideways or within
         one token pitch (5 px) above or below it (plus single cells that would be stranded between two
         left-out cells), so the dim grid surrounds the two lines and follows their lengths: the pocket
         after the shorter '/usage' keeps its tokens. The literal 1 px knockout (alt-tight-knockout/)
         leaves token rows 2 px from the i-dots and the descenders; the v7 photo shows the dim tokens far
         brighter than lcd() and the dome ghosting the type down-right, so at arm's length those rows
         crowd the URL. The extra pitch above and below is the fix; it costs 19 grid cells (63 left out, not 44).
         The burst is a cascade that ends at the URL, as v6's burst ended on its URL (note 1): a solid lime
         source block at the right of key 3 is bitten and eroded on its left; the debris blows left through
         the bezel into key 2, falls through key 2 and the bezel into key 5, turns left through the bezel
         into key 4 and parts around the end of the URL, above and below it. Key 2's empty corner is the
         one next to the logo, key 5's the one next to the slogan. Key 4 keeps white for the type: its
         landed tokens are lime only, never level with a line's end (where a dot reads as punctuation), at
         least 5 px from any ink, never in the same column above and below (no frame).
Type     Soehne Buch through v8_common.text. URL 10.5 px / 13 px, tracking -0.06, flush left, pen x 28,
         cap top 156: ink x 28-71 (an anti-aliased column of the first 'i' at x 27) by y 156-178, centred
         on window 4 to (-0.5, -0.5), the board's own offset, so the grid sits 4 px from the stems on both
         sides. Slogan 9.5 px / 12 px, flush right with its last ink column on x 290 (291 rings outside the
         tile: halo 5.0), cap top 152: ink x 234-290 by y 152-182, the same 167.5 centre line as the URL.
Rules    The brief's art rules, enforced while placing and re-checked (art_checks), with two adaptations:
         lit tokens never touch a board's outer ring (every board edge is 6-12 px from its window edge, and
         v7's photo shows the bevel reflecting tokens at 16 px), so the ring inside it counts as the lit
         edge (at most 2 marks per edge row or column, its corners unlit). Added: no dotted line of 3 (one
         empty cell between), no square of 4 (a dice face), key 4 at most 2 marks per row or column.

usage: make.py                  render SEED here and the tight-knockout alternative into alt-tight-knockout/
                                (exits 1 if a hard rule or an art rule fails in the main render)
       make.py --seed N [--out DIR] [--dil H V]
       make.py --search N       list seeds 1..N that pass every art rule, best first
"""
import argparse, json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WELCOME = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WELCOME)
import v8_common as v                                   # noqa: E402
from PIL import Image                                   # noqa: E402

W, H = v.W, v.H
INK, LIME, WHITE, UNLIT, MID = v.INK, v.LIME, v.WHITE, v.UNLIT, v.MID_LIME
BRIGHT = (LIME, WHITE)
PITCH, SQ = v.PITCH, v.SQ
ART = (3, 2, 5, 4)                                      # the flow, source key first
SEED = 263                                              # chosen by eye among the seeds 1-600 that pass every art rule
RGB_MARGIN = 8                                          # seed choice: colour halo at most 8 (the hard limit is 10)
ALT_DIR = os.path.join(HERE, "alt-tight-knockout")

# ---------------------------------------------------------------- type
URL = ["io.stigg.io", "/usage"]
SLOGAN = ["The AI Usage", "Management", "Console"]
URL_PEN, URL_CAP, URL_SIZE, URL_LEAD = 28, 156, 10.5, 13          # pen = left ink edge
SLOGAN_PEN, SLOGAN_CAP, SLOGAN_SIZE, SLOGAN_LEAD = 291, 152, 9.5, 12   # pen = right ink edge, exclusive
TRACK = -0.06
DIL = (1, 5)                # knockout: within 1 px of the ink sideways, within a token pitch (5 px) above / below
CLEAR = 5                   # lit tokens in key 4 keep at least 5 empty px from the ink
PUNCT = 15                  # px after a line's last glyph where a lit dot reads as punctuation or a cursor
ROW_MAX = {4: 2}            # marks per row / column (3 elsewhere): key 4's landed dust stays loose


def url_ink():
    m = Image.new("RGB", (W, H), INK)
    lines = v.text(m, URL_PEN, URL_CAP, URL, URL_SIZE, TRACK, URL_LEAD, "left")
    px = m.load()
    return {(x, y) for y in range(H) for x in range(W) if px[x, y] != INK}, lines


INKSET, URL_LINES = url_ink()                           # every pixel the URL changes, and its line boxes
URL_BOX = (min(x for x, _ in INKSET), min(y for _, y in INKSET), max(x for x, _ in INKSET), max(y for _, y in INKSET))


def ink_gap(a, b):
    """Empty px between key 4 cell (a, b)'s token and the nearest URL ink pixel (Chebyshev)."""
    x, y = v.cell_px(4, a, b)
    return min(max(max(0, x - px, px - (x + SQ - 1)), max(0, y - py, py - (y + SQ - 1))) - 1 for (px, py) in INKSET)


GAP4 = {(4, a, b): ink_gap(a, b) for (a, b) in v.board_cells(4)}


def knockout(dil):
    """Key 4 cells left out under the URL: the token touches the ink dilated by dil = (side, vertical)
    px, plus single cells that would be stranded between two left-out cells."""
    dh, dv = dil
    ko = set()
    for (a, b) in v.board_cells(4):
        x, y = v.cell_px(4, a, b)
        if any(x - dh <= px <= x + SQ - 1 + dh and y - dv <= py <= y + SQ - 1 + dv for (px, py) in INKSET):
            ko.add((4, a, b))
    changed = True
    while changed:
        changed = False
        for (a, b) in v.board_cells(4):
            if (4, a, b) not in ko and (((4, a, b - 1) in ko and (4, a, b + 1) in ko)
                                        or ((4, a - 1, b) in ko and (4, a + 1, b) in ko)):
                ko.add((4, a, b)); changed = True
    return ko


KO = knockout(DIL)


def set_knockout(dil):
    global DIL, KO
    DIL, KO = tuple(dil), knockout(dil)
    FIELDS.clear()


def knock_gaps():
    """Empty px between the URL's ink and the surviving tokens: straight out from each side of its ink box
    (tokens level with it, or over / under it), and the smallest gap in any direction (diagonal)."""
    x0, y0, x1, y1 = URL_BOX
    side = {"left": [], "right": [], "above": [], "below": [], "any": []}
    for (a, b) in v.board_cells(4):
        if (4, a, b) in KO:
            continue
        x, y = v.cell_px(4, a, b)
        g = GAP4[(4, a, b)]
        level, under = y + SQ - 1 >= y0 and y <= y1, x + SQ - 1 >= x0 and x <= x1
        if level and x + SQ - 1 < x0: side["left"].append(g)
        if level and x > x1: side["right"].append(g)
        if under and y + SQ - 1 < y0: side["above"].append(g)
        if under and y > y1: side["below"].append(g)
        side["any"].append(g)
    return {k: min(g) for k, g in side.items()}


def beside_type(k, a, b):
    """A key-4 token level with one of the URL's lines and within PUNCT px after its last glyph reads as
    a period, a cursor or a status dot: no lit token there (the pocket after '/usage' stays dim)."""
    if k != 4:
        return False
    x, y = v.cell_px(k, a, b)
    for (x0, y0, x1, y1) in URL_LINES:                  # exclusive right / bottom
        if y + SQ - 1 >= y0 and y <= y1 - 1 and x + SQ - 1 >= x1 and x <= x1 - 1 + PUNCT:
            return True
    return False


# ---------------------------------------------------------------- boards
NCR = {k: (v.BOARDS[k][2], v.BOARDS[k][3]) for k in ART}
QUIET = {(k, a, b) for k in ART for (a, b) in v.quiet(k)}


def cells(k):
    return [(k, a, b) for (a, b) in v.board_cells(k)]


ALL = [c_ for k in ART for c_ in cells(k)]


def ring(c_):
    """The board's outer ring, plus the corners of the ring inside it (the lit edge never turns a corner)."""
    k, a, b = c_
    nc, nr = NCR[k]
    return a in (0, nc - 1) or b in (0, nr - 1) or (a in (1, nc - 2) and b in (1, nr - 2))


def centre(c_):
    x, y = v.cell_px(*c_)
    return x + SQ / 2.0, y + SQ / 2.0


# ---------------------------------------------------------------- the cascade (after welcome_v7's burst)
def catmull(points, n=60):
    """Dense polyline through the control points (Catmull-Rom)."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for s in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[s - 1], pts[s], pts[s + 1], pts[s + 2]
        for t in [q / n for q in range(n)]:
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[a]) + (-p0[a] + p2[a]) * t + (2 * p0[a] - 5 * p1[a] + 4 * p2[a] - p3[a]) * t2
                                    + (-p0[a] + 3 * p1[a] - 3 * p2[a] + p3[a]) * t3) for a in (0, 1)))
    out.append(points[-1])
    return out


def project(poly, cum, p):
    """Arc length s of the nearest spine point and the signed distance q from it."""
    best = (1e9, 0, 0.0)
    for n in range(len(poly) - 1):
        ax, ay = poly[n]; bx, by = poly[n + 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        qx, qy = p[0] - (ax + t * dx), p[1] - (ay + t * dy)
        d = math.hypot(qx, qy)
        if d < best[0]:
            side = 1.0 if (dx * qy - dy * qx) < 0 else -1.0
            best = (d, cum[n] + t * math.sqrt(L2), side * d)
    return best[1], best[2]


P = dict(
    # panel px: out of key 3's source to the left, across key 2 and down through the bezel into key 5,
    # left again through the bezel into key 4, ending at the end of the URL (an S, empty corners at the
    # logo and at the slogan)
    spine=[(267, 58), (245, 58), (215, 57), (187, 57), (169, 62), (161, 76), (158, 100), (160, 141),
           (156, 158), (146, 171), (125, 177), (97, 176), (72, 172)],
    src=(6, 3, 4, 6),              # key 3 source block: a0, b0, cols, rows (x 269-286, y 43-70)
    erode=0.4,                     # pixelmark erosion of its left columns, strongest at the bottom
    lam_n=12.0, th0=198.0, aim=2.0,   # near field: blast from the source's left edge (px decay, deg y up, focus)
    fringe=0.35,                   # extra weight right against the source's left edge or its bitten corner
    band_w=(9.0, 0.05), soft=0.45, lam_f=260.0, band_lo=0.16,   # the stream between clusters
    clusters=[(249, 60, 10, 7, 0.45),     # key 3: where the debris leaves for key 2
              (182, 56, 12, 8, 1.0),      # key 2: where the stream arrives from key 3
              (161, 76, 11, 8, 0.9),      # key 2: where it bends down
              (162, 150, 12, 8, 0.8),     # key 5: where it arrives from key 2
              (142, 174, 12, 8, 0.65),    # key 5: where it turns left
              (64, 148, 10, 5, 0.45),     # key 4: the stream parts around the end of the URL, above ...
              (64, 187, 10, 5, 0.45)],    # ... and below
    jitter=4.0,                    # seeded jitter of each cluster centre (px)
    target={3: 12, 2: 17, 5: 13, 4: 4},  # flying bright tokens per key (key 3: beyond the source)
    white={3: 6, 2: 10, 5: 8, 4: 0},     # 24 of 65 bright (37 %); key 4 keeps white for the type
    white_base=0.30, white_min_r=1.5,    # white leans to the far end, never next to the source
    depth={5: 1, 4: 1}, depth_from=0.6, depth_min_w=0.3,   # #639840 inside the far stream only
    min_w=0.05, min_w_key={3: 0.06, 4: 0.4},   # cells under this fraction of their key's peak weight never light
    gap0=1.0, gap1=0.4,            # min centre distance between bright tokens, cells: gap0 + gap1 * s/S
)


class Field:
    """Seed-independent geometry of the cascade."""

    def __init__(self, p):
        self.p = p
        self.poly = catmull(p["spine"])
        self.cum = [0.0]
        for a_, b_ in zip(self.poly, self.poly[1:]):
            self.cum.append(self.cum[-1] + math.hypot(b_[0] - a_[0], b_[1] - a_[1]))
        self.S = self.cum[-1]
        a0, b0, nc, nr = p["src"]
        self.rect = {(3, a, b) for a in range(a0, a0 + nc) for b in range(b0, b0 + nr)}
        src = set(self.rect)
        for corner in [(a0, b0 + nr - 1), (a0, b0 + nr - 2), (a0 + 1, b0 + nr - 1), (a0, b0)]:
            src.discard((3,) + corner)             # the burst corner (bottom left) bitten, the top left rounded
        self.src = src                             # its rounded corners and eroded cells stay empty
        self.src_a0, self.src_a1, self.src_b0, self.src_b1 = a0, a0 + nc - 1, b0, b0 + nr - 1
        src_pts = [centre(c_) for c_ in src]
        self.ox = v.cell_px(3, a0, b0)[0]          # blast origin: the source's left edge, two thirds down
        self.oy = v.cell_px(3, a0, b0)[1] + (PITCH * nr - (PITCH - SQ)) * 0.66
        self.info = {}
        for c_ in ALL:
            if c_ in self.rect:
                continue
            cx, cy = centre(c_)
            s, q = project(self.poly, self.cum, (cx, cy))
            r = (min(math.hypot(cx - x, cy - y) for x, y in src_pts) - PITCH) / PITCH if c_[0] == 3 else 99.0
            self.info[c_] = (s, q, r)

    def free(self, c_):
        return c_ not in self.rect and c_ not in KO and c_ not in QUIET and not ring(c_) \
            and (c_[0] != 4 or (GAP4[c_] >= CLEAR and not beside_type(*c_)))


FIELDS = {}


def field(p=P):
    key = json.dumps(p, sort_keys=True)
    if key not in FIELDS:
        FIELDS[key] = Field(p)
    return FIELDS[key]


def touches_source_wrongly(F, a, b):
    """Debris may touch the source only on its left side and under its bitten bottom-left corner."""
    return a >= F.src_a1 or b <= F.src_b0 or (b >= F.src_b1 and a >= F.src_a0 + 2)


def violates(F, lit, cell, bright):
    """Why lighting `cell` would read as a mistake, or None. Source cells never count as marks."""
    k, a, b = cell
    src = F.src
    r_src = F.info[cell][2]
    if not F.free(cell):
        return "not free"
    if any((k, a + da, b + db) in src for da in (-1, 0, 1) for db in (-1, 0, 1)):
        if not bright:
            return "depth on the source"
        if touches_source_wrongly(F, a, b):
            return "debris on the source's crisp side"
    marked = lambda c_: c_ == cell or (c_ in lit and c_ not in src)
    is_bright = lambda c_: (c_ == cell and bright) or (c_ in lit and c_ not in src and lit[c_] in BRIGHT)
    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):            # beyond the debris, tokens touch only at corners
        nb = (k, a + da, b + db)
        if marked(nb) and (r_src >= 1.0 or F.info[nb][2] >= 1.0):
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
        for o in (-4, -2, 0):                                    # no dotted line of 3, one cell between
            if all(marked((k, a + (o + n) * da, b + (o + n) * db)) for n in (0, 2, 4)):
                return "even dots"
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
    for d in (2, 3):                                             # no square of 4 (a dice face)
        for oa in (0, -d):
            for ob in (0, -d):
                if all(marked((k, a + oa + x, b + ob + y)) for x in (0, d) for y in (0, d)):
                    return "square"
    if k == 4:                                                   # above vs below the URL: never one column (a frame)
        up = v.cell_px(k, a, b)[1] < URL_BOX[1]
        if any(c_[0] == 4 and c_[1] == a and (v.cell_px(*c_)[1] < URL_BOX[1]) != up for c_ in lit):
            return "mirrored"
    nc, nr = NCR[k]
    col = sum(1 for n in range(nr) if marked((k, a, n)))
    row = sum(1 for n in range(nc) if marked((k, n, b)))
    if col > ROW_MAX.get(k, 3) or row > ROW_MAX.get(k, 3):
        return "row"
    if (a in (1, nc - 2) and col > 2) or (b in (1, nr - 2) and row > 2):
        return "edge"                                            # the inner ring is the lit edge: at most 2 there
    return None


def es_order(cells_, wfun, r):
    """Weighted random order (Efraimidis-Spirakis): sampling without replacement by weight."""
    return sorted(cells_, key=lambda c_: -(r.random() ** (1.0 / max(wfun(c_), 1e-9))))


def weights(F, rnd, p):
    clusters = []
    for (x, y, ss, sq, amp) in p["clusters"]:
        s0, q0 = project(F.poly, F.cum, (x, y))
        clusters.append((s0 + rnd.uniform(-1, 1) * p["jitter"], q0 + rnd.uniform(-1, 1) * p["jitter"], ss, sq, amp))
    th0 = math.radians(p["th0"])
    weight = {}
    for c_, (s, q, r) in F.info.items():
        if not F.free(c_):
            continue
        cx, cy = centre(c_)
        near = 0.0
        if c_[0] == 3:
            dd = math.hypot(cx - F.ox, cy - F.oy)
            th = math.atan2(-(cy - F.oy), cx - F.ox)
            near = math.exp(-dd / p["lam_n"]) * (0.08 + 0.92 * max(0.0, math.cos(th - th0)) ** p["aim"])
            k, a, b = c_
            if (k, a + 1, b) in F.src or ((k, a, b - 1) in F.src and a <= F.src_a0 + 1):
                near += p["fringe"]
        w = p["band_w"][0] + p["band_w"][1] * s
        env = 1.0 / (1.0 + math.exp((abs(q) - w) / (p["soft"] * w)))
        cl = sum(amp * math.exp(-((s - s0) / ss) ** 2 / 2 - ((q - q0) / sq) ** 2 / 2) for s0, q0, ss, sq, amp in clusters)
        weight[c_] = near + p["band_lo"] * math.exp(-s / p["lam_f"]) * env + cl
    return weight


def floor_w(p, k, colour):
    f = p["min_w_key"].get(k, p["min_w"])
    return max(f, p["depth_min_w"]) if colour == MID else f


def cascade(seed, p=P):
    """One seeded burst: ({cell: colour}, the field, the per-cell weights)."""
    F = field(p)
    rnd = random.Random(seed)
    a0, b0, nc, nr = p["src"]
    lit = {}
    # 1. erosion: the source's left columns break off, most at the bottom (pixelmark: u > 0.5 erodes)
    for c_ in sorted(F.src, key=lambda c_: (c_[2], c_[1])):
        _, a, b = c_
        u = (a0 + nc - a) / nc                      # 1 at the left column
        vv = (b - b0 + 1) / nr                      # 1 at the bottom row
        if rnd.random() >= p["erode"] * max(0.0, (u - 0.5) / 0.5) ** 1.6 * (0.3 + 0.7 * vv):
            lit[c_] = LIME
    weight = weights(F, rnd, p)
    rnd_colour = {k: random.Random(seed * 7919 + 17 * k) for k in ART}      # colour and depth have their own
    rnd_depth = {k: random.Random(seed * 104729 + 3 * k) for k in ART}      # streams: they never move a token
    # 2. bright tokens, exact counts per key, in flow order
    for k in ART:
        wmax = max(weight[c_] for c_ in weight if c_[0] == k)
        cand = [c_ for c_ in weight if c_[0] == k and weight[c_] >= floor_w(p, k, LIME) * wmax]
        placed = 0
        for c_ in es_order(cand, lambda c_: weight[c_], rnd):
            if placed >= p["target"][k]:
                break
            g = p["gap0"] + p["gap1"] * F.info[c_][0] / F.S
            rr = int(math.ceil(g))
            _, a, b = c_
            if any((k, a + da, b + db) in lit and (k, a + da, b + db) not in F.src
                   for da in range(-rr, rr + 1) for db in range(-rr, rr + 1)
                   if (da or db) and da * da + db * db < g * g):
                continue
            if violates(F, lit, c_, True):
                continue
            lit[c_] = LIME
            placed += 1
    # 3. colour: an exact number of white tokens per key, leaning to the far end, never next to the source
    for k in ART:
        cand = [c_ for c_ in lit if c_[0] == k and c_ not in F.src and F.info[c_][2] >= p["white_min_r"]]
        for c_ in es_order(cand, lambda c_: p["white_base"] + F.info[c_][0] / F.S, rnd_colour[k])[:p["white"][k]]:
            lit[c_] = WHITE
    # 4. depth: a few dim tokens inside the far stream
    for k, want in p["depth"].items():
        wmax = max(weight[c_] for c_ in weight if c_[0] == k)
        far = [c_ for c_ in weight if c_[0] == k and c_ not in lit and F.info[c_][0] >= p["depth_from"] * F.S
               and weight[c_] >= floor_w(p, k, MID) * wmax]
        placed = 0
        for c_ in es_order(far, lambda c_: weight[c_], rnd_depth[k]):
            if placed >= want:
                break
            if violates(F, lit, c_, False):
                continue
            lit[c_] = MID
            placed += 1
    return lit, F, weight


# ---------------------------------------------------------------- checks on the art (mirror the rules)
def art_checks(lit, F, p=P, weight=None):
    fails = []
    src = F.src
    marks = {c_ for c_ in lit if c_ not in src}
    bright = {c_ for c_ in marks if lit[c_] in BRIGHT}
    if weight is not None:                                   # no stray far from the field
        for k in ART:
            wmax = max(weight[c_] for c_ in weight if c_[0] == k)
            for c_ in marks:
                if c_[0] == k and weight.get(c_, 0.0) < floor_w(p, k, lit[c_]) * wmax:
                    fails.append("stray at %s" % (c_,))
    n = {k: sum(1 for c_ in lit if c_[0] == k and lit[c_] in BRIGHT) for k in ART}
    if not (n[3] > n[2] > n[5] > n[4] >= 2):
        fails.append("counts do not fall along the flow %s" % n)
    for k in ART:
        flying = [c_ for c_ in bright if c_[0] == k]
        if len(flying) != p["target"][k]:
            fails.append("key %d: %d flying tokens, wanted %d" % (k, len(flying), p["target"][k]))
        if flying and sum(1 for c_ in flying if lit[c_] == LIME) * 3 < len(flying):
            fails.append("key %d: less than a third lime" % k)
    for c_ in marks:
        k, a, b = c_
        for da, db in ((1, 0), (0, 1)):
            if (k, a + da, b + db) in marks and (k, a + 2 * da, b + 2 * db) in marks:
                fails.append("straight run of 3 at %s" % (c_,))
            if (k, a + 2 * da, b + 2 * db) in marks and (k, a + 4 * da, b + 4 * db) in marks:
                fails.append("dotted line of 3 at %s" % (c_,))
        for da, db in ((1, 1), (1, -1)):
            if (k, a + da, b + db) in marks and (k, a + 2 * da, b + 2 * db) in marks:
                fails.append("diagonal of 3 at %s" % (c_,))
        for d in (2, 3):
            if all((k, a + x, b + y) in marks for x in (0, d) for y in (0, d)):
                fails.append("square of 4 at %s" % (c_,))
        if c_ in bright:
            if sum(1 for x in range(3) for y in range(3) if (k, a + x, b + y) in bright) > 4:
                fails.append("clump at %s" % (c_,))
            if F.info[c_][2] >= 2.5:
                for da, db in ((1, 0), (0, 1)):
                    if sum(1 for m_ in range(7) if (k, a + m_ * da, b + m_ * db) in bright) >= 4:
                        fails.append("4 bright within 7 cells at %s" % (c_,))
        if F.info[c_][2] >= 1.0 and any((k, a + x, b + y) in marks for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            fails.append("side-by-side pair at %s" % (c_,))
        if ring(c_):
            fails.append("lit on the outer ring or an inner-ring corner at %s" % (c_,))
        if c_ in QUIET:
            fails.append("lit quiet cell %s" % (c_,))
        if c_ in KO:
            fails.append("lit knocked-out cell %s" % (c_,))
        if k == 4 and (GAP4[c_] < CLEAR or beside_type(*c_)):
            fails.append("lit token beside the URL or %d px from it at %s" % (GAP4[c_], c_))
        if any((k, a + x, b + y) in src for x in (-1, 0, 1) for y in (-1, 0, 1)):
            if lit[c_] == MID or touches_source_wrongly(F, a, b):
                fails.append("mark on the source's crisp side, or depth on it, at %s" % (c_,))
    above = {c_[1] for c_ in marks if c_[0] == 4 and v.cell_px(*c_)[1] < URL_BOX[1]}
    below = {c_[1] for c_ in marks if c_[0] == 4 and v.cell_px(*c_)[1] > URL_BOX[3]}
    if above & below:
        fails.append("key 4: tokens above and below the URL share a column %s" % sorted(above & below))
    for c_ in [c_ for c_ in src if c_ in lit]:               # ledges: a source row or column run on by debris
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
        nc, nr = NCR[k]
        for m_ in range(max(nc, nr)):
            col = sum(1 for t in range(nr) if (k, m_, t) in marks)
            row = sum(1 for t in range(nc) if (k, t, m_) in marks)
            if col > ROW_MAX.get(k, 3) or row > ROW_MAX.get(k, 3):
                fails.append("row or column of more than %d marks, key %d" % (ROW_MAX.get(k, 3), k))
            if (m_ in (0, 1, nc - 2, nc - 1) and col > 2) or (m_ in (0, 1, nr - 2, nr - 1) and row > 2):
                fails.append("more than 2 marks along a board edge, key %d" % k)
        if any((k, a, b) in lit for a in (0, nc - 1) for b in (0, nr - 1)):
            fails.append("lit board corner, key %d" % k)
    nl = sum(1 for v_ in lit.values() if v_ == LIME); nw = sum(1 for v_ in lit.values() if v_ == WHITE)
    wf = nw / max(1, nl + nw)
    if not (0.34 <= wf <= 0.44):
        fails.append("white %.2f" % wf)
    return sorted(set(fails)), n, wf


def continuity(lit, F):
    """Tokens leaving one key meet tokens entering the next near the same row or column (0-18): key 3's
    left columns / key 2's right columns, key 2's bottom rows / key 5's top rows, key 5's left columns /
    key 4's right columns. Each pair of boards shares its panel rows or columns."""
    m = lambda c_: c_ in lit and c_ not in F.src
    out3 = [b for b in range(NCR[3][1]) for a in (1, 2) if m((3, a, b))]
    in2 = [b for b in range(NCR[2][1]) for a in (NCR[2][0] - 2, NCR[2][0] - 3) if m((2, a, b))]
    out2 = [a for a in range(NCR[2][0]) for b in (NCR[2][1] - 2, NCR[2][1] - 3) if m((2, a, b))]
    in5 = [a for a in range(NCR[5][0]) for b in (1, 2) if m((5, a, b))]
    out5 = [b for b in range(NCR[5][1]) for a in (1, 2) if m((5, a, b))]
    in4 = [b for b in range(NCR[4][1]) for a in (NCR[4][0] - 2, NCR[4][0] - 3) if m((4, a, b))]
    near = lambda x, y: sum(1 for i in x if any(abs(i - j) <= 1 for j in y))
    return (min(near(out3, in2), 3) + min(near(in2, out3), 3) + min(near(out2, in5), 3) + min(near(in5, out2), 3)
            + min(near(out5, in4), 3) + min(near(in4, out5), 3))


# ---------------------------------------------------------------- compose
def slogan_mass(boxes):
    """Horizontal centre of the slogan's ink, each line weighted by its width (where the eye puts it)."""
    tot = sum(b[2] - b[0] for b in boxes)
    return sum((b[2] - b[0]) * (b[0] + b[2]) / 2.0 for b in boxes) / tot


def compose(seed=SEED, p=P):
    img = Image.new("RGB", (W, H), INK)
    lit, F, weight = cascade(seed, p)
    for k in ART:
        v.draw_board(img, k, lit={(a, b): col for (kk, a, b), col in lit.items() if kk == k},
                     skip={(a, b) for (kk, a, b) in KO if kk == k})
    logo_box = v.logo(img)
    ub = v.text(img, URL_PEN, URL_CAP, URL, URL_SIZE, TRACK, URL_LEAD, "left")
    sb = v.text(img, SLOGAN_PEN, SLOGAN_CAP, SLOGAN, SLOGAN_SIZE, TRACK, SLOGAN_LEAD, "right")
    fails, n, wf = art_checks(lit, F, p, weight)
    ubox, sbox = v.ink_box(ub), v.ink_box(sb)
    true_url = (URL_BOX[0], URL_BOX[1], URL_BOX[2] + 1, URL_BOX[3] + 1)
    tokens = {}
    for k in ART:
        cs = cells(k)
        flying = [c_ for c_ in cs if lit.get(c_) in BRIGHT and c_ not in F.src]
        tokens["key%d" % k] = {
            "lime": sum(1 for c_ in flying if lit[c_] == LIME),
            "white": sum(1 for c_ in flying if lit[c_] == WHITE),
            "source_lime": sum(1 for c_ in cs if c_ in F.src and c_ in lit),
            "depth_639840": sum(1 for c_ in cs if lit.get(c_) == MID),
            "unlit_2C2F2B": sum(1 for c_ in cs if c_ not in lit and c_ not in KO),
            "left_out_under_url": sum(1 for c_ in cs if c_ in KO),
            "board_x0_y0_cols_rows": v.BOARDS[k], "board_px": v.board_px(k),
            "board_centre_offset_vs_window": v.board_offset(k)}
    a0, b0, nc, nr = p["src"]
    meta = {
        "candidate": "d-type-on-field", "seed": seed,
        "layout": {"key1": "logo", "key2": "art: the stream arrives from key 3 and falls",
                   "key3": "art: the source block and its debris", "key4": "URL printed over the field, landed tokens",
                   "key5": "art: the stream turns toward the URL", "key6": "slogan"},
        "logo": {"box_excl": logo_box, "centre_offset_vs_window": v.centre_offset(logo_box, 1)},
        "url": {"size_px": URL_SIZE, "leading_px": URL_LEAD, "tracking_px": TRACK, "pen_x": URL_PEN,
                "cap_top": URL_CAP, "align": "left", "line_ink_excl": ub, "ink_excl": ubox,
                "centre_offset_vs_window": v.centre_offset(ubox, 4),
                "ink_incl_antialias_excl": true_url, "centre_offset_incl_antialias": v.centre_offset(true_url, 4),
                "knockout": {"dilate_px_side_vertical": list(DIL), "cells_left_out": len(KO),
                             "min_gap_px_to_ink": knock_gaps(), "lit_clearance_px": CLEAR,
                             "punctuation_zone_px": PUNCT}},
        "slogan": {"size_px": SLOGAN_SIZE, "leading_px": SLOGAN_LEAD, "tracking_px": TRACK,
                   "right_edge_excl": SLOGAN_PEN, "cap_top": SLOGAN_CAP, "align": "right", "line_ink_excl": sb,
                   "ink_excl": sbox, "centre_offset_vs_window": v.centre_offset(sbox, 6),
                   "width_weighted_centre_offset_x": round(slogan_mass(sb) - v.window_centre(6)[0], 1)},
        "source": {"key": 3, "cells_a_b_cols_rows": [a0, b0, nc, nr],
                   "px": [v.cell_px(3, a0, b0)[0], v.cell_px(3, a0, b0)[1],
                          v.cell_px(3, a0 + nc - 1, 0)[0] + SQ - 1, v.cell_px(3, 0, b0 + nr - 1)[1] + SQ - 1],
                   "lit_cells": sum(1 for c_ in F.src if c_ in lit), "eroded": sum(1 for c_ in F.src if c_ not in lit)},
        "tokens": tokens,
        "bright_total": sum(n.values()), "white_share_of_bright": round(wf, 3),
        "art_fails": fails, "bezel_continuity_0_18": continuity(lit, F),
    }
    return img, meta, lit, F


def render(seed, out, dil=None):
    if dil:
        set_knockout(dil)
    img, meta, lit, F = compose(seed)
    checks = v.render(img, out, extra={"layout": meta})
    return checks, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dil", type=int, nargs=2, default=None)
    ap.add_argument("--search", type=int, default=0)
    a = ap.parse_args()
    if a.search:
        if a.dil:
            set_knockout(a.dil)
        ok = []
        for s in range(1, a.search + 1):
            lit, F, weight = cascade(s)
            fails, n, wf = art_checks(lit, F, P, weight)
            if fails:
                continue
            img, meta, lit, F = compose(s)
            rgb, _ = v.rgb_halo(v.c.v6.decode_box(v.c.v6.jpeg(img, v.c.QUALITY)))
            ok.append((max(rgb) <= RGB_MARGIN, continuity(lit, F), -max(rgb), s, n, round(wf, 3), rgb))
        ok.sort(key=lambda o: (-o[0], -o[1], -o[2], o[3]))
        print(len(ok), "of", a.search, "seeds pass every art rule;", sum(1 for o in ok if o[0]),
              "keep the colour halo <= %d; best bezel continuity first" % RGB_MARGIN)
        for o in ok[:40]:
            print(o[1:])
        return
    if a.out or a.dil or a.seed != SEED:
        checks, meta = render(a.seed, a.out or HERE, a.dil)
        alt = None
    else:
        checks, meta = render(SEED, HERE)
        alt, alt_meta = render(SEED, ALT_DIR, (1, 1))
        set_knockout((1, 5))
    print(json.dumps({k: v_ for k, v_ in checks.items() if k != "layout"}, indent=1, default=str))
    print(json.dumps(meta, indent=1, default=str))
    if alt is not None:
        print("alternative (literal 1 px knockout) in %s: hard_rules_pass %s, art_fails %s, cells left out %d, "
              "min gap to ink %s" % (ALT_DIR, alt["hard_rules_pass"], alt_meta["art_fails"],
                                     alt_meta["url"]["knockout"]["cells_left_out"],
                                     alt_meta["url"]["knockout"]["min_gap_px_to_ink"]))
    if not checks["hard_rules_pass"]:
        raise SystemExit("hard rules fail")
    if meta["art_fails"]:
        raise SystemExit("art rules fail: %s" % meta["art_fails"])


if __name__ == "__main__":
    main()
