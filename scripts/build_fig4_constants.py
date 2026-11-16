"""Build fig4_origin_constants.json from the frozen matplotlib reference geometry.
No metric recomputation; only text/geometry bookkeeping.

FINAL-FIX pass (2026-11-03, Fig.4 Origin only):
  * legend block back on the reference lines (LEG_DY = 0) -> above the 0.301 guide
  * panel-A note restored to the reference 2-line wrap / right edge, panel-B notes to the
    upper-left (they used to be pushed into the free lower-right corner)
  * b_xtitle gets the real superscript (y_L^proxy) and the D-hat marks are carried as
    polylines (Origin cannot set U+0302)
  * text targets are pen-x / baseline pairs taken straight from the frozen reference,
    the anchor->pen correction is measured per item by the Origin probe (calib_fig4_anchor_read.py)
"""
import os, json
from PIL import ImageFont

B   = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD  = os.path.join(B, "outputs", "origin_data")
PT  = 72.0 / 2.54
OFF = 0.25                      # cm: design origin inset from page corner
FSMAP = {"4.5":[19,4.5153,5.0796],"5.0":[21,5.0166,5.6437],"5.5":[23,5.5183,6.2081],
         "6.5":[27,6.478,7.2877],"7.5":[31,7.4377,8.3674],"8.0":[33,7.9175,8.9072],
         "9.0":[38,9.1172,11.3365],"10.0":[42,10.0769,11.3365]}
FSMAP["9.0"][2] = 10.2568
def fsr(fs): return FSMAP["%.1f" % fs][1]

# ---------- Arial advance model (sub/superscript = 0.684x, Origin \-(...) \+(...) ) ----------
FD = r"C:\Windows\Fonts"
P  = {"reg": FD+r"\arial.ttf", "bold": FD+r"\arialbd.ttf", "ital": FD+r"\ariali.ttf",
      "boldital": FD+r"\arialbi.ttf"}
_c = {}
def F(face, px):
    k = (face, px)
    if k not in _c: _c[k] = ImageFont.truetype(P[face], px)
    return _c[k]
def W(face, txt, size):
    if not txt: return 0.0
    return F(face, max(1, int(round(size*100)))).getlength(txt)/100.0
def match(t, j):
    d = 0
    while j < len(t):
        if t[j] == "(": d += 1
        elif t[j] == ")":
            d -= 1
            if d == 0: return j
        j += 1
    raise ValueError(t)
def _emit(acc, ch, face, scale, merge=True):
    if merge and acc and acc[-1][1] == face and abs(acc[-1][2]-scale) < 1e-9:
        acc[-1][0] += ch
    else:
        acc.append([ch, face, scale])
def runs(t, face="reg", scale=1.0, acc=None, merge=True):
    if acc is None: acc = []
    i = 0
    while i < len(t):
        if t[i] == "\\" and i+1 < len(t):
            n = t[i+1]
            if n == "x":
                a = t.index("(", i+2); b = t.index(")", a)
                _emit(acc, chr(int(t[a+1:b], 16)), face, scale, merge); i = b+1; continue
            if n in ("i", "b", "-", "+"):
                a = i+2
                if t[a] != "(" and n in "-+": grp, b = t[a], a
                else: b = match(t, a); grp = t[a+1:b]
                stack = (face, scale)
                if n == "i": face = "ital" if face == "reg" else "boldital"
                elif n == "b": face = "bold" if face == "reg" else "boldital"
                elif n in "-+": scale = scale*0.684
                runs(grp, face, scale, acc, merge); face, scale = stack; i = b+1; continue
            if n == "\\": _emit(acc, "\\", face, scale, merge); i += 2; continue
        _emit(acc, t[i], face, scale, merge); i += 1
    return acc
def width(t, fs, merge=True):
    """rendered advance in design pt when the item is placed with nominal fs"""
    return sum(W(f, s, fsr(fs)*sc) for s, f, sc in runs(t, merge=merge))
def glyph_adv(t, fs, want, occ):
    """(x_before, w) of the occ-th character `want` in the expanded markup stream"""
    x = 0.0; seen = 0
    for ch, face, sc in runs(t, merge=False):
        w = W(face, ch, fsr(fs)*sc)
        if ch == want:
            if seen == occ: return x, w
            seen += 1
        x += w
    raise ValueError("%s: no #%d '%s' in %s" % (t, occ, want, ascii(t)[:40]))

# ---------- frozen reference geometry (design pt, top-left origin) ----------
FR = {"a": dict(x0=31.802, x1=184.401, y0=17.399, y1=126.743),
      "b": dict(x0=227.854, x1=380.447, y0=17.399, y1=126.743)}
for p in FR.values():
    p["w"] = p["x1"]-p["x0"]; p["h"] = p["y1"]-p["y0"]
    p["cx"] = p["x0"]+p["w"]/2.0; p["cy"] = p["y0"]+p["h"]/2.0
TICK = 3.62                      # inward tick length, design pt
# lay0 canvas design-pt -> rendered raw-PDF pt (measured on the panel frames)
PDFX, PDFY = 7.0866, 7.872
DX = round(PDFX - 0.05*72/2.54, 4)     # 5.6693
DY = round(0.05*72/2.54 + 13.4*PT - PDFY, 4)
# D-hat caret geometry, measured from the frozen reference ink (design pt)
HAT = dict(rise=7.85, leg=1.26, half=1.24, lead=0.86)
# anchor -> pen/base offsets measured on the Origin probe page (calib_fig4_anchor_read.py)
OFFJ = os.path.join(OD, "fig4_text_offsets.json")
OFFS = json.load(open(OFFJ, encoding="utf-8")) if os.path.exists(OFFJ) else {}

def H(name, txt, fs, color, Lx, By, align="pen", tx=None):
    d = dict(name=name, txt=txt, fs=fs, color=color, rot=False,
             Lx=round(Lx,4), By=round(By,4), align=align)
    if tx is not None: d["tx"] = round(tx, 4)
    return d
# FINAL-FIX (ink audit): the anchor probe reported a_ytitle's anchor->pen offset against
# the subscript column (jx1) instead of the main baseline, so the rotated A title rendered
# 2.111 pt left of the frozen reference (b_ytitle, placed with the same rule, is only
# -0.126 pt off).  Nudge the pen target of that single item; nothing else reads it.
PEN_FIX = {"a_ytitle": (2.0793, 0.0)}   # closed loop on the rendered ink (dx 2.022 -> 9.963, 2.111 -> 10.213)
def R(name, txt, fs, color, bx, ps, cy, Lm):
    fdx, fdy = PEN_FIX.get(name, (0.0, 0.0))
    return dict(name=name, txt=txt, fs=fs, color=color, rot=True,
                bx=round(bx+fdx,4), ps=round(ps+fdy,4), cy=round(cy,4), Lm=round(Lm,3))

items = []
def addH(*a, **k): items.append(H(*a, **k))
def addR(*a, **k): items.append(R(*a, **k))

# ===== panel A =====
# analytic positions of OUR OWN axis ticks (design pt); the labels must sit on their ticks
def txa(v, xf=921.5, xt=1394.5):
    return FR["a"]["x0"] + (v - xf)/(xt - xf)*FR["a"]["w"]
def txb(v, xf=-8.16873, xt=-7.42695):
    return FR["b"]["x0"] + (v - xf)/(xt - xf)*FR["b"]["w"]
addH("A_letter", r"\b((a))", 10.0, "#000000", 13.490, 9.753, align="left", tx=14.0)
for i, (v, t) in enumerate([(1000., "1000"), (1100., "1100"), (1200., "1200"), (1300., "1300")]):
    addH("ax%d" % (i+1), t, 8.0, "#000000", txa(v) - 8.8, 136.3752, align="center", tx=txa(v))
for i, (rt, (py, t)) in enumerate(zip([27.75, 26.50, 27.50, 27.75, 27.75],
        [(124.9643, "0.0"), (99.4689, "0.1"), (73.9736, "0.2"), (48.4783, "0.3"), (22.9819, "0.4")])):
    addH("ay%d" % (i+1), t, 8.0, "#000000", rt - 11.0, py, align="right", tx=rt)
t = r"\i(T) (K)"
addH("a_xtitle", t, 9.0, "#222222", 108.500 - width(t, 9.0)/2.0, 149.0102, align="center", tx=108.500)
# CALLOUT REMOVAL (2026-11-11): the (a) upper-right note
#   "dashed: log10 2 ~ 0.301 (Factor2)"   (a_note1 / a_note2)
# is deleted from the figure; its meaning moves to the Word caption.  The
# Factor-2 dashed guide itself (fig4_panelA_guide_dashpath.csv + K["ref"]) and
# the legend block below it are UNCHANGED.
LEG_DY = 0.0                     # 0 -> legend block sits above the 0.301 guide, as in the reference
addH("a_leg1", r"HF-only", 6.5, "#000000", 134.957, 26.988 + LEG_DY)
addH("a_leg2", r"residual MFNN", 6.5, "#000000", 134.957, 36.654 + LEG_DY)
ta = r"|\x(0394)log\-(10)\i(D)| = |log\-(10)\i(D) \x(2212) log\-(10)\i(D)\-(true)|"
addR("a_ytitle", ta, 8.0, "#222222", 10.1083, 126.8227, FR["a"]["cy"], width(ta, 8.0))

# ===== panel B =====
addH("B_letter", r"\b((b))", 10.0, "#000000", 209.5379, 9.7529, align="left", tx=210.0)
for i, (v, t) in enumerate([(-8.0, r"\x(2212)8.0"), (-7.8, r"\x(2212)7.8"), (-7.6, r"\x(2212)7.6")]):
    addH("bx%d" % (i+1), t, 8.0, "#000000", txb(v) - 9.3, 136.375, align="center", tx=txb(v))
for i, (rt, (px, py, t)) in enumerate(zip([223.50, 223.75, 223.50],
        [(207.916, 108.910, r"\x(2212)0.2"), (212.742, 77.489, "0.0"), (212.742, 46.069, "0.2")])):
    addH("by%d" % (i+1), t, 8.0, "#000000", rt - 10.8, py, align="right", tx=rt)
tb = r"\i(y)\-(L)\+(proxy) \x(3D) log\-(10)\i(D)\+(LF-only)"
addH("b_xtitle", tb, 8.0, "#222222", 303.375 - width(tb, 8.0)/2.0, 150.124, align="center", tx=303.375)
# CALLOUT REMOVAL (2026-11-11): the three-line (b) upper-left note
#   "LF-only prediction as / Sutherland D_LF proxy / (no explicit y_L column)"
#   (b_note1 / b_note2 / b_note3) is deleted from the figure; it sat on top of
# the (b) scatter.  Its meaning moves to the Word caption.  The (b) MFNN points,
# the zero line and the gray band are UNCHANGED.
tbb = r"log\-(10)\i(D)\-(MFNN) \x(2212) log\-(10)\i(D)\-(true)"
addR("b_ytitle", tbb, 8.0, "#222222", 201.3304, 112.3602, FR["b"]["cy"], width(tbb, 8.0))

# ===== D-hat carets (polylines on lay0): occ is 0-based among the wanted glyph =====
def rendered_pen(it):
    """where the pen/base of `it` actually lands on the page, given the probe offsets"""
    o = OFFS.get(it["name"])
    if not o:
        return (it.get("Lx", it.get("bx")), it.get("By", it.get("ps")))
    if it.get("rot"):
        ax = it["bx"] - o["ox"]; ay = it["ps"] - o["oy"]
    else:
        al = it.get("align", "pen")
        if al == "left":      ax = it["tx"] - o["jx0"]
        elif al == "right":   ax = it["tx"] - o["jx1"]
        elif al == "center":  ax = it["tx"] - 0.5*(o["jx0"] + o["jx1"])
        else:                 ax = it["Lx"] - o["ox"]
        ay = it["By"] - o["oy"]
    return (ax + o["ox"], ay + o["oy"])

def hat_for(it, ch, occ):
    h = dict(HAT)
    px, py = rendered_pen(it)
    if it.get("rot"):
        xb, wd = glyph_adv(it["txt"], it["fs"], ch, occ)
        yc = py - xb - wd/2.0                            # glyph centre along the advance
        ax_, ay_ = px - h["rise"], yc - h["lead"]        # apex points to -x for rotated text
        pts = [(ax_ + h["leg"], ay_ + h["half"]), (ax_, ay_), (ax_ + h["leg"], ay_ - h["half"])]
    else:
        xb, wd = glyph_adv(it["txt"], it["fs"], ch, occ)
        xc = px + xb + wd/2.0 + h["lead"]
        ay_ = py - h["rise"]
        pts = [(xc - h["half"], ay_ + h["leg"]), (xc, ay_), (xc + h["half"], ay_ + h["leg"])]
    return dict(name=ch + "_hat_" + it["name"], item=it["name"], glyph=ch, occ=occ,
                pts=[[round(p[0],4), round(p[1],4)] for p in pts])
BYNAME = {i["name"]: i for i in items}
hats = [hat_for(BYNAME["a_ytitle"], "D", 1),
        hat_for(BYNAME["b_ytitle"], "D", 0),
        hat_for(BYNAME["b_xtitle"], "D", 0)]

horiz = [i for i in items if not i.get("rot")]
rot   = [i for i in items if i.get("rot")]

K = dict(
  pt=PT, off_cm=OFF, page_cm=[14.0, 6.0], fs_map=FSMAP,
  decoy=dict(dx=DX, dy=DY, pdfx=PDFX, pdfy=PDFY, leg_dy=LEG_DY),
  spine="#333333", dark="#333333", band="#F3F3F3", ref="#7F7F7F",
  guide_dash=dict(type=5, width=0.8, on=3.058, off=1.322),
  tick=dict(len_nom=3.6, thick=0.75),
  layers=dict(
    a=dict(left=round(OFF+FR["a"]["x0"]/PT,5), top=round(OFF+FR["a"]["y0"]/PT,5),
           width=round(FR["a"]["w"]/PT,5), height=round(FR["a"]["h"]/PT,5),
           xf=921.5, xt=1394.5, xi=100.0, xfirst=1000.0,
           yf=-0.018772, yt=0.410093, yi=0.1, yfirst=0.0),
    b=dict(left=round(OFF+FR["b"]["x0"]/PT,5), top=round(OFF+FR["b"]["y0"]/PT,5),
           width=round(FR["b"]["w"]/PT,5), height=round(FR["b"]["h"]/PT,5),
           xf=-8.16873, xt=-7.42695, xi=0.2, xfirst=-8.0,
           yf=-0.332661, yt=0.363732, yi=0.2, yfirst=-0.2)),
  markers=dict(MFNN=dict(kind=2, fill="#009E73", edge="#006B4E", z=6.127, lw=0.5, transparency=0),
               HF_only=dict(kind=3, fill="#0072B2", edge="#004D7A", z=4.08, lw=0.4, transparency=45)),
  legend_handles=[dict(kind=3, z=4.08, cx=122.865, cy=round(25.226+LEG_DY,3), fill="#0072B2", edge="#004D7A", transparency=45),
                  dict(kind=2, z=6.127, cx=122.872, cy=round(34.893+LEG_DY,3), fill="#009E73", edge="#006B4E", transparency=0)],
  horiz=horiz, rot=rot, hats=hats,
  probe=dict(dx=DX, dy=DY, x_step=170.0, y_step=26.0, x0=25.0, y0=150.0, per_col=9,
             hwin=100.0, rot_x0=520.0, rot_dx=50.0, rot_y=150.0),
)
# ---- preserve sections this builder does not own -------------------------------
# `ticks_extra` (hand-drawn top/right tick anchors, added by the 2026-11-04 tick
# round) is consumed by plot_fig4_origin.py but never emitted here.  Regenerating
# the JSON must not destroy it, so any key present in the existing file and
# absent from K is carried over unchanged.
OUTJSON = os.path.join(OD, "fig4_origin_constants.json")
carried = []
if os.path.exists(OUTJSON):
    prev = json.load(open(OUTJSON, encoding="utf-8"))
    for k, v in prev.items():
        if k not in K:
            K[k] = v; carried.append(k)
json.dump(K, open(OUTJSON, "w", encoding="utf-8"), indent=1)
print("carried over non-owned keys:", carried)
print("horiz=%d rot=%d hats=%d dx=%.4f dy=%.4f" % (len(horiz), len(rot), len(hats), DX, DY))
for it in horiz:
    if any(k in it["name"] for k in ("xtitle","note","leg")):
        print("  %-9s Lx=%8.3f By=%8.3f w=%6.2f right=%8.3f" % (it["name"], it["Lx"], it["By"],
              width(it["txt"], it["fs"]), it["Lx"]+width(it["txt"], it["fs"])))
for it in rot:
    print("  ROT %-9s bx=%7.3f ps=%7.3f cy=%7.3f Lm=%7.2f" % (it["name"], it["bx"], it["ps"], it["cy"], it["Lm"]))
for h in hats:
    print("  HAT %-16s %s" % (h["name"], ascii(h["pts"])))
