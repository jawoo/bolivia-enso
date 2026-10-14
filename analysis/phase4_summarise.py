#!/usr/bin/env python3
"""Phase 4 analogue ensemble for the 2026/27 campaign.
Reads runs/phase4/analog_<A>_combinedOutput.csv.gz (one per analogue sowing year A), builds the distribution of
2026/27 yields by crop x departamento x zone and nationally, conditions it on ENSO class of the analogue
(strong EP analogues; all El Niño; La Niña; neutral; all 42), and writes derived/phase4/*.csv + figures.
Anomalies are % of the all-analogue mean (the unconditional expectation for 2026/27 under the same management)."""
import os, glob, json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); OUT = f'{ROOT}/derived/phase4'; os.makedirs(f'{OUT}/figures', exist_ok=True)
SPLICE = pd.Timestamp(open(f'{OUT}/splice_date.txt').read().strip()) if os.path.exists(f'{OUT}/splice_date.txt') else pd.Timestamp('2026-09-26'); SPL = SPLICE.strftime('%-d %b')
NAME = {'SB': 'Soya', 'MZ': 'Maíz', 'RI': 'Arroz', 'SG': 'Sorgo', 'WH': 'Trigo'}; CROPS = ['SB', 'MZ', 'RI', 'SG', 'WH']
enso = pd.read_csv(f'{ROOT}/derived/enso_classification_1983-2024.csv').set_index('sow_year')
cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv').set_index('CELL5M'); elev = pd.read_csv(f'{ROOT}/derived/cells_elev_tav.csv').set_index('CELL5M').elev
area = {(json.loads(l)['cell5m'], c['code']): c['area'] for l in open(f'{ROOT}/Tapiti/res/input/unit-information.jsonl') for c in json.loads(l)['crops']}
frames = []
for f in sorted(glob.glob(f'{ROOT}/runs/phase4/analog_*_combinedOutput.csv.gz')):
    A = int(os.path.basename(f).split('_')[1]); d = pd.read_csv(f, usecols=['SoilProfileID', 'CropCode', 'PDAT', 'MDAT', 'HWAM', 'PRCP'], low_memory=False)
    d['CELL5M'] = d.SoilProfileID.str[2:].astype(int); d['analog'] = A; frames.append(d.drop(columns='SoilProfileID'))
cy = pd.concat(frames); cy['dep'] = cy.CELL5M.map(cells.departamento); cy['zone'] = pd.cut(cy.CELL5M.map(elev), [-1, 800, 2800, 9999], labels=['lowland', 'valleys', 'altiplano']).astype(str)
cy['w'] = [area.get((c, k), 0) for c, k in zip(cy.CELL5M, cy.CropCode)]; cy['y'] = cy.HWAM.clip(lower=0); cy['sow_doy'] = cy.PDAT % 1000
cy = cy.join(enso[['phase', 'category', 'strong_EP_analogue', 'oni_djf']], on='analog')
print(f'{cy.analog.nunique()} analogues loaded: {sorted(cy.analog.unique())}')
# ---- aggregate yields per analogue
def wavg(g): return np.average(g.y, weights=g.w) if g.w.sum() > 0 else np.nan
rows = []
for key, g in [(('Bolivia', 'all', c), gg) for c, gg in cy.groupby('CropCode')] + [((d, z, c), gg) for (d, z, c), gg in cy.groupby(['dep', 'zone', 'CropCode']) if gg.CELL5M.nunique() >= 5] + [(('Bolivia', z, c), gg) for (z, c), gg in cy.groupby(['zone', 'CropCode']) if gg.CELL5M.nunique() >= 5]:
    s = g.groupby('analog').apply(wavg); sd = g.groupby('analog').sow_doy.median()
    for A in s.index: rows.append({'departamento': key[0], 'zone': key[1], 'crop': key[2], 'analog': A, 'campaign_analog': f'{A}/{str(A+1)[2:]}', 'yield_kg_ha': s[A], 'anom_pct_vs_all': (s[A] / s.mean() - 1) * 100, 'sow_doy_median': sd[A], 'phase': enso.phase[A], 'category': enso.category[A], 'strong_EP': bool(enso.strong_EP_analogue[A]), 'n_cells': g.CELL5M.nunique(), 'area_kha': g.drop_duplicates('CELL5M').w.sum() / 1000})
ser = pd.DataFrame(rows); ser.to_csv(f'{OUT}/analogue_ensemble_series.csv', index=False)
# ---- conditional distributions
def dist(v):
    v = np.asarray(v, float); return {'n': len(v), 'mean': v.mean(), 'median': np.median(v), 'p10': np.percentile(v, 10), 'p90': np.percentile(v, 90), 'min': v.min(), 'max': v.max(), 'p_loss10': (v <= -10).mean(), 'p_loss20': (v <= -20).mean()}
import sys
WEIGHTS = pd.read_csv(sys.argv[1]).set_index('sow_year').weight if len(sys.argv) > 1 else None
cond = [('all 42 analogues', lambda s: s.analog == s.analog), ('El Niño analogues', lambda s: s.phase == 'El Niño'), ('strong El Niño (ONI≥1.5)', lambda s: s.category == 'strong El Niño'), ('strong EP analogues 1997/2015/2023', lambda s: s.strong_EP), ('La Niña analogues', lambda s: s.phase == 'La Niña'), ('neutral analogues', lambda s: s.phase == 'neutral')]
rows = []
for (dep, zone, crop), g in ser.groupby(['departamento', 'zone', 'crop']):
    for lab, sel in cond:
        v = g[sel(g)]; 
        if len(v) == 0: continue
        rows.append({'departamento': dep, 'zone': zone, 'crop': crop, 'area_kha': g.area_kha.iloc[0], 'condition': lab, **dist(v.anom_pct_vs_all), 'mean_yield_kg_ha': v.yield_kg_ha.mean(), 'analogues': ' '.join(str(a) for a in sorted(v.analog))})
    if WEIGHTS is not None:
        wv = g.analog.map(WEIGHTS).fillna(0).values; a = g.anom_pct_vs_all.values; order = np.argsort(a); cw = np.cumsum(wv[order]) / wv.sum()
        q = lambda p: a[order][np.searchsorted(cw, p)]
        rows.append({'departamento': dep, 'zone': zone, 'crop': crop, 'area_kha': g.area_kha.iloc[0], 'condition': 'SEAS5-weighted analogues', 'n': int((wv > 0.005).sum()), 'mean': np.average(a, weights=wv), 'median': q(0.5), 'p10': q(0.1), 'p90': q(0.9), 'min': a.min(), 'max': a.max(),
                     'p_loss10': wv[a <= -10].sum() / wv.sum(), 'p_loss20': wv[a <= -20].sum() / wv.sum(), 'mean_yield_kg_ha': np.average(g.yield_kg_ha.values, weights=wv), 'analogues': 'weighted'})
cd = pd.DataFrame(rows); cd.to_csv(f'{OUT}/analogue_ensemble_conditional.csv', index=False)
pd.set_option('display.width', 240)
nat = cd[(cd.departamento == 'Bolivia') & (cd.zone == 'all')]
print('\n2026/27 national yield anomaly (% of the all-analogue mean), by conditioning set:')
print(nat.pivot(index='crop', columns='condition', values='mean').round(1).reindex(CROPS).rename(index=NAME).reindex(columns=[c for c, _ in cond] + (['SEAS5-weighted analogues'] if WEIGHTS is not None else [])).to_string())
print('\nstrong EP analogues, per event (national):'); print(ser[(ser.departamento == 'Bolivia') & (ser.zone == 'all') & ser.strong_EP].pivot(index='crop', columns='campaign_analog', values='anom_pct_vs_all').round(1).reindex(CROPS).rename(index=NAME).to_string())
print('\nP(loss ≥ 10%) under El Niño analogues vs all:'); print(nat[nat.condition.isin(['all 42 analogues', 'El Niño analogues', 'strong EP analogues 1997/2015/2023', 'SEAS5-weighted analogues'])].pivot(index='crop', columns='condition', values=['p_loss10', 'p_loss20']).round(2).reindex(CROPS).rename(index=NAME).to_string())
# ---- figures: distribution strips per crop (national), and EP-mean map per crop
fig, axes = plt.subplots(1, 5, figsize=(17, 4.2), sharey=True); NINO, NINA, NEU = '#eb6834', '#2a78d6', '#9b9a94'
for ax, crop in zip(axes, CROPS):
    g = ser[(ser.departamento == 'Bolivia') & (ser.zone == 'all') & (ser.crop == crop)].sort_values('anom_pct_vs_all')
    col = [NINO if p == 'El Niño' else NINA if p == 'La Niña' else NEU for p in g.phase]
    ax.scatter(np.random.default_rng(1).uniform(-0.25, 0.25, len(g)), g.anom_pct_vs_all, c=col, s=34, edgecolor='white', lw=0.6, zorder=3)
    for r in g[g.strong_EP].itertuples(): ax.annotate(r.campaign_analog, (0.3, r.anom_pct_vs_all), fontsize=8, color='#8a2f0c', va='center')
    ax.axhline(0, color='#e4e3dd'); ax.set_xlim(-0.6, 0.9); ax.set_xticks([]); ax.set_title(NAME[crop]); 
    for s in ['top', 'right', 'bottom']: ax.spines[s].set_visible(False)
axes[0].set_ylabel('2026/27 national yield, % vs all-analogue mean'); axes[0].scatter([], [], c=NINO, label='El Niño analogue'); axes[0].scatter([], [], c=NINA, label='La Niña analogue'); axes[0].scatter([], [], c=NEU, label='neutral'); axes[0].legend(frameon=False, fontsize=8, loc='lower left')
fig.text(0.5, -0.02, 'Each dot is the 2026/27 campaign simulated with one past campaign\'s weather from ' + SPL + ' onward (observed 2026 weather before that). Labels: strong eastern-Pacific analogues. Sorgo and Santa Cruz trigo are invierno crops sown Apr–Jun 2026, inside the observed period, hence no spread.', ha='center', fontsize=8, color='#6b6a66')
fig.savefig(f'{OUT}/figures/chart_2026_27_analogue_distribution.png', dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig)
gj = json.load(open(f'{ROOT}/derived/gis/bolivia_adm1_geoboundaries.geojson'))
def rings(geom):
    if geom['type'] == 'Polygon': yield from geom['coordinates']
    else:
        for poly in geom['coordinates']: yield from poly
cellmean = cy.groupby(['CELL5M', 'CropCode']).y.mean().rename('clim'); ep = cy[cy.strong_EP_analogue].groupby(['CELL5M', 'CropCode']).y.mean().rename('ep')
m = pd.concat([cellmean, ep], axis=1).dropna(); m['anom'] = (m.ep / m.clim.replace(0, np.nan) - 1) * 100
cmap = matplotlib.colors.LinearSegmentedColormap.from_list('div', ['#b85042', '#f2f2f2', '#1c5cab']); norm = TwoSlopeNorm(vmin=-50, vcenter=0, vmax=50)
fig, axes = plt.subplots(1, 5, figsize=(22, 5.6)); fig.subplots_adjust(wspace=0.02)
for ax, crop in zip(axes, CROPS):
    d = m.xs(crop, level='CropCode').anom.clip(-50, 50).dropna(); c = d.index.values; row, col = c // 4320, c % 4320; r0, r1, c0, c1 = row.min(), row.max() + 1, col.min(), col.max() + 1
    Z = np.full((r1 - r0, c1 - c0), np.nan); Z[row - r0, col - c0] = d.values; lon = -180 + np.arange(c0, c1 + 1) * (5 / 60); lat = 90 - np.arange(r0, r1 + 1) * (5 / 60)
    pm = ax.pcolormesh(lon, lat, Z, cmap=cmap, norm=norm)
    for f in gj['features']:
        for r in rings(f['geometry']): r = np.array(r); ax.plot(r[:, 0], r[:, 1], color='#4a4a46', lw=0.5)
    ax.set_xlim(-69.8, -57.3); ax.set_ylim(-23.2, -9.5); ax.set_aspect('equal'); ax.axis('off'); ax.set_title(NAME[crop], fontsize=13)
cb = fig.colorbar(pm, ax=axes, fraction=0.012, pad=0.01); cb.set_label('2026/27 under strong-EP analogue weather: % vs all-analogue mean', fontsize=10); cb.outline.set_visible(False)
fig.savefig(f'{OUT}/figures/map_2026_27_strongEP_vs_climatology.png', dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig); print('\nfigures written')
