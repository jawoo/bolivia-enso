#!/usr/bin/env python3
"""Phase 5: forecast-spliced weather for the 2026/27 campaign, one directory per ECMWF ensemble member (PLAN.md s12).

For each cell and member m:  observed NASA POWER (1981-2026_bol .WTH) from 1 Jan 2025 to its last day L
                             -> Open-Meteo ecmwf_seasonal_seamless member m (EC46 then SEAS5), bias-adjusted, L+1 .. F
                             -> weather of the top-weighted Phase 4 analogue year, F+1 .. 31 Dec 2027
Bias adjustment (monthly, interpolated to the day): the model's monthly climatology at the forecast point is
(monthly ensemble mean - monthly anomaly) as served by the API; the target is the POWER 1991-2020 climatology of the cell.
Tmax and Tmin are shifted separately by (POWER monthly Tmax|Tmin climatology - model monthly Tmax|Tmin climatology), where the
model's Tmax|Tmin climatology is the ensemble-mean monthly Tmax|Tmin of the daily members minus the API's mean-temperature
anomaly (the same anomaly is assumed for max and min). Adjusting both by the mean-temperature delta alone (first version,
runs/phase5/2026-10-14/v1_meanshift) left a +0.6 C warm bias (the API's true daily mean sits ~0.6 C below (Tmax+Tmin)/2)
and a further +0.7 C on Tmin / -0.7 C on Tmax from the model's narrower diurnal range. Rain and SRAD are scaled by
(POWER / model) monthly totals (the API's monthly means are the monthly totals of the ensemble mean), the rain factor
clipped to [0.2, 5] and the SRAD factor to [0.5, 2]. Members keep their own daily wet/dry sequence.
Writes Tapiti/res/weather/2026_fc_<mm>/<CELL5M>.WTH (mm = 00 control .. 50) and derived/phase5/<run>/splice.json.

Usage: python3 prep/gen_weather_forecast.py [--run YYYY-MM-DD] [--cells sample|all] [--members 0-50 | 0,1,7] [--analogue YEAR]"""
import os, sys, json, gzip, glob, time, argparse, datetime as dt
import numpy as np, pandas as pd

ROOT = os.path.expanduser('~/Claude/bolivia-enso'); SRC = f'{ROOT}/Tapiti/res/weather/1981-2026_bol'
ap = argparse.ArgumentParser(); ap.add_argument('--run', default=None); ap.add_argument('--cells', default='all'); ap.add_argument('--members', default='0-50'); ap.add_argument('--analogue', type=int, default=None)
a = ap.parse_args()
runs = sorted(os.listdir(f'{ROOT}/derived/phase5/om')); RUN = a.run or runs[-1]; OM = f'{ROOT}/derived/phase5/om/{RUN}'
members = list(range(int(a.members.split('-')[0]), int(a.members.split('-')[1]) + 1)) if '-' in a.members else [int(m) for m in a.members.split(',')]
START, END = pd.Timestamp('2025-01-01'), pd.Timestamp('2027-12-31'); tgt = pd.date_range(START, END, freq='D')
CLIM0, CLIM1 = 1991, 2020

# ---- analogue year for the tail: highest weight in the latest Phase 4 weight file
if a.analogue is None:
    wf = sorted(glob.glob(f'{ROOT}/derived/phase4/analogue_weights_*.csv'))[-1]; w = pd.read_csv(wf); A = int(w.sort_values('weight', ascending=False).sow_year.iloc[0])
else: A, wf = a.analogue, 'argument'
print(f'run {RUN}; members {members[0]}..{members[-1]} ({len(members)}); tail analogue {A}/{A+1} (from {wf})', flush=True)

LABEL = a.cells if a.cells in ('sample', 'all') else os.path.splitext(os.path.basename(a.cells))[0]
cp = pd.read_csv(f'{OM}/cell_points_{LABEL}.csv'); cp['pt'] = [f'{p}_{q}' for p, q in zip(cp.plat, cp.plon)]
def read_wth(path):
    L = open(path).read().split('\n'); k = next(i for i, l in enumerate(L) if l.startswith('@  DATE'))
    rows = [(int(l[0:7]), float(l[7:13]), float(l[13:19]), float(l[19:25]), float(l[25:31])) for l in L[k + 1:] if l.strip()]
    d = pd.DataFrame(rows, columns=['k', 'srad', 'tmax', 'tmin', 'rain']); d.index = pd.to_datetime((d.k // 1000).astype(str) + '-01-01') + pd.to_timedelta(d.k % 1000 - 1, unit='D')
    return L[:k + 1], d.drop(columns='k')
def mid(m, y): return pd.Timestamp(y, m, 15)
def daily_factor(monthly, dates):
    """monthly: {Timestamp(month start): value} -> value per date, linear between mid-months, held flat outside."""
    xs = np.array([(mid(t.month, t.year) - START).days for t in monthly]); ys = np.array(list(monthly.values())); o = np.argsort(xs)
    return np.interp((dates - START).days.values, xs[o], ys[o])

# ---- model monthly climatology per point (from the API's monthly mean and anomaly)
pts = {}
for pt in cp.pt.unique():
    j = json.load(gzip.open(f'{OM}/{pt}.json.gz', 'rt')); m = j['monthly']; t = pd.to_datetime(m['time'])
    clim = {}
    for v, mean, anom in [('p', 'precipitation_mean', 'precipitation_anomaly'), ('r', 'shortwave_radiation_mean', 'shortwave_radiation_anomaly')]:
        clim[v] = {ts: mm - aa for ts, mm, aa in zip(t, m[mean], m[anom]) if mm is not None and aa is not None}
    d = j['daily']; dates = pd.to_datetime(d['time'])
    def mem(v, k): return np.array(d[v if k == 0 else f'{v}_member{k:02d}'], dtype=float)
    tmax = np.stack([mem('temperature_2m_max', k) for k in range(51)]); tmin = np.stack([mem('temperature_2m_min', k) for k in range(51)])
    ens = pd.DataFrame({'tx': np.nanmean(tmax, axis=0), 'tn': np.nanmean(tmin, axis=0)}, index=dates).resample('MS').mean()
    anom_t = {ts: aa for ts, aa in zip(t, m['temperature_2m_anomaly']) if aa is not None}
    clim['tx'] = {ts: ens.tx[ts] - aa for ts, aa in anom_t.items() if ts in ens.index and not np.isnan(ens.tx[ts])}
    clim['tn'] = {ts: ens.tn[ts] - aa for ts, aa in anom_t.items() if ts in ens.index and not np.isnan(ens.tn[ts])}
    pts[pt] = dict(clim=clim, dates=dates, tmax=tmax, tmin=tmin,
                   rain=np.stack([mem('precipitation_sum', k) for k in range(51)]), srad=np.stack([mem('shortwave_radiation_sum', k) for k in range(51)]), units=j['daily_units']['shortwave_radiation_sum'])
    assert j['daily_units']['precipitation_sum'] == 'mm' and j['monthly_units']['precipitation_mean'] == 'mm'
print(f'{len(pts)} forecast points loaded', flush=True)

t0 = time.time(); splice_info = {}; stats = []
for n, c in enumerate(cp.itertuples(), 1):
    hdr, obs = read_wth(f'{SRC}/{c.CELL5M}.WTH'); P = pts[c.pt]
    L = obs.index.max(); obs_part = obs.loc[START:L]
    # POWER climatology 1991-2020 by calendar month
    cl = obs.loc[f'{CLIM0}':f'{CLIM1}']; g = cl.groupby(cl.index.month)
    pw = dict(tx=g.tmax.mean(), tn=g.tmin.mean(), p=(cl.rain.resample('MS').sum().groupby(lambda d: d.month).mean()), r=(cl.srad.resample('MS').sum().groupby(lambda d: d.month).mean()))
    fdates = P['dates']; fmask = fdates > L
    shift_x = daily_factor({ts: pw['tx'][ts.month] - v for ts, v in P['clim']['tx'].items()}, fdates); shift_n = daily_factor({ts: pw['tn'][ts.month] - v for ts, v in P['clim']['tn'].items()}, fdates)
    fp = daily_factor({ts: np.clip(pw['p'][ts.month] / max(v, 1.0), 0.2, 5.0) for ts, v in P['clim']['p'].items()}, fdates)
    fr = daily_factor({ts: np.clip(pw['r'][ts.month] / max(v, 1.0), 0.5, 2.0) for ts, v in P['clim']['r'].items()}, fdates)
    valid = ~np.isnan(P['tmax']).any(axis=0) & ~np.isnan(P['rain']).any(axis=0) & ~np.isnan(P['srad']).any(axis=0) & ~np.isnan(P['tmin']).any(axis=0)
    F = fdates[fmask & valid].max()
    fsel = fmask & valid & (fdates <= F)
    assert (fdates[fsel].min() - L).days == 1, f'{c.CELL5M}: forecast does not start the day after POWER ends ({L} -> {fdates[fsel].min()})'
    # analogue tail F+1 .. END, mapped by calendar date
    tail_dates = tgt[tgt > F]; sh = 2026 - A
    def src_day(d):
        try: return d.replace(year=d.year - sh)
        except ValueError: return (d - pd.Timedelta(days=1)).replace(year=d.year - sh)
    tail = obs.loc[[src_day(d) for d in tail_dates]].set_axis(tail_dates)
    if n == 1: splice_info = dict(run=RUN, power_last=str(L.date()), forecast_first=str((L + pd.Timedelta(days=1)).date()), forecast_last=str(F.date()), analogue_tail=A, tail_first=str((F + pd.Timedelta(days=1)).date()), members=members, cells=int(len(cp)))
    for m in members:
        tmax = P['tmax'][m][fsel] + shift_x[fsel]; tmin = P['tmin'][m][fsel] + shift_n[fsel]; tmin = np.minimum(tmin, tmax - 0.1)
        rain = np.maximum(P['rain'][m][fsel] * fp[fsel], 0); srad = np.clip(P['srad'][m][fsel] * fr[fsel], 0.1, 45)
        fc = pd.DataFrame({'srad': srad, 'tmax': tmax, 'tmin': tmin, 'rain': rain}, index=fdates[fsel])
        full = pd.concat([obs_part, fc, tail]); assert len(full) == len(tgt) and (full.index == tgt).all(), f'{c.CELL5M} m{m}: {len(full)} rows'
        out = f'{ROOT}/Tapiti/res/weather/2026_fc_{m:02d}'; os.makedirs(out, exist_ok=True)
        h0 = hdr[0] + f'  | 2026/27 forecast member {m:02d}: POWER to {L.date()}, ECMWF EC46/SEAS5 via Open-Meteo (run {RUN}, bias-adjusted) to {F.date()}, then analogue {A}/{A+1}'
        keys = full.index.year * 1000 + full.index.dayofyear
        rows = [f'{k:7d}{s:6.1f}{tx:6.1f}{tn:6.1f}{r:6.1f}' for k, s, tx, tn, r in zip(keys, full.srad, full.tmax, full.tmin, full.rain)]
        with open(f'{out}/{c.CELL5M}.WTH', 'w') as f: f.write('\n'.join([h0] + hdr[1:] + rows) + '\n')
        if m == members[0]:
            nd = (fdates[fsel] >= '2026-11-01') & (fdates[fsel] <= '2027-03-31'); ens_rain = float(np.nanmean(P['rain'][:, fsel][:, nd] * fp[fsel][nd], axis=0).sum())
            stats.append(dict(CELL5M=c.CELL5M, forecast_last=str(F.date()), shift_Tmax=float(np.mean(shift_x[fsel])), shift_Tmin=float(np.mean(shift_n[fsel])), f_rain=float(np.mean(fp[fsel])), f_srad=float(np.mean(fr[fsel])), fc_rain_NDJFM=float(fc.loc['2026-11-01':'2027-03-31'].rain.sum()), ens_rain_NDJFM=ens_rain, obs_clim_rain_NDJFM=float(pw['p'][[11, 12, 1, 2, 3]].sum())))
    if n % 200 == 0 or n == len(cp): print(f'  {n}/{len(cp)} cells, {time.time() - t0:.0f} s', flush=True)
os.makedirs(f'{ROOT}/derived/phase5/{RUN}', exist_ok=True); json.dump(splice_info, open(f'{ROOT}/derived/phase5/{RUN}/splice.json', 'w'), indent=1)
st = pd.DataFrame(stats); st.to_csv(f'{ROOT}/derived/phase5/{RUN}/bias_factors_{LABEL}.csv', index=False)
print(json.dumps(splice_info)); print('bias factors (mean over forecast days, member 00 cells):'); print(st.describe().loc[['mean', 'min', 'max']].round(2).to_string()); print('forecast horizon by cell count:', st.forecast_last.value_counts().to_dict())
