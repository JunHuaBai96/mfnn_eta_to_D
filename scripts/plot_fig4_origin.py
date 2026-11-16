import os, json, csv, traceback
import originpro as op
BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(BASE, "outputs", "origin_data")
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
PROBE = os.environ.get("F4PROBE", "0") == "1"
TAG = "_probe" if PROBE else ""
LOG = os.path.join(OD, "_qa_fig4_render%s.txt" % TAG)
OFF_JSON = os.path.join(OD, "fig4_text_offsets.json")
HAT_JSON = os.path.join(OD, "fig4_hat_coords.json")
log = []
def L(s):
    log.append(str(s))
    with open(LOG, "w", encoding="ascii", errors="replace") as f:
        f.write("\n".join(log) + "\n")
def COL(h): return op.ocolor(h)
import re as _re
def fix_txt(name, t):
    t = _re.sub(r"\\x\(([0-9A-Fa-f]{1,6})\)", lambda m: "\\x(%04X)" % int(m.group(1), 16), t)
    if _re.match(r"^[0-9]+$", t):
        t += "\\x(00A0)"
    return t
def rd(name): return list(csv.DictReader(open(os.path.join(OD, name), encoding="utf-8")))
PT = 72.0 / 2.54
L0 = {"left": 0.05, "top": 0.05, "width": 19.0, "height": 13.4}
try:
    K = json.load(open(os.path.join(OD, "fig4_origin_constants.json"), encoding="utf-8"))
    fsmap = K["fs_map"]
    def fsr(fs): return fsmap["%.1f" % fs][1]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    DEC = K["decoy"]; DX = DEC["dx"]; DY = DEC["dy"]
    OFFS = {}
    if PROBE:
        L("PROBE mode: text-only calibration page (no data, no frames, no ticks)")
    else:
        if not os.path.exists(OFF_JSON):
            raise RuntimeError("missing " + OFF_JSON + " -- run with F4PROBE=1 first")
        OFFS = json.load(open(OFF_JSON, encoding="utf-8"))
        L("anchor offsets loaded for %d items" % len(OFFS))
    pr = K["probe"]
    def hslot(i):
        c = i // pr["per_col"]; r = i % pr["per_col"]
        return (pr["x0"] + c * pr["x_step"], pr["y0"] + r * pr["y_step"])
    def rslot(j):
        return (pr["rot_x0"] + j * pr["rot_dx"], pr["rot_y"])
    def anchor_h(it, o):
        al = it.get("align", "pen")
        if al == "pen":    return (it["Lx"] - o["ox"], it["By"] - o["oy"])
        if al == "left":   return (it["tx"] - o["jx0"], it["By"] - o["oy"])
        if al == "right":  return (it["tx"] - o["jx1"], it["By"] - o["oy"])
        if al == "center": return (it["tx"] - 0.5 * (o["jx0"] + o["jx1"]), it["By"] - o["oy"])
        raise ValueError("bad align " + al)
    def anchor_r(it, o):
        ax = it["bx"] - o["ox"] if it.get("align_x", "pen") == "pen" else it["tx"] - 0.5 * (o["jx0"] + o["jx1"])
        ay = it["ps"] - o["oy"] if it.get("align_y", "pen") == "pen" else it["ty"] - 0.5 * (o["jy0"] + o["jy1"])
        return (ax, ay)
    def coord_h(it, i):
        if PROBE: return hslot(i)
        return anchor_h(it, OFFS[it["name"]])
    def coord_r(it, j):
        if PROBE: return rslot(j)
        return anchor_r(it, OFFS[it["name"]])
    op.set_show(False)
    gp = op.new_graph("Fig4")
    ws = op.new_sheet("w", "D4")
    ci = [0]
    def add(vals, lname, axis=""):
        ws.from_list(ci[0], vals, lname=lname, axis=axis); ci[0] += 1; return lname
    def numlist(rows, key):
        return [None if (r[key] == "" or r[key] is None) else float(r[key]) for r in rows]
    def axis_style(lay, a):
        lay.lt_exec("layer.%s.ticks=1;layer.%s.minorTicks=0;layer.%s.ticklength=3.6;layer.%s.tickthickness=0.75;"
                    "layer.%s.color=color(51,51,51);layer.%s.thickness=0.75;layer.%s.showlabel=0;" % (a, a, a, a, a, a, a))
    def bare(lay):
        "PROBE: no frame / no tick marks, so the ink windows only ever see text"
        lay.lt_exec("layer.showframe=0;")
        for a in ("x", "x2", "y", "y2"):
            lay.lt_exec("layer.%s.ticks=0;" % a)
        lgb = lay.label("legend")
        if lgb is not None: lgb.remove()
    def drop_titles(lay):
        for nm in ("xb", "xt", "yl", "yr"):
            try:
                lb = lay.label(nm)
                if lb is not None: lb.remove()
            except Exception: pass
    def kill_legend(lay, tag):
        "Origin auto-creates a bordered legend box when plots are added; the"
        "reference figure has no such box, so drop it once plots exist."
        try:
            lb = lay.label("legend")
            if lb is None:
                L("legend[%s]: none" % tag); return
            lb.remove()
            L("legend[%s]: removed" % tag)
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
    lay1 = gp[0]; lay2 = gp.add_layer(0); lay0 = gp.add_layer(0)
    L("z-order: lay1=gp[0](A) lay2=add(A) lay0=add(text/top)  dx=%g dy=%g" % (DX, DY))

    # ---------- Panel A ----------
    A = K["layers"]["a"]
    lay1.activate()
    lay1.lt_exec("layer.unit=3;")
    lay1.lt_exec("layer.left=%g;layer.top=%g;layer.width=%g;layer.height=%g;" % (A["left"], A["top"], A["width"], A["height"]))
    lay1.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.x.inc=%g;layer.x.firstTick=%g;" % (A["xf"], A["xt"], A["xi"], A["xfirst"]))
    lay1.lt_exec("layer.y.from=%g;layer.y.to=%g;layer.y.inc=%g;layer.y.firstTick=%g;" % (A["yf"], A["yt"], A["yi"], A["yfirst"]))
    for a in ("x", "x2", "y", "y2"): axis_style(lay1, a)
    if not PROBE:
        ga = rd("fig4_panelA_guide_dashpath.csv")
        dx_ = add(numlist(ga, "x"), "dashx", "X"); dy_ = add(numlist(ga, "y"), "dashy", "Y")
        pdl = lay1.add_plot(ws, dy_, dx_, type="l"); pdl.color = COL(K["ref"])
        pdl.set_cmd("-wp %g" % K["guide_dash"]["width"], "-d 0")   # solid pen, dashes come from the path
        M = K["markers"]
        def scat(lay, csvname, gpre, pre):
            rows = rd(csvname)
            xx = add([float(r["x"]) for r in rows], pre + "x", "X"); yy = add([float(r["y"]) for r in rows], pre + "y", "Y")
            m = M[gpre]
            p = lay.add_plot(ws, yy, xx, type="s")
            p.symbol_kind = m["kind"]; p.symbol_size = m["z"]; p.symbol_interior = 1
            p.set_cmd("-csf %d" % COL(m["fill"]), "-cse %d" % COL(m["edge"]), "-kh 6")
            if m.get("transparency"): p.transparency = m["transparency"]
            return p
        scat(lay1, "fig4_panelA_hf.csv", "HF_only", "hf")
        scat(lay1, "fig4_panelA_mfnn.csv", "MFNN", "ma")
    else:
        bare(lay1)
    L("panel A done")

    # ---------- Panel B ----------
    Bs = K["layers"]["b"]
    lay2.activate()
    lay2.lt_exec("layer.unit=3;")
    lay2.lt_exec("layer.left=%g;layer.top=%g;layer.width=%g;layer.height=%g;" % (Bs["left"], Bs["top"], Bs["width"], Bs["height"]))
    lay2.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.x.inc=%g;layer.x.firstTick=%g;" % (Bs["xf"], Bs["xt"], Bs["xi"], Bs["xfirst"]))
    lay2.lt_exec("layer.y.from=%g;layer.y.to=%g;layer.y.inc=%g;layer.y.firstTick=%g;" % (Bs["yf"], Bs["yt"], Bs["yi"], Bs["yfirst"]))
    for a in ("x", "x2", "y", "y2"): axis_style(lay2, a)
    if not PROBE:
        gb = rd("fig4_panelB_guides.csv")
        def part(nm): return [r for r in gb if r["part"] == nm]
        bu = part("band_upper"); bl = part("band_lower"); zr = part("zero")
        bxx = add(numlist(bu, "x"), "bandx", "X")
        buy = add(numlist(bu, "y"), "banduy", "Y"); ply = lay2.add_plot(ws, buy, bxx, type="l")
        ply.color = COL(K["band"]); ply.set_cmd("-wp 0.6", "-d 0")
        ply.set_fill_area(op.ocolor(K["band"]), 9, op.ocolor(K["band"]))
        bly = add(numlist(bl, "y"), "bandly", "Y"); plz = lay2.add_plot(ws, bly, bxx, type="l")
        plz.color = COL(K["band"]); plz.set_cmd("-wp 0.6", "-d 0")
        zxx = add(numlist(zr, "x"), "zerx", "X"); zyy = add(numlist(zr, "y"), "zery", "Y")
        pz = lay2.add_plot(ws, zyy, zxx, type="l"); pz.color = COL(K["dark"]); pz.set_cmd("-wp 0.8", "-d 0")
        scat(lay2, "fig4_panelB_mfnn.csv", "MFNN", "mb")
    else:
        bare(lay2)
    L("panel B done")

    # ---------- lay0 : text / handle / hat canvas ----------
    cfg_canvas(lay0)
    if not PROBE:
        for i, h in enumerate(K["legend_handles"]):
            hx = add([h["cx"] + DX], "lghx%d" % i, "X"); hy = add([DY - h["cy"]], "lghy%d" % i, "Y")
            ph = lay0.add_plot(ws, hy, hx, type="s")
            ph.symbol_kind = h["kind"]; ph.symbol_size = h["z"]; ph.symbol_interior = 1
            ph.set_cmd("-csf %d" % COL(h["fill"]), "-cse %d" % COL(h["edge"]), "-kh 6")
            if h.get("transparency"): ph.transparency = h["transparency"]
        hats = K["hats"]
        if os.path.exists(HAT_JSON):
            hats = json.load(open(HAT_JSON, encoding="utf-8"))
            L("hat coords overridden from fig4_hat_coords.json")
        for i, ht in enumerate(hats):
            hxx = add([p[0] + DX for p in ht["pts"]], "htx%d" % i, "X")
            hyy = add([DY - p[1] for p in ht["pts"]], "hty%d" % i, "Y")
            php = lay0.add_plot(ws, hyy, hxx, type="l")
            php.color = COL(ht.get("color", "#222222")); php.set_cmd("-wp 0.6", "-d 0")
        L("lay0 handles=%d hats=%d" % (len(K["legend_handles"]), len(hats)))
        # ---------- top/right tick marks ----------
        # Origin only ever renders tick marks on the bottom (x) and left (y)
        # spines of these layers -- layer.x2/.y2.ticks / .ticklength are no-ops
        # (verified with scripts/_z21_tickprobe.py: values 1/2/3 all draw
        # nothing).  The reference has inward ticks on all four spines, so the
        # missing top/right ticks are drawn on the overlay canvas.
        #
        # They are placed from MEASURED anchors (scripts/_z31_tickmap.py on the
        # rendered pdf) rather than the ideal design-space formula: the overlay
        # canvas carries a small systematic offset (+0.46pt in x, +0.74pt in y)
        # plus ~0.1pt quantisation jitter, which the per-item text/hat offsets
        # absorb but raw line work does not.  Using the measured spine and
        # bottom/left tick positions guarantees the new ticks land exactly on
        # the spines and line up with the opposite spine's ticks, as in the
        # reference.  inv is the least-squares fit of that page map.
        TK = K.get("ticks_extra", {})
        TL = float(TK.get("length", 3.36))
        TW = float(TK.get("width", 0.75))
        TC = TK.get("color", "#333333")
        INV = TK["inv"]; TG = TK["targets_final"]
        def to_page(fx, fy):
            dx_ = (fx - INV["x"][0]) / INV["x"][1]
            dy_ = (fy - INV["y"][0]) / INV["y"][1]
            return dx_ + DX, DY - dy_
        tkx = []; tky = []
        for key in ("a", "b"):
            t = TG[key]
            for fx in t["xticks"]:                      # top spine, inward
                u0, v0 = to_page(fx, t["y0"])
                _d, v1 = to_page(fx, t["y0"] + TL)
                tkx += [u0, u0, None]; tky += [v0, v1, None]
            for fy in t["yticks"]:                      # right spine, inward
                u0, v0 = to_page(t["x1"], fy)
                u1, _d = to_page(t["x1"] - TL, fy)
                tkx += [u0, u1, None]; tky += [v0, v0, None]
        tkxa = add(tkx, "tkx", "X"); tkya = add(tky, "tky", "Y")
        ptk = lay0.add_plot(ws, tkya, tkxa, type="l")
        ptk.color = COL(TC); ptk.set_cmd("-wp %g" % TW, "-d 0")
        L("lay0 extra ticks=%d len=%g width=%g color=%s" % (len(tkx) // 3, TL, TW, TC))
    else:
        L("PROBE: handles/hats skipped")
    lay0.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" % (L0["width"] * PT, L0["height"] * PT))

    for i, h in enumerate(K["horiz"]):
        cxp, cyp = coord_h(h, i)
        place(cxp, cyp, "T_" + h["name"], fix_txt(h["name"], h["txt"]), h["fs"], h["color"])
    for j, r in enumerate(K["rot"]):
        cxp, cyp = coord_r(r, j)
        place(cxp, cyp, "T_" + r["name"], fix_txt(r["name"], r["txt"]), r["fs"], r["color"], rotate=True)
    L("texts horiz=%d rot=%d" % (len(K["horiz"]), len(K["rot"])))

    lay1.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" % (A["xf"], A["xt"], A["yf"], A["yt"]))
    lay2.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" % (Bs["xf"], Bs["xt"], Bs["yf"], Bs["yt"]))
    lay0.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" % (L0["width"] * PT, L0["height"] * PT))
    for lay in (lay0, lay1, lay2): drop_titles(lay)
    L("ranges locked, titles dropped")
    for lay, tg in ((lay1, "lay1"), (lay2, "lay2"), (lay0, "lay0")):
        kill_legend(lay, tg)
    if PROBE:
        pdfp = gp.save_fig(os.path.join(OUT, "_probe_fig4_anchors.pdf"), type="pdf")
        L("probe pdf=" + str(pdfp))
    else:
        opju = os.path.join(OUT, "Fig4_protocol_W_residual_topology.opju")
        op.save(opju); L("opju=" + opju)
        svgp = gp.save_fig(os.path.join(OUT, "_raw.svg"), type="svg"); L("svg raw=" + str(svgp))
        pngp = gp.save_fig(os.path.join(OUT, "_raw.png"), type="png", width=6433); L("png raw=" + str(pngp))
        pdfp = gp.save_fig(os.path.join(OUT, "_raw.pdf"), type="pdf"); L("pdf raw=" + str(pdfp))
    op.exit(); L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())
