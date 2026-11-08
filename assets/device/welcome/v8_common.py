"""Shared helpers for the v8 welcome-screen candidates (Nov 2, 2026), own code.

v8 answers Gabriel's notes on v7 as burned (photos/welcome-v7-on-deck.webp): tokens in the URL's key too,
no big empty margin between the boards and the window edges, URL bottom left and slogan bottom right.
Every candidate imports this module, so all of them are laid out, rendered, checked and previewed the
same way. It builds on v7_common (render, previews, the LCD emulation) and welcome_v7 (the type pipeline).

  board_fit(key, max_off)  the largest board of 3 px tokens on a 5 px pitch that stays inside region(key)
                           with its centre within max_off px of the WINDOW centre on both axes
  BOARDS                   {key: (x0, y0, cols, rows)} for keys 2-6 (max_off 1.5 px)
  board_cells(key)         [(a, b)] column / row indices of a key's board; cell_px(key, a, b) -> (x, y)
  quiet(key)               {(a, b)}: cells whose token shares an 8 x 8 JPEG block with window pixels
                           outside the tile; they stay unlit (#2C2F2B), never lime or white
  measure(lines, size, track, leading)   ink box of each line, pen x 0 / cap top 0
  text(img, pen_x, cap_top, lines, size, track, leading, align)   v7's type at any size; align 'left'
                           (pen x is the left ink edge), 'right' (pen x is the right ink edge, each line
                           flush on it) or 'centre' (pen x is the centre of each line's ink)
  render(img, outdir, extra)   v7_common.render plus the colour halo (worst channel deviation from
                           #131512 outside the tiles, decoded as burned); returns checks
  photo_sheet(dirs, out)   the v7 photo of the deck next to each candidate's LCD preview

Board geometry, why: the firmware draws each key's 64 x 64 tile at a fixed spot that is off-centre in the
window (flush with the left edge in the right column, 1 px from the top and 11 px above the bottom in the
bottom row), and the burned image stays visible around the app's tiles at runtime, so nothing may be
drawn outside the tiles. A board centred on its window can therefore be at most as wide as twice the
distance from the window centre to the nearer tile edge. v7 used one 10 x 10 board (48 px) everywhere,
the largest that fits every key; v8 fits each key on its own (its own lattice phase: the bezels between
keys hide 32-40 px, so no one can see whether the lattice continues from one key to the next).
"""
import json, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v7_common as c                                     # noqa: E402
import welcome_v7 as w7                                   # noqa: E402
from panel_geometry import TILE, WINDOWS, tile_origin     # noqa: E402

W, H = c.W, c.H
INK, LIME, WHITE = c.INK, c.LIME, c.WHITE
UNLIT = (0x2C, 0x2F, 0x2B)          # Stigg neutral 800, v7's board colour (seen on the deck in the v7 photo)
MID_LIME = (0x63, 0x98, 0x40)       # After Tokens depth step
PITCH, SQ = 5, 3
RIM = c.RIM
PHOTO_V7 = os.path.join(HERE, "..", "photos", "welcome-v7-on-deck.webp")
RGB_HALO_SOFT = 10                  # v6 burned with a 10-level blue bleed beside its source block, unnoticed


def window_centre(key):
    return c.window_centre(key)


def board_fit(key, max_off=1.5, rim=RIM, min_n=8, max_n=13):
    """(x0, y0, cols, rows) of the largest board inside region(key) centred on the window to max_off px.
    Ties go to the smaller offset."""
    rx0, ry0, rx1, ry1 = c.region(key, rim)                 # exclusive right / bottom
    cx, cy = window_centre(key)
    best = None
    for nc in range(min_n, max_n + 1):
        wpx = PITCH * nc - (PITCH - SQ)
        for x0 in range(rx0, rx1 - wpx + 1):
            ox = x0 + wpx / 2.0 - cx
            if abs(ox) > max_off:
                continue
            for nr in range(min_n, max_n + 1):
                hpx = PITCH * nr - (PITCH - SQ)
                for y0 in range(ry0, ry1 - hpx + 1):
                    oy = y0 + hpx / 2.0 - cy
                    if abs(oy) > max_off:
                        continue
                    score = (nc * nr, -(abs(ox) + abs(oy)))
                    if best is None or score > best[0]:
                        best = (score, (x0, y0, nc, nr))
    return best[1] if best else None


BOARDS = {k: board_fit(k) for k in (2, 3, 4, 5, 6)}


def board_px(key, board=None):
    x0, y0, nc, nr = board or BOARDS[key]
    return x0, y0, x0 + PITCH * nc - (PITCH - SQ) - 1, y0 + PITCH * nr - (PITCH - SQ) - 1   # inclusive


def board_offset(key, board=None):
    x0, y0, x1, y1 = board_px(key, board)
    cx, cy = window_centre(key)
    return round((x0 + x1 + 1) / 2.0 - cx, 1), round((y0 + y1 + 1) / 2.0 - cy, 1)


def board_cells(key, board=None):
    x0, y0, nc, nr = board or BOARDS[key]
    return [(a, b) for b in range(nr) for a in range(nc)]


def cell_px(key, a, b, board=None):
    x0, y0, nc, nr = board or BOARDS[key]
    return x0 + PITCH * a, y0 + PITCH * b


def _outside_tiles_in_window(x, y):
    for (x0, y0, x1, y1) in WINDOWS:
        if x0 <= x < x1 and y0 <= y < y1:
            for k in range(1, 7):
                tx, ty = tile_origin(k)
                if tx <= x < tx + TILE and ty <= y < ty + TILE:
                    return False
            return True
    return False


def _block_leaks(bx, by, n=8):
    return any(_outside_tiles_in_window(x, y) for y in range(by, by + n) for x in range(bx, bx + n))


def quiet(key, board=None, n=8):
    """Cells whose 3 x 3 token touches an n x n JPEG block (aligned on multiples of n in panel space; the
    90 degree rotation keeps that alignment because 240 is a multiple of 16) that also holds window pixels
    outside the tiles. Lit tokens there ring outside the tile; keep them unlit."""
    out = set()
    for (a, b) in board_cells(key, board):
        x, y = cell_px(key, a, b, board)
        blocks = {((x + dx) // n * n, (y + dy) // n * n) for dx in range(SQ) for dy in range(SQ)}
        if any(_block_leaks(bx, by, n) for bx, by in blocks):
            out.add((a, b))
    return out


def draw_board(img, key, lit=None, board=None, skip=()):
    """Every cell an unlit token unless lit[(a, b)] gives its colour; cells in skip draw nothing."""
    d = ImageDraw.Draw(img)
    lit = lit or {}
    for (a, b) in board_cells(key, board):
        if (a, b) in skip:
            continue
        x, y = cell_px(key, a, b, board)
        d.rectangle([x, y, x + SQ - 1, y + SQ - 1], fill=lit.get((a, b), UNLIT))


# ---------------------------------------------------------------- type (v7's pipeline at any size)
def _set(size, track, leading):
    w7.SIZE, w7.TRACK, w7.LEADING = size, track, leading


def measure(lines, size=10.5, track=-0.06, leading=13):
    """Ink box (x0, y0, x1, y1), exclusive right / bottom, of each line drawn at pen x 0, cap top 0."""
    _set(size, track, leading)
    pen, cap = 100.0, 100
    _, boxes = w7.text_mask([(pen, cap, lines)])
    return [(b[0] - pen, b[1] - cap, b[2] - pen, b[3] - cap) for b in boxes]


def text(img, pen_x, cap_top, lines, size=10.5, track=-0.06, leading=13, align="left", fg=WHITE):
    """Draws the lines; returns each line's ink box (exclusive right / bottom). Pen positions are snapped
    to whole pixels so stems stay crisp (v7 did the same for the URL)."""
    _set(size, track, leading)
    boxes = measure(lines, size, track, leading)
    blocks = []
    for n, (t, bx) in enumerate(zip(lines, boxes)):
        if align == "left":
            px = pen_x - bx[0]
        elif align == "right":
            px = pen_x - bx[2]
        else:
            px = pen_x - (bx[0] + bx[2]) / 2.0
        blocks.append((float(round(px)), cap_top + n * leading, [t]))
    _set(size, track, leading)
    w7.v6.GAMMA = w7.GAMMA
    cov, out = w7.text_mask([(p, ct, [t]) for p, ct, (t,) in blocks])
    w7.v6.composite_text(img, cov, fg)
    return out


def ink_box(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def centre_offset(box, key):
    cx, cy = window_centre(key)
    return round((box[0] + box[2]) / 2.0 - cx, 1), round((box[1] + box[3]) / 2.0 - cy, 1)


def logo(img, xy=(20, 50)):
    lg, _ = c.logo_image()
    img.paste(lg, xy)
    return (xy[0], xy[1], xy[0] + lg.width, xy[1] + lg.height)


# ---------------------------------------------------------------- render and checks
def rgb_halo(seen):
    px = seen.load(); worst = [0, 0, 0]; cnt = 0
    tiles = [tile_origin(k) for k in range(1, 7)]
    for (x0, y0, x1, y1) in WINDOWS:
        for y in range(y0, y1):
            for x in range(x0, x1):
                if any(tx <= x < tx + TILE and ty <= y < ty + TILE for tx, ty in tiles):
                    continue
                dv = [abs(px[x, y][i] - INK[i]) for i in range(3)]
                worst = [max(a, b) for a, b in zip(worst, dv)]
                cnt += max(dv) > 4
    return worst, cnt


def render(img, outdir, extra=None):
    """v7_common.render (hard rules: outside_tiles 0, darker 0, rim 0, halo_count 0, JPEG <= 22,300 bytes)
    plus the colour halo; hard_rules_pass also needs the colour halo <= RGB_HALO_SOFT."""
    checks = c.render(img, outdir, extra)
    seen = c.v6.decode_box(open(os.path.join(outdir, "welcome-sent.jpg"), "rb").read())
    worst, cnt = rgb_halo(seen)
    checks["rgb_halo_worst"] = worst
    checks["rgb_halo_pixels_over_4"] = cnt
    checks["hard_rules_pass"] = bool(checks["hard_rules_pass"] and max(worst) <= RGB_HALO_SOFT)
    json.dump(checks, open(os.path.join(outdir, "checks.json"), "w"), indent=2, default=str)
    return checks


_PH_BG = (55, 91, 122)              # #131512 in the v7 photo (window area beside key 3's board)
_PH_WH = (130, 225, 250)            # #FFFFFF tokens in the v7 photo
_PH_LIN = [c._s2l(v) for v in range(256)]


def photo_emul(img):
    """How the phone camera rendered v7 (photos/welcome-v7-on-deck.webp): blue-lifted black, and a steep tone
    curve that lifts dark greys. The unlit #2C2F2B tokens measured about (70, 135, 185) on (55, 91, 122)
    black, about a third of the way to white, far brighter than lcd() draws them. Per channel:
    out = black + (white - black) * t ** 0.3, t = linear light above #131512. Lime comes out a little
    greyer than the photo (the camera's colour matrix is not modelled)."""
    luts = []
    for ch in range(3):
        b0 = _PH_LIN[INK[ch]]
        luts.append([round(_PH_BG[ch] + (_PH_WH[ch] - _PH_BG[ch]) * max(0.0, (_PH_LIN[v] - b0) / (1 - b0)) ** 0.3)
                     for v in range(256)])
    return Image.merge("RGB", [band.point(luts[i]) for i, band in enumerate(img.convert("RGB").split())])


def photo_preview(outdir):
    """preview-photo-3x.png next to a candidate's welcome-sent.jpg (decoded as burned)."""
    seen = c.v6.decode_box(open(os.path.join(outdir, "welcome-sent.jpg"), "rb").read())
    c.face(photo_emul(seen), plate=(20, 18, 16)).save(os.path.join(outdir, "preview-photo-3x.png"))


def photo_sheet(dirs, out, labels=None, which="preview-lcd-3x.png"):
    """Row 1: the v7 photo of the deck (what Gabriel saw). Then each candidate's preview."""
    ph = Image.open(PHOTO_V7).convert("RGB").crop((280, 420, 1380, 1160))
    ims = [("v7 on the deck (photo)", ph.resize((1032, int(1032 * ph.height / ph.width))))]
    for i, dname in enumerate(dirs):
        ims.append(((labels or [os.path.basename(d.rstrip("/")) for d in dirs])[i],
                    Image.open(os.path.join(dname, which)).convert("RGB")))
    cols = 2
    cw = max(im.width for _, im in ims); ch = max(im.height for _, im in ims) + 24
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cw + 10) + 10, rows * (ch + 10) + 10), (50, 50, 50))
    d = ImageDraw.Draw(sheet)
    for n, (name, im) in enumerate(ims):
        x = 10 + (n % cols) * (cw + 10); y = 10 + (n // cols) * (ch + 10)
        d.text((x, y), name, fill=(255, 255, 255))
        sheet.paste(im, (x, y + 20))
    sheet.save(out)
    return out


if __name__ == "__main__":
    for k in (2, 3, 4, 5, 6):
        print("key", k, "board", BOARDS[k], "px", board_px(k), "offset vs window", board_offset(k),
              "quiet", sorted(quiet(k)))
    print("text ink at 10.5 / -0.06:", measure(["The AI Usage", "Management", "Console", "io.stigg.io", "/usage"]))
    print("text ink at 9.5 / -0.06:", measure(["The AI Usage", "Management", "Console"], 9.5, -0.06, 12))
