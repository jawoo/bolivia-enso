#!/usr/bin/env python3
"""Station arbiter summary: per station, annual precipitation (obs / POWER / ERA5-Open-Meteo), monthly correlation, NDJFM interannual
anomaly correlation, and mean-temperature bias (reanalysis minus station). Reads debug/openmeteo/station_monthly.csv."""
import os, numpy as np, pandas as pd
D = os.path.expanduser('~/Claude/bolivia-enso/debug/openmeteo'); df = pd.read_csv(f'{D}/station_monthly.csv')
rows = []
for s, g in df.groupby('station'):
    r = dict(station=s[:22], alt=g.alt.iloc[0], elev_om=g.elev_om.iloc[0] if 'elev_om' in g else np.nan, power_grid=g.power_grid.iloc[0])
    gp = g.dropna(subset=['p', 'p_power', 'p_om']) if 'p_om' in g else g.dropna(subset=['p', 'p_power'])
    r['n_mon'] = len(gp); r['P_obs'] = gp.p.mean() * 12
    for src in ['power', 'om']:
        c = f'p_{src}'
        if c not in gp: continue
        r[f'P_{src}'] = gp[c].mean() * 12; r[f'rP_m_{src}'] = gp.p.corr(gp[c])
        t = gp.copy(); t['sy'] = np.where(t.month >= 11, t.year, t.year - 1); t = t[t.month.isin([11, 12, 1, 2, 3])].groupby('sy').agg(p=('p', 'sum'), x=(c, 'sum'), n=('p', 'size')); t = t[t.n == 5]
        r[f'rP_ndjfm_{src}'] = t.p.corr(t.x); r['n_seas'] = len(t)
    if 't' in g:
        gt = g.dropna(subset=['t', 'tmax_power', 'tmin_power'])
        r['T_obs'] = gt.t.mean(); r['dT_power'] = ((gt.tmax_power + gt.tmin_power) / 2 - gt.t).mean()
        if 'tmax_om' in gt: gt2 = gt.dropna(subset=['tmax_om', 'tmin_om']); r['dT_om'] = ((gt2.tmax_om + gt2.tmin_om) / 2 - gt2.t).mean()
    if 'tmax' in g and g.tmax.notna().any():
        gt = g.dropna(subset=['tmax', 'tmin', 'tmax_power', 'tmin_power'])
        r['dTmax_power'] = (gt.tmax_power - gt.tmax).mean(); r['dTmin_power'] = (gt.tmin_power - gt.tmin).mean()
        if 'tmax_om' in gt: r['dTmax_om'] = (gt.tmax_om - gt.tmax).mean(); r['dTmin_om'] = (gt.tmin_om - gt.tmin).mean()
    rows.append(r)
out = pd.DataFrame(rows).sort_values('alt'); out.to_csv(f'{D}/compare_stations.csv', index=False)
pd.set_option('display.width', 250)
print('P_* = mean annual precipitation (mm); rP_m = monthly correlation with station; rP_ndjfm = interannual correlation of NDJFM totals;')
print('dT = mean (Tmax+Tmin)/2 minus station mean temperature (°C); power = NASA POWER nearest MERRA-2 point; om = Open-Meteo era5_seamless at station coords')
print(out.round(2).to_string(index=False))
print('\nmedians:'); print(out.median(numeric_only=True).round(2).to_string())
print('\nabsolute annual-precipitation error, median over stations (% of obs):')
for src in ['power', 'om']:
    if f'P_{src}' in out: print(f'  {src}: {(100 * (out[f"P_{src}"] - out.P_obs).abs() / out.P_obs).median():.0f}%   (median signed: {(100 * (out[f"P_{src}"] - out.P_obs) / out.P_obs).median():+.0f}%)')
