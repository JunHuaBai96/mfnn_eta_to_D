import os, json, csv, math, traceback
import originpro as op
BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(BASE, "outputs", "origin_data")
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
LOG = os.path.join(OD, "_qa_fig3_render.txt")
EMIT_CONTROLS = os.environ.get("F3CTRL", "1") == "1"
B = chr(92); MN = B + "x(2212)"
log = []
def L(s):
    log.append(str(s))
    with open(LOG, "w", encoding="ascii", errors="replace") as f:
        f.write("\n".join(log) + "\n")
def COL(h): return op.ocolor(h)
import re as _re
def fix_txt(name, t):
    t = _re.sub(r"\\x\(([0-9A-Fa-f]{1,6})\)", lambda m: "\\x(%04X)" % int(m.group(1), 16), t)
    if name == "a_ytitle":
        t = t.replace("`n", "")
    if _re.match(r"^[0-9]+$", t):
        t += "\\x(00A0)"
    return t
def rd(name): return list(csv.DictReader(open(os.path.join(OD, name), encoding="utf-8")))
# panel-a canvas<->data transforms
AX0, AY1, XSPAN, YSPAN = 39.80125, 141.915361, 89.2915, 78.0300
def a_cy2dy(cy): return -9.2 + (AY1 - cy) / YSPAN
try:
    K = json.load(open(os.path.join(OD, "fig3_origin_constants.json"), encoding="utf-8"))
    K["decoy"]["basey"] = float(os.environ.get("F3BASEY", "0.87"))
    fsmap = K["fs_map"]
    def fsr(fs): return fsmap["%.1f" % fs][1]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    op.set_show(False)
    gp = op.new_graph("Fig3")
    ws = op.new_sheet("w", "D3")
    ci = [0]
    def add(vals, lname, axis=""):
        ws.from_list(ci[0], vals, lname=lname, axis=axis); ci[0] += 1; return lname
    def numlist(rows, key):
        return [None if (r[key] == "" or r[key] is None) else float(r[key]) for r in rows]
    def axis_style(lay, a):
        lay.lt_exec("layer.%s.ticks=1;layer.%s.minorTicks=0;layer.%s.ticklength=3.6;layer.%s.tickthickness=0.75;"
                    "layer.%s.color=color(51,51,51);layer.%s.thickness=0.75;layer.%s.showlabel=0;" % (a, a, a, a, a, a, a))

    # ---------- L0 decoy ----------
    lay0 = gp[0]; lay0.activate()
    lay0.lt_exec("layer.unit=3;")
    PT = 72.0 / 2.54
    lay0.lt_exec("layer.left=0.05;layer.top=0.05;layer.width=19.0;layer.height=13.4;")
    lay0.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" % (19*PT, 13.4*PT))
    for a in ("x", "x2", "y", "y2"):
        lay0.lt_exec("layer.%s.ticks=0;layer.%s.minorTicks=0;layer.%s.showlabel=0;layer.%s.thickness=0;" % (a, a, a, a))
    lb0 = lay0.label("legend")
    if lb0 is not None: lb0.remove()
    DX, DY = K["decoy"]["dx"], K["decoy"]["dy"]
    def place(cx, cy, name, txt, fs, color, rotate=False):
        u = cx + DX; v = DY - cy
        lay0.lt_exec('label -a %g %g -n %s "%s";' % (u, v, name, txt))
        lay0.lt_exec("%s.fsize=%g;%s.font=font(arial);%s.color=color(%d,%d,%d);" %
                     (name, fsn(fs), name, name, int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)))
        if rotate: lay0.lt_exec("%s.rotate=90;" % name)
    def drop_titles(lay):
        for nm in ("xb", "xt", "yl", "yr"):
            try:
                lb = lay.label(nm)
                if lb is not None: lb.remove()
            except Exception: pass
    # Origin cannot draw U+0302 combining hat -> small polyline over the D of panel-A y title
    lay0.lt_exec("layer.sauto=0;")
    HP = [(4.6, 102.82), (2.6, 105.32), (4.6, 107.82)]
    hxx = add([cx + DX for cx, cy in HP], "hatx"); hyy = add([DY - cy for cx, cy in HP], "haty")
    ph = lay0.add_plot(ws, hyy, hxx, type="l"); ph.color = COL("#222222"); ph.set_cmd("-wp 0.6", "-d 0")
    lay0.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" % (19 * PT, 13.4 * PT))
    L("L0 ready controls=%s hat=on" % EMIT_CONTROLS)

    # ---------- Panel A ----------
    A = K["layers"]["a"]; lay1 = gp.add_layer(0); lay1.activate()
    lay1.lt_exec("layer.unit=3;")
    lay1.lt_exec("layer.left=%g;layer.top=%g;layer.width=%g;layer.height=%g;" % (A["left"], A["top"], A["width"], A["height"]))
    lay1.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.x.inc=%g;layer.x.firstTick=%g;" % (A["xf"], A["xt"], A["xi"], A["xfirst"]))
    lay1.lt_exec("layer.y.from=%g;layer.y.to=%g;layer.y.inc=%g;layer.y.firstTick=%g;" % (A["yf"], A["yt"], A["yi"], A["yfirst"]))
    for a in ("x", "x2", "y", "y2"): axis_style(lay1, a)
    SP = K["spine"]; TK = K["tick"]["len_nom"]; TW = K["tick"]["thick"]
    bands = rd("fig3_parity_reference_lines.csv")
    bx = add(numlist(bands, "x"), "bandx", "X")
    bu = add(numlist(bands, "band_upper"), "bandu", "Y")
    bl = add(numlist(bands, "band_lower"), "bandl", "Y")
    idn = add(numlist(bands, "identity"), "ident", "Y")
    pbu = lay1.add_plot(ws, bu, bx, type="l"); pbu.color = COL(K["band"]); pbu.set_cmd("-wp 0.6", "-d 0")
    pbl = lay1.add_plot(ws, bl, bx, type="l"); pbl.color = COL(K["band"]); pbl.set_cmd("-wp 0.6", "-d 0")
    pbu.set_fill_area(op.ocolor(K["band"]), 9, op.ocolor(K["band"]))
    pi = lay1.add_plot(ws, idn, bx, type="l"); pi.color = COL(SP); pi.set_cmd("-wp 1.15")
    eb = rd("fig3_parity_errorbar_paths.csv")
    edgecol = dict(LF_only="#A87300", HF_only="#004D7A", MFNN="#006B4E")
    for g in ("LF_only", "HF_only", "MFNN"):
        rows = [r for r in eb if r["group"] == g]
        ex = add(numlist(rows, "x"), "eax_" + g, "X"); ey = add(numlist(rows, "y"), "eay_" + g, "Y")
        pe = lay1.add_plot(ws, ey, ex, type="l"); pe.color = COL(edgecol[g]); pe.set_cmd("-wp 1.0")
    pts = rd("fig3_parity_points.csv"); M = K["markers"]
    for g in ("LF_only", "HF_only", "MFNN"):
        f = [r for r in pts if r["group"] == g and r["subset"] == "filled"]
        o = [r for r in pts if r["group"] == g and r["subset"] == "open"]
        fill = M[g]["fill"]; edge = M[g]["edge"]; z = M[g]["z"]; kd = M[g]["kind"]
        fx = add([float(r["x"]) for r in f], "fx_" + g, "X"); fy = add([float(r["y"]) for r in f], "fy_" + g, "Y")
        ps = lay1.add_plot(ws, fy, fx, type="s"); ps.symbol_kind = kd; ps.symbol_size = z; ps.symbol_interior = 1
        ps.set_cmd("-csf %d" % COL(fill), "-cse %d" % COL(edge), "-kh 6")
        ox = add([float(r["x"]) for r in o], "ox_" + g, "X"); oy = add([float(r["y"]) for r in o], "oy_" + g, "Y")
        pv = lay1.add_plot(ws, oy, ox, type="s"); pv.symbol_kind = kd; pv.symbol_size = z; pv.symbol_interior = 2
        pv.set_cmd("-cse %d" % COL(edge), "-kh 6")
    LG = K["legend"]; gxv = LG["gx_data"]
    for i, it in enumerate(LG["items"]):
        gy = add([a_cy2dy(it["cy"])], "lgy%d" % i, "Y"); gx = add([gxv], "lgx%d" % i, "X")
        if it.get("interior", 0) == 0 and "edge" in it:
            pk = lay1.add_plot(ws, gy, gx, type="s"); pk.symbol_kind = it["kind"]; pk.symbol_size = it["z"]
            pk.symbol_interior = 1
            pk.set_cmd("-csf %d" % COL(it["fill"]), "-cse %d" % COL(it["edge"]), "-kh 6")
        else:
            pk = lay1.add_plot(ws, gy, gx, type="s"); pk.symbol_kind = it["kind"]; pk.symbol_size = it["z"]
            pk.symbol_interior = 2
            pk.set_cmd("-cse %d" % COL(it["color"] if "color" in it else it["edge"]), "-kh 6")
    # SKIP_CALLOUT_BOX: keep R2 text (cal1/cal2) but do not draw green rectangle / white fill
    if os.environ.get("FIG3_DRAW_CALLOUT_BOX", "0") == "1":
        co = rd("fig3_callout_paths.csv")
        fb = [r for r in co if r["part"] == "fill"]; fb2 = [r for r in co if r["part"] == "fill2"]; st = [r for r in co if r["part"] == "stroke"]
        cx1 = add(numlist(fb, "x"), "coxb", "X"); cy1 = add(numlist(fb, "y"), "coyb", "Y")
        cx2 = add(numlist(fb2, "x"), "coxt", "X"); cy2 = add(numlist(fb2, "y"), "coyt", "Y")
        pc1 = lay1.add_plot(ws, cy1, cx1, type="l"); pc1.color = COL("#FFFFFF"); pc1.set_cmd("-wp 0.6", "-d 0")
        pc2 = lay1.add_plot(ws, cy2, cx2, type="l"); pc2.color = COL("#FFFFFF"); pc2.set_cmd("-wp 0.6", "-d 0")
        pc1.set_fill_area(op.ocolor("#FFFFFF"), 9, op.ocolor("#FFFFFF"))
        sx = add(numlist(st, "x"), "cosx", "X"); sy = add(numlist(st, "y"), "cosy", "Y")
        pc3 = lay1.add_plot(ws, sy, sx, type="l"); pc3.color = COL(K["callout"]["stroke"]); pc3.set_cmd("-wp 0.75")
    else:
        L("callout box skipped (text only)")
    L("panel A done")

    def setup_bc(Lspec, ylo, yhi, yinc):
        lay = gp.add_layer(0); lay.activate()
        lay.lt_exec("layer.unit=3;")
        lay.lt_exec("layer.left=%g;layer.top=%g;layer.width=%g;layer.height=%g;" % (Lspec["left"], Lspec["top"], Lspec["width"], Lspec["height"]))
        lay.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.x.inc=%g;layer.x.firstTick=%g;" % (Lspec["xf"], Lspec["xt"], Lspec["xi"], Lspec["xfirst"]))
        lay.lt_exec("layer.y.from=%g;layer.y.to=%g;layer.y.inc=%g;" % (ylo, yhi, yinc))
        for a in ("x", "x2", "y", "y2"): axis_style(lay, a)
        return lay
    layB = setup_bc(K["layers"]["b"], 0, K["layers"]["b"]["yt"], 25)
    layC = setup_bc(K["layers"]["c"], 0, 1.25, 0.2)
    def bars(lay, csvname, pre):
        rows = rd(csvname); xi = {"LF-only":0.0,"HF-only":1.0,"MFNN":2.0}
        by = add([float(r["value"]) for r in rows], pre+"v", "Y")
        bxx = add([xi[r["group"]] for r in rows], pre+"x", "X")
        pcol = lay.add_plot(ws, by, bxx, type="c"); pcol.color = COL(SP); pcol.set_cmd("-vg 48", "-pbs 0", "-vw 0.9")
        faces = ["#E69F00", "#0072B2", "#009E73"]; edges = ["#A87300", "#004D7A", "#006B4E"]
        for i in range(3):
            pcol.set_cmd("%d -pfb %d" % (i+1, COL(faces[i])), "%d -pbc %d" % (i+1, COL(edges[i])))
    bars(layB, "fig3_metrics_mape.csv", "mb"); bars(layC, "fig3_metrics_factor2.csv", "mc")
    be = rd("fig3_bar_errorbar_paths.csv")
    # Each bar error mark is plotted as TWO independent line plots (stem+bottom-cap,
    # top-cap) so Origin cannot connect segments ACROSS bars (the diagonal defect).
    for lay, pn in ((layB, "b"), (layC, "c")):
        datar = [r for r in be if r["panel"] == pn]   # 18 rows = 3 bars x 6; blank separators dropped
        for bi in range(3):
            blk = datar[bi*6:(bi+1)*6]
            sa, sb = blk[0:4], blk[4:6]
            ax = add([float(r["x"]) for r in sa], "bex_%s%d_a" % (pn, bi), "X")
            ay = add([float(r["y"]) for r in sa], "bey_%s%d_a" % (pn, bi), "Y")
            pa = lay.add_plot(ws, ay, ax, type="l"); pa.color = COL(K["dark"]); pa.set_cmd("-wp 0.9")
            bx = add([float(r["x"]) for r in sb], "bex_%s%d_b" % (pn, bi), "X")
            by = add([float(r["y"]) for r in sb], "bey_%s%d_b" % (pn, bi), "Y")
            pbb = lay.add_plot(ws, by, bx, type="l"); pbb.color = COL(K["dark"]); pbb.set_cmd("-wp 0.9")
    dash = rd("fig3_panel_c_dashline_paths.csv")
    dxx = add(numlist(dash, "x"), "dashx", "X"); dyy = add(numlist(dash, "y"), "dashy", "Y")
    pdl = layC.add_plot(ws, dyy, dxx, type="l"); pdl.color = COL("#7F7F7F"); pdl.set_cmd("-wp 0.9")
    L("panels B/C done")
    lay1.lt_exec("layer.x.from=-9.2;layer.x.to=-7.6;layer.y.from=-9.2;layer.y.to=-7.6;")
    layB.lt_exec("layer.x.from=-0.51825;layer.x.to=2.51825;layer.y.from=0;layer.y.to=%g;" % K["layers"]["b"]["yt"])
    layC.lt_exec("layer.x.from=-0.51825;layer.x.to=2.51825;layer.y.from=0;layer.y.to=1.25;")

    for h in K["horiz"]:
        cxp = h["Lx"] - K["decoy"]["adv"]; cyp = h["By"] - K["decoy"]["basey"]
        place(cxp, cyp, "T_" + h["name"], fix_txt(h["name"], h["txt"]), h["fs"], h["color"])
    for r in K["rot"]:
        fsR = fsr(r["fs"]); Lm = r["Lref"] * fsR / r["fs"]
        A_x = r["bx"] - 0.643 * fsR
        A_y = r["cy"] - Lm / 2
        place(A_x, A_y, "T_" + r["name"], fix_txt(r["name"], r["txt"]), r["fs"], r["color"], rotate=True)
        if EMIT_CONTROLS:
            place(250.0, 210.0, "CTRL_" + r["name"], "MW-" + r["name"][:4], r["fs"], "#FF0000", rotate=True)
            place(270.0, 210.0, "CTRH_" + r["name"], "12-" + r["name"][:4], r["fs"], "#0000FF")
    L("texts horiz=%d rot=%d" % (len(K["horiz"]), len(K["rot"])))

    for lay in (lay0, lay1, layB, layC): drop_titles(lay)
    L("titles dropped")
    opju = os.path.join(OUT, "Fig3_protocol_W_parity_metrics.opju")
    op.save(opju); L("opju=" + opju)
    svgp = gp.save_fig(os.path.join(OUT, "_raw.svg"), type="svg"); L("svg raw=" + str(svgp))
    pngp = gp.save_fig(os.path.join(OUT, "_raw.png"), type="png", width=6433); L("png raw=" + str(pngp))
    pdfp = gp.save_fig(os.path.join(OUT, "_raw.pdf"), type="pdf"); L("pdf raw=" + str(pdfp))
    op.exit(); L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())


