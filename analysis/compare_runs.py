#!/usr/bin/env python3
"""Side-by-side skill of two runs against INE: level ratio and anomaly correlation per crop
(national, INE-area-weighted) and per crop x departamento.
Usage: python3 analysis/compare_runs.py <A_vs_ine.csv> <B_vs_ine.csv> [labelA labelB]
(the *_vs_ine.csv files come from analysis/compare_ine.py)."""
import sys, numpy as np, pandas as pd
a, b = pd.read_csv(sys.argv[1]), pd.read_csv(sys.argv[2])
la, lb = (sys.argv[3], sys.argv[4]) if len(sys.argv) > 4 else ('A', 'B')
def stats(g):
    if len(g) < 5: return pd.Series({'ratio': np.nan, 'r': np.nan, 'n': len(g)})
    am, ai = g.yield_wmean - g.yield_wmean.mean(), g.yield_dry - g.yield_dry.mean()
    r = np.corrcoef(am, ai)[0, 1] if am.std() > 0 and ai.std() > 0 else np.nan
    return pd.Series({'ratio': g.yield_wmean.mean() / g.yield_dry.mean(), 'r': r, 'n': len(g)})
def national(x):
    n = x.groupby(['crop', 'sow_year']).apply(lambda g: pd.Series({'yield_wmean': np.average(g.yield_wmean, weights=g.area_ha_ine), 'yield_dry': np.average(g.yield_dry, weights=g.area_ha_ine)})).reset_index()
    return n.groupby('crop')[n.columns].apply(stats)
pd.set_option('display.width', 200)
na, nb = national(a), national(b)
t = pd.DataFrame({f'ratio {la}': na.ratio, f'ratio {lb}': nb.ratio, f'r {la}': na.r, f'r {lb}': nb.r, 'n': nb.n}).round(2)
print('national (INE-area-weighted):'); print(t.to_string())
da = a.groupby(['crop', 'departamento'])[a.columns].apply(stats); db = b.groupby(['crop', 'departamento'])[b.columns].apply(stats)
d = pd.DataFrame({f'ratio {la}': da.ratio, f'ratio {lb}': db.ratio, f'r {la}': da.r, f'r {lb}': db.r}).round(2)
print('\nby crop x departamento:'); print(d.to_string())
