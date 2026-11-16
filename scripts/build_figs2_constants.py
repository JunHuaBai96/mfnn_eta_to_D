r"""Build outputs/origin_data/figs2_origin_constants.json for the Origin redraw of Fig. S2.

House twin of build_figs4_constants.py (bars + annotations) and build_fig7_constants.py
(TWO EQUAL-WIDTH panels, native ticks/labels off, hand-drawn inward ticks), but for the
SI mid-column ink width 135.0 mm (Elsevier mid), NOT the 88 mm of Fig. S4 and NOT the
6.30 in of the main text.

REFUSES TO RUN without the two session measurements, because both are figure-specific:
  * outputs/origin_data/figs2_font_calibration.json  (_z_figs2_fontcal.py)
  * outputs/origin_data/figs2_symbol_calibration.json (_z_figs2_symbolprobe.py)

What this figure fixes about the matplotlib stem (redraw prompt):
  1. panel (b) loses the two-line caution sentence (it is Word-caption wording only), so
     nothing sits on the seed-1 Protocol G marker any more;
  2. panel (b) ylim(10, 50) with majors 10/20/30/40/50 lifts 13.46 off the bottom spine;
  3. panel (a) bar-top annotations move ABOVE the error caps, horizontally centred, 7 pt
     clear of the cap ink (they are no longer tucked beside a cap);
  4. Arial only (\x(00B1), \b(...)), no mathtext, no in-figure suptitle;
  5. the two frames are exactly equal width and the ink closes on 135.0 mm.

Frozen display values (never recomputed): W 26.18 +/- 1.33 %, G 27.36 +/- 12.88 %, and the
ten per-seed MAPEs of scripts/prepare_figs2_origin_data.py.

Every text target below is an INK-BOX edge in design pt (top-left origin, y down); the
anchor->ink offsets come from scripts/_z_figs2_measure.py (figs2_text_offsets.json) and
are used as soon as they exist, so a second build tightens the ink-width closure.
"""
import os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figs2_layout as F
from figs2_layout import (PT, BS, OD, B, OFF, PAGE, PDFX, PDFY, DX, DY, CANV,
                          INK_W_MM, INK_H_MM, INK_TARGET_PT, INK_TARGET_H_PT,
                          FRAME_T, STROKE_HALF, TICK_LEN, BAR_PEN, EB_PEN, EB_CAP_HALF,
                          LINE_PEN, SPINE, DARK, BLACK, W_COLOR, G_COLOR,
                          A_XF, A_XT, A_YF, A_YT, B_XF, B_XT, B_YF, B_YT,
                          A_XTICKS, A_YTICKS, B_XTICKS, B_YTICKS, B_XLABELS, BAR_W_DU,
                          TICK_DX_R, YTITLE_CLEAR, XTICK_DY_B, XTITLE_DX_C, XTITLE_DY_B,
                          CAT1_DY_B, CAT2_DY_B, CTITLE_DY_B, LETTER_DX_L, LETTER_DY_B,
                          LAB_GAP, LEG_LEFT_DX, LEG_LINE_W, LEG_TXGAP, LEG_TOP_D,
                          LEG_ITEM_GAP, PROBE)

FCALP = os.path.join(OD, "figs2_font_calibration.json")
SCALP = os.path.join(OD, "figs2_symbol_calibration.json")
assert os.path.exists(FCALP), ("missing figs2_font_calibration.json -- run "
                               "scripts/_z_figs2_fontcal.py first (no calibration, no build)")
assert os.path.exists(SCALP), ("missing figs2_symbol_calibration.json -- run "
                               "scripts/_z_figs2_symbolprobe.py first")
FCAL = json.load(open(FCALP, encoding="utf-8-sig"))
SCAL = json.load(open(SCALP, encoding="utf-8-sig"))
FSMAP = dict(FCAL["fs_map"])
for _need in ("7.5", "8.0", "9.0", "10.0"):
    assert _need in FSMAP, "figs2_font_calibration.json lacks nominal %s pt" % _need

OFFS = {}
OFFJSON = os.path.join(OD, "figs2_text_offsets.json")
if os.path.exists(OFFJSON):
    OFFS = json.load(open(OFFJSON, encoding="utf-8-sig"))

def inkw(name, est):
    o = OFFS.get(name)
    return (o["jx1"] - o["jx0"]) if o else est
def inkh(name, est):
    o = OFFS.get(name)
    return (o["jy1"] - o["jy0"]) if o else est

GEO = F.geometry(OFFS)
MP = F.maps(GEO)
LAY = {k: F.layer_spec(GEO, k) for k in ("a", "b", "canvas")}
FLA, FRA, FLB, FRB = GEO["fl_a"], GEO["fr_a"], GEO["fl_b"], GEO["fr_b"]
FT, FB, CXA, CXB, CY = GEO["ft"], GEO["fb"], GEO["cx_a"], GEO["cx_b"], GEO["cy"]

# ---------------------------------------------------------------- frozen data
META = json.load(open(os.path.join(OD, "figs2_data_meta.json"), encoding="utf-8-sig"))
W_M, W_E = META["bars"][0]["value_pct"], META["bars"][0]["err_pct"]
G_M, G_E = META["bars"][1]["value_pct"], META["bars"][1]["err_pct"]
SEEDS = META["trajectories"][0]["seeds"]
W_TR = META["trajectories"][0]["mape_pct"]
G_TR = META["trajectories"][1]["mape_pct"]
assert (W_M, W_E, G_M, G_E) == (26.18, 1.33, 27.36, 12.88), "frozen display changed"

# ---------------------------------------------------------------- panel (a)
BC1 = round(MP["ax2x"](0.0), 4)
BC2 = round(MP["ax2x"](1.0), 4)
BAR_HALF_PT = round((BAR_W_DU / 2.0) * MP["sx_a"], 4)
CAP_HALF_PT = round((BAR_W_DU / 2.0) * MP["sx_a"], 4)      # alias for the cap lane
ERR_HALF = 0.375 + 0.4            # 0.8 pt cap stroke half + rounded-cap overshoot
CAP1_Y = round(MP["ay2y"](W_M + W_E), 4)
CAP2_Y = round(MP["ay2y"](G_M + G_E), 4)
BAR1_TOP = round(MP["ay2y"](W_M), 4)
BAR2_TOP = round(MP["ay2y"](G_M), 4)

# ---------------------------------------------------------------- panel (b)
MARK = dict(
    W=dict(kind=2, z=SCAL["pick"]["circle"]["z"],
           ink=max(SCAL["pick"]["circle"]["ink_w"], SCAL["pick"]["circle"]["ink_h"]),
           fill=W_COLOR["fill"], edge=W_COLOR["edge"]),
    G=dict(kind=1, z=SCAL["pick"]["square"]["z"],
           ink=max(SCAL["pick"]["square"]["ink_w"], SCAL["pick"]["square"]["ink_h"]),
           fill=G_COLOR["fill"], edge=G_COLOR["edge"]))
TRAJ = dict(
    W=[dict(seed=SEEDS[i], xcat=float(i), mape=W_TR[i],
            x_pt=round(MP["bx2x"](float(i)), 4), y_pt=round(MP["by2y"](W_TR[i]), 4))
       for i in range(5)],
    G=[dict(seed=SEEDS[i], xcat=float(i), mape=G_TR[i],
            x_pt=round(MP["bx2x"](float(i)), 4), y_pt=round(MP["by2y"](G_TR[i]), 4))
       for i in range(5)])

# ---------------------------------------------------------------- legend (b, inside top-left)
# ONE horizontal row in the verified empty top-left lane of (b):
#   [swatch W] text W  [swatch G] text G
LEG_SW0 = round(FLB + LEG_LEFT_DX, 4)
LEG_TX_W = round(LEG_SW0 + LEG_LINE_W + LEG_TXGAP, 4)
LEG_SW1 = round(LEG_TX_W + inkw("LgB_W", 36.75) + LEG_ITEM_GAP, 4)
LEG_TX_G = round(LEG_SW1 + LEG_LINE_W + LEG_TXGAP, 4)
LEG_ROW_CY = round(FT + LEG_TOP_D + 0.5 * inkh("LgB_W", 5.9), 4)
LEG_SW = [dict(x0=LEG_SW0, x1=round(LEG_SW0 + LEG_LINE_W, 4), cx=round(LEG_SW0 + 0.5 * LEG_LINE_W, 4),
               cy=LEG_ROW_CY, proto="W"),
          dict(x0=LEG_SW1, x1=round(LEG_SW1 + LEG_LINE_W, 4), cx=round(LEG_SW1 + 0.5 * LEG_LINE_W, 4),
               cy=LEG_ROW_CY, proto="G")]
LEG_INK_RIGHT = round(LEG_TX_G + inkw("LgB_G", 35.1), 4)
LEG_INK_TOP = round(FT + LEG_TOP_D, 4)
LEG_INK_BOTTOM = round(LEG_ROW_CY + 0.5 * max(MARK["W"]["ink"], MARK["G"]["ink"]), 4)

# ---------------------------------------------------------------- typography
def H(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, ax=ax, tx=round(tx, 4), ay=ay,
                ty=round(ty, 4), rot=False)
def Rr(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, ax=ax, tx=round(tx, 4), ay=ay,
                ty=round(ty, 4), rot=True)
def key(v):
    return ("%g" % v).replace(".", "p").replace("-", "m")

YTITLE_DX_R = GEO["ytitle_dx_r"]
PMIN = BS + "x(00B1)"
horiz = [
    H("A_letter", BS + "b((a))", 10.0, BLACK, "left", FLA + LETTER_DX_L, "bottom", FT + LETTER_DY_B),
    H("A_ctitle", "Mean " + PMIN + " seed std (frozen)", 8.0, BLACK, "center", CXA,
      "bottom", FT - CTITLE_DY_B),
]
for v in A_YTICKS:
    horiz.append(H("A_yt_%s" % key(v), "%g" % v, 8.0, BLACK, "right", FLA + TICK_DX_R,
                   "center", MP["ay2y"](v)))
horiz += [
    H("A_bar1_lab", "%s%s%s%%" % ("%.2f" % W_M, PMIN, "%.2f" % W_E), 7.5, DARK, "center",
      BC1, "bottom", CAP1_Y - ERR_HALF - LAB_GAP),
    H("A_bar2_lab", "%s%s%s%%" % ("%.2f" % G_M, PMIN, "%.2f" % G_E), 7.5, DARK, "center",
      BC2, "bottom", CAP2_Y - ERR_HALF - LAB_GAP),
    H("A_cat1_1", "Protocol W", 8.0, BLACK, "center", BC1, "bottom", FB + CAT1_DY_B),
    H("A_cat1_2", "(primary)", 8.0, BLACK, "center", BC1, "bottom", FB + CAT2_DY_B),
    H("A_cat2_1", "Protocol G", 8.0, BLACK, "center", BC2, "bottom", FB + CAT1_DY_B),
    H("A_cat2_2", "(caution)", 8.0, BLACK, "center", BC2, "bottom", FB + CAT2_DY_B),
    H("B_letter", BS + "b((b))", 10.0, BLACK, "left", FLB + LETTER_DX_L, "bottom", FT + LETTER_DY_B),
    H("B_ctitle", "Per-seed trajectories (caution for G)", 8.0, BLACK, "center", CXB,
      "bottom", FT - CTITLE_DY_B),
]
for i, v in enumerate(B_XTICKS):
    horiz.append(H("B_xt_%d" % i, B_XLABELS[i], 8.0, BLACK, "center", MP["bx2x"](v),
                   "bottom", FB + XTICK_DY_B))
for v in B_YTICKS:
    horiz.append(H("B_yt_%s" % key(v), "%g" % v, 8.0, BLACK, "right", FLB + TICK_DX_R,
                   "center", MP["by2y"](v)))
horiz += [
    H("B_xtitle", "Seed", 9.0, DARK, "center", CXB + XTITLE_DX_C, "bottom", FB + XTITLE_DY_B),
    H("LgB_W", "Protocol W", 7.5, BLACK, "left", LEG_TX_W, "top", LEG_INK_TOP),
    H("LgB_G", "Protocol G", 7.5, BLACK, "left", LEG_TX_G, "top", LEG_INK_TOP),
]
rot = [
    Rr("A_ytitle", "MFNN MAPE (%)", 9.0, DARK, "right", FLA + YTITLE_DX_R, "center", CY),
    Rr("B_ytitle", "MFNN MAPE (%)", 9.0, DARK, "right", FLB + YTITLE_DX_R, "center", CY),
]

INK_LEFT = round(FLA - GEO["lhang"], 4)
INK_RIGHT = round(FRB + STROKE_HALF, 4)
INK_TOP = round(FT - GEO["top_hang"], 4)
INK_BOTTOM = round(FB + GEO["bhang"], 4)

K = dict(
    note="Fig. S2 Origin redraw (SI caution: Protocol G seed variance). Okabe-Ito, Arial "
         "only, closed 4-side box, hand-drawn inward ticks on all four sides, no in-figure "
         "suptitle, no caution sentence inside panel (b), two EQUAL-width frames, ink width "
         "135 mm.",
    pt=PT, off_cm=OFF, page_cm=PAGE, fs_map=FSMAP,
    font_calibration=dict(rendered=FSMAP, source="figs2_font_calibration.json"),
    decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY),
    canvas=CANV, spine=SPINE, dark=DARK, black=BLACK,
    w_color=W_COLOR, g_color=G_COLOR,
    tick=dict(len_nom=3.6, len_rendered=TICK_LEN, thick=FRAME_T,
              label_fs=8.0, label_color=BLACK, title_fs=9.0, title_color=DARK),
    frame=dict(FT=FT, FB=FB, FL_A=FLA, FR_A=FRA, FL_B=FLB, FR_B=FRB,
               sx_a=MP["sx_a"], sy_a=MP["sy_a"], sx_b=MP["sx_b"], sy_b=MP["sy_b"],
               cx_a=CXA, cx_b=CXB, cy=CY, w_panel=GEO["w_panel"], gutter=GEO["gutter"],
               lhang=GEO["lhang"], top_hang=GEO["top_hang"], bhang=GEO["bhang"],
               a_xticks=A_XTICKS, a_yticks=A_YTICKS, b_xticks=B_XTICKS, b_yticks=B_YTICKS),
    layers=dict(a=LAY["a"], b=LAY["b"], canvas=LAY["canvas"]),
    bars=dict(centres=[0.0, 1.0], width_du=BAR_W_DU, half_pt=BAR_HALF_PT, pen=BAR_PEN,
              items=[dict(x=0.0, value=W_M, err=W_E, fill=W_COLOR["fill"],
                          edge=W_COLOR["edge"], name="Protocol W (primary)",
                          cat=["Protocol W", "(primary)"], x_pt=BC1, top_pt=BAR1_TOP,
                          cap_pt=CAP1_Y),
                     dict(x=1.0, value=G_M, err=G_E, fill=G_COLOR["fill"],
                          edge=G_COLOR["edge"], name="Protocol G (caution)",
                          cat=["Protocol G", "(caution)"], x_pt=BC2, top_pt=BAR2_TOP,
                          cap_pt=CAP2_Y)]),
    errbar=dict(color=SPINE, pen=EB_PEN, cap_half=EB_CAP_HALF, ink_half=ERR_HALF),
    traj=dict(pen=LINE_PEN, points=TRAJ, marker=MARK),
    legend=dict(sw=LEG_SW, top_d=LEG_TOP_D, row_cy=LEG_ROW_CY, line_w=LEG_LINE_W,
                txgap=LEG_TXGAP, item_gap=LEG_ITEM_GAP, left_dx=LEG_LEFT_DX,
                ink_right=LEG_INK_RIGHT, ink_left=LEG_SW0, ink_top=LEG_INK_TOP,
                ink_bottom=LEG_INK_BOTTOM),
    lanes=dict(tick_dx_r=TICK_DX_R, ytitle_dx_r=YTITLE_DX_R, ytitle_clear=YTITLE_CLEAR,
               xtick_dy_b=XTICK_DY_B, xtitle_dy_b=XTITLE_DY_B, xtitle_dx_c=XTITLE_DX_C,
               cat1_dy_b=CAT1_DY_B, cat2_dy_b=CAT2_DY_B, ctitle_dy_b=CTITLE_DY_B,
               letter_dx_l=LETTER_DX_L, letter_dy_b=LETTER_DY_B, lab_gap=LAB_GAP,
               err_half=ERR_HALF, tick_w=GEO["tick_w"], cross=GEO["cross"]),
    design_ink=[INK_LEFT, INK_TOP, INK_RIGHT, INK_BOTTOM],
    horiz=horiz, rot=rot,
    probe=PROBE,
    symbol_calibration=dict(circle=SCAL["pick"]["circle"], square=SCAL["pick"]["square"],
                            reference_ink_pt=SCAL["reference_ink_pt"]),
    export=dict(png_width=6433, target_ink_width_pt=INK_TARGET_PT,
                target_ink_width_mm=INK_W_MM, target_ink_height_mm=INK_H_MM,
                target_ink_height_pt=INK_TARGET_H_PT),
    qa=dict(allowed_numbers=["26.18", "1.33", "27.36", "12.88", "0", "1", "2", "42", "123",
                             "10", "20", "30", "40", "50", "55"],
            forbidden_numbers=["177.91", "29.22", "0.791", "0.257"],
            forbidden_strings=["hold-out", "headline", "Factor2", "LF_only", "HF_only",
                               "PINN", "PPINN"],
            min_gap_pt=7.0,
            frozen_traj={"W": W_TR, "G": G_TR, "seeds": SEEDS}),
)
json.dump(K, open(os.path.join(OD, "figs2_origin_constants.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

print("offsets available for %d items (%s)" %
      (len(OFFS), "measured" if OFFS else "pre-measurement estimates"))
print("frame  A[%.3f..%.3f] B[%.3f..%.3f]  FT=%.3f FB=%.3f  W=%.4f  gutter=%.4f" %
      (FLA, FRA, FLB, FRB, FT, FB, GEO["w_panel"], GEO["gutter"]))
print("scale  sx_a=%.5f sy_a=%.5f  sx_b=%.5f sy_b=%.5f  bar_half=%.3f" %
      (MP["sx_a"], MP["sy_a"], MP["sx_b"], MP["sy_b"], BAR_HALF_PT))
print("bars   BC1=%.3f BC2=%.3f  cap1=%.3f cap2=%.3f  label ink bottoms %.3f %.3f" %
      (BC1, BC2, CAP1_Y, CAP2_Y, CAP1_Y - ERR_HALF - LAB_GAP, CAP2_Y - ERR_HALF - LAB_GAP))
print("traj   seed1 G y=%.3f (=%.2f pt above FB)  seed123 G y=%.3f (=%.2f pt below FT)" %
      (TRAJ["G"][1]["y_pt"], FB - TRAJ["G"][1]["y_pt"], TRAJ["G"][4]["y_pt"],
       TRAJ["G"][4]["y_pt"] - FT))
print("legend ink x %.3f..%.3f  y %.3f..%.3f  (seed2 G marker x %.3f ink top %.3f)" %
      (LEG_SW0, LEG_INK_RIGHT, LEG_INK_TOP, LEG_INK_BOTTOM, TRAJ["G"][2]["x_pt"],
       TRAJ["G"][2]["y_pt"] - 0.5 * MARK["G"]["ink"]))
print("markers  circle z=%.2f ink %.2f pt | square z=%.2f ink %.2f pt (ref 5.0)" %
      (MARK["W"]["z"], MARK["W"]["ink"], MARK["G"]["z"], MARK["G"]["ink"]))
print("design ink [%.3f %.3f %.3f %.3f] w=%.3f pt (%.4f mm) h=%.3f pt (%.4f mm)" %
      (INK_LEFT, INK_TOP, INK_RIGHT, INK_BOTTOM, INK_RIGHT - INK_LEFT,
       (INK_RIGHT - INK_LEFT) * 25.4 / 72.0, INK_BOTTOM - INK_TOP,
       (INK_BOTTOM - INK_TOP) * 25.4 / 72.0))
print("horiz=%d rot=%d" % (len(horiz), len(rot)))
for it in horiz:
    print("  %-10s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
for it in rot:
    print("  ROT %-10s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
print("DONE_FIGS2_CONSTANTS")
