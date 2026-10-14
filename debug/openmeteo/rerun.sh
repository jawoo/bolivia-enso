#!/bin/bash
# Retry the two Open-Meteo pulls until both complete (free-tier daily quota resets); up to 20 attempts, 30 min apart.
cd ~/Claude/bolivia-enso
for i in $(seq 1 60); do
  echo "== attempt $i $(date)"
  python3 -u debug/openmeteo/om_fetch.py > debug/openmeteo/om_fetch.log 2>&1; a=$(grep -c "gave up" debug/openmeteo/om_fetch.log)
  python3 -u debug/openmeteo/stations2.py > debug/openmeteo/stations2.log 2>&1; b=$?
  echo "om_fetch gave_up=$a stations2 exit=$b"
  if [ "$a" = 0 ] && [ "$b" = 0 ]; then echo ALL_COMPLETE; exit 0; fi
  sleep 1800
done
echo GAVE_UP_AFTER_60
