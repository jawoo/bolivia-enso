#!/bin/bash
# Phase 4 analogue ensemble: run the 2026/27 campaign under each analogue year's weather.
#   analysis/phase4_run_analogues.sh 1997 2015 2023 ...      (sowing years 1983..2024)
# For each A: build res/weather/2026_analog_A (prep/gen_weather_analogue.py), run Tapiti with
# firstPlantingYear 2026 / numberOfYears 1 on the full unit table, archive the merged output to
# runs/phase4/analog_A_combinedOutput.csv.gz, then remove the analogue weather directory.
set -euo pipefail
ROOT=~/Claude/bolivia-enso; T=$ROOT/Tapiti; mkdir -p $ROOT/runs/phase4
pgrep -f "^java -jar target/tapiti-" >/dev/null && { echo "a Tapiti run is already in progress"; exit 1; }
shopt -s nullglob; left=("$T"/res/result/*combinedOutput*.csv); shopt -u nullglob
[ ${#left[@]} -gt 0 ] && { echo "res/result holds an unarchived merged output; archive it first"; exit 1; }
cp "$T/config.yml" "$ROOT/runs/phase4/config.yml.prod.bak"
trap 'cp "$ROOT/runs/phase4/config.yml.prod.bak" "$T/config.yml"' EXIT
for A in "$@"; do
  out=$ROOT/runs/phase4/analog_${A}_combinedOutput.csv.gz
  [ -f "$out" ] && { echo "analogue $A already archived, skipping"; continue; }
  [ -d "$T/res/weather/2026_analog_$A" ] || python3 "$ROOT/prep/gen_weather_analogue.py" "$A"
  sed -e "s#^  weather: .*#  weather: 2026_analog_$A#" -e 's/^firstPlantingYear: .*/firstPlantingYear: 2026/' -e 's/^numberOfYears: .*/numberOfYears: 1/' "$ROOT/runs/phase4/config.yml.prod.bak" > "$T/config.yml"
  cd "$T"; find res/.temp/summary -name '*.csv' -delete; for t in res/threads/T*/; do rm -f "$t/ERROR.OUT"; done
  start=$(date +%s); java -jar target/tapiti-1.0-SNAPSHOT-jar-with-dependencies.jar > "$ROOT/runs/phase4/analog_${A}.log" 2>&1 || true
  errs=$(tr '\r' '\n' < "$ROOT/runs/phase4/analog_${A}.log" | grep -c "Error code" || true)
  f=$(ls res/result/*combinedOutput*.csv 2>/dev/null | head -1)
  if [ -z "$f" ]; then echo "analogue $A: NO OUTPUT (see runs/phase4/analog_${A}.log)"; continue; fi
  gzip -c "$f" > "$out"; rm -f res/result/*combinedOutput*.csv; rm -rf "res/weather/2026_analog_$A"
  echo "analogue $A: $(( $(zcat "$out" | wc -l) - 1 )) seasons, $errs DSSAT errors, $(( $(date +%s) - start )) s -> $out"
done
