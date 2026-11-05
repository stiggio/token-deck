"""Token Deck welcome screen v7, variant B "slogan under logo, tokens emitted by the logo" (Nov 2, 2026), own code.

Layout   key 1 logo          | key 2 tokens: the stream leaves the wordmark | key 3 tokens: the fan
         key 4 slogan         | key 5 tokens: falling out of the stream      | key 6 URL
Type     Soehne Buch 10.5 px on 13 px leading, white (cap height 8, x-height 6; v6 was 9.5 / 7 / 5), through
         v7_common.text (v6's sub-pixel, gamma-1.5 pipeline). Slogan 'The AI Usage' / 'Management' / 'Console',
         pen at x = 20 flush with the logo, cap top to last baseline centred on key 4's window. URL
         'io.stigg.io' / '/usage' centred on key 6's window. At 10.5 px the slogan's two long lines are 62 px:
         they fit only the left column (61 px centred budget); the right column centres at most 50 px, which
         the URL (45 px) fits. So the larger type Gabriel asked for puts the slogan on the left.
Lattice  one lattice for the whole panel: 3 x 3 px squares at x = 130 + 6i, y = 29 + 6j (an open grid, half the
         token of v6's 4 px). Each art key holds the largest block of lattice points centred on its window
         inside its region (key 2 10 x 10, key 3 8 x 10, key 5 10 x 9; every block within 1 px of its window's
         centre). Every point of a block holds a token: unlit #3C3E3A (Stigg n700, visible in the LCD
         preview, quieter than any lit token) unless lit.
Burst    a density field (prob) with the source at the left of key 2, level with the logo: a dense jet across
         key 2 at the wordmark's height, a long thin tail into key 3, and a lobe falling into key 5.
         1. jet: points where the field is dense are lit with that probability; its leading column (x = 130,
            the four rows level with the wordmark) is whole; no straight run longer than 3 (2 in its tail).
         2. dust: a fixed count per key by best-candidate sampling weighted by the field, so it is even and
            still thins out: never touching another token, never in a corner, at most two per lattice row or
            column, at most one more on each side of the block's outer ring, never three on one line within
            a short span or evenly spaced (no dotted rules).
         3. colour: exactly 40 % of lit tokens are white, weighted toward the far dust (the jet's edge stays
            lime). depth: the After Tokens lime steps #436633 / #639840 / #92E759 and neutral steps #6A6D69 /
            #9EA19D / #FFFFFF, dimmer steps likelier with distance (dim points behind bright ones, as in the
            stigg.io hero). Lit tokens on the right column of each block and the bottom row of key 5 take the
            dimmest step: there the JPEG block reaches past the tile edge and a bright token would ring there.
         Seeds that pass lint() are ranked by score() (composition); the seed is then chosen by eye.

usage: make.py [--seed N]    render into this folder via v7_common.render (default SEED)
       make.py --search N    list the seeds 1..N that pass the layout checks, best composition score first
"""
import json, math, os, random, sys

WELCOME = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, WELCOME)
import v7_common as C
from PIL import Image, ImageDraw

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = C.W, C.H
SEED = 662                           # chosen by eye among the best-scored seeds that pass lint()

# ------------------------------------------------------------------ lattice
PITCH, SQ = 6, 3
LX, LY = 130, 29                     # the one lattice: squares at x = LX + 6i, y = LY + 6j
# token block per art key: inclusive square-origin ranges (x0, x1, y0, y1)
AREA = {2: (LX, LX + 9 * PITCH, LY, LY + 9 * PITCH),
        3: (LX + 19 * PITCH, LX + 26 * PITCH, LY, LY + 9 * PITCH),
        5: (LX, LX + 9 * PITCH, LY + 19 * PITCH, LY + 27 * PITCH)}
for _k, (_x0, _x1, _y0, _y1) in AREA.items():
    _rx0, _ry0, _rx1, _ry1 = C.region(_k)
    assert _rx0 <= _x0 and _x1 + SQ <= _rx1 and _ry0 <= _y0 and _y1 + SQ <= _ry1, "block %d leaves its region" % _k
    assert all((v - o) % PITCH == 0 for v, o in ((_x0, LX), (_x1, LX), (_y0, LY), (_y1, LY))), "off the lattice"

# ------------------------------------------------------------------ colours
INK, UNLIT = C.INK, C.UNLIT
LIME, WHITE = C.LIME, C.WHITE
LIME_STEPS = [(0x43, 0x66, 0x33), (0x63, 0x98, 0x40), LIME]          # After Tokens depth steps (far, mid, near)
WHITE_STEPS = [(0x6A, 0x6D, 0x69), (0x9E, 0xA1, 0x9D), WHITE]        # Stigg neutral 550 / 400 / white

# ------------------------------------------------------------------ type
SIZE, LEAD = 10.5, 13
SLOGAN = ["The AI Usage", "Management", "Console"]
URL = ["io.stigg.io", "/usage"]

# ------------------------------------------------------------------ burst
P = dict(
    xs=126.0, ys=58.0,               # the source: left of key 2, level with the logo's centre (y 58.5)
    tilt=-0.02,                      # the stream's centre line climbs slightly to the right
    # jet: dense next to the wordmark, a band of half-height h0 (+ spread per px), density d0 * exp(-u / lam)
    d0=1.00, lam=30.0, h0=11.0, spread=0.12, soft=0.25,
    # dust: the long thin tail that carries on into key 3
    d1=0.22, lam2=400.0, hd0=12.0, spread_d=0.06, soft_d=0.35,
    # falling lobe: tokens dropping out of the stream into key 5, drifting right as they fall
    fy0=70.0, f0=0.25, flam=50.0, fx=22.0, fdrift=0.15, fw=12.0, fwg=0.12,
    # jet / dust split (field density) and the longest straight run allowed inside the jet
    core_u=20.0, sparse_p=0.40, loose_p=0.50, max_run=3,
    # colour and depth
    white_share=0.40, white_near=0.12, white_far=0.60, white_u=90.0,
    dim_jet=0.15, dim_near=0.25, dim_far=0.36, far_of_dim=0.4,
    # dust counts per key and best-candidate sampling (candidates per pick, density weighting, ring weight)
    n2=8, n3=11, n5=10, bc_m=6, bc_pow=1.0, dust_pow=1.0, edge_w=0.35,
)


def smooth(e0, e1, v):
    v = max(0.0, min(1.0, (v - e0) / (e1 - e0)))
    return v * v * (3 - 2 * v)


def key_of(x, y):
    for k, (x0, x1, y0, y1) in AREA.items():
        if x0 <= x <= x1 and y0 <= y <= y1:
            return k
    return None


def lattice(key):
    x0, x1, y0, y1 = AREA[key]
    return [(x, y) for y in range(y0, y1 + 1, PITCH) for x in range(x0, x1 + 1, PITCH)]


def dist_u(x, y, P):
    """How far the square at (x, y) has travelled from the source, in px (vertical travel counts less)."""
    cx, cy = x + SQ / 2, y + SQ / 2
    return math.hypot(cx - P["xs"], (cy - P["ys"]) * 0.6)


def prob(x, y, P):
    """The burst's density field at the square (x, y): jet + dust tail + falling lobe."""
    cx, cy = x + SQ / 2, y + SQ / 2
    u = cx - P["xs"]
    if u < 0:
        return 0.0
    yc = P["ys"] + P["tilt"] * u
    dy = abs(cy - yc)
    h = P["h0"] + P["spread"] * u
    core = P["d0"] * math.exp(-u / P["lam"]) * (1 - smooth(h * (1 - P["soft"]), h * (1 + P["soft"]), dy))
    hd = P["hd0"] + P["spread_d"] * u
    dust = P["d1"] * math.exp(-u / P["lam2"]) * (1 - smooth(hd * (1 - P["soft_d"]), hd * (1 + P["soft_d"]), dy))
    fall_p = 0.0
    if cy > P["fy0"]:
        fall = cy - P["fy0"]
        xf = P["xs"] + P["fx"] + P["fdrift"] * fall
        ef = math.exp(-0.5 * ((cx - xf) / (P["fw"] + P["fwg"] * fall)) ** 2)
        fall_p = P["f0"] * math.exp(-fall / P["flam"]) * ef * smooth(0, 6, fall)
    return min(1.0, core + dust + fall_p)


LINE_SPANS = (((1, 0), 4), ((0, 1), 4), ((1, 1), 3), ((1, -1), 3))   # rows/columns: 3 in 5 cells; diagonals: 3 in 4


def is_sparse(x, y, P):
    """Dust, as opposed to the dense jet: decided by the local density of the field."""
    return prob(x, y, P) < P["sparse_p"]


def makes_line(p, sparse):
    """True if p and two other sparse tokens of the same key would sit on one straight line and read as drawn
    rather than as dust: on a lattice row, column or diagonal within a short span (rows/columns 5 cells,
    diagonals 4), or on a line of any direction (knight-move slopes included) with nearly even gaps (the
    larger at most twice the smaller), which reads as a dotted rule."""
    x, y = p
    k = key_of(x, y)
    for (dx, dy), span in LINE_SPANS:
        on = [s for s in range(-10, 11) if s and (x + dx * PITCH * s, y + dy * PITCH * s) in sparse
              and key_of(x + dx * PITCH * s, y + dy * PITCH * s) == k]
        for i, a in enumerate(on):
            for b in on[i + 1:]:
                t = sorted((a, b, 0))
                if t[2] - t[0] <= span or t[1] - t[0] == t[2] - t[1]:
                    return True
    pc = ((x - LX) // PITCH, (y - LY) // PITCH)
    others = [((q[0] - LX) // PITCH, (q[1] - LY) // PITCH) for q in sparse if q != p and key_of(*q) == k]
    for i, a in enumerate(others):
        for b in others[i + 1:]:
            if (a[0] - pc[0]) * (b[1] - pc[1]) - (a[1] - pc[1]) * (b[0] - pc[0]):
                continue                                   # not collinear
            u, v, w = sorted((pc, a, b))
            g1 = math.hypot(v[0] - u[0], v[1] - u[1]); g2 = math.hypot(w[0] - v[0], w[1] - v[1])
            if max(g1, g2) <= 2 * min(g1, g2):
                return True
    return False


def run(lit, p, dx, dy):
    """Length of the straight run of lit tokens through p (p counted as lit) along (dx, dy)."""
    n = 1
    for sgn in (1, -1):
        q = (p[0] + sgn * dx * PITCH, p[1] + sgn * dy * PITCH)
        while q in lit:
            n += 1
            q = (q[0] + sgn * dx * PITCH, q[1] + sgn * dy * PITCH)
    return n


def on_edge(x, y):
    """On the outer ring of its key's block (dust there would trace the block's border)."""
    x0, x1, y0, y1 = AREA[key_of(x, y)]
    return x in (x0, x1) or y in (y0, y1)


def edge_count(lit, p):
    """Lit tokens already on the same side of the block's outer ring as p (0 when p is not on the ring)."""
    k = key_of(*p)
    x0, x1, y0, y1 = AREA[k]
    n = 0
    for side, v in ((0, x0), (0, x1), (1, y0), (1, y1)):
        if p[side] == v:
            n = max(n, sum(1 for q in lit if key_of(*q) == k and q[side] == v))
    return n


def line_count(sparse, p):
    """Most dust tokens of p's key already on p's lattice row or column (dust stays at two per line)."""
    k = key_of(*p)
    row = sum(1 for q in sparse if q[1] == p[1] and key_of(*q) == k)
    col = sum(1 for q in sparse if q[0] == p[0] and key_of(*q) == k)
    return max(row, col)


def hot_edge(x, y):
    """Right column of every block, bottom row of key 5: the JPEG block there reaches past the tile edge."""
    k = key_of(x, y)
    x0, x1, y0, y1 = AREA[k]
    return x == x1 or (k == 5 and y == y1)


def corner(x, y):
    k = key_of(x, y)
    x0, x1, y0, y1 = AREA[k]
    return x in (x0, x1) and y in (y0, y1)


def place(seed, P):
    """Lit tokens: {(x, y): (colour, depth)}, colour 0 lime / 1 white, depth 0 far / 1 mid / 2 near."""
    rng = random.Random(seed)
    pts = [p for k in AREA for p in lattice(k)]
    rng.shuffle(pts)
    x0 = AREA[2][0]
    # 1. the jet. Its edge at the left of key 2 is whole: the four rows level with the wordmark.
    lit = {p: None for p in lattice(2) if p[0] == x0 and prob(p[0], p[1], P) >= 0.9}
    sparse = set()
    for (x, y) in pts:
        if (x, y) in lit or prob(x, y, P) < P["sparse_p"] or rng.random() >= prob(x, y, P):
            continue
        mr = P["max_run"] if x <= x0 + 2 * PITCH else P["max_run"] - 1
        if x != x0 and (run(lit, (x, y), 1, 0) > mr or run(lit, (x, y), 0, 1) > mr):
            continue                          # no ruled lines inside the jet: short runs only, shorter in its tail
        lit[(x, y)] = None
    # 2. the dust, by best-candidate sampling: each pick is the best of bc_m candidates drawn from the field,
    # the one farthest from the tokens already in its key relative to the local density. Lines are checked
    # against the dust and the jet's loose tail (single tokens that read as dots, like the dust).
    loose = {p for p in lit if prob(p[0], p[1], P) < P["loose_p"]}
    for k, n in ((2, int(P["n2"])), (3, int(P["n3"])), (5, int(P["n5"]))):
        cand = [p for p in lattice(k) if 0.01 < prob(p[0], p[1], P) < P["sparse_p"]
                and not (k == 2 and p[0] <= x0 + 2 * PITCH and not 41 <= p[1] <= 71)   # a clean origin
                and not (k == 5 and p[1] == AREA[5][3])]                               # see hot_edge()
        for _ in range(n):
            ok = [p for p in cand if p not in lit and not corner(*p) and not makes_line(p, sparse | loose)
                  and not any((p[0] + PITCH * i, p[1] + PITCH * j) in lit for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j)
                  and edge_count(lit, p) < 2 and line_count(sparse, p) < 2]
            if not ok:
                break
            wts = [prob(p[0], p[1], P) ** P["dust_pow"] * (P["edge_w"] if on_edge(*p) else 1.0) for p in ok]
            best, best_s = None, -1
            for _ in range(int(P["bc_m"])):
                c = rng.choices(ok, weights=wts)[0]
                others = [q for q in lit if key_of(*q) == k]
                dmin = min((math.hypot((c[0] - q[0]) / PITCH, (c[1] - q[1]) / PITCH) for q in others), default=9.0)
                s = dmin * prob(c[0], c[1], P) ** P["bc_pow"]
                if s > best_s:
                    best, best_s = c, s
            lit[best] = None
            sparse.add(best)
    # 3. colour: exactly white_share of the lit tokens are white, picked by weighted sampling without replacement
    # (the weight grows with distance from the source: the jet's edge stays lime, the dust turns white).
    # depth: the dimmer steps become likelier with distance. Separate random streams: colour never moves a token.
    cells = sorted(lit, key=lambda p: (p[1], p[0]))

    def far(p):
        return smooth(0, P["white_u"], dist_u(p[0], p[1], P) - P["core_u"])
    lead = {p for p in cells if p[0] == x0 and prob(p[0], p[1], P) >= P["sparse_p"]}
    rc = random.Random(seed * 7919 + 17)
    pool = [p for p in cells if p not in lead]
    keys = {p: rc.random() ** (1.0 / (P["white_near"] + (P["white_far"] - P["white_near"]) * far(p))) for p in pool}
    whites = set(sorted(pool, key=lambda p: -keys[p])[:round(P["white_share"] * len(cells))])
    rd = random.Random(seed * 104729 + 3)
    out = {}
    for p in cells:
        if prob(p[0], p[1], P) >= P["sparse_p"]:          # the jet: bright, a few mid tokens for texture
            depth = 1 if (p not in lead and rd.random() < P["dim_jet"]) else 2
        else:                                              # the dust: dimmer steps likelier with distance
            pd = P["dim_near"] + (P["dim_far"] - P["dim_near"]) * far(p)
            r = rd.random()
            depth = 0 if r < pd * P["far_of_dim"] else (1 if r < pd else 2)
        out[p] = (1 if p in whites else 0, depth)
    for p in out:                                          # see hot_edge()
        if hot_edge(*p):
            out[p] = (out[p][0], 0)
    return out


# ------------------------------------------------------------------ layout checks
def lint(lit, P):
    fails = []
    n = {k: sum(1 for (x, y) in lit if key_of(x, y) == k) for k in AREA}
    if not (20 <= n[2] <= 32): fails.append("key 2 count %d" % n[2])
    if not (9 <= n[3] <= 15): fails.append("key 3 count %d" % n[3])
    if not (9 <= n[5] <= 15): fails.append("key 5 count %d" % n[5])
    tot = len(lit); wh = sum(1 for v in lit.values() if v[0] == 1)
    if not (0.35 <= wh / max(1, tot) <= 0.45): fails.append("white share %.2f" % (wh / max(1, tot)))
    sparse = {p for p in lit if is_sparse(p[0], p[1], P)}
    loose = {p for p in lit if prob(p[0], p[1], P) < P["loose_p"]}
    for p in loose:                                        # accidental lines (the sampler avoids them already)
        if makes_line(p, loose - {p}):
            fails.append("line at %s" % (p,))
    for (x, y) in sparse:                                  # clumps: a 3 x 3 cell window with more than 3 tokens
        c = sum(1 for dx in range(3) for dy in range(3) if (x + dx * PITCH, y + dy * PITCH) in lit)
        if c > 3: fails.append("clump at %s" % ((x, y),))
    for k in (3, 5):                                       # dust keys: every quadrant used, no corner token
        x0, x1, y0, y1 = AREA[k]
        ts = [p for p in lit if key_of(*p) == k]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        quad = {(p[0] > mx, p[1] > my) for p in ts}
        if len(quad) < 4: fails.append("key %d quadrants %d" % (k, len(quad)))
        for p in ts:
            if p[0] in (x0, x1) and p[1] in (y0, y1): fails.append("key %d corner token" % k)
    return sorted(set(fails)), n


def score(lit, P):
    """Composition score, lower is better (ranks the seeds that pass lint; the final pick is by eye)."""
    s = 0.0
    x0 = AREA[2][0]
    band = (47, 53, 59, 65)                                   # the stream's rows, level with the wordmark
    s += 3 * sum(1 for y in band if (x0, y) not in lit)       # the stream's edge at the left of key 2 is whole
    # along the stream the fill falls off steadily: left third > middle third > right third
    thirds = [sum(1 for x in xs for y in band if (x, y) in lit) / (len(xs) * 4)
              for xs in ((136, 142, 148), (154, 160, 166), (172, 178, 184))]
    s += 6 * max(0, thirds[1] - thirds[0] + 0.1) + 6 * max(0, thirds[2] - thirds[1] + 0.05)
    s += 4 * max(0, 0.12 - thirds[2])                          # ... but it still reaches the right of key 2
    for x in range(x0 + PITCH, x0 + 8 * PITCH, PITCH):        # ... without a gap that cuts it in two
        c = sum(1 for y in band + (41, 71) if (x, y) in lit)
        s += 3 * max(0, (2 if x <= x0 + 5 * PITCH else 1) - c)
    s += 3 * sum(1 for (x, y) in lit if key_of(x, y) == 2 and x <= x0 + 2 * PITCH and (y <= 35 or y >= 77))
    for k in (3, 5):
        kx0, kx1, ky0, ky1 = AREA[k]
        ts = [p for p in lit if key_of(*p) == k]
        if not ts:
            return 99
        mx = (kx0 + kx1) / 2
        left = sum(1 for p in ts if p[0] < mx); right = len(ts) - left
        s += 1.5 * max(0, 3 - min(left, right))
        cx = sum(p[0] for p in ts) / len(ts)
        s += 2 * max(0, abs(cx - mx) / PITCH - 0.8)
        wh = sum(1 for p in ts if lit[p][0] == 1)
        s += max(0, 3 - wh) + max(0, wh - 7)
        dim = sum(1 for p in ts if lit[p][1] < 2)
        s += max(0, 2 - dim) + max(0, dim - 6)
    ts3 = [p for p in lit if key_of(*p) == 3]
    s += 1.5 * sum(1 for p in ts3 if p[1] < 35 or p[1] > 77)  # key 3 carries the stream on at its height
    ts5 = [p for p in lit if key_of(*p) == 5]
    top = sum(1 for p in ts5 if p[1] < 167); bot = len(ts5) - top
    s += max(0, bot - top + 2)                                # key 5: tokens falling, thinning downward
    wh2 = sum(1 for p in lit if key_of(*p) == 2 and lit[p][0] == 1)
    s += max(0, 3 - wh2) + max(0, wh2 - 8)
    return round(s, 2)


# ------------------------------------------------------------------ compose
def hexc(c):
    return "#%02X%02X%02X" % tuple(c)


def compose(seed, P=P):
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)

    # ---- logo, key 1: the official file, 60 x 17, centred on the window as far as whole pixels allow
    logo, base_off = C.logo_image()
    cx, cy = C.window_centre(1)
    lx, ly = 20, round(cy - logo.height / 2)
    img.paste(logo, (lx, ly))

    # ---- slogan, key 4: pen at the logo's left edge; cap top to last baseline centred on the window
    cap = C.cap_height(SIZE)
    s_cap = round(C.window_centre(4)[1] - (cap + 2 * LEAD) / 2)
    sb = C.text(img, [(lx, s_cap, SLOGAN)], SIZE, LEAD)
    # At 10.5 px 'The AI Usage' and 'Management' rasterise 63 columns wide; the 63rd (x = 82) only holds the
    # 20-24 % anti-alias fringe of the final 'e' and 't', and x = 82 is inside the 6 px keycap rim. Snap the
    # line ends to x = 81 by dropping that fringe column (the strokes themselves end at x = 81).
    rx1 = C.region(4)[2]
    for (bx0, by0, bx1, by1) in sb:
        for y in range(by0, by1):
            for x in range(rx1, bx1):
                img.putpixel((x, y), INK)
    sb = [(b[0], b[1], min(b[2], rx1), b[3]) for b in sb]

    # ---- URL, key 6: ink box centred on the window. The pen goes to the whole pixel left of the exact centre
    # (ink x 244-288 around 266.5, window centre 267): at the half pixel the final 'o' spreads into x = 289
    # and its JPEG ringing reaches 4.0 luma levels just outside the tile; at x = 244 it stays at 3.2.
    ub = C.measure(URL, SIZE, LEAD)
    ux0, ux1 = min(b[0] for b in ub), max(b[2] for b in ub)
    u_pen = math.floor(C.window_centre(6)[0] - (ux1 - ux0) / 2 - ux0)
    u_cap = math.floor(C.window_centre(6)[1] - (cap + LEAD) / 2)      # cap top to last baseline around y 168
    ubox = C.text(img, [(u_pen, u_cap, URL)], SIZE, LEAD)

    # ---- tokens
    lit = place(seed, P)
    fails, n = lint(lit, P)
    for k in AREA:
        for (x, y) in lattice(k):
            if (x, y) in lit:
                ci, di = lit[(x, y)]
                col = (WHITE_STEPS if ci else LIME_STEPS)[di]
            else:
                col = UNLIT
            d.rectangle([x, y, x + SQ - 1, y + SQ - 1], fill=col)

    per_key = {}
    for k in AREA:
        ts = [v for p, v in lit.items() if key_of(*p) == k]
        per_key["key%d" % k] = {
            "lattice_points": len(lattice(k)), "lit": len(ts), "unlit": len(lattice(k)) - len(ts),
            "lime": sum(1 for v in ts if v[0] == 0), "white": sum(1 for v in ts if v[0] == 1),
            "lit_by_depth_far_mid_near": [sum(1 for v in ts if v[1] == j) for j in range(3)]}
    tot = len(lit); wh = sum(1 for v in lit.values() if v[0] == 1)
    info = {
        "variant": "b-slogan-under-logo-emit", "seed": seed,
        "layout": {"key1": "logo", "key2": "tokens: the stream leaving the wordmark (dense jet)",
                   "key3": "tokens: the fan (dust)", "key4": "slogan, flush left with the logo",
                   "key5": "tokens: falling out of the stream (dust)", "key6": "URL, centred"},
        "logo": {"x": lx, "y": ly, "size": list(logo.size), "wordmark_baseline": round(ly + base_off, 1)},
        "type": {"face": "Soehne Buch", "colour": "#FFFFFF",
                 "slogan": {"size_px": SIZE, "leading_px": LEAD, "cap_height_px": cap, "lines": SLOGAN,
                            "pen_x": lx, "cap_top": s_cap, "ink_boxes": sb},
                 "url": {"size_px": SIZE, "leading_px": LEAD, "cap_height_px": cap, "lines": URL,
                         "pen_x": u_pen, "cap_top": u_cap, "ink_boxes": ubox}},
        "lattice": {"pitch_px": PITCH, "square_px": SQ, "origin": [LX, LY],
                    "blocks": {"key%d" % k: {"x": [a[0], a[1] + SQ - 1], "y": [a[2], a[3] + SQ - 1]}
                               for k, a in AREA.items()}},
        "colours": {"canvas": hexc(INK), "unlit": hexc(UNLIT), "lime_far_mid_near": [hexc(c) for c in LIME_STEPS],
                    "white_far_mid_near": [hexc(c) for c in WHITE_STEPS]},
        "tokens": per_key, "lit_total": tot, "white_total": wh, "white_share": round(wh / max(1, tot), 2),
        "layout_checks": "pass" if not fails else fails,
    }
    return img, fails, info


if __name__ == "__main__":
    if "--search" in sys.argv:
        N = int(sys.argv[sys.argv.index("--search") + 1])
        ok = []
        for s in range(1, N + 1):
            lit = place(s, P)
            fails, n = lint(lit, P)
            if not fails:
                ok.append((score(lit, P), s, n))
        ok.sort()
        print("seeds passing the layout checks: %d of %d (best composition score first)" % (len(ok), N))
        for sc, s, n in ok[:30]:
            print("  seed", s, "score", sc, n)
        sys.exit(0)
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else SEED
    img, fails, info = compose(seed)
    print("layout checks:", "pass" if not fails else fails)
    checks = C.render(img, OUT, extra=info)
    print(json.dumps({k: checks[k] for k in ("outside_tiles", "darker_than_ink", "rim", "jpeg_bytes", "halo_count",
                                             "halo_worst", "lime", "hard_rules_pass")}, indent=1))
    print(json.dumps(info["tokens"]), info["lit_total"], info["white_share"])
