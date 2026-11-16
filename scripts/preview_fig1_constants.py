# -*- coding: ascii -*-
"""PIL preview of fig1_origin_constants.json (no Origin session).

Renders the DESIGN intent the way the builder's audit sees it:
  fills (rect/band/halo) -> polygons;  lines -> dashed polylines;
  symbols -> disks;  arrows -> shaft + head;
  texts -> Arial runs placed at the model ink box (own markup parser so that
  sub/superscripts are shifted, which the width model cannot distinguish).

usage:  python scripts/preview_fig1_constants.py [--boxes]
writes outputs/origin_data/_preview_fig1[_boxes].png
"""
import os, io, sys, json, math, runpy
from PIL import Image, ImageDraw, ImageFont

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
SHOW = "--boxes" in sys.argv
SS = 4                        # final preview pixels per design pt
IS = 16                       # internal supersample (px per design pt)
MARG = 14.0                   # design pt of white margin around the ink area

G = runpy.run_path(os.path.join(B, "scripts", "build_fig1_constants.py"))
ink_box = G["ink_box"]
D = json.load(io.open(os.path.join(OD, "fig1_origin_constants.json"), encoding="utf-8"))
INK_W = D["cal"]["ink_w"]; INK_H = D["cal"]["ink_h"]

FACES = {"reg": "arial.ttf", "bold": "arialbd.ttf", "ital": "ariali.ttf",
         "bi": "arialbi.ttf"}
_FC = {}
def font(face, size_pt):
    px = max(1, int(round(size_pt * IS)))
    k = (face, px)
    if k not in _FC:
        _FC[k] = ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", FACES[face]), px)
    return _FC[k]

def parse(t, face="reg", scale=1.0, off=0.0, acc=None):
    """markup -> [(char, face, size_scale, baseline offset in parent em, Y down +)]"""
    if acc is None:
        acc = []
    def match(j):
        d = 0
        while j < len(t):
            if t[j] == "(":
                d += 1
            elif t[j] == ")":
                d -= 1
                if d == 0:
                    return j
            j += 1
        raise ValueError(t)
    i = 0
    while i < len(t):
        if t[i] == "\\" and i + 1 < len(t):
            n = t[i + 1]
            if n == "x":
                a = t.index("(", i + 2); b = t.index(")", a)
                acc.append((chr(int(t[a + 1:b], 16)), face, scale, off))
                i = b + 1
                continue
            if n in ("i", "b", "-", "+"):
                a = i + 2
                if t[a] != "(" and n in "-+":
                    grp, b = t[a], a
                else:
                    b = match(a); grp = t[a + 1:b]
                fmap = {"i": {"reg": "ital", "bold": "bi"},
                        "b": {"reg": "bold", "ital": "bi"}}.get(n, {})
                s2 = scale * 0.684 if n in "-+" else scale
                o2 = off + (0.25 * scale if n == "-" else (-0.42 * scale if n == "+" else 0.0))
                parse(grp, fmap.get(face, face), s2, o2, acc)
                i = b + 1
                continue
        acc.append((t[i], face, scale, off))
        i += 1
    return acc

def label_tile(it):
    """(ink-cropped tile at SS px/pt, advance pt) with the ink drawn black."""
    fs = it["fs"]
    items = parse(it["txt"])
    asc = 1.15 * fs; desc = 0.45 * fs
    W = sum(font(f, fs * sc).getlength(ch) / IS for ch, f, sc, off in items)
    tile = Image.new("L", (max(1, int(round((W + 2) * IS))),
                           max(1, int(round((asc + desc + 2) * IS)))), 0)
    td = ImageDraw.Draw(tile)
    base = int(round((asc + 0.5) * IS))
    pen = 0.0
    for ch, f, sc, off in items:
        fl = font(f, fs * sc)
        td.text((int(round(pen * IS)), int(round(base + off * IS))), ch, font=fl,
                fill=255, anchor="ls")
        pen += fl.getlength(ch) / IS
    bb = tile.getbbox()
    if bb is None:
        return None, W
    crop = tile.crop(bb)
    small = crop.resize((max(1, int(round((bb[2] - bb[0]) / IS * SS))),
                         max(1, int(round((bb[3] - bb[1]) / IS * SS)))), Image.LANCZOS)
    out = Image.new("RGBA", small.size, (0, 0, 0, 255))
    out.putalpha(small)                      # L ink -> alpha
    return out, W

# ------------------------------------------------------------------ canvas
img = Image.new("RGB", (int(round((INK_W + 2 * MARG) * SS)),
                        int(round((INK_H + 2 * MARG) * SS))), "white")
dr = ImageDraw.Draw(img)
def X(x): return (MARG + x) * SS
def Y(y): return (MARG + y) * SS
def P(p): return (X(p[0]), Y(p[1]))

for f in D["fills"]:
    pts = [P(p) for p in f["top"]] + [P(p) for p in reversed(f["bottom"])]
    if len(pts) >= 3:
        dr.polygon(pts, fill=f["color"])

# preview approximation of the Origin dash styles (the json stores the names)
DASHP = {"solid": None, "long": [7.0, 3.0], "short": [3.2, 2.2],
         "dashdot": [6.0, 2.0, 1.0, 2.0], "dotted": [0.9, 1.7]}
def dash_poly(pts, pat):
    if not pat:
        return [[tuple(p) for p in pts]]
    out = []; on = True; cur = [tuple(pts[0])]; need = pat[0] * SS; pi = 0
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if seg <= 0:
            continue
        ux = (b[0] - a[0]) / seg; uy = (b[1] - a[1]) / seg
        done = 0.0
        while done < seg - 1e-9:
            step = min(need, seg - done)
            if step <= 1e-9:
                break
            nx, ny = a[0] + ux * (done + step), a[1] + uy * (done + step)
            if on:
                cur.append((nx, ny))
            else:
                if len(cur) > 1: out.append(cur)
                cur = [(nx, ny)]
            done += step; need -= step
            if need <= 1e-9:
                pi = (pi + 1) % len(pat); need = pat[pi] * SS; on = not on
    if on and len(cur) > 1: out.append(cur)
    return out

for ln in D["lines"]:
    runs_ = []; cur = []
    for p in ln["pts"]:
        if p is None:
            if len(cur) > 1: runs_.append(cur)
            cur = []
        else:
            cur.append(P(p))
    if len(cur) > 1: runs_.append(cur)
    dash = ln["dash"]
    if isinstance(dash, int):
        dash = {v: k for k, v in D["dash"].items()}[dash]
    pat = DASHP[dash]
    wpx = max(1, int(round(ln["w"] * SS)))
    for run in runs_:
        for piece in dash_poly(run, pat):
            dr.line(piece, fill=ln["color"], width=wpx, joint="curve")

for g in D["symbols"]:
    r = 0.5 * g["dia"] * SS
    wpx = max(1, int(round(g["ew"] * SS)))
    for cx, cy in g["pts"]:
        dr.ellipse((X(cx) - r, Y(cy) - r, X(cx) + r, Y(cy) + r),
                   fill=g["fill"], outline=g["edge"], width=wpx)

for a in D["arrows"]:
    x1, y1, x2, y2 = X(a["x1"]), Y(a["y1"]), X(a["x2"]), Y(a["y2"])
    ang = math.atan2(y2 - y1, x2 - x1)
    hl = a["head"] * SS; hw = 0.46 * a["head"] * SS
    bx, by = x2 - hl * math.cos(ang), y2 - hl * math.sin(ang)
    dr.line((x1, y1, bx, by), fill=a["color"], width=max(1, int(round(a["w"] * SS))))
    ux, uy = math.cos(ang), math.sin(ang)
    dr.polygon([(x2, y2), (bx - hw * uy, by + hw * ux), (bx + hw * uy, by - hw * ux)],
               fill=a["color"])

nbad = []
for it in D["texts"]:
    box = ink_box(it)
    x0, y0, x1, y1 = box
    tile, W = label_tile(it)
    if tile is None:
        continue
    if it.get("rot"):
        tile = tile.rotate(-90, expand=True)     # first glyph -> bottom
    tw = tile.width / float(SS); th = tile.height / float(SS)
    if tw > (x1 - x0) + 0.6 or th > (y1 - y0) + 0.6:
        nbad.append("%s model=%.2fx%.2f ink=%.2fx%.2f" %
                    (it["name"], x1 - x0, y1 - y0, tw, th))
    px = X(x0); py = Y(y1) - tile.height if it.get("rot") else Y(y0)
    if SHOW:
        dr.rectangle((X(x0), Y(y0), X(x1), Y(y1)), outline=(220, 60, 60), width=1)
    img.paste(tile, (int(round(px)), int(round(py))), tile)

out = os.path.join(OD, "_preview_fig1%s.png" % ("_boxes" if SHOW else ""))
img.save(out)
print("wrote %s  size=%dx%d  oversize=%d" % (out, img.width, img.height, len(nbad)))
for z in nbad:
    print("  OVER", z)