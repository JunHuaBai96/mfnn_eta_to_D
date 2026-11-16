import fitz, os, re
from PIL import Image

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
RAWP = os.path.join(B, "outputs", "figures_origin", "_raw.pdf")
RAWPNG = os.path.join(B, "outputs", "figures_origin", "_raw.png")
RAWSVG = os.path.join(B, "outputs", "figures_origin", "_raw.svg")
OUTD = os.path.join(B, "outputs", "figures_origin")

def near(v, t):
    return abs(v - t) < 0.6

def content_bbox(path):
    d = fitz.open(path)
    pg = d[0]
    W, H = pg.mediabox.width, pg.mediabox.height
    xs0, ys0, xs1, ys1 = [], [], [], []
    for dr in pg.get_drawings():
        for it in dr["items"]:
            if it[0] == "l":
                p1, p2 = it[1], it[2]
                if near(p1.x, 1.44) and near(p2.x, 1.44):
                    continue
                if near(p1.x, 540.0) and near(p2.x, 540.0):
                    continue
                if near(p1.y, 2.24) and near(p2.y, 2.24):
                    continue
                if near(p1.y, 382.17) and near(p2.y, 382.17):
                    continue
                pts = [p1, p2]
            elif it[0] == "re":
                r = it[1]
                if near(r.x0, 1.44) and near(r.x1, 540.0):
                    continue
                pts = [fitz.Point(r.x0, r.y0), fitz.Point(r.x1, r.y1)]
            elif it[0] == "c":
                pts = [it[1], it[2], it[3], it[4]]
            else:
                continue
            for p in pts:
                xs0.append(p.x); ys0.append(p.y); xs1.append(p.x); ys1.append(p.y)
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                bb = s["bbox"]
                xs0.append(bb[0]); ys0.append(bb[1]); xs1.append(bb[2]); ys1.append(bb[3])
    d.close()
    return (min(xs0), min(ys0), max(xs1), max(ys1)), W, H

bb, W, H = content_bbox(RAWP)
M = 2.0
crop = fitz.Rect(max(0.0, bb[0] - M), max(0.0, bb[1] - M), min(W, bb[2] + M), min(H, bb[3] + M))
print("content bbox", [round(v, 3) for v in bb], "-> crop", [round(v, 3) for v in crop], "size %.3f x %.3f" % (crop.width, crop.height))

# PDF
src = fitz.open(RAWP)
out = fitz.open()
pg = out.new_page(width=crop.width, height=crop.height)
pg.show_pdf_page(pg.rect, src, 0, clip=crop)
out_pdf = os.path.join(OUTD, "Fig3_protocol_W_parity_metrics.pdf")
out.save(out_pdf, garbage=4, deflate=True)
out.close(); src.close()

# PNG from cropped PDF at 600 dpi (stable vs raw-png scale drift)
fin = fitz.open(out_pdf)
fp = fin[0]
zoom = 600.0 / 72.0
pm = fp.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
Image.frombytes("RGB", (pm.width, pm.height), pm.samples).save(
    os.path.join(OUTD, "Fig3_protocol_W_parity_metrics.png")
)
print("PNG from PDF @600dpi", pm.width, pm.height)
fin.close()

# SVG viewBox rewrite
svg = open(RAWSVG, encoding="utf-8").read()
m = re.search(r'viewBox="0,0 ([\d.]+),([\d.]+)"', svg)
if not m:
    m = re.search(r'viewBox="([\d.]+),([\d.]+) ([\d.]+),([\d.]+)"', svg)
    if m and float(m.group(1)) == 0 and float(m.group(2)) == 0:
        sw, sh = float(m.group(3)), float(m.group(4))
    else:
        raise SystemExit("unexpected raw SVG viewBox")
else:
    sw, sh = float(m.group(1)), float(m.group(2))
sxu, syu = sw / W, sh / H
newtag = (
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
    'xmlns:olab="http://www.originlab.com/namespaces/olab" '
    'viewBox="%.4f,%.4f %.4f,%.4f" width="%.4fpt" height="%.4fpt">'
    % (crop.x0 * sxu, crop.y0 * syu, crop.width * sxu, crop.height * syu, crop.width, crop.height)
)
open(os.path.join(OUTD, "Fig3_protocol_W_parity_metrics.svg"), "w", encoding="utf-8").write(
    re.sub(r"<svg[^>]*>", newtag, svg, count=1)
)
print("SVG", newtag[newtag.find("viewBox"): newtag.find("width")])

bb2, _, _ = content_bbox(out_pdf)
print("FINAL content bbox", [round(v, 3) for v in bb2])
print("FINAL pdf page", round(crop.width, 3), round(crop.height, 3))
print("DONE_CROP")
