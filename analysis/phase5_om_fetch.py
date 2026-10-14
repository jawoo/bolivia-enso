#!/usr/bin/env python3
"""Phase 5: fetch Open-Meteo ECMWF seasonal members (EC46 -> SEAS5, `ecmwf_seasonal_seamless`) for every forecast grid point
that the modelled cells fall on, plus the monthly ensemble means and anomalies needed for the bias adjustment (PLAN.md s12).

Grid: the seasonal API serves ECMWF's O320 octahedral reduced-Gaussian grid (~36 km). It is reproduced locally (640 Gaussian
latitudes; row k from the pole has 4k+16 points), which matches the lat/lon the API reports to 1e-5 deg, so cells are mapped
to points without any API calls. 483 points cover the 3,568 cropland cells.

Per point, two requests, cached as derived/phase5/om/<run>/<lat>_<lon>.json.gz:
  daily   temperature_2m_max/min, precipitation_sum, shortwave_radiation_sum x 51 members, past_days=14 (archived lead-1
          values that bridge POWER's ~7-day lag), forecast_days=210
  monthly temperature_2m_mean, precipitation_mean, shortwave_radiation_mean + their anomalies vs the model hindcast climate
Cost: ~270 free-tier "calls" per point (free tier: 600/min, 5k/h, 10k/day -> ~18 points/h). With OPEN_METEO_API_KEY set, or a key in
~/.config/open-meteo/apikey, the customer endpoint is used (no rate limit on paid tiers).

Usage: python3 analysis/phase5_om_fetch.py [--cells sample|all] [--run YYYY-MM-DD] [--workers N]
  --cells sample  = the 16 cells in debug/openmeteo/sample_cells.csv (one point each); all = derived/cells_bolivia_mapspam2020.csv
  --run           = run date label (default today, UTC); the cache is per run date
Exit 2 if any point is still missing (rerun to resume)."""
import os, sys, json, gzip, time, argparse, urllib.request, urllib.parse, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np, pandas as pd

ROOT = os.path.expanduser('~/Claude/bolivia-enso')
ap = argparse.ArgumentParser(); ap.add_argument('--cells', default='all'); ap.add_argument('--run', default=dt.datetime.utcnow().strftime('%Y-%m-%d'))
ap.add_argument('--workers', type=int, default=None); ap.add_argument('--forecast_days', type=int, default=210); ap.add_argument('--past_days', type=int, default=14)
a = ap.parse_args()
KEYFILE = os.path.expanduser('~/.config/open-meteo/apikey')      # paid key: env var OPEN_METEO_API_KEY, else this file (chmod 600), never in the repo
KEY = os.environ.get('OPEN_METEO_API_KEY') or (open(KEYFILE).read().strip() if os.path.exists(KEYFILE) else None); HOST = 'https://customer-seasonal-api.open-meteo.com' if KEY else 'https://seasonal-api.open-meteo.com'
WORKERS = a.workers or (4 if KEY else 1)
OUT = f'{ROOT}/derived/phase5/om/{a.run}'; os.makedirs(OUT, exist_ok=True)

# ---- O320 grid
_x, _ = np.polynomial.legendre.leggauss(640); GLATS = np.degrees(np.arcsin(_x))            # ascending, -89.86 .. 89.86
def snap(lat, lon):
    i = int(np.argmin(np.abs(GLATS - lat))); k = min(i, 639 - i) + 1; n = 4 * k + 16
    j = int(np.round(((lon + 360) % 360) / (360 / n))) % n; plon = j * 360 / n; plon = plon - 360 if plon > 180 else plon
    return round(float(GLATS[i]), 5), round(float(plon), 5)

CELLS = {'sample': f'{ROOT}/debug/openmeteo/sample_cells.csv', 'all': f'{ROOT}/derived/cells_bolivia_mapspam2020.csv'}.get(a.cells, a.cells)   # or a path to a csv with CELL5M,x,y
LABEL = a.cells if a.cells in ('sample', 'all') else os.path.splitext(os.path.basename(a.cells))[0]
cells = pd.read_csv(CELLS)
cells[['plat', 'plon']] = [snap(y, x) for x, y in zip(cells.x, cells.y)]
cells[['CELL5M', 'x', 'y', 'plat', 'plon']].to_csv(f'{OUT}/cell_points_{LABEL}.csv', index=False)
points = cells[['plat', 'plon']].drop_duplicates().values.tolist()
print(f'{len(cells)} cells -> {len(points)} forecast points; run {a.run}; endpoint {HOST}; workers {WORKERS}', flush=True)

def get(url, tries=5):
    for t in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=300) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            if e.code == 429:
                wait = 65 if 'Minutely' in body else (600 if 'Hourly' in body else 3600)
                print(f'  429 ({body[:60]}); waiting {wait}s', flush=True); time.sleep(wait); continue
            return {'error': body}
        except Exception as e: print('  ERR', type(e).__name__, str(e).replace(KEY, '***') if KEY else e, flush=True); time.sleep(10)
    return {'error': 'gave up'}

def fetch(pt):
    plat, plon = pt; path = f'{OUT}/{plat}_{plon}.json.gz'
    if os.path.exists(path): return pt, 'cached'
    common = dict(latitude=plat, longitude=plon, models='ecmwf_seasonal_seamless', timezone='GMT')
    if KEY: common['apikey'] = KEY
    qd = dict(common, daily='temperature_2m_max,temperature_2m_min,precipitation_sum,shortwave_radiation_sum', past_days=a.past_days, forecast_days=a.forecast_days)
    qm = dict(common, monthly='temperature_2m_mean,precipitation_mean,shortwave_radiation_mean,temperature_2m_anomaly,precipitation_anomaly,shortwave_radiation_anomaly')
    for attempt in range(8):      # some responses lack the last month of the accumulated fields (rain, SRAD) while temperature is complete; refetch
        jd = get(f'{HOST}/v1/seasonal?' + urllib.parse.urlencode(qd))
        if 'daily' not in jd: return pt, f'daily failed: {jd.get("error", jd.get("reason"))}'
        last = {v: max((t for t, x in zip(jd['daily']['time'], jd['daily'][v]) if x is not None), default='') for v in ('temperature_2m_max', 'precipitation_sum', 'shortwave_radiation_sum')}
        if min(last.values()) >= last['temperature_2m_max']: break
        print(f'  {pt}: rain/SRAD end {min(last.values())} vs temperature {last["temperature_2m_max"]}; refetch {attempt + 1}', flush=True); time.sleep(2)
    else: return pt, f'daily failed: horizon mismatch persists ({last})'
    jm = get(f'{HOST}/v1/seasonal?' + urllib.parse.urlencode(qm))
    if 'monthly' not in jm: return pt, f'monthly failed: {jm.get("error", jm.get("reason"))}'
    if abs(jd['latitude'] - plat) > 0.01 or abs(jd['longitude'] - plon) > 0.01: print(f'  grid mismatch at {pt}: API {jd["latitude"]},{jd["longitude"]}', flush=True)
    rec = dict(run=a.run, fetched=dt.datetime.utcnow().isoformat(), point=[plat, plon], api_point=[jd['latitude'], jd['longitude']], elevation=jd.get('elevation'),
               daily=jd['daily'], daily_units=jd['daily_units'], monthly=jm['monthly'], monthly_units=jm['monthly_units'])
    with gzip.open(path + '.tmp', 'wt') as f: json.dump(rec, f)
    os.replace(path + '.tmp', path); return pt, 'ok'

t0 = time.time(); status = {}
with ThreadPoolExecutor(WORKERS) as ex:
    futs = [ex.submit(fetch, tuple(p)) for p in points]
    for n, fu in enumerate(as_completed(futs), 1):
        pt, st = fu.result(); status[st.split(':')[0]] = status.get(st.split(':')[0], 0) + 1
        if st not in ('ok', 'cached') or n % 25 == 0: print(f'  [{n}/{len(points)}] {pt} {st}  ({time.time() - t0:.0f} s)', flush=True)
missing = len(points) - status.get('ok', 0) - status.get('cached', 0)
print(f'done: {status}; missing {missing}; {time.time() - t0:.0f} s; cache {OUT}')
sys.exit(2 if missing else 0)
