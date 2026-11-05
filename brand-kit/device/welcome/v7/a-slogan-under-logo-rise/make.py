"""Token Deck welcome screen v7, variant a-slogan-under-logo-rise (Nov 2, 2026), own code.

Layout     key 1  Stigg logo alone, centred on its window (60 x 17 at x 20, y 50)
           key 4  the slogan under it, flush left on the logo's x = 20: one brand lockup down the left column
           key 6  the URL, centred on its window
           keys 2, 3, 5  token art: one After Tokens burst that rises from a dense source low in key 5 (its
                  left side, next to the slogan) up through key 2 and out into key 3, thinning toward the
                  top-right corner. Key 6 stays clean.
Type       Soehne Buch 10.4 px on 13 px leading for the slogan and the URL (one size), white, through
           v7_common's type pipeline. 10.4 px is the largest size at which 'Management' fits key 4's region
           (x 20-81): at 10.5 px its ink needs x 20-82 and column 82 sits inside the 6 px keycap rim.
           Slogan pen x 20.05, cap top 152 (ink y 152-184, block centre 168.5 on the window's 168; of the
           positions searched, this one keeps the JPEG ringing beside key 4's tile edges at 3.0 luma levels,
           where cap tops 150-151 reach 4.0-4.3 at x 17-19).
           URL pen x 245 (the k3 grid's first column), cap top 157 (ink y 157-178, centred on 168).
Lattice    one strict global lattice: x = 5i, y = 5j + 4, 3 px squares (pitch 5, the stigg.io hero's finer
           points instead of v6's 4 px on 6). Background (unlit #3C3E3A) tokens on every lattice point of the
           art keys' token areas: 10 x 10 in keys 2 and 5 (x 135-182), 9 x 10 in key 3 (x 245-287), rows
           y 34-81 (top) and 144-191 (bottom). Each area is centred on its window to 0.5 px and lies wholly
           inside the JPEG 8 x 8 blocks that are inside the tile, so its ringing outside the tile stays under
           0.4 luma levels (a 12 x 11 grid reached 4.6 there and failed the halo rule).
Burst      a 4 x 4 lime source in key 5's lower-left corner, eroded toward its top-right corner (pixelmark's
           u0 / pow / erode rule), then a seeded density field sampled cell by cell in an LCG order:
           (d0 * exp(-r / lam) + dust) * exp(-((theta - theta0) / sigma)^2), with r the distance from the
           source and theta the angle from its centre. Distances are measured with the hidden bezels shrunk to
           a 10 px gutter, so the density runs on from the top of key 5 into the bottom of key 2 and on into
           key 3 the way the eye joins the windows. Rules while sampling: no lit grid corners (other than the
           source's), no straight run of 3 lit tokens in any direction, no dotted run of 3 with 1-cell gaps
           far out, no 2 x 2 clump (unless the source makes them), no orthogonal neighbours beyond the debris
           zone next to the source, no two lit tokens side by side along a grid edge, and a minimum spacing
           that grows with distance (even dust far out).
Checks     (choose the seed) lit counts key 5 27-40 > key 2 15-22 > key 3 8-12; white share 35-44 %; no dotted
           column or row; in keys 2 and 3 no 3 lit tokens in one column or row within 6 cells and no 3 whites
           in one column or row at all; at most 6 / 4 tokens on the outer ring of keys 2 / 3; key 2 heavier at
           the bottom, key 3 heavier on the left with its top-right quadrant nearly empty; key 5's lower right
           (beside the source) quiet. 111 of seeds 1-20000 pass; score() ranks them; the seed below was chosen
           by eye among the top ones (staircase erosion with fragments, bottom-heavy key 2, sparse key 3).
Colour     lime #92E759 and white #FFFFFF (white only beyond the debris zone, 60 % of spray tokens, so all lit
           tokens are about 62 / 38 lime / white), plus one depth step: lime tokens more than 20 px from the
           source that sit on the fan's fringe (envelope below 0.5, about 25 degrees off its axis) are After
           Tokens' #639840, dim points behind bright ones as on the stigg.io hero: the burst's core stays
           bright and its edges recede. No red.

usage: make.py                 render the chosen seed into this folder (v7_common.render)
       make.py --seed N        render seed N into this folder
       make.py --search 20000  list the seeds that pass every layout check, ranked by score()
"""
import sys, os, math, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
WELCOME = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WELCOME)
import v7_common as c
from PIL import Image, ImageDraw

SEED = 14772

# ---------------------------------------------------------------- lattice and token areas
PITCH, SQ = 5, 3
X0, Y0 = 0, 4                                          # x = 5i, y = 5j + 4 (panel px)
GRIDS = {2: (27, 36, 6, 15), 3: (49, 57, 6, 15), 5: (27, 36, 28, 37)}    # i0, i1, j0, j1 (inclusive)
SHIFT = {2: (0, 0), 3: (52, 0), 5: (0, 52)}            # bezel compression (px) for the density field only
MIDLIME = (0x63, 0x98, 0x40)                           # After Tokens depth step on the lime side
COLOURS = {"lime": c.LIME, "white": c.WHITE, "mid": MIDLIME}

# ---------------------------------------------------------------- type
SIZE, LEADING = 10.4, 13
SLOGAN = ["The AI Usage", "Management", "Console"]
URL = ["io.stigg.io", "/usage"]
SLOGAN_PEN, SLOGAN_CAP = 20.05, 152
URL_PEN, URL_CAP = 245.0, 157
LOGO_AT = (20, 50)

# ---------------------------------------------------------------- burst parameters
P = dict(src=(27, 30, 34, 37),                         # source block cells (x 135-153, y 174-192)
         erode=0.7, u0=0.5, epow=1.5,                  # pixelmark erosion toward the top-right corner
         theta0=62.0, sigma=28.0,                      # fan axis and angular spread (degrees, y up)
         d0=1.9, lam=40.0, dust=0.05,                  # density near the source, falloff (px), far dust
         debris=0.6, debris_r=7.0,                     # fragments right next to the source
         pair_r=14.0,                                  # beyond this, no orthogonal neighbours
         g1=1.55, gR=100.0, gfar=1.01,                 # minimum spacing (cells) growing with distance
         wfrom=8.0, white=0.6,                         # white share of spray tokens beyond wfrom px
         mid_env=0.5, midfrom=20.0)                    # depth step: lime tokens beyond midfrom px on the
                                                       # fan's fringe (envelope below mid_env, ~25 deg off axis)


def xy(i, j):
    return PITCH * i + X0, PITCH * j + Y0


ALL = {}
for _k, (_i0, _i1, _j0, _j1) in GRIDS.items():
    for _i in range(_i0, _i1 + 1):
        for _j in range(_j0, _j1 + 1):
            ALL[(_i, _j)] = _k


def local(cell):
    k = ALL[cell]; i0, i1, j0, j1 = GRIDS[k]
    return k, cell[0] - i0, cell[1] - j0, i1 - i0, j1 - j0


def on_ring(cell):
    k, a, b, w, h = local(cell)
    return a in (0, w) or b in (0, h)


def is_corner(cell):
    k, a, b, w, h = local(cell)
    return a in (0, w) and b in (0, h)


def virt(cell):
    x, y = xy(*cell); sx, sy = SHIFT[ALL[cell]]
    return x + 1 - sx, y + 1 - sy


class LCG:                                             # pixelmark.js rng(seed)
    def __init__(self, seed): self.s = (seed & 0xffffffff) or 1

    def __call__(self):
        self.s = (self.s * 1664525 + 1013904223) & 0xffffffff
        return self.s / 4294967296


def field(seed, P=P):
    """-> ({cell: 'lime' | 'white' | 'mid'}, source cells)"""
    R = LCG(seed); RW = LCG(seed * 7919 + 17)          # RW: colour only, so white never moves a token
    i0, i1, j0, j1 = P["src"]
    src = {(i, j) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)}
    vs = [virt(q) for q in src]
    rect = (min(v[0] for v in vs) - 1, min(v[1] for v in vs) - 1, max(v[0] for v in vs) + 1, max(v[1] for v in vs) + 1)
    acx, acy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
    tokens = {q: "lime" for q in src}
    span = (i1 - i0) + (j1 - j0)
    for (i, j) in sorted(src, key=lambda q: (q[1], q[0])):
        u = ((i - i0) + (j1 - j)) / span                                 # 0 bottom-left, 1 top-right corner
        pr = 0.0 if u <= P["u0"] else ((u - P["u0"]) / (1 - P["u0"])) ** P["epow"] * P["erode"]
        if R() < pr:
            tokens.pop((i, j), None)

    def bad_shape(q, far):
        i, j = q
        for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1)):
            for off in (0, 1, 2):
                run = [(i + (n - off) * di, j + (n - off) * dj) for n in range(3)]
                if all(p == q or p in tokens for p in run) and sum(p in src for p in run) < 2:
                    return True
            if far:                                                    # dotted lines with 1-cell gaps
                for off in (0, 1, 2):
                    run = [(i + 2 * (n - off) * di, j + 2 * (n - off) * dj) for n in range(3)]
                    if all(p == q or (p in tokens and p not in src) for p in run):
                        return True
        for a in (0, -1):
            for b in (0, -1):
                blk = [(i + a, j + b), (i + a + 1, j + b), (i + a, j + b + 1), (i + a + 1, j + b + 1)]
                if all(p == q or p in tokens for p in blk) and sum(p in src for p in blk) < 2:
                    return True
        if on_ring(q):                                                 # no dashes along a grid edge
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (i + di, j + dj)
                if p in tokens and p not in src and p in ALL and on_ring(p):
                    return True
        return False

    order = sorted(ALL)
    for k in range(len(order) - 1, 0, -1):                             # Fisher-Yates with the LCG
        m = int(R() * (k + 1)); order[k], order[m] = order[m], order[k]
    for cell in order:
        if cell in src or is_corner(cell):
            continue
        vx, vy = virt(cell)
        dx = max(rect[0] - vx, 0, vx - rect[2]); dy = max(rect[1] - vy, 0, vy - rect[3])
        r = math.hypot(dx, dy)
        th = math.degrees(math.atan2(acy - vy, vx - acx))
        env = math.exp(-((th - P["theta0"]) / P["sigma"]) ** 2)
        dens = (P["d0"] * math.exp(-r / P["lam"]) + P["dust"]) * env
        if r <= P["debris_r"]:
            dens = max(dens, P["debris"] * env)
        if R() >= dens:
            continue
        far = ALL[cell] in (2, 3) or r > P["pair_r"]
        g = P["g1"] * min(1.0, r / P["gR"])
        if far:
            g = max(g, P["gfar"])
        if g > 0:
            rr = int(math.ceil(g))
            if any((cell[0] + di, cell[1] + dj) in tokens for di in range(-rr, rr + 1) for dj in range(-rr, rr + 1)
                   if (di or dj) and di * di + dj * dj < g * g):
                continue
        if bad_shape(cell, far):
            continue
        white = r >= P["wfrom"] and RW() < P["white"]
        mid = (not white) and r >= P["midfrom"] and env < P["mid_env"]  # the core stays bright, the fringe recedes
        tokens[cell] = "white" if white else ("mid" if mid else "lime")
    return tokens, src


def stats(tokens):
    n = {k: {"lime": 0, "mid": 0, "white": 0, "unlit": 0} for k in GRIDS}
    for q, k in ALL.items():
        n[k][tokens.get(q, "unlit")] += 1
    return n


# ---------------------------------------------------------------- layout checks
def checks(tokens, src):
    fails = []
    lit = set(tokens); nonsrc = lit - src
    for q in nonsrc:                                                   # dotted rows / columns
        i, j = q
        for axis in (0, 1):
            span = [((i, j + n) if axis == 0 else (i + n, j)) for n in range(5)]
            if sum(p in nonsrc for p in span) >= 3:
                side = [((p[0] + s, p[1]) if axis == 0 else (p[0], p[1] + s)) for p in span for s in (-1, 1)]
                if not any(p in lit for p in side):
                    fails.append("dotted line at %s" % (q,))
            if ALL[q] in (2, 3):                                       # sparse keys: no 3 lit in one column
                span = [((i, j + n) if axis == 0 else (i + n, j)) for n in range(6)]   # or row within 6 cells
                if sum(p in lit for p in span) >= 3:
                    fails.append("aligned tokens at %s" % (q,))
    for k in (2, 3):                                                   # no column / row of 3 whites in a sparse key
        whites = [q for q in lit if ALL[q] == k and tokens[q] == "white"]
        for axis in (0, 1):
            lines = {}
            for q in whites:
                lines[q[axis]] = lines.get(q[axis], 0) + 1
            if max(lines.values(), default=0) >= 3:
                fails.append("key %d: 3 whites in one %s" % (k, "column" if axis == 0 else "row"))
    n = stats(tokens)
    tot = {k: v["lime"] + v["mid"] + v["white"] for k, v in n.items()}
    if not (27 <= tot[5] <= 40): fails.append("key 5 has %d" % tot[5])
    if not (15 <= tot[2] <= 22): fails.append("key 2 has %d" % tot[2])
    if not (8 <= tot[3] <= 12): fails.append("key 3 has %d" % tot[3])
    wf = sum(v["white"] for v in n.values()) / sum(tot.values())
    if not (0.35 <= wf <= 0.44): fails.append("white share %.2f" % wf)
    for k in (2, 3):
        ring = sum(1 for q in lit if ALL[q] == k and on_ring(q))
        if ring > (6 if k == 2 else 4): fails.append("key %d edge tokens %d" % (k, ring))
    k2 = [local(q) for q in lit if ALL[q] == 2]
    if sum(b for _, a, b, _, _ in k2) / len(k2) < 4.8: fails.append("key 2 not bottom-heavy")
    k3 = [local(q) for q in lit if ALL[q] == 3]
    if sum(a for _, a, b, _, _ in k3) / max(1, len(k3)) > 3.6: fails.append("key 3 not left-heavy")
    if sum(1 for _, a, b, _, _ in k3 if a >= 5 and b <= 3) > 1: fails.append("key 3 top-right busy")
    k5 = [local(q) for q in nonsrc if ALL[q] == 5]
    if sum(1 for _, a, b, _, _ in k5 if a >= 6 and b >= 6) > 1: fails.append("key 5 lower-right busy")
    return fails, tot, round(wf, 3)


def score(tokens, src):
    """Composition score used only to rank passing seeds for review (higher = clearer burst)."""
    lit = set(tokens); nonsrc = lit - src
    sx, sy = xy(30, 34); sx += 3                                       # the source's top-right corner
    k5 = [q for q in nonsrc if ALL[q] == 5]
    cone = sum(1 for q in k5 if 25 <= math.degrees(math.atan2(sy - xy(*q)[1], xy(*q)[0] - sx)) <= 100) / len(k5)
    k2 = [local(q) for q in lit if ALL[q] == 2]
    grad2 = (sum(1 for t in k2 if t[2] >= 5) - sum(1 for t in k2 if t[2] < 5)) / len(k2)
    k3 = [local(q) for q in lit if ALL[q] == 3]
    left3 = sum(1 for t in k3 if t[1] <= 3) / len(k3)
    i0, i1, j0, j1 = P["src"]                                          # coherence with the fan axis (k2, k3)
    vs = [virt(q) for q in src]
    acx = (min(v[0] for v in vs) + max(v[0] for v in vs)) / 2; acy = (min(v[1] for v in vs) + max(v[1] for v in vs)) / 2
    far = [q for q in lit if ALL[q] in (2, 3)]
    coh = sum(math.exp(-((math.degrees(math.atan2(acy - virt(q)[1], virt(q)[0] - acx)) - P["theta0"]) / 20.0) ** 2)
              for q in far) / len(far)
    tl2 = sum(1 for t in k2 if t[1] <= 4 and t[2] <= 4)                # key 2's top-left quadrant (away from the fan)
    r3 = sum(1 for t in k3 if t[1] >= 6)                               # key 3's right third
    n = stats(tokens)
    bal = -sum(abs(n[k]["white"] / max(1, n[k]["white"] + n[k]["lime"] + n[k]["mid"]) - 0.5) for k in (2, 3))
    return round(cone + 0.8 * coh + 0.4 * grad2 + 0.4 * left3 - 0.12 * tl2 - 0.12 * r3 + 0.5 * bal, 3)


# ---------------------------------------------------------------- compose
def compose(tokens):
    img = Image.new("RGB", (c.W, c.H), c.INK)
    d = ImageDraw.Draw(img)
    for q in ALL:
        x, y = xy(*q)
        d.rectangle([x, y, x + SQ - 1, y + SQ - 1], fill=COLOURS.get(tokens.get(q), c.UNLIT))
    logo, base_off = c.logo_image()
    img.paste(logo, LOGO_AT)
    boxes = c.text(img, [(SLOGAN_PEN, SLOGAN_CAP, SLOGAN), (URL_PEN, URL_CAP, URL)], SIZE, LEADING)
    return img, boxes, logo.size


def info(seed, tokens, src, boxes, logo_size):
    n = stats(tokens)
    tot = {k: v["lime"] + v["mid"] + v["white"] for k, v in n.items()}
    lime = sum(v["lime"] + v["mid"] for v in n.values()); white = sum(v["white"] for v in n.values())
    def area(k):
        i0, i1, j0, j1 = GRIDS[k]; x0, y0 = xy(i0, j0); x1, y1 = xy(i1, j1)
        return [x0, y0, x1 + SQ - 1, y1 + SQ - 1]
    def centre_off(k, box):
        cx, cy = c.window_centre(k)
        return [round((box[0] + box[2] + 1) / 2 - cx, 1), round((box[1] + box[3] + 1) / 2 - cy, 1)]
    slogan_box = [min(b[0] for b in boxes[:3]), boxes[0][1], max(b[2] for b in boxes[:3]) - 1, boxes[2][3] - 1]
    url_box = [min(b[0] for b in boxes[3:]), boxes[3][1], max(b[2] for b in boxes[3:]) - 1, boxes[4][3] - 1]
    logo_box = [LOGO_AT[0], LOGO_AT[1], LOGO_AT[0] + logo_size[0] - 1, LOGO_AT[1] + logo_size[1] - 1]
    return {
        "variant": "a-slogan-under-logo-rise",
        "seed": seed,
        "layout": {"key1": "logo", "key4": "slogan (flush left on the logo's x)", "key6": "URL",
                   "art": [2, 3, 5], "burst": "source low-left in key 5, rising through key 2 into key 3"},
        "type": {"font": "Soehne Buch", "size_px": SIZE, "leading_px": LEADING, "cap_height_px": c.cap_height(SIZE),
                 "slogan_lines": SLOGAN, "slogan_pen_x": SLOGAN_PEN, "slogan_cap_top": SLOGAN_CAP,
                 "slogan_ink_box": slogan_box, "slogan_offset_from_window_centre": centre_off(4, slogan_box),
                 "url_lines": URL, "url_pen_x": URL_PEN, "url_cap_top": URL_CAP, "url_ink_box": url_box,
                 "url_offset_from_window_centre": centre_off(6, url_box)},
        "logo": {"box": logo_box, "offset_from_window_centre": centre_off(1, logo_box)},
        "lattice": {"pitch": PITCH, "square": SQ, "origin": "x = 5i, y = 5j + 4",
                    "areas": {"key%d" % k: area(k) for k in GRIDS},
                    "area_offset_from_window_centre": {"key%d" % k: centre_off(k, area(k)) for k in GRIDS}},
        "colours": {"lime": "#92E759", "white": "#FFFFFF", "depth_lime": "#639840", "unlit": "#3C3E3A"},
        "tokens": {"key%d" % k: {"lit": tot[k], "lime": n[k]["lime"], "depth_lime": n[k]["mid"],
                                 "white": n[k]["white"], "unlit": n[k]["unlit"]} for k in GRIDS},
        "tokens_lit_total": sum(tot.values()),
        "lit_mix": {"lime_incl_depth_pct": round(100 * lime / (lime + white), 1),
                    "white_pct": round(100 * white / (lime + white), 1)},
        "source_cells_lit": sum(1 for q in src if q in tokens),
    }


def main():
    if "--search" in sys.argv:
        N = int(sys.argv[sys.argv.index("--search") + 1])
        ok = []
        for s in range(1, N + 1):
            tk, src = field(s)
            fails, tot, wf = checks(tk, src)
            if not fails:
                ok.append((score(tk, src), s, tot, wf))
        ok.sort(reverse=True)
        print("seeds passing every layout check: %d of %d" % (len(ok), N))
        for sc, s, tot, wf in ok[:30]:
            print("  seed %4d  score %.3f  lit %s  white %.2f" % (s, sc, tot, wf))
        return
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else SEED
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else HERE
    tokens, src = field(seed)
    fails, tot, wf = checks(tokens, src)
    img, boxes, logo_size = compose(tokens)
    extra = info(seed, tokens, src, boxes, logo_size)
    extra["layout_checks"] = fails or "pass"
    res = c.render(img, out, extra)
    print(json.dumps({k: res[k] for k in ("outside_tiles", "darker_than_ink", "rim", "jpeg_bytes", "halo_count",
                                          "halo_worst", "lime", "hard_rules_pass")}))
    print("layout checks:", fails or "pass", "| lit per key", tot, "| white %.2f" % wf)


if __name__ == "__main__":
    main()
