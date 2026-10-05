#!/usr/bin/env python3
"""Figures and chart data for the progress deck, from an archived run folder.
Usage: python3 analysis/deck_figures.py runs/<folder> [outdir]
Writes PNG maps (matplotlib) and JSON chart data to <outdir> (default derived/deck_<tag>/)."""
import sys, os, json, glob, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, TwoSlopeNorm, BoundaryNorm
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); run = sys.argv[1].rstrip('/')
out = sys.argv[2] if len(sys.argv) > 2 else f"{ROOT}/derived/deck_{os.path.basename(run).split('_',1)[-1]}"; os.makedirs(out, exist_ok=True)
# palette (dataviz reference instance): categorical slots, sequential blue ramp, diverging orange<->blue
CAT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']; INK = '#1a1a19'; MUTED = '#6b6a66'; GRID = '#e4e3dd'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.edgecolor': GRID, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED, 'text.color': INK})
# ---- data
cy = pd.read_csv(glob.glob(f'{run}/combinedOutput_cellyear.csv*')[0])
vs = pd.read_csv(f'{run}/combinedOutput_vs_ine.csv'); nat = pd.read_csv(f'{run}/combinedOutput_national.csv')
cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv'); elev = pd.read_csv(f'{ROOT}/derived/cells_elev_tav.csv')
units = [json.loads(l) for l in open(f'{ROOT}/Tapiti/res/input/unit-information.jsonl')]
gj = json.load(open(f'{ROOT}/derived/gis/bolivia_adm1_geoboundaries.geojson'))
def rings(geom):
    if geom['type'] == 'Polygon': yield from geom['coordinates']
    else:
        for poly in geom['coordinates']: yield from poly
def draw_boundaries(ax, lw=0.6, color='#4a4a46'):
    for f in gj['features']:
        for r in rings(f['geometry']):
            r = np.array(r); ax.plot(r[:, 0], r[:, 1], color=color, lw=lw, solid_capstyle='round')
    ax.set_xlim(-69.8, -57.3); ax.set_ylim(-23.2, -9.5); ax.set_aspect('equal'); ax.axis('off')
def grid_from(series_by_cell):
    """cell5m -> value  =>  pcolormesh arrays"""
    c = np.array(list(series_by_cell.keys())); v = np.array(list(series_by_cell.values()), dtype=float)
    row, col = c // 4320, c % 4320; r0, r1, c0, c1 = row.min(), row.max() + 1, col.min(), col.max() + 1
    Z = np.full((r1 - r0, c1 - c0), np.nan); Z[row - r0, col - c0] = v
    lon = -180 + np.arange(c0, c1 + 1) * (5 / 60); lat = 90 - np.arange(r0, r1 + 1) * (5 / 60)
    return lon, lat, Z
def finish(fig, name, note=None):
    pass  # footnotes are carried by the slide text, not the image
    fig.savefig(f'{out}/{name}.png', dpi=200, bbox_inches='tight', facecolor='white'); plt.close(fig); print('wrote', name)

# ---- Map 1: modelled cells by dominant crop (largest area in cell)
code_name = {'SB': 'Soya', 'MZ': 'Maíz', 'RI': 'Arroz', 'SG': 'Sorgo', 'WH': 'Trigo'}; order = ['SB', 'MZ', 'RI', 'SG', 'WH']
dom = {u['cell5m']: order.index(max(u['crops'], key=lambda c: c['area'])['code']) for u in units}
lon, lat, Z = grid_from(dom)
fig, ax = plt.subplots(figsize=(6.2, 6.6)); ax.pcolormesh(lon, lat, Z, cmap=ListedColormap(CAT[:5]), vmin=-0.5, vmax=4.5, shading='flat'); draw_boundaries(ax)
for i, k in enumerate(order): ax.scatter([], [], marker='s', s=60, color=CAT[i], label=f"{code_name[k]}")
ax.legend(loc='upper right', frameon=False, fontsize=10, title='Dominant crop in cell', title_fontsize=10)
finish(fig, 'map_cells_dominant_crop', f'{len(units):,} 5-arcmin cells with ≥25 ha of an in-scope crop (MapSPAM 2020); department boundaries geoBoundaries')

# ---- Map 2: elevation zones
ez = dict(zip(elev.CELL5M, pd.cut(elev.elev, [-1, 800, 2800, 9999], labels=[0, 1, 2]).astype(int)))
lon, lat, Z = grid_from({u['cell5m']: ez[u['cell5m']] for u in units})
fig, ax = plt.subplots(figsize=(6.2, 6.6)); ax.pcolormesh(lon, lat, Z, cmap=ListedColormap(['#9ec5f4', '#3987e5', '#0d366b']), vmin=-0.5, vmax=2.5); draw_boundaries(ax)
for c, l in zip(['#9ec5f4', '#3987e5', '#0d366b'], ['Lowland < 800 m', 'Valleys 800–2,800 m', 'Altiplano > 2,800 m']): ax.scatter([], [], marker='s', s=60, color=c, label=l)
ax.legend(loc='upper right', frameon=False, fontsize=10)
finish(fig, 'map_zones', 'Zone by cell-mean elevation (NASA POWER DEM); drives season, management class and cultivar')

# ---- Map 3: simulated yield anomaly (%) in selected sowing years, per crop
cy['anom'] = cy.groupby(['CELL5M', 'CropCode']).yield_kg_ha.transform(lambda s: (s - s.mean()) / s.mean() * 100 if s.mean() > 0 else np.nan)
def anomaly_map(crop, years, name):
    fig, axes = plt.subplots(1, len(years), figsize=(5.2 * len(years), 4.9)); fig.subplots_adjust(wspace=0.02)
    norm = TwoSlopeNorm(vmin=-60, vcenter=0, vmax=60); cmap = matplotlib.colors.LinearSegmentedColormap.from_list('div', ['#b85042', '#f2f2f2', '#1c5cab'])
    for ax, y in zip(np.atleast_1d(axes), years):
        d = cy[(cy.CropCode == crop) & (cy.sow_year == y)]; lon, lat, Z = grid_from(dict(zip(d.CELL5M, d.anom.clip(-60, 60))))
        m = ax.pcolormesh(lon, lat, Z, cmap=cmap, norm=norm); draw_boundaries(ax); ax.set_title(f'{code_name[crop]} — sowing year {y} ({y}/{str(y+1)[2:]} campaign)', fontsize=11, color=INK)
    cb = fig.colorbar(m, ax=axes, fraction=0.025, pad=0.02, shrink=0.7); cb.set_label('Simulated yield anomaly, % of 1983–2024 cell mean', fontsize=9); cb.outline.set_visible(False)
    finish(fig, name, 'Tapiti hindcast, rainfed and irrigated as recorded; brown = below the cell mean, blue = above')
anomaly_map('MZ', [1997, 2015, 2023], 'map_anom_maize_elnino_years')
anomaly_map('SB', [1997, 2015, 2023], 'map_anom_soya_elnino_years')
anomaly_map('MZ', [2010, 2016], 'map_anom_maize_other_years')

# ---- Chart data: national model vs INE 2012-2024 by crop (dry matter)
MOIST = {'SB': 0.13, 'MZ': 0.14, 'RI': 0.14, 'SG': 0.14, 'WH': 0.13}
natvs = vs.groupby(['crop', 'sow_year']).apply(lambda g: pd.Series({'model': np.average(g.yield_wmean, weights=g.area_ha_ine), 'ine': np.average(g.yield_dry, weights=g.area_ha_ine)})).reset_index()
chart = {}
for crop, g in natvs.groupby('crop'):
    g = g.sort_values('sow_year'); chart[crop] = {'years': g.sow_year.astype(int).tolist(), 'model': g.model.round(0).tolist(), 'ine': g.ine.round(0).tolist(),
        'ratio': round(g.model.mean() / g.ine.mean(), 2), 'r': round(float(np.corrcoef(g.model - g.model.mean(), g.ine - g.ine.mean())[0, 1]), 2)}
json.dump(chart, open(f'{out}/national_vs_ine.json', 'w'), indent=1)
# ---- Chart data: national simulated series 1983-2024 with ENSO phase (ONI DJF of the campaign)
oni = pd.read_csv(f'{ROOT}/derived/oni_cpc.txt', sep=r'\s+'); djf = oni[oni.SEAS == 'DJF'].set_index('YR').ANOM   # DJF labelled by the January year
ens = {}; trends = {}
for crop, g in nat.groupby('CropCode'):
    g = g.sort_values('sow_year'); mean = g.yield_wmean.mean(); yrs = g.sow_year.values.astype(float)
    b, a = np.polyfit(yrs, g.yield_wmean.values, 1); fit = a + b * yrs; trends[crop] = round(b / mean * 100, 2)   # % of mean per year
    ens[crop] = {'years': g.sow_year.astype(int).tolist(), 'anom_pct': ((g.yield_wmean - mean) / mean * 100).round(1).tolist(),
                 'anom_detrended_pct': ((g.yield_wmean - fit) / mean * 100).round(1).tolist(), 'trend_pct_per_yr': trends[crop],
                 'oni_djf': [round(float(djf.get(y + 1, np.nan)), 2) for y in g.sow_year]}
print('linear trend of simulated national yield, % of mean per year:', trends)
json.dump(trends, open(f'{out}/model_trends.json', 'w'))
json.dump(ens, open(f'{out}/national_anomalies_enso.json', 'w'), indent=1)
# ---- Chart data: level ratio and r by crop for this run (national)
json.dump({c: {'ratio': chart[c]['ratio'], 'r': chart[c]['r']} for c in chart}, open(f'{out}/skill_by_crop.json', 'w'), indent=1)
print(json.dumps({c: (chart[c]['ratio'], chart[c]['r']) for c in chart}))
# ---- Figure: ENSO preview scatter (maize + soya national anomaly vs ONI)
fig, axes = plt.subplots(1, 2, figsize=(10, 4.4)); fig.subplots_adjust(bottom=0.22, wspace=0.3)
for ax, crop in zip(axes, ['MZ', 'SB']):
    e = ens[crop]; x = np.array(e['oni_djf'], dtype=float); y = np.array(e['anom_detrended_pct']); yrs = e['years']
    col = np.where(x >= 0.5, '#eb6834', np.where(x <= -0.5, '#2a78d6', '#9b9a94'))
    ax.axhline(0, color=GRID, lw=1); ax.axvline(0, color=GRID, lw=1); ax.scatter(x, y, c=col, s=42, edgecolor='white', lw=0.8)
    for xi, yi, yr in zip(x, y, yrs):
        if abs(xi) >= 1.5: ax.annotate(f'{yr}/{str(yr+1)[2:]}', (xi, yi), textcoords='offset points', xytext=(5, 4), fontsize=8, color=MUTED)
    ax.set_title(f'{code_name[crop]}: simulated national yield anomaly vs ENSO', fontsize=11); ax.set_xlabel('ONI, DJF of the campaign (°C)'); ax.set_ylabel('Detrended anomaly, % of 1983–2024 mean')
    for s in ['top', 'right']: ax.spines[s].set_visible(False)
axes[0].scatter([], [], c='#eb6834', label='El Niño (ONI ≥ 0.5)'); axes[0].scatter([], [], c='#2a78d6', label='La Niña (ONI ≤ −0.5)'); axes[0].scatter([], [], c='#9b9a94', label='Neutral'); fig.legend(loc='lower center', ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 0.0))
finish(fig, 'chart_enso_preview', 'Preview only — Phase 3 does the composite analysis properly. Linear trend removed; 42 campaigns 1983–2024.')
print('done ->', out)
