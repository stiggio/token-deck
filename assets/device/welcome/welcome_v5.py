"""Token Deck welcome screen v5 (the image burned into the deck's boot slot), own code.

Brief (Gabriel, Nov 2): the tokens pattern on black, the Stigg logo, the slogan "The AI Usage Management
Console", the URL io.stigg.io/usage; logo top-left, slogan flush left, URL bottom-right, mostly the token
explosion; tokens a little smaller and more exploded; "think as an expert and make it perfect".

What makes v5 different from v1-v4:
- The explosion is the approved one: box/tools/explosion_svg.py (pixelmark's burst generalised to a wall,
  the box's back wall uses it), run at the panel's own pixels (pitch 5 px, square 4 px = ratio 0.8, one
  strict grid, one token per cell, lime). Each key's window shows a slice of ONE explosion.
- One type size (Soehne Buch 9.5 px, 12 px leading, white) and one left margin: logo, slogan and URL ink
  all start 7 px in from their window's left edge (optical: aligned on the glyph ink, not the advance box).
- Everything stays inside the six tile rects (so the app's tiles cover it at runtime) and the generator
  proves it: 0 non-#131512 pixels outside the tile rects in the JPEG as burned.

usage: welcome_v5.py [--explosion-args "..."] [--out DIR]
"""
import io, os, re, shlex, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from panel_geometry import TILE, WINDOWS, tile_origin
import welcome_screen as base                      # fonts, logo, preview and stray-pixel helpers

W, H = 320, 240
INK, WHITE = base.INK, base.WHITE
INSET = 7                                          # shared left margin inside each window (ink edge)
SIZE, LEADING = 9.5, 12
LOGO_W = 60

# the explosion: approved generator, panel pixels. safe=1 puts the grid at x, y = 3 + 5k (whole pixels).
EXPLOSION = ("--panel 320x240 --safe 1 --pitch 5 --ratio 0.8 --model field --source core --air 0 "
             "--src-w 20 --src-h 0.11 --src-y 0.72 --air-left 4 "
             "--erode 0.6 --u0 0.45 --erode-pow 1.5 --reach 1.0 --spread0 0.08 --spread1 0.34 --fanpow 0.8 "
             "--rise 0.45 --lam 0.48 --d0 0.55 --soft 0.4 --gap0 0 --gap1 2.2 --seed 7")


def window_centre(key):
    x0, y0, x1, y1 = WINDOWS[key - 1]
    return (x0 + x1) / 2, (y0 + y1) / 2


def budget_box(key, inset=1):
    cx, cy = window_centre(key)
    tx, ty = tile_origin(key)
    hw = min(cx - tx, tx + TILE - cx) - inset
    hh = min(cy - ty, ty + TILE - cy) - inset
    return (cx - hw, cy - hh, cx + hw, cy + hh)


def inside_tile(key, box):
    tx, ty = tile_origin(key)
    x0, y0, x1, y1 = box
    return tx <= x0 and ty <= y0 and x1 <= tx + TILE and y1 <= ty + TILE


def explosion_tokens(args):
    out = os.path.join(HERE, "_explosion.svg")
    subprocess.run([sys.executable, os.path.join(HERE, "explosion_svg.py"), out] + shlex.split(args), check=True)
    svg = open(out).read()
    toks = [(float(x), float(y), float(s), c) for x, y, s, c in
            re.findall(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="[\d.]+" fill="(#[0-9a-f]+)"', svg)]
    return toks


def ink_text(img, x_ink, y_cap, lines, colour=WHITE):
    """Flush-left lines whose glyph INK starts at x_ink (optical alignment); y_cap = cap top of line 1."""
    font = ImageFont.truetype(base.FONT, SIZE)
    d = ImageDraw.Draw(img)
    cap_off = font.getbbox("H")[1]
    boxes = []
    for i, t in enumerate(lines):
        bx0 = font.getbbox(t)[0]                   # left side bearing of the first glyph
        x = x_ink - bx0
        y = y_cap - cap_off + i * LEADING
        d.text((x, y), t, font=font, fill=colour)
        bb = d.textbbox((x, y), t, font=font)
        boxes.append(bb)
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def text_size(lines):
    """Width of the widest line's ink, and the OPTICAL height: cap top of line 1 to the baseline of the
    last line (descenders hang below, as a typesetter centres a block)."""
    font = ImageFont.truetype(base.FONT, SIZE)
    asc, desc = font.getmetrics()
    cap_off = font.getbbox("H")[1]
    w = max(font.getbbox(t)[2] - font.getbbox(t)[0] for t in lines)
    h = (asc - cap_off) + LEADING * (len(lines) - 1)
    return w, h


def compose(explosion_args=EXPLOSION):
    img = Image.new("RGB", (W, H), INK)
    report, clear = {}, {}
    # key 1: logo, ink at the inset, centred vertically in the window
    src = Image.open(base.LOGO).convert("RGBA"); src = src.crop(src.getchannel("A").getbbox())
    lh = round(LOGO_W * src.height / src.width)
    big = Image.new("RGBA", src.size, INK + (255,)); big.alpha_composite(src)
    lx = WINDOWS[0][0] + INSET
    ly = round(window_centre(1)[1] - lh / 2)
    assert inside_tile(1, (lx, ly, lx + LOGO_W, ly + lh)), "logo leaves tile 1"
    img.paste(big.convert("RGB").resize((LOGO_W, lh), Image.LANCZOS), (lx, ly))
    report[1] = "logo %dx%d at (%d,%d)" % (LOGO_W, lh, lx, ly)
    # key 3: slogan, flush left at the inset, block centred vertically
    slogan = ["The AI", "Usage", "Management", "Console"]
    sw, sh = text_size(slogan)
    sx, sy = WINDOWS[2][0] + INSET, round(window_centre(3)[1] - sh / 2)
    bb = ink_text(img, sx, sy, slogan)
    assert inside_tile(3, bb), "slogan leaves tile 3: %s" % (bb,)
    report[3] = "slogan ink %s" % (bb,)
    # key 6: URL, flush left at the inset, centred vertically; keep a clear zone around it for the dust
    url = ["io.stigg.io", "/usage"]
    uw, uh = text_size(url)
    ux, uy = WINDOWS[5][0] + INSET, round(window_centre(6)[1] - uh / 2)
    bb = ink_text(img, ux, uy, url)
    assert inside_tile(6, bb), "URL leaves tile 6: %s" % (bb,)
    clear[6] = (bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)
    report[6] = "URL ink %s" % (bb,)
    # the explosion, clipped to the explosion keys' window-centred boxes (2, 4, 5) and key 6 outside the URL
    toks = explosion_tokens(explosion_args)
    d = ImageDraw.Draw(img)
    shown = {2: 0, 4: 0, 5: 0, 6: 0}
    regions = {}
    for k in (2, 4, 5, 6):
        tx, ty = tile_origin(k)
        regions[k] = (tx + 2, ty + 2, tx + TILE - 2, ty + TILE - 2)
    for (x, y, s, c) in toks:
        x, y, s = round(x), round(y), round(s)
        for k, (bx0, by0, bx1, by1) in regions.items():
            if bx0 <= x and by0 <= y and x + s <= bx1 and y + s <= by1:
                if k in clear:
                    cx0, cy0, cx1, cy1 = clear[k]
                    if x < cx1 and cx0 < x + s and y < cy1 and cy0 < y + s:
                        break
                d.rectangle([x, y, x + s - 1, y + s - 1], fill=c)
                shown[k] += 1
                break
    report["tokens"] = "%d generated, shown per key %s" % (len(toks), shown)
    return img, toks, report


def full_explosion_preview(toks, scale=2):
    """The whole generated explosion with the six windows outlined: what each key is a slice of."""
    im = Image.new("RGB", (W * scale, H * scale), INK)
    d = ImageDraw.Draw(im)
    for (x, y, s, c) in toks:
        d.rectangle([round(x) * scale, round(y) * scale, (round(x) + round(s)) * scale - 1, (round(y) + round(s)) * scale - 1], fill=c)
    for (x0, y0, x1, y1) in WINDOWS:
        d.rectangle([x0 * scale, y0 * scale, x1 * scale - 1, y1 * scale - 1], outline=(120, 120, 120))
    return im


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--explosion-args") + 1] if "--explosion-args" in sys.argv else EXPLOSION
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else HERE
    img, toks, report = compose(args)
    img.save(os.path.join(out, "welcome-320x240.png"))
    data = base.jpeg_as_burned(img)
    open(os.path.join(out, "welcome-sent.jpg"), "wb").write(data)
    seen = Image.open(io.BytesIO(data)).rotate(90, expand=True).convert("RGB")
    base.face(seen).save(os.path.join(out, "preview-face-3x.png"))
    base.face(seen, runtime=True).save(os.path.join(out, "preview-runtime-3x.png"))
    full_explosion_preview(toks).save(os.path.join(out, "preview-explosion-2x.png"))
    for k, v in report.items():
        print(k, v)
    print("welcome JPEG as burned: %d bytes" % len(data))
    print("non-#131512 pixels outside the tile rects (as burned):", base.stray_pixels(seen))
