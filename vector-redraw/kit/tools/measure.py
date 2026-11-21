import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, hand as h
def edge_auto(guide, r=4.0, step=1.5, res=0.1, chan=None, inner=None, outer=None, img=None, minc=60):
    """half-way crossing between the two end colours of each normal profile (inner end = dark side unless given).
    Measurement only, along MY guide."""
    P = h.densify(guide, step); N = h.normals(P); offs = np.arange(-r, r + res/2, res)
    out=[]; ok=[]
    for p,n in zip(P,N):
        Q=p[None]+offs[:,None]*n[None]; c=h.at(Q[:,0],Q[:,1]) if img is None else h.at(Q[:,0],Q[:,1],img)
        v = c.sum(1) if chan is None else c[:,chan]
        a = np.median(v[:8]); b = np.median(v[-8:])
        if abs(b-a) < minc: out.append(p); ok.append(False); continue
        t=(v-a)/(b-a); s=np.sign(t-0.5); idx=np.where(np.diff(s)!=0)[0]
        if len(idx)==0: out.append(p); ok.append(False); continue
        k=idx[np.argmin(np.abs(offs[idx]))]; f=(0.5-t[k])/(t[k+1]-t[k]+1e-12)
        out.append(p+(offs[k]+f*res)*n); ok.append(True)
    return np.array(out), np.array(ok)

def nearest_i(P, p): return int(np.argmin(np.linalg.norm(P - np.asarray(p, float), axis=1)))

def cusp(P, approx, r0=1.2, r1=5.0):
    """corner point = intersection of straight-line fits to the samples just before / after the corner (by sample order)."""
    i = nearest_i(P, approx); d = np.linalg.norm(P - P[i], axis=1)
    idx = np.arange(len(P))
    before = P[(idx < i) & (d > r0) & (d < r1)]; after = P[(idx > i) & (d > r0) & (d < r1)]
    return h.intersect(h.line_fit(before), h.line_fit(after))

def run_fit(P, anchors, kinds, tan=None, idx=None):
    """P ordered samples of ONE visible run; anchors (points, chosen by me) with kinds 's' (G1 via measured tangent) / 'c'.
    Returns ctrls list and report per segment (max, mean, n)."""
    tan = tan or {}
    A = [np.asarray(a, float) for a in anchors]; idx = idx or [nearest_i(P, a) for a in A]
    T = []
    for k, a in enumerate(A):
        if k in tan: t = np.asarray(tan[k], float); T.append(t / np.linalg.norm(t)); continue
        if kinds[k] != 's': T.append(None); continue
        t = h.tangent_at(P, a, 4.0)
        prv = A[k - 1] if k > 0 else a; nxt = A[k + 1] if k + 1 < len(A) else a
        if t is None: t = (nxt - prv) / (np.linalg.norm(nxt - prv) + 1e-9); print('  [note] smooth anchor with few nearby samples at', np.round(a, 1))
        if t @ (nxt - prv) < 0: t = -t
        T.append(t)
    C = []; rep = []
    for j in range(len(A) - 1):
        lo, hi = idx[j], idx[j + 1]
        s = P[lo + 1:hi] if hi > lo else P[0:0]
        s = s[(np.linalg.norm(s - A[j], axis=1) > 0.3) & (np.linalg.norm(s - A[j + 1], axis=1) > 0.3)]
        c = h.solve(A[j], A[j + 1], s, T[j], (-T[j + 1]) if T[j + 1] is not None else None)
        e = h.err(c, s) if len(s) else np.zeros(1)
        C.append(c); rep.append((round(float(e.max()), 2), round(float(e.mean()), 2), len(s)))
    return C, rep

def handle_check(C):
    """flags degenerate / crossing handles: returns list of (seg, ratio0, ratio1) where handle len/chord outside [0.05,0.75]"""
    bad = []
    for j, c in enumerate(C):
        ch = np.linalg.norm(c[3] - c[0]) + 1e-9
        r0 = np.linalg.norm(c[1] - c[0]) / ch; r1 = np.linalg.norm(c[2] - c[3]) / ch
        if not (0.03 < r0 < 0.8 and 0.03 < r1 < 0.8): bad.append((j, round(r0, 2), round(r1, 2)))
    return bad

def ops_of(C): return [['C', c[1].tolist(), c[2].tolist(), c[3].tolist()] for c in C]
def rgb(c): return [int(round(v)) for v in c]

def check_img(path=os.path.join(h.JOB, 'checks', 'check.png'), bg=(255, 255, 255)):
    from PIL import Image
    m = Image.open(path).convert('RGBA'); b = Image.new('RGBA', m.size, bg + (255,)); b.alpha_composite(m)
    return np.asarray(b.convert('RGB')).astype(np.float32)

def reverify(guide, src_pts, img, r=5, **kw):
    """re-measure my guide on the exported render and report the distance from each source sample to the render's edge."""
    Q, ok = edge_auto(guide, r=r, img=img, **kw)
    Q = Q[ok]
    d = np.array([np.min(np.linalg.norm(Q - p, axis=1)) for p in src_pts])
    return d

def line_c(guide, r=2.5, step=1.5, res=0.1, chan=None, kind='dark', img=None):
    """centre + width of a thin ink line near my guide. bg = the NEARER-to-ink of the two profile ends, so a line between two
    different light areas (skin | white) is not pulled toward the darker area. Returns pts, widths, depth."""
    A = h.IMG if img is None else img
    Lg = (A[..., 0] * 0.299 + A[..., 1] * 0.587 + A[..., 2] * 0.114) if chan is None else A[..., chan]
    P = h.densify(guide, step); N = h.normals(P); offs = np.arange(-r, r + res / 2, res)
    out = []; wid = []; dep = []
    for p, n in zip(P, N):
        Q = p[None] + offs[:, None] * n[None]; l = h.at(Q[:, 0], Q[:, 1], Lg)
        e0 = np.median(l[:5]); e1 = np.median(l[-5:])
        bg = min(e0, e1) if kind == 'dark' else max(e0, e1)
        w = np.clip((bg - l) if kind == 'dark' else (l - bg), 0, None)
        if w.max() < 8: continue
        w = np.where(w > 0.2 * w.max(), w, 0)
        out.append(p + ((w * offs).sum() / w.sum()) * n); wid.append(w.sum() * res / w.max()); dep.append(w.max())
    return np.array(out), np.array(wid), np.array(dep)


def ridge(guide, r=2.5, step=1.0, res=0.1, kind='light', img=None):
    """centre of a FAINT line (contrast < line_c's threshold): per normal profile along MY guide, the extreme of the luminance
    (max for light, min for dark), refined by a parabola. Returns pts, depth (vs the profile's median)."""
    A = h.IMG if img is None else img
    P = h.densify(guide, step); N = h.normals(P); offs = np.arange(-r, r + res / 2, res)
    out = []; dep = []
    for p, n in zip(P, N):
        Q = p[None] + offs[:, None] * n[None]; c = h.at(Q[:, 0], Q[:, 1], A)
        L = c @ np.array([0.299, 0.587, 0.114]); L = L if kind == 'light' else -L
        k = int(np.argmax(L)); f = 0.0
        if 0 < k < len(L) - 1:
            a, b, d = L[k - 1], L[k], L[k + 1]; den = a - 2 * b + d
            if den < 0: f = 0.5 * (a - d) / den
        out.append(p + (offs[k] + f * res) * n); dep.append(L[k] - np.median(L))
    return np.array(out), np.array(dep)
