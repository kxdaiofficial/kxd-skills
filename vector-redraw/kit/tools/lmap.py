"""lmap.py x0 y0 x1 y1 — ASCII luminance map (one char per pixel, pixel i shown at column i): '#'<110 '%'<140 '+'<165 '-'<190 '.'<215 ' ' else.
Helper added by part 21 (reading pixel positions for guides; measurement only)."""
import sys, numpy as np
sys.path.insert(0, 'tools'); import hand as h
x0, y0, x1, y1 = map(int, sys.argv[1:5])
L = h.IMG[..., 0] * .299 + h.IMG[..., 1] * .587 + h.IMG[..., 2] * .114
print('     ' + ''.join(str((x // 10) % 10) if x % 10 == 0 else ' ' for x in range(x0, x1)))
print('     ' + ''.join(str(x % 10) for x in range(x0, x1)))
for y in range(y0, y1):
    print('%4d ' % y + ''.join('#' if v < 110 else '%' if v < 140 else '+' if v < 165 else '-' if v < 190 else '.' if v < 215 else ' ' for v in L[y, x0:x1]))
