"""Minimal Stream Dock N3 probe, written from the documented protocol (no external code).

usage: probe_n3.py            push three labelled test tiles to keys 1-3, listen 3 s
       probe_n3.py listen 20  only listen for input reports for 20 s (press keys/knobs)
Protocol (vendor HID interface, usage page 0xFFA0):
  output report 1024 bytes (hidapi write: leading 0x00 report id + 1024)
  input  report 512 bytes: b"ACK\0\0OK\0\0" (9 bytes) + code@9 + state@10
  CRT\0\0LIG\0\0<pct>        brightness
  CRT\0\0DIS / HAN           wake / sleep
  CRT\0\0STP                 refresh
  CRT\0\0BAT<u32be len><key> + JPEG in 1024-byte chunks   (64x64 tile, pre-rotated 90 deg clockwise)
"""
import ctypes, io, struct, sys, time
import hid
from PIL import Image, ImageDraw, ImageFont

VIDS = {0x5548, 0x6603}
REPORT_OUT, REPORT_IN = 1024, 512


def find():
    for d in hid.enumerate():
        if d["vendor_id"] in VIDS and d.get("usage_page") == 0xFFA0 and d.get("usage") == 1:
            return d
    raise SystemExit("no Stream Dock vendor interface found")


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
        n = self.h.write(bytes(pkt))
        if n < 0:
            raise RuntimeError("hid write failed: %s" % self.h.error())

    def cmd(self, tag: bytes, tail: bytes = b""):
        self.write(b"CRT\x00\x00" + tag + tail)

    def firmware(self):
        r = bytes(self.h.get_input_report(0, 64))
        return r.lstrip(b"\x00").split(b"\x00", 1)[0].decode("ascii", "replace")

    def stream(self, tag: bytes, data: bytes, last: int):
        self.cmd(tag, struct.pack(">I", len(data)) + bytes([last]))
        for i in range(0, len(data), REPORT_OUT):
            self.write(data[i:i + REPORT_OUT])

    def set_key(self, key: int, im: Image.Image):
        im = im.convert("RGB").resize((64, 64)).rotate(-90, expand=True)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=100, subsampling=2, optimize=False, progressive=False)
        self.stream(b"BAT", buf.getvalue(), key)

    def handshake(self, brightness: int = 70):
        """What the vendor app sends on connect: wake, brightness, QUCMD config, brightness."""
        self.cmd(b"DIS")
        self.cmd(b"LIG", b"\x00\x00" + bytes([brightness]))
        self.cmd(b"QUCMD", b"\x1f\x11\x00\x11\x00\x11\x00")
        self.cmd(b"LIG", b"\x00\x00" + bytes([brightness]))

    def events(self, seconds: float):
        end = time.time() + seconds
        last_beat = time.time()
        while time.time() < end:
            if time.time() - last_beat > 10:          # the vendor app's CONNECT heartbeat
                self.cmd(b"CONNECT")
                last_beat = time.time()
            data = self.h.read(REPORT_IN, 50)
            if data:
                pkt = bytes(data)
                if pkt[:3] == b"ACK":
                    yield {"code": pkt[9], "state": pkt[10], "raw": pkt[:12].hex()}
                else:
                    yield {"raw": pkt[:16].hex()}


def tile(label: str) -> Image.Image:
    im = Image.new("RGB", (64, 64), "#131512")
    d = ImageDraw.Draw(im)
    for x in range(4, 64, 8):                      # a lime token row along the TOP edge
        d.rectangle([x, 4, x + 4, 8], fill="#92e759")
    d.text((10, 18), label, fill="white", font=ImageFont.load_default(size=26))
    d.polygon([(32, 46), (25, 56), (39, 56)], fill="#92e759")   # arrow pointing UP
    return im


if __name__ == "__main__":
    deck = Deck()
    print("device:", deck.info["product_string"], deck.info["serial_number"])
    print("firmware:", deck.firmware())
    if len(sys.argv) > 1 and sys.argv[1] == "listen":
        secs = float(sys.argv[2]) if len(sys.argv) > 2 else 20
        deck.handshake()
        print("listening %.0f s, press keys and turn knobs..." % secs, flush=True)
        for ev in deck.events(secs):
            print("%.3f" % time.time(), ev, flush=True)
        raise SystemExit
    deck.cmd(b"DIS")
    deck.cmd(b"LIG", b"\x00\x00" + bytes([70]))
    for k in (1, 2, 3):
        deck.set_key(k, tile(str(k)))
    deck.cmd(b"STP")
    print("sent tiles to keys 1-3; listening 3 s for reports")
    for ev in deck.events(3):
        print(ev)
    print("done")
