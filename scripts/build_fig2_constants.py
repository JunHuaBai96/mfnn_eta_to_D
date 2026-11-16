r"""Build outputs/origin_data/fig2_origin_constants.json for the Origin redraw of Fig. 2.

House twin of build_fig6_constants.py / build_fig4_constants.py.

Style parity with Fig.3/Fig.4/Fig.6: same spine/tick geometry (closed 4-side box,
0.75 pt black frame, inward ticks of 3.36 pt rendered length on ALL four sides),
Arial throughout (Origin \i() \b() \x() markup -- NO mathtext/STIX anywhere),
Okabe-Ito colours, tick labels 8.0 pt, axis titles 9.0 pt, legend 6.5 pt,
and NO in-figure suptitle (the caption line lives in the manuscript).

Design coordinates are PAGE POINTS with the origin at the top-left of the Origin
page, 1 pt = 1 pt (verified by scripts/_z_fig2_sizeprobe.py: the page -> exported
PDF map is the identity to within 0.2 pt).  Every text target below is an INK-BOX
edge; the anchor -> ink offsets of each individual string are measured on a probe
page (plot_fig2_origin.py with F2PROBE=1, then _z_fig2_measure.py), exactly as in
the Fig. 4 / Fig. 6 house workflow.

Canvas: the frozen matplotlib figure is 6.837 x 2.183 in of ink (aspect 3.13) and
Word embeds it 6.00 in wide.  The deliverable here is 6.30 in (453.6 pt) of ink to
match the frozen Origin figures, and the panels are made TALLER (150 pt instead of
the reference 108 pt) because the reference aspect leaves no empty box large enough
for the (a) legend / (a) note / (b) legend without pressing on data.  Two axis
ranges were also opened up so that those three items sit in provably empty regions:
  * panel (a) note moved from the bottom-left corner (which the x=0 Al-Ce-Ni /
    Al-Mg-Si / Al-Cu-impurity column and the x=5/10/15 interdiffusion squares
    occupy) into the empty lane x ~ 1..12 at.%, T ~ 1016..1116 K;
  * panel (a) legend re-laid as 2 columns x 3 rows inside the empty lane
    T ~ 1231..1350 K instead of the old upper-right block that sat on the
    x=20 / x=25 tracer columns;
  * panel (b) legend re-laid as 2 columns x 3 rows in a strip at the TOP of the
    panel, which required raising the D axis limit from 4.5e-8 to 1.2e-7 so the
    strip clears every modified-Sutherland "+" point (top 3.66e-8) and the pure-Al
    guide (top 2.37e-8) by >= 7 pt.
Frozen numbers are untouched; only presentation geometry changed.
"""
import os, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PT = 72.0 / 2.54
OFF = 0.25                                        # cm page margin used by the house
BS = chr(92)                                      # Origin escape character

# ---------------------------------------------------------------- page / canvas
CANV = dict(left=0.05, top=0.05, width=24.0, height=13.4)          # cm
PDFX = PDFY = round(OFF * PT, 4)   # design(0,0) = the 0.25 cm page inset, i.e.
                                      # exactly where the data layers sit, so text and
                                      # frames share one coordinate system
DX = round(PDFX - CANV["left"] * PT, 4)                            # -1.4173
DY = round(CANV["top"] * PT + CANV["height"] * PT - PDFY, 4)       # 381.2605

F4 = json.load(open(os.path.join(OD, "fig4_origin_constants.json"), encoding="utf-8-sig"))
FSMAP = dict(F4["fs_map"])
FSMAP["7.0"] = [29, 7.0, 7.875]
FSMAP.setdefault("6.0", [25, 6.0, 6.75])

# ---------------------------------------------------------------- panel frames
FT, FB = 21.0, 171.0                        # 150 pt panel height
FLA, FRA = 38.0, 208.0                      # panel (a) 170 pt
FLB, FRB = 262.0, 457.0                     # panel (b) 195 pt
WA, WB = FRA - FLA, FRB - FLB
CX_A, CX_B = 0.5 * (FLA + FRA), 0.5 * (FLB + FRB)
CY = 0.5 * (FT + FB)

# ---------------------------------------------------------------- axis ranges
AXF, AXT = -1.5, 27.5                       # panel (a): solute fraction (at.%)
AYF, AYT = 900.0, 1440.0                    # panel (a): T (K)
BUF, BUT = -3.301, -2.469                   # panel (b): u = log10 eta (Pa s)
BVF, BVT = -8.699, -6.9205                  # panel (b): v = log10 D (m2/s)
SX_A = WA / (AXT - AXF); SY_A = (FB - FT) / (AYT - AYF)
SX_B = WB / (BUT - BUF); SY_B = (FB - FT) / (BVT - BVF)
def ax2x(v): return FLA + (v - AXF) * SX_A
def ay2y(v): return FT + (AYT - v) * SY_A
def bx2x(v): return FLB + (v - BUF) * SX_B
def by2y(v): return FT + (BVT - v) * SY_B

A_XTICKS = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]
A_YTICKS = [1000.0, 1100.0, 1200.0, 1300.0, 1400.0]
import math
B_XTICKS = [math.log10(6e-4), math.log10(1e-3), math.log10(2e-3), math.log10(3e-3)]
B_XLABELS = ["6" + BS + "x(00D7)10" + BS + "+(" + BS + "x(2212)4)",
             "10" + BS + "+(" + BS + "x(2212)3)",
             "2" + BS + "x(00D7)10" + BS + "+(" + BS + "x(2212)3)",
             "3" + BS + "x(00D7)10" + BS + "+(" + BS + "x(2212)3)"]
B_YTICKS = [math.log10(v) for v in (3e-9, 4e-9, 6e-9, 1e-8, 2e-8, 3e-8, 4e-8)]
B_YLABELS = ["3" + BS + "x(00D7)10" + BS + "+(" + BS + "x(2212)9)",
             "4" + BS + "x(00D7)10" + BS + "+(" + BS + "x(2212)9)",
             "6" + BS + "x(00D7)10" + BS + "+(" + BS + "x(2212)9)",
             "10" + BS + "+(" + BS + "x(2212)8)",
             "2" + BS + "x(00D7)10" + BS + "+(" + BS + "x(2212)8)",
             "3" + BS + "x(00D7)10" + BS + "+(" + BS + "x(2212)8)",
             "4" + BS + "x(00D7)10" + BS + "+(" + BS + "x(2212)8)"]

# ---------------------------------------------------------------- colours (Okabe-Ito)
SPINE = "#333333"; DARK = "#333333"; REF = "#7F7F7F"
TRACER    = dict(fill="#D55E00", edge="#994300")
INTER     = dict(fill="#56B4E9", edge="#1B5E82")
IMPURITY  = dict(fill="#CC79A7", edge="#8F4B70")
SELF      = dict(fill="#7F7F7F", edge="#333333")
PRIOR     = dict(color="#E69F00")                    # modified Sutherland LF prior
GUIDE     = dict(color="#A87300")                    # pure-Al Sutherland guide
SPARSE    = {"Al-Ce-Ni": "#CC79A7", "Al-Mg-Si": "#56B4E9", "Al-Ag-Cu": "#E69F00"}

# symbol_kind verified by scripts/_z_fig2_shapes2.py (1 square, 2 circle, 3 tri-up,
# 5 diamond, 6 plus, 7 cross).  z values are the Origin size that the ink scan of
# scripts/_z_fig2_sizeprobe.py puts at the house ink size (~6.4-6.9 pt, cf. Fig.6
# circle 6.78 / square 7.26); measured raster ink is quoted in the comment.
MARK = dict(
    tracer   = dict(kind=2, z=5.7,  ink=6.69, **TRACER),      # circle
    inter    = dict(kind=1, z=6.4,  ink=6.69, **INTER),       # square
    impurity = dict(kind=3, z=5.2,  ink=7.12, **IMPURITY),    # triangle up
    self     = dict(kind=5, z=4.3,  ink=6.44, **SELF),        # diamond
    prior    = dict(kind=6, z=4.6,  ink=5.00, fill=PRIOR["color"], edge=PRIOR["color"]),
    cross    = dict(kind=7, z=5.9,  ink=6.94),                # open cross, per system
)
HALF = {k: v["ink"] / 2.0 for k, v in MARK.items()}

# ---------------------------------------------------------------- house ink offsets
LETTER_DX_L = -16.738      # (a)/(b) ink left   - frame left
LETTER_DY_B = -5.569       # (a)/(b) ink bottom - frame top
XTICK_DY_B  = 9.429        # x tick label ink bottom - frame bottom
YTICK_DX_R  = -3.863       # y tick label ink right  - frame left
XTITLE_DX_C = 0.99
XTITLE_DY_B = 23.554
LEG_DX_R    = -6.039       # legend ink right - frame right
LEG_GAP     = 12.0         # handle centre -> label ink left
LEG_PITCH   = 9.0          # legend row pitch

# rotated y title: right edge sits 4.1 pt left of the widest tick label's ink left
A_YTLBL_W = 16.875           # "1000" .. "1400" at 8 pt (measured in the Fig.6 probe)
B_YTLBL_W = 24.375           # "3x10^-9" at 8 pt
A_YTITLE_DX_R = FLA + YTICK_DX_R - A_YTLBL_W - 4.1
B_YTITLE_DX_R = FLB + YTICK_DX_R - B_YTLBL_W - 4.1
A_YTITLE_DY_C = 0.24
B_YTITLE_DY_C = -0.13

def H(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=False, ax=ax, tx=round(tx, 4), ay=ay, ty=round(ty, 4))
def R(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=True, ax=ax, tx=round(tx, 4), ay=ay, ty=round(ty, 4))

horiz = []
# ---------------- panel (a) typography
horiz.append(H("A_letter", BS + "b((a))", 10.0, "#000000", "left", FLA + LETTER_DX_L, "bottom", FT + LETTER_DY_B))
for v in A_XTICKS:
    horiz.append(H("a_xt_%d" % v, "%d" % v, 8.0, "#000000", "center", ax2x(v), "bottom", FB + XTICK_DY_B))
for v in A_YTICKS:
    horiz.append(H("a_yt_%d" % v, "%d" % v, 8.0, "#000000", "right", FLA + YTICK_DX_R, "center", ay2y(v)))
horiz.append(H("A_xtitle", "x" + BS + "-(Cu) or solute fraction (at.%)", 9.0, DARK,
               "center", CX_A + XTITLE_DX_C, "bottom", FB + XTITLE_DY_B))
# relocated note: two lines in the empty lane x ~ 1..12.5 at.%, T ~ 1016..1116 K
NOTE_L, NOTE_T = 20.0, 90.0
horiz.append(H("NoteA1", "honest " + BS + "i(" + BS + "x(03B7))" + "-paired HF only", 6.5, DARK,
               "left", FLA + NOTE_L, "top", FT + NOTE_T))
horiz.append(H("NoteA2", "(no Kozlov fill)", 6.5, DARK, "left", FLA + NOTE_L, "top", FT + NOTE_T + LEG_PITCH))

# ---------------- panel (b) typography
horiz.append(H("B_letter", BS + "b((b))", 10.0, "#000000", "left", FLB + LETTER_DX_L, "bottom", FT + LETTER_DY_B))
for i, v in enumerate(B_XTICKS):
    horiz.append(H("b_xt_%d" % i, B_XLABELS[i], 8.0, "#000000", "center", bx2x(v), "bottom", FB + XTICK_DY_B))
for i, v in enumerate(B_YTICKS):
    horiz.append(H("b_yt_%d" % i, B_YLABELS[i], 8.0, "#000000", "right", FLB + YTICK_DX_R, "center", by2y(v)))
horiz.append(H("B_xtitle", BS + "i(" + BS + "x(03B7)) (Pa" + BS + "x(00B7)s)", 9.0, DARK,
               "center", CX_B + XTITLE_DX_C, "bottom", FB + XTITLE_DY_B))

# ---------------- legends (2 columns x 3 rows, handles drawn on the data layers)
LEGA = dict(fs=6.5, color="#000000",
            col1=["tracer", "inter", "impurity"], col2=["Al-Ce-Ni", "Al-Mg-Si"],
            txt1=["Al" + BS + "x(2013)Cu tracer", "Al" + BS + "x(2013)Cu inter", "Al" + BS + "x(2013)Cu impurity"],
            txt2=["Al" + BS + "x(2013)Ce" + BS + "x(2013)Ni (sparse)", "Al" + BS + "x(2013)Mg" + BS + "x(2013)Si (sparse)"],
            # empty lane measured free: T 1231..1350 K
            box=dict(L=26.0, T=25.0, w=138.0, h=33.0))
LEGB = dict(fs=6.5, color="#000000",
            col1=["tracer", "inter", "impurity"], col2=["prior", "guide", "self"],
            txt1=["exp. tracer", "exp. inter", "exp. impurity"],
            txt2=["modified Sutherland LF prior",
                  "Sutherland guide (" + BS + "i(T)" + " = 1000 K, Al)",
                  "exp. self"],
            # top strip, free because the D axis was raised to 1.2e-7
            box=dict(L=7.0, T=5.0, w=181.0, h=31.0))
for tag, LEG, FL, FR in (("A", LEGA, FLA, FRA), ("B", LEGB, FLB, FRB)):
    LEG["label_left1"] = round(FL + LEG["box"]["L"] + LEG_GAP, 4)
    LEG["handle_cx1"] = round(FL + LEG["box"]["L"], 4)
    LEG["rows"] = []
    for i, (src, t) in enumerate(zip(LEG["col1"], LEG["txt1"])):
        LEG["rows"].append(dict(name="Lg%s_%d" % (tag, i + 1), txt=t, src=src, col=1,
                                label_left=LEG["label_left1"],
                                ink_top=round(FT + LEG["box"]["T"] + 4.0 + i * LEG_PITCH, 4)))
    n1 = len(LEG["col1"])
    for i, (src, t) in enumerate(zip(LEG["col2"], LEG["txt2"])):
        LEG["rows"].append(dict(name="Lg%s_%d" % (tag, n1 + i + 1), txt=t, src=src, col=2,
                                label_left=round(FL + LEG["box"]["L"] + LEG_GAP, 4),  # refined at render
                                ink_top=round(FT + LEG["box"]["T"] + 4.0 + i * LEG_PITCH, 4)))
    LEG["pitch"] = LEG_PITCH; LEG["gap"] = LEG_GAP
    FL = FLA if tag == "A" else FLB
    for r in LEG["rows"]:
        horiz.append(H(r["name"], r["txt"], LEG["fs"], LEG["color"], "left",
                       FL + LEG["box"]["L"] + LEG_GAP, "top", r["ink_top"]))

rot = [R("A_ytitle", BS + "i(T) (K)", 9.0, DARK, "right", A_YTITLE_DX_R, "center", CY + A_YTITLE_DY_C),
       R("B_ytitle", BS + "i(D) (m" + BS + "+(2) s" + BS + "+(" + BS + "x(2212)1))", 9.0, DARK,
         "right", B_YTITLE_DX_R, "center", CY + B_YTITLE_DY_C)]

K = dict(
    note=("Fig.2 Origin redraw. Okabe-Ito, Arial only (no STIX/mathtext), closed 4-side "
          "box, inward ticks on all four sides, no in-figure suptitle. Panel geometry and "
          "tick/label/title sizes copied from the Fig.4/Fig.6 house recipe."),
    pt=PT, off_cm=OFF, page_cm=[CANV["width"], CANV["height"]], canvas=CANV,
    fs_map=FSMAP, decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY),
    spine=SPINE, dark=DARK, ref=REF,
    tick=dict(len_nom=3.6, len_rendered=3.36, thick=0.75,
              label_fs=8.0, label_color="#000000", title_fs=9.0, title_color=DARK),
    markers=MARK, half=HALF, sparse_colors=SPARSE, prior=PRIOR, guide=GUIDE,
    legend=dict(A=LEGA, B=LEGB),
    layers=dict(
        a=dict(left=round(OFF + FLA / PT, 5), top=round(OFF + FT / PT, 5),
               width=round(WA / PT, 5), height=round((FB - FT) / PT, 5),
               xf=AXF, xt=AXT, yf=AYF, yt=AYT, xticks=A_XTICKS, yticks=A_YTICKS),
        b=dict(left=round(OFF + FLB / PT, 5), top=round(OFF + FT / PT, 5),
               width=round(WB / PT, 5), height=round((FB - FT) / PT, 5),
               xf=BUF, xt=BUT, yf=BVF, yt=BVT, xticks=B_XTICKS, yticks=B_YTICKS)),
    frame=dict(FT=FT, FB=FB, FL_A=FLA, FR_A=FRA, FL_B=FLB, FR_B=FRB,
               sx_a=SX_A, sy_a=SY_A, sx_b=SX_B, sy_b=SY_B),
    horiz=horiz, rot=rot,
    probe=dict(x0=10.0, x_step=165.0, per_col=10, y0=10.0, y_step=22.0,
               win_x0=-4.0, win_x1=160.0, win_y0=-3.0, win_y1=17.0,
               rot_x0=430.0, rot_dx=50.0, rot_y=250.0, rot_win_x=24.0, rot_win_y=80.0),
    export=dict(png_width=5292, target_ink_width_pt=453.6),
)
json.dump(K, open(os.path.join(OD, "fig2_origin_constants.json"), "w", encoding="utf-8"), indent=1)

print("horiz=%d rot=%d" % (len(horiz), len(rot)))
print("sx_a=%.6f sy_a=%.6f sx_b=%.4f sy_b=%.4f" % (SX_A, SY_A, SX_B, SY_B))
print("A ytitle_dx_r=%.3f  B ytitle_dx_r=%.3f" % (A_YTITLE_DX_R - FLA, B_YTITLE_DX_R - FLB))
print("ink x: letter %.3f .. FRB %.3f ; A ytitle ink left ~ %.3f" % (FLA + LETTER_DX_L, FRB, A_YTITLE_DX_R - 9))
for it in horiz:
    print("  %-10s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" % (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
for it in rot:
    print("  ROT %-10s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" % (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
