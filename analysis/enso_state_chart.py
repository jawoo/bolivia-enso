#!/usr/bin/env python3
"""Niño-3.4 and Niño-1+2 monthly anomalies: the 2026 event against the strong eastern-Pacific events 1982/83, 1997/98, 2015/16 (and 2023/24).
Usage: python3 analysis/enso_state_chart.py [--refresh]     (--refresh re-downloads the two CPC index tables)
Reads  derived/enso_state/sstoi.indices  (CPC monthly OISST Niño indices, 1982–)  and  derived/enso_state/wksst9120.for  (weekly, 1990–)
Writes derived/enso_state/figures/chart_nino_indices_2026_vs_analogues.png and derived/enso_state/summary.json"""
import os, re, sys, json, urllib.request, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); D = f'{ROOT}/derived/enso_state'; os.makedirs(f'{D}/figures', exist_ok=True)
SRC = {'sstoi.indices': 'https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices', 'wksst9120.for': 'https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for'}
if '--refresh' in sys.argv:
    for f, u in SRC.items(): urllib.request.urlretrieve(u, f'{D}/{f}'); print('fetched', f)
INK, MUTED, GRID = '#1a1a19', '#6b6a66', '#e4e3dd'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': GRID, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED, 'text.color': INK})
# ---- monthly table
m = pd.read_csv(f'{D}/sstoi.indices', sep=r'\s+'); m.columns = ['yr', 'mon', 'n12', 'a12', 'n3', 'a3', 'n4', 'a4', 'n34', 'a34']
# ---- weekly table (fixed width; SST and anomaly may be glued, e.g. 23.4-0.4)
wk = []
for line in open(f'{D}/wksst9120.for'):
    mm = re.match(r'\s*(\d{2}[A-Z]{3}\d{4})\s+(.*)', line)
    if not mm: continue
    v = re.findall(r'-?\d+\.\d', mm.group(2))
    if len(v) == 8: wk.append((pd.to_datetime(mm.group(1), format='%d%b%Y'), float(v[1]), float(v[5])))
wk = pd.DataFrame(wk, columns=['date', 'a12', 'a34']); last = wk.iloc[-1]
EVENTS = [(1982, '1982/83', '#6b6a66', '--', 1.5), (1997, '1997/98', '#1a1a19', '-', 1.9), (2015, '2015/16', '#2a78d6', '-', 1.6), (2023, '2023/24', '#9b9a94', '-', 1.4), (2026, '2026/27', '#eb6834', '-', 3.0)]
MON = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic', 'ene', 'feb', 'mar', 'abr']
def series(y, col):
    a = m[(m.yr == y) & (m.mon >= 1)][['mon', col]].assign(x=lambda d: d.mon - 0.5); b = m[(m.yr == y + 1) & (m.mon <= 4)][['mon', col]].assign(x=lambda d: d.mon + 11.5)
    s = pd.concat([a, b]); return s.x.values, s[col].values
WMO_OND, WMO_DATE = 3.7, '8 oct'     # WMO Global Seasonal Climate Update OND 2026: Niño-3.4 seasonal mean ≈ +3.7 °C
fig, axes = plt.subplots(2, 1, figsize=(6.1, 3.9), sharex=True); fig.subplots_adjust(left=0.1, right=0.98, top=0.9, bottom=0.1, hspace=0.36)
summ = {'last_monthly': {'year': int(m.yr.iloc[-1]), 'month': int(m.mon.iloc[-1]), 'a34': float(m.a34.iloc[-1]), 'a12': float(m.a12.iloc[-1])},
        'last_weekly': {'date': last.date.strftime('%Y-%m-%d'), 'a34': float(last.a34), 'a12': float(last.a12)}, 'same_month_past': {}}
lm = int(m.mon.iloc[-1])
for ax, col, lab in [(axes[0], 'a34', 'Niño-3.4 (Pacífico central)'), (axes[1], 'a12', 'Niño-1+2 (costa de Perú y Ecuador)')]:
    ax.axvspan(10, 15, color='#eff0e6', zorder=0); ax.axhline(0, color=GRID, lw=1); ax.axhline(0.5, color=GRID, lw=0.8, ls=':')
    for y, name, c, ls, lw in EVENTS:
        x, v = series(y, col); ax.plot(x, v, color=c, ls=ls, lw=lw, solid_capstyle='round', zorder=3 if y == 2026 else 2)
        if y != 2026: ax.plot([], [], color=c, ls=ls, lw=lw, label=name)
        else:
            ax.plot([], [], color=c, lw=lw, label=name)
            ax.plot([x[-1], 9 + last.date.day / 31], [v[-1], last[col]], color=c, lw=lw, zorder=3); ax.scatter([9 + last.date.day / 31], [last[col]], color=c, s=28, zorder=4)
            ax.annotate(f'{last[col]:+.1f} °C ({last.date.day} {MON[last.date.month - 1]})', (9 + last.date.day / 31, last[col]), textcoords='offset points', xytext=(-8, 5), fontsize=8.5, color=c, fontweight='bold', ha='right', va='bottom')
            for yy in (1982, 1997, 2015, 2023):
                r = m[(m.yr == yy) & (m.mon == lm)]; summ['same_month_past'].setdefault(str(yy), {})[col] = float(r[col].iloc[0])
    if col == 'a34':
        ax.scatter([10.5], [WMO_OND], facecolor='white', edgecolor='#eb6834', s=46, lw=1.6, zorder=4)
        ax.annotate(f'pronóstico OMM ({WMO_DATE}):\n+{WMO_OND:.1f} °C, media oct–dic', (10.5, WMO_OND), textcoords='offset points', xytext=(8, 3), fontsize=8, color='#eb6834', va='bottom')
        ax.legend(loc='upper left', ncol=2, frameon=False, fontsize=8, handlelength=1.8, columnspacing=1.0, borderaxespad=0.2)
    ax.set_title(lab, fontsize=10, loc='left', color=INK, pad=4); ax.set_ylabel('anomalía TSM (°C)', fontsize=8.5, color=MUTED)
    for sp in ['top', 'right']: ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=8.5)
axes[0].set_ylim(-1.2, 4.8); axes[1].set_ylim(-1.6, 7.0); axes[1].set_xlim(0, 16.2); axes[1].set_xticks(np.arange(16) + 0.5); axes[1].set_xticklabels(MON)
axes[1].text(12.5, 6.75, 'lluvias principales\nen Bolivia (nov–mar)', fontsize=7.5, color=MUTED, ha='center', va='top')
fig.suptitle('Anomalía de TSM: 2026/27 frente a los El Niño fuertes del Pacífico oriental', fontsize=9.5, x=0.1, ha='left', color=INK)
fig.text(0.1, 0.005,  'Fuente: NOAA CPC, índices Niño OISST (base 1991–2020), mensual a sep y semanal a 7 oct; OMM GSCU oct–dic 2026.', fontsize=6.5, color=MUTED)
fig.savefig(f'{D}/figures/chart_nino_indices_2026_vs_analogues.png', dpi=220, facecolor='white'); plt.close(fig)
json.dump(summ, open(f'{D}/summary.json', 'w'), indent=1); print(json.dumps(summ, indent=1))
