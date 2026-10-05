# Additional data to request from the Bolivian team — Tapiti section

Review of `data/El Nino Bolivia - data requirements and availability.xlsx`, rows 3–11
(component 1, Tapiti model). Assessed against what is actually in hand (verified by opening
every file — see `DATA-INVENTORY.md`) and against what the model structurally requires
(`~/Codebase/Tokki/prep/constructing_unit-information.md`).

Rows 9, 10, 17–19 (water access, prices, CPI) and rows 12–22 (POVANA, RIAPA) are inputs to the
poverty and CGE components, not to the crop model. DSSAT does not use prices. Not assessed here.

---

## Part 1 — Two corrections to what the sheet records as already available

These matter because if the lead believes the climate data is in hand, they won't push for it.

### Rows 4 and 5: "Have data set for 1991-2020 (by month)" is not what we hold

Audited all 56 SENAMHI station files in
`data/NOTA CONCEPTUAL CAF/DATOS CLIMATICOS/DATOS SENAMHI/`:

| Finding | Detail |
|---|---|
| **Records end in 2009** | 52 of 56 end exactly at 2009; the rest at 2003–2008. **None reach 2010**, let alone 2020. There is a 17-year hole from 2010 to present. |
| **Temperature is MEAN, not max/min** | **54 of 56** files carry only *temperatura media*. Exactly 1 file has max/min blocks, and those are *extrema* (absolute extremes), not daily means of Tmax/Tmin. Row 5's requested variable is effectively **absent**. |
| Records start early | Most begin in the 1970s; 55 of 56 begin in 1991 or earlier. The archive's value is **depth, not recency**. |
| Time step | **Monthly.** Not daily. |

The only genuine 1991–2020 monthly series we hold is
`NORMALES 1991-2020 (OMM)...xlsx` — and that is **one station**, El Alto Aeropuerto.

DSSAT needs **daily Tmax and Tmin separately**; monthly mean temperature cannot be used.

### The daily file we do have is reanalysis, not observations

`DATOS OAP/BD_CLIMA_DIARIO_20050101_20260630.csv` is gap-free daily for 340 municipios,
2005-01-01 → 2026-06-30. But its column names (`T2M`, `T2M_MAX`, `PRECTOTCORR`, `WS2M`) are
**NASA POWER** identifiers — this is reanalysis aggregated to municipality, not station data.
It also has **no solar radiation** and starts in 2005, excluding the 1982/83 and 1997/98
El Niños.

---

## Part 2 — What to request, in priority order

Priorities reflect whether a workaround exists, not just desirability.

### PRIORITY 1 — Blocks Phase 1, no workaround

**1.1 Agro-ecological zone map (GIS, any format)**

The crop calendar we decoded from `calendario_agricola.xlsx` keys every sowing window to a
zone — *valles mesotérmicos*, *área integrada*, *altiplano*, *trópico*, *chaco*. We have the
windows but **no spatial definition of the zones**, so we cannot assign the correct sowing
window to a given grid cell. Soya verano sows 1 Nov–15 Dec in the área integrada; trigo in the
valles mesotérmicos sows 16 Apr–31 May. Without the zone boundaries those cannot be placed.

This is cheap for them to provide (it underpins their own calendar) and it is the one item
with no substitute. **Ask first.**

Source: INIAF / MDRyT, or whoever authored the *calendario agrícola* (credited to INE, INIAF,
MDRyT).

**1.2 Municipality codes and boundaries, with the code vintage**

Every delivery should carry the **INE municipality code**, not just the name. Two concrete
problems already visible in the data we hold:

- The OAP climate file has mangled encoding — `AscensiA3n_de_Guarayos` for *Ascensión de
  Guarayos*. Name joins will fail silently.
- It has **340** municipios; `agricola_municipal.xlsx` has **338**. Joining on names will
  silently drop rows without telling us which.

Also request the municipality boundary shapefile with matching codes. INE's geoportal
(`idg.ine.gob.bo`, already cited in row 9) appears to have it, so this may be self-serve — but
we need confirmation of which code vintage matches the agricultural data, since municipios were
created over the period.

### PRIORITY 2 — Materially improves quality; a weaker fallback exists

**2.1 Station-level daily data — and note the spatial unit in rows 4–5 is wrong for this model**

Rows 4 and 5 request precipitation and temperature *"by agricultural zones and
municipalities"*. Tokki simulates **5-arcmin grid cells**, and municipality means destroy
exactly the spatial variance the model uses. We also already hold municipality-aggregated
reanalysis, so that request would largely duplicate what we have.

What is actually useful: **daily station observations with coordinates**, which let us
bias-correct the gridded reanalysis that drives the model. Specifically:

- Daily **precipitation**, **Tmax**, **Tmin** per station (not monthly, not zone means)
- **From 1981**, not 1991 — see 2.2
- A **station inventory** as a separate table: station name, INE/WMO code, latitude, longitude,
  elevation, period of record, and **percent completeness per variable**. We hold 56 station
  files with no inventory, so we cannot tell which stations are usable without opening each one.

Fallback if declined: NASA POWER, which is what the working pipeline already uses. But POWER
precipitation over steep Andean terrain carries large uncertainty, and rainfall is the variable
carrying the ENSO signal — so station data is what would let us state that uncertainty instead
of assuming it away.

**2.2 Extend the climate request back to 1981**

Rows 4–5 ask for 1991 onward. Recommend **1981**:

- CPC's DJF ONI puts **1982/83 at +2.1** and **1997/98 at +2.2**. With Niño-1+2 currently at
  +3.4 °C, the 2026-27 event is strongly eastern-Pacific weighted, and 1982/83 and 1997/98 are
  the closest structural analogues — the two events Bolivian institutions treat as the
  benchmark drought years.
- Starting at 1991 forfeits **1982/83 and 1986/87**, leaving only 1997/98 and 2015/16 as strong
  analogues.
- INE's agricultural series starts at **1983-84**, so 1981 aligns the climate and yield records.
- NASA POWER also starts in 1981, so the two sources stay comparable.

**2.3 Solar radiation or sunshine hours — absent from the entire sheet**

DSSAT requires daily solar radiation. It is not requested anywhere in the sheet.

To be precise about the severity: this is **not a blocker**, because NASA POWER supplies SRAD
and that is what the working pipeline and our Bolivian smoke test already use successfully. The
reason to ask is that POWER serves SRAD on a coarse 1°×1° grid, so station measurements would
let us check it rather than trust it.

SENAMHI does hold this. Their SISMET database is documented as covering solar radiation and
sunshine hours alongside temperature and precipitation, and 2 of the 56 station files we were
given already contain radiation blocks (in `KCAL/CM2/MIN` and `CAL/CM2/DÍA`).

Request, in order of preference:
1. Daily **global solar radiation** at stations where measured
2. Daily **sunshine hours (heliofanía)** as the fallback — convertible to radiation via
   Ångström–Prescott
3. The **Atlas de Radiación Solar Global de Bolivia** (UMSS) as a secondary gridded product

**2.4 Soil data — also absent from the entire sheet**

No soil data is requested anywhere, yet it is one of Tokki's three required inputs per grid
cell. The model needs DSSAT-format profiles: horizon-wise clay/silt/sand, bulk density,
organic carbon, and depth to any restrictive layer.

Fallback is ISRIC SoilGrids v2 (global, modelled at 250 m) with HC27 pedotransfer functions —
which is what the US workspace uses. National survey data would be a real improvement,
particularly for rooting depth, which has no global source of comparable quality. For the US
this came from USDA SSURGO; Bolivia has no equivalent, so our placeholder is currently the
weakest part of the soil chain.

Request:
- Any **national soil map and profile database** (INIAF / MDRyT)
- Any existing **DSSAT-format soil library** for Bolivia (worth asking — agronomy groups
  sometimes have one already built)
- **ZONISIG / departmental PLUS** land-use zoning studies, which typically carry soil profile
  descriptions by mapping unit

**2.5 Censo Agropecuario 2013 — the best single source for crop management, and it's missing**

The sheet has no source for four fields Tokki needs per cell per crop: fertilizer rate applied,
recommended rate, planting density, and irrigated/rainfed status. Row 8 asks for the irrigated
share alone.

The **Censo Agropecuario 2013** (INE) covers *insumos* (inputs), *uso de agua para riego*
(irrigation water use), cultivated area by season, and agricultural practices — **at municipal
level**, with microdata catalogued on ANDA (`anda.ine.gob.bo/index.php/catalog/24`) and a
municipal query tool at `sice.ine.gob.bo/censofichacna/`. It is absent from the sheet entirely.

This is the highest-value addition to the ask list after the zone map, because it addresses
four gaps at once with one dataset. Add it, and ask specifically for the **microdata** rather
than published tabulations, so rates can be computed by crop × department.

On **row 8** as written: "1991-2026, annual" for irrigated shares is not realistic and probably
does not exist. A single recent cross-section by municipality and crop is sufficient — Bolivia
is overwhelmingly rainfed outside the valleys, which conveniently means the ENSO rainfall
signal passes through with little irrigation buffering.

### PRIORITY 3 — Determines calibration quality

**3.1 Varieties grown, and variety trial data**

This is the request most likely to change the numbers we publish. Our end-to-end smoke test on
real Santa Cruz cells produced **maize at 11.5–12.8 t/ha** against a Bolivian reality nearer
3–5 t/ha, because the model is currently running **US-calibrated cultivar coefficients**.
Soybean came out closer, at 2.3–3.1 t/ha dry matter.

To calibrate rather than merely rescale, we need:
- **Which varieties are actually grown**, by crop and region, with approximate area shares
- Their **maturity group** or days to maturity
- Ideally **variety trial data**: yield *plus* observed phenology dates (emergence, flowering,
  maturity), with site, year, and management

The phenology dates are the part that matters most and the part usually omitted. Without
observed flowering dates we can only match yield *level*, not *timing* — and timing is what
determines whether an ENSO rainfall anomaly lands on the critical flowering window, which is
the entire mechanism this study rests on.

Likely holders: **INIAF**, **CIAT Santa Cruz** (Centro de Investigación Agrícola Tropical),
and **ANAPO** for soy, maize, sorghum, wheat and sunflower.

**3.2 Sowing progress by campaign**

The smoke test confirmed the rainfall-onset scan is picking year-specific sowing dates — this
is the channel that carries a delayed rainy season into the yield result. To validate it we need
observed sowing dates or sowing progress by campaign.

The US equivalent is USDA NASS weekly planting progress. The Bolivian analogue is **ANAPO**,
which tracks sowing progress for Santa Cruz; MDRyT may hold more.

Without this, the planting-date response is a modelling assumption rather than a calibrated
behaviour, and it should be reported as such.

### PRIORITY 4 — Independent validation of the impact estimates

**4.1 Crop loss and affected-area records by campaign, municipality and hazard**

Nothing in the sheet records what actually happened on the ground in past El Niño years. Row 11
asks for a *risk map*, which is a hazard layer, not an outcome record.

Request:
- **VIDECI** (Viceministerio de Defensa Civil) emergency declarations and affected-area
  estimates by municipality and event type — drought, flood, hail, frost
- **MDRyT** damage and loss assessments by campaign and crop
- Loss records from the **Seguro Agrario Universal ("Pachamama")** crop insurance scheme, if
  accessible

This is the natural independent check on simulated yield anomalies for 2015/16 and 2023/24, and
it is the evidence a policy audience will find most legible. It is also the only channel that
captures flood and hail damage, which DSSAT systematically **under**estimates.

**4.2 Pre-2012 campaign split, if it exists**

INE's public campaign tables (verano, invierno) only start in 2012–2013. The long
1983-84 → 2024-25 series is *año agrícola* — both campaigns combined. Since this study is
verano-focused, ask INE whether **campaign-level data for 1984–2011 exists in unpublished
form**. If not, that is a stated limitation of the historical analysis rather than a gap to
chase.

---

## Part 3 — Do not request: already obtainable, or not needed

Keeping the ask list short makes it more likely to be answered.

**Row 7 (departmental, by campaign, 1984-2025) — already downloaded.** INE publishes this
openly and we have pulled all three files (production, yield, area), verified as
1983-84 → 2024-25 across 9 departments plus national, one sheet per department, yield in kg/ha.
Links are in `DATA-INVENTORY.md` §4. No need to burden the team — only the pre-2012 campaign
split (4.2 above) is worth asking about.

**Rows 9, 10, 11, 17, 18, 19 — not crop-model inputs.** Water access, producer and consumer
prices, and CPI feed the POVANA and RIAPA components. DSSAT does not use prices. The climate
risk map (row 11) is useful context for interpretation but is not a model input.

---

## Part 4 — One thing we could not verify

**Row 6's "Need to check on downloadable data" (OAP) is unresolved from our side.**
`oap.produccion.gob.bo` is unreachable from this network — the base URL and both cited paths
return no response at all, which may be geo-blocking rather than an outage.

So the question in row 6 cannot be answered by us. Ask the Bolivian team either to confirm the
download paths, or simply to **extract the municipal production/area/yield series for
2000–2022** and send it — we already hold 2023–2025 (26,415 rows, 338 municipios, 73 crops).

One caveat to flag when requesting it: the municipal data we hold is *gestión* (año agrícola,
both campaigns combined), so it cannot separate verano from invierno. Worth asking whether OAP
holds it **split by campaign**, since El Niño hits the verano season specifically.

---

## Part 5 — Forward-looking runs (Phase 4)

SENAMHI's own note states it downloads seasonal forecast models from the Copernicus CDS —
**ECMWF, NCEP, JMA, ECCC** — and that it is the only Bolivian institution with ENSO analysis
capability. The same note records that the Directorate of Watersheds and the Vice-Ministry of
Rural Development have **no tool for ENSO analysis**, which is precisely the gap a crop-yield
impact layer fills.

Worth asking:
- What seasonal forecast products they can share, in what format and at what lead time
- Whether they would **co-produce** the forward-looking runs, which would make the output
  something the national system can carry rather than an external study

A simpler alternative is our own Copernicus CDS account, since
`~/Claude/weathernext-data/wn2dssat/c3s.py` already targets that source. Worth deciding which
route before asking, so the request is concrete.

---

## Summary — the short version to send

| # | Request | Why |
|---|---|---|
| 1 | **Agro-ecological zone map (GIS)** | Blocks Phase 1; no substitute. Sowing windows cannot be placed spatially without it |
| 2 | **INE municipality codes + boundaries** in all deliveries | 340 vs 338 municipios and mangled accents mean name joins fail silently |
| 3 | **Daily station precip + Tmax/Tmin, 1981–2026, with a station inventory** | What we hold is monthly, ends 2009, and has mean temperature only |
| 4 | **Solar radiation or sunshine hours (heliofanía)** | Required by DSSAT; absent from the sheet. SISMET holds it |
| 5 | **National soil profile data / any DSSAT soil library** | Absent from the sheet; currently falling back to global modelled soils |
| 6 | **Censo Agropecuario 2013 microdata** | Covers fertilizer, irrigation and practices at municipal level — fills four gaps at once |
| 7 | **Varieties grown + variety trial data with phenology dates** | Maize currently simulates at 12.8 vs ~3–5 t/ha on US coefficients |
| 8 | **Sowing progress by campaign (ANAPO/MDRyT)** | Validates the planting-delay response that carries the ENSO signal |
| 9 | **VIDECI/MDRyT crop loss records by municipality and hazard** | The independent check on past-event impact estimates |
| 10 | **OAP municipal series 2000–2022, split by campaign if held** | We cannot reach the OAP site; we hold only 2023–2025 |
