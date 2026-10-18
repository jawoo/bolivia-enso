#!/usr/bin/env python3
"""Cumulative season rainfall by agro-ecological zone: every campaign since 1981/82 as a line coloured by ENSO phase,
with the current campaign highlighted, and (optional second figure) the Phase 5 ECMWF members continuing it.

Zone daily rainfall = crop-area-weighted mean of NASA POWER cell rainfall (Tapiti/res/weather/<latest>_bol/*.WTH).
Season = 1 September (sowing year) to 30 April. ENSO phase = DJF Oceanic Nino Index of the campaign (>= 0.5 El Nino,
<= -0.5 La Nina), as in the Phase 3/4 tables. The current campaign is classed by the CPC advisory (El Nino) but drawn
in ink so it is never read as a phase member.

Writes derived/season_progress/zone_daily_rain.csv (cache), derived/season_progress/season_cumulative.csv and
derived/season_progress/figures/chart_season_progress{,_forecast}.png.  Usage: python3 analysis/season_progress_chart.py [--run 2026-10-14]"""
import os, sys, glob, json, argparse, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); OUT = f'{ROOT}/derived/season_progress'; os.makedirs(f'{OUT}/figures', exist_ok=True)
ap = argparse.ArgumentParser(); ap.add_argument('--run', default=None); ap.add_argument('--refresh', action='store_true'); a = ap.parse_args()
WDIR = sorted(glob.glob(f'{ROOT}/Tapiti/res/weather/1981-*_bol'))[-1]
INK, MUTED, GRID = '#1a1a19', '#6b6a66', '#e4e3dd'; PH = {'El Niño': '#eb6834', 'La Niña': '#2a78d6', 'neutral': '#9b9a94'}
ZONES = [('altiplano', 'Altiplano (> 2,800 m)'), ('valleys', 'Valles (800–2,800 m)'), ('lowland', 'Tierras bajas (< 800 m)')]
SEASON0 = (9, 1); NDAYS = 242   # 1 Sep .. 30 Apr
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': GRID, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED, 'text.color': INK})

# ---- zone daily rainfall (cached)
cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv'); elev = pd.read_csv(f'{ROOT}/derived/cells_elev_tav.csv').set_index('CELL5M').elev
zone = pd.cut(cells.CELL5M.map(elev), [-1, 800, 2800, 9999], labels=['lowland', 'valleys', 'altiplano']).astype(str); cells['zone'] = zone.values
area = {json.loads(l)['cell5m']: sum(c['area'] for c in json.loads(l)['crops']) for l in open(f'{ROOT}/Tapiti/res/input/unit-information.jsonl')}
cells['w'] = cells.CELL5M.map(area).fillna(0)
cache = f'{OUT}/zone_daily_rain.csv'
def read_rain(path):
    L = open(path).read().split('\n'); k = next(i for i, l in enumerate(L) if l.startswith('@  DATE'))
    keys = np.array([int(l[0:7]) for l in L[k + 1:] if l.strip()]); rain = np.array([float(l[25:31]) for l in L[k + 1:] if l.strip()])
    idx = pd.to_datetime((keys // 1000).astype(str) + '-01-01') + pd.to_timedelta(keys % 1000 - 1, unit='D'); return pd.Series(rain, index=idx)
if os.path.exists(cache) and not a.refresh:   # --refresh after a POWER update
    zd = pd.read_csv(cache, index_col=0, parse_dates=True, comment='#')
else:
    acc = {z: None for z, _ in ZONES}; wsum = {z: 0.0 for z, _ in ZONES}; n = 0
    for c in cells.itertuples():
        if c.w <= 0: continue
        r = read_rain(f'{WDIR}/{c.CELL5M}.WTH') * c.w; acc[c.zone] = r if acc[c.zone] is None else acc[c.zone].add(r, fill_value=0); wsum[c.zone] += c.w; n += 1
        if n % 500 == 0: print(f'  {n} cells read', flush=True)
    zd = pd.DataFrame({z: acc[z] / wsum[z] for z, _ in ZONES}); zd.index.name = 'date'; zd.to_csv(cache, float_format='%.2f')
LAST = zd.index.max(); print(f'zone daily rainfall from {WDIR}: {zd.index.min().date()} .. {LAST.date()}; cell weights = MapSPAM crop area')

# ---- seasons and ENSO phase
oni = pd.read_csv(f'{ROOT}/derived/oni_cpc.txt', sep=r'\s+'); djf = oni[oni.SEAS == 'DJF'].set_index('YR').ANOM
def phase(sy):
    v = djf.get(sy + 1, np.nan)
    return 'El Niño' if v >= 0.5 else 'La Niña' if v <= -0.5 else 'neutral' if v == v else None
CUR = LAST.year if LAST >= pd.Timestamp(LAST.year, *SEASON0) else LAST.year - 1
rows = []
for sy in range(zd.index.min().year, CUR + 1):
    t0 = pd.Timestamp(sy, *SEASON0); win = zd.loc[t0:t0 + pd.Timedelta(days=NDAYS - 1)]
    if len(win) == 0: continue
    cum = win.cumsum(); cum['day'] = (cum.index - t0).days; cum['sow_year'] = sy; cum['phase'] = phase(sy) if sy < CUR else 'current'; rows.append(cum)
cs = pd.concat(rows); cs.to_csv(f'{OUT}/season_cumulative.csv', index=False)
cur = cs[cs.sow_year == CUR]; hist = cs[cs.sow_year < CUR]
print(f'current campaign {CUR}/{str(CUR + 1)[2:]}: {len(cur)} days observed (to {LAST.date()}); {hist.sow_year.nunique()} past campaigns')

# ---- optional forecast continuation from the Phase 5 members
fc = None
if a.run:
    import gzip
    OM = f'{ROOT}/derived/phase5/om/{a.run}'; cp = pd.read_csv(f'{OM}/cell_points_all.csv'); bf = pd.read_csv(f'{ROOT}/derived/phase5/{a.run}/bias_factors_all.csv').set_index('CELL5M').f_rain
    cp['zone'] = cp.CELL5M.map(dict(zip(cells.CELL5M, cells.zone))); cp['w'] = cp.CELL5M.map(area).fillna(0); cp['f'] = cp.CELL5M.map(bf)
    pts = {}
    for pt in cp[['plat', 'plon']].drop_duplicates().itertuples():
        j = json.load(gzip.open(f'{OM}/{pt.plat}_{pt.plon}.json.gz', 'rt')); d = j['daily']
        pts[(pt.plat, pt.plon)] = (pd.to_datetime(d['time']), np.stack([np.array(d['precipitation_sum' if k == 0 else f'precipitation_sum_member{k:02d}'], dtype=float) for k in range(51)]))
    dates = next(iter(pts.values()))[0]; fc = {}
    for z, _ in ZONES:
        g = cp[(cp.zone == z) & (cp.w > 0)]; acc = np.zeros((51, len(dates)))
        for r in g.itertuples(): acc += pts[(r.plat, r.plon)][1] * r.f * r.w
        fc[z] = pd.DataFrame((acc / g.w.sum()).T, index=dates)   # zone daily rain per member, bias-adjusted
    print(f'forecast members loaded (run {a.run}); horizon {dates.max().date()}')

# ---- figure
def draw(with_fc, name):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.1), sharey=False); fig.subplots_adjust(wspace=0.22, bottom=0.2, top=0.80 if with_fc else 0.84)
    months = [(0, 'Sep'), (30, 'Oct'), (61, 'Nov'), (91, 'Dec'), (122, 'Ene'), (153, 'Feb'), (181, 'Mar'), (212, 'Abr')]
    for ax, (z, zl) in zip(axes, ZONES):
        for ph in ['neutral', 'La Niña', 'El Niño']:
            for sy, g in hist[hist.phase == ph].groupby('sow_year'): ax.plot(g.day, g[z], color=PH[ph], lw=0.9, alpha=0.45, zorder=2)
            med = hist[hist.phase == ph].groupby('day')[z].median(); ax.plot(med.index, med.values, color=PH[ph], lw=2.2, zorder=3, label=f'{ph} (mediana)' if ax is axes[0] else None)
        for sy in [1997, 2015, 2023]:
            g = hist[hist.sow_year == sy]; ax.annotate(f'{sy}/{str(sy + 1)[2:]}', (g.day.iloc[-1] + 2, g[z].iloc[-1]), fontsize=7.5, color=PH['El Niño'], va='center')
        if with_fc and fc is not None:
            f = fc[z].loc[LAST + pd.Timedelta(days=1):pd.Timestamp(CUR + 1, 4, 30)]; base = cur[z].iloc[-1]; cumf = f.cumsum() + base; dd = (f.index - pd.Timestamp(CUR, *SEASON0)).days
            ax.fill_between(dd, np.percentile(cumf.values, 10, axis=1), np.percentile(cumf.values, 90, axis=1), color=INK, alpha=0.10, lw=0, zorder=4, label='Pronóstico ECMWF, 51 miembros (p10–p90)' if ax is axes[0] else None)
            ax.plot(dd, np.median(cumf.values, axis=1), color=INK, lw=1.6, ls=(0, (3, 2)), zorder=5, label='Pronóstico, mediana' if ax is axes[0] else None)
        ax.plot(cur.day, cur[z], color=INK, lw=2.8, zorder=6, label=f'{CUR}/{str(CUR + 1)[2:]} hasta {LAST.day} {["", "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"][LAST.month]}' if ax is axes[0] else None)
        ax.plot([cur.day.iloc[-1]], [cur[z].iloc[-1]], 'o', color=INK, ms=6, zorder=7, markeredgecolor='white', mew=1.2)
        ax.axvline(cur.day.iloc[-1], color=INK, lw=0.6, ls=':', zorder=1)
        ax.annotate(f'{cur[z].iloc[-1]:.0f} mm', (cur.day.iloc[-1] + 3, cur[z].iloc[-1]), fontsize=8.5, color=INK, fontweight='bold', va='bottom')
        ax.set_title(zl, fontsize=11, color=INK, loc='left'); ax.set_xlim(0, NDAYS + 14); ax.set_ylim(0, None)
        ax.set_xticks([m[0] for m in months]); ax.set_xticklabels([f'{m[0]}\n{m[1]}' for m in months], fontsize=8.5)
        ax.grid(axis='y', color=GRID, lw=0.6); ax.set_axisbelow(True)
        for s in ['top', 'right']: ax.spines[s].set_visible(False)
    axes[0].set_ylabel('Lluvia acumulada desde el 1 de septiembre (mm)'); axes[1].set_xlabel('Días desde el inicio de la campaña (1 de septiembre)', color=MUTED)
    fig.legend(loc='upper center', ncol=6 if with_fc else 4, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 0.99), handlelength=2.2, columnspacing=1.4)
    fig.text(0.5, 0.02, f'Cada línea es una campaña 1981/82–{CUR - 1}/{str(CUR)[2:]} (lluvia NASA POWER promediada por zona, ponderada por área de cultivo); el color es la fase ENSO del DJF de esa campaña (ONI ≥ 0.5 El Niño, ≤ −0.5 La Niña); la línea gruesa de cada color es la mediana de la fase. En negro, la campaña {CUR}/{str(CUR + 1)[2:]} observada hasta el {LAST.strftime("%d-%m-%Y")}.' + (' Banda y línea punteada: continuación según los 51 miembros ECMWF (EC46→SEAS5) ajustados a la climatología de cada celda.' if with_fc else ''), ha='center', fontsize=7.5, color=MUTED, wrap=True)
    fig.savefig(f'{OUT}/figures/{name}.png', dpi=200, bbox_inches='tight', facecolor='white'); plt.close(fig); print('wrote', f'{OUT}/figures/{name}.png')
draw(False, 'chart_season_progress')
if fc is not None: draw(True, 'chart_season_progress_forecast')
# summary table: where the current season sits vs the phase distributions at the same day
d0 = int(cur.day.iloc[-1]); same = hist[hist.day == d0]; summ = {'campaign': f'{CUR}/{str(CUR + 1)[2:]}', 'last_obs': str(LAST.date()), 'day': d0, 'n_past': int(hist.sow_year.nunique()), 'zones': {}}
for z, zl in ZONES:
    v = cur[z].iloc[-1]; pct = (same[z] < v).mean() * 100; rank = int((same[z] > v).sum()) + 1
    summ['zones'][z] = {'mm': round(float(v)), 'percentile': round(float(pct)), 'rank_wettest': rank, 'median_all': round(float(same[z].median())), **{f'median_{ph}': round(float(same[same.phase == ph][z].median())) for ph in PH}, 'mm_1997': round(float(same[same.sow_year == 1997][z].iloc[0]))}
    if fc is not None:
        f = fc[z].loc[LAST + pd.Timedelta(days=1):pd.Timestamp(CUR + 1, 4, 30)]; end = f.sum().values + v; clim_end = hist[hist.day == NDAYS - 1][z]
        summ['zones'][z].update({'fc_end_median_mm': round(float(np.median(end))), 'fc_end_p10_mm': round(float(np.percentile(end, 10))), 'fc_end_p90_mm': round(float(np.percentile(end, 90))), 'clim_end_median_mm': round(float(clim_end.median())), 'fc_end_pct_of_clim': round(float(np.median(end) / clim_end.median() * 100))})
    print(f'{z:10s} day {d0}: ' + json.dumps(summ['zones'][z]))
json.dump(summ, open(f'{OUT}/summary.json', 'w'), indent=1)
