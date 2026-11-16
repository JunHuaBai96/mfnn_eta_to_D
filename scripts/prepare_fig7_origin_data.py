r"""Prepare the Fig.7 Origin workbook data (LOGO distance-caution panels).

House twin of prepare_fig5_origin_data.py / prepare_fig6_origin_data.py.

NOTHING is recomputed here.  Inputs are the frozen CSVs only:
  * outputs/results/LOGO_AlCu_difftype_feat_summary.csv  (MFNN rows, 13 folds)
  * outputs/results/LOGO_AlCu_delta_xCu_from_summary.csv (13 points, delta_x_Cu)
  * scripts/publish_figures/_style.py FROZEN["LOGO_mean"] = (39.4, 39.7)

The reference matplotlib axes are rebuilt in memory (Agg, NEVER saved) only so
the Origin panels can adopt the SAME axis limits/tick values the frozen PNG
used -- exactly the Fig.5 recipe.  generate_p1_gemini.py is NOT run; no
training, no checkpoints, no CSV is rewritten.

Writes:
  outputs/origin_data/fig7_a_bars.csv   row,mape,n,cls,label
  outputs/origin_data/fig7_b_points.csv cls,x,y
  outputs/origin_data/fig7_data_meta.json
"""
import os, csv, json, sys

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
sys.path.insert(0, B)
sys.path.insert(0, os.path.join(B, "scripts", "publish_figures"))
RESULTS = os.path.join(B, "outputs", "results")
OD = os.path.join(B, "outputs", "origin_data")
os.makedirs(OD, exist_ok=True)

import pandas as pd

# frozen display order (MAPE ascending, bottom->top), from the现役 figure
ORDER = ["Al81Cu19_inter", "Al85Cu15_inter", "Al80Cu20_inter",
         "PureAl_impurityCu_impurity", "Al95Cu5_inter", "Al81.3Cu18.7_inter",
         "Al90Cu10_inter", "Al87Cu13_inter", "Al82.9Cu17.1_tracer",
         "Al75Cu25_tracer", "Al90Cu10_tracer", "Al70Cu30_inter", "Al80Cu20_tracer"]

def cls_of(g):
    if "tracer" in g: return "tracer"
    if "inter" in g: return "inter"
    return "impurity"

LABEL = {
    "Al81Cu19_inter": "Al{81}Cu{19} (inter)",
    "Al85Cu15_inter": "Al{85}Cu{15} (inter)",
    "Al80Cu20_inter": "Al{80}Cu{20} (inter)",
    "PureAl_impurityCu_impurity": "Pure Al + Cu (impurity)",
    "Al95Cu5_inter": "Al{95}Cu{5} (inter)",
    "Al81.3Cu18.7_inter": "Al{81.3}Cu{18.7} (inter)",
    "Al90Cu10_inter": "Al{90}Cu{10} (inter)",
    "Al87Cu13_inter": "Al{87}Cu{13} (inter)",
    "Al82.9Cu17.1_tracer": "Al{82.9}Cu{17.1} (tracer)",
    "Al75Cu25_tracer": "Al{75}Cu{25} (tracer)",
    "Al90Cu10_tracer": "Al{90}Cu{10} (tracer)",
    "Al70Cu30_inter": "Al{70}Cu{30} (inter)",
    "Al80Cu20_tracer": "Al{80}Cu{20} (tracer)",
}

def num(v): return repr(float(v))

logo = pd.read_csv(os.path.join(RESULTS, "LOGO_AlCu_difftype_feat_summary.csv"))
m = logo[logo.model == "MFNN"].copy()
assert len(m) == 13, len(m)
by = {r.holdout_group: r for r in m.itertuples()}
assert set(by) == set(ORDER), set(by) ^ set(ORDER)

rows = []
for i, g in enumerate(ORDER):
    r = by[g]
    rows.append(dict(row=i, group=g, mape=float(r.MAPE_pct), n=int(r.n),
                     cls=cls_of(g), label=LABEL[g]))
with open(os.path.join(OD, "fig7_a_bars.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["row", "holdout_group", "mape", "n", "cls", "label"])
    for r in rows:
        cw.writerow([r["row"], r["group"], num(r["mape"]), r["n"], r["cls"], r["label"]])

dist = pd.read_csv(os.path.join(RESULTS, "LOGO_AlCu_delta_xCu_from_summary.csv"))
assert len(dist) == 13
drows = []
for r in dist.itertuples():
    g = r.holdout_group
    assert g in by, g
    assert abs(float(r.MAPE_pct) - float(by[g].MAPE_pct)) < 1e-9, g
    drows.append(dict(group=g, cls=cls_of(g), x=float(r.delta_x_Cu) * 100.0,
                      y=float(r.MAPE_pct)))
with open(os.path.join(OD, "fig7_b_points.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["holdout_group", "cls", "x", "y"])
    for r in drows:
        cw.writerow([r["group"], r["cls"], num(r["x"]), num(r["y"])])

# ---------------------------------------------------------------- reference axes (in-memory, never saved)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from _style import FROZEN

mean, std = FROZEN["LOGO_mean"]
assert (mean, std) == (39.4, 39.7), (mean, std)

fig, axes = plt.subplots(1, 2, figsize=(180 / 25.4, 70 / 25.4),
                         gridspec_kw={"width_ratios": [1.25, 1.0]})
ax = axes[0]
vals = [r["mape"] for r in rows]
ax.barh(np.arange(13), vals, height=0.72)
ax.set_xlim(0, 210)
ax2 = axes[1]
ax2.scatter([r["x"] for r in drows], [r["y"] for r in drows], s=42)
ref = {}
for tag, a in (("a", ax), ("b", ax2)):
    ref[tag] = dict(xlim=[float(v) for v in a.get_xlim()],
                    ylim=[float(v) for v in a.get_ylim()],
                    xticks=[float(v) for v in a.get_xticks() if a.get_xlim()[0] <= v <= a.get_xlim()[1]],
                    yticks=[float(v) for v in a.get_yticks() if a.get_ylim()[0] <= v <= a.get_ylim()[1]])
plt.close(fig)

meta = dict(
    source_summary="LOGO_AlCu_difftype_feat_summary.csv (MFNN only, 13 folds, read-only)",
    source_delta="LOGO_AlCu_delta_xCu_from_summary.csv (read-only; generate_p1_gemini.py NOT run)",
    frozen_mean=[mean, std],
    display_decimals=1,
    bars=[dict(row=r["row"], group=r["group"], mape=r["mape"], n=r["n"], cls=r["cls"],
               disp="%.1f" % r["mape"], label=r["label"]) for r in rows],
    points=[dict(group=r["group"], cls=r["cls"], x=r["x"], y=r["y"]) for r in drows],
    reference_axes=ref,
    note=("reference axes rebuilt in memory only (Agg, never saved); (b) ylim top will "
          "be raised in the Origin redraw to open the annotation lane (presentation only)"),
)
with open(os.path.join(OD, "fig7_data_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1)
print(json.dumps(meta["reference_axes"], indent=1))
print("bars=%d points=%d frozen_mean=%s" % (len(rows), len(drows), (mean, std)))


