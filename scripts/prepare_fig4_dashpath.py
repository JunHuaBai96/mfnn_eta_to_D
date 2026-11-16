"""Emit fig4_panelA_guide_dashpath.csv: the panel-A 0.301 guide as explicit pen segments.

Origin's built-in dash codes cannot reproduce the reference pattern, so the dash train is
drawn as one XYY line plot with missing-Y breaks (Origin breaks the line at missing Y and
adds a round cap of width/2 to every pen end -> ink = pen + 0.8 pt for -wp 0.8).

Reference ink (design pt): x 31.802..184.401, on=3.058, off=1.322, pen width 0.8.
"""
import os, csv, json
B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
PT = 72.0/2.54
K = json.load(open(os.path.join(OD, "fig4_origin_constants.json"), encoding="utf-8"))
A = K["layers"]["a"]
GD = K["guide_dash"]
Y = 0.3010299956639812                     # frozen guide value (unchanged, read-only source)
x0 = (A["left"] - K["off_cm"])*PT          # panel-A frame left, design pt
x1 = x0 + A["width"]*PT                    # panel-A frame right, design pt
sc = (A["xt"] - A["xf"])/(x1 - x0)         # A-x data units per design pt
w = GD["width"]
pen_on  = GD["on"]  - w                    # 2.258
period  = GD["on"] + GD["off"]             # 4.380
start0  = x0 + w/2.0                       # first pen start  (ink starts exactly on the frame)
end_last = x1 - w/2.0
d2x = lambda d: A["xf"] + (d - x0)*sc
rows = []
k = 0; n = 0
while True:
    a = start0 + k*period
    if a >= end_last - 1e-9: break
    b = min(a + pen_on, end_last)
    if n: rows.append(("", "", ""))        # missing-Y break between two dashes
    rows.append(("dashseg", d2x(a), Y)); rows.append(("dashseg", d2x(b), Y)); n += 1
    k += 1
out = os.path.join(OD, "fig4_panelA_guide_dashpath.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f); wr.writerow(["part", "x", "y"])
    for r in rows:
        wr.writerow([r[0], ("%.6f" % r[1]) if r[1] != "" else "", ("%.16f" % r[2]) if r[2] != "" else ""])
print("frame design x %.3f..%.3f  scale %.5f pt->data" % (x0, x1, sc))
print("pen_on=%.4f period=%.4f nseg=%d first_pen=%.4f last_pen=%.4f" % (pen_on, period, n, start0, b))
print("ink design x %.4f..%.4f  (target %.4f..%.4f)" % (start0-w/2, b+w/2, x0, x1))
print("data x %.5f..%.5f   rows=%d -> %s" % (d2x(start0), d2x(b), len(rows)+1, os.path.basename(out)))
