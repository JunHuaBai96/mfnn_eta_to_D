r"""Fig. 5  (representative Arrhenius panels) -- native Origin redraw.

House twin of plot_fig2_origin.py / plot_fig6_origin.py / plot_fig4_origin.py:
  * two data layers (a, b) in cm units + one canvas layer (lay0) for ALL text
  * every string is placed from an INK-BOX target using per-item anchor->ink
    offsets measured on a dedicated probe page (F5PROBE=1, then _z_fig5_measure.py)
  * Origin is told to draw NO ticks and NO tick labels; the inward ticks of all
    four sides are hand-drawn at the measured rendered length (3.36 pt) and the
    house thickness (0.75 pt), so the box is closed on four sides with identical
    inward ticks everywhere.
  * Arial throughout (Origin \i \b \- \+ \x markup only -- no mathtext / STIX)
  * Okabe-Ito colours, NO in-figure suptitle
  * the dotted / dashed / dash-dot series are emitted as EXPLICIT dash polylines:
    the custom command "set plot -1 <style>" is not accepted by Origin 2026 and
    blocks the automation server, so every dash pattern is generated here from the
    frozen reference pattern (matplotlib ':' / '--' / '-.' at lw 1.2) scaled to the
    6.30 in deliverable.  The LF-only NN zig-zag is the checkpoint prediction and is
    NOT smoothed: dashes are laid along the raw 40-point polyline.

    F5PROBE=1 python scripts/plot_fig5_origin.py   # text anchor calibration page
    python scripts/plot_fig5_origin.py             # production render + .opju
"""
import os, json, csv, re, math, bisect, traceback
import originpro as op

BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(BASE, "outputs", "origin_data")
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
PROBE = os.environ.get("F5PROBE", "0") == "1"
TAG = "_probe" if PROBE else ""
LOG = os.path.join(OD, "_qa_fig5_render%s.txt" % TAG)
OFF_JSON = os.path.join(OD, "fig5_text_offsets.json")
NAME = "Fig5_arrhenius_representative"
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
    """polyline (design pt) -> dash segments, None-separated, same pt units.

    pattern = [on, off, on, off, ...] in design pt; a 2-element pattern is a plain
    dashed line, a 4-element pattern is a dash-dot line."""
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
    K = json.load(open(os.path.join(OD, "fig5_origin_constants.json"), encoding="utf-8-sig"))
    fsmap = K["fs_map"]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    DEC = K["decoy"]; DX = DEC["dx"]; DY = DEC["dy"]
    FR = K["frame"]; M = K["markers"]; LN = K["lines"]
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
            raise RuntimeError("missing " + OFF_JSON + " -- run F5PROBE=1 then _z_fig5_measure.py")
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
    gp = op.new_graph("Fig5")
    ws = op.new_sheet("w", "D5")
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
    def dashline(lay, csvname, pre, FL, sx, sy, xf, xt, yf, yt, spec):
        """explicit dash polyline: data -> design pt -> dash pattern -> data."""
        rows = rd(csvname)
        pts = [(FL + (float(r["x"]) - xf) * sx, FT + (yt - float(r["y"])) * sy) for r in rows]
        segs = dashify(pts, spec["pattern"])
        conv = (a_pt2data if pre.startswith("a") else b_pt2data)
        dd = [conv(x, y) if x is not None else (None, None) for x, y in segs]
        xx = add([q[0] for q in dd], pre + "x", "X"); yy = add([q[1] for q in dd], pre + "y", "Y")
        p = lay.add_plot(ws, yy, xx, type="l")
        p.color = COL(spec["color"]); p.set_cmd("-wp %g" % spec["width"], "-d 0")
        L("dash %s n=%d dashes=%d pat=%s w=%.3f" % (pre, len(rows), len(dd) // 3, spec["pattern"], spec["width"]))
        return p
    def solidline(lay, csvname, pre, spec):
        rows = rd(csvname)
        xx = add([float(r["x"]) for r in rows], pre + "x", "X")
        yy = add([float(r["y"]) for r in rows], pre + "y", "Y")
        p = lay.add_plot(ws, yy, xx, type="l")
        p.color = COL(spec["color"]); p.set_cmd("-wp %g" % spec["width"], "-d 0")
        L("solid %s n=%d w=%.3f" % (pre, len(rows), spec["width"]))
        return p
    def scat(lay, csvname, pre, m):
        rows = rd(csvname)
        if not rows:
            L("scat %s: EMPTY -> skipped" % pre); return None
        xx = add([float(r["x"]) for r in rows], pre + "x", "X")
        yy = add([float(r["y"]) for r in rows], pre + "y", "Y")
        p = lay.add_plot(ws, yy, xx, type="s")
        p.symbol_kind = m["kind"]; p.symbol_size = m["z"]
        p.symbol_interior = 1
        p.set_cmd("-csf %d" % COL(m["fill"]), "-cse %d" % COL(m["edge"]),
                  "-kh 6", "-wp %g" % m["pen"])
        L("scat %s n=%d kind=%d z=%g ink=%.2f" % (pre, len(rows), m["kind"], m["z"], m["ink"]))
        return p
    L("boot ok")

    lay1 = gp[0]; lay2 = gp.add_layer(0); lay0 = gp.add_layer(0)
    L("z-order: lay1=gp[0](A) lay2=(B) lay0=(text canvas)  dx=%g dy=%g" % (DX, DY))
    setup(lay1, A); setup(lay2, Bs)

    # ------------------------------------------------ data series
    for tag, lay, spec, FL, sx, sy in (("a", lay1, A, FLA, SXA, SYA), ("b", lay2, Bs, FLB, SXB, SYB)):
        if PROBE:
            bare(lay); continue
        for pre in ("prior", "lf", "hf"):
            dashline(lay, "fig5_%s_%s.csv" % (tag, pre), "%s_%s" % (tag, pre),
                     FL, sx, sy, spec["xf"], spec["xt"], spec["yf"], spec["yt"], LN[pre])
        solidline(lay, "fig5_%s_mfnn.csv" % tag, "%s_mfnn" % tag, LN["mfnn"])
        scat(lay, "fig5_%s_exp.csv" % tag, "%s_exp" % tag, M["exp"])

    # ------------------------------------------------ legend handles
    if not PROBE:
        for tag, rows in (("A", K["legend"]["A"]), ("B", K["legend"]["B"])):
            HIT = {it["name"]: it for it in K["horiz"]}
            pre = tag.lower()
            w1 = [OFFS[r["name"]]["jx1"] - OFFS[r["name"]]["jx0"] for r in rows["rows"] if r["col"] == 1]
            lab1 = FLA + rows["box"]["L"] + rows["gap"] if tag == "A" else FLB + rows["box"]["L"] + rows["gap"]
            col2h = lab1 + max(w1) + rows["gap"]
            n1 = len(rows["col1"])
            for r in rows["rows"]:
                it = HIT[r["name"]]
                it["ax"] = "left"
                it["tx"] = round(lab1 if r["col"] == 1 else col2h + rows["gap"], 4)
            L("legend %s: lab1=%.3f col1w=%.3f col2h=%.3f" % (tag, lab1, max(w1), col2h))
            FL = FLA if tag == "A" else FLB
            sx = SXA if tag == "A" else SXB
            sy = SYA if tag == "A" else SYB
            lay = lay1 if tag == "A" else lay2
            conv = a_pt2data if tag == "A" else b_pt2data
            for r in rows["rows"]:
                cx = (lab1 - rows["gap"]) if r["col"] == 1 else col2h
                cy = r["ink_top"] + 2.4
                src = r["src"]
                if src == "exp":
                    dxv, dyv = conv(FL + (cx - FL) + 0.0, cy)
                    hx = add([dxv], "lghx_%s_e" % tag, "X"); hy = add([dyv], "lghy_%s_e" % tag, "Y")
                    pl = lay.add_plot(ws, hy, hx, type="s")
                    m = M["exp"]
                    pl.symbol_kind = m["kind"]; pl.symbol_size = m["z"]; pl.symbol_interior = 1
                    pl.set_cmd("-csf %d" % COL(m["fill"]), "-cse %d" % COL(m["edge"]),
                               "-kh 6", "-wp %g" % m["pen"])
                    L("legend handle %s/exp cx=%.3f cy=%.3f" % (tag, cx, cy))
                    continue
                sp = LN[src]
                seg = [(cx - 7.0, cy), (cx + 7.0, cy)]
                hs = dashify(seg, sp["pattern"]) if sp["pattern"] else seg
                hd = [conv(x, y) if x is not None else (None, None) for x, y in hs]
                hx = add([q[0] for q in hd], "lghx_%s_%s" % (tag, src), "X")
                hy = add([q[1] for q in hd], "lghy_%s_%s" % (tag, src), "Y")
                ph = lay.add_plot(ws, hy, hx, type="l")
                ph.color = COL(sp["color"]); ph.set_cmd("-wp %g" % sp["width"], "-d 0")
                L("legend handle %s/%s cx=%.3f cy=%.3f segs=%d" % (tag, src, cx, cy, len(hd) // 3))

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
        L("probe pdf=" + str(gp.save_fig(os.path.join(OUT, "_probe_fig5_anchors.pdf"), type="pdf")))
    else:
        opju = os.path.join(OUT, NAME + ".opju")
        op.save(opju); L("opju=" + opju)
        L("svg raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_fig5.svg"), type="svg")))
        L("png raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_fig5.png"), type="png", width=K["export"]["png_width"])))
        L("pdf raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_fig5.pdf"), type="pdf")))
    op.exit(); L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())
    try:
        op.exit()
    except Exception:
        pass
print("\n".join(log))
