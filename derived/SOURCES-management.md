# Sources for derived/management_defaults_bolivia.csv

Compiled 2026-10-03 by an automated literature pass (Claude subagent, web search + PDF
extraction) and then edited by hand into the CSV the input builder reads. Treat every number as
a documented default, not a measurement: confidence labels are the compiler's own, and rows
marked `fill` in the CSV have **no source of their own** — they copy the nearest zone/season.

How the CSV departs from the table below:
- Sowing `plantingDate` is the median of the source window, **capped at DOY 335** because Tokki's
  rainfall-onset scan runs ±30 days and is truncated at 31 December (year-wrap hazard). Affected:
  lowland sorgo verano (true centre ~349), valleys/lowland trigo verano (official window
  20 Nov–30 Jan, centre ~350). Lowland maize is set to 320, inside both the source window
  (15 Oct–15 Jan) and INE's primavera+manual calendar (1 Sep–16 Dec). Lowland sorgo invierno is
  105, inside both the source window (1 Mar–15 May) and INE's calendar (16 Apr–16 Jun).
- `nFertRateAct` is what the production run applies (`nitrogenRateSource: actual` in
  `Tapiti/config.yml`); `nFertRateRec` is carried for the recommended-practice scenario.
- Cultivar codes are the generic DSSAT entries chosen in `prep/build_unit_information_bolivia.py`,
  not from these sources.
- Text extracts of the PDFs used are kept in `documents/management-sources-extracts/`.

---

# Sources and derivations for management_defaults_bolivia.csv

Compiled 2026-10-03 from web research only (no project files read). Every number in the CSV is traced below. Items marked **ASSUMPTION** are judgements, not evidence. Items marked **CONFLICT** have materially disagreeing sources; the range is given.

Conventions
- `sowingStartDOY`/`sowingEndDOY` are calendar day-of-year. Where a window crosses 1 January the end DOY is smaller than the start DOY (rows lowland MZ verano 288->15, lowland SG verano 319->15, valleys WH verano 305->30). Treat as wrap-around.
- Bolivian statistics (INE, ANAPO, MDRyT) use only two campaigns: *verano* (rain-fed summer, sown Oct-Jan) and *invierno* (dry-season/winter, sown Mar-Jul). No distinct *primavera* campaign exists for maize or rice in Bolivian usage, so no primavera rows are given.
- Seed-to-plant conversions: plants/m2 = (kg/ha * 1000 / TKW_g) * establishment_fraction / 10000. TKW and establishment values used are stated per row.
- Nitrogen: urea = 46 % N; 18-46-00 = 18 % N; 15-15-15 = 15 % N; Sulfammo N-Pro = 26 % N; Compo Master = 34 % N (both from the Chane paper).

Local text copies of the PDFs used are in this directory (`*.txt`, extracted with pypdf) for audit.

---

## 0. National context figures (used to sanity-check N rates)

| Figure | Value | Source | Quote / note |
|---|---|---|---|
| FAOSTAT N use per cropland ha, Bolivia | 3.38 kg N/ha (2023); 2019-2023 mean 3.55; range 2.65-4.73 | FAOSTAT via Our World in Data grapher CSV (downloaded, `owid_n_full.csv`), https://ourworldindata.org/grapher/nitrogen-fertilizer-application-per-hectare-of-cropland | Neighbours 2022: Paraguay 24.8, Argentina 40.0, Peru 45.2, Brazil 96.2 |
| Fertilized area 2018 | 754,740 ha = 20.17 % of cultivated area; soya 277,486 ha, papa 109,210 ha, maiz 92,787 ha; urea 48,165 t | Fundacion Solon 2021 citing Senasag/ANAPO Plan Nacional de Fertilizacion, https://fundacionsolon.org/2021/05/20/los-agroquimicos-mas-usados-en-bolivia-entre-toxicidad-y-prohibiciones-internacionales/ (page now 404; figures recovered from search index) | Derived: 48,165 t urea x 0.46 = 22,156 t N; / 754,740 ha = 29 kg N/ha on fertilized land; / 3.74 Mha total = 5.9 kg N/ha, consistent with FAOSTAT |
| Santa Cruz fertilized share 2019 | "Solo el 18% de las 2.6 millones de hectareas cultivadas en Santa Cruz son fertilizadas"; "alrededor de 25 mil toneladas de urea"; crops most fertilized with urea: rice, maize, wheat | Publiagro 23-May-2019, CIAB president J.L. Llanos, https://publiagro.com.bo/2019/05/productores-de-santa-cruz-solo-fertilizan-el-18-por-ciento-de-la-superficie-cultivada/ | Derived: 25,000 t urea / ~500,000 ha fertilized = 50 kg urea/ha = **23 kg N/ha on fertilized fields** (Santa Cruz average dose) |
| Censo Agropecuario 2013: UPAs applying chemical fertilizer | Bolivia 30.5 %; Chuquisaca 31.1; La Paz 28.6; Cochabamba 46.1; Oruro 2.5; Potosi 19.6; Tarija 58.0; Santa Cruz 33.3; Beni 5.3; Pando 3.6 | INE Censo Agropecuario 2013 summary (CEDLA edition) Cuadro 50, https://cedla.org/wp-content/uploads/2016/06/cna_BOLIVIA_final.pdf (`cedla_censo.txt`) | UPA counts, not area; valley use is dominated by potato (CIAB: 80 % of Cochabamba potato area fertilized) |
| Senasag fertilizer distribution by crop | soya 46.2 %, barbecho 10.9 %, arroz 10.6 %, maiz 7 %, papa 3.4 %, cana 2.4 %, trigo 2.3 % | Fundacion Solon 2022 citing Senasag, https://fundacionsolon.org/2022/04/13/insumos-agricolas-una-nueva-industria-nacional-de-fertilizantes-y-agroquimicos/ (figures from search index) | All fertilizers, not N only |

---

## 1. lowland / SB / verano  (28 pl/m2; N act 0; N rec 0; DOY 305-355; 110 d; high)

- **plantingDensity 28 pl/m2**
  - "la densidad de siembra debe estar dentro de un rango de 250 mil a 350 mil plantas/ha., esto se logra con 50 a 70 kg/ha. de semilla ... se espera tener de 12 a 15 plantas establecidas por metro lineal" - Zamorano thesis (Diagnostico situacional de la produccion de soya, Santa Cruz), citing ANAPO, https://bdigital.zamorano.edu/bitstreams/efbd762b-1c00-4998-a329-548cbdd5fc87/download (`zamorano_soya.txt` l.167-171).
  - "FUNDACRUZ, aconseja a los productores una poblacion de 280 mil planta por hectareas de soya en la campana de verano y 300 mil plantas para invierno" - UCS 2014 density trial, San Pedro, http://www.revistasbolivianas.ciencia.bo/scielo.php?pid=S8888-88882014000100004&script=sci_arttext (`umsa_soya_dens.txt` l.119).
  - Verano populations "entre 200.000-280.000 pl/ha" - agrosoftware.wordpress.com 2011 (compilation of Santa Cruz variety sheets), https://agrosoftware.wordpress.com/2011/03/15/variedades-de-soya-en-santa-cruz-bolivia/.
  - Conversion: 280,000 plants/ha / 10,000 = 28 plants/m2 (plant counts, no seed conversion needed). Range 20-35.
- **nFertRateAct 0 / nFertRateRec 0**
  - "Tienen fertilidad natural alta todavia, por lo que el cultivo del trigo y soya se realizan sin fertilizantes" - UAGRM 2007 Estrategias para la ampliacion del cultivo de trigo, p.84, https://files.uagrm.edu.bo/entidad/62/file/2007_09__Estrategia_para_la_ampliacin_de_cultivo_de_trigo..pdf (`uagrm_trigo_estrategia.txt` l.3516).
  - Trials routinely inoculate: "La semilla de soya se inoculo con el inoculante N2 en dosis de 35ml/100 kg de semilla" (UCS 2014, l.174).
  - Senasag 2018: 277,486 ha of soya fertilized of ~1.3 Mha (about 21 %); the Santa Cruz fertilizer market for soya is P/K and micronutrients. **ASSUMPTION**: residual N in starter blends on fertilized fields is < 5 kg N/ha; rounded to 0. A regional recommendation of 100 kg/ha of 18-46-00 (= 18 kg N) appears in generic agronomy pages surfaced by search but could not be tied to a Bolivian institution; not adopted.
- **sowing 305-355 (1 Nov - 20 Dec)**
  - "01 de noviembre al 20 de diciembre" (zona Este), "15 de noviembre al 20 de diciembre" (zona Norte) - agrosoftware 2011 variety sheets.
  - "la campana de verano comprende desde la primera quincena de noviembre hasta el final del mes de diciembre (FUNDACRUZ, 2009)" - UCS 2014 l.51.
  - "La siembra ideal esta entre el 15 de noviembre hasta el 10 de diciembre (verano)" - FUNDACRUZ Huracan sheet, UCS 2014 l.120.
- **cycleDays 110**
  - ANAPO classes: "precoces de hasta 105 dias, intermedias de 106 a 115 dias y tardias mayores a 116 dias" (agrosoftware 2011; also quoted via search of autoridadempresas.gob.bo soya study). Midpoint of the dominant intermediate class = 110.
- Area context: verano 1.1-1.3 Mha vs invierno ~0.4 Mha (ANAPO 2023-25 via Publiagro/AgroSinergia/ValorAgro).

## 2. lowland / SB / invierno  (32 pl/m2; N 0/0; DOY 161-201; 105 d; high)

- Density: "300.000 a 450.000 plantas/ha en variedades de porte alto y bajo respectivamente con 0.4 metros entre surcos" (search snippet of a Santa Cruz guide) and FUNDACRUZ 300,000 (UCS 2014 l.119); agrosoftware invierno "250.000-350.000 pl/ha". Used 320,000/ha = 32 pl/m2. Trial optimum "15 plantas/metro lineal" at 36 cm rows = 417,000/ha (UCS 2014) is the upper end.
- Sowing: "10 de junio al 20 de julio" (agrosoftware 2011); "campana de invierno desde la primera quincena de junio hasta mediados de julio (FUNDACRUZ, 2009)" (UCS 2014 l.51); ANAPO: soya invierno "su siembra se concentra principalmente entre junio y julio" (Publiagro 16-May-2025). DOY 161 (10 Jun) - 201 (20 Jul).
- Cycle: Huracan RG "ciclo precoz de 100 dias de maduracion" (UCS 2014 l.112,140); intermediate class 106-115. Used 105.
- N: as row 1.

## 3. lowland / MZ / verano  (5.5 pl/m2; N act 25; N rec 100; DOY 288-15; 115 d; medium)

- **plantingDensity 5.5 pl/m2 = 55,000 plants/ha**
  - "una poblacion uniforme de plantas de 4 - 5 plantas/m lineal y una poblacion de 55000 plantas/ha" - UCB thesis, EEAS Saavedra urea trial, https://repositorio.ucb.edu.bo/bitstreams/7a6a988a-aca4-4f7c-af53-e1b62f00d662/download (`ucb_maiz_urea.txt` l.212-214).
  - "una poblacion aproximada de 57.000 plantas por hectarea" - UAGRM 2024 sowing-date trial, El Vallecito (380 m), https://ojs.uagrm.edu.bo/revista-cientifica-uagrm/article/download/2/1/16 (`uagrm_maiz_epocas.txt` l.287).
  - 65,000/ha in CIFUMSS 2022 Vallecito/Mairana trial (`cifumss_rev65_5.txt` l.283). Commercial hybrid seed in Pailon cost sheet: 20 kg/ha (IPDRS, search snippet) which at ~0.30 g/seed and 85 % establishment gives ~57,000/ha.
- **nFertRateAct 25 kg N/ha**
  - IPDRS/campovirtual cost sheet "CULTIVO MAIZ AMARILLO DURO ... Pailon": urea "2 qq" per ha (search snippet; file requires login) = 92 kg urea = **42 kg N/ha on a fertilized mechanised field**.
  - Only ~18 % of Santa Cruz cropland fertilized; maize among the three crops that are (CIAB 2019). Senasag 2018: 92,787 ha of maize fertilized nationally of ~470,000 ha (~20 %); Santa Cruz is ~50-58 % of national maize area (INE table in UAJMS thesis: Santa Cruz 106,100 ha of 301,650 ha in 2011/12, 58 %), so the fertilized share within Santa Cruz is plausibly 30-60 %.
  - **ASSUMPTION**: 25 kg N/ha = ~60 % of fields at 42 kg N and 40 % at 0. Range 15-42.
- **nFertRateRec 100 kg N/ha**
  - "el tratamiento: 100 kg N ha-1, aplicados en VE + V6, se presento el mayor rendimiento (5.541 kg ha-1)" and abstract yields 3,326 / 4,718 / 3,488 kg for 50/100/150 kg N - UCB EEAS Saavedra (`ucb_maiz_urea.txt`).
  - Supporting: "Mas del 70 % de las fincas ... rendimientos por debajo de los 3500-4000 kg ha-1 ... Esto se atribuye principalmente a la falta de fertilizacion" (same source l.60-70).
- **sowing 288-15 (15 Oct - 15 Jan, wraps)**
  - "Cuellar (2022) senala que el calendario de siembra de maiz varia de acuerdo a la zona de produccion y el establecimiento de las lluvias, desde 15 de octubre al 15 enero en verano y desde el 15 de marzo a fines de abril en invierno" - UAGRM 2024 l.173-177.
  - ANAPO general verano window "entre el 15 de noviembre y el 15 de diciembre ... en el Norte ... hasta el 15 de enero" (Unitel/ANAPO 2024 via search).
- **cycleDays 115**
  - UAGRM 2024 Table 1: Dec sowing 110 d to harvest, Jan 111, Feb 101 (`uagrm_maiz_epocas.txt` l.277-282); CIAT hybrids "cosechan entre 120 a 150 dias" (IBCE/CIAT). Used 115 (physiological maturity ~10 d before harvest maturity for the 120-130 d class).
- Area: ANAPO projects ~100,000 ha maize verano 2024/25 and 2026/27 (ValorAgro/ANAPO); yields verano 2020/21 5.01 t/ha vs invierno 2021 2.32 t/ha (ANAPO 2021 cited in UAGRM 2024 l.170-172).

## 4. lowland / MZ / invierno  (5.5; 25/100; DOY 74-120; 120 d; medium)

- Sowing "desde el 15 de marzo a fines de abril en invierno" (Cuellar 2022 in UAGRM 2024). DOY 74-120.
- Cycle: UAGRM 2024 Table 1: Mar sowing 112 d, Apr 117 d, May 131 d to harvest. Used 120.
- Density and N as row 3 (same farms, same cost structure). **ASSUMPTION** that N practice equals verano; winter yields (2.3-2.6 t/ha) suggest some farmers apply less; range 10-42.

## 5. lowland / RI / verano  (220 pl/m2; N act 15; N rec 100; DOY 288-349; 130 d; low)

- **System shares (direct-seeded secano vs irrigated)**
  - "La superficie cultivada en el ambito nacional es de 179.162 hectareas (90% a secano y solo 10% bajo riego)" and "442 mil toneladas (80%) provienen del sistema de produccion a secano" (2006) - CIPCA, El arroz en Bolivia, https://biblioteca.cipca.org.bo/pdf-download/el-arroz-en-bolivia/ (`cipca_arroz.txt` l.5941-5946).
  - By system: "el sistema manual representa el 34% de la superficie cultivada ... 61 mil hectareas ... aporta solamente el 19% de la produccion"; "el sistema bajo riego ... 10% de la superficie ... 20% de la produccion"; "mecanizado a secano ... 55% de la produccion nacional, una superficie cultivada de 90 mil hectareas" (l.2276-2284).
  - FENCA 2013: "el 90% de produccion se desarrolla en el sistema 'secano'" (El Dia 14-Feb-2013, https://www.eldia.com.bo/noticia.php?id=110276&id_cat=473). Later press: "80% ... secano y solo 20% ... con riego" (production basis; Publiagro/El Dia on San Juan de Yapacani).
  - Irrigated rice is also mostly **direct seeded**, not transplanted: "Se siembra con maquinas sembradoras o boleadoras ... a excepcion del arroz pregerminado o transplantado" (CIPCA l.2229-2236). Transplanting is used only for CIAT seed multiplication.
  - **Row represents direct-seeded rain-fed (secano) rice, ~90 % of area.** For an irrigated variant use: 100 kg/ha seed, urea 70 kg + 15-15-15 50 kg = 32+7.5 = **40 kg N/ha** (CIPCA irrigated cost sheet l.8954-8958), yield 6 t/ha, FLAR recommends N split 80 % V4 / 20 % panicle differentiation (`ciat_flar_arroz.txt` p.17).
- **plantingDensity 220 pl/m2**
  - Seed rates: mechanised secano "Se utiliza de 100 a 120 kilos de semilla por hectarea" (CIPCA l.2112, 2185); INIAF Yapacani trial "al voleo a razon de 90 kg" (`iniaf_arroz_N.txt` l.122); CIAT recommendation "para variedades modernas de grano largo fino (MAC FL-18) no deberia exceder los 70-80 kg/ha; ... Jasaye ... 100-120 kg/ha" (CIAT/IBCE); FLAR: 80 kg/ha gives "planta mas fuerte, muchos macollos" vs 160 kg/ha "planta debil" (`ciat_flar_arroz.txt` p.12).
  - TKW: MAC-18 "Peso de mil granos: 30,2g"; SACIAT FL-40 33.7 g (CIAT Variedades de arroz 2020, `ciat_arroz_variedades.txt`).
  - Conversion (farmer practice 100 kg/ha): 100,000 g / 30.2 g = 3.31 M seeds/ha = 331 seeds/m2; x 0.65 field establishment (**ASSUMPTION**, broadcast on unlevelled secano) = 215 -> **220 pl/m2**. Cross-check: Chane trial drilled 65 seeds/m at 17 cm rows = 382 seeds/m2 and counted 44-54 plants per linear metre = 260-320 pl/m2 (`umsa_arroz_chane.txt` l.93). Range 150-320.
  - Manual (chaqueado) system, 34 % of area in 2006: "se siembra con matraca o punzon a una distancia de 30 a 40 centimetros entre surcos y entre plantas ... 20 a 40 kilos de semilla por hectarea" (CIPCA l.1993-1997) = 6-11 hills/m2, roughly 30-50 pl/m2. Not represented in the row.
- **nFertRateAct 15 kg N/ha**
  - Manual system: "no se realiza fertilizacion" (CIPCA l.2016); combined system: "en este sistema no se ocupa fertilizantes" (l.2115); mechanised secano cost sheets: "Urea kg 50,00" per ha (l.8759, 8809) = **23 kg N/ha**; irrigated 40 kg N/ha (above).
  - **ASSUMPTION** (area-weighted 2006 shares): 0.34 x 0 + 0.56 x 23 + 0.10 x 40 = 17 -> rounded 15. Range 0-40. Rice is 10.6 % of national fertilizer use (Senasag) so some intensification since 2006 is likely; confidence low.
- **nFertRateRec 100 kg N/ha - CONFLICT, weakest number in the table**
  - Chane 2008/09 (UCEBOL): best economic treatment 100 kg/ha Sulfammo (26 % N) = **26 kg N/ha**, +42 % yield over 0 N; linear response to Compo Master up to 120 kg (= 41 kg N) (`umsa_arroz_chane.txt` l.43,112-118).
  - INIAF Yapacani 2015/16 (MAC-18, secano): "maximo de rendimiento de 4246 kg/ha con una dosis optima de 225 kg N/ha" from a quadratic fit in a season where "las condiciones de precipitacion pluvial no fueron favorables" (`iniaf_arroz_N.txt` l.21-25), http://www.revistasbolivianas.ciencia.bo/pdf/rciii/v1n7/v1n7_a09.pdf.
  - CIAT/FLAR 2020 secano recommendation is a split (50 % N incorporated pre-sowing, 25 % V4, 25 % DPF) without a rate (`ciat_flar_arroz.txt` p.16).
  - **ASSUMPTION**: 100 kg N/ha chosen as a mid value between the Chane economic optimum (26) and INIAF agronomic optimum (225); it also equals the INIAF trial's second dose. Range 26-225. A Brazilian upland-rice analogue would be 60-90 kg N/ha.
- **sowing 288-349 (15 Oct - 15 Dec)**
  - "Siembra. Se realiza entre la segunda quincena de octubre y la primera quincena de diciembre" (mechanised secano and irrigated, CIPCA l.2108, 2179, 2229); manual system "desde la segunda quincena de septiembre hasta la segunda quincena de noviembre" (l.1993). INIAF trial sown 6 Oct 2015; Chane trial Oct 2008.
- **cycleDays 130**
  - MAC-18 "A floracion: 107 dias; A maduracion: 137 dias" (63 % of certified seed 2018/19); SACIAT FL-40 124 d; Jasaye 139 d; SACIAT FL-41 131 d; CIAT BIO-44 123 d (`ciat_arroz_variedades.txt`). Seed-weighted ~132 -> 130.

## 6. lowland / SG / verano  (15 pl/m2; N act 10; N rec 90; DOY 319-15; 112 d; low)

- Density: Usuri hybrids, "140.000 a 160,000 plantas de sorgo por hectarea" (AgroSinergia, Exposoya 2026, https://agrosinergia.com.bo/exposoya-2026-usuri-semillas-presento-tres-hibridos-de-sorgo-para-las-principales-zonas-productivas/) = 14-16 pl/m2 -> 15. Generic Bolivian student review gives 20-30 pl/m2 / 200,000-300,000 ha and 15 kg/ha hybrid seed (Agro-Vet 2017, http://www.revistasbolivianas.ciencia.bo/scielo.php?script=sci_arttext&pid=S2523-20372017000100006, `agrovet_sorgo.txt` l.34-37). Cuatro Canadas cost sheet: 10 kg seed/ha (IPDRS snippet). Range 12-25.
- Sowing: ANAPO verano window "entre el 15 de noviembre y el 15 de diciembre ... Norte hasta el 15 de enero" (Unitel/ANAPO 2024 via search); Agro-Vet: "se debe sembrar entre los meses de noviembre hasta febrero". DOY 319-15.
- Cycle: "Raptor AT ... ciclo corto de 110 dias en verano"; "Sayubu 103 / Santa Fe ... 115 dias en verano" (AgroSinergia 2026). Used 112.
- N act 10 / N rec 90: see row 7.
- Area: ~100,000 ha verano (ANAPO 2024/25, 2026/27 projections) vs 535,000-612,000 ha invierno.

## 7. lowland / SG / invierno  (15; 10/90; DOY 60-135; 120 d; low)

- Sowing: ANAPO/CAO 16-May-2025: sorghum "80 %" sown, wheat/maize/sunflower ">60 %" (Publiagro, https://publiagro.com.bo/2025/05/campana-de-invierno-en-santa-cruz-alcanza-el-50-de-avance-en-la-siembra/); maize invierno window 15 Mar-end Apr (Cuellar 2022). **ASSUMPTION**: sorghum window 1 Mar - 15 May (DOY 60-135), consistent with 80 % completion by mid-May.
- Cycle: "125 dias a cosecha en invierno (ciclo intermedio)", "115 dias ... ciclo corto" (AgroSinergia 2026). Used 120.
- **nFertRateAct 10 kg N/ha - ASSUMPTION.** No Bolivian cost sheet with sorghum fertilizer could be opened (IPDRS file behind login). Evidence: sorghum is a low-input rotation crop ("cultivo de rotacion", ANAPO 2026, https://eju.tv/2026/05/santa-cruz-sorgo-es-el-principal-cultivo-de-la-campana-de-invierno/); sorghum is not among the three most-fertilized crops in Senasag 2018 (soya, papa, maiz) nor in CIAB's Santa Cruz list (arroz, maiz, trigo); Santa Cruz average dose on fertilized land is 23 kg N. 10 = roughly 40 % of fields at the Santa Cruz average dose. Range 0-23.
- **nFertRateRec 90 kg N/ha**: "Una recomendacion muy general es de 90-60-30 Kg/ha de N, P y K" (Agro-Vet 2017 l.42). This is a Bolivian-published but generic (textbook) recommendation; no ANAPO/CIAT sorghum N guide was found. Range 50-90 (Argentine guides: 50-60 kg N single application).

## 8. lowland / WH / invierno  (280 pl/m2; N act 23; N rec 60; DOY 105-181; 105 d; medium)

- **Regional split and area shares**
  - "En Bolivia, el trigo se cultiva en dos regiones definidas: occidental y oriental. La region occidental (tradicional) ... Cochabamba, Chuquisaca, Potosi, Tarija y en menor superficie en Oruro y La Paz; produccion de verano ... La region oriental ... Santa Cruz ... en invierno a escala empresarial y en rotacion con el cultivo de soya" - MDRyT/SIIP 2024, Analisis del complejo productivo del trigo 2023, https://siip.produccion.gob.bo/noticias/files/2024-f0723-LIBRO-complejo-productivo-TRIGO-.pdf (`trigo_complejo2023.txt` l.290-300).
  - Shares: "el 75% de la produccion de invierno se encuentra en el departamento de Santa Cruz ... el occidente con el 25% en campana de verano" (l.302-306); Santa Cruz 75.2 % and Cochabamba 8.2 % of production (l.529); Santa Cruz 140,789 ha, 1.7 t/ha in 2022 (l.678-681) of a national 206,763-214,962 ha (l.553-554, 615) = ~66-68 % of area. Censo 2013: 74,708 of 130,476 ha (57.3 %) in Santa Cruz, Chuquisaca 16,240 ha (12.4 %) (Correo del Sur 2015).
  - Yields: oriente 0.9-2.3 t/ha, area tradicional 0.7-1.0 t/ha (INIAF-Totora paper l.55-57).
- **plantingDensity 280 pl/m2**: "se emplea una densidad de 300-400 semillas por m2 (de 100 a 130 kilos de semilla)" (UAJMS wheat thesis via search, Bolivian); Enciclopedia Bolivia Agropecuaria wheat sheet: "400 plantas por m2. Entre 120 y 150 kg/Ha de semillas" (`enc_agricultura.txt` l.553). Conversion: 115 kg/ha / 38 g TKW (**ASSUMPTION** typical Motacu seed) = 303 seeds/m2 x 0.9 establishment (drilled) = 272 -> 280. Range 250-400.
- **nFertRateAct 23 kg N/ha**: wheat is one of the three Santa Cruz crops "mas fertilizados con urea" (CIAB 2019); Santa Cruz average dose on fertilized land = 50 kg urea = 23 kg N/ha (derived above). Earlier (2007) UAGRM: "el cultivo del trigo y soya se realizan sin fertilizantes" on Rio Grande soils. **ASSUMPTION**: all current Santa Cruz wheat receives the average fertilized-field dose; if only half is fertilized the figure is ~12. Range 0-46.
- **nFertRateRec 60 kg N/ha - ASSUMPTION (derived).** No ANAPO/CIAT numeric N recommendation for Santa Cruz wheat was found. Derived from the rule "25-30 kg de N por cada tonelada de rendimiento esperado" (Paraguayan/Argentine extension via search) x 2.0-2.5 t/ha attainable (Motacu average 2.5 t/ha, CIAT) = 50-75. INIAF's valley recommendation is 100 kg N (row 10). Range 50-100.
- **sowing 105-181 (15 Apr - 30 Jun)**: official "en la zona oriental ... el trigo se cultiva en invierno, entre los meses de mayo, junio y julio" (MDRyT 2023 l.667-670); but ANAPO reported wheat ">60 %" sown by 16 May 2025 (Publiagro), so sowing starts in April. Window chosen to bracket both. Range DOY 91-212.
- **cycleDays 105**: Motacu-CIAT "100-106 dias a madurez fisiologica", 70-72 d to flowering (UAJMS thesis via search; CIAT); "Mas del 90% del area de trigo ... en Santa Cruz usa variedades generadas por el CIAT".

## 9. valleys / MZ / verano  (4.5 pl/m2; N act 10; N rec 80; DOY 274-365; 165 d; low)

- Zone/area: INE 2011/12 maize area: Chuquisaca 69,320 ha, Tarija 36,730, Cochabamba 37,400, Potosi 20,050, La Paz 18,350 (UAJMS thesis Table 1, `uajms_maiz_tarija.txt` l.60-72). Tarija's area is largely in the Chaco (Gran Chaco province, lowland), so the valley maize zone is chiefly Chuquisaca-Cochabamba-Tarija valleys and La Paz/Potosi inter-Andean valleys.
- **plantingDensity 4.5 pl/m2 - ASSUMPTION.** Enciclopedia Bolivia Agropecuaria maize sheet: "varia entre 35 000 y 120 000 plantas por hectarea. Se requiere entre 18 a 25 kg de semilla por hectarea ... separacion entre surcos de entre 50 cm a 1 m" (`enc_agricultura.txt` l.241-245). A search-indexed Bolivian valley guide gives 80 cm x 40 cm = 44,000 plants/ha. Trials in valleys use 57,000-65,000 (UAGRM, CIFUMSS, Tarija INIAF 64,000). Farmer manual sowing of criollo maize is at the low end; 45,000/ha = 4.5 pl/m2 chosen. Conversion check: 20 kg/ha seed / 0.35 g = 57,000 seeds/ha x 0.8 = 46,000. Range 3.5-6.
- **nFertRateAct 10 kg N/ha - ASSUMPTION.** La Paz valley survey (Inquisivi, 2,700 m): "El cultivo de maiz es 100% organico ya que todas las familias entrevistadas indican que no utilizan fertilizantes quimicos" (UMSA Cibum Scientia 2023, https://cibumscientia.umsa.bo/index.php/1/article/download/40/40/46, `umsa_maiz_lapaz.txt` l.352). Censo 2013: 31-58 % of UPAs in Chuquisaca/Cochabamba/Tarija use chemical fertilizer, concentrated on potato. Tarija thesis notes farmers "fertilizan los cultivos sin ninguna dosificacion en especifico" (l.200). 10 kg N = about 20 % of fields at ~50 kg N. Range 0-20.
- **nFertRateRec 80 kg N/ha**: "Las Necesidades aproximadas de ... para el cultivo de maiz con riego por surcos es de 80 kg/ha de Nitrogeno, 40 kg/ha de Fosforo y 60 kg/ha de Potasio" (SEDAG Tarija 2019 cited in UAJMS thesis l.1707-1709); the thesis' own optimum at Chaguaya (1,957 m) was 140 kg urea = 64 kg N (4,070 kg/ha vs 2,780 at 0 N) (l.2578-2593, 2716). Range 64-100.
- **sowing 274-365 (Oct-Dec)**: "Meses de siembra: Valles: de octubre a diciembre; (zonas con riego y sin heladas: agosto y septiembre)" (Enciclopedia, l.238-239); Tarija trial "la siembra se realizo a fines de octubre" (l.1380); "La epoca de siembra de maiz Kculli en los valles interandinos de Bolivia se efectua en el mes diciembre" (Ortiz 2012 in UAGRM 2024 l.178-181); MDRyT calendar via search: maize planted Sep-Nov.
- **cycleDays 165**: "Morado Criollo ... un ciclo de cinco meses adaptado para los valles de Tarija, Cochabamba, Chuquisaca y Potosi" (INIAF 2019 in UAGRM 2024 l.158-164); Valle Alto 2,760 m: "la madurez de cosecha ocurrio a los 6 meses y 6 dias" (Mamani 2021 in CIFUMSS 2022 l.433-436); Inquisivi 2,700 m: harvest at 210-240 d (l.559-560). Used 165 (5.5 months) for the 2,000-2,800 m band; use 200+ above 2,700 m.

## 10. valleys / WH / verano  (170 pl/m2; N act 5; N rec 100; DOY 305-30; 135 d; medium)

- **Season confirmed**: highland/valley wheat is a rain-fed summer crop: "En el area tradicional la siembra de trigo se realiza en verano, desde el 20 de noviembre hasta el 30 de enero" (MDRyT 2023 l.661-665); "el trigo se cultiva en epoca de lluvia (noviembre - abril)" (UAGRM 2007 l.4586); Chuquisaca harvest May-July (INIAF via Publiagro 2025). Sowing is therefore mainly **Nov-Jan, not Oct-Dec**; Oct sowing occurs only in early-rain or irrigated spots. Window used 1 Nov - 30 Jan (DOY 305-30, wraps). Range: 20 Nov-30 Jan official.
- **plantingDensity 170 pl/m2**: farmer seed "Los productores de trigo siembran cantidades de semilla que oscilan entre los 80 y 100 kg/ha, es decir menores a la recomendada" (optimum 120 kg/ha) - UAGRM 2007 citing PROTRIGO (l.2179-2188); INIAF-Totora recommendation 100 kg/ha. "la baja densidad de plantas" is listed among limiting factors in the traditional area (MDRyT 2023 l.312). Conversion: 90 kg/ha / 38 g TKW = 237 seeds/m2 x 0.7 establishment (broadcast, animal traction - **ASSUMPTION**) = 166 -> 170. Range 120-260.
- **nFertRateAct 5 kg N/ha**: "No obstante de que los suelos estan agotados en su fertilidad, el campesino no usa su escaso capital para fertilizar el trigo" (UAGRM 2007 l.3557); wheat only 2.3 % of national fertilizer use (Senasag). **ASSUMPTION**: 5 (a minority of seed producers apply 15-15-15). Range 0-15.
- **nFertRateRec 100 kg N/ha**: "una densidad de siembra de 100 kg*ha-1, y una dosis de fertilizacion de 100 kg*ha-1 de nitrogeno, en funcion del suelo ... 50% en la siembra y el resto en la etapa de macollaje" - INIAF-Totora 2014 release paper, http://www.revistasbolivianas.ciencia.bo/pdf/rciii/v1n7/v1n7_a08.pdf (`iniaf_totora_trigo.txt` l.232-241).
- **cycleDays 135**: INIAF-Totora 2014 "el ciclo vegetativo es de 78 dias y 135 dias a madurez fisiologica" (l.156-157), recommended 2,000-2,990 m in Cochabamba. Older varieties BR18 108-118 d, San Marcos 105 d (feria-trigo l.361-362) are earlier; local criollos are longer.

## 11. altiplano / WH / verano  (170 pl/m2; N act 3; N rec 100; DOY 288-335; 165 d; low)

- Scope: wheat above ~2,800 m in La Paz, Oruro and Potosi (Betanzos 3,327 m, Puna). Official data lump Potosi with the valleys; La Paz + Oruro (+ Beni, Pando) = "2% de la produccion nacional" (MDRyT 2023 l.647-649). Area share of this row is therefore small (roughly 5-8 % of national wheat area, **ASSUMPTION** based on Potosi plus La Paz/Oruro).
- Density: as row 10 (same farmer seed rates 80-100 kg/ha; no separate highland figure found).
- **nFertRateAct 3 kg N/ha - ASSUMPTION** from Censo 2013 chemical-fertilizer use: Oruro 2.5 % of UPAs, Potosi 19.6 %, La Paz 28.6 % (mostly potato). Range 0-10.
- **nFertRateRec 100 kg N/ha**: analogue from INIAF-Totora (valleys) - **labelled analogue**; no INIAF altiplano wheat recommendation found. Oruro "trigo de altura" trials (INIAF/UTO, La Patria) report adaptation but not rates (page unreachable at time of writing).
- **sowing 288-335 (15 Oct - 1 Dec) - ASSUMPTION/analogue.** Official traditional-area window is 20 Nov-30 Jan; at >3,000 m sowing must be earlier to mature before April-May frosts. A World Bank/INIA-Peru search snippet for the southern highlands gives "September to the first half of January". Range DOY 260-15.
- **cycleDays 165 - ASSUMPTION.** No highland-specific figure found; INIAF-Totora is 135 d at 2,000-2,990 m; Peruvian sierra wheat at 3,300-3,800 m matures in 170-200 d (analogue). Range 150-200.

---

## Rows deliberately omitted

- **altiplano / MZ**: INE 2011/12 Oruro 40 ha; La Paz 18,350 ha but concentrated in inter-Andean valleys below 2,800 m (Inquisivi 2,700 m, Larecaja, Yungas); maize "excepcionalmente puede alcanzar los 3.800 metros ... en las orillas aledanas al lago Titicaca" (Avila 2008 in UMSA 2023 l.98-99). Treated as valleys.
- **valleys / RI**: rice in Cochabamba (Chapare) and La Paz (Alto Beni, Caranavi, San Buenaventura) is below 800 m; use the lowland row. Manual chaqueado system parameters (20-40 kg/ha seed, no fertilizer, sown mid-Sep to Nov) are given under row 5.
- **valleys / SB, SG and altiplano / SB, SG, RI**: not grown at meaningful scale (Pasorapa sorghum trials are forage only).
- **primavera** rows: no such campaign in Bolivian practice/statistics.

## Three weakest numbers

1. lowland RI nFertRateRec = 100 (sources span 26-225 kg N/ha; chosen value is a judgement).
2. lowland SG nFertRateAct = 10 (no direct observation of farmer N on sorghum; inferred from crop-ranking statements).
3. altiplano WH sowing window and cycle (288-335 d, 165 d) - built from analogues and frost logic, not Bolivian observations. Close behind: valleys MZ plantingDensity (4.5) and lowland WH nFertRateRec (60), both derived rather than quoted.
