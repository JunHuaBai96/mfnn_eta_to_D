r"""Fig. S3  (Al80Cu20 tracer few-shot anchor-temperature / sparse-neighborhood diagnostic)
-- native Origin redraw, house twin of scripts/plot_figs4_origin.py:
  * one data layer (a) in cm units + one canvas layer (lay0) for ALL text
  * every string is placed from an INK-BOX target using per-item anchor->ink offsets
    measured on a dedicated probe page (FS3PROBE=1, then scripts/_z_figs3_measure.py)
  * Origin draws NO ticks and NO tick labels: the twenty inward major ticks (4 x-ticks on
    the top+bottom spines, 6 y-ticks on the left+right spines) are hand-drawn at the
    measured rendered length (3.36 pt) with the house thickness (0.75 pt), so all four
    sides of the closed box get identical inward ticks
  * the four vertical bars are hand-drawn: one closed 5-point rectangle per bar,
    Fill-Area in the tracer fill #D55E00 plus the same rectangle stroked 0.6 pt in the
    tracer edge #994300 (identical to the Fig.7 / Fig. S4 bar recipe, rotated vertical)
  * the +/- 5-seed scatter (population std, ddof=0, hardcoded) is hand-drawn as #333333
    line segments (0.8 pt) with 5.0 pt caps, exactly like the frozen figure's
    yerr capsize=2.5
  * NO in-figure suptitle and NO 'Factor2 = 0 (all k)' ink -- both defects of the
    matplotlib stem; the wording lives in the Word caption only
  * Arial only: plain Arial strings (the stem's mathtext italic k / T become upright
    Arial; NO mathtext -> no STIX); pure-digit labels get the house trailing NBSP
  * frozen display values only: bars 178.20/169.55/175.27/142.93, labels
    178.2/169.6/175.3/142.9

    FS3PROBE=1 python scripts/plot_figs3_origin.py   # text-only calibration page
    python scripts/plot_figs3_origin.py              # production render + .opju
"""
import os, json, csv, re, traceback
import originpro as op

BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(BASE, "outputs", "origin_data")
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
PROBE = os.environ.get("FS3PROBE", "0") == "1"
TAG = "_probe" if PROBE else ""
LOG = os.path.join(OD, "_qa_figs3_render%s.txt" % TAG)
OFF_JSON = os.path.join(OD, "figs3_text_offsets.json")
NAME = "FigS3_al80_anchor_k"
log = []
def L(s):
    log.append(str(s))
    with open(LOG, "w", encoding="ascii", errors="replace") as f:
        f.write("\n".join(log) + "\n")
def COL(h): return op.ocolor(h)
def fix_txt(name, t):
    t = re.sub(r"\\x\(([0-9A-Fa-f]{1,6})\)", lambda m: "\\x(%04X)" % int(m.group(1), 16), t)
    if re.match(r"^[0-9]+$", t):
        t += "\\x(00A0)"
    return t
PT = 72.0 / 2.54

try:
    K = json.load(open(os.path.join(OD, "figs3_origin_constants.json"), encoding="utf-8-sig"))
    fsmap = K["fs_map"]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    DEC = K["decoy"]; DX = DEC["dx"]; DY = DEC["dy"]
    FRM = K["frame"]; A = K["layers"]["a"]
    TL = K["tick"]["len_rendered"]
    CANV = K["canvas"]
    L0 = dict(left=CANV["left"], top=CANV["top"], width=CANV["width"], height=CANV["height"])
    FT, FB, FL, FR = FRM["FT"], FRM["FB"], FRM["FL"], FRM["FR"]
    SX, SY = FRM["sx"], FRM["sy"]
    BARS = K["bars"]; EB = K["errbar"]; LN = K["lanes"]
    OFFS = {}
    if PROBE:
        L("PROBE mode: text-only calibration page (no data, no frames, no ticks)")
    else:
        if not os.path.exists(OFF_JSON):
            raise RuntimeError("missing " + OFF_JSON + " -- run FS3PROBE=1 then _z_figs3_measure.py")
        OFFS = json.load(open(OFF_JSON, encoding="utf-8-sig"))
        L("anchor offsets loaded for %d items" % len(OFFS))
    pr = K["probe"]
    def hslot(i):
        c = i // pr["per_col"]; r = i % pr["per_col"]
        return (pr["x0"] + c * pr["x_step"], pr["y0"] + r * pr["y_step"])
    def rslot(j):
        return (pr["rot_x0"] + j * pr["rot_dx"], pr["rot_y"])
    def anchor(it, o):
        ax = {"left": it["tx"] - o["jx0"], "right": it["tx"] - o["jx1"],
              "center": it["tx"] - 0.5 * (o["jx0"] + o["jx1"])}[it["ax"]]
        ay = {"top": it["ty"] - o["jy0"], "bottom": it["ty"] - o["jy1"],
              "center": it["ty"] - 0.5 * (o["jy0"] + o["jy1"])}[it["ay"]]
        return (ax, ay)
    def coord(it, i, rot):
        if PROBE:
            return rslot(i) if rot else hslot(i)
        return anchor(it, OFFS[it["name"]])
    def pt2data(x, y): return (XLO + (x - FL) / SX, YHI - (y - FT) / SY)
    XLO, XHI, YLO, YHI = A["xf"], A["xt"], A["yf"], A["yt"]
    HIT = {it["name"]: it for it in K["horiz"]}

    op.set_show(False)
    gp = op.new_graph("FigS3")
    ws = op.new_sheet("w", "DS3")
    ci = [0]
    def add(vals, lname, axis=""):
        ws.from_list(ci[0], vals, lname=lname, axis=axis); ci[0] += 1; return lname
    def axis_style(lay, a):
        lay.lt_exec("layer.%s.ticks=0;layer.%s.minorTicks=0;layer.%s.showlabel=0;"
                    "layer.%s.thickness=0.75;layer.%s.color=color(%d,%d,%d);" %
                    (a, a, a, a, a, int(K["spine"][1:3], 16), int(K["spine"][3:5], 16),
                     int(K["spine"][5:7], 16)))
    def bare(lay):
        lay.activate()
        lay.lt_exec("layer.showframe=0;")
        for a in ("x", "x2", "y", "y2"):
            lay.lt_exec("layer.%s.ticks=0;layer.%s.minorTicks=0;layer.%s.thickness=0;" % (a, a, a))
        lgb = lay.label("legend")
        if lgb is not None: lgb.remove()
    def drop_titles(lay):
        for nm in ("xb", "xt", "yl", "yr"):
            try:
                lb = lay.label(nm)
                if lb is not None: lb.remove()
            except Exception: pass
    def kill_legend(lay, tag):
        try:
            lb = lay.label("legend")
            if lb is None:
                L("legend[%s]: none" % tag); return
            lb.remove(); L("legend[%s]: removed" % tag)
        except Exception as e:
            L("legend[%s]: ERR %r" % (tag, e))
    def place(cx, cy, name, txt, fs, color, rotate=False):
        u = cx + DX; v = DY - cy
        lay0.lt_exec('label -a %g %g -n %s "%s";' % (u, v, name, txt))
        lay0.lt_exec("%s.fsize=%g;%s.font=font(arial);%s.color=color(%d,%d,%d);" %
                     (name, fsn(fs), name, name, int(color[1:3], 16), int(color[3:5], 16),
                      int(color[5:7], 16)))
        if rotate: lay0.lt_exec("%s.rotate=90;" % name)
    def cfg_canvas(lay):
        lay.activate()
        lay.lt_exec("layer.unit=3;")
        lay.lt_exec("layer.left=%g;layer.top=%g;layer.width=%g;layer.height=%g;" %
                    (L0["left"], L0["top"], L0["width"], L0["height"]))
        lay.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" %
                    (L0["width"] * PT, L0["height"] * PT))
        for a in ("x", "x2", "y", "y2"):
            lay.lt_exec("layer.%s.ticks=0;layer.%s.minorTicks=0;layer.%s.showlabel=0;layer.%s.thickness=0;" % (a, a, a, a))
        lb0 = lay.label("legend")
        if lb0 is not None: lb0.remove()
        lay.lt_exec("layer.sauto=0;")
    def setup(lay, spec):
        lay.activate()
        lay.lt_exec("layer.unit=3;")
        lay.lt_exec("layer.left=%g;layer.top=%g;layer.width=%g;layer.height=%g;" %
                    (spec["left"], spec["top"], spec["width"], spec["height"]))
        lay.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" %
                    (spec["xf"], spec["xt"], spec["yf"], spec["yt"]))
        lay.lt_exec("layer.sauto=0;")
        for a in ("x", "x2", "y", "y2"): axis_style(lay, a)
    def draw_poly(lay, pts_pt, pre, colorhex, width, fill=None, connect=True):
        dd = [pt2data(x, y) if x is not None else (None, None) for x, y in pts_pt]
        xx = add([q[0] for q in dd], pre + "x", "X"); yy = add([q[1] for q in dd], pre + "y", "Y")
        p = lay.add_plot(ws, yy, xx, type="l")
        p.color = COL(colorhex); p.set_cmd("-wp %g" % width, "-d 0")
        if fill is not None:
            lay.lt_exec("{range rr=%s; set rr -pf 1; set rr -pfv 1; set rr -pfb %d;}" %
                        (p.lt_range(), COL(colorhex)))
        return p
    L("boot ok  FL=%.3f FR=%.3f FT=%.3f FB=%.3f sx=%.5f sy=%.5f" % (FL, FR, FT, FB, SX, SY))

    lay1 = gp[0]; lay0 = gp.add_layer(0)
    L("z-order: lay1=gp[0](data) lay0=gp.add(0)(text canvas)  dx=%g dy=%g" % (DX, DY))
    setup(lay1, A)

    if not PROBE:
        # ---------- bars: closed 5-point rectangles, fill then edge ----------
        half = BARS["half_pt"]
        for i, b in enumerate(BARS["items"]):
            cx = FL + (b["x"] - XLO) * SX
            ytop = FB - b["value"] * SY
            ybot = FB                              # bar base sits ON the bottom spine, as in the ref
            rp = [(cx - half, ybot), (cx + half, ybot), (cx + half, ytop),
                  (cx - half, ytop), (cx - half, ybot)]
            draw_poly(lay1, rp, "bf%d" % i, b["fill"], BARS["pen"], fill=1)
            draw_poly(lay1, rp, "bo%d" % i, b["edge"], BARS["pen"])
            L("bar %d x=%.3f half=%.3f top=%.3f (value %.2f) fill=%s edge=%s" %
              (i, cx, half, ytop, b["value"], b["fill"], b["edge"]))
        # ---------- error bars: stem + two caps ----------
        for i, b in enumerate(BARS["items"]):
            cx = FL + (b["x"] - XLO) * SX
            ytop = FB - (b["value"] + b["err"]) * SY
            ybot = FB - (b["value"] - b["err"]) * SY
            segs = [[(cx, ytop), (cx, ybot)],
                    [(cx - EB["cap_half"], ytop), (cx + EB["cap_half"], ytop)],
                    [(cx - EB["cap_half"], ybot), (cx + EB["cap_half"], ybot)]]
            flat = []
            for s in segs:
                flat += [s[0], s[1], (None, None)]
            draw_poly(lay1, flat[:-1], "eb%d" % i, EB["color"], EB["pen"])
            L("errbar %d x=%.3f y %.3f..%.3f cap_half=%.2f pen=%.2f" %
              (i, cx, ytop, ybot, EB["cap_half"], EB["pen"]))
    else:
        bare(lay1)

    # ---------- hand-drawn inward ticks, all four sides ----------
    if not PROBE:
        tx = []; ty = []
        for v in A["xticks"]:
            for y0, y1 in ((YHI, YHI - TL / SY), (YLO, YLO + TL / SY)):
                tx += [v, v, None]; ty += [y0, y1, None]
        for v in A["yticks"]:
            for x0, x1 in ((XHI, XHI - TL / SX), (XLO, XLO + TL / SX)):
                tx += [x0, x1, None]; ty += [v, v, None]
        xx = add(tx, "tkx_a", "X"); yy = add(ty, "tky_a", "Y")
        ptk = lay1.add_plot(ws, yy, xx, type="l")
        ptk.color = COL(K["spine"]); ptk.set_cmd("-wp %g" % K["tick"]["thick"], "-d 0")
        L("ticks n=%d len=%.2f width=%.2f (x %d / y %d, 4 sides)" %
          (len(tx) // 3, TL, K["tick"]["thick"], len(A["xticks"]), len(A["yticks"])))

    # ---------- lay0 : all text ----------
    cfg_canvas(lay0)
    for i, it in enumerate(K["horiz"]):
        cxp, cyp = coord(it, i, False)
        col = "#000000" if PROBE else it["color"]
        place(cxp, cyp, "T_" + it["name"], fix_txt(it["name"], it["txt"]), it["fs"], col)
    for j, it in enumerate(K["rot"]):
        cxp, cyp = coord(it, j, True)
        col = "#000000" if PROBE else it["color"]
        place(cxp, cyp, "T_" + it["name"], fix_txt(it["name"], it["txt"]), it["fs"], col, rotate=True)
    L("texts horiz=%d rot=%d (probe forces black)" % (len(K["horiz"]), len(K["rot"])))

    lay1.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" % (XLO, XHI, YLO, YHI))
    lay0.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" % (L0["width"] * PT, L0["height"] * PT))
    for lay in (lay0, lay1): drop_titles(lay)
    for lay, tg in ((lay1, "lay1"), (lay0, "lay0")): kill_legend(lay, tg)
    L("ranges locked, titles dropped")
    if PROBE:
        L("probe pdf=" + str(gp.save_fig(os.path.join(OUT, "_probe_figs3_anchors.pdf"), type="pdf")))
    else:
        opju = os.path.join(OUT, NAME + ".opju")
        op.save(opju); L("opju=" + opju)
        L("svg raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs3.svg"), type="svg")))
        L("png raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs3.png"), type="png", width=K["export"]["png_width"])))
        L("pdf raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs3.pdf"), type="pdf")))
    op.exit(); L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())
    try:
        op.exit()
    except Exception:
        pass
print("\n".join(log))
