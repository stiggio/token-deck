"""Shared helpers for the v7 welcome-screen candidates (Nov 2, 2026), own code.

Every candidate imports this module so all of them are rendered, checked and previewed the same way.

  region(key)            tile rect intersected with the window shrunk by RIM: where content may sit
  centred_budget(key)    the largest box centred on the key's WINDOW that stays inside region(key)
  measure(lines, size, leading)   ink boxes of each line (pen x 0, cap top 0), from v6's type pipeline
  text(img, blocks, size, leading)   v6's sub-pixel, gamma-1.5 type; blocks = [(pen_x, cap_top, lines)]
  logo_image()           the official logo, 60 x 17, plus its wordmark baseline offset (from v6)
  lcd(img)               a crude emulation of how the panel photographs (fitted to the Nov 2 photo)
  render(img, outdir)    writes the standard files and returns (and writes) checks.json
  compare_sheet(dirs, out)   one PNG with every candidate's previews side by side
"""
import io, json, os, subprocess, sys, tempfile
from PIL import Image, ImageChops, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from panel_geometry import TILE, WINDOWS, tile_origin
import welcome_screen as base
import welcome_v6 as v6

W, H = 320, 240
INK = (0x13, 0x15, 0x12)
LIME = (0x92, 0xE7, 0x59)
WHITE = (0xFF, 0xFF, 0xFF)
UNLIT = (0x3C, 0x3E, 0x3A)        # Stigg neutral "borders" grey: visible on the panel, below the lit tokens
RIM = 6
QUALITY = 97
MAX_JPEG = 22300                  # the largest LOG write verified on the unit (22,307 bytes)


def window_centre(key):
    x0, y0, x1, y1 = WINDOWS[key - 1]
    return (x0 + x1) / 2, (y0 + y1) / 2


def region(key, rim=RIM):
    tx, ty = tile_origin(key)
    wx0, wy0, wx1, wy1 = WINDOWS[key - 1]
    return (max(tx, wx0 + rim), max(ty, wy0 + rim), min(tx + TILE, wx1 - rim), min(ty + TILE, wy1 - rim))


def centred_budget(key, rim=RIM):
    cx, cy = window_centre(key)
    x0, y0, x1, y1 = region(key, rim)
    hw, hh = min(cx - x0, x1 - cx), min(cy - y0, y1 - cy)
    return (cx - hw, cy - hh, cx + hw, cy + hh)


def _set_type(size, leading):
    v6.SIZE, v6.LEADING = size, leading


def measure(lines, size, leading):
    """Ink box (x0, y0, x1, y1) of each line drawn with pen x = 0 and cap top y = 0."""
    _set_type(size, leading)
    pen, cap = 40, 40
    _, boxes = v6.text_mask([(pen, cap, lines)])
    return [(b[0] - pen, b[1] - cap, b[2] - pen, b[3] - cap) for b in boxes]


def cap_height(size):
    f = v6.ImageFont.truetype(base.FONT, size)
    b = f.getbbox("H")
    return b[3] - b[1]


def text(img, blocks, size, leading, fg=WHITE):
    """Draw blocks [(pen_x, cap_top_y, [lines])] with v6's type pipeline; returns each line's ink box."""
    _set_type(size, leading)
    cov, boxes = v6.text_mask(blocks)
    v6.composite_text(img, cov, fg)
    return boxes


def logo_image():
    return v6.logo_image()


def _s2l(v):
    v /= 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def _l2s(v):
    v = max(0.0, min(1.0, v))
    return round(255 * (v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055))


_BLK = [_s2l(c) for c in (40, 74, 112)]       # #131512 as the Nov 2 photo shows it (raised, blue black)
_WHT = [_s2l(c) for c in (171, 221, 252)]     # #FFFFFF as the photo shows it
_LUT = [[_l2s(_BLK[c] + (_WHT[c] - _BLK[c]) * _s2l(v)) for v in range(256)] for c in range(3)]


def lcd(img):
    """Per-channel affine map in linear light from the photo: raised blue black, cool white. Crude: it
    only says whether dim things stay visible against the panel's black, not exact colours."""
    return Image.merge("RGB", [ch.point(_LUT[i]) for i, ch in enumerate(img.convert("RGB").split())])


def face(img, scale=3, plate=(8, 8, 8), runtime=False):
    pad = 12
    out = Image.new("RGB", ((W + 2 * pad) * scale, (H + 2 * pad) * scale), plate)
    big = img.resize((W * scale, H * scale), Image.NEAREST)
    if runtime:
        d = ImageDraw.Draw(big)
        for k in range(1, 7):
            tx, ty = tile_origin(k)
            d.rectangle([tx * scale, ty * scale, (tx + TILE) * scale - 1, (ty + TILE) * scale - 1], fill=(60, 62, 58))
    for (x0, y0, x1, y1) in WINDOWS:
        out.paste(big.crop((x0 * scale, y0 * scale, x1 * scale, y1 * scale)), ((x0 + pad) * scale, (y0 + pad) * scale))
    return out


def _inside_tiles(x, y):
    for k in range(1, 7):
        tx, ty = tile_origin(k)
        if tx <= x < tx + TILE and ty <= y < ty + TILE:
            return True
    return False


def rim_violations(img, rim=RIM):
    """Non-ink source pixels inside a window but closer than rim to its edge."""
    px = img.load(); bad = 0
    for (x0, y0, x1, y1) in WINDOWS:
        for y in range(y0, y1):
            for x in range(x0, x1):
                if px[x, y] != INK and (x < x0 + rim or x >= x1 - rim or y < y0 + rim or y >= y1 - rim):
                    bad += 1
    return bad


def lime_purity(img, seen):
    """For source pixels that are exactly LIME: mean and max channel deviation after the deck's decode."""
    s, d = img.load(), seen.load(); n = 0; tot = 0; worst = 0
    for y in range(H):
        for x in range(W):
            if s[x, y] == LIME:
                dev = max(abs(a - b) for a, b in zip(d[x, y], LIME)); n += 1; tot += dev; worst = max(worst, dev)
    return {"lime_pixels": n, "mean_dev": round(tot / n, 1) if n else 0, "max_dev": worst}


def render(img, outdir, extra=None):
    """Standard outputs + checks. Hard rules: outside_tiles == 0, darker == 0, rim == 0, halo_count == 0,
    jpeg_bytes <= MAX_JPEG."""
    os.makedirs(outdir, exist_ok=True)
    outside, darker = v6.source_clean(img)
    data = v6.jpeg(img, QUALITY)
    seen = v6.decode_box(data)
    cnt, worst = v6.halo(seen)
    checks = {"outside_tiles": outside, "darker_than_ink": darker, "rim": rim_violations(img),
              "jpeg_bytes": len(data), "halo_count": cnt, "halo_worst": worst, "lime": lime_purity(img, seen)}
    checks["hard_rules_pass"] = (outside == 0 and darker == 0 and checks["rim"] == 0 and cnt == 0
                                 and len(data) <= MAX_JPEG)
    if extra:
        checks.update(extra)
    img.save(os.path.join(outdir, "welcome-320x240.png"))
    open(os.path.join(outdir, "welcome-sent.jpg"), "wb").write(data)
    face(seen).save(os.path.join(outdir, "preview-face-3x.png"))
    face(seen, scale=1).save(os.path.join(outdir, "preview-face-1x.png"))
    face(lcd(seen), plate=(34, 32, 30)).save(os.path.join(outdir, "preview-lcd-3x.png"))
    face(lcd(seen), scale=1, plate=(34, 32, 30)).save(os.path.join(outdir, "preview-lcd-1x.png"))
    face(seen, runtime=True).save(os.path.join(outdir, "preview-runtime-3x.png"))
    amp = Image.eval(ImageChops.difference(seen, Image.new("RGB", (W, H), INK)), lambda v: min(255, v * 6))
    d = ImageDraw.Draw(amp)
    for k in range(1, 7):
        tx, ty = tile_origin(k)
        d.rectangle([tx, ty, tx + TILE - 1, ty + TILE - 1], fill=(40, 40, 40))
    face(amp).save(os.path.join(outdir, "preview-halo-x6-3x.png"))
    json.dump(checks, open(os.path.join(outdir, "checks.json"), "w"), indent=2)
    return checks


def compare_sheet(dirs, out, which=("preview-face-3x.png", "preview-lcd-3x.png")):
    rows = []
    for dname in dirs:
        ims = [Image.open(os.path.join(dname, w)) for w in which]
        rows.append((os.path.basename(dname.rstrip("/")), ims))
    w = sum(im.width for im in rows[0][1]) + 10 * (len(which) + 1)
    h = sum(r[1][0].height + 30 for r in rows) + 10
    sheet = Image.new("RGB", (w, h), (50, 50, 50)); d = ImageDraw.Draw(sheet); y = 10
    for name, ims in rows:
        d.text((10, y), name, fill=(255, 255, 255)); x = 10
        for im in ims:
            sheet.paste(im, (x, y + 20)); x += im.width + 10
        y += ims[0].height + 30
    sheet.save(out)
    return out


if __name__ == "__main__":
    img = Image.open(os.path.join(HERE, "welcome-v6-320x240.png")).convert("RGB")   # v6, as burned on Nov 2
    print(json.dumps(render(img, os.path.join(HERE, "v7", "_v6-reference")), indent=1))
    for k in range(1, 7):
        print(k, "region", region(k), "centred budget", tuple(round(v, 1) for v in centred_budget(k)))
