# Bolivia ENSO — Data Inventory

Status of every file received, verified by opening it (not by filename). Reviewed 2026-09-15.

`data/` and `data/NOTA CONCEPTUAL CAF/` hold the same five Excel files; the top-level copies
appear to be duplicates of the CAF note bundle. Only the CAF folder carries `DATOS CLIMATICOS`.

---

## 1. Agricultural statistics

### 1.1 `Serie estadística agrícola - plana v2 oficial 28.2.25 (1).xlsx` — **primary calibration target**

Ten sheets; the two that matter are `Campaña Verano` and `Campaña Invierno`
(`BASE UNIDA` is the two of them pasted side by side; the rest are scratch/pivot sheets).

| | |
|---|---|
| Structure | Wide. Header on row 3: `DEPTO, ESTACION, GRUPO, CULTIVO`, then triplets `SUP. / PROD. / REND.` per campaign |
| Units | SUP = ha, PROD = t, REND = kg/ha |
| Geography | `BOLIVIA` + 9 departments (`POTOSÌ` is misspelled with a grave accent) |
| Crops | 73, in 7 `GRUPO`s (cereales, oleaginosas e industriales, tubérculos y raíces, hortalizas, frutales, estimulantes, forrajes) |
| Verano coverage | 13 campaigns, **2012-13 → 2024-25** |
| Invierno coverage | 14 campaigns, **2012 → 2025** |

Crop names carry footnote markers that must be stripped before joining:
`Soya (1)`, `Maíz en grano (1)`, `Trigo (1)`, `Sorgo en grano (1)`, `Frijol/poroto (1)`,
`Girasol (1)`. Several have trailing spaces (`Café `, `Plátano `, `Banano `, `Avena berza `).

**Area shares (2023-24 verano / 2024 invierno, national):**

| Verano (3.14 M ha) | % | Invierno (1.31 M ha) | % |
|---|---|---|---|
| Soya | 40.5 | Sorgo en grano | 36.8 |
| Maíz en grano | 11.7 | Soya | 32.4 |
| Caña de azúcar | 6.7 | **Girasol** | 13.8 |
| Arroz con cáscara | 6.6 | Trigo | 6.5 |
| **Papa** | 6.1 | Maíz en grano | 5.0 |
| **Quínua** | 3.8 | Frijol/poroto | 1.6 |
| Trigo | 2.5 | | |
| Sorgo en grano | 2.5 | | |
| Frijol/poroto | 2.3 | | |

Bold = no DSSAT module wired into Tokki today (see PLAN.md §4).

### 1.2 `agricola_municipal.xlsx` — **spatial allocation key**

Long format, already tidy: `gestion, departamento, municipio, cultivo, superficie, produccion, rendimiento`.
26,415 rows. **338 municipios**, 9 departments, 73 crops. Yield in **t/ha** (not kg/ha — differs
from 1.1). `gestion` = 2023, 2024, 2025 only, and is the *año agrícola* (both campaigns combined),
so it cannot separate verano from invierno.

Three years is too short to calibrate against, but it is the only sub-departmental crop
distribution in hand and it aligns with the 340 municipios in the climate file (§2.1).

### 1.3 `calendario_agricola.xlsx` — **crop calendar, seasons and sowing windows**

Two sheets. The calendar is encoded as **cell background shading, not cell values** — reading
it with pandas returns an all-NaN grid. Layout: column 2 onward, two columns per month
(1st/2nd half), running **Jul → Oct of the following year** (26 months). Source line credits
INE, INIAF, MDRyT.

Decoded to `derived/crop_calendar_bolivia.csv` (106 activity windows, 51 crop/season entries),
with explicit `start_year_offset` / `end_year_offset` flags for windows that cross 1 January.

Sowing windows for the crops that matter:

| Crop / season | Sowing | Harvest |
|---|---|---|
| Soya verano | 1 Nov – 15 Dec (DOY 305–335) | Apr – May |
| Soya invierno | 16 May – 15 Jun (DOY 136–152) | Sep – Oct |
| Maíz primavera | 1 Sep – 15 Oct (DOY 244–274) | Apr – Jun |
| Maíz manual | 16 Oct – 31 Dec (DOY 289–350) | Apr – Jun |
| Arroz verano | 16 Oct – 30 Nov (DOY 289–320) | Mar – Apr |
| Arroz primavera | 1 – 30 Sep (DOY 244–259) | Dec – Jan |
| Sorgo verano | 16 Oct – 15 Jan (crosses year end) | Feb – Apr |
| Sorgo invierno | 16 Apr – 30 Jun (DOY 106–167) | Sep – Oct |
| Trigo valles mesotérmicos | 16 Apr – 31 May (DOY 106–136) | Aug – Sep |
| Papa valles verano | 1 Aug – 15 Sep (DOY 213–244) | Nov – Dec |
| Frejol valles | 16 Oct – 15 Jan (crosses year end) | Feb – Apr |

Two label rows were mis-parsed in the source file and carry no window
(`TRIGO (Area integ-Invierno)`, `LECHUGA BLANCA (Altiplano)`); both need a manual read of the
spreadsheet if they are wanted. The calendar is national, with agro-ecological qualifiers
(*valles mesotérmicos*, *área integrada*, *altiplano*, *trópico*) rather than mapped zones —
so it gives the window, not its spatial footprint.

### 1.4 `ESTADISTICA PECUARIA.xlsx`, `pecuario_dptal.xlsx` — livestock

Nine sheets by species (bovino, ovino, porcino, caprino, llamas, alpaca, avícola carne/huevo).
Out of scope for a crop-model exercise; relevant only if the assessment extends to forage and
pasture. Not profiled further.

---

## 2. Climate data (`data/NOTA CONCEPTUAL CAF/DATOS CLIMATICOS/`)

### 2.1 `DATOS OAP/BD_CLIMA_DIARIO_20050101_20260630.csv` — 223 MB, daily, municipal

2,669,340 rows. Columns: `YEAR, DOY, T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, WS2M, WS2M_MAX,
WS2M_MIN, MUNICIPIO, FECHA, MO, DY, DIA_TXT, MES_NOMBRE, NUM_SEMANA`.

**340 municipios × 7,851 days, 2005-01-01 → 2026-06-30, zero gaps and zero missing values.**
Every municipio has exactly the same day count.

The variable names (`T2M`, `PRECTOTCORR`, `WS2M`) are **NASA POWER** identifiers, so this is
POWER reanalysis aggregated to municipality, not station observations.

Two limits for DSSAT use:
- **No solar radiation.** `ALLSKY_SFC_SW_DWN` is absent; DSSAT will not run without SRAD.
- **No coordinates.** Municipality names only, and non-ASCII characters are mangled
  (`AscensiA3n_de_Guarayos` = Ascensión de Guarayos), so a name join needs normalising.
- Starts 2005, so it **excludes the 1982/83 and 1997/98 El Niños** — the two closest analogues
  to what is now forecast.

### 2.2 `DATOS SENAMHI/*.xls` — 56 station files, monthly

44 files at the top level plus 12 in `LA PAZ/`. One sheet each, with stacked variable blocks.
Header carries station name, province, department, lat/long in degrees-minutes, and elevation.
Requires `xlrd` (legacy `.xls`); pandas' default engine cannot read them.

Audited all 56 (not just a sample), because the requirements sheet records these as
"1991-2020 (by month)" and that is not what they contain:

| | |
|---|---|
| **Period** | **All end 2009 or earlier** — 52 end exactly at 2009, the rest 2003–2008. **None reach 2010.** Most begin in the 1970s; 55 of 56 begin in 1991 or earlier. Value is depth, not recency. |
| **Temperature** | **54 of 56 carry *temperatura media* only.** Exactly 1 file has max/min, and those are *extrema* (absolute), not daily means of Tmax/Tmin. DSSAT needs Tmax and Tmin separately, so this variable is effectively absent. |
| **Precipitation** | Monthly totals. Present in most files under ~10 spelling variants of `PRECIPITACION ... (mm)`. |
| **Solar radiation** | Present in only **2** files, in non-standard units (`KCAL/CM2/MIN`, `CAL/CM2/DÍA`). No sunshine-hours blocks found. |
| **Wind** | Monthly mean direction/speed in knots, most files. |

**Monthly, not daily** — usable for bias-checking gridded precipitation and for extending ENSO
composites back to the 1970s, but not usable as DSSAT input. See `DATA-REQUEST.md` §2.1.

### 2.3 `NORMALES 1991-2020 (OMM) Y EXTREMAS PCPN_TX_TN (1)_5824.xlsx`

Three sheets (`NOR-PCPN`, `NOR-TMAX`, `NOR-TMIN`) for **one station only** —
El Alto Aeropuerto, La Paz, 4,071 m — monthly, 1991–2020. A spot check, nothing more.

### 2.4 ⚠️ Unexpected executables

`DATOS SENAMHI/newcpuspeedcheck/` contains two identical **Windows PE32 executables**
(`cpufix.exe`, 937 KB, dated 2015), a 2 MB zip with a scrambled name
(`asasdaddsldl.zip`), and `alover/cpuchecker.txt`. Nothing here is climate data and nothing
in the CAF note refers to it — it looks like a cracking/patching tool that rode along in the
shared folder. I have not opened or run any of it. Recommend deleting the directory and
mentioning it to whoever packaged the transfer.

---

## 3. Documents

`documents/` holds the same SENAMHI note in Spanish and English translation:
*Technological resources for the analysis of climate models and the El Niño phenomenon used
by SENAMHI*. The operationally relevant content:

- SENAMHI monitors NOAA SST anomalies, RONI and SOI, and runs station-based monitoring of
  Tmax/Tmin/precipitation plus anomaly *predictions* for all three.
- It downloads **seasonal forecast models from the Copernicus CDS**: ECMWF, NCEP, JMA, ECCC.
- Hydrology: Continuum and wflow; WEAP is recommended as the agricultural entry point,
  from a water-allocation angle.
- Explicit statement: the Directorate of Watersheds and the Vice-Ministry of Rural Development
  report having **no tool for ENSO analysis**, and SENAMHI is the only body in the country
  with ENSO analysis capability.

Two things follow. First, there is no crop-yield impact layer anywhere in the national system
— that is the gap Tokki would fill, not a duplication. Second, SENAMHI already pulls C3S
seasonal forecasts, which is the same source `~/Claude/weathernext-data/wn2dssat/c3s.py`
reads, so a forward-looking chain can be built on data Bolivia already has in hand.

---

## 4. Additional sources confirmed online

| Source | What it gives | Verified |
|---|---|---|
| INE *Año Agrícola por Departamento* — [production](https://nube.ine.gob.bo/index.php/s/sDryAo3LRxEvQcr/download), [yield](https://nube.ine.gob.bo/index.php/s/heefZ2fZlqIIMik/download), [area](https://nube.ine.gob.bo/index.php/s/6kBAE1i0Ys4tF0U/download) | **1983-84 → 2024-25, 42 seasons**, 9 departments + national, by crop. One sheet per department. Yield in kg/ha | Downloaded and opened — HTTP 200, valid xlsx |
| INE campaign tables (verano 2013-2025, invierno 2012-2025) | Same as the local file §1.1 | Listed on the page |
| [SIIP](https://siip.produccion.gob.bo/) | Municipal crop and livestock production, interactive viewer | No API or bulk download advertised; would need scraping or a data request |

The INE 42-season series is the single most valuable addition: it triples the record
available locally and is the only agricultural dataset in hand that covers 1982/83 and
1997/98. Note it is *año agrícola* (verano + invierno combined), so it constrains annual
departmental yield, not campaign-specific yield. The 2012+ campaign split (§1.1) is needed
to separate the two.

---

## 5. What is missing for a Tokki run

| Need | Status |
|---|---|
| MapSPAM 2020 crop area rasters, Bolivia | **Absent.** `/home/jawoo/Claude/mapspam-2020/` no longer exists — must re-download from mapspam.info |
| Daily weather with SRAD, per grid cell | **Must be generated.** §2.1 has no SRAD and starts 2005 |
| DSSAT soil profiles (`BO.SOL`) | **Present** (corrected 2026-10-03): `data/BO.SOL`, 13,069 profiles, full national extract of the ISRIC SoilGrids + HC27 5-arcmin library used for the US |
| Municipality boundaries / centroids | **Absent.** Needed to join §1.2 and §2.1 to grid cells |
| Fertilizer rates, planting density, irrigated share | **Absent.** No Bolivian equivalent of the NASS surveys used for the US |
| Cultivar coefficients for Bolivian germplasm | **Absent.** The tracked `MZCER048.CUL` / `SBGRO048.CUL` carry US calibration |
