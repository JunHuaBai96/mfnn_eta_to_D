import fitz, json, os, csv

BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
REF = os.path.join(BASE, "outputs", "figures", "Fig4_protocol_W_residual_topology.pdf")
OD = os.path.join(BASE, "outputs", "origin_data")

d = fitz.open(REF)
pg = d[0]
W, H = pg.mediabox.width, pg.mediabox.height
SCALE = 382.68 / W

spans = []
for b in pg.get_text("dict")["blocks"]:
    for li, l in enumerate(b.get("lines", [])):
        for si, s in enumerate(l["spans"]):
            spans.append(dict(
                block=b["number"], line=li, span=si, text=s["text"],
                font=s["font"], size=round(s["size"], 4),
                ox=round(s["origin"][0], 3), oy=round(s["origin"][1], 3),
                x0=round(s["bbox"][0], 3), y0=round(s["bbox"][1], 3),
                x1=round(s["bbox"][2], 3), y1=round(s["bbox"][3], 3),
                dirdx=round(l["dir"][0], 4), dirdy=round(l["dir"][1], 4),
                color="%06X" % s["color"]))
with open(os.path.join(OD, "fig4_ref_spans.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(spans[0].keys()))
    w.writeheader(); w.writerows(spans)

out = []
out.append("PAGE %.3f x %.3f   SCALE %.6f  -> content %.2f x %.2f pt (%.2f x %.2f mm)" %
           (W, H, SCALE, W * SCALE, H * SCALE, W * SCALE * 25.4 / 72, H * SCALE * 25.4 / 72))
rects, lines, curves = [], [], []
for dr in pg.get_drawings():
    col = dr.get("color"); fill = dr.get("fill")
    wdt = dr.get("width"); dash = dr.get("dashes")
    for it in dr["items"]:
        if it[0] == "re":
            r = it[1]; rects.append((r.x0, r.y0, r.x1, r.y1, col, fill, wdt, dash))
        elif it[0] == "l":
            p1, p2 = it[1], it[2]; lines.append((p1.x, p1.y, p2.x, p2.y, col, fill, wdt, dash))
        elif it[0] == "c":
            curves.append((it[1].x, it[1].y, it[4].x, it[4].y, col, fill, wdt, dash))

def cs(c):
    if c is None: return "None"
    return "#%02X%02X%02X" % tuple(int(round(v * 255)) for v in c)

out.append("\n== RECTS (%d) ==" % len(rects))
for r in sorted(rects, key=lambda t: (t[1], t[0])):
    out.append("  x %.3f..%.3f y %.3f..%.3f stroke %s fill %s w %s dash %s" %
               (r[0], r[2], r[1], r[3], cs(r[4]), cs(r[5]), r[6], r[7]))
out.append("\n== LINES (%d) ==" % len(lines))
for l in sorted(lines, key=lambda t: (str(t[4]), t[1], t[0])):
    out.append("  (%.3f,%.3f)-(%.3f,%.3f) col %s w %s dash %s" %
               (l[0], l[1], l[2], l[3], cs(l[4]), l[6], l[7]))
out.append("\n== CURVES (%d) first 30 ==" % len(curves))
for c in curves[:30]:
    out.append("  (%.3f,%.3f)..(%.3f,%.3f) col %s fill %s w %s dash %s" %
               (c[0], c[1], c[2], c[3], cs(c[4]), cs(c[5]), c[6], c[7]))
open(os.path.join(OD, "fig4_ref_drawings.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")

tgt = []
for s in spans:
    tgt.append(dict(text=s["text"], font=s["font"], size=s["size"],
                    px=round(s["ox"] * SCALE, 4), py=round(s["oy"] * SCALE, 4),
                    x0=round(s["x0"] * SCALE, 4), y0=round(s["y0"] * SCALE, 4),
                    x1=round(s["x1"] * SCALE, 4), y1=round(s["y1"] * SCALE, 4),
                    dirdx=s["dirdx"], dirdy=s["dirdy"], color=s["color"],
                    ref=[s["ox"], s["oy"], s["x0"], s["y0"], s["x1"], s["y1"]]))
json.dump(dict(page=[round(W, 3), round(H, 3)], scale=SCALE,
               content_pt=[round(W * SCALE, 3), round(H * SCALE, 3)], spans=tgt),
          open(os.path.join(OD, "fig4_ref_targets.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("page %.3f x %.3f scale %.6f -> %.2f x %.2f pt" % (W, H, SCALE, W*SCALE, H*SCALE))
print("spans", len(spans), "rects", len(rects), "lines", len(lines), "curves", len(curves))
print("WROTE")
