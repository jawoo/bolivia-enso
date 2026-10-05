#!/usr/bin/env python3
"""Does the model get the sign of the Santa Cruz soya weather response right?
Correlates INE Santa Cruz verano soya yield and the model's area-weighted Santa Cruz soya yield
(from a *_cellyear.csv) with the season climate indicators in
derived/soya_scz_climate_indicators_1983-2024.csv, over 2012-2023 (INE overlap) and over the
full 1983-2023 record for the model alone.
Usage: python3 analysis/soya_anomaly_check.py <run>_cellyear.csv"""
import sys, numpy as np, pandas as pd
ROOT = '/home/jawoo/Claude/bolivia-enso'
cy = pd.read_csv(sys.argv[1]); sb = cy[(cy.CropCode == 'SB') & (cy.departamento == 'Santa Cruz')]
m = sb.groupby('sow_year').apply(lambda g: np.average(g.yield_kg_ha, weights=g.area_ha.fillna(0))).rename('model_sb_scz')
ind = pd.read_csv(f'{ROOT}/derived/soya_scz_climate_indicators_1983-2024.csv').set_index('sow_year')
t = ind.join(m)
pd.set_option('display.width', 200)
cols = [c for c in ind.columns if c != 'ine_sb_scz_kg_ha']
x = t.dropna(subset=['ine_sb_scz_kg_ha', 'model_sb_scz'])
print(f'2012-2023 (n={len(x)}): correlation with INE vs with model, Santa Cruz soya')
print(pd.DataFrame({'INE': x[cols + ['model_sb_scz']].corrwith(x.ine_sb_scz_kg_ha), 'model': x[cols].corrwith(x.model_sb_scz)}).round(2).to_string())
y = t.dropna(subset=['model_sb_scz'])
print(f'\n1983-2023 (n={len(y)}): model correlation with indicators'); print(y[cols].corrwith(y.model_sb_scz).round(2).to_string())
print('\nINE vs model anomaly correlation 2012-2023: %.2f' % np.corrcoef(x.ine_sb_scz_kg_ha - x.ine_sb_scz_kg_ha.mean(), x.model_sb_scz - x.model_sb_scz.mean())[0, 1])
