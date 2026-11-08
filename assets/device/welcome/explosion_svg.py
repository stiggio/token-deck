#!/usr/bin/env python3
"""Token explosion for a whole panel: the After Tokens burst (pixelmark.js) scaled up to a wall, on one strict grid.

Usage:
  python3 tools/explosion_svg.py out.svg [options]            writes out.svg (+ out.json sidecar)

The model is pixelmark's, generalised from the "ns" to a dense source block:
  1. source  - a dense block of tokens at the left of the art box ("the ns"), shape set by --source
  2. erode   - source cells toward its right edge break off with p = ((u-0.5)/0.5)^1.8 * erode
  3. flying  - each broken-off cell lands a little to the right (pixelmark's dx/dy formulas)
  4. spray   - N tokens blown out to the right: t = R^tpow, x = edge + t * reach, and a vertical
               spread that widens with t (the fan); most stay near the edge, the rest thin out
With --model field (used for the box's back wall) steps 3-4 are replaced by a density field: density
d0 * exp(-t / lam) inside a fan-shaped envelope, sampled cell by cell in a seeded random order, where a
token needs gap0 + gap1 * t cells of clearance, so the burst is dense and clustered at the edge and turns
into even dust further out. The particle steps still run first, so a seed keeps giving the same wall.
Every token snaps to the grid, one square per cell (pixelmark `snap`), never overlapping, and stays
inside the safe area. Randomness is pixelmark's LCG; white/lime is drawn from its own stream, so
--white recolours tokens without moving any of them.

Options (mm unless noted):
  --panel 162x65      panel size; the SVG viewBox is the whole panel, art upright, transparent
  --safe 5            safe margin inside the panel
  --pitch 1.5         grid pitch; square = ratio * pitch (default ratio 0.8, the lockups' 4:1)
  --ratio 0.8
  --source band|core|edge|wave   band: a rounded upright bar; core: a shorter rounded block; edge: full
                      height; wave: full height with an S-curved right boundary (the s of "Tokens", magnified)
  --wave-amp 4        wave: amplitude of the S curve (mm); --wave-phase shifts it (radians)
  --src-w 10          source width
  --src-h 0.6         source height as a fraction of the art height (band/core)
  --src-y 0.5         source centre as a fraction of the art height
  --erode 0.55        pixelmark erode
  --spray 400         number of spray tokens (before collisions)
  --reach 1.0         spray reach as a fraction of the art width beyond the source edge
  --spread0 0.35      vertical half-spread next to the source (fraction of the art height)
  --spread1 0.55      extra half-spread at full reach (the fan opening)
  --tpow 1.25         t = R^tpow (pixelmark 1.25; larger = more tokens near the source)
  --falloff pow|exp   pow: t = R^tpow (pixelmark); exp: t from a truncated exponential, mean ~tau
  --tau 0.3           exp falloff length as a fraction of the reach (density drops by e every tau)
  --fanpow 1.0        spread = spread0 + spread1 * t^fanpow (below 1 the fan opens early)
  --u0 0.5            erosion starts at this fraction across the source (pixelmark 0.5)
  --erode-pow 1.8     erosion curve exponent (pixelmark 1.8)
  --dust-from 2       beyond this t, a token needs --dust-gap cells to its neighbours (even dust, no clumps)
  --dust-gap 1.5
  --up 0.5            share of spray tokens that fly upward (pixelmark 0.5)
  --rise 0            the fan's centre line climbs this fraction of the art height over the full reach
  --air 0             keep this many empty grid cells inside the safe area at the top, bottom and right
  --air-left 0        ... and at the left (the source moves in by this much)
  --model particles|field   particles: pixelmark's spray (above). field: a density field sampled in a
                      random order with a minimum spacing that grows with distance (even dust far out):
  --lam 0.22          field: density falls by e every lam * reach beyond the source edge
  --d0 0.75           field: density right at the source edge
  --soft 0.35         field: softness of the fan's edges (fraction of the local half-spread)
  --gap0 0 --gap1 2.6 field: minimum centre distance to other tokens, gap0 + gap1 * t (cells)
  --rays 0            >0: spray tokens travel along this many rays fanning from the source edge (debris trails)
  --ray-angle 14      half-angle of the ray fan, degrees
  --ray-width 0.8     sideways scatter around a ray, cells
  --ypow 0.8          vertical offset = R^ypow * spread (pixelmark 0.8)
  --white 0           fraction of spray tokens drawn #ffffff (BRIEF 6: ~0.4 like the stigg.io field)
  --white-from 0.15   white tokens only beyond this t (the dense edge stays lime)
  --seed 11
"""
import argparse, json, math
from pathlib import Path

LIME, WHITE = '#92e759', '#ffffff'

ap = argparse.ArgumentParser()
ap.add_argument('out')
ap.add_argument('--panel', default='162x65')
ap.add_argument('--safe', type=float, default=5)
ap.add_argument('--pitch', type=float, default=1.5)
ap.add_argument('--ratio', type=float, default=0.8)
ap.add_argument('--source', choices=['band', 'core', 'edge', 'wave'], default='band')
ap.add_argument('--wave-amp', type=float, default=4)
ap.add_argument('--wave-phase', type=float, default=0)
ap.add_argument('--src-w', type=float, default=10)
ap.add_argument('--src-h', type=float, default=0.6)
ap.add_argument('--src-y', type=float, default=0.5)
ap.add_argument('--erode', type=float, default=0.55)
ap.add_argument('--spray', type=int, default=400)
ap.add_argument('--reach', type=float, default=1.0)
ap.add_argument('--spread0', type=float, default=0.35)
ap.add_argument('--spread1', type=float, default=0.55)
ap.add_argument('--tpow', type=float, default=1.25)
ap.add_argument('--falloff', choices=['pow', 'exp'], default='pow')
ap.add_argument('--tau', type=float, default=0.3)
ap.add_argument('--fanpow', type=float, default=1.0)
ap.add_argument('--u0', type=float, default=0.5)
ap.add_argument('--erode-pow', type=float, default=1.8)
ap.add_argument('--dust-from', type=float, default=2.0)
ap.add_argument('--dust-gap', type=float, default=1.5)
ap.add_argument('--up', type=float, default=0.5)
ap.add_argument('--rise', type=float, default=0.0)
ap.add_argument('--air', type=int, default=0)
ap.add_argument('--air-left', type=int, default=0)
ap.add_argument('--model', choices=['particles', 'field'], default='particles')
ap.add_argument('--lam', type=float, default=0.22)
ap.add_argument('--d0', type=float, default=0.75)
ap.add_argument('--soft', type=float, default=0.35)
ap.add_argument('--gap0', type=float, default=0.0)
ap.add_argument('--gap1', type=float, default=2.6)
ap.add_argument('--rays', type=int, default=0)
ap.add_argument('--ray-angle', type=float, default=14)
ap.add_argument('--ray-width', type=float, default=0.8)
ap.add_argument('--ypow', type=float, default=0.8)
ap.add_argument('--white', type=float, default=0.0)
ap.add_argument('--white-from', type=float, default=0.15)
ap.add_argument('--seed', type=int, default=11)
a = ap.parse_args()

class LCG:  # pixelmark.js rng(seed)
    def __init__(self, seed): self.s = (seed & 0xffffffff) or 1
    def __call__(self):
        self.s = (self.s * 1664525 + 1013904223) & 0xffffffff
        return self.s / 4294967296
R = LCG(a.seed)
RW = LCG(a.seed * 7919 + 17)                      # colour only: white or not never moves a token

PW, PH = (float(v) for v in a.panel.lower().split('x'))
AW, AH = PW - 2 * a.safe, PH - 2 * a.safe
p, sq = a.pitch, round(a.pitch * a.ratio, 4)
gap = round(p - sq, 4)
NC = int((AW - sq) // p) + 1; NR = int((AH - sq) // p) + 1
gx0 = a.safe + (AW - ((NC - 1) * p + sq)) / 2     # left edge of column 0's square, grid centred in the art box
gy0 = a.safe + (AH - ((NR - 1) * p + sq)) / 2

# 1. source cells (in grid units; x to the right, y down)
sw = max(2, round(a.src_w / p))
yc = (NR - 1) * a.src_y
src = set()
edge_at = {}                                       # per row: the source's right edge (cells), for erosion
if a.source == 'edge':
    src = {(i, j) for i in range(sw) for j in range(NR)}
elif a.source == 'wave':
    amp = a.wave_amp / p
    for j in range(NR):
        e = sw + amp * math.sin(2 * math.pi * j / (NR - 1) + a.wave_phase)
        edge_at[j] = e
        for i in range(max(1, int(round(e)))): src.add((i, j))
else:
    hh = NR * a.src_h / 2                          # half height in cells
    r = sw * (0.55 if a.source == 'band' else 0.9) # corner radius of the rounded block, cells
    for i in range(sw):
        for j in range(NR):
            dy = abs(j - yc)
            # rounded rectangle: inside the straight part, or inside the corner circles on the right side
            if dy <= hh - r: src.add((i, j)); continue
            if dy > hh: continue
            cx, cy = sw - 1 - r, hh - r
            if i <= cx or (i - cx) ** 2 + (dy - cy) ** 2 <= r * r: src.add((i, j))
if a.air_left:                                     # move the source in from the left margin
    src = {(i + a.air_left, j) for i, j in src}
    edge_at = {j: e + a.air_left for j, e in edge_at.items()}
src = {(i, j) for i, j in src if a.air <= j < NR - a.air}
right = max(i for i, _ in src) + 1                 # the source's right edge, in cells
inside = lambda i, j: a.air_left <= i < NC - a.air and a.air <= j < NR - a.air
taken = set(src)
tokens = {}                                        # (i, j) -> colour
flying = []
# 2. erosion (pixelmark: u is 0 at the inner side of the source, 1 at its right edge)
for (i, j) in sorted(src, key=lambda c: (c[1], c[0])):
    u = (i + 1 - a.air_left) / ((edge_at[j] if j in edge_at else right) - a.air_left)
    pr = 0 if u <= a.u0 else ((u - a.u0) / (1 - a.u0)) ** a.erode_pow * a.erode
    if R() < pr: flying.append((i, j, u))
    else: tokens[(i, j)] = LIME
def put(x, y, colour, t=0.0):
    i, j = round(x), round(y)
    if (i, j) in taken or not inside(i, j): return False
    if t > a.dust_from:
        g = a.dust_gap; r = int(math.ceil(g))
        if any((i + di, j + dj) in tokens for di in range(-r, r + 1) for dj in range(-r, r + 1) if (di or dj) and di * di + dj * dj <= g * g): return False
    taken.add((i, j)); tokens[(i, j)] = colour; return True
# 3. flying cells, displaced as pixelmark does (in cells)
reach = a.reach * (NC - a.air - right)
for (i, j, u) in flying:
    t = R() ** 1.4
    dx = (0.5 + t * 4) + u * 3.5 * R()            # fragments land within a few cells, as on the logo (reachX*0.25 ~ 3 cells there)
    dy = (j - yc) * (0.15 + t * 0.6) + (R() - 0.5) * 3
    put(i + dx, j + dy, LIME)
# 4. spray: the fan
E1 = 1 - math.exp(-1 / a.tau)
rays = []
for k in range(a.rays):                            # each ray: an origin on the source edge and a direction
    th = math.radians(a.ray_angle) * (2 * (k + 0.5) / a.rays - 1 + (R() - 0.5) * 1.2 / a.rays)
    y0 = yc + (R() - 0.5) * (NR * a.src_h if a.source != 'edge' else NR) * 0.8
    rays.append((th, y0))
for _ in range(a.spray if a.rays else 0):
    k = int(R() * a.rays); th, y0 = rays[k]
    t = R() ** a.tpow if a.falloff == 'pow' else -a.tau * math.log(1 - R() * E1)
    d = t * reach
    w = (R() - 0.5) * 2 * a.ray_width * (1 + d / 40)
    x = right - 1 + d * math.cos(th) - w * math.sin(th)
    y = y0 + d * math.sin(th) + w * math.cos(th)
    colour = WHITE if (t > a.white_from and RW() < a.white) else LIME
    put(x, y, colour, t)
for _ in range(0 if a.rays else a.spray):
    t = R() ** a.tpow if a.falloff == 'pow' else -a.tau * math.log(1 - R() * E1)
    x = right - 2 + t * reach
    up = R() < a.up
    spread = NR * (a.spread0 + a.spread1 * t ** a.fanpow)
    y = yc - a.rise * NR * t + (-1 if up else 1) * R() ** a.ypow * spread
    colour = WHITE if (t > a.white_from and RW() < a.white) else LIME
    put(x, y, colour, t)

if a.model == 'field':
    # restart from the source only: erosion and particles above are replaced by one sampled density field
    tokens = {c: LIME for c in src}; taken = set(src)
    order = [(i, j) for i in range(NC) for j in range(NR)]
    for k in range(len(order) - 1, 0, -1):          # Fisher-Yates with the pixelmark LCG
        m = int(R() * (k + 1)); order[k], order[m] = order[m], order[k]
    def smooth(e0, e1, v):
        v = max(0.0, min(1.0, (v - e0) / (e1 - e0))); return v * v * (3 - 2 * v)
    for (i, j) in order:
        if (i, j) in taken or not inside(i, j): continue
        edge = edge_at.get(j, right)
        if i < edge - 3: continue                    # deep inside / behind the source: leave it as drawn
        t = max(0.0, (i - edge + 1) / reach)
        if t > 1: continue
        h = NR * (a.spread0 + a.spread1 * t ** a.fanpow)
        yc_t = yc - a.rise * NR * t
        dy = abs(j - yc_t)
        env = 1 - smooth(h * (1 - a.soft), h * (1 + a.soft), dy)
        if a.source == 'edge' or a.source == 'wave': env = 1.0
        d = a.d0 * math.exp(-t / a.lam) * env
        if R() >= d: continue
        g = a.gap0 + a.gap1 * t
        if g > 0:
            r = int(math.ceil(g))
            if any((i + di, j + dj) in tokens for di in range(-r, r + 1) for dj in range(-r, r + 1) if (di or dj) and di * di + dj * dj < g * g): continue
        colour = WHITE if (t > a.white_from and RW() < a.white) else LIME
        tokens[(i, j)] = colour; taken.add((i, j))
    # erode the source's right side, as pixelmark erodes the s (cells nearest the edge break off)
    for (i, j) in sorted(src, key=lambda c: (c[1], c[0])):
        edge = edge_at.get(j, right); u = (i + 1 - a.air_left) / (edge - a.air_left)
        pr = 0 if u <= a.u0 else ((u - a.u0) / (1 - a.u0)) ** a.erode_pow * a.erode
        if R() < pr: tokens.pop((i, j), None)
    flying = []

# SVG + sidecar
f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(PW)} {f(PH)}">']
for colour, gid in ((LIME, 'tokens-lime'), (WHITE, 'tokens-white')):
    cells = sorted(c for c, col in tokens.items() if col == colour)
    if not cells: continue
    lines.append(f'<g id="{gid}">')
    for (i, j) in sorted(cells, key=lambda c: (c[1], c[0])):
        lines.append(f'<rect x="{f(gx0 + i * p)}" y="{f(gy0 + j * p)}" width="{f(sq)}" height="{f(sq)}" fill="{colour}"/>')
    lines.append('</g>')
lines.append('</svg>')
Path(a.out).write_text('\n'.join(lines) + '\n')
xs = [gx0 + i * p for i, _ in tokens]; ys = [gy0 + j * p for _, j in tokens]
n_lime = sum(1 for c in tokens.values() if c == LIME); n_white = len(tokens) - n_lime
side = {
    'file': Path(a.out).name, 'units': 'mm', 'panel': [PW, PH], 'viewBox': [0, 0, PW, PH], 'safe': a.safe,
    'artBox': {'x': a.safe, 'y': a.safe, 'w': AW, 'h': AH},
    'bbox': {'x': round(min(xs), 4), 'y': round(min(ys), 4), 'w': round(max(xs) + sq - min(xs), 4), 'h': round(max(ys) + sq - min(ys), 4)},
    'pitch': p, 'square': sq, 'gap': gap, 'grid': {'cols': NC, 'rows': NR, 'x0': round(gx0, 4), 'y0': round(gy0, 4)},
    'counts': {'tokens': len(tokens), 'lime': n_lime, 'white': n_white, 'source': len(src), 'flying': len(flying), 'cellsFilled': round(len(tokens) / (NC * NR), 4)},
    'params': {k: v for k, v in vars(a).items() if k != 'out'},
}
Path(a.out).with_suffix('.json').write_text(json.dumps(side, indent=2) + '\n')
print(f"{a.out}: {NC}x{NR} grid, pitch {p} / square {sq} / gap {gap} mm, {len(tokens)} tokens ({n_lime} lime, {n_white} white), {side['counts']['cellsFilled'] * 100:.1f}% of cells")
