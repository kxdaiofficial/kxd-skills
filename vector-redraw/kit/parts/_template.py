"""<PART NAME> — copy this file to parts/<nn>_<part>.py, one file per part.

YOU decide every guide and anchor, reading coordinates off gridded zooms (tools/zoom.py).
The code only MEASURES along your guides and SOLVES handle lengths. No tracing, no contour extraction,
no coordinates typed from memory or from a downscaled image.

Run:  python3 parts/<nn>_<part>.py    -> writes sections/<part>.json + prints the fit report (gate 2)."""
import sys, os, json
JOB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(JOB, 'tools'))
from measure import *          # h (hand), line_c, edge_auto, cusp, run_fit, handle_check, ops_of, rgb
import numpy as np

PART = '<NN>_<part>'             # file stem of the section JSON: MUST equal its line in sections/ZORDER.txt
GROUP = '10 Character'           # top-level group name (shared by all parts of one object)
SECTION = 'C1 <Part name>'       # this part's container; re-running replaces it in place
rep = []

# ---------- 1. one visible ink line ----------
# Guide = a rough polyline that FOLLOWS the line, ~every 5-10 px, read off the zoom (within ~2 px of the ink is enough).
G = [(0, 0), (10, 10)]                                  # <- replace with points read from the zoom
P, W, D = line_c(G, r=3)                                # measured centres, widths, depth (dark line on light)
# Drop samples where another line crosses / touches this one (they pull the centre and make a fake wobble):
# P = P[(P[:, 1] < y_junction - 2) | (P[:, 1] > y_junction + 2)]

# Anchors: as FEW as the shape needs. Corners at real corners (cusp() = intersection of the two sides), smooth ('s')
# where the line keeps going. Every anchor is a point ON the measured samples or a cusp(), never a typed guess.
a0 = P[0]; a1 = P[-1]
# a_mid = cusp(P, (x, y))       # corner read from the zoom -> exact intersection of the two measured sides
C, r = run_fit(P, [a0, a1], ['c', 'c'])
for k, x in enumerate(r): rep.append(('line seg %d' % k,) + x)
bad = handle_check(C)            # degenerate / lopsided handles -> pick anchors again even if the error is low

# ink colour + width: sampled, never chosen
def ink(P, W):
    cols = []
    for p, w in zip(P, W):
        if w < 1.4: continue
        x, y = int(p[0]), int(p[1]); blk = h.IMG[y - 1:y + 2, x - 1:x + 2].reshape(-1, 3)
        cols.append(blk[blk.sum(1).argmin()])
    return rgb(np.median(cols, 0)) if cols else [0, 0, 0]

line_path = {'start': C[0][0].tolist(), 'ops': ops_of(C), 'closed': False}

# ---------- 2. the fill behind it ----------
# Fill = no stroke. Its visible edge reuses the line centre above; where it goes under a front object, route it freely.
fill_col = rgb(h.colour(0, 0, 4, 4))                    # <- a small box INSIDE the flat colour, read from the zoom
fill_path = {'start': C[0][0].tolist(), 'ops': ops_of(C) + [['L', [0, 20]]], 'closed': True}

# ---------- 3. write the section: back to front ----------
objs = [
    {'name': '<Part> fill', 'fill': fill_col, 'path': fill_path},
    {'name': '<Part> outline', 'stroke': ink(P, W), 'width': round(float(np.median(W)), 2), 'path': line_path},
]
os.makedirs(os.path.join(JOB, 'sections'), exist_ok=True)
json.dump({'group': GROUP, 'section': SECTION, 'objects': objs}, open(os.path.join(JOB, 'sections', PART + '.json'), 'w'))
for x in rep: print('%-28s max %.2f mean %.2f n %d' % x)
print('degenerate handles:', bad or 'none')
