#!/bin/bash
# new-job.sh <source image> <job-name> [parent folder]
# Copies the kit into a fresh job folder and puts the source in as source.png at FULL size (never resized).
# Parent folder defaults to the current folder.
set -e
SRC="$1"; NAME="$2"; ROOT="${3:-$PWD}"
if [[ ! -f "$SRC" || -z "$NAME" ]]; then echo "usage: new-job.sh <source image> <job-name> [parent folder]"; exit 1; fi
KIT="$(cd "$(dirname "$0")/.." && pwd)/kit"
ROOT="$(mkdir -p "$ROOT" && cd "$ROOT" && pwd)"; JOB="$ROOT/$NAME"
if [[ -e "$JOB" ]]; then echo "exists, not touching it: $JOB"; exit 1; fi
mkdir -p "$ROOT"; cp -R "$KIT" "$JOB"
python3 - "$SRC" "$JOB/source.png" "$JOB/progress.md" "$NAME" <<'PY'
import sys
from PIL import Image
src, out, prog, name = sys.argv[1:]
im = Image.open(src); im.load()
if im.mode not in ('RGB', 'RGBA'): im = im.convert('RGB')
im.save(out)
s = open(prog).read().replace('<job name>', name).replace('<W>×<H>', '%d×%d' % im.size)
open(prog, 'w').write(s)
print('source.png %dx%d' % im.size)
PY
echo "job: $JOB"
