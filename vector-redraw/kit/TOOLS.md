# Tools: what to call (do NOT open the source files)

Everything you need is on this page. Reading `tools/*.py` costs tokens and teaches nothing the signatures below do not.
Run from the job folder with `python3`. Coordinates are source px; pixel i spans [i, i+1], its centre is i + 0.5.

## Where coordinates come from: text first, images only for corners
| Command | Output | Use for |
|---|---|---|
| `tools/runs.py x0 y0 x1 y1 [thr] [--cols] [--chan=N]` | per row (or column): centre(min L) of every dark run | placing guides along long lines. Inside a dark fill (hair) the default threshold returns the whole mass: lower `thr` (e.g. 60) to get the line |
| `tools/lmap.py x0 y0 x1 y1` | ASCII luminance map, one char per px, axis labels | shapes, ends of lines, what is where (keep boxes ≤ 80×60) |
| `tools/gmap.py x0 y0 x1 y1 [chan]` | same, one channel | dark line on a dark fill (e.g. navy on navy) |
| `tools/zoom.py x0 y0 x1 y1 [--k 8] [--section S.json] [--out f]` | gridded PNG, capped at 512 px (box ≤ 64 px at 8×) | corners, junctions, tips, Gate 1 overlay. Refuses a bigger box: split it |
| `tools/zoom.py … --overview` | whole box ≤ 512 px, grid 10 | layout only, never for coordinates |

## In a part script (`from measure import *` gives `h`, `np` and these)
| Call | Returns | Note |
|---|---|---|
| `line_c(G, r=2.5, kind='dark', chan=None, img=None)` | `P, W, D` centres, widths, depth | ink line along guide G (list of (x, y)) |
| `ridge(G, r=2.5, kind='light')` | `P, depth` | faint line (contrast < ~40) that line_c drops. No width: take the stroke width from `line_c` on the same line |
| `edge_auto(G, r=4, chan=None, inner=None, outer=None)` | `P, ok` (use `P[ok]`) | colour edge (fill boundary) along G |
| `h.edge(G, cA, cB, r=4)` | `P` | edge between two known colours |
| `cusp(P, (x, y))` | point | exact corner = intersection of the two sides near (x, y). Needs measured samples 1.2–5 px from the corner on BOTH sides (a gap there raises `zero-size array`): measure closer or pick the corner from a zoom |
| `run_fit(P, anchors, kinds, tan=None, idx=None)` | `C, report` | kinds `'c'` corner / `'s'` smooth; report = (max, mean, n) per segment (Gate 2). Closed loops: pass `idx` = the sample index of each anchor (incl. the closing one), or a segment gets n = 0 |
| `handle_check(C)` | list of (seg, ratio0, ratio1) | flags a handle shorter than 0.05 or longer than 0.75 of its chord: re-pick anchors. A very short tail (≤ ~3 px) can be a straight `L` instead |
| `ops_of(C)` · `rgb(c)` · `h.colour(x0, y0, x1, y1)` | path ops · int colour · median colour of a box | colours always sampled |
| `poly.polygon_c(corners, kinds)` | clean polygon | rigid objects; kinds per side `v h s x` |
| `fitcheck.try_anchors(P, A0, t0, mids, A1)` | fit for trial anchor picks | testing picks on one run |
| `rays.rays(c, col)` · `vbound.bounds(x, y0, y1)` · `cloudtools.scan/fit_bumps` | radial edge · column boundaries · bumpy edges | special shapes |

## Checking
| Command | Output | Open |
|---|---|---|
| `tools/render.py checks/NN-vK.png --all` | render of every section in ZORDER.txt that exists (this is the Gate 3 render) | nothing |
| `tools/verify.py sections/NN.json checks/NN-vK.png [--covered "x,y;x,y"] [--full]` | p95/mean/max per object, look spots L1…, RESULT line | `-look.png` (only if PASS on numbers) + `-side-100.png` once. `--full` adds a 400 % crop: only when the user asks |
| `tools/hotspots.py checks/NN-vK.png [--box x0,y0,x1,y1] [--top 12] [--thr 60]` | mean, p95, % > 60, spots H1… ranked | `-hot.png` |
| `tools/side.py render out.png x0,y0,x1,y1 … --k=4` | source \| render rows for boxes you name | only for a spot the numbers did not cover |

## Path format (section JSON)
`{"group", "section", "objects": [{"name", "fill": [r,g,b] | "stroke": [r,g,b], "width", "path": {"start": [x,y], "ops": [["C",[x1,y1],[x2,y2],[x3,y3]] | ["L",[x,y]], …], "closed": bool}}]}` · `ops_of(C)` writes the ops for you.

## Gotchas
- `-look.png` / `-side-100.png` are named after the RENDER file. Checking two sections against one render overwrites the first one's sheet: render once per part (`checks/<NN>-vK.png`).
- A fill that runs to the edge of the picture: `verify.py` also measures the canvas border, so spots there are not real misses; open the look sheet, confirm, and pass them with `--covered`.
- If every failing sample sits under a part not drawn yet or on the canvas border, you may open `-look.png` to confirm that before using `--covered`.
- A version counts toward the 3-version cap when it was rendered and checked; a run that crashed does not.
- A real miss in a back part that is already at v3 may be fixed by a front object in a later part (e.g. a skin patch in front of the hair). Say so in both reports.

## Output
`scripts/export-svg.sh redraw.svg` → one SVG of every section in ZORDER order, one `<g>` per section, every path named.
`tools/section_d.py S.json` prints each object as `{name, d, fill|stroke, width}` if you push objects into a vector app one by one.
