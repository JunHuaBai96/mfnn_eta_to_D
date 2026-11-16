r"""Build outputs/origin_data/fig7_origin_constants.json for the Origin redraw of Fig. 7.

House twin of build_fig5_constants.py / build_fig6_constants.py.

Style parity with Fig.2/Fig.3/Fig.4/Fig.5/Fig.6: closed 4-side box (#333333,
0.75 pt), hand-drawn inward ticks of 3.36 pt rendered length on ALL four sides,
no minor ticks, no grid, Arial only (Origin \i() \b() \-(...) \x() markup -- NO
mathtext/STIX anywhere), Okabe-Ito class colours EXACTLY as the frozen figure
(tracer #D55E00/#994300, inter #56B4E9/#1B5E82, impurity #CC79A7/#8F4B70), tick
labels 8.0 pt, axis titles 9.0 pt, category labels 7.0 pt, bar-end labels 6.5 pt,
legend and (b) notes 6.5 pt, panel letters 10.0 pt bold, panel titles 8.0 pt,
NO in-figure suptitle (the caption lives in the Word).

Design coordinates are PAGE POINTS, 1 pt = 1 pt, delivered ink width
453.6 pt = 6.30 in (the frozen Word width of Fig.1-6).  Every text target below
is an INK-BOX edge; anchor->ink offsets are measured on a probe page
(plot_fig7_origin.py with F7PROBE=1, then scripts/_z_fig7_measure.py), exactly
as in the Fig.2/4/5/6 house workflow.

matplotlib-defect fixes encoded here (see the redraw prompt):
  1. the three-class key moves BELOW the (a) axis title into its own empty lane;
  2. Arial subscript markup only, no STIX;
  3. (a) title = 8 pt "LOGO MAPE by hold-out (caution)"; the frozen mean becomes
     a two-line block in the verified empty lane right of the dashed line and
     the short bars: "frozen mean" / "39.4 \x(00B1) 39.7%";
  4. ink height raised to ~220 pt (~3.05 in) so 13 bars + key are not squashed;
  5. the (a)/(b) gutter keeps the (b) axis-title lane >=7 pt off the (a) right
     spine (37.0 pt, see item 9);
  6. axis titles 9 pt, ticks 8, categories 7, bar labels 6.5, notes 6.5;
  7. the 39.4 guide stays DASHED in both panels, drawn as explicit dash
     polylines with -d 0 + -wp (set plot -1 is forbidden in Origin 2026);
  8. closed box + inward ticks kept, 3.36 pt rendered.
  9. PANEL WIDTH BALANCE (this round): the (a) and (b) boxes are EQUAL width.
     W = (CXB - FLA - GUTTER) / 1.5 = 167.6667 pt for BOTH frames, because
     FLA = 78.0 must stay (the 74 pt category-label lane / left ink edge),
     GUTTER = 37.0 must stay wide enough for the rotated (b) y-title, and
     CXB = 366.5 keeps the 176 pt (b) x-title -- the right ink edge -- exactly
     where it was, so the delivered ink width stays 454.6 pt = 6.314 in.
     Splitting the old 198/108 pt frames into 153/153 pt instead would shrink
     the figure to ~6.00 in of ink and break the Fig.1-6 width parity.
     Consequence: "156.5% (n=10)" is the ONLY bar-end label that no longer fits
     2 pt outside its tip inside the narrower (a) box (it would land at
     249.4 pt, past FR_A = 245.7), so it moves INSIDE the Al-(80)Cu-(20)
     (tracer) bar: right-leaning, ink right 7.0 pt off the bar tip, 49.7 pt off
     the right spine, colour #000000 on #D55E00 (measured WCAG 5.43:1; white on
     the same fill is only 3.87:1).  The text itself is untouched; the other 12
     bar-end labels stay outside their tips exactly as before.

Data geometry is frozen: (a) xlim 0..210 ticks 0/50/100/150/200, rows 0..12 at
the reference ylim (-0.996, 12.996); (b) keeps the reference xlim (1.115, 5.185)
and bottom -6.6304; only its TOP is raised to 175.0 to open the note lane
(presentation only; every dot keeps its CSV coordinates, 156.5 stays inside).
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

F5 = json.load(open(os.path.join(OD, "fig5_origin_constants.json"), encoding="utf-8-sig"))
FSMAP = dict(F5["fs_map"])                        # incl. 6.0/6.5/7.0/8.0/9.0/10.0

# ---------------------------------------------------------------- panel frames
FT, FB = 24.0, 192.0                      # 168 pt panel height (unchanged)
FLA = 78.0                                # (a) left spine unchanged -> left ink edge unchanged
GUTTER = 37.0                             # (a) right spine -> (b) left spine: the (b) y-title lane
CXB = 366.5                               # (b) frame centre = old centre -> x-title keeps the right ink edge
W_PANEL = (CXB - FLA - GUTTER) / 1.5      # 167.6667 pt, EQUAL for (a) and (b)
FRA = FLA + W_PANEL
FLB = FRA + GUTTER
FRB = FLB + W_PANEL
WA, WB = FRA - FLA, FRB - FLB             # equal by construction
CX_A, CX_B = 0.5 * (FLA + FRA), 0.5 * (FLB + FRB)
CY = 0.5 * (FT + FB)

# ---------------------------------------------------------------- axis ranges
META = json.load(open(os.path.join(OD, "fig7_data_meta.json"), encoding="utf-8-sig"))
RA = META["reference_axes"]["a"]; RB = META["reference_axes"]["b"]
AXF, AXT = RA["xlim"]                             # 0, 210 (frozen)
AYF, AYT = RA["ylim"]                             # -0.996, 12.996 (frozen)
BUF, BUT = RB["xlim"]                             # 1.115, 5.185 (frozen)
BVF, BVT = RB["ylim"][0], 175.0                   # bottom frozen, top opened for the lane
SX_A = WA / (AXT - AXF); SY_A = (FB - FT) / (AYT - AYF)
SX_B = WB / (BUT - BUF); SY_B = (FB - FT) / (BVT - BVF)
def ax2x(v): return FLA + (v - AXF) * SX_A
def ay2y(v): return FT + (AYT - v) * SY_A
def bx2x(v): return FLB + (v - BUF) * SX_B
def by2y(v): return FT + (BVT - v) * SY_B

A_XTICKS = [0.0, 50.0, 100.0, 150.0, 200.0]
A_YTICKS = [float(i) for i in range(13)]          # every hold-out row
B_XTICKS = [2.0, 3.0, 4.0, 5.0]
B_YTICKS = [0.0, 25.0, 50.0, 75.0, 100.0, 125.0, 150.0]
def xlab(v): return "%d" % v
def key(v): return "%d" % int(round(v))

# ---------------------------------------------------------------- colours
SPINE = "#333333"; DARK = "#333333"
CLS = dict(
    tracer   = dict(fill="#D55E00", edge="#994300"),
    inter    = dict(fill="#56B4E9", edge="#1B5E82"),
    impurity = dict(fill="#CC79A7", edge="#8F4B70"),
)
BAR_PEN = 0.6                     # bar edge line width (frozen)

# ---------------------------------------------------------------- bars (panel a)
BARS = []
for r in META["bars"]:
    i = r["row"]; v = r["mape"]
    BARS.append(dict(row=i, group=r["group"], cls=r["cls"], mape=v, n=r["n"],
                     disp=r["disp"], label=r["label"],
                     ann="%s%% (n=%d)" % (r["disp"], r["n"]),
                     ann_x=round(v * SX_A + 2.0, 4)))
BAR_HALF = round(0.36 * SY_A, 4)          # bar height = 0.72 of the row pitch, in pt

# ---------------------------------------------------------------- markers (panel b)
# Origin kinds: 1 square, 2 circle, 3 triangle-up (scripts/_z_fig2_shapes2.py).
# s=42 pt^2 in the reference; z trimmed to 6.0 so the six coincident x=5.0 points
# overlap less (slight shrink allowed; coordinates are NOT moved).
MARK = dict(
    tracer   = dict(kind=2, z=6.0, ink=6.57, fill=CLS["tracer"]["fill"],   edge=CLS["tracer"]["edge"]),
    inter    = dict(kind=1, z=6.0, ink=6.25, fill=CLS["inter"]["fill"],    edge=CLS["inter"]["edge"]),
    impurity = dict(kind=3, z=6.0, ink=8.80, fill=CLS["impurity"]["fill"], edge=CLS["impurity"]["edge"]),
)

# ---------------------------------------------------------------- mean guide (both panels)
MEAN = dict(v=META["frozen_mean"][0],
            width_a=1.0, width_b=0.9,
            pattern=[3.7, 1.6], color=SPINE)

# ---------------------------------------------------------------- house ink offsets
LETTER_DX_L = -16.738      # (a)/(b) ink left   - frame left
LETTER_DY_B = -5.569       # (a)/(b) ink bottom - frame top
XTICK_DY_B  = 9.429        # x tick label ink bottom - frame bottom
YTICK_DX_R  = -3.863       # y tick label ink right  - frame left
XTITLE_DX_C = 0.99
XTITLE_DY_B = 23.554
CTITLE_DY_B = 6.0          # panel title ink bottom - frame top
CAT_DX_R    = -3.0         # category labels right-align (3 pt off the left spine)
LEG_TOP_D   = 31.0         # legend ink top - FB (>= 7 pt below the x-title ink bottom)
LEG_HW, LEG_HH = 6.0, 3.0  # legend swatch half width / half height
LEG_TXGAP, LEG_ITEMGAP = 4.0, 18.0
NOTE_DX_R   = -7.0         # (b) note lane ink right - FRB
NOTE_DY_T   = 7.0          # (b) note lane ink top   - FT
NOTE_PITCH  = 9.0
MEANBOX_DX_R = 118.2       # frozen-mean block ink right - FLA (verified empty lane)
MEANBOX_DY_T = 159.7 - FB  # ink top of line 1, relative to FB
MEANBOX_PITCH = 8.5
INBAR_ROW = 12               # the only bar whose outside label would cross FR_A
INBAR_EDGE_GAP = 7.0         # in-bar label: ink right -> bar tip (>= 7 pt off the spine too)
INBAR_COLOR = "#000000"      # WCAG 5.43:1 on #D55E00; white would be 3.87:1

OFFS = {}
OFFJSON = os.path.join(OD, "fig7_text_offsets.json")
if os.path.exists(OFFJSON):
    OFFS = json.load(open(OFFJSON, encoding="utf-8-sig"))
def inkw(name, est):
    o = OFFS.get(name)
    return (o["jx1"] - o["jx0"]) if o else est

def sub(txt):
    # "Al{81}Cu{19} (inter)" -> Al\-(81)Cu\-(19) (inter)   (plain parens stay plain)
    out = []; i = 0
    while i < len(txt):
        if txt[i] == "{":
            j = txt.index("}", i)
            out.append(BS + "-(" + txt[i + 1:j] + ")")
            i = j + 1
        else:
            out.append(txt[i]); i += 1
    return "".join(out)

def H(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=False, ax=ax,
                tx=round(tx, 4), ay=ay, ty=round(ty, 4))
def Rr(name, txt, fs, color, ax, tx, ay, ty):
    return dict(name=name, txt=txt, fs=fs, color=color, rot=True, ax=ax,
                tx=round(tx, 4), ay=ay, ty=round(ty, 4))

X_TITLE_A = "MAPE (%)"
X_TITLE_B = BS + "x(0394)" + BS + "i(x)" + BS + "-(Cu) to nearest train composition (at.%)"
Y_TITLE_B = "LOGO MFNN MAPE (%)"
CT_A = "LOGO MAPE by hold-out (caution)"
CT_B = "Error vs composition distance (caution)"

horiz = []
# ---------------- panel (a) typography
horiz.append(H("A_letter", BS + "b((a))", 10.0, "#000000", "left", FLA + LETTER_DX_L, "bottom", FT + LETTER_DY_B))
horiz.append(H("A_ctitle", CT_A, 8.0, "#000000", "center", CX_A + XTITLE_DX_C, "bottom", FT - CTITLE_DY_B))
for v in A_XTICKS:
    horiz.append(H("a_xt_%s" % key(v), xlab(v), 8.0, "#000000", "center", ax2x(v), "bottom", FB + XTICK_DY_B))
for b in BARS:
    horiz.append(H("a_cat_%d" % b["row"], sub(b["label"]), 7.0, "#000000", "right",
                   FLA + CAT_DX_R, "center", ay2y(b["row"])))
    if b["row"] == INBAR_ROW:
        b["ann_place"] = "inside"
        horiz.append(H("a_ann_%d" % b["row"], b["ann"], 6.5, INBAR_COLOR, "right",
                       FLA + b["mape"] * SX_A - INBAR_EDGE_GAP, "center", ay2y(b["row"])))
    else:
        b["ann_place"] = "right"
        horiz.append(H("a_ann_%d" % b["row"], b["ann"], 6.5, "#000000", "left",
                       FLA + b["ann_x"], "center", ay2y(b["row"])))
horiz.append(H("A_xtitle", X_TITLE_A, 9.0, DARK, "center", CX_A + XTITLE_DX_C, "bottom", FB + XTITLE_DY_B))
# frozen-mean block (verified empty lane right of the dashed line / short bars)
MEANBOX_TX = FLA + MEAN["v"] * SX_A + 16.7
horiz.append(H("Mean_1", "frozen mean", 6.5, DARK, "left", MEANBOX_TX, "top", FB + MEANBOX_DY_T))
horiz.append(H("Mean_2", "39.4 " + BS + "x(00B1) 39.7%", 6.5, DARK, "left",
               MEANBOX_TX, "top", FB + MEANBOX_DY_T + MEANBOX_PITCH))
# ---------------- legend (a): three class swatches, one row, below the x title.
# x positions are refined at render time from the measured label widths.
LEGTXT = dict(tracer="tracer", inter="inter", impurity="impurity")
LEGROWS = []
for c in ("tracer", "inter", "impurity"):
    LEGROWS.append(dict(cls=c, name="LgA_%s" % c[:2], txt=LEGTXT[c],
                        ink_top=round(FB + LEG_TOP_D, 4)))
    horiz.append(H("LgA_%s" % c[:2], LEGTXT[c], 6.5, "#000000", "left", 0.0, "top", FB + LEG_TOP_D))
# ---------------- panel (b) typography
horiz.append(H("B_letter", BS + "b((b))", 10.0, "#000000", "left", FLB + LETTER_DX_L, "bottom", FT + LETTER_DY_B))
CT_B_DX = (FLB + LETTER_DX_L + inkw("B_letter", 12.88) + 4.5 + 0.5 * inkw("B_ctitle", 140.62)) - CX_B   # nudge right so the 141 pt title clears the bold (b) letter
horiz.append(H("B_ctitle", CT_B, 8.0, "#000000", "center", CX_B + CT_B_DX, "bottom", FT - CTITLE_DY_B))
for v in B_XTICKS:
    horiz.append(H("b_xt_%s" % key(v), xlab(v), 8.0, "#000000", "center", bx2x(v), "bottom", FB + XTICK_DY_B))
for v in B_YTICKS:
    horiz.append(H("b_yt_%s" % key(v), "%d" % v, 8.0, "#000000", "right", FLB + YTICK_DX_R, "center", by2y(v)))
horiz.append(H("B_xtitle", X_TITLE_B, 9.0, DARK, "center", CX_B + XTITLE_DX_C, "bottom", FB + XTITLE_DY_B))
B_YTLBL_W = max(inkw("b_yt_%s" % key(v), 13.0) for v in B_YTICKS)
B_YTITLE_DX_R = FLB + YTICK_DX_R - B_YTLBL_W - 4.1
NOTE_TXT = ["not a success claim",
            "nearest-neighbor |" + BS + "x(0394)" + BS + "i(x)" + BS + "-(Cu)|",
            "in training pool"]
for i_, t_ in enumerate(NOTE_TXT):
    horiz.append(H("Bn%d" % (i_ + 1), t_, 6.5, DARK, "right", FRB + NOTE_DX_R, "top",
                   FT + NOTE_DY_T + i_ * NOTE_PITCH))
rot = [Rr("B_ytitle", Y_TITLE_B, 9.0, DARK, "right", B_YTITLE_DX_R, "center", CY)]

K = dict(
    note=("Fig.7 Origin redraw. Okabe-Ito class colours kept from the frozen figure, Arial only "
          "(no STIX/mathtext), closed 4-side box, inward ticks on all four sides, no in-figure "
          "suptitle. Geometry recipe copied from the Fig.2/Fig.4/Fig.5/Fig.6 house."),
    pt=PT, off_cm=OFF, page_cm=[CANV["width"], CANV["height"]], canvas=CANV,
    fs_map=FSMAP, decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY),
    spine=SPINE, dark=DARK,
    tick=dict(len_nom=3.6, len_rendered=3.36, thick=0.75,
              label_fs=8.0, label_color="#000000", title_fs=9.0, title_color=DARK),
    cls=CLS, bars=BARS, bar_half=BAR_HALF, bar_pen=BAR_PEN,
    markers=MARK, mean=MEAN,
    legend=dict(rows=LEGROWS, top_d=LEG_TOP_D, hw=LEG_HW, hh=LEG_HH,
                txgap=LEG_TXGAP, itemgap=LEG_ITEMGAP),
    layers=dict(
        a=dict(left=round(OFF + FLA / PT, 5), top=round(OFF + FT / PT, 5),
               width=round(WA / PT, 5), height=round((FB - FT) / PT, 5),
               xf=AXF, xt=AXT, yf=AYF, yt=AYT, xticks=A_XTICKS, yticks=A_YTICKS),
        b=dict(left=round(OFF + FLB / PT, 5), top=round(OFF + FT / PT, 5),
               width=round(WB / PT, 5), height=round((FB - FT) / PT, 5),
               xf=BUF, xt=BUT, yf=BVF, yt=BVT, xticks=B_XTICKS, yticks=B_YTICKS)),
    frame=dict(FT=FT, FB=FB, FL_A=FLA, FR_A=FRA, FL_B=FLB, FR_B=FRB,
               sx_a=SX_A, sy_a=SY_A, sx_b=SX_B, sy_b=SY_B,
               a_xticks=A_XTICKS, a_yticks=A_YTICKS, b_xticks=B_XTICKS, b_yticks=B_YTICKS),
    balance=dict(old_FL_A=78.0, old_FR_A=276.0, old_W_a=198.0,
                 old_FL_B=312.5, old_FR_B=420.5, old_W_b=108.0, old_gutter=36.5,
                 new_W=W_PANEL, new_gutter=GUTTER, new_FL_A=FLA, new_FR_A=FRA,
                 new_FL_B=FLB, new_FR_B=FRB, inbar_row=INBAR_ROW,
                 inbar_edge_gap=INBAR_EDGE_GAP, inbar_color=INBAR_COLOR),
    horiz=horiz, rot=rot,
    probe=dict(x0=10.0, x_step=185.0, per_col=14, y0=10.0, y_step=20.0,
               win_x0=-4.0, win_x1=180.0, win_y0=-3.0, win_y1=16.0,
               rot_x0=745.0, rot_dx=60.0, rot_y=40.0, rot_win_x=30.0, rot_win_y=150.0),
    export=dict(png_width=6433, target_ink_width_pt=453.6),
)
json.dump(K, open(os.path.join(OD, "fig7_origin_constants.json"), "w", encoding="utf-8"), indent=1)

print("horiz=%d rot=%d" % (len(horiz), len(rot)))
print("sx_a=%.4f sy_a=%.4f sx_b=%.4f sy_b=%.4f bar_half=%.3f" % (SX_A, SY_A, SX_B, SY_B, BAR_HALF))
print("FRAMES  a=[%.4f, %.4f] w=%.4f pt (%.5f cm)   b=[%.4f, %.4f] w=%.4f pt (%.5f cm)" %
      (FLA, FRA, WA, WA / PT, FLB, FRB, WB, WB / PT))
print("WIDTH DIFF a-b = %.6f pt   gutter = %.4f pt   CX_A=%.4f CX_B=%.4f   ratio %.4f:1" %
      (WA - WB, FLB - FRA, CX_A, CX_B, WA / WB))
print("B ytitle_dx_r=%.3f (ytlbl w %.3f)" % (B_YTITLE_DX_R - FLB, B_YTLBL_W))
for it in horiz:
    print("  %-10s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))
for it in rot:
    print("  ROT %-10s fs=%4.1f ax=%-6s tx=%8.3f ay=%-6s ty=%8.3f %s" %
          (it["name"], it["fs"], it["ax"], it["tx"], it["ay"], it["ty"], ascii(it["txt"])))







