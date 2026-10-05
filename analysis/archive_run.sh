#!/bin/bash
# Archive a finished Tapiti run so it survives the next launch (Tapiti wipes res/result on startup).
#
#   analysis/archive_run.sh <tag> [path/to/run.log]
#
# Moves Tapiti/res/result/*combinedOutput*.csv to runs/<YYYYMMDD-HHMM>_<tag>/, gzips it, snapshots
# config.yml, the Tapiti commit, checksums of the inputs and genotype files, copies the log, then
# runs analysis/summarise_run.py and analysis/compare_ine.py into the same folder and appends a
# line to runs/INDEX.md. Pass --no-analysis to skip the summaries.
set -euo pipefail
ROOT=~/Claude/bolivia-enso; T=$ROOT/Tapiti
tag=${1:?usage: archive_run.sh <tag> [run.log] [--no-analysis]}; log=${2:-}; analysis=1
for a in "$@"; do [ "$a" = "--no-analysis" ] && analysis=0; done
[ "$log" = "--no-analysis" ] && log=""
shopt -s nullglob; files=("$T"/res/result/*combinedOutput*.csv); shopt -u nullglob
[ ${#files[@]} -eq 0 ] && { echo "nothing to archive: no *combinedOutput*.csv in $T/res/result"; exit 1; }
[ ${#files[@]} -gt 1 ] && { echo "more than one merged output in res/result — archive them one at a time"; ls "${files[@]}"; exit 1; }
src=${files[0]}; stamp=$(date -r "$src" +%Y%m%d-%H%M); dir=$ROOT/runs/${stamp}_${tag}
mkdir -p "$dir"; mv "$src" "$dir/combinedOutput.csv"
[ -n "$log" ] && [ -f "$log" ] && cp "$log" "$dir/run.log"
cp "$T/config.yml" "$dir/config.yml"
{ echo "# Run $tag"; echo; echo "- archived: $(date -Iseconds)"; echo "- merged output written: $(date -r "$dir/combinedOutput.csv" -Iseconds)";
  echo "- Tapiti commit: $(git -C "$T" rev-parse --short HEAD) ($(git -C "$T" log -1 --format=%s))"; echo "- Tapiti dirty files: $(git -C "$T" status --short | grep -v Zone.Identifier | wc -l)";
  echo "- jar: $(ls -la "$T"/target/tapiti-*-jar-with-dependencies.jar | awk '{print $6,$7,$8}')";
  echo "- rows in merged output: $(($(wc -l < "$dir/combinedOutput.csv")-1))";
  echo; echo "## Input checksums (md5)"; for f in res/input/unit-information.jsonl res/input/BO.SOL res/.csm/MZCER048.CUL res/.csm/SBGRO048.CUL res/.csm/RICER048.CUL res/.csm/SGCER048.CUL res/.csm/WHCER048.CUL; do echo "- $f: $(md5sum "$T/$f" | cut -c1-12)"; done
  echo; echo "## Startup settings echoed by Tapiti"; [ -f "$dir/run.log" ] && tr '\r' '\n' < "$dir/run.log" | grep -E "^> (Soil file|Number of threads|Weather data|Nitrogen rate|Rice system|Simulation start|Soil organic|Initial soil|Number of units|First planting|Done)" | sed 's/^/    /' || echo "    (no log given)";
} > "$dir/MANIFEST.md"
if [ $analysis -eq 1 ]; then
  ( cd "$ROOT" && python3 analysis/summarise_run.py "$dir/combinedOutput.csv" > "$dir/summary.txt" 2>&1 && python3 analysis/compare_ine.py "$dir/combinedOutput_depto_year.csv" > "$dir/vs_ine.txt" 2>&1 ) || echo "analysis step reported an error; see $dir/*.txt"
fi
gzip -f "$dir/combinedOutput.csv"; [ -f "$dir/combinedOutput_cellyear.csv" ] && gzip -f "$dir/combinedOutput_cellyear.csv"
mkdir -p "$ROOT/runs"; [ -f "$ROOT/runs/INDEX.md" ] || printf '# Archived runs\n\n| Folder | Tag | Tapiti commit | Rows | Notes |\n|---|---|---|---|---|\n' > "$ROOT/runs/INDEX.md"
echo "| ${stamp}_${tag} | $tag | $(git -C "$T" rev-parse --short HEAD) | $(zcat "$dir/combinedOutput.csv.gz" | wc -l) | |" >> "$ROOT/runs/INDEX.md"
echo "archived to $dir"; ls -la "$dir" | awk 'NR>1{print "  "$5"\t"$9}'
