#!/usr/bin/env python3
"""Phase 3 step 2: simulated yield anomalies by ENSO phase (mechanistic line), plus INE per-event anomalies (statistical line).
Usage: python3 analysis/phase3_yield_composites.py runs/<v8 folder>
Outputs in derived/phase3/: yield_composites_simulated.csv, yield_series_simulated.csv, ine_event_anomalies.csv, analogue_events_simulated.csv"""
import sys, os, json, numpy as np, pandas as pd
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); OUT = f'{ROOT}/derived/phase3'; RUN = sys.argv[1].rstrip('/'); rng = np.random.default_rng(11)
enso = pd.read_csv(f'{ROOT}/derived/enso_classification_1983-2024.csv').set_index('sow_year')
cy = pd.read_csv(f'{RUN}/combinedOutput_cellyear.csv.gz'); cy['area_ha'] = cy.area_ha.fillna(0)
NAME = {'SB': 'Soya', 'MZ': 'Maíz', 'RI': 'Arroz', 'SG': 'Sorgo', 'WH': 'Trigo'}
def boot_ci(x, n=3000):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 3: return (np.nan, np.nan)
    m = rng.choice(x, (n, len(x))).mean(axis=1); return (np.percentile(m, 2.5), np.percentile(m, 97.5))
def detrended_anom(s):
    """s: Series indexed by sow_year (area-weighted yield). Linear detrend; anomaly in % of trend mean."""
    y = s.values.astype(float); x = s.index.values.astype(float); ok = ~np.isnan(y)
    b, a = np.polyfit(x[ok], y[ok], 1); fit = a + b * x; return pd.Series((y - fit) / fit.mean() * 100, index=s.index), b / fit.mean() * 100
series_rows, comp_rows = [], []
groups = [(('Bolivia', 'all', crop), g) for crop, g in cy.groupby('CropCode')] + [((d, z, c), g) for (d, z, c), g in cy.groupby(['departamento', 'zone', 'CropCode']) if g.CELL5M.nunique() >= 5] + [(('Bolivia', z, c), g) for (z, c), g in cy.groupby(['zone', 'CropCode']) if g.CELL5M.nunique() >= 5]
for (dep, zone, crop), g in groups:
    s = g.groupby('sow_year').apply(lambda d: np.average(d.yield_kg_ha, weights=d.area_ha) if d.area_ha.sum() > 0 else np.nan)
    fail = g.groupby('sow_year').failed.mean()
    if s.notna().sum() < 30: continue
    anom, trend = detrended_anom(s)
    for y in s.index: series_rows.append({'departamento': dep, 'zone': zone, 'crop': crop, 'sow_year': y, 'yield_kg_ha': s[y], 'anom_detrended_pct': anom[y], 'fail_share': fail[y], 'phase': enso.phase.get(y), 'category': enso.category.get(y), 'oni_djf': enso.oni_djf.get(y)})
    sj = anom.to_frame('v').join(enso[['phase', 'category', 'strong_EP_analogue']]); neutral = sj[sj.phase == 'neutral'].v
    for ph, sel in [('El Niño', sj.phase == 'El Niño'), ('La Niña', sj.phase == 'La Niña'), ('neutral', sj.phase == 'neutral'), ('strong El Niño (ONI≥1.5)', sj.category == 'strong El Niño'), ('strong EP analogues 1997/2015/2023', sj.strong_EP_analogue)]:
        v = sj[sel].v; lo, hi = boot_ci(v); dlo, dhi = boot_ci(v) if len(v) >= 3 else (np.nan, np.nan)
        # CI on the difference vs neutral by independent resampling of both groups
        if len(v) >= 3:
            diff = rng.choice(v.values, (3000, len(v))).mean(axis=1) - rng.choice(neutral.values, (3000, len(neutral))).mean(axis=1); dlo, dhi = np.percentile(diff, 2.5), np.percentile(diff, 97.5)
        comp_rows.append({'departamento': dep, 'zone': zone, 'crop': crop, 'n_cells': g.CELL5M.nunique(), 'area_kha': g.drop_duplicates('CELL5M').area_ha.sum() / 1000, 'trend_pct_per_yr': trend, 'phase': ph, 'n_years': int(v.notna().sum()),
                          'mean_anom_pct': v.mean(), 'ci_lo': lo, 'ci_hi': hi, 'diff_vs_neutral': v.mean() - neutral.mean(), 'diff_ci_lo': dlo, 'diff_ci_hi': dhi, 'distinct_from_neutral': bool((dlo > 0) or (dhi < 0)) if not np.isnan(dlo) else False,
                          'min_anom_pct': v.min(), 'worst_year': int(v.idxmin()) if v.notna().any() else None, 'years': ' '.join(str(y) for y in v.index)})
ser = pd.DataFrame(series_rows); comp = pd.DataFrame(comp_rows); ser.to_csv(f'{OUT}/yield_series_simulated.csv', index=False); comp.to_csv(f'{OUT}/yield_composites_simulated.csv', index=False)
pd.set_option('display.width', 240)
nat = comp[(comp.departamento == 'Bolivia') & (comp.zone == 'all')]
print('SIMULATED national detrended yield anomaly (% ) by crop and phase  [mean, 95% CI of the phase mean]')
for ph in ['El Niño', 'La Niña', 'neutral', 'strong El Niño (ONI≥1.5)', 'strong EP analogues 1997/2015/2023']:
    t = nat[nat.phase == ph]; print(f'  {ph:36s}', '  '.join(f"{NAME[r.crop]} {r.mean_anom_pct:+5.1f} [{r.ci_lo:+.0f},{r.ci_hi:+.0f}]{'*' if r.distinct_from_neutral else ' '}" for r in t.itertuples()))
print('  * = difference from neutral years has a 95% bootstrap CI excluding zero')
print('\nby zone, El Niño vs La Niña (mean anomaly %):'); z = comp[(comp.departamento == 'Bolivia') & (comp.zone != 'all') & comp.phase.isin(['El Niño', 'La Niña', 'strong EP analogues 1997/2015/2023'])]
print(z.pivot_table(index=['crop', 'zone'], columns='phase', values='mean_anom_pct').round(1).to_string())
# ---- analogue events: per crop x department x zone anomaly in 1997, 2015, 2023 (+ 1991, 2009 moderate/strong CP for contrast)
ev = ser[ser.sow_year.isin([1991, 1997, 2009, 2015, 2023])].pivot_table(index=['crop', 'departamento', 'zone'], columns='sow_year', values='anom_detrended_pct').round(1)
ev.to_csv(f'{OUT}/analogue_events_simulated.csv'); print('\nanalogue events, national:'); print(ev.loc[(slice(None), 'Bolivia', 'all'), :].droplevel([1, 2]).to_string())
# ---- INE statistical line: detrended departmental anomalies 2012-2024 for El Niño campaigns in the overlap
ine = pd.read_csv(f'{ROOT}/derived/ine_yields_depto_campaign_2012-2024.csv'); rows = []
for (dep, crop, season), g in ine.groupby(['departamento', 'crop', 'season']):
    g = g.dropna(subset=['yield_kg_ha']).sort_values('sow_year')
    if len(g) < 9 or g.area_ha.mean() < 500: continue
    anom, trend = detrended_anom(g.set_index('sow_year').yield_kg_ha)
    for y, v in anom.items(): rows.append({'departamento': dep, 'crop': crop, 'season': season, 'sow_year': y, 'ine_anom_detrended_pct': v, 'phase': enso.phase.get(y), 'category': enso.category.get(y), 'area_ha': g.set_index('sow_year').area_ha.get(y)})
ia = pd.DataFrame(rows); ia.to_csv(f'{OUT}/ine_event_anomalies.csv', index=False)
print('\nINE (observed) detrended anomaly %, national (Bolivia row), El Niño campaigns in 2012-2024:')
print(ia[(ia.departamento == 'Bolivia') & (ia.phase == 'El Niño')].pivot_table(index=['crop', 'season'], columns='sow_year', values='ine_anom_detrended_pct').round(1).to_string())
print('\nINE phase means 2012-2024 (national, n years in brackets):')
t = ia[ia.departamento == 'Bolivia'].groupby(['crop', 'season', 'phase']).ine_anom_detrended_pct.agg(['mean', 'count']).round(1); print(t.unstack('phase').to_string())
