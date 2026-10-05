# Email draft — reply to project lead

**Subject:** Bolivia El Niño — additional data needs for the Tapiti component

---

Hi [name],

Yes — there are a few things, and one correction to the availability sheet that I think matters
for how hard we push.

**The climate data is thinner than the sheet suggests.** Rows 4–5 record "Have data set for
1991-2020 (by month)". I went through all 56 SENAMHI station files we received: they are
monthly, they **all end in 2009 or earlier** (none reach 2010), and **54 of the 56 contain mean
temperature only** — not the daily maxima and minima the crop model needs. The one genuine
1991–2020 monthly series we hold is a single station, El Alto. The gap-free daily file in the
folder is NASA POWER reanalysis aggregated to municipality, not station observations, and it
has no solar radiation.

So rows 4–5 are still very much open, and worth requesting properly rather than treating as
covered.

**Two scope adjustments I'd suggest before we send anything:**

1. Rows 4–5 ask for climate data "by agricultural zones and municipalities". The model runs on
   5-arcminute grid cells, and municipality averages remove exactly the spatial variation it
   uses — and we already hold municipality-level reanalysis. What would actually help is
   **station-level daily data with coordinates**, which lets us correct the gridded data we
   drive the model with.
2. Rows 4–5 start at 1991. I'd ask for **1981**. The two closest historical analogues to what
   is now forecast are 1982/83 and 1997/98; starting at 1991 gives up 1982/83 and 1986/87 and
   leaves us only two strong analogues to composite. INE's yield series starts at 1983-84, so
   1981 lines the two records up.

**Priorities, so the ask doesn't arrive flat.** Only one item actually blocks us: the
**agro-ecological zone map**. The crop calendar they gave us keys every sowing window to a zone
— *valles mesotérmicos*, *área integrada*, *altiplano*, *trópico* — but we have no spatial
definition of those zones, so we cannot place the windows on the map. There is no workaround,
and it should be cheap for them since it underpins their own calendar.

I want to be straight about the rest: solar radiation and station rainfall are **quality
issues, not blockers**. NASA POWER supplies both, and our first end-to-end test run on real
Santa Cruz cells worked on them. The reason to ask is that POWER's radiation sits on a coarse
1° grid and its rainfall over the Andes is uncertain — station data would let us *quantify*
that uncertainty rather than assume it away. Rainfall is the variable carrying the El Niño
signal, so it's worth asking, but we are not stuck without it.

**The item most likely to change our published numbers** is variety and trial data. Our first
test run put maize at roughly 12.8 t/ha against a Bolivian reality nearer 3–5, because the model
is still using cultivar coefficients calibrated for the United States. To fix that properly we
need observed **phenology dates** (flowering, maturity) from variety trials, not just yields —
without them we can match yield levels but not timing, and timing is what determines whether a
rainfall anomaly lands on the crop's critical window. That is the mechanism the whole study
rests on.

**Worth adding to the sheet:** the **Censo Agropecuario 2013** isn't on it, and it covers
fertilizer use, irrigation and farm practices at municipal level with microdata on INE's ANDA
archive. That single dataset fills four gaps in the model's management inputs, which currently
have no Bolivian source at all.

**One question for them, and one for us.** Row 6 asks whether OAP data is downloadable — I
can't answer that, because `oap.produccion.gob.bo` is unreachable from our network entirely
(possibly geo-blocking). Simplest is to ask them to either confirm the download paths or just
extract the municipal series for 2000–2022; we already have 2023–2025. Worth also asking
whether OAP holds it **split by summer/winter campaign** — what we have combines both, and
El Niño hits the summer season specifically.

**And one thing not to re-request:** row 7 (departmental, by campaign, 1984–2025) is already
done — INE publishes it openly and I've downloaded all three tables. Keeping the list short
should help. The only related gap worth raising with INE is that the summer/winter split only
exists from 2012; if pre-2012 campaign data isn't available even unpublished, that becomes a
stated limitation of the historical analysis rather than something to chase.

I've put a forwardable list of the ten requests below, with enough specificity that they can
act on it without coming back to us for clarification. Happy to adjust the framing before it
goes out.

Separately and much more minor: the shared climate folder contains a subdirectory
(`DATOS CLIMATICOS/DATOS SENAMHI/newcpuspeedcheck/`) holding two Windows executables and a zip
that aren't climate data and look like they rode along by accident. Nothing was opened on our
side. Worth a quiet word with whoever packaged the transfer.

Best,
Jawoo

---

## Annex — requests for the Bolivian team (forwardable)

Ordered by priority. Items 1–2 are blocking or affect every subsequent join; 3–6 materially
improve model quality; 7–8 determine how well we can calibrate; 9–10 let us validate results
against what actually happened.

**1. Agro-ecological zone map (GIS, any format — shapefile, KML, or even a georeferenced PDF)**
Boundaries for the zones used in the *calendario agrícola*: *valles mesotérmicos*, *área
integrada*, *altiplano*, *trópico*, *chaco*. Needed to assign each crop's sowing window to the
right location. Likely holder: INIAF or MDRyT (the calendar is credited to INE, INIAF, MDRyT).

**2. INE municipality codes and boundaries**
Please include the **INE municipality code**, not only the name, in every dataset. Two problems
already present in the files we hold: the daily climate file has corrupted accented characters
(`AscensiA3n_de_Guarayos` for *Ascensión de Guarayos*), and it lists 340 municipios while the
agricultural file lists 338 — so joining on names drops records silently. Also the municipal
boundary shapefile, with confirmation of which code vintage matches the agricultural data.

**3. Daily station climate data, 1981–2026**
Per station, not aggregated to municipality or zone: daily **precipitation**, **maximum
temperature** and **minimum temperature**. Plus a separate **station inventory** table: station
name, code, latitude, longitude, elevation, period of record, and percent completeness per
variable. We hold 56 station files with no index, so we cannot tell which are usable without
opening each one.

**4. Solar radiation or sunshine hours**
In order of preference: (a) daily global solar radiation where measured; (b) daily **sunshine
hours / heliofanía**, which we can convert; (c) the *Atlas de Radiación Solar Global de Bolivia*
(UMSS) as a gridded alternative. SENAMHI's SISMET database is documented as holding both
radiation and sunshine hours, and 2 of the 56 files we received already contain radiation.

**5. Censo Agropecuario 2013 — microdata**
Specifically the *insumos* (inputs), *uso de agua para riego* (irrigation) and practices
modules, at municipal level, catalogued at `anda.ine.gob.bo/index.php/catalog/24`. Microdata
rather than published tables, so rates can be computed by crop and department. Access terms
and any request procedure would be useful to know.

**6. Soil data**
Any national soil map and profile database (horizon-by-horizon texture, bulk density, organic
carbon, depth to restrictive layer); any existing **DSSAT-format soil library** for Bolivia, if
an agronomy group has already built one; and ZONISIG or departmental PLUS land-use zoning
studies, which usually carry soil profile descriptions by mapping unit.

**7. Varieties grown, and variety trial data**
Which varieties are actually planted, by crop and region, with approximate area shares and
maturity group or days to maturity. Most importantly, **variety trial records that include
observed phenology dates** — emergence, flowering, maturity — alongside yield, site, year and
management. Likely holders: INIAF, CIAT Santa Cruz, and ANAPO for soybean, maize, sorghum,
wheat and sunflower.

**8. Sowing progress by campaign**
Observed sowing dates or sowing-progress series by campaign and crop, ideally by department.
ANAPO tracks this for Santa Cruz; MDRyT may hold more. This is what lets us verify how sowing
shifts when the rainy season starts late.

**9. Crop loss and affected-area records**
By campaign, municipality and hazard type (drought, flood, hail, frost): VIDECI emergency
declarations and affected-area estimates; MDRyT damage and loss assessments; and loss records
from the *Seguro Agrario Universal (Pachamama)* scheme if accessible.

**10. OAP municipal production series, 2000–2022**
Production, area and yield by crop and municipality. We already hold 2023–2025. Two questions:
can the earlier years be downloaded (we cannot reach `oap.produccion.gob.bo` at all from
outside Bolivia), and is the series available **split by summer and winter campaign** rather
than combined into the agricultural year?
