"""Stream Dock N3 panel geometry, measured on Gabriel's unit (VSD N3, firmware V3.VSDN3_PXL.02.010) on
Nov 2, 2026 from photos of a calibration ruler burned with LOG (tests 14 and 15). Panel coordinates are
the 320 x 240 image as seen (before the 90 degree rotation applied on the wire). Accuracy about +-1 px.

TILE_*: where the firmware draws each 64 x 64 key image (BAT). Fixed grid, pitch 104 x 103.
WINDOWS: what each key's window shows of the panel (x0, y0, x1, y1). The windows show the burned
background around each tile: up to 7 px on the left, 14 px on the right, 8 px on top, 11 px below.
WINDOWS are half-open: x1 and y1 are exclusive (as v7_common.region uses them).
"""
TILE = 64
TILE_X = (20, 124, 228)
TILE_Y = (28, 131)
WINDOWS = [(13, 20, 88, 97), (120, 20, 198, 97), (228, 20, 306, 97),
           (13, 130, 88, 206), (120, 130, 198, 206), (228, 130, 306, 206)]


def tile_origin(key):
    """Keys 1-6, left to right, top to bottom."""
    return TILE_X[(key - 1) % 3], TILE_Y[(key - 1) // 3]
