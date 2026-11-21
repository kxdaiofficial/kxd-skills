"""Gridded zoom of the source — where YOU read anchor and guide coordinates. Optionally overlays a section's paths.

    python3 tools/zoom.py 1150 210 1330 410                      # 8x, grid every 5 px, labels every 10
    python3 tools/zoom.py 1150 210 1330 410 --k 12 --section sections/face.json --out checks/face-zoom.png

Grid: yellow every `grid` px, red every 50, labels = source px. Pixel i spans [i, i+1]; a grid line at 1200 is the
LEFT edge of pixel 1200, so the centre of that pixel is 1200.5. Overlay: magenta = path, cyan circle = anchor.
Output is capped at --max 512 px (a 64 px box at 8x): zoom the corners, junctions and tips; read long lines as text
with tools/runs.py / tools/lmap.py. --overview shows a whole part small, for layout only."""
import sys, os, argparse
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand as h


def pts_of(path, n=24):
    cur = np.array(path['start'], float); out = [cur]; anc = [cur]
    for q in path['ops']:
        if q[0] == 'L': cur = np.array(q[1], float); out.append(cur)
        else:
            c = np.array([cur, q[1], q[2], q[3]], float); out += list(h.bez(c, np.linspace(0, 1, n))[1:]); cur = c[3]
        anc.append(cur)
    if path.get('closed'): out.append(out[0])
    return np.array(out), np.array(anc)


def view(box, k=8, grid=5, objs=(), out=None):
    x0, y0, x1, y1 = box
    im = Image.fromarray(h.IMG.astype(np.uint8)).crop(box).resize(((x1 - x0) * k, (y1 - y0) * k), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for x in range((x0 // grid + 1) * grid, x1, grid):
        X = (x - x0) * k; d.line([(X, 0), (X, im.height)], fill=(255, 0, 0) if x % 50 == 0 else (255, 220, 0))
        if x % (10 if k >= 4 else 50) == 0: d.text((X + 2, 2), str(x), fill=(255, 0, 0))
    for y in range((y0 // grid + 1) * grid, y1, grid):
        Y = (y - y0) * k; d.line([(0, Y), (im.width, Y)], fill=(255, 0, 0) if y % 50 == 0 else (255, 220, 0))
        if y % (10 if k >= 4 else 50) == 0: d.text((2, Y + 2), str(y), fill=(255, 0, 0))
    for o in objs:
        for p in (o.get('paths') or [o['path']]):
            P, A = pts_of(p)
            d.line([tuple((q - [x0, y0]) * k) for q in P], fill=(255, 0, 255), width=1)
            for a in A:
                X, Y = (a - [x0, y0]) * k; d.ellipse([X - 4, Y - 4, X + 4, Y + 4], outline=(0, 255, 255))
    out = out or os.path.join(h.JOB, 'checks', 'zoom-%d-%d-%d-%d.png' % box)
    os.makedirs(os.path.dirname(out), exist_ok=True); im.save(out); print(out, im.size)
    return out


if __name__ == '__main__':
    import json
    a = argparse.ArgumentParser(); a.add_argument('box', type=int, nargs=4); a.add_argument('--k', type=int, default=8)
    a.add_argument('--grid', type=int, default=5); a.add_argument('--section'); a.add_argument('--out')
    a.add_argument('--max', type=int, default=512, help='longest side of the output image, px (image tokens grow with pixels)')
    a.add_argument('--overview', action='store_true', help='fit the box into --max at any k, grid 10 (layout only, not for coordinates)')
    o = a.parse_args()
    bw, bh = o.box[2] - o.box[0], o.box[3] - o.box[1]
    if o.overview:
        o.k = max(1, o.max // max(bw, bh)); o.grid = max(o.grid, 10)
    elif max(bw, bh) * o.k > o.max:
        k = o.max // max(bw, bh)
        if k < 8:
            sys.exit('box %dx%d at 8x is %d px > --max %d. Zoom only the corner / junction / tip (<= %d px box), read long lines'
                     ' with tools/runs.py or tools/lmap.py (text), or use --overview for layout.' %
                     (bw, bh, max(bw, bh) * 8, o.max, o.max // 8))
        print('k %d -> %d to stay within %d px' % (o.k, k, o.max)); o.k = k
    objs = []
    if o.section:
        def walk(L):
            for x in L: yield x; yield from walk(x.get('children', []))
        objs = list(walk(json.load(open(o.section))['objects']))
    view(tuple(o.box), o.k, o.grid, objs, o.out)
