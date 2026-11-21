"""side.py render.png out.png x0,y0,x1,y1 [x0,y0,x1,y1 ...] — stacked rows of source | render crops at --k (default 6)."""
import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, 'tools')
from measure import check_img
import hand as h
args = [a for a in sys.argv[1:] if not a.startswith('--')]
k = int(next((a[4:] for a in sys.argv if a.startswith('--k=')), 6))
R = check_img(args[0]); out = args[1]; rows = []
for b in args[2:]:
    x0, y0, x1, y1 = map(int, b.split(','))
    s = Image.fromarray(h.IMG[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * k, (y1 - y0) * k), Image.NEAREST)
    r = Image.fromarray(R[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * k, (y1 - y0) * k), Image.NEAREST)
    row = Image.new('RGB', (s.width * 2 + 6, s.height + 14), (255, 0, 255)); row.paste(s, (0, 14)); row.paste(r, (s.width + 6, 14))
    ImageDraw.Draw(row).text((2, 1), b, fill=(0, 0, 0)); rows.append(row)
W = max(r.width for r in rows); H = sum(r.height for r in rows) + 4 * len(rows)
img = Image.new('RGB', (W, H), (255, 255, 255)); y = 0
for r in rows: img.paste(r, (0, y)); y += r.height + 4
img.save(out); print(out, img.size)
