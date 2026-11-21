"""Polygon from my rough corners: each side measured sub-pixel along its normal (colour projection between the
two sides of that edge), robust line fit per side, corners = intersections of adjacent side lines."""
import numpy as np, hand as h
I = h.IMG


def side_samples(p, q, r=3.0, trim=0.2, step=1.0, res=0.05):
    p = np.asarray(p, float); q = np.asarray(q, float); d = q - p; L = np.linalg.norm(d); d /= L
    n = np.array([-d[1], d[0]])
    out = []
    for s in np.arange(trim * L, (1 - trim) * L + 1e-9, step):
        c = p + d * s
        offs = np.arange(-r, r + res / 2, res); Q = c[None] + offs[:, None] * n[None]
        col = h.at(Q[:, 0], Q[:, 1])
        A = col[:int(0.6 / res)].mean(0); B = col[-int(0.6 / res):].mean(0); dd = B - A
        if dd @ dd < 300: continue
        t = ((col - A) @ dd) / (dd @ dd)
        k = np.where((t[:-1] < 0.5) & (t[1:] >= 0.5))[0]
        if len(k) != 1: continue
        k = k[0]; o = offs[k] + (0.5 - t[k]) / (t[k + 1] - t[k] + 1e-12) * res
        out.append(c + o * n)
    return np.array(out)


def polygon(corners, r=3.0, trim=0.2, fixed=()):
    """corners: rough (x, y) in order. fixed: indices of sides NOT measured (hidden) -> kept as the rough line."""
    C = [np.asarray(c, float) for c in corners]; n = len(C); lines = []; rep = []
    for i in range(n):
        p, q = C[i], C[(i + 1) % n]
        if i in fixed:
            d = (q - p) / np.linalg.norm(q - p); lines.append((p, d)); rep.append((i, 'hidden')); continue
        S = side_samples(p, q, r, trim)
        if len(S) < 3:
            d = (q - p) / np.linalg.norm(q - p); lines.append((p, d)); rep.append((i, 'too few samples', len(S))); continue
        c, d, res = h.line_fit(S)
        lines.append((c, d)); rep.append((i, len(S), round(res, 2)))
    V = [h.intersect(lines[i - 1], lines[i]) for i in range(n)]
    return V, rep


def quad_path(V):
    return {'start': V[0].tolist(), 'ops': [['L', v.tolist()] for v in V[1:]], 'closed': True}


def fill_inside(V, shrink=2.0):
    import cv2
    V = np.array(V, float); c = V.mean(0)
    Vs = c + (V - c) * np.clip(1 - shrink / np.linalg.norm(V - c, axis=1, keepdims=True), 0.2, 1)
    m = np.zeros(I.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.round((Vs - 0.5) * 16).astype(np.int32)], 1, cv2.LINE_8, 4)
    return np.median(I[m > 0], 0) if m.any() else None


def polygon_c(corners, kinds, r=2.5, trim=0.2):
    """Clean architectural polygon. kinds[i] for side i (corner i -> i+1): 'v' vertical, 'h' horizontal
    (position = mean of the measured samples, direction forced), 's' free straight line (fitted),
    'x' hidden (kept on my rough corners, direction forced v/h if the rough side is axis-aligned).
    Corners = intersections of consecutive side lines, so shared points stay exact."""
    C = [np.asarray(c, float) for c in corners]; n = len(C); lines = []; rep = []
    for i in range(n):
        p, q = C[i], C[(i + 1) % n]; k = kinds[i]
        S = side_samples(p, q, r, trim) if k in 'vhs' else np.zeros((0, 2))
        if k == 'v' or (k == 'x' and abs(q[0] - p[0]) < 1e-6):
            x = float(np.median(S[:, 0])) if len(S) >= 3 else float((p[0] + q[0]) / 2)
            lines.append((np.array([x, 0.0]), np.array([0.0, 1.0]))); rep.append((i, 'v', round(x, 2), len(S), round(float(np.abs(S[:, 0] - x).max()), 2) if len(S) else None))
        elif k == 'h' or (k == 'x' and abs(q[1] - p[1]) < 1e-6):
            y = float(np.median(S[:, 1])) if len(S) >= 3 else float((p[1] + q[1]) / 2)
            lines.append((np.array([0.0, y]), np.array([1.0, 0.0]))); rep.append((i, 'h', round(y, 2), len(S), round(float(np.abs(S[:, 1] - y).max()), 2) if len(S) else None))
        elif k == 's' and len(S) >= 3:
            c, d, res = h.line_fit(S); lines.append((c, d)); rep.append((i, 's', len(S), round(res, 2)))
        else:
            d = (q - p) / np.linalg.norm(q - p); lines.append((p, d)); rep.append((i, 'rough'))
    V = [h.intersect(lines[i - 1], lines[i]) for i in range(n)]
    return V, rep
