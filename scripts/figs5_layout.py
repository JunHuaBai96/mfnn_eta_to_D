r"""Shared layout maths for the Fig. S5 Origin redraw (no Origin, no calibration needed).

House twin of scripts/figs2_layout.py (TWO EQUAL-WIDTH panels, 135 mm Elsevier-mid ink,
page 24 x 15 cm, canvas inset 0.05 cm, OFF 0.25 cm, exported PDF pt = design pt +
(7.0866, 7.0866), 1 design pt = 1 pt), with the Fig. S1 deviation: the axis names are
9 pt HORIZONTAL (prompt item 8), so there is NO rotated lane at all.

Everything here is DESIGN POINTS with y pointing DOWN, origin at the canvas-layer top-left.

Top lanes (this figure):
    lane A (just above the frame): horizontal y-axis name, ink bottom - FT = -7.5,
           ink left aligned to the y tick-label lane (FL + TICK_DX_R - tick_w)
    lane B (above lane A):           panel letter (a)/(b) + centred panel title,
           ink bottom - FT = -(YTITLE_DY_B + ytitle_h + 7.5)
    letter ink left  - FL           = -16.738 (family lane)
    y tick label ink right - FL     = -4.0    (family lane)
    category line 1/2 ink bottom - FB = +10.93 / +19.51 (family two-line lane)
    bar-top / cap-top annotation ink bottom - ink top of what it labels = -7.0
    inward tick rendered length = 3.36 pt, frame/tick thickness 0.75 pt
Legend (a, upper-right inside, THREE rows so every swatch matches one bar colour):
    ink right = FR_A - 12.0; swatch 14.0 x 4.9 pt; swatch->text gap 5.6 pt;
    row text-ink tops FT + [11.5, 22.6, 33.7] (row 1 keeps >= 7 pt from the inward
    top-tick tips at FT+3.36; rows 2/3 clear the 156.5% annotation and the joint
    tracer bar by >= 7 pt on the x axis).
"""
import os, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PT = 72.0 / 2.54
BS = chr(92)

# ------------------------------------------------------------------ page / canvas
OFF = 0.25                                       # cm, house page inset
PAGE = [24.0, 15.0]                              # cm, house canvas/page
PDFX = PDFY = round(OFF * PT, 4)                 # 7.0866 design -> exported PDF pt
DX = round(PDFX - 0.05 * PT, 4)                  # 5.6693
DY = round(0.05 * PT + PAGE[1] * PT - PDFY, 4)   # 419.5276
CANV = dict(left=0.05, top=0.05, width=PAGE[0], height=PAGE[1])

# ------------------------------------------------------------------ ink targets
INK_W_MM = 135.0                                 # Elsevier mid, NOT 88 mm / 6.30 in
INK_H_MM = 72.0                                  # Note deleted -> 65..75 mm band, 72 chosen
INK_TARGET_PT = round(INK_W_MM * 72.0 / 25.4, 3)  # 382.677
INK_TARGET_H_PT = round(INK_H_MM * 72.0 / 25.4, 3)
# Origin quantises layer geometry; these residuals are measured on the delivered PDF by
# finalize_figs5_crop.py and fed back here after the first render (house iteration).
INK_X_RESID_PT = -0.104
INK_Y_RESID_PT = -0.688

# ------------------------------------------------------------------ strokes
FRAME_T = 0.75
STROKE_HALF = FRAME_T / 2.0
TICK_LEN = 3.36                                  # rendered inward tick length
BAR_PEN = 0.6
EB_PEN = 0.8
EB_CAP_HALF = 2.5                                # cap total ink 5.0 pt, as the family
EB_INK_HALF = 0.775                              # 0.4 stroke/round overshoot + 0.375

# ------------------------------------------------------------------ colours (frozen Okabe-Ito)
SPINE = "#333333"; DARK = "#333333"; BLACK = "#000000"
SEP_COLOR   = dict(fill="#7F7F7F", edge="#333333")   # (a) Separate pools
TRacer_COLOR = dict(fill="#D55E00", edge="#994300")  # (a) Joint tracer / (b) Separate tracer pool
INTER_COLOR = dict(fill="#56B4E9", edge="#1B5E82")   # (a) Joint inter  / (b) Separate inter
JOINT_COLOR = dict(fill="#009E73", edge="#006B4E")   # (b) Joint+one-hot
EB_COLOR = "#333333"                             # error stems + caps (NOT #1F77B4)

# ------------------------------------------------------------------ axis ranges
A_XF, A_XT = -0.5, 1.5                           # (a) groups at x = 0, 1
A_YF, A_YT = 0.0, 210.0                          # majors 0/50/100/150/200
B_XF, B_XT = -0.5, 2.5                           # (b) bars at x = 0, 1, 2
B_YF, B_YT = 0.0, 190.0                          # majors 0..175 step 25
A_XTICKS = [0.0, 1.0]
A_YTICKS = [0.0, 50.0, 100.0, 150.0, 200.0]
B_XTICKS = [0.0, 1.0, 2.0]
B_YTICKS = [0.0, 25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 175.0]
A_BAR_W_DU = 0.35                                # separate at x-0.175, joint at x+0.175
B_BAR_W_DU = 0.55

# ------------------------------------------------------------------ family lanes
TICK_DX_R = -4.0
XTICK_DY_B = 9.429
CAT1_DY_B = 10.93
CAT2_DY_B = 19.51
YTITLE_DY_B = 7.5                                # lane A ink bottom -> FT
LAB_GAP = 7.0
LETTER_DX_L = -16.738
LEG_RIGHT_DX = -12.0                             # legend ink right -> FR_A
LEG_SW = dict(w=14.0, h=4.9)
LEG_TXGAP = 5.6
LEG_ROW_TOPS = [11.5, 22.6, 33.7]                # text-ink tops rel. FT

# pre-measurement ink estimates (tight Arial ink at the rendered family sizes)
EST_TICK_W_8 = 14.0              # "200"/"175" at 8.40 pt
EST_YTITLE_H = 5.4               # horizontal 9.6 pt axis name ink height
EST_TITLE_H = 6.0                # 8.40 pt panel title ink height
EST_CAP_H_10 = 7.6               # 10.56 pt bold panel letter ink height
EST_LEG_W = [78.0, 46.0, 42.0]   # legend texts at 7.44 pt
EST_LAB_W = [25.5, 25.5, 20.0, 18.0]   # (a) bar-top labels at 7.92 pt
EST_BLAB_W = 38.0                # (b) cap-top labels at 7.92 pt


def geometry(offs=None):
    """Frame geometry closed on the 135 mm x 72 mm ink box.  offs = figs5_text_offsets.json."""
    offs = offs or {}
    def ink(name, est):
        o = offs.get(name)
        return (o["jx1"] - o["jx0"]) if o else est
    def inh(name, est):
        o = offs.get(name)
        return (o["jy1"] - o["jy0"]) if o else est
    tick_w = max(ink("A_yt_200", EST_TICK_W_8), ink("A_yt_100", EST_TICK_W_8),
                 ink("B_yt_175", EST_TICK_W_8), ink("B_yt_100", EST_TICK_W_8))
    ytitle_h = inh("A_ytitle", EST_YTITLE_H)
    ctitle_dy = round(YTITLE_DY_B + ytitle_h + 7.5, 4)   # lane B ink bottom -> FT
    lhang = max(-TICK_DX_R + tick_w, -LETTER_DX_L)
    gutter = round(lhang + STROKE_HALF + 7.0, 4)
    w_panel = (INK_TARGET_PT - INK_X_RESID_PT - lhang - gutter - STROKE_HALF) / 2.0
    fl_a = 33.0
    fr_a = fl_a + w_panel
    fl_b = fr_a + gutter
    fr_b = fl_b + w_panel
    top_hang = ctitle_dy + max(inh("A_ctitle", EST_TITLE_H),
                               inh("A_letter", EST_CAP_H_10)) + STROKE_HALF
    bhang = CAT2_DY_B + STROKE_HALF
    h_frame = round(INK_TARGET_H_PT - INK_Y_RESID_PT - top_hang - bhang, 3)
    ft = 34.0    # two top lanes (axis names + letter/title): keep ink on the page
    fb = round(ft + h_frame, 3)
    return dict(tick_w=round(tick_w, 4), ytitle_h=round(ytitle_h, 4),
                ctitle_dy=ctitle_dy, lhang=round(lhang, 4), gutter=gutter,
                w_panel=round(w_panel, 4), fl_a=fl_a, fr_a=round(fr_a, 4),
                fl_b=round(fl_b, 4), fr_b=round(fr_b, 4),
                top_hang=round(top_hang, 4), bhang=round(bhang, 4),
                ft=ft, fb=fb, h=h_frame, cx_a=round(0.5 * (fl_a + fr_a), 4),
                cx_b=round(0.5 * (fl_b + fr_b), 4), cy=round(0.5 * (ft + fb), 3))


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


PROBE = dict(x0=10.0, x_step=185.0, per_col=14, y0=10.0, y_step=30.0,
             win_x0=-4.0, win_x1=180.0, win_y0=-3.0, win_y1=22.0)
