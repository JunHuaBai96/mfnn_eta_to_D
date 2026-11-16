"""Fig.6 crop/finalise: trim _raw_fig6.{pdf,png,svg} to the ink bbox + margin and write
the deliverables outputs/figures_origin/Fig6_Al80_tracer_inter.{pdf,png,svg}.

House numbers (identical to Fig.3/4): margin M=2.0 pt, ink threshold 254, raster scale 20.
"""
import fitz, os, re, json, numpy as np
from PIL import Image
B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
FO = os.path.join(B, "outputs", "figures_origin")
RAWP = os.path.join(FO, "_raw_fig6.pdf"); RAWPNG = os.path.join(FO, "_raw_fig6.png"); RAWSVG = os.path.join(FO, "_raw_fig6.svg")
NAME = "Fig6_Al80_tracer_inter"
SC = 20.0; THR = 254; M = 2.0
def inkbox(path, sc=SC, thr=THR):
    pg = fitz.open(path)[0]
    pm = pg.get_pixmap(matrix=fitz.Matrix(sc, sc), alpha=False)
    a = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, pm.n)[:, :, 0]
    m = a < thr
    rs = np.nonzero(m.any(axis=1))[0]; cs = np.nonzero(m.any(axis=0))[0]
    box = (cs[0] / sc, rs[0] / sc, (cs[-1] + 1) / sc, (rs[-1] + 1) / sc)
    return pg.rect, box
rect, ib = inkbox(RAWP)
W, H = rect.width, rect.height
crop = fitz.Rect(max(0.0, ib[0] - M), max(0.0, ib[1] - M), min(W, ib[2] + M), min(H, ib[3] + M))
print("raw page %.3f x %.3f" % (W, H))
print("raw ink  [%.3f, %.3f, %.3f, %.3f]  w=%.3f h=%.3f" % (ib[0], ib[1], ib[2], ib[3], ib[2] - ib[0], ib[3] - ib[1]))
print("crop     [%.3f, %.3f, %.3f, %.3f]  w=%.3f h=%.3f  margins L%.3f T%.3f R%.3f B%.3f" %
      (crop.x0, crop.y0, crop.x1, crop.y1, crop.width, crop.height,
       ib[0] - crop.x0, ib[1] - crop.y0, crop.x1 - ib[2], crop.y1 - ib[3]))
print("ink width = %.3f pt = %.4f mm   (target %.3f pt = 135.0 mm)" % (ib[2] - ib[0], (ib[2] - ib[0]) * 25.4 / 72.0, 382.677))
src = fitz.open(RAWP); out = fitz.open(); pg = out.new_page(width=crop.width, height=crop.height)
pg.show_pdf_page(pg.rect, src, 0, clip=crop)
out_pdf = os.path.join(FO, NAME + ".pdf"); out.save(out_pdf, garbage=4, deflate=True); out.close(); src.close()
r2, b2 = inkbox(out_pdf)
print("FINAL pdf page %.3f x %.3f  ink [%.3f, %.3f, %.3f, %.3f]" % (r2.width, r2.height, b2[0], b2[1], b2[2], b2[3]))
ok = abs(b2[0] - M) < 0.15 and abs(b2[1] - M) < 0.15 and abs((crop.width - b2[2]) - M) < 0.15 and abs((crop.height - b2[3]) - M) < 0.15
print("NO_INK_CUT =", ok)
fin = fitz.open(out_pdf); fp = fin[0]
pm = fp.get_pixmap(matrix=fitz.Matrix(600.0 / 72.0, 600.0 / 72.0), alpha=False)
Image.frombytes("RGB", (pm.width, pm.height), pm.samples).save(os.path.join(FO, NAME + ".png"), dpi=(600.0, 600.0))
print("FINAL png %dx%d @600dpi" % (pm.width, pm.height)); fin.close()
svg = open(RAWSVG, encoding="utf-8").read()
m = re.search(r'viewBox="([\-\d.]+),([\-\d.]+) ([\d.]+),([\d.]+)"', svg)
ox, oy, sw, sh = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
assert (ox, oy) == (0.0, 0.0), ascii((ox, oy))
sxu, syu = sw / W, sh / H
newtag = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
          'xmlns:olab="http://www.originlab.com/namespaces/olab" '
          'viewBox="%.4f,%.4f %.4f,%.4f" width="%.4fpt" height="%.4fpt">' %
          (crop.x0 * sxu, crop.y0 * syu, crop.width * sxu, crop.height * syu, crop.width, crop.height))
open(os.path.join(FO, NAME + ".svg"), "w", encoding="utf-8").write(re.sub(r"<svg[^>]*>", newtag, svg, count=1))
print("FINAL svg", newtag[newtag.find("viewBox"):newtag.find("width")], " units/pt %.5f %.5f" % (sxu, syu))
res = dict(raw_ink=[round(v, 3) for v in ib], crop=[round(v, 3) for v in (crop.x0, crop.y0, crop.x1, crop.y1)],
           final_page=[round(crop.width, 3), round(crop.height, 3)], final_ink=[round(v, 3) for v in b2],
           no_ink_cut=bool(ok), margin=M, threshold=THR)
open(os.path.join(B, "outputs", "origin_data", "fig6_finalize_report.json"), "w", encoding="utf-8").write(json.dumps(res, indent=1))
print("DONE_CROP")
