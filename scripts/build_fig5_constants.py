r"""Build outputs/origin_data/fig5_origin_constants.json for the Origin redraw of Fig. 5.

House twin of build_fig2_constants.py / build_fig6_constants.py / build_fig4_constants.py.

Style parity with Fig.3/Fig.4/Fig.6: same spine/tick geometry (closed 4-side box,
0.75 pt black frame, inward ticks of 3.36 pt rendered length on ALL four sides),
Arial throughout (Origin \i() \b() \-(...) \+(...) \x() markup -- NO mathtext/STIX
anywhere), Okabe-Ito colours, tick labels 8.0 pt, axis titles 9.0 pt, legend 6.5 pt,
panel letters 10.0 pt bold, and NO in-figure suptitle (the caption lives in the Word).

Design coordinates are PAGE POINTS with the origin at the top-left of the Origin
page, 1 pt = 1 pt (the same identity map verified for Fig.2 by
scripts/_z_fig2_sizeprobe.py).  Every text target below is an INK-BOX edge; the
anchor -> ink offsets of each individual string are measured on a probe page
(plot_fig5_origin.py with F5PROBE=1, then scripts/_z_fig5_measure.py), exactly as
in the Fig.2 / Fig.4 / Fig.6 house workflow.

Canvas: the frozen matplotlib figure is 4146 x 1300 px @600 dpi = 6.910 x 2.167 in
of ink (aspect 3.188) and Word embeds it 6.00 in wide.  Like the other frozen
Origin figures, the deliverable here is 6.30 in (453.6 pt) of ink.  The panels are
made TALLER than the reference (190 pt instead of ~108 pt) and the two y axes are
given extra headroom at the TOP, because the reference frame leaves no rectangle
inside either panel that is large enough for the five-row key without the yellow
modified-Sutherland dotted line crossing it:
  * reference (a) legend sat in the upper right, i.e. exactly on the dotted prior
    line (the prior descends 0.20 decades across the panel, so no wide box can fit
    between it and the LF-only NN curve);
  * reference (b) legend sat in the lower left, i.e. between the HF experiment
    points and the dotted prior line, and both were crossed by them.
Both keys are therefore re-laid as 2 columns x 3 rows in the empty strip at the TOP
of each panel, right-aligned, which needs the y upper limits raised from
-7.5391 / -7.5490 to -7.30.  The x limits, the tick VALUES, the curve/scatter data
and the coordinate system (1000/T vs log10 D) are the frozen ones; only the top of
the y range gains 0.24 decades of white space, and that is where the key lives.
Frozen numbers are untouched; only presentation geometry changed.
"""
import os, json, csv

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PT = 72.0 / 2.54
OFF = 0.25                                        # cm page margin used by the house
BS = chr(92)                                      # Origin escape character

# ---------------------------------------------------------------- page / canvas
CANV = dict(left=0.05, top=0.05, width=24.0, height=15.0)          # cm
PDFX = PDFY = round(OFF * PT, 4)                  # design(0,0) = the 0.25 cm page inset
DX = round(PDFX - CANV["left"] * PT, 4)
DY = round(CANV["top"] * PT + CANV["height"] * PT - PDFY, 4)

F4 = json.load(open(os.path.join(OD, "fig4_origin_constants.json"), encoding="utf-8-sig"))
FSMAP = dict(F4["fs_map"])
FSMAP["7.0"] = [29, 7.0, 7.875]
FSMAP.setdefault("6.0", [25, 6.0, 6.75])

# ---------------------------------------------------------------- panel frames
FT, FB = 21.0, 211.0                      # 190 pt panel height
FLA, FRA = 36.0, 225.0                    # panel (a) 189 pt
FLB, FRB = 267.0, 453.50                  # panel (b) 186.50 pt
WA, WB = FRA - FLA, FRB - FLB
CX_A, CX_B = 0.5 * (FLA + FRA), 0.5 * (FLB + FRB)
CY = 0.5 * (FT + FB)

# ---------------------------------------------------------------- axis ranges
META = json.load(open(os.path.join(OD, "fig5_data_meta.json"), encoding="utf-8-sig"))
RA = META["panels"]["a"]["reference_axes"]
RB = META["panels"]["b"]["reference_axes"]
AXF, AXT = RA["xlim"]                             # frozen x range, panel (a)
AYF, AYT = RA["ylim"][0], -7.30                   # y bottom frozen, top opened for the key
BUF, BUT = RB["xlim"]
BVF, BVT = RB["ylim"][0], -7.30
SX_A = WA / (AXT - AXF); SY_A = (FB - FT) / (AYT - AYF)
SX_B = WB / (BUT - BUF); SY_B = (FB - FT) / (BVT - BVF)
def ax2x(v): return FLA + (v - AXF) * SX_A
def ay2y(v): return FT + (AYT - v) * SY_A
def bx2x(v): return FLB + (v - BUF) * SX_B
def by2y(v): return FT + (BVT - v) * SY_B

A_XTICKS = [0.90, 0.95, 1.00, 1.05]
A_YTICKS = [-7.4, -7.6, -7.8, -8.0, -8.2]
B_XTICKS = [0.85, 0.90, 0.95, 1.00]
B_YTICKS = [-7.4, -7.6, -7.8, -8.0, -8.2, -8.4, -8.6]
def xlab(v): return "%.2f" % v
def key(v): return ("%.2f" % v).replace(".", "p").replace("-", "m")
def ylab(v): return BS + "x(2212)" + "%.1f" % abs(v)

# ---------------------------------------------------------------- colours (Okabe-Ito, _style.py)
SPINE = "#333333"; DARK = "#333333"; REF = "#7F7F7F"
EXP       = "#333333"                  # C["ref_dark"]  -- HF experiment
PRIOR_C   = "#E69F00"                  # C["LF"]        -- modified Sutherland prior (dotted)
LF_C      = "#E69F00"                  # C["LF"]        -- LF-only NN (dashed)
HF_C      = "#0072B2"                  # C["HF"]        -- HF-only NN (dash-dot)
MFNN_C    = "#009E73"                  # C["MFNN"]      -- residual MFNN (solid)

# line widths / dash patterns: the frozen reference used lw 1.2 / 1.2 / 1.2 / 1.4 at
# 6.910 in of ink; delivered at 6.300 in the on-page weight is preserved by x0.912,
# which also lands inside the Fig.3/Fig.4 house range (0.6 .. 1.15 pt).
SC = 6.30 / 6.910
LINES = dict(
    prior = dict(color=PRIOR_C, width=round(1.2 * SC, 3), pattern=[1.2 * SC, 1.8 * SC]),
    lf    = dict(color=LF_C,    width=round(1.2 * SC, 3), pattern=[7.2 * SC, 1.8 * SC]),
    hf    = dict(color=HF_C,    width=round(1.2 * SC, 3), pattern=[3.6 * SC, 1.2 * SC, 1.44 * SC, 1.2 * SC]),
    mfnn  = dict(color=MFNN_C,  width=round(1.4 * SC, 3), pattern=None),
)
for k in LINES:
    if LINES[k]["pattern"]:
        LINES[k]["pattern"] = [round(v, 3) for v in LINES[k]["pattern"]]

# circle verified by scripts/_z_fig2_shapes2.py (1 square, 2 circle, 3 tri-up,
# 5 diamond, 6 plus, 7 cross).  z is the Origin size that puts the raster ink at the
# house ~6.4-6.9 pt; the reference scatter is s=36 pt^2 -> 6.77 pt diameter.
MARK = dict(
    exp = dict(kind=2, z=6.37, ink=6.78, fill=EXP, edge="#FFFFFF", pen=0.5),
)
HALF = {k: v["ink"] / 2.0 for k, v in MARK.items()}

# ---------------------------------------------------------------- house ink offsets
LETTER_DX_L = -16.738      # (a)/(b) ink left   - frame left
LETTER_DY_B = -5.569       # (a)/(b) ink bottom - frame top
XTICK_DY_B  = 9.429        # x tick label ink bottom - frame bottom
YTICK_DX_R  = -3.863       # y tick label ink right  - frame left
XTITLE_DX_C = 0.99
XTITLE_DY_B = 23.554
CTITLE_DY_B = 6.0          # panel title ink bottom - frame top
LEG_GAP     = 12.0         # handle centre -> label ink left
LEG_PITCH   = 9.0          # legend row pitch
LEG_HANDLE_HALF = 7.0      # line handle half-length
LEG_HANDLE_DY = 2.4        # handle centre below label ink top

OFFS = {}
OFFJSON = os.path.join(OD, "fig5_text_offsets.json")
if os.path.exists(OFFJSON):
    OFFS = json.load(open(OFFJSON, encoding="utf-8-sig"))
def inkw(name, est):
    o = OFFS.get(name)
    return (o["jx1"] - o["jx0"]) if o else est
A_YTLBL_W = max(inkw("a_yt_%s" % key(v), 14.0) for v in A_YTICKS)
B_YTLBL_W = max(inkw("b_yt_%s" % key(v), 14.0) for v in B_YTICKS)
A_YTITLE_DX_R = FLA + YTICK_DX_R - A_YTLBL_W - 4.1
B_YTITLE_DX_R = FLB + YTICK_DX_R - B_YTLBL_W - 4.1
A_YTITLE_DY_C = 0.0
B_YTITLE_DY_C = 0.0

def H(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=False, ax=ax,
                tx=round(tx, 4), ay=ay, ty=round(ty, 4))
def R(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=True, ax=ax,
                tx=round(tx, 4), ay=ay, ty=round(ty, 4))

X_TITLE = "1000/" + BS + "i(T)" + " (" + BS + "i(K)" + BS + "+(" + BS + "x(2212)1))"
Y_TITLE = ("log" + BS + "-(10) " + BS + "i(D)" + " (" + BS + "i(D)" + " in m" + BS +
           "+(2) s" + BS + "+(" + BS + "x(2212)1))")

horiz = []
# ---------------- panel (a) typography
horiz.append(H("A_letter", BS + "b((a))", 10.0, "#000000", "left", FLA + LETTER_DX_L, "bottom", FT + LETTER_DY_B))
horiz.append(H("A_ctitle", "Pure Al self-diffusion", 8.0, "#000000", "center", CX_A + XTITLE_DX_C, "bottom", FT - CTITLE_DY_B))
for v in A_XTICKS:
    horiz.append(H("a_xt_%s" % key(v), xlab(v), 8.0, "#000000", "center", ax2x(v), "bottom", FB + XTICK_DY_B))
for v in A_YTICKS:
    horiz.append(H("a_yt_%s" % key(v), ylab(v), 8.0, "#000000", "right", FLA + YTICK_DX_R, "center", ay2y(v)))
horiz.append(H("A_xtitle", X_TITLE, 9.0, DARK, "center", CX_A + XTITLE_DX_C, "bottom", FB + XTITLE_DY_B))
# ---------------- panel (b) typography
horiz.append(H("B_letter", BS + "b((b))", 10.0, "#000000", "left", FLB + LETTER_DX_L, "bottom", FT + LETTER_DY_B))
horiz.append(H("B_ctitle", "Al" + BS + "-(80)Cu" + BS + "-(20) Cu-tracer", 8.0, "#000000",
               "center", CX_B + XTITLE_DX_C, "bottom", FT - CTITLE_DY_B))
for v in B_XTICKS:
    horiz.append(H("b_xt_%s" % key(v), xlab(v), 8.0, "#000000", "center", bx2x(v), "bottom", FB + XTICK_DY_B))
for v in B_YTICKS:
    horiz.append(H("b_yt_%s" % key(v), ylab(v), 8.0, "#000000", "right", FLB + YTICK_DX_R, "center", by2y(v)))
horiz.append(H("B_xtitle", X_TITLE, 9.0, DARK, "center", CX_B + XTITLE_DX_C, "bottom", FB + XTITLE_DY_B))

# ---------------- legends (2 columns x 3 rows, handles drawn on the data layers)
SRC = ["exp", "prior", "lf", "hf", "mfnn"]
TXT = ["HF experiment",
       "modified Sutherland prior",
       "LF-only NN",
       "HF-only NN",
       "residual MFNN"]
LEGA = dict(fs=6.5, color="#000000",
            col1=[SRC[0], SRC[1], SRC[2]], col2=[SRC[3], SRC[4]],
            txt1=TXT[0:3], txt2=TXT[3:5],
            box=dict(L=16.0, T=4.0))
LEGB = dict(fs=6.5, color="#000000",
            col1=[SRC[0], SRC[1], SRC[2]], col2=[SRC[3], SRC[4]],
            txt1=TXT[0:3], txt2=TXT[3:5],
            box=dict(L=16.0, T=4.0))
for tag, LEG, FL in (("A", LEGA, FLA), ("B", LEGB, FLB)):
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
    for r in LEG["rows"]:
        horiz.append(H(r["name"], r["txt"], LEG["fs"], LEG["color"], "left",
                       r["label_left"], "top", r["ink_top"]))

rot = [R("A_ytitle", Y_TITLE, 9.0, DARK, "right", A_YTITLE_DX_R, "center", CY + A_YTITLE_DY_C),
       R("B_ytitle", Y_TITLE, 9.0, DARK, "right", B_YTITLE_DX_R, "center", CY + B_YTITLE_DY_C)]

K = dict(
    note=("Fig.5 Origin redraw. Okabe-Ito, Arial only (no STIX/mathtext), closed 4-side "
          "box, inward ticks on all four sides, no in-figure suptitle. Panel geometry and "
          "tick/label/title sizes copied from the Fig.2/Fig.4/Fig.6 house recipe."),
    pt=PT, off_cm=OFF, page_cm=[CANV["width"], CANV["height"]], canvas=CANV,
    fs_map=FSMAP, decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY),
    spine=SPINE, dark=DARK, ref=REF, exp=EXP,
    tick=dict(len_nom=3.6, len_rendered=3.36, thick=0.75,
              label_fs=8.0, label_color="#000000", title_fs=9.0, title_color=DARK),
    markers=MARK, half=HALF, lines=LINES,
    legend=dict(A=LEGA, B=LEGB),
    layers=dict(
        a=dict(left=round(OFF + FLA / PT, 5), top=round(OFF + FT / PT, 5),
               width=round(WA / PT, 5), height=round((FB - FT) / PT, 5),
               xf=AXF, xt=AXT, yf=AYF, yt=AYT, xticks=A_XTICKS, yticks=A_YTICKS),
        b=dict(left=round(OFF + FLB / PT, 5), top=round(OFF + FT / PT, 5),
               width=round(WB / PT, 5), height=round((FB - FT) / PT, 5),
               xf=BUF, xt=BUT, yf=BVF, yt=BVT, xticks=B_XTICKS, yticks=B_YTICKS)),
    frame=dict(FT=FT, FB=FB, FL_A=FLA, FR_A=FRA, FL_B=FLB, FR_B=FRB,
               sx_a=SX_A, sy_a=SY_A, sx_b=SX_B, sy_b=SY_B,
               a_xticks=A_XTICKS, a_yticks=A_YTICKS, b_xticks=B_XTICKS, b_yticks=B_YTICKS,
               ),
    horiz=horiz, rot=rot,
    probe=dict(x0=10.0, x_step=165.0, per_col=10, y0=10.0, y_step=22.0,
               win_x0=-4.0, win_x1=160.0, win_y0=-3.0, win_y1=17.0,
               rot_x0=430.0, rot_dx=60.0, rot_y=250.0, rot_win_x=30.0, rot_win_y=150.0),
    export=dict(png_width=5292, target_ink_width_pt=453.6),
)
json.dump(K, open(os.path.join(OD, "fig5_origin_constants.json"), "w", encoding="utf-8"), indent=1)

print("horiz=%d rot=%d" % (len(horiz), len(rot)))
print("sx_a=%.4f sy_a=%.4f sx_b=%.4f sy_b=%.4f" % (SX_A, SY_A, SX_B, SY_B))
print("A ytitle_dx_r=%.3f  B ytitle_dx_r=%.3f  (ytlbl w %.3f/%.3f)" %
      (A_YTITLE_DX_R - FLA, B_YTITLE_DX_R - FLB, A_YTLBL_W, B_YTLBL_W))
for tag, LEG, FL in (("A", LEGA, FLA), ("B", LEGB, FLB)):
    w1 = max(inkw(r["name"], {"HF experiment": 42.0, "modified Sutherland prior": 83.0,
                              "LF-only NN": 38.0, "HF-only NN": 38.0, "residual MFNN": 45.0}[r["txt"]])
             for r in LEG["rows"] if r["col"] == 1)
    w2 = max(inkw(r["name"], 45.0) for r in LEG["rows"] if r["col"] == 2)
    print("legend %s: ink x %.2f..%.2f  y %.2f..%.2f  (prior py at box left = %.2f)" %
          (tag, FL + LEG["box"]["L"] - LEG_HANDLE_HALF,
           FL + LEG["box"]["L"] + LEG_GAP + w1 + LEG_GAP + LEG_HANDLE_HALF + w2,
           FT + LEG["box"]["T"] + 4.0, FT + LEG["box"]["T"] + 4.0 + 2 * LEG_PITCH + 5.0,
           (AYT - (-7.575 if tag == "A" else -7.6046)) * SY_A if tag == "A" else (BVT + 7.6046) * SY_B))
for it in horiz:
    print("  %-12s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
for it in rot:
    print("  ROT %-12s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
