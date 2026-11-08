"""Token Deck welcome screen (the image burned into the deck's boot slot), own code. v2, Nov 2, 2026.

Gabriel's brief: the tokens pattern on black, the Stigg logo, the slogan "The AI Usage Management
Console" and the URL io.stigg.io/usage. Feedback on v1: content must be centred in what each key shows.

Two constraints from the measured panel (../panel_geometry.py):
1. Every element is centred in its key's WINDOW (what the eye sees through the key).
2. Every element stays inside the key's 64 x 64 TILE rect (where the app's tiles land at runtime), so
   the app covers it completely and only #131512 shows around the app's tiles.
That gives each key a budget for a centred element: width <= 61 / 56 / 48 px (left / middle / right
column), height <= 61 (top row) / 52 (bottom row). The middle column may shift 1 px left (58 px).

Layout:   [tokens]          [Stigg logo]          [tokens, mirrored]
          [The AI / Usage]  [Management / Console] [io.stigg.io / /usage]
Type: Soehne Buch 9.5 px, 13 px leading, white (URL in #C4C7C3); Management (56 px) sets the size.
Tokens: 5 x 5 cells of 10 px, 6 x 6 squares (the After Tokens token size), unlit #242723, lit 60 % lime /
40 % white, seeded, denser toward the logo; the right field is the mirror of the left.

usage: welcome_screen.py   writes welcome-320x240.png, welcome-sent.jpg (as burned, rotated),
                           preview-face-3x.png (boot), preview-runtime-3x.png (app tiles over it)
"""
import io, os, random, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from panel_geometry import TILE, TILE_X, TILE_Y, WINDOWS, tile_origin

W, H = 320, 240
INK = (0x13, 0x15, 0x12)
LIME = (0x92, 0xE7, 0x59)
WHITE = (0xFF, 0xFF, 0xFF)
GREY = (0xC4, 0xC7, 0xC3)
UNLIT = (0x24, 0x27, 0x23)
FONT_CANDIDATES = [
    os.environ.get("SOEHNE_BUCH", ""),
    os.path.join(HERE, "..", "..", "site-fonts", "soehne-buch.woff2"),               # token-deck kit
    os.path.join(HERE, "..", "..", "..", "plans", "token-deck", "assets", "site-fonts", "soehne-buch.woff2"),
    os.path.join(HERE, "..", "..", "..", "box", "_source", "stigg-brand", "plugins", "stigg-design",
                 "skills", "stigg-ds-master", "assets", "fonts", "Soehne-Buch.otf"),
]
FONT = next((f for f in FONT_CANDIDATES if f and os.path.exists(f)), None)
if FONT is None:
    raise SystemExit("Soehne Buch not found; set SOEHNE_BUCH to the font file (woff2 or otf)")
LOGO = os.path.join(HERE, "stigg-logo-20x.png")   # stigg-logo-on-dark.svg rendered by Chrome at 20x
SIZE, LEADING = 9.5, 13


def window_centre(key):
    x0, y0, x1, y1 = WINDOWS[key - 1]
    return (x0 + x1) / 2, (y0 + y1) / 2


def place(key, w, h, dx=0, fit=False):
    """Top-left of a w x h box centred in the key's window (shifted dx). With fit=True, a box that
    would leave the tile rect is moved the minimum needed to stay inside it; the shift is recorded."""
    cx, cy = window_centre(key)
    x, y = round(cx - w / 2 + dx), round(cy - h / 2)
    tx, ty = tile_origin(key)
    if fit:
        nx = min(max(x, tx), tx + TILE - w)
        ny = min(max(y, ty), ty + TILE - h)
        if (nx, ny) != (x, y):
            SHIFTS[key] = (nx - round(cx - w / 2), ny - round(cy - h / 2))
        x, y = nx, ny
    inside = tx <= x and x + w <= tx + TILE and ty <= y and y + h <= ty + TILE
    if not inside:
        raise SystemExit("key %d: %dx%d box at (%d,%d) leaves the tile rect (%d,%d,64,64)" % (key, w, h, x, y, tx, ty))
    return x, y


SHIFTS = {}


def tokens(img, key, seed, toward):
    n, pitch, sq = 5, 10, 6
    size = (n - 1) * pitch + sq
    x0, y0 = place(key, size, size)
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for r in range(n):
        for c in range(n):
            t = c / (n - 1) if toward == "right" else 1 - c / (n - 1)    # 1 next to the logo
            mid = 1 - abs(r - (n - 1) / 2) / ((n - 1) / 2)                # 1 in the middle rows
            p = 0.08 + 0.80 * t ** 1.4 * (0.7 + 0.3 * mid)
            x, y = x0 + c * pitch, y0 + r * pitch
            lit = rng.random() < p
            colour = (LIME if rng.random() < 0.6 else WHITE) if lit else UNLIT
            d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=colour)
    return (x0, y0, size)


def logo(img, key, width=54):
    src = Image.open(LOGO).convert("RGBA")
    src = src.crop(src.getchannel("A").getbbox())
    h = round(width * src.height / src.width)
    x, y = place(key, width, h)
    big = Image.new("RGBA", src.size, INK + (255,))
    big.alpha_composite(src)
    img.paste(big.convert("RGB").resize((width, h), Image.LANCZOS), (x, y))
    return (x, y, width, h)


def two_lines(img, key, lines, colour=WHITE, dx=0):
    """Two centred lines; the block (cap top of line 1 to the descender of line 2) is centred."""
    font = ImageFont.truetype(FONT, SIZE)
    d = ImageDraw.Draw(img)
    asc, desc = font.getmetrics()
    cap = font.getbbox("H")[1]                                   # empty space above the cap height
    widths = [font.getlength(t) for t in lines]
    bw = max(widths)
    top_to_cap = asc - cap
    bh = int(round(top_to_cap + LEADING + desc))                 # cap top of line 1 .. descender of line 2
    bx, by = place(key, int(round(bw)) + 1, bh, dx)
    cx = bx + (int(round(bw)) + 1) / 2
    for i, (t, w) in enumerate(zip(lines, widths)):
        d.text((round(cx - w / 2), by - cap + i * LEADING), t, font=font, fill=colour)
    return widths


def text_block(img, key, lines, size, leading, colour=WHITE, top_extra=0, draw_at=None, align="center"):
    """n centred lines; returns the block size (cap top of line 1 .. descender of the last line)."""
    font = ImageFont.truetype(FONT, size)
    asc, desc = font.getmetrics()
    cap = font.getbbox("H")[1]
    widths = [font.getlength(t) for t in lines]
    bw = int(round(max(widths))) + 1
    bh = int(round(asc - cap + leading * (len(lines) - 1) + desc))
    if draw_at is None:
        return bw, bh, widths
    bx, by = draw_at
    d = ImageDraw.Draw(img)
    for i, (t, w) in enumerate(zip(lines, widths)):
        lx = bx if align == "left" else round(bx + bw / 2 - w / 2)
        d.text((lx, by - cap + i * leading), t, font=font, fill=colour)
    return bw, bh, widths


SOURCE = (50, 58)                  # the explosion starts at the logo (key 1's window centre)
TARGET = (267, 168)                # and flies toward the slogan (key 6's window centre)
PITCH, SQ = 6, 4                   # one lattice for the whole panel; 4 x 4 tokens (the app's token size)


def budget_box(key, inset=1):
    """Largest box centred in the key's window that stays inside its tile rect (panel coords)."""
    cx, cy = window_centre(key)
    tx, ty = tile_origin(key)
    hw = min(cx - tx, tx + TILE - cx) - inset
    hh = min(cy - ty, ty + TILE - cy) - inset
    return cx - hw, cy - hh, cx + hw, cy + hh


def cell_random(i, j, salt):
    return random.Random((i * 7919 + j * 104729 + salt * 1299709) & 0xFFFFFFFF).random()


def explosion(img, box, floor=0.0):
    """Lit tokens on the global lattice inside box: density falls with distance from SOURCE and is
    strongest along the SOURCE -> TARGET direction (the After Tokens burst, thinning as it flies)."""
    import math
    x0, y0, x1, y1 = box
    ux, uy = TARGET[0] - SOURCE[0], TARGET[1] - SOURCE[1]
    ul = math.hypot(ux, uy)
    d = ImageDraw.Draw(img)
    lit = 0
    for j in range(int(y0 // PITCH), int(y1 // PITCH) + 1):
        for i in range(int(x0 // PITCH), int(x1 // PITCH) + 1):
            x, y = i * PITCH + 1, j * PITCH + 1
            if x < x0 or y < y0 or x + SQ > x1 or y + SQ > y1:
                continue
            vx, vy = x + SQ / 2 - SOURCE[0], y + SQ / 2 - SOURCE[1]
            dist = math.hypot(vx, vy)
            cos = (vx * ux + vy * uy) / (dist * ul) if dist else 1
            core = math.exp(-max(0.0, (dist - 60) / 70) ** 1.3)          # 0.9 next to the logo, ~0.1 at 200 px
            p = 0.78 * core * (0.75 + 0.25 * cos)
            p = max(p, floor)
            if cell_random(i, j, 1) < p:
                d.rectangle([x, y, x + SQ - 1, y + SQ - 1], fill=LIME if cell_random(i, j, 2) < 0.6 else WHITE)
                lit += 1
    return lit


def compose_v3():
    img = Image.new("RGB", (W, H), INK)
    report = {}
    logo(img, 1, width=56)
    for key in (2, 4, 5):
        report[key] = "%d tokens" % explosion(img, budget_box(key))
    # key 3: the burst's last tokens over the URL
    uw, uh, uwid = text_block(img, 3, ["io.stigg.io", "/usage"], 10, 13)
    bx0, by0, bx1, by1 = budget_box(3)
    ux = round((bx0 + bx1) / 2 - uw / 2)
    uy = round(by1 - uh - 6)                                       # URL in the lower part of the key
    text_block(img, 3, ["io.stigg.io", "/usage"], 10, 13, colour=WHITE, draw_at=(ux, uy))
    report[3] = "%d tokens + URL %s" % (explosion(img, (bx0, by0, bx1, uy - 6), floor=0.16), [round(w, 1) for w in uwid])
    # key 6: the slogan
    sw, sh, swid = text_block(img, 6, ["The AI", "Usage", "Management", "Console"], 9, 12)
    sx, sy = place(6, sw, sh, fit=True)
    text_block(img, 6, ["The AI", "Usage", "Management", "Console"], 9, 12, draw_at=(sx, sy))
    report[6] = "slogan %dx%d %s" % (sw, sh, [round(w, 1) for w in swid])
    return img, report


INSET = 9                          # v4: logo, slogan and URL all start 9 px in from their window's left edge


def flush_left(key, w, h):
    """x = window left + INSET, y = centred in the window; both checked against the tile rect."""
    x0w = WINDOWS[key - 1][0]
    cx, cy = window_centre(key)
    x, y = x0w + INSET, round(cy - h / 2)
    tx, ty = tile_origin(key)
    if not (tx <= x and x + w <= tx + TILE and ty <= y and y + h <= ty + TILE):
        raise SystemExit("key %d: flush-left %dx%d box at (%d,%d) leaves the tile rect" % (key, w, h, x, y))
    return x, y


def compose_v4():
    global TARGET
    TARGET = window_centre(6)                                     # the burst flies toward the URL
    img = Image.new("RGB", (W, H), INK)
    report = {}
    src = Image.open(LOGO).convert("RGBA"); src = src.crop(src.getchannel("A").getbbox())
    lw = 56; lh = round(lw * src.height / src.width)
    lx, ly = flush_left(1, lw, lh)
    big = Image.new("RGBA", src.size, INK + (255,)); big.alpha_composite(src)
    img.paste(big.convert("RGB").resize((lw, lh), Image.LANCZOS), (lx, ly))
    report[1] = "logo %dx%d at x=%d" % (lw, lh, lx)
    for key in (2, 4, 5):
        report[key] = "%d tokens" % explosion(img, budget_box(key))
    slogan = ["The AI", "Usage", "Management", "Console"]
    sw, sh, swid = text_block(img, 3, slogan, 9, 12)
    sx, sy = flush_left(3, sw, sh)
    text_block(img, 3, slogan, 9, 12, draw_at=(sx, sy), align="left")
    report[3] = "slogan %dx%d at x=%d %s" % (sw, sh, sx, [round(w, 1) for w in swid])
    url = ["io.stigg.io", "/usage"]
    uw, uh, uwid = text_block(img, 6, url, 10, 13)
    tok_h, gap = 2 * PITCH + SQ, 7                                # three lattice rows of trailing tokens
    bx, by = flush_left(6, uw, tok_h + gap + uh)
    tx, ty = tile_origin(6)
    lit = explosion(img, (bx - 1, by - 1, tx + TILE - 2, by + tok_h + 1), floor=0.2)
    text_block(img, 6, url, 10, 13, draw_at=(bx, by + tok_h + gap), align="left")
    report[6] = "%d tokens + URL at x=%d %s" % (lit, bx, [round(w, 1) for w in uwid])
    return img, report


def compose():
    img = Image.new("RGB", (W, H), INK)
    x0, y0, size = tokens(img, 1, 21, "right")
    tx, ty = place(3, size, size)
    img.paste(img.crop((x0, y0, x0 + size, y0 + size)).transpose(Image.FLIP_LEFT_RIGHT), (tx, ty))
    logo(img, 2)
    widths = {
        4: two_lines(img, 4, ["The AI", "Usage"]),
        5: two_lines(img, 5, ["Management", "Console"], dx=-1),
        6: two_lines(img, 6, ["io.stigg.io", "/usage"], colour=GREY),
    }
    return img, widths


def jpeg_as_burned(img, quality=92):
    buf = io.BytesIO()
    img.rotate(-90, expand=True).save(buf, "JPEG", quality=quality, subsampling=2, optimize=False, progressive=False)
    return buf.getvalue()


def stray_pixels(seen, tol=24):
    """Pixels outside every tile rect that are not #131512 (JPEG ringing tolerated up to tol)."""
    px = seen.load()
    rects = [(tile_origin(k), k) for k in range(1, 7)]
    bad = 0
    for y in range(H):
        for x in range(W):
            if any(tx <= x < tx + TILE and ty <= y < ty + TILE for (tx, ty), _ in rects):
                continue
            if max(abs(a - b) for a, b in zip(px[x, y], INK)) > tol:
                bad += 1
    return bad


def face(img, scale=3, runtime=False):
    pad = 12
    out = Image.new("RGB", ((W + 2 * pad) * scale, (H + 2 * pad) * scale), (8, 8, 8))
    big = img.resize((W * scale, H * scale), Image.NEAREST)
    if runtime:                                      # the app's tiles drawn over the burned image
        d = ImageDraw.Draw(big)
        for k in range(1, 7):
            tx, ty = tile_origin(k)
            d.rectangle([tx * scale, ty * scale, (tx + TILE) * scale - 1, (ty + TILE) * scale - 1], fill=(60, 62, 58))
    for (x0, y0, x1, y1) in WINDOWS:
        out.paste(big.crop((x0 * scale, y0 * scale, x1 * scale, y1 * scale)), ((x0 + pad) * scale, (y0 + pad) * scale))
    return out


if __name__ == "__main__":
    layout = sys.argv[sys.argv.index("--layout") + 1] if "--layout" in sys.argv else "v4"
    img, widths = {"v4": compose_v4, "v3": compose_v3, "v2": compose}[layout]()
    img.save(os.path.join(HERE, "welcome-320x240.png"))
    data = jpeg_as_burned(img)
    open(os.path.join(HERE, "welcome-sent.jpg"), "wb").write(data)
    seen = Image.open(io.BytesIO(data)).rotate(90, expand=True).convert("RGB")
    face(seen).save(os.path.join(HERE, "preview-face-3x.png"))
    face(seen, runtime=True).save(os.path.join(HERE, "preview-runtime-3x.png"))
    print("font:", os.path.relpath(FONT, HERE))
    print("layout:", layout, widths)
    print("shifts off the window centre to stay inside the tile (dx, dy):", SHIFTS or "none")
    print("welcome JPEG as burned: %d bytes" % len(data))
    print("non-#131512 pixels outside the tile rects (as burned):", stray_pixels(seen))
