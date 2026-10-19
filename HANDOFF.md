# Handoff — where things stand (updated 2026-10-08)

Resume with `claude --resume` (or `claude -c`) in `~/Claude/bolivia-enso`, or just read this file.

## State (2026-10-08)
- **Phase 4 October update done**: `documents/Phase4-2026-27-outlook_2026-10-08.md` (SEAS5 init 2026-10, splice 2 Oct 2026,
  42 members rerun, 0 DSSAT errors). September runs/tables archived in `runs/phase4_2026-09/`, `derived/phase4_2026-09/`.
  Findings in `PLAN.md` §9 "Update 2026-10-08". The deck was rebuilt 2026-10-14 as `documents/Tapiti-progress-report_2026-10-19.pptx` (28 slides) with
  `DECK_PHASE5=1 python3 analysis/build_deck.py derived/deck_v8 runs/20261004-2232_v8_calib-round2 <out.pptx>`: October SEAS5
  numbers read from `derived/phase4/`, a season-so-far slide (3, from `analysis/season_progress_chart.py --run <run>`, rerun with `--refresh` after a POWER
  update), a what-the-science-says slide (4, added 2026-10-18: Niño-3.4/1+2 chart from `analysis/enso_state_chart.py --refresh`, which re-downloads the
  CPC index tables into `derived/enso_state/`; the quotes and their dates are hard-coded in `build_deck.py` and must be re-checked by hand at each update,
  next CPC discussion 12 Nov 2026), a weather-sources slide (22) and three Phase 5 slides (23–25); render to PNG with
  `analysis/render_pptx_windows.sh` to check.
- **Invierno 2026 check**: INE not yet published; ANAPO press figures agree in sign and size with the nowcast (report §3).
- **This workspace is a git repo** (`main`) with **no remote** — `gh` is not logged in and `jawoo/bolivia-enso` does not exist on
  GitHub. Create it (private) and `git remote add origin https://github.com/jawoo/bolivia-enso.git && git push -u origin main`.
- **NeuralGCM feasibility (2026-10-08)**: runs on this laptop's RTX A1000 (6 GB). Measured per forecast day: 2.8° deterministic 6 s,
  1.4° stochastic 40 s (2 GB VRAM, ~2 h per 180-day member), 2.8° precip model 3.3 s. Scratch install only (JAX 0.6.2 + CUDA 12,
  pip `--target`, not in the repo); `python3-venv` is not installed. Caveats: global-only, 20 (2.8°) / 99 (1.4°) cells over Bolivia,
  v1 models output no precipitation / 2 m temperature / radiation, SST + sea-ice forcing must be prescribed for the season.
  ARCO ERA5 on GCS is anonymous and populated to 2026-10-02. Decision pending: whether and where it enters the pipeline.
- Nothing is running.

## Monthly update loop (verified 2026-10-08, ~50 min wall-clock)
1. `python3 analysis/phase4_c3s_fetch.py YYYY-MM` (CDS; request accepted immediately once the release is out, ~the 8th)
2. `python3 analysis/phase4_forecast_weights.py derived/phase4/c3s/seas5_YYYY-MM_bolivia.nc`
3. `python3 analysis/phase4_seas5_figure.py derived/phase4/seas5_YYYY-MM_zone_member_anomalies.csv`
4. `python3 prep/gen_weather_bolivia.py` (POWER refresh, ~3 min) → archive `runs/phase4/analog_*` to `runs/phase4_<prev>/` →
   `bash analysis/phase4_run_analogues.sh $(seq 1983 2024)` (~40 min; splice date is derived automatically)
5. `python3 analysis/phase4_summarise.py derived/phase4/analogue_weights_YYYY-MM.csv` (**the argument is required**)
6. `python3 analysis/phase4_report.py documents/Phase4-2026-27-outlook_<date>.md YYYY-MM`

## When the user is back: first actions
1. Push this workspace (above) — still pending, needs `gh auth login` or a repo created on GitHub.
2. ~~Decide on NeuralGCM~~ — decided 2026-10-14: NeuralGCM dropped; POWER history → Open-Meteo `ecmwf_seasonal_seamless` members (EC46 → SEAS5) drive DSSAT (PLAN.md §12). Professional tier being subscribed. **Built and smoke-tested 2026-10-14** (16 sample + 6 smoke cells fetched, member weather written, Tapiti ran the 2026/27 campaign on member 01 with 0 errors).
   Phase 5 loop (after the SEAS5 release on the 5th, or any day for an EC46 refresh of days 1–46):
   paid key in `~/.config/open-meteo/apikey` (chmod 600, outside the repo) or `export OPEN_METEO_API_KEY=...` (→ customer endpoint; without it the free tier manages ~18 points/h, 10k calls/day ≈ 37 points, and 483 points are needed)
   1. `python3 analysis/phase5_om_fetch.py --cells all` (483 points, ~2 min on the paid tier; cache `derived/phase5/om/<run>/`, resumable, exit 2 while points are missing; refetches responses whose rain/SRAD end early)
   2. `python3 prep/gen_weather_forecast.py --run <run>` (51 dirs `Tapiti/res/weather/2026_fc_<mm>/`, 8 GB, ~5 min; or let step 3 build each on demand)
   3. `bash analysis/phase5_run_members.sh <run> $(seq 0 50)` (~1 min per member on the smoke set; the full table is ~1 min/analogue in Phase 4, so expect ~1 h)
   4. `python3 analysis/phase5_summarise.py <run>` → `derived/phase5/<run>/member_ensemble_*.csv`, figure `chart_2026_27_members_vs_analogues.png`
   Tail beyond the forecast horizon = top-weighted Phase 4 analogue (`--analogue YEAR` overrides). Bias factors per cell in `derived/phase5/<run>/bias_factors_*.csv`.
3. Next SEAS5 release ~8 Nov: run the monthly loop above.
4. Re-check INE for invierno 2026 statistics (nowcast: Santa Cruz sorgo +49% vs last ten campaigns).

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

## Open-Meteo assessment (2026-10-13/14) — see `documents/OpenMeteo-assessment_2026-10-14.md`
Verdict: keep POWER for historical weather (its gauge-corrected precipitation beats ERA5 against SENAMHI stations: NDJFM
interannual r 0.80 vs 0.42, annual error −3 % vs +30 %); temperature differences are an elevation-representation issue to fix
on the POWER cache (DEM + lapse rate), not a source issue; radiation equivalent. The one pipeline-relevant novelty: free daily
SEAS5 members (51, 36 km, 7 months) and EC46 (46 d) via Open-Meteo since ECMWF open data (Oct 2025) — three options in the
document §4, decision pending. SARAH-3 radiation covers Bolivia only east of 65°W; WeatherNext 2 is on the ensemble API.
Completed 2026-10-14 on the paid archive endpoint: all 18 stations and 16 cells (document §3 updated; POWER wins at 15 of 18
stations, Chimoré/Chapare is POWER's blind spot: 736 vs 4,089 mm/yr observed). Decision taken: option 2 → Phase 5 (PLAN.md
§12), Professional tier subscribed, key in `~/.config/open-meteo/apikey`. First 51-member run done 2026-10-14; results in
`derived/phase5/2026-10-14/` and §8 of the outlook document. v1 of the bias adjustment (single mean-T shift) is archived under
`v1_meanshift/`; the production version shifts Tmax and Tmin separately.
