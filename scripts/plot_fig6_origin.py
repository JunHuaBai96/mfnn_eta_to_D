"""Fig. 6  (Al80Cu20 tracer vs interdiffusivity) -- native Origin redraw.

Same house workflow as Fig. 3 / Fig. 4:
  * two data layers (a, b) in cm units + one canvas layer (lay0) for ALL text
  * every string is placed from an ink-box target using per-item anchor->ink offsets
    that were measured on a dedicated probe page (F6PROBE=1 -> _z_fig6_measure.py)
  * Origin renders ticks only on the bottom/left spines, so the top/right inward
    ticks are hand-drawn on the data layers at the measured tick length (3.36 pt)
  * closed 4-side box, Arial throughout, Okabe-Ito colours, NO in-figure suptitle

    F6PROBE=1 python scripts/plot_fig6_origin.py     # text anchor calibration page
    python scripts/plot_fig6_origin.py               # production render + .opju
"""
import os, json, csv, re, traceback
import originpro as op

BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(BASE, "outputs", "origin_data")
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
PROBE = os.environ.get("F6PROBE", "0") == "1"
TAG = "_probe" if PROBE else ""
LOG = os.path.join(OD, "_qa_fig6_render%s.txt" % TAG)
OFF_JSON = os.path.join(OD, "fig6_text_offsets.json")
NAME = "Fig6_Al80_tracer_inter"
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
L0 = {"left": 0.05, "top": 0.05, "width": 19.0, "height": 13.4}

try:
    K = json.load(open(os.path.join(OD, "fig6_origin_constants.json"), encoding="utf-8-sig"))
    fsmap = K["fs_map"]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    DEC = K["decoy"]; DX = DEC["dx"]; DY = DEC["dy"]
    FR = K["frame"]
    A = K["layers"]["a"]; Bs = K["layers"]["b"]
    TL = K["tick"]["len_rendered"]
    OFFS = {}
    if PROBE:
        L("PROBE mode: text-only calibration page (no data, no frames, no ticks)")
    else:
        if not os.path.exists(OFF_JSON):
            raise RuntimeError("missing " + OFF_JSON + " -- run F6PROBE=1 and _z_fig6_measure.py first")
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
    op.set_show(False)
    gp = op.new_graph("Fig6")
    ws = op.new_sheet("w", "D6")
    ci = [0]
    def add(vals, lname, axis=""):
        ws.from_list(ci[0], vals, lname=lname, axis=axis); ci[0] += 1; return lname
    def axis_style(lay, a):
        lay.lt_exec("layer.%s.ticks=1;layer.%s.minorTicks=0;layer.%s.ticklength=3.6;layer.%s.tickthickness=0.75;"
                    "layer.%s.color=color(51,51,51);layer.%s.thickness=0.75;layer.%s.showlabel=0;" % (a, a, a, a, a, a, a))
    def bare(lay):
        "PROBE only: no frame lines and no ticks, so ink windows can only see text."
        lay.activate()   # lt_exec "layer." acts on the ACTIVE layer
        lay.lt_exec("layer.showframe=0;")
        for a in ("x", "x2", "y", "y2"):
            # showframe=0 alone still keeps left/bottom -> also zero the axis thickness
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
        lay.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" % (L0["width"] * PT, L0["height"] * PT))
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
        lay.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.x.inc=%g;layer.x.firstTick=%g;" %
                    (spec["xf"], spec["xt"], spec["xi"], spec["xfirst"]))
        lay.lt_exec("layer.y.from=%g;layer.y.to=%g;layer.y.inc=%g;layer.y.firstTick=%g;" %
                    (spec["yf"], spec["yt"], spec["yi"], spec["yfirst"]))
        lay.lt_exec("layer.sauto=0;")
        for a in ("x", "x2", "y", "y2"): axis_style(lay, a)
    lay1 = gp[0]; lay2 = gp.add_layer(0); lay0 = gp.add_layer(0)
    L("z-order: lay1=gp[0](A) lay2=add(A) lay0=add(text canvas)  dx=%g dy=%g" % (DX, DY))
    setup(lay1, A); setup(lay2, Bs)

    # ---------- panel A ----------
    if not PROBE:
        AR = K["arrow"]
        segs = AR["shaft"] + [[None, None]] + AR["head_up"] + [[None, None]] + AR["head_dn"]
        axx = add([s[0] for s in segs], "arx", "X"); ayy = add([s[1] for s in segs], "ary", "Y")
        par = lay1.add_plot(ws, ayy, axx, type="l")
        par.color = COL(AR["color"]); par.set_cmd("-wp %g" % AR["pen"], "-d 0")
        L("arrow: shaft x=%.3f  y(data) %.4f..%.4f  pen=%.2f" %
          (AR["shaft"][0][0], AR["shaft"][0][1], AR["shaft"][1][1], AR["pen"]))
        def scat(lay, csvname, pre, m):
            rows = rd(csvname)
            xx = add([float(r["x"]) for r in rows], pre + "x", "X"); yy = add([float(r["y"]) for r in rows], pre + "y", "Y")
            p = lay.add_plot(ws, yy, xx, type="s")
            p.symbol_kind = m["kind"]; p.symbol_size = m["z"]; p.symbol_interior = 1
            p.set_cmd("-csf %d" % COL(m["fill"]), "-cse %d" % COL(m["edge"]), "-kh 6")
            L("scat %s n=%d kind=%d z=%g" % (pre, len(rows), m["kind"], m["z"]))
        M = K["markers"]
        scat(lay1, "fig6_panelA_tracer.csv", "tr", M["tracer"])
        scat(lay1, "fig6_panelA_inter.csv", "it", M["inter"])
        # legend handles: symbols on lay1 (identical geometry to the data -> same size law)
        # legend = ONE aligned column: both handles share x, both labels share their
        # left edge, and the widest label still ends LEG_DX_R inside the frame right.
        LEG = K["legend"]
        HIT = {it["name"]: it for it in K["horiz"]}
        LGW = [OFFS[r["name"]]["jx1"] - OFFS[r["name"]]["jx0"] for r in LEG["rows"]]
        LAB_L = LEG["rows"][0]["label_right"] - max(LGW)
        for r in LEG["rows"]:
            HIT[r["name"]]["ax"] = "left"; HIT[r["name"]]["tx"] = LAB_L
        L("legend column: widths=%s label_left=%.3f right=%.3f handle_cx=%.3f" %
          (["%.3f" % w for w in LGW], LAB_L, LEG["rows"][0]["label_right"], LAB_L - LEG["handle_gap"]))
        for i, row in enumerate(LEG["rows"]):
            hcx = LAB_L - LEG["handle_gap"]
            hcy = row["ink_top"] + LEG["handle_dy"]
            dxv = A["xf"] + (hcx - FR["FL_A"]) / FR["sx_a"]
            dyv = A["yt"] - (hcy - FR["FT"]) / FR["sy_a"]
            m = M[row["src"]]
            hx = add([dxv], "lghx%d" % i, "X"); hy = add([dyv], "lghy%d" % i, "Y")
            ph = lay1.add_plot(ws, hy, hx, type="s")
            ph.symbol_kind = m["kind"]; ph.symbol_size = m["z"]; ph.symbol_interior = 1
            ph.set_cmd("-csf %d" % COL(m["fill"]), "-cse %d" % COL(m["edge"]), "-kh 6")
            L("legend handle %d inkW=%.3f cx=%.3f cy=%.3f -> data(%.3f,%.4f)" % (i, LGW[i], hcx, hcy, dxv, dyv))
    else:
        bare(lay1)

    # ---------- panel B ----------
    if not PROBE:
        bb = K["bars"]; rows = rd("fig6_panelB_bars.csv")
        byc = add([float(r["value"]) for r in rows], "barv", "Y")
        bxc = add([float(r["x"]) for r in rows], "barx", "X")
        pcol = lay2.add_plot(ws, byc, bxc, type="c")
        pcol.color = COL(K["dark"]); pcol.set_cmd(bb["gap_cmd"], bb["pbs"], bb["vw"])
        for i in range(len(rows)):
            pcol.set_cmd("%d -pfb %d" % (i + 1, COL(bb["faces"][i])), "%d -pbc %d" % (i + 1, COL(bb["edges"][i])))
        L("bars n=%d %s width_du=%.2f" % (len(rows), bb["gap_cmd"], bb["width_du"]))
    else:
        bare(lay2)

    # ---------- hand-drawn top / right inward ticks (Origin cannot draw them) ----------
    if not PROBE:
        for lay, spec, sx, sy, pre in ((lay1, A, FR["sx_a"], FR["sy_a"], "a"), (lay2, Bs, FR["sx_b"], FR["sy_b"], "b")):
            tx = []; ty = []
            for v in spec["xticks"]:
                tx += [v, v, None]; ty += [spec["yt"], spec["yt"] - TL / sy, None]
            for v in spec["yticks"]:
                tx += [spec["xt"], spec["xt"] - TL / sx, None]; ty += [v, v, None]
            xx = add(tx, "tkx_" + pre, "X"); yy = add(ty, "tky_" + pre, "Y")
            ptk = lay.add_plot(ws, yy, xx, type="l")
            ptk.color = COL(K["spine"]); ptk.set_cmd("-wp %g" % K["tick"]["thick"], "-d 0")
            L("ticks_extra %s n=%d len=%.2f width=%.2f" % (pre, len(tx) // 3, TL, K["tick"]["thick"]))

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

    lay1.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" % (A["xf"], A["xt"], A["yf"], A["yt"]))
    lay2.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" % (Bs["xf"], Bs["xt"], Bs["yf"], Bs["yt"]))
    lay0.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" % (L0["width"] * PT, L0["height"] * PT))
    for lay in (lay0, lay1, lay2): drop_titles(lay)
    for lay, tg in ((lay1, "lay1"), (lay2, "lay2"), (lay0, "lay0")): kill_legend(lay, tg)
    L("ranges locked, titles dropped")
    if PROBE:
        pdfp = gp.save_fig(os.path.join(OUT, "_probe_fig6_anchors.pdf"), type="pdf")
        L("probe pdf=" + str(pdfp))
    else:
        opju = os.path.join(OUT, NAME + ".opju")
        op.save(opju); L("opju=" + opju)
        svgp = gp.save_fig(os.path.join(OUT, "_raw_fig6.svg"), type="svg"); L("svg raw=" + str(svgp))
        pngp = gp.save_fig(os.path.join(OUT, "_raw_fig6.png"), type="png", width=K["export"]["png_width"]); L("png raw=" + str(pngp))
        pdfp = gp.save_fig(os.path.join(OUT, "_raw_fig6.pdf"), type="pdf"); L("pdf raw=" + str(pdfp))
    op.exit(); L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())
    try:
        op.exit()
    except Exception:
        pass
print("\n".join(log))
