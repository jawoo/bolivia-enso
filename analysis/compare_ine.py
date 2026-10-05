#!/usr/bin/env python3
"""Compare a summarised Tapiti run with INE departmental yields, 2012-2024.

Inputs
  <stem>_depto_year.csv   from analysis/summarise_run.py (area-weighted model yield by
                          crop x departamento x sowing year, kg/ha dry matter)
  derived/ine_yields_depto_campaign_2012-2024.csv   INE yield at commercial moisture
Season matching: the model simulates one campaign per crop per department (see
prep/build_unit_information_bolivia.py::season_for); INE rows are taken from the campaign
that dominates the modelled area in that department. INE yields are converted to dry matter
with standard commercial moisture (soya 13%, maize/sorghum/paddy 14%, wheat 13%).
Outputs <stem>_vs_ine.csv (matched rows) and prints level bias, ratio, and the correlation of
year-to-year anomalies per crop x departamento and nationally (sowing years 2012-2024).
Usage: python3 analysis/compare_ine.py <stem>_depto_year.csv
"""
import sys, os, numpy as np, pandas as pd
ROOT = os.path.expanduser('~/Claude/bolivia-enso')
MOIST = {'SB': 0.13, 'MZ': 0.14, 'RI': 0.14, 'SG': 0.14, 'WH': 0.13}
m = pd.read_csv(sys.argv[1])
ine = pd.read_csv(f'{ROOT}/derived/ine_yields_depto_campaign_2012-2024.csv')
ine['yield_dry'] = ine.yield_kg_ha * (1 - ine.crop.map(MOIST))
# dominant modelled season per crop x depto from the unit table
import json
cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv').set_index('CELL5M')
sys.path.insert(0, f'{ROOT}/prep')
rows = []
for l in open(f'{ROOT}/Tapiti/res/input/unit-information.jsonl'):
    r = json.loads(l); dep = cells.loc[r['cell5m'], 'departamento']
    for c in r['crops']:
        season = {105: 'invierno', 143: 'invierno'}.get(c['plantingDate'], 'verano')   # invierno medians per management table
        rows.append((dep, c['code'], season, c['area']))
u = pd.DataFrame(rows, columns=['departamento', 'crop', 'season', 'area'])
dom = u.groupby(['departamento', 'crop', 'season']).area.sum().reset_index().sort_values('area').groupby(['departamento', 'crop']).tail(1)[['departamento', 'crop', 'season']]
ine = ine.merge(dom, on=['departamento', 'crop', 'season'])
x = m.rename(columns={'CropCode': 'crop'}).merge(ine, on=['crop', 'departamento', 'sow_year'], suffixes=('_model', '_ine'))
x = x[(x.sow_year >= 2012) & (x.sow_year <= 2024) & x.yield_dry.notna() & (x.area_ha_ine > 500)]
x.to_csv(sys.argv[1].replace('_depto_year.csv', '_vs_ine.csv'), index=False)

def stats(g):
    if len(g) < 5: return pd.Series({'n': len(g), 'model': g.yield_wmean.mean(), 'ine_dry': g.yield_dry.mean(), 'ratio': np.nan, 'r_anom': np.nan})
    am = g.yield_wmean - g.yield_wmean.mean(); ai = g.yield_dry - g.yield_dry.mean()
    return pd.Series({'n': len(g), 'model': g.yield_wmean.mean(), 'ine_dry': g.yield_dry.mean(),
                      'ratio': g.yield_wmean.mean() / g.yield_dry.mean(), 'r_anom': np.corrcoef(am, ai)[0, 1] if ai.std() > 0 and am.std() > 0 else np.nan})
pd.set_option('display.width', 200)
print('by crop x departamento (model dry kg/ha vs INE converted to dry; ratio = model/INE; r_anom = correlation of yearly anomalies):')
print(x.groupby(['crop', 'departamento'])[x.columns].apply(stats).round(2).to_string())
# national: area-weight model by INE area within crop-year
nat = x.groupby(['crop', 'sow_year']).apply(lambda g: pd.Series({'yield_wmean': np.average(g.yield_wmean, weights=g.area_ha_ine), 'yield_dry': np.average(g.yield_dry, weights=g.area_ha_ine)})).reset_index()
print('\nnational:'); print(nat.groupby('crop')[nat.columns].apply(stats).round(2).to_string())
