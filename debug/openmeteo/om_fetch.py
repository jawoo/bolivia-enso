import pandas as pd, numpy as np, json, time, urllib.request, urllib.parse, sys, os
S = os.path.dirname(os.path.abspath(__file__))
sel = pd.read_csv(f'{S}/sample_cells.csv')
def get(url, tries=4):
    for t in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]; print('HTTP', e.code, body, flush=True)
            if e.code == 429: time.sleep(30*(t+1)); continue
            return {'error': body}
        except Exception as e: print('ERR', str(e).replace(KEY, '***') if KEY else e, flush=True); time.sleep(5)
    return {'error': 'gave up'}
KEYFILE = os.path.expanduser('~/.config/open-meteo/apikey'); KEY = os.environ.get('OPEN_METEO_API_KEY') or (open(KEYFILE).read().strip() if os.path.exists(KEYFILE) else None)
ARCHIVE = ('https://customer-archive-api.open-meteo.com/v1/archive?' + (f'apikey={KEY}&' if KEY else '')) if KEY else 'https://archive-api.open-meteo.com/v1/archive?'
base = ARCHIVE
out = []
for r in sel.itertuples():
    for model, extra in [('era5_seamless', ''), ('era5_land', '&elevation=nan')]:
        cf = f'{S}/cache/{r.CELL5M}_{model}.csv'; os.makedirs(f'{S}/cache', exist_ok=True)
        if os.path.exists(cf): out.append(pd.read_csv(cf)); print(r.CELL5M, model, 'cached', flush=True); continue
        q = dict(latitude=r.y, longitude=r.x, start_date='1984-01-01', end_date='2024-12-31', timezone='GMT', models=model,
                 daily='temperature_2m_max,temperature_2m_min,precipitation_sum,shortwave_radiation_sum')
        j = get(base + urllib.parse.urlencode(q) + extra)
        if 'daily' not in j: print(r.CELL5M, model, j); continue
        d = pd.DataFrame(j['daily']); d['CELL5M'] = r.CELL5M; d['model'] = model + ('_noelev' if extra else ''); d['om_elev'] = j.get('elevation')
        print(r.CELL5M, r.departamento, r.zone, model, 'elev', j.get('elevation'), 'rows', len(d), flush=True)
        d.to_csv(cf, index=False); out.append(d); time.sleep(1)
pd.concat(out).to_csv(f'{S}/om_daily.csv.gz', index=False)
