#!/usr/bin/env python3
"""Bolivia subset of MapSPAM 2020 v2r2 harvested area by technology (TI irrigated,
TR rainfed, TA all) for the in-scope crops -> derived/mapspam_irrigation_bolivia.csv.
Columns per crop: <crop>_TI, <crop>_TR, <crop>_TA (ha). Used by
build_unit_information_bolivia.py for the waterSupply flag (I if TI/TA > 0.5)."""
import pandas as pd, os
D = os.path.expanduser('~/Claude/mapspam-2020/spam2020/harv/spam2020V2r2_global_harvested_area/')
crops = ['soyb', 'maiz', 'rice', 'sorg', 'whea', 'pota']
out = None
for tech in ['TI', 'TR', 'TA']:
    parts = []
    for ch in pd.read_csv(f'{D}spam2020V2r2_global_H_{tech}.csv', chunksize=250000, low_memory=False):
        sub = ch[ch['ADM0_NAME'] == 'Bolivia']
        if len(sub): parts.append(sub)
    df = pd.concat(parts)
    df = df[['grid_code'] + crops].rename(columns={'grid_code': 'CELL5M', **{c: f'{c}_{tech}' for c in crops}}).set_index('CELL5M')
    out = df if out is None else out.join(df, how='outer')
    print(tech, len(df), 'cells', flush=True)
out = out.fillna(0).reset_index()
out.to_csv(os.path.expanduser('~/Claude/bolivia-enso/derived/mapspam_irrigation_bolivia.csv'), index=False)
tot = {c: (out[f'{c}_TI'].sum(), out[f'{c}_TA'].sum()) for c in crops}
for c, (ti, ta) in tot.items(): print(f'{c}: irrigated {ti:,.0f} ha of {ta:,.0f} ha ({100*ti/max(ta,1):.1f}%)')
