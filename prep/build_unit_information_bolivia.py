#!/usr/bin/env python3
"""Assemble Tapiti/res/input/unit-information.jsonl (and cell-gdd.csv) for Bolivia.

Inputs (all under ~/Claude/bolivia-enso):
  derived/cells_bolivia_mapspam2020.csv   3,568 MapSPAM 2020 cells, harvested area (ha) per crop
  derived/mapspam_irrigation_bolivia.csv  MapSPAM irrigated / rainfed / all-tech area per crop
  derived/cells_elev_tav.csv              elevation from the .WTH headers (POWER DEM)
  derived/cells_gdd_bolivia.csv           1991-2020 mean GDD (base 10, cap 30) over 150 d from
                                          sowing DOY 289/305/320, plus frost statistics
  derived/management_defaults_bolivia.csv zone x crop x season table: median sowing DOY,
                                          density, N rates, cultivar (see SOURCES in derived/)
  Tapiti/res/input/BO.SOL               soil profiles (prep/build_soil_bolivia.py)

Rules
  * zone by elevation: lowland < 800 m, valleys 800-2800 m, altiplano > 2800 m.
  * one record per crop code per cell (Tokki keys output files by unit/cell/crop/cultivar,
    not by planting date, so a second season of the same crop would collide). The season
    simulated is the dominant one for that crop in that department per INE 2012-2024
    (derived/ine_season_shares_by_depto.csv): verano for SB/RI, primavera-manual for MZ,
    wheat and sorghum invierno in the Santa Cruz lowlands (89% / 87% of their departmental
    area) and in Tarija/Beni for wheat, verano everywhere else. See season_for().
  * a crop is included in a cell when its MapSPAM harvested area is >= AREA_MIN ha, except
    rice and soya above 2,800 m (MapSPAM allocation errors, logged to derived/).
  * waterSupply = I when irrigated share of the crop's harvested area > 0.5, else R.
    Irrigated rice gets nFertRateAct 40 (the secano row carries 15); Tokki's riceSystem:
    upland then writes it as direct-seeded, puddled, bunded and flooded from 25 DAP.
  * maize cultivar by zone: BOL LOWLAND / BOL VALLEYS / BOL ALTIPLANO in MZCER048.CUL,
    calibrated on INE yield levels (PLAN.md 7.3); soybean MG by the latitude rule (MG 8
    everywhere in Bolivia); other crops take the fixed cultivar in the management table
    because their CUL files carry no flagged entries and Tapiti would otherwise run nothing.
  * soilRootingDepth = 200 cm (full HC27 profile). No national restrictive-layer source.
"""
import json, os, sys
import pandas as pd, numpy as np
import jsonschema

ROOT = os.path.expanduser('~/Claude/bolivia-enso')
INP = f'{ROOT}/Tapiti/res/input'
AREA_MIN = 25.0
SPAM = {'SB': 'soyb', 'MZ': 'maiz', 'RI': 'rice', 'SG': 'sorg', 'WH': 'whea'}
MZ_CLASS = {3.0: ('990001', 'LONG SEASON'), 2.0: ('990002', 'MEDIUM SEASON'), 1.0: ('990003', 'SHORT SEASON')}   # US generics (reference)
MZ_ZONE = {'lowland': ('BOLL11', 'BOL LOWLAND'), 'lowland_traditional': ('BOLV03', 'BOL VALLEYS'), 'valleys': ('BOLV03', 'BOL VALLEYS'), 'altiplano': ('BOLA03', 'BOL ALTIPLANO')}
COMMERCIAL_LOWLAND_MAIZE = {'Santa Cruz', 'Tarija'}   # mechanised maize; elsewhere lowland maize is smallholder manual

cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv')
irr = pd.read_csv(f'{ROOT}/derived/mapspam_irrigation_bolivia.csv')
elev = pd.read_csv(f'{ROOT}/derived/cells_elev_tav.csv')[['CELL5M', 'elev']]
gdd = pd.read_csv(f'{ROOT}/derived/cells_gdd_bolivia.csv').rename(columns={'cell5m': 'CELL5M'})
mgmt = pd.read_csv(f'{ROOT}/derived/management_defaults_bolivia.csv')
schema = json.load(open(f'{INP}/unit-information.schema.json'))
soil_ids = {l[1:11] for l in open(f'{INP}/BO.SOL') if l.startswith('*BO')}

df = cells.merge(irr, on='CELL5M', how='left').merge(elev, on='CELL5M').merge(gdd, on='CELL5M')
df = df.sort_values('CELL5M').reset_index(drop=True)
df['zone'] = pd.cut(df.elev, [-1, 800, 2800, 99999], labels=['lowland', 'valleys', 'altiplano']).astype(str)
M = mgmt.set_index(['zone', 'crop', 'season'])

def season_for(code, zone, depto):
    """Dominant campaign for the crop in this department (INE 2012-2024 area shares)."""
    if code == 'WH':
        return 'invierno' if (depto == 'Santa Cruz' and zone == 'lowland') or (depto in ('Tarija', 'Beni') and zone != 'altiplano') else 'verano'
    if code == 'SG':
        return 'invierno' if depto == 'Santa Cruz' and zone == 'lowland' else 'verano'
    return 'primavera' if code == 'MZ' and zone == 'lowland' else 'verano'

def gdd_at(row, doy):
    k = min((289, 305, 320), key=lambda d: abs(d - doy))
    return float(row[f'gdd150_d{k}'])

records, stats, excluded, excluded_alloc = [], [], 0, []
for r in df.itertuples(index=False):
    rd = r._asdict()
    crops = []
    for code, sp in SPAM.items():
        area = float(rd[f'{sp}_H_TA_ha'])
        if not area >= AREA_MIN: continue
        if code in ('RI', 'SB') and r.zone == 'altiplano':
            # MapSPAM allocation error: La Paz departmental rice (grown at 400-1,000 m in Alto
            # Beni / Caranavi) lands on 3,500-4,000 m pixels, Tarija soya (Chaco lowlands) on
            # ~2,960 m pixels. 129 rice + 12 soya records, 7.4 kha; they fail in ~100% of
            # seasons (baseline v4). Excluded; see PLAN.md §7.0.
            excluded_alloc.append({'CELL5M': int(r.CELL5M), 'departamento': r.departamento, 'elev_m': float(r.elev), 'crop': code, 'area_ha': area})
            continue
        season = season_for(code, r.zone, r.departamento)
        mzone = r.zone
        if code == 'MZ' and r.zone == 'lowland' and r.departamento not in COMMERCIAL_LOWLAND_MAIZE:
            mzone = 'lowland_traditional'   # Beni, Pando, Chapare, lowland La Paz/Chuquisaca: manual, low-input maize
        m = M.loc[(mzone, code, season)]
        ti, ta = float(rd.get(f'{sp}_TI', 0) or 0), float(rd.get(f'{sp}_TA', 0) or 0)
        water = 'I' if ta > 0 and ti / ta > 0.5 else 'R'
        pdoy = int(m.plantingDate)
        if code == 'MZ':
            # Bolivia zone cultivars calibrated on yield level (PLAN.md 7.3, 2026-10-04); the GDD class
            # rule used for the US generics is kept in cell-gdd.csv for reference only.
            cv_code, cv_name = MZ_ZONE[mzone]
        else:
            cv_code, cv_name = str(m.cultivarCode), str(m.cultivarName)
        n_act, n_rec = float(m.nFertRateAct), float(m.nFertRateRec)
        if code == 'RI' and water == 'I':
            # Irrigated rice (~10% of area) is direct-seeded but fertilised: CIPCA irrigated
            # cost sheet 70 kg urea + 50 kg 15-15-15 = 40 kg N/ha (derived/SOURCES-management.md §5).
            n_act = 40.0
        crops.append({'code': code, 'plantingDate': pdoy, 'area': round(area, 1),
                      'nFertRateAct': n_act, 'nFertRateRec': n_rec,
                      'waterSupply': water, 'plantingDensity': float(m.plantingDensity),
                      'cultivar': {'code': cv_code, 'name': cv_name}})
        stats.append({'zone': mzone, 'crop': code, 'season': season, 'area': area, 'water': water,
                      'cultivar': cv_name, 'plantingDate': pdoy})
    if not crops: excluded += 1; continue
    sid = f'BO{int(r.CELL5M):08d}'
    assert sid in soil_ids, sid
    rec = {'unitId': len(records), 'cell5m': int(r.CELL5M), 'x': round(float(r.x), 4), 'y': round(float(r.y), 4),
           'soilProfileId': sid, 'soilRootingDepth': 200, 'crops': crops}
    jsonschema.validate(rec, schema)
    records.append(rec)

with open(f'{INP}/unit-information.jsonl', 'w') as f:
    for rec in records: f.write(json.dumps(rec) + '\n')
# cell-gdd.csv for prep/stamp_cultivars.py compatibility: GDD at the maize sowing date of the cell's zone
mzdoy = {z: int(M.loc[(z, 'MZ', season_for('MZ', z, ''))].plantingDate) for z in ('lowland', 'valleys', 'altiplano')}
pd.DataFrame({'cell5m': df.CELL5M, 'gdd': [gdd_at(rd, mzdoy[rd['zone']]) for rd in df.to_dict('records')]}) \
  .to_csv(f'{INP}/cell-gdd.csv', index=False)

pd.DataFrame(excluded_alloc).to_csv(f'{ROOT}/derived/excluded_mapspam_allocation.csv', index=False)
st = pd.DataFrame(stats)
print(f'excluded as MapSPAM allocation errors (RI/SB above 2,800 m): {len(excluded_alloc)} records -> derived/excluded_mapspam_allocation.csv')
print(f'wrote {INP}/unit-information.jsonl: {len(records)} cells, {len(st)} crop records; '
      f'{excluded} cells had no in-scope crop >= {AREA_MIN} ha (potato-only)')
print('\ncrop records and MapSPAM area (kha) by zone:')
t = st.pivot_table(index='crop', columns='zone', values='area', aggfunc=['count', 'sum']).fillna(0)
t['sum'] = (t['sum'] / 1000).round(1); print(t.to_string())
print('\nirrigated records:'); print(st[st.water == 'I'].groupby(['crop', 'zone']).size().to_string())
print('\ncultivars:'); print(st.groupby(['crop', 'cultivar', 'season', 'plantingDate']).size().to_string())
