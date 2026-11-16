r"""Fig. S6  (Al80Cu20 tracer, fixed k=2 anchor reweighting w=1->5->10, dual axes)
-- native Origin 2026 redraw, house twin of scripts/plot_figs4_origin.py (page/canvas/
text recipe), scripts/plot_figs2_origin.py (native line+symbol trajectories) and
scripts/plot_fig6_origin.py (legend handle column):

  * one data layer (a, cm units) + one canvas layer (lay0) for ALL text
  * Origin draws NO native ticks and NO native labels (default theme emits SIMSUN):
    the inward major ticks are hand-drawn -- 3 x-ticks on top+bottom, 7 left-scale
    ticks on the left spine, 6 right-scale ticks on the right spine -- at the measured
    rendered length 3.36 pt, house pen 0.75, colour #333333; the closed 4-side box is
    drawn by Origin with all four axis lines #333333 at 0.75 pt (NOT a blue right spine)
  * data ink (frozen, hardcoded via constants; NOTHING recomputed here):
      - MAPE band: closed polygon f +/- half-width around the frozen points, fill
        #D55E00 transparency 85 % (= the frozen alpha 0.15 fill_between), 0.6 pt edge
      - MAPE polyline #D55E00 1.4 pt (two straight segments, NO smoothing)
      - Factor2 polyline #0072B2 1.4 pt on the RIGHT scale (0.15/1.0/1.0, mapped to
        the left-scale data coords of layer a)
      - circles kind 2 (fill #D55E00 edge #994300) + squares kind 1 (#0072B2/#004D7A),
        sizes from the production-layer symbol calibration
      - frameless legend, centre-right: 14 pt swatch line + marker handle + 7 pt text
  * the three MAPE annotations are ink #994300 7.5 pt, only "122%" "48%" "31%"
  * NO in-figure suptitle (the deleted "Counterfactual k=2 ... (SI only)" wording lives
    in the Word caption only); no panel letter; no Factor2 numbers; no error bars
  * Arial only: \i(w) italic for the x-axis name, NBSP pad for pure-digit labels,
    no mathtext -> no STIX

    F6PROBE=1 python scripts/plot_figs6_origin.py   # text-only calibration page
    python scripts/plot_figs6_origin.py             # production render + .opju
"""
import os, json, re, traceback
import originpro as op

BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(BASE, "outputs", "origin_data")
OUT = os.path.join(BASE, "outputs", "figures_origin")
os.makedirs(OUT, exist_ok=True)
PROBE = os.environ.get("F6PROBE", "0") == "1"
TAG = "_probe" if PROBE else ""
LOG = os.path.join(OD, "_qa_figs6_render%s.txt" % TAG)
OFF_JSON = os.path.join(OD, "figs6_text_offsets.json")
NAME = "FigS6_al80_upweight_w"
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
    K = json.load(open(os.path.join(OD, "figs6_origin_constants.json"), encoding="utf-8-sig"))
    fsmap = K["fs_map"]
    def fsn(fs): return fsmap["%.1f" % fs][2]
    DEC = K["decoy"]; DX = DEC["dx"]; DY = DEC["dy"]
    FRM = K["frame"]; A = K["layers"]["a"]
    TL = K["tick"]["len_rendered"]
    CANV = K["canvas"]
    L0 = dict(left=CANV["left"], top=CANV["top"], width=CANV["width"], height=CANV["height"])
    FT, FB, FL, FR = FRM["FT"], FRM["FB"], FRM["FL"], FRM["FR"]
    SX, SY, SY2 = FRM["sx"], FRM["sy"], FRM["sy2"]
    INK = K["ink"]
    XLO, XHI, YLO, YHI = A["xf"], A["xt"], A["yf"], A["yt"]
    OFFS = {}
    if PROBE:
        L("PROBE mode: text-only calibration page (no data, no frames, no ticks)")
    else:
        if not os.path.exists(OFF_JSON):
            raise RuntimeError("missing " + OFF_JSON + " -- run F6PROBE=1 then _z_figs6_measure.py")
        OFFS = json.load(open(OFF_JSON, encoding="utf-8-sig"))
        L("anchor offsets loaded for %d items" % len(OFFS))
    pr = K["probe"]
    def hslot(i):
        c = i // pr["per_col"]; r = i % pr["per_col"]
        return (pr["x0"] + c * pr["x_step"], pr["y0"] + r * pr["y_step"])
    def rslot(j):
        return (pr["rot_x0"] + j * pr["rot_dx"], pr["rot_y"])
    HIT = {it["name"]: it for it in K["horiz"]}
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
    def pt2data(x, y): return (XLO + (x - FL) / SX, YLO + (FB - y) / SY)

    op.set_show(False)
    gp = op.new_graph("FigS6")
    ws = op.new_sheet("w", "DS6")
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
    def draw_poly(lay, pts_pt, pre, colorhex, width, fill=None, transparency=None,
                  fill_hex=None):
        dd = [pt2data(x, y) if x is not None else (None, None) for x, y in pts_pt]
        xx = add([q[0] for q in dd], pre + "x", "X"); yy = add([q[1] for q in dd], pre + "y", "Y")
        p = lay.add_plot(ws, yy, xx, type="l")
        p.color = COL(colorhex); p.set_cmd("-wp %g" % width, "-d 0")
        if fill is not None:
            lay.lt_exec("{range rr=%s; set rr -pf 1; set rr -pfv 1; set rr -pfb %d;}" %
                        (p.lt_range(), COL(fill_hex if fill_hex else colorhex)))
        if transparency is not None:
            p.transparency = transparency
        return p
    def draw_marks(lay, spec, pre):
        dx = [pt2data(x, y) for x, y in spec["pts"]]
        xx = add([q[0] for q in dx], pre + "x", "X"); yy = add([q[1] for q in dx], pre + "y", "Y")
        p = lay.add_plot(ws, yy, xx, type="s")
        p.symbol_kind = spec["kind"]; p.symbol_size = spec["z"]; p.symbol_interior = 1
        p.set_cmd("-csf %d" % COL(spec["fill"]), "-cse %d" % COL(spec["edge"]), "-kh 6")
        L("marks %s n=%d kind=%d z=%g fill=%s edge=%s" %
          (pre, len(dx), spec["kind"], spec["z"], spec["fill"], spec["edge"]))
        return p
    L("boot ok  FL=%.3f FR=%.3f FT=%.3f FB=%.3f sx=%.5f sy=%.5f sy2=%.5f" % (FL, FR, FT, FB, SX, SY, SY2))

    lay1 = gp[0]; lay0 = gp.add_layer(0)
    L("z-order: lay1=gp[0](data) lay0=gp.add(0)(text canvas)  dx=%g dy=%g" % (DX, DY))
    setup(lay1, A)

    if not PROBE:
        # ---------- MAPE band: Fill-between (type 9) top/bottom chains ----------
        pt_ = draw_poly(lay1, INK["band"]["pts_top"], "bdu", INK["band"]["rim"], INK["band"]["pen"])
        draw_poly(lay1, INK["band"]["pts_bot"], "bdb", INK["band"]["rim"], INK["band"]["pen"])
        pt_.set_fill_area(COL(INK["band"]["fill"]), INK["band"]["fill_between_type"],
                          COL(INK["band"]["fill"]))
        L("band top=%s bot=%s fill=%s rim=%s fill-between=%d (pre-composited 15%% alpha; see constants note)" %
          (str(INK["band"]["pts_top"]), str(INK["band"]["pts_bot"]), INK["band"]["fill"],
           INK["band"]["rim"], INK["band"]["fill_between_type"]))
        # ---------- polylines: line under, symbols over (figs2 recipe) ----------
        for key, pre in (("mape_line", "ml"), ("f2_line", "fl")):
            draw_poly(lay1, INK[key]["pts"], pre, INK[key]["color"], INK[key]["pen"])
            L("poly %s %s pen=%.2f" % (key, pre, INK[key]["pen"]))
        draw_marks(lay1, INK["mape_marks"], "mm")
        draw_marks(lay1, INK["f2_marks"], "fm")
        # ---------- legend: swatch lines + handles (frameless) ----------
        for key, pre in (("leg_line_mape", "lg1"), ("leg_line_f2", "lg2")):
            draw_poly(lay1, INK[key]["pts"], pre, INK[key]["color"], INK[key]["pen"])
        draw_marks(lay1, INK["leg_mark_mape"], "lgm1")
        draw_marks(lay1, INK["leg_mark_f2"], "lgm2")
        L("legend swatch rows at FT+%.1f / FT+%.1f, text left FL+%.1f" %
          (K["legend"]["cy1"], K["legend"]["cy2"], K["legend"]["text_x"]))
        # ---------- hand-drawn inward ticks (four sides, two scales) ----------
        tx = []; ty = []
        for v in A["xticks"]:
            for y0, y1 in ((YHI, YHI - TL / SY), (YLO, YLO + TL / SY)):
                tx += [v, v, None]; ty += [y0, y1, None]
        for v in A["yticks_left"]:
            tx += [XLO, XLO + TL / SX, None]; ty += [v, v, None]
        YR = A["yhi_right"]
        for v in A["yticks_right"]:
            dv = (YHI - YLO) * v / YR + YLO
            tx += [XHI, XHI - TL / SX, None]; ty += [dv, dv, None]
        xx = add(tx, "tkx_a", "X"); yy = add(ty, "tky_a", "Y")
        ptk = lay1.add_plot(ws, yy, xx, type="l")
        ptk.color = COL(K["spine"]); ptk.set_cmd("-wp %g" % K["tick"]["thick"], "-d 0")
        L("ticks n=%d len=%.2f width=%.2f (x %d top+bottom, y-left %d, y-right %d)" %
          (len(tx) // 3, TL, K["tick"]["thick"], len(A["xticks"]) * 2,
           len(A["yticks_left"]), len(A["yticks_right"])))
    else:
        bare(lay1)

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
        L("probe pdf=" + str(gp.save_fig(os.path.join(OUT, "_probe_figs6_anchors.pdf"), type="pdf")))
    else:
        opju = os.path.join(OUT, NAME + ".opju")
        op.save(opju); L("opju=" + opju)
        L("svg raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs6.svg"), type="svg")))
        L("png raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs6.png"), type="png", width=K["export"]["png_width"])))
        L("pdf raw=" + str(gp.save_fig(os.path.join(OUT, "_raw_figs6.pdf"), type="pdf")))
    op.exit(); L("DONE")
except Exception:
    L("EXC " + traceback.format_exc())
    try:
        op.exit()
    except Exception:
        pass
print("\n".join(log))
