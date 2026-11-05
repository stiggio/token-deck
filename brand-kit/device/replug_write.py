"""Wait for the deck to be unplugged and plugged back in, then run one log_test.py write, own code.

usage: replug_write.py [--settle S] <log_test.py arguments...>   e.g.  replug_write.py --settle 8 card --tiles
Polls hid.enumerate() twice a second for the vendor interface (usage page 0xFFA0, usage 1); fires S seconds
(default 3) after the device reappears. Gives up after 60 minutes.
"""
import os, subprocess, sys, time
import hid

VIDS = {0x5548, 0x6603}
HERE = os.path.dirname(os.path.abspath(__file__))

def present():
    return any(d["vendor_id"] in VIDS and d.get("usage_page") == 0xFFA0 and d.get("usage") == 1 for d in hid.enumerate())

if __name__ == "__main__":
    argv = sys.argv[1:]
    settle = 3.0
    if "--settle" in argv:
        i = argv.index("--settle"); settle = float(argv[i + 1]); del argv[i:i + 2]
    t0 = time.time()
    was = present()
    print("deck present now: %s; waiting for unplug + replug" % was, flush=True)
    seen_absent = not was
    while time.time() - t0 < 3600:
        p = present()
        if not p and not seen_absent:
            seen_absent = True
            print("+%.0fs unplugged" % (time.time() - t0), flush=True)
        elif p and seen_absent:
            print("+%.0fs back; settling %.0f s" % (time.time() - t0, settle), flush=True)
            time.sleep(settle)
            cmd = [sys.executable, "-u", os.path.join(HERE, "log_test.py")] + argv
            print("running:", " ".join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd)), flush=True)
            sys.exit(subprocess.call(cmd))
        time.sleep(0.5)
    print("gave up after 60 minutes without a replug", flush=True)
    sys.exit(2)
