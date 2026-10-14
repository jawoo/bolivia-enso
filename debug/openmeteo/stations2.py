#!/usr/bin/env python3
"""Station arbiter: SENAMHI monthly precipitation + mean temperature (1984-2009) and El Alto normals (P, Tmax, Tmin 1991-2020)
vs NASA POWER (nearest MERRA-2 point, from weather/cache) vs Open-Meteo era5_seamless at the station coordinates (90 m DEM downscaled).
Resumable: per-station Open-Meteo responses cached in debug/openmeteo/cache/. Writes debug/openmeteo/station_monthly.csv."""
import xlrd, openpyxl, re, glob, os, json, time, urllib.request, urllib.parse, numpy as np, pandas as pd
KEYFILE = os.path.expanduser('~/.config/open-meteo/apikey'); KEY = os.environ.get('OPEN_METEO_API_KEY') or (open(KEYFILE).read().strip() if os.path.exists(KEYFILE) else None)
ARCHIVE = ('https://customer-archive-api.open-meteo.com/v1/archive?' + (f'apikey={KEY}&' if KEY else '')) if KEY else 'https://archive-api.open-meteo.com/v1/archive?'
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); S = f'{ROOT}/debug/openmeteo'; os.makedirs(f'{S}/cache', exist_ok=True)
D = f'{ROOT}/data/NOTA CONCEPTUAL CAF/DATOS CLIMATICOS/DATOS SENAMHI'
want = ['MONTERO_SC_09.xls','VIRU_VIRU_09.xls','Cochabamba_2009.xls','Oruro_09.xls','Potosi_09.xls','LA PAZ/EL ALTO_09.xls','Sucre_09.xls','Monteagudo_09.xls','Trinidad_09.xls','Tarija_asaana.xls','VALLEGRANDE_09.XLS','San_Ignacio_Velasco_09.xls','Uyuni_09.XLS','Camiri _09.XLS','Chimore(La jota)_09.XLS','Cobija_09.XLS','Roboré_09.xls','San_Jose_Chiquitos_09.xls']
def dm(s):
    n = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', s)]
    return None if not n else n[0] + (n[1]/60 if len(n) > 1 else 0) + (n[2]/3600 if len(n) > 2 else 0)
def coords(s):
    hdr = ' | '.join(' '.join(str(v) for v in s.row_values(i)) for i in range(min(10, s.nrows)))
    lat = re.search(r'Lat\w*\.?\s*S?\w*\.?\s*:?\s*([\d°º\'\" .]+)', hdr); lon = re.search(r'Lon\w*\.?\s*[WO]?\w*\.?\s*:?\s*([\d°º\'\" .]+)', hdr); alt = re.search(r'\b(?:Altura|Altitud|Alt\.)[^:\d|]*:?\s*([\d .]+)', hdr)
    la = dm(lat.group(1)) if lat else None; lo = dm(lon.group(1)) if lon else None
    al = None
    if alt:
        a = alt.group(1).replace(' ', '').strip('.')
        try: al = float(a); al = al * 1000 if al < 10 else al
        except: al = None
    return (-la if la else None), (-lo if lo else None), al
def blocks(s):
    rows = []; block = None
    for i in range(s.nrows):
        c0 = str(s.cell_value(i, 0)).strip()
        if re.search(r'PRECIP', c0, re.I): block = 'p'; continue
        if re.search(r'TEMP', c0, re.I): block = 't' if re.search(r'MEDIA', c0, re.I) and not re.search(r'MAX|MIN', c0, re.I) else None; continue
        if c0 and not re.fullmatch(r'\d{4}(\.0)?', c0) and block and re.search(r'[A-Za-z]{4}', c0) and not re.match(r'A[ÑN]O', c0): block = None; continue
        if block and re.fullmatch(r'\d{4}(\.0)?', c0):
            for m, v in enumerate(s.row_values(i)[1:13], 1):
                try: rows.append((int(float(c0)), m, block, float(v)))
                except: pass
    return pd.DataFrame(rows, columns=['year', 'month', 'var', 'val']).drop_duplicates(['year', 'month', 'var']).pivot(index=['year', 'month'], columns='var', values='val').reset_index()
st = []; meta = []
for w in want:
    f = f'{D}/{w}'
    if not os.path.exists(f): print('missing', w); continue
    s = xlrd.open_workbook(f).sheet_by_index(0); la, lo, alt = coords(s); d = blocks(s); name = re.sub(r'[_ ]?0\d\.\.?xlsx?$|_2009\.xls$|_asaana\.xls$', '', os.path.basename(w), flags=re.I)
    if la is None or lo is None: print('no coords:', w); continue
    d['station'] = name; st.append(d); meta.append(dict(station=name, lat=la, lon=lo, alt=alt, y0=1984, y1=2009, n_p=int(d['p'].notna().sum()) if 'p' in d else 0, n_t=int(d['t'].notna().sum()) if 't' in d else 0))
# El Alto normals (xlsx)
wb = openpyxl.load_workbook(f'{ROOT}/data/NORMALES 1991-2020 (OMM) Y EXTREMAS PCPN_TX_TN  (1)_5824.xlsx', read_only=True, data_only=True)
ea = {}
for sh, var in [('NOR-PCPN', 'p'), ('NOR-TMAX', 'tmax'), ('NOR-TMIN', 'tmin')]:
    started = False                                   # first year-block only; the sheets carry 'EXTREMAS' blocks further down
    for row in wb[sh].iter_rows(values_only=True):
        isyear = row and str(row[0]).strip().isdigit() and 1900 < int(row[0]) < 2100
        if started and not isyear: break
        if isyear:
            started = True
            for m in range(1, 13):
                try: ea[(int(row[0]), m, var)] = float(row[m])
                except: pass
d = pd.Series(ea).rename_axis(['year', 'month', 'var']).reset_index(name='val').pivot(index=['year', 'month'], columns='var', values='val').reset_index(); d['station'] = 'EL ALTO Aeropuerto (normals)'; d['t'] = (d.tmax + d.tmin) / 2
st.append(d); meta.append(dict(station='EL ALTO Aeropuerto (normals)', lat=-(16 + 30/60 + 37/3600), lon=-(68 + 11/60 + 55/3600), alt=4071, y0=1991, y1=2020, n_p=int(d.p.notna().sum()), n_t=int(d.t.notna().sum())))
obs = pd.concat(st); meta = pd.DataFrame(meta); print(meta.to_string(), flush=True)
# POWER nearest grid point
pts = {}
for f in glob.glob(f'{ROOT}/weather/cache/*_1990_RAIN.npz'):
    z = np.load(f); tile = os.path.basename(f).rsplit('_1990', 1)[0]
    for k, (a, o) in enumerate(zip(z['lat'], z['lon'])): pts[(round(float(a), 3), round(float(o), 3))] = (tile, k)
P = np.array(list(pts.keys()))
def power_monthly(lat, lon, y0, y1):
    i = np.argmin((P[:, 0] - lat)**2 + ((P[:, 1] - lon) * np.cos(np.radians(lat)))**2); a, o = P[i]; tile, k = pts[(a, o)]; out = []
    for y in range(y0, y1 + 1):
        ser = {}
        for v, col in [('RAIN', 'p'), ('TMAX', 'tmax'), ('TMIN', 'tmin')]:
            f = f'{ROOT}/weather/cache/{tile}_{y}_{v}.npz'
            if not os.path.exists(f): continue
            x = np.load(f)['vals'][k]; s = pd.Series(x, pd.date_range(f'{y}-01-01', periods=len(x))); s = s.where(s > -90)
            ser[col] = s.resample('MS').sum(min_count=25) if v == 'RAIN' else s.resample('MS').mean()
        if ser: m = pd.DataFrame(ser); out.append(pd.DataFrame({'year': m.index.year, 'month': m.index.month, **{f'{c}_power': m[c].values for c in m}}))
    return pd.concat(out), (a, o)
def get(url):
    for t in range(4):
        try:
            with urllib.request.urlopen(url, timeout=180) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            print('HTTP', e.code, flush=True); time.sleep(60 * (t + 1))
        except Exception as e: print('ERR', str(e).replace(KEY, '***') if KEY else e, flush=True); time.sleep(10)
    return {}
allc = []; missing = 0
for m in meta.itertuples():
    pw, gp = power_monthly(m.lat, m.lon, m.y0, m.y1); print(m.station, round(m.lat, 3), round(m.lon, 3), 'POWER grid', gp, flush=True)
    cf = f'{S}/cache/st2_{m.station}.csv'
    if os.path.exists(cf): om = pd.read_csv(cf)
    else:
        q = dict(latitude=m.lat, longitude=m.lon, start_date=f'{m.y0}-01-01', end_date=f'{m.y1}-12-31', timezone='GMT', models='era5_seamless', daily='temperature_2m_max,temperature_2m_min,precipitation_sum')
        j = get(ARCHIVE + urllib.parse.urlencode(q))
        if 'daily' not in j: print('  fail', j, flush=True); missing += 1; om = None
        else:
            dd = pd.DataFrame(j['daily']); dd['time'] = pd.to_datetime(dd.time); dd = dd.set_index('time')
            mm = pd.DataFrame({'p_om': dd.precipitation_sum.resample('MS').sum(min_count=25), 'tmax_om': dd.temperature_2m_max.resample('MS').mean(), 'tmin_om': dd.temperature_2m_min.resample('MS').mean()})
            om = pd.DataFrame({'year': mm.index.year, 'month': mm.index.month, **{c: mm[c].values for c in mm}}); om['elev_om'] = j.get('elevation'); om.to_csv(cf, index=False); time.sleep(2)
    df = obs[obs.station == m.station].merge(pw, on=['year', 'month'], how='left')
    if om is not None: df = df.merge(om, on=['year', 'month'], how='left')
    df['lat'] = m.lat; df['lon'] = m.lon; df['alt'] = m.alt; df['power_grid'] = f'{gp[0]},{gp[1]}'; allc.append(df)
pd.concat(allc).to_csv(f'{S}/station_monthly.csv', index=False); meta.to_csv(f'{S}/station_meta2.csv', index=False)
print('done; stations missing Open-Meteo:', missing); raise SystemExit(2 if missing else 0)
