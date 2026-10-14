#!/bin/bash
# Phase 5 forecast ensemble: run the 2026/27 campaign under each ECMWF member's spliced weather (PLAN.md s12).
#   analysis/phase5_run_members.sh <run YYYY-MM-DD> <member> [<member> ...]        (members 0..50; 0 = control)
# Expects Tapiti/res/weather/2026_fc_<mm>/ from prep/gen_weather_forecast.py. Runs Tapiti with firstPlantingYear 2026 /
# numberOfYears 1, archives the merged output to runs/phase5/<run>/fc_<mm>_combinedOutput.csv.gz, removes the weather dir.
set -euo pipefail
ROOT=~/Claude/bolivia-enso; T=$ROOT/Tapiti; RUN=$1; shift; OUTD=$ROOT/runs/phase5/$RUN; mkdir -p "$OUTD"
pgrep -f "^java -jar target/tapiti-" >/dev/null && { echo "a Tapiti run is already in progress"; exit 1; }
shopt -s nullglob; left=("$T"/res/result/*combinedOutput*.csv); shopt -u nullglob
[ ${#left[@]} -gt 0 ] && { echo "res/result holds an unarchived merged output; archive it first"; exit 1; }
cp "$T/config.yml" "$OUTD/config.yml.prod.bak"
trap 'cp "$OUTD/config.yml.prod.bak" "$T/config.yml"' EXIT
for M in "$@"; do
  mm=$(printf "%02d" "$M"); out=$OUTD/fc_${mm}_combinedOutput.csv.gz
  [ -f "$out" ] && { echo "member $mm already archived, skipping"; continue; }
  [ -d "$T/res/weather/2026_fc_$mm" ] || python3 "$ROOT/prep/gen_weather_forecast.py" --run "$RUN" --members "$M"
  sed -e "s#^  weather: .*#  weather: 2026_fc_$mm#" -e 's/^firstPlantingYear: .*/firstPlantingYear: 2026/' -e 's/^numberOfYears: .*/numberOfYears: 1/' "$OUTD/config.yml.prod.bak" > "$T/config.yml"
  cd "$T"; find res/.temp/summary -name '*.csv' -delete; for t in res/threads/T*/; do rm -f "$t/ERROR.OUT"; done
  start=$(date +%s); java -jar target/tapiti-1.0-SNAPSHOT-jar-with-dependencies.jar > "$OUTD/fc_${mm}.log" 2>&1 || true
  errs=$(tr '\r' '\n' < "$OUTD/fc_${mm}.log" | grep -c "Error code" || true)
  f=$(ls res/result/*combinedOutput*.csv 2>/dev/null | head -1)
  if [ -z "$f" ]; then echo "member $mm: NO OUTPUT (see $OUTD/fc_${mm}.log)"; continue; fi
  gzip -c "$f" > "$out"; rm -f res/result/*combinedOutput*.csv; rm -rf "res/weather/2026_fc_$mm"
  echo "member $mm: $(( $(zcat "$out" | wc -l) - 1 )) seasons, $errs DSSAT errors, $(( $(date +%s) - start )) s -> $out"
done
