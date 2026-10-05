#!/usr/bin/env python3
"""Summarise a Tapiti merged output (res/result/*_combinedOutput_*.csv).

Writes next to the input, with the same stem:
  <stem>_cellyear.csv   one row per crop record x sowing year: cell, departamento, zone, crop,
                        cultivar, sowing DOY, maturity, season length, HWAM (kg/ha dry), area,
                        failure flag (HWAM <= 0 or no maturity), rain/ET over the season
  <stem>_depto_year.csv area-weighted mean yield by crop x departamento x sowing year, with
                        failure share and number of cells
  <stem>_national.csv   same at national level
Prints a compact overview. Usage: python3 analysis/summarise_run.py [path-to-combined-csv]
(defaults to the newest file in Tapiti/res/result; .csv.gz accepted).
"""
import sys, os, glob, json
import pandas as pd, numpy as np
ROOT = os.path.expanduser('~/Claude/bolivia-enso')
path = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(f'{ROOT}/Tapiti/res/result/*_combinedOutput_*.csv'))[-1]
stem = path[:-7] if path.endswith('.csv.gz') else path[:-4]
df = pd.read_csv(path, low_memory=False)
cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv')[['CELL5M', 'departamento']]
elev = pd.read_csv(f'{ROOT}/derived/cells_elev_tav.csv')[['CELL5M', 'elev']]
area = {}
for l in open(f'{ROOT}/Tapiti/res/input/unit-information.jsonl'):
    r = json.loads(l)
    for c in r['crops']: area[(r['cell5m'], c['code'])] = c['area']
df['CELL5M'] = df.SoilProfileID.str[2:].astype(int)
df = df.merge(cells, on='CELL5M', how='left').merge(elev, on='CELL5M', how='left')
df['zone'] = pd.cut(df.elev, [-1, 800, 2800, 99999], labels=['lowland', 'valleys', 'altiplano']).astype(str)
df['sow_year'] = df.PDAT // 1000; df['sow_doy'] = df.PDAT % 1000
pd_ = pd.to_datetime(df.PDAT.astype(str), format='%Y%j', errors='coerce')
md_ = pd.to_datetime(df.MDAT.where(df.MDAT > 0).astype('Int64').astype(str), format='%Y%j', errors='coerce')
df['season_days'] = (md_ - pd_).dt.days
df['area_ha'] = [area.get((c, k), np.nan) for c, k in zip(df.CELL5M, df.CropCode)]
n0 = len(df); df = df[df.area_ha.notna()].copy()   # drop records not in the current unit table (e.g. excluded allocation errors)
if len(df) < n0: print(f'dropped {n0-len(df):,} seasons whose cell x crop is not in the current unit-information.jsonl')
df['failed'] = (df.HWAM <= 0) | (df.MDAT <= 0)
df['yield_kg_ha'] = df.HWAM.clip(lower=0)
keep = ['CELL5M', 'departamento', 'zone', 'elev', 'CropCode', 'CultivarCode', 'sow_year', 'sow_doy', 'ADAT', 'MDAT',
        'season_days', 'yield_kg_ha', 'CWAM', 'failed', 'area_ha', 'PRCP', 'ETCP', 'IRCM', 'NICM']
cy = df[[k for k in keep if k in df.columns]]
cy.to_csv(f'{stem}_cellyear.csv', index=False)

def agg(g):
    w = g.area_ha.fillna(0)
    return pd.Series({'yield_wmean': np.average(g.yield_kg_ha, weights=w) if w.sum() > 0 else g.yield_kg_ha.mean(),
                      'yield_median': g.yield_kg_ha.median(), 'fail_share': g.failed.mean(),
                      'sow_doy_median': g.sow_doy.median(), 'n_cells': g.CELL5M.nunique(), 'area_ha': w.sum()})
dy = cy.groupby(['CropCode', 'departamento', 'sow_year'])[cy.columns].apply(agg).reset_index()
dy.to_csv(f'{stem}_depto_year.csv', index=False)
nat = cy.groupby(['CropCode', 'sow_year'])[cy.columns].apply(agg).reset_index()
nat.to_csv(f'{stem}_national.csv', index=False)

pd.set_option('display.width', 220)
print(f'{len(df):,} seasons, {df.CELL5M.nunique():,} cells, sowing years {df.sow_year.min()}-{df.sow_year.max()}; '
      f'failed seasons {df.failed.mean():.1%}')
print('\nnational area-weighted yield (kg/ha dry) by crop and sowing year:')
print(nat.pivot(index='sow_year', columns='CropCode', values='yield_wmean').round(0).to_string())
print('\nfailure share by crop x zone:')
print(cy.groupby(['CropCode', 'zone']).failed.mean().unstack().round(3).to_string())
print(f'\nwrote {stem}_cellyear.csv, _depto_year.csv, _national.csv')
