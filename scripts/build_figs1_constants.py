r"""Build outputs/origin_data/figs1_origin_constants.json for the Origin redraw of Fig. S1.

House twin of build_figs3_constants.py / build_figs4_constants.py (single-column SI
diagnostic), adapted to the TEN grouped bars + TWO frozen-mean dashed guides of Fig. S1:
  * ink width = 88.0 mm (249.449 pt) single-column target, ink height target 60.0 mm
    (band 55..65 mm after the in-figure mean-number box was deleted); NOT the 135 mm of
    Fig. S2, NOT the 6.30 in of the main-text figures;
  * canvas / page / decoy unchanged from the Fig.7 house recipe (page 24 x 15 cm,
    canvas inset 0.05 cm, OFF 0.25 cm, PDF pt = design pt + (7.0866, 7.0866));
  * closed 4-side box #333333 at 0.75 pt, hand-drawn inward major ticks 3.36 pt rendered,
    NO minor ticks, NO grid; Origin draws no native ticks/labels/frame (2026 theme emits
    SimSun), every string is hand-placed from measured ink boxes -> Arial only;
  * the axis name "Mixing weight" is 9 pt HORIZONTAL (this figure's explicit deviation
    from the rotated family titles, prompt defect-list item 5), left-aligned to the y tick
    lane, its ink bottom >= 7 pt clear of the top spine ink; a rotated or left-centred
    horizontal title would either violate the prompt or starve the category lane
    (seed labels need the full ~44.6 pt pitch for >= 7 pt adjacency at 88 mm);
  * NO mean-value box and NO "+/- std" ink: both live in the Word caption (prompt item 1);
    the two dashed guides at the FROZEN means 0.5369 / 0.6525 are the only furniture
    added; their frozen display values are hardcoded, never recomputed floats;
  * ten bars hardcoded at the exact per-seed table values (17-digit floats): five groups
    x = 0..4 EQUALLY spaced (NOT numeric seeds), bar width 0.38, alpha_1 left, alpha_2 right;
  * dash geometry is explicit (dashify + -d 0), NOT the `set plot -1 <style>` call that
    hangs Origin 2026 automation; pattern 5.4/5.4 pt = matplotlib's "--" at lw 0.9;
  * legend hand-built in the top-left inside: two 14.0 x 4.9 pt swatches (stem-matched)
    + Arial strings "alpha_1 (linear)" / "alpha_2 (nonlinear residual)" with ORIGIN
    subscripts \-(1)/\-(2) (proven ArialMT on Fig. S4) -- no mathtext, no STIX;
  * Okabe-Ito semantic colours frozen from _style.py: alpha_1 = C["LF"]/C["LF_stroke"]
    #E69F00 / #A87300, alpha_2 = C["MFNN"]/C["MFNN_stroke"] #009E73 / #006B4E; edges and
    dashed guides at 0.6 / 0.9 pt.

fsize -> rendered pt comes from scripts/_z_figs1_fontcal.py (measured in THIS page/
canvas/layer environment, aux raster ink for the lane widths); no calibration file ->
refuse to run.

Writes outputs/origin_data/figs1_origin_constants.json
"""
import os, sys, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PT = 72.0 / 2.54
OFF = 0.25                                  # cm, house canvas/page inset
PDFX = PDFY = 7.0866                        # = OFF * PT : design -> exported-PDF pt
DX = round(PDFX - 0.05 * PT, 4)             # 5.6693
PAGE = [24.0, 15.0]                         # cm, Fig.7 house canvas
DY = round(0.05 * PT + PAGE[1] * PT - PDFY, 4)   # 419.5276

FCALP = os.path.join(OD, "figs1_font_calibration.json")
if not os.path.exists(FCALP):
    sys.exit("REFUSING TO BUILD: run scripts/_z_figs1_fontcal.py first "
             "(missing " + FCALP + ")")
FCAL = json.load(open(FCALP, encoding="utf-8-sig"))
FSMAP = dict(FCAL["fs_map"])               # nominal -> [grid index, rendered pt, fsize to set]
for _need in ("7.5", "8.0", "9.0"):
    assert _need in FSMAP, "figs1_font_calibration.json lacks nominal %s pt" % _need
AUX = FCAL["aux"]

# ---------------- data-space mapping (frozen geometry of the matplotlib stem) -------
XLO, XHI = -0.618, 4.618                    # xlim measured off the frozen stem PDF frame
YLO, YHI = 0.0, 1.05                        # ylim(0,1.05) kept: the 1.0 tick does not touch
                                            # the top spine (prompt item 4/geometry)
YTICKS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
XTICKS = [0.0, 1.0, 2.0, 3.0, 4.0]
SEEDS  = [0, 1, 2, 42, 123]
A1 = [0.4708741307258606, 0.5989418029785156, 0.3363686800003052,
      0.6021012663841248, 0.6761338114738464]
A2 = [0.6265072822570801, 0.6315324306488037, 0.7088405489921570,
      0.6377006173133850, 0.6578147411346436]
MEAN1, MEAN2 = 0.5369, 0.6525               # FROZEN display values (_style.py FROZEN)
BAR_W_DU = 0.38                             # matplotlib width; centres c +/- 0.19

# ---------------- frame -------------------------------------------------------------
INK_TARGET_MM = 88.0
INK_TARGET_PT = round(INK_TARGET_MM * 72.0 / 25.4, 3)          # 249.449
INK_TARGET_H_MM = 60.0
INK_TARGET_H_PT = round(INK_TARGET_H_MM * 72.0 / 25.4, 3)      # 170.079
INK_HEIGHT_BAND_MM = [55.0, 65.0]
FL = 33.0
FT = 26.0
STROKE_HALF = 0.75 / 2.0
# left lane: y tick labels right-anchor FL-4.0; "0.0" at 8.4 pt renders ~2 digits + dot
WTICK_EST = 11.7                            # house digit width; probe re-measures exactly
TICK_DX_R = -4.0
LHANG_EST = -TICK_DX_R + WTICK_EST          # 15.7 : ink left = FL - 15.7
# horizontal axis name aligned to the tick lane:
TITLE_TX_L = round(TICK_DX_R - WTICK_EST, 4)        # -15.7  (ink left target)
# v4: the delivered v3 audit measured the axis-name ink 7.28 pt from the TOP SPINE INK
#     (the drawn spine centreline sits 0.83 pt below nominal, the house vector-lane
#     offset), i.e. only 6.8 pt with the antialiasing skirt -> below the 7 pt rule.
TITLE_GAP_B = 8.5                            # ink bottom -> FT centreline (spine ink +0.375)
TITLE_H = AUX["title"]["ink_h"]              # 9.000 raster pt @9.6 rendered
TOPHANG_EST = round(TITLE_GAP_B + TITLE_H, 4)       # 16.0
# bottom lane: ONE category line below the frame (family line-1 lane, 10.93 pt ink bottom
# below the frame centreline, as measured for Fig. S3 / S4)
CAT_DY_B = 10.93
INK_X_EXTRA = 0.431                          # family stroke+quantisation slack (Fig.7 house)
W_F = round(INK_TARGET_PT - LHANG_EST - INK_X_EXTRA, 3)      # 233.318
H_F = round(INK_TARGET_H_PT - CAT_DY_B - TOPHANG_EST, 3)     # 143.149
FR = round(FL + W_F, 3)
FB = round(FT + H_F, 3)
SX = W_F / (XHI - XLO)
SY = H_F / (YHI - YLO)
CX = 0.5 * (FL + FR)
CY = 0.5 * (FT + FB)

def bx2x(v): return FL + (v - XLO) * SX
def by2y(v): return FB - (v - YLO) * SY

# ---------------- colours (frozen, = _style.py C["LF"]/C["MFNN"] + strokes) ---------
SPINE = "#333333"; DARK = "#333333"; BLACK = "#000000"
ALPHA1 = dict(fill="#E69F00", edge="#A87300")     # linear branch
ALPHA2 = dict(fill="#009E73", edge="#006B4E")     # nonlinear residual branch
BAR_PEN = 0.6
DASH_W = 0.9
DASH_PATTERN = [5.4, 5.4]                          # matplotlib "--" scaled by lw 0.9

TL = 3.36                                           # rendered inward tick length
YTITLE_DX_R = TICK_DX_R                             # (unused: this figure has no rot item)

# ---------------- legend (hand-built, top-left inside) ------------------------------
LEG = dict(
    # v4b: FL+8.0 put the swatch column only 3.9 pt right of the inward LEFT-spine ticks
    #     (row 2 sat 4.48 pt from the 0.8 tick).  The tick tips reach FL+3.36, so the
    #     swatch ink must start at >= FL+3.36+0.375+7 = FL+10.7: use FL+12.0.
    sw=dict(w=14.0, h=4.9, left=round(FL + 12.0, 4)),        # stem swatch ink 14.0x4.9
    # v4: 11.0/22.5 put row 1 only 2.3 pt from the inward top ticks and 5.7 pt from the
    #     top spine ink (Fig. S1 v3 occlusion audit).  Inward ticks are 3.36 pt long,
    #     so a legend inside the box must clear the TICK TIPS by >= 7 pt: row 1 ink top
    #     is now FT+12.625 -> 8.2 pt below the tick tips, 11.4 pt below the spine ink.
    row_c_dy=[16.5, 28.0],                                  # text-ink centres rel. FT
    tx_left=round(FL + 12.0 + 14.0 + 5.6, 4),                # stem handle->label gap 5.6
    gap_frame=7.0)

# ---------------- ten bars + two dashed guides --------------------------------------
BITEMS = []
for i in range(5):
    BITEMS.append(dict(which=1, seed=SEEDS[i], xc=round(XTICKS[i] - BAR_W_DU / 2.0, 6),
                       value=A1[i], fill=ALPHA1["fill"], edge=ALPHA1["edge"],
                       cx_pt=round(bx2x(XTICKS[i] - BAR_W_DU / 2.0), 4),
                       top_pt=round(by2y(A1[i]), 4)))
    BITEMS.append(dict(which=2, seed=SEEDS[i], xc=round(XTICKS[i] + BAR_W_DU / 2.0, 6),
                       value=A2[i], fill=ALPHA2["fill"], edge=ALPHA2["edge"],
                       cx_pt=round(bx2x(XTICKS[i] + BAR_W_DU / 2.0), 4),
                       top_pt=round(by2y(A2[i]), 4)))
BAR_HALF_PT = round((BAR_W_DU / 2.0) * SX, 4)
DASHES = [dict(v=MEAN1, color=ALPHA1["edge"], width=DASH_W, pattern=DASH_PATTERN),
          dict(v=MEAN2, color=ALPHA2["edge"], width=DASH_W, pattern=DASH_PATTERN)]

BS = chr(92)
def H(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=False,
                ax=ax, tx=round(tx, 4), ay=ay, ty=round(ty, 4))

horiz = []
YTN = {0.0: "y_t_00", 0.2: "y_t_02", 0.4: "y_t_04", 0.6: "y_t_06", 0.8: "y_t_08", 1.0: "y_t_10"}
for v in YTICKS:
    horiz.append(H(YTN[v], "%.1f" % v, 8.0, BLACK, "right", FL + TICK_DX_R, "center", by2y(v)))
for i, s in enumerate(SEEDS):
    horiz.append(H("cat_%d" % (i + 1), "seed %d" % s, 8.0, BLACK,
                   "center", bx2x(XTICKS[i]), "bottom", FB + CAT_DY_B))
# horizontal axis name: ink left aligned to the tick lane, ink bottom 7 pt above the frame
horiz.append(H("y_title", "Mixing weight", 9.0, DARK, "left", FL + TITLE_TX_L,
               "top", FT - TITLE_GAP_B - TITLE_H))
# legend strings (their swatches are separate data-furniture drawn by the plot script)
L1 = "\\x(03B1)\\-(1) (linear)"
L2 = "\\x(03B1)\\-(2) (nonlinear residual)"
horiz.append(H("leg_1", L1, 7.5, BLACK, "left", LEG["tx_left"], "center", FT + LEG["row_c_dy"][0]))
horiz.append(H("leg_2", L2, 7.5, BLACK, "left", LEG["tx_left"], "center", FT + LEG["row_c_dy"][1]))

rot = []   # Fig. S1 has NO rotated string (axis name is horizontal by prompt)

K = dict(
    note="Fig. S1 Origin redraw (Protocol W residual-MFNN mixing-weight SI diagnostic). "
         "Okabe-Ito LF/MFNN semantic colours, Arial only, closed box, inward ticks on all "
         "four sides, NO mean-value box, NO +/- std ink, NO error bars, horizontal 9 pt "
         "axis name, single-column 88 mm x 60 mm ink, dashed guides at the frozen means "
         "0.5369 / 0.6525 (hardcoded display values).",
    pt=PT, off_cm=OFF, page_cm=PAGE, fs_map=FSMAP,
    decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY),
    canvas=dict(left=0.05, top=0.05, width=PAGE[0], height=PAGE[1]),
    spine=SPINE, dark=DARK, black=BLACK, alpha1=ALPHA1, alpha2=ALPHA2,
    tick=dict(len_nom=3.6, len_rendered=TL, thick=0.75,
              label_fs=8.0, label_color=BLACK, title_fs=9.0, title_color=DARK),
    frame=dict(FT=FT, FB=FB, FL=FL, FR=FR, sx=SX, sy=SY, cx=CX, cy=CY),
    layers=dict(a=dict(left=round(OFF + FL / PT, 5), top=round(OFF + FT / PT, 5),
                       width=round(W_F / PT, 5), height=round(H_F / PT, 5),
                       xf=XLO, xt=XHI, yf=YLO, yt=YHI,
                       xticks=XTICKS, yticks=YTICKS)),
    bars=dict(width_du=BAR_W_DU, half_pt=BAR_HALF_PT, pen=BAR_PEN, items=BITEMS),
    dashes=DASHES,
    legend=LEG,
    lanes=dict(tick_dx_r=TICK_DX_R, wtick_est=WTICK_EST, title_tx_l=TITLE_TX_L,
               title_gap_b=TITLE_GAP_B, title_h=TITLE_H, title_w=AUX["title"]["ink_w"],
               cat_dy_b=CAT_DY_B, seeds=SEEDS,
               bcx=[round(bx2x(v), 4) for v in XTICKS]),
    horiz=horiz, rot=rot,
    probe=dict(x0=20.0, x_step=170.0, per_col=6, y0=10.0, y_step=30.0,
               win_x0=-4.0, win_x1=165.0, win_y0=-3.0, win_y1=17.0,
               rot_x0=745.0, rot_dx=60.0, rot_y=40.0, rot_win_x=30.0, rot_win_y=150.0),
    export=dict(png_width=6433,
                target_ink_width_pt=INK_TARGET_PT, target_ink_width_mm=INK_TARGET_MM,
                target_ink_height_mm=INK_TARGET_H_MM, ink_height_band_mm=INK_HEIGHT_BAND_MM),
    qa=dict(forbidden_words=["PINN", "PPINN", "LOGO", "frozen", "mean", "std", "ddof",
                             "callout", "LF", "HF"],
            forbidden_tokens=["\\xb1", "+/-", "0.5369", "0.6525", "0.1200", "0.0301",
                              "0.1342", "0.0337"],
            allowed_texts=["0.0", "0.2", "0.4", "0.6", "0.8", "1.0",
                           "seed 0", "seed 1", "seed 2", "seed 42", "seed 123",
                           "Mixing weight", L1, L2],
            min_gap_pt=7.0,
            bar_values=[{"seed": SEEDS[i], "alpha_1": A1[i], "alpha_2": A2[i]} for i in range(5)],
            dashed_values=[MEAN1, MEAN2]),
)
json.dump(K, open(os.path.join(OD, "figs1_origin_constants.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print("frame  FL=%.3f FR=%.3f W=%.3f | FT=%.3f FB=%.3f H=%.3f" % (FL, FR, W_F, FT, FB, H_F))
print("scale  sx=%.5f pt/unit-x  sy=%.5f pt/unit-w  CX=%.3f CY=%.3f" % (SX, SY, CX, CY))
print("bars   half=%.3f pt | centres=%s" % (BAR_HALF_PT, str([round(v, 3) for v in [bx2x(t) for t in XTICKS]])))
print("design ink: x %.3f..%.3f (w=%.3f = %.4f mm) ; y %.3f..%.3f (h=%.4f mm)" %
      (FL - LHANG_EST, FR + STROKE_HALF, INK_TARGET_PT, INK_TARGET_MM,
       FT - TOPHANG_EST, FB + CAT_DY_B, (TOPHANG_EST + H_F + CAT_DY_B) * 25.4 / 72.0))
print("dashed: 0.5369 -> y=%.3f (FT+%.3f) ; 0.6525 -> y=%.3f (FT+%.3f)" %
      (by2y(MEAN1), by2y(MEAN1) - FT, by2y(MEAN2), by2y(MEAN2) - FT))
print("legend: sw left=%.3f top1=%.3f top2=%.3f | text left=%.3f c1=%.3f c2=%.3f" %
      (LEG["sw"]["left"], FT + LEG["row_c_dy"][0] - LEG["sw"]["h"] / 2,
       FT + LEG["row_c_dy"][1] - LEG["sw"]["h"] / 2, LEG["tx_left"],
       FT + LEG["row_c_dy"][0], FT + LEG["row_c_dy"][1]))
hi = by2y(max(A2))   # highest bar top (seed 2 alpha_2)
print("headroom: highest bar ink top FT+%.3f vs legend ink bottom FT+%.3f -> gap %.3f (need >= 7)" %
      (hi - FT, FT + LEG["row_c_dy"][1] + AUX["leg2"]["ink_h"] / 2.0 - FT,
       (hi - FT) - (LEG["row_c_dy"][1] + AUX["leg2"]["ink_h"] / 2.0)))
print("category adjacency: pitch %.3f pt, widest pair seed42/seed123 ink %s -> gap ~%.3f pt" %
      (SX, str([round(v, 2) for v in [28.6, AUX["cat"]["ink_w"]]]),
       SX - 0.5 * (28.6 + AUX["cat"]["ink_w"])))
print("horiz=%d rot=%d" % (len(horiz), len(rot)))
for it in horiz:
    print("  %-8s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
print("DONE_FIGS1_CONSTANTS")
