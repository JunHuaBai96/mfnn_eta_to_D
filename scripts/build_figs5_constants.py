r"""Build outputs/origin_data/figs5_origin_constants.json for the Origin redraw of Fig. S5.

House twin of build_figs2_constants.py (TWO EQUAL-WIDTH panels, 135 mm Elsevier-mid ink,
native ticks/labels/frame off, hand-drawn inward ticks, bars + cap-top annotations), with
the Fig. S1 deviation: the 9 pt axis names are HORIZONTAL (prompt item 8), so the figure
has NO rotated items.  REFUSES TO RUN without figs5_font_calibration.json (figure- and
session-specific, produced by scripts/_z_figs5_fontcal.py).

What this figure fixes about the matplotlib stem (redraw prompt defect list):
  1. the (a) legend gets THREE rows whose swatch colours match the four bar fills
     (grey Separate / orange Joint tracer / sky-blue Joint inter) -- the stem's orange
     swatch on the sky-blue inter-joint bar is the core defect; a two-row legend cannot
     keep the required >= 7 pt clearance from the 156.5% annotation in this geometry;
  2. the two-line Note below (b) is DELETED (Word-caption wording only, same convention
     as Fig. S2 / S4 / main-text Fig. 7);
  3. all THREE (b) annotations sit centred ABOVE the error caps (the stem parked
     39.4+/-39.7 beside the green stem); ylim(0,190) with majors 0..175 keeps >= 7 pt
     from the top inward ticks;
  4. error stems AND caps are #333333 (the stem SVG had matplotlib's default-blue
     #1F77B4 caps);
  5. Arial only: Al\\-(80)Cu\\-(20) origin subscripts, \\x(00B1), no mathtext -> no STIX;
  6. no in-figure suptitle; outside-frame panel titles are "Al80 hold-outs" /
     "Pool-level LOGO means" (no negative-ablation / caution wording);
  7. two equal-width frames, ink closes on 135.0 mm x 72.0 mm, NO_INK_CUT, ~2 pt margins.

Frozen display values (never recomputed): (a) 173.0 / 156.5 / 11.0 / 6.5 %;
(b) 99.66+/-54.55 -> 99.7+/-54.5, 17.96+/-16.90 -> 18.0+/-16.9, 39.4+/-39.7 (FROZEN).

Every text target below is an INK-BOX edge in design pt (top-left origin, y down); the
anchor->ink offsets come from scripts/_z_figs5_measure.py (figs5_text_offsets.json) and
are used as soon as they exist, so a second build tightens the lane closure.
"""
import os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figs5_layout as F
from figs5_layout import (PT, BS, OD, B, OFF, PAGE, PDFX, PDFY, DX, DY, CANV,
                          INK_W_MM, INK_H_MM, INK_TARGET_PT, INK_TARGET_H_PT,
                          FRAME_T, STROKE_HALF, TICK_LEN, BAR_PEN, EB_PEN, EB_CAP_HALF,
                          EB_INK_HALF, SPINE, DARK, BLACK, SEP_COLOR, TRacer_COLOR,
                          INTER_COLOR, JOINT_COLOR, EB_COLOR,
                          A_XF, A_XT, A_YF, A_YT, B_XF, B_XT, B_YF, B_YT,
                          A_XTICKS, A_YTICKS, B_XTICKS, B_YTICKS,
                          A_BAR_W_DU, B_BAR_W_DU,
                          TICK_DX_R, CAT1_DY_B, CAT2_DY_B, YTITLE_DY_B, LAB_GAP,
                          LETTER_DX_L, LEG_RIGHT_DX, LEG_SW, LEG_TXGAP, LEG_ROW_TOPS,
                          EST_TICK_W_8, EST_YTITLE_H, EST_TITLE_H, EST_CAP_H_10,
                          EST_LEG_W, EST_LAB_W, EST_BLAB_W, PROBE)

FCALP = os.path.join(OD, "figs5_font_calibration.json")
assert os.path.exists(FCALP), ("missing figs5_font_calibration.json -- run "
                               "scripts/_z_figs5_fontcal.py first (no calibration, no build)")
FCAL = json.load(open(FCALP, encoding="utf-8-sig"))
FSMAP = dict(FCAL["fs_map"])
for _need in ("7.0", "7.5", "8.0", "9.0", "10.0"):
    assert _need in FSMAP, "figs5_font_calibration.json lacks nominal %s pt" % _need

OFFS = {}
OFFJSON = os.path.join(OD, "figs5_text_offsets.json")
if os.path.exists(OFFJSON):
    OFFS = json.load(open(OFFJSON, encoding="utf-8-sig"))

def inkw(name, est):
    o = OFFS.get(name)
    return (o["jx1"] - o["jx0"]) if o else est
def inkh(name, est):
    o = OFFS.get(name)
    return (o["jy1"] - o["jy0"]) if o else est

META = json.load(open(os.path.join(OD, "figs5_data_meta.json"), encoding="utf-8-sig"))
A_BARS = META["panel_a"]["bars"]
B_BARS = META["panel_b"]["bars"]
assert [b["label"] for b in A_BARS] == ["173.0%", "156.5%", "11.0%", "6.5%"]
assert [b["display"] for b in B_BARS] == ["99.7\u00b154.5", "18.0\u00b116.9", "39.4\u00b139.7"]

GEO = F.geometry(OFFS)
MP = F.maps(GEO)
LAY = {k: F.layer_spec(GEO, k) for k in ("a", "b", "canvas")}
FLA, FRA, FLB, FRB = GEO["fl_a"], GEO["fr_a"], GEO["fl_b"], GEO["fr_b"]
FT, FB, CXA, CXB, CY = GEO["ft"], GEO["fb"], GEO["cx_a"], GEO["cx_b"], GEO["cy"]
CTDY = GEO["ctitle_dy"]
TITLE_TX_L = round(TICK_DX_R - GEO["tick_w"], 4)      # horizontal axis name ink left -> FL

# ---------------------------------------------------------------- panel (a) bars
A_HALF = round((A_BAR_W_DU / 2.0) * MP["sx_a"], 4)
AITEMS = []
for i, b in enumerate(A_BARS):
    AITEMS.append(dict(name="%s_%s" % (b["group"][0], b["series"][0]), x=b["x"],
                       value=b["value"], label=b["label"], fill=b["fill"], edge=b["edge"],
                       x_pt=round(MP["ax2x"](b["x"]), 4),
                       top_pt=round(MP["ay2y"](b["value"]), 4)))
# ---------------------------------------------------------------- panel (b) bars + error bars
B_HALF = round((B_BAR_W_DU / 2.0) * MP["sx_b"], 4)
BITEMS = []
for i, b in enumerate(B_BARS):
    v, e = b["value"], b["err"]
    hi = v + e
    lo = v - e
    BITEMS.append(dict(name="b%d" % i, x=b["x"], value=v, err=e, display=b["display"],
                       fill=b["fill"], edge=b["edge"], cat=b["name"].split(" ", 1),
                       x_pt=round(MP["bx2x"](b["x"]), 4),
                       top_pt=round(MP["by2y"](v), 4),
                       cap_hi_pt=round(MP["by2y"](hi), 4),
                       stem_lo_pt=round(MP["by2y"](max(lo, 0.0)), 4),
                       cap_lo_pt=(round(MP["by2y"](lo), 4) if lo > 0.0 else None)))

# ---------------------------------------------------------------- legend (a, upper-right, 3 rows)
LEG_RIGHT = round(FRA + LEG_RIGHT_DX, 4)
LEG_ROWS = []
for k, (txt, col, est) in enumerate((
        ("Separate pools (12-D)", SEP_COLOR, EST_LEG_W[0]),
        ("Joint tracer", TRacer_COLOR, EST_LEG_W[1]),
        ("Joint inter", INTER_COLOR, EST_LEG_W[2]))):
    nm = "LgA_%d" % (k + 1)
    tw = inkw(nm, est)
    th = inkh(nm, 5.1)
    top = FT + LEG_ROW_TOPS[k]
    tx_left = round(LEG_RIGHT - tw, 4)
    sw_right = round(tx_left - LEG_TXGAP, 4)
    sw_left = round(sw_right - LEG_SW["w"], 4)
    LEG_ROWS.append(dict(name=nm, text=txt, fill=col["fill"], edge=col["edge"],
                         tx_left=tx_left, ink_top=round(top, 4),
                         cy=round(top + 0.5 * th, 4),
                         sw=[sw_left, round(sw_left + LEG_SW["w"], 4)],
                         ink_right=LEG_RIGHT))
LEG_INK_LEFT = min(r["sw"][0] for r in LEG_ROWS)
LEG_INK_TOP = round(LEG_ROW_TOPS[0] + FT - max(0.0, 0.5 * (inkh("LgA_1", 5.1) - LEG_SW["h"])), 4)
LEG_INK_BOTTOM = round(max(r["cy"] + 0.5 * LEG_SW["h"] for r in LEG_ROWS), 4)

# ---------------------------------------------------------------- typography
def H(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, ax=ax, tx=round(tx, 4), ay=ay,
                ty=round(ty, 4), rot=False)
def key(v):
    return ("%g" % v).replace(".", "p").replace("-", "m")

PM = BS + "x(00B1)"
AL = "Al" + BS + "-(80)Cu" + BS + "-(20)"
horiz = [
    H("A_letter", BS + "b((a))", 10.0, BLACK, "left", FLA + LETTER_DX_L, "bottom", FT - CTDY),
    H("A_ctitle", "Al80 hold-outs", 8.0, BLACK, "center", CXA, "bottom", FT - CTDY),
    H("A_ytitle", "MFNN MAPE (%)", 9.0, DARK, "left", FLA + TITLE_TX_L, "bottom", FT - YTITLE_DY_B),
]
for v in A_YTICKS:
    horiz.append(H("A_yt_%s" % key(v), "%g" % v, 8.0, BLACK, "right", FLA + TICK_DX_R,
                   "center", MP["ay2y"](v)))
for it in AITEMS:
    horiz.append(H("A_lab_" + it["name"], it["label"], 7.5, DARK, "center", it["x_pt"],
                   "bottom", round(it["top_pt"] - BAR_PEN / 2.0 - LAB_GAP, 4)))
horiz += [
    H("A_cat1_1", AL, 8.0, BLACK, "center", MP["ax2x"](0.0), "bottom", FB + CAT1_DY_B),
    H("A_cat1_2", "tracer", 8.0, BLACK, "center", MP["ax2x"](0.0), "bottom", FB + CAT2_DY_B),
    H("A_cat2_1", AL, 8.0, BLACK, "center", MP["ax2x"](1.0), "bottom", FB + CAT1_DY_B),
    H("A_cat2_2", "inter", 8.0, BLACK, "center", MP["ax2x"](1.0), "bottom", FB + CAT2_DY_B),
    H("B_letter", BS + "b((b))", 10.0, BLACK, "left", FLB + LETTER_DX_L, "bottom", FT - CTDY),
    H("B_ctitle", "Pool-level LOGO means", 8.0, BLACK, "center", CXB, "bottom", FT - CTDY),
    H("B_ytitle", "Mean LOGO MFNN MAPE (%)", 9.0, DARK, "left", FLB + TITLE_TX_L,
      "bottom", FT - YTITLE_DY_B),
]
for v in B_YTICKS:
    horiz.append(H("B_yt_%s" % key(v), "%g" % v, 8.0, BLACK, "right", FLB + TICK_DX_R,
                   "center", MP["by2y"](v)))
for it in BITEMS:
    horiz.append(H("B_lab_" + it["name"], it["display"].replace("\u00b1", PM), 7.5, DARK,
                   "center", it["x_pt"], "bottom", round(it["cap_hi_pt"] - EB_INK_HALF - LAB_GAP, 4)))
B_CATS = [["Separate", "tracer pool"], ["Separate", "inter (excl. Al70)"], ["Joint+one-hot", "(13 folds)"]]
for i, (c1, c2) in enumerate(B_CATS):
    horiz.append(H("B_cat%d_1" % (i + 1), c1, 7.0, BLACK, "center", MP["bx2x"](float(i)),
                   "bottom", FB + CAT1_DY_B))
    horiz.append(H("B_cat%d_2" % (i + 1), c2, 7.0, BLACK, "center", MP["bx2x"](float(i)),
                   "bottom", FB + CAT2_DY_B))
for r in LEG_ROWS:
    horiz.append(H(r["name"], r["text"], 7.0, BLACK, "left", r["tx_left"], "top", r["ink_top"]))
rot = []

INK_LEFT = round(FLA - GEO["lhang"], 4)
INK_RIGHT = round(FRB + STROKE_HALF, 4)
INK_TOP = round(FT - GEO["top_hang"], 4)
INK_BOTTOM = round(FB + GEO["bhang"], 4)

K = dict(
    note="Fig. S5 Origin redraw (SI negative ablation: separate tracer/inter pools vs joint "
         "+ diff_type one-hot; splitting does NOT beat joint). Okabe-Ito, Arial only, closed "
         "4-side box, hand-drawn inward ticks on all four sides, HORIZONTAL 9 pt axis names "
         "(Fig. S1 convention), NO in-figure suptitle, NO Note below (b), THREE-row legend "
         "with swatch colours matching the four bar fills, error stems AND caps #333333, two "
         "EQUAL-width frames, ink 135.0 mm x 72.0 mm.",
    pt=PT, off_cm=OFF, page_cm=PAGE, fs_map=FSMAP,
    font_calibration=dict(rendered=FSMAP, source="figs5_font_calibration.json"),
    decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY),
    canvas=CANV, spine=SPINE, dark=DARK, black=BLACK,
    sep_color=SEP_COLOR, tracer_color=TRacer_COLOR, inter_color=INTER_COLOR,
    joint_color=JOINT_COLOR, eb_color=EB_COLOR,
    tick=dict(len_nom=3.6, len_rendered=TICK_LEN, thick=FRAME_T,
              label_fs=8.0, label_color=BLACK, title_fs=9.0, title_color=DARK),
    frame=dict(FT=FT, FB=FB, FL_A=FLA, FR_A=FRA, FL_B=FLB, FR_B=FRB,
               sx_a=MP["sx_a"], sy_a=MP["sy_a"], sx_b=MP["sx_b"], sy_b=MP["sy_b"],
               cx_a=CXA, cx_b=CXB, cy=CY, w_panel=GEO["w_panel"], gutter=GEO["gutter"],
               lhang=GEO["lhang"], top_hang=GEO["top_hang"], bhang=GEO["bhang"],
               a_xticks=A_XTICKS, a_yticks=A_YTICKS, b_xticks=B_XTICKS, b_yticks=B_YTICKS),
    layers=dict(a=LAY["a"], b=LAY["b"], canvas=LAY["canvas"]),
    bars_a=dict(width_du=A_BAR_W_DU, half_pt=A_HALF, pen=BAR_PEN, items=AITEMS),
    bars_b=dict(width_du=B_BAR_W_DU, half_pt=B_HALF, pen=BAR_PEN, items=BITEMS),
    errbar=dict(color=EB_COLOR, pen=EB_PEN, cap_half=EB_CAP_HALF, ink_half=EB_INK_HALF),
    legend=dict(right=LEG_RIGHT, sw=LEG_SW, txgap=LEG_TXGAP, rows=LEG_ROWS,
                ink_left=LEG_INK_LEFT, ink_top=LEG_INK_TOP, ink_bottom=LEG_INK_BOTTOM),
    lanes=dict(tick_dx_r=TICK_DX_R, title_tx_l=TITLE_TX_L, ytitle_dy_b=YTITLE_DY_B,
               ctitle_dy=CTDY, cat1_dy_b=CAT1_DY_B, cat2_dy_b=CAT2_DY_B,
               letter_dx_l=LETTER_DX_L, lab_gap=LAB_GAP, tick_w=GEO["tick_w"],
               ytitle_h=GEO["ytitle_h"]),
    design_ink=[INK_LEFT, INK_TOP, INK_RIGHT, INK_BOTTOM],
    horiz=horiz, rot=rot,
    probe=PROBE,
    export=dict(png_width=6433, target_ink_width_pt=INK_TARGET_PT,
                target_ink_width_mm=INK_W_MM, target_ink_height_mm=INK_H_MM,
                target_ink_height_pt=INK_TARGET_H_PT),
    qa=dict(allowed_numbers=["173.0", "156.5", "11.0", "6.5", "99.7", "54.5", "18.0",
                             "16.9", "39.4", "39.7", "0", "50", "100", "150", "200",
                             "25", "75", "125", "175", "12", "13"],
            forbidden_numbers=["173.29", "156.49", "10.95", "6.48", "39.43", "39.71",
                               "62.99", "18.25", "173.3", "173%"],
            forbidden_strings=["negative ablation", "caution", "Note", "Factor2", "n=",
                               "HF_only", "LF_only", "PINN", "PPINN", "Al70Cu30",
                               "explosion", "one-hot (13", "Separate pools (12-D) 13"],
            min_gap_pt=7.0,
            frozen_display=dict(a=["173.0%", "156.5%", "11.0%", "6.5%"],
                                b=["99.7+/-54.5", "18.0+/-16.9", "39.4+/-39.7"])),
)
json.dump(K, open(os.path.join(OD, "figs5_origin_constants.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

print("offsets available for %d items (%s)" %
      (len(OFFS), "measured" if OFFS else "pre-measurement estimates"))
print("frame  A[%.3f..%.3f] B[%.3f..%.3f]  FT=%.3f FB=%.3f  W=%.4f  gutter=%.4f" %
      (FLA, FRA, FLB, FRB, FT, FB, GEO["w_panel"], GEO["gutter"]))
print("scale  sx_a=%.5f sy_a=%.5f  sx_b=%.5f sy_b=%.5f  a_half=%.3f b_half=%.3f" %
      (MP["sx_a"], MP["sy_a"], MP["sx_b"], MP["sy_b"], A_HALF, B_HALF))
print("design ink [%.3f %.3f %.3f %.3f] w=%.3f pt (%.4f mm) h=%.3f pt (%.4f mm)" %
      (INK_LEFT, INK_TOP, INK_RIGHT, INK_BOTTOM, INK_RIGHT - INK_LEFT,
       (INK_RIGHT - INK_LEFT) * 25.4 / 72.0, INK_BOTTOM - INK_TOP,
       (INK_BOTTOM - INK_TOP) * 25.4 / 72.0))
print("legend ink x %.3f..%.3f  y %.3f..%.3f" % (LEG_INK_LEFT, LEG_RIGHT, LEG_INK_TOP, LEG_INK_BOTTOM))
print("a labels ink bottoms: %s" % ["%.2f" % it["ty"] for it in horiz if it["name"].startswith("A_lab")])
print("b caps y: %s  labels ink bottoms: %s" %
      (["%.2f" % it["cap_hi_pt"] for it in BITEMS],
       ["%.2f" % it["ty"] for it in horiz if it["name"].startswith("B_lab")]))
print("horiz=%d rot=%d" % (len(horiz), len(rot)))
for it in horiz:
    print("  %-12s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
print("DONE_FIGS5_CONSTANTS")
