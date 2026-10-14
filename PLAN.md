# Repurposing Tokki for Bolivia — ENSO crop-impact assessment

Drafted 2026-09-15. Companion to `DATA-INVENTORY.md` (what we have) — this file is what can be
built from it.

---

## 1. The timing constraint shapes everything

CPC's September 2026 diagnostic discussion carries an **El Niño Advisory**: >90% chance of a
very strong event in NH autumn–winter 2026-27, Niño-3.4 at +1.8 °C, Niño-3 at +2.5 °C and
**Niño-1+2 at +3.4 °C**, with a 75% chance that OND 2026 exceeds any event since 1950 on a
3-month RONI basis. ([CPC ENSO diagnostic discussion](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml),
[IRI](https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/))

Two consequences for the work plan:

1. **Bolivia's *campaña verano* is being sown right now.** Maíz primavera and arroz primavera
   sow from 1 September; soya verano from 1 November. The season this El Niño will hit is the
   one starting this month. A retrospective product delivered in, say, March 2027 describes a
   harvest that has already happened.
2. **The strong eastern-Pacific signature points at specific analogues.** 1982/83 (DJF ONI
   +2.1), 1997/98 (+2.2) and 2015/16 (+2.5) are the closest matches; 2023/24 (+1.8) is the most
   recent. Of those, only 2015/16 and 2023/24 are inside the daily climate file we were given
   (2005+). The two events that Bolivian institutional memory treats as the benchmark drought
   years are outside it. That single fact drives the weather-generation decision in §6.2.

So the plan is staged to put a defensible *historical analogue* product in front of people
within weeks, and to keep the forward-looking simulation as a second, separable stage.

---

## 2. Which crops and seasons — narrowing to the ENSO-exposed set

El Niño in Bolivia is not one signal. The literature and SENAMHI's own framing describe a
broadly **drier and warmer Altiplano and valleys** and **more variable, often wetter lowlands**
during the austral summer, with the strongest anomalies Dec–Mar. Our data can test rather than
assume this (§7), but the seasonal targeting is unambiguous: the exposure window is
**October → April**, which is precisely *campaña verano*.

Scoping against `derived/crop_calendar_bolivia.csv` and the area shares in
`DATA-INVENTORY.md` §1.1:

### In scope — Tokki runs these today with no new crop module

| Crop | DSSAT code | Season | Sowing DOY | Verano area share | Why it matters |
|---|---|---|---|---|---|
| Soya | `SB` | verano **and** invierno | 305–335 / 136–152 | 40.5% | Dominant crop; the whole Santa Cruz economy |
| Maíz en grano | `MZ` | primavera + manual | 244–274 / 289–350 | 11.7% | Food security crop, spans lowland + valleys |
| Arroz con cáscara | `RI` | verano + primavera | 289–320 / 244–259 | 6.6% | Rainfed lowland, highly rainfall-sensitive |
| Sorgo en grano | `SG` | verano + invierno | 289–015 / 106–167 | 2.5% (36.8% invierno) | Largest invierno crop |
| Trigo | `WH` | valles + invierno | 106–136 | 2.5% | Import-substitution politics |

Together these are **≈64% of verano area and ≈81% of invierno area**.

### Deferred — real area, but needs model work

- **Papa** (6.1% verano) — DSSAT SUBSTOR-Potato exists but is not wired into Tokki. Highest
  priority deferred crop: it is the Altiplano/valles staple, i.e. exactly the region where the
  El Niño drought signal is expected to be strongest. Dropping it means the food-security story
  is told with the wrong crops.
- **Quínua** (3.8% verano) — no DSSAT module. Not solvable inside this framework.
- **Caña de azúcar** (6.7%) — CANEGRO exists in DSSAT; perennial/ratoon handling is a poor fit
  for Tokki's single-season loop.
- **Girasol** (13.8% invierno) — OILCROP-SUN exists in DSSAT, not in Tokki's crop enum.
- **Frijol/poroto** (2.3%) — CROPGRO dry bean (`BN`); note Tokki's enum has `FB` (faba bean),
  which is a different crop.

**Recommendation:** ship phase 1 on the five in-scope crops, and treat **potato** as the one
crop worth the module work in phase 2. Without it the assessment under-represents the
highlands, and that limitation should be stated in any output rather than glossed.

---

## 3. Workspace: a separate clone, not a separate config

The requirement is no interference with the running US work. A config-only split
(`working: res-bo` in `config.yml`) is not enough, because the two workspaces would still
share `res/.csm/` — and `MZCER048.CUL` / `SBGRO048.CUL` in there carry **US-specific
calibration** that is tracked in the repo. Bolivian cultivar coefficients must diverge from
US ones, so the CUL files have to be separate files, not separate config entries.

```
~/Codebase/Tokki                  # untouched — US production
~/Claude/bolivia-enso/Tapiti               # fresh clone; own res/, own .csm/, own CUL files
~/Claude/bolivia-enso          # this folder: data prep, calibration, analysis, outputs
  data/            as received
  derived/         machine-readable artefacts (crop calendar is the first)
  prep/            input-table builders  (mirrors Tokki/prep for the US)
  weather/         staging for .WTH generation
  analysis/        calibration + ENSO composites  (mirrors ~/Claude/tokki-results/analysis)
```

`~/Claude/tokki-results/` is the model for the analysis side and its
`analysis/scripts/step1_qc.py … step6_figures.py` chain is directly reusable in structure:
QC → admin join → area-weighted aggregate → join official statistics → metrics → figures.
Only `step4_nass.py` needs replacing wholesale (NASS → INE).

---

## 4. Tokki code changes required

Reviewed the 3,852 lines in `~/Codebase/Tokki/src/main/java/org/cgiar/tokki/`. The framework is
closer to country-agnostic than expected — most of what looks US-specific is data, not code.
Concrete changes, smallest first:

**Config only, no code change**
- `countryCode: BOL`, `tableNameUnitInformation`, `directory.weather`, `firstPlantingYear`,
  `numberOfYears`.
- `latBandSize` — the US uses 1° over a 24° span. Bolivia spans ~10–23 °S; keep 1°.
- `CO2048.csv` already runs 1958 → 2050, so it covers any year we would simulate. No change.

**Must change (2 lines + 1 schema)**
1. `App.java:457` — `String soilFile = directoryInput + "US.SOL";` is hardcoded in
   `validateEnvironment()`. Parameterise from `countryCode` (→ `BO.SOL`).
   `ThreadSeasonalRuns.java:223` and `ThreadFloweringRuns.java:92` already derive the filename
   from `soilProfileID.substring(0,2)`, so they need nothing — only the startup check is wrong.
2. `res/input/unit-information.schema.json` — `soilProfileId.pattern` is `^US[0-9]{8}$`.
   Widen to `^[A-Z]{2}[0-9]{8}$`.

**Must verify by smoke test — southern-hemisphere season crossing 1 January**

This is the one genuine technical risk, and it is worth being precise about where it lives.

- `SnxWriterSeasonalRuns.java:239` sets `icdat = yy + "001"` — simulation start is 1 January of
  the **sowing** year. For soya sown DOY 305, DSSAT then runs ~300 days of fallow before
  planting. Not wrong (soil water arrives well initialised) but it lengthens every run, and it
  means the weather file must contain 1 Jan of the sowing year through harvest in the *next*
  year.
- `SnxWriterSeasonalRuns.java:271-282` sets `harvestDate = 365` with
  `harvestYear = yy + 1`, so `HDATE` is already in the following year and `HARVS = M`
  (at maturity) for non-wheat. This looks southern-hemisphere-safe as written.
- `ScanningPlantingDates.findOnsetDate()` returns `candidateKey % 1000` — a bare DOY with the
  year discarded — while the caller pairs it with the loop year. **Debugged, reproduced and
  fixed: see `debug/planting-date-yearwrap/`.** The scan window is ±30 days for every crop
  (`getPlantingDateCriteria` index 4), so any median within 30 days of a year boundary can
  return a DOY from the adjacent year, planting the crop 365 days early or late. On real US
  weather at wrap-prone medians it fires in 28% of decisions.

  Severity, stated precisely: the **US production run is unaffected** (medians ~DOY 110–150;
  43,400 decisions byte-identical before and after the fix), and **Bolivia as planned would
  not have fired it either** — but sorgo verano and frejol have only **8 days of headroom**
  at their window midpoints. It is a latent hazard, not a live defect, and worth fixing before
  Phase 1 because the failure is silent: the run completes with a plausible yield for a crop
  grown in the wrong season. Patch is written and verified; apply it to the `Tapiti` clone.
- **Two-digit years.** `yy = String.valueOf(simYear).substring(2)` and DSSAT's century
  windowing need checking across 1999→2000 if we simulate back to the 1980s.

**Already correct for the southern hemisphere (verified, no change)**
- `Utility.maturityTarget()` takes `Math.abs(latitude)`, so the soybean MG rule
  `MG = (46 − |lat|)/2` returns MG 8 (clamped) for Santa Cruz at ~17.5 °S. MG 7–8 is a
  reasonable default for the Bolivian lowlands, so the fallback degrades sensibly.
- `latBand = floor(y / latBandSize) * latBandSize` behaves correctly for negative latitudes.

**Must rebuild as data, not code**
- `res/input/cell-gdd.csv` drives maize cultivar assignment. Its US definition is
  "planting → first fall frost", which is meaningless in the Santa Cruz lowlands. Needs a
  Bolivia rule — most defensibly GDD accumulated over a fixed calendar season length, with a
  separate rule above ~2,000 m where frost does bound the season.
- Cultivars must be **explicitly stamped** into `unit-information.jsonl` (the schema supports
  `cultivar: {code, name}`) rather than left to the fallback, so the input file documents what
  was run.

---

## 5. Order of work

```
Phase 0  scaffold        DONE    clone, config, smoke test on a handful of cells
Phase 1  input build     DONE    MapSPAM + soil + calendar + weather  → unit-information.jsonl (2026-10-03; management table provisional)
Phase 2  calibration     2-3 wk  INE 1984-2025 departmental yields
Phase 3  ENSO hindcast   1-2 wk  composites by ENSO phase, 1983-2025
Phase 4  forward runs    2-3 wk  2026-27 season under C3S seasonal forecast + analogues
```

**Phase 0 complete (2026-09-15).** Workspace is `~/Claude/bolivia-enso/Tapiti`, branch `bolivia`, cloned
from upstream `master` (which now carries the year-wrap fix). Full divergence record in
`~/Claude/bolivia-enso/Tapiti/BOLIVIA.md`. Three things were settled by the end-to-end smoke run on real
Santa Cruz cells with real NASA POWER weather:

1. **The southern-hemisphere season crossing 1 January works with no model changes** —
   `PDAT 2016336 → MDAT 2017076` under the existing `icdat = yy001` / `harvestYear = yy+1` /
   `HARVS = M` scheme. This was the largest technical unknown in §4 and it is now closed.
2. **The onset scan picks year-specific sowing dates** (DOY 296/305/336 across cells and
   years), confirming the channel that carries the ENSO signal into planting date is live.
3. **The inherited cultivars need recalibration, maize most urgently** — it reaches
   12.8 t/ha against a Bolivian reality nearer 3–5 t/ha. Soybean is closer at 2.3–3.1 t/ha
   dry matter. This sharpens Phase 2: maize first, and calibrate on yield level before
   drawing any conclusion about anomalies.

Also found and fixed during Phase 0: `US.SOL` was hardcoded in **two** places, not one as §4
stated — the startup check in `App.validateEnvironment` *and* the actual profile load in
`Utility.getUnitInfo`. Both are now driven by a `soilFileName` config key.

Phases 1 and 2 overlap: weather generation is long-running and unattended, so calibration
prep can proceed against a subset.

---

## 6. Phase 1 — building the Bolivian input table

Mirrors `prep/constructing_unit-information.md`, substituting Bolivian sources.

### 6.1 Spatial frame

MapSPAM 2020 at 5 arc-minute, filtered to Bolivia and to cells with ≥25 ha of any in-scope
crop (the US threshold). Bolivia is ~1.1 M km² ≈ 13,500 cells total; with the crop-area filter
expect **~2,000–5,000 cell-crop records** — an order of magnitude smaller than the US 47,707,
so runtime is not a constraint.

MapSPAM must be re-downloaded (`/home/jawoo/Claude/mapspam-2020/` is gone). `prep/process_mapspam.py`
works as-is once `ADM0_NAME == 'Bolivia'` replaces the USA filter.

**Cross-check worth doing:** MapSPAM 2020 is a modelled allocation. We hold *observed*
municipal areas for 2023–2025 (`agricola_municipal.xlsx`, 338 municipios). Comparing
MapSPAM's municipal totals against INE's is a cheap, genuinely informative validation of the
spatial frame — and if they diverge badly, the municipal data can be used to rescale MapSPAM
within municipality. This is a step the US workflow never had available.

**Update (2026-10-03): done.** `derived/cells_bolivia_mapspam2020.csv` holds 3,568 cells with
≥25 ha of any in-scope crop or potato; `prep/build_unit_information_bolivia.py` writes 3,469
cells / 9,249 crop records (99 cells are potato-only). MapSPAM national totals in the table:
soya 1.39 Mha, maíz 0.42, sorgo 0.44, trigo 0.18, arroz 0.17 — consistent with INE. The
municipal cross-check above has **not** been done yet.

### 6.2 Weather — the decision that matters most

**Recommendation: regenerate daily weather per grid cell from NASA POWER for 1981–2026, rather
than use the supplied municipal file.** Reasons, in order of weight:

1. The supplied file (`BD_CLIMA_DIARIO`) **has no solar radiation**. DSSAT cannot run without
   SRAD, and there is no honest way to synthesise it at the accuracy the rest of the chain
   assumes.
2. It **starts in 2005**, excluding 1982/83 and 1997/98 — the analogues closest to what is
   forecast.
3. It is aggregated to **municipality**, whereas Tokki's unit is the 5-arcmin cell.

The machinery already exists and is proven at scale:
`~/Claude/tokki-results/hindcast/gen_weather_full.py` (parallel, resumable, writes Tokki-format
`.WTH` straight into the weather dir) plus `srad_fix.py`, which handles the awkward part —
POWER serves SRAD on a coarser 1°×1° grid than T/precip, and `srad_fix.py` already implements
the tiled fetch, caching and remapping. Both need only their cell list and year range swapped.

Because the file is the same POWER product aggregated differently, the supplied municipal file
becomes a **free validation set**: aggregate our per-cell POWER draw to municipality and it
should reproduce `BD_CLIMA_DIARIO` almost exactly for 2005–2026. Any mismatch means our
pipeline is wrong. The ~60 SENAMHI station files (monthly, back to 1984) give a second,
genuinely independent check on POWER's precipitation bias — which in the Andes can be large,
and which matters because rainfall is the variable carrying the ENSO signal.

**Update (2026-10-02): done.** `prep/gen_weather_bolivia.py` wrote 3,568 cell files
(1981-01-01 → 2026-09-25) to `Tapiti/res/weather/1981-2026_bol`, from the MapSPAM cell list in
`derived/cells_bolivia_mapspam2020.csv`; raw POWER responses are cached in `weather/cache/`.
Three caveats are documented in the script header and stamped into each `.WTH` first line:
POWER radiation begins 1984, so **1981–83 SRAD is estimated** from the diurnal temperature
range (Hargreaves, monthly coefficient per cell, in-sample RMSE ≈ 3.9 MJ/m²/d); two single-day
radiation gaps were interpolated; and a MERRA-2 dry-season rainfall artifact on 4–5 June 2020
(500–850 mm/day over the Cochabamba–Potosí highlands, 615 cells) was replaced by interpolation.
The Tokki smoke configuration runs cleanly against the new directory.

**State this plainly in any output:** the weather driving these simulations is reanalysis, not
observations. POWER's precipitation over steep Andean terrain is the largest single source of
uncertainty in the whole chain.

### 6.3 Soil

Same recipe as the US: ISRIC SoilGrids v2 aggregated to 5 arc-minute, HC27 pedotransfer for the
DSSAT hydraulic parameters, written as `BO.SOL` with `BO` + zero-padded CELL5M ids. No Bolivian
equivalent of SSURGO exists, so rooting depth has no national source — the US pipeline queried
USDA SDA and filled nulls at 200 cm. For Bolivia, derive from SoilGrids depth-to-bedrock and
document the assumption.

**Update (2026-10-03): done, and simpler than planned.** `data/BO.SOL` (31 MB, 13,069 profiles)
turned out to be the full national extract of the same ISRIC SoilGrids + HC27 5-arcmin library the
US run uses — `DATA-INVENTORY.md` had it listed as absent. `prep/build_soil_bolivia.py` subsets it
to the modelled cells; 10 cells (Pando/Santa Cruz/Oruro/Potosí edge pixels) had no profile and
take their nearest neighbour, relabelled (`derived/soil_fill_log.csv`). Rooting depth is the full
200 cm profile for every cell; there is no national restrictive-layer source and SoilGrids v2 has
no depth-to-bedrock layer. Altiplano soils are shallower than that in reality, so treat
`soilRootingDepth` as a Phase 2 sensitivity item.

### 6.4 Management

This is where Bolivia is genuinely data-poor and the US approach does not transfer. There is no
Bolivian NASS: no chemical-use survey, no planting-progress series, no objective-yield plant
population survey.

**Update (2026-09-15):** the **Censo Agropecuario 2013** (INE) covers *insumos* (inputs),
*uso de agua para riego* and agricultural practices **at municipal level**, with microdata
catalogued on ANDA. That is a far better source than the literature-table fallback below for
three of the four management fields, and it has been added to the data request
(`DATA-REQUEST.md` §2.5). Treat the table below as the fallback if the microdata proves
inaccessible.

| Field | Approach |
|---|---|
| `plantingDate` | From `derived/crop_calendar_bolivia.csv` as the window **midpoint** (not the window end — see §4), then let Tokki's rainfall-onset scan pick the year-specific date inside the ±30 d window. **This is the mechanism that carries the El Niño signal into sowing date** — a delayed rainy season shifts planting, which the model captures endogenously. Apply the year-wrap patch (§4) first, and keep sorgo/frejol medians at or below DOY 335. |
| `nFertRateAct` | No national survey. Build a documented table by department × crop from FAOSTAT national N use, INIAF/MDRyT extension guides, and the soybean-sector literature for Santa Cruz. Coarse; flag as such. |
| `nFertRateRec` | INIAF extension recommendations where published; otherwise agronomic defaults. |
| `waterSupply` | MapSPAM 2020 irrigated/rainfed ratio, same rule as the US (`I` if TI/(TI+TR) > 0.5). Bolivia is overwhelmingly rainfed outside the valleys, which conveniently means the ENSO rainfall signal passes through with little irrigation buffering. |
| `plantingDensity` | Extension guides and the regional agronomic literature. |

Honest assessment: the management inputs will be the weakest link. That argues for leaning on
Tokki's scenario switches to report yields as a **range across plausible management** rather
than a single number — and for framing results as **relative anomaly (% deviation from the
non-ENSO baseline)** rather than absolute yield. Relative anomalies are far less sensitive to
management-level errors than absolute levels are, and they are what a seasonal-outlook user
needs anyway.

**Update (2026-10-03): first full input table built.** `derived/management_defaults_bolivia.csv`
is a zone × crop × season table (lowland <800 m, valleys 800–2,800 m, altiplano >2,800 m by
POWER elevation) that `prep/build_unit_information_bolivia.py` reads; `derived/SOURCES-management.md`
records the evidence behind each number. Decisions taken in the build, all revisable in that CSV:

- **One record per crop code per cell.** Tokki names output files by unit/cell/crop/cultivar,
  not planting date, so two seasons of the same crop in one cell would overwrite each other.
  Each crop is simulated in its **dominant campaign for the department** (INE 2012–2024 area
  shares, `derived/ine_season_shares_by_depto.csv`): SB and RI verano (77% / 99% nationally),
  MZ primavera–manual (79%), **sorgo invierno in the Santa Cruz lowlands** (87% of Santa Cruz
  sorghum; sown Apr–Jun on residual moisture, so its ENSO exposure runs through autumn rainfall
  rather than the Dec–Mar core), and trigo invierno in Santa Cruz/Tarija/Beni (89% of Santa
  Cruz wheat) but verano in Chuquisaca, Cochabamba, Potosí, La Paz and Oruro (100%). Soya
  invierno (23%) and Santa Cruz maíz invierno (41% of that department's maize) are therefore
  **not** simulated. For invierno crops the rainfall-onset scan is the wrong trigger — it fires
  on the first wet spell inside the window — so their medians are set late (WH 136, SG 151)
  to keep the earliest pick inside INE's sowing window; a per-crop fixed-date option would
  need a small Tokki change.
- **Cultivars are stamped explicitly for every crop.** `WHCER048.CUL`, `SGCER048.CUL` and
  `RICER048.CUL` carry no `*`-flagged entries, so an unstamped WH/SG/RI record runs nothing.
  Maize uses the US GDD class rule (LONG ≥1,600, MEDIUM ≥1,250, else SHORT; base 10 °C, cap 30 °C,
  150 days from sowing, 1991–2020) so the inherited coefficients keep their meaning: all 2,027
  lowland cells are LONG, the Altiplano is uniformly SHORT with frost inside the season in half
  the years. Soybean is MG 8 everywhere by the latitude rule. Wheat `AW0071 Yecora_Rojo`
  (spring type), sorghum `990001 N.AMERICAN`, rice `IB0010 UPLRI5` are generic placeholders.
- `waterSupply` = I where MapSPAM's irrigated share of the crop exceeds 0.5 (164 of 9,249
  records; 1.7% of soya area, 11% of maize).
- **Rice runs in upland mode (decided and implemented 2026-10-03).** Upstream Tokki wrote
  every rice run as transplanted, puddled, bunded paddy flooded 5 days after planting — the
  Asian irrigated system, whereas ~90% of Bolivian rice is direct-seeded *secano* (CIPCA).
  `Tapiti` now has `riceSystem: upland`: rainfed records are dry-seeded and run like any
  rainfed crop; irrigated records (~10% of area, 40 kg N/ha) are dry-seeded into a puddled,
  bunded field and flooded from 25 days after planting (DSSAT refuses a constant flood
  without bund + puddling). Details and the verification in `Tapiti/BOLIVIA.md`.

**Management numbers (2026-10-03, afternoon).** The provisional table was replaced by a sourced
one: a literature pass over ANAPO/FUNDACRUZ, CIAT Santa Cruz, INIAF, MDRyT 2023 (trigo), CIPCA
(arroz), the Censo 2013 summary, FAOSTAT and university trials, written up figure by figure in
`derived/SOURCES-management.md` (extracts in `documents/management-sources-extracts/`). Headline
values: soya 28 pl/m², no N; lowland maize 5.5 pl/m², 25 kg N/ha applied vs 100 recommended;
rice 220 pl/m² direct-seeded, 15 N; sorgo 15 pl/m², 10 N; Santa Cruz wheat 280 pl/m², 23 N;
highland wheat 170 pl/m², 3–5 N. Weakest numbers, in the compiler's own ranking: rice
recommended N (sources span 26–225), sorghum farmer N (inferred, not observed), Altiplano wheat
window and cycle (analogues, not Bolivian observations). Rows with no source of their own are
marked `fill` in the CSV. National context that bounds all of it: FAOSTAT 3.4 kg N/ha of
cropland; Censo 2013 says 30% of farm units use chemical fertiliser, concentrated on potato.

**Which N column the model applies.** Upstream Tokki, with the override switch on, applies
`nFertRateRec` and ignores `nFertRateAct`. The Bolivia clone adds `nitrogenRateSource: actual`
so the hindcast runs farmer practice; the recommended column is kept for a later scenario
(`Tapiti/BOLIVIA.md`). Worth checking what this means for the US production run.

**Sowing window matters more than N.** Moving the lowland maize median from DOY 289 to 320
flipped the smoke-run ranking of 2015 and 2016 in Santa Cruz: with the earlier window the
scan sowed into the 2016 spring drought (~0.6 t/ha); with the later one it sowed on 1 Dec 2016,
after the rains broke, and 2016 came out *above* 2015. INE's verano series says 2016-17 maize
was in fact unremarkable (2.5 t/ha nationally) while the 2016 *invierno* crops collapsed
(maíz 1.5, sorgo 1.8, trigo 0.75 t/ha) — which the invierno sorghum and wheat runs reproduce
directionally. The lesson for Phase 3: the planting-date channel is doing real work, and the
window definition deserves a sensitivity run of its own.

Smoke run on the final table (6 cells, 2015–16, `res/input/unit-information-smoke.jsonl`):
48 DSSAT seasons, no errors; soya 1.0–3.4, maize 2.4–10.0, sorgo invierno 0.8–3.2, trigo
0.6–1.9 t/ha dry matter. Rice under the paddy template came out at 0.16–0.6 t/ha; under upland mode rainfed rice is
2.6–7.7 t/ha (Santa Cruz vs Beni) and the two "irrigated" Santa Cruz cells stay near 0.3 t/ha
even with 40 kg N.

**The rice diagnosis exposed something general.** Those two cells are on a low-carbon soil
(SoilGrids SLOC 0.77%); the crop is nitrogen-starved there whether flooded or not (N stress
0.8–0.9 in the vegetative phase, 0.2 t/ha at 14 kg N, 3.1 t/ha at 100 kg N), while the Beni soil
(SLOC 1.84%) mineralises 160–210 kg N/ha in a season and yields 7 t/ha with no fertiliser at
all. Tokki initialises every season with essentially zero mineral N (`SNH4 = SNO3 = 0.001 ppm`),
which is harmless under US fertiliser rates and decisive under Bolivian ones. In low-input
systems the simulated yield is governed by initial mineral N and SoilGrids organic carbon
rather than by the management table. This moves **soil N initialisation and mineralisation**
to the front of the Phase 2 calibration list for all five crops (§7.3), ahead of cultivar
coefficients.

---

## 7. Phase 2 — calibration against Bolivian statistics

### 7.0 Baseline — first full run, uncalibrated (2026-10-03)

`runs/prod_1983-2024_v4.log`: 388,287 seasons, 42 sowing years, 72 min, no DSSAT errors; 3.8% of
seasons failed (crop death), almost all in Altiplano cells. Summary tables in `derived/baseline_v4/`
(national, departamento × year, matched to INE 2012–2024). Model yields are dry matter; INE is
converted to dry matter at commercial moisture.

| Crop | Model / INE level (national) | r of yearly anomalies, national | Where the anomaly signal is |
|---|---|---|---|
| Soya | **1.01** | 0.37 | Santa Cruz 0.34, Beni 0.42 — the weakest crop, and the one that matters most |
| Sorgo | 1.42 | **0.81** | Santa Cruz 0.81 (invierno) |
| Trigo | 2.24 | **0.73** | Santa Cruz 0.72 (invierno), Tarija 0.68, highlands ~0 |
| Maíz | 2.54 | 0.61 | Beni 0.68, Tarija 0.59, Santa Cruz 0.45; valleys/Altiplano ~0 or negative |
| Arroz | 1.87 | 0.58 | Santa Cruz 0.49, Cochabamba 0.39 |

Twelve years is a short record and these correlations have wide intervals, but the pattern is
clear: **the model already carries the year-to-year weather signal for the Santa Cruz lowland
crops, levels are wrong by a crop-specific factor, and the highlands are not yet represented.**
Three readings, in order of priority for Phase 2:

1. **Levels.** Soya is right. Maize is 2.5× too high everywhere (the US cultivars, as the Phase 0
   smoke test warned), wheat 2–5× too high and worst in the highlands (Chuquisaca 4.9×, La Paz
   5.0×: 170 plants/m², a spring wheat generic and 200 cm of rooting depth on soils that yield
   0.6–0.8 t/ha in reality), rice 1.9× and sorghum 1.4×. These are the cultivar and soil-N
   calibration targets (§7.3). Note the direction: the model is *too optimistic*, which is what
   zero-initial-N-plus-SoilGrids-carbon plus US cultivars would produce.
2. **Soya anomalies are weak** despite the right level. Soya is 1.38 Mha and the whole Santa
   Cruz economy, so this is the first anomaly problem to diagnose: candidates are the single MG 8
   cultivar, the DOY 330 median with a ±30 d onset scan (sowing in reality spans Oct–Jan), and
   waterlogging, which DSSAT does not simulate and which is the lowland El Niño mechanism.
3. **Highlands.** Altiplano rice fails in 100% of seasons (129 cells, 6 kha) and soya in 98%:
   these are Yungas and Alto Beni valley-bottom crops sitting in 5-arcmin cells whose *mean*
   elevation exceeds 2,800 m. The zone rule needs a department-aware override for La Paz and
   Cochabamba (the La Paz maize and rice rows in the INE comparison are meaningless until then).
   Altiplano maize fails in 38% of seasons, which may be partly real (frost) and partly the
   SHORT-season US cultivar.

ENSO years in the national series, for orientation only (Phase 3 does this properly): sowing
year 1997 (El Niño 1997/98) has the lowest maize, rice and third-lowest soya of the 1990s;
2015 (El Niño 2015/16) is the lowest maize year of the whole record and a low soya year;
2023 (El Niño 2023/24) is the lowest soya and second-lowest rice year. 2010–2011 (La Niña,
Santa Cruz drought) is the lowest soya and sorghum pair in the record. The signal is there
before any calibration, and the Altiplano, where the El Niño drought story is usually told, is
the part the model currently says least about.

### 7.1 Target data

**Update (2026-10-03):** the INE departmental series is tidied in
`derived/ine_yields_depto_campaign_2012-2024.csv` (departamento × crop × campaign × sowing year,
area / production / yield, 970 rows) and the campaign shares in
`derived/ine_season_shares_by_depto.csv`. It covers sowing years **2012–2024 only**; the
1984–2011 departmental series referred to below is not in the files we hold and must be requested.
`analysis/summarise_run.py` produces the matching model-side table (area-weighted yield by
crop × departamento × sowing year) from any merged Tokki output.

- **Backbone:** INE *Año Agrícola por Departamento*, **1983-84 → 2024-25** (42 seasons),
  yield in kg/ha, one sheet per department. Links verified in `DATA-INVENTORY.md` §4.
- **Campaign split:** the 2012+ verano/invierno tables (local file §1.1), needed because the
  42-season series combines both campaigns and our simulations are campaign-specific.
- **Spatial detail:** `agricola_municipal.xlsx` 2023–2025 for the area weights.

### 7.2 Unit harmonisation — simpler than the US

`step5_compare.py` in the US chain spends most of its logic converting NASS bu/acre at market
moisture to kg/ha dry matter. Bolivia reports **kg/ha directly**, so only the moisture
correction remains: DSSAT `HWAH` is dry matter, INE yields are at commercial moisture
(soya ~13%, maíz ~14%, arroz paddy ~14%, trigo ~13%, sorgo ~14%). One documented factor per
crop. Watch the `t/ha` vs `kg/ha` difference between the municipal and departmental files.

### 7.3 What "calibration" means here

**Added 2026-10-03:** first item is soil nitrogen supply, not cultivars. Tokki starts each
season at ~0 mineral N and relies on SOM mineralisation from SoilGrids carbon; under Bolivian
N rates (0–25 kg/ha) that single assumption swings simulated yield by an order of magnitude
between soils (Santa Cruz vs Beni rice test in §6.4). Options to evaluate against INE: a
realistic initial NO₃/NH₄ profile (DSSAT defaults are ~1–5 ppm), a residue/fallow carry-over,
and a check of SoilGrids SLOC against any Bolivian soil-survey carbon values. Do this before
touching cultivar coefficients, or the cultivar "calibration" will absorb a soil error.

**Result (2026-10-04): the soil-N problem is mostly a boundary-condition problem.** Four config
switches were added to Tapiti (`somModel`, `simulationStartDaysBeforePlanting`,
`initialSoilWaterFraction`, `initialSoilN`; all default to upstream behaviour) and a 60-cell
stratified sample (`res/input/unit-information-sample60.jsonl`, sowing years 2012–2017) was run
under 14 combinations; full table in `derived/phase2_soilN_sensitivity_sample60.csv`.

| Setup (CENTURY SOM unless stated) | Maíz | Arroz | Soya | Sorgo | Trigo | N mineralised, maize (kg/ha/season) |
|---|---|---|---|---|---|---|
| Upstream: start 1 Jan, 0 initial N, fixed water | 2.54 | 2.48 | 1.20 | 1.67 | 2.18 | 165 |
| 1 Jan, initial N 1/2 ppm | 2.88 | 2.89 | 1.22 | 2.20 | 3.02 | 160 |
| CERES SOM, 1 Jan | 2.25 | 2.00 | 1.18 | 1.28 | 1.49 | 148 |
| **Start 60 d before sowing**, 0 N, water 0.5 PAW | **1.48** | **1.28** | **1.05** | **1.52** | **1.51** | 83 |
| Start 60 d, N 0.3/0.7 ppm (≈27 kg N/ha in 2 m) | 1.74 | 1.58 | 1.06 | 1.80 | 1.82 | 81 |
| Start 60 d, N 1/2 ppm (≈80 kg N/ha in 2 m) | 2.31 | 2.10 | 1.07 | 2.14 | 2.43 | 78 |
| CERES SOM, start 60 d, N 1/2, water 0.5 | 1.94 | 1.64 | 1.06 | 2.03 | 1.99 | — |

Ratios are model ÷ INE 2012–2024 national dry-matter yield; the sample is 60 cells × 6 years, so
read the pattern, not the second decimal.

What this says:
- **The 1 January start is the main culprit.** Upstream starts every season on 1 Jan of the
  sowing year, so a verano crop follows ~10 months of bare fallow in which SoilGrids organic
  carbon mineralises 150–250 kg N/ha with no plant to take it up and, in a 2 m profile, little
  of it leaches. That is a US convention (spring sowing, 4 months of frozen fallow) that does not
  transfer. Starting 60 days before sowing halves mineralised N and removes most of the level
  bias; it also matches the Santa Cruz reality of a winter crop occupying the field until a few
  weeks before verano sowing.
- **Initial mineral N is a strong lever once the fallow is short**, and the unit matters: ppm
  applies to the whole 2 m profile, so 1/2 ppm is ~80 kg N/ha of free nitrate, far above what a
  low-input field carries at sowing. 0 to ~0.3/0.7 ppm is the defensible range.
- **CENTURY vs CERES is secondary** (10–25% on N-responsive crops) once the start date is fixed.
- **Soya does not care** (1.03–1.07 throughout) because it fixes its own N, which is why its
  level was right from the start and why its *anomaly* problem (§7.0) must be something else.
- **The residual is now crop-specific and plausible as cultivar error**: maize ~1.5× with
  US-calibrated LONG/MEDIUM/SHORT generics, wheat ~1.5× with a spring-wheat generic at 170–280
  plants/m², rice and sorghum ~1.3–1.5× with stock DSSAT generics. That is what Phase 2
  cultivar work should absorb; the soil-N term should not be tuned further to hide it.

**Phase 2 default adopted 2026-10-04:** CENTURY, start 60 days before sowing, initial water 0.5 of
plant-available water per layer, initial N 0.3/0.7 ppm (`Tapiti/config.yml`; run v5 =
`runs/prod_1983-2024_v5_preseason60.log`).

Follow the US pattern: keep the generic maturity cultivars' phenology, and adjust the yield
coefficients (maize `G2/G3/PHINT`; soybean the `LFMAX`-onward tail) so simulated departmental
means match observed. `draft_calibration.py` does exactly this transplant-from-a-donor-cultivar
operation and is directly adaptable.

Discipline that matters more than the mechanics:

- **Split the record.** Calibrate on one subset of seasons, validate on held-out seasons, and
  in particular **hold out the strong El Niño years**. A model tuned on 42 seasons including
  2015/16 and then shown to "reproduce" 2015/16 has demonstrated nothing about its skill in
  2026/27.
- **Report metrics per department × crop**, not pooled. The US chain's
  `bias_ME / MAE / RMSE / RRMSE / r / R² / slope` set is fine.
- **Detrend before attributing anomalies to climate.** Bolivian soybean and sorghum yields
  carry a strong technology trend over 42 years (visible already in the maize series:
  ~1,490 kg/ha in 1983-84 rising through the 1990s). Any ENSO signal must be measured against
  the trend, not against the 42-year mean.
- **Area change is not yield change.** ENSO affects planted area too (farmers respond to a
  late rainy season by switching crop or not planting). DSSAT simulates yield only. Production
  impact = yield effect × area effect, and we can only model the first. Say so.

---

### 7.3b Cultivar calibration on yield level (2026-10-04)

Method: with the Phase 2 pre-season defaults fixed, run the 60-cell sample (2012–2017) under
candidate cultivar coefficients and compare area-weighted yield by zone with the INE 2012–2024
departmental mean (dry matter, weighted by the sample's MapSPAM area per department). Grids and
results: `derived/phase2_cultivar_calibration_sample60.csv`. New cultivars live in
`Tapiti/res/.csm/*.CUL` with a `BOL` prefix and a comment line stating the source coefficients.

| Crop | What was wrong | What was done | Sample result (model ÷ INE) |
|---|---|---|---|
| Maíz | US-calibrated generics have G2/G3 (kernels, fill rate) 25–65% above stock DSSAT | **BOL LOWLAND** = stock LONG with G2 +10% (682, 6.0); **BOL VALLEYS** = MEDIUM phenology with low potential (G2 420, G3 5.0); **BOL ALTIPLANO** = SHORT with G3 10 | lowland 0.97, valleys 1.00, altiplano 0.89 with 42% frost/cold failures that no cultivar removes |
| Arroz | stock UPLRI5 1.5× | **BOL SECANO** = UPLRI5 with G1 (spikelet coeff.) 50 → 40 | lowland 1.04 |
| Sorgo | stock N.AMERICAN 1.8× | **BOL GRANIFERO** = G2 (partitioning to panicle) 6.0 → 2.6 | lowland 0.96, valleys 0.98 |
| Trigo | Yecora_Rojo 1.5–1.8× in every zone | **nothing** — G1, G2, G3 and ecotype RUE (×0.65, ×0.5) move yield <15%, and lower RUE *raises* highland yield; the simulated crop is not limited by any genetic coefficient tested | 1.55–1.78 unchanged |
| Soya | — | unchanged (MG 8); level already 1.0–1.07 | — |

Two cautions. First, these are **level** calibrations on a 60-cell sample; the full run (v6)
is the real check, and the year-to-year anomaly correlations (§7.0) must not deteriorate — if a
coefficient change buys level at the cost of anomaly skill, it is the wrong change. Second,
the valley maize cultivar encodes more than genetics: 4.5 plants/m², 10 kg N and a 1.8 t/ha
reality on slopes with hail and frost are being summarised by a low-potential cultivar because
the model has no other place to put them. State that when the results are used.

**Round 2 (2026-10-04, after full run v7).** v7 (`runs/20261004-*_v7_bol-cultivars/`) put maize at 1.10
nationally but 0.82 in Santa Cruz and 2.0 in Beni/Pando, sorghum at 0.82; anomaly r held for rice
(0.66), sorghum (0.75) and wheat (0.71), slipped for maize (0.61 → 0.52) and soya (0.37 → 0.28).
A factorial on 300 Santa Cruz maize cells over 2012–2024 (1 Jan vs −60 d start × US vs BOL cultivar,
plus −120 d and drier initial water) gave anomaly r between 0.30 and 0.41 for every combination — the
differences are inside the noise of 12 years, so neither the pre-season change nor the cultivars can
be blamed for the maize slip; what the factorial did show is that **one lowland maize cultivar cannot
serve both mechanised Santa Cruz and smallholder Beni/Pando**. Changes committed for run v8:
`BOL LOWLAND` → G2 820, G3 7.0 (Santa Cruz 0.98); a `lowland_traditional` management class (4.5
plants/m², 10 kg N, `BOL VALLEYS` cultivar) for lowland maize outside Santa Cruz/Tarija (Beni/Pando
1.12, but r 0.47 → 0.14 on 12 years — 11 kha, accepted); `BOL GRANIFERO` G2 2.6 → 3.4 (Santa Cruz
sorghum 0.99, r 0.75). Results: `derived/phase2_cultivar_calibration_round2.csv`.

**Phase 2 reference run = v8 (`runs/20261004-2232_v8_calib-round2/`, 2026-10-04).** National level ratios and anomaly
correlations against INE 2012–2024: soya 0.93 / 0.28, maíz 1.19 / 0.42, arroz 0.95 /
0.66, sorgo 0.96 / 0.76, trigo 1.67 / 0.71. Maíz is ~1.0–1.1 in Santa Cruz, Tarija, Beni and Pando; the
national excess sits in Chuquisaca (1.7), Potosí (1.7) and Cochabamba (1.4), where INE yields of 1.0–1.3 t/ha
are below what the model reaches with the valley cultivar. Maíz anomaly skill fell from 0.61 (v4) to 0.42 across
the two calibration rounds; twelve years cannot separate that from noise (the Santa Cruz factorial gave 0.30–0.41
for every setup), so Phase 2 is closed here and the anomaly question moves to Phase 3, where the 42-year record
is tested against ENSO rather than against 12 years of INE. Simulated soya also carries a −1.25%/yr trend
(1983–2024) tied to rising Tmax in MERRA-2 that INE 2012–24 does not show (−0.5%/yr); detrend before composites.

**Wheat** stays biased high by ~1.6× and is handled as a per-department bias factor at
analysis time (`analysis/compare_ine.py` reports the ratio). The missing processes are known:
*Pyricularia* (blast) in Santa Cruz winter wheat, hail and frost in the highlands, and poor
stands — none of them cultivar coefficients. The altiplano maize failure rate (42%) is the
same kind of gap in the other direction and is probably partly real.

### 7.3c Soya anomalies — a climate-only diagnostic (2026-10-04)

Soya's level is right but its yearly anomalies track INE weakly (r ≈ 0.35, §7.0). Before
blaming cultivar or sowing window, the weather itself was checked against INE Santa Cruz verano
soya yield, 2012–2023 (12 seasons; area-weighted over the 400 largest soya cells;
`derived/soya_scz_climate_indicators_1983-2024.csv`):

| Indicator over the Nov–Mar season | r with INE Santa Cruz soya yield |
|---|---|
| Total rainfall | −0.02 |
| Days with > 50 mm | **−0.51** |
| Jan–Feb rainfall | −0.30 |
| Days with Tmax > 35 °C | −0.38 |
| Mean Tmax | −0.33 |
| Nov–Dec rainfall | +0.14 |
| 10-day windows with < 5 mm (dry spells) | **−0.47** |

Twelve points, so none of this is significant on its own, but the pattern is coherent and it
is only half of what a water-stress model produces: Santa Cruz soya loses yield to dry spells
(which the model should capture) **and** to heavy-rain events and heat (which it will not), while
seasonal rainfall total carries no signal at all. That is the lowland El Niño signature
(§2) and the mechanism — waterlogging, saturated soils, harvest losses — is the one §10 said
DSSAT handles poorly. CROPGRO does have an excess-water response (soil saturation reduces
photosynthesis and N fixation via the species `PORMIN`/`RTEXF` parameters), and whether it is
active and strong enough in these HC27 profiles (2 m deep, SLDR 0.5, so they rarely saturate)
was the first thing tested on the v6 output (below): correlate simulated soya
anomalies with the same indicators and see which sign the model gets. If the model cannot be
made to lose yield in wet years, the honest route for Phase 3 is a hybrid: model anomalies for
drought-driven losses, a statistical wet-day term for the rest, stated as such.

**v6 result (2026-10-04, `analysis/soya_anomaly_check.py`):** the model's Santa Cruz soya yield
correlates **+0.73** with Nov–Mar rainfall total over 2012–2023 (+0.75 over 1983–2023) where INE
shows −0.02; it gets heat right (−0.54 vs INE −0.38) and dry spells right in sign (−0.29 vs
−0.47), but responds *positively* to wet-day counts where INE responds negatively. The model is
a rainfall-loving model and Santa Cruz soya is not a rainfall-loving crop. Model-vs-INE anomaly
correlation for soya fell from 0.37 (v4) to 0.26 (v6) with the shorter pre-season, because the
60-day start makes the crop more dependent on in-season rain. CROPGRO's excess-water stress is
evidently not biting in these profiles. Options, in order of honesty: (i) a soil-side fix —
HC27 SLDR 0.5 and 2 m depth make the lowland profiles drain too freely; a shallower effective
rooting depth or lower SLDR for the Santa Cruz plains would let saturation occur; (ii) a
statistical wet-day/heat term on top of model anomalies for Phase 3; (iii) both, with (i)
tested on the 60-cell sample first.

**Soil-side test (2026-10-04, 28 Santa Cruz soya cells × 42 years in the scratch copy):** neither a
100 cm rooting depth nor SLDR 0.50 → 0.20 changes the sign — model yield vs Nov–Mar rainfall stays
at +0.67/+0.72, vs wet days > 30 mm at +0.47/+0.54, and the model-INE anomaly correlation does not
improve (0.24 → 0.12 / 0.22). CROPGRO's excess-water stress does not bite in these HC27 profiles
even when drainage is slowed; the mechanism would need standing water or a shallow water table
(`ICWD`), which 5-arcmin soil data cannot place. **Conclusion for Phase 3: route (ii).** Use the
model for the drought and heat channels, where its signs agree with INE (dry spells −0.44 vs
−0.47; hot days −0.73 vs −0.38), and add a statistical excess-rain term fitted on the INE
overlap, reported separately and labelled as such. Soya's weak anomaly skill is a structural
limit of the water-balance model in a flood-prone plain, not a calibration failure.

## 8. Phase 3 — the historical ENSO assessment (the first deliverable)

This is the part answering "what kinds of impacts did the country face in the past", and it is
deliverable without any forward-looking modelling.

**Status (2026-10-05): done as a first full pass** — `documents/Phase3-ENSO-hindcast_2026-10-05.md`, built by
`analysis/phase3_weather_composites.py`, `phase3_yield_composites.py`, `phase3_figures.py`, `phase3_report.py` from
reference run v8; tables in `derived/phase3/`. Headlines: (1) the ENSO signal in Bolivia's weather and simulated
yields is carried by the **strong eastern-Pacific events** (1997/98, 2015/16, 2023/24), not by El Niño as a class —
the all-El-Niño composite is within ±2% of neutral for every verano crop; (2) in those three campaigns simulated
maíz −18%, arroz −18%, soya −20% nationally (intervals excluding zero), concentrated in the Santa Cruz plain, while
the invierno crops sown in the developing-El Niño autumn (April–June of the onset year) gain (sorgo +26%, trigo +13%)
and the developing-La Niña winter costs sorgo −15%; (3) the observed record agrees where
it overlaps — 2023/24 matches on every crop, 2015/16 on all but soya; (4) SENAMHI stations (29, 1970–2009) show the
classic El Niño drying of the Altiplano (−11%, CI excluding zero) that POWER only half reproduces (−5%), so the
Altiplano is unresolved by the model (its maize even gains from warmth). Central-Pacific events (1991/92, 2009/10) are
not drought years in either data or model, which is why the 2026/27 event (Niño-1+2 ≈ +3.4) must be read against the
EP analogues only.

### 8.1 Two independent lines of evidence, deliberately kept separate

**(a) Statistical — observed yields vs ENSO phase.** No crop model involved. Classify each
*año agrícola* 1983-84 → 2024-25 by DJF ONI, detrend departmental yields, and test whether
yield anomalies differ by phase. 42 seasons gives roughly 11–13 El Niño, 12–14 La Niña and
~16 neutral seasons — enough for composite means with confidence intervals, not enough for
anything elaborate. This is descriptive and fast.

**(b) Mechanistic — Tokki simulations under observed ENSO-phase weather.** Run every season
1983-2025 with observed weather, then composite simulated yields by phase. Because everything
except weather is held constant, the difference between phases is **attributable to climate
alone** — which the statistical line cannot claim, since observed yields also move with prices,
area, technology and policy.

Where (a) and (b) agree, the finding is robust. Where they diverge, the gap is itself
informative: it bounds how much of the historical impact was climate versus everything else.
Presenting them as one blended number would destroy that information.

### 8.2 ENSO classification

Use CPC's ONI (ERSSTv6) DJF value per season, with the conventional ±0.5 °C threshold and
weak/moderate/strong/very-strong bands. Verified DJF values for the analogue years:
1982/83 **+2.1**, 1997/98 **+2.2**, 2015/16 **+2.5**, 2023/24 **+1.8**, 1991/92 +1.5,
2009/10 +1.5, 1986/87 +1.2, 2018/19 +1.0.

Two refinements worth including given the current event's structure:
- Also stratify by **Niño-1+2 / eastern-Pacific** amplitude, not just Niño-3.4. Bolivia's
  Andean teleconnection is stronger for EP events, and the 2026 event is strongly EP-weighted
  (+3.4 °C in Niño-1+2). A composite dominated by central-Pacific events would understate it.
- Check whether the climate anomalies actually appear in the Bolivian data before compositing
  yields. Run the phase composite on the weather itself — POWER precipitation and Tmax by
  department, and independently the SENAMHI station monthlies. If the expected dry-Altiplano /
  variable-lowland pattern is not present in the input weather, no crop-model result downstream
  can be trusted.

### 8.3 Outputs

- Yield anomaly by department × crop × ENSO phase, observed and simulated, with uncertainty.
- Maps of simulated yield anomaly under strong-El-Niño composite weather.
- Per-event narratives for 1982/83, 1997/98, 2015/16, 2023/24 — the analogue set.
- An explicit statement of which anomalies are statistically distinguishable from zero and
  which are not.

---

## 9. Phase 4 — the forward-looking 2026-27 estimate

**Status (2026-10-05): first estimate delivered** — `documents/Phase4-2026-27-outlook_2026-10-05.md`, from
`prep/gen_weather_analogue.py` (observed weather to 25 Sep 2026 + analogue weather after), `analysis/phase4_run_analogues.sh`
(42 members, ~1 min each), `phase4_c3s_fetch.py` + `phase4_forecast_weights.py` (SEAS5 system 51, init 2026-09,
51 members → analogue weights; 40% on 1997/98, 2015/16, 2023/24), `phase4_summarise.py`, `phase4_report.py`.
Verano 2026/27 national outlook, % of the all-analogue mean (SEAS5-weighted / strong-EP analogues): soya
-13 / -31, maíz -8 / -23, arroz -9 / -21;
P(≥10% loss) SEAS5-weighted: soya 0.42, maíz 0.54, arroz 0.44. Invierno 2026 (sown Apr–Jun 2026, inside the
observed splice) is a **nowcast**: Santa Cruz sorgo +62% vs the hindcast trend (rank 39 of 43), trigo +29% — the
developing-El Niño winter gain of Phase 3, checkable against INE when the invierno 2026 statistics appear. SEAS5
itself: Altiplano Nov–Mar rainfall −33% (all members dry), valleys −5%, lowlands ~0 with wide spread, +1.6 to +2.5 °C.
Monthly update path: rerun the three forecast scripts on each SEAS5 release and move the splice date forward.

**Update 2026-10-08 (October SEAS5, splice moved to 2 Oct 2026)** — `documents/Phase4-2026-27-outlook_2026-10-08.md`.
POWER weather refreshed to 1 Oct 2026 (`prep/gen_weather_bolivia.py`, 12 tile-requests, 143 s); `gen_weather_analogue.py` now
derives the splice date from the last observed day and writes `derived/phase4/splice_date.txt`, which `phase4_summarise.py` and
`phase4_report.py` read (no more hard-coded dates). 42 members rerun (382 364 seasons, 0 DSSAT errors, ~40 min); the September
runs and tables are archived in `runs/phase4_2026-09/` and `derived/phase4_2026-09/`. SEAS5 init 2026-10 is slightly drier on the
Altiplano (−37%) and slightly less warm in the lowlands (+1.3 °C) than September; weights on the strong-EP campaigns fell from 40% to 34%
(1997/98 0.20, 2015/16 0.09). SEAS5-weighted national outlook moved a little toward neutral: soya −9 (was −13), maíz −7 (−8), arroz −7 (−9);
P(≥10% loss) 0.38 / 0.47 / 0.38. Strong-EP composite unchanged within a point (−30 / −22 / −20). The invierno 2026 nowcast is
unchanged (sorgo +49% vs last ten campaigns, trigo +14%) and now has a first external check: INE has not published, but ANAPO's
close-of-campaign expectations (sorgo 2.8–3.5 t/ha on 70% of 612 kha; trigo 1.6–1.7 t/ha on 57 kha, 'climate favoured the crop') are
+29–62% and +10–17% on the INE 2015–2024 Santa Cruz means — same sign and size. Revisit when INE publishes.
Note for the pipeline: `phase4_summarise.py` needs the weights CSV as its argument or the SEAS5-weighted rows are silently
omitted and `phase4_report.py` fails on `KeyError: 'SB'`.


Two approaches, both worth running because they fail differently.

**Analogue resampling (robust, cheap, available first).** Drive the 2026-27 season with observed
weather from the strong-EP-El-Niño analogue years, sowing on the actual 2026-27 calendar. Output
is a distribution across analogues rather than a single forecast. No new data needed once
phases 1–3 are done, and the method's assumptions are easy to state.

**Seasonal-forecast-driven (sharper, more machinery).** `~/Claude/weathernext-data/wn2dssat/`
already has `c3s.py` alongside `nasapower.py`, `srad.py` and `splice.py` — i.e. the C3S
seasonal-forecast path is partly built. SENAMHI independently downloads the same ECMWF/NCEP/JMA/ECCC
seasonal forecasts from CDS, which makes this the natural point of institutional connection:
we would be consuming data they already hold. Each ensemble member becomes one weather
realisation; Tokki yields a yield distribution. Requires disaggregating monthly/seasonal
forecast anomalies to daily — a well-known weak point that must be documented, not hidden.

As the season unfolds, `splice.py`'s pattern (observed-to-date + forecast-forward) supports
updating the estimate monthly, which is what makes this operationally useful rather than a
one-off study.

---

## 10. What this cannot do

Stating these up front, because they will otherwise be read into the results:

- **No area or planting-decision response.** DSSAT simulates yield on planted area. Farmers
  respond to a failed rainy season by planting less or switching crop; that channel is often
  larger than the yield channel and is entirely outside this framework.
- **No floods, hail, frost damage or pest/disease.** DSSAT's water balance handles drought
  well and waterlogging poorly. El Niño in the Bolivian lowlands can bring damaging excess
  rainfall, and that impact will be systematically **under**estimated.
- **Reanalysis weather in complex terrain.** POWER precipitation in the Andes carries large
  uncertainty; the SENAMHI monthlies bound it but cannot fix it.
- **Weak management inputs.** No Bolivian fertiliser or density survey exists. Relative
  anomalies are defensible; absolute yield levels are much less so.
- **Small samples.** 42 seasons, ~12 of them El Niño, and only 3–4 strong. Composite means
  will have wide intervals, and that width is a result, not a nuisance.
- **No potato or quinoa in phase 1**, which means the Altiplano — the region where the El Niño
  drought signal is expected to be strongest — is represented mainly by valley maize and
  wheat. This is the most consequential scope gap.

---

## 11. Decisions needed before Phase 1 starts

1. **Crop scope.** Five crops (soya, maíz, arroz, sorgo, trigo) for phase 1, or invest ~1–2
   weeks up front wiring SUBSTOR-Potato so the Altiplano is covered from the start?
2. **Deliverable and deadline.** Is there a fixed date — a CAF submission, a SENAMHI briefing?
   That determines whether phase 3 or phase 4 is the target, and phase 3 alone is a coherent
   product.
3. **Weather span.** 1981–2026 (full POWER record, all analogues, more generation time) or
   1991–2026 (drops 1982/83, faster)? Recommend the full record — 1982/83 is one of only three
   strong-EP analogues.
4. **Institutional channel.** Is there a counterpart at SENAMHI or INIAF? Their C3S access and
   station network are the two things that would most improve this, and the SENAMHI note says
   plainly that no crop-impact tool exists on their side.
5. **Housekeeping:** the `newcpuspeedcheck/` directory of Windows executables inside the
   climate data (`DATA-INVENTORY.md` §2.4) should be deleted and flagged to whoever assembled
   the transfer.

---

## 12. Phase 5 — forecast-spliced weather (decisions 2026-10-14)

**Decisions (user, 2026-10-14):** keep NASA POWER for history; drive DSSAT with spliced **POWER (observed) → Open-Meteo
`ecmwf_seasonal_seamless` members (ECMWF EC46 for days 1–46, then SEAS5 to ~7 months)**; NeuralGCM dropped from the
pipeline (v1 has no surface variables); Open-Meteo Professional tier (5M calls/month) to be subscribed. Background:
`documents/OpenMeteo-assessment_2026-10-14.md`. Same three-tier structure as `~/Claude/weathernext-data/wn2dssat/pipeline.py`,
extended from a few sites to the 3,568 cells with a 51-member ensemble.

### 12.1 What the API serves (checked 2026-10-14)
- `ecmwf_seasonal_seamless`: 51 members (control + 50), daily `temperature_2m_max/min`, `precipitation_sum`,
  `shortwave_radiation_sum`; EC46 (today's 00Z run, 51 of its 100 members, 45–46 days) through ~day 42, then SEAS5 (monthly
  run, 5th) to 7 months (`forecast_days` ≤ ~210). Member *k* of EC46 is paired with member *k* of SEAS5. EC46 refreshes
  daily (20:30Z), so the seam moves every day.
- **No daily anomalies.** Monthly anomalies exist (`temperature_2m_anomaly`, `precipitation_anomaly`,
  `shortwave_radiation_anomaly`, vs the model hindcast climate), so the model monthly climatology at a point is
  (monthly ensemble-mean forecast − monthly anomaly): enough for a monthly delta/ratio correction.
- Archive begins at the 2026-09 initialisation: no hindcasts, no in-house skill assessment (C3S hindcasts remain the route).
- Grid O320 (~36 km); the 3,568 cells map onto 483 forecast points; 51 members × 4 variables × 183 days ≈ 267 "calls" per
  point, ≈ 148k per monthly pull. Professional tier 5M/month; paid requests go to `customer-*.open-meteo.com` with `apikey=`.

### 12.2 Design
1. **Cell → forecast point.** Query each cell centre once; the response carries the snapped grid lat/lon; group cells by it.
   Fetch per point (daily members + monthly ensemble means and anomalies), cache per `(run date, point)` under `derived/phase5/om/`.
2. **Bias adjustment to the POWER cell climatology** (so no climatological jump at the seams): per cell and calendar month,
   POWER 1991–2020 means of Tmax, Tmin, rain, SRAD from `weather/cache`; model monthly climatology per point from 12.1.
   Tmax/Tmin: additive shifts, each against its own model climatology = ensemble-mean monthly Tmax|Tmin of the daily
   members minus the served mean-temperature anomaly (assumed equal for max and min). A single mean-temperature shift
   (v1, 2026-10-14) left +0.6 °C (the API's true daily mean is ~0.6 °C below (Tmax+Tmin)/2) plus +0.7 °C on Tmin and
   −0.7 °C on Tmax from the model's narrower diurnal range (7.1–7.6 °C in DJF vs 8.7 °C in POWER at lowland cells), which
   DSSAT turned into a ~20 % soya/maize/rice loss on its own. Rain and SRAD: multiplicative,
   member daily × (POWER clim / model clim), monthly factors interpolated to the day, rain factor capped (0.2–5).
   The member's own wet/dry-day sequence is kept.
3. **Beyond the seasonal horizon** (≈ May 2027 for an Oct run): fill to 31 Dec 2027 with the weather of the top-weighted
   Phase 4 analogue year (realistic daily structure; climatology has none). Recorded in the .WTH header.
4. **Runs.** `Tapiti/res/weather/2026_fc_<member>/` × 51, run as the analogue ensemble is (`phase4_run_analogues.sh` pattern,
   ~50 min for 42 analogues). Summarise per crop/zone as `phase4_summarise.py`; **keep the analogue-weighted ensemble as the
   comparison**. The member spread is forecast uncertainty, not climatological spread.
5. **Monthly loop:** pull after the SEAS5 release (5th on Open-Meteo), rebuild member directories, run. EC46 updates daily,
   so a mid-month refresh only changes days 1–46.

### 12.3 Status
Built 2026-10-14: `analysis/phase5_om_fetch.py` (local O320 snapping, cached per run date), `prep/gen_weather_forecast.py`, `analysis/phase5_run_members.sh`, `analysis/phase5_summarise.py`. Smoke test passed (Tapiti 0 errors on member 01). Full pull done 2026-10-14 on the Professional endpoint (key in `~/.config/open-meteo/apikey`): 483 points in ~2 min; POWER ends
2026-10-01, forecast 2026-10-02 → 2027-05-03 (October SEAS5 init), analogue tail 1997/98 from 2027-05-04. Two Lake Titicaca
points are relocated by the API to the nearest land point (recorded as `api_point` in the cache). About 1 response in 4 came
back with the last month of rain/SRAD missing while temperature was complete (server-side inconsistency, not timing); the fetch
script now detects this and refetches, which clears it in a few tries.
Bias factors over all 3,568 cells (member 00): T shift mean +2.1 °C in the lowland (model cool vs POWER, consistent with the
ERA5-vs-station result), −9.7 to +18.3 °C in the valleys/Altiplano; the shift correlates 0.94 with (forecast-point elevation −
POWER elevation) at 5.9 °C/km, i.e. it is a lapse-rate correction for the 36 km point sitting on a different height than the
POWER cell. 223 cells have |shift| > 6 °C and 23 > 10 °C; those cells inherit the wet/dry sequence of a much higher point
(rain factor at the 0.2 floor at 8 cells); the diurnal range is corrected by the separate Tmax/Tmin shifts (v2).
Ensemble-mean NDJFM rain after adjustment is 613 mm vs the 636 mm POWER climatology (cell mean), consistent with the
slightly negative served precipitation anomaly. v1 (single mean-temperature shift) outputs are kept in
`runs/phase5/2026-10-14/v1_meanshift/` and `derived/phase5/2026-10-14/v1_meanshift/` as the record of the artefact.
**v2 results (2026-10-14, 51 members, 0 DSSAT errors, ~50 s per member):** national member mean vs all-analogue mean: soya
-17.1 %, maize -16.0 %, rice -13.1 %, sorghum -0.9 %, wheat -5.3 % (SEAS5-weighted analogues −9.5/−7.0/−6.8/−0.3/−2.2; strong-EP
−30.5/−22.5/−20.2/−0.8/−2.6). Season Tmax/Tmin of the members now sit inside the 1997/2015/2023 analogue range; daily rain
structure matches POWER in the lowland. Written up as §8 of `documents/Phase4-2026-27-outlook_2026-10-08.md`. Possible refinement: choose, among the nearest four O320 points, the one
closest in elevation to the POWER cell. Rain factor 0.57 median in valleys/Altiplano, 0.84 lowland; SRAD 0.95–1.23.

### 12.4 Caveats to carry into any output
Raw members are area forecasts at 36 km, bias-adjusted by a monthly delta/ratio to a gauge-corrected reanalysis climatology;
daily rainfall statistics (dry-day frequency, intensity) are the model's, and DSSAT is sensitive to them. No skill
verification is possible from the Open-Meteo archive.
