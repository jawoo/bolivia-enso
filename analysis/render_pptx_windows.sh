#!/bin/bash
# Render a .pptx to PNGs with the Windows PowerPoint installation (WSL). Usage: render_pptx_windows.sh deck.pptx outdir
set -euo pipefail
src=$(readlink -f "$1"); out=$2; mkdir -p "$out"
WU=/mnt/c/Users/JKOO/; stage="${WU}Documents/tapiti-deck"; mkdir -p "$stage"; rm -rf "$stage/png"; cp "$src" "$stage/deck.pptx"
wstage=$(wslpath -w "$stage")
/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "\$app = New-Object -ComObject PowerPoint.Application; \$p = \$app.Presentations.Open('$wstage\\deck.pptx', \$true, \$false, \$false); \$p.SaveAs('$wstage\\png', 18); \$p.Close(); \$app.Quit()" 2>&1 | tr -d '\r' | grep -v "^$" | head -5 || true
ls "$stage/png"/*.PNG >/dev/null 2>&1 && cp "$stage/png"/*.PNG "$out"/ && ls "$out" | head -3 && echo "rendered $(ls "$out" | wc -l) slides to $out" || { echo "render failed"; exit 1; }
