r"""Build outputs/origin_data/figs6_origin_constants.json for the Origin redraw of Fig. S6.

House twin of build_figs4_constants.py (single-column 88 mm SI, 24x15 cm page, 0.05 cm
canvas, OFF 0.25, PDF = design + (7.0866, 7.0866) pt, 1 pt = 1 pt), extended for the
DUAL-AXES figure: left MFNN MAPE scale 0..160, right Factor2 scale 0..1.15.

Style parity with the family + frozen-matplotlib reference (outputs/figures/
FigS6_al80_upweight_w.{png,pdf,svg}, SHA 68cfa1ce...):
  * closed 4-side box #333333 at 0.75 pt; inward major ticks 3.36 pt rendered, hand-
    drawn: 3 x-ticks on top+bottom, 7 left-scale ticks on the left spine, 6 right-
    scale ticks on the right spine (Origin draws no native ticks/labels at all, and
    the default theme would emit SIMSUN -> everything hand-placed);
  * Arial only (\i() for the italic w in the x-axis name; % is a plain Arial glyph;
    NO mathtext -> no STIX); axis name 9 pt, tick labels 8 pt, MAPE annotations 7.5 pt,
    legend text 7 pt -> nothing below 7 pt; sizes from figs6_font_calibration.json;
  * NO in-figure suptitle (the deleted "Counterfactual k=2 up-weighting (SI only)"
    wording lives in the Word caption only); NO panel letter;
  * Okabe-Ito frozen: MAPE line/fill/band #D55E00 (edge #994300), Factor2 #0072B2
    (edge #004D7A); LEFT tick labels + left axis name #994300, RIGHT counterparts
    #004D7A; x labels / x name / legend text #333333; band transparency 85 % (= alpha
    0.15 on white, the frozen alpha fill_between);
  * frozen numbers ONLY: 122 / 48 / 31 shown as "122%" "48%" "31%"; band half-widths
    14.89 / 4.16 / 7.91 around the frozen points (NOT around the 122.10/47.89/31.30
    means); Factor2 0.15 / 1.0 / 1.0 with NO numbers, NO error bars, NO band;
  * axes: xlim (0.55, 10.45) as the reference; left ylim (0, 160) -- 160 is pure
    annotation-avoidance headroom, all ticks 0/25/.../150 and the 150 tick retained,
    top spine at 160; right ylim (0, 1.15) unchanged so the y=1.0 squares are unclipped;
  * markers: sizes from figs6_symbol_calibration.json measured in this exact layer
    (circle z=7.00 -> ink 6.75 pt vs reference 7.0; square z=7.75 -> ink 6.33 vs 6.5);
  * legend: hand-built, frameless (as the frozen PDF: no legend patch), centre-right
    lane, swatch line 14 pt + marker handle + 7 pt text, ink columns aligned to the
    frozen SVG offsets.

Annotation placement (ink-CENTRE targets, design pt from FL/FT; see _z_figs6_occ.py
for the delivered-PDF gap audit). Reference defects fixed: "122%" no longer sits on
the descending line/band (moved above the band's top edge, 1.2 data-units right of
the w=1 point, still clearly paired with it); "48%" / "31%" stay above their points
with >=7 pt to marker/line/band; legend keeps >=7 pt from everything.

Every text target below is an INK-BOX edge in design pt (top-left origin).  The
anchor->ink offsets are measured on the F6PROBE page by scripts/_z_figs6_measure.py.
"""
import os, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PT = 72.0 / 2.54
OFF = 0.25
PAGE = [24.0, 15.0]
PDFX = PDFY = 7.0866
DX = round(PDFX - 0.05 * PT, 4)
DY = round(0.05 * PT + PAGE[1] * PT - PDFY, 4)

FCAL = json.load(open(os.path.join(OD, "figs6_font_calibration.json"), encoding="utf-8-sig"))
FSMAP = dict(FCAL["fs_map"])
for _need in ("7.0", "7.5", "8.0", "9.0"):
    assert _need in FSMAP, "figs6_font_calibration.json lacks nominal %s pt" % _need
SCAL = json.load(open(os.path.join(OD, "figs6_symbol_calibration.json"), encoding="utf-8-sig"))
ZC = SCAL["pick"]["circle"]["z"]; ZQ = SCAL["pick"]["square"]["z"]
INK_C = max(SCAL["pick"]["circle"]["ink_w"], SCAL["pick"]["circle"]["ink_h"])
INK_Q = max(SCAL["pick"]["square"]["ink_w"], SCAL["pick"]["square"]["ink_h"])

# ---------------- data-space mapping (frozen geometry + avoidance, see header) -------
XLO, XHI = 0.55, 10.45
YLO, YHI = 0.0, 160.0                       # left scale (150 tick kept, headroom)
YLO2, YHI2 = 0.0, 1.15                      # right scale (unchanged vs reference)
WT = [1, 5, 10]
MAPE = [122.0, 48.0, 31.0]
BAND_HALF = [14.89, 4.16, 7.91]
F2 = [0.15, 1.0, 1.0]
YTICKS_L = [0, 25, 50, 75, 100, 125, 150]
YTICKS_R = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

# ---------------- frame -------------------------------------------------------------
INK_TARGET_MM = 88.0
INK_TARGET_PT = round(INK_TARGET_MM * 72.0 / 25.4, 3)          # 249.449
INK_HEIGHT_BAND_MM = [55.0, 65.0]
STROKE_HALF = 0.375
FL = 33.0
FT = 26.0
# left overhang: rotated 9 pt axis name ink right at FL-24.0, cross ink ~9 pt  -> FL-33
# right overhang: mirrored, rotated "Factor2" ink left at FR+24, ink right ~FR+33
LHANG_EST = 33.0
RHANG_EST = 33.0
# bottom overhang: 8 pt tick-label line (ink bottom FB+11.1) + 9 pt axis name
# (ink bottom FB+23.4, both measured on the frozen reference PDF) + stroke half
XTICK_DY_B = 11.10
XTITLE_DY_B = 23.40
BHANG_EST = XTITLE_DY_B + STROKE_HALF
# W_F start value: INK_TARGET_PT - LHANG - RHANG - stroke halves; the true closure is
# iterated against the delivered ink width via finalize/occ (Origin quantises the
# layer width, see the figs4 note: d(ink)/d(W_F) ~ 1.7).
# The rotated right-hand name is the SHORTER string: the probe measured cross-inks
# 9.00 pt for 'MFNN MAPE (%)' (incl. the ' (%)' descent band) vs 7.125 pt for
# 'Factor2' (cap-height only), so the right overhang is 24.0 + 7.125, not 33.
# (fitz span bboxes UNDER-report Origin Type-3 Arial subsets; the raster ink is the
# truth -- same lesson as the figs4 self-check.)  True closure is iterated against
# the delivered ink width via finalize/occ (d(ink)/d(W_F) ~ 1.7 here).
RHANG_EFF = 24.0 + 7.125
INK_X_EXTRA = -0.144   # closure: first render delivered ink 249.200 pt (short
# 0.249); with the measured d(ink)/d(W_F) = 1.73 (figs4 note) add 0.144 to W_F.
W_F = round(INK_TARGET_PT - LHANG_EST - RHANG_EFF - STROKE_HALF - INK_X_EXTRA, 3)  # 184.949
H_F = round(60.0 * 72.0 / 25.4 - BHANG_EST - STROKE_HALF, 3)                        # 145.928
FR = round(FL + W_F, 3)
FB = round(FT + H_F, 3)
SX = W_F / (XHI - XLO)
SY = H_F / (YHI - YLO)
SY2 = H_F / (YHI2 - YLO2)
CX = 0.5 * (FL + FR)
CY = 0.5 * (FT + FB)

def bx2x(v): return FL + (v - XLO) * SX
def by2y(v): return FB - (v - YLO) * SY
def by2y2(v): return FB - (v - YLO2) * SY2

# ---------------- colours (frozen) ---------------------------------------------------
SPINE = "#333333"; TXTDARK = "#333333"; BLACK = "#000000"
MAPEC = dict(fill="#D55E00", edge="#994300", ann="#994300", band_transp=85, band_pen=0.6,
           band_fill_export="#F9E7D9", band_rim_export="#F3D2B9",
           band_note="Origin 2026 drops Fill-Area when Plot.transparency is set on a line+area "
                    "plot (verified: control fill exports, fill+transparency does not). The band "
                    "therefore ships PRE-COMPOSITED: fill = #D55E00 @15%% on white = #F9E7D9; rim "
                    "= stroke(.15) over fill(.15) = #F3D2B9. Pixels are identical to the frozen "
                    "alpha band because nothing else lies UNDER the band (frame/ticks/labels all "
                    "outside its 23.09..136.89 span).")
F2C = dict(fill="#0072B2", edge="#004D7A")
LEFTC = "#994300"; RIGHTC = "#004D7A"

# ---------------- lanes / gaps --------------------------------------------------------
TICK_DX_R = -4.0
YTITLE_DX_R = -24.0
Y2TITLE_DX_L = 24.0
TL = 3.36
GAP = 7.0

# ---------------- annotation ink-centre targets (see header + occ audit) --------------
# Ink-CENTRE targets, derived from the frozen geometry (band half-widths, marker/line
# inks, real 7.9 pt-rendered text ink) with >=7 pt everywhere incl. the sloped band
# edge's perpendicular distance; _z_figs6_occ.py re-audits on the delivered PDF.
ANN = [
    # 122%: real raster ink 18.875 x 5.875 -> centre (1.95, 142.45): band-perp 7.18,
    # top frame 12.7, marker dy 12.9; clearly paired with the w=1 point, above the
    # band edge instead of sitting ON the line/band (the reference defect).
    ("ann122", "122%", 7.5, round(bx2x(1.95), 3), round(by2y(142.45), 3)),
    # 48%: ink 15.125 x 5.875 -> centred over the w=5 point at value 77.0:
    # band-perp 8.0, MAPE-line perp 11.5, marker top dy 18.3.
    ("ann48",  "48%",  7.5, round(bx2x(5.0), 3),  round(by2y(77.0), 3)),
    # 31%: value 58.5; ink centre pulled LEFT of the w=10 point (to
    # FR - 0.375 - 7 - 7.56 - 6.33) so the ink stays >=7 pt from the inward
    # right-spine ticks and the frame; band-perp 11.8, marker dy 18.6.
    ("ann31",  "31%",  7.5, round(FR - STROKE_HALF - GAP - 7.56 - INK_Q, 3),
     round(by2y(58.5), 3)),
]

# ---------------- legend geometry (frameless; frozen offsets rel. to FL/FT) -----------
LEG = dict(sx0=120.0, sx1=134.0, handle_cx=127.0, text_x=139.6,
           cy1=40.5, cy2=50.6, pen=1.4)

BS = chr(92)
def H(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=False,
                ax=ax, tx=round(tx, 4), ay=ay, ty=round(ty, 4))
def R(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=True,
                ax=ax, tx=round(tx, 4), ay=ay, ty=round(ty, 4))

horiz = []
for v in YTICKS_L:
    horiz.append(H("y_tL_%d" % v, "%d" % v, 8.0, LEFTC, "right", FL + TICK_DX_R, "center", by2y(v)))
for v in YTICKS_R:
    horiz.append(H("y_tR_%01d" % int(round(v * 10)), "%.1f" % v, 8.0, RIGHTC, "left",
                   FR - TICK_DX_R, "center", by2y2(v)))
for w in WT:
    horiz.append(H("x_t_%d" % w, "%d" % w, 8.0, TXTDARK, "center", bx2x(w), "bottom", FB + XTICK_DY_B))
for name, txt, fs, xc, yc in ANN:
    horiz.append(H(name, txt, fs, MAPEC["ann"], "center", xc, "center", yc))
horiz.append(H("legM", "MAPE", 7.0, TXTDARK, "left", FL + LEG["text_x"], "center", FT + LEG["cy1"]))
horiz.append(H("legF", "Factor2", 7.0, TXTDARK, "left", FL + LEG["text_x"], "center", FT + LEG["cy2"]))
horiz.append(H("x_title", "Anchor weight " + BS + "i(w)", 9.0, TXTDARK, "center", CX,
               "bottom", FB + XTITLE_DY_B))
rot = [R("y_title", "MFNN MAPE (%)", 9.0, LEFTC, "right", FL + YTITLE_DX_R, "center", CY),
       R("y2_title", "Factor2", 9.0, RIGHTC, "left", FR + Y2TITLE_DX_L, "center", CY)]

# ---------------- data-ink (design pt -> converted to data by the plot script) --------
band_top = [round(MAPE[i] + BAND_HALF[i], 2) for i in range(3)]
band_bot = [round(MAPE[i] - BAND_HALF[i], 2) for i in range(3)]
INKSPEC = dict(
    band=dict(fill=MAPEC["band_fill_export"], rim=MAPEC["band_rim_export"],
              pen=MAPEC["band_pen"], transparency=None,
              fill_between_type=9,
              pts_top=[[round(bx2x(w), 3), round(by2y(v), 3)] for w, v in zip(WT, band_top)],
              pts_bot=[[round(bx2x(w), 3), round(by2y(v), 3)] for w, v in zip(WT, band_bot)]),
    mape_line=dict(color=MAPEC["fill"], pen=1.4,
                   pts=[[round(bx2x(w), 3), round(by2y(v), 3)] for w, v in zip(WT, MAPE)]),
    f2_line=dict(color=F2C["fill"], pen=1.4,
                 pts=[[round(bx2x(w), 3), round(by2y2(v), 3)] for w, v in zip(WT, F2)]),
    mape_marks=dict(kind=2, z=ZC, ink=INK_C, fill=MAPEC["fill"], edge=MAPEC["edge"],
                    pts=[[round(bx2x(w), 3), round(by2y(v), 3)] for w, v in zip(WT, MAPE)]),
    f2_marks=dict(kind=1, z=ZQ, ink=INK_Q, fill=F2C["fill"], edge=F2C["edge"],
                  pts=[[round(bx2x(w), 3), round(by2y2(v), 3)] for w, v in zip(WT, F2)]),
    leg_line_mape=dict(color=MAPEC["fill"], pen=LEG["pen"],
                       pts=[[round(FL + LEG["sx0"], 3), round(FT + LEG["cy1"], 3)],
                            [round(FL + LEG["sx1"], 3), round(FT + LEG["cy1"], 3)]]),
    leg_line_f2=dict(color=F2C["fill"], pen=LEG["pen"],
                     pts=[[round(FL + LEG["sx0"], 3), round(FT + LEG["cy2"], 3)],
                          [round(FL + LEG["sx1"], 3), round(FT + LEG["cy2"], 3)]]),
    leg_mark_mape=dict(kind=2, z=ZC, fill=MAPEC["fill"], edge=MAPEC["edge"],
                       pts=[[round(FL + LEG["handle_cx"], 3), round(FT + LEG["cy1"], 3)]]),
    leg_mark_f2=dict(kind=1, z=ZQ, fill=F2C["fill"], edge=F2C["edge"],
                     pts=[[round(FL + LEG["handle_cx"], 3), round(FT + LEG["cy2"], 3)]]),
)

K = dict(
    note="Fig. S6 Origin redraw (SI counterfactual, fixed k=2 anchor reweighting; dual "
         "axes; Okabe-Ito, Arial only, closed box, hand-drawn inward ticks on all four "
         "sides, NO in-figure suptitle, single-column 88 mm ink).",
    pt=PT, off_cm=OFF, page_cm=PAGE, fs_map=FSMAP,
    decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY),
    canvas=dict(left=0.05, top=0.05, width=PAGE[0], height=PAGE[1]),
    spine=SPINE, dark=TXTDARK, black=BLACK, leftc=LEFTC, rightc=RIGHTC,
    mape=MAPEC, f2=F2C,
    tick=dict(len_nom=3.6, len_rendered=TL, thick=0.75,
              label_fs=8.0, title_fs=9.0, ann_fs=7.5, leg_fs=7.0),
    frame=dict(FT=FT, FB=FB, FL=FL, FR=FR, sx=SX, sy=SY, sy2=SY2, cx=CX, cy=CY),
    layers=dict(a=dict(left=round(OFF + FL / PT, 5), top=round(OFF + FT / PT, 5),
                       width=round(W_F / PT, 5), height=round(H_F / PT, 5),
                       xf=XLO, xt=XHI, yf=YLO, yt=YHI,
                       xticks=WT, yticks_left=YTICKS_L, yticks_right=YTICKS_R,
                       yhi_right=YHI2)),
    data=dict(w=WT, mape=MAPE, band_half=BAND_HALF, band_top=band_top, band_bot=band_bot,
              f2=F2),
    ink=INKSPEC,
    lanes=dict(tick_dx_r=TICK_DX_R, ytitle_dx_r=YTITLE_DX_R, y2title_dx_l=Y2TITLE_DX_L,
               xtick_dy_b=XTICK_DY_B, xtitle_dy_b=XTITLE_DY_B),
    legend=LEG,
    horiz=horiz, rot=rot,
    probe=dict(x0=10.0, x_step=170.0, per_col=10, y0=10.0, y_step=22.0,
               win_x0=-4.0, win_x1=165.0, win_y0=-3.0, win_y1=17.0,
               rot_x0=520.0, rot_dx=60.0, rot_y=40.0, rot_win_x=30.0, rot_win_y=150.0),
    export=dict(png_width=6433,
                target_ink_width_pt=INK_TARGET_PT, target_ink_width_mm=INK_TARGET_MM,
                ink_height_band_mm=INK_HEIGHT_BAND_MM),
    qa=dict(forbidden_numbers=["122.10", "47.89", "31.30", "16.65", "4.65", "8.85",
                               "0.150", "0.300", "n=5"],
            allowed_numbers=["122%", "48%", "31%", "150", "0.0", "1.0"],
            min_gap_pt=7.0),
)
json.dump(K, open(os.path.join(OD, "figs6_origin_constants.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print("frame  FL=%.3f FR=%.3f W_F=%.3f | FT=%.3f FB=%.3f H_F=%.3f" % (FL, FR, W_F, FT, FB, H_F))
print("scale  sx=%.4f sy=%.4f sy2=%.4f | CY=%.3f CX=%.3f" % (SX, SY, SY2, CY, CX))
print("design ink: x %.3f..%.3f (w=%.3f pt = %.4f mm) ; y %.3f..%.3f (h=%.4f mm)" %
      (FL - LHANG_EST, FR + RHANG_EFF + STROKE_HALF, FR - FL + RHANG_EST + STROKE_HALF + LHANG_EST,
       (FR - FL + RHANG_EFF + STROKE_HALF + LHANG_EST) * 25.4 / 72.0,
       FT - STROKE_HALF, FB + BHANG_EST, (BHANG_EST + H_F + STROKE_HALF) * 25.4 / 72.0))
print("markers: circle z=%.2f ink=%.2f ; square z=%.2f ink=%.2f" % (ZC, INK_C, ZQ, INK_Q))
print("ann targets:")
for name, txt, fs, xc, yc in ANN:
    v = (FB - yc) / SY
    print("  %-7s at (%.3f, %.3f)  -> data approx x=%.3f value=%.1f" % (name, xc, yc, (xc - FL) / SX + XLO, v))
for it in horiz:
    print("  %-9s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
for it in rot:
    print("  ROT %-9s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
print("DONE_FIGS6_CONSTANTS")

