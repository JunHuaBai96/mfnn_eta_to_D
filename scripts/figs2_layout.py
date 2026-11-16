r"""Shared layout maths for the Fig. S2 Origin redraw (no Origin, no calibration needed).

Both scripts/_z_figs2_fontcal.py and scripts/build_figs2_constants.py import this module,
so the font/symbol calibration runs in the EXACT production page / canvas / layer geometry
(the Fig.6/Fig.7/Fig.S4 house recipe: page 24 x 15 cm, canvas inset 0.05 cm, OFF 0.25 cm,
exported PDF pt = design pt + (7.0866, 7.0866), 1 design pt = 1 pt).

Everything here is DESIGN POINTS with y pointing DOWN, origin at the canvas-layer top-left.

Family-consistent lanes (measured on the delivered Fig.6/Fig.7/Fig.S4 + the frozen
matplotlib Fig. S2 PDF, see scripts/build_fig7_constants.py / build_figs4_constants.py):
    y tick label ink right   - FL            = -4.0
    x tick label ink bottom  - FB            = +9.429
    x axis title ink bottom  - FB            = +23.554
    category line 1/2 ink bottom - FB        = +10.93 / +19.51
    bar-top label ink bottom - cap ink       = -7.0  (annotation clearance rule)
    panel title ink bottom   - FT            = -6.0
    panel letter ink left/bottom - frame     = -16.738 / -5.569
    inward tick rendered length             = 3.36 pt, thickness 0.75 pt
"""
import os, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PT = 72.0 / 2.54
BS = chr(92)

# ------------------------------------------------------------------ page / canvas
OFF = 0.25                                       # cm, house page inset
PAGE = [24.0, 15.0]                              # cm, house canvas/page
PDFX = PDFY = round(OFF * PT, 4)                 # design -> exported PDF pt
DX = round(PDFX - 0.05 * PT, 4)                  # 5.6693
DY = round(0.05 * PT + PAGE[1] * PT - PDFY, 4)   # 419.5276
CANV = dict(left=0.05, top=0.05, width=PAGE[0], height=PAGE[1])

# ------------------------------------------------------------------ ink targets
INK_W_MM = 135.0                                 # Elsevier mid width, NOT 88 mm / 6.30 in
INK_H_MM = 60.0                                  # 55 mm (matplotlib) -> a little taller
INK_TARGET_PT = round(INK_W_MM * 72.0 / 25.4, 3)  # 382.677
INK_TARGET_H_PT = round(INK_H_MM * 72.0 / 25.4, 3)
# Origin quantises layer geometry, so the DELIVERED ink is not exactly the design ink.
# These residuals are measured on the delivered PDF by finalize_figs2_crop.py (raster
# threshold 254) and fed back here, exactly as build_figs4_constants.py did with its
# INK_X_EXTRA.  Values below are the last measured closure of this figure.
INK_X_RESID_PT = 0.323                           # delivered width  - predicted width
INK_Y_RESID_PT = -0.129                          # delivered height - predicted height

# ------------------------------------------------------------------ strokes
FRAME_T = 0.75
STROKE_HALF = FRAME_T / 2.0
TICK_LEN = 3.36                                  # rendered inward tick length
BAR_PEN = 0.6
EB_PEN = 0.8
EB_CAP_HALF = 2.5                                # +/- seed std caps: 5.0 pt total ink, as ref
LINE_PEN = 1.25                                  # (b) trajectories, solid

# ------------------------------------------------------------------ colours (frozen)
SPINE = "#333333"; DARK = "#333333"; BLACK = "#000000"
W_COLOR = dict(fill="#009E73", edge="#006B4E")   # Protocol W (primary)
G_COLOR = dict(fill="#0072B2", edge="#004D7A")   # Protocol G (caution)

# ------------------------------------------------------------------ axis ranges
A_XF, A_XT = -0.4, 1.4                           # (a) bars at x = 0, 1
A_YF, A_YT = 0.0, 55.0                           # major ticks 0..50
B_XF, B_XT = -0.3, 4.3                           # (b) CATEGORICAL 0..4 (not seed-value)
B_YF, B_YT = 10.0, 50.0                          # major ticks 10..50: seed 1 / seed 123 clear
A_XTICKS = [0.0, 1.0]
A_YTICKS = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
B_XTICKS = [0.0, 1.0, 2.0, 3.0, 4.0]
B_YTICKS = [10.0, 20.0, 30.0, 40.0, 50.0]
B_XLABELS = ["0", "1", "2", "42", "123"]
BAR_W_DU = 0.55

# ------------------------------------------------------------------ family lanes
TICK_DX_R = -4.0
YTITLE_CLEAR = 8.5            # rotated axis name ink -> neighbouring ink
#                             # (7.0 rule + the ~0.6 pt Origin layer quantisation)
XTICK_DY_B = 9.429
XTITLE_DX_C = 0.99
XTITLE_DY_B = 23.554
CAT1_DY_B = 10.93
CAT2_DY_B = 19.51
CTITLE_DY_B = 7.5
LETTER_DX_L = -16.738
LETTER_DY_B = -5.569
LAB_GAP = 7.0
LEG_LEFT_DX = 9.0             # legend swatch ink left  - FL_B (>= 7 pt off the
#                             # left spine ink after Origin layer quantisation)
LEG_LINE_W = 10.0             # trajectory swatch line length
LEG_TXGAP = 4.0               # swatch ink right -> text ink left
LEG_TOP_D = 12.0              # legend ink top - FT (>= 7 pt below the top-spine
#                             # inward ticks, >= 7 pt above the seed-2 G marker)
LEG_ITEM_GAP = 10.0           # gap between the two horizontal legend items

# pre-measurement ink-width estimates (tight Arial ink, rendered family sizes)
EST_TICK_W_8 = 9.34           # "50" / "40" at 8.4 pt
EST_CROSS_9 = 9.80            # cross ink of the rotated 9.6 pt axis name
EST_CAP_H_8 = 6.0             # "Mean ..." panel title ink height at 8.4 pt
EST_CAP_H_10 = 7.60           # panel letter ink height at 10.56 pt bold


def geometry(offs=None):
    """Frame geometry closed on the 135 mm ink width.  `offs` = figs2_text_offsets.json."""
    offs = offs or {}
    def ink(name, est):
        """tight INK WIDTH (jx1-jx0) measured on the Fig. S2 probe page."""
        o = offs.get(name)
        return (o["jx1"] - o["jx0"]) if o else est
    def inh(name, est):
        """tight INK HEIGHT (jy1-jy0); for rotated items this is the along-length."""
        o = offs.get(name)
        return (o["jy1"] - o["jy0"]) if o else est
    tick_w = max(ink("A_yt_50", EST_TICK_W_8), ink("A_yt_40", EST_TICK_W_8),
                 ink("B_yt_50", EST_TICK_W_8), ink("B_yt_20", EST_TICK_W_8))
    cross = ink("A_ytitle", EST_CROSS_9)
    ytitle_dx_r = round(TICK_DX_R - tick_w - YTITLE_CLEAR, 4)
    lhang = -ytitle_dx_r + cross                   # axis-name ink left -> FL_A
    letter_left = -LETTER_DX_L                      # panel letter ink left -> FL
    lhang = max(lhang, letter_left)
    gutter = round(-ytitle_dx_r + cross + YTITLE_CLEAR + STROKE_HALF, 4)
    w_panel = (INK_TARGET_PT - INK_X_RESID_PT - lhang - gutter - STROKE_HALF) / 2.0
    fl_a = 33.0
    fr_a = fl_a + w_panel
    fl_b = fr_a + gutter
    fr_b = fl_b + w_panel
    top_hang = max(-LETTER_DY_B + inh("A_letter", EST_CAP_H_10),
                   CTITLE_DY_B + inh("A_ctitle", EST_CAP_H_8))
    bhang = max(CAT2_DY_B, XTITLE_DY_B) + STROKE_HALF
    h_frame = round(INK_TARGET_H_PT - INK_Y_RESID_PT - top_hang - bhang, 3)
    ft = 26.0
    fb = round(ft + h_frame, 3)
    return dict(lhang=lhang, gutter=gutter, w_panel=round(w_panel, 4), fl_a=fl_a,
                fr_a=round(fr_a, 4), fl_b=round(fl_b, 4), fr_b=round(fr_b, 4),
                ytitle_dx_r=ytitle_dx_r, tick_w=tick_w, cross=cross,
                top_hang=round(top_hang, 4), bhang=round(bhang, 4),
                ft=ft, fb=fb, h=h_frame, cx_a=round(0.5 * (fl_a + fr_a), 4),
                cx_b=round(0.5 * (fl_b + fr_b), 4), cy=round(0.5 * (ft + fb), 4))


def maps(g):
    """design pt <-> data units for both panels."""
    sxa = (g["fr_a"] - g["fl_a"]) / (A_XT - A_XF); sya = g["h"] / (A_YT - A_YF)
    sxb = (g["fr_b"] - g["fl_b"]) / (B_XT - B_XF); syb = g["h"] / (B_YT - B_YF)
    return dict(
        sx_a=sxa, sy_a=sya, sx_b=sxb, sy_b=syb,
        ax2x=lambda v: g["fl_a"] + (v - A_XF) * sxa,
        ay2y=lambda v: g["ft"] + (A_YT - v) * sya,
        bx2x=lambda v: g["fl_b"] + (v - B_XF) * sxb,
        by2y=lambda v: g["ft"] + (B_YT - v) * syb)


def layer_spec(g, which):
    """Origin layer geometry in cm for the given panel (or the text canvas)."""
    if which == "canvas":
        return dict(left=CANV["left"], top=CANV["top"], width=CANV["width"],
                    height=CANV["height"], xf=0.0, xt=CANV["width"] * PT,
                    yf=0.0, yt=CANV["height"] * PT)
    fl, fr = (g["fl_a"], g["fr_a"]) if which == "a" else (g["fl_b"], g["fr_b"])
    xf, xt = (A_XF, A_XT) if which == "a" else (B_XF, B_XT)
    yf, yt = (A_YF, A_YT) if which == "a" else (B_YF, B_YT)
    return dict(left=round(OFF + fl / PT, 5), top=round(OFF + g["ft"] / PT, 5),
                width=round((fr - fl) / PT, 5), height=round(g["h"] / PT, 5),
                xf=xf, xt=xt, yf=yf, yt=yt,
                xticks=(A_XTICKS if which == "a" else B_XTICKS),
                yticks=(A_YTICKS if which == "a" else B_YTICKS))


# Fig. S2 has TWO rotated items (one axis name per panel), so the rotation lane is
# shifted left of the Fig.7/Fig.S4 single-item lane: both slots must stay inside the
# 772 pt exported page (design x + 7.0866 < 772).
PROBE = dict(x0=10.0, x_step=185.0, per_col=14, y0=10.0, y_step=20.0,
             win_x0=-4.0, win_x1=180.0, win_y0=-3.0, win_y1=17.0,
             rot_x0=690.0, rot_dx=42.0, rot_y=40.0, rot_win_x=30.0, rot_win_y=150.0)
