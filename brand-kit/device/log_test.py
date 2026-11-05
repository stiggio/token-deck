"""Diagnostic for the LOG (boot/background image) slot, own code.

usage: log_test.py lime|white|black|ink|field|card [options]
  lime/white/black/ink  solid colour (lime is 1,830 bytes at q90)
  field                 the token-field placeholder (11,139 bytes at q90)
  card                  a rich test card: hue gradient + 24 numbered cells (6 x 4), also usable for the
                        window-geometry calibration (which numbers show in which key window)
  ruler                 calibration rulers crossing at each window's estimated centre (calib_images.py)
  Rhythm: wake + brightness, LOG, wait up to N s for the device's write report (stop as soon as it comes),
  STP, 1 s quiet, hold with the CONNECT heartbeat, close with no goodbye frame.
  --tiles               first paint six solid tiles (keys 1,3,5 lime; 2,4,6 white) + STP (test 3 did this)
  --wait-before-stp S   max seconds to wait for the write report before STP (default 3)
  --after-stp S         quiet seconds after STP (default 1)
  --hold S              seconds to keep the handle open afterwards, heartbeat every 10 s (default 10)
  --brightness N        LIG percent (default 100)
  --landscape           send the JPEG as 320x240 instead of the SDK's rotated 240x320
  --quality Q           JPEG quality (default 90; the vendor C++ SDK uses 85)
  --fit-bytes N         use the highest JPEG quality whose file is at most N bytes (overrides --quality)
  --grain-bytes N       lime with film grain tuned to about N bytes (a valid JPEG, no padding)
  --tail-pad N          append zero bytes after EOI so the stream is exactly N bytes
  --chunk-gap MS        pause between the 1024-byte chunks (default 0, like libtransport)
  --com-pad N           insert a JPEG COM segment after SOI so the (still valid) file is N bytes
  --frame420 K          after the LOG, paint the 64 x 64 frame tile on key K (q100, 4:2:0) + STP
  --frame444 K          after the LOG, paint the frame tile on key K (q100, 4:4:4) + STP
  --dc                  send CLE DC before closing (vendor: "disconnects and clears all display")
Working rule from Nov 2: after a failed write, power-cycle the deck before the next attempt; the firmware
appears to ignore further image writes in the same power cycle, so later results there mean nothing.
"""
import colorsys, io, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
from burn_logo import Deck, token_field, LIME, WHITE, INK, OUT
from calib_images import ruler_card, frame_tile

COLOURS = {"lime": LIME, "white": WHITE, "black": (0, 0, 0), "ink": INK}


def arg(name, default):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def encode(im, landscape=False, quality=90):
    im = im.convert("RGB")
    if im.size != (320, 240):
        im = im.resize((320, 240), Image.LANCZOS)
    if not landscape:
        im = im.rotate(-90, expand=True)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, subsampling=2, optimize=False, progressive=False)
    return buf.getvalue(), im.size


def test_card():
    W, H = 320, 240
    im = Image.new("RGB", (W, H))
    px = im.load()
    for x in range(W):
        r, g, b = colorsys.hsv_to_rgb(x / W, 0.85, 1.0)
        for y in range(H):
            v = 0.55 + 0.45 * (1 - y / (H - 1))
            px[x, y] = (int(r * 255 * v), int(g * 255 * v), int(b * 255 * v))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 34)
    cw, ch = W / 6, H / 4
    for i in range(1, 6):
        d.line([(round(i * cw), 0), (round(i * cw), H)], fill=(0, 0, 0), width=1)
    for j in range(1, 4):
        d.line([(0, round(j * ch)), (W, round(j * ch))], fill=(0, 0, 0), width=1)
    for row in range(4):
        for col in range(6):
            d.text(((col + 0.5) * cw, (row + 0.5) * ch), str(row * 6 + col + 1), font=font,
                   fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    return im


def build_image(what):
    if what == "field":
        return token_field()
    if what == "card":
        return test_card()
    if what == "ruler":
        return ruler_card()
    return Image.new("RGB", (320, 240), COLOURS[what])


if __name__ == "__main__":
    what = next((a for a in sys.argv[1:] if not a.startswith("--") and not a.replace(".", "").isdigit()), "lime")
    landscape = "--landscape" in sys.argv
    im = build_image(what)
    q = int(arg("--quality", "90"))
    grain_target = int(arg("--grain-bytes", "0"))
    if grain_target:
        noise = Image.effect_noise((320, 240), 48).convert("RGB")
        lo, hi = 0.0, 1.0
        for _ in range(18):
            mid = (lo + hi) / 2
            n = len(encode(Image.blend(Image.new("RGB", (320, 240), LIME), noise, mid), landscape, q)[0])
            lo, hi = (mid, hi) if n < grain_target else (lo, mid)
        im = Image.blend(Image.new("RGB", (320, 240), LIME), noise, (lo + hi) / 2)
        what = "grain%d" % grain_target
    fit = int(arg("--fit-bytes", "0"))
    if fit:
        q = next((qq for qq in range(95, 9, -1) if len(encode(im, landscape, qq)[0]) <= fit), None)
        if q is None:
            raise SystemExit("%s does not fit into %d bytes even at q10" % (what, fit))
    jpeg, size = encode(im, landscape=landscape, quality=q)
    com = int(arg("--com-pad", "0"))
    if com > len(jpeg) + 4:
        extra = com - len(jpeg)
        chunks, left = [], extra
        while left > 0:
            body = min(left - 4, 65533)
            if body < 1:
                break
            chunks.append(b"\xff\xfe" + (body + 2).to_bytes(2, "big") + b"C" * body)
            left -= body + 4
        jpeg = jpeg[:2] + b"".join(chunks) + jpeg[2:]
        print("COM segments added: file is %d bytes (target %d)" % (len(jpeg), com), flush=True)
    tail = int(arg("--tail-pad", "0"))
    if tail > len(jpeg):
        assert jpeg[-2:] == b"\xff\xd9", "no EOI at the end"
        jpeg = jpeg + b"\x00" * (tail - len(jpeg))
        print("padded after EOI to %d bytes" % len(jpeg), flush=True)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "test-%s-sent.jpg" % what), "wb") as f:
        f.write(jpeg)
    im.convert("RGB").save(os.path.join(OUT, "test-%s-as-seen.png" % what))
    deck = Deck()
    print("device:", deck.info["product_string"], deck.info["serial_number"], "firmware:", deck.firmware(), flush=True)
    print("image: %s, q%d, %d bytes as %dx%d JPEG, %d chunks" % (what, q, len(jpeg), size[0], size[1], -(-len(jpeg) // 1024)), flush=True)
    deck.handshake(int(arg("--brightness", "100")))
    deck.listen(0.5, "after handshake")
    if "--tiles" in sys.argv:
        for key in range(1, 7):
            tile = Image.new("RGB", (64, 64), LIME if key % 2 else WHITE)
            tbuf = io.BytesIO()
            tile.rotate(-90, expand=True).save(tbuf, "JPEG", quality=100, subsampling=2, optimize=False, progressive=False)
            deck.stream(b"BAT", tbuf.getvalue(), key)
        deck.cmd(b"STP")
        print("six tiles sent (1,3,5 lime; 2,4,6 white) + STP", flush=True)
        deck.listen(1, "after tiles")
    gap = float(arg("--chunk-gap", "0")) / 1000.0
    t0 = time.time()
    deck.stream(b"LOG", jpeg, 1, gap=gap)
    print("LOG sent in %.2f s (chunk gap %d ms)" % (time.time() - t0, gap * 1000), flush=True)
    wait = float(arg("--wait-before-stp", "3"))
    acks = deck.listen(wait, "write report", stop_on_ack=True) if wait > 0 else []
    print("write report: %s" % ("YES" if any(a.startswith("ack code=0x00") for a in acks) else "none"), flush=True)
    deck.cmd(b"STP")
    print("STP sent", flush=True)
    after = float(arg("--after-stp", "1"))
    if after > 0:
        deck.listen(after, "after STP")
    for flag, sub in (("--frame420", 2), ("--frame444", 0)):
        if flag in sys.argv:
            key = int(arg(flag, "5"))
            tb = io.BytesIO()
            frame_tile().rotate(-90, expand=True).save(tb, "JPEG", quality=100, subsampling=sub, optimize=False, progressive=False)
            deck.stream(b"BAT", tb.getvalue(), key)
            deck.cmd(b"STP")
            print("frame tile on key %d (%s, %d bytes) + STP" % (key, "4:2:0" if sub else "4:4:4", len(tb.getvalue())), flush=True)
            deck.listen(0.5, "after frame tile")
    hold = float(arg("--hold", "10"))
    t1 = time.time(); beat = t1
    while time.time() - t1 < hold:
        if time.time() - beat >= 10:
            deck.cmd(b"CONNECT"); beat = time.time()
        time.sleep(0.2)
    if "--dc" in sys.argv:
        deck.cmd(b"CLE", b"\x00\x00DC")
        deck.listen(1, "after CLE DC")
        print("CLE DC sent", flush=True)
    deck.h.close()
    print("closed (%s)" % ("with CLE DC" if "--dc" in sys.argv else "no goodbye frame"), flush=True)
