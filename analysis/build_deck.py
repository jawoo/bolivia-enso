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
DATE = '5 October 2026'
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
text(s, 0.8, 3.45, 11.5, 0.8, 'Progress report — Phases 1–4 of the Tapiti gridded-DSSAT assessment' if os.environ.get('DECK_PHASE34') == '1' else 'Progress report — Phases 1 and 2 of the Tapiti gridded-DSSAT assessment', size=22, color='moss')
text(s, 0.8, 5.6, 11, 0.5, f'IFPRI  ·  {DATE}', size=14, color='white')
text(s, 0.8, 6.05, 11, 0.5, 'Tapiti: a Bolivia fork of Tokki, named after the tapití, Bolivia\'s native cottontail', size=12, color='moss')
notes(s, 'Progress report to the project lead. Phases 1 (inputs) and 2 (calibration) are complete; Phase 3 (historical ENSO assessment) starts next. All numbers in this deck are from the archived production run named in the manifest.')
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
# ================= 3 Status timeline
s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Where we are: all four phases have a first pass; the update loop is next' if os.environ.get('DECK_PHASE34') == '1' else 'Where we are: inputs and calibration done, ENSO assessment next'); footer(s, n)
phases = [('Phase 0', 'Scaffold', 'Fork Tokki → Tapiti; smoke test on real cells', 'done'), ('Phase 1', 'Inputs', 'Weather, soil, management, cultivars, unit table', 'done'),
          ('Phase 2', 'Calibration', 'Boundary conditions and yield levels vs INE', 'done'), ('Phase 3', 'ENSO hindcast', 'Composites by ENSO phase, 1983–2024', 'done' if os.environ.get('DECK_PHASE34') == '1' else 'next'), ('Phase 4', 'Forward 2026/27', 'Analogue weather + seasonal forecasts', 'done' if os.environ.get('DECK_PHASE34') == '1' else 'later')]
x0, wcol = 0.6, 2.38
for i, (ph, nm, d, st) in enumerate(phases):
    x = x0 + i * (wcol + 0.08); col = {'done': 'green', 'next': 'nino', 'later': 'neutral'}[st]
    box(s, x, 1.6, wcol, 0.08, fill=col); text(s, x, 1.8, wcol, 0.35, ph, size=11, color='muted'); text(s, x, 2.1, wcol, 0.5, nm, size=20, bold=True, color='dark', font=HEAD)
    text(s, x, 2.65, wcol, 1.0, d, size=12, color='ink'); text(s, x, 3.7, wcol, 0.35, ({'done': 'First pass complete', 'next': 'Starting now', 'later': 'Planned'}[st] if i >= 3 else {'done': 'Complete', 'next': 'Starting now', 'later': 'Planned'}[st]), size=11, bold=True, color=col)
text(s, 0.6, 4.5, 12.1, 0.4, 'What changed since the plan was written', size=14, bold=True, color='green')
bullets(s, 0.6, 4.9, 12.1, 2.0, [
    'The tool is now Tapiti (github.com/jawoo/Tapiti): a renamed fork of Tokki with the US-only material removed, ' + NCOMMITS + ' commits of Bolivia-specific changes, every run archived with a manifest',
    'Two inherited assumptions had to be reworked before calibration made sense: how rice is grown, and when a season starts (slides 7–8)',
    'Soya — 1.4 Mha and the Santa Cruz economy — turns out to be the crop the water-balance model explains least (slide 12)'], size=12)
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
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 4: what the September SEAS5 forecast says for Nov–Mar 2026/27'); footer(s, n)
    image(s, f'{P4F}/chart_seas5_2026-09_vs_analogues.png', 1.2, 1.35, w=10.9)
    bullets(s, 0.6, 5.5, 12.1, 1.4, [('51 ECMWF members: ', 'Altiplano rainfall −33% with every member dry (80% between −47 and −16%), valleys −5%, lowlands near zero with a wide spread; temperatures +1.6 to +2.5 °C in every zone'),
        ('In the lowlands and valleys the members cluster around 1997/98 and 2015/16; ', 'in the Altiplano the forecast is drier and warmer than any campaign since 1983 — beyond what the analogue method can represent there'),
        ('Each past campaign is weighted by its closeness to the members: ', '40% of the weight falls on 1997/98, 2015/16 and 2023/24, 59% on El Niño campaigns, 16% on La Niña')], size=11, gap=3)
    notes(s, 'SEAS5 system 51, initialised September 2026, monthly anomalies relative to its own hindcast climatology; precipitation scaled by the POWER Nov-Mar mean; T2m matched to POWER Tmax. Weights are a Gaussian kernel on standardised distance, averaged over members. Refreshed on each monthly release.')
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
    text(s, 0.6, 5.5, 12.1, 1.2, 'Each dot is the 2026/27 campaign simulated with one past campaign\'s weather from 26 September onward, with the real 2026 weather before that. The three strong eastern-Pacific analogues sit at the bottom for soya, maíz and arroz; the SEAS5-weighted range for soya still spans −43% to +19% between its 10th and 90th percentiles. Sorgo and Santa Cruz trigo show no spread because their season was already over at the splice date.', size=12)
    notes(s, 'The same pipeline supports monthly updates: move the splice date forward and refresh the SEAS5 weights; the spread narrows as the season advances.')
    # --- Phase 4: map
    s = prs.slides.add_slide(BLANK); n += 1; title(s, 'Phase 4: 2026/27 under strong eastern-Pacific weather, cell by cell'); footer(s, n)
    image(s, f'{P4F}/map_2026_27_strongEP_vs_climatology.png', 0.5, 1.5, w=12.3)
    text(s, 0.6, 5.3, 12.1, 1.3, 'Mean over the 1997/98, 2015/16 and 2023/24 members relative to the all-analogue mean. The exposure is the Santa Cruz plain and the Chiquitanía for soya, maíz and arroz; the Altiplano, where SEAS5 is driest, is where this tool says least: no potato or quinoa, and a maíz response of the wrong sign in the reanalysis.', size=12)
    notes(s, 'Map of the strong-EP conditioned members; the SEAS5-weighted version is in the report tables by department and zone.')
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
cols = [('Monthly update loop (from the 8th of each month)', ['Pull the new SEAS5 release, refresh the analogue weights and the outlook tables in minutes', 'Move the splice date forward with the latest observed weather and rerun the 42-member ensemble (~45 min)', 'Check the invierno 2026 nowcast against INE when published; 2015/16 and 2023/24 as the reference events']), ('Model work still open', ['Statistical excess-rain term for soya, fitted on the INE overlap and reported separately', 'Potato (SUBSTOR) for the Altiplano — the forecast is driest where this tool says least', 'Per-department deliverable tables; municipal cross-check of MapSPAM against INE 2023–25']), ('Decisions and requests', ['INE departmental series 1984–2011 (only 2012–2024 in hand)', 'SENAMHI/INIAF counterpart: station data after 2009, seasonal forecasts they already hold', 'How the outlook is communicated: conditional distributions, never a single number'])] if os.environ.get('DECK_PHASE34') == '1' else [('Phase 3 — ENSO hindcast (1–2 weeks)', ['Classify the 42 campaigns by ONI and by the Niño-1+2 eastern-Pacific signature', 'Composite simulated anomalies by phase, per crop × department × zone, with bootstrap intervals',
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
                                  f'This deck: Phase 2 reference run {os.path.basename(RUN)}, figures regenerated by analysis/deck_figures.py'], size=13, color='white')
notes(s, 'Contact: the IFPRI Bolivia ENSO team.')
prs.save(OUT); print('saved', OUT, 'slides', n)
