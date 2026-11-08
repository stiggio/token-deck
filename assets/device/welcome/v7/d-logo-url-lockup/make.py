"""Token Deck welcome v7, variant d-logo-url-lockup (Nov 2, 2026), own code.

Gabriel's option 1: key 1 = the logo with the URL under it, key 6 = the slogan (bottom right), keys 2, 3, 4,
5 = one token burst running the diagonal from a dense lime block in key 4 up through keys 5 and 2 into key 3.
His v6 feedback, answered: white tokens and v1's "background" tokens are back, finer (3 px, like the
stigg.io hero's small points), lime and white with a depth step; text as large as the right column allows.

Layout (panel px; every window centre is from panel_geometry.WINDOWS)
  key 1  logo 60 x 17 at (20, 32); URL "io.stigg.io" / "/usage" flush left at pen x 21 (the round mark
         overshoots the i stem by 1 px), cap top 66: 17 px clear below the logo (= the mark's height), and the
         group (logo top 32 to last baseline 85) is centred on the window's 58.5. Left/right the key allows only
         7-8 px, which is the clear space Stigg's rule waives "where the key allows it".
  key 6  slogan "The AI Usage" / "Management" / "Console", pen x 234, cap top 152 (baselines 159/171/183,
         centre 167.5 vs 168). The right column's usable band is x 234-291 (tile ends 14 px before the
         window's right edge; rim rule 6 px from its left edge), so "Management" sets the size: 58 columns at
         9.6-9.7 px with v6's sub-pixel pipeline (59 at 9.75, 60 at 10). Ink fills x 234-291 exactly, i.e. as
         far right as the tile allows: the measure is centred 4 px left of the window centre (263 vs 267).
  type   Soehne Buch 9.7 px on 12 px leading for both slogan and URL (one size; cap height 7 px).
Tokens
  lattice x = 5i, y = 4 + 5j, 3 px squares, one global grid. Every art key shows a full matrix of unlit
  #3C3E3A tokens, sized and placed so it is centred on its window within 1 px and lies wholly inside the
  JPEG 8 x 8 blocks that are inside the tile (no ringing or 4:2:0 chroma past the tile edge):
  key 4 11 x 10 (x 25-77, y 144-191), keys 5/2 10 x 10 (x 135-182), key 3 9 x 10 (x 245-287), y 34-81 top.
  lit: lime #92E759, white #FFFFFF, and After Tokens' lime step #639840 for depth (dim lime sits off the
  stream's core: "dim points behind bright ones"). No red.
  burst: a 4 x 7 lime block (rounded right corners) in key 4's lower left, eroded from its right edge inward
  (pixelmark's erosion, no holes); then a stream (Catmull-Rom path) that leaves the block's face, crosses
  key 5's upper left, climbs through key 2 from bottom centre to top right and fans out across key 3.
  Exact counts per key (key 4: 12 beside the block; 5: 16; 2: 13; 3: 9) are drawn by weight from a
  Gaussian band around the path, with spacing (tokens may touch at corners only) and refusals that keep
  out accidental figures: no evenly spaced triple at step 1 or 2 in any direction, no diagonal chain over 3,
  no 4-token diamond, no lit grid corner, at most 2 lit tokens on any grid edge. Whites go downstream
  (key 4 4, key 5 8, key 2 9, key 3 7), so the burst cools from lime to white as it disperses.
Checks  checks() (counts, lines, dotted lines, edges, clumps, isolated sparks, a comb-like block edge, lime in
  key 3, white share 36-44 %) plus v7_common.render()'s hard rules. The seed is chosen by eye among the passing
  seeds ranked by how closely their tokens follow the stream (--search).

usage: make.py [--seed N]            render the final image, previews and checks.json (default seed 1513)
       make.py --search 4000         rank the seeds that pass every layout check
       make.py --sheet 1,2,3 --out sheet.png    contact sheet of candidate seeds (COLS=3 LCD=1 optional)
"""
import json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WELCOME = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WELCOME)
import v7_common as c
from panel_geometry import WINDOWS
from PIL import Image, ImageDraw

W, H = c.W, c.H
INK, LIME, WHITE, UNLIT = c.INK, c.LIME, c.WHITE, c.UNLIT
LIME_MID = (0x63, 0x98, 0x40)            # After Tokens' own lime step, the depth layer
SEED = 1513

# ---------------------------------------------------------------- lattice
PX, PY, P, SQ = 0, 4, 5, 3               # x = 5i, y = 4 + 5j, 3 px squares, 2 px gaps
GRID = {4: (range(5, 16), range(28, 38)),   # 11 x 10, x 25-77,  y 144-191
        5: (range(27, 37), range(28, 38)),  # 10 x 10, x 135-182, y 144-191
        2: (range(27, 37), range(6, 16)),   # 10 x 10, x 135-182, y 34-81
        3: (range(49, 58), range(6, 16))}   #  9 x 10, x 245-287, y 34-81
ART = (4, 5, 2, 3)


def xy(i, j):
    return PX + P * i, PY + P * j


def key_of(i, j):
    for k, (I, J) in GRID.items():
        if i in I and j in J:
            return k
    return None


CELLS = [(i, j) for k in ART for i in GRID[k][0] for j in GRID[k][1]]

# ---------------------------------------------------------------- burst field
FIELD = dict(
    src_i0=5, src_w=4, src_jb=37, src_h=7, corner=1,   # the block: x 25-42, y 159-191, right corners rounded
    erode=0.55, u0=0.5, epow=1.5,                       # pixelmark erosion of its right half
    way=((118, 170), (148, 152), (158, 118), (162, 84), (172, 60), (205, 52), (250, 56), (292, 50)),
    sigma=((0, 8.0), (60, 9.0), (130, 11.0), (200, 13.0), (260, 16.0), (340, 20.0)),   # band width (px)
    floor=0.03,                       # weight far from the stream (relative to its core)
    edge=0.45,                        # weight on each grid's outer ring
    n=({4: 12, 5: 16, 2: 13, 3: 9}),  # tokens placed per key (key 4: beside the block)
    nw=({4: 4, 5: 8, 2: 9, 3: 7}),    # of which white
    wnoise=60.0,                      # whites go downstream, with this much jitter (px of path)
    dim=0.33,                         # scales the chance that a lime off the stream's core is drawn #639840
    edge_dim=0.0,                     # dimming the block's eroding column: tried, invisible on the device
    gap=1.05)                         # spacing beyond the block: tokens may touch at corners, never sides


def knots(kn, r):
    if r <= kn[0][0]:
        return kn[0][1]
    for (r0, v0), (r1, v1) in zip(kn, kn[1:]):
        if r <= r1:
            return v0 + (v1 - v0) * (r - r0) / (r1 - r0)
    return kn[-1][1]


def catmull(pts, n=40):
    """Catmull-Rom spline through the waypoints, densely sampled, with the arc length at each sample."""
    P_ = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for k in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[k - 1], P_[k], P_[k + 1], P_[k + 2]
        for q in range(n):
            t = q / n
            out.append(tuple(0.5 * (2 * p1[a] + (-p0[a] + p2[a]) * t + (2 * p0[a] - 5 * p1[a] + 4 * p2[a] - p3[a]) * t * t
                                    + (-p0[a] + 3 * p1[a] - 3 * p2[a] + p3[a]) * t ** 3) for a in (0, 1)))
    out.append(tuple(pts[-1]))
    s = [0.0]
    for a, b in zip(out, out[1:]):
        s.append(s[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return out, s


def source_cells(p):
    i0, w, jb, h = p["src_i0"], p["src_w"], p["src_jb"], p["src_h"]
    s = {(i, j) for i in range(i0, i0 + w) for j in range(jb - h + 1, jb + 1)}
    if p["corner"]:
        s -= {(i0 + w - 1, jb - h + 1), (i0 + w - 1, jb)}
    return s


def stream_map(p):
    """Per cell: (weight, downstream position s along the path, distance from its centre line in sigmas)."""
    src = source_cells(p)
    i0, w = p["src_i0"], p["src_w"]
    ox = xy(i0 + w, 0)[0] - 1.0
    rows = sorted({j for _, j in src})
    oy = (xy(0, rows[0])[1] + xy(0, rows[-1])[1] + SQ) / 2.0
    path, arc = catmull([(ox, oy)] + list(p["way"]))
    out = {}
    for (i, j) in CELLS:
        if (i, j) in src:
            continue
        x, y = xy(i, j)
        cx, cy = x + 1.5, y + 1.5
        if cx < ox - 2:
            continue                                        # behind or above the block's face
        n = min(range(len(path)), key=lambda q: (path[q][0] - cx) ** 2 + (path[q][1] - cy) ** 2)
        dd, s = math.hypot(path[n][0] - cx, path[n][1] - cy), arc[n]
        sig = knots(p["sigma"], s)
        wgt = p["floor"] + (1 - p["floor"]) * math.exp(-dd * dd / (2 * sig * sig))
        k = key_of(i, j); I, J = GRID[k]
        if i in (I[0], I[-1]) or j in (J[0], J[-1]):
            wgt *= p["edge"]
        out[(i, j)] = (wgt, s, dd / sig)
    return out, src


_MAP = {}


def field(seed, p=FIELD):
    """-> ({cell: colour} for lit cells, block cells, stream map). Exact counts per key, weighted by the stream."""
    rng = random.Random(seed)
    if id(p) not in _MAP:
        _MAP[id(p)] = stream_map(p)
    smap, src = _MAP[id(p)]
    i0, w = p["src_i0"], p["src_w"]
    lit = set(src)
    for (i, j) in sorted(src, key=lambda t: (t[1], -t[0])):           # the block erodes from its right edge
        u = (i + 1 - i0) / w                                          # inward: a cell breaks off only once
        pr = 0 if u <= p["u0"] else ((u - p["u0"]) / (1 - p["u0"])) ** p["epow"] * p["erode"]
        if (i + 1, j) not in lit and rng.random() < pr:              # the cell to its right has gone (no holes)
            lit.discard((i, j))
    near_block = {(i + di, j + dj) for (i, j) in src for di in (-1, 0, 1) for dj in (-1, 0, 1)}

    def free(cell):
        i, j = cell
        g = p["gap"]
        if any((i + di, j + dj) in src for di in (-1, 0, 1) for dj in (-1, 0, 1)):     # fragments at the face
            return not any((i + di, j + dj) in lit and (i + di, j + dj) not in src
                           for di in (-1, 0, 1) for dj in (-1, 0, 1) if di or dj)
        rr = int(math.ceil(g))
        if any((i + di, j + dj) in lit for di in range(-rr, rr + 1) for dj in range(-rr, rr + 1)
               if (di or dj) and di * di + dj * dj < g * g):
            return False
        loose = lambda q: q in lit and q not in src
        for d in ((1, 0), (0, 1), (1, 1), (1, -1)):                  # never complete an evenly spaced triple
            for st in (1, 2):
                a1 = (i - d[0] * st, j - d[1] * st); a2 = (i - 2 * d[0] * st, j - 2 * d[1] * st)
                b1 = (i + d[0] * st, j + d[1] * st); b2 = (i + 2 * d[0] * st, j + 2 * d[1] * st)
                if (loose(a1) and loose(a2)) or (loose(a1) and loose(b1)) or (loose(b1) and loose(b2)):
                    return False
        for (ei, ej) in ((i, j - 1), (i, j + 1), (i - 1, j), (i + 1, j)):   # no four-token diamond round a gap
            if (ei, ej) not in lit and all(loose(q) or q == (i, j)
                                           for q in ((ei, ej - 1), (ei, ej + 1), (ei - 1, ej), (ei + 1, ej))):
                return False
        chain, todo = {(i, j)}, [(i, j)]                             # diagonal chains of at most three
        while todo:
            a = todo.pop()
            for di in (-1, 1):
                for dj in (-1, 1):
                    q = (a[0] + di, a[1] + dj)
                    if loose(q) and q not in chain and q not in near_block:
                        chain.add(q); todo.append(q)
        if len(chain) > 3 and (i, j) not in near_block:
            return False
        k = key_of(i, j); I, J = GRID[k]
        if i in (I[0], I[-1]) and j in (J[0], J[-1]):
            return False                                             # grid corners stay unlit (frame marks)
        for edge in ([(x, J[0]) for x in I], [(x, J[-1]) for x in I], [(I[0], y) for y in J], [(I[-1], y) for y in J]):
            if (i, j) in edge and sum(1 for q in edge if loose(q)) >= 2:
                return False                                         # at most two lit tokens on a grid edge
        return True

    placed = {}
    for k in ART:
        pool = [cell for cell in smap if key_of(*cell) == k]
        got = 0
        while got < p["n"][k] and pool:
            cell = rng.choices(pool, weights=[smap[q][0] for q in pool])[0]
            pool.remove(cell)
            if cell in lit or not free(cell):
                continue
            lit.add(cell); placed[cell] = k; got += 1
    col = {cell: LIME for cell in lit if cell in src}
    right = max(i for i, _ in src)
    for cell in sorted(col):
        if cell[0] == right and rng.random() < p["edge_dim"]:
            col[cell] = LIME_MID
    for k in ART:
        mine = [cell for cell in placed if placed[cell] == k]
        ranked = sorted(mine, key=lambda q: smap[q][1] + rng.gauss(0, p["wnoise"]), reverse=True)
        whites = set(ranked[:p["nw"][k]])
        for cell in mine:
            if cell in whites:
                col[cell] = WHITE
            else:
                far = smap[cell][2]                                  # distance from the stream core, in sigmas
                pdim = 0 if k == 4 else min(0.9, p["dim"] * (0.4 + far))
                col[cell] = LIME_MID if rng.random() < pdim else LIME
    return col, src, smap


# ---------------------------------------------------------------- layout checks
def lines_in(cells, step=1):
    """Runs of 3 lit cells at the given step along rows, columns and diagonals."""
    out = []
    for (i, j) in cells:
        for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1)):
            if (i + di * step, j + dj * step) in cells and (i + 2 * di * step, j + 2 * dj * step) in cells:
                out.append(((i, j), (di, dj)))
    return out


def checks(col, src):
    fails = []
    n = {k: 0 for k in ART}
    for cc in col:
        n[key_of(*cc)] += 1
    if not (n[4] > n[5] > n[2] >= n[3] >= 7):
        fails.append("counts %s" % n)
    near_src = {(i + di, j + dj) for (i, j) in src for di in (-1, 0, 1) for dj in (-1, 0, 1)}
    loose = {cc for cc in col if cc not in near_src}
    for (a, dvec) in lines_in(loose, 1):
        fails.append("run of 3 at %s %s" % (a, dvec)); break
    for (a, dvec) in lines_in({cc for cc in loose if key_of(*cc) in (5, 2, 3)}, 2):
        if dvec in ((1, 0), (0, 1)) and (a[0] + dvec[0], a[1] + dvec[1]) not in col:
            fails.append("dotted line at %s %s" % (a, dvec)); break
    for k in ART:
        I, J = GRID[k]
        for name, ring in (("top", [(i, J[0]) for i in I]), ("bottom", [(i, J[-1]) for i in I]),
                           ("left", [(I[0], j) for j in J]), ("right", [(I[-1], j) for j in J])):
            m = sum(1 for cc in ring if cc in col and cc not in src)
            if m >= 3:
                fails.append("key %d %s edge has %d" % (k, name, m))
    for k in (5, 2, 3):
        I, J = GRID[k]
        for i in I:
            for j in J:
                if sum(1 for di in range(3) for dj in range(3) if (i + di, j + dj) in col) > 4:
                    fails.append("clump in key %d" % k); break
    for k, reach in ((4, 2.3), (5, 2.3), (2, 2.3), (3, 3.2)):         # no marooned spark (reads as a dead pixel)
        mine = [cc for cc in col if key_of(*cc) == k and cc not in src]
        for a in mine:
            near = min((math.hypot(a[0] - b[0], a[1] - b[1]) for b in col if b != a and key_of(*b) == k), default=99)
            if near > reach:
                fails.append("isolated token %s in key %d" % (a, k)); break
    for i in sorted({i for i, _ in src}):                             # the eroded edge must not read as a comb
        rows = sorted(j for (ii, j) in src if ii == i)
        bits = "".join("1" if (i, j) in col else "0" for j in range(rows[0], rows[-1] + 1))
        if "10101" in bits or "01010" in bits:
            fails.append("comb in block column %d" % i)
    lime_k3 = sum(1 for cc, v in col.items() if key_of(*cc) == 3 and v in (LIME, LIME_MID))
    if lime_k3 < 2:
        fails.append("key 3 has %d lime" % lime_k3)
    wshare = sum(1 for v in col.values() if v == WHITE) / len(col)
    if not 0.36 <= wshare <= 0.44:
        fails.append("white share %.2f" % wshare)
    return fails, n


def adherence(col, smap):
    """Mean stream weight of the tokens in keys 5, 2 and 3 (the weakest key and the average)."""
    per = {}
    for k in (5, 2, 3):
        ws = [smap[cc][0] for cc in col if cc in smap and key_of(*cc) == k]
        per[k] = sum(ws) / max(1, len(ws))
    return min(per.values()), sum(per.values()) / 3


# ---------------------------------------------------------------- compose
SIZE = 9.7                     # the largest size at which "Management" fits key 6's 58 columns
LEAD = 12
LOGO_XY = (20, 32)
URL_PEN, URL_CAP = 21, 66      # cap top 66 = logo bottom 49 + 17 px clear space
SLO_PEN, SLO_CAP = 234, 152
URL = ["io.stigg.io", "/usage"]
SLOGAN = ["The AI Usage", "Management", "Console"]


def compose(seed=SEED, p=FIELD):
    img = Image.new("RGB", (W, H), INK)
    logo, base_off = c.logo_image()
    img.paste(logo, LOGO_XY)
    ub = c.text(img, [(URL_PEN, URL_CAP, URL)], SIZE, LEAD)
    sb = c.text(img, [(SLO_PEN, SLO_CAP, SLOGAN)], SIZE, LEAD)
    col, src, smap = field(seed, p)
    d = ImageDraw.Draw(img)
    for (i, j) in CELLS:
        x, y = xy(i, j)
        d.rectangle([x, y, x + SQ - 1, y + SQ - 1], fill=col.get((i, j), UNLIT))
    return img, col, src, smap, ub, sb


def describe(seed, col, src, smap, ub, sb):
    hexc = lambda t: "#%02X%02X%02X" % t
    wc = lambda k: c.window_centre(k)
    tokens = {}
    for k in ART:
        I, J = GRID[k]
        mine = {cc: v for cc, v in col.items() if key_of(*cc) == k}
        x0, y0 = xy(I[0], J[0]); x1, y1 = xy(I[-1], J[-1])
        tokens["key %d" % k] = {
            "grid": "%d x %d, x %d-%d, y %d-%d" % (len(I), len(J), x0, x1 + SQ - 1, y0, y1 + SQ - 1),
            "grid_centre_offset_px": [round((x0 + x1 + SQ) / 2 - wc(k)[0], 1), round((y0 + y1 + SQ) / 2 - wc(k)[1], 1)],
            "lit": len(mine), "block": sum(1 for cc in mine if cc in src),
            "lime": sum(1 for cc, v in mine.items() if v == LIME and cc not in src),
            "lime_dim": sum(1 for v in mine.values() if v == LIME_MID),
            "white": sum(1 for v in mine.values() if v == WHITE),
            "unlit": len(I) * len(J) - len(mine)}
    lit = len(col)
    nwhite = sum(1 for v in col.values() if v == WHITE)
    slo_x0, slo_x1 = min(b[0] for b in sb), max(b[2] for b in sb)
    slo_last_base = SLO_CAP + c.cap_height(SIZE) + LEAD * (len(SLOGAN) - 1)
    url_last_base = URL_CAP + c.cap_height(SIZE) + LEAD * (len(URL) - 1)
    fails, _ = checks(col, src)
    weak, mean = adherence(col, smap)
    return {
        "variant": "d-logo-url-lockup", "seed": seed, "layout_checks": fails or "pass",
        "layout": {"key 1": "logo + URL lockup", "key 2": "burst (rising band)", "key 3": "burst (outer dust)",
                   "key 4": "burst source block + fragments", "key 5": "burst (plume)", "key 6": "slogan"},
        "type": {"font": "Soehne Buch", "size_px": SIZE, "leading_px": LEAD, "cap_height_px": c.cap_height(SIZE),
                 "slogan": {"pen_x": SLO_PEN, "cap_top": SLO_CAP, "ink_boxes": sb,
                            "ink_x": [slo_x0, slo_x1 - 1], "measure_centre_offset_px": round((slo_x0 + slo_x1) / 2 - wc(6)[0], 1),
                            "block_centre_offset_px": round((SLO_CAP + slo_last_base) / 2 - wc(6)[1], 1)},
                 "url": {"pen_x": URL_PEN, "cap_top": URL_CAP, "ink_boxes": ub}},
        "logo": {"xy": list(LOGO_XY), "size": [60, 17], "clear_space_below_px": URL_CAP - (LOGO_XY[1] + 17),
                 "group_centre_offset_px": [round(LOGO_XY[0] + 30 - wc(1)[0], 1),
                                            round((LOGO_XY[1] + url_last_base) / 2 - wc(1)[1], 1)]},
        "lattice": {"pitch": P, "square": SQ, "origin": [PX, PY], "rule": "x = 5i, y = 4 + 5j"},
        "colours": {"unlit": hexc(UNLIT), "lime": hexc(LIME), "lime_dim": hexc(LIME_MID), "white": hexc(WHITE)},
        "tokens": tokens,
        "tokens_total": {"lit": lit, "white": nwhite, "lime_incl_dim": lit - nwhite,
                         "white_pct": round(100 * nwhite / lit, 1),
                         "unlit": sum(len(GRID[k][0]) * len(GRID[k][1]) for k in ART) - lit},
        "stream_adherence": {"weakest_key": round(weak, 3), "mean": round(mean, 3)},
    }


def sheet(seeds, out, p=FIELD):
    tiles = []
    for s in seeds:
        img, col, src, smap, _, _ = compose(s, p)
        fails, n = checks(col, src)
        f = c.face(c.lcd(img), scale=2, plate=(34, 32, 30)) if os.environ.get("LCD") else c.face(img, scale=2)
        wp = round(100 * sum(1 for v in col.values() if v == WHITE) / len(col))
        ImageDraw.Draw(f).text((6, 4), "seed %d %s w%d%% %s" % (s, n, wp, "PASS" if not fails else fails[0][:40]),
                               fill=(255, 255, 255))
        tiles.append(f)
    cols = int(os.environ.get("COLS", 4))
    tw, th = tiles[0].size
    sh = Image.new("RGB", (cols * tw, ((len(tiles) + cols - 1) // cols) * th), (0, 0, 0))
    for n, t in enumerate(tiles):
        sh.paste(t, ((n % cols) * tw, (n // cols) * th))
    sh.save(out)
    return out


if __name__ == "__main__":
    if "--search" in sys.argv:
        N = int(sys.argv[sys.argv.index("--search") + 1])
        ranked = []
        for s in range(1, N + 1):
            col, src, smap = field(s)
            if not checks(col, src)[0]:
                weak, mean = adherence(col, smap)
                ranked.append((round(weak, 3), round(mean, 3), s))
        ranked.sort(reverse=True)
        print("%d of %d seeds pass every layout check; best by stream adherence:" % (len(ranked), N))
        for weak, mean, s in ranked[:20]:
            print("  seed %d  weakest key %.3f  mean %.3f" % (s, weak, mean))
        sys.exit(0)
    if "--sheet" in sys.argv:
        spec = sys.argv[sys.argv.index("--sheet") + 1]
        print(sheet([int(v) for v in spec.split(",")], sys.argv[sys.argv.index("--out") + 1]))
        sys.exit(0)
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else SEED
    img, col, src, smap, ub, sb = compose(seed)
    info = describe(seed, col, src, smap, ub, sb)
    assert info["layout_checks"] == "pass", info["layout_checks"]
    checks_out = c.render(img, HERE, extra=info)
    print(json.dumps(checks_out, indent=1))
    assert checks_out["hard_rules_pass"], "a hard rule failed"
