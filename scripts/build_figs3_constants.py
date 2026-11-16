r"""Build outputs/origin_data/figs3_origin_constants.json for the Origin redraw of Fig. S3.

House twin of build_figs4_constants.py (single-column SI diagnostic), adapted to FOUR
tracer bars with cap-above one-decimal annotations and NO delta note box:
  * ink width = 88.0 mm (3.4646 in) single-column target, ink height target 60.0 mm
    (band 55..65 mm after the in-figure suptitle was deleted); NOT the 135 mm of Fig. S2,
    NOT the 6.30 in of the main-text figures;
  * canvas / page / decoy unchanged from the Fig.7 house recipe (page 24 x 15 cm,
    canvas inset 0.05 cm, OFF 0.25 cm, PDF pt = design pt + (7.0866, 7.0866));
  * closed 4-side box #333333 at 0.75 pt, hand-drawn inward major ticks 3.36 pt rendered,
    NO minor ticks, NO grid; Origin draws no native ticks/labels/frame (2026 theme emits
    SimSun), every string is hand-placed from measured ink boxes -> Arial only;
  * NO in-figure suptitle and NO 'Factor2 = 0 (all k)' ink: both live in the Word caption;
  * axis title 9 pt ("MFNN MAPE (%)", rotated upright), tick labels 8 pt, category names
    8 pt (family bump from the stem's 7.5 pt), bar-top annotations 7.5 pt, nothing < 7 pt;
    single panel, no (a) label;
  * Okabe-Ito tracer colours frozen: fill #D55E00, edge #994300 at 0.6 pt, error bars
    #333333 at 0.8 pt with 2.5 pt half-caps (5.0 pt total cap ink, as the stem);
  * frozen display values ONLY (hardcoded, never recomputed): heights 178.20/169.55/
    175.27/142.93, labels 178.2/169.6/175.3/142.9, error bars = 5-seed population std
    (ddof=0) 29.053385/35.509400/32.925206/35.532553.

fsize -> rendered pt comes from scripts/_z_figs3_fontcal.py (measured in THIS page/
canvas/layer environment); no calibration file -> refuse to run.

Every text target below is an INK-BOX edge in design pt (top-left origin).  The
anchor->ink offsets are measured on the F3PROBE page by scripts/_z_figs3_measure.py.
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

FCALP = os.path.join(OD, "figs3_font_calibration.json")
if not os.path.exists(FCALP):
    sys.exit("REFUSING TO BUILD: run scripts/_z_figs3_fontcal.py first "
             "(missing " + FCALP + ")")
FCAL = json.load(open(FCALP, encoding="utf-8-sig"))
FSMAP = dict(FCAL["fs_map"])               # nominal -> [grid index, rendered pt, fsize to set]
for _need in ("7.5", "8.0", "9.0"):
    assert _need in FSMAP, "figs3_font_calibration.json lacks nominal %s pt" % _need

# ---------------- data-space mapping (frozen geometry of the current figure) -------
XLO, XHI = -0.5, 3.5                        # xlim of the matplotlib reference (bars 0..3)
YLO, YHI = 0.0, 250.0                       # ylim(0,250): headroom for cap + label
YTICKS = [0.0, 50.0, 100.0, 150.0, 200.0, 250.0]   # all six labelled (stem behaviour)
XTICKS = [0.0, 1.0, 2.0, 3.0]               # the four bar centres
BC = [0.0, 1.0, 2.0, 3.0]
BAR_W_DU = 0.6

# ---------------- frame -------------------------------------------------------------
INK_TARGET_MM = 88.0
INK_TARGET_PT = round(INK_TARGET_MM * 72.0 / 25.4, 3)          # 249.449
INK_TARGET_H_MM = 60.0
INK_TARGET_H_PT = round(INK_TARGET_H_MM * 72.0 / 25.4, 3)      # 170.079
INK_HEIGHT_BAND_MM = [55.0, 65.0]
FL = 33.0
FT = 26.0
STROKE_HALF = 0.75 / 2.0                    # frame line ink sticks out 0.375 pt
# left overhang: rotated 9 pt axis name -> ink right at FL-24.0, cross ink ~9 pt wide
LHANG_EST = 24.0 + 9.0                      # 33.0 -> ink left ~ FL-33.0
# bottom overhang: ONE category line below the frame (family line-1 lane, measured on
# the Fig. S4 probe: ink bottom 10.93 pt below the frame bottom centreline)
CAT_DY_B = 10.93
BHANG_EST = CAT_DY_B + STROKE_HALF
# top overhang: the "250" tick label is centred ON the top spine, so its ink (8 pt
# digits measured 6.25 pt tall on the family probe) sticks 3.125 pt above the frame.
TOPHANG_EST = 6.25 / 2.0
# Ink-width closure (measured on the delivered Fig. S4 renders; the left lane, the axis
# name and the right stroke are byte-identical here, so the same numbers carry over):
#     W_F = 216.018 -> ink width 249.449 pt (88.000 mm) at Origin's ~0.05 pt page-unit
#     resolution; d(ink)/d(W_F) = 1.73 because Origin quantises the layer size in cm.
INK_X_EXTRA = 0.431
W_F = round(INK_TARGET_PT - LHANG_EST - INK_X_EXTRA, 3)     # 216.018
H_F = round(INK_TARGET_H_PT - CAT_DY_B - TOPHANG_EST, 3)    # 156.024 (first pass; the
                                            # finalize report closes it on the render).
                                            # top ink = "250" label at FT-3.125, bottom
                                            # ink = category line at FB+10.93; the 0.375
                                            # stroke half-widths are inside both.
FR = round(FL + W_F, 3)
FB = round(FT + H_F, 3)
SX = W_F / (XHI - XLO)
SY = H_F / (YHI - YLO)
CX = 0.5 * (FL + FR)
CY = 0.5 * (FT + FB)

def bx2x(v): return FL + (v - XLO) * SX
def by2y(v): return FB - (v - YLO) * SY

# ---------------- frozen display values --------------------------------------------
VAL = [178.20, 169.55, 175.27, 142.93]          # FROZEN["S1_MAPE"] (legacy key = Fig. S3)
ERR = [29.053385, 35.509400, 32.925206, 35.532553]   # 5-seed POPULATION std (ddof=0)
LAB = ["178.2", "169.6", "175.3", "142.9"]      # one decimal, rounded from the frozen
CATS = ["k = 0", "k = 1 low T", "k = 1 high T", "k = 2"]

# ---------------- colours (frozen) --------------------------------------------------
SPINE = "#333333"; DARK = "#333333"; BLACK = "#000000"
TRACER = dict(fill="#D55E00", edge="#994300")

# ---------------- lanes / gaps ------------------------------------------------------
TICK_DX_R = -4.0            # tick-label lane, identical to Fig.6 B / Fig. S4 / the ref
YTITLE_DX_R = -24.0         # axis name ink right - frame left -> >=7 pt clear of "250"
ERR_HALF = 0.8 / 2.0        # error-bar stroke half (ink sticks 0.4 pt past the cap line)
LAB_GAP = 7.0               # bar-top annotation ink bottom -> error-cap INK top (>=7)
BAR_PEN = 0.6
ERRBAR = dict(color=SPINE, pen=0.8, cap_half=2.5)   # 5.0 pt total cap ink, as the stem
TL = 3.36                                           # rendered inward tick length

CAP_Y = [round(by2y(VAL[i] + ERR[i]), 4) for i in range(4)]
BCX = [round(bx2x(BC[i]), 4) for i in range(4)]
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
for i, t in enumerate(CATS):
    horiz.append(H("cat_%d" % (i + 1), t, 8.0, BLACK, "center", BCX[i], "bottom", FB + CAT_DY_B))
for i, t in enumerate(LAB):
    horiz.append(H("bar%d_lab" % (i + 1), t, 7.5, DARK, "center", BCX[i], "bottom",
                   CAP_Y[i] - ERR_HALF - LAB_GAP))
rot = [R("y_title", "MFNN MAPE (%)", 9.0, DARK, "right", FL + YTITLE_DX_R, "center", CY)]

K = dict(
    note="Fig. S3 Origin redraw (SI few-shot anchor-k diagnostic). Okabe-Ito tracer, "
         "Arial only, closed box, inward ticks on all four sides, NO in-figure suptitle, "
         "NO Factor2 ink, single-column 88 mm x 60 mm ink.",
    pt=PT, off_cm=OFF, page_cm=PAGE, fs_map=FSMAP,
    decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY),
    canvas=dict(left=0.05, top=0.05, width=PAGE[0], height=PAGE[1]),
    spine=SPINE, dark=DARK, black=BLACK, tracer=TRACER,
    tick=dict(len_nom=3.6, len_rendered=TL, thick=0.75,
              label_fs=8.0, label_color=BLACK, title_fs=9.0, title_color=DARK),
    frame=dict(FT=FT, FB=FB, FL=FL, FR=FR, sx=SX, sy=SY, cx=CX, cy=CY),
    layers=dict(a=dict(left=round(OFF + FL / PT, 5), top=round(OFF + FT / PT, 5),
                       width=round(W_F / PT, 5), height=round(H_F / PT, 5),
                       xf=XLO, xt=XHI, yf=YLO, yt=YHI,
                       xticks=XTICKS, yticks=YTICKS)),
    bars=dict(centres=BC, width_du=BAR_W_DU, half_pt=BAR_HALF_PT, pen=BAR_PEN,
              items=[dict(x=BC[i], value=VAL[i], err=ERR[i], label=LAB[i],
                          fill=TRACER["fill"], edge=TRACER["edge"], category=CATS[i])
                     for i in range(4)]),
    errbar=ERRBAR,
    lanes=dict(tick_dx_r=TICK_DX_R, ytitle_dx_r=YTITLE_DX_R, cat_dy_b=CAT_DY_B,
               lab_gap=LAB_GAP, cap_y=CAP_Y, bc=BCX),
    horiz=horiz, rot=rot,
    probe=dict(x0=20.0, x_step=170.0, per_col=6, y0=10.0, y_step=30.0,
               win_x0=-4.0, win_x1=165.0, win_y0=-3.0, win_y1=17.0,
               rot_x0=745.0, rot_dx=60.0, rot_y=40.0, rot_win_x=30.0, rot_win_y=150.0),
    export=dict(png_width=6433,
                target_ink_width_pt=INK_TARGET_PT, target_ink_width_mm=INK_TARGET_MM,
                target_ink_height_mm=INK_TARGET_H_MM, ink_height_band_mm=INK_HEIGHT_BAND_MM),
    qa=dict(forbidden_numbers=["178.20", "169.55", "175.27", "142.93", "32.482672",
                               "39.700716", "36.811499", "39.726602"],
            forbidden_words=["Factor2", "Few-shot", "diagnostic", "LOGO", "PINN", "PPINN",
                             "LF_only", "HF_only"],
            allowed_numbers=["178.2", "169.6", "175.3", "142.9",
                             "0", "50", "100", "150", "200", "250"],
            min_gap_pt=7.0),
)
json.dump(K, open(os.path.join(OD, "figs3_origin_constants.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print("frame  FL=%.3f FR=%.3f W=%.3f | FT=%.3f FB=%.3f H=%.3f" % (FL, FR, W_F, FT, FB, H_F))
print("scale  sx=%.5f pt/data-x  sy=%.5f pt/%%   CY=%.3f CX=%.3f" % (SX, SY, CY, CX))
print("bars   BC=%s half=%.3f | CAP_Y=%s" % (str([round(v, 3) for v in BCX]), BAR_HALF_PT,
                                             str([round(v, 3) for v in CAP_Y])))
print("bar label ink bottoms: %s" % str([round(CAP_Y[i] - ERR_HALF - LAB_GAP, 3) for i in range(4)]))
for i in range(4):
    print("headroom bar %d: label ink top ~ frame top + %.3f pt ; vs top-spine tick ink %.3f pt (need >= 7)" %
          (i + 1, CAP_Y[i] - ERR_HALF - LAB_GAP - 5.875 - FT,
           CAP_Y[i] - ERR_HALF - LAB_GAP - 5.875 - (FT + STROKE_HALF + TL)))
print("design ink: x %.3f..%.3f (w=%.3f = %.3f mm) ; y %.3f..%.3f (h=%.3f mm)" %
      (FL - LHANG_EST, FR + STROKE_HALF, INK_TARGET_PT, INK_TARGET_MM,
       FT - TOPHANG_EST, FB + CAT_DY_B, (CAT_DY_B + H_F + TOPHANG_EST) * 25.4 / 72.0))
print("horiz=%d rot=%d" % (len(horiz), len(rot)))
for it in horiz:
    print("  %-9s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
for it in rot:
    print("  ROT %-9s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
print("DONE_FIGS3_CONSTANTS")
