"""Build outputs/origin_data/fig6_origin_constants.json for the Origin redraw of Fig. 6.

Style parity with Fig.3/Fig.4: identical panel size (5.38335 x 3.85741 cm), the same
spine/tick geometry, Arial throughout, Okabe-Ito colours, closed 4-side box with inward
ticks, and NO in-figure suptitle (the caption line lives in the manuscript).

Every text target is an INK-BOX edge in design pt (page units = PDF pt, 1:1 with the
exported PDF, origin at the top-left of the page).  The anchor->ink offsets of each item
are measured on an Origin probe page (plot_fig6_origin.py with F6PROBE=1, then
_z_fig6_measure.py), exactly as in the Fig. 4 house workflow.

Frozen numbers (never recomputed): MAPE 156.5 / 6.5, Fac2 0.00 / 1.00, n 10 / 2,
t_ref 983 K, ratio 2.9806 -> label "~3.0x" drawn with U+2248 because Arial has no
U+223C glyph (deliberate, reported deviation).
"""
import os, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PT = 72.0 / 2.54
OFF = 0.25
PDFX, PDFY = 7.0866, 7.872
DX = round(PDFX - 0.05 * PT, 4)              # 5.6693
DY = round(0.05 * PT + 13.4 * PT - PDFY, 4)   # 373.3878
F4 = json.load(open(os.path.join(OD, "fig4_origin_constants.json"), encoding="utf-8-sig"))
FSMAP = dict(F4["fs_map"])
FSMAP["7.0"] = [29, 7.0, 7.875]               # rendered = set * 8/9

# ---------------- panel frames (design pt, top-left origin) ----------------
FT = 17.399; FB = 126.7537
FL_A = 31.8024; FR_A = 184.3996
FL_B = 238.271; FR_B = 390.8682   # shifted 1.623 pt left: ink width -> 382.677 pt = 135.000 mm
W = FR_A - FL_A
CX_A = 0.5 * (FL_A + FR_A); CX_B = 0.5 * (FL_B + FR_B)
CY = 0.5 * (FT + FB)

# ---------------- axis ranges (chosen so the ticks land as in the ref) -----
AXF, AXT, AYF, AYT = 972.15, 1210.85, 2.02141, 9.22746
BXF, BXT, BYF, BYT = -0.3527, 1.3525, 0.0, 230.0
SX_A = W / (AXT - AXF); SY_A = (FB - FT) / (AYT - AYF)
SX_B = W / (BXT - BXF); SY_B = (FB - FT) / (BYT - BYF)
AX_TICKS = [1000.0, 1050.0, 1100.0, 1150.0, 1200.0]
AY_TICKS = [4.0, 6.0, 8.0]
BX_TICKS = [0.0, 1.0]
BY_TICKS = [0.0, 50.0, 100.0, 150.0, 200.0]
def ax2x(v): return FL_A + (v - AXF) * SX_A
def ay2y(v): return FT + (AYT - v) * SY_A
def bx2x(v): return FL_B + (v - BXF) * SX_B
def by2y(v): return FB - (v - BYF) * SY_B

# ---------------- colours ----------------
SPINE = "#333333"; DARK = "#333333"; REF = "#7F7F7F"
TRACER = dict(fill="#D55E00", edge="#994300")
INTER = dict(fill="#56B4E9", edge="#1B5E82")
# symbol_kind 2 = circle, 1 = square (verified by scripts/_z_fig6_probe13.py:
# kind 1 draws a PDF rectangle, kind 2 four bezier arcs).
# SIZE LAW.  scripts/_z_fig6_probe16.py bisected the graph: the 19 x 13.4 cm text
# canvas enlarges the Origin page and that inflates every symbol (z=7.4 circle ->
# 7.44 pt ink on the production page path, but 6.01 pt in a canvas-free replica),
# so the old probe14/probe15 calibration (0.8*z) does NOT describe the deliverable.
# scripts/_z_fig6_probe17.py scanned z ON THE PRODUCTION PAGE PATH and the rendered
# vector box is a staircase with a fixed 0.4825 pt step:
#   circle  z 6.25/6.50 -> 6.478   6.75 -> 6.960   7.00/7.25 -> 7.442   7.50 -> 7.922
#   square  z 7.00/7.25 -> 6.478   7.50/7.75 -> 6.960   8.00/8.25 -> 7.440
# The matplotlib reference (publish_figures/fix_layout_fig346_s5s6.py:385-393:
# s=36 marker="o" lw=0.6 -> 6.603 pt, s=42 marker="s" -> 7.083 pt, both measured at
# 600 dpi by scripts/_z_fig6_mkcc.py) cannot be reproduced exactly because Origin
# quantises symbol size; the 600 dpi raster also adds ~0.30 pt of anti-aliasing on
# top of the vector box.  The two z below sit mid-bucket and give raster ink
# ~6.78 (circle, +0.18 vs ref) and ~7.26 (square, +0.18 vs ref); the previous
# z=7.4/9.0 gave 7.80/8.64 (+18% / +22%) and pushed the 983 K arrow tips into the
# markers.
MARK_TRACER = dict(kind=2, z=6.37)   # vector 6.478 pt -> raster ~6.78 pt
MARK_INTER = dict(kind=1, z=7.62)   # vector 6.960 pt -> raster ~7.26 pt

# ---------------- reference-derived offsets (pt, ink-box edges rel. to frame) -------------
LETTER_DX_L = -16.738      # (a)/(b) ink left  - frame left      (fig6_ref_reltargets A_letter)
LETTER_DY_B = -5.569       # (a)/(b) ink bottom - frame top
AYTICK_DX_R = -3.863       # panel-A y tick label ink right - frame left
AXTICK_DY_B = 9.429        # panel-A x tick label ink bottom - frame bottom
AXTITLE_DX_C = 0.99        # panel-A x title ink centre - frame centre
AXTITLE_DY_B = 23.554
AYTITLE_DX_R = -11.988     # panel-A rotated y title ink right - frame left
AYTITLE_DY_C = 0.24
BYTICK_DX_R = -3.819
BYTITLE_DX_R = -20.694
BYTITLE_DY_C = -0.13
CAT1_DY_B = 10.929         # category label line 1 ink bottom - frame bottom
CAT2_DY_B = 19.304         # category label line 2 ink bottom - frame bottom
NOTE_DY_B = 31.304         # panel-B note ink bottom - frame bottom
LEG_DX_R = -6.039          # legend text ink right - frame right (kept from the reference)
LEG1_DY_T = 7.0            # NEW row-1 ink top  - frame top   (was lower right; relocated
LEG2_DY_T = 16.35          # NEW row-2 ink top  - frame top    to clear 1075-1090 K points)
LEG_HANDLE_GAP = 12.0      # handle centre to label ink left
LEG_HANDLE_DY = 2.4        # handle centre below the label ink top
RATIO_DX = 9.27            # ratio ink left - arrow shaft x
RATIO_DY = -0.84           # ratio ink centre - midpoint of the two 983 K marker centres
BAR1_DY = [96.3337, 89.2567, 82.1797]   # ink bottom above frame bottom, top line first.
   # 2026-11-11: tracer labels moved ABOVE the orange bar (was inside, white).  Stack sits in the
   # 17.67..52.10 corridor (top-frame ink bottom .. orange-bar ink top, 600dpi raster), keeps the
   # blue stack pitch 7.077 pt, centered so both raster end-gaps are ~7.5-7.7 pt (>=7 required).
   # ylim (0..230) and the 0/50/100/150/200 ticks are UNCHANGED.
BAR2_DY = [22.900, 15.823, 8.746]

SHAFT_X = ax2x(983.0)
Y_SQ = ay2y(7.0); Y_CI = ay2y(2.3485027817660353)
TIP_UP = Y_SQ + 4.58       # 6.960/2 (square half ink, probe17 law) + 1.1 clearance
TIP_DN = Y_CI - 4.34       # 6.478/2 (circle half ink, probe17 law) + 1.1 clearance
WING_Y = 3.2; WING_X = 1.6

def d2ax(x): return AXF + (x - FL_A) / SX_A
def d2ay(y): return AYT - (y - FT) / SY_A

arrow = {
    "color": REF, "pen": 1.0,
    "shaft": [[d2ax(SHAFT_X), d2ay(TIP_UP)], [d2ax(SHAFT_X), d2ay(TIP_DN)]],
    "head_up": [[d2ax(SHAFT_X - WING_X), d2ay(TIP_UP + WING_Y)],
                [d2ax(SHAFT_X), d2ay(TIP_UP)],
                [d2ax(SHAFT_X + WING_X), d2ay(TIP_UP + WING_Y)]],
    "head_dn": [[d2ax(SHAFT_X - WING_X), d2ay(TIP_DN - WING_Y)],
                [d2ax(SHAFT_X), d2ay(TIP_DN)],
                [d2ax(SHAFT_X + WING_X), d2ay(TIP_DN - WING_Y)]],
}

BS = chr(92)
def H(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=False,
                ax=ax, tx=round(tx, 4), ay=ay, ty=round(ty, 4))
def R(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=True,
                ax=ax, tx=round(tx, 4), ay=ay, ty=round(ty, 4))

horiz = []
# ===== panel A =====
horiz.append(H("A_letter", BS + "b((a))", 10.0, "#000000", "left", FL_A + LETTER_DX_L, "bottom", FT + LETTER_DY_B))
for v in AY_TICKS:
    horiz.append(H("a_yt_%d" % v, "%d" % v, 8.0, "#000000", "right", FL_A + AYTICK_DX_R, "center", ay2y(v)))
for v in AX_TICKS:
    horiz.append(H("a_xt_%d" % v, "%d" % v, 8.0, "#000000", "center", ax2x(v), "bottom", FB + AXTICK_DY_B))
horiz.append(H("A_xtitle", "Temperature " + BS + "i(T) (K)", 9.0, DARK, "center", CX_A + AXTITLE_DX_C, "bottom", FB + AXTITLE_DY_B))
horiz.append(H("Ratio", BS + "x(2248)3.0" + BS + "x(00D7)", 7.5, DARK, "left", SHAFT_X + RATIO_DX, "center", 0.5 * (Y_SQ + Y_CI) + RATIO_DY))
# ===== panel B =====
horiz.append(H("B_letter", BS + "b((b))", 10.0, "#000000", "left", FL_B + LETTER_DX_L, "bottom", FT + LETTER_DY_B))
for v in BY_TICKS:
    horiz.append(H("b_yt_%d" % v, "%d" % v, 8.0, "#000000", "right", FL_B + BYTICK_DX_R, "center", by2y(v)))
BC1 = bx2x(0.0); BC2 = bx2x(1.0)
for i, t in enumerate(["MAPE=156.5%", "Fac2=0.00", "n=10"]):
    horiz.append(H("b_bar1_%d" % (i + 1), t, 6.5, DARK, "center", BC1, "bottom", FB - BAR1_DY[i]))
for i, t in enumerate(["MAPE=6.5%", "Fac2=1.00", "n=2"]):
    horiz.append(H("b_bar2_%d" % (i + 1), t, 6.5, DARK, "center", BC2, "bottom", FB - BAR2_DY[i]))
CAT = "Al" + BS + "-(80)Cu" + BS + "-(20)"
for j, (bcx, l2) in enumerate(((BC1, "tracer"), (BC2, "inter"))):
    horiz.append(H("b_cat%d_1" % (j + 1), CAT, 8.0, "#000000", "center", bcx, "bottom", FB + CAT1_DY_B))
    horiz.append(H("b_cat%d_2" % (j + 1), l2, 8.0, "#000000", "center", bcx, "bottom", FB + CAT2_DY_B))
horiz.append(H("Note", BS + "i(Same composition; incompatible D scales)", 7.0, REF,
               "center", bx2x(0.5), "bottom", FB + NOTE_DY_B))
# ===== legend (relocated to the empty upper-right of panel A) =====
horiz.append(H("Lg1", "Cu tracer (Zhang et al.)", 6.5, "#000000", "right", FR_A + LEG_DX_R, "top", FT + LEG1_DY_T))
horiz.append(H("Lg2", "Interdiffusivity", 6.5, "#000000", "right", FR_A + LEG_DX_R, "top", FT + LEG2_DY_T))
rot = [R("A_ytitle", BS + "i(D) (10" + BS + "-(" + BS + "x(2212)9) m" + BS + "+(2) s" + BS + "+(" + BS + "x(2212)1))",
         9.0, DARK, "right", FL_A + AYTITLE_DX_R, "center", CY + AYTITLE_DY_C),
       R("B_ytitle", "MFNN MAPE (%)", 9.0, DARK, "right", FL_B + BYTITLE_DX_R, "center", CY + BYTITLE_DY_C)]

K = dict(
    note="Fig.6 Origin redraw. Okabe-Ito, Arial, closed box, inward ticks on all four "
         "sides, no in-figure suptitle. Panel geometry copied from Fig.4.",
    pt=PT, off_cm=OFF, page_cm=[19.0, 13.4], fs_map=FSMAP,
    decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY),
    spine=SPINE, dark=DARK, ref=REF, tracer=TRACER, inter=INTER,
    tick=dict(len_nom=3.6, len_rendered=3.36, thick=0.75,
              label_fs=8.0, label_color="#000000", title_fs=9.0, title_color=DARK),
    markers=dict(tracer=dict(**MARK_TRACER, **TRACER), inter=dict(**MARK_INTER, **INTER)),
    layers=dict(
        a=dict(left=round(OFF + FL_A / PT, 5), top=round(OFF + FT / PT, 5),
               width=round(W / PT, 5), height=round((FB - FT) / PT, 5),
               xf=AXF, xt=AXT, xi=50.0, xfirst=1000.0,
               yf=AYF, yt=AYT, yi=2.0, yfirst=4.0,
               xticks=AX_TICKS, yticks=AY_TICKS),
        b=dict(left=round(OFF + FL_B / PT, 5), top=round(OFF + FT / PT, 5),
               width=round(W / PT, 5), height=round((FB - FT) / PT, 5),
               xf=BXF, xt=BXT, xi=1.0, xfirst=0.0,
               yf=BYF, yt=BYT, yi=50.0, yfirst=0.0,
               xticks=BX_TICKS, yticks=BY_TICKS)),
    frame=dict(FT=FT, FB=FB, FL_A=FL_A, FR_A=FR_A, FL_B=FL_B, FR_B=FR_B,
               sx_a=SX_A, sy_a=SY_A, sx_b=SX_B, sy_b=SY_B,
               shaft_x=SHAFT_X, y_sq=Y_SQ, y_ci=Y_CI, tip_up=TIP_UP, tip_dn=TIP_DN),
    bars=dict(gap_cmd="-vg 45", pbs="-pbs 0", vw="-vw 0.6", width_du=0.55,
              faces=[TRACER["fill"], INTER["fill"]], edges=[TRACER["edge"], INTER["edge"]]),
    arrow=arrow,
    legend=dict(fs=6.5, color="#000000", handle_gap=LEG_HANDLE_GAP, handle_dy=LEG_HANDLE_DY,
                rows=[dict(name="Lg1", txt="Cu tracer (Zhang et al.)", src="tracer", label_right=FR_A + LEG_DX_R, ink_top=FT + LEG1_DY_T),
                      dict(name="Lg2", txt="Interdiffusivity", src="inter", label_right=FR_A + LEG_DX_R, ink_top=FT + LEG2_DY_T)]),
    horiz=horiz, rot=rot,
    probe=dict(x0=10.0, x_step=165.0, per_col=10, y0=10.0, y_step=22.0,
               win_x0=-4.0, win_x1=160.0, win_y0=-3.0, win_y1=17.0,
               rot_x0=520.0, rot_dx=80.0, rot_y=250.0, rot_win_x=30.0, rot_win_y=180.0),
    export=dict(png_width=6433, target_ink_width_pt=382.677),
)
json.dump(K, open(os.path.join(OD, "fig6_origin_constants.json"), "w", encoding="utf-8"), indent=1)
print("horiz=%d rot=%d" % (len(horiz), len(rot)))
print("sx_a=%.6f sy_a=%.5f sx_b=%.4f sy_b=%.6f" % (SX_A, SY_A, SX_B, SY_B))
print("a left=%s top=%s w=%s h=%s  b left=%s" % (K["layers"]["a"]["left"], K["layers"]["a"]["top"],
      K["layers"]["a"]["width"], K["layers"]["a"]["height"], K["layers"]["b"]["left"]))
print("shaft=%.3f y_sq=%.3f y_ci=%.3f tip_up=%.3f tip_dn=%.3f" % (SHAFT_X, Y_SQ, Y_CI, TIP_UP, TIP_DN))
print("ink bbox design: x %.3f..%.3f (w=%.3f = %.2f mm)" % (FL_A + LETTER_DX_L, FR_B, FR_B - (FL_A + LETTER_DX_L), (FR_B - FL_A - LETTER_DX_L) / PT * 25.4))
print("arrow data: shaft x=%.1f  D %.4f..%.4f" % (arrow["shaft"][0][0], arrow["shaft"][0][1], arrow["shaft"][1][1]))
for it in horiz:
    print("  %-10s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" % (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
for it in rot:
    print("  ROT %-10s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" % (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
