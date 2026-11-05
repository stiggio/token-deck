"""Calibration images for the N3 panel, own code.

ruler_card(): 320 x 240 as seen. For each of the six key windows (estimated centres from the Nov 2 test 13
photo: x 53/160/267, y 54/161) an x ruler and a y ruler cross at the estimated centre: ticks every 2 px,
longer every 10 px, longest + the absolute coordinate every 20 px. Read a photo: the label nearest each
window edge plus the ticks give that edge's panel coordinate to about +-2 px. Background is a smooth
two-colour gradient (dark, so the white ruler reads), which also makes this a realistic "rich" JPEG.

frame_tile(): 64 x 64 key tile: 2 px magenta border, 2 px white, 2 px black, then an 8 px grey checkerboard
with "64" in the middle. Painted over the ruler it shows whether the firmware scales a 64 px tile to the
window or places it 1:1 with the ruler visible around it.
"""
from PIL import Image, ImageDraw

CX = (53, 160, 267)
CY = (54, 161)
HALF = 52                       # ruler half-length around the estimated centre


DIGITS = {
    "0": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
}


def _crisp_text(img, xy, text, scale, fill, anchor):
    """Draw digits with a 5 x 7 pixel font (no anti-aliasing, no ambiguous glyphs). anchor: 'ms' = middle
    of the text at its bottom edge, 'lm' = left edge at its vertical middle, 'mm' = centred."""
    w = (len(text) * 6 - 1) * scale
    h = 7 * scale
    x, y = xy
    if anchor == "ms":
        x0, y0 = x - w // 2, y - h
    elif anchor == "lm":
        x0, y0 = x, y - h // 2
    else:
        x0, y0 = x - w // 2, y - h // 2
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    for i, ch in enumerate(text):
        rows = DIGITS[ch]
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                if v == "#":
                    px0 = x0 + (i * 6 + c) * scale
                    py0 = y0 + r * scale
                    d.rectangle([px0, py0, px0 + scale - 1, py0 + scale - 1], fill=255)
    return mask, mask.getbbox()


def _overlaps(b, boxes, pad):
    if b is None:
        return False
    for o in boxes:
        if b[0] - pad < o[2] and o[0] < b[2] + pad and b[1] - pad < o[3] and o[1] < b[3] + pad:
            return True
    return False


def ruler_card():
    W, H = 320, 240
    img = Image.new("RGB", (W, H))
    px = img.load()
    a, b = (18, 64, 92), (96, 30, 86)          # deep teal -> deep magenta
    for y in range(H):
        for x in range(W):
            t = (x / (W - 1) * 0.65 + y / (H - 1) * 0.35)
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    d = ImageDraw.Draw(img)
    white, yellow = (255, 255, 255), (255, 236, 120)
    rulers, labels = [], []
    for cy in CY:
        for cx in CX:
            x0, x1 = max(0, cx - HALF), min(W - 1, cx + HALF)
            y0, y1 = max(0, cy - HALF), min(H - 1, cy + HALF)
            # x ruler: baseline at cy, ticks upward
            d.line([(x0, cy), (x1, cy)], fill=white)
            for x in range(x0, x1 + 1):
                if x % 2:
                    continue
                L = 8 if x % 20 == 0 else 5 if x % 10 == 0 else 2
                d.line([(x, cy - L), (x, cy)], fill=white)
            # y ruler: line at cx, ticks to the right
            d.line([(cx, y0), (cx, y1)], fill=yellow)
            for y in range(y0, y1 + 1):
                if y % 2:
                    continue
                L = 8 if y % 20 == 0 else 5 if y % 10 == 0 else 2
                d.line([(cx, y), (cx + L, y)], fill=yellow)
            rulers.append((x0, cy - 9, x1, cy + 1))
            rulers.append((cx - 1, y0, cx + 9, y1))
    # labels: x values above the x rulers (white), y values right of the y rulers (yellow); skip collisions
    for cy in CY:
        for cx in CX:
            for x in range(max(0, cx - HALF), min(W, cx + HALF + 1)):
                if x % 20 == 0:
                    m, bb = _crisp_text(img, (x, cy - 10), str(x), 1, 255, "ms")
                    if bb and not _overlaps(bb, rulers, 0) and not _overlaps(bb, labels, 3):
                        img.paste(white, (0, 0), m); labels.append(bb)
            for y in range(max(0, cy - HALF), min(H, cy + HALF + 1)):
                if y % 20 == 0:
                    m, bb = _crisp_text(img, (cx + 10, y), str(y), 1, 255, "lm")
                    if bb and not _overlaps(bb, rulers, 0) and not _overlaps(bb, labels, 3):
                        img.paste(yellow, (0, 0), m); labels.append(bb)
    return img


def frame_tile():
    t = Image.new("RGB", (64, 64), (0, 0, 0))
    d = ImageDraw.Draw(t)
    for yy in range(6, 58, 8):
        for xx in range(6, 58, 8):
            if ((xx - 6) // 8 + (yy - 6) // 8) % 2 == 0:
                d.rectangle([xx, yy, min(xx + 7, 57), min(yy + 7, 57)], fill=(90, 90, 90))
            else:
                d.rectangle([xx, yy, min(xx + 7, 57), min(yy + 7, 57)], fill=(150, 150, 150))
    d.rectangle([0, 0, 63, 63], outline=(255, 0, 255), width=2)
    d.rectangle([2, 2, 61, 61], outline=(255, 255, 255), width=2)
    d.rectangle([4, 4, 59, 59], outline=(0, 0, 0), width=2)
    m, _ = _crisp_text(t, (32, 32), "64", 2, 255, "mm")
    t.paste((255, 255, 255), (0, 0), m)
    return t
