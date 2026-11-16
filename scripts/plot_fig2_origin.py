r"""Fig. 2  (phase-space coverage + D vs eta) -- native Origin redraw.

House twin of plot_fig6_origin.py / plot_fig4_origin.py:
  * two data layers (a, b) in cm units + one canvas layer (lay0) for ALL text
  * every string is placed from an INK-BOX target using per-item anchor->ink
    offsets measured on a dedicated probe page (F2PROBE=1, then _z_fig2_measure.py)
  * Origin is told to draw NO ticks and NO tick labels; the inward ticks of all
    four sides are hand-drawn at the measured rendered length (3.36 pt) and the
    house thickness (0.75 pt), so the box is closed on four sides with identical
    inward ticks everywhere.  Panel (b) needs non-uniform log tick positions, so
    hand-drawn ticks are required there anyway.
  * Arial throughout (Origin \i \b \x markup only -- no mathtext / STIX)
  * Okabe-Ito colours, NO in-figure suptitle
  * the modified-Sutherland guide is emitted as an explicit dash polyline: the
    custom command "set plot -1 <style>" is not accepted by Origin 2026 and
    blocks the automation server, so the dash pattern is generated here
    (5.5 pt on / 5.5 pt off = the frozen reference dash period scaled to this
    canvas).

    F2PROBE=1 python scripts/plot_fig2_origin.py   # text anchor calibration page
    python scripts/plot_fig2_origin.py             # production render + .opju
"""
import os, json, csv, re, math, bisect, traceback
import originpro as op

BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(BASE, "outputs", "origin_data")
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
PROBE = os.environ.get("F2PROBE", "0") == "1"
TAG = "_probe" if PROBE else ""
LOG = os.path.join(OD, "_qa_fig2_render%s.txt" % TAG)
OFF_JSON = os.path.join(OD, "fig2_text_offsets.json")
NAME = "Fig2_phase_space_coverage"
DASH_ON, DASH_OFF = 5.5, 5.5
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

def dashify(pts, on=DASH_ON, off=DASH_OFF):
    """polyline (design pt) -> dash segments, None-separated, same pt units."""
    cum = [0.0]; total = 0.0
    for i in range(len(pts) - 1):
        total += math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        cum.append(total)
    def at(d):
        d = max(0.0, min(total, d))
        k = max(0, min(bisect.bisect_left(cum, d) - 1, len(pts) - 2))
        s0, s1 = cum[k], cum[k + 1]
        f = 0.0 if s1 <= s0 else (d - s0) / (s1 - s0)
        return (pts[k][0] + f * (pts[k + 1][0] - pts[k][0]),
                pts[k][1] + f * (pts[k + 1][1] - pts[k][1]))
    out = []; d = 0.0; first = True
    while d < total - 1e-9:
        a = at(d); b = at(min(total, d + on))
        if not first:
            out.append((None, None))
        out.append(a); out.append(b); first = False
        d += on + off
    return out

try:
    K = json.load(open(os.path.join(OD, "fig2_origin_constants.json"), encoding="utf-8-sig"))
    fsmap = K["fs_map"]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    DEC = K["decoy"]; DX = DEC["dx"]; DY = DEC["dy"]
    FR = K["frame"]; M = K["markers"]
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
            raise RuntimeError("missing " + OFF_JSON + " -- run F2PROBE=1 then _z_fig2_measure.py")
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
    gp = op.new_graph("Fig2")
    ws = op.new_sheet("w", "D2")
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
    def scat(lay, csvname, pre, m, open_sym=False, pen=1.0):
        rows = rd(csvname)
        if not rows:
            L("scat %s: EMPTY -> skipped" % pre); return None
        xx = add([float(r["x"]) for r in rows], pre + "x", "X")
        yy = add([float(r["y"]) for r in rows], pre + "y", "Y")
        p = lay.add_plot(ws, yy, xx, type="s")
        p.symbol_kind = m["kind"]; p.symbol_size = m["z"]
        p.symbol_interior = 0 if open_sym else 1
        if open_sym:
            p.set_cmd("-c %d" % COL(m["edge"]), "-cse %d" % COL(m["edge"]),
                      "-csf 1", "-kh 6", "-wp %g" % pen)
        else:
            p.set_cmd("-csf %d" % COL(m["fill"]), "-cse %d" % COL(m["edge"]), "-kh 6")
        L("scat %s n=%d kind=%d z=%g ink=%.2f open=%d" % (pre, len(rows), m["kind"], m["z"], m["ink"], int(open_sym)))
        return p
    L("boot ok")

    lay1 = gp[0]; lay2 = gp.add_layer(0); lay0 = gp.add_layer(0)
    L("z-order: lay1=gp[0](A) lay2=(B) lay0=(text canvas)  dx=%g dy=%g" % (DX, DY))
    setup(lay1, A); setup(lay2, Bs)

    # ------------------------------------------------ panel (a)
    if not PROBE:
        scat(lay1, "fig2_a_tracer.csv", "at", M["tracer"])
        scat(lay1, "fig2_a_inter.csv", "ai", M["inter"])
        scat(lay1, "fig2_a_impurity.csv", "ap", M["impurity"])
        scat(lay1, "fig2_a_self.csv", "as", M["self"])
        for sysname in ("Al-Ce-Ni", "Al-Mg-Si", "Al-Ag-Cu"):
            cm = dict(M["cross"]); cm["edge"] = K["sparse_colors"][sysname]
            scat(lay1, "fig2_a_%s.csv" % sysname.lower().replace("-", ""),
                 "ax_" + sysname[:2].lower() + sysname[-2:].lower(), cm, open_sym=True)
    else:
        bare(lay1)

    # ------------------------------------------------ panel (b)
    if not PROBE:
        # guide first (z-order underneath), as an explicit dash polyline
        g = [(FLB + (float(r["x"]) - Bs["xf"]) * SXB, FT + (Bs["yt"] - float(r["y"])) * SYB)
             for r in rd("fig2_b_guide.csv")]
        gsegs = dashify(g)
        gd = [b_pt2data(x, y) if x is not None else (None, None) for x, y in gsegs]
        gu = add([q[0] for q in gd], "gbu", "X"); gv = add([q[1] for q in gd], "gbv", "Y")
        pg = lay2.add_plot(ws, gv, gu, type="l")
        pg.color = COL(K["guide"]["color"]); pg.set_cmd("-wp 1.0", "-d 0")
        L("guide dashes=%d pen=1.00 on/off=%.1f/%.1f" % (len(gd) // 3, DASH_ON, DASH_OFF))
        for dt in ("tracer", "inter", "impurity", "self"):
            scat(lay2, "fig2_b_%s.csv" % dt, "bt_" + dt[:2], M[dt])
        scat(lay2, "fig2_b_prior.csv", "bp", M["prior"], open_sym=True, pen=0.8)
    else:
        bare(lay2)

    # ------------------------------------------------ legend handles
    LEGW = {}
    if not PROBE:
        for tag, rows in (("A", K["legend"]["A"]), ("B", K["legend"]["B"])):
            HIT = {it["name"]: it for it in K["horiz"]}
            w1 = [OFFS[r["name"]]["jx1"] - OFFS[r["name"]]["jx0"] for r in rows["rows"] if r["col"] == 1]
            lab1 = FLA + rows["box"]["L"] + rows["gap"] if tag == "A" else FLB + rows["box"]["L"] + rows["gap"]
            col2h = lab1 + max(w1) + rows["gap"]
            n1 = len(rows["col1"])
            for r in rows["rows"]:
                it = HIT[r["name"]]
                it["ax"] = "left"
                it["tx"] = round(lab1 if r["col"] == 1 else col2h + rows["gap"], 4)
            LEGW[tag] = dict(lab1=lab1, col2h=col2h, w1=max(w1),
                             w2=max(OFFS[r["name"]]["jx1"] - OFFS[r["name"]]["jx0"]
                                    for r in rows["rows"] if r["col"] == 2))
            L("legend %s: lab1=%.3f col1w=%.3f col2h=%.3f col2w=%.3f right=%.3f" %
              (tag, lab1, max(w1), col2h, LEGW[tag]["w2"], col2h + rows["gap"] + LEGW[tag]["w2"]))
            # handles: single-point scatter plots on the data layer (same size law)
            hdy = 2.4
            for r in rows["rows"]:
                cx = (lab1 - rows["gap"]) if r["col"] == 1 else col2h
                cy = r["ink_top"] + hdy
                if tag == "A":
                    dxv, dyv = a_pt2data(cx, cy)
                else:
                    dxv, dyv = b_pt2data(cx, cy)
                src = r["src"]
                if src == "guide":
                    hsegs = [(cx - 7.0, cy), (None, None), (cx + 2.0, cy), (cx + 7.0, cy)]
                    hs = [b_pt2data(x, y) if x is not None else (None, None) for x, y in hsegs]
                    hx = add([q[0] for q in hs], "lghx_%s_g" % tag, "X")
                    hy = add([q[1] for q in hs], "lghy_%s_g" % tag, "Y")
                    ph = lay2.add_plot(ws, hy, hx, type="l")
                    ph.color = COL(K["guide"]["color"]); ph.set_cmd("-wp 1.0", "-d 0")
                    L("legend handle %s/%s LINE cx=%.3f cy=%.3f" % (tag, src, cx, cy))
                    continue
                if src in ("Al-Ce-Ni", "Al-Mg-Si", "Al-Ag-Cu"):
                    m = dict(M["cross"]); m["edge"] = K["sparse_colors"][src]; op_ = True; pen = 1.0
                elif src == "prior":
                    m = M["prior"]; op_ = True; pen = 1.0
                else:
                    m = M[src]; op_ = False; pen = 0.9
                hx = add([dxv], "lghx_%s_%s" % (tag, src), "X")
                hy = add([dyv], "lghy_%s_%s" % (tag, src), "Y")
                pl = (lay1 if tag == "A" else lay2).add_plot(ws, hy, hx, type="s")
                pl.symbol_kind = m["kind"]; pl.symbol_size = m["z"]; pl.symbol_interior = 0 if op_ else 1
                if op_:
                    pl.set_cmd("-c %d" % COL(m["edge"]), "-cse %d" % COL(m["edge"]), "-csf 1", "-kh 6", "-wp %g" % pen)
                else:
                    pl.set_cmd("-csf %d" % COL(m["fill"]), "-cse %d" % COL(m["edge"]), "-kh 6")
                L("legend handle %s/%s kind=%d z=%g cx=%.3f cy=%.3f" % (tag, src, m["kind"], m["z"], cx, cy))

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
        L("probe pdf=" + str(gp.save_fig(os.path.join(OUT, "_probe_fig2_anchors.pdf"), type="pdf")))
    else:
        opju = os.path.join(OUT, NAME + ".opju")
        op.save(opju); L("opju=" + opju)
        L("svg raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_fig2.svg"), type="svg")))
        L("png raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_fig2.png"), type="png", width=K["export"]["png_width"])))
        L("pdf raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_fig2.pdf"), type="pdf")))
    op.exit(); L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())
    try:
        op.exit()
    except Exception:
        pass
print("\n".join(log))
