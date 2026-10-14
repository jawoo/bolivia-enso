import xlrd, re, glob, os, json, time, urllib.request, urllib.parse, numpy as np, pandas as pd
S = os.path.dirname(os.path.abspath(__file__)); D = 'data/NOTA CONCEPTUAL CAF/DATOS CLIMATICOS/DATOS SENAMHI'
want = ['MONTERO_SC_09.xls','VIRU_VIRU_09.xls','Cochabamba_2009.xls','Oruro_09.xls','Potosi_09.xls','LA PAZ/EL ALTO_09.xls','Sucre_09.xls','Monteagudo_09.xls','Trinidad_09.xls','Tarija_asaana.xls','VALLEGRANDE_09.XLS','San_Ignacio_Velasco_09.xls','Uyuni_09.XLS','Camiri _09.XLS','Chimore(La jota)_09.XLS','Cobija_09.XLS']
def dm(s):
    n = [float(x) for x in re.findall(r'[\d.]+', s)]
    if not n: return None
    return n[0] + (n[1]/60 if len(n) > 1 else 0) + (n[2]/3600 if len(n) > 2 else 0)
def parse(f):
    b = xlrd.open_workbook(f); s = b.sheet_by_index(0); hdr = ' | '.join(' '.join(str(v) for v in s.row_values(i)) for i in range(4))
    lat = re.search(r'Latitud\s*S?\s*:?\s*([\d°\'\" .]+)', hdr); lon = re.search(r'Longitud\s*W?\s*:?\s*([\d°\'\" .]+)', hdr); alt = re.search(r'Alt\w*\s*m?\s*:?\s*([\d.]+)', hdr)
    rows = []; block = None
    for i in range(s.nrows):
        c0 = str(s.cell_value(i, 0)).strip()
        if re.search(r'PRECIP', c0, re.I): block = 'P'; continue
        if re.search(r'TEMP|VIENTO|DIRECC|HUMEDAD|RADIAC|EVAP|NUBOS|INSOL|HELAD|PRESION', c0, re.I): block = None; continue
        if block == 'P' and re.fullmatch(r'\d{4}(\.0)?', c0):
            vals = s.row_values(i)[1:13]
            for m, v in enumerate(vals, 1):
                try: rows.append((int(float(c0)), m, float(v)))
                except: pass
    return dict(file=os.path.basename(f), hdr=hdr[:120], lat=(-dm(lat.group(1)) if lat and dm(lat.group(1)) else None), lon=(-dm(lon.group(1)) if lon and dm(lon.group(1)) else None), alt=float(alt.group(1)) if alt else None), pd.DataFrame(rows, columns=['year','month','p'])
meta = []; st = []
for w in want:
    f = f'{D}/{w}'
    if not os.path.exists(f): print('missing', w); continue
    m, d = parse(f); m['n'] = len(d); m['y0'] = d.year.min() if len(d) else None; m['y1'] = d.year.max() if len(d) else None; meta.append(m); d['station'] = m['file']; st.append(d)
    print(m)
meta = pd.DataFrame(meta); st = pd.concat(st); st.to_csv(f'{S}/senamhi_monthly_p.csv', index=False)
# POWER grid points from cache (RAIN, 1984-2009)
pts = {}
for f in glob.glob('weather/cache/*_1990_RAIN.npz'):
    z = np.load(f); tile = os.path.basename(f).rsplit('_1990', 1)[0]
    for k, (la, lo) in enumerate(zip(z['lat'], z['lon'])): pts[(round(float(la),3), round(float(lo),3))] = (tile, k)
P = np.array(list(pts.keys()))
def power_monthly(lat, lon):
    i = np.argmin((P[:,0]-lat)**2 + ((P[:,1]-lon)*np.cos(np.radians(lat)))**2); la, lo = P[i]; tile, k = pts[(la, lo)]; out = []
    for y in range(1984, 2010):
        f = f'weather/cache/{tile}_{y}_RAIN.npz'
        if not os.path.exists(f): continue
        v = np.load(f)['vals'][k]; idx = pd.date_range(f'{y}-01-01', periods=len(v)); s = pd.Series(v, idx); s = s.where(s > -90)
        mm = s.resample('MS').sum(min_count=25); out += [(t.year, t.month, float(x)) for t, x in mm.items()]
    return pd.DataFrame(out, columns=['year','month','power']), (la, lo)
def get(url):
    for t in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            print('HTTP', e.code); time.sleep(30*(t+1))
    return {}
allc = []
for m in meta.itertuples():
    if m.lat is None or m.lon is None: print('no coords', m.file); continue
    pw, gp = power_monthly(m.lat, m.lon); print(m.file, 'station', round(m.lat,3), round(m.lon,3), 'POWER grid', gp, flush=True)
    df = pw
    for model in ['era5_seamless', 'era5']:
        cf = f'{S}/cache/st_{m.file}_{model}.csv'; os.makedirs(f'{S}/cache', exist_ok=True)
        if os.path.exists(cf): df = df.merge(pd.read_csv(cf), on=['year','month'], how='outer'); print('  cached', model); continue
        q = dict(latitude=m.lat, longitude=m.lon, start_date='1984-01-01', end_date='2009-12-31', timezone='GMT', models=model, daily='precipitation_sum')
        j = get('https://archive-api.open-meteo.com/v1/archive?' + urllib.parse.urlencode(q) + ('&elevation=nan' if model == 'era5' else ''))
        if 'daily' not in j: print('  fail', model, j); continue
        s = pd.Series(j['daily']['precipitation_sum'], pd.to_datetime(j['daily']['time'])).astype(float).resample('MS').sum(min_count=25)
        c = pd.DataFrame({'year': s.index.year, 'month': s.index.month, model: s.values}); c.to_csv(cf, index=False)
        df = df.merge(c, on=['year','month'], how='outer'); time.sleep(2)
    df['station'] = m.file; allc.append(df)
pd.concat(allc).to_csv(f'{S}/station_compare_monthly.csv', index=False); meta.to_csv(f'{S}/station_meta.csv', index=False); print('done')
