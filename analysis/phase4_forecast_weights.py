#!/usr/bin/env python3
"""Forecast-conditioned analogue weights for the 2026/27 campaign.
Compares each SEAS5 ensemble member's forecast anomaly (NDJFM precipitation rate and 2 m temperature, zone means
over Bolivia) with each analogue year's observed POWER anomaly for the same months and zones, and turns the
distances into analogue weights (Gaussian kernel, averaged over members). Output: derived/phase4/analogue_weights_<init>.csv
Usage: python3 analysis/phase4_forecast_weights.py derived/phase4/c3s/seas5_2026-09_bolivia.nc"""
import sys, os, json, numpy as np, pandas as pd, xarray as xr
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); nc = sys.argv[1]; init = os.path.basename(nc).split('_')[1]
ds = xr.open_dataset(nc).squeeze(drop=True); print({v: ds[v].attrs.get('units') for v in ds.data_vars}, dict(ds.sizes))
# --- SEAS5: members x leadtime -> NDJFM mean anomaly per zone (zone masks from the modelled cells' elevation)
cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv'); elev = pd.read_csv(f'{ROOT}/derived/cells_elev_tav.csv').set_index('CELL5M').elev
cells['zone'] = pd.cut(cells.CELL5M.map(elev), [-1, 800, 2800, 9999], labels=['lowland', 'valleys', 'altiplano']).astype(str)
latn = [c for c in ds.coords if c.startswith('lat')][0]; lonn = [c for c in ds.coords if c.startswith('lon')][0]
tvar = [v for v in ds.data_vars if v.startswith('t2') or 'temperature' in v][0]; pvar = [v for v in ds.data_vars if v.startswith('tp') or 'precip' in v][0]
timedim = 'forecastMonth' if 'forecastMonth' in ds.dims else [d for d in ds[tvar].dims if d not in ('number', latn, lonn)][0]
# lead months: init month m0 -> valid months; keep Nov..Mar
m0 = int(init.split('-')[1]); valid_month = {i: ((m0 + i - 1) % 12) + 1 for i in range(1, 8)}
tvals = ds[timedim].values
if np.issubdtype(tvals.dtype, np.datetime64): months = pd.DatetimeIndex(tvals).month
else: months = np.array([valid_month.get(int(l), -1) for l in tvals])
keep = np.isin(months, [11, 12, 1, 2, 3]); print('valid months kept (lead months):', list(zip(tvals[keep], months[keep])))
rows = []
for z, g in cells.groupby('zone'):
    lat = xr.DataArray(g.y.values, dims='pt'); lon = xr.DataArray(g.x.values, dims='pt')
    sub = ds.sel({latn: lat, lonn: lon}, method='nearest').isel({timedim: keep})
    t = sub[tvar].mean(('pt', timedim)); p = sub[pvar].mean(('pt', timedim))   # per member
    for n in range(sub.sizes['number']): rows.append({'zone': z, 'member': int(sub.number.values[n]), 't2m_anom': float(t.isel(number=n)), 'tp_anom_rate': float(p.isel(number=n))})
fc = pd.DataFrame(rows); fc.to_csv(f'{ROOT}/derived/phase4/seas5_{init}_zone_member_anomalies.csv', index=False)
print('\nSEAS5 member anomalies (kept lead months) by zone (mean over members, and member spread):'); print(fc.groupby('zone')[['t2m_anom', 'tp_anom_rate']].agg(['mean', 'std', 'min', 'max']).round(3).to_string())
# --- observed analogue anomalies (POWER cells, NDJFM ~ Nov-Mar season indicators already cached)
w = pd.read_csv(f'{ROOT}/derived/cell_season_weather_1983-2024.csv.gz'); w['zone'] = w.CELL5M.map(cells.set_index('CELL5M').zone)
area = {json.loads(l)['cell5m']: sum(c['area'] for c in json.loads(l)['crops']) for l in open(f'{ROOT}/Tapiti/res/input/unit-information.jsonl')}; w['w'] = w.CELL5M.map(area)
obs = w.groupby(['zone', 'sow_year']).apply(lambda d: pd.Series({'rain': np.average(d.rain_v, weights=d.w), 'tmax': np.average(d.tmax_v, weights=d.w)})).reset_index()
obs['rain_anom_pct'] = obs.groupby('zone').rain.transform(lambda s: (s - s.mean()) / s.mean() * 100); obs['t_anom'] = obs.groupby('zone').tmax.transform(lambda s: s - s.mean())
# --- forecast precipitation anomaly rate (m/s or mm/day?) -> % of climatology: use POWER zone climatology (mm/day over NDJFM)
clim_mmday = obs.groupby('zone').rain.mean() / 151.0   # Nov-Mar POWER climatology, mm/day
unit_scale = 86400 * 1000 if fc.tp_anom_rate.abs().max() < 1e-3 else 1.0   # m s-1 -> mm day-1 if needed
fc['tp_anom_pct'] = fc.apply(lambda r: r.tp_anom_rate * unit_scale / clim_mmday[r.zone] * 100, axis=1)
fc.to_csv(f'{ROOT}/derived/phase4/seas5_{init}_zone_member_anomalies.csv', index=False)
print('\nSEAS5 Nov-Mar precipitation anomaly as % of POWER climatology, by zone (member mean / p10 / p90):'); print(fc.groupby('zone').tp_anom_pct.describe(percentiles=[.1, .9])[['mean', '10%', '90%']].round(1).to_string())
# --- distance in standardized (rain %, temperature) space, per member, averaged across zones -> weights
sd_r = obs.rain_anom_pct.std(); sd_t = obs.t_anom.std(); rows = []
for A, ga in obs.groupby('sow_year'):
    ga = ga.set_index('zone'); dists = []
    for mbr, gm in fc.groupby('member'):
        gm = gm.set_index('zone'); z = [zz for zz in ga.index if zz in gm.index]
        d2 = np.mean([((ga.loc[zz, 'rain_anom_pct'] - gm.loc[zz, 'tp_anom_pct']) / sd_r) ** 2 + ((ga.loc[zz, 't_anom'] - gm.loc[zz, 't2m_anom']) / sd_t) ** 2 for zz in z]); dists.append(d2)
    dists = np.array(dists); rows.append({'sow_year': A, 'mean_sq_dist': dists.mean(), 'weight_raw': np.mean(np.exp(-0.5 * dists))})
wt = pd.DataFrame(rows); wt['weight'] = wt.weight_raw / wt.weight_raw.sum(); wt = wt.merge(pd.read_csv(f'{ROOT}/derived/enso_classification_1983-2024.csv')[['sow_year', 'campaign', 'category', 'strong_EP_analogue']], on='sow_year')
wt.sort_values('weight', ascending=False).to_csv(f'{ROOT}/derived/phase4/analogue_weights_{init}.csv', index=False)
print(f'\nforecast-conditioned analogue weights (SEAS5 init {init}); top 12:'); print(wt.sort_values('weight', ascending=False).head(12)[['campaign', 'category', 'weight', 'mean_sq_dist']].round(3).to_string(index=False))
print('weight on El Niño analogues: %.2f; on strong EP analogues: %.2f; on La Niña: %.2f' % (wt[wt.category.str.contains('Niño')].weight.sum(), wt[wt.strong_EP_analogue].weight.sum(), wt[wt.category.str.contains('Niña')].weight.sum()))
