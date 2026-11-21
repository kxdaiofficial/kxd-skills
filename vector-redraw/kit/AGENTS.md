# Hand-redraw a raster picture as vector: rules for this job folder

**Goal:** redraw `source.png` (an illustration, character, icon, scene) as clean paths a person can edit, matching the source to about 1 px, and deliver one SVG.
**Method in one sentence:** **you decide every anchor from text tables and gridded zooms; code only *measures* along your guides and *solves* handle lengths; you verify with numbers on the rendered result.**

---

## Hard rules: breaking one means stop and redo the part

1. **No tracing of any kind.** Banned: Illustrator Image Trace, Inkscape Trace Bitmap, potrace, vtracer, `cv2.findContours`, k-means colour regions turned into contours, online vectorisers, any image model that "generates an SVG" (it makes new art, it does not redraw this picture), and any home-made pipeline that decides shapes from pixels. Automation may MEASURE and SOLVE. It never decides where a shape or an anchor goes. If the user asks for a tracer, say once that this skill redraws by hand and ask before doing anything else.
2. **No coordinates from memory or from a downscaled look.** Every guide and anchor is read off a text table (`tools/runs.py`, `lmap.py`, `gmap.py`), a gridded zoom (`tools/zoom.py`, ≥ 8×) or comes out of a measurement (`cusp()`, a measured sample). Every colour is **sampled** (`h.colour(box)` inside the flat area). Never type an eyeballed hex or coordinate.
3. **One part at a time.** Never write the whole picture in one go. The first 1–2 parts: pass the gates, show the user, **wait for OK** (this sets the style). After that, continue part by part with one review at the end, unless the user asked to approve every part.
4. **Structure of every object:** a **fill with no stroke**, plus a **separate stroke object for each visible ink line**, ordered back to front in the section JSON. Where a fill edge is hidden under a front object, route it freely underneath. Do not try to match an edge nobody can see.
5. **Pixel convention:** pixel *i* covers [i, i+1], so its centre is **i + 0.5**. The tools already work this way. Add 0.5 yourself only when you turn an array index (`img[y, x]`) into a coordinate. Skipping it shifts every line by 0.5–1 px.
6. **Never claim "matches" or ✅ for a region you have not looked at at 100 % or more.** Say "not checked at 100 %" instead.
7. **Numbers first, images only where the numbers point.** Every image you open stays in context and is paid for again on every later step. Open: small zooms of corners / junctions / tips, the `-look.png` and `-hot.png` sheets, `-side-100.png` once per version. Do not open `tools/*.py` (signatures are in `TOOLS.md`), and do not open an image while a gate is still failing on numbers.
8. **At most 3 versions per part.** If v3 still fails a gate, stop: report the failing objects, their p95, the look spots with coordinates, and what you think the cause is.

## At the start of every session, and again after every context compaction
Read `progress.md`. It is the job's memory: trust it over what you think you remember.

## Setup (once per job)
1. `source.png` sits in the job root at **full original resolution** (never a screenshot or a resized copy). Its size is in `progress.md`.
2. Look at the whole picture once with `python3 tools/zoom.py 0 0 <W> <H> --overview`.
3. Split it into **parts, ordered back to front** (e.g. background → hair-back → face → hair-front → body → hands → props), each with a box. Write the list into `progress.md` and the section names into `sections/ZORDER.txt` (one per line, back → front). **Show the list to the user before drawing.**

## Per-part loop

| # | Step | Tool | Pass condition |
|---|---|---|---|
| 1 | Read the part as text: `runs.py` along each long line, `lmap.py` (or `gmap.py`) on small boxes for ends and shapes. Image zooms only on corners, junctions and tips (≤ 64 px box). | `tools/runs.py` · `tools/lmap.py` · `tools/zoom.py` | — |
| 2 | Write `parts/<NN>_<part>.py` from `parts/_template.py` (`PART = '<NN>_<part>'`, the same stem as its ZORDER line). Place a guide along each visible line. Few anchors: corners via `cusp()`, `'s'` where the line keeps going. Drop samples within ~2 px of a crossing line. Run it: it writes `sections/<NN>_<part>.json` and prints the fit report. | `python3 parts/<NN>_<part>.py` | — |
| 3 | **Gate 1, overlay** | `tools/zoom.py … --section sections/<NN>_<part>.json` | the magenta path sits on the ink centre along its whole length |
| 4 | **Gate 2, fit report** (printed by the part script) | — | every segment max ≤ 1.0 px, mean ≤ 0.4; `degenerate handles: none` |
| 5 | Render | `tools/render.py checks/<NN>-vK.png --all` | — |
| 6 | **Gate 3, render check** | `tools/verify.py sections/<NN>_<part>.json checks/<NN>-vK.png` | every object p95 ≤ 1.0 px. Still failing → fix anchors, open no images yet. Passing → open `-look.png` and answer every spot L1, L2 …: junction → OK; real miss → fix; **covered** by a front part or a part not drawn yet → rerun with `--covered "x,y;x,y"` and name what covers each point. Never use `--covered` on a spot you have not seen. |
| 7 | **Missing features** | `tools/hotspots.py checks/<NN>-vK.png --box <part box>`, open `-hot.png`, plus `-side-100.png` once | every spot H1 … answered: a feature the part forgot → add it; shading/gradient left out on purpose → "not drawn"; another part's area → name it. No wobble, gaps or white slivers in `-side-100` |
| 8 | Report (format below) with `-look.png` and `-hot.png`, update `progress.md`. Wait for OK only while the user is still approving parts one by one (rule 3). | — | — |

When a gate fails, **change the anchors** (add one where the error peaks, move a corner onto the `cusp()`, drop samples polluted by a crossing line). Do not nudge handles by hand and do not rotate them afterwards. Use a smooth `'s'` anchor so the fit itself keeps the joint tangent.

### Report format (one per part)
```
Part 03 Face — v2
Anchors: profile 7 (corners: bridge, philtrum, jaw · smooth: nose tip, chin), neck back 2
Gate 2 fit: worst "nose top" max 0.44 / mean 0.27 px · handles OK
Gate 3 render: p95 0.42–0.75 px · L1 junction OK · L2 (1275,245) covered: forehead top under the hair
Hotspots: H1 blush gradient, not drawn · H2 hair area (part 05)
Colours (sampled): skin [253,190,159] box (1240,330)-(1255,345) · ink [106,84,76] width 1.36
Not checked at 100 %: — (or list it)
Files: checks/03-v2-look.png · checks/03-v2-hot.png
```

## Finish
1. `tools/render.py checks/final.png --all` → `tools/hotspots.py checks/final.png` (mean diff, p95, share of pixels > 60, ranked spots) → open `-hot.png` → look at the whole render once at 100 % beside the source. Name what was left out on purpose (gradients, blush, texture).
2. `scripts/export-svg.sh redraw.svg` → one SVG, one named group per section, every path named. The user opens it in Illustrator, Figma, Affinity or Inkscape. The SVG holds paths only, no bitmap.
3. If the user exports another format from their app (.ai, .eps), tell them to check the file holds no embedded image.
4. Tell the user the file is ready for real Visual Design / UI work: each section is its own editable layer and can be recoloured to their brand.

## When the user says "it doesn't look like the original"
Do not start over, do not "adjust from memory", do not touch parts the user did not name.
1. Find **which region** they mean (ask, or `tools/hotspots.py` on the latest render).
2. Zoom that region and find the **measured cause**: a wrong anchor, a sample polluted by a crossing, a missing line, the z-order, the colour.
3. Fix only that, run gates 1–3 again for the part, and report what changed and why.

## Lessons from earlier jobs (each one cost an iteration)
- **Judge quality only at full size.** A downscaled view averages away wobble, stair-steps and small features.
- **Rigid objects** (folder, phone, card, building edges) must be straight lines; curves fitted to them wobbled 3.7 px. Use `tools/poly.py`: measure each side, fit a robust line, take the corners as the side intersections.
- **A dark line on a dark fill** may have almost no luminance contrast (< 40). Measure on the channel that separates them: `line_c(G, chan=2)` for blue.
- **Thin slivers** (hair notches, a spike): measure as one light line, `line_c(G, kind='light')`, centre ± width/2, not as two edges.
- **Fingertips:** put the corner exactly where the finger line meets the outline (a deep V); the cap is a semicircle whose radius is half the width 5 px from the tip.
- If two anchors' handles nearly cross or one is near zero, the path is not hand-editable. Re-pick the anchors even when the error is low.
- A part checked on its own looks odd where its fill is routed under parts not drawn yet (straight polygon edges in the render). That is expected; later parts cover them.
- A part's own check misses things. After all parts, the whole-image `hotspots.py` caught a forgotten eye tick and a whole chair caster on one job.

## Tools
Every command and call, with its signature and which image to open, is in **`TOOLS.md`**. Do not read `tools/*.py`.
