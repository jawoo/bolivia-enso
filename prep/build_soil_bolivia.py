#!/usr/bin/env python3
"""Subset the national ISRIC SoilGrids + HC27 soil library (data/BO.SOL, 13,069
5-arcmin profiles covering all of Bolivia) to the modelled cells and write
Tapiti/res/input/BO.SOL.

Cells with no profile of their own (water / no-data pixels in SoilGrids) take the
nearest available profile, relabelled with the cell's own id and centroid so the
soilProfileId == BO + CELL5M convention holds for every record. Each such fill is
listed in derived/soil_fill_log.csv.
"""
import os, re, numpy as np, pandas as pd
ROOT = os.path.expanduser('~/Claude/bolivia-enso')
cells = pd.read_csv(f'{ROOT}/derived/cells_bolivia_mapspam2020.csv')
prof, cur = {}, None
for line in open(f'{ROOT}/data/BO.SOL', errors='replace'):
    if line.startswith('*BO'):
        cur = int(line[3:11]); prof[cur] = [line.rstrip('\n')]
    elif cur is not None:
        prof[cur].append(line.rstrip('\n'))
pids = np.array(sorted(prof))
coord = np.array([[float(prof[p][2].split()[2]), float(prof[p][2].split()[3])] for p in pids])

def retoken(line, repl):
    out = list(line)
    for i, m in enumerate(re.finditer(r'\S+', line)):
        if i in repl:
            w = m.end() - m.start(); out[m.start():m.end()] = list(str(repl[i])[:w].rjust(w))
    return ''.join(out)

out = ['*SOILS: Bolivia, ISRIC SoilGrids v2 + HC27 (5 arc-min), subset to modelled cells by prep/build_soil_bolivia.py', '']
fills = []
for r in cells.itertuples():
    c = int(r.CELL5M)
    if c in prof:
        body = list(prof[c])
    else:
        d = np.hypot(coord[:, 0] - r.y, coord[:, 1] - r.x); j = int(d.argmin()); src = int(pids[j])
        body = list(prof[src])
        body[0] = f'*BO{c:08d}' + body[0][11:]
        body[2] = retoken(body[2], {2: f'{r.y:.3f}', 3: f'{r.x:.3f}'})
        fills.append({'CELL5M': c, 'x': r.x, 'y': r.y, 'departamento': r.departamento,
                      'source_profile': f'BO{src:08d}', 'distance_deg': round(float(d[j]), 3)})
    while body and not body[-1].strip(): body.pop()
    out += body + ['']
dst = f'{ROOT}/Tapiti/res/input/BO.SOL'
open(dst, 'w').write('\n'.join(out) + '\n')
pd.DataFrame(fills).to_csv(f'{ROOT}/derived/soil_fill_log.csv', index=False)
print(f'wrote {dst}: {len(cells)} profiles, {len(fills)} filled from nearest neighbour')
print(pd.DataFrame(fills).to_string(index=False))
