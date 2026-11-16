# -*- coding: ascii -*-
"""Build fig1_origin_constants.json for the native-Origin redraw of Fig.1.

Design space: pt, X right, Y DOWN.  Canvas transform into the Origin layer:
    u = X + OX ,  v = OY - Y          (1 data unit = 1 pt, layer.unit=3)
Raw PDF page map (calibrated in outputs/origin_data/_z_fig1probe):
    pdf_x = u + 1.44 ,  pdf_y = 455.92 - v

Content is taken from scripts/publish_figures/fig1_lu_style.py (frozen matplotlib
reference); geometry is re-laid-out natively so that
  * panel A keeps four-side closed boxes with inward ticks,
  * every rendered glyph is >= 8 pt (>= 7 pt after the Word paste),
  * the four known occlusions are removed (D title vs NN_H tag, C y_L vs dashed
    box, residual arc vs neurons, legends vs frames),
  * a colour / symbol key strip is added.
Nothing here touches Fig.3 / Fig.4 / Word / frozen numbers.
"""
import os, io, json, math, csv

B  = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PT = 72.0 / 2.54

# ---------------------------------------------------------------- calibration
OX, OY = 40.0, 420.0                  # design (0,0) -> canvas u,v
INK_W, INK_H = 452.0, 382.0           # target ink extent (design pt)
CAL = dict(ox=OX, oy=OY, pdf_dx=1.44, pdf_dy=455.92,
           canvas_cm=[20.0, 16.0], canvas_left=0.05, canvas_top=0.05,
           unit=3, px_per_pt_png=6433.0 / 772.0, raw_page_pt=[772.0, 548.0],
           fsize_scale=1.125, cap_ratio=0.72, sub_scale=0.684,
           ink_left_off=0.66, ink_top_off=0.56, ink_w_pad=1.10,
           rot_ink_left=0.25, rot_ink_w=0.90, rot_ink_top=-0.24, rot_len_pad=1.5,
           arrow_head_scale=1.02, arrow_head_width=4.8, tick_len=3.4)

# ---------------------------------------------------------------- palette
C = dict(MFNN="#009E73", MFNN_EC="#006B4E", HF="#0072B2", HF_EC="#004D7A",
         LF="#E69F00", LF_EC="#A87300", RES="#D55E00",
         IN_FC="#D5D0E8", IN_EC="#6B5B95", HID_FC="#FFFFFF", HID_EC="#333333",
         OUTL_FC="#F0C674", OUTH_FC="#7EB6D9", SUM_EC="#222222",
         MIX_FC="#FFF4E0", MIX_EC="#E69F00", BOX_EC="#888888",
         AX="#333333", TXT="#222222", SUB="#555555", CAP="#666666",
         TAG="#444444", EDGE="#555555",
         BOX_LF="#FFF8EB", BOX_HF="#EBF5FB", WASH_D="#F3FAF7", CHIP="#FFFFFF")

DASH = dict(solid=0, long=1, short=2, dashdot=3, dotted=6)

# ---------------------------------------------------------------- emitters
TXTS, LINES, FILLS, DISKS, SYMS, ARRS = [], [], [], [], [], []
HALOED = set()
_audit = []

def text(name, t, fs, color, x, y, align="left", valign="top", rot=False, note=""):
    assert float(int(fs)) == fs, "font size must be an integer pt: %r" % fs
    assert fs >= 8, "text %s below the 8 pt floor: %r" % (name, fs)
    TXTS.append(dict(name=name, txt=t, fs=fs, color=color, x=round(x, 4),
                     y=round(y, 4), align=align, valign=valign, rot=rot, note=note))

def _dashname(dash):
    if isinstance(dash, str):
        assert dash in DASH, dash
        return dash
    return ("solid" if dash == 0 else ("long" if dash == 1 else
            ("short" if dash == 2 else ("dashdot" if dash == 3 else "dotted"))))

def line(pts, color, w, dash=0, owner=None):
    q = [None if p is None else [round(p[0], 4), round(p[1], 4)] for p in pts]
    LINES.append(dict(pts=q, color=color, w=w, dash=_dashname(dash), owner=owner))

def poly(pts, color, w, dash=0, owner=None):
    """one connected polyline"""
    line(pts, color, w, dash, owner)

def segs(pairs, color, w, dash=0):
    """many independent segments -> single None-separated polyline"""
    flat = []
    for a, b in pairs:
        flat += [a, b, None]
    if flat:
        flat.pop()
        line(flat, color, w, dash)

def rect_box(x0, y0, x1, y1, color, w, dash=0, owner=None):
    poly([[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]], color, w, dash, owner)

def fill_band(top, bottom, color, kind="band"):
    FILLS.append(dict(top=[[round(p[0], 4), round(p[1], 4)] for p in top],
                      bottom=[[round(p[0], 4), round(p[1], 4)] for p in bottom],
                      color=color, kind=kind))

def fill_rect(x0, y0, x1, y1, color, kind="rect"):
    fill_band([[x0, y0], [x1, y0]], [[x0, y1], [x1, y1]], color, kind)

def halo_behind(name, color, pad_x=2.0, pad_y=1.5):
    "opaque chip painted over the polylines but under the label itself"
    cand = [z for z in TXTS if z["name"] == name]
    assert len(cand) == 1, name
    b = ink_box(cand[0])
    fill_rect(b[0] - pad_x, b[1] - pad_y, b[2] + pad_x, b[3] + pad_y, color, kind="halo")
    HALOED.add(name)

def disk(cx, cy, r, fill=None, edge=None, ew=0.7):
    DISKS.append(dict(cx=round(cx, 4), cy=round(cy, 4), r=round(r, 4),
                      fill=fill, edge=edge, ew=ew))

def symbol(cx, cy, dia, fill, edge):
    SYMS.append(dict(cx=round(cx, 4), cy=round(cy, 4), dia=dia, fill=fill, edge=edge))

def arrow(x1, y1, x2, y2, color, w, head=5.0):
    ARRS.append(dict(x1=round(x1, 4), y1=round(y1, 4), x2=round(x2, 4),
                     y2=round(y2, 4), color=color, w=w, head=head))

# ---------------------------------------------------------------- panel frames
COL1, COL2 = 0.0, 230.0
COLW = 222.0
ROW1 = (0.0, 168.0)
ROW2 = (172.0, 350.0)
KEYY = (356.0, 382.0)
SX = COLW / 10.0                       # 22.2 pt per panel-x unit
SY1 = (ROW1[1] - ROW1[0]) / 6.2        # 27.097
SY2 = (ROW2[1] - ROW2[0]) / 6.2        # 28.710

def PA(px, py):  return (COL1 + px * SX, ROW1[0] + (6.2 - py) * SY1)
def PB(px, py):  return (COL2 + px * SX, ROW1[0] + (6.2 - py) * SY1)
def PC(px, py):  return (COL1 + px * SX, ROW2[0] + (6.2 - py) * SY2)
def PD(px, py):  return (COL2 + px * SX, ROW2[0] + (6.2 - py) * SY2)
# ---------------------------------------------------------------- text model
FD = r"C:\Windows\Fonts"
from PIL import ImageFont
_P = {"reg": FD + r"\arial.ttf", "bold": FD + r"\arialbd.ttf",
      "ital": FD + r"\ariali.ttf", "bi": FD + r"\arialbi.ttf"}
_c = {}
def _F(face, px):
    k = (face, px)
    if k not in _c:
        _c[k] = ImageFont.truetype(_P[face], px)
    return _c[k]
def _W(face, txt, size):
    if not txt:
        return 0.0
    return _F(face, max(1, int(round(size * 100)))).getlength(txt) / 100.0

def _match(t, j):
    d = 0
    while j < len(t):
        if t[j] == "(":
            d += 1
        elif t[j] == ")":
            d -= 1
            if d == 0:
                return j
        j += 1
    raise ValueError(t)

def runs(t, face="reg", scale=1.0, acc=None):
    """expand Origin markup (\\i \\b \\- \\+ \\x(hhhh)) into (text, face, scale) runs"""
    if acc is None:
        acc = []
    i = 0
    while i < len(t):
        if t[i] == "\\" and i + 1 < len(t):
            n = t[i + 1]
            if n == "x":
                a = t.index("(", i + 2)
                b = t.index(")", a)
                acc.append([chr(int(t[a + 1:b], 16)), face, scale])
                i = b + 1
                continue
            if n in ("i", "b", "-", "+"):
                a = i + 2
                if t[a] != "(" and n in "-+":
                    grp, b = t[a], a
                else:
                    b = _match(t, a)
                    grp = t[a + 1:b]
                stack = (face, scale)
                if n == "i":
                    face = "ital" if face == "reg" else "bi"
                elif n == "b":
                    face = "bold" if face == "reg" else "bi"
                elif n in "-+":
                    scale = scale * 0.684
                runs(grp, face, scale, acc)
                face, scale = stack
                i = b + 1
                continue
        acc.append([t[i], face, scale])
        i += 1
    return acc

PAD = 1.10          # Origin-reported advance box minus ink width (pt)
EDGE_L = 0.66       # ink left edge minus anchor u (pt)
EDGE_T = 0.56       # ink top edge minus anchor v (pt)

def tw(t, fs):
    """Arial advance width (design pt) of markup string t at RENDERED size fs"""
    return sum(_W(f, s, fs * sc) for s, f, sc in runs(t))
def inkw(t, fs):
    """predicted ink width as Origin will report it (advance - PAD)"""
    return tw(t, fs) - PAD
def cap(fs):
    """cap / digit height (pt) -- the ink height of a no-descender string"""
    return 0.72 * fs

def vert_ext(txt, fs):
    # (t, b) ink offsets below the label anchor, design pt.  Calibrated against
    # the rendered probe: the ink top of a cap/digit string sits 0.56 pt below
    # the anchor, hence the baseline is at 0.56 + 0.72 fs; every other glyph is
    # placed from that baseline with the real Arial outline extents.
    T = 0.0; B = 0.0
    for s0, f, sc in runs(txt):
        if not s0.strip():
            continue
        d = 0.01
        bb = _F(f, max(1, int(round(fs * sc * 100)))).getbbox(s0)
        T = min(T, bb[1] * d); B = max(B, bb[3] * d)
    base = 0.56 + 0.72 * fs
    return (base + T, base + B)

def anchor_uv(it, Wrep=None):
    # design-space anchor (u, v) that puts the ink where the item asks;
    # returns (u, v, reported advance width used)
    fs = it["fs"]; txt = it["txt"]
    W = tw(txt, fs) if Wrep is None else Wrep
    if it.get("rot"):
        ux = it["x"] - CAL["rot_ink_left"] * fs
        uy = (it["y"] - 0.5 * W if it["valign"] == "center" else it["y"] - W)
        return (ux, uy + CAL["rot_ink_top"], W)
    a = it["align"]
    if a == "left":
        ux = it["x"] - CAL["ink_left_off"]
    elif a == "center":
        ux = it["x"] - 0.5 * W - 0.11
    elif a == "right":
        ux = it["x"] - W + CAL["ink_w_pad"] - CAL["ink_left_off"]
    else:
        raise ValueError(a)
    t, b = vert_ext(txt, fs)
    uy = it["y"] - t if it["valign"] == "top" else it["y"] - 0.5 * (t + b)
    return (ux, uy, W)

def inkh(fs, desc=True):
    """ink height (pt); descenders add ~0.23 fs"""
    return (0.95 if desc else 0.72) * fs
def ink_box(it, Wrep=None):
    # design-space ink rectangle of a text item, derived from its anchor
    fs = it["fs"]
    ux, uy, W = anchor_uv(it, Wrep)
    if it.get("rot"):
        x0 = ux + CAL["rot_ink_left"] * fs
        y0 = uy - CAL["rot_ink_top"]
        return (x0, y0, x0 + CAL["rot_ink_w"] * fs, y0 + W)
    t, b = vert_ext(it["txt"], fs)
    return (ux + CAL["ink_left_off"], uy + t, ux + W - 0.44, uy + b)

# ---------------------------------------------------------------- node helpers
R_IN, R_HID, R_LIN, R_SUM, R_OUT, R_MIX = 5.0, 5.0, 5.5, 6.0, 6.5, 7.0
NODE = dict(inp=(R_IN, C["IN_FC"], C["IN_EC"], None, 8),
            hid=(R_HID, C["HID_FC"], C["HID_EC"], "\\x(03C3)", 8),
            lin=(R_LIN, C["HID_FC"], C["HID_EC"], "I", 8),
            sum=(R_SUM, C["HID_FC"], C["SUM_EC"], "+", 8),
            outl=(R_OUT, C["OUTL_FC"], C["LF_EC"], None, 8),
            outh=(R_OUT, C["OUTH_FC"], C["HF_EC"], None, 8),
            mix=(R_MIX, C["MIX_FC"], C["MIX_EC"], None, 8))

def node(col, cy, kind, name, tag_above=None, tag_below=None, glyph=None,
         glyph_fs=8, glyph_col=None):
    r, fc, ec, gl, _ = NODE[kind]
    disk(col, cy, r, fill=fc, edge=ec, ew=0.7)
    g = glyph if glyph is not None else gl
    if g is not None:
        text(name + "_g", g, glyph_fs, glyph_col or C["TXT"], col, cy,
             align="center", valign="center", note="node glyph")
    return (col, cy, r)

def connect(A, B, color=None, w=0.35, pad=0.8):
    """fully connect two node columns, trimming each segment at the disk edge"""
    color = color or C["EDGE"]
    pairs = []
    for ax, ay, ar in A:
        for bx, by, br in B:
            dx, dy = bx - ax, by - ay
            d = math.hypot(dx, dy)
            if d < 1e-9:
                continue
            ux, uy = dx / d, dy / d
            s = ar + pad
            e = d - br - pad
            if e <= s:
                continue
            pairs.append(((ax + ux * s, ay + uy * s), (ax + ux * e, ay + uy * e)))
    segs(pairs, color, w)
    return pairs
def link(A, B, color=None, w=0.7, pad=0.8):
    "single straight segment between two nodes, trimmed at both disk edges"
    color = color or C["EDGE"]
    ax, ay, ar = A; bx, by, br = B
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    s, e = ar + pad, d - br - pad
    if e <= s:
        _audit.append("link degenerate: %.2f -> %.2f len %.2f" % (ax, bx, e - s))
        return
    segs([((ax + ux * s, ay + uy * s), (ax + ux * e, ay + uy * e))], color, w)

# ================================================================ PANEL A
# --- panel letter / frame titles
text("A_letter", "\\b(A)", 11, C["TXT"], 0.0, 0.0, note="panel letter")
text("A_t1", "Viscosity / LF prior", 9, C["TXT"], 64.5, 12.5, align="center", note="frame title")
text("A_t2", "Scarce HF D\\-(exp)", 9, C["TXT"], 177.5, 12.5, align="center", note="frame title")

FR1 = (27.0, 26.0, 102.0, 118.0)          # x0,y0,x1,y1  (design pt)
FR2 = (140.0, 26.0, 215.0, 118.0)
AX, AXW = C["AX"], 0.7
TICKL = CAL["tick_len"]

def mini_frame(box):
    x0, y0, x1, y1 = box
    rect_box(x0, y0, x1, y1, AX, AXW)
    return (x0, y0, x1, y1)

def inward_ticks(box, xt, yt):
    """xt/yt: list of design coords of the tick marks on all four sides"""
    x0, y0, x1, y1 = box
    seg = []
    for tx in xt:
        seg.append(((tx, y1), (tx, y1 - TICKL)))          # bottom, inward
        seg.append(((tx, y0), (tx, y0 + TICKL)))          # top, inward
    for ty in yt:
        seg.append(((x0, ty), (x0 + TICKL, ty)))          # left, inward
        seg.append(((x1, ty), (x1 - TICKL, ty)))          # right, inward
    segs(seg, AX, AXW)

# --- FR1 : eta(T) = 1.8 exp(2800/T),  T 900..1400, eta 12..42
f1 = mini_frame(FR1)
T1a, T1b, E1a, E1b = 900.0, 1400.0, 12.0, 42.0
def m1x(T): return FR1[0] + (T - T1a) / (T1b - T1a) * (FR1[2] - FR1[0])
def m1y(e): return FR1[3] - (e - E1a) / (E1b - E1a) * (FR1[3] - FR1[1])
eta_pts = []
for i in range(61):
    T = T1a + (T1b - T1a) * i / 60.0
    eta_pts.append((m1x(T), m1y(1.8 * math.exp(2800.0 / T))))
poly(eta_pts, C["LF_EC"], 1.4)
xt1 = [m1x(t) for t in (900.0, 1100.0, 1300.0)]
yt1 = [m1y(e) for e in (20.0, 30.0, 40.0)]
inward_ticks(FR1, xt1, yt1)
for t, ux in zip(("900", "1100", "1300"), xt1):
    text("A_f1_xt_%s" % t, t, 8, C["TXT"], ux, 120.5, align="center", note="FR1 x tick")
for e, uy in zip(("20", "30", "40"), yt1):
    text("A_f1_yt_%s" % e, e, 8, C["TXT"], 24.0, uy, align="right", valign="center", note="FR1 y tick")
text("A_f1_xlab", "\\i(T) (K)", 8, C["TXT"], 64.5, 130.0, align="center", note="FR1 x title")
text("A_f1_ylab", "\\i(\\x(03B7)) (mPa\\x(00B7)s)", 8, C["LF_EC"], 6.5, 72.0,
     align="left", valign="center", rot=True, note="FR1 y title")
text("A_f1_leg", "\\i(\\x(03B7))(T)", 8, C["LF_EC"], 96.0, 36.5, align="right",
     valign="center", note="FR1 inline series label")

# --- FR2 : log10 D 0.01..0.1 vs T 900..1350
f2 = mini_frame(FR2)
T2a, T2b, L2a, L2b = 900.0, 1350.0, math.log10(0.01), math.log10(0.1)
def m2x(T): return FR2[0] + (T - T2a) / (T2b - T2a) * (FR2[2] - FR2[0])
def m2y(D): return FR2[3] - (math.log10(D) - L2a) / (L2b - L2a) * (FR2[3] - FR2[1])
# identical random draw to the frozen matplotlib reference (default_rng(7))
import numpy as _np
_rnd = _np.random.default_rng(7)
_thf = (950., 1000., 1050., 1100., 1150., 1200., 1250., 1300.)
_Dtrue = 2.5e-9 * _np.exp(-4500.0 / _np.array(_thf)) * 1e9
_Dhf = _Dtrue * (1 + 0.12 * _rnd.normal(size=len(_thf)))
for _t, _d in zip(_thf, _Dhf):
    symbol(m2x(_t), m2y(max(float(_d), 1e-2)), 6.0, C["HF"], C["HF_EC"])
lf_pts = []
for i in range(46):
    T = 900.0 + (1350.0 - 900.0) * i / 45.0
    lf_pts.append((m2x(T), m2y(0.8 * math.exp(-3800.0 / T))))
poly(lf_pts, C["LF"], 1.1, dash="long")
xt2 = [m2x(t) for t in (1000.0, 1200.0)]
yt2 = [m2y(d) for d in (0.01, 0.02, 0.05, 0.1)]
inward_ticks(FR2, xt2, yt2)
for t, ux in zip(("1000", "1200"), xt2):
    text("A_f2_xt_%s" % t, t, 8, C["TXT"], ux, 120.5, align="center", note="FR2 x tick")
for d, lab, uy in zip((0.01, 0.02, 0.05, 0.1), ("0.01", "0.02", "0.05", "0.1"), yt2):
    text("A_f2_yt%s" % lab.replace(".", ""), lab, 8, C["TXT"], 137.0, uy,
         align="right", valign="center", note="FR2 y tick")
text("A_f2_xlab", "\\i(T) (K)", 8, C["TXT"], 177.5, 130.0, align="center", note="FR2 x title")
text("A_f2_ylab", "\\i(D) (10\\+(\\x(2212)9) m\\x(00B2)/s)", 8, C["HF_EC"], 111.0, 72.0,
     align="left", valign="center", rot=True, note="FR2 y title")
text("A_f2_leg1", "\\i(D)\\-(\\x(00A0)exp)", 8, C["HF_EC"], 209.0, 96.0, align="right",
     valign="center", note="FR2 inline label: dots")
text("A_f2_leg2", "\\i(D)\\-(\\x(00A0)LF)", 8, C["LF_EC"], 209.0, 106.0, align="right",
     valign="center", note="FR2 inline label: dashed prior")

# --- A: two callout bars
BAR = ((6.0, 141.5, 216.0, 153.5, C["BOX_LF"], C["LF"],
        "Modified Sutherland: \\i(D)\\-(LF) = \\i(k)\\-(B)\\i(T)/\\x(00B7)(\\i(c)\\x(00B7)\\x(03B7)\\x(00B7)\\i(r)\\-(i))"),
       (6.0, 155.5, 216.0, 167.5, C["BOX_HF"], C["HF"],
        "HF targets: \\i(y)\\-(H) = log\\-(10) \\i(D)\\-(exp) (sparse)"))
for i, (bx0, by0, bx1, by1, fc, ec, t) in enumerate(BAR):
    fill_rect(bx0, by0, bx1, by1, fc)
    rect_box(bx0, by0, bx1, by1, ec, 0.6, owner=("A_bar%d" % i,))
    text("A_bar%d" % i, t, 8, C["TXT"], 0.5 * (bx0 + bx1), 0.5 * (by0 + by1),
         align="center", valign="center", note="callout bar")
# ================================================================ shared NN helpers
def arrow_between(A, B, color=None, w=0.6, head=4.6, pad=0.9):
    """arrow from the edge of node A to the edge of node B (nodes = (x,y,r))"""
    color = color or C["TXT"]
    x1, y1, r1 = A; x2, y2, r2 = B
    dx, dy = x2 - x1, y2 - y1
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    s, e = r1 + pad, d - r2 - pad
    if e - s < 3.0:
        _audit.append("short arrow %s->%s len=%.2f" % (A[:2], B[:2], e - s))
    arrow(x1 + ux * s, y1 + uy * s, x1 + ux * e, y1 + uy * e, color, w, head)

def dashed_box(col0, px0, py0, px1, py1, color=None, w=0.7, dash="short"):
    """dashed module box from panel coords (px0,py0)-(px1,py1) using PC/PD-style map"""
    a = col0(px0, py0); b = col0(px1, py1)
    rect_box(a[0], a[1], b[0], b[1], color or C["BOX_EC"], w, dash)
    return (a[0], a[1], b[0], b[1])

# ================================================================ PANEL B
text("B_letter", "\\b(B)", 11, C["TXT"], COL2, 0.0, note="panel letter")
text("B_title", "\\b(Single-fidelity NN)", 9, C["TXT"], COL2 + 111.0, 2.0,
     align="center", note="panel title")
BX_IN, BX_H1, BX_H2, BX_O = 262.0, 308.0, 354.0, 400.0
b_in = []
for i, (lab, py) in enumerate([("\\i(T)", 4.6), ("\\i(x)", 3.533), ("\\i(\\x(03B7))", 2.467),
                               ("type", 1.4)]):
    x, y = PB(0.0, py); x = BX_IN
    b_in.append(node(x, y, "inp", "B_in%d" % i))
    text("B_inl%d" % i, lab, 8, C["TXT"], 253.0, y, align="right", valign="center",
         note="input label")
b_h1 = [node(BX_H1, PB(0.0, py)[1], "hid", "B_h1_%d" % i)
        for i, py in enumerate([4.7, 3.9, 3.1, 2.3, 1.5])]
b_h2 = [node(BX_H2, PB(0.0, py)[1], "hid", "B_h2_%d" % i)
        for i, py in enumerate([4.5, 3.5, 2.5, 1.5])]
b_out = node(BX_O, PB(0.0, 3.0)[1], "outh", "B_out")
text("B_yl", "\\i(y)", 8, C["HF_EC"], BX_O, 66.5, align="center", note="output label")
text("B_ylog", "log\\-(10) \\i(D)", 8, C["SUB"], BX_O + 11.0, 92.0, align="left", valign="center", note="output unit")
connect(b_in, b_h1); connect(b_h1, b_h2); connect(b_h2, [b_out])
text("B_cap", "\\i(HF-only baseline (no LF channel))", 8, C["CAP"], COL2 + 111.0, 153.0,
     align="center", valign="center", note="panel caption")

# ================================================================ PANEL C
text("C_letter", "\\b(C)", 11, C["TXT"], COL1, ROW2[0], note="panel letter")
text("C_title", "\\b(Multi-fidelity NN)", 9, C["TXT"], COL1 + 111.0, ROW2[0] + 1.0,
     align="center", note="panel title")
CL = lambda px, py: PC(px, py)
c_in = []
for i, (lab, py) in enumerate([("\\i(x)\\-(1)", 4.3), ("\\i(x)\\-(2)", 2.7)]):
    x, y = CL(1.00, py)
    c_in.append(node(x, y, "inp", "C_in%d" % i))
    text("C_inl%d" % i, lab, 8, C["TXT"], x - 8.0, y, align="right", valign="center",
         note="input label")
c_l1 = [node(CL(2.00, py)[0], CL(2.00, py)[1], "hid", "C_l1_%d" % i)
        for i, py in enumerate([4.2, 3.25, 2.3])]
c_l2 = [node(CL(2.75, py)[0], CL(2.75, py)[1], "hid", "C_l2_%d" % i)
        for i, py in enumerate([3.75, 2.75])]
c_yl = node(*CL(4.05, 3.25), "outl", "C_yl")
text("C_yl_lab", "\\i(y)\\-(L)", 8, C["LF_EC"], CL(4.05, 0)[0], 240.0, align="center",
     note="LF output label")
halo_behind("C_yl_lab", C["CHIP"])
c_hb = dashed_box(CL, 4.62, 1.00, 8.90, 4.85)
c_lb = dashed_box(CL, 1.45, 1.50, 3.20, 5.00)
text("C_nnL", "\\i(NN)\\-(L)", 8, C["TAG"], CL(2.325, 0)[0], 195.5, align="center",
     note="module tag")
text("C_nnH", "\\i(NN)\\-(H)", 8, C["TAG"], CL(6.76, 0)[0], 195.5, align="center",
     note="module tag")
c_hin = [node(CL(5.15, py)[0], CL(5.15, py)[1], "inp", "C_hin%d" % i)
         for i, py in enumerate([4.05, 3.35, 2.65])]
c_nl1 = [node(CL(6.05, py)[0], CL(6.05, py)[1], "hid", "C_nl1_%d" % i)
         for i, py in enumerate([3.85, 3.15, 2.45])]
c_nl2 = [node(CL(6.85, py)[0], CL(6.85, py)[1], "hid", "C_nl2_%d" % i)
         for i, py in enumerate([3.5, 2.8])]
c_lin = node(*CL(6.45, 1.35), "lin", "C_lin")
c_plus = node(*CL(8.45, 2.5), "sum", "C_plus")
c_yh = node(*CL(9.45, 2.5), "outh", "C_yh")
text("C_yh_lab", "\\i(y)\\-(H)", 8, C["HF_EC"], CL(9.45, 0)[0], 258.5, align="center",
     note="HF output label")
connect(c_in, c_l1); connect(c_l1, c_l2); connect(c_l2, [c_yl])
connect(c_in, c_hin[:2], w=0.3)
connect(c_hin, c_nl1); connect(c_nl1, c_nl2)
link(c_yl, c_hin[2], C["LF"], 0.7)
connect(c_hin, [c_lin], w=0.3)
for n in c_nl2:
    arrow_between(n, c_plus, w=0.6)
arrow_between(c_lin, c_plus, w=0.6)
arrow_between(c_plus, c_yh, w=0.7)
text("C_cap", "\\i(Composite MFNN: linear \\x(0049) + nonlinear \\x(03C3) on [\\x(00A0)x, y\\-(L)])",
     8, C["CAP"], COL1 + 111.0, 341.5, align="center", valign="center", note="panel caption")
# ================================================================ PANEL D
fill_rect(COL2, ROW2[0], COL2 + COLW, ROW2[1], C["WASH_D"])     # wash, drawn first
text("D_letter", "\\b(D)", 11, C["TXT"], COL2, ROW2[0], note="panel letter")
text("D_title", "\\b(Residual multi-fidelity NN (this work))", 9, C["MFNN_EC"],
     COL2 + 111.0, ROW2[0] + 1.0, align="center", note="panel title")
DL = lambda px, py: PD(px, py)
d_in = []
for i, (lab, py) in enumerate([("\\i(T)", 4.4), ("\\i(x)", 3.25), ("\\i(\\x(03B7))", 2.1)]):
    x, y = DL(1.00, py)
    d_in.append(node(x, y, "inp", "D_in%d" % i))
    text("D_inl%d" % i, lab, 8, C["TXT"], x - 8.0, y, align="right", valign="center",
         note="input label")
d_l1 = [node(*DL(2.00, py), "hid", "D_l1_%d" % i) for i, py in enumerate([4.2, 3.25, 2.3])]
d_l2 = [node(*DL(2.75, py), "hid", "D_l2_%d" % i) for i, py in enumerate([3.75, 2.75])]
d_yl = node(*DL(4.05, 3.25), "outl", "D_yl")
text("D_yl_lab", "\\i(y)\\-(L)", 8, C["LF_EC"], DL(4.05, 0)[0], 240.0, align="center",
     note="LF output label")
halo_behind("D_yl_lab", C["WASH_D"])
d_hb = dashed_box(DL, 4.62, 1.00, 8.90, 4.85)
d_lb = dashed_box(DL, 1.45, 1.50, 3.20, 5.00)
text("D_nnL", "\\i(NN)\\-(L)", 8, C["TAG"], DL(2.325, 0)[0], 195.5, align="center",
     note="module tag")
text("D_nnH", "\\i(NN)\\-(H) (residual)", 8, C["TAG"], DL(6.76, 0)[0], 195.5, align="center",
     note="module tag")
d_hin = [node(*DL(5.15, py), "inp", "D_hin%d" % i)
         for i, py in enumerate([4.05, 3.35, 2.65, 1.95])]
d_nl1 = [node(*DL(6.05, py), "hid", "D_nl1_%d" % i) for i, py in enumerate([3.85, 3.15, 2.45])]
d_nl2 = [node(*DL(6.85, py), "hid", "D_nl2_%d" % i) for i, py in enumerate([3.5, 2.8])]
d_lin = node(*DL(6.45, 1.35), "lin", "D_lin")
d_mixn = node(*DL(7.65, 3.5), "mix", "D_mixn")
d_mixl = node(*DL(7.65, 1.35), "mix", "D_mixl")
d_plus = node(*DL(8.45, 2.5), "sum", "D_plus")
d_yh = node(*DL(9.45, 2.5), "outh", "D_yh")
text("D_a2", "\\b(\\x(03B1))\\-(2)", 8, C["LF_EC"], DL(7.65, 3.5)[0], DL(7.65, 3.5)[1],
     align="center", valign="center", note="mixing weight inside node")
text("D_a1", "\\b(\\x(03B1))\\-(1)", 8, C["LF_EC"], DL(7.65, 1.35)[0], DL(7.65, 1.35)[1],
     align="center", valign="center", note="mixing weight inside node")
text("D_yh_lab", "\\i(y)\\-(H)", 8, C["HF_EC"], DL(9.45, 0)[0], 258.5, align="center",
     note="HF output label")
_Dhat = "\\i(D)\\-(HF)"
text("D_yh_sub", _Dhat, 8, C["SUB"], 439.8, 292.0, align="center", note="output unit")
_HATW = 2.9
_hx = 439.8 - 0.5 * tw(_Dhat, 8) + 0.5 * tw("\\i(D)", 8)
poly([(_hx - _HATW, 290.4), (_hx, 288.6), (_hx + _HATW, 290.4)], C["SUB"], 0.6,
     owner="D_yh_sub")

connect(d_in, d_l1); connect(d_l1, d_l2); connect(d_l2, [d_yl])
connect(d_in, d_hin[:3], w=0.3)
connect(d_hin, d_nl1); connect(d_nl1, d_nl2)
connect(d_hin, [d_lin], w=0.3)
link(d_yl, d_hin[3], C["LF"], 0.7)
for n in d_nl2:
    arrow_between(n, d_mixn, w=0.55)
arrow_between(d_lin, d_mixl, w=0.55)
arrow_between(d_mixn, d_plus, w=0.65)
arrow_between(d_mixl, d_plus, w=0.65)
arrow_between(d_plus, d_yh, w=0.7)

# --- vermillion residual link: y_L -> (+), bridged over the top node columns
def catmull(P, n=14):
    Q = [P[0]] + list(P) + [P[-1]]
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for k in range(n):
            t = k / float(n); t2 = t * t; t3 = t2 * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append((P[-1][0], P[-1][1]))
    return out

ARC_WPTS = [(d_yl[0] + 6.0, d_yl[1] - 5.0), (d_yl[0] + 14.0, d_yl[1] - 24.0),
            (DL(5.15, 0)[0] + 2.0, 223.0), (DL(6.05, 0)[0] + 4.0, 216.5),
            (DL(6.85, 0)[0] + 12.0, 216.0), (d_plus[0] - 4.0, 224.0),
            (d_plus[0] + 0.5, d_plus[1] - d_plus[2] - 1.3)]
_arc = catmull(ARC_WPTS)
def _out_of(p, nd, extra=1.1):
    return math.hypot(p[0] - nd[0], p[1] - nd[1]) > nd[2] + extra
_arc = [p for p in _arc if _out_of(p, d_yl) and _out_of(p, d_plus)]
_head = CAL["arrow_head_scale"]
# peel the arrowhead off the tail of the curve
_tip = _arc[-1]
_cut = len(_arc) - 1
_acc = 0.0
while _cut > 1 and _acc < 5.0:
    _acc += math.hypot(_arc[_cut][0] - _arc[_cut - 1][0], _arc[_cut][1] - _arc[_cut - 1][1])
    _cut -= 1
poly(_arc[:_cut + 1], C["RES"], 1.35)
arrow(_arc[_cut][0], _arc[_cut][1], _tip[0], _tip[1], C["RES"], 1.35, head=5.4)
RES_MIN = min(min(math.hypot(p[0] - n[0], p[1] - n[1]) - n[2] for p in _arc)
              for n in (d_yl, d_hin[0], d_nl1[0], d_nl2[0], d_mixn, d_plus, d_lin, d_mixl))
_audit.append("residual arc: min clearance to nodes = %.2f pt" % RES_MIN)
text("D_res", "\\i(residual)", 8, C["RES"], 390.0, 226.0, align="center",
     note="residual link label")

# --- D equation strip (two lines)
fill_rect(236.0, 325.0, 448.0, 350.0, "#F7FBF9")
rect_box(236.0, 325.0, 448.0, 350.0, C["MFNN"], 0.7, owner=("D_eq1", "D_eq2"))
text("D_eq1", "\\i(y)\\-(H) = \\x(03B1)\\-(1)(A[x,\\x(00A0)y\\-(L)]+b) + \\x(03B1)\\-(2)F\\-(nl)(x,\\x(00A0)y\\-(L))",
     8, C["TXT"], 342.0, 332.5, align="center", valign="center", note="model equation")
text("D_eq2", "\\i(y)\\-(L) = log\\-(10) \\i(D)\\-(LF)   \\x(00B7)   positivity \\i(D)\\-(\\x(00A0)HF) = 10\\+(\\i(y)\\-(H))",
     8, C["SUB"], 342.0, 343.5, align="center", valign="center", note="model notes")
# ================================================================ KEY STRIP
# colour / symbol key under the four panels: swatch + Arial 8 pt caption.
KEY_X0, KEY_X1 = 4.0, 448.0
KEY_ROWS = (361.5, 374.0)
KEY_ROW_X = (0.0, 10.0)
SW = 16.0                      # swatch width
GAP = 9.0                      # gap between items
KEY_ITEMS = [
    ("disk", "inp",  None,               "input"),
    ("disk", "hid",  None,               "hidden neuron"),
    ("disk", "lin",  None,               "linear term"),
    ("disk", "sum",  None,               "summation"),
    ("disk", "outl", None,               "LF output"),
    ("disk", "outh", None,               "HF output"),
    ("disk", "mix",  "\\b(\\x(03B1))",   "mixing weight"),
    ("res",  None,   None,               "residual link"),
    ("conn", None,   None,               "full connectivity"),
    ("lf",   None,   None,               "LF branch"),
    ("dot",  None,   None,               "HF data"),
    ("dashl", None,  None,               "LF prior"),
    ("box",  None,   None,               "\\i(NN) module"),
]
def key_swatch(kind, arg, glyph, x, cy):
    if kind == "disk":
        r = NODE[arg][0]
        node(x + r, cy, arg, "K_%d" % int(x * 10), glyph=glyph)
    elif kind == "res":
        arrow(x, cy, x + SW, cy, C["RES"], 1.35, head=4.6)
    elif kind == "conn":
        segs([[(x, cy - 3.2), (x + SW, cy + 3.2)],
              [(x, cy + 3.2), (x + SW, cy - 3.2)]], C["EDGE"], 0.35)
    elif kind == "lf":
        line([(x, cy + 2.0), (x + SW, cy - 2.0)], C["LF"], 0.9)
    elif kind == "dot":
        disk(x + 0.5 * SW, cy, 3.0, C["HF"], C["HF_EC"], 0.6)
    elif kind == "dashl":
        line([(x, cy), (x + SW, cy)], C["LF"], 1.1, dash="long")
    elif kind == "box":
        rect_box(x, cy - 4.5, x + SW, cy + 4.5, C["BOX_EC"], 0.7, "short")

KEYBOX = None
def pack_key():
    global KEYBOX
    rows = [[] for _ in KEY_ROWS]
    for kind, arg, glyph, lab in KEY_ITEMS:
        w = SW + 3.0 + inkw(lab, 8)
        rows[0].append((kind, arg, glyph, lab, w))
    # greedy split into two rows of roughly equal width
    tot = sum(it[4] + GAP for it in rows[0]) + KEY_X0 - GAP
    best, bs = 1, 1e9
    for k in range(1, len(rows[0])):
        w0 = KEY_X0 + sum(it[4] + GAP for it in rows[0][:k]) - GAP
        w1 = KEY_X0 + sum(it[4] + GAP for it in rows[0][k:]) - GAP
        sc = abs(max(w0, w1) - KEY_X1) + 6.0 * abs(w0 - w1)
        if sc < bs:
            bs, best = sc, k
    out = [rows[0][:best], rows[0][best:]]
    for ri, row in enumerate(out):
        x = KEY_X0 + KEY_ROW_X[ri]
        cy = KEY_ROWS[ri]
        for kind, arg, glyph, lab, w in row:
            key_swatch(kind, arg, glyph, x, cy)
            text("K_lab%d" % ri + "_" + str(int(x)), lab, 8, C["TXT"],
                 x + SW + 3.0, cy, align="left", valign="center", note="key caption")
            x += w + GAP
        _audit.append("key row %d: %d items, right edge %.1f (limit %.1f)"
                      % (ri, len(row), x - GAP, KEY_X1))
    return out
KEYROWS = pack_key()

# ================================================================ GEOMETRY AUDIT
def _polys():
    """all vector ink as (kind, segments) ; kind in line/arrow"""
    seg = []
    for it in LINES:
        pts = it["pts"]
        cur = []
        for p in pts:
            if p is None:
                if len(cur) > 1:
                    seg += [(cur[i], cur[i + 1], it) for i in range(len(cur) - 1)]
                cur = []
            else:
                cur.append((p[0], p[1]))
        if len(cur) > 1:
            seg += [(cur[i], cur[i + 1], it) for i in range(len(cur) - 1)]
    return seg
SEG = _polys()
for a in ARRS:
    SEG.append(((a["x1"], a["y1"]), (a["x2"], a["y2"]),
                dict(color=a["color"], w=a["w"], dash="solid", kind="arrow", head=a["head"])))

def seg_pt(a, b, p):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < 1e-12:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def box_seg(b, a, c):
    """true if segment a-c intersects or touches rectangle b=(x0,y0,x1,y1)"""
    x0, y0, x1, y1 = b
    if min(a[0], c[0]) > x1 or max(a[0], c[0]) < x0 or min(a[1], c[1]) > y1 or max(a[1], c[1]) < y0:
        return False
    return seg_pt(a, c, (max(x0, min(x1, 0.5 * (a[0] + c[0]))),
                         max(y0, min(y1, 0.5 * (a[1] + c[1]))))) < 1e-9 or _segbx(b, a, c)

def _segbx(b, a, c):
    """exact segment / rectangle overlap test (Liang-Barsky)"""
    x0, y0, x1, y1 = b
    dx, dy = c[0] - a[0], c[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return False
    return True

def seg_box_d(b, a, c):
    """minimum distance from a segment to a rectangle (0 if they touch)"""
    x0, y0, x1, y1 = b
    if _segbx(b, a, c):
        return 0.0
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    d = min(seg_pt(a, c, p) for p in corners)
    d = min(d, min(seg_pt((x0, y0), (x1, y0), p) for p in (a, c)))
    d = min(d, min(seg_pt((x1, y0), (x1, y1), p) for p in (a, c)))
    d = min(d, min(seg_pt((x1, y1), (x0, y1), p) for p in (a, c)))
    d = min(d, min(seg_pt((x0, y1), (x0, y0), p) for p in (a, c)))
    return d

BK = []
for it in TXTS:
    BK.append((it["name"], ink_box(it), it))

R = []
W = R.append
W("Fig.1 design audit  (design pt, Y down, ink box 0..%.1f x 0..%.1f)" % (INK_W, INK_H))
W("texts=%d  vector-segments=%d  disks=%d  symbol-groups-input=%d  arrows=%d  fills=%d"
  % (len(TXTS), len(SEG), len(DISKS), len(SYMS), len(ARRS), len(FILLS)))

# --- 1. ink inside the canvas
bad = [(nm, b) for nm, b, it in BK
       if b[0] < -0.4 or b[2] > INK_W + 0.4 or b[1] < -0.4 or b[3] > INK_H + 0.4]
W("[bounds] violations: %d %s" % (len(bad), [nm for nm, b in bad]))
for nm, b in bad:
    W("   %-12s ink=(%.1f,%.1f,%.1f,%.1f)" % (nm, b[0], b[1], b[2], b[3]))

# --- 2. text vs text
own = set(nm for nm, b, it in BK if it["note"] == "node glyph")
worst = []
for i in range(len(BK)):
    for j in range(i + 1, len(BK)):
        n1, b1, t1 = BK[i]; n2, b2, t2 = BK[j]
        gx = max(b1[0], b2[0]) - min(b1[2], b2[2])
        gy = max(b1[1], b2[1]) - min(b1[3], b2[3])
        if gx >= 0 or gy >= 0:
            g = math.hypot(max(gx, 0.0), max(gy, 0.0))
        else:
            g = -min(-gx, -gy)
        worst.append((g, n1, n2))
worst.sort()
W("[text-text] worst 10 gaps:")
for g, n1, n2 in worst[:10]:
    W("   %7.2f  %-14s %-14s" % (g, n1, n2))

# --- 3. text vs vector ink (lines, dashed boxes, arrows)
PADT = 0.8
hits = []
nmask = []
for nm, b, it in BK:
    if it["note"] == "node glyph":
        continue
    bb = (b[0] - PADT, b[1] - PADT, b[2] + PADT, b[3] + PADT)
    masked = 0
    mind, who = 9e9, None
    for a, c, s in SEG:
        own = s.get("owner")
        if own is not None and nm in (own if isinstance(own, tuple) else (own,)):
            continue
        if nm in HALOED and s.get("kind") != "arrow":
            masked += 1
            continue
        d = seg_box_d(bb, a, c)
        if d < mind:
            mind, who = d, (a, c, s)
    if masked:
        nmask.append("%s(%d)" % (nm, masked))
    if mind < 1.2:
        hits.append((nm, round(mind, 2), who[0], who[1], who[2].get("kind", "line"), who[2]["color"]))
W("[text-line] ink within 1.2 pt of a text box (pad %.1f): %d" % (PADT, len(hits)))
W("[text-line] halo-masked polylines: %s" % (nmask if nmask else "none"))
for h in hits:
    W("   %-12s d=%.2f  (%.1f,%.1f)-(%.1f,%.1f) %s %s"
      % (h[0], h[1], h[2][0], h[2][1], h[3][0], h[3][1], h[4], h[5]))

# --- 4. text vs disks (glyphs excepted)
td = []
for nm, b, it in BK:
    if it["note"] in ("node glyph", "mixing weight inside node"):
        continue
    for d in DISKS:
        cx, cy, r = d["cx"], d["cy"], d["r"]
        px = max(b[0], min(b[2], cx)); py = max(b[1], min(b[3], cy))
        dd = math.hypot(cx - px, cy - py)
        if dd - r < 1.2:
            td.append((nm, round(dd - r, 2), (round(cx, 1), round(cy, 1), r)))
td.sort(key=lambda z: z[1])
W("[text-disk] clearance < 1.2 pt: %d" % len(td))
for t in td[:16]:
    W("   %-12s d=%.2f disk=%s" % t)
W("[glyph-in-disk] ink corner radius vs disk radius:")
for nm, b, it in BK:
    if it["note"] != "mixing weight inside node":
        continue
    cx0 = 0.5 * (b[0] + b[2]); cy0 = 0.5 * (b[1] + b[3])
    dsk = min(DISKS, key=lambda d: math.hypot(d["cx"] - cx0, d["cy"] - cy0))
    m = max(math.hypot(px - dsk["cx"], py - dsk["cy"])
            for px, py in ((b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])))
    W("   %-8s disk r=%.1f corner=%.1f  %s" % (nm, dsk["r"], m,
      "FITS" if m < dsk["r"] - 0.8 else "TIGHT - move outside"))
W("[halo] polylines clipped by a halo chip:")
_hbad = []
for f in FILLS:
    if f.get("kind") != "halo":
        continue
    hb = (f["top"][0][0], f["top"][0][1], f["bottom"][1][0], f["bottom"][1][1])
    for a, c, s in SEG:
        if s.get("kind") == "arrow" or s["color"] == C["RES"]:
            continue
        if seg_box_d(hb, a, c) == 0.0:
            _hbad.append((hb, s["color"]))
W("   none" if not _hbad else "".join(["\n   halo=(%.1f,%.1f,%.1f,%.1f) clips %s"
                                       % (z[0][0], z[0][1], z[0][2], z[0][3], z[1]) for z in _hbad[:8]]))

# --- 5. disk vs disk, disk vs vector ink
ov = []
for i in range(len(DISKS)):
    for j in range(i + 1, len(DISKS)):
        a, b2 = DISKS[i], DISKS[j]
        dd = math.hypot(a["cx"] - b2["cx"], a["cy"] - b2["cy"]) - a["r"] - b2["r"]
        if dd < 1.0:
            ov.append((round(dd, 2), (a["cx"], a["cy"]), (b2["cx"], b2["cy"])))
ov.sort()
W("[disk-disk] overlaps < 1.0 pt: %d" % len(ov))
for o in ov[:12]:
    W("   %.2f  %s %s" % o)
dl = []
for d in DISKS:
    for a, c, s in SEG:
        if s.get("kind") == "arrow":
            continue
        if seg_pt(a, c, (d["cx"], d["cy"])) < d["r"] - 0.35:
            dl.append((round(d["cx"], 1), round(d["cy"], 1), d["r"],
                       (a, c), s["color"], s["dash"]))
W("[disk-line] vector ink crossing a disk interior: %d (expected for hidden full-"
  "connectivity hairlines drawn underneath)" % len(dl))
for z in dl[:6]:
    W("   node (%.1f,%.1f) r=%.1f  seg %s %s %s" % (z[0], z[1], z[2], z[3], z[4], z[5]))

# --- 6. residual arc clearance (arc is the vermillion polyline)
arc_pts = []
for a, c, s in SEG:
    if s["color"] == C["RES"] and s["w"] > 1.0:
        arc_pts += [a, c]
if arc_pts:
    worst = 9e9; who = None
    for p in arc_pts:
        for d in DISKS:
            g = math.hypot(p[0] - d["cx"], p[1] - d["cy"]) - d["r"]
            if g < worst:
                worst, who = g, (round(d["cx"], 1), round(d["cy"], 1), d["r"])
        for nm, b, it in BK:
            if it["note"] == "node glyph":
                continue
            px = max(b[0], min(b[2], p[0])); py = max(b[1], min(b[3], p[1]))
            dd = math.hypot(p[0] - px, p[1] - py)
            if dd < worst:
                worst, who = dd, (nm, round(b[0], 1), round(b[1], 1), round(b[2], 1), round(b[3], 1))
    W("[arc] points=%d  min clearance=%.2f pt  nearest=%s" % (len(arc_pts), worst, who))

# --- 7. rect-contained text (callout bars, equation strip, key rows)
def inside(rect, names, tag, pad=2.0):
    ok = True
    for nm in names:
        b = dict((x[0], x[1]) for x in BK)[nm]
        if b[0] < rect[0] + pad or b[2] > rect[2] - pad or b[1] < rect[1] + pad or b[3] > rect[3] - pad:
            ok = False
            W("   [%s] %-10s ink=(%.1f,%.1f,%.1f,%.1f) rect=(%.1f,%.1f,%.1f,%.1f) OVERFLOW"
              % (tag, nm, b[0], b[1], b[2], b[3], rect[0], rect[1], rect[2], rect[3]))
    if ok:
        W("   [%s] all text fits with >=%.1f pt" % (tag, pad))
W("[contain]")
inside((BAR[0][0], BAR[0][1], BAR[0][2], BAR[0][3]), ["A_bar0"], "bar1", pad=1.3)
inside((BAR[1][0], BAR[1][1], BAR[1][2], BAR[1][3]), ["A_bar1"], "bar2", pad=1.3)
inside((236.0, 325.0, 448.0, 350.0), ["D_eq1", "D_eq2"], "Dstrip")
_kb = []
for nm, b, it in BK:
    if not nm.startswith("K_lab"):
        continue
    if b[2] > KEY_X1 + 0.5 or b[0] < KEY_X0 - 0.5 or b[1] < KEYY[0] - 0.5 or b[3] > KEYY[1] + 0.5:
        _kb.append("   [keyrow] %-12s x=(%.1f,%.1f) y=(%.1f,%.1f)" % (nm, b[0], b[2], b[1], b[3]))
W("\n".join(_kb) if _kb else "   [keyrow] all captions inside %.1f..%.1f / %.1f..%.1f"
  % (KEY_X0, KEY_X1, KEYY[0], KEYY[1]))

# --- 8. font floor and effective size after the Word paste
fsmin = min(it["fs"] for it in TXTS)
target_in = 6.30
scale = target_in * 72.0 / INK_W
W("[fonts] min design fs=%d pt ; paste width %.2f in -> scale %.4f -> smallest rendered %.2f pt"
  % (fsmin, target_in, scale, fsmin * scale))
W("[fonts] ink width %.1f pt = %.2f mm ; ink height %.2f mm (<= 180 mm target)"
  % (INK_W, INK_W * 25.4 / 72.0, INK_H * 25.4 / 72.0))

W("[builder notes]")
for m in _audit:
    W("   " + m)
txt = "\n".join(R) + "\n"
io.open(os.path.join(OD, "_qa_fig1_design.txt"), "w", encoding="ascii", errors="replace").write(txt)

GRP = {}
for d in DISKS:
    GRP.setdefault((round(2 * d["r"], 2), d["fill"], d["edge"], round(d["ew"], 2)), []).append(
        [round(d["cx"], 3), round(d["cy"], 3)])
for s in SYMS:
    GRP.setdefault((round(s["dia"], 2), s["fill"], s["edge"], 0.7), []).append(
        [round(s["cx"], 3), round(s["cy"], 3)])
symbols = [dict(dia=k[0], fill=k[1], edge=k[2], ew=k[3], pts=v) for k, v in GRP.items()]

data = dict(cal=dict(CAL, ink_w=INK_W, ink_h=INK_H, ox=OX, oy=OY),
            palette=C, dash=DASH, texts=TXTS, lines=LINES, fills=FILLS,
            symbols=symbols, arrows=ARRS,
            notes=dict(key_rows=[[list(t[4:5]) for t in r] for r in KEYROWS]))
json.dump(data, io.open(os.path.join(OD, "fig1_origin_constants.json"), "w", encoding="utf-8"),
          indent=1, sort_keys=True)
print("wrote json: texts=%d lines=%d seg=%d symbols=%d arrows=%d fills=%d"
      % (len(TXTS), len(LINES), len(SEG), len(symbols), len(ARRS), len(FILLS)))
print("min fs=%d  worst arc=%s" % (fsmin, [z for z in R if z.startswith("[arc]")]))