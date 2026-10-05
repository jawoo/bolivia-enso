#!/usr/bin/env python3
"""Phase 3 step 1: is the ENSO signal present in the weather before any crop model is involved?
(a) NASA POWER per-cell seasonal indicators (derived/cell_season_weather_1983-2024.csv.gz), area-weighted
    to department x zone, composited by ENSO phase with bootstrap CIs.
(b) SENAMHI station monthly precipitation (35 .xls files), Nov-Mar totals per campaign, composited by phase.
Outputs: derived/phase3/weather_composites_power.csv, senamhi_stations.csv, senamhi_novmar_anomalies.csv,
         weather_composites_senamhi.csv"""
import os, re, glob, json, numpy as np, pandas as pd
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); OUT = f'{ROOT}/derived/phase3'; rng = np.random.default_rng(7)
enso = pd.read_csv(f'{ROOT}/derived/enso_classification_1983-2024.csv').set_index('sow_year')
def boot_ci(x, n=2000):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 3: return (np.nan, np.nan)
    m = rng.choice(x, (n, len(x))).mean(axis=1); return (np.percentile(m, 2.5), np.percentile(m, 97.5))
def composite(series, label_cols):
    """series: DataFrame indexed by sow_year with one column 'v' (anomaly). Returns rows per phase."""
    s = series.join(enso[['phase', 'category', 'strong_EP_analogue']]); rows = []
    neutral = s[s.phase == 'neutral'].v
    for ph, g in [('El Niño', s[s.phase == 'El Niño']), ('La Niña', s[s.phase == 'La Niña']), ('neutral', s[s.phase == 'neutral']),
                  ('strong El Niño (ONI≥1.5)', s[s.category == 'strong El Niño']), ('strong EP analogues 1997/2015/2023', s[s.strong_EP_analogue])]:
        lo, hi = boot_ci(g.v); rows.append({**label_cols, 'phase': ph, 'n_years': int(g.v.notna().sum()), 'mean': g.v.mean(), 'ci_lo': lo, 'ci_hi': hi,
                                            'diff_vs_neutral': g.v.mean() - neutral.mean(), 'years': ' '.join(str(y) for y in g.index[g.v.notna()])})
    return rows
# ---------- (a) POWER cells
w = pd.read_csv(f'{ROOT}/derived/cell_season_weather_1983-2024.csv.gz')
cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv').set_index('CELL5M'); elev = pd.read_csv(f'{ROOT}/derived/cells_elev_tav.csv').set_index('CELL5M').elev
area = {}
for l in open(f'{ROOT}/Tapiti/res/input/unit-information.jsonl'):
    r = json.loads(l); area[r['cell5m']] = sum(c['area'] for c in r['crops'])
w['dep'] = w.CELL5M.map(cells.departamento); w['zone'] = pd.cut(w.CELL5M.map(elev), [-1, 800, 2800, 9999], labels=['lowland', 'valleys', 'altiplano']).astype(str); w['w'] = w.CELL5M.map(area)
rows = []
groups = [('Bolivia', 'all', w)] + [((d, z), None, g) for (d, z), g in w.groupby(['dep', 'zone']) if g.CELL5M.nunique() >= 5] + [(('Bolivia', z), None, g) for z, g in w.groupby('zone')]
for key, _, g in groups:
    dep, zone = (key if isinstance(key, tuple) else (key, 'all'))
    agg = g.groupby('sow_year').apply(lambda d: pd.Series({k: np.average(d[k], weights=d.w) for k in ['rain_v', 'tmax_v', 'hot35_v', 'wet50_v', 'dry10_v', 'frost_v', 'rain_i', 'tmax_i']}))
    for var, kind in [('rain_v', 'pct'), ('rain_i', 'pct'), ('tmax_v', 'abs'), ('hot35_v', 'abs'), ('wet50_v', 'abs'), ('dry10_v', 'abs'), ('frost_v', 'abs')]:
        x = agg[var]; v = (x - x.mean()) / x.mean() * 100 if kind == 'pct' else x - x.mean()
        rows += composite(pd.DataFrame({'v': v}), {'departamento': dep, 'zone': zone, 'variable': var, 'unit': '% of mean' if kind == 'pct' else 'abs anomaly', 'n_cells': g.CELL5M.nunique(), 'clim_mean': x.mean()})
pw = pd.DataFrame(rows); pw.to_csv(f'{OUT}/weather_composites_power.csv', index=False)
pd.set_option('display.width', 220)
print('POWER: Nov-Mar rainfall anomaly (% of mean) by zone and phase'); t = pw[(pw.departamento == 'Bolivia') & (pw.variable == 'rain_v')]
print(t.pivot(index='zone', columns='phase', values='mean').round(1).to_string())
print('\nPOWER: Tmax Nov-Mar anomaly (°C) by zone and phase'); t = pw[(pw.departamento == 'Bolivia') & (pw.variable == 'tmax_v')]; print(t.pivot(index='zone', columns='phase', values='mean').round(2).to_string())
# ---------- (b) SENAMHI stations
def dms(s):
    m = re.findall(r'(\d+)', str(s)); return -(float(m[0]) + float(m[1]) / 60 + (float(m[2]) / 3600 if len(m) > 2 else 0)) if m else np.nan
st_rows, an_rows = [], []
for f in sorted(glob.glob(f'{ROOT}/data/NOTA CONCEPTUAL CAF/DATOS CLIMATICOS/DATOS SENAMHI/*.xls') + glob.glob(f'{ROOT}/data/NOTA CONCEPTUAL CAF/DATOS CLIMATICOS/DATOS SENAMHI/*.XLS')):
    try: d = pd.read_excel(f, header=None)
    except Exception as e: print('skip', os.path.basename(f), e); continue
    head = d.iloc[:7].astype(str)
    def find(pat):
        for r in range(head.shape[0]):
            for c in range(head.shape[1]):
                v = head.iat[r, c]
                if re.search(pat, v, re.I): return r, c, v
        return None
    es = find(r'estaci'); dp = find(r'departamento'); vr = find(r'precip')
    if es is None or vr is None: print('skip', os.path.basename(f), 'no station/precip header'); continue
    def value(hit):
        r, c, v = hit
        if ':' in v and v.split(':', 1)[1].strip(): return v.split(':', 1)[1].strip()
        for cc in range(c + 1, head.shape[1]):
            if head.iat[r, cc] != 'nan': return head.iat[r, cc].strip()
        return ''
    name = value(es).title(); dep = value(dp).title() if dp else ''
    la = find(r'latitud'); lo = find(r'longitud'); al = find(r'altura|altitud')
    lat = dms(value(la)) if la else np.nan; lon = dms(value(lo)) if lo else np.nan; alt = pd.to_numeric(value(al), errors='coerce') if al else np.nan
    if not pd.isna(alt) and alt < 10: alt = alt * 1000   # '2.952' = 2,952 m (thousands separator)
    DEPZONE = {'La Paz': 'altiplano', 'Oruro': 'altiplano', 'Potosi': 'altiplano', 'Potosí': 'altiplano', 'Cochabamba': 'valleys', 'Chuquisaca': 'valleys', 'Tarija': 'valleys', 'Santa Cruz': 'lowland', 'Beni': 'lowland', 'Pando': 'lowland'}
    zone = ('lowland' if alt <= 800 else 'valleys' if alt <= 2800 else 'altiplano') if not pd.isna(alt) else DEPZONE.get(dep, 'unknown')
    hdr = d.index[d.iloc[:, 0].astype(str).str.strip().str.upper() == 'AÑO']
    if len(hdr) == 0: print('skip', os.path.basename(f), 'no AÑO row'); continue
    tab = d.iloc[hdr[0] + 1:, :13].copy(); tab.columns = ['year'] + list(range(1, 13)); tab = tab[pd.to_numeric(tab.year, errors='coerce').notna()]
    tab['year'] = tab.year.astype(int); m = tab.drop_duplicates('year').set_index('year')[list(range(1, 13))].apply(pd.to_numeric, errors='coerce'); m = m[(m.index >= 1950) & (m.index <= 2030)]
    st_rows.append({'station': name, 'departamento': dep, 'lat': lat, 'lon': lon, 'alt_m': alt, 'zone': zone, 'years': f'{m.index.min()}-{m.index.max()}', 'file': os.path.basename(f)})
    for y in range(1983, 2025):
        parts = [float(m.at[y, 11]) if y in m.index else np.nan, float(m.at[y, 12]) if y in m.index else np.nan] + [float(m.at[y + 1, k]) if (y + 1) in m.index else np.nan for k in (1, 2, 3)]
        an_rows.append({'station': name, 'departamento': dep, 'zone': st_rows[-1]['zone'], 'sow_year': y, 'rain_novmar': sum(parts) if not any(pd.isna(parts)) else np.nan})
st = pd.DataFrame(st_rows); an = pd.DataFrame(an_rows)
st.to_csv(f'{OUT}/senamhi_stations.csv', index=False)
an['anom_pct'] = an.groupby('station').rain_novmar.transform(lambda s: (s - s.mean()) / s.mean() * 100); an.to_csv(f'{OUT}/senamhi_novmar_anomalies.csv', index=False)
print(f'\nSENAMHI: {len(st)} stations parsed; by zone: {st.zone.value_counts().to_dict()}; campaigns with data per station median {an.groupby("station").rain_novmar.count().median():.0f}')
rows = []
for key, g in [('Bolivia', an)] + list(an.groupby('zone')) + list(an.groupby('departamento')):
    s = g.groupby('sow_year').anom_pct.mean().rename('v').to_frame(); nst = g.station.nunique()
    if nst < 2 and key != 'Bolivia': continue
    rows += composite(s, {'group': key if isinstance(key, str) else key, 'n_stations': nst})
sen = pd.DataFrame(rows); sen.to_csv(f'{OUT}/weather_composites_senamhi.csv', index=False)
print('\nSENAMHI stations: Nov-Mar rainfall anomaly (% of station mean), station-mean by group and phase')
print(sen.pivot(index='group', columns='phase', values='mean').round(1).to_string())
print('\nSENAMHI 95% CI El Niño vs neutral, by zone:'); print(sen[sen.phase.isin(['El Niño', 'neutral']) & sen.group.isin(['lowland', 'valleys', 'altiplano'])][['group', 'phase', 'n_years', 'mean', 'ci_lo', 'ci_hi']].round(1).to_string(index=False))
