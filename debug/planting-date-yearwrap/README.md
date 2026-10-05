# Bug: `ScanningPlantingDates` discards the year, wrapping planting dates by ±365 days

Debugged 2026-09-15. Reproducer, fix and regression evidence are in this directory.

**Status: COMMITTED in `~/Codebase/Tokki` on 2026-09-15** as `92b7078` on branch
**`fix/planting-date-year-wrap`**, one commit off `master`, 22 insertions / 6 deletions in
`src/main/java/org/cgiar/tokki/ScanningPlantingDates.java`. Compiles clean off master.

The commit was made through a temporary `git worktree` rather than by switching branches:
`res/.csm/MZCER048.CUL` and `res/.csm/SBGRO048.CUL` exist only on
`commit-calibrated-cultivars`, so a plain `git checkout master` would have deleted the
calibrated cultivars from the working tree.

The same edit also remains **uncommitted in the working tree on
`commit-calibrated-cultivars`**, which is what the currently built jar contains. To
de-duplicate: `git checkout -- src/main/java/org/cgiar/tokki/ScanningPlantingDates.java`
then merge `fix/planting-date-year-wrap`.

## Diagnosis

`ScanningPlantingDates.findOnsetDate()` parses the weather file into a map keyed by
`YYYYDDD`, builds its scan window in **index space** around the median planting date, then
returns the day-of-year only:

```java
// ScanningPlantingDates.java:143
return candidateKey % 1000;      // and :220 in fallbackMaxRainfall
```

The caller pairs that bare DOY with the loop year:

```java
// ScanningPlantingDates.java:97
yearToPlantingDate.put(yr, ddd);
```

and `SnxWriterSeasonalRuns` composes the DSSAT `PDATE` as `yy + ddd`, i.e. it assumes the DOY
belongs to `yr`. The scan window is **±30 days for every crop** — `getPlantingDateCriteria()`
index 4, not the 7 at index 3 (that is `drySpellMaxDays`). So whenever the median planting
date falls within 30 days of a year boundary, the window spans two calendar years and the
returned DOY may belong to the wrong one.

The onset look-ahead (`sumRainfall`, `hasFalseStart`) reading past the boundary is *correct* —
rain expected in early January is a legitimate reason to sow in late December. Only the
**candidate day** must be constrained.

## Reproduction — the bug is bidirectional

Synthetic Santa Cruz lowland cell (`wth/9999999.WTH`), 2026 rains fail and the season finally
breaks on 15 Jan 2027 — a severe El Niño delay, which is exactly the case of interest:

```
crop=SG  tmin>=12C  onsetRain>=20mm/10d  drySpellMax=7d  windowHalfDays=+/-30

medianDOY  window(DOY)    returned  planted on  offset vs intent
350        320..380 <-- crosses    7        2026-007   WRONG: -365 d (intended 2027-007)
360        330..390 <-- crosses    7        2026-007   WRONG: -365 d (intended 2027-007)
```

The scan correctly identifies 2027-007 as the onset, returns `7`, and the crop is planted
**2026-007 — 365 days early**.

The mirror case (`wth/8888888.WTH`, Dec 2026 wet / Jan–Apr 2027 dry, `simYear=2027`):

```
medianDOY  window(DOY)             returned  planted on  verdict
5          -25..35 <-- prior Dec      340    2027-340    WRONG: +365 d (intended 2026-340)
20         -10..50 <-- prior Dec      355    2027-355    WRONG: +365 d (intended 2026-355)
```

Reproduce with:

```bash
JAR=~/Codebase/Tokki/target/tokki-1.0-SNAPSHOT-jar-with-dependencies.jar
javac -cp "$JAR" -d out src/PdBug.java src/PdBug2.java     # place under org/cgiar/tokki/
java -cp "out:$JAR" org.cgiar.tokki.PdBug  ./wth SG
java -cp "out:$JAR" org.cgiar.tokki.PdBug2 ./wth SG 2027 8888888.WTH
```

## Frequency on real weather

`PdRegress` over 40 real US cells × 31 years × 5 crops from
`res/weather/1995-2025_usa-mzsb-47707`, at wrap-prone medians (`base_edge.txt`):

| median DOY | wrapped decisions |
|---|---|
| 5 | 50–63% |
| 15 | 34–50% |
| 340 | 2–7% |
| 350 | 10–19% |
| 360 | 20–32% |
| **overall** | **8,775 / 31,000 = 28.3%** |

So when the configuration puts the median near a year boundary, the bug fires in a large
fraction of years — it is not a rare edge case.

## Severity for the actual runs

**The US production run is unaffected.** US maize/soybean medians are ~DOY 110–150, so the
±30 window never approaches a boundary. Verified: 40 cells × 5 crops × 7 medians (100–160)
× 31 years = 43,400 decisions, `base_us.txt` vs `fix_us.txt` **byte-identical**.

**Bolivia, as planned, would also not have fired it** — but with little margin. Scanning ±30
around each window midpoint from `derived/crop_calendar_bolivia.csv`:

| Crop / season | Sowing window (DOY) | Median | Scan span | Headroom to 365 |
|---|---|---|---|---|
| Soya verano | 305–335 | 320 | 290..350 | 15 d |
| Maíz manual | 289–350 | 319 | 289..349 | 16 d |
| **Sorgo verano** | 289–366 | 327 | 297..357 | **8 d** |
| **Frejol valles** | 289–366 | 327 | 297..357 | **8 d** |
| Arroz verano | 289–320 | 304 | 274..334 | 31 d |

So the bug is a **latent hazard rather than a live defect** for the planned configuration.
It becomes reachable if any of the following happens — all of them plausible:

- medians are set per-cell or per-department from spatially varying data rather than one
  national midpoint, and drift later than DOY 335 (8 days of drift for sorgo/frejol);
- a median is taken from the window *end* instead of its midpoint;
- `windowHalfDays` is widened — a natural first reaction if onset detection fails in dry years;
- a later-sown crop or season is added.

It is worth fixing before Phase 1 rather than after, because the failure is **silent**: a
planting date of DOY 7 is perfectly valid-looking, and the run completes with a plausible
yield for a crop grown in entirely the wrong season.

## Fix (`planting-date-yearwrap.patch`)

Constrain the candidate day — and the fallback — to `year`, leaving the look-ahead free to
read across the boundary:

```java
if (candidateKey / 1000 != year) continue;
```

plus `fallbackMaxRainfall` gains `year`/`medianDDD` parameters, skips out-of-year days, and
returns `medianDDD` if the window holds no day inside `year` (previously it seeded `bestKey`
with `allDays.get(startIdx)`, which could itself be out of year).

### Verification

Re-run after applying to `~/Codebase/Tokki` and rebuilding, i.e. against the **real built jar**
rather than a classpath-shadowed class:

| Test | Result |
|---|---|
| Case A forward wrap | fixed — returns 320/330/335, all in year |
| Case B backward wrap | fixed — returns 001, in year |
| US regression, medians 100–160 | **PASS, byte-identical** to the pre-patch baseline (0 / 1,400 lines; 43,400 year-decisions) |
| Control, medians 5–360 | **946 / 1,000 lines changed** — confirms the patch is actually in the jar |
| Cross-check | new build byte-identical to the verified scratchpad patch |

The control matters: without it, "no diff" is indistinguishable from "patch never loaded".
`base_us.txt` / `base_edge.txt` are the pre-patch baselines, `fix_*` the scratchpad patch,
and the post-build run reproduced both exactly.

## Residual limitation, by design

The patch **truncates** sowing windows at 31 December rather than following them into January.
For sorgo verano and frejol (windows running to 15 Jan) a genuinely delayed onset will now be
clamped to late December instead of being allowed to slip into January. That is a conservative,
visible compromise in place of a silent 365-day error.

Removing it properly means widening the contract so the scan returns `YYYYDDD` and letting the
planting *year* vary — which reaches into `SnxWriterSeasonalRuns` (`icdat = yy+"001"`,
`harvestYear = yy+1`, `PDATE`), `SnxWriterFloweringRuns`, the CO₂ lookup and the output
labelling. That is a larger change that would alter US behaviour, so it is deliberately
deferred. Whether it is worth doing depends on how much of the sorghum/frejol crop is actually
sown in January — checkable against INE data once Phase 1 is running.
