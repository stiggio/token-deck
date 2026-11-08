"""Paint the 64 x 64 frame tile on keys (RAM only, no flash write) and hold the session, own code.

usage: paint_tiles.py [--keys 1,2,3,4,5,6] [--hold 240]
Over a burned ruler image, a photo then shows each tile's exact panel position (calibration step).
"""
import io, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from burn_logo import Deck
from calib_images import frame_tile


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


if __name__ == "__main__":
    keys = [int(k) for k in arg("--keys", "1,2,3,4,5,6").split(",")]
    hold = float(arg("--hold", "240"))
    deck = Deck()
    print("device:", deck.info["product_string"], deck.info["serial_number"], "firmware:", deck.firmware(), flush=True)
    deck.handshake(100)
    deck.listen(0.5, "after handshake")
    tb = io.BytesIO()
    frame_tile().rotate(-90, expand=True).save(tb, "JPEG", quality=100, subsampling=2, optimize=False, progressive=False)
    for k in keys:
        deck.stream(b"BAT", tb.getvalue(), k)
    deck.cmd(b"STP")
    print("frame tiles on keys %s + STP; holding %.0f s" % (keys, hold), flush=True)
    t0 = time.time(); beat = t0
    while time.time() - t0 < hold:
        if time.time() - beat >= 10:
            deck.cmd(b"CONNECT"); beat = time.time()
        time.sleep(0.2)
    deck.h.close()
    print("closed (no goodbye frame)", flush=True)
