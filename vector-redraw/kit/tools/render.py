"""Render of section JSONs (no vector app needed): back to front in the order given, 4x supersampled, on white.
This is the Gate 3 render. If you also open the SVG in a vector app, its PNG export can be checked the same way.
Usage: python3 tools/render.py out.png sections/01_ponytail.json sections/03_shoes.json ...   (list them back -> front)"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand as h

SS = 4


def flat(path, n=32):
    cur = np.array(path['start'], float); pts = [cur]
    for q in path['ops']:
        if q[0] == 'L': cur = np.array(q[1], float); pts.append(cur)
        else:
            c = np.array([cur, q[1], q[2], q[3]], float); pts += list(h.bez(c, np.linspace(0, 1, n))[1:]); cur = c[3]
    return np.array(pts)


def draw(img, o):
    d = ImageDraw.Draw(img)
    P = flat(o['path']) * SS
    pts = [tuple(p) for p in P]
    if 'fill' in o:
        d.polygon(pts, fill=tuple(o['fill']))
    else:
        w = max(1, int(round(o['width'] * SS))); col = tuple(o['stroke'])
        if o['path'].get('closed'): pts = pts + [pts[0]]
        d.line(pts, fill=col, width=w, joint='curve')
        r = w / 2
        for p in (pts[0], pts[-1]): d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)


def render(out, secs):
    img = Image.new('RGB', (h.W * SS, h.H * SS), (255, 255, 255))
    for s in secs:
        for o in json.load(open(s))['objects']: draw(img, o)
    img.resize((h.W, h.H), Image.LANCZOS).save(out)


if __name__ == '__main__':
    secs = sys.argv[2:]
    if secs == ['--all']:   # every section listed in sections/ZORDER.txt that exists, in that order
        root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sections')
        names = [l.strip() for l in open(os.path.join(root, 'ZORDER.txt')) if l.strip() and not l.startswith('#')]
        secs = [os.path.join(root, n + '.json') for n in names if os.path.exists(os.path.join(root, n + '.json'))]
    render(sys.argv[1], secs); print(sys.argv[1], len(secs), 'sections')
