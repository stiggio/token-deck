"""Token Deck welcome screen v6 (the image burned into the deck's boot slot), own code.

v6 = v5 (Gabriel's layout: logo top-left, slogan top-right flush left, URL bottom-right, the approved
After Tokens explosion rising from a source block in key 4 toward the slogan) plus every fix from a
four-critic expert review (typography, composition, brand, device), each enforced by a check:

Type   Soehne Buch 9.5 px / 12 px leading, white, pen at the shared 7 px window inset (x = 20 / 235).
       Every glyph sits at its exact shaped x (sub-pixel), composited with gamma 1.5 so strokes keep their
       light without reading bold. Periods are single crisp #FFFFFF pixels at Söhne's own spacing (no
       respacing); the '/u' kern is dropped. Slogan in three lines, 'The AI Usage' / 'Management' / 'Console' (lines 1
       and 2 share one 57 px measure); its middle baseline sits on the 'stigg' wordmark baseline in key 1.
Logo   Official stigg-logo-on-dark, exact aspect (padded, not stretched), 60 px, LANCZOS clamped so no
       pixel is darker than #131512.
Tokens One explosion from the approved tool (box/tools/explosion_svg.py) on a 6 px lattice with 4 px
       squares at even panel coordinates (x = 2 + 6i, y = 4 + 6j), so every token covers whole 4:2:0
       chroma blocks and stays brand lime after JPEG; column x = 20 is the logo's edge. A solid source
       block at x = 20 in key 4 erodes on its right; the fan rises through key 5 and key 2 toward the
       slogan; a few tokens arrive around the URL. The seed is chosen by layout checks (below).
Rules  All content inside the six tile rects (the app's tiles cover it at runtime); tokens at least 6 px
       from every window edge (keycap rim glare); per-line clear zones around the URL; the JPEG as burned
       keeps luma within 4 levels of #131512 outside the tiles (no halo around the app's tiles).

usage: welcome_v6.py [--seed N]       render the final image and previews (default seed 259)
       welcome_v6.py --search 400        list the seeds that pass every layout check
"""
import io, math, os, re, runpy, subprocess, sys, tempfile
from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from panel_geometry import TILE, WINDOWS, tile_origin
import welcome_screen as base

W, H = 320, 240
INK = (0x13, 0x15, 0x12)
LIME = (0x92, 0xE7, 0x59)
WHITE = (0xFF, 0xFF, 0xFF)
SIZE, LEADING, GAMMA = 9.5, 12, 1.5
PEN_L, PEN_R = 20, 235                          # 7 px in from the left windows (13) and right windows (228)
LOGO_W = 60
RIM = 6                                         # tokens keep this far from every window edge
QUALITY = 97                                    # q97: luma within 3.3 levels of #131512 outside the tiles

EXPLOSION = ("--panel 320x240 --safe 2 --pitch 6 --ratio 0.666667 --model field --source band --air 0 "
             "--src-w 24 --src-h 0.16 --src-y 0.7105 --air-left 3 --erode 0.5 --u0 0.55 --erode-pow 1.5 "
             "--reach 1.0 --fanpow 0.8 --soft 0.4 --gap0 0 --gap1 1.6 --spread0 0.09 --spread1 0.40 "
             "--d0 0.45 --lam 0.8 --rise 0.50")
SEED = 259                                      # chosen by eye among the seeds 1-400 that pass every layout check


# ---------------------------------------------------------------- type
def font():
    return ImageFont.truetype(base.FONT, SIZE)


def kern(f, a, b):
    return f.getlength(a + b) - f.getlength(a) - f.getlength(b)


def layout_line(f, text, pen, no_kern=(("/", "u"),), period_air=0.0):
    """Exact pen x of every glyph: shaped advances with pair kerning, minus dropped kerns, plus air
    around periods."""
    xs, extra = [], 0.0
    for j, ch in enumerate(text):
        x = pen + f.getlength(text[:j + 1]) - f.getlength(ch) + extra
        if j and (text[j - 1], ch) in no_kern:
            extra -= kern(f, text[j - 1], ch)
            x -= kern(f, text[j - 1], ch)
        if ch == ".":
            x += period_air
            extra += 2 * period_air
        xs.append(x)
    return xs


def text_mask(blocks):
    """blocks: [(pen_x, cap_top_y, [lines])] -> L coverage mask for the whole panel (max of glyphs),
    plus the list of period pixels, plus each line's ink box."""
    f = font()
    asc, _ = f.getmetrics()
    cap_off = f.getbbox("H")[1]
    cov = Image.new("L", (W, H), 0)
    dots, boxes = [], []
    for pen, cap_top, lines in blocks:
        for i, t in enumerate(lines):
            top = cap_top - cap_off + i * LEADING          # PIL draws from the ascender line
            base_y = top + asc
            xs = layout_line(f, t, pen)
            lb = [W, H, 0, 0]
            for ch, x in zip(t, xs):
                if ch == " ":
                    continue
                if ch == ".":
                    px, py = round(x + 0.51), base_y - 1
                    dots.append((px, py))
                    lb = [min(lb[0], px), min(lb[1], py), max(lb[2], px + 1), max(lb[3], py + 1)]
                    continue
                fx = math.floor(x); phi = x - fx
                g = Image.new("L", (W, H), 0)
                ImageDraw.Draw(g).text((fx, top), ch, font=f, fill=255)
                if phi > 0.01:
                    g = Image.blend(g, ImageChops.offset(g, 1, 0), phi)
                cov = ImageChops.lighter(cov, g)
                bb = g.getbbox()
                if bb:
                    lb = [min(lb[0], bb[0]), min(lb[1], bb[1]), max(lb[2], bb[2]), max(lb[3], bb[3])]
            boxes.append(tuple(lb))
    for (px, py) in dots:
        cov.putpixel((px, py), 255)
    return cov, boxes


def composite_text(img, cov, fg=WHITE):
    """Gamma-correct blend of fg over the background through the coverage mask."""
    luts = []
    for c in range(3):
        b = INK[c] / 255.0
        f = fg[c] / 255.0
        luts.append([round(255 * ((m / 255.0) * f ** GAMMA + (1 - m / 255.0) * b ** GAMMA) ** (1 / GAMMA)) for m in range(256)])
    layer = Image.merge("RGB", [cov.point(luts[c]) for c in range(3)])
    img.paste(layer, (0, 0), cov.point(lambda v: 255 if v else 0))


# ---------------------------------------------------------------- logo
def logo_image():
    src = Image.open(base.LOGO).convert("RGBA")
    src = src.crop(src.getchannel("A").getbbox())                 # 1845 x 512 at 20x
    target_h = 17
    pad_h = round(target_h * src.width / LOGO_W)                   # 523: the exact-aspect canvas height
    canvas = Image.new("RGBA", (src.width, pad_h), INK + (255,))
    top = (pad_h - src.height) // 2
    canvas.alpha_composite(src, (0, top))
    small = canvas.convert("RGB").resize((LOGO_W, target_h), Image.LANCZOS)
    small = ImageChops.lighter(small, Image.new("RGB", small.size, INK))     # no undershoot below the canvas
    baseline_in_src = 19.3 * 20 + top                              # the wordmark baseline (viewBox y 19.3) at 20x
    return small, baseline_in_src * target_h / pad_h


# ---------------------------------------------------------------- explosion
def explosion_tokens(args, seed):
    out = os.path.join(tempfile.gettempdir(), "tokendeck_explosion_%d.svg" % os.getpid())
    argv = sys.argv
    try:
        sys.argv = ["explosion_svg.py", out] + args.split() + ["--seed", str(seed)]
        import contextlib
        with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
            runpy.run_path(os.path.join(HERE, "explosion_svg.py"), run_name="__main__")
    finally:
        sys.argv = argv
    svg = open(out).read()
    return [(round(float(x)), round(float(y)), round(float(s)), c) for x, y, s, c in
            re.findall(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="[\d.]+" fill="(#[0-9a-f]+)"', svg)]


def region(key):
    """Tile rect intersected with the window shrunk by RIM (keycap rim): where tokens may sit."""
    tx, ty = tile_origin(key)
    wx0, wy0, wx1, wy1 = WINDOWS[key - 1]
    return (max(tx, wx0 + RIM), max(ty, wy0 + RIM), min(tx + TILE, wx1 - RIM), min(ty + TILE, wy1 - RIM))


def place_tokens(toks, url_clear, min_x6):
    shown = {2: [], 4: [], 5: [], 6: []}
    regs = {k: region(k) for k in shown}
    for (x, y, s, c) in toks:
        for k, (x0, y0, x1, y1) in regs.items():
            if x0 <= x and y0 <= y and x + s <= x1 and y + s <= y1:
                if k == 6:
                    if x < min_x6 or any(x < cx1 and cx0 < x + s and y < cy1 and cy0 < y + s for (cx0, cy0, cx1, cy1) in url_clear):
                        break
                shown[k].append((x, y, s, c))
                break
    return shown


# ---------------------------------------------------------------- layout checks (from the review)
def checks(shown, url_boxes, src_x0=20, pitch=6):
    fails = []
    n = {k: len(v) for k, v in shown.items()}
    if not (n[4] > n[5] > n[2] >= 8): fails.append("counts %s" % n)
    if n[2] > 28: fails.append("key 2 too busy")
    if not (3 <= n[6] <= 8): fails.append("key 6 has %d" % n[6])
    k2 = shown[2]
    if len(k2) >= 3:
        mx = sum(t[0] for t in k2) / len(k2); my = sum(t[1] for t in k2) / len(k2)
        sxx = sum((t[0] - mx) ** 2 for t in k2) or 1
        slope = sum((t[0] - mx) * (t[1] - my) for t in k2) / sxx
        if slope > -0.3: fails.append("key 2 slope %.2f" % slope)
        if sum(1 for t in k2 if t[0] >= 155 and t[1] <= 60) < 2: fails.append("key 2 upper right empty")
    for k in (2, 5, 6):
        cells = {(t[0], t[1]) for t in shown[k]}
        for axis in (0, 1):
            lines = {}
            for c in cells:
                lines.setdefault(c[axis], []).append(c[1 - axis])
            for v, others in lines.items():
                if len(others) >= 3:
                    lo, hi = min(others), max(others)
                    neighbours = [c for c in cells if abs(c[axis] - v) == pitch and lo <= c[1 - axis] <= hi]
                    if not neighbours: fails.append("key %d isolated line" % k)
    for k in (2, 4, 5):
        x0, y0, x1, y1 = region(k)
        cells = {(t[0], t[1]) for t in shown[k]}
        edges = []
        if k == 5: edges.append(("row", min((c[1] for c in cells), default=0)))
        if k == 2: edges.append(("row", max((c[1] for c in cells), default=0)))
        for kind, v in edges:
            row = sorted(c[0] for c in cells if c[1] == v)
            run = best = 1
            for a, b in zip(row, row[1:]):
                run = run + 1 if b - a == pitch else 1; best = max(best, run)
            if len(row) >= 3 and best >= 3: fails.append("key %d edge run" % k)
    k6 = shown[6]
    if k6:
        top_url = min(b[1] for b in url_boxes)
        if not any(t[1] + t[2] <= top_url for t in k6): fails.append("nothing above the URL")
        right = [t for t in k6 if (t[0] >= url_boxes[1][2] + 3 and url_boxes[1][1] - 4 <= t[1] <= url_boxes[1][3]) or t[0] >= url_boxes[0][2] + 3]
        if not right: fails.append("nothing beside the URL")
        cells = [(t[0], t[1]) for t in k6]
        pair = any((a != b) and ((a[0] == b[0] and abs(a[1] - b[1]) <= 2 * pitch) or (a[1] == b[1] and abs(a[0] - b[0]) <= 2 * pitch)) for a in cells for b in cells)
        if not pair: fails.append("key 6 lattice invisible")
    k4 = {(t[0], t[1]) for t in shown[4]}
    rows4 = sorted({c[1] for c in k4 if c[0] == src_x0})
    if len(rows4) < 4: fails.append("source block too small")
    for y in rows4[1:-1]:
        if (src_x0 + pitch, y) not in k4: fails.append("source second column broken"); break
    k5 = {(t[0], t[1]) for t in shown[5]}
    for (x, y) in k5:
        clump = sum(1 for dx in (0, pitch, 2 * pitch) for dy in (0, pitch, 2 * pitch) if (x + dx, y + dy) in k5)
        if clump > 5: fails.append("key 5 clump"); break
    return fails, n


# ---------------------------------------------------------------- compose
def compose(seed, args=EXPLOSION, verbose=False):
    img = Image.new("RGB", (W, H), INK)
    logo, base_off = logo_image()
    lx = PEN_L
    ly = round((WINDOWS[0][1] + WINDOWS[0][3]) / 2 - logo.height / 2)
    img.paste(logo, (lx, ly))
    wordmark_base = ly + base_off                                  # about 62.6
    f = font(); cap_h = f.getbbox("H")[3] - f.getbbox("H")[1]
    # slogan: 'Management' (line 2) baseline on the wordmark baseline, if that keeps the block centred
    slogan = ["The AI Usage", "Management", "Console"]
    cap_top_centred = round((WINDOWS[2][1] + WINDOWS[2][3]) / 2 - (cap_h + 2 * LEADING) / 2)
    cap_top_aligned = round(wordmark_base - LEADING - cap_h)
    s_cap = cap_top_aligned if abs(cap_top_aligned - cap_top_centred) <= 1 else cap_top_centred
    url = ["io.stigg.io", "/usage"]
    u_cap = round((WINDOWS[5][1] + WINDOWS[5][3]) / 2 - (cap_h + LEADING) / 2)
    cov, boxes = text_mask([(PEN_R, s_cap, slogan), (PEN_R, u_cap, url)])
    composite_text(img, cov)
    url_boxes = boxes[3:5]
    url_clear = [(b[0] - 3, b[1] - 3, b[2] + 3, b[3] + 3) for b in url_boxes]
    toks = explosion_tokens(args, seed)
    shown = place_tokens(toks, url_clear, min_x6=PEN_R + 7)
    d = ImageDraw.Draw(img)
    for k, ts in shown.items():
        for (x, y, s, c) in ts:
            d.rectangle([x, y, x + s - 1, y + s - 1], fill=c)
    fails, n = checks(shown, url_boxes)
    info = {"seed": seed, "logo": (lx, ly, logo.size), "wordmark_baseline": round(wordmark_base, 1),
            "slogan_cap_top": s_cap, "slogan_boxes": boxes[:3], "url_boxes": url_boxes, "tokens": n,
            "lime_pct": round(100 * sum(len(v) for v in shown.values()) * 16 / sum((w[2] - w[0]) * (w[3] - w[1]) for w in WINDOWS), 2)}
    return img, fails, info, toks


# ---------------------------------------------------------------- checks on the burned JPEG
def jpeg(img, quality=QUALITY):
    buf = io.BytesIO()
    img.rotate(-90, expand=True).save(buf, "JPEG", quality=quality, subsampling=2, optimize=False, progressive=False)
    return buf.getvalue()


def decode_box(data):
    """Decode like an MCU (no fancy upsampling) with djpeg -nosmooth; falls back to PIL."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as t:
            t.write(data)
        ppm = subprocess.run(["djpeg", "-nosmooth", "-ppm", t.name], capture_output=True, check=True).stdout
        os.unlink(t.name)
        return Image.open(io.BytesIO(ppm)).rotate(90, expand=True).convert("RGB")
    except Exception:
        return Image.open(io.BytesIO(data)).rotate(90, expand=True).convert("RGB")


def halo(seen):
    """Luma deviation from #131512 for window pixels outside the tile rects: (count > 4, max)."""
    y_ink = 0.299 * INK[0] + 0.587 * INK[1] + 0.114 * INK[2]
    px = seen.load(); cnt = 0; worst = 0.0
    tiles = [tile_origin(k) for k in range(1, 7)]
    for (x0, y0, x1, y1) in WINDOWS:
        for y in range(y0, y1):
            for x in range(x0, x1):
                if any(tx <= x < tx + TILE and ty <= y < ty + TILE for tx, ty in tiles):
                    continue
                r, g, b = px[x, y]
                dy = abs(0.299 * r + 0.587 * g + 0.114 * b - y_ink)
                worst = max(worst, dy)
                if dy > 4: cnt += 1
    return cnt, round(worst, 1)


def source_clean(img):
    """Exact: no pixel outside the tiles differs from #131512; no pixel anywhere darker than it."""
    px = img.load(); outside = darker = 0
    tiles = [tile_origin(k) for k in range(1, 7)]
    for y in range(H):
        for x in range(W):
            p = px[x, y]
            if all(p[c] < INK[c] for c in range(3)): darker += 1
            if p != INK and not any(tx <= x < tx + TILE and ty <= y < ty + TILE for tx, ty in tiles): outside += 1
    return outside, darker


def previews(img, data, out):
    seen_pil = Image.open(io.BytesIO(data)).rotate(90, expand=True).convert("RGB")
    seen_box = decode_box(data)
    base.face(seen_pil).save(os.path.join(out, "preview-face-3x.png"))
    base.face(seen_box).save(os.path.join(out, "preview-face-box-3x.png"))
    base.face(seen_pil, scale=1).save(os.path.join(out, "preview-face-1x.png"))
    base.face(seen_box, runtime=True).save(os.path.join(out, "preview-runtime-3x.png"))
    amp = Image.eval(ImageChops.difference(seen_box, Image.new("RGB", (W, H), INK)), lambda v: min(255, v * 6))
    d = ImageDraw.Draw(amp)
    for k in range(1, 7):
        tx, ty = tile_origin(k); d.rectangle([tx, ty, tx + TILE - 1, ty + TILE - 1], fill=(40, 40, 40))
    base.face(amp).save(os.path.join(out, "preview-halo-x6-3x.png"))
    return seen_pil, seen_box


if __name__ == "__main__":
    if "--search" in sys.argv:
        N = int(sys.argv[sys.argv.index("--search") + 1])
        ok = []
        for s in range(1, N + 1):
            _, fails, info, _ = compose(s)
            if not fails:
                ok.append((s, info["tokens"], info["lime_pct"]))
        print("seeds passing every layout check:", len(ok))
        for s, n, lime in ok[:40]:
            print("  seed %d tokens %s lime %.1f%%" % (s, n, lime))
        sys.exit(0)
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else SEED
    img, fails, info, toks = compose(seed)
    for k, v in info.items():
        print(k, v)
    print("layout checks:", "pass" if not fails else fails)
    outside, darker = source_clean(img)
    print("source: %d pixels outside the tiles differ from #131512; %d pixels darker than #131512" % (outside, darker))
    assert not fails and outside == 0 and darker == 0, "a hard rule failed"
    data = jpeg(img)
    cnt, worst = halo(decode_box(data))
    print("JPEG q%d: %d bytes; window pixels outside the tiles more than 4 luma levels off #131512: %d (worst %.1f)" % (QUALITY, len(data), cnt, worst))
    assert cnt == 0, "halo outside the tiles"
    out = HERE
    img.save(os.path.join(out, "welcome-320x240.png"))
    open(os.path.join(out, "welcome-sent.jpg"), "wb").write(data)
    previews(img, data, out)
    print("wrote welcome-320x240.png, welcome-sent.jpg and the previews")
