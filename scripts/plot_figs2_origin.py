r"""Fig. S2  (Protocol W vs random between-group Protocol G: seed variance / caution)
-- native Origin 2026 redraw (originpro / FigureSpec-style house recipe).

House twin of scripts/plot_fig7_origin.py (two equal-width data layers + text canvas) and
scripts/plot_figs4_origin.py (hand-drawn vertical bars + error caps):
  * two data layers (a, b) in cm units + one canvas layer (lay0) for ALL text
  * every string is placed from an INK-BOX target using per-item anchor->ink offsets
    measured on this figure's own probe page (FS2PROBE=1, then _z_figs2_measure.py)
  * Origin draws NO ticks and NO tick labels (its default theme would emit SIMSUN):
    the inward major ticks of all four sides are hand-drawn at the measured rendered
    length 3.36 pt with the house 0.75 pt pen -> closed 4-side box #333333
  * the two (a) bars are hand-drawn closed 5-point rectangles (Fill-Area + 0.6 pt edge),
    the +/- seed std error bars are hand-drawn #333333 segments (0.8 pt, 5.0 pt caps)
  * the (b) trajectories are native line plots (1.25 pt solid) + native symbol plots
    (circle = Protocol W, square = Protocol G) at the probed marker sizes
  * the (b) legend sits in the verified empty top-left lane: swatch line + marker + text
  * NO in-figure suptitle and NO caution sentence inside panel (b): the caution wording
    lives in the Word caption only (same convention as Fig. S4 / main-text Fig. 7)
  * Arial only: \x(00B1) and \b(...), no mathtext -> no STIX, no SimSun
  * frozen display values only: 26.18+/-1.33 %, 27.36+/-12.88 %, ten per-seed MAPEs

    FS2PROBE=1 python scripts/plot_figs2_origin.py   # text-only calibration page
    python scripts/plot_figs2_origin.py              # production render + .opju
"""
import os, json, re, traceback
import originpro as op
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figs2_layout as F

BASE = F.B
OD = F.OD
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
PROBE = os.environ.get("FS2PROBE", "0") == "1"
TAG = "_probe" if PROBE else ""
LOG = os.path.join(OD, "_qa_figs2_render%s.txt" % TAG)
OFF_JSON = os.path.join(OD, "figs2_text_offsets.json")
NAME = "FigS2_protocol_G_variance"
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
PT = F.PT

try:
    K = json.load(open(os.path.join(OD, "figs2_origin_constants.json"), encoding="utf-8-sig"))
    fsmap = K["fs_map"]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    DEC = K["decoy"]; DX = DEC["dx"]; DY = DEC["dy"]
    FRM = K["frame"]; LA = K["layers"]["a"]; LB = K["layers"]["b"]; LC = K["layers"]["canvas"]
    TL = K["tick"]["len_rendered"]
    BARS = K["bars"]; EB = K["errbar"]; TR = K["traj"]; LG = K["legend"]
    FT, FB, FLA, FRA = FRM["FT"], FRM["FB"], FRM["FL_A"], FRM["FR_A"]
    FLB, FRB = FRM["FL_B"], FRM["FR_B"]
    SXA, SYA, SXB, SYB = FRM["sx_a"], FRM["sy_a"], FRM["sx_b"], FRM["sy_b"]
    AXF, AXT, AYF, AYT = LA["xf"], LA["xt"], LA["yf"], LA["yt"]
    BUF, BUT, BVF, BVT = LB["xf"], LB["xt"], LB["yf"], LB["yt"]
    OFFS = {}
    if PROBE:
        L("PROBE mode: text-only calibration page (no data, no frames, no ticks)")
    else:
        if not os.path.exists(OFF_JSON):
            raise RuntimeError("missing " + OFF_JSON + " -- run FS2PROBE=1 then "
                               "scripts/_z_figs2_measure.py first")
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
    def a_pt2data(x, y): return (AXF + (x - FLA) / SXA, AYT - (y - FT) / SYA)
    def b_pt2data(x, y): return (BUF + (x - FLB) / SXB, BVT - (y - FT) / SYB)

    op.set_show(False)
    gp = op.new_graph("FigS2")
    ws = op.new_sheet("w", "DS2")
    ci = [0]
    def add(vals, lname, axis=""):
        ws.from_list(ci[0], vals, lname=lname, axis=axis); ci[0] += 1; return lname
    def axis_style(lay, a):
        lay.lt_exec("layer.%s.ticks=0;layer.%s.minorTicks=0;layer.%s.showlabel=0;"
                    "layer.%s.thickness=%g;layer.%s.color=color(%d,%d,%d);" %
                    (a, a, a, a, K["tick"]["thick"], a,
                     int(K["spine"][1:3], 16), int(K["spine"][3:5], 16),
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
                    (LC["left"], LC["top"], LC["width"], LC["height"]))
        lay.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" %
                    (LC["xt"], LC["yt"]))
        for a in ("x", "x2", "y", "y2"):
            lay.lt_exec("layer.%s.ticks=0;layer.%s.minorTicks=0;layer.%s.showlabel=0;"
                        "layer.%s.thickness=0;" % (a, a, a, a))
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
    def draw_poly(lay, pts_pt, conv, pre, colorhex, width, fill=None):
        dd = [conv(x, y) if x is not None else (None, None) for x, y in pts_pt]
        xx = add([q[0] for q in dd], pre + "x", "X"); yy = add([q[1] for q in dd], pre + "y", "Y")
        p = lay.add_plot(ws, yy, xx, type="l")
        p.color = COL(colorhex); p.set_cmd("-wp %g" % width, "-d 0")
        if fill is not None:
            lay.lt_exec("{range rr=%s; set rr -pf 1; set rr -pfv 1; set rr -pfb %d;}" %
                        (p.lt_range(), COL(colorhex)))
        return p
    L("boot ok  A[%.3f..%.3f] B[%.3f..%.3f] FT=%.3f FB=%.3f  sx_a=%.5f sy_a=%.5f "
      "sx_b=%.5f sy_b=%.5f" % (FLA, FRA, FLB, FRB, FT, FB, SXA, SYA, SXB, SYB))

    lay1 = gp[0]; lay2 = gp.add_layer(0); lay0 = gp.add_layer(0)
    L("z-order: lay1=gp[0](panel a) lay2=(panel b) lay0=(text canvas)  dx=%g dy=%g" % (DX, DY))
    setup(lay1, LA); setup(lay2, LB)

    if PROBE:
        bare(lay1); bare(lay2)
    else:
        # ---------- panel (a): bars = closed 5-point rectangles (fill then edge) ----------
        half = BARS["half_pt"]
        for i, b in enumerate(BARS["items"]):
            cx = b["x_pt"]; ytop = b["top_pt"]; ybot = FB
            rp = [(cx - half, ybot), (cx + half, ybot), (cx + half, ytop),
                  (cx - half, ytop), (cx - half, ybot)]
            draw_poly(lay1, rp, a_pt2data, "bf%d" % i, b["fill"], BARS["pen"], fill=1)
            draw_poly(lay1, rp, a_pt2data, "bo%d" % i, b["edge"], BARS["pen"])
            L("bar %d x=%.3f half=%.3f top=%.3f (value %.2f) fill=%s edge=%s" %
              (i, cx, half, ytop, b["value"], b["fill"], b["edge"]))
        # ---------- panel (a): error bars = stem + two caps ----------
        for i, b in enumerate(BARS["items"]):
            cx = b["x_pt"]
            ytop = FB - (b["value"] + b["err"]) * SYA
            ybot = FB - (b["value"] - b["err"]) * SYA
            segs = [[(cx, ytop), (cx, ybot)],
                    [(cx - EB["cap_half"], ytop), (cx + EB["cap_half"], ytop)],
                    [(cx - EB["cap_half"], ybot), (cx + EB["cap_half"], ybot)]]
            flat = []
            for s in segs:
                flat += [s[0], s[1], (None, None)]
            draw_poly(lay1, flat[:-1], a_pt2data, "eb%d" % i, EB["color"], EB["pen"])
            L("errbar %d x=%.3f y %.3f..%.3f (caps %.2f..%.2f) cap_half=%.2f pen=%.2f" %
              (i, cx, ytop, ybot, ytop, ybot, EB["cap_half"], EB["pen"]))
        # ---------- panel (b): trajectories (line under, symbols over) ----------
        for pk, col in (("W", K["w_color"]), ("G", K["g_color"])):
            pts = TR["points"][pk]
            m = TR["marker"][pk]
            xs = add([p["xcat"] for p in pts], "tr%sx" % pk, "X")
            ys = add([p["mape"] for p in pts], "tr%sy" % pk, "Y")
            pl = lay2.add_plot(ws, "tr%sy" % pk, "tr%sx" % pk, type="l")
            pl.color = COL(col["fill"]); pl.set_cmd("-wp %g" % TR["pen"], "-d 0")
            ps = lay2.add_plot(ws, "tr%sy" % pk, "tr%sx" % pk, type="s")
            ps.symbol_kind = m["kind"]; ps.symbol_size = m["z"]; ps.symbol_interior = 1
            ps.set_cmd("-csf %d" % COL(m["fill"]), "-cse %d" % COL(m["edge"]),
                       "-kh 6", "-wp %g" % BARS["pen"])
            L("traj %s n=%d kind=%d z=%g ink=%.2f line=%.2f colour=%s edge=%s" %
              (pk, len(pts), m["kind"], m["z"], m["ink"], TR["pen"], col["fill"], col["edge"]))
        # ---------- panel (b): legend swatches (line + marker) in the empty top-left lane --
        for i, (pk, col) in enumerate((("W", K["w_color"]), ("G", K["g_color"]))):
            m = TR["marker"][pk]; sw = LG["sw"][i]; cy = sw["cy"]
            dd = [b_pt2data(x, cy) for x in (sw["x0"], sw["x1"])]
            add([q[0] for q in dd], "lgl%ssx" % pk, "X")
            add([q[1] for q in dd], "lgl%ssy" % pk, "Y")
            pl = lay2.add_plot(ws, "lgl%ssy" % pk, "lgl%ssx" % pk, type="l")
            pl.color = COL(col["fill"]); pl.set_cmd("-wp %g" % TR["pen"], "-d 0")
            cxm = sw["cx"]
            dm = b_pt2data(cxm, cy)
            add([dm[0]], "lgm%ssx" % pk, "X"); add([dm[1]], "lgm%ssy" % pk, "Y")
            ps = lay2.add_plot(ws, "lgm%ssy" % pk, "lgm%ssx" % pk, type="s")
            ps.symbol_kind = m["kind"]; ps.symbol_size = m["z"]; ps.symbol_interior = 1
            ps.set_cmd("-csf %d" % COL(m["fill"]), "-cse %d" % COL(m["edge"]),
                       "-kh 6", "-wp %g" % BARS["pen"])
            L("legend swatch %s x %.3f..%.3f cx=%.3f cy=%.3f kind=%d z=%g" %
              (pk, sw["x0"], sw["x1"], sw["cx"], cy, m["kind"], m["z"]))

    # ---------- hand-drawn inward ticks, all four sides of both frames ----------
    if not PROBE:
        for lay, spec, sx, sy, pre in ((lay1, LA, SXA, SYA, "a"), (lay2, LB, SXB, SYB, "b")):
            tx = []; ty = []
            for v in spec["xticks"]:
                for y0, y1 in ((spec["yt"], spec["yt"] - TL / sy), (spec["yf"], spec["yf"] + TL / sy)):
                    tx += [v, v, None]; ty += [y0, y1, None]
            for v in spec["yticks"]:
                for x0, x1 in ((spec["xt"], spec["xt"] - TL / sx), (spec["xf"], spec["xf"] + TL / sx)):
                    tx += [x0, x1, None]; ty += [v, v, None]
            xx = add(tx, "tkx_" + pre, "X"); yy = add(ty, "tky_" + pre, "Y")
            ptk = lay.add_plot(ws, yy, xx, type="l")
            ptk.color = COL(K["spine"]); ptk.set_cmd("-wp %g" % K["tick"]["thick"], "-d 0")
            L("ticks %s n=%d len=%.2f width=%.2f (x %d / y %d, 4 sides)" %
              (pre, len(tx) // 3, TL, K["tick"]["thick"], len(spec["xticks"]), len(spec["yticks"])))

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

    lay1.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" %
                 (AXF, AXT, AYF, AYT))
    lay2.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" %
                 (BUF, BUT, BVF, BVT))
    lay0.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" %
                 (LC["xt"], LC["yt"]))
    for lay in (lay0, lay1, lay2): drop_titles(lay)
    for lay, tg in ((lay1, "lay1"), (lay2, "lay2"), (lay0, "lay0")): kill_legend(lay, tg)
    L("ranges locked, titles dropped")
    if PROBE:
        L("probe pdf=" + str(gp.save_fig(os.path.join(OUT, "_probe_figs2_anchors.pdf"), type="pdf")))
    else:
        opju = os.path.join(OUT, NAME + ".opju")
        op.save(opju); L("opju=" + opju)
        L("svg raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs2.svg"), type="svg")))
        L("png raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs2.png"), type="png",
                                        width=K["export"]["png_width"])))
        L("pdf raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs2.pdf"), type="pdf")))
    op.exit(); L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())
    try:
        op.exit()
    except Exception:
        pass
print("\n".join(log))
