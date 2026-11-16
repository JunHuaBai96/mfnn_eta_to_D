import fitz, os, re, numpy as np
from PIL import Image
B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
FD = os.path.join(B, "outputs", "figures_origin")
NAME = "Fig1_mfnn_residual_schema"
RAWP = os.path.join(FD, "_raw.pdf")
RAWSVG = os.path.join(FD, "_raw.svg")
MARGIN = 2.5

# ---- ink bbox from an 8x raster (Origin span/drawing dicts underestimate:
#      light washes sit at ink level 4-11, and scatter markers/arrow caps are not spans)
d = fitz.open(RAWP); pg = d[0]
W, H = pg.mediabox.width, pg.mediabox.height
Z = 8.0
pm = pg.get_pixmap(matrix=fitz.Matrix(Z, Z), alpha=False)
a = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, 3)
lev = 255.0 - a.min(2).astype(np.float32)          # lightest channel -> catches pale washes
mask = lev >= 1.5
rows = np.where(mask.any(1))[0]; cols = np.where(mask.any(0))[0]
bb = (cols.min() / Z, rows.min() / Z, (cols.max() + 1) / Z, (rows.max() + 1) / Z)
print("page %.1f x %.1f  ink bbox %s  w=%.2f h=%.2f" % (W, H, [round(v, 3) for v in bb], bb[2]-bb[0], bb[3]-bb[1]))
for th in (1.0, 1.5, 3.0, 8.0, 15.0, 60.0):
    m = lev >= th
    r = np.where(m.any(1))[0]; c = np.where(m.any(0))[0]
    print("  thr %-5.1f -> x %.2f..%.2f  y %.2f..%.2f" % (th, c.min()/Z, c.max()/Z, r.min()/Z, r.max()/Z))
crop = fitz.Rect(max(0.0, bb[0]-MARGIN), max(0.0, bb[1]-MARGIN), min(W, bb[2]+MARGIN), min(H, bb[3]+MARGIN))
print("crop %s size %.3f x %.3f pt (%.3f x %.3f in / %.1f x %.1f mm)" % (
    [round(v,3) for v in crop], crop.width, crop.height, crop.width/72, crop.height/72,
    crop.width*25.4/72, crop.height*25.4/72))

# ---- PDF: vector-preserving crop
src = fitz.open(RAWP); out = fitz.open()
p = out.new_page(width=crop.width, height=crop.height)
p.show_pdf_page(p.rect, src, 0, clip=crop)
outp = os.path.join(FD, NAME + ".pdf")
out.save(outp, garbage=4, deflate=True); out.close(); src.close()

# ---- PNG from the cropped PDF @600 dpi
fin = fitz.open(outp); fp = fin[0]
zoom = 600.0/72.0
pm2 = fp.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
Image.frombytes("RGB", (pm2.width, pm2.height), pm2.samples).save(
    os.path.join(FD, NAME + ".png"), optimize=True, dpi=(600, 600))
print("PNG %d x %d px @600dpi -> %.3f x %.3f in" % (pm2.width, pm2.height, pm2.width/600.0, pm2.height/600.0))
n_txt = len(fp.get_text("dict")["blocks"])
print("cropped PDF text blocks:", n_txt, " spans:", sum(len(b.get('lines',[])) for b in fp.get_text('dict')['blocks']))
fin.close()

# ---- SVG: rewrite viewBox to the same rect (Origin writes user units == pt here)
svg = open(RAWSVG, encoding="utf-8").read()
m = re.search(r'viewBox="0,0 ([\d.]+),([\d.]+)"', svg) or re.search(r'viewBox="0,0 ([\d.]+) ([\d.]+)"', svg)
if not m:
    m = re.search(r'viewBox="([\d.]+)[, ]([\d.]+)[, ]([\d.]+)[, ]([\d.]+)"', svg)
    sw, sh = float(m.group(3)), float(m.group(4))
    if float(m.group(1)) != 0 or float(m.group(2)) != 0: raise SystemExit("unexpected raw SVG viewBox " + m.group(0))
else:
    sw, sh = float(m.group(1)), float(m.group(2))
print("raw SVG viewBox", sw, sh, " page", W, H, " -> unit scale %.5f %.5f" % (sw/W, sh/H))
sxu, syu = sw/W, sh/H
newtag = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
          'xmlns:olab="http://www.originlab.com/namespaces/olab" '
          'viewBox="%.4f,%.4f %.4f,%.4f" width="%.4fpt" height="%.4fpt">' % (
          crop.x0*sxu, crop.y0*syu, crop.width*sxu, crop.height*syu, crop.width, crop.height))
open(os.path.join(FD, NAME + ".svg"), "w", encoding="utf-8").write(re.sub(r"<svg[^>]*>", newtag, svg, count=1))
print("SVG tag:", newtag[newtag.find("viewBox"):newtag.find("width")])
print("DONE_CROP_FIG1")
