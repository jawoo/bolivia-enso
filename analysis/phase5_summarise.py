#!/usr/bin/env python3
"""Phase 5 forecast ensemble for the 2026/27 campaign (PLAN.md s12).
Reads runs/phase5/<run>/fc_<mm>_combinedOutput.csv.gz (one per ECMWF member), aggregates 2026/27 yields by crop x departamento
x zone and nationally per member, expresses them as % of the Phase 4 all-analogue mean (the same reference the analogue
tables use, derived/phase4/analogue_ensemble_series.csv), and writes derived/phase5/<run>/member_ensemble_{series,summary}.csv
plus a figure comparing the member distribution with the analogue sets. Usage: python3 analysis/phase5_summarise.py [run]"""
import os, sys, glob, json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = os.path.expanduser('~/Claude/bolivia-enso')
RUN = sys.argv[1] if len(sys.argv) > 1 else sorted(os.listdir(f'{ROOT}/runs/phase5'))[-1]; OUT = f'{ROOT}/derived/phase5/{RUN}'; os.makedirs(f'{OUT}/figures', exist_ok=True)
NAME = {'SB': 'Soya', 'MZ': 'Maíz', 'RI': 'Arroz', 'SG': 'Sorgo', 'WH': 'Trigo'}; CROPS = ['SB', 'MZ', 'RI', 'SG', 'WH']
cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv').set_index('CELL5M'); elev = pd.read_csv(f'{ROOT}/derived/cells_elev_tav.csv').set_index('CELL5M').elev
area = {(json.loads(l)['cell5m'], c['code']): c['area'] for l in open(f'{ROOT}/Tapiti/res/input/unit-information.jsonl') for c in json.loads(l)['crops']}
frames = []
for f in sorted(glob.glob(f'{ROOT}/runs/phase5/{RUN}/fc_*_combinedOutput.csv.gz')):
    m = int(os.path.basename(f).split('_')[1]); d = pd.read_csv(f, usecols=['SoilProfileID', 'CropCode', 'PDAT', 'MDAT', 'HWAM', 'PRCP'], low_memory=False)
    d['CELL5M'] = d.SoilProfileID.str[2:].astype(int); d['member'] = m; frames.append(d.drop(columns='SoilProfileID'))
cy = pd.concat(frames); cy['dep'] = cy.CELL5M.map(cells.departamento); cy['zone'] = pd.cut(cy.CELL5M.map(elev), [-1, 800, 2800, 9999], labels=['lowland', 'valleys', 'altiplano']).astype(str)
cy['w'] = [area.get((c, k), 0) for c, k in zip(cy.CELL5M, cy.CropCode)]; cy['y'] = cy.HWAM.clip(lower=0)
print(f'{cy.member.nunique()} members loaded for run {RUN}: {sorted(cy.member.unique())}')
ana = pd.read_csv(f'{ROOT}/derived/phase4/analogue_ensemble_series.csv'); ref = ana.groupby(['departamento', 'zone', 'crop']).yield_kg_ha.mean().rename('ref_all_analogue')
def wavg(g): return np.average(g.y, weights=g.w) if g.w.sum() > 0 else np.nan
rows = []
for key, g in [(('Bolivia', 'all', c), gg) for c, gg in cy.groupby('CropCode')] + [((d, z, c), gg) for (d, z, c), gg in cy.groupby(['dep', 'zone', 'CropCode']) if gg.CELL5M.nunique() >= 5] + [(('Bolivia', z, c), gg) for (z, c), gg in cy.groupby(['zone', 'CropCode']) if gg.CELL5M.nunique() >= 5]:
    s = g.groupby('member')[['y', 'w']].apply(wavg); r = ref.get(key, np.nan)
    for m in s.index: rows.append({'departamento': key[0], 'zone': key[1], 'crop': key[2], 'member': m, 'yield_kg_ha': s[m], 'anom_pct_vs_all_analogue': (s[m] / r - 1) * 100 if r == r else np.nan, 'anom_pct_vs_member_mean': (s[m] / s.mean() - 1) * 100, 'n_cells': g.CELL5M.nunique(), 'area_kha': g.drop_duplicates('CELL5M').w.sum() / 1000})
ser = pd.DataFrame(rows); ser.to_csv(f'{OUT}/member_ensemble_series.csv', index=False)
def dist(v):
    v = np.asarray(v, float); v = v[~np.isnan(v)]; return {'n': len(v), 'mean': v.mean(), 'median': np.median(v), 'p10': np.percentile(v, 10), 'p90': np.percentile(v, 90), 'min': v.min(), 'max': v.max(), 'p_loss10': (v <= -10).mean(), 'p_loss20': (v <= -20).mean()}
summ = pd.DataFrame([{'departamento': d, 'zone': z, 'crop': c, 'area_kha': g.area_kha.iloc[0], 'condition': f'ECMWF members {RUN}', **dist(g.anom_pct_vs_all_analogue), 'mean_yield_kg_ha': g.yield_kg_ha.mean()} for (d, z, c), g in ser.groupby(['departamento', 'zone', 'crop'])])
summ.to_csv(f'{OUT}/member_ensemble_summary.csv', index=False)
cond = pd.read_csv(f'{ROOT}/derived/phase4/analogue_ensemble_conditional.csv'); keep = ['all 42 analogues', 'El Niño analogues', 'strong EP analogues 1997/2015/2023', 'SEAS5-weighted analogues']
both = pd.concat([cond[cond.condition.isin(keep)], summ]); nat = both[(both.departamento == 'Bolivia') & (both.zone == 'all')]
pd.set_option('display.width', 240)
print('\n2026/27 national yield anomaly, % of the all-analogue mean: analogue conditioning sets vs the ECMWF member ensemble')
print(nat.pivot(index='crop', columns='condition', values='mean').round(1).reindex(CROPS).rename(index=NAME).reindex(columns=keep + [f'ECMWF members {RUN}']).to_string())
print('\nmember ensemble spread (national): median, p10, p90, P(loss>=10%), P(loss>=20%)')
print(summ[(summ.departamento == 'Bolivia') & (summ.zone == 'all')].set_index('crop')[['n', 'median', 'p10', 'p90', 'p_loss10', 'p_loss20']].round(2).reindex(CROPS).rename(index=NAME).to_string())
print('\nby zone (mean anomaly %; zone x crop groups under 5 kha omitted, e.g. Altiplano sorghum 0.5 kha with a ~190 kg/ha baseline):'); print(both[(both.departamento == 'Bolivia') & (both.zone != 'all') & (both.area_kha >= 5)].pivot_table(index=['zone', 'crop'], columns='condition', values='mean').round(1).reindex(columns=keep + [f'ECMWF members {RUN}']).to_string())
# ---- figure: national strips, members vs analogues
fig, axes = plt.subplots(1, 5, figsize=(17, 4.2), sharey=True); rng = np.random.default_rng(1)
for ax, crop in zip(axes, CROPS):
    g = ana[(ana.departamento == 'Bolivia') & (ana.zone == 'all') & (ana.crop == crop)]; mm = ser[(ser.departamento == 'Bolivia') & (ser.zone == 'all') & (ser.crop == crop)]
    ax.scatter(rng.uniform(-0.2, 0.2, len(g)), g.anom_pct_vs_all, c=['#eb6834' if p == 'El Niño' else '#2a78d6' if p == 'La Niña' else '#9b9a94' for p in g.phase], s=28, edgecolor='white', lw=0.5, zorder=3)
    ax.scatter(1 + rng.uniform(-0.2, 0.2, len(mm)), mm.anom_pct_vs_all_analogue, c='#3f8f5f', s=28, edgecolor='white', lw=0.5, zorder=3)
    ax.axhline(0, color='#e4e3dd'); ax.set_xticks([0, 1]); ax.set_xticklabels(['42 analogues', f'{len(mm)} ECMWF\nmembers']); ax.set_title(NAME[crop]); ax.set_xlim(-0.6, 1.6)
    for s in ['top', 'right']: ax.spines[s].set_visible(False)
axes[0].set_ylabel('2026/27 national yield, % vs all-analogue mean')
fig.text(0.5, -0.03, f'Left: 2026/27 simulated with each past campaign\'s weather (orange El Niño, blue La Niña, grey neutral). Right: simulated with each bias-adjusted ECMWF EC46/SEAS5 member (Open-Meteo run {RUN}), analogue tail beyond the forecast horizon.', ha='center', fontsize=8, color='#6b6a66')
fig.savefig(f'{OUT}/figures/chart_2026_27_members_vs_analogues.png', dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig)
print('\nwrote', OUT)
