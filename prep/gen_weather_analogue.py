#!/usr/bin/env python3
"""Spliced weather for the 2026/27 campaign: observed 1 Jan 2025 - 25 Sep 2026 (NASA POWER, as in
1981-2026_bol), then the weather of analogue campaign A from 26 Sep onward, mapped by calendar date
(26 Sep A .. 31 Dec A+1  ->  26 Sep 2026 .. 31 Dec 2027). Writes Tapiti/res/weather/2026_analog_<A>/.
Usage: python3 prep/gen_weather_analogue.py <A> [<A> ...]   (A = analogue sowing year, 1983..2024)"""
import sys, os, glob, time
import pandas as pd
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); SRC = f'{ROOT}/Tapiti/res/weather/1981-2026_bol'
SPLICE = pd.Timestamp('2026-09-26'); TARGET_END = pd.Timestamp('2027-12-31'); START = pd.Timestamp('2025-01-01')
files = sorted(glob.glob(f'{SRC}/*.WTH')); tgt = pd.date_range(START, TARGET_END, freq='D')
def src_key(d, shift):
    if d < SPLICE: s = d
    else:
        try: s = d.replace(year=d.year - shift)
        except ValueError: s = (d - pd.Timedelta(days=1)).replace(year=d.year - shift)
    return s.year * 1000 + s.dayofyear
for A in [int(a) for a in sys.argv[1:]]:
    t0 = time.time(); out = f'{ROOT}/Tapiti/res/weather/2026_analog_{A}'; os.makedirs(out, exist_ok=True); shift = 2026 - A
    keys = [src_key(d, shift) for d in tgt]; tkeys = [f'{d.year}{d.dayofyear:03d}' for d in tgt]   # same mapping for every file
    for i, p in enumerate(files):
        L = open(p).read().split('\n'); k = next(j for j, l in enumerate(L) if l.startswith('@  DATE'))
        rest = {int(l[0:7]): l[7:] for l in L[k + 1:] if l.strip()}
        try: rows = [tk + rest[sk] for tk, sk in zip(tkeys, keys)]
        except KeyError as e: raise SystemExit(f'missing day {e} in {p}')
        hdr0 = L[0] + f'  | 2026/27 analogue {A}: observed to 2026-09-25, then {A}/{A+1} weather'
        with open(f'{out}/{os.path.basename(p)}', 'w') as f: f.write('\n'.join([hdr0] + L[1:k + 1] + rows) + '\n')
    print(f'analogue {A}: wrote {len(files)} files to {out}  ({int((tgt < SPLICE).sum())} observed days, {int((tgt >= SPLICE).sum())} analogue days, {time.time() - t0:.0f} s)')
