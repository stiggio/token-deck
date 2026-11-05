"""The welcome screen's six key-tile crops, encoded byte for byte as burn_logo.py sends them, own code.

Every accepted LOG write on this deck came right after these six tiles + STP (device/NOTES.md, the rule
after test 17), so the app sends exactly these bytes before its LOG, and also paints them on quit and on
the idle screen: crop welcome-320x240.png at each tile origin (panel_geometry.py), rotate 90 degrees
clockwise, Pillow JPEG quality 100, 4:2:0, baseline.

usage: welcome_tiles.py [image.png] [outdir]     default: welcome-320x240.png -> welcome-tiles/key1.jpg ... key6.jpg
"""
import io, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from panel_geometry import TILE, tile_origin   # noqa: E402


def crops(png):
    im = Image.open(png).convert("RGB")
    out = []
    for key in range(1, 7):
        x, y = tile_origin(key)
        buf = io.BytesIO()
        im.crop((x, y, x + TILE, y + TILE)).rotate(-90, expand=True).save(
            buf, "JPEG", quality=100, subsampling=2, optimize=False, progressive=False)
        out.append(buf.getvalue())
    return out


if __name__ == "__main__":
    png = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "welcome-320x240.png")
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "welcome-tiles")
    os.makedirs(outdir, exist_ok=True)
    for key, data in enumerate(crops(png), 1):
        open(os.path.join(outdir, "key%d.jpg" % key), "wb").write(data)
        print("key%d.jpg %d bytes" % (key, len(data)))
