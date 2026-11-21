"""Cloud helpers: measure a top edge column by column (colour projection between the cloud colour and the
colour just above it), split it at cusps I read from the zooms, fit each bump between my cusps."""
import numpy as np, hand as h
from fitcheck import try_anchors

I = h.IMG


def top_edge(x, y0, y1, inside, above_off=5.0, step=0.05):
    """sub-pixel y where the column x+0.5 turns into `inside` colour, searching down from y0."""
    ys = np.arange(y0, y1, step); c = h.at(np.full(len(ys), x + 0.5), ys)
    inside = np.asarray(inside, float)
    diff = np.abs(c - inside).max(1)
    k = np.where(diff < 18)[0]
    if not len(k): return None
    yin = ys[k[0]]
    A = h.at(x + 0.5, yin - above_off); d = inside - A
    if d @ d < 400: return None
    seg = slice(max(0, k[0] - int(8 / step)), k[0] + 1)
    t = ((c[seg] - A) @ d) / (d @ d); yy = ys[seg]
    j = np.where(t >= 0.5)[0]
    return float(yy[j[0]]) if len(j) else float(yin)


def scan(xs, y0, y1, inside):
    P = [(x + 0.5, top_edge(x, y0, y1, inside)) for x in xs]
    return np.array([p for p in P if p[1] is not None])


def cusp_near(P, x, r=4):
    m = np.abs(P[:, 0] - x) <= r
    q = P[m]
    return q[np.argmax(q[:, 1])] if len(q) else None


def fit_bumps(P, cusps, apex_split=1.0, name=''):
    """P: edge samples sorted by x; cusps: list of anchor points (x, y) in order. One cubic per bump; if its max
    error > apex_split, add a smooth anchor at the bump apex (min y)."""
    ops = []; rep = []
    for a, b in zip(cusps[:-1], cusps[1:]):
        s = P[(P[:, 0] > a[0] + 0.3) & (P[:, 0] < b[0] - 0.3)]
        A, C, r = try_anchors(s, np.asarray(a, float), None, [], np.asarray(b, float)) if len(s) > 3 else (None, [h.solve(a, b, s)], [(0, 0, 0)])
        if r[0][0] > apex_split and len(s) > 8:
            ap = s[np.argmin(s[:, 1])]
            A, C, r = try_anchors(s, np.asarray(a, float), None, [ap], np.asarray(b, float))
        rep.append((name, [round(float(a[0]), 1), round(float(a[1]), 1)], r))
        ops += [['C', c[1].tolist(), c[2].tolist(), c[3].tolist()] for c in C]
    return ops, rep
