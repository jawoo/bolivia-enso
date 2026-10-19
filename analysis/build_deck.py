#!/usr/bin/env python3
"""Progress deck for the Bolivia ENSO crop-impact assessment (Tapiti).
Usage: python3 analysis/build_deck.py <figdir> <run_folder> <out.pptx> [baseline_vs_ine.csv]"""
import sys, os, json, numpy as np, pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_TICK_LABEL_POSITION
ROOT = os.path.expanduser('~/Claude/bolivia-enso')
FIG, RUN, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; BASE = sys.argv[4] if len(sys.argv) > 4 else f'{ROOT}/derived/baseline_v4/vs_ine.csv'
P5 = os.environ.get('DECK_PHASE5') == '1'
if P5: os.environ['DECK_PHASE34'] = '1'
DATE = '14 October 2026' if P5 else '5 October 2026'
# ---- palette: forest green primary, sand tint, El Niño orange / La Niña blue accents (same as the charts)
P = {'green': '2C5F2D', 'dark': '1F3A22', 'moss': '97BC62', 'sand': 'EFF0E6', 'ink': '1A1A19', 'muted': '6B6A66', 'grid': 'E4E3DD', 'white': 'FFFFFF',
     'nino': 'EB6834', 'nina': '2A78D6', 'neutral': '9B9A94', 'bad': 'B85042'}
def rgb(k): return RGBColor.from_string(P[k] if k in P else k)
HEAD, BODY = 'Cambria', 'Calibri'
prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5); BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5
def box(s, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, radius=None):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill: sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
    else: sh.fill.background()
    if line: sh.line.color.rgb = rgb(line); sh.line.width = Pt(0.75)
    else: sh.line.fill.background()
    sh.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE: sh.adjustments[0] = radius
    return sh
def text(s, x, y, w, h, runs, size=14, color='ink', bold=False, align=PP_ALIGN.LEFT, font=BODY, anchor=MSO_ANCHOR.TOP, margin=0, line_spacing=None, space_after=None):
    """runs: str | list of paragraphs; a paragraph is str or list of (text, {opts}) runs; opts: bold,color,size,italic,bullet"""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(margin); tf.vertical_anchor = anchor
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        if line_spacing: p.line_spacing = line_spacing
        if space_after is not None: p.space_after = Pt(space_after)
        pruns = para if isinstance(para, list) else [(para, {})]
        for t, o in pruns:
            r = p.add_run(); r.text = t; f = r.font; f.name = o.get('font', font); f.size = Pt(o.get('size', size)); f.bold = o.get('bold', bold); f.italic = o.get('italic', False)
            f.color.rgb = rgb(o.get('color', color))
    return tb
def bullets(s, x, y, w, *args, size=14, color='ink', gap=6):
    h, items = (args[0], args[1]) if len(args) == 2 else (5.0, args[0])
    paras = []
    for it in items:
        if isinstance(it, tuple): paras.append([('•  ', {'color': 'green', 'bold': True}), (it[0], {'bold': True}), (it[1], {})])
        else: paras.append([('•  ', {'color': 'green', 'bold': True}), (it, {})])
    return text(s, x, y, w, h, paras, size=size, color=color, space_after=gap)
def title(s, t, dark=False):
    text(s, 0.6, 0.3, 12.1, 0.95, t, size=26, bold=True, color='white' if dark else 'dark', font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
def footer(s, n, dark=False):
    c = 'moss' if dark else 'muted'
    text(s, 0.6, 7.05, 9, 0.3, f'IFPRI  ·  Bolivia El Niño crop-impact assessment  ·  progress report, {DATE}', size=9, color=c)
    text(s, 12.2, 7.05, 0.55, 0.3, str(n), size=9, color=c, align=PP_ALIGN.RIGHT)
def notes(s, t): s.notes_slide.notes_text_frame.text = t
def image(s, path, x, y, w=None, h=None):
    kw = {}
    if w: kw['width'] = Inches(w)
    if h: kw['height'] = Inches(h)
    return s.shapes.add_picture(path, Inches(x), Inches(y), **kw)
def stat(s, x, y, w, number, label, color='green'):
    text(s, x, y, w, 0.9, number, size=40, bold=True, color=color, font=HEAD, anchor=MSO_ANCHOR.BOTTOM)
    text(s, x, y + 0.92, w, 0.6, label, size=12, color='muted')
def card(s, x, y, w, h, head, body, headcolor='green', size=12):
    box(s, x, y, w, h, fill='sand', shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    text(s, x + 0.2, y + 0.15, w - 0.4, 0.45, head, size=14, bold=True, color=headcolor)
    text(s, x + 0.2, y + 0.62, w - 0.4, h - 0.75, body, size=size, color='ink', space_after=3)
def style_chart(ch, legend=True, label_size=10):
    ch.font.name = BODY; ch.font.size = Pt(label_size); ch.font.color.rgb = rgb('ink')
    ch.has_legend = legend
    if legend: ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(label_size)
    va = ch.value_axis; va.has_major_gridlines = True; va.major_gridlines.format.line.color.rgb = rgb('grid'); va.format.line.fill.background(); va.tick_labels.font.size = Pt(label_size); va.tick_labels.font.color.rgb = rgb('muted')
    ca = ch.category_axis; ca.has_major_gridlines = False; ca.format.line.color.rgb = rgb('grid'); ca.tick_labels.font.size = Pt(label_size); ca.tick_labels.font.color.rgb = rgb('muted')
def colorize(ch, colors):
    for ser, c in zip(ch.plots[0].series, colors):
        ser.format.fill.solid(); ser.format.fill.fore_color.rgb = rgb(c); ser.invert_if_negative = False
        try: ser.format.line.color.rgb = rgb(c)
        except Exception: pass
# ---- data
skill = json.load(open(f'{FIG}/skill_by_crop.json')); natvs = json.load(open(f'{FIG}/national_vs_ine.json')); ens = json.load(open(f'{FIG}/national_anomalies_enso.json')); trends = json.load(open(f'{FIG}/model_trends.json'))
def nat_skill(path):
    x = pd.read_csv(path); n = x.groupby(['crop', 'sow_year']).apply(lambda g: pd.Series({'m': np.average(g.yield_wmean, weights=g.area_ha_ine), 'i': np.average(g.yield_dry, weights=g.area_ha_ine)})).reset_index()
    out = {}
    for c, g in n.groupby('crop'): out[c] = {'ratio': round(g.m.mean() / g.i.mean(), 2), 'r': round(float(np.corrcoef(g.m - g.m.mean(), g.i - g.i.mean())[0, 1]), 2)}
    return out
base = nat_skill(BASE)
CROPS = ['SB', 'MZ', 'RI', 'SG', 'WH']; NAME = {'SB': 'Soya', 'MZ': 'Maíz', 'RI': 'Arroz', 'SG': 'Sorgo', 'WH': 'Trigo'}
import subprocess
_base = subprocess.run(['git', '-C', f'{ROOT}/Tapiti', 'log', '--format=%H', '--grep=Repurpose workspace for Bolivia'], capture_output=True, text=True).stdout.split()
NCOMMITS = str(int(subprocess.run(['git', '-C', f'{ROOT}/Tapiti', 'rev-list', '--count', f'{_base[-1]}..HEAD'], capture_output=True, text=True).stdout.strip()) + 1) if _base else '?'
man = open(f'{RUN}/MANIFEST.md').read(); nrows = [l for l in man.splitlines() if 'rows in merged output' in l][0].split(':')[-1].strip()
n = 0
# ================= 1 Title (dark)
s = prs.slides.add_slide(BLANK); n += 1; box(s, 0, 0, W, H, fill='dark')
text(s, 0.8, 1.9, 11.5, 1.6, 'Simulating El Niño impacts on Bolivian crops', size=44, bold=True, color='white', font=HEAD)
text(s, 0.8, 3.45, 11.5, 0.8, ('Progress report — Phases 1–5 of the Tapiti gridded-DSSAT assessment' if P5 else 'Progress report — Phases 1–4 of the Tapiti gridded-DSSAT assessment') if os.environ.get('DECK_PHASE34') == '1' else 'Progress report — Phases 1 and 2 of the Tapiti gridded-DSSAT assessment', size=22, color='moss')
text(s, 0.8, 5.6, 11, 0.5, f'IFPRI  ·  {DATE}', size=14, color='white')
text(s, 0.8, 6.05, 11, 0.5, 'Tapiti: a Bolivia fork of Tokki, named after the tapití, Bolivia\'s native cottontail', size=12, color='moss')
notes(s, 'Phases 1-5 have a first pass: inputs, calibration, the historical ENSO hindcast, the analogue-driven 2026/27 outlook and the forecast-member ensemble. All numbers are from archived runs named in the manifests.' if P5 else 'Progress report to the project lead. Phases 1 (inputs) and 2 (calibration) are complete; Phase 3 (historical ENSO assessment) starts next. All numbers in this deck are from the archived production run named in the manifest.')
# ================= 2 Why now, what we are building
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Why now: the season this El Niño will hit is being sown this month'); footer(s, n)
bullets(s, 0.6, 1.45, 6.4, 3.2, [
    ('CPC El Niño Advisory (Sep 2026): ', '>90% chance of a very strong event; Niño-1+2 at +3.4 °C, the eastern-Pacific signature of 1982/83, 1997/98 and 2015/16'),
    ('Campaña verano sows Sep–Dec: ', 'maíz and arroz from September, soya from November — the exposure window is Oct–Apr'),
    ('Deliverable 1 (weeks): ', 'a historical-analogue product — what happened to simulated and observed yields in past El Niño campaigns'),
    ('Deliverable 2 (separable): ', 'a forward estimate for 2026/27 driven by analogue weather and seasonal forecasts')], size=13)
box(s, 7.4, 1.45, 5.3, 4.9, fill='sand', shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
text(s, 7.7, 1.6, 4.8, 0.4, 'The Tapiti hindcast, by the numbers', size=13, bold=True, color='green')
stat(s, 7.7, 2.0, 2.3, '5', 'crops: soya, maíz, arroz, sorgo, trigo'); stat(s, 10.1, 2.0, 2.3, '3,469', '5-arcmin grid cells')
stat(s, 7.7, 3.6, 2.3, '42', 'campaigns, 1983/84 – 2024/25'); stat(s, 10.1, 3.6, 2.3, f'{int(nrows.replace(",", ""))//1000}k', 'DSSAT seasons per run')
text(s, 7.7, 5.3, 4.8, 0.9, 'Weather per cell from NASA POWER (MERRA-2), soils from ISRIC SoilGrids + HC27, areas from MapSPAM 2020, calibration against INE departmental statistics 2012–2024.', size=11, color='muted')
notes(s, 'Timing drives the plan: a retrospective product in March 2027 describes a harvest that has already happened, so the historical analogue product comes first. The forward estimate is a second, separable stage.')
# ================= 2b Season so far (Phase 5 deck)
if P5 and os.path.exists(f'{ROOT}/derived/season_progress/summary.json'):
    SP = json.load(open(f'{ROOT}/derived/season_progress/summary.json')); zs = SP['zones']; lo = pd.Timestamp(SP['last_obs'])
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'This season so far: wet start in the highlands, ordinary in the lowlands'); footer(s, n)
    image(s, f'{ROOT}/derived/season_progress/figures/chart_season_progress.png', 0.5, 1.3, w=12.3)
    bullets(s, 0.6, 5.45, 12.1, 1.5, [(f'Rain since 1 September, to {lo.day} {lo.strftime("%B")}: ', f"Altiplano {zs['altiplano']['mm']} mm (rank {zs['altiplano']['rank_wettest']} of {SP['n_past'] + 1} campaigns at this date; El Niño median {zs['altiplano']['median_El Niño']} mm), valleys {zs['valleys']['mm']} mm (rank {zs['valleys']['rank_wettest']}), lowlands {zs['lowland']['mm']} mm, near the middle of the record"),
        ('A wet September in the highlands is not evidence against the El Niño outlook: ', f"1997/98 began the same way (Altiplano {zs['altiplano']['mm_1997']} mm at this date) and the El Niño deficit arrives with the main rains, December to March"),
        ('The lines fan out from November: ', 'the campaign is decided in the next five months, which is what the forecast slides address')], size=11, gap=3)
    notes(s, 'Figure: analysis/season_progress_chart.py. Zone rainfall = NASA POWER cell rainfall averaged over the modelled cells, weighted by MapSPAM crop area; each line is one campaign from 1 September; phase = DJF ONI of the campaign; thick lines are phase medians. Observed data to the last POWER day (lag of about a week).')
# ================= 2c What the science says now (Phase 5 deck)
if P5 and os.path.exists(f'{ROOT}/derived/enso_state/summary.json'):
    ES = json.load(open(f'{ROOT}/derived/enso_state/summary.json')); lwk = ES['last_weekly']; lwd = pd.Timestamp(lwk['date']); lmo = ES['last_monthly']; sp = ES['same_month_past']
    lmon = pd.Timestamp(year=lmo['year'], month=lmo['month'], day=1).strftime('%B'); pm = lambda v, d=1: f'{v:+.{d}f}'.replace('-', '−')
    sen97 = pd.read_csv(f'{ROOT}/derived/phase3/senamhi_novmar_anomalies.csv'); sen97 = sen97[sen97.sow_year == 1997].dropna().groupby('zone').anom_pct.mean()
    yc = pd.read_csv(f'{ROOT}/derived/phase3/yield_composites_simulated.csv'); yc = yc[(yc.departamento == 'Bolivia') & (yc.zone == 'all') & yc.phase.str.startswith('strong EP')].set_index('crop').mean_anom_pct
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'What the science says today: a record El Niño of the 1997/98 type'); footer(s, n)
    text(s, 0.6, 1.2, 12.1, 0.3, 'Status at 18 October 2026 from the operational centres and published analyses. Quotes are verbatim; links in the notes.', size=11, color='muted')
    image(s, f'{ROOT}/derived/enso_state/figures/chart_nino_indices_2026_vs_analogues.png', 0.5, 1.55, w=6.15)
    def qcard(y, head, body, h=0.96, headcolor='green'):
        box(s, 6.9, y, 5.85, h, fill='sand', shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
        text(s, 7.05, y + 0.05, 5.6, 0.28, head, size=10.5, bold=True, color=headcolor)
        text(s, 7.05, y + 0.31, 5.6, h - 0.34, body, size=9.5, color='ink')
    qcard(1.55, 'NOAA Climate Prediction Center, 8 October', [[('“El Niño continues to strengthen, with a strong-to-very strong El Niño likely through January–March 2027.” ', {}),
        ('Niño-3.4 +2.1 °C, Niño-1+2 +3.9 °C in September; an 83% chance that October–December exceeds every event on record since 1950.', {'color': 'muted'})]])
    qcard(2.57, 'WMO Global Seasonal Climate Update, 8 October', [[('Niño-3.4 “forecast to reach approximately +3.7 °C during OND 2026, with the warming trend peaking around December”; “the spread among individual forecast systems generally remains narrow, reflecting high forecast confidence.” ', {}),
        ('Near-100% likelihood that El Niño persists through February 2027.', {'color': 'muted'})]])
    qcard(3.59, 'Columbia Climate School / IRI, 1 October', [[('A. Robertson: “We’ve never seen a forecast like this one in terms of certainty. This sort of magnitude is also unprecedented.” ', {}),
        ('M. A. Ehsan: all 22 models point to a very strong El Niño from September through February 2027; projected peak +3.4 °C (Nov–Jan) against +2.4 °C in 1997/98.', {'color': 'muted'})]])
    qcard(4.61, 'The caution the same community attaches', [[('NOAA (M. L’Heureux): “even if this ends up being a historic El Niño, there will be impacts in some locations that do not align with the expected El Niño impact.” ', {}),
        ('Carbon Brief (Z. Hausfather, 21 Sep): “No seasonal forecast system has ever been verified against an event of this size, because none has ever occurred.”', {'color': 'muted'})]], headcolor='nino')
    qcard(5.63, 'Regional services', [[('ENFEN (Peru), communiqué 18-2026, 16 October: El Niño costero of “extraordinary” magnitude through January 2027, easing to “strong” by autumn. ', {}),
        ('SENAMHI (Bolivia), July–August: a “Niño muy fuerte” peaking Oct–Dec; “en el sector del altiplano vamos a tener presencia de sequía y en el sector del oriente … más precipitaciones”; critical phase November to January.', {'color': 'muted'})]], h=1.1)
    text(s, 0.6, 5.5, 6.0, 0.3, 'Reading for Bolivia', size=11, bold=True, color='green')
    bullets(s, 0.6, 5.8, 6.0, 1.25, [
        (f'Ocean: ', f'at the same date, 2026 is past 1997/98 on both indices (Niño-3.4 {pm(lmo["a34"])} vs {pm(sp["1997"]["a34"])} °C, Niño-1+2 {pm(lmo["a12"])} vs {pm(sp["1997"]["a12"])} °C in {lmon}); the eastern-Pacific signature is the one that, in the record, cuts Bolivian verano yields'),
        ('Atmosphere over Bolivia: ', 'too early to call; the campaign\'s rain falls from November and no system has been tested on an event this size'),
        ('So the next section asks what the eastern-Pacific campaigns did: ', f'1997/98 stations {pm(sen97["altiplano"], 0)}% Nov–Mar rain in the Altiplano, {pm(sen97["valleys"], 0)}% valleys; simulated soya {pm(yc["SB"], 0)}%, maíz {pm(yc["MZ"], 0)}%, arroz {pm(yc["RI"], 0)}% over 1997/98, 2015/16, 2023/24')], size=9.5, gap=2)
    notes(s, 'Sources (all accessed 18 October 2026). NOAA CPC ENSO Diagnostic Discussion, 8 Oct 2026: https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_disc_oct2026/ensodisc.shtml (next update 12 Nov). WMO Global Seasonal Climate Update OND 2026, 8 Oct: https://wmo.int/resources/publication-series/global-seasonal-climate-updates/gscu-ond2026 ; WMO news 16 Oct (World Food Day): https://wmo.int/media/news/el-nino-looms-large-world-food-day . Columbia Climate School, 1 Oct 2026, "El Niño 2026: how big could it get?": https://news.climate.columbia.edu/2026/10/01/el-nino-2026-how-big-could-it-get/ . NOAA quotes: ABC News, 13 Aug 2026 (M. L\'Heureux, CPC). Carbon Brief, Z. Hausfather, 21 Sep 2026: https://www.carbonbrief.org/analysis-super-el-nino-reaches-remarkable-all-time-record . ENFEN comunicado oficial 18-2026, 16 Oct 2026 (via Latin Times) and 14 Aug 2026 (via RPP). SENAMHI Bolivia: H. Quisbert, 14 Jul 2026 (FM La Paz); K. Quisberth, 3 Aug 2026 updated 18 Oct (FM Bolivia). Figure: analysis/enso_state_chart.py from CPC sstoi.indices (monthly OISST, 1991-2020 base) and wksst9120.for (weekly). Point of divergence to handle in discussion: SENAMHI\'s public line is a wetter oriente in Oct-Dec; the Phase 3 record for the three strong eastern-Pacific campaigns shows the lowlands drier and hotter in the verano (POWER -17% rain, stations -9% in 1997/98) and wetter only in the invierno build-up. The 1982/83 line in the chart pre-dates the simulated record and is shown for the ocean comparison only.')
# ================= 3 Status timeline
s = prs.slides.add_slide(BLANK); n += 1; title(s, ('Where we are: all five phases have a first pass; updates are next' if P5 else 'Where we are: all four phases have a first pass; the update loop is next') if os.environ.get('DECK_PHASE34') == '1' else 'Where we are: inputs and calibration done, ENSO assessment next'); footer(s, n)
phases = [('Phase 0', 'Scaffold', 'Fork Tokki → Tapiti; smoke test on real cells', 'done'), ('Phase 1', 'Inputs', 'Weather, soil, management, cultivars, unit table', 'done'),
          ('Phase 2', 'Calibration', 'Boundary conditions and yield levels vs INE', 'done'), ('Phase 3', 'ENSO hindcast', 'Composites by ENSO phase, 1983–2024', 'done' if os.environ.get('DECK_PHASE34') == '1' else 'next'), ('Phase 4', 'Forward 2026/27', 'Analogue weather + seasonal forecasts', 'done' if os.environ.get('DECK_PHASE34') == '1' else 'later')]
if P5: phases[4] = ('Phase 4', 'Outlook 2026/27', 'Analogue weather + seasonal forecasts', 'done'); phases.append(('Phase 5', 'Forecast members', '51 ECMWF members drive DSSAT, beside the analogues', 'done'))
x0 = 0.6; wcol = (12.1 - 0.08 * (len(phases) - 1)) / len(phases)
for i, (ph, nm, d, st) in enumerate(phases):
    x = x0 + i * (wcol + 0.08); col = {'done': 'green', 'next': 'nino', 'later': 'neutral'}[st]
    box(s, x, 1.6, wcol, 0.08, fill=col); text(s, x, 1.8, wcol, 0.35, ph, size=11, color='muted'); text(s, x, 2.1, wcol, 0.5, nm, size=15 if P5 else 20, bold=True, color='dark', font=HEAD)
    text(s, x, 2.65, wcol, 1.0, d, size=12, color='ink'); text(s, x, 3.7, wcol, 0.35, ({'done': 'First pass complete', 'next': 'Starting now', 'later': 'Planned'}[st] if i >= 3 else {'done': 'Complete', 'next': 'Starting now', 'later': 'Planned'}[st]), size=11, bold=True, color=col)
text(s, 0.6, 4.5, 12.1, 0.4, 'What changed since the plan was written', size=14, bold=True, color='green')
bullets(s, 0.6, 4.9, 12.1, 2.0, [
    'The tool is now Tapiti (github.com/jawoo/Tapiti): a renamed fork of Tokki with the US-only material removed, ' + NCOMMITS + ' commits of Bolivia-specific changes, every run archived with a manifest',
    'Two inherited assumptions had to be reworked before calibration made sense: how rice is grown, and when a season starts (slides 7–8)',
    'Soya — 1.4 Mha and the Santa Cruz economy — turns out to be the crop the water-balance model explains least (slide 12)'] + (['Weather sources settled after a check against 18 SENAMHI stations: NASA POWER for the observed record, the 51 ECMWF forecast members (EC46 then SEAS5) for the season ahead (slide 20)'] if P5 else []), size=12)
notes(s, 'Phase 2 is closed as a calibration round; it can be reopened if Phase 3 shows a specific weakness. Potato and quinoa remain out of scope (no module wired / no DSSAT module).')
# ================= 4 Spatial frame maps
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'The spatial frame: 3,469 cells, five crops, three zones'); footer(s, n)
image(s, f'{FIG}/map_cells_dominant_crop.png', 0.5, 1.4, h=5.3); image(s, f'{FIG}/map_zones.png', 5.9, 1.4, h=5.3)
text(s, 0.6, 6.7, 10.5, 0.3, 'Cells: MapSPAM 2020 harvested area ≥25 ha. Zones: cell-mean elevation from the NASA POWER DEM. Boundaries: geoBoundaries ADM1.', size=9, color='muted')
bullets(s, 11.1, 1.5, 2.0, 5.3, ['Cells with ≥25 ha of an in-scope crop in MapSPAM 2020', 'Soya and sorgo in the Santa Cruz plain; maíz in the valleys; trigo valleys and Altiplano; arroz in Beni and the Norte Integrado',
                              'Zone by cell elevation sets season, management class and cultivar', '141 rice/soya records above 2,800 m dropped as MapSPAM allocation errors'], size=10, gap=4)
notes(s, 'MapSPAM totals match INE national areas (soya 1.39 Mha, maize 0.42, sorghum 0.44, wheat 0.18, rice 0.17). The municipal cross-check of MapSPAM against INE 2023-25 municipal data is still to do.')
# ================= 5 Inputs table
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 1 inputs: what was built and where it is weak'); footer(s, n)
rows = [('Weather', 'NASA POWER (MERRA-2 0.5°) daily per cell, 1981–2026; 1981–83 radiation estimated from temperature range', 'Reanalysis rainfall in complex terrain; 0.5° grid vs 5-arcmin cells'),
        ('Soil', 'ISRIC SoilGrids + HC27 profiles, the same library as the US work; 10 edge cells filled from neighbours', 'Rooting depth 200 cm everywhere; organic carbon drives mineralised N'),
        ('Management', 'Zone × crop × season table from ANAPO, CIAT, INIAF, MDRyT, CIPCA, Censo 2013, FAOSTAT — sources documented figure by figure', 'No national survey; rows marked "fill" copy a neighbour; sowing windows capped by a model limit'),
        ('Seasons', 'Dominant campaign per department from INE 2012–24: verano for soya/rice, invierno for Santa Cruz sorgo and trigo, verano for highland trigo', 'One season per crop per cell; soya invierno (23%) not simulated'),
        ('Cultivars', 'Explicit per cell: Bolivia zone cultivars for maíz, arroz, sorgo; DSSAT generics for soya (MG 8) and trigo', 'Level-calibrated, not variety-specific; trigo uncalibrated (slide 9)')]
ys = 1.45
text(s, 0.6, ys, 1.7, 0.35, 'Component', size=11, bold=True, color='muted'); text(s, 2.4, ys, 6.2, 0.35, 'What was built', size=11, bold=True, color='muted'); text(s, 8.8, ys, 3.9, 0.35, 'Known weakness', size=11, bold=True, color='muted')
for i, (a, b, c) in enumerate(rows):
    y = ys + 0.42 + i * 1.02; box(s, 0.6, y - 0.08, 12.1, 0.02, fill='grid')
    text(s, 0.6, y, 1.7, 0.9, a, size=13, bold=True, color='green'); text(s, 2.4, y, 6.2, 0.95, b, size=11); text(s, 8.8, y, 3.9, 0.95, c, size=11, color='muted')
notes(s, 'Everything is reproducible from scripts in the workspace: prep/gen_weather_bolivia.py, build_soil_bolivia.py, build_unit_information_bolivia.py; sources in derived/SOURCES-management.md.')
# ================= 6 Tapiti changes
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Tapiti: four inherited assumptions that did not transfer from the US'); footer(s, n)
cards = [('Rice was paddy', 'Tokki wrote every rice run as transplanted, puddled, flooded paddy. Bolivian rice is ~90% direct-seeded secano. Tapiti adds an upland mode; rainfed rice now runs like any rainfed crop.', 'riceSystem: upland'),
         ('The wrong N column', 'With the override on, Tokki applies the recommended N rate and never reads the farmer rate. A hindcast needs farmer practice.', 'nitrogenRateSource: actual'),
         ('Seasons started on 1 January', 'A verano crop sat behind ten months of bare fallow in which soil carbon mineralised 150–250 kg N/ha that nothing took up. Tapiti starts 60 days before sowing with explicit initial soil water and mineral N.', 'simulationStartDaysBeforePlanting: 60  ·  initialSoilWaterFraction: 0.5  ·  initialSoilN: 0.3/0.7 ppm'),
         ('US cultivars', 'The US-calibrated maize generics have kernel number and fill rate 25–65% above stock DSSAT. Bolivia zone cultivars replace them for maíz, arroz and sorgo.', 'BOL LOWLAND · BOL VALLEYS · BOL ALTIPLANO · BOL SECANO · BOL GRANIFERO')]
for i, (h, b, k) in enumerate(cards):
    x = 0.6 + (i % 2) * 6.15; y = 1.45 + (i // 2) * 2.7; card(s, x, y, 5.95, 2.5, h, b, size=13)
    text(s, x + 0.2, y + 1.95, 5.55, 0.4, k, size=10, color='muted', font='Consolas')
text(s, 0.6, 6.95-0.3, 12.1, 0.3, 'Every switch defaults to upstream behaviour, so Tokki results stay reproducible from the same code.', size=11, color='muted')
notes(s, 'All four are config switches defaulting to upstream behaviour, so Tokki results are reproducible from the same code. The N-column finding also applies to the US production run.')
# ================= 7 Levels before/after (native bar chart)
s = prs.slides.add_slide(BLANK); n += 1; within10 = sum(1 for c in CROPS if abs(skill[c]['ratio'] - 1) <= 0.10); title(s, f'Yield levels: from 2–2.5× too high to within 10% for {["zero","one","two","three","four","five"][within10]} of five crops'); footer(s, n)
cd = CategoryChartData(); cd.categories = [NAME[c] for c in CROPS]; cd.add_series('Inherited setup (first run)', [base[c]['ratio'] for c in CROPS]); cd.add_series('Phase 2 reference run', [skill[c]['ratio'] for c in CROPS])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.7), Inches(7.6), Inches(5.1), cd); ch = gf.chart; style_chart(ch); colorize(ch, ['neutral', 'green'])
ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 3.0; ch.value_axis.major_unit = 0.5; ch.plots[0].gap_width = 60; ch.plots[0].has_data_labels = True; ch.plots[0].data_labels.font.size = Pt(10); ch.plots[0].data_labels.number_format = '0.00'; ch.plots[0].data_labels.number_format_is_linked = False; ch.plots[0].data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
text(s, 0.6, 1.35, 7.6, 0.3, 'Simulated ÷ observed national yield, dry matter, sowing years 2012–2024 (1.0 = INE level)', size=11, color='muted')
bullets(s, 8.6, 1.5, 4.2, [
    ('What was wrong: ', 'the 1 January start, not the management table. Starting 60 days before sowing halved mineralised N and removed most of the bias on its own (60-cell sensitivity, 14 setups).'),
    ('Then cultivars: ', f'yield components set against INE by zone on department samples. Maíz is {skill["MZ"]["ratio"]:.2f} nationally but ~1.0 in Santa Cruz, Tarija, Beni and Pando; the excess is in valley and Altiplano departments whose 1.0–1.3 t/ha the model does not reach down to.'),
    ('Trigo stays 1.7×: ', 'no genetic coefficient tested moves it. Blast, hail, frost and poor stands are the missing processes; handled as a bias factor, not hidden.'),
    ('Soya was right from the start ', '(it fixes its own N) — which is why its level never moved.')], size=11, gap=5)
notes(s, 'The sensitivity table is in PLAN.md 7.3. Initial mineral N is a strong lever once the fallow is short, and its unit matters: 1 ppm over a 2 m profile is about 27 kg N/ha. The adopted default is 0.3/0.7 ppm.')
# ================= 8 Anomaly skill (native bar chart)
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Year-to-year skill: the weather signal is live for the lowland crops'); footer(s, n)
cd = CategoryChartData(); cd.categories = [NAME[c] for c in CROPS]; cd.add_series('Inherited setup', [base[c]['r'] for c in CROPS]); cd.add_series('Phase 2 reference run', [skill[c]['r'] for c in CROPS])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.7), Inches(7.6), Inches(5.1), cd); ch = gf.chart; style_chart(ch); colorize(ch, ['neutral', 'green'])
ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 1.0; ch.value_axis.major_unit = 0.2; ch.plots[0].gap_width = 60; ch.plots[0].has_data_labels = True; ch.plots[0].data_labels.font.size = Pt(10); ch.plots[0].data_labels.number_format = '0.00'; ch.plots[0].data_labels.number_format_is_linked = False; ch.plots[0].data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
text(s, 0.6, 1.35, 7.6, 0.3, 'Correlation of simulated and INE national yield anomalies, 12–13 overlapping years', size=11, color='muted')
bullets(s, 8.6, 1.5, 4.2, [
    ('Sorgo and trigo in Santa Cruz ', f'track INE at {skill["SG"]["r"]:.2f} and {skill["WH"]["r"]:.2f} — the invierno crops read the autumn rainfall right'),
    ('Arroz ', f'improved to {skill["RI"]["r"]:.2f}; maíz slipped from {base["MZ"]["r"]:.2f} to {skill["MZ"]["r"]:.2f} as its level was fixed — twelve years cannot say whether that is real, and valley and Altiplano maize carry almost no signal'),
    ('Soya is the weak crop ', f'({skill["SB"]["r"]:.2f}) despite the right level — slide 12 explains why'),
    ('Caveat: ', 'twelve years is a short record; these correlations have wide intervals and say the mechanism is live, not that the model is validated')], size=11, gap=5)
notes(s, 'Level calibration kept skill for rice, sorghum and wheat. Soya drifted down (0.37 to 0.28) with the shorter pre-season and maize from 0.61 to 0.42 across the two calibration rounds; a factorial on 300 Santa Cruz maize cells gave anomaly correlations of 0.30-0.41 for every combination of start date and cultivar, i.e. within the noise of 12 years. Phase 3 tests the anomaly response on the 42-year record against ENSO, not only against 12 years of INE.')
# ================= 9 Time series (two native line charts)
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Model against INE, 2012–2024: sorgo and maíz'); footer(s, n)
for i, c in enumerate(['SG', 'MZ']):
    d = natvs[c]; cd = CategoryChartData(); cd.categories = [f'{y}/{str(y+1)[2:]}' if c != 'SG' else str(y) for y in d['years']]
    cd.add_series('INE (converted to dry matter)', d['ine']); cd.add_series('Tapiti', d['model'])
    gf = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.6 + i * 6.25), Inches(1.75), Inches(5.9), Inches(4.5), cd); ch = gf.chart; style_chart(ch); colorize(ch, ['ink', 'green'])
    for ser in ch.plots[0].series: ser.smooth = False; ser.format.line.width = Pt(2.25); ser.marker.size = 7
    ch.value_axis.minimum_scale = 0; ch.has_title = True; ch.chart_title.text_frame.text = f"{NAME[c]}, kg/ha dry matter — ratio {d['ratio']}, r {d['r']}"; ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(12); ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
text(s, 0.6, 1.2, 12.1, 0.5, 'Sorgo invierno is the cleanest test: sown Apr–Jun on residual moisture, its 2016 and 2021–22 collapses are reproduced. Maíz verano follows the same drought years (2015/16, 2023/24) with less fidelity in the valleys.', size=12, color='muted')
text(s, 0.6, 6.35, 12.1, 0.5, 'INE departmental series exist only from 2012; the 1984–2011 series needed for a longer validation has been requested.', size=11, color='muted')
notes(s, 'Sowing-year labels: a verano campaign sown in 2015 is 2015/16; invierno sorghum is labelled by its calendar year.')
# ================= 10 Maps El Niño years
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'The model sees the El Niño droughts in the Santa Cruz plain'); footer(s, n)
image(s, f'{FIG}/map_anom_maize_elnino_years.png', 0.5, 1.4, w=12.3)
text(s, 0.6, 5.5, 12.1, 1.2, 'Simulated maíz yield anomaly per cell in the three strong eastern-Pacific El Niño campaigns since 1983. Santa Cruz loses 20–60%; the Altiplano and valleys show a weaker and sometimes opposite response, consistent with the literature\'s "drier highlands, wetter/variable lowlands" picture only in part — Phase 3 tests this properly, per crop and per zone.', size=12, color='ink')
notes(s, 'Anomalies are relative to each cell\'s own 1983–2024 mean. 1982/83 is outside the simulated record (weather starts 1981, sowing 1983).')
# ================= 11 ENSO preview
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Preview: strong El Niño campaigns are the lowest simulated maíz years'); footer(s, n)
image(s, f'{FIG}/chart_enso_preview.png', 1.2, 1.3, w=10.9)
text(s, 0.6, 6.35, 12.1, 0.6, f'Detrended national anomalies vs the DJF Oceanic Niño Index. Simulated soya carries a downward trend of {abs(trends["SB"]):.1f}% per year linked to rising maximum temperatures in the reanalysis, which INE does not show — a Phase 3 check before any composite is quoted.', size=11, color='muted')
notes(s, 'This is a preview, not the Phase 3 result: composites by ENSO phase with uncertainty, per crop and department, come next. Note the asymmetry: La Niña campaigns are mildly positive for maize (wetter Santa Cruz), strong El Niño strongly negative.')
# ================= 12 Soya diagnosis (native bar chart)
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Soya: right level, wrong weather response — a structural limit'); footer(s, n)
ind = pd.read_csv(f'{ROOT}/derived/soya_scz_climate_indicators_1983-2024.csv').set_index('sow_year')
cy = pd.read_csv([p for p in os.listdir(RUN) if p.startswith('combinedOutput_cellyear')] and f'{RUN}/' + [p for p in os.listdir(RUN) if p.startswith('combinedOutput_cellyear')][0])
sb = cy[(cy.CropCode == 'SB') & (cy.departamento == 'Santa Cruz')]; m = sb.groupby('sow_year').apply(lambda g: np.average(g.yield_kg_ha, weights=g.area_ha.fillna(0))).rename('model')
t = ind.join(m).dropna(subset=['ine_sb_scz_kg_ha', 'model']); labs = [('rain_nov_mar', 'Season rainfall total'), ('wetdays50', 'Days with > 50 mm'), ('dry10', '10-day dry spells'), ('hot35', 'Days with Tmax > 35 °C')]
cd = CategoryChartData(); cd.categories = [l for _, l in labs]; cd.add_series('Observed (INE Santa Cruz soya)', [round(float(t[k].corr(t.ine_sb_scz_kg_ha)), 2) for k, _ in labs]); cd.add_series('Simulated (Tapiti)', [round(float(t[k].corr(t.model)), 2) for k, _ in labs])
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.7), Inches(7.4), Inches(4.9), cd); ch = gf.chart; style_chart(ch); colorize(ch, ['ink', 'green'])
ch.value_axis.minimum_scale = -0.8; ch.value_axis.maximum_scale = 0.8; ch.value_axis.major_unit = 0.4; ch.plots[0].gap_width = 60; ch.plots[0].has_data_labels = True; ch.plots[0].data_labels.font.size = Pt(10); ch.plots[0].data_labels.number_format = '0.00'; ch.plots[0].data_labels.number_format_is_linked = False
ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
text(s, 0.6, 1.35, 7.4, 0.3, f'Correlation of Santa Cruz soya yield with Nov–Mar weather indicators, sowing years 2012–2023 (n = {len(t)})', size=11, color='muted')
bullets(s, 8.4, 1.5, 4.4, [
    ('Observed soya ', 'is indifferent to rainfall total and loses to heavy-rain days, dry spells and heat'),
    ('Simulated soya ', 'loves rainfall and gains from wet days; it gets dry spells and heat right'),
    ('Why: ', 'the water-balance model has no waterlogging or harvest-loss channel, and the deep HC27 profiles never saturate — a 1 m rooting depth and slow drainage did not change the sign'),
    ('For Phase 3: ', 'use the model for the drought and heat channels and add a statistical excess-rain term fitted on the INE overlap, reported separately and labelled as such')], size=11, gap=5)
notes(s, 'Twelve points; indicative, not significant. The conclusion is about mechanism, not sample size: the lowland El Niño impact on soya runs through excess water, which DSSAT handles poorly, as the plan said from the start.')
# ================= 11b Phase 3 headline (optional, env DECK_PHASE3=1)
if (os.environ.get('DECK_PHASE3') == '1' or os.environ.get('DECK_PHASE34') == '1') and os.path.exists(f'{ROOT}/derived/phase3/figures/chart_phase_composites_national.png'):
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 3, first pass: the signal is in the strong eastern-Pacific events'); footer(s, n)
    image(s, f'{ROOT}/derived/phase3/figures/chart_phase_composites_national.png', 0.5, 1.4, w=12.3)
    bullets(s, 0.6, 4.75, 12.1, 2.1, [
        ('El Niño as a class does nothing to the verano crops ', '(soya, maíz, arroz within ±2% of neutral over 14 campaigns); the three eastern-Pacific analogues 1997/98, 2015/16 and 2023/24 cost them 18–20% nationally, intervals excluding zero'),
        ('The invierno crops gain during the El Niño build-up: ', 'sorgo +26%, trigo +13% in the winter before the peak; the developing La Niña costs sorgo −15%. The observed record agrees where it overlaps: 2023/24 matches on every crop'),
        ('Central-Pacific events (1991/92, 2009/10) are not drought years ', 'in the data or the model — the 2026/27 event (Niño-1+2 ≈ +3.4 °C) must be read against the EP analogues only'),
        ('SENAMHI stations confirm the El Niño drying of the Altiplano (−11%) ', 'that the reanalysis only half reproduces; the highlands stay unresolved by this tool')], size=11, gap=4)
    notes(s, 'Full report: documents/Phase3-ENSO-hindcast_2026-10-05.md. Detrended national anomalies, bootstrap intervals over years within phase. The strong-EP composites rest on three events; report them as what happened in those campaigns, not as a climatological expectation.')
if os.environ.get('DECK_PHASE34') == '1':
    P3F = f'{ROOT}/derived/phase3/figures'; P4F = f'{ROOT}/derived/phase4/figures'
    # --- weather check
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 3: the El Niño signal in observed weather and in the model input'); footer(s, n)
    image(s, f'{P3F}/chart_weather_composites_rain.png', 2.0, 1.3, w=9.3)
    bullets(s, 0.6, 5.35, 12.1, 1.5, [('29 SENAMHI stations (1970–2009): ', 'El Niño campaigns are drier in the Altiplano (−11%, interval excluding zero) and valleys (−5%), not in the lowlands; La Niña is wetter everywhere; 1997/98 alone was −35% in the Altiplano'),
        ('The reanalysis that drives the model reproduces half of the Altiplano deficit ', '(−5%), so highland results are conservative; in both datasets the signal is carried by the strong eastern-Pacific events (−17 to −19% in every zone), not by El Niño as a class')], size=11, gap=4)
    notes(s, 'Checked before compositing yields, as the plan required. POWER is MERRA-2 at 0.5 degrees, which smooths the Andes. Station records end in 2009, so the station strong-EP bar is the 1997/98 event alone.')
    # --- strong EP maps
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 3: where the strong eastern-Pacific losses and gains sit'); footer(s, n)
    image(s, f'{P3F}/map_strongEP_composite_by_crop.png', 0.5, 1.5, w=12.3)
    text(s, 0.6, 5.3, 12.1, 1.4, 'Mean detrended yield anomaly per cell over 1997/98, 2015/16 and 2023/24. Soya, maíz and arroz lose across the Santa Cruz plain and the Chiquitanía; sorgo and trigo, the invierno crops sown while the El Niño was building, gain there. Altiplano maíz shows the opposite sign — the model is cold-limited there and the reanalysis under-represents the drying, so that sign is unresolved, not a result.', size=12)
    notes(s, 'Composite of three events; intervals in the report. The invierno gain is the developing-El Niño winter (April–June of the onset year), not the winter after the peak.')
    # --- Phase 4: SEAS5
    S5 = '2026-10' if P5 else '2026-09'; S5M = {'2026-10': 'October', '2026-09': 'September'}[S5]
    zm = pd.read_csv(f'{ROOT}/derived/phase4/seas5_{S5}_zone_member_anomalies.csv'); zz = zm.groupby('zone').agg(tp=('tp_anom_pct', 'mean'), tp10=('tp_anom_pct', lambda v: np.percentile(v, 10)), tp90=('tp_anom_pct', lambda v: np.percentile(v, 90)), t=('t2m_anom', 'mean'), dry=('tp_anom_pct', lambda v: (v < 0).mean()))
    aw = pd.read_csv(f'{ROOT}/derived/phase4/analogue_weights_{S5}.csv'); w_ep = aw[aw.strong_EP_analogue].weight.sum(); w_en = aw[aw.category.str.contains('El Niño')].weight.sum(); w_ln = aw[aw.category.str.contains('La Niña')].weight.sum()
    s = prs.slides.add_slide(BLANK); n += 1; title(s, f'Phase 4: what the {S5M} SEAS5 forecast says for Nov–Mar 2026/27'); footer(s, n)
    image(s, f'{P4F}/chart_seas5_{S5}_vs_analogues.png', 1.2, 1.35, w=10.9)
    dry_txt = 'every member' if zz.loc['altiplano', 'dry'] == 1 else f"{zz.loc['altiplano', 'dry']:.0%} of members"
    bullets(s, 0.6, 5.5, 12.1, 1.4, [('51 ECMWF members: ', f"Altiplano rainfall {zz.loc['altiplano', 'tp']:+.0f}% with {dry_txt} dry (80% between {zz.loc['altiplano', 'tp10']:.0f} and {zz.loc['altiplano', 'tp90']:.0f}%), valleys {zz.loc['valleys', 'tp']:+.0f}%, lowlands {zz.loc['lowland', 'tp']:+.0f}% with a wide spread; temperatures {zz.t.min():+.1f} to {zz.t.max():+.1f} °C across the zones"),
        ('In the lowlands and valleys the members cluster around 1997/98 and 2015/16; ', 'in the Altiplano the forecast is drier and warmer than any campaign since 1983 — beyond what the analogue method can represent there'),
        ('Each past campaign is weighted by its closeness to the members: ', f'{w_ep:.0%} of the weight falls on 1997/98, 2015/16 and 2023/24, {w_en:.0%} on El Niño campaigns, {w_ln:.0%} on La Niña')], size=11, gap=3)
    notes(s, f'SEAS5 system 51, initialised {S5M} 2026, monthly anomalies relative to its own hindcast climatology; precipitation scaled by the POWER Nov-Mar mean; T2m matched to POWER Tmax. Weights are a Gaussian kernel on standardised distance, averaged over members. Refreshed on each monthly release.')
    # --- Phase 4: outlook (native chart + callouts)
    cdp = pd.read_csv(f'{ROOT}/derived/phase4/analogue_ensemble_conditional.csv'); natp = cdp[(cdp.departamento == 'Bolivia') & (cdp.zone == 'all')]
    nw = pd.read_csv(f'{ROOT}/derived/phase4/invierno2026_nowcast.csv'); nwsc = nw[(nw.departamento == 'Santa Cruz') & (nw.zone == 'lowland')].set_index('crop')
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 4: the 2026/27 verano outlook, with the invierno 2026 already in'); footer(s, n)
    vc = ['SB', 'MZ', 'RI']; cd = CategoryChartData(); cd.categories = [NAME[c] for c in vc]
    for cond, lab in [('El Niño analogues', 'All El Niño analogues (14)'), ('SEAS5-weighted analogues', 'SEAS5-weighted analogues'), ('strong EP analogues 1997/2015/2023', 'Strong eastern-Pacific analogues (3)')]:
        cd.add_series(lab, [float(natp[(natp.crop == c) & (natp.condition == cond)].iloc[0]['mean']) for c in vc])
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.7), Inches(7.4), Inches(4.9), cd); ch = gf.chart; style_chart(ch); colorize(ch, ['nino', 'green', 'bad'])
    ch.value_axis.minimum_scale = -35; ch.value_axis.maximum_scale = 5; ch.value_axis.major_unit = 5; ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW; ch.plots[0].gap_width = 60; ch.plots[0].has_data_labels = True; ch.plots[0].data_labels.font.size = Pt(10); ch.plots[0].data_labels.number_format = '+0;-0;0'; ch.plots[0].data_labels.number_format_is_linked = False
    text(s, 0.6, 1.35, 7.4, 0.3, 'Simulated 2026/27 national yield, % of the mean over all 42 analogue seasons (same management, same cells)', size=11, color='muted')
    box(s, 8.4, 1.45, 4.3, 5.35, fill='sand', shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
    text(s, 8.65, 1.6, 3.9, 0.4, 'Chance of a ≥10% national loss, SEAS5-weighted', size=12, bold=True, color='green')
    sw = natp[natp.condition == 'SEAS5-weighted analogues'].set_index('crop')
    for i, c in enumerate(vc): stat(s, 8.65 + (i % 2) * 2.0, 2.05 + (i // 2) * 1.5, 1.9, f"{sw.loc[c, 'p_loss10']:.0%}", NAME[c])
    text(s, 8.65, 5.05, 3.9, 0.4, 'Invierno 2026, already harvested (nowcast)', size=12, bold=True, color='green')
    text(s, 8.65, 5.45, 3.9, 1.3, [f"Santa Cruz sorgo {nwsc.loc['SG', 'anom_vs_trend_pct']:+.0f}% vs the hindcast trend (rank {nwsc.loc['SG', 'rank_of_42']} of 43 seasons); trigo {nwsc.loc['WH', 'anom_vs_trend_pct']:+.0f}%. The developing-El Niño winter gain of Phase 3, under observed 2026 weather — checkable against INE when the invierno 2026 figures appear."], size=11, color='ink')
    notes(s, 'Conditional distributions over real seasons, not point forecasts; the 10th-90th percentile ranges are in the report. No area response, no floods or pests; soya magnitude is the least reliable (Phase 2/3). Absolute tonnes are not defensible, relative anomalies are.')
    # --- Phase 4: spread
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 4: the spread is the result'); footer(s, n)
    image(s, f'{P4F}/chart_2026_27_analogue_distribution.png', 0.5, 1.4, w=12.3)
    spl = pd.Timestamp(open(f'{ROOT}/derived/phase4/splice_date.txt').read().strip()); swsb = natp[(natp.condition == 'SEAS5-weighted analogues') & (natp.crop == 'SB')].iloc[0]
    text(s, 0.6, 5.5, 12.1, 1.2, f'Each dot is the 2026/27 campaign simulated with one past campaign\'s weather from {spl.day} {spl.strftime("%B")} onward, with the real 2026 weather before that. The three strong eastern-Pacific analogues sit at the bottom for soya, maíz and arroz; the SEAS5-weighted range for soya still spans {swsb.p10:+.0f}% to {swsb.p90:+.0f}% between its 10th and 90th percentiles. Sorgo and Santa Cruz trigo show no spread because their season was already over at the splice date.'.replace('-', '−'), size=12)
    notes(s, 'The same pipeline supports monthly updates: move the splice date forward and refresh the SEAS5 weights; the spread narrows as the season advances.')
    # --- Phase 4: map
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 4: 2026/27 under strong eastern-Pacific weather, cell by cell'); footer(s, n)
    image(s, f'{P4F}/map_2026_27_strongEP_vs_climatology.png', 0.5, 1.5, w=12.3)
    text(s, 0.6, 5.3, 12.1, 1.3, 'Mean over the 1997/98, 2015/16 and 2023/24 members relative to the all-analogue mean. The exposure is the Santa Cruz plain and the Chiquitanía for soya, maíz and arroz; the Altiplano, where SEAS5 is driest, is where this tool says least: no potato or quinoa, and a maíz response of the wrong sign in the reanalysis.', size=12)
    notes(s, 'Map of the strong-EP conditioned members; the SEAS5-weighted version is in the report tables by department and zone.')
if P5:
    P5D = f'{ROOT}/derived/phase5/2026-10-14'; sp = json.load(open(f'{P5D}/splice.json')); m5 = pd.read_csv(f'{P5D}/member_ensemble_summary.csv'); nat5 = m5[(m5.departamento == 'Bolivia') & (m5.zone == 'all')].set_index('crop')
    bf = pd.read_csv(f'{P5D}/bias_factors_all.csv')
    def dlab(d): d = pd.Timestamp(d); return f'{d.day} {d.strftime("%b")} {d.year}'
    # --- Slide: weather sources now in use (timeline schematic + three cards)
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'The weather behind the estimate: observed to date, forecast members, then analogues'); footer(s, n)
    segs = [('Observed: NASA POWER', f'1981 → {dlab(sp["power_last"])}', 'Gauge-corrected reanalysis, daily, per cell', 'green', 4.0), ('Forecast: ECMWF EC46 → SEAS5, 51 members', f'{dlab(sp["forecast_first"])} → {dlab(sp["forecast_last"])}', 'Served by Open-Meteo; each member bias-adjusted to the cell\'s own climatology', 'nino', 5.3), ('Analogue tail', f'from {dlab(sp["tail_first"])}', f'Top-weighted past campaign ({sp["analogue_tail"]}/{str(sp["analogue_tail"] + 1)[2:]})', 'neutral', 2.8)]
    x = 0.6
    for h, when, d, col, w in segs:
        box(s, x, 1.55, w - 0.08, 0.5, fill=col); text(s, x + 0.12, 1.6, w - 0.3, 0.45, h, size=12, bold=True, color='white', anchor=MSO_ANCHOR.MIDDLE)
        text(s, x, 2.12, w - 0.1, 0.3, when, size=11, bold=True, color='dark'); text(s, x, 2.42, w - 0.1, 0.6, d, size=10.5, color='muted'); x += w
    text(s, 0.6, 3.05, 12.1, 0.35, 'One daily weather file per cell and per member; DSSAT runs the 2026/27 campaign 51 times, exactly as it runs the 42 analogue campaigns.', size=11, color='ink')
    card(s, 0.6, 3.6, 3.9, 2.9, 'Why NASA POWER for the record', 'Checked against 18 SENAMHI stations: annual rainfall within 6% (ERA5 via Open-Meteo: 25%), and season-to-season rainfall tracked at r 0.79 (ERA5: 0.40). Its precipitation is corrected to the CPC gauge analysis, so over Bolivia it is close to a gauge product. Blind spot: the Chapare, where it is five times too dry.', size=11.5)
    card(s, 4.7, 3.6, 3.9, 2.9, 'Why the ECMWF members', 'ECMWF\'s operational extended-range (EC46, to day 46) and seasonal (SEAS5, to May) ensembles, the same 51 members in one product, refreshed daily and monthly. Each member is shifted and scaled, month by month, onto the cell\'s POWER climatology; its own run of wet and dry days is kept. Ensemble-mean season rainfall lands within 4% of climatology, as the forecast anomalies imply.', headcolor='nino', size=11.5)
    card(s, 8.8, 3.6, 3.9, 2.9, 'What cannot be checked', 'The member product carries no hindcasts, so there is no skill score for Bolivia; the analogue sets stay the primary estimate and the members are a second opinion in the same units. The adjustment choices move the national numbers by a few points; that sensitivity is part of the uncertainty.', headcolor='bad', size=11.5)
    notes(s, 'Decision record: documents/OpenMeteo-assessment_2026-10-14.md and PLAN.md s12. POWER = MERRA-2 with PRECTOTCORR (CPC Unified correction). EC46 = ECMWF extended range (ensemble, 46 days); SEAS5 = ECMWF seasonal system 5; both via the Open-Meteo seasonal API (Professional tier). Bias adjustment: separate Tmax/Tmin shifts, rain and radiation ratios, monthly, interpolated to the day. Weather pull ~2 minutes, 51 DSSAT runs ~45 minutes.')
    # --- Slide: Phase 5 headline (native chart + member probabilities)
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 5: forecast members side with the strong El Niño analogues'); footer(s, n)
    vc = ['SB', 'MZ', 'RI']; cd = CategoryChartData(); cd.categories = [NAME[c] for c in vc]
    cd.add_series('SEAS5-weighted analogues', [float(natp[(natp.crop == c) & (natp.condition == 'SEAS5-weighted analogues')].iloc[0]['mean']) for c in vc])
    cd.add_series('51 ECMWF members (mean)', [float(nat5.loc[c, 'mean']) for c in vc])
    cd.add_series('Strong eastern-Pacific analogues (3)', [float(natp[(natp.crop == c) & (natp.condition == 'strong EP analogues 1997/2015/2023')].iloc[0]['mean']) for c in vc])
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.7), Inches(7.4), Inches(4.9), cd); ch = gf.chart; style_chart(ch); colorize(ch, ['green', 'nino', 'bad'])
    ch.value_axis.minimum_scale = -35; ch.value_axis.maximum_scale = 5; ch.value_axis.major_unit = 5; ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW; ch.plots[0].gap_width = 60; ch.plots[0].has_data_labels = True; ch.plots[0].data_labels.font.size = Pt(10); ch.plots[0].data_labels.number_format = '+0;-0;0'; ch.plots[0].data_labels.number_format_is_linked = False
    text(s, 0.6, 1.35, 7.4, 0.3, 'Simulated 2026/27 national yield, % of the mean over all 42 analogue seasons (same management, same cells)', size=11, color='muted')
    box(s, 8.4, 1.45, 4.3, 5.35, fill='sand', shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
    text(s, 8.65, 1.6, 3.9, 0.4, 'Chance of a ≥10% national loss, ECMWF members', size=12, bold=True, color='nino')
    for i, c in enumerate(vc): stat(s, 8.65 + (i % 2) * 2.0, 2.05 + (i // 2) * 1.5, 1.9, f"{nat5.loc[c, 'p_loss10']:.0%}", NAME[c], color='nino')
    text(s, 8.65, 5.05, 3.9, 0.4, 'Where the members put the signal', size=12, bold=True, color='nino')
    text(s, 8.65, 5.45, 3.9, 1.3, [f"Lowland season warmth of about +1.5 °C over the analogue mean, inside the 1997/98, 2015/16 and 2023/24 range; Altiplano rainfall about a quarter below normal (trigo {m5[(m5.departamento == 'Bolivia') & (m5.zone == 'altiplano') & (m5.crop == 'WH')].iloc[0]['mean']:+.0f}%). 10th–90th percentile of the members: soya {nat5.loc['SB', 'p10']:+.0f} to {nat5.loc['SB', 'p90']:+.0f}%, maíz {nat5.loc['MZ', 'p10']:+.0f} to {nat5.loc['MZ', 'p90']:+.0f}%, arroz {nat5.loc['RI', 'p10']:+.0f} to {nat5.loc['RI', 'p90']:+.0f}%.".replace('-', '−')], size=11, color='ink')
    notes(s, 'Members: ECMWF run of 2026-10-14 (EC46 to about day 42, then the October SEAS5), bias-adjusted and spliced onto observed POWER to 2026-10-01; 1997/98 weather after 2027-05-03. The member mean sits between the SEAS5-weighted analogue set and the strong-EP set for the three summer crops. Not a verified forecast: no hindcasts exist for the member product, so this is a second opinion in the same units as the analogue sets, not a replacement. Sorgo and trigo (invierno) are untouched by the forecast window except highland trigo.')
    # --- Slide: members beside analogues (figure)
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 5: 51 forecast members beside 42 analogue campaigns'); footer(s, n)
    image(s, f'{P5D}/figures/chart_2026_27_members_vs_analogues.png', 0.5, 1.4, w=12.3)
    text(s, 0.6, 5.35, 12.1, 1.4, 'Left of each panel: the 2026/27 campaign under each past campaign\'s weather (orange El Niño, blue La Niña, grey neutral). Right: under each bias-adjusted ECMWF member. The members sit below the all-analogue mean for soya, maíz and arroz with a spread as wide as the analogue set, and overlap the strong eastern-Pacific campaigns at their lower end; for sorgo and trigo the forecast window barely touches the season. The two columns are different objects: the analogues span what past seasons did, the members span what the model thinks this season will do.', size=12)
    notes(s, 'Figure: derived/phase5/2026-10-14/figures/chart_2026_27_members_vs_analogues.png; tables derived/phase5/2026-10-14/member_ensemble_summary.csv. Both columns are % of the all-analogue mean, so they are directly comparable.')
    if os.path.exists(f'{ROOT}/derived/season_progress/figures/chart_season_progress_forecast.png'):
        SP = json.load(open(f'{ROOT}/derived/season_progress/summary.json')); zs = SP['zones']
        s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 5: where the members take the season\'s rainfall'); footer(s, n)
        image(s, f'{ROOT}/derived/season_progress/figures/chart_season_progress_forecast.png', 0.5, 1.3, w=12.3)
        bullets(s, 0.6, 5.45, 12.1, 1.5, [('Season total to 30 April, member median: ', f"Altiplano {zs['altiplano']['fc_end_median_mm']} mm ({zs['altiplano']['fc_end_pct_of_clim']}% of the all-campaign median; 80% of members between {zs['altiplano']['fc_end_p10_mm']} and {zs['altiplano']['fc_end_p90_mm']}), valleys {zs['valleys']['fc_end_median_mm']} mm ({zs['valleys']['fc_end_pct_of_clim']}%), lowlands {zs['lowland']['fc_end_median_mm']} mm ({zs['lowland']['fc_end_pct_of_clim']}%)"),
            ('Same picture as the analogues: ', 'the Altiplano deficit builds from December; valleys and lowlands end near normal once the wet start is counted, and the lowland risk runs through heat and the timing of dry spells, which a seasonal total does not show'),
            ('The band is the forecast spread, not a confidence interval of the outcome: ', 'members are bias-adjusted to the POWER climatology of each cell and cannot be verified against past seasons')], size=11, gap=3)
        notes(s, 'Observed POWER rainfall to the last available day, then the 51 bias-adjusted ECMWF members (EC46 then SEAS5, run 2026-10-14) accumulated from that day; dashed = member median, band = 10th-90th percentile. Zone series weighted by crop area as on the season slide.')
# ================= 13 Caveats
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'What these results cannot say'); footer(s, n)
cav = [('No area response', 'DSSAT simulates yield on planted area. Farmers plant less or switch crop after a failed onset; that channel is often larger than the yield channel and is outside this framework.'),
       ('No floods, hail, frost damage, pests', 'Excess-rain losses in the lowlands and hail/frost in the highlands are systematically under-estimated; wheat and soya show it.'),
       ('Reanalysis weather in the Andes', 'MERRA-2 at 0.5° in complex terrain; Altiplano maize fails in 42% of simulated seasons, partly real, partly resolution.'),
       ('Levels are calibrated, anomalies are not', 'Relative anomalies (% of normal) are the defensible output; absolute tonnes are not.'),
       ('No potato or quinoa', 'The Altiplano, where the El Niño drought story is usually told, is represented by valley maíz and highland trigo only.'),
       ('Twelve years of validation', 'INE departmental data run 2012–2024; every skill number here has a wide interval.')]
for i, (h, b) in enumerate(cav):
    x = 0.6 + (i % 3) * 4.1; y = 1.6 + (i // 3) * 2.45; card(s, x, y, 3.9, 2.25, h, b, headcolor='bad', size=13)
notes(s, 'These are the limitations the plan listed before Phase 1 started; the calibration work sharpened rather than removed them.')
# ================= 14 Next steps
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Next: the monthly update loop and the open model questions' if os.environ.get('DECK_PHASE34') == '1' else 'Next: the historical ENSO assessment, then the 2026/27 estimate'); footer(s, n)
cols = [('Monthly update loop (from the 8th of each month)', ['Pull the new SEAS5 release and the 51 ECMWF members (minutes with the Open-Meteo subscription); refresh the analogue weights', 'Move the splice date forward with the latest observed weather; rerun the 42 analogues and the 51 members (~1.5 h); the spread narrows as the season advances', 'Check the invierno 2026 nowcast against INE when published; 2015/16 and 2023/24 as the reference events'] if P5 else ['Pull the new SEAS5 release, refresh the analogue weights and the outlook tables in minutes', 'Move the splice date forward with the latest observed weather and rerun the 42-member ensemble (~45 min)', 'Check the invierno 2026 nowcast against INE when published; 2015/16 and 2023/24 as the reference events']), ('Model work still open', ['Statistical excess-rain term for soya, fitted on the INE overlap and reported separately', 'Potato (SUBSTOR) for the Altiplano — the forecast is driest where this tool says least', 'Per-department deliverable tables; municipal cross-check of MapSPAM against INE 2023–25']), ('Decisions and requests', ['INE departmental series 1984–2011 (only 2012–2024 in hand)', 'SENAMHI/INIAF counterpart: station data after 2009, seasonal forecasts they already hold', 'How the outlook is communicated: conditional distributions, never a single number'])] if os.environ.get('DECK_PHASE34') == '1' else [('Phase 3 — ENSO hindcast (1–2 weeks)', ['Classify the 42 campaigns by ONI and by the Niño-1+2 eastern-Pacific signature', 'Composite simulated anomalies by phase, per crop × department × zone, with bootstrap intervals',
          'Side by side with INE 2012–2024 and with the SENAMHI station rainfall, kept as independent evidence', 'Detrend and document the simulated soya trend before quoting anything', 'Statistical excess-rain term for soya']),
        ('Phase 4 — 2026/27 (2–3 weeks)', ['Analogue resampling: drive the 2026/27 season with 1997/98, 2015/16, 2023/24 weather on the actual sowing calendar', 'Seasonal-forecast-driven variant via the C3S path (ECMWF/NCEP/JMA ensembles SENAMHI already holds)', 'Monthly updates as the season unfolds: observed-to-date + forecast forward']),
        ('Decisions and requests', ['INE departmental series 1984–2011 (only 2012–2024 in hand)', 'SENAMHI/INIAF counterpart for station data and seasonal forecasts', 'Potato (SUBSTOR) for the Altiplano: 1–2 weeks of module work — worth it before Phase 4?', 'Municipal cross-check of MapSPAM against INE 2023–25'])]
for i, (h, items) in enumerate(cols):
    x = 0.6 + i * 4.1; box(s, x, 1.45, 3.9, 5.35, fill='sand', shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
    text(s, x + 0.2, 1.6, 3.5, 0.6, h, size=14, bold=True, color='green' if i < 2 else 'nino'); bullets(s, x + 0.2, 2.25, 3.5, 4.4, items, size=12.5, gap=7)
notes(s, 'Phase 3 is the first deliverable and a coherent product on its own. The potato question is the one scope decision that changes the Altiplano story.')
# ================= 15 Closing (dark)
s = prs.slides.add_slide(BLANK); n += 1; box(s, 0, 0, W, H, fill='dark')
text(s, 0.8, 2.3, 11.5, 1.0, 'Everything is reproducible and archived', size=34, bold=True, color='white', font=HEAD)
bullets(s, 0.8, 3.5, 11.5, 2.4, ['Code: github.com/jawoo/Tapiti (branch bolivia) — ' + NCOMMITS + ' Bolivia-specific commits, every switch defaults to upstream behaviour',
                                  'Workspace: PLAN.md (decisions and findings), DATA-INVENTORY.md, HANDOFF.md, derived/ (inputs, sources, sensitivity tables), runs/ (every production run with manifest, config and summaries)',
                                  f'This deck: Phase 2 reference run {os.path.basename(RUN)}, figures regenerated by analysis/deck_figures.py'] + (['Workspace repository: github.com/jawoo/bolivia-enso (private); Phase 5 runs archived under runs/phase5/'] if P5 else []), size=13, color='white')
notes(s, 'Contact: the IFPRI Bolivia ENSO team.')
prs.save(OUT); print('saved', OUT, 'slides', n)
