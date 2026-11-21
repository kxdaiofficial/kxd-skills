"""Whole-image check by numbers, then a look only where it is off. Main session, after assembly (or on the proxy render).

    python3 tools/hotspots.py checks/main-3.png            # top 12 spots -> checks/main-3-hot.png
    python3 tools/hotspots.py checks/final.png --top 18 --thr 60
    python3 tools/hotspots.py checks/08-v2.png --box 276,228,374,310      # one part, Gate 3

Prints mean diff /255, p95, share of pixels > thr, then the biggest blobs of pixels that differ by more than thr
(max channel), ranked by area x mean diff. Each blob is a SPOT TO LOOK AT (a missing tick, a caster, a z-order slip,
a gradient left out on purpose), not a shape: nothing here is drawn from it. Tiles in -hot.png: source | render."""
import sys, os, argparse
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand as h
from measure import check_img
from sheet import sheet

a = argparse.ArgumentParser(); a.add_argument('render'); a.add_argument('--top', type=int, default=12)
a.add_argument('--thr', type=float, default=60); a.add_argument('--min', type=int, default=4, help='min blob area px')
a.add_argument('--box', help='x0,y0,x1,y1: only this part (catches a small feature the part forgot, e.g. an eye tick)')
o = a.parse_args()
R = check_img(o.render)
if R.shape[:2] != h.IMG.shape[:2]: sys.exit('render is not at source size')
A = np.abs(R.astype(float) - h.IMG.astype(float)); D = A.max(2); keep = np.ones_like(D, bool)
if o.box:   # one part: only its box counts (spots of parts not drawn yet fall outside it, or are named as such)
    x0, y0, x1, y1 = map(int, o.box.split(',')); keep[:] = False; keep[y0:y1, x0:x1] = True; D = np.where(keep, D, 0)
    print('box', o.box, end=' · ')
print('mean %.2f/255 · p95 %.1f · >%d: %.2f %% of pixels' % (A[keep].mean(), np.percentile(D[keep], 95), o.thr,
      100 * (D[keep] > o.thr).mean()))
M = cv2.dilate((D > o.thr).astype(np.uint8), np.ones((3, 3), np.uint8))     # join 1-px gaps along a thin miss
n, lab, st, cen = cv2.connectedComponentsWithStats(M, 8)
spots = []
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] < o.min: continue
    m = lab == i; md = D[m].mean(); ys, xs = np.nonzero(m); k = np.argmax(D[m])
    spots.append((st[i, cv2.CC_STAT_AREA] * md, xs[k] + 0.5, ys[k] + 0.5, md, st[i, cv2.CC_STAT_AREA],
                  st[i, 0], st[i, 1], st[i, 0] + st[i, 2], st[i, 1] + st[i, 3]))
spots.sort(reverse=True)
print('%d spots over %d px; top %d (open %s):' % (len(spots), o.min, min(o.top, len(spots)),
      os.path.splitext(o.render)[0] + '-hot.png'))
for j, s in enumerate(spots[:o.top]):
    print('  H%d (%.0f, %.0f) mean %.0f, %d px, box %d,%d,%d,%d' % ((j + 1,) + s[1:]))
sheet([(s[1], s[2], s[3], s[4]) for s in spots[:o.top]], R, os.path.splitext(o.render)[0] + '-hot.png', box=40, k=4, tag='H')
