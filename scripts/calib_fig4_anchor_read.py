"""Read the Origin probe PDF -> per-item anchor offsets AND real ink extents.

probe PDF: only the 28 calibration texts (+ decoy marker grid) are drawn, each text sits
at its grid slot anchor.  Mapping: PDF = design + (pdfx, pdfy), 1 pt = 1 pt.

For every item we report, relative to the slot ANCHOR (design pt):
  ox, oy    : pen x   / baseline y            (what Origin's "label -a" anchor means)
  jx0, jx1  : left / right INK edge           (pixel-measured, 8x magnification)
  jy0, jy1  : top  / bottom INK edge
Rotated items (dir = (0,-1)) additionally give the ink cross-axis band and the
along-line extent, expressed in the same anchor-relative frame.

Writes fig4_text_offsets.json  and  _qa_fig4_anchor_offsets.txt (ASCII).
"""
import os, json, fitz, numpy as np
B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PROBE = os.path.join(B, "outputs", "figures_origin", "_probe_fig4_anchors.pdf")
K = json.load(open(os.path.join(OD, "fig4_origin_constants.json"), encoding="utf-8"))
PDFX, PDFY = K["decoy"]["pdfx"], K["decoy"]["pdfy"]
pr = K["probe"]
M = 8.0                                    # raster magnification for ink measurement

doc = fitz.open(PROBE); pg = doc[0]
pm = pg.get_pixmap(matrix=fitz.Matrix(M, M), alpha=False)
arr = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)
dark = arr[:, :, 0].astype(int) < 200
print("probe page %.3f x %.3f  raster %dx%d" % (pg.mediabox.width, pg.mediabox.height, pm.width, pm.height))

# ---- all lines (not spans): sub/superscripts live on their own lines ----
lines = []
for b in pg.get_text("dict")["blocks"]:
    for l in b.get("lines", []):
        dx, dy = l["dir"]
        sp = l["spans"]
        szs = [s["size"] for s in sp]
        msl = [o for o, z in zip(sp, szs) if z >= 0.85*max(szs)]
        lines.append(dict(dx=dx, dy=dy, rot=abs(dx) < 0.05,
                          penx=min(s["origin"][0] for s in msl),
                          base=max(s["origin"][1] for s in msl),
                          x0=min(s["bbox"][0] for s in sp), x1=max(s["bbox"][2] for s in sp),
                          y0=min(s["bbox"][1] for s in sp), y1=max(s["bbox"][3] for s in sp),
                          size=max(szs),
                          txt="".join(s["text"] for s in sp)))
nh = [l for l in lines if not l["rot"]]
nr = [l for l in lines if l["rot"]]

def hslot(i):
    c = i // pr["per_col"]; r = i % pr["per_col"]
    return (pr["x0"] + c*pr["x_step"], pr["y0"] + r*pr["y_step"])
def rslot(j):
    return (pr["rot_x0"] + j*pr["rot_dx"], pr["rot_y"])

def inkbox(x0, y0, x1, y1):
    ix0 = max(int(np.floor(x0*M)), 0); iy0 = max(int(np.floor(y0*M)), 0)
    ix1 = min(int(np.ceil(x1*M)), pm.width-1); iy1 = min(int(np.ceil(y1*M)), pm.height-1)
    sub = dark[iy0:iy1+1, ix0:ix1+1]
    ys, xs = np.nonzero(sub)
    if not len(xs): return None
    return dict(x0=(ix0+xs.min())/M, x1=(ix0+xs.max())/M, y0=(iy0+ys.min())/M, y1=(iy0+ys.max())/M,
                n=len(xs), touch=(xs.min() == 0 or xs.max() == ix1-ix0 or ys.min() == 0 or ys.max() == iy1-iy0))

res = {}
out = ["probe ink calibration  M=%.1f  nlines=%d (horiz %d / rot %d)" % (M, len(lines), len(nh), len(nr))]
miss = []
for i, it in enumerate(K["horiz"]):
    ax, ay = hslot(i); axp, ayp = ax + PDFX, ay + PDFY
    # line-level match window (validated in handoff 6): pen x within 8, baseline within [-4, +19]
    cands = [l for l in nh if abs(l["penx"] - axp) <= 8.0 and -4.0 <= l["base"] - ayp <= 19.0]
    if not cands:
        out.append("MISS  %-11s anchor=%8.3f,%8.3f" % (ascii(it["name"]), axp, ayp)); miss.append(it["name"]); continue
    main = [l for l in cands if l["size"] >= 0.85*max(z["size"] for z in cands)]
    # slot window for the ink: everything that belongs to this text (main + sub/super lines)
    win = (axp - 6.0, ayp - 3.0, axp + pr.get("hwin", 150.0), ayp + 17.0)
    ii = inkbox(*win)
    pen = min(l["penx"] for l in main); base = max(l["base"] for l in main)
    if ii is None:
        out.append("NOINK %-11s" % ascii(it["name"])); miss.append(it["name"]); continue
    # trim: ignore ink beyond 150pt / other slot artefacts
    res[it["name"]] = dict(ox=round(pen - axp, 4), oy=round(base - ayp, 4),
                           jx0=round(ii["x0"] - axp, 4), jx1=round(ii["x1"] - axp, 4),
                           jy0=round(ii["y0"] - ayp, 4), jy1=round(ii["y1"] - ayp, 4),
                           n=ii["n"], fs=max(l["size"] for l in cands), nlines=len(cands))
    out.append("H %-11s anchor=%7.2f,%7.2f ox=%+7.3f oy=%+7.3f | ink jx0=%+7.3f jx1=%+7.3f (w=%6.3f) "
               "jy0=%+7.3f jy1=%+7.3f (h=%5.3f) | n=%5d nlines=%2d fs=%5.2f %s | %s" %
               (ascii(it["name"]), axp, ayp, res[it["name"]]["ox"], res[it["name"]]["oy"],
                res[it["name"]]["jx0"], res[it["name"]]["jx1"], res[it["name"]]["jx1"]-res[it["name"]]["jx0"],
                res[it["name"]]["jy0"], res[it["name"]]["jy1"], res[it["name"]]["jy1"]-res[it["name"]]["jy0"],
                ii["n"], len(cands), max(l["size"] for l in cands),
                "TOUCH!" if ii["touch"] else "     ",
                ascii("|".join(l["txt"].strip() for l in sorted(cands, key=lambda z: (z["base"], z["penx"])))[:46])))
for j, it in enumerate(K["rot"]):
    ax, ay = rslot(j); axp, ayp = ax + PDFX, ay + PDFY
    # rotated runs: group by CROSS-AXIS only (the run's baseline x); the string
    # starts at the bottom (largest y) and advances upward, so y is not a filter.
    cands = [l for l in nr if abs(l["penx"] - axp) <= 20.0]
    if not cands:
        out.append("MISS  %-11s rot anchor=%8.3f,%8.3f" % (ascii(it["name"]), axp, ayp)); miss.append(it["name"]); continue
    main = [l for l in cands if l["size"] >= 0.85*max(z["size"] for z in cands)]
    win = (axp - 14.0, ayp - 20.0, axp + 22.0, ayp + 160.0)
    ii = inkbox(*win)
    base = max(l["penx"] for l in main)          # cross-axis "pen" = the run's x (glyph top side)
    ps = max(l["base"] for l in main)            # along start = largest baseline y of the main runs
    if ii is None:
        out.append("NOINK %-11s rot" % ascii(it["name"])); miss.append(it["name"]); continue
    res[it["name"]] = dict(ox=round(base - axp, 4), oy=round(ps - ayp, 4), rot=True,
                           jx0=round(ii["x0"] - axp, 4), jx1=round(ii["x1"] - axp, 4),
                           jy0=round(ii["y0"] - ayp, 4), jy1=round(ii["y1"] - ayp, 4),
                           n=ii["n"], fs=max(l["size"] for l in cands), nlines=len(cands))
    out.append("R %-11s anchor=%7.2f,%7.2f ox=%+7.3f oy=%+7.3f | ink jx0=%+7.3f jx1=%+7.3f (w=%6.3f) "
               "jy0=%+7.3f jy1=%+7.3f (L=%6.3f) | n=%5d nlines=%2d fs=%5.2f %s | %s" %
               (ascii(it["name"]), axp, ayp, res[it["name"]]["ox"], res[it["name"]]["oy"],
                res[it["name"]]["jx0"], res[it["name"]]["jx1"], res[it["name"]]["jx1"]-res[it["name"]]["jx0"],
                res[it["name"]]["jy0"], res[it["name"]]["jy1"], res[it["name"]]["jy1"]-res[it["name"]]["jy0"],
                ii["n"], len(cands), max(l["size"] for l in cands),
                "TOUCH!" if ii["touch"] else "     ",
                ascii("|".join(l["txt"].strip() for l in sorted(cands, key=lambda z: -z["base"]))[:46])))
out.append("items=%d/%d  miss=%s" % (len(res), len(K["horiz"])+len(K["rot"]), ascii(miss)))
json.dump(res, open(os.path.join(OD, "fig4_text_offsets.json"), "w", encoding="utf-8"), indent=1)
open(os.path.join(OD, "_qa_fig4_anchor_offsets.txt"), "w", encoding="ascii").write("\n".join(out) + "\n")
print("\n".join(out))
