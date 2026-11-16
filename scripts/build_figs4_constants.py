r"""Build outputs/origin_data/figs4_origin_constants.json for the Origin redraw of Fig. S4.

House twin of build_fig6_constants.py / build_fig7_constants.py, but SINGLE-COLUMN:
the ink width is the SI single-column target 88.0 mm (3.4646 in), NOT the 6.30 in of
the main-text figures.  Canvas / page / decoy settings are taken unchanged from the
Fig.7 house recipe (page 24 x 15 cm, canvas offset 0.05 cm, OFF 0.25, PDF = design +
(7.0866, 7.0866) pt, 1 pt = 1 pt) because that is a known-good Origin 2026 export
configuration.

Style parity with the family (Fig.6 panel B / Fig.7):
  * closed 4-side box #333333 at 0.75 pt, inward major ticks 3.36 pt rendered
    (nominal 3.6), NO minor ticks, NO grid; Origin draws no ticks and no labels at
    all -- both are hand-placed, so all four sides get identical inward ticks;
  * Arial throughout (Origin \i \b \-(...) \x(...) markup, NO mathtext -> no STIX);
    log10 uses a REAL Arial subscript "10", exactly like main-text Fig.4;
  * NO in-figure suptitle (the caution wording lives in the Word caption);
  * axis title 9 pt, tick labels 8 pt, category names 8 pt (two lines), bar-top
    annotations 7.5 pt, delta note 7.5 pt -- nothing below 7 pt;
  * Okabe-Ito colours frozen: raw #D55E00/#994300, shift #009E73/#006B4E,
    error bars + frame + ticks #333333.

Frozen numbers (hardcoded from scripts/prepare_figs4_origin_data.py, never recomputed):
  raw 175.20 +/- 28.78 %, shift 9.81 +/- 1.73 %, delta note "0.482 +/- 0.046 ~ -log10 3".

Every text target below is an INK-BOX edge in design pt (top-left origin).  The
anchor->ink offsets are measured on the F4PROBE page by scripts/_z_figs4_measure.py.
"""
import os, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PT = 72.0 / 2.54
OFF = 0.25                                  # cm, house canvas/page inset
PDFX = PDFY = 7.0866                        # = OFF * PT : design -> exported-PDF pt
DX = round(PDFX - 0.05 * PT, 4)             # 5.6693
PAGE = [24.0, 15.0]                         # cm, Fig.7 house canvas
DY = round(0.05 * PT + PAGE[1] * PT - PDFY, 4)   # 419.5276

# fsize -> rendered pt is session/page specific (scripts/_z_figs4_fontcal.py): the
# Fig.4/6/7 fs_map renders ~9-11 % too large in this environment, so the map comes from
# the measured calibration, whose TARGETS are the Fig.6/Fig.7 delivered-PDF sizes
# (nominal 8 pt -> 8.40, 9 pt -> 9.60, 7.5 pt -> 7.92).  No calibration file -> no build.
FCAL = json.load(open(os.path.join(OD, "figs4_font_calibration.json"), encoding="utf-8-sig"))
FSMAP = dict(FCAL["fs_map"])               # nominal -> [grid index, rendered pt, fsize to set]
for _need in ("7.5", "8.0", "9.0"):
    assert _need in FSMAP, "figs4_font_calibration.json lacks nominal %s pt" % _need

# ---------------- data-space mapping (frozen geometry of the current figure) -------
XLO, XHI = -0.45, 1.30                      # xlim of the matplotlib reference
YLO, YHI = 0.0, 250.0                       # ylim(0,250): headroom for cap + label
YTICKS = [0.0, 50.0, 100.0, 150.0, 200.0]   # 250 is NOT labelled (reference behaviour)
XTICKS = [0.0, 0.85]                        # the two bar centres
BC = [0.0, 0.85]
BAR_W_DU = 0.55

# ---------------- frame -------------------------------------------------------------
INK_TARGET_MM = 88.0
INK_TARGET_PT = round(INK_TARGET_MM * 72.0 / 25.4, 3)          # 249.449
INK_TARGET_H_MM = 92.0
FL = 33.0
FT = 26.0
STROKE_HALF = 0.75 / 2.0                    # frame line ink sticks out 0.375 pt
# left overhang: rotated 9 pt axis name -> ink right at FL-24.0, cross ink ~9 pt wide
LHANG_EST = 24.0 + 9.0                      # 33.0 -> ink left ~ FL-33.0
# bottom overhang: two 8 pt category lines below the frame (lane measured on the probe)
CAT1_DY_B = 10.93                           # line-1 ink bottom - frame bottom (ref value)
CAT2_DY_B = 19.51                           # line-2 ink bottom - frame bottom (measured on
                                            # the frozen matplotlib Fig. S4 PDF: 240.71-221.20)
BHANG_EST = CAT2_DY_B + STROKE_HALF
# Ink-width closure, measured on two delivered renders (vector read-back of the four
# spines in _z_figs4_occ.py + figs4_finalize_report.json):
#     W_F = 216.074 -> ink width 249.546 pt (raster-threshold 249.550)
#     W_F = 215.977 -> ink width 249.378 pt (raster-threshold 249.300)
# i.e. d(ink)/d(W_F) = 1.73, because Origin quantises the layer width in cm.  Solving
# 249.378 + 1.73*dW = 249.449 gives dW = +0.041, so W_F = 216.018 and the ink width is
# 88.000 mm to within Origin's ~0.05 pt page-unit resolution (the raster threshold adds
# a further +-0.25 pt of antialiasing noise, which is why the vector read-back is the
# number reported in the self-check).
INK_X_EXTRA = 0.431
W_F = round(INK_TARGET_PT - LHANG_EST - INK_X_EXTRA, 3)     # 216.018
H_F = round(INK_TARGET_H_MM * 72.0 / 25.4 - BHANG_EST, 3)      # 240.902
FR = round(FL + W_F, 3)
FB = round(FT + H_F, 3)
SX = W_F / (XHI - XLO)
SY = H_F / (YHI - YLO)
CX = 0.5 * (FL + FR)
CY = 0.5 * (FT + FB)

def bx2x(v): return FL + (v - XLO) * SX
def by2y(v): return FB - (v - YLO) * SY

# ---------------- frozen display values --------------------------------------------
RAW_M, RAW_E = 175.20, 28.78
SH_M, SH_E = 9.81, 1.73

# ---------------- colours (frozen) --------------------------------------------------
SPINE = "#333333"; DARK = "#333333"; BLACK = "#000000"
RAWC = dict(fill="#D55E00", edge="#994300")
SHC = dict(fill="#009E73", edge="#006B4E")

# ---------------- lanes / gaps ------------------------------------------------------
TICK_DX_R = -4.0            # tick-label lane, identical to Fig.6 B (-3.819) / the ref (3.51)
YTITLE_DX_R = -24.0         # axis name ink right - frame left -> >=7 pt clear of "200"
NOTE_BOX_GAP_R = 12.0       # note BOX right  - frame right; measured on the deliverable:
                            #   8.18 pt to the right-spine tick ink, 11.6 pt to the spine
NOTE_BOX_GAP_T = 12.0       # note BOX top    - frame top;   measured: 8.02 pt to the
                            #   inward x-tick ink (the axis ink sits ~0.83 pt below the
                            #   design top edge, so 11.0 would have left only 7.04 pt)
NOTE_PAD_X = 3.0            # box padding around the note ink  (ref boxstyle pad=0.25*7.5=1.875)
NOTE_PAD_Y = 2.2
ERR_HALF = 0.8 / 2.0            # error-bar stroke half (ink sticks 0.4 pt past the cap line)
LAB_GAP = 7.0                  # bar-top annotation ink bottom -> error-cap INK top (>=7)
BAR_PEN = 0.6
ERRBAR = dict(color=SPINE, pen=0.8, cap_half=2.5)   # 5.0 pt total cap ink, as the ref
TL = 3.36                                           # rendered inward tick length

CAP1_Y = round(by2y(RAW_M + RAW_E), 4)
CAP2_Y = round(by2y(SH_M + SH_E), 4)
BC1 = round(bx2x(BC[0]), 4)
BC2 = round(bx2x(BC[1]), 4)
BAR_HALF_PT = round(0.5 * BAR_W_DU * SX, 4)

BS = chr(92)
def H(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=False,
                ax=ax, tx=round(tx, 4), ay=ay, ty=round(ty, 4))
def R(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=True,
                ax=ax, tx=round(tx, 4), ay=ay, ty=round(ty, 4))

horiz = []
for v in YTICKS:
    horiz.append(H("y_t_%d" % v, "%d" % v, 8.0, BLACK, "right", FL + TICK_DX_R, "center", by2y(v)))
CAT = ["Raw held-out", "(no shift)", "Post-hoc B2", "intercept shift"]
for i, t in enumerate(CAT[:2]):
    horiz.append(H("cat1_%d" % (i + 1), t, 8.0, BLACK, "center", BC1, "bottom", FB + (CAT1_DY_B if i == 0 else CAT2_DY_B)))
for i, t in enumerate(CAT[2:]):
    horiz.append(H("cat2_%d" % (i + 1), t, 8.0, BLACK, "center", BC2, "bottom", FB + (CAT1_DY_B if i == 0 else CAT2_DY_B)))
horiz.append(H("bar1_lab", "175.20" + BS + "x(00B1)28.78%", 7.5, DARK, "center", BC1, "bottom", CAP1_Y - ERR_HALF - LAB_GAP))
horiz.append(H("bar2_lab", "9.81" + BS + "x(00B1)1.73%", 7.5, DARK, "center", BC2, "bottom", CAP2_Y - ERR_HALF - LAB_GAP))
# delta note: ink RIGHT/TOP pinned so that the box (drawn around the measured ink in the
# plot script) lands NOTE_BOX_GAP_* inside the frame on the top-right.
horiz.append(H("delta_note", BS + "x(03B4) = " + BS + "x(2212)0.482 " + BS + "x(00B1) 0.046 "
               + BS + "x(2248) " + BS + "x(2212)log" + BS + "-(10) 3",
               7.5, DARK, "right", round(FR - NOTE_BOX_GAP_R - NOTE_PAD_X, 4), "top",
               round(FT + NOTE_BOX_GAP_T + NOTE_PAD_Y, 4)))
rot = [R("y_title", "MFNN MAPE (%)", 9.0, DARK, "right", FL + YTITLE_DX_R, "center", CY)]

K = dict(
    note="Fig. S4 Origin redraw (SI mechanism diagnostic). Okabe-Ito, Arial only, closed "
         "box, inward ticks on all four sides, no in-figure suptitle, single-column 88 mm ink.",
    pt=PT, off_cm=OFF, page_cm=PAGE, fs_map=FSMAP,
    decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY),
    canvas=dict(left=0.05, top=0.05, width=PAGE[0], height=PAGE[1]),
    spine=SPINE, dark=DARK, black=BLACK, raw=RAWC, shift=SHC,
    tick=dict(len_nom=3.6, len_rendered=TL, thick=0.75,
              label_fs=8.0, label_color=BLACK, title_fs=9.0, title_color=DARK),
    frame=dict(FT=FT, FB=FB, FL=FL, FR=FR, sx=SX, sy=SY, cx=CX, cy=CY),
    layers=dict(a=dict(left=round(OFF + FL / PT, 5), top=round(OFF + FT / PT, 5),
                       width=round(W_F / PT, 5), height=round(H_F / PT, 5),
                       xf=XLO, xt=XHI, yf=YLO, yt=YHI,
                       xticks=XTICKS, yticks=YTICKS)),
    bars=dict(centres=BC, width_du=BAR_W_DU, half_pt=BAR_HALF_PT, pen=BAR_PEN,
              items=[dict(x=BC[0], value=RAW_M, err=RAW_E, fill=RAWC["fill"], edge=RAWC["edge"],
                          name="Raw held-out (no shift)"),
                     dict(x=BC[1], value=SH_M, err=SH_E, fill=SHC["fill"], edge=SHC["edge"],
                          name="Post-hoc B2 intercept shift")]),
    errbar=ERRBAR,
    note_box=dict(gap_right=NOTE_BOX_GAP_R, gap_top=NOTE_BOX_GAP_T, pad_x=NOTE_PAD_X,
              pad_y=NOTE_PAD_Y, edge=SHC["edge"], pen=0.5),
    lanes=dict(tick_dx_r=TICK_DX_R, ytitle_dx_r=YTITLE_DX_R, cat1_dy_b=CAT1_DY_B,
               cat2_dy_b=CAT2_DY_B, lab_gap=LAB_GAP, cap1_y=CAP1_Y, cap2_y=CAP2_Y,
               bc1=BC1, bc2=BC2),
    horiz=horiz, rot=rot,
    probe=dict(x0=10.0, x_step=170.0, per_col=10, y0=10.0, y_step=22.0,
               win_x0=-4.0, win_x1=165.0, win_y0=-3.0, win_y1=17.0,
               rot_x0=745.0, rot_dx=60.0, rot_y=40.0, rot_win_x=30.0, rot_win_y=150.0),
    export=dict(png_width=6433,
                target_ink_width_pt=INK_TARGET_PT, target_ink_width_mm=INK_TARGET_MM,
                target_ink_height_mm=INK_TARGET_H_MM),
    qa=dict(forbidden_numbers=["177.91", "29.22", "-0.444", "0.0544", "0.059"],
            allowed_numbers=["175.20", "28.78", "9.81", "1.73", "0.482", "0.046"],
            min_gap_pt=7.0),
)
json.dump(K, open(os.path.join(OD, "figs4_origin_constants.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print("frame  FL=%.3f FR=%.3f W=%.3f | FT=%.3f FB=%.3f H=%.3f" % (FL, FR, W_F, FT, FB, H_F))
print("scale  sx=%.5f pt/data-x  sy=%.5f pt/%%   CY=%.3f CX=%.3f" % (SX, SY, CY, CX))
print("bars   BC1=%.3f BC2=%.3f half=%.3f | CAP1=%.3f CAP2=%.3f" % (BC1, BC2, BAR_HALF_PT, CAP1_Y, CAP2_Y))
print("bar tops: raw %.3f  shift %.3f ; label ink bottoms %.3f %.3f (= cap centre - err_half - lab_gap)" %
      (by2y(RAW_M), by2y(SH_M), CAP1_Y - ERR_HALF - LAB_GAP, CAP2_Y - ERR_HALF - LAB_GAP))
print("headroom: bar1 label ink top ~ frame top + %.1f pt (needs >= 7)" %
      (CAP1_Y - ERR_HALF - LAB_GAP - 5.875 - FT))
print("design ink: x %.3f..%.3f (w=%.3f = %.3f mm) ; y %.3f..%.3f (h=%.1f mm)" %
      (FL - LHANG_EST, FR + STROKE_HALF, INK_TARGET_PT, INK_TARGET_MM,
       FT - STROKE_HALF, FB + BHANG_EST, (BHANG_EST + H_F + STROKE_HALF) * 25.4 / 72.0))
print("horiz=%d rot=%d" % (len(horiz), len(rot)))
for it in horiz:
    print("  %-10s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
for it in rot:
    print("  ROT %-10s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
print("DONE_FIGS4_CONSTANTS")


