"""LOG write sweep, own code: find what this firmware accepts, using the device's write report as the
oracle (ACK code 0x00 after the last chunk = written; no report = not written). No eyes needed.

usage: log_sweep.py lime                      one solid-lime attempt (1.8 KB; known good): is the device sane?
       log_sweep.py field q50 q70 q85 q90      token field at these JPEG qualities, smallest first,
                                              stop at the first attempt that gets no report
       log_sweep.py pad 4000 8000 12000        solid lime padded with JPEG COM segments to these sizes
options: --wait S (report wait per attempt, default 8) --no-stp (never refresh, just test the report)
Every successful attempt is followed by STP (so the panel shows it) unless --no-stp. Ends with a 10 s
heartbeat hold and a silent close.
"""
import io, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from burn_logo import Deck, token_field, LIME, OUT

def jpeg_of(im, q):
    b = io.BytesIO()
    im.convert("RGB").rotate(-90, expand=True).save(b, "JPEG", quality=q, subsampling=2, optimize=False, progressive=False)
    return b.getvalue()

def pad(jpeg, size):
    """Insert one COM segment (FF FE, u16be length, data) right after SOI so the file is `size` bytes."""
    extra = size - len(jpeg)
    if extra < 4:
        return jpeg
    body = b"P" * (extra - 4)
    seg = b"\xff\xfe" + (len(body) + 2).to_bytes(2, "big") + body
    return jpeg[:2] + seg + jpeg[2:]

def attempt(deck, label, data, wait, do_stp):
    print("-- %s: %d bytes, %d chunks" % (label, len(data), -(-len(data) // 1024)), flush=True)
    deck.stream(b"LOG", data, 1)
    acks = deck.listen(wait, "   report", stop_on_ack=True)
    ok = any(a.startswith("ack code=0x00") for a in acks)
    if ok and do_stp:
        deck.cmd(b"STP")
        deck.listen(1, "   after STP")
    print("   %s" % ("WRITTEN" if ok else "NO REPORT"), flush=True)
    return ok

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    wait = float(sys.argv[sys.argv.index("--wait") + 1]) if "--wait" in sys.argv else 8.0
    args = [a for a in args if a != str(wait) and a != str(int(wait))]
    do_stp = "--no-stp" not in sys.argv
    mode = args[0] if args else "lime"
    lime = Image.new("RGB", (320, 240), LIME)
    plan = []
    if mode == "lime":
        plan.append(("lime q90", jpeg_of(lime, 90)))
    elif mode == "field":
        for q in [int(x.lstrip("q")) for x in args[1:]] or [50, 70, 85, 90]:
            plan.append(("token field q%d" % q, jpeg_of(token_field(), q)))
    elif mode == "pad":
        base = jpeg_of(lime, 90)
        for n in [int(x) for x in args[1:]]:
            plan.append(("lime padded to %d" % n, pad(base, n)))
    deck = Deck()
    print("device:", deck.info["product_string"], deck.info["serial_number"], "firmware:", deck.firmware(), flush=True)
    deck.handshake(100)
    deck.listen(2, "settle after handshake")
    results = []
    for label, data in plan:
        ok = attempt(deck, label, data, wait, do_stp)
        results.append((label, len(data), ok))
        if not ok:
            print("stopping at the first failure (the device may now be waiting for image bytes; replug before the next run)", flush=True)
            break
        time.sleep(1)
    t1 = time.time()
    while time.time() - t1 < 10:
        if 5 <= time.time() - t1 < 5.3:
            deck.cmd(b"CONNECT")
        time.sleep(0.3)
    deck.h.close()
    print("summary:", "; ".join("%s (%d B): %s" % (l, n, "written" if ok else "no report") for l, n, ok in results), flush=True)
