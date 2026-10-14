# Does Open-Meteo offer anything that warrants changing our weather sources?

Assessment, 2026-10-13/14. Question from the user after seeing a study that used the Open-Meteo API. Current sources: NASA POWER
(historical daily weather, 1981–present), ECMWF SEAS5 via the Copernicus CDS (monthly anomalies, Phase 4 analogue weights),
NeuralGCM and WeatherNext (experimental, outside this workspace). All Open-Meteo facts below were checked with live API calls;
the comparison scripts and raw pulls are in `debug/openmeteo/`.

## Verdict in one paragraph

Open-Meteo does not offer a better *historical* weather record for Bolivia than POWER: its precipitation (ERA5) is clearly
worse against SENAMHI stations, its radiation is equivalent, and its temperature differs mainly through elevation
representation, which we can fix on the POWER cache without changing source. What it does offer, new since ECMWF's open-data
switch on 1 Oct 2025, is **free daily ECMWF SEAS5 ensemble members (51, 36 km, 7 months) and the 46-day EC46 ensemble, with no
CDS queue**. That is the one item that could change the Phase 4 design: from "SEAS5 monthly anomalies weight historical
analogues" to "SEAS5 daily members drive DSSAT directly", or a hybrid where EC46 fills the first six weeks after the splice
date. The trade-offs are listed in §4; the choice is a design decision for the user, not something the data settle.

## 1. What Open-Meteo serves (checked 2026-10-13)

| Product | Content | Relevance here |
|---|---|---|
| Historical Weather API | ERA5 0.25° (1940–), ERA5-Land 0.1° (1950–), `era5_seamless` = ERA5-Land temperature/humidity + ERA5 precipitation/radiation/wind; 5-day lag; temperature statistically downscaled to a 90 m DEM at the requested point | Candidate replacement for POWER; tested in §2 |
| Seasonal Forecast API | `ecmwf_seas5` 51 members, 7 months, O320 (~36 km), 6-hourly → daily/weekly/monthly incl. anomalies vs model climate; `ecmwf_ec46` 51 members, 46 days, updated daily; archived runs only back to the 2026-09 initialisation; not bias-corrected | New option for Phase 4 (§4) |
| Ensemble API | ECMWF IFS/AIFS ENS (51, 15 d), GFS ensemble (31, 35 d), **Google WeatherNext 2** (`google_weathernext_2`, 64 members, 15 d) | WeatherNext without the Google Cloud route |
| Satellite Radiation API | SARAH-3 0.05°, 1983–, 1-day lag | Covers Bolivia **only east of ~65°W** (no data at 65.5°W and beyond: Altiplano, La Paz, Oruro, western Cochabamba/Potosí excluded) |
| Elevation API | 90 m Copernicus DEM | Point values only; a cell-mean DEM for the elevation fix needs a raster anyway |
| Terms | Free tier non-commercial; 600/min, 5,000/h, 10,000/day "calls" where a call is ~1 location × 14 days × 10 variables | A 41-year daily pull of 4 variables costs ~430 calls per point: 16 points exhausted the daily quota. A 3,568-cell refetch is not free-tier feasible; the same data are on the CDS (ERA5-Land, AgERA5) and in Open-Meteo's open AWS bucket |

## 2. Historical weather: POWER vs Open-Meteo at 16 representative cells, 1984–2024

Daily POWER (.WTH files) vs `era5_seamless` at the cell centre (temperature downscaled to the 90 m DEM). Bias = Open-Meteo − POWER.

| Zone (cells) | Tmax bias °C | Tmin bias °C | SRAD bias MJ/m²/d | Annual rain POWER / OM mm | Monthly rain r | NDJFM-total interannual r |
|---|---|---|---|---|---|---|
| Lowland (6) | −2.6 | −0.6 | −0.5 | 1,239 / 1,615 | 0.77 | 0.49 |
| Valleys (4) | −3.9 | −1.3 | −1.2 | 914 / 1,534 | 0.73 | 0.34 |
| Altiplano (6) | −1.4 | +1.7 | +0.8 | 611 / 941 | 0.77 | 0.44 |

Daily temperature correlations are 0.70–0.93, radiation 0.71–0.86. Three things stand out:

- **Precipitation totals disagree by 30–70 %** in the zone means, and by more at single cells (Chapare cell 5552581: POWER 752 mm/yr vs ERA5 3,164; Cochabamba valley cell 5578496: 667 vs 3,136). ERA5 is wetter almost everywhere.
- **The interannual NDJFM anomaly series, which carries the ENSO signal, correlate only 0.3–0.5 between the two reanalyses** (Santa Cruz lowland cell 5582853: 0.19). The two sources do not agree on which seasons were wet. This is the number that matters for the whole project and it is why a station arbiter was needed (§3).
- **Elevation.** POWER's header elevation is its 0.5° grid-point DEM; Open-Meteo's is the 90 m DEM at the cell-centre point. They differ by up to 1,100 m (cell 5578496: 1,727 m vs 2,865 m; Tarija cell 5785862: 2,962 vs 1,936), and the Tmax differences follow the elevation differences (−7.0 °C at the first, +1.1 °C at the second). Neither is the 5-arcmin cell mean. This confirms PLAN.md §6.2's "largest single uncertainty" but says nothing about which *source* is better.

## 3. Station arbiter: SENAMHI monthly records vs POWER vs ERA5

SENAMHI monthly precipitation and mean temperature, 1984–2009 (the `DATOS SENAMHI` files), plus the El Alto 1991–2020 normals
(the only station with Tmax/Tmin). POWER taken at the nearest MERRA-2 point; Open-Meteo `era5_seamless` at the station
coordinates. All 18 stations (completed 2026-10-14 on the paid archive endpoint; `debug/openmeteo/compare_stations.py`):

| Station (m) | Obs mm/yr | POWER mm/yr | ERA5 mm/yr | Monthly r POWER / ERA5 | NDJFM interannual r POWER / ERA5 | Mean-T bias POWER / ERA5 °C |
|---|---|---|---|---|---|---|
| Trinidad (157) | 1,841 | 1,761 | 2,059 | 0.83 / 0.77 | 0.49 / 0.44 | +1.0 / +0.0 |
| Cobija (280) | 1,935 | 1,764 | 1,859 | 0.91 / 0.81 | 0.48 / 0.32 | +0.0 / +0.2 |
| San José de Chiquitos (280) | 1,042 | 1,049 | 1,060 | 0.94 / 0.68 | 0.87 / 0.49 | +0.7 / +0.0 |
| Roboré (300) | 1,098 | 1,016 | 1,035 | 0.94 / 0.71 | 0.91 / 0.25 | +1.0 / +0.2 |
| Montero (317) | 1,320 | 1,319 | 1,835 | 0.79 / 0.73 | 0.52 / 0.41 | +0.7 / -0.7 |
| Chimoré (La Jota) (350) | 4,089 | 736 | 2,921 | 0.71 / 0.74 | 0.05 / 0.49 | +0.5 / -1.4 |
| Viru Viru (373) | 1,392 | 1,371 | 1,139 | 0.94 / 0.63 | 0.80 / 0.20 | +1.1 / -0.4 |
| San Ignacio de Velasco (413) | 1,103 | 1,135 | 1,133 | 0.97 / 0.77 | 0.96 / 0.38 | +0.9 / +0.3 |
| Camiri  (810) | 784 | 929 | 1,057 | 0.95 / 0.83 | 0.78 / 0.29 | -0.6 / -5.6 |
| Monteagudo (1,130) | 1,020 | 939 | 1,239 | 0.84 / 0.83 | 0.28 / 0.28 | +1.1 / -0.8 |
| Tarija (1,875) | 600 | 1,023 | 1,224 | 0.64 / 0.90 | 0.34 / 0.52 | -5.8 / -2.2 |
| Vallegrande (1,998) | 635 | 718 | 1,566 | 0.96 / 0.79 | 0.95 / 0.49 | +2.5 / +0.1 |
| Cochabamba (2,560) | 448 | 461 | 845 | 0.96 / 0.87 | 0.94 / 0.57 | -3.7 / -1.9 |
| Sucre (2,904) | 645 | 579 | 1,055 | 0.96 / 0.83 | 0.88 / 0.53 | +0.5 / -1.9 |
| Uyuni (3,660) | 194 | 327 | 456 | 0.72 / 0.79 | 0.40 / 0.37 | -0.3 / +0.3 |
| Oruro (3,701) | 407 | 403 | 632 | 0.96 / 0.85 | 0.87 / 0.45 | -0.3 / +0.3 |
| El Alto normals 1991–2020 (4,071) | 613 | 614 | 702 | 0.93 / 0.90 | 0.69 / 0.32 | +0.7 / -0.4 |
| El Alto SENAMHI (4,071) | 624 | 601 | 709 | 0.94 / 0.87 | 0.79 / 0.40 | +0.8 / -0.2 |
| **Median (18)** | | **6 % abs. error** | **25 %** | **0.94 / 0.80** | **0.79 / 0.40** | **0.7 / 0.4 (abs.)** |

El Alto normals, Tmax / Tmin bias: POWER +0.0 / +1.3 °C; ERA5 -2.3 / +1.5 °C.

**Precipitation: POWER wins at 15 of 18 stations and is never much worse.** Its annual totals are within a few percent (median absolute error
6 % vs 25 % for ERA5), and its NDJFM interannual series tracks the stations (median r 0.79) where ERA5 does not
(0.40). The exception is Chimoré in the Chapare, the wettest place in Bolivia: the station records 4,089 mm/yr, POWER 736 mm
and ERA5 2,921 mm, and POWER's NDJFM series has no skill there (r 0.05 vs 0.49). The CPC gauge analysis evidently has no
gauge in the Chapare wet belt, so POWER inherits a dry MERRA-2 background. This matches the §2 cell finding (Chapare cell
5552581: POWER 752 vs ERA5 3,164 mm). The Chapare is a minor cropland area for the five modelled crops (rice and maize
only) but any result there should be read with that caveat. Both sources are too wet at Tarija (obs 600 mm; POWER 1,023,
ERA5 1,224) and Uyuni (194; 327, 456), the two driest stations, where ERA5's NDJFM series is marginally the better one. The reason is structural: POWER's `PRECTOTCORR` is
MERRA-2 precipitation corrected to the CPC Unified gauge analysis, with full correction at Bolivian latitudes (Reichle et al.
2017), so over land it is essentially a gridded gauge product; ERA5 precipitation is model output. The check is therefore
partly circular for GTS synoptic stations (El Alto, Cochabamba, Oruro, Sucre, Viru Viru, Trinidad likely feed CPC), but the
agreement at Montero and Monteagudo, and the clear failure of ERA5 at the same points, make the conclusion safe:
**do not replace POWER precipitation with ERA5/Open-Meteo.** It also means the "POWER precipitation in the Andes is the
largest uncertainty" caveat in PLAN.md can be softened to "gauge-corrected, but gauge density in the Andes is low".

**Temperature: a question of elevation, not source.** POWER's mean-temperature bias is small (within ±1.1 °C) at lowland and
Altiplano stations whose MERRA-2 grid point sits at a similar height, and large where it does not (Cochabamba −3.7 °C,
Tarija −5.8 °C, Vallegrande +2.5 °C). ERA5 with 90 m downscaling halves those errors (−1.9, −2.2, +0.1 °C) but is
0.4–1.4 °C too cool at most lowland stations and misses Camiri by −5.6 °C. At El Alto, the only station with Tmax and Tmin,
POWER has Tmax right and Tmin 1.3 °C warm; ERA5 has Tmax 2.3 °C cold and Tmin 1.5 °C warm, so ERA5's smaller mean bias
elsewhere partly comes from compensating errors. The direction is clear: the planned **5-arcmin DEM + lapse-rate adjustment of the POWER cache**
(no refetch; PLAN.md §6.2) addresses the valley-cell problem without changing source, and it should use a cell-mean DEM,
not a point DEM as Open-Meteo does.

**Radiation:** POWER and ERA5 agree within ~1 MJ/m²/d with daily r ≈ 0.8. No change. SARAH-3 satellite radiation would be a
third opinion for the eastern lowlands only.

## 4. Seasonal forecasts: the item that could change the pipeline

What we do now: pull SEAS5 monthly-mean anomalies (2 m T, precipitation) from the CDS, compare each of 51 members with the
41 historical analogue seasons by zone, and weight the analogue DSSAT runs accordingly (`analysis/phase4_forecast_weights.py`).

What Open-Meteo adds: the same SEAS5 members as **daily Tmax/Tmin/precipitation/SRAD at 36 km** (checked at the Santa Cruz
lowland cell: 51 series × 183 days from the 2026-10 initialisation; monthly anomalies there, +1.1 to +1.7 K Nov–Mar, agree
with our CDS zone means), and the EC46 46-day ensemble refreshed daily.

Three ways to use it, in increasing order of change:

1. **CDS-independent cross-check / fallback for the current weights.** Pull monthly anomalies at a few points per zone
   each month (a handful of calls). Cheap, no design change, removes the dependence on CDS queue times. Low value if the
   CDS fetch keeps working, since the numbers agree.
2. **Fill the splice gap with EC46.** Today the spliced weather jumps from the last observed day straight into analogue
   weather. Replacing the first 46 days with EC46 members (or their mean) would make the early-season part of the 2026/27
   runs a forecast rather than an analogue. Modest machinery (one fetch per zone-representative point, a bias adjustment
   against the POWER climatology because the model climate differs), and it is where seasonal skill is highest.
3. **Forecast-driven DSSAT runs.** Drive each cell with each of the 51 daily members instead of weighting 41 analogue years.
   Costs: 51 members × 3,568 cells × 4 variables × 183 days is ~950k Open-Meteo "calls" per month, far beyond the free tier,
   so it would mean a few representative points per zone, or fetching the same members from the CDS/ECMWF open data as
   gridded files. The members are not bias-corrected and are "area forecasts" at 36 km, so a quantile or delta mapping
   against POWER climatology is needed before DSSAT sees them. Open-Meteo holds no hindcasts (archive starts 2026-09), so
   skill assessment and calibration would still come from the C3S hindcast set. Against that, the analogue approach's
   strength is that every driving season actually happened; the forecast-driven approach samples the forecast spread
   directly but inherits any model bias in daily rainfall statistics (dry-day frequency, intensity), which DSSAT is
   sensitive to.

Evidence on which is better for yield outlooks is mixed in the literature and depends on region and lead; this assessment
cannot settle it. A cheap experiment is option 3 at the 16 sample cells (one fetch each) compared with the analogue
ensemble at the same cells for 2026/27.

## 5. Other items noted

- **WeatherNext 2** is available free as an ensemble model on Open-Meteo (15 days, 64 members), which may simplify the
  `weathernext-data` workspace if it currently goes through Google Cloud.
- **Open-Meteo SEAS5 archive** starts at the 2026-09 initialisation; nothing older is retrievable.
- **Quota reality:** the free tier is sized for point queries, not gridded pulls. Anything cell-scale goes through the CDS
  or the Open-Meteo AWS open-data bucket.

## 6. Pending

- Station and cell comparisons completed 2026-10-14 (all 18 stations, 16 cells). Decision taken: option 2 of §4, i.e.
  Open-Meteo's EC46/SEAS5 members as a forecast tier spliced onto POWER (Phase 5, PLAN.md §12), Professional tier subscribed.
- Open question raised by Chimoré: whether POWER precipitation should be flagged or replaced in the Chapare wet belt only.
