#!/usr/bin/env python3
"""Spliced weather for the 2026/27 campaign: observed 1 Jan 2025 - <last observed day> (NASA POWER, as in
1981-2026_bol), then the weather of analogue campaign A from the next day onward, mapped by calendar date
(S A .. 31 Dec A+1  ->  S 2026 .. 31 Dec 2027, S = splice date). Writes Tapiti/res/weather/2026_analog_<A>/.
The splice date is the day after the last day present in every source .WTH file (so it moves forward whenever
prep/gen_weather_bolivia.py is rerun) and is recorded in derived/phase4/splice_date.txt for the report scripts.
Usage: python3 prep/gen_weather_analogue.py <A> [<A> ...]   (A = analogue sowing year, 1983..2024)"""
import sys, os, glob, time
import pandas as pd
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); SRC = f'{ROOT}/Tapiti/res/weather/1981-2026_bol'
TARGET_END = pd.Timestamp('2027-12-31'); START = pd.Timestamp('2025-01-01')
files = sorted(glob.glob(f'{SRC}/*.WTH')); tgt = pd.date_range(START, TARGET_END, freq='D')
def last_day(p):
    k = [l for l in open(p).read().split('\n') if l.strip()][-1][:7]; return pd.Timestamp(year=int(k[:4]), month=1, day=1) + pd.Timedelta(days=int(k[4:]) - 1)
SPLICE = min(last_day(p) for p in files) + pd.Timedelta(days=1); LAST_OBS = (SPLICE - pd.Timedelta(days=1)).date()
os.makedirs(f'{ROOT}/derived/phase4', exist_ok=True); open(f'{ROOT}/derived/phase4/splice_date.txt', 'w').write(f'{SPLICE.date()}\n')
print(f'observed weather ends {LAST_OBS}; splice date {SPLICE.date()}')
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
        hdr0 = L[0] + f'  | 2026/27 analogue {A}: observed to {LAST_OBS}, then {A}/{A+1} weather'
        with open(f'{out}/{os.path.basename(p)}', 'w') as f: f.write('\n'.join([hdr0] + L[1:k + 1] + rows) + '\n')
    print(f'analogue {A}: wrote {len(files)} files to {out}  ({int((tgt < SPLICE).sum())} observed days, {int((tgt >= SPLICE).sum())} analogue days, {time.time() - t0:.0f} s)')
