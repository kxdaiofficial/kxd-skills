"""runs.py x0 y0 x1 y1 [thr] [--cols] — per row (or per column), centres of dark runs (L < thr, default 150), luminance-weighted.
Helper added by part 21: raw pixel rows/columns to place guides (measurement only, I still choose the guide)."""
import sys, numpy as np
sys.path.insert(0, 'tools'); import hand as h
a = [x for x in sys.argv[1:] if not x.startswith('--')]
x0, y0, x1, y1 = map(int, a[:4]); thr = float(a[4]) if len(a) > 4 else 150
ch = next((int(x[7:]) for x in sys.argv if x.startswith("--chan=")), None)
L = h.IMG[..., 0] * .299 + h.IMG[..., 1] * .587 + h.IMG[..., 2] * .114 if ch is None else h.IMG[..., ch]
cols = '--cols' in sys.argv
rng = range(x0, x1) if cols else range(y0, y1)
for k in rng:
    v = L[y0:y1, k] if cols else L[k, x0:x1]; base = y0 if cols else x0
    m = v < thr; out = []; i = 0
    while i < len(v):
        if m[i]:
            j = i
            while j < len(v) and m[j]: j += 1
            w = thr - v[i:j]; c = (np.arange(i, j) * w).sum() / w.sum() + base + 0.5
            out.append('%.1f(%d)' % (c, int(v[i:j].min()))); i = j
        else: i += 1
    print(('x' if cols else 'y') + '%d: ' % k + ' '.join(out))
