# Handoff — where things stand (written 2026-10-03, end of day)

Resume with `claude --resume` (or `claude -c`) in `~/Claude/bolivia-enso`, or just read this file.

## State (updated 2026-10-03, second stop)
- **Everything through the rename is done, committed and pushed**: Phase 1 inputs, `nitrogenRateSource`,
  `riceSystem: upland`, Tapiti rename, US-history purge. `~/Claude/bolivia-enso/Tapiti` is clean on
  `bolivia`, tracking `origin/bolivia` (github.com/jawoo/Tapiti).
- **Phase 2 reference run: v8** (`runs/20261004-2232_v8_calib-round2/`, archived with manifest; PLAN §7.3b). Progress deck for the
  project lead built from it: `documents/Tapiti-progress-report_2026-10-05.pptx` (+ rendered slides; also copied to
  `C:\Users\JKOO\Documents\tapiti-deck\`); a variant with one Phase 3 headline slide is `..._with-Phase3.pptx` (build with `DECK_PHASE3=1`); **`..._v2.pptx` (22 slides, build with `DECK_PHASE34=1`) adds the Phase 3–4 section with visuals and updated status/next-steps slides**, rebuilt by
  `python3 analysis/deck_figures.py runs/<run> derived/deck_<tag> && python3 analysis/build_deck.py derived/deck_<tag> runs/<run> <out.pptx>`.
- **Runs:** v4 (baseline, 2026-10-03) and v5 (pre-season defaults, old cultivars, 2026-10-04, 55 min, no errors)
  completed, but both merged outputs were lost to the next launch (see recipe below); their summary tables survive
  in `derived/baseline_v4/` (v5 has none). **v6** (pre-season defaults + BOL cultivars) launched 2026-10-04 ~19:45,
  log `runs/prod_1983-2024_v6_bol-cultivars.log`. Re-run v5 only if the boundary-condition vs cultivar
  decomposition is wanted at full scale; the 60-cell sample already gives it (PLAN §7.3, §7.3b).

## Next: Phase 2 (calibration), in this order — see `PLAN.md` §7.0 for the baseline numbers
1. ~~Zone fix~~ — done 2026-10-04: the La Paz rice sits at 3,500–4,000 m (MapSPAM allocation error, not cell
   averaging), so RI/SB above 2,800 m are excluded (141 records, `derived/excluded_mapspam_allocation.csv`).
2. ~~Soil N sensitivity~~ — done 2026-10-04; the real culprit is the 1 January simulation start (PLAN §7.3).
   Four config knobs added (somModel, simulationStartDaysBeforePlanting, initialSoilWaterFraction, initialSoilN).
   Adopted (user, 2026-10-04): start −60 d, water 0.5 PAW, N 0.3/0.7, CENTURY; committed fbe5816; run v5 launched.
3. ~~Cultivar calibration~~ — done on the sample 2026-10-04 (PLAN §7.3b): BOL maize ×3 zones, BOL SECANO rice, BOL GRANIFERO
   sorghum; wheat left as is (insensitive, ~1.6× bias handled statistically). v7 verified at full scale; round 2
   (SC maize G2 820/G3 7.0, lowland_traditional class, sorghum G2 3.4) committed and run as **v8** (2026-10-04 evening).
4. ~~Soya anomaly diagnosis~~ — done 2026-10-04 (PLAN §7.3c): the model is rainfall-loving (+0.73) where INE is flat;
   soil-side fixes don't flip it. Phase 3 uses the model for drought/heat and a statistical excess-rain term for soya.
5. ~~Phase 3 first pass~~ — done 2026-10-05: `documents/Phase3-ENSO-hindcast_2026-10-05.md` (+ `derived/phase3/`, figures).
   Open items inside Phase 3: statistical excess-rain term for soya (designed, not fitted); per-department tables for the
   deliverable; 1982/83 only via stations. Then **Phase 4** (analogue resampling for 2026/27; C3S path) and the MapSPAM
   municipal cross-check (PLAN §6.1).
6. ~~Phase 4 first estimate~~ — done 2026-10-05: `documents/Phase4-2026-27-outlook_2026-10-05.md`; analogue ensemble in
   `runs/phase4/` (42 × 9.1k seasons), SEAS5 Sep-2026 weights in `derived/phase4/`. **Monthly update**: on each SEAS5 release
   (~8th) run `analysis/phase4_c3s_fetch.py YYYY-MM`, `phase4_forecast_weights.py <nc>`, `phase4_summarise.py <weights>`,
   `phase4_report.py <out.md> YYYY-MM`; to move the splice date, regenerate POWER weather (`prep/gen_weather_bolivia.py`),
   set SPLICE in `prep/gen_weather_analogue.py`, delete `runs/phase4/analog_*` and rerun the ensemble (~45 min).
   Open: soya excess-rain term; per-department deliverable tables; potato module; 1984–2011 INE request.

Full-run recipe (55–75 min) — **use `analysis/run_tapiti.sh <tag>` to launch and `analysis/archive_run.sh <tag> runs/prod_<tag>.log` when it finishes**; they encode the steps below and `runs/INDEX.md` lists every archived run. Background: **Tapiti wipes `res/result/` and `res/.temp/summary/` when it starts** — archive
the previous run's merged output *before* launching the next one, or it is gone (this is how the v4 and v5
merged outputs were lost on 2026-10-03/04; v5 is reproducible from `runs/prod_1983-2024_v5_preseason60.log`
settings = the committed config at fbe5816 with the pre-calibration cultivars).
```bash
cd ~/Claude/bolivia-enso/Tapiti
mkdir -p ../runs/<prev-tag> && mv res/result/*combinedOutput*.csv ../runs/<prev-tag>/ 2>/dev/null   # archive first!
nohup java -jar target/tapiti-1.0-SNAPSHOT-jar-with-dependencies.jar > ../runs/prod_<tag>.log 2>&1 &
# when done, from ~/Claude/bolivia-enso:
mkdir -p runs/<tag> && mv Tapiti/res/result/*combinedOutput*.csv runs/<tag>/
python3 analysis/summarise_run.py runs/<tag>/<file>.csv && python3 analysis/compare_ine.py runs/<tag>/<stem>_depto_year.csv
```

## Decisions taken by the user (2026-10-03)
1. **Rice → upland mode.** Agreed and **implemented 2026-10-03** (`riceSystem: upland`, both SNX writers, verified; see `Tapiti/BOLIVIA.md`).
2. **Rename Tokki → Tapiti** (no accent). Agreed and **done 2026-10-03**: directory `Tapiti`, Maven `org.cgiar:tapiti`, Java package `org.cgiar.tapiti`, class `TapitiConfig`, output `tapiti_combinedOutput_*.csv`, git remote `tokki-upstream`; all workspace docs/scripts/memory updated. Pushed to github.com/jawoo/Tapiti (`origin`, branch `bolivia`). History rewritten 2026-10-03 with git-filter-repo to purge inherited US data (US.SOL, US unit tables, prep/); Tapiti shares no commits with Tokki any more.

## Next steps, in order
1. ~~Rice upland mode~~ — done 2026-10-03. Finding: soil N initialisation (0 ppm) now tops the Phase 2 list (`PLAN.md` §7.3).
2. ~~Rename to Tapiti~~ — done 2026-10-03.
3. ~~Commit~~ — done and pushed to github.com/jawoo/Tapiti (`bolivia`).
4. **Production run** — see Restart above.
5. Phase 2 begins from that comparison (maize cultivar recalibration first).

## Open items noted today
- Sowing-window sensitivity: the lowland maize median (289 vs 320) flips 2015/2016 in Santa Cruz;
  needs its own sensitivity run in Phase 3 (`PLAN.md` §6.4).
- Upstream US run applied `nFertRateRec`, not NASS actual N (memory note + `BOLIVIA.md`).
- INE departmental series only covers 2012–2024; 1984–2011 must be requested.
- `openpyxl` is now installed (user site), so the INE and SENAMHI Excel files are readable.
