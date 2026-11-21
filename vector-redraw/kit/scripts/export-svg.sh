#!/bin/bash
# export-svg.sh [out.svg]  -> one SVG of every section listed in sections/ZORDER.txt that exists, back to front.
# Run from the job folder.
set -e
OUT="${1:-redraw.svg}"; LIST=()
while read -r n; do [[ -z "$n" || "$n" == \#* ]] && continue; [[ -f "sections/$n.json" ]] && LIST+=("sections/$n.json"); done < sections/ZORDER.txt
[[ ${#LIST[@]} -gt 0 ]] || { echo "no sections listed in sections/ZORDER.txt exist yet"; exit 1; }
python3 tools/section_svg.py "$OUT" "${LIST[@]}"
echo "${#LIST[@]} sections"
