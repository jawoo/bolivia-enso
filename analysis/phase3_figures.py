#!/usr/bin/env python3
"""Phase 3 figures: composite anomaly maps (strong EP analogues), phase-composite bars with CIs, weather composites.
Usage: python3 analysis/phase3_figures.py runs/<v8 folder>"""
import sys, os, json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); RUN = sys.argv[1].rstrip('/'); OUT = f'{ROOT}/derived/phase3/figures'; os.makedirs(OUT, exist_ok=True)
INK, MUTED, GRID = '#1a1a19', '#6b6a66', '#e4e3dd'; NINO, NINA, NEU = '#eb6834', '#2a78d6', '#9b9a94'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': GRID, 'xtick.color': MUTED, 'ytick.color': MUTED, 'text.color': INK})
NAME = {'SB': 'Soya', 'MZ': 'Maíz', 'RI': 'Arroz', 'SG': 'Sorgo', 'WH': 'Trigo'}; CROPS = ['SB', 'MZ', 'RI', 'SG', 'WH']
enso = pd.read_csv(f'{ROOT}/derived/enso_classification_1983-2024.csv').set_index('sow_year')
cy = pd.read_csv(f'{RUN}/combinedOutput_cellyear.csv.gz'); gj = json.load(open(f'{ROOT}/derived/gis/bolivia_adm1_geoboundaries.geojson'))
def rings(geom):
    if geom['type'] == 'Polygon': yield from geom['coordinates']
    else:
        for poly in geom['coordinates']: yield from poly
def boundaries(ax):
    for f in gj['features']:
        for r in rings(f['geometry']): r = np.array(r); ax.plot(r[:, 0], r[:, 1], color='#4a4a46', lw=0.5)
    ax.set_xlim(-69.8, -57.3); ax.set_ylim(-23.2, -9.5); ax.set_aspect('equal'); ax.axis('off')
def grid_from(d):
    c = np.array(list(d.keys())); v = np.array(list(d.values()), float); row, col = c // 4320, c % 4320; r0, r1, c0, c1 = row.min(), row.max() + 1, col.min(), col.max() + 1
    Z = np.full((r1 - r0, c1 - c0), np.nan); Z[row - r0, col - c0] = v; return -180 + np.arange(c0, c1 + 1) * (5 / 60), 90 - np.arange(r0, r1 + 1) * (5 / 60), Z
# cell-level detrended anomalies
def cell_anom(g):
    y = g.yield_kg_ha.values.astype(float); x = g.sow_year.values.astype(float)
    if np.nanmean(y) <= 0 or len(y) < 20: return pd.Series(np.nan, index=g.index)
    b, a = np.polyfit(x, y, 1); fit = a + b * x; return pd.Series((y - fit) / max(fit.mean(), 1) * 100, index=g.index)
cy['anom'] = cy.groupby(['CELL5M', 'CropCode'], group_keys=False).apply(cell_anom)
cy = cy.join(enso[['phase', 'category', 'strong_EP_analogue']], on='sow_year')
cmap = matplotlib.colors.LinearSegmentedColormap.from_list('div', ['#b85042', '#f2f2f2', '#1c5cab']); norm = TwoSlopeNorm(vmin=-50, vcenter=0, vmax=50)
# ---- Fig 1: strong-EP composite maps, five crops
fig, axes = plt.subplots(1, 5, figsize=(22, 5.6)); fig.subplots_adjust(wspace=0.02)
for ax, crop in zip(axes, CROPS):
    d = cy[(cy.CropCode == crop) & cy.strong_EP_analogue].groupby('CELL5M').anom.mean(); lon, lat, Z = grid_from(d.clip(-50, 50).to_dict())
    m = ax.pcolormesh(lon, lat, Z, cmap=cmap, norm=norm); boundaries(ax); ax.set_title(NAME[crop], fontsize=13, color=INK)
cb = fig.colorbar(m, ax=axes, fraction=0.012, pad=0.01); cb.set_label('Mean detrended yield anomaly, % (1997/98, 2015/16, 2023/24)', fontsize=10); cb.outline.set_visible(False)
fig.savefig(f'{OUT}/map_strongEP_composite_by_crop.png', dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig); print('map_strongEP_composite_by_crop')
# ---- Fig 2: El Niño vs La Niña composite maps for maize and soya (all events)
fig, axes = plt.subplots(2, 2, figsize=(10, 11)); fig.subplots_adjust(wspace=0.02, hspace=0.08)
for i, crop in enumerate(['MZ', 'SB']):
    for j, ph in enumerate(['El Niño', 'La Niña']):
        d = cy[(cy.CropCode == crop) & (cy.phase == ph)].groupby('CELL5M').anom.mean(); lon, lat, Z = grid_from(d.clip(-50, 50).to_dict())
        m = axes[i, j].pcolormesh(lon, lat, Z, cmap=cmap, norm=norm); boundaries(axes[i, j]); axes[i, j].set_title(f'{NAME[crop]} — all {ph} campaigns (n={int((enso.phase == ph).sum())})', fontsize=11)
cb = fig.colorbar(m, ax=axes, fraction=0.02, pad=0.02); cb.set_label('Mean detrended yield anomaly, %', fontsize=10); cb.outline.set_visible(False)
fig.savefig(f'{OUT}/map_phase_composites_maize_soya.png', dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig); print('map_phase_composites_maize_soya')
# ---- Fig 3: national phase composites with CIs (dot + interval) per crop
comp = pd.read_csv(f'{ROOT}/derived/phase3/yield_composites_simulated.csv'); nat = comp[(comp.departamento == 'Bolivia') & (comp.zone == 'all')]
phases = [('La Niña', NINA), ('neutral', NEU), ('El Niño', NINO), ('strong El Niño (ONI≥1.5)', '#c04a1c'), ('strong EP analogues 1997/2015/2023', '#8a2f0c')]
fig, axes = plt.subplots(1, 5, figsize=(18, 4.4), sharey=True); fig.subplots_adjust(wspace=0.12)
for ax, crop in zip(axes, CROPS):
    for k, (ph, col) in enumerate(phases):
        r = nat[(nat.crop == crop) & (nat.phase == ph)].iloc[0]; ax.plot([k, k], [r.ci_lo, r.ci_hi], color=col, lw=2.5, solid_capstyle='round'); ax.scatter([k], [r.mean_anom_pct], color=col, s=55, zorder=3, edgecolor='white', lw=1)
        ax.annotate(f'{r.mean_anom_pct:+.0f}%', (k, r.mean_anom_pct), textcoords='offset points', xytext=(9, -3), fontsize=9, color=INK)
    ax.axhline(0, color=GRID, lw=1); ax.set_title(NAME[crop], fontsize=12); ax.set_xticks(range(5)); ax.set_xticklabels(['La Niña\n(16)', 'neutral\n(12)', 'El Niño\n(14)', 'strong\nEl Niño (4)', 'strong EP\n(3)'], fontsize=8)
    for s in ['top', 'right']: ax.spines[s].set_visible(False)
axes[0].set_ylabel('National detrended yield anomaly, %'); fig.text(0.5, -0.03, 'Dots: mean over the campaigns in each phase (count in brackets); bars: 95% bootstrap interval of that mean.', ha='center', fontsize=9, color=MUTED)
fig.savefig(f'{OUT}/chart_phase_composites_national.png', dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig); print('chart_phase_composites_national')
# ---- Fig 4: weather composites (POWER by zone + SENAMHI by zone), Nov-Mar rainfall anomaly %
pw = pd.read_csv(f'{ROOT}/derived/phase3/weather_composites_power.csv'); se = pd.read_csv(f'{ROOT}/derived/phase3/weather_composites_senamhi.csv')
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
for ax, (src, df, key) in zip(axes, [('NASA POWER (model input), modelled cells 1983–2024', pw[(pw.departamento == 'Bolivia') & (pw.variable == 'rain_v') & (pw.zone != 'all')], 'zone'), ('SENAMHI stations (observed), 29 stations, 1970–2009', se[se.group.isin(['lowland', 'valleys', 'altiplano'])], 'group')]):
    zones = ['lowland', 'valleys', 'altiplano']; width = 0.17
    for k, (ph, col) in enumerate(phases):
        for zi, z in enumerate(zones):
            r = df[(df[key] == z) & (df.phase == ph)]
            if r.empty: continue
            r = r.iloc[0]; x = zi + (k - 2) * width; ax.bar(x, r['mean'], width * 0.9, color=col, edgecolor='white'); ax.plot([x, x], [r.ci_lo, r.ci_hi], color=INK, lw=0.8)
    ax.axhline(0, color=GRID); ax.set_xticks(range(3)); ax.set_xticklabels(['Lowland', 'Valleys', 'Altiplano']); ax.set_title(src, fontsize=10)
    for s in ['top', 'right']: ax.spines[s].set_visible(False)
axes[0].set_ylabel('Nov–Mar rainfall anomaly, % of 1983–2024 mean')
for ph, col in phases: axes[1].bar([np.nan], [0], color=col, label=ph)
axes[1].legend(frameon=False, fontsize=8, loc='lower left'); fig.text(0.5, -0.04, 'Bars: mean anomaly by phase; lines: 95% bootstrap interval of the phase mean. Station records end in 2009, so the station strong-EP bar is the 1997/98 event alone.', ha='center', fontsize=8, color=MUTED)
fig.savefig(f'{OUT}/chart_weather_composites_rain.png', dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig); print('chart_weather_composites_rain')
