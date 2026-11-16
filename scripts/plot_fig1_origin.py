# -*- coding: ascii -*-
"""Fig.1 native-Origin renderer (mfnn_eta_to_D).  Reads the frozen design
outputs/origin_data/fig1_origin_constants.json (design pt, X right, Y DOWN)
and paints it on ONE frame-less Origin canvas where 1 layer unit = 1 pt:

    u = X + ox(40) ,  v = oy(420) - Y          (layer.unit = 3)

Modes (env F1MODE):
  probe_text  : every text drawn alone in a clean slot  -> anchor/ink pass 1
  probe_calib : pen width / dash / line-break / disk / arrowhead calibration
  final       : the deliverable (default)
Text anchors use the proven two-pass method: pass 1 measures rendered ink vs
anchor, pass 2 solves the anchor so the RENDERED ink lands on the audited
model ink box.  Nothing here touches Fig.3 / Fig.4 / Word / frozen numbers.
"""
import os, io, json, math, re, traceback
import originpro as op

B    = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD   = os.path.join(B, "outputs", "origin_data")
OUTD = os.path.join(B, "outputs", "figures_origin")
os.makedirs(OUTD, exist_ok=True)
MODE = os.environ.get("F1MODE", "final")
NAME = "Fig1_mfnn_residual_schema"
PT   = 72.0 / 2.54

D    = json.load(io.open(os.path.join(OD, "fig1_origin_constants.json"), encoding="utf-8"))
CAL  = D["cal"]; DASH = D["dash"]
OX, OY = float(CAL["ox"]), float(CAL["oy"])
CW, CH = CAL["canvas_cm"]
WPU, HPU = CW * PT, CH * PT                      # 566.929 x 453.543 layer units
OFF_JSON = os.path.join(OD, "fig1_text_offsets.json")
PEN_JSON = os.path.join(OD, "fig1_pen_calib.json")
SLOTS_JSON = os.path.join(OD, "fig1_probe_slots.json")

LOG = os.path.join(OD, "_qa_fig1_render_%s.txt" % MODE)
logf = io.open(LOG, "w", encoding="ascii", errors="replace")
def L(*a):
    logf.write(" ".join(str(x) for x in a) + "\n"); logf.flush()

def u_of(X): return X + OX
def v_of(Y): return OY - Y
def rgb(h):  return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)

_rx_hex = re.compile(r"\\x\(([0-9A-Fa-f]{1,6})\)")
def fix_txt(t):
    """same guards as plot_fig4_origin.py: 4 hex digits, pad pure numbers"""
    t = _rx_hex.sub(lambda m: "\\x(%04X)" % int(m.group(1), 16), t)
    if re.match(r"^[0-9]+$", t):
        t += "\\x(00A0)"
    return t

def strip_markup(t):
    t = _rx_hex.sub("M", t)
    prev = None
    while prev != t:
        prev = t
        t = re.sub(r"\\([bi+-])\(([^()]*)\)", r"\2", t)
    return t.replace("\\", "")
def est_w(it):
    return len(strip_markup(it["txt"])) * 0.72 * float(it["fs"]) + 4.0

# ---------------------------------------------------------------- geometry I/O
BOXES = json.load(io.open(os.path.join(OD, "fig1_text_boxes.json"), encoding="utf-8"))
def model_box(it):
    "design-space ink rectangle (Y down) the RENDERED glyphs must land on"
    return BOXES[it["name"]]

# ---------------------------------------------------------------- Origin session
op.set_show(False)
gp = op.new_graph(NAME if MODE == "final" else "F1P_" + MODE)
lay = gp[0]; lay.activate()
lay.lt_exec("layer.unit=3;layer.showframe=0;")
lay.lt_exec("layer.left=0.05;layer.top=0.05;layer.width=%g;layer.height=%g;" % (CW, CH))
for a in ("x", "x2", "y", "y2"):
    lay.lt_exec("layer.%s.ticks=0;layer.%s.minorTicks=0;layer.%s.showlabel=0;layer.%s.thickness=0;" % (a, a, a, a))
lay.lt_exec("layer.sauto=0;")
lb = lay.label("legend")
if lb is not None: lb.remove()
lay.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" % (WPU, HPU))
for nm in ("xb", "xt", "yl", "yr"):
    try:
        lb = lay.label(nm)
        if lb is not None: lb.remove()
    except Exception: pass
L("mode=%s  canvas %gx%g cm  unit=3  x 0..%g  y 0..%g  (1 unit = 1 design pt)" %
  (MODE, CW, CH, WPU, HPU))

ws = op.new_sheet("w", "F1")
_ci = [0]
def add(vals, lname, axis=""):
    ws.from_list(_ci[0], vals, lname=lname, axis=axis); _ci[0] += 1
    return lname

PENS = json.load(io.open(PEN_JSON, encoding="utf-8")) if os.path.exists(PEN_JSON) else None
if PENS is not None:
    L("pen calib: mode=%s min_w=%s  wp_from_w=%s" %
      (PENS.get("mode"), PENS.get("min_w"), PENS.get("wp_from_w")))
def pen_w(w):
    "design pt -> the -wp number that actually produces it (from probe_calib)"
    if PENS is None or MODE != "final":
        return float(w)
    m = PENS["wp_from_w"]
    k = "%.2f" % float(w)
    if k in m:
        return float(m[k])
    ks = sorted(m, key=lambda z: abs(float(z) - float(w)))
    return float(m[ks[0]])

def pen_lw(w):
    "design pt -> the linewidth number for lay.add_line (different quantiser than -wp)"
    if PENS is None or MODE != "final":
        return float(w)
    m = PENS.get("lw_from_w") or {}
    k = "%.2f" % float(w)
    if k in m:
        return float(m[k])
    if not m:
        return pen_w(w)
    ks = sorted(m, key=lambda z: abs(float(z) - float(w)))
    return float(m[ks[0]])

def place(name, txt, fs, color, u, v, rot=False):
    lay.lt_exec('label -a %g %g -n %s "%s";' % (round(u, 4), round(v, 4), name, txt))
    r, g, b = rgb(color)
    lay.lt_exec("%s.font=font(arial);%s.fsize=%g;%s.color=color(%d,%d,%d);" % (name, name, float(fs), name, r, g, b))
    if rot:
        lay.lt_exec("%s.rotate=90;" % name)

def export(tag, wpng=6433):
    for t, w in (("pdf", 0), ("svg", 0), ("png", wpng)):
        try:
            lay.activate()
            L("export %s -> %s" % (t, gp.save_fig(os.path.join(PDIR, tag + "." + t), type=t, width=w)))
        except Exception as e:
            L("export %s ERR %r" % (t, e))

# =============================================================== PROBE: texts
if MODE == "probe_text":
    PDIR = os.path.join(OD, "_z_fig1probe")
    items = [t for t in D["texts"] if not t.get("rot")]
    rot   = [t for t in D["texts"] if t.get("rot")]
    GAP, PITCH, U0, U1, V0 = 15.0, 25.0, 26.0, 546.0, 432.0
    slots = {}
    u, v, row = U0, V0, 0
    for i, it in enumerate(items):
        w = model_box(it)[2] - model_box(it)[0]
        if u + w > U1 and u > U0:
            row += 1; u = U0; v = V0 - row * PITCH
        slots[it["name"]] = dict(u=round(u, 3), v=round(v, 3), fs=float(it["fs"]),
                                 w=round(w, 3), txt=fix_txt(it["txt"]), rot=False, i=i)
        u += w + GAP
    for j, it in enumerate(rot):
        b = model_box(it); Lh = b[3] - b[1]
        uu = 40.0 + j * 60.0
        vv = min(v - 45.0, 120.0)
        slots[it["name"]] = dict(u=round(uu, 3), v=round(vv + 0.5 * Lh, 3), fs=float(it["fs"]),
                                 w=round(b[2] - b[0], 3), txt=fix_txt(it["txt"]), rot=True,
                                 length=round(Lh, 3), i=len(items) + j)
    L("probe_text packed %d rows, last v=%g, items=%d (+%d rotated)" % (row, v, len(items), len(rot)))
    if v < 40:
        L("!! WARNING slots ran off the bottom of the canvas")
    for nm, s in slots.items():
        place(nm, s["txt"], s["fs"], "#000000", s["u"], s["v"], rot=s["rot"])
    json.dump(slots, io.open(SLOTS_JSON, "w", encoding="utf-8"), indent=1, sort_keys=True)
    L("slots -> " + SLOTS_JSON)
    L("opju -> " + str(op.save(os.path.join(PDIR, "anchor.opju"))))
    export("anchor")

# ============================================================= PROBE: calib
elif MODE == "probe_calib":
    PDIR = os.path.join(OD, "_z_fig1probe")
    def hline(u0, u1, vv, col, w, dash=0, nm="W"):
        x = add([u0, u1], nm + "x", "X"); y = add([vv, vv], nm + "y", "Y")
        p = lay.add_plot(ws, y, x, type="l")
        p.color = op.ocolor(col); p.set_cmd("-wp %g" % w, "-d %d" % dash)
        return p
    WV = [0.2, 0.3, 0.35, 0.5, 0.6, 0.7, 0.8, 0.9, 1.1, 1.35, 1.4, 2.0]
    L("--- A. -wp on line plots : 100-unit segments at u 40..140 ---")
    for i, w in enumerate(WV):
        v = 425.0 - i * 15.0
        hline(40.0, 140.0, v, "#000000", w, 0, "wa%d" % i)
        L("WP %5.2f at v=%g" % (w, v))
    L("--- B. -wp on line plots, Okabe-Ito colour, u 180..280 ---")
    for i, w in enumerate(WV[:8]):
        v = 425.0 - i * 15.0
        hline(180.0, 280.0, v, "#0072B2", w, 0, "wb%d" % i)
    L("--- C. dash codes (set_cmd -d) at -wp 0.7, u 320..480 ---")
    for i, (nmt, code) in enumerate(sorted(DASH.items(), key=lambda kv: kv[1])):
        v = 425.0 - i * 15.0
        hline(320.0, 480.0, v, "#D55E00", 0.7, code, "d1_%s" % nmt)
        L("DASH %s code=%d at v=%g" % (nmt, code, v))
    L("--- D. dash codes at -wp 1.4, u 320..480 ---")
    for i, (nmt, code) in enumerate(sorted(DASH.items(), key=lambda kv: kv[1])):
        v = 330.0 - i * 12.0
        hline(320.0, 480.0, v, "#009E73", 1.4, code, "d2_%s" % nmt)
    L("--- E. do None gaps break a line plot?  u 40..140 v=250, gap 70..90 ---")
    xe = add([40.0, 65.0, None, 115.0, 140.0], "gapx", "X"); ye = add([250.0, 250.0, None, 250.0, 250.0], "gapy", "Y")
    pg = lay.add_plot(ws, ye, xe, type="l"); pg.color = op.ocolor("#222222"); pg.set_cmd("-wp 0.9", "-d 0")
    L("gap plot added: %s" % pg)
    L("--- F. scatter circles (symbol_kind=3 filled circle) size -> diameter, u 40..300 v=215 ---")
    for i, z in enumerate([6, 10, 11, 12, 13, 14, 16, 20]):
        uu = 45.0 + i * 32.0
        add([uu], "scx%d" % i, "X"); add([215.0], "scy%d" % i, "Y")
        p = lay.add_plot(ws, "scy%d" % i, "scx%d" % i, type="s")
        p.symbol_kind = 3; p.symbol_size = z; p.symbol_interior = 1
        p.set_cmd("-csf %d" % op.ocolor("#D5D0E8"), "-cse %d" % op.ocolor("#6B5B95"))
        L("SCAT size=%g at u=%g" % (z, uu))
    L("--- G. scatter circles with explicit edge width -csw, v=180 ---")
    for i, (z, ew) in enumerate([(10, 0.35), (10, 0.7), (13, 0.7), (13, 1.2)]):
        uu = 200.0 + i * 40.0
        add([uu], "sx%d" % i, "X"); add([180.0], "sy%d" % i, "Y")
        p = lay.add_plot(ws, "sy%d" % i, "sx%d" % i, type="s")
        p.symbol_kind = 3; p.symbol_size = z; p.symbol_interior = 1
        try:
            p.set_cmd("-csf %d" % op.ocolor("#FFF4E0"), "-cse %d" % op.ocolor("#E69F00"), "-csw %g" % ew)
        except Exception as e:
            L("csw ERR %r" % (e,))
        L("SCATW size=%g ew=%g at u=%g" % (z, ew, uu))
    L("--- H. polygon circles: arc pair + fill_area, r=3,5,6.5,7 v=140 ---")
    for i, r in enumerate([3.0, 5.0, 6.5, 7.0]):
        uu = 45.0 + i * 34.0; vv = 140.0
        th = [k * math.pi / 24.0 for k in range(25)]
        tx = [uu + r * math.cos(t) for t in th]; ty = [vv + r * math.sin(t) for t in th]
        bx = [uu + r * math.cos(t) for t in reversed(th)]; by = [vv + r * math.sin(t) for t in reversed(th)]
        c = add(tx, "ptx%d" % i, "X"); t1 = add(ty, "pty%d" % i, "Y"); t2 = add(by, "ptyb%d" % i, "Y")
        p1 = lay.add_plot(ws, t1, c, type="l"); p2 = lay.add_plot(ws, t2, c, type="l")
        p1.color = op.ocolor("#333333"); p2.color = op.ocolor("#333333")
        p1.set_cmd("-wp 0.7", "-d 0"); p2.set_cmd("-wp 0.7", "-d 0")
        p1.set_fill_area(op.ocolor("#FFFFFF"), 9, op.ocolor("#333333"))
        L("POLYC r=%g at (%g,%g)" % (r, uu, vv))
    L("--- I. closed single polyline + fill_area, r=5,7 v=110 ---")
    for i, r in enumerate([5.0, 7.0]):
        uu = 200.0 + i * 34.0; vv = 110.0
        th = [k * 2 * math.pi / 48.0 for k in range(49)]
        c = add([uu + r * math.cos(t) for t in th], "cx%d" % i, "X")
        yy = add([vv + r * math.sin(t) for t in th], "cy%d" % i, "Y")
        p = lay.add_plot(ws, yy, c, type="l"); p.color = op.ocolor("#004D7A")
        p.set_cmd("-wp 0.7", "-d 0")
        try:
            p.set_fill_area(op.ocolor("#7EB6D9"), 9, op.ocolor("#004D7A"))
        except Exception as e:
            L("closed fill ERR %r" % (e,))
    L("--- J. rect band fills (the wash / key chips), 2-pt edges ---")
    for i, (col, uu) in enumerate([("#FFF8EB", 40.0), ("#EBF5FB", 110.0), ("#F3FAF7", 180.0), ("#F7FBF9", 250.0), ("#FFFFFF", 320.0)]):
        c = add([uu, uu + 60.0], "rx%d" % i, "X")
        t1 = add([90.0, 90.0], "rt%d" % i, "Y"); t2 = add([60.0, 60.0], "rb%d" % i, "Y")
        p1 = lay.add_plot(ws, t1, c, type="l"); p2 = lay.add_plot(ws, t2, c, type="l")
        p1.color = op.ocolor(col); p2.color = op.ocolor(col)
        p1.set_cmd("-wp 0.5", "-d 0"); p2.set_cmd("-wp 0.5", "-d 0")
        p1.set_fill_area(op.ocolor(col), 9, op.ocolor(col))
        L("BAND %s u %g..%g v 60..90" % (col, uu, uu + 60.0))
    L("--- K. arrowheads (shape 4) : lw x arrowendlength ---")
    for i, (lw, al) in enumerate([(0.6, 4.6), (1.35, 4.6), (0.35, 4.6), (1.1, 5.4), (0.7, 6.0), (1.4, 3.6)]):
        vv = 30.0 - i * 4.0
        ln = lay.add_line(40.0, vv, 140.0, vv)
        ln.set_int("attach", 2); ln.set_int("arrowbegin", 0); ln.set_int("arrowend", 1)
        ln.set_int("arrowendshape", 4); ln.set_int("color", op.ocolor("#222222"))
        ln.set_float("linewidth", lw); ln.set_float("arrowendlength", al)
        L("ARR lw=%g len=%g v=%g" % (lw, al, vv))
    L("--- L. add_line linewidth (no head) u 180..280 ---")
    for i, lw in enumerate([0.2, 0.3, 0.35, 0.5, 0.7, 1.1, 1.4]):
        vv = 425.0 - i * 15.0
        ln = lay.add_line(180.0 + 0.0, vv, 280.0, vv)
        ln.set_int("attach", 2); ln.set_int("color", op.ocolor("#CC79A7"))
        ln.set_float("linewidth", lw)
        L("LINE lw=%g v=%g" % (lw, vv))
    export("calib", wpng=6433)
    L("opju -> " + str(op.save(os.path.join(PDIR, "calib.opju"))))

# =================================================================== FINAL
elif MODE == "final":
    PDIR = OUTD
    if not os.path.exists(OFF_JSON):
        raise RuntimeError("missing " + OFF_JSON + " -- run F1MODE=probe_text and read it first")
    OFFS = json.load(io.open(OFF_JSON, encoding="utf-8"))
    L("anchor offsets for %d/%d items" % (len(OFFS), len(D["texts"])))
    n = [t["name"] for t in D["texts"] if t["name"] not in OFFS]
    if n:
        L("!! MISSING OFFSETS: %d %s" % (len(n), n[:8]))

    def band_fill(fl, tag):
        top, bot, col = fl["top"], fl["bottom"], fl["color"]
        c = add([p[0] + OX for p in top], tag + "x", "X")
        t1 = add([OY - p[1] for p in top], tag + "t", "Y")
        t2 = add([OY - p[1] for p in bot], tag + "b", "Y")
        p1 = lay.add_plot(ws, t1, c, type="l"); p2 = lay.add_plot(ws, t2, c, type="l")
        p1.color = op.ocolor(col); p2.color = op.ocolor(col)
        p1.set_cmd("-wp 0.5", "-d 0"); p2.set_cmd("-wp 0.5", "-d 0")
        gp.activate()          # set_fill_area runs through global LabTalk -> graph page must be active
        p1.set_fill_area(op.ocolor(col), 9, op.ocolor(col))
        L("fill[%s] %s u %g..%g v %g..%g" % (fl["kind"], col, min(top[0][0], top[-1][0]) + OX,
                                             max(top[0][0], top[-1][0]) + OX,
                                             OY - max(top[0][1], bot[0][1]), OY - min(top[0][1], bot[0][1])))

    for i, fl in enumerate(D["fills"]):
        if fl["kind"] != "halo":
            band_fill(fl, "bg%d" % i)

    def runs_of(pts):
        out = []; cur = []
        for p in pts:
            if p is None:
                if len(cur) > 1: out.append(cur)
                cur = []
            else:
                cur.append(p)
        if len(cur) > 1: out.append(cur)
        return out
    G = []
    for ln in D["lines"]:
        k = (ln["color"], round(pen_w(ln["w"]), 4), int(DASH[ln["dash"]]))
        rr = runs_of(ln["pts"])
        if not rr: continue
        if G and G[-1][0] == k: G[-1][1].extend(rr)
        else: G.append((k, list(rr)))
    L("lines: %d json polylines -> %d style groups" % (len(D["lines"]), len(G)))
    nplot = 0
    for gi, ((col, w, dash), rrs) in enumerate(G):
        X = []; Y = []
        for j, r in enumerate(rrs):
            if j: X.append(None); Y.append(None)
            X += [p[0] + OX for p in r]; Y += [OY - p[1] for p in r]
        cx = add(X, "gx%d" % gi, "X"); cy = add(Y, "gy%d" % gi, "Y")
        p = lay.add_plot(ws, cy, cx, type="l")
        p.color = op.ocolor(col); p.set_cmd("-wp %g" % w, "-d %d" % dash)
        nplot += 1
    L("line plots added: %d  (columns so far %d)" % (nplot, _ci[0]))

    SIZED = {}
    for _k, _v in ((PENS or {}).get("sym_size_from_dia", {}) or {}).items():
        SIZED[round(float(_k), 3)] = float(_v)
    L("sym calib keys: %s" % (sorted(SIZED),))
    def sym_size(dia):
        d = round(float(dia), 3)
        if d in SIZED: return SIZED[d]
        if not SIZED: return d
        k = min(SIZED, key=lambda z: abs(z - d))
        if abs(k - d) > 0.05:
            L("!! sym dia %g not in calib (%g used)" % (d, k))
            return d
        return SIZED[k]
    for i, gg in enumerate(D["symbols"]):
        pts = gg["pts"]
        cx = add([p[0] + OX for p in pts], "sxg%d" % i, "X")
        cy = add([OY - p[1] for p in pts], "syg%d" % i, "Y")
        p = lay.add_plot(ws, cy, cx, type="s")
        p.symbol_kind = 3; p.symbol_size = sym_size(gg["dia"]); p.symbol_interior = 1
        p.set_cmd("-csf %d" % op.ocolor(gg["fill"]), "-cse %d" % op.ocolor(gg["edge"]))
        L("sym[%d] dia=%g->size=%g n=%d fill=%s edge=%s" %
          (i, gg["dia"], sym_size(gg["dia"]), len(pts), gg["fill"], gg["edge"]))

    for i, a in enumerate(D["arrows"]):
        ln = lay.add_line(a["x1"] + OX, OY - a["y1"], a["x2"] + OX, OY - a["y2"])
        ln.set_int("attach", 2); ln.set_int("arrowbegin", 0); ln.set_int("arrowend", 1)
        ln.set_int("arrowendshape", 4); ln.set_int("color", op.ocolor(a["color"]))
        ln.set_float("linewidth", pen_lw(a["w"])); ln.set_float("arrowendlength", float(a["head"]))
        L("arr[%d] (%g,%g)->(%g,%g) w=%g->lw %g head=%g %s" %
          (i, a["x1"], a["y1"], a["x2"], a["y2"], a["w"], pen_lw(a["w"]), a["head"], a["color"]))

    for i, fl in enumerate(D["fills"]):
        if fl["kind"] == "halo":
            band_fill(fl, "hc%d" % i)

    nplaced = 0
    for it in D["texts"]:
        o = OFFS.get(it["name"])
        if o is None:
            L("SKIP text (no offset) " + it["name"]); continue
        b = model_box(it)
        u = b[0] - o["dxL"] + OX
        v = OY - (b[1] - o["dyT"])
        place(it["name"], fix_txt(it["txt"]), it["fs"], it["color"], u, v, rot=bool(it.get("rot")))
        nplaced += 1
    L("texts placed: %d" % nplaced)
    lb = lay.label("legend")
    if lb is not None:
        lb.remove(); L("legend removed after plotting")
    L("opju -> " + str(op.save(os.path.join(OUTD, NAME + ".opju"))))
    export("_raw", wpng=6433)

else:
    raise SystemExit("bad F1MODE=" + MODE)

op.exit()
L("DONE")
logf.close()
print(open(LOG, encoding="ascii", errors="replace").read()[-2500:])
