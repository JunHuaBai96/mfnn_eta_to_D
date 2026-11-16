r"""Fig. 7  (LOGO distance-caution panels) -- native Origin redraw.

House twin of plot_fig5_origin.py / plot_fig6_origin.py / plot_fig2_origin.py:
  * two data layers (a, b) in cm units + one canvas layer (lay0) for ALL text
  * every string is placed from an INK-BOX target using per-item anchor->ink
    offsets measured on a dedicated probe page (F7PROBE=1, then _z_fig7_measure.py)
  * Origin draws NO ticks and NO tick labels; the inward ticks of all four sides
    are hand-drawn at the measured rendered length (3.36 pt) and the house
    thickness (0.75 pt) -> closed 4-side box, identical inward ticks everywhere
  * the 13 horizontal bars are hand-drawn: one closed 5-point rectangle per bar
    with Fill-Area (type 1, verified by scripts/_z_fig7_probe2.py) in the class
    fill colour, plus the same rectangle stroked 0.6 pt in the class edge colour.
    (Origin's native column plot cannot be oriented horizontally from set plot,
    and thick -wp segments get ROUNDED caps -- both verified by probe.)
  * the frozen-mean guide (39.4) is an EXPLICIT dash polyline (-d 0 + -wp);
    "set plot -1 <style>" is forbidden (hangs Origin 2026 automation)
  * Arial throughout (Origin \i \b \- \x markup only -- no mathtext / STIX)
  * Okabe-Ito class colours exactly as the frozen figure; NO in-figure suptitle

    F7PROBE=1 python scripts/plot_fig7_origin.py   # text-only calibration page
    python scripts/plot_fig7_origin.py             # production render + .opju
"""
import os, json, csv, re, math, bisect, traceback
import originpro as op

BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(BASE, "outputs", "origin_data")
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
PROBE = os.environ.get("F7PROBE", "0") == "1"
TAG = "_probe" if PROBE else ""
LOG = os.path.join(OD, "_qa_fig7_render%s.txt" % TAG)
OFF_JSON = os.path.join(OD, "fig7_text_offsets.json")
NAME = "Fig7_LOGO_distance_caution"
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
def rd(name): return list(csv.DictReader(open(os.path.join(OD, name), encoding="utf-8-sig")))
PT = 72.0 / 2.54

def dashify(pts, pattern):
    """polyline (design pt) -> dash segments, None-separated, same pt units."""
    cum = [0.0]; total = 0.0
    for i in range(len(pts) - 1):
        total += math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        cum.append(total)
    if total <= 0:
        return list(pts)
    def at(d):
        d = max(0.0, min(total, d))
        k = max(0, min(bisect.bisect_left(cum, d) - 1, len(pts) - 2))
        s0, s1 = cum[k], cum[k + 1]
        f = 0.0 if s1 <= s0 else (d - s0) / (s1 - s0)
        return (pts[k][0] + f * (pts[k + 1][0] - pts[k][0]),
                pts[k][1] + f * (pts[k + 1][1] - pts[k][1]))
    out = []; d = 0.0; pi = 0; on = True; first = True
    while d < total - 1e-9:
        seg = pattern[pi]
        if on:
            a = at(d); b = at(min(total, d + seg))
            if not first:
                out.append((None, None))
            out.append(a); out.append(b); first = False
        d += seg
        pi = (pi + 1) % len(pattern); on = not on
    return out

try:
    K = json.load(open(os.path.join(OD, "fig7_origin_constants.json"), encoding="utf-8-sig"))
    fsmap = K["fs_map"]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    DEC = K["decoy"]; DX = DEC["dx"]; DY = DEC["dy"]
    FR = K["frame"]; M = K["markers"]; MEAN = K["mean"]; LEG = K["legend"]
    A = K["layers"]["a"]; Bs = K["layers"]["b"]
    TL = K["tick"]["len_rendered"]
    CANV = K["canvas"]
    L0 = dict(left=CANV["left"], top=CANV["top"], width=CANV["width"], height=CANV["height"])
    FT, FB = FR["FT"], FR["FB"]
    FLA, FRA, FLB, FRB = FR["FL_A"], FR["FR_A"], FR["FL_B"], FR["FR_B"]
    SXA, SYA, SXB, SYB = FR["sx_a"], FR["sy_a"], FR["sx_b"], FR["sy_b"]
    OFFS = {}
    if PROBE:
        L("PROBE mode: text-only calibration page (no data, no frames, no ticks)")
    else:
        if not os.path.exists(OFF_JSON):
            raise RuntimeError("missing " + OFF_JSON + " -- run F7PROBE=1 then _z_fig7_measure.py")
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
    def a_pt2data(x, y): return (A["xf"] + (x - FLA) / SXA, A["yt"] - (y - FT) / SYA)
    def b_pt2data(x, y): return (Bs["xf"] + (x - FLB) / SXB, Bs["yt"] - (y - FT) / SYB)

    op.set_show(False)
    gp = op.new_graph("Fig7")
    ws = op.new_sheet("w", "D7")
    ci = [0]
    def add(vals, lname, axis=""):
        ws.from_list(ci[0], vals, lname=lname, axis=axis); ci[0] += 1; return lname
    def axis_style(lay, a):
        lay.lt_exec("layer.%s.ticks=0;layer.%s.minorTicks=0;layer.%s.showlabel=0;"
                    "layer.%s.thickness=0.75;layer.%s.color=color(%d,%d,%d);" %
                    (a, a, a, a, a, int(K["spine"][1:3], 16), int(K["spine"][3:5], 16), int(K["spine"][5:7], 16)))
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
                     (name, fsn(fs), name, name, int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)))
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
    def rect_pts(v, row):
        """bar rectangle (design pt): 5-point closed polyline."""
        x0, x1 = FLA, FLA + v * SXA
        yc = FT + (A["yt"] - row) * SYA
        h = K["bar_half"]
        return [(x0, yc - h), (x1, yc - h), (x1, yc + h), (x0, yc + h), (x0, yc - h)]
    def draw_poly(lay, pts_pt, conv, pre, colorhex, width, fill=None):
        dd = [conv(x, y) if x is not None else (None, None) for x, y in pts_pt]
        xx = add([q[0] for q in dd], pre + "x", "X"); yy = add([q[1] for q in dd], pre + "y", "Y")
        p = lay.add_plot(ws, yy, xx, type="l")
        p.color = COL(colorhex); p.set_cmd("-wp %g" % width, "-d 0")
        if fill is not None:
            # manual fill: set_fill_area() uses bare "set <name>" which binds to the
            # ACTIVE layer; production has 3 layers, so bind the range explicitly.
            lay.lt_exec("{range rr=%s; set rr -pf 1; set rr -pfv 1; set rr -pfb %d;}" %
                        (p.lt_range(), COL(colorhex)))
        return p
    L("boot ok")

    lay1 = gp[0]; lay2 = gp.add_layer(0); lay0 = gp.add_layer(0)
    L("z-order: lay1=gp[0](A) lay2=(B) lay0=(text canvas)  dx=%g dy=%g" % (DX, DY))
    setup(lay1, A); setup(lay2, Bs)

    bars = rd("fig7_a_bars.csv")
    pts = rd("fig7_b_points.csv")

    # ------------------------------------------------ mean guide (behind everything)
    if not PROBE:
        segA = [(FLA + MEAN["v"] * SXA, FT), (FLA + MEAN["v"] * SXA, FB)]
        dshA = [a_pt2data(x, y) if x is not None else (None, None) for x, y in dashify(segA, MEAN["pattern"])]
        xx = add([q[0] for q in dshA], "meanax", "X"); yy = add([q[1] for q in dshA], "meanay", "Y")
        pa = lay1.add_plot(ws, yy, xx, type="l")
        pa.color = COL(MEAN["color"]); pa.set_cmd("-wp %g" % MEAN["width_a"], "-d 0")
        segB = [(FLB, FT + (Bs["yt"] - MEAN["v"]) * SYB), (FRB, FT + (Bs["yt"] - MEAN["v"]) * SYB)]
        dshB = [b_pt2data(x, y) if x is not None else (None, None) for x, y in dashify(segB, MEAN["pattern"])]
        xx = add([q[0] for q in dshB], "meanbx", "X"); yy = add([q[1] for q in dshB], "meanby", "Y")
        pb = lay2.add_plot(ws, yy, xx, type="l")
        pb.color = COL(MEAN["color"]); pb.set_cmd("-wp %g" % MEAN["width_b"], "-d 0")
        L("mean guide dashes a=%d b=%d at %.1f" % (len(dshA) // 3, len(dshB) // 3, MEAN["v"]))

    # ------------------------------------------------ panel (a): bars
    if not PROBE:
        CLS = K["cls"]
        for r in bars:
            row = int(r["row"]); v = float(r["mape"]); c = r["cls"]
            rp = rect_pts(v, row)
            draw_poly(lay1, rp, a_pt2data, "bf%d" % row, CLS[c]["fill"], K["bar_pen"], fill=1)
            draw_poly(lay1, rp, a_pt2data, "bo%d" % row, CLS[c]["edge"], K["bar_pen"])
        L("bars drawn n=%d half=%.3f pen=%.2f" % (len(bars), K["bar_half"], K["bar_pen"]))
    else:
        bare(lay1)

    # ------------------------------------------------ panel (b): scatter
    if not PROBE:
        for c in ("tracer", "inter", "impurity"):
            sub = [r for r in pts if r["cls"] == c]
            xx = add([float(r["x"]) for r in sub], "bpt_%sx" % c[:2], "X")
            yy = add([float(r["y"]) for r in sub], "bpt_%sy" % c[:2], "Y")
            p = lay2.add_plot(ws, yy, xx, type="s")
            m = M[c]
            p.symbol_kind = m["kind"]; p.symbol_size = m["z"]; p.symbol_interior = 1
            p.set_cmd("-csf %d" % COL(m["fill"]), "-cse %d" % COL(m["edge"]),
                      "-kh 6", "-wp %g" % K["bar_pen"])
            L("scat %s n=%d kind=%d z=%g" % (c, len(sub), m["kind"], m["z"]))
    else:
        bare(lay2)

    # ------------------------------------------------ legend (a): swatches + label x
    if not PROBE:
        HIT = {it["name"]: it for it in K["horiz"]}
        rows = LEG["rows"]; hw = LEG["hw"]; txg = LEG["txgap"]; itg = LEG["itemgap"]
        ws_ = [OFFS[r["name"]]["jx1"] - OFFS[r["name"]]["jx0"] for r in rows]
        tot = sum(2 * hw + txg + w + itg for w in ws_) - itg
        handles = []; acc = 0.0
        X0 = (FLA + FRA) / 2.0 - tot / 2.0
        for r, w in zip(rows, ws_):
            hcx = X0 + acc + hw
            it = HIT[r["name"]]
            it["ax"] = "left"
            it["tx"] = round(hcx + hw + txg, 4)
            handles.append((r["cls"], hcx, FB + LEG["top_d"] + 3.35))
            acc += 2 * hw + txg + w + itg
        L("legend row: tot=%.2f X0=%.2f handles=%s" % (tot, X0, [(h[1]) for h in handles]))
        for c, hcx, hcy in handles:
            rp = [(hcx - hw, hcy - LEG["hh"]), (hcx + hw, hcy - LEG["hh"]),
                  (hcx + hw, hcy + LEG["hh"]), (hcx - hw, hcy + LEG["hh"]),
                  (hcx - hw, hcy - LEG["hh"])]
            # hatch fill drawn on the CANVAS layer: the swatch lane sits below
            # lay1's y range, and data plots are clipped to their layer frame.
            segs = []
            y = hcy - LEG["hh"] + 0.25
            while y <= hcy + LEG["hh"] - 0.25 + 1e-9:
                segs += [(hcx - hw, y), (hcx + hw, y), (None, None)]
                y += 0.35
            dd = [(x, L0["height"] * PT - y) if x is not None else (None, None)
                  for x, y in segs]
            xx = add([q[0] for q in dd], "lgh_%sx" % c[:2], "X")
            yy2 = add([q[1] for q in dd], "lgh_%sy" % c[:2], "Y")
            ph = lay0.add_plot(ws, yy2, xx, type="l")
            ph.color = COL(CLS[c]["fill"]); ph.set_cmd("-wp 0.5", "-d 0")
            dd2 = [(x, L0["height"] * PT - y) for x, y in rp]
            xx = add([q[0] for q in dd2], "lgo_%sx" % c[:2], "X")
            yy3 = add([q[1] for q in dd2], "lgo_%sy" % c[:2], "Y")
            po = lay0.add_plot(ws, yy3, xx, type="l")
            po.color = COL(CLS[c]["edge"]); po.set_cmd("-wp 0.5", "-d 0")

    # ------------------------------------------------ hand-drawn inward ticks, 4 sides
    if not PROBE:
        for lay, spec, sx, sy, pre in ((lay1, A, SXA, SYA, "a"), (lay2, Bs, SXB, SYB, "b")):
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
            L("ticks %s n=%d len=%.2f width=%.2f" % (pre, len(tx) // 3, TL, K["tick"]["thick"]))

    # ------------------------------------------------ lay0 : all text
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

    lay1.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" % (A["xf"], A["xt"], A["yf"], A["yt"]))
    lay2.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" % (Bs["xf"], Bs["xt"], Bs["yf"], Bs["yt"]))
    lay0.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" % (L0["width"] * PT, L0["height"] * PT))
    for lay in (lay0, lay1, lay2): drop_titles(lay)
    for lay, tg in ((lay1, "lay1"), (lay2, "lay2"), (lay0, "lay0")): kill_legend(lay, tg)
    L("ranges locked, titles dropped")
    if PROBE:
        L("probe pdf=" + str(gp.save_fig(os.path.join(OUT, "_probe_fig7_anchors.pdf"), type="pdf")))
    else:
        opju = os.path.join(OUT, NAME + ".opju")
        op.save(opju); L("opju=" + opju)
        L("svg raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_fig7.svg"), type="svg")))
        L("png raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_fig7.png"), type="png", width=K["export"]["png_width"])))
        L("pdf raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_fig7.pdf"), type="pdf")))
    op.exit(); L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())
    try:
        op.exit()
    except Exception:
        pass
print("\n".join(log))




