"""Build the Field Shift pitch deck (.pptx), v2: titles 35 pt, all other text 16-22 pt, airy spacing.

Usage: python build_deck_v2.py ART_DIR SCREENSHOT.png OUT.pptx
Dark green theme, Title Case, British English. Display numerals (hero figures, step numbers, scores) are larger by
design; footers, the kicker and chips are page furniture at 11-12 pt.
Every number comes from the project's data files (data/validation.json, web/src/data.json, docs/SUBMISSION.md).
"""
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ART, SHOT, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
PANEL, MINT, GOLD, WHITE, BODY, MUTED, RED = "0B3A2C", "2EE6A0", "F2B544", "F3FFF9", "DCEFE6", "A9CDBE", "FF8A70"
HEAD, TEXT = "Aptos Display", "Aptos"
KICKER = "NASA SPACE APPS CHALLENGE 2026   •   FIELD SHIFT"
SW, SH = 13.333, 7.5
LEFT, RIGHT = 0.75, SW - 0.75       # side margins
TOP, BOTTOM = 2.7, 6.75             # content band under the subtitle
FULL = RIGHT - LEFT
rgb = lambda h: RGBColor.from_string(h)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
BLANK = prs.slide_layouts[6]


def alpha(color_parent, pct):
    clr = color_parent.find(qn("a:solidFill")).find(qn("a:srgbClr"))
    etree.SubElement(clr, qn("a:alpha")).set("val", str(int(pct * 1000)))


def text(slide, x, y, w, h, runs, size=16, color=BODY, bold=False, font=TEXT, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         spacing=None, line=1.12, name=None):
    """`runs`: a string, or a list of paragraphs; each paragraph a string or a list of (text, {overrides}) runs."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        box.name = name
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, 0)
    for i, para in enumerate(runs if isinstance(runs, list) else [runs]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line
        for chunk in (para if isinstance(para, list) else [(para, {})]):
            content, o = chunk if isinstance(chunk, tuple) else (chunk, {})
            r = p.add_run()
            r.text = content
            f = r.font
            f.name, f.size, f.bold = o.get("font", font), Pt(o.get("size", size)), o.get("bold", bold)
            f.color.rgb = rgb(o.get("color", color))
            if o.get("spacing", spacing):
                r._r.get_or_add_rPr().set("spc", str(o.get("spacing", spacing)))
    return box


def panel(slide, x, y, w, h, fill=PANEL, opacity=80, border=MINT, border_opacity=45, radius=0.06):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = radius
    s.shadow.inherit = False
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    alpha(s.fill._xPr, opacity)
    s.line.color.rgb = rgb(border)
    s.line.width = Pt(1.25)
    alpha(s.line._get_or_add_ln(), border_opacity)
    return s


def bar(slide, x, y, w, h, color=MINT, opacity=100, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.shadow.inherit = False
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(color)
    if opacity < 100:
        alpha(s.fill._xPr, opacity)
    s.line.fill.background()
    return s


def chip(slide, x, y, label, color=MINT, pad=0.5):
    w = pad + 0.118 * len(label)
    panel(slide, x, y, w, 0.34, fill=color, opacity=16, border=color, border_opacity=85, radius=0.5)
    text(slide, x, y, w, 0.34, label, size=11, color=color, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, spacing=120)
    return w


def frame(slide, number, title, subtitle, source=None):
    slide.shapes.add_picture(str(ART / f"bg_{number}.jpg"), 0, 0, prs.slide_width, prs.slide_height)
    text(slide, LEFT, 0.42, 7, 0.3, KICKER, size=11, color=MINT, bold=True, spacing=200)
    logo_h = 0.5
    slide.shapes.add_picture(str(ART / "logo_spaceapps.png"), Inches(RIGHT - logo_h * 440 / 172), Inches(0.32), height=Inches(logo_h))
    text(slide, LEFT, 0.84, FULL, 0.85, title, size=35, color=WHITE, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE, line=1.0, name="Title")
    bar(slide, LEFT, 1.76, 1.0, 0.055, GOLD)
    text(slide, LEFT, 1.95, FULL, 0.45, subtitle, size=18, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)
    text(slide, LEFT, 7.02, 5, 0.3, "Field Shift   |   Change The Future", size=11, color=MUTED)
    text(slide, RIGHT - 0.6, 7.02, 0.6, 0.3, f"{number:02d}", size=12, color=MINT, bold=True, align=PP_ALIGN.RIGHT)
    if source:
        text(slide, 4.2, 7.02, RIGHT - 4.2 - 0.8, 0.3, source, size=11, color=MUTED, align=PP_ALIGN.RIGHT)


def style_chart(chart, legend=False):
    chart.has_title = False
    chart.font.name, chart.font.size = TEXT, Pt(14)
    chart.font.color.rgb = rgb(BODY)
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(16)
        chart.legend.font.color.rgb = rgb(WHITE)
    for axis in (chart.category_axis, chart.value_axis):
        axis.format.line.color.rgb = rgb("2A5A49")
        axis.tick_labels.font.size = Pt(14)
        axis.tick_labels.font.color.rgb = rgb(BODY)
    chart.value_axis.has_major_gridlines = True
    chart.value_axis.major_gridlines.format.line.color.rgb = rgb("1D4A3B")


def notes(slide, body):
    slide.notes_slide.notes_text_frame.text = body


# ------------------------------------------------------------------ 1. cover
s = prs.slides.add_slide(BLANK)
s.shapes.add_picture(str(ART / "bg_cover.jpg"), 0, 0, prs.slide_width, prs.slide_height)
s.shapes.add_picture(str(ART / "logo_spaceapps.png"), Inches(0.85), Inches(0.6), height=Inches(0.95))
s.shapes.add_picture(str(ART / "logo_team.png"), Inches(SW - 0.85 - 1.9 * 1004 / 1055), Inches(0.45), height=Inches(1.9))
text(s, 0.85, 2.3, 9, 0.35, "CHALLENGE:  FIELD SHIFT — ADAPTING FARMS WITH NASA DATA", size=12, color=MINT, bold=True, spacing=200)
text(s, 0.85, 2.72, 9, 1.35, "Field Shift", size=84, color=WHITE, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE, line=1.0, name="Title")
bar(s, 0.85, 4.2, 1.3, 0.065, GOLD)
text(s, 0.85, 4.42, 9.5, 0.55, "Understand The Field. Rotate Smarter.", size=22, color=MINT, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.85, 5.08, 8.2, 0.9, "NASA Data, Proven Against The Ground, Behind Every Crop Rotation Decision At Maru, Jordan.", size=18, color=BODY, line=1.2)
text(s, 0.85, 6.42, 9.5, 0.35, "Zaid   •   Sadeel   •   Kosay   •   Lana   •   Mohammad   •   Dr. Hossam", size=16, color=WHITE, bold=True)
text(s, 0.85, 6.86, 9.5, 0.3, "Team Change The Future   |   JUST, Jordan   |   14–15 November 2026", size=12, color=MUTED)
notes(s, "[20 s] We are Change The Future. Field Shift answers one question for a rainfed farmer at Maru, near Irbid: which crop rotation fits my field? Our difference is simple. We tested NASA data against the ground before we used it, and we tell the farmer how far to trust every number.")

# ------------------------------------------------------------------ 2. problem
s = prs.slides.add_slide(BLANK)
frame(s, 2, "The Problem: Farmers Choose Rotations Blind",
      "Rain Is Failing, Satellite Numbers Go Unchecked, And No Tool Shows How Far To Trust Them.",
      "Sources: NASA POWER 1998–2025, GPM IMERG, HLS NDVI (Mean Of Three Maru Fields)")
H = BOTTOM - TOP
panel(s, LEFT, TOP, 4.5, H, border=GOLD, border_opacity=70)
text(s, LEFT + 0.35, TOP + 0.15, 3.8, 1.4, "−55%", size=88, color=GOLD, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE, line=1.0)
text(s, LEFT + 0.35, TOP + 1.65, 3.8, 0.75, "Rain In 2024–25 Against The Other 26 Seasons", size=20, color=WHITE, bold=True)
chip(s, LEFT + 0.35, TOP + 2.58, "MEASURED", GOLD)
text(s, LEFT + 0.35, TOP + 3.1, 3.8, 0.7, "Crop Greenness Fell From 0.82 To 0.48", size=17, color=BODY)
cx, cw = LEFT + 4.5 + 0.3, FULL - 4.5 - 0.3
panel(s, cx, TOP, cw, 2.8)
text(s, cx + 0.3, TOP + 0.15, cw - 0.6, 0.35, "Season Rain At Maru, mm (GPM IMERG)", size=17, color=WHITE, bold=True)
seasons = ["15–16", "16–17", "17–18", "18–19", "19–20", "20–21", "21–22", "22–23", "23–24", "24–25"]
rain = [323, 251, 355, 515, 481, 318, 324, 270, 384, 159]
cd = CategoryChartData()
cd.categories = seasons
cd.add_series("Rain", rain)
ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(cx + 0.15), Inches(TOP + 0.52), Inches(cw - 0.3), Inches(2.22), cd).chart
style_chart(ch)
ch.value_axis.visible = False
ch.value_axis.has_major_gridlines = False
plot = ch.plots[0]
plot.gap_width = 45
plot.has_data_labels = True
plot.data_labels.font.size = Pt(14)
plot.data_labels.font.color.rgb = rgb(WHITE)
for i, v in enumerate(rain):
    pt = plot.series[0].points[i]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = rgb(RED if v == min(rain) else "1F8A5B")
panel(s, cx, TOP + 3.0, cw, H - 3.0, fill=GOLD, opacity=14, border=GOLD, border_opacity=75)
text(s, cx + 0.35, TOP + 3.0, cw - 0.7, H - 3.0, "A Maru Farmer Commits A Full Season On Numbers Nobody Has Checked.", size=19, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[35 s] Last season was the driest in 27 years at Maru: 55 percent less rain than the other seasons. Two independent NASA sources agree, and the satellites saw the crop suffer: the greenness peak fell from 0.82 to 0.48. Farmers here grow on rain alone. Rotation is one of the few levers they control, and today they pull it without checked data.")

# ------------------------------------------------------------------ 3. solution
s = prs.slides.add_slide(BLANK)
frame(s, 3, "The Solution: Rotations Ranked By Priority",
      "Arabic First, Built For A Phone In The Field. It Ranks The Options. The Farmer Decides.")
steps = [("01", "Pick The Field", "11 Years Of Satellite History, Rain, Soil"),
         ("02", "Set Priorities", "Water, Dry Years, Soil, Cover, Harvests"),
         ("03", "Compare Rotations", "Numbers, Source And Confidence Per Score"),
         ("04", "Stress-Test", "27 Real Seasons Replayed Or Simulated")]
sw, sh, sg = 6.1, 0.9, 0.15
for i, (num, head, body) in enumerate(steps):
    y = TOP + i * (sh + sg)
    panel(s, LEFT, y, sw, sh)
    text(s, LEFT + 0.3, y, 0.9, sh, num, size=30, color=MINT, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE, line=1.0)
    text(s, LEFT + 1.25, y + 0.1, sw - 1.45, 0.36, head, size=20, color=WHITE, bold=True, line=1.0)
    text(s, LEFT + 1.25, y + 0.48, sw - 1.45, 0.34, body, size=16, color=BODY, line=1.0)
px, pw = LEFT + sw + 0.3, FULL - sw - 0.3
panel(s, px, TOP, pw, 3.35, fill="FFFFFF", opacity=100, border=MINT, border_opacity=85, radius=0.04)
shot_w = 3.85
s.shapes.add_picture(str(SHOT), Inches(px + (pw - shot_w) / 2), Inches(TOP + 0.08), width=Inches(shot_w))
demo_w = chip(s, px, TOP + 3.58, "LIVE DEMO", GOLD)
text(s, px + demo_w + 0.2, TOP + 3.55, pw - demo_w - 0.2, 0.4, "zaid-sh05.github.io/field-shift", size=18, color=MINT, bold=True, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[40 s] The farmer picks a field on a satellite map, sets five priorities with sliders, and gets three rotations ranked: wheat after wheat, wheat then lentil, wheat then fallow. With equal priorities on our first field the scores are 71, 51 and 43. Every score opens to show its numbers, its source and its confidence. Then the farmer can stress-test the result. [Switch to the live site here.]")

# ------------------------------------------------------------------ 4. proof
s = prs.slides.add_slide(BLANK)
frame(s, 4, "NASA Data, Proven Against The Ground",
      "We Compared NASA With 18 Months Of Maru Station Records Before Using A Single Number.",
      "Ground Truth: Published Maru Station Months, NARC / JUST (doi 10.15159/AR.20.236). A Check, Not A Calibration.")
stats = [("0.81 °C", "Temperature Error After Correction, Down From 2.37 °C", MINT),
         ("440 m", "NASA’s Grid Cell Sits This Far Below Maru", MINT),
         ("−22%", "Rain Missed By NASA POWER And GPM IMERG", RED)]
lw, ch_h, cg = 5.0, 1.22, 0.19
for i, (num, body, color) in enumerate(stats):
    y = TOP + i * (ch_h + cg)
    panel(s, LEFT, y, lw, ch_h, border=color, border_opacity=65)
    text(s, LEFT + 0.3, y, 2.15, ch_h, num, size=34, color=color, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE, line=1.0)
    text(s, LEFT + 2.45, y, lw - 2.7, ch_h, body, size=16, color=BODY, anchor=MSO_ANCHOR.MIDDLE, line=1.1)
cx, cw = LEFT + lw + 0.3, FULL - lw - 0.3
panel(s, cx, TOP, cw, 3.1)
text(s, cx + 0.3, TOP + 0.15, 4.4, 0.35, "Monthly Mean Temperature, °C", size=17, color=WHITE, bold=True)
chip(s, cx + cw - 0.3 - (0.5 + 0.118 * 8), TOP + 0.15, "MEASURED", MINT)
months = ["Oct 15", "Nov", "Dec", "Jan 16", "Feb", "Mar", "Apr", "May", "Jun", "Oct 16", "Nov", "Dec", "Jan 17", "Feb", "Mar", "Apr", "May", "Jun"]
station = [21.73, 15.27, 9.43, 8.21, 10.19, 13.77, 19.41, 21.23, 26.3, 21.94, 13.7, 8.58, 7.78, 8.7, 12.71, 17.53, 21.85, 26.7]
nasa = [24.71, 18.24, 11.66, 10.31, 14.07, 15.93, 21.53, 23.63, 28.81, 24.25, 18.24, 11.0, 9.71, 10.04, 15.01, 19.38, 24.11, 27.16]
fixed = [round(v - 6.5 * 440.14 / 1000, 2) for v in nasa]
cd = CategoryChartData()
cd.categories = months
cd.add_series("Maru Station", station)
cd.add_series("NASA, Raw", nasa)
cd.add_series("NASA, Corrected", fixed)
ch = s.shapes.add_chart(XL_CHART_TYPE.LINE, Inches(cx + 0.15), Inches(TOP + 0.55), Inches(cw - 0.3), Inches(2.5), cd).chart
style_chart(ch, legend=True)
ch.category_axis.tick_labels.font.size = Pt(12)
for series, color, width in zip(ch.plots[0].series, (WHITE, RED, MINT), (3.0, 2.0, 2.5)):
    series.format.line.color.rgb = rgb(color)
    series.format.line.width = Pt(width)
    series.smooth = False
text(s, cx, TOP + 3.25, cw, 0.35, "Six NASA And Partner Datasets In The Pipeline", size=16, color=MINT, bold=True)
x = cx
for name in ("NASA POWER", "HLS", "GPM IMERG", "SMAP", "GRACE", "SRTM"):
    x += chip(s, x, TOP + 3.68, name, MINT, pad=0.3) + 0.09
notes(s, "[45 s] This is the core of our project. Against 18 months of published station data, NASA POWER read 2.4 degrees too warm. The cause: its grid cell sits 440 metres below Maru. A standard elevation correction cut the error by two thirds, to 0.81 degrees, and the result holds for any correction rate from 5 to 7 degrees per kilometre. Rainfall is different: both NASA products miss 22 percent of local rain. We do not hide it. We show rainfall with medium confidence.")

# ------------------------------------------------------------------ 5. what sets us apart
s = prs.slides.add_slide(BLANK)
frame(s, 5, "What Sets Field Shift Apart",
      "Other Tools Take Satellite Data As The Truth. We Test It First, Then Show Our Working.")
cards = [("01", "Tested Before Trusted", "NASA Ran 2.4 °C Warm. We Found Why And Fixed It.", MINT),
         ("02", "Confidence Per Score", "High For Satellite Observation, Low For Rules.", MINT),
         ("03", "Rotation From Space", "33 Field-Seasons, Zero Fallow, No Questions Asked.", MINT),
         ("04", "Testable By Anyone", "27 Real Seasons Replayed. Any Climate Simulated.", MINT),
         ("05", "Ranks, Never Dictates", "The Farmer’s Priorities Set The Order.", MINT),
         ("★", "No Black Box", "Rule-Based Scores. No Generative AI In The App.", GOLD)]
gap = 0.25
cw, chh = (FULL - 2 * gap) / 3, (BOTTOM - TOP - gap) / 2
for i, (num, head, body, color) in enumerate(cards):
    cx, cy = LEFT + (i % 3) * (cw + gap), TOP + (i // 3) * (chh + gap)
    gold = color == GOLD
    panel(s, cx, cy, cw, chh, fill=GOLD if gold else PANEL, opacity=18 if gold else 80, border=color, border_opacity=85 if gold else 45)
    text(s, cx + 0.32, cy + 0.2, 1, 0.4, num, size=22, color=color, bold=True, font=HEAD, line=1.0)
    text(s, cx + 0.32, cy + 0.66, cw - 0.64, 0.4, head, size=19, color=GOLD if gold else WHITE, bold=True, line=1.0)
    text(s, cx + 0.32, cy + 1.1, cw - 0.64, 0.7, body, size=16, color=BODY, line=1.15)
notes(s, "[40 s] A mentor told us this idea already exists. Crop comparison does. What does not exist is a tool that tests the satellite data first and shows the farmer how far to trust each number. Five things set us apart. One: tested before trusted. Two: confidence on every score. Three: the current rotation is read from eleven years of imagery. Four: anyone can test it. Five: it ranks and never dictates. And there is no black box: rule-based scores, one small model with its error on screen, no generative AI.")

# ------------------------------------------------------------------ 6. impact
s = prs.slides.add_slide(BLANK)
frame(s, 6, "The Impact: Decisions That Hold In A Dry Year",
      "Every Result Below Comes From 27 Real Seasons Of NASA Data At Maru.",
      "Crop Water Need: FAO-56 Penman–Monteith. Rain: NASA POWER. Demand Is Modelled; The Seasons Are Real.")
pw, ph = (FULL - 2 * gap) / 3, 3.0
panels = [
    ("Drought Season 2024–25", "Water Need Met By Rain", [("Wheat → Wheat", 23, "23%", RED), ("Wheat → Lentil", 40, "40%", GOLD), ("Wheat → Fallow", 61, "61%", MINT)], 100),
    ("Seasons Under Half Need", "Out Of 27 Seasons", [("Wheat → Wheat", 14, "14", RED), ("Wheat → Lentil", 3, "3", GOLD), ("Wheat → Fallow", 0, "0", MINT)], 27),
    ("After 3 Wheat Seasons", "Advisor Score Out Of 100", [("Lentil", 80, "80", MINT), ("Fallow", 53, "53", GOLD), ("Wheat", 43, "43", RED)], 100),
]
for i, (head, sub, rows, top) in enumerate(panels):
    px = LEFT + i * (pw + gap)
    panel(s, px, TOP, pw, ph)
    text(s, px + 0.3, TOP + 0.16, pw - 0.6, 0.36, head, size=19, color=WHITE, bold=True, line=1.0)
    text(s, px + 0.3, TOP + 0.56, pw - 0.6, 0.32, sub, size=16, color=MUTED, line=1.0)
    for r, (label, value, shown, color) in enumerate(rows):
        ry = TOP + 1.08 + r * 0.62
        track = pw - 0.6 - 0.95
        text(s, px + 0.3, ry, track, 0.3, label, size=16, color=BODY, bold=True, line=1.0)
        bar(s, px + 0.3, ry + 0.36, track, 0.13, "FFFFFF", opacity=10, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        if value:
            bar(s, px + 0.3, ry + 0.36, max(0.1, track * value / top), 0.13, color, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        text(s, px + pw - 0.3 - 0.9, ry + 0.02, 0.9, 0.5, shown, size=22, color=color, bold=True, font=HEAD, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, line=1.0)
chip(s, LEFT, TOP + ph + 0.18, "MODELLED FROM MEASURED RAIN", GOLD)
by = TOP + ph + 0.66
panel(s, LEFT, by, FULL, BOTTOM - by + 0.1, fill=MINT, opacity=12, border=MINT, border_opacity=75)
text(s, LEFT + 0.35, by, FULL - 0.7, BOTTOM - by + 0.1, [[("Repeatable:  ", {"color": MINT, "bold": True}), ("One Station Record Gives Any Village The Same Check And Scores.", {})]],
     size=18, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[45 s] Here is the impact, in numbers from the real record. In last season’s drought, rain covered 23 percent of the water need of wheat after wheat, 40 percent for wheat then lentil, and 61 percent for wheat then fallow. Across 27 seasons, wheat after wheat fell under half its need 14 times; wheat then lentil 3 times. And the advisor: after three wheat seasons it ranks lentil first at 80. The crop demand is modelled with FAO-56; the seasons are real. The method repeats for any village with a station record.")

# ------------------------------------------------------------------ 7. built, tested, live
s = prs.slides.add_slide(BLANK)
frame(s, 7, "Built, Tested, Live", "A Working Product Today, With A Clear Next Step.")
hw, hh = (FULL - gap) / 2, 2.7
columns = [("Built So Far", MINT, ["Live On Any Phone, Arabic And English", "3 Real Fields, 11 Years Of Satellite Data", "57 Automated Tests Passing", "Every Result Rebuilds From Open Data"]),
           ("Next Step", GOLD, ["Field Pilot With Maru Farmers", "Local Prices For A True Income Score", "More Villages, Same Method", "Heat And Frost Checked Locally"])]
for i, (head, color, lines) in enumerate(columns):
    px = LEFT + i * (hw + gap)
    panel(s, px, TOP, hw, hh, border=color, border_opacity=60)
    text(s, px + 0.35, TOP + 0.17, hw - 0.7, 0.4, head, size=22, color=color, bold=True, font=HEAD, line=1.0)
    for r, line_text in enumerate(lines):
        y = TOP + 0.78 + r * 0.46
        bar(s, px + 0.35, y + 0.1, 0.15, 0.15, color, shape=MSO_SHAPE.OVAL)
        text(s, px + 0.7, y, hw - 1.05, 0.36, line_text, size=17, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, line=1.0)
by = TOP + hh + 0.22
bh = BOTTOM - by + 0.1
panel(s, LEFT, by, FULL, bh, fill=MINT, opacity=14, border=MINT, border_opacity=85)
text(s, LEFT + 0.35, by + 0.1, 7.2, 0.5, "zaid-sh05.github.io/field-shift", size=22, color=MINT, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE, line=1.0)
text(s, LEFT + 0.35, by + 0.62, 7.2, 0.4, "Code And Data:  github.com/Zaid-sh05/field-shift", size=16, color=BODY, anchor=MSO_ANCHOR.MIDDLE, line=1.0)
logo_h = bh - 0.2
s.shapes.add_picture(str(ART / "logo_team.png"), Inches(RIGHT - 0.25 - logo_h * 1004 / 1055), Inches(by + 0.1), height=Inches(logo_h))
text(s, RIGHT - 0.25 - logo_h - 3.1, by, 3.0, bh, "It Supports The Farmer’s Decision. It Does Not Make It.", size=16, color=MUTED, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[25 s] Everything you saw is built and live at this address. Three real fields, eleven years of satellite history, 57 automated tests, and every result rebuilds from the open repository. Our next step is a field pilot with Maru farmers and extension officers, and local prices for a true income score. Field Shift supports the farmer’s decision. It does not make it. Thank you. [Total: about 4 minutes 10 seconds.]")

prs.save(OUT)
print("saved", OUT)
