#!/usr/bin/env python3
"""Historical daily weather via the NASA POWER REGIONAL API -> Tokki .WTH, Bolivia, 1981-present.

Adapted from prep/gen_weather_us_new.py (US 1995-2025 run). Same design: rate-limited,
Retry-After aware, per-request compressed cache so a re-run only fetches what is missing,
regional tiles on POWER's native grids, vectorised .WTH writing.

Bolivia-specific changes
  * Cell list comes from derived/cells_bolivia_mapspam2020.csv (MapSPAM 2020 V2r2 cells with
    >= 25 ha of soya, maize, rice, sorghum, wheat or potato). Fetch cost does not depend on
    the number of cells - it is tiles x years x parameters - so adding cells later costs
    nothing but a re-write.
  * Years 1981 (start of the POWER record) to the present. 1981 is deliberate: it keeps the
    1982/83 and 1986/87 El Nino seasons, which a 1991 start would lose (PLAN.md s6.2).
  * The current year is partial. Its cache key carries the end date, so a later re-run
    refreshes only that year; days after the last fully valid day are not written.
  * POWER radiation (ALLSKY_SFC_SW_DWN) begins 1984-01-01; the API refuses earlier dates.
    SRAD for 1981-1983 is therefore ESTIMATED from the diurnal temperature range with the
    Hargreaves relation, Rs = Krs * sqrt(Tmax - Tmin) * Ra, where Krs is fitted per cell and
    calendar month on the 1984-2026 overlap (captures wet-season cloudiness). The header line
    of every file says so, and the fit statistics are printed at the end of the run. Those
    three years exist to keep the 1982/83 El Nino in the hindcast; treat their radiation as
    an estimate when interpreting that season.
  * Short interior gaps (<= 5 consecutive missing days in any variable, e.g. POWER's missing
    SRAD on 1992-06-30 and 2026-09-07) are linearly interpolated, because DSSAT stops on a
    -99 in the daily record. Counts are printed.
  * One documented data artifact is neutralised: on 2020-06-04/05 MERRA-2 PRECTOTCORR puts
    500-850 mm/day over the Cochabamba-Potosi highlands in the middle of the dry season, with
    ~0 mm on the surrounding days. Those two days are replaced by the 06-03 -> 06-06 linear
    interpolation at every grid point where 06-04 >= 100 mm. The rule is explicit (RAIN_FIXES)
    rather than a generic cap, so genuine lowland extremes (200+ mm days in Chapare/Santa
    Cruz) are left untouched. 2023-10-22 (240-270 mm, southern Altiplano) is suspicious but
    not corrected; review before using the 2023 invierno/verano results there.
  * Header layout follows DSSAT's PARSE_HEADERS column rules exactly (field i is read from
    end-of-label(i-1)+2 to end-of-label(i)); the US script's 10.3f latitude shifted every
    later field one column right, truncating TAV/AMP decimals and the leading digit of any
    four-digit elevation.
  * ELEV in the header is taken from POWER's own DEM at the MERRA-2 grid point (0.5 x 0.625
    deg). In the Andes that is a coarse value: a 5-arcmin cell can sit 1-2 km above or below
    its grid-point mean. The temperature series carries the same coarse-grid signature, which
    matters for the valleys and Altiplano and is flagged in PLAN.md as the largest single
    uncertainty in the chain. A 5-arcmin DEM plus a lapse-rate adjustment is the follow-up;
    it needs no refetch because the cache holds the raw grid-point weather.

Usage:  python3 prep/gen_weather_bolivia.py [WORKERS=3] [RATE=2.0]
Exit 2 = fetch incomplete (throttled); re-run the same command to resume.
"""
import os, sys, json, time, threading, urllib.request, urllib.parse
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np, pandas as pd

sys.path.insert(0, os.path.expanduser("~/Claude/weathernext-data"))
from wn2dssat.wthwrite import compute_tav_amp
from wn2dssat.srad import extraterrestrial_radiation

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # ~/Claude/bolivia-enso
CELLS = f"{ROOT}/derived/cells_bolivia_mapspam2020.csv"
Y0    = 1981
SRAD_START = 1984                          # POWER radiation record begins here
TODAY = date.today()
LAST  = TODAY - timedelta(days=7)          # POWER lags ~2-7 days; SRAD lags most
Y1    = LAST.year
OUT   = f"{ROOT}/Tapiti/res/weather/{Y0}-{Y1}_bol"
CACHE = f"{ROOT}/weather/cache"
os.makedirs(CACHE, exist_ok=True); os.makedirs(OUT, exist_ok=True)
BASE  = "https://power.larc.nasa.gov/api/temporal/daily/regional"
PARAMS = {"SRAD": "ALLSKY_SFC_SW_DWN", "TMAX": "T2M_MAX", "TMIN": "T2M_MIN", "RAIN": "PRECTOTCORR"}
WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
RATE    = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0

cdf = pd.read_csv(CELLS)
cells = [(int(r.CELL5M), float(r.x), float(r.y)) for r in cdf.itertuples()]

# POWER serves these parameters on two grids. T2M_MAX / T2M_MIN / PRECTOTCORR are on the
# 0.5 x 0.625 deg MERRA-2 grid; ALLSKY_SFC_SW_DWN is on a 1 deg grid centred at k+0.5.
# Each grid has its own point list and index map (see the US script for the history).
def center(x, y):  return (round(round(y / 0.5) * 0.5, 3), round(round(x / 0.625) * 0.625, 3))
def scenter(x, y): return (round(np.floor(y) + 0.5, 3), round(np.floor(x) + 0.5, 3))
cell_center = {c5: center(x, y) for c5, x, y in cells}
cell_scen   = {c5: scenter(x, y) for c5, x, y in cells}
needed   = sorted(set(cell_center.values())); pidx = {c: i for i, c in enumerate(needed)}; N = len(needed)
needed_s = sorted(set(cell_scen.values()));   sidx = {c: i for i, c in enumerate(needed_s)}; NS = len(needed_s)
def idxmap(p): return sidx if p == "SRAD" else pidx

dates = pd.date_range(f"{Y0}-01-01", LAST.isoformat(), freq="D")
year_slice = {y: (int(np.searchsorted(dates.year, y)), int(np.searchsorted(dates.year, y + 1)))
              for y in range(Y0, Y1 + 1)}
A = {p: np.full((NS if p == "SRAD" else N, len(dates)), np.nan, dtype=np.float32) for p in PARAMS}
ELEV = np.full(N, np.nan, dtype=np.float32)      # POWER DEM at each MERRA-2 point
print(f"{len(cells)} cells -> {N} MERRA-2 points, {NS} 1-deg SRAD points; "
      f"{dates[0].date()} .. {dates[-1].date()} ({len(dates)} days)", flush=True)

lats = [c[0] for c in needed]; lons = [c[1] for c in needed]
tiles = [(la, la + 10, lo, lo + 10)
         for la in range(int(np.floor(min(lats))), int(np.ceil(max(lats))), 10)
         for lo in range(int(np.floor(min(lons))), int(np.ceil(max(lons))), 10)
         if any(la <= c[0] <= la + 10 and lo <= c[1] <= lo + 10 for c in needed)]
jobs = [(t, y, p) for t in tiles for y in range(Y0, Y1 + 1) for p in PARAMS
        if not (p == "SRAD" and y < SRAD_START)]
print(f"{len(tiles)} tiles x {Y1-Y0+1} yrs x {len(PARAMS)} params = {len(jobs)} requests", flush=True)

_rl = threading.Lock(); _next = [0.0]; MIN_INT = 1.0 / RATE
def throttle():
    with _rl:
        now = time.time(); t = max(now, _next[0]); _next[0] = t + MIN_INT
    if t > now: time.sleep(t - now)

def year_end(yr): return LAST.strftime("%Y%m%d") if yr == Y1 else f"{yr}1231"
def cpath(job):
    (a, _, c, _), yr, p = job
    tag = f"{yr}" if yr < Y1 else f"{yr}_to{year_end(yr)}"      # partial year keyed by end date
    return f"{CACHE}/{a}_{c}_{tag}_{p}.npz"

def fill_from(idxs, vals, pcol, yr):
    y0, y1 = year_slice[yr]; A[pcol][idxs, y0:y0 + vals.shape[1]] = vals

lock = threading.Lock(); prog = {"ok": 0, "cache": 0, "fail": 0}
consec = [0]; tripped = threading.Event()
def do(job):
    cp = cpath(job)
    if os.path.exists(cp):
        z = np.load(cp); m = idxmap(job[2])
        pairs = [(m[k], i) for i, k in enumerate(zip(z["lat"].tolist(), z["lon"].tolist())) if k in m]
        if pairs:
            ii = np.array([a for a, _ in pairs], dtype=np.int64)
            fill_from(ii, z["vals"][[b for _, b in pairs]], job[2], job[1])
            if job[2] != "SRAD" and "elev" in z.files: ELEV[ii] = z["elev"][[b for _, b in pairs]]
        with lock: prog["cache"] += 1
        return
    if tripped.is_set(): return
    (a, b, c, d), yr, pcol = job
    q = urllib.parse.urlencode({"parameters": PARAMS[pcol], "community": "AG",
        "latitude-min": a, "latitude-max": b, "longitude-min": c, "longitude-max": d,
        "start": f"{yr}0101", "end": year_end(yr), "format": "JSON"})
    for attempt in range(3):
        throttle()
        try:
            with urllib.request.urlopen(f"{BASE}?{q}", timeout=180) as r:
                feats = json.load(r)["features"]
            idxs, rows, klat, klon, kel = [], [], [], [], []
            for f in feats:
                coords = f["geometry"]["coordinates"]; lon, lat = coords[:2]
                key = (round(lat, 3), round(lon, 3)); i = idxmap(pcol).get(key)
                if i is None: continue
                s = pd.Series(f["properties"]["parameter"][PARAMS[pcol]]).sort_index()
                v = s.values.astype(np.float32); v[v == -999.0] = np.nan
                idxs.append(i); rows.append(v); klat.append(key[0]); klon.append(key[1])
                kel.append(float(coords[2]) if len(coords) > 2 else np.nan)
            if not idxs:
                raise RuntimeError(f"no returned point matched the {pcol} grid ({len(feats)} features)")
            idxs = np.array(idxs, dtype=np.int64); vals = np.array(rows, dtype=np.float32)
            fill_from(idxs, vals, pcol, yr)
            if pcol != "SRAD": ELEV[idxs] = np.array(kel, dtype=np.float32)
            np.savez_compressed(cp, vals=vals, lat=np.array(klat), lon=np.array(klon),
                                elev=np.array(kel, dtype=np.float32))
            with lock: prog["ok"] += 1; consec[0] = 0
            return
        except urllib.error.HTTPError as e:
            ra = e.headers.get("Retry-After")
            time.sleep(float(ra) if ra and ra.isdigit() else min(60, 3 * 2 ** attempt))
        except Exception:
            time.sleep(min(30, 2 ** attempt))
    with lock:
        prog["fail"] += 1; consec[0] += 1
        if consec[0] >= 40 and not tripped.is_set():
            tripped.set(); print("CIRCUIT BREAKER: sustained failures, aborting pass", flush=True)

t0 = time.time()
with ThreadPoolExecutor(WORKERS) as ex:
    futs = [ex.submit(do, j) for j in jobs]
    for k, _ in enumerate(as_completed(futs), 1):
        if k % 100 == 0:
            el = time.time() - t0
            print(f"  [{k}/{len(jobs)}] ok={prog['ok']} cache={prog['cache']} fail={prog['fail']} "
                  f"{k/el:.1f}/s ETA {(len(jobs)-k)/(k/el)/60:.0f}m", flush=True)
ncache = len([1 for j in jobs if os.path.exists(cpath(j))])
print(f"fetch: ok={prog['ok']} cache={prog['cache']} fail={prog['fail']} | cached {ncache}/{len(jobs)} "
      f"in {time.time()-t0:.0f}s", flush=True)
if ncache < len(jobs):
    print(f"** FETCH INCOMPLETE ({len(jobs)-ncache} missing). Re-run the same command to resume. **", flush=True)
    sys.exit(2)

# ---- QC fixes (operate on grid-point arrays, before the per-cell write) ----
MAXGAP = 5
def fill_short_gaps(a):
    """Linear interpolation of interior NaN runs of length <= MAXGAP, per row. Returns count."""
    n = 0
    for r in range(a.shape[0]):
        nan = np.isnan(a[r])
        if not nan.any(): continue
        idx = np.flatnonzero(nan); good = np.flatnonzero(~nan)
        if good.size < 2: continue
        # only interior runs (strictly between first and last valid day) and short ones
        runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
        for run in runs:
            if run[0] <= good[0] or run[-1] >= good[-1] or run.size > MAXGAP: continue
            a[r, run] = np.interp(run, good, a[r, good]); n += run.size
    return n
pre_mask = dates.year.values < SRAD_START
for p in PARAMS:
    a = A[p]
    if p == "SRAD":   # do not touch the pre-1984 block here; it is estimated later
        sub = a[:, ~pre_mask]; k = fill_short_gaps(sub); a[:, ~pre_mask] = sub
    else:
        k = fill_short_gaps(a)
    print(f"  {p}: interpolated {k} short-gap values", flush=True)

RAIN_FIXES = [  # (trigger date, days to replace, threshold mm, reason)
    ("2020-06-04", ["2020-06-04", "2020-06-05"], 100.0,
     "MERRA-2 dry-season artifact, 500-850 mm/day over Cochabamba-Potosi highlands"),
]
di = {d.date().isoformat(): k for k, d in enumerate(dates)}
for trig, days, thr, why in RAIN_FIXES:
    t = di[trig]; rows = np.flatnonzero(A["RAIN"][:, t] >= thr)
    ks = [di[d] for d in days]; lo, hi = min(ks) - 1, max(ks) + 1
    for r in rows:
        A["RAIN"][r, ks] = np.interp(ks, [lo, hi], [A["RAIN"][r, lo], A["RAIN"][r, hi]])
    print(f"  RAIN fix {trig}: {len(rows)} grid points replaced on {days} ({why})", flush=True)

# ---- QC summary before writing ----
for p in PARAMS:
    a = A[p]; print(f"  {p}: NaN {np.isnan(a).mean()*100:.3f}%  min {np.nanmin(a):.1f}  max {np.nanmax(a):.1f}", flush=True)
print(f"  ELEV: {np.nanmin(ELEV):.0f} .. {np.nanmax(ELEV):.0f} m, missing {np.isnan(ELEV).sum()}", flush=True)

# ---- vectorised .WTH writing ----
print("fetch complete - writing .WTH files ...", flush=True)
DATEP = np.array([f"{d.year:04d}{d.dayofyear:03d}" for d in dates])
DOY = dates.dayofyear.values; MONTH = dates.month.values
PRE = dates.year.values < SRAD_START                 # days needing estimated SRAD
def col(a): return np.char.mod("%6.1f", np.where(np.isnan(a), -99.0, a))

def estimate_pre1984_srad(sr, tx, tn, lat):
    """Fill SRAD before SRAD_START with Hargreaves, Krs fitted per calendar month on the
    observed overlap. Returns (filled series, in-sample RMSE, bias) for this cell."""
    ra = extraterrestrial_radiation(lat, DOY)
    base = np.sqrt(np.clip(tx - tn, 0.0, None)) * ra
    ok = ~PRE & ~np.isnan(sr) & ~np.isnan(base)
    krs = np.full(13, np.nan)
    for m in range(1, 13):
        sel = ok & (MONTH == m)
        krs[m] = np.nansum(sr[sel]) / np.nansum(base[sel]) if sel.any() and np.nansum(base[sel]) > 0 else 0.16
    est = np.clip(krs[MONTH] * base, 0.0, ra).astype(np.float32)
    out = sr.copy(); fill = PRE & np.isnan(out); out[fill] = est[fill]
    resid = (est - sr)[ok]
    return out, float(np.sqrt(np.mean(resid ** 2))), float(np.mean(resid))

tw = time.time(); w = 0; nan_days = 0; trunc = []; fit_rmse = []; fit_bias = []
for c5, x, y in cells:
    i = pidx[cell_center[c5]]; j = sidx[cell_scen[c5]]
    sr, tx, tn, rn = A["SRAD"][j], A["TMAX"][i], A["TMIN"][i], A["RAIN"][i]
    note = ""
    if np.isnan(sr[PRE]).any():
        sr, r_, b_ = estimate_pre1984_srad(sr, tx, tn, y); fit_rmse.append(r_); fit_bias.append(b_)
        note = f"; SRAD {Y0}-{SRAD_START-1} ESTIMATED (Hargreaves, monthly Krs fitted {SRAD_START}-{Y1})"
    # drop the trailing tail where any variable is still missing (POWER lag), keep interior as-is
    valid = ~(np.isnan(sr) | np.isnan(tx) | np.isnan(tn) | np.isnan(rn))
    last = int(np.max(np.nonzero(valid)[0])) + 1 if valid.any() else 0
    trunc.append(len(dates) - last)
    sr, tx, tn, rn, dp = sr[:last], tx[:last], tn[:last], rn[:last], DATEP[:last]
    nan_days += int((~valid[:last]).sum())
    elev = float(ELEV[i]) if not np.isnan(ELEV[i]) else -99.0
    tav, amp = compute_tav_amp(pd.DataFrame({"date": dates[:last], "TMAX": tx, "TMIN": tn}))
    body = np.char.add(np.char.add(np.char.add(np.char.add(dp, col(sr)), col(tx)), col(tn)), col(rn))
    txt = (f"$WEATHER DATA : CELL5M {c5}  LAT {y:.4f}  LON {x:.4f}  NASA POWER (MERRA-2 0.5x0.625 T/RAIN, 1deg SRAD; ELEV = POWER DEM at grid point{note})\n"
           "@ INSI      LAT     LONG  ELEV   TAV   AMP REFHT WNDHT\n"
           f"  BOLI{y:9.3f}{x:9.3f}{elev:6.0f}{tav:6.1f}{amp:6.1f}{2.0:6.1f}{2.0:6.1f}\n"
           "@  DATE  SRAD  TMAX  TMIN  RAIN\n" + "\n".join(body) + "\n")
    tmp = f"{OUT}/{c5}.WTH.tmp"; open(tmp, "w").write(txt); os.replace(tmp, f"{OUT}/{c5}.WTH")
    w += 1
    if w % 1000 == 0: print(f"  wrote {w}/{len(cells)} ({time.time()-tw:.0f}s)", flush=True)
if fit_rmse:
    print(f"  pre-{SRAD_START} SRAD estimate, in-sample fit on {SRAD_START}-{Y1} across {len(fit_rmse)} cells: "
          f"RMSE median {np.median(fit_rmse):.2f} (max {np.max(fit_rmse):.2f}) MJ/m2/d, "
          f"bias median {np.median(fit_bias):+.3f}", flush=True)
print(f"\nDONE: {w} .WTH -> {OUT}  | interior -99 days total {nan_days} | "
      f"tail truncated by {min(trunc)}..{max(trunc)} days | total {time.time()-t0:.0f}s", flush=True)
