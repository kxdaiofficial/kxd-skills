"""gmap.py x0 y0 x1 y1 [chan] — ASCII map of one channel (default green): '#'<100 '%'<112 '+'<124 '-'<132 ' '<160 '.' else.
Helper added by part 21 for dark-pink-on-pink lines (pink G 136). Measurement only."""
import sys; sys.path.insert(0, 'tools'); import hand as h
x0, y0, x1, y1 = map(int, sys.argv[1:5]); ch = int(sys.argv[5]) if len(sys.argv) > 5 else 1
G = h.IMG[..., ch]
print('     ' + ''.join(str((x // 10) % 10) if x % 10 == 0 else ' ' for x in range(x0, x1)))
print('     ' + ''.join(str(x % 10) for x in range(x0, x1)))
for y in range(y0, y1):
    print('%4d ' % y + ''.join('#' if v < 100 else '%' if v < 112 else '+' if v < 124 else '-' if v < 132 else ' ' if v < 160 else '.' for v in G[y, x0:x1]))
