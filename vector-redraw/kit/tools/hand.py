"""Hand-redraw helpers (approved method).
I place guides and anchors; this module only MEASURES along my guides and SOLVES handles.
Coordinates: doc px, pixel i covers [i, i+1] (centre i+0.5)."""
import numpy as np, cv2, json, os
from PIL import Image

JOB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the job folder (tools/ lives inside it)
SRC = os.environ.get('REDRAW_SRC') or os.path.join(JOB, 'source.png')
IMG = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32)
H, W = IMG.shape[:2]


def at(x, y, A=IMG):
    """bilinear sample at doc coords (arrays ok)."""
    x = np.clip(np.asarray(x, float) - 0.5, 0, A.shape[1] - 1.001); y = np.clip(np.asarray(y, float) - 0.5, 0, A.shape[0] - 1.001)
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[..., None] if A.ndim == 3 else x - x0
    fy = (y - y0)[..., None] if A.ndim == 3 else y - y0
    return A[y0, x0] * (1 - fx) * (1 - fy) + A[y0, x0 + 1] * fx * (1 - fy) + A[y0 + 1, x0] * (1 - fx) * fy + A[y0 + 1, x0 + 1] * fx * fy


def colour(x0, y0, x1, y1):
    """median colour of a box I pick."""
    return np.median(IMG[int(y0):int(y1), int(x0):int(x1)].reshape(-1, 3), 0)


def densify(guide, step=2.0):
    g = np.asarray(guide, float)
    out = [g[0]]
    for a, b in zip(g[:-1], g[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        for k in range(1, n + 1): out.append(a + (b - a) * k / n)
    return np.array(out)


def normals(P):
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    return np.stack([-T[:, 1], T[:, 0]], 1)


def edge(guide, cA, cB, r=4.0, step=2.0, res=0.1):
    """points where colour goes from cA to cB, searched along the normal of my guide (±r).
    returns (pts, ok_mask). A sample is rejected when the profile does not reach both colours."""
    P = densify(guide, step); N = normals(P)
    offs = np.arange(-r, r + res / 2, res)
    cA = np.asarray(cA, float); cB = np.asarray(cB, float); d = cB - cA; dd = d @ d
    out = []; ok = []
    for p, n in zip(P, N):
        Q = p[None] + offs[:, None] * n[None]
        c = at(Q[:, 0], Q[:, 1])
        t = ((c - cA) @ d) / dd
        s = np.sign(t - 0.5)
        idx = np.where(np.diff(s) != 0)[0]
        if len(idx) == 0 or t.min() > 0.25 or t.max() < 0.75:
            out.append(p); ok.append(False); continue
        k = idx[np.argmin(np.abs(offs[idx]))]
        f = (0.5 - t[k]) / (t[k + 1] - t[k] + 1e-12)
        o = offs[k] + f * res
        out.append(p + o * n); ok.append(True)
    return np.array(out), np.array(ok)


def line(guide, kind='dark', r=3.0, step=2.0, res=0.1, ref=None, chan=None):
    """centre of a thin line near my guide: contrast-weighted centroid across the normal.
    ref: background colour (default = brightest/darkest end of each profile). Returns pts, widths."""
    P = densify(guide, step); N = normals(P)
    offs = np.arange(-r, r + res / 2, res)
    Lg = cv2.cvtColor(IMG.astype(np.uint8), cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32) if chan is None else IMG[..., chan].copy()
    out = []; wid = []
    for p, n in zip(P, N):
        Q = p[None] + offs[:, None] * n[None]
        l = at(Q[:, 0], Q[:, 1], Lg)
        bg = max(l[0], l[-1]) if kind == 'dark' else min(l[0], l[-1])
        w = np.clip((bg - l) if kind == 'dark' else (l - bg), 0, None)
        if w.max() < 6: out.append(None); wid.append(None); continue
        w = np.where(w > 0.15 * w.max(), w, 0)
        o = (w * offs).sum() / w.sum()
        out.append(p + o * n)
        wid.append(w.sum() * res / max(w.max(), 1e-6))
    keep = [i for i, q in enumerate(out) if q is not None]
    return np.array([out[i] for i in keep]), np.array([wid[i] for i in keep])


# ---------- solving handles ----------
def bez(c, t):
    t = np.asarray(t)[:, None]; u = 1 - t
    return u ** 3 * c[0] + 3 * u * u * t * c[1] + 3 * u * t * t * c[2] + t ** 3 * c[3]


def nearest_t(c, pts, n=400):
    T = np.linspace(0, 1, n); B = bez(c, T)
    d = ((pts[:, None, :] - B[None]) ** 2).sum(2)
    k = d.argmin(1)
    return T[k], np.sqrt(d[np.arange(len(pts)), k])


def solve(p0, p3, pts, t0=None, t3=None, iters=8):
    """cubic from p0 to p3 fitted to measured pts. t0 / t3: unit tangents (t3 points backward, into
    the segment) -> only handle lengths are solved (G1); None -> that handle is free."""
    p0 = np.asarray(p0, float); p3 = np.asarray(p3, float); pts = np.asarray(pts, float)
    if len(pts) == 0:
        return np.array([p0, p0 + (p3 - p0) / 3, p3 - (p3 - p0) / 3, p3])
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([p0, pts, p3]), axis=0), axis=1))])
    u = d[1:-1] / d[-1]
    for _ in range(iters):
        b0 = (1 - u) ** 3; b1 = 3 * (1 - u) ** 2 * u; b2 = 3 * (1 - u) * u * u; b3 = u ** 3
        rhs = pts - b0[:, None] * p0 - b3[:, None] * p3
        if t0 is not None and t3 is not None:
            r2 = rhs - b1[:, None] * p0 - b2[:, None] * p3
            A = np.stack([np.concatenate([b1 * t0[0], b1 * t0[1]]), np.concatenate([b2 * t3[0], b2 * t3[1]])], 1)
            (a, b), *_ = np.linalg.lstsq(A, np.concatenate([r2[:, 0], r2[:, 1]]), rcond=None)
            c = np.array([p0, p0 + a * np.asarray(t0), p3 + b * np.asarray(t3), p3])
        elif t0 is not None:
            # unknowns: a (length along t0), P2 (x,y)
            A = np.zeros((2 * len(u), 3)); y = np.zeros(2 * len(u))
            A[:len(u), 0] = b1 * t0[0]; A[len(u):, 0] = b1 * t0[1]
            A[:len(u), 1] = b2; A[len(u):, 2] = b2
            y[:len(u)] = rhs[:, 0] - b1 * p0[0]; y[len(u):] = rhs[:, 1] - b1 * p0[1]
            (a, x2, y2), *_ = np.linalg.lstsq(A, y, rcond=None)
            c = np.array([p0, p0 + a * np.asarray(t0), [x2, y2], p3])
        elif t3 is not None:
            A = np.zeros((2 * len(u), 3)); y = np.zeros(2 * len(u))
            A[:len(u), 0] = b1; A[len(u):, 1] = b1
            A[:len(u), 2] = b2 * t3[0]; A[len(u):, 2] = b2 * t3[1]
            y[:len(u)] = rhs[:, 0] - b2 * p3[0]; y[len(u):] = rhs[:, 1] - b2 * p3[1]
            (x1, y1, b), *_ = np.linalg.lstsq(A, y, rcond=None)
            c = np.array([p0, [x1, y1], p3 + b * np.asarray(t3), p3])
        else:
            A = np.stack([b1, b2], 1)
            (P12), *_ = np.linalg.lstsq(A, rhs, rcond=None)
            c = np.array([p0, P12[0], P12[1], p3])
        u, _ = nearest_t(c, pts)
        u = np.clip(u, 1e-3, 1 - 1e-3)
    return c


def tangent_at(pts, p, r=5.0):
    """direction of the measured edge around anchor p (line fit to samples within r)."""
    pts = np.asarray(pts); m = np.linalg.norm(pts - p, axis=1) < r
    q = pts[m]
    if len(q) < 3: return None
    _, _, vt = np.linalg.svd(q - q.mean(0))
    return vt[0]


def err(c, pts):
    _, d = nearest_t(c, np.asarray(pts), 800)
    return d


class Path:
    """anchors I choose, samples for each segment, corner/smooth flags -> path dict + report."""

    def __init__(self, closed=True):
        self.A = []; self.kind = []; self.S = []; self.closed = closed; self.fixed_t = {}

    def anchor(self, p, kind='c', tangent=None):
        self.A.append(np.asarray(p, float)); self.kind.append(kind)
        if tangent is not None: self.fixed_t[len(self.A) - 1] = np.asarray(tangent, float) / np.linalg.norm(tangent)
        return self

    def samples(self, pts):
        """samples of the segment from the last anchor to the next one ('L' = straight)."""
        self.S.append(pts); return self

    def build(self):
        n = len(self.A); nseg = n if self.closed else n - 1
        allpts = np.vstack([s for s in self.S if not isinstance(s, str) and len(s)] or [np.zeros((0, 2))])
        T = {}
        for i in range(n):
            if i in self.fixed_t: T[i] = self.fixed_t[i]
            elif self.kind[i] == 's':
                t = tangent_at(allpts, self.A[i])
                nx = self.A[(i + 1) % n]; pv = self.A[i - 1]
                if t is not None and np.dot(t, nx - pv) < 0: t = -t
                T[i] = t
        ops = []; rep = []
        for j in range(nseg):
            a, b = j, (j + 1) % n
            s = self.S[j]
            if isinstance(s, str) and s == 'L':
                ops.append(['L', self.A[b].tolist()]); rep.append((0.0, 0.0, 0)); continue
            t0 = T.get(a); t3 = -T[b] if T.get(b) is not None else None
            c = solve(self.A[a], self.A[b], s, t0, t3)
            e = err(c, s)
            rep.append((float(e.max()) if len(e) else 0.0, float(e.mean()) if len(e) else 0.0, len(s)))
            ops.append(['C', c[1].tolist(), c[2].tolist(), c[3].tolist()])
        return {'start': self.A[0].tolist(), 'ops': ops, 'closed': self.closed, 'anchors': n}, rep


def seg_pts(pts, a, b):
    """samples of measured edge pts lying between anchors a and b (by projection order along pts)."""
    pts = np.asarray(pts)
    ia = np.argmin(np.linalg.norm(pts - a, axis=1)); ib = np.argmin(np.linalg.norm(pts - b, axis=1))
    lo, hi = sorted((ia, ib))
    q = pts[lo + 1:hi]
    return q if ia <= ib else q[::-1]


def line_fit(pts):
    pts = np.asarray(pts); c = pts.mean(0); _, _, vt = np.linalg.svd(pts - c)
    d = vt[0]; r = np.abs((pts - c) @ np.array([-d[1], d[0]]))
    q = pts[r < max(0.4, 2.5 * np.median(r))]
    c = q.mean(0); _, _, vt = np.linalg.svd(q - c)
    return c, vt[0], float(np.abs((q - c) @ np.array([-vt[0][1], vt[0][0]])).max())


def intersect(l1, l2):
    (c1, d1), (c2, d2) = l1[:2], l2[:2]
    t = np.linalg.solve(np.array([d1, -d2]).T, c2 - c1)
    return c1 + t[0] * d1
