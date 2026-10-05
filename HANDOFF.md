# Handoff — where things stand (written 2026-10-03, end of day)

Resume with `claude --resume` (or `claude -c`) in `~/Claude/bolivia-enso`, or just read this file.

## State (updated 2026-10-05, user away until ~2026-10-08)
- **Phases 1–4 all have a first pass.** Reports: `documents/Phase3-ENSO-hindcast_2026-10-05.md`,
  `documents/Phase4-2026-27-outlook_2026-10-05.md`; deck `documents/Tapiti-progress-report_2026-10-05_v2.pptx`
  (22 slides, also in `C:\Users\JKOO\Documents\tapiti-deck\`). Findings are summarised in `PLAN.md` §7.0–§9 status blocks.
- **Tapiti repo** (`Tapiti/`, branch `bolivia`): clean, all commits pushed to github.com/jawoo/Tapiti.
- **This workspace is now a git repo** (`main`, commit 58dd862, 196 files) with **no remote yet** — the user will create
  one (suggested `jawoo/bolivia-enso`, private) or run `gh auth login`; then `git remote add origin <url> && git push -u origin main`.
- Nothing is running. Phase 2 reference run v8 and the 42-member Phase 4 ensemble are archived under `runs/` (local only).

## When the user is back: first actions
1. Push this workspace (above).
2. If the October SEAS5 release is out (~8 Oct): `python3 analysis/phase4_c3s_fetch.py 2026-10`, then
   `phase4_forecast_weights.py derived/phase4/c3s/seas5_2026-10_bolivia.nc`, `phase4_summarise.py derived/phase4/analogue_weights_2026-10.csv`,
   `phase4_report.py documents/Phase4-2026-27-outlook_<date>.md 2026-10`; optionally regenerate POWER weather to extend the
   observed splice (`prep/gen_weather_bolivia.py`, then set SPLICE in `prep/gen_weather_analogue.py`, delete `runs/phase4/analog_*`, rerun
   `analysis/phase4_run_analogues.sh $(seq 1983 2024)`, ~45 min).
3. Check INE for invierno 2026 statistics (nowcast test: Santa Cruz sorgo +62% vs trend).

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
