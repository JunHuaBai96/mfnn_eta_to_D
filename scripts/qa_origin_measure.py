"""Measure rendered text clusters + geometry in an Origin raw PDF export.
Usage: python qa_origin_measure.py <raw.pdf> <out.txt>
ASCII-only output. No metric recomputation."""
import sys, fitz, json

RAW = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D\outputs\figures_origin\_raw.pdf"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D\outputs\origin_data\_qa_measure.txt"
out = []
def P(s):
    out.append(s)

d = fitz.open(RAW)
pg = d[0]
P("PAGE %.4f %.4f" % (pg.mediabox.width, pg.mediabox.height))

spans = []
for b in pg.get_text("dict")["blocks"]:
    for l in b.get("lines", []):
        for s in l["spans"]:
            bb = s["bbox"]
            ox, oy = s["origin"]
            dx, dy = l["dir"]
            txt = s["text"]
            asc = s.get("ascender", 0.75); desc = s.get("descender", -0.25)
            spans.append(dict(x0=bb[0], y0=bb[1], x1=bb[2], y1=bb[3], ox=ox, oy=oy,
                              dx=dx, dy=dy, size=s["size"], font=s["font"], txt=txt,
                              asc=asc, desc=desc))
P("nspans %d" % len(spans))

# cluster horizontal spans by baseline, then merge by x-contiguity
hor = [s for s in spans if abs(s["dy"]) < 0.05]
rot = [s for s in spans if abs(s["dx"]) < 0.05]

def cluster(items, key1, key2, tol1, gap):
    groups = []
    for s in sorted(items, key=lambda z: (round(z[key1], 2), z[key2])):
        placed = False
        for g in groups:
            if abs(g["b1"] - s[key1]) <= tol1:
                if s[key2] - 0.5 <= g["e2"] + gap:
                    g["e2"] = max(g["e2"], s[key2] + 0.5)
                    g["sp"].append(s); placed = True; break
                if s[key2] - gap <= g["b2"] - 0.5:
                    g["b2"] = min(g["b2"], s[key2] - 0.5)
                    g["sp"].append(s); placed = True; break
            if placed: break
        if not placed:
            groups.append(dict(b1=s[key1], b2=s[key2] - 0.5, e2=s[key2] + 0.5, sp=[s]))
    return groups

def emit(tag, groups, isrot):
    for gi, g in enumerate(groups):
        sp = g["sp"]
        x0 = min(s["x0"] for s in sp); x1 = max(s["x1"] for s in sp)
        y0 = min(s["y0"] for s in sp); y1 = max(s["y1"] for s in sp)
        big = [s for s in sp if s["size"] >= 0.85 * max(z["size"] for z in sp)]
        mx0 = min(s["x0"] for s in big); mx1 = max(s["x1"] for s in big)
        my0 = min(s["y0"] for s in big); my1 = max(s["y1"] for s in big)
        sizes = sorted(set(round(s["size"], 3) for s in sp))
        fonts = sorted(set(s["font"] for s in sp))
        text = "".join(s["txt"] for s in sorted(sp, key=lambda z: (z["oy"], z["ox"])))
        asc = max(s["asc"] for s in big); desc = min(s["desc"] for s in big)
        if isrot:
            base = max(s["ox"] for s in big)
            P("%s#%02d base_x=%.3f band_x=%.3f..%.3f (c=%.3f w=%.3f) y=%.3f..%.3f (c=%.3f L=%.3f) "
              "sizes=%s fonts=%s asc=%.4f desc=%.4f | %s" %
              (tag, gi, base, mx0, mx1, (mx0+mx1)/2, mx1-mx0, my0, my1, (my0+my1)/2, my1-my0,
               sizes, fonts, asc, desc, ascii(text)[:48]))
        else:
            base = max(s["oy"] for s in big)
            P("%s#%02d base_y=%.3f x=%.3f..%.3f (c=%.3f W=%.3f) band_y=%.3f..%.3f "
              "sizes=%s fonts=%s asc=%.4f desc=%.4f | %s" %
              (tag, gi, base, x0, x1, (x0+x1)/2, x1-x0, y0, y1,
               sizes, fonts, asc, desc, ascii(text)[:48]))

hg = cluster(hor, "oy", "x0", 0.35, 7.0)
P("--- HORIZONTAL %d ---" % len(hg)); emit("H", hg, False)
rg = cluster(rot, "ox", "y1", 0.35, 7.0)
P("--- ROTATED %d ---" % len(rg)); emit("R", rg, True)

# geometry
frames = []
ticks = []
fills = {}
other = []
for dr in pg.get_drawings():
    col = dr.get("color"); fil = dr.get("fill")
    for it in dr["items"]:
        if it[0] == "l":
            p1, p2 = it[1], it[2]
            ln = ((p2.x-p1.x)**2 + (p2.y-p1.y)**2) ** 0.5
            if ln > 60:
                frames.append((p1.x, p1.y, p2.x, p2.y, col, dr.get("width")))
            elif ln > 1.0:
                ticks.append((p1.x, p1.y, p2.x, p2.y, col, dr.get("width"), ln))
            else:
                other.append((p1.x, p1.y, p2.x, p2.y, col))
        elif it[0] == "re":
            r = it[1]
            frames.append((r.x0, r.y0, r.x1, r.y1, col, dr.get("width")))
P("--- LONG SEGMENTS/RECTS %d ---" % len(frames))
for f in sorted(frames, key=lambda z: (z[1], z[0])):
    P("FR %.3f %.3f %.3f %.3f w=%s col=%s" % (f[0], f[1], f[2], f[3], f[4], str(f[5])))
P("--- SHORT SEGMENTS %d (grouped) ---" % len(ticks))
from collections import Counter
cx = Counter()
for t in ticks:
    if abs(t[1]-t[3]) < 0.2: cx["H@y%.1f" % t[1]] += 1
    elif abs(t[0]-t[2]) < 0.2: cx["V@x%.1f" % t[0]] += 1
for k, v in sorted(cx.items()):
    P("TK %s n=%d" % (k, v))
# marker fills: polygons with fill colour
sym = []
for dr in pg.get_drawings():
    fil = dr.get("fill")
    if fil is None: continue
    r = dr["rect"]
    if r.width < 12 and r.height < 12 and r.width > 1:
        sym.append((round(r.x0+r.width/2, 2), round(r.y0+r.height/2, 2), round(r.width, 2), round(r.height, 2), tuple(round(c, 3) for c in fil)))
P("--- SMALL FILLED SHAPES %d ---" % len(sym))
for s in sorted(sym, key=lambda z: (z[1], z[0])):
    P("SYM %.2f %.2f %.2f %.2f %s" % s)
open(OUT, "w", encoding="ascii").write("\n".join(out) + "\n")
print("WROTE", OUT, len(out))
