#!/usr/bin/env python3
"""Build a minimal Bolivian smoke-test input set for Tapiti.

Three real 5-arcmin cells in the Santa Cruz Norte Integrado soybean/maize zone,
real NASA POWER daily weather, and placeholder soil profiles cloned from the US
soil library with a BO prefix.

NOT production data. The soil profiles are placeholders whose only purpose is to
prove the chain runs end to end; Phase 1 rebuilds them from SoilGrids v2 + HC27.
"""
import json, os, re, sys
from datetime import date
sys.path.insert(0, os.path.expanduser("~/Claude/weathernext-data"))
from wn2dssat.nasapower import fetch_weather

BO   = os.path.expanduser("~/Claude/bolivia-enso/Tapiti")
INP  = f"{BO}/res/input"
WTH  = f"{BO}/res/weather/smoke"
Y0, Y1 = 2015, 2017          # sowing years 2015, 2016 + maturation into 2017
RES = 5/60

def cell5m(x, y):
    col = int((x + 180) / RES)
    row = int((90 - y) / RES)
    return row * 4320 + col

def centre(c5):
    row, col = divmod(c5, 4320)
    return (-180 + (col + 0.5) * RES, 90 - (row + 0.5) * RES)

# Santa Cruz lowland: Norte Integrado / Cuatro Cañadas soybean-maize belt
SITES = [(-63.20, -17.38), (-62.80, -17.05), (-63.55, -16.75)]

os.makedirs(WTH, exist_ok=True)
records, cells = [], []
for i, (x, y) in enumerate(SITES):
    c5 = cell5m(x, y)
    cx, cy = centre(c5)
    cells.append((c5, cx, cy))
    print(f"cell5m {c5}  centre {cy:.4f}N {cx:.4f}E", flush=True)

    df = fetch_weather(cy, cx, date(Y0, 1, 1), date(Y1, 12, 31))
    hdr = (f"$WEATHER DATA : CELL5M {c5}  LAT {cy:.4f}  LON {cx:.4f}\n"
           "@ INSI      LAT     LONG  ELEV   TAV   AMP REFHT WNDHT\n"
           f"  BOLI   {cy:7.3f} {cx:8.3f} 350.0  "
           f"{df.TMAX.add(df.TMIN).div(2).mean():5.1f} "
           f"{(df.TMAX.mean()-df.TMIN.mean()):5.1f}   2.0   2.0\n"
           "@  DATE  SRAD  TMAX  TMIN  RAIN\n")
    rows = "".join(
        f"{d.year}{d.dayofyear:03d} {s:5.1f} {mx:5.1f} {mn:5.1f} {r:5.1f}\n"
        for d, s, mx, mn, r in zip(df.date, df.SRAD, df.TMAX, df.TMIN, df.RAIN))
    open(f"{WTH}/{c5}.WTH", "w").write(hdr + rows)
    print(f"  wrote {c5}.WTH  {len(df)} days  "
          f"{df.date.min().date()}..{df.date.max().date()}  "
          f"annual rain ~{df.RAIN.sum()/ (Y1-Y0+1):.0f} mm", flush=True)

    # Crop records. Planting dates are the window midpoints from
    # derived/crop_calendar_bolivia.csv; both are safely below DOY 335.
    records.append({
        "unitId": i, "cell5m": c5, "x": round(cx, 4), "y": round(cy, 4),
        "soilProfileId": f"BO{c5:08d}", "soilRootingDepth": 150,
        "crops": [
            {"code": "SB", "plantingDate": 320, "area": 5000.0,      # soya verano
             "nFertRateAct": 0.0, "nFertRateRec": 0.0,
             "waterSupply": "R", "plantingDensity": 30.0},
            {"code": "MZ", "plantingDate": 319, "area": 1500.0,      # maiz manual
             "nFertRateAct": 40.0, "nFertRateRec": 60.0,
             "waterSupply": "R", "plantingDensity": 5.5},
        ],
    })

with open(f"{INP}/unit-information.jsonl", "w") as f:
    for r in records:
        f.write(json.dumps(r) + "\n")
print(f"\nwrote {INP}/unit-information.jsonl ({len(records)} cells)")

# Placeholder BO.SOL: clone distinct profiles out of the US library, relabel BO.
us_sol = os.path.expanduser("~/Codebase/Tokki/res/input/US.SOL")
profiles, cur = [], []
with open(us_sol, errors="replace") as f:
    for line in f:
        if line.startswith("*") and not line.startswith("*SOILS"):
            if cur: profiles.append(cur)
            cur = [line]
            if len(profiles) > 3: break
        elif cur:
            cur.append(line)
if cur and len(profiles) <= 3: profiles.append(cur)

def retoken(line, replacements):
    """Replace whitespace-separated tokens by index, right-aligned into the
    ORIGINAL token width. DSSAT's soil reader (IPSOIL) is fixed-column, so a
    replacement that changes a field's width shifts every later field out of
    position and the profile fails to parse with error 5010."""
    out = list(line)
    for i, m in enumerate(re.finditer(r"\S+", line)):
        if i in replacements:
            width = m.end() - m.start()
            out[m.start():m.end()] = list(str(replacements[i])[:width].rjust(width))
    return "".join(out)

out = ["*SOILS: Bolivia SMOKE-TEST placeholders (cloned from US.SOL, NOT production)\n\n"]
for (c5, cx, cy), prof in zip(cells, profiles):
    body = "".join(prof).replace("\r\n", "\n").rstrip("\n").split("\n")
    # Header: swap ONLY the 10-character soil id, leaving the SOURCE / TEXTURE /
    # DEPTH columns exactly where IPSOIL expects them. Writing a free-text header
    # here is what caused error 5010 on the first smoke run.
    body[0] = f"*BO{c5:08d}" + body[0][11:]
    # @SITE data line tokens: SITE, COUNTRY, LAT, LONG, SCS-family.
    for j, ln in enumerate(body):
        if j and body[j - 1].startswith("@SITE"):
            body[j] = retoken(ln, {1: "BO", 2: f"{cy:.3f}", 3: f"{cx:.3f}"})
    out.append("\n".join(body) + "\n\n")
open(f"{INP}/BO.SOL", "w").write("".join(out))
print(f"wrote {INP}/BO.SOL ({len(cells)} placeholder profiles)")
