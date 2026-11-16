r"""Fig. S1  (Protocol W residual-MFNN mixing weights alpha_1 / alpha_2, five within_T seeds)
-- native Origin redraw, house twin of scripts/plot_figs3_origin.py / plot_figs4_origin.py:
  * one data layer (a) in cm units + one canvas layer (lay0) for ALL text
  * every string is placed from an INK-BOX target using per-item anchor->ink offsets
    measured on a dedicated probe page (FS1PROBE=1, then scripts/_z_figs1_measure.py)
  * Origin draws NO ticks and NO tick labels: the twenty-two inward major ticks
    (5 x-ticks on the top+bottom spines, 6 y-ticks on the left+right spines) are
    hand-drawn at the measured rendered length (3.36 pt) with the house thickness
    (0.75 pt), so all four sides of the closed box get identical inward ticks
  * the ten bars are hand-drawn: one closed 5-point rectangle per bar, Fill-Area in
    the branch fill (#E69F00 alpha_1 / #009E73 alpha_2) plus the same rectangle
    stroked 0.6 pt in the branch edge (#A87300 / #006B4E) -- Fig.7/S3/S4 bar recipe
  * the two frozen-mean guides are EXPLICIT dash polylines (-d 0 + hand-dashed
    segments at 5.4/5.4 pt = matplotlib '--' x lw 0.9), never `set plot -1 <style>`
    (that variant hangs Origin 2026 automation); they are drawn AFTER the ten bars so
    they cross the bar bodies exactly like the frozen figure
  * the legend is hand-built in the top-left inside: two 14.0x4.9 swatch rectangles
    (fill+edge identical to the bars) + two Arial strings with Origin subscripts
    \-(1)/\-(2); NO mathtext, NO STIX; the mean-value box of the matplotlib stem is
    GONE (defect 1): no "+/- std" ink anywhere, the numbers live in the Word caption
  * the axis name "Mixing weight" is 9 pt HORIZONTAL (prompt item 5), left-aligned to
    the y tick lane, ink bottom 7 pt above the frame
  * Arial only: plain Arial strings; Greek alpha via Unicode \x(03B1) (proven ArialMT
    on Fig. S4), subscripts via Origin \-( ) markup (proven ArialMT on Fig. S4)

    FS1PROBE=1 python scripts/plot_figs1_origin.py   # text-only calibration page
    python scripts/plot_figs1_origin.py              # production render + .opju
"""
import os, json, csv, re, math, bisect, traceback
import originpro as op

BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(BASE, "outputs", "origin_data")
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
PROBE = os.environ.get("FS1PROBE", "0") == "1"
TAG = "_probe" if PROBE else ""
LOG = os.path.join(OD, "_qa_figs1_render%s.txt" % TAG)
OFF_JSON = os.path.join(OD, "figs1_text_offsets.json")
NAME = "FigS1_alpha_mixing_weights"
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

def dashify(pts, pattern):
    """polyline (design pt) -> dash segments, None-separated, same pt units (fig7 house)."""
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
    out = []
    d = 0.0
    while d < total - 1e-9:
        a = d; b = min(total, d + pattern[0])
        out.append(at(a)); out.append(at(b))
        out.append((None, None))
        d += pattern[0] + pattern[1]
    return out[:-1]

try:
    K = json.load(open(os.path.join(OD, "figs1_origin_constants.json"), encoding="utf-8-sig"))
    fsmap = K["fs_map"]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    DEC = K["decoy"]; DX = DEC["dx"]; DY = DEC["dy"]
    FR = K["frame"]; A = K["layers"]["a"]
    TL = K["tick"]["len_rendered"]
    CANV = K["canvas"]
    L0 = dict(left=CANV["left"], top=CANV["top"], width=CANV["width"], height=CANV["height"])
    FT, FB, FL, FR_ = FR["FT"], FR["FB"], FR["FL"], FR["FR"]
    SX, SY = FR["sx"], FR["sy"]
    BARS = K["bars"]; DASH = K["dashes"]; LEG = K["legend"]; LN = K["lanes"]
    OFFS = {}
    if PROBE:
        L("PROBE mode: text-only calibration page (no data, no frames, no ticks)")
    else:
        if not os.path.exists(OFF_JSON):
            raise RuntimeError("missing " + OFF_JSON + " -- run FS1PROBE=1 then _z_figs1_measure.py")
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
    def coord(it, i, rot):
        if PROBE:
            return hslot(i)
        return anchor(it, OFFS[it["name"]])
    def pt2data(x, y): return (XLO + (x - FL) / SX, YHI - (y - FT) / SY)
    XLO, XHI, YLO, YHI = A["xf"], A["xt"], A["yf"], A["yt"]
    HIT = {it["name"]: it for it in K["horiz"]}

    op.attach()            # this machine blocks COM auto-launch: attach to a running OriginPro 2026
    op.set_show(False)
    op.new()               # clean project: the saved opju holds ONLY this figure
    op.lt_exec("@LCP=2;")   # flat (butt) line end caps for plots, session-only: matches
                            # matplotlib dashes and makes the swatch fill-line exactly 14x4.9
    gp = op.new_graph("FigS1")
    ws = op.new_sheet("w", "DS1")
    ci = [0]
    def add(vals, lname, axis=""):
        ws.from_list(ci[0], vals, lname=lname, axis=axis); ci[0] += 1; return lname
    def axis_style(lay, a):
        lay.lt_exec("layer.%s.ticks=0;layer.%s.minorTicks=0;layer.%s.showlabel=0;"
                    "layer.%s.thickness=0.75;layer.%s.color=color(%d,%d,%d);" %
                    (a, a, a, a, a, int(K["spine"][1:3], 16), int(K["spine"][3:5], 16),
                     int(K["spine" ][5:7], 16)))
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
    def draw_poly(lay, pts_pt, pre, colorhex, width, fill=None, dash=None):
        dd = [pt2data(x, y) if x is not None else (None, None) for x, y in pts_pt]
        xx = add([q[0] for q in dd], pre + "x", "X"); yy = add([q[1] for q in dd], pre + "y", "Y")
        p = lay.add_plot(ws, yy, xx, type="l")
        p.color = COL(colorhex); p.set_cmd("-wp %g" % width, "-d 0")
        if fill is not None:
            lay.lt_exec("{range rr=%s; set rr -pf 1; set rr -pfv 1; set rr -pfb %d;}" %
                        (p.lt_range(), COL(colorhex)))
        return p
    L("boot ok  FL=%.3f FR=%.3f FT=%.3f FB=%.3f sx=%.5f sy=%.5f" % (FL, FR_, FT, FB, SX, SY))

    lay1 = gp[0]; lay0 = gp.add_layer(0)
    L("z-order: lay1=gp[0](data) lay0=gp.add(0)(text canvas)")
    setup(lay1, A)

    if not PROBE:
        # ---------- ten bars: closed 5-point rectangles, fill then edge ----------
        half = BARS["half_pt"]
        for i, b in enumerate(BARS["items"]):
            cx = b["cx_pt"]; ytop = b["top_pt"]; ybot = FB   # base sits ON the bottom spine
            rp = [(cx - half, ybot), (cx + half, ybot), (cx + half, ytop),
                  (cx - half, ytop), (cx - half, ybot)]
            draw_poly(lay1, rp, "bf%d" % i, b["fill"], BARS["pen"], fill=1)
            draw_poly(lay1, rp, "bo%d" % i, b["edge"], BARS["pen"])
            L("bar %d seed %3d alpha_%d centre=%.3f top=%.3f value=%.16f fill=%s edge=%s" %
              (i, b["seed"], b["which"], cx, ytop, b["value"], b["fill"], b["edge"]))
        # ---------- two frozen-mean dashed guides (drawn over the bars, as in the stem) --
        for k, d in enumerate(DASH):
            y = by2y = FB - (d["v"] - YLO) * SY
            seg = dashify([(FL, y), (FR_, y)], d["pattern"])
            draw_poly(lay1, seg, "dh%d" % k, d["color"], d["width"])
            L("dashed guide %d at %.4f y=%.3f nseg=%d pen=%.2f pattern=%s color=%s" %
              (k, d["v"], y, (len(seg) + 1) // 3, d["width"], str(d["pattern"]), d["color"]))
        # ---------- legend swatches (fill + edge, identical recipe to the bars) ----------
        sw = LEG["sw"]
        A1C = K["alpha1"]; A2C = K["alpha2"]
        for k, (fillc, edgec, cd_y) in enumerate(
                ((A1C["fill"], A1C["edge"], LEG["row_c_dy"][0]),
                 (A2C["fill"], A2C["edge"], LEG["row_c_dy"][1]))):
            cx0 = sw["left"]; cy = FT + cd_y
            # swatch BODY = one thick horizontal segment (width = swatch height):
            # Origin's line-plot area fill (-pf) fills UNDER THE CURVE down to the X
            # axis, which is invisible for the bars (base on the axis) but would paint
            # a band under a floating swatch; a thick butt-capped line is the exact
            # 14.0 x 4.9 pt rectangle, then the same closed 5-point polygon is stroked
            # 0.6 pt in the branch edge colour (no fill), as the stem legend shows.
            draw_poly(lay1, [(cx0, cy), (cx0 + sw["w"], cy)], "lsw%d" % k, fillc, sw["h"])
            rp = [(cx0, cy - sw["h"] / 2.0), (cx0 + sw["w"], cy - sw["h"] / 2.0),
                  (cx0 + sw["w"], cy + sw["h"] / 2.0), (cx0, cy + sw["h"] / 2.0),
                  (cx0, cy - sw["h"] / 2.0)]
            draw_poly(lay1, rp, "lse%d" % k, edgec, BARS["pen"])
            L("legend swatch %d rect [%.3f %.3f %.3f %.3f] fill-line w=%.2f edge=%s" %
              (k, cx0, cy - sw["h"] / 2.0, cx0 + sw["w"], cy + sw["h"] / 2.0, sw["h"], edgec))
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
    L("texts horiz=%d (probe forces black)" % len(K["horiz"]))

    lay1.lt_exec("layer.x.from=%g;layer.x.to=%g;layer.y.from=%g;layer.y.to=%g;" % (XLO, XHI, YLO, YHI))
    lay0.lt_exec("layer.x.from=0;layer.x.to=%g;layer.y.from=0;layer.y.to=%g;" % (L0["width"] * PT, L0["height"] * PT))
    for lay in (lay0, lay1): drop_titles(lay)
    for lay, tg in ((lay1, "lay1"), (lay0, "lay0")): kill_legend(lay, tg)
    L("ranges locked, titles dropped")
    if PROBE:
        L("probe pdf=" + str(gp.save_fig(os.path.join(OUT, "_probe_figs1_anchors.pdf"), type="pdf")))
    else:
        opju = os.path.join(OUT, NAME + ".opju")
        op.save(opju); L("opju=" + opju)
        L("svg raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs1.svg"), type="svg")))
        L("png raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs1.png"), type="png", width=K["export"]["png_width"])))
        L("pdf raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs1.pdf"), type="pdf")))
    L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())
print("\n".join(log))
