#!/usr/bin/env python3
"""Production weather via NASA POWER REGIONAL API -> .WTH for all US cells, 1995-2025.

Rate-limited + Retry-After aware + per-request disk cache (resumable: re-run only
fetches what's missing). Regional returns POWER's native 0.5x0.625 grid; each cell
snaps to its nearest grid point. Fast vectorized .WTH writing.
"""
import os, sys, json, time, gzip, threading, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np, pandas as pd

sys.path.insert(0, os.path.expanduser("~/Claude/weathernext-data"))
from wn2dssat.wthwrite import compute_tav_amp

TOKKI = os.path.expanduser("~/Codes/Tokki")
HC = os.path.expanduser("~/Claude/tokki-results/hindcast")
JSONL = "/tmp/claude-1000/-home-jawoo-Codes-Tokki/06b3073d-980e-4b48-b2b8-b624609be04f/scratchpad/us-new-cells.jsonl"
SRC_WTH = None
Y0, Y1 = 1995, 2025
OUT = f"{TOKKI}/res/weather/{Y0}-{Y1}_usa-mzsb-47707"
CACHE = "/home/jawoo/Claude/us-weather/cache"; os.makedirs(CACHE, exist_ok=True); os.makedirs(OUT, exist_ok=True)
BASE = "https://power.larc.nasa.gov/api/temporal/daily/regional"
PARAMS = {"SRAD": "ALLSKY_SFC_SW_DWN", "TMAX": "T2M_MAX", "TMIN": "T2M_MIN", "RAIN": "PRECTOTCORR"}
WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
RATE = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0        # requests/sec cap (proactive)

cells = []
for ln in open(JSONL):
    r = json.loads(ln); cells.append((r["cell5m"], r["x"], r["y"]))
# POWER serves these parameters on TWO different grids, and mixing them up is the
# trap this script originally fell into: T2M_MAX/T2M_MIN/PRECTOTCORR come back on
# the 0.5 x 0.625 deg MERRA-2 grid, while ALLSKY_SFC_SW_DWN (SRAD) comes back on a
# 1 deg grid with centres at k+0.5. Only about one in eight SRAD longitudes happens
# to coincide with a 0.625 multiple, so indexing SRAD against the MERRA-2 grid
# silently discards most of it and leaves SRAD as NaN. Each grid therefore gets its
# own point list and its own index map.
def center(x, y): return (round(round(y / 0.5) * 0.5, 3), round(round(x / 0.625) * 0.625, 3))
def scenter(x, y): return (round(np.floor(y) + 0.5, 3), round(np.floor(x) + 0.5, 3))
cell_center = {c5: center(x, y) for c5, x, y in cells}
cell_scen = {c5: scenter(x, y) for c5, x, y in cells}
needed = sorted(set(cell_center.values()))
pidx = {c: i for i, c in enumerate(needed)}; N = len(needed)
needed_s = sorted(set(cell_scen.values()))
sidx = {c: i for i, c in enumerate(needed_s)}; NS = len(needed_s)
def idxmap(p): return sidx if p == "SRAD" else pidx
dates = pd.date_range(f"{Y0}-01-01", f"{Y1}-12-31", freq="D")
year_slice = {y: (int(np.searchsorted(dates.year, y)), int(np.searchsorted(dates.year, y + 1))) for y in range(Y0, Y1 + 1)}
A = {p: np.full((NS if p == "SRAD" else N, len(dates)), np.nan, dtype=np.float32)
     for p in PARAMS}
print(f"{len(cells)} cells -> {N} MERRA-2 points, {NS} 1-deg SRAD points", flush=True)

lats = [c[0] for c in needed]; lons = [c[1] for c in needed]
tiles = [(la, la + 10, lo, lo + 10)
         for la in range(int(np.floor(min(lats))), int(np.ceil(max(lats))), 10)
         for lo in range(int(np.floor(min(lons))), int(np.ceil(max(lons))), 10)
         if any(la <= c[0] <= la + 10 and lo <= c[1] <= lo + 10 for c in needed)]
jobs = [(t, y, p) for t in tiles for y in range(Y0, Y1 + 1) for p in PARAMS]
print(f"{len(tiles)} tiles x {Y1-Y0+1} yrs x {len(PARAMS)} params = {len(jobs)} requests", flush=True)

# proactive rate limiter (space request starts globally)
_rl = threading.Lock(); _next = [0.0]; MIN_INT = 1.0 / RATE
def throttle():
    with _rl:
        now = time.time(); t = max(now, _next[0]); _next[0] = t + MIN_INT
    if t > now: time.sleep(t - now)

def cpath(job):
    (a, _, c, _), yr, p = job; return f"{CACHE}/{a}_{c}_{yr}_{p}.npz"

def fill_from(idxs, vals, pcol, yr):
    y0, y1 = year_slice[yr]; A[pcol][idxs, y0:y1] = vals

lock = threading.Lock(); prog = {"ok": 0, "cache": 0, "fail": 0}
consec = [0]; tripped = threading.Event()          # circuit breaker on sustained 429s
def do(job):
    cp = cpath(job)
    if os.path.exists(cp):                        # resume from cache (always, free)
        z = np.load(cp)
        if "lat" not in z.files:
            # Caches written before 2026-09-20 stored row indices into the point
            # list. Those are only valid for the cell set that built them: change
            # the cells and the list re-orders, silently giving one grid point's
            # weather to another. Drop and refetch rather than trust it.
            z.close(); os.remove(cp)
        else:
            m = idxmap(job[2])
            pairs = [(m[k], i) for i, k in
                     enumerate(zip(z["lat"].tolist(), z["lon"].tolist())) if k in m]
            if pairs:
                fill_from(np.array([a for a, _ in pairs], dtype=np.int64),
                          z["vals"][[b for _, b in pairs]], job[2], job[1])
            with lock: prog["cache"] += 1
            return
    if tripped.is_set(): return                   # throttled: skip new fetches this pass
    (a, b, c, d), yr, pcol = job
    q = urllib.parse.urlencode({"parameters": PARAMS[pcol], "community": "AG",
        "latitude-min": a, "latitude-max": b, "longitude-min": c, "longitude-max": d,
        "start": f"{yr}0101", "end": f"{yr}1231", "format": "JSON"})
    for attempt in range(3):   # fail-fast; the driver's pass-loop retries misses
        throttle()
        try:
            with urllib.request.urlopen(f"{BASE}?{q}", timeout=180) as r:
                feats = json.load(r)["features"]
            idxs, rows, klat, klon = [], [], [], []
            for f in feats:
                lon, lat = f["geometry"]["coordinates"][:2]
                key = (round(lat, 3), round(lon, 3))
                i = idxmap(pcol).get(key)
                if i is None: continue
                s = pd.Series(f["properties"]["parameter"][PARAMS[pcol]]).sort_index()
                v = s.values.astype(np.float32); v[v == -999.0] = np.nan
                idxs.append(i); rows.append(v)
                klat.append(key[0]); klon.append(key[1])
            if not idxs:
                raise RuntimeError(f"no returned point matched the {pcol} grid "
                                   f"({len(feats)} features) - wrong grid for this parameter?")
            idxs = np.array(idxs, dtype=np.int64); vals = np.array(rows, dtype=np.float32)
            fill_from(idxs, vals, pcol, yr)
            # Store coordinates, not indices, so the cache survives a change of
            # cell set (see the loader above).
            np.savez_compressed(cp, vals=vals,
                                lat=np.array(klat, dtype=np.float64),
                                lon=np.array(klon, dtype=np.float64))
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
            tripped.set(); print("CIRCUIT BREAKER: sustained 429s, aborting pass (driver will retry)", flush=True)

t0 = time.time()
with ThreadPoolExecutor(WORKERS) as ex:
    futs = [ex.submit(do, j) for j in jobs]
    for k, _ in enumerate(as_completed(futs), 1):
        if k % 200 == 0:
            el = time.time() - t0
            print(f"  [{k}/{len(jobs)}] ok={prog['ok']} cache={prog['cache']} fail={prog['fail']} "
                  f"{k/el:.1f}/s ETA {(len(jobs)-k)/(k/el)/60:.0f}m", flush=True)
ncache = len([1 for j in jobs if os.path.exists(cpath(j))])
print(f"fetch: ok={prog['ok']} cache={prog['cache']} fail={prog['fail']} | cached {ncache}/{len(jobs)} in {time.time()-t0:.0f}s", flush=True)
if ncache < len(jobs):
    print(f"** FETCH INCOMPLETE ({len(jobs)-ncache} missing, 429 throttle). Cache saved. "
          f"RE-RUN (same cmd) to fetch the rest — writing is skipped until fetch is complete. **", flush=True)
    sys.exit(2)   # distinct code: fetch incomplete, safe to re-run
print("fetch complete — writing .WTH files ...", flush=True)

# ---- vectorized .WTH writing ----
def header_meta(c5):
    """Station code and elevation for the .WTH header.

    The US run copied both from an earlier .WTH for the same cell. Brazil has no
    such predecessor, so SRC_WTH is None and every cell falls back to ELEV = -99
    (DSSAT's missing marker). That is a known gap, not an oversight: elevation
    enters the ET calculation via atmospheric pressure, and the Brazilian cells
    span roughly sea level to 1000 m on the Cerrado plateaux, so it is worth
    filling from a DEM. Doing so needs no refetch — the POWER cache holds the
    weather, and only these header lines change."""
    if SRC_WTH:
        try:
            L = open(f"{SRC_WTH}/{c5}.WTH").read().splitlines()
            for i, l in enumerate(L):
                if l.lstrip().startswith("@ INSI"):
                    s = L[i + 1]
                    try: elev = float(s[25:31])
                    except ValueError: elev = -99.0
                    return (s[2:6].strip() or "WSTA"), elev
        except Exception:
            pass
    return "USAW", -99.0
DATEP = np.array([f"{d.year:04d}{d.dayofyear:03d}" for d in dates])
def col(a): return np.char.mod("%6.1f", np.where(np.isnan(a), -99.0, a))
tw = time.time(); w = 0
for c5, x, y in cells:
    i = pidx[cell_center[c5]]
    j = sidx[cell_scen[c5]]
    sr, tx, tn, rn = A["SRAD"][j], A["TMAX"][i], A["TMIN"][i], A["RAIN"][i]
    insi, elev = header_meta(c5)
    tmean = np.nanmean([np.nanmean(tx), np.nanmean(tn)]) if not np.all(np.isnan(tx)) else -99.0
    df = pd.DataFrame({"date": dates, "TMAX": tx, "TMIN": tn})
    tav, amp = compute_tav_amp(df) if not np.all(np.isnan(tx)) else (-99.0, 0.0)
    body = np.char.add(np.char.add(np.char.add(np.char.add(DATEP, col(sr)), col(tx)), col(tn)), col(rn))
    txt = (f"$WEATHER DATA : CELL5M {c5}  LAT {y:.4f}  LON {x:.4f}\n"
           "@ INSI      LAT     LONG  ELEV   TAV   AMP REFHT WNDHT\n"
           f"  {insi:<4}{y:10.3f}{x:9.3f}{elev:6.1f}{tav:6.1f}{amp:6.1f}{2.0:6.1f}{2.0:6.1f}\n"
           "@  DATE  SRAD  TMAX  TMIN  RAIN\n" + "\n".join(body) + "\n")
    tmp = f"{OUT}/{c5}.WTH.tmp"; open(tmp, "w").write(txt); os.replace(tmp, f"{OUT}/{c5}.WTH")
    w += 1
    if w % 10000 == 0: print(f"  wrote {w}/{len(cells)} ({(time.time()-tw):.0f}s)", flush=True)
print(f"\nDONE: {w} .WTH written -> {OUT} (total {time.time()-t0:.0f}s)", flush=True)
