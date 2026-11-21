"""Print each object of a section JSON as {name, d, fill|stroke, width} for draw_path.
Usage: python3 tools/section_d.py sections/<part>.json"""
import sys, json


def d_of(p):
    f = lambda v: '%.2f %.2f' % (v[0], v[1])
    s = ['M' + f(p['start'])]
    for q in p['ops']:
        s.append(('L' + f(q[1])) if q[0] == 'L' else ('C' + ' '.join(f(v) for v in q[1:])))
    return ' '.join(s) + (' Z' if p.get('closed') else '')


hexc = lambda c: '#%02x%02x%02x' % tuple(c)

if __name__ == '__main__':
    sec = json.load(open(sys.argv[1]))
    out = []
    for o in sec['objects']:
        e = {'name': o['name'], 'd': d_of(o['path'])}
        if 'fill' in o: e.update(fill=hexc(o['fill']), stroke='none')
        else: e.update(fill='none', stroke=hexc(o['stroke']), strokeWidth=o['width'])
        out.append(e)
    print(json.dumps({'section': sec['section'], 'objects': out}))
