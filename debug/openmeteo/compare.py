#!/usr/bin/env python3
"""Compare NASA POWER (.WTH in Tapiti/res/weather/1981-2026_bol) with Open-Meteo ERA5-based series for the 16 sample cells,
and POWER vs ERA5 vs SENAMHI station monthly precipitation. Reads debug/openmeteo/om_daily.csv.gz and station_compare_monthly.csv."""
import os, numpy as np, pandas as pd
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); D = f'{ROOT}/debug/openmeteo'
sel = pd.read_csv(f'{D}/sample_cells.csv').set_index('CELL5M')

def read_wth(c):
    L = open(f'{ROOT}/Tapiti/res/weather/1981-2026_bol/{c}.WTH').read().split('\n'); k = next(i for i, l in enumerate(L) if l.startswith('@  DATE'))
    rows = [(l[0:7], float(l[7:13]), float(l[13:19]), float(l[19:25]), float(l[25:31])) for l in L[k + 1:] if l.strip()]
    df = pd.DataFrame(rows, columns=['k', 'srad', 'tmax', 'tmin', 'rain']); df['time'] = pd.to_datetime(df.k.str[:4] + '-01-01') + pd.to_timedelta(df.k.str[4:].astype(int) - 1, unit='D')
    return df.drop(columns='k').set_index('time').loc['1984':'2024']

if os.path.exists(f'{D}/om_daily.csv.gz'):
    om = pd.read_csv(f'{D}/om_daily.csv.gz', parse_dates=['time'])
    om = om.rename(columns={'temperature_2m_max': 'tmax', 'temperature_2m_min': 'tmin', 'precipitation_sum': 'rain', 'shortwave_radiation_sum': 'srad'})
    rows = []; ndj = []
    for c, g in om.groupby('CELL5M'):
        pw = read_wth(c); z = sel.loc[c]
        for model, h in g.groupby('model'):
            h = h.set_index('time')[['tmax', 'tmin', 'rain', 'srad']].loc['1984':'2024']
            j = pw.join(h, rsuffix='_om', how='inner')
            r = dict(CELL5M=c, dept=z.departamento, zone=z.zone, elev_power=z.elev, elev_om=h.index.size and float(g[g.model == model].om_elev.iloc[0]), model=model)
            for v in ['tmax', 'tmin', 'srad']: r[f'{v}_bias'] = (j[f'{v}_om'] - j[v]).mean(); r[f'{v}_r'] = j[v].corr(j[f'{v}_om'])
            r['rain_power_yr'] = j.rain.mean() * 365.25; r['rain_om_yr'] = j.rain_om.mean() * 365.25
            m = j[['rain', 'rain_om']].resample('MS').sum(); r['rain_r_monthly'] = m.rain.corr(m.rain_om)
            # NDJFM season totals (sow year = year of N) and their interannual correlation
            s = m.copy(); s['sy'] = np.where(s.index.month >= 11, s.index.year, s.index.year - 1); s = s[s.index.month.isin([11, 12, 1, 2, 3])].groupby('sy').sum(); s = s.loc[1984:2023]
            r['ndjfm_power'] = s.rain.mean(); r['ndjfm_om'] = s.rain_om.mean(); r['ndjfm_anom_r'] = s.rain.corr(s.rain_om)
            rows.append(r); ndj.append(s.assign(CELL5M=c, model=model, zone=z.zone))
    out = pd.DataFrame(rows); out.to_csv(f'{D}/compare_cells.csv', index=False)
    pd.set_option('display.width', 250)
    print('=== POWER vs Open-Meteo, 16 sample cells, 1984-2024 (bias = OM - POWER, daily)')
    print(out.sort_values(['zone', 'model', 'elev_power']).round(2).to_string(index=False))
    print('\n=== zone means')
    print(out.groupby(['zone', 'model'])[['elev_power', 'elev_om', 'tmax_bias', 'tmin_bias', 'srad_bias', 'tmax_r', 'tmin_r', 'srad_r', 'rain_power_yr', 'rain_om_yr', 'rain_r_monthly', 'ndjfm_anom_r']].mean().round(2).to_string())

if os.path.exists(f'{D}/station_compare_monthly.csv'):
    st = pd.read_csv(f'{D}/station_compare_monthly.csv'); obs = pd.read_csv(f'{D}/senamhi_monthly_p.csv'); meta = pd.read_csv(f'{D}/station_meta.csv').set_index('file')
    df = st.merge(obs, on=['station', 'year', 'month'], how='inner').dropna(subset=['p'])
    rows = []
    for s, g in df.groupby('station'):
        g = g[(g.year >= 1984) & (g.year <= 2009)]; r = dict(station=s.replace('_09', '').replace('.xls', '').replace('.XLS', ''), alt=meta.loc[s, 'alt'], n_months=len(g), obs_yr=g.p.mean() * 12)
        for src in ['power', 'era5_seamless', 'era5']:
            if src not in g: continue
            r[f'{src}_yr'] = g[src].mean() * 12; r[f'{src}_r_m'] = g.p.corr(g[src])
            # NDJFM totals per season, anomaly correlation with station
            t = g.copy(); t['sy'] = np.where(t.month >= 11, t.year, t.year - 1); t = t[t.month.isin([11, 12, 1, 2, 3])].groupby('sy').agg(p=('p', 'sum'), x=(src, 'sum'), n=('p', 'size')); t = t[t.n == 5]
            r[f'{src}_r_ndjfm'] = t.p.corr(t.x); r['n_seasons'] = len(t)
        rows.append(r)
    out = pd.DataFrame(rows); out.to_csv(f'{D}/compare_stations.csv', index=False)
    print('\n=== SENAMHI station monthly precipitation vs POWER (nearest MERRA-2 point) vs Open-Meteo ERA5 at station coords, 1984-2009')
    print('(yr = mean annual total mm; r_m = monthly correlation; r_ndjfm = interannual correlation of NDJFM season totals)')
    print(out.round(2).to_string(index=False))
    print('\nmedian over stations:'); print(out.drop(columns='station').median(numeric_only=True).round(2).to_string())
