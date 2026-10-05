#!/usr/bin/env python3
"""Figure: SEAS5 member anomalies for Nov-Mar 2026/27 by zone (precip % and T2m), plus observed analogue years for reference.
Usage: python3 analysis/phase4_seas5_figure.py derived/phase4/seas5_2026-09_zone_member_anomalies.csv"""
import sys, os, json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); fc = pd.read_csv(sys.argv[1]); init = os.path.basename(sys.argv[1]).split('_')[1]
INK, MUTED, GRID, NINO, NINA, NEU = '#1a1a19', '#6b6a66', '#e4e3dd', '#eb6834', '#2a78d6', '#9b9a94'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': GRID, 'xtick.color': MUTED, 'ytick.color': MUTED, 'text.color': INK})
cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv'); elev = pd.read_csv(f'{ROOT}/derived/cells_elev_tav.csv').set_index('CELL5M').elev
cells['zone'] = pd.cut(cells.CELL5M.map(elev), [-1, 800, 2800, 9999], labels=['lowland', 'valleys', 'altiplano']).astype(str)
w = pd.read_csv(f'{ROOT}/derived/cell_season_weather_1983-2024.csv.gz'); w['zone'] = w.CELL5M.map(cells.set_index('CELL5M').zone)
area = {json.loads(l)['cell5m']: sum(c['area'] for c in json.loads(l)['crops']) for l in open(f'{ROOT}/Tapiti/res/input/unit-information.jsonl')}; w['w'] = w.CELL5M.map(area)
obs = w.groupby(['zone', 'sow_year']).apply(lambda d: pd.Series({'rain': np.average(d.rain_v, weights=d.w), 'tmax': np.average(d.tmax_v, weights=d.w)})).reset_index()
obs['rain_anom_pct'] = obs.groupby('zone').rain.transform(lambda s: (s - s.mean()) / s.mean() * 100); obs['t_anom'] = obs.groupby('zone').tmax.transform(lambda s: s - s.mean())
enso = pd.read_csv(f'{ROOT}/derived/enso_classification_1983-2024.csv').set_index('sow_year'); obs = obs.join(enso[['phase', 'strong_EP_analogue', 'campaign']], on='sow_year')
zones = ['lowland', 'valleys', 'altiplano']; fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
for ax, z in zip(axes, zones):
    o = obs[obs.zone == z]; col = [NINO if p == 'El Niño' else NINA if p == 'La Niña' else NEU for p in o.phase]
    ax.scatter(o.rain_anom_pct, o.t_anom, c=col, s=28, edgecolor='white', lw=0.5, zorder=3, label=None)
    for r in o[o.strong_EP_analogue].itertuples(): ax.annotate(r.campaign, (r.rain_anom_pct, r.t_anom), textcoords='offset points', xytext=(5, 3), fontsize=8, color='#8a2f0c')
    f = fc[fc.zone == z]; ax.scatter(f.tp_anom_pct, f.t2m_anom, marker='x', c='#1a1a19', s=22, lw=0.8, alpha=0.7, zorder=4)
    ax.scatter([f.tp_anom_pct.mean()], [f.t2m_anom.mean()], marker='X', c='#1a1a19', s=120, zorder=5, edgecolor='white')
    ax.axhline(0, color=GRID); ax.axvline(0, color=GRID); ax.set_title(z.capitalize(), fontsize=12); ax.set_xlabel('Nov–Mar rainfall anomaly, % of climatology')
    for s in ['top', 'right']: ax.spines[s].set_visible(False)
axes[0].set_ylabel('Temperature anomaly, °C (obs: Tmax; SEAS5: T2m)')
axes[0].scatter([], [], c=NINO, label='observed El Niño campaign'); axes[0].scatter([], [], c=NINA, label='observed La Niña'); axes[0].scatter([], [], c=NEU, label='observed neutral'); axes[0].scatter([], [], marker='x', c='#1a1a19', label=f'SEAS5 member, init {init}'); axes[0].scatter([], [], marker='X', c='#1a1a19', s=80, label='SEAS5 ensemble mean'); axes[0].legend(frameon=False, fontsize=8, loc='lower left')
fig.text(0.5, -0.03, 'Observed anomalies from NASA POWER over the modelled cells, 1983/84–2024/25; SEAS5 (ECMWF system 51) anomalies are relative to its own hindcast climatology, precipitation scaled by the POWER Nov–Mar mean.', ha='center', fontsize=8, color=MUTED)
os.makedirs(f'{ROOT}/derived/phase4/figures', exist_ok=True); fig.savefig(f'{ROOT}/derived/phase4/figures/chart_seas5_{init}_vs_analogues.png', dpi=180, bbox_inches='tight', facecolor='white'); print('figure written')
