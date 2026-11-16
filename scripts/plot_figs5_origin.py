r"""Fig. S5  (SI negative ablation: separate tracer/inter pools vs joint + diff_type one-hot)
-- native Origin 2026 redraw (originpro / FigureSpec-style house recipe).

House twin of scripts/plot_figs2_origin.py (two equal-width data layers + text canvas,
hand-drawn bars + error caps) and scripts/plot_figs1_origin.py (horizontal 9 pt axis
name, hand-built legend swatches):
  * two data layers (a, b) in cm units + one canvas layer (lay0) for ALL text
  * every string is placed from an INK-BOX target using per-item anchor->ink offsets
    measured on this figure's own probe page (FS5PROBE=1, then _z_figs5_measure.py)
  * Origin draws NO ticks and NO tick labels (its default theme emits SIMSUN): the
    inward major ticks of all four sides are hand-drawn at the measured rendered length
    3.36 pt with the house 0.75 pt pen -> closed 4-side box #333333
  * the (a) four bars are hand-drawn closed 5-point rectangles (Fill-Area + 0.6 pt edge)
    with the frozen fills grey/orange/sky-blue; NO error bars in (a)
  * the (b) three bars likewise; the error stems AND caps are hand-drawn #333333
    (0.8 pt, 5.0 pt caps) -- NOT matplotlib's default-blue #1F77B4 caps; the
    Joint+one-hot lower cap is below 0 and is clipped at the axis (stem ends at 0)
  * the (a) legend is hand-built upper-right with THREE rows whose swatch colours match
    the bar fills: grey "Separate pools (12-D)", orange "Joint tracer", sky-blue
    "Joint inter" (fixes the stem's orange-swatch/blue-bar mismatch)
  * NO in-figure suptitle, NO Note below (b): the note wording lives in the Word caption
  * Arial only: \\x(00B1), \\-(80) origin subscripts, \\b(...), no mathtext -> no STIX/SimSun
  * frozen display values only: 173.0/156.5/11.0/6.5 % and 99.7+/-54.5 / 18.0+/-16.9 /
    39.4+/-39.7

    FS5PROBE=1 python scripts/plot_figs5_origin.py   # text-only calibration page
    python scripts/plot_figs5_origin.py              # production render + .opju
"""
import os, json, re, traceback, sys
import originpro as op
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figs5_layout as F

BASE = F.B
OD = F.OD
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
PROBE = os.environ.get("FS5PROBE", "0") == "1"
TAG = "_probe" if PROBE else ""
LOG = os.path.join(OD, "_qa_figs5_render%s.txt" % TAG)
OFF_JSON = os.path.join(OD, "figs5_text_offsets.json")
NAME = "FigS5_difftype_split_ablation"
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
    K = json.load(open(os.path.join(OD, "figs5_origin_constants.json"), encoding="utf-8-sig"))
    fsmap = K["fs_map"]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    DEC = K["decoy"]; DX = DEC["dx"]; DY = DEC["dy"]
    FRM = K["frame"]; LA = K["layers"]["a"]; LB = K["layers"]["b"]; LC = K["layers"]["canvas"]
    TL = K["tick"]["len_rendered"]
    BA = K["bars_a"]; BB = K["bars_b"]; EB = K["errbar"]; LG = K["legend"]
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
            raise RuntimeError("missing " + OFF_JSON + " -- run FS5PROBE=1 then "
                               "scripts/_z_figs5_measure.py first")
        OFFS = json.load(open(OFF_JSON, encoding="utf-8-sig"))
        L("anchor offsets loaded for %d items" % len(OFFS))
    pr = K["probe"]
    def hslot(i):
        c = i // pr["per_col"]; r = i % pr["per_col"]
        return (pr["x0"] + c * pr["x_step"], pr["y0"] + r * pr["y_step"])
    def anchor(it, o):
        ax = {"left": it["tx"] - o["jx0"], "right": it["tx"] - o["jx1"],
              "center": it["tx"] - 0.5 * (o["jx0"] + o["jx1"])}[it["ax"]]
        ay = {"top": it["ty"] - o["jy0"], "bottom": it["ty"] - o["jy1"],
              "center": it["ty"] - 0.5 * (o["jy0"] + o["jy1"])}[it["ay"]]
        return (ax, ay)
    def coord(it, i):
        return hslot(i) if PROBE else anchor(it, OFFS[it["name"]])
    def a_pt2data(x, y): return (AXF + (x - FLA) / SXA, AYT - (y - FT) / SYA)
    def b_pt2data(x, y): return (BUF + (x - FLB) / SXB, BVT - (y - FT) / SYB)

    op.set_show(False)
    op.new()
    op.lt_exec("@LCP=2;")   # flat (butt) line end caps for plots, session-only (Fig. S1 recipe)
    gp = op.new_graph("FigS5")
    ws = op.new_sheet("w", "DS5")
    ci = [0]
    def add(vals, lname, axis=""):
        ws.from_list(ci[0], vals, lname=lname, axis=axis); ci[0] += 1; return lname
    def axis_style(lay, a):
        lay.lt_exec("layer.%s.ticks=0;layer.%s.minorTicks=0;layer.%s.showlabel=0;"
                    "layer.%s.thickness=%g;layer.%s.color=color(%d,%d,%d);" %
                    (a, a, a, a, K["tick"]["thick"], a,
                     int(K["spine"][1:3], 16), int(K["spine"][3:5], 16), int(K["spine"][5:7], 16)))
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
    def place(cx, cy, name, txt, fs, color):
        u = cx + DX; v = DY - cy
        lay0.lt_exec('label -a %g %g -n %s "%s";' % (u, v, name, txt))
        lay0.lt_exec("%s.fsize=%g;%s.font=font(arial);%s.color=color(%d,%d,%d);" %
                     (name, fsn(fs), name, name, int(color[1:3], 16), int(color[3:5], 16),
                      int(color[5:7], 16)))
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
        # ---------- panel (a): four bars, no error bars ----------
        half = BA["half_pt"]
        for i, b in enumerate(BA["items"]):
            cx = b["x_pt"]; ytop = b["top_pt"]; ybot = FB
            rp = [(cx - half, ybot), (cx + half, ybot), (cx + half, ytop),
                  (cx - half, ytop), (cx - half, ybot)]
            draw_poly(lay1, rp, a_pt2data, "af%d" % i, b["fill"], BAR_P := BA["pen"], fill=1)
            draw_poly(lay1, rp, a_pt2data, "ae%d" % i, b["edge"], BA["pen"])
            L("bar-a %s x=%.3f half=%.3f top=%.3f value=%s fill=%s edge=%s" %
              (b["name"], cx, half, ytop, b["value"], b["fill"], b["edge"]))
        # ---------- panel (a): legend swatches (fill band + edge), three rows ----------
        # swatch BODY = one thick horizontal segment (pen width = swatch height) with
        # session-level flat caps (@LCP=2): Origin's area fill would paint a band from a
        # floating swatch down to the X axis; the butt-capped thick line is the exact
        # 14.0 x 4.9 pt rectangle, then the same closed polygon is stroked 0.6 pt in the
        # edge colour (no fill) -- the Fig. S1 v4 recipe.
        sw = LG["sw"]
        for k, r in enumerate(LG["rows"]):
            x0, x1 = r["sw"]; cy = r["cy"]
            draw_poly(lay1, [(x0, cy), (x1, cy)], a_pt2data, "lsw%d" % k, r["fill"], sw["h"])
            rp = [(x0, cy - sw["h"] / 2.0), (x1, cy - sw["h"] / 2.0),
                  (x1, cy + sw["h"] / 2.0), (x0, cy + sw["h"] / 2.0),
                  (x0, cy - sw["h"] / 2.0)]
            draw_poly(lay1, rp, a_pt2data, "lse%d" % k, r["edge"], BA["pen"])
            L("legend swatch %d rect [%.3f %.3f] cy=%.3f fill=%s edge=%s" %
              (k, x0, x1, cy, r["fill"], r["edge"]))
        # ---------- panel (b): three bars + #333333 error stems/caps ----------
        halfb = BB["half_pt"]
        for i, b in enumerate(BB["items"]):
            cx = b["x_pt"]; ytop = b["top_pt"]; ybot = FB
            rp = [(cx - halfb, ybot), (cx + halfb, ybot), (cx + halfb, ytop),
                  (cx - halfb, ytop), (cx - halfb, ybot)]
            draw_poly(lay2, rp, b_pt2data, "bf%d" % i, b["fill"], BB["pen"], fill=1)
            draw_poly(lay2, rp, b_pt2data, "be%d" % i, b["edge"], BB["pen"])
            segs = [[(cx, b["cap_hi_pt"]), (cx, b["stem_lo_pt"])],
                    [(cx - EB["cap_half"], b["cap_hi_pt"]), (cx + EB["cap_half"], b["cap_hi_pt"])]]
            if b["cap_lo_pt"] is not None:
                segs.append([(cx - EB["cap_half"], b["cap_lo_pt"]),
                             (cx + EB["cap_half"], b["cap_lo_pt"])])
            flat = []
            for s in segs:
                flat += [s[0], s[1], (None, None)]
            draw_poly(lay2, flat[:-1], b_pt2data, "eb%d" % i, EB["color"], EB["pen"])
            L("bar-b %s x=%.3f top=%.3f cap_hi=%.3f stem_lo=%.3f cap_lo=%s fill=%s edge=%s" %
              (b["name"], cx, ytop, b["cap_hi_pt"], b["stem_lo_pt"], b["cap_lo_pt"],
               b["fill"], b["edge"]))

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
        cxp, cyp = coord(it, i)
        col = "#000000" if PROBE else it["color"]
        place(cxp, cyp, "T_" + it["name"], fix_txt(it["name"], it["txt"]), it["fs"], col)
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
        L("probe pdf=" + str(gp.save_fig(os.path.join(OUT, "_probe_figs5_anchors.pdf"), type="pdf")))
    else:
        opju = os.path.join(OUT, NAME + ".opju")
        op.save(opju); L("opju=" + opju)
        L("svg raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs5.svg"), type="svg")))
        L("png raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs5.png"), type="png",
                                        width=K["export"]["png_width"])))
        L("pdf raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs5.pdf"), type="pdf")))
    op.exit(); L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())
    try:
        op.exit()
    except Exception:
        pass
print("\n".join(log))


