"""Write the Stream Dock N3 boot/background image (the `LOG` frame), own code from the documented protocol.

usage: burn_logo.py                 compose the token-field placeholder and write it
       burn_logo.py image.png       write a given image instead (resized to 320 x 240, then rotated)
       burn_logo.py --dc            lab option, never in the app: after the write, also send CLE DC (the vendor "software disconnected"
                                    notice; the vendor documents it as "clears all display" and on Nov 1
                                    it left this unit's panel black; only for a controlled test)
       burn_logo.py --dc-only       only send CLE DC and listen
       burn_logo.py --wait 10       seconds to wait for the device's write report before STP (default 10;
                                    it comes after about 12 ms per KB: 0.13 s for 11 KB, 0.26 s for 22 KB)

What the vendor SDK says about this frame (CPP_README "ROM vs RAM"): setBackgroundImgFile writes the
startup background to the device ROM and it "remains after restart"; key images are RAM and vanish at
power-off. Flash wears, so this is written once per device, never on launch.

Frame: CRT\0\0LOG <u32be jpegLength> \x01, then the JPEG in 1024-byte payload chunks. Rhythm, copied
from what the vendor's libtransport puts on the wire: after the last chunk it blocks on ONE input read
with a 3 s timeout (on this unit a good write answers with one code-0x00 report 0.12-0.26 s after the
last chunk, and the image's six tile crops + STP must go first, NOTES.md), only then does CRT\0\0STP go out, and the
vendor's N3 test sleeps 1 s after that. We then keep the handle open with the CONNECT heartbeat for
10 s more and close without any goodbye frame: the deck keeps showing what it shows, and when the
firmware restarts on its own (about a minute after the host goes silent) it comes up on the ROM image.
Image: 320 x 240 landscape as seen, rotated 90 degrees clockwise before encoding (PIL rotate(-90)),
so the JPEG sent is 240 x 320, like the 64 x 64 key tiles are rotated. The vendor encodes at q85 4:2:0.
"""
import ctypes, io, os, random, struct, sys, time
import hid
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_geometry import TILE, tile_origin

VIDS = {0x5548, 0x6603}
REPORT_OUT, REPORT_IN = 1024, 512
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "boot-image")
INK, LIME, WHITE = (19, 21, 18), (146, 231, 89), (255, 255, 255)


def find():
    for d in hid.enumerate():
        if d["vendor_id"] in VIDS and d.get("usage_page") == 0xFFA0 and d.get("usage") == 1:
            return d
    raise SystemExit("no Stream Dock vendor interface found (is the deck plugged in? is StreamDock quit?)")


class Deck:
    def __init__(self):
        self.info = find()
        if sys.platform == "darwin":
            try:
                ctypes.CDLL(hid.__file__).hid_darwin_set_open_exclusive(ctypes.c_int(0))
            except Exception:
                pass
        self.h = hid.device()
        self.h.open_path(self.info["path"])
        self.h.set_nonblocking(1)

    def write(self, payload: bytes):
        pkt = bytearray(1 + REPORT_OUT)
        pkt[1:1 + len(payload)] = payload
        if self.h.write(bytes(pkt)) < 0:
            raise RuntimeError("hid write failed: %s" % self.h.error())

    def cmd(self, tag: bytes, tail: bytes = b""):
        self.write(b"CRT\x00\x00" + tag + tail)

    def firmware(self):
        try:
            r = bytes(self.h.get_input_report(0, 64))
            return r.lstrip(b"\x00").split(b"\x00", 1)[0].decode("ascii", "replace")
        except Exception as e:
            return "n/a (%s)" % e

    def handshake(self, brightness: int = 70):
        self.cmd(b"DIS")
        self.cmd(b"LIG", b"\x00\x00" + bytes([brightness]))
        self.cmd(b"QUCMD", b"\x1f\x11\x00\x11\x00\x11\x00")
        self.cmd(b"LIG", b"\x00\x00" + bytes([brightness]))

    def stream(self, tag: bytes, data: bytes, last: int, gap: float = 0.0):
        """Header, then the payload in 1024-byte chunks; `gap` seconds of pause between chunks."""
        self.cmd(tag, struct.pack(">I", len(data)) + bytes([last]))
        for i in range(0, len(data), REPORT_OUT):
            if gap and i:
                time.sleep(gap)
            self.write(data[i:i + REPORT_OUT])

    def listen(self, seconds: float, label: str, stop_on_ack: bool = False):
        """Read input reports for `seconds`; with stop_on_ack, return as soon as a write report
        (ACK code 0x00) arrives. The LOG write is the one write this firmware acknowledges."""
        start = time.time()
        end = start + seconds
        seen = []
        while time.time() < end:
            data = self.h.read(REPORT_IN, 50)
            if data:
                pkt = bytes(data)
                at = time.time() - start
                if pkt[:3] == b"ACK":
                    seen.append("ack code=0x%02x state=%d at +%.2fs [%s]" % (pkt[9], pkt[10], at, pkt[:16].hex()))
                    if stop_on_ack and pkt[9] == 0x00:
                        break
                else:
                    seen.append("raw %s at +%.2fs" % (pkt[:16].hex(), at))
        print("%s: %s" % (label, ", ".join(seen) if seen else "no input reports"), flush=True)
        return seen


def token_field() -> Image.Image:
    """A geometry-free placeholder: #131512 with the Stigg token grid (6 px squares on a 16 px pitch,
    about 60 % lime / 40 % white points, a little denser toward the bottom right). It reads as ours
    whichever parts of the 320 x 240 panel the six windows show."""
    im = Image.new("RGB", (320, 240), INK)
    d = ImageDraw.Draw(im)
    rng = random.Random(1110)
    for cy in range(15):
        for cx in range(20):
            p = 0.10 + 0.16 * ((cx / 19 + cy / 14) / 2)
            if rng.random() < p:
                x, y = cx * 16 + 5, cy * 16 + 5
                d.rectangle([x, y, x + 5, y + 5], fill=LIME if rng.random() < 0.6 else WHITE)
    return im


def encode(im: Image.Image, quality: int = 97) -> bytes:   # q97: no JPEG halo outside the tile rects
    im = im.convert("RGB")
    if im.size != (320, 240):
        im = im.resize((320, 240), Image.LANCZOS)
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, "boot-image-as-seen.png"))
    rotated = im.rotate(-90, expand=True)           # 240 x 320, clockwise, like the key tiles
    buf = io.BytesIO()
    rotated.save(buf, "JPEG", quality=quality, subsampling=2, optimize=False, progressive=False)
    data = buf.getvalue()
    with open(os.path.join(OUT, "boot-image-sent.jpg"), "wb") as f:
        f.write(data)
    return data


if __name__ == "__main__":
    deck = Deck()
    print("device:", deck.info["manufacturer_string"], deck.info["product_string"], deck.info["serial_number"])
    print("firmware:", deck.firmware(), flush=True)
    deck.handshake()
    if "--dc-only" in sys.argv:
        deck.cmd(b"CLE", b"\x00\x00DC")                # vendor: "disconnects and clears all display"
        deck.listen(2, "after CLE DC")
        deck.h.close()
        raise SystemExit
    src = [a for a in sys.argv[1:] if not a.startswith("--") and not a.replace(".", "").isdigit()]
    wait = float(sys.argv[sys.argv.index("--wait") + 1]) if "--wait" in sys.argv else 10.0
    im = Image.open(src[0]) if src else token_field()
    jpeg = encode(im)
    print("jpeg: %d bytes, %d chunks" % (len(jpeg), -(-len(jpeg) // REPORT_OUT)), flush=True)
    deck.listen(0.5, "after handshake")
    # Tiles first: every accepted LOG write on this firmware came after a BAT + STP in the same session
    # (Nov 2 tests 3, 13, 14); every write without it failed. Paint the image's own six tile crops so
    # the panel already shows the right picture in the six squares.
    seen = Image.open(os.path.join(OUT, "boot-image-as-seen.png")).convert("RGB")
    for key in range(1, 7):
        x, y = tile_origin(key)
        tb = io.BytesIO()
        seen.crop((x, y, x + TILE, y + TILE)).rotate(-90, expand=True).save(
            tb, "JPEG", quality=100, subsampling=2, optimize=False, progressive=False)
        deck.stream(b"BAT", tb.getvalue(), key)
    deck.cmd(b"STP")
    print("six tile crops + STP sent", flush=True)
    deck.listen(1, "after tiles")
    t0 = time.time()
    deck.stream(b"LOG", jpeg, 1)
    print("LOG sent in %.2f s; waiting up to %.0f s for the write report (libtransport: 3 s)" % (time.time() - t0, wait), flush=True)
    acks = deck.listen(wait, "after LOG", stop_on_ack=True)   # the vendor's STP waits behind this read
    if not any(a.startswith("ack code=0x00") for a in acks):
        deck.h.close()
        raise SystemExit("no write report within %.0f s: nothing refreshed. Replug the deck and retry." % wait)
    deck.cmd(b"STP")
    print("STP sent", flush=True)
    deck.listen(1, "after STP")                        # the vendor's N3 test sleeps 1 s here
    t1 = time.time()
    while time.time() - t1 < 10:                       # keep the session alive a little longer; heartbeat at 5 s
        if 5 <= time.time() - t1 < 5.3:
            deck.cmd(b"CONNECT")
        time.sleep(0.3)
    if "--dc" in sys.argv:
        deck.cmd(b"CLE", b"\x00\x00DC")
        deck.listen(1, "after CLE DC")
        print("CLE DC sent (controlled test)", flush=True)
    deck.h.close()
    print("closed with no goodbye frame. Look at the deck now, then unplug and replug it with nothing")
    print("running: the image must be there both times. The result goes into NOTES.md.")
