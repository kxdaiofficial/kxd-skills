"""Assembly helper (main session only): sections -> one SVG at source size, one <g> per section, objects in file order.
Usage: python3 tools/section_svg.py out.svg sections/03_shoes.json [...]"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from section_d import d_of, hexc   # noqa: E402  (same folder)
import hand as h                   # source size comes from source.png, never typed

out, secs = sys.argv[1], sys.argv[2:]
xid = lambda s: s.replace('&', '&amp;').replace('"', '&quot;')   # vector apps keep the id text as the layer name
L = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (h.W, h.H, h.W, h.H)]
for s in secs:
    sec = json.load(open(s))
    L.append('<g id="%s">' % xid(sec['section']))
    for o in sec['objects']:
        a = 'fill="%s" stroke="none"' % hexc(o['fill']) if 'fill' in o else \
            'fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"' % (hexc(o['stroke']), o['width'])
        L.append('<path id="%s" %s d="%s"/>' % (xid(o['name']), a, d_of(o['path'])))
    L.append('</g>')
L.append('</svg>')
open(out, 'w').write('\n'.join(L)); print(out)
