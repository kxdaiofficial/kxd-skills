"""Small source | render crops around a few points, in ONE image. This is what you open instead of a whole-part 400 % crop:
the numbers already say where to look, so only those spots cost image tokens.

    from sheet import cluster, sheet
    C = cluster(points, dists)            # [(x, y, worst, n), ...] worst first, points within 8 px merged
    sheet(C[:12], render_array, 'checks/03-v2-look.png')

Each tile = source (left) | render (right) of a 28 px box at 6x, labelled with its id (L1, L2 ...) and the centre."""
import numpy as np
from PIL import Image, ImageDraw
import hand as h

MAX_TILES = 12


def cluster(pts, d, r=8.0):
    """greedy: worst sample first, swallow every sample within r px. Returns [(x, y, worst, n)] sorted worst first."""
    pts = np.asarray(pts, float).reshape(-1, 2); d = np.asarray(d, float)
    left = np.argsort(-d); used = np.zeros(len(d), bool); out = []
    for i in left:
        if used[i]: continue
        near = (~used) & (np.linalg.norm(pts - pts[i], axis=1) <= r)
        used |= near
        out.append((float(pts[i][0]), float(pts[i][1]), float(d[i]), int(near.sum())))
    return out


def sheet(C, R, out, box=28, k=6, cols=3, tag='L'):
    """C from cluster(); R = render array (same size as the source). Writes out, returns its path (None if C is empty)."""
    if not len(C): return None
    t = box * k; tw, th = t * 2 + 4, t + 14; rows = (len(C) + cols - 1) // cols
    img = Image.new('RGB', (tw * min(cols, len(C)) + 6 * (min(cols, len(C)) - 1), th * rows + 6 * (rows - 1)), (255, 255, 255))
    for n, (x, y, w, _) in enumerate(C):
        x0 = int(np.clip(round(x) - box // 2, 0, h.W - box)); y0 = int(np.clip(round(y) - box // 2, 0, h.H - box))
        s = Image.fromarray(h.IMG[y0:y0 + box, x0:x0 + box].astype(np.uint8)).resize((t, t), Image.NEAREST)
        r = Image.fromarray(np.asarray(R)[y0:y0 + box, x0:x0 + box].astype(np.uint8)).resize((t, t), Image.NEAREST)
        tile = Image.new('RGB', (tw, th), (255, 0, 255)); tile.paste(s, (0, 14)); tile.paste(r, (t + 4, 14))
        dr = ImageDraw.Draw(tile); dr.rectangle([0, 0, tw, 13], fill=(255, 255, 255))
        dr.text((2, 1), '%s%d (%.0f,%.0f) %.1f' % (tag, n + 1, x, y, w), fill=(0, 0, 0))
        cx, cy = (x - x0) * k, (y - y0) * k + 14     # cross-hair on the point, both halves
        for ox in (0, t + 4):
            dr.line([(ox + cx - 5, cy), (ox + cx + 5, cy)], fill=(0, 200, 255)); dr.line([(ox + cx, cy - 5), (ox + cx, cy + 5)], fill=(0, 200, 255))
        img.paste(tile, ((n % cols) * (tw + 6), (n // cols) * (th + 6)))
    img.save(out)
    return out
