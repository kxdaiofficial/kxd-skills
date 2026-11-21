"""Gate 3 — verify one section on the EXPORTED render, not on the fit report.

    python3 tools/verify.py sections/face.json checks/face-v1.png
    python3 tools/verify.py sections/face.json checks/face-v2.png --covered "1275,245;1252,396"

For every path in the section, the path itself is used as the guide: the ink-line centre (stroke objects) or the colour
edge (fill-only objects) is measured on the SOURCE and on the RENDER, and each source sample's distance to the render
is reported. Gate = p95 <= 1.0 px per object. Samples > 1.5 px are listed by position: they are almost always at a
junction or an end routed under a front object (on an approved face: p95 0.57-0.75, max 2.7-4.0 at the
collar / strap). They are merged by position into a few spots L1, L2 ... and drawn as small source|render tiles in ONE
image, <render>-look.png: open that and say for each id which it is; a real miss there is still a fix. Also writes the
whole part at 100 % (<render>-side-100.png); the whole part at 400 % only with --full.
A fill edge is only compared where it is VISIBLE in the source: one side of it (2.5 px along the normal) must be the
fill's own colour. Edges routed under hair / collar / any front object are skipped and counted as 'hidden' — so a part
can be checked before the parts in front of it exist.
--covered: points you have LOOKED AT in the -side-400 crop and found to be under a front object (or a part not drawn
yet). Samples within 4 px are left out of the gate. Every covered point goes in the report with what covers it."""
import sys, os, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand as h
from measure import line_c, edge_auto, check_img
from sheet import cluster, sheet, MAX_TILES

P95_LIMIT = 1.0   # px — object FAILS the gate above this
LOOK = 1.5        # px — samples above this are listed for a 400 % look


def sample_path(p, step=2.0):
    pts = [np.asarray(p['start'], float)]
    for op in p['ops']:
        a = pts[-1]
        if op[0] == 'L':
            b = np.asarray(op[1], float); n = max(1, int(np.linalg.norm(b - a) / step))
            pts += [a + (b - a) * k / n for k in range(1, n + 1)]
        else:
            c = np.array([a, op[1], op[2], op[3]], float)
            L = sum(np.linalg.norm(np.diff(c, axis=0), axis=1)); n = max(2, int(L / step))
            pts += list(h.bez(c, np.linspace(0, 1, n + 1)[1:]))
    return np.array(pts)


def visible(pts, guide, fill, off=2.5, tol=30):
    """True where one side of the edge is the fill colour in the source (the edge is not under a front object)."""
    N = h.normals(guide); fill = np.asarray(fill, float); out = []
    for p in pts:
        n = N[np.argmin(np.linalg.norm(guide - p, axis=1))]
        a = h.at(*(p + off * n)); b = h.at(*(p - off * n))
        out.append(min(np.abs(a - fill).max(), np.abs(b - fill).max()) < tol)
    return np.array(out, bool)


def walk(objs):
    for o in objs:
        yield o
        yield from walk(o.get('children', []))


def main(sec_path, render_path, covered=(), pad=12, full=False):
    S = json.load(open(sec_path))
    R = check_img(render_path)
    if R.shape[:2] != h.IMG.shape[:2]:
        sys.exit('render %s is %dx%d but source is %dx%d — export at 100 %% of the source size' %
                 (render_path, R.shape[1], R.shape[0], h.W, h.H))
    allpts = []; fails = 0; lookp = []; lookd = []; lookn = []
    print('%-44s %-5s %6s %6s %6s %5s' % ('object', 'kind', 'p95', 'mean', 'max', 'n'))
    for o in walk(S['objects']):
        for p in (o.get('paths') or [o['path']]):
            G = sample_path(p); allpts.append(G)
            hidden = 0
            if o.get('stroke'):
                kind = 'line'
                src, _, _ = line_c(G, r=3.0); ren, _, _ = line_c(G, r=3.0, img=R)
            else:
                kind = 'edge'
                src, ok = edge_auto(G, r=4.0); src = src[ok]
                hidden = 0
                if len(src) and o.get('fill'):
                    v = visible(src, G, o['fill']); hidden = int((~v).sum()); src = src[v]
                ren, ok = edge_auto(G, r=4.0, img=R); ren = ren[ok]
            if len(src) == 0:
                print('%-44s %-5s %6s %6s %6s %5d  (nothing visible on source)' % (o['name'][:44], kind, '-', '-', '-', 0)); continue
            if len(ren) == 0:
                print('%-44s %-5s %6s %6s %6s %5d  FAIL — missing on render' % (o['name'][:44], kind, '-', '-', '-', len(src))); fails += 1; continue
            if len(covered):
                keep = np.array([np.min(np.linalg.norm(covered - q, axis=1)) > 4.0 for q in src]); src = src[keep]
                if not len(src): continue
            d = np.array([np.min(np.linalg.norm(ren - q, axis=1)) for q in src])
            p95 = np.percentile(d, 95); bad = p95 > P95_LIMIT; fails += bad
            print('%-44s %-5s %6.2f %6.2f %6.2f %5d%s%s' % (o['name'][:44], kind, p95, d.mean(), d.max(), len(d),
                  '  (%d hidden skipped)' % hidden if kind == 'edge' and hidden else '', '  FAIL' if bad else ''))
            k = np.where(d > LOOK)[0]
            lookp.append(src[k]); lookd.append(d[k]); lookn += [o['name']] * len(k)
    P = np.vstack(allpts)
    x0, y0 = np.maximum(np.floor(P.min(0)) - pad, 0).astype(int)
    x1, y1 = np.minimum(np.ceil(P.max(0)) + pad, [h.W, h.H]).astype(int)
    src = Image.fromarray(h.IMG[y0:y1, x0:x1].astype(np.uint8)); ren = Image.fromarray(R[y0:y1, x0:x1].astype(np.uint8))
    base = os.path.splitext(render_path)[0]
    for z in ((1, 4) if full else (1,)):
        w, hh = src.width * z, src.height * z
        side = Image.new('RGB', (w * 2 + 8, hh), (255, 0, 255))
        side.paste(src.resize((w, hh), Image.NEAREST), (0, 0)); side.paste(ren.resize((w, hh), Image.NEAREST), (w + 8, 0))
        side.save('%s-side-%d00.png' % (base, z))
    print('\ncrop box', [int(v) for v in (x0, y0, x1, y1)], '-> %s-side-100.png%s (left = source, right = render)' %
          (base, ' / -side-400.png' if full else ''))
    # look points: merged by position, worst first, one small tile each in ONE image
    LP = np.vstack(lookp) if lookp else np.zeros((0, 2)); LD = np.concatenate(lookd) if lookd else np.zeros(0)
    C = cluster(LP, LD)
    if C:
        print('\nlook at (open %s-look.png; answer each id: junction OK / covered by <part> / real miss):' % base)
        for n, (x, y, w, m) in enumerate(C[:MAX_TILES]):
            names = sorted({lookn[i] for i in np.where(np.linalg.norm(LP - [x, y], axis=1) <= 8.0)[0]})
            print('  L%d (%.0f, %.0f) worst %.1f px, %d samples — %s' % (n + 1, x, y, w, m, ', '.join(names)[:70]))
        sheet(C[:MAX_TILES], R, base + '-look.png')
        if len(C) > MAX_TILES:
            print('  ... %d more spots not drawn. That many misses means the anchors are off: fix the worst objects and'
                  ' re-run before looking.' % (len(C) - MAX_TILES))
    if fails:
        print('RESULT: %d object(s) FAIL (p95 > %.1f px). Fix anchors first; looking at images can wait.' % (fails, P95_LIMIT))
    elif C:
        print('RESULT: PASS on numbers. Open %s-look.png (%d spots) and -side-100.png once; nothing else.' % (base, min(len(C), MAX_TILES)))
    else:
        print('RESULT: PASS, no look spots. Open %s-side-100.png once.' % base)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser(); a.add_argument('section'); a.add_argument('render'); a.add_argument('--covered', default='')
    a.add_argument('--full', action='store_true', help='also write the whole-part -side-400.png (costly to open; only when asked)')
    o = a.parse_args()
    cov = np.array([[float(v) for v in c.split(',')] for c in o.covered.split(';') if c.strip()]).reshape(-1, 2)
    if len(cov): print('covered (left out of the gate):', '; '.join('(%g, %g)' % tuple(c) for c in cov))
    main(o.section, o.render, cov, full=o.full)
