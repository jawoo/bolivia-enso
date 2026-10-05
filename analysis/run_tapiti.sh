#!/bin/bash
# Launch a full Tapiti run safely: refuses if res/result still holds an unarchived merged output,
# logs to runs/prod_<tag>.log, prints the pid. Archive afterwards with analysis/archive_run.sh <tag> runs/prod_<tag>.log
set -euo pipefail
ROOT=~/Claude/bolivia-enso; T=$ROOT/Tapiti; tag=${1:?usage: run_tapiti.sh <tag>}
shopt -s nullglob; left=("$T"/res/result/*combinedOutput*.csv); shopt -u nullglob
[ ${#left[@]} -gt 0 ] && { echo "res/result holds an unarchived merged output — run analysis/archive_run.sh first:"; ls "${left[@]}"; exit 1; }
pgrep -f "^java -jar target/tapiti-" >/dev/null && { echo "a Tapiti run is already in progress"; exit 1; }
cd "$T"; find res/.temp/summary -name '*.csv' -delete; for t in res/threads/T*/; do rm -f "$t/ERROR.OUT"; done
nohup java -jar target/tapiti-1.0-SNAPSHOT-jar-with-dependencies.jar > "$ROOT/runs/prod_${tag}.log" 2>&1 &
echo "launched pid $! -> $ROOT/runs/prod_${tag}.log  (archive when done: analysis/archive_run.sh $tag runs/prod_${tag}.log)"
