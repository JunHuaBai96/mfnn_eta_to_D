"""Prepare Fig6 Origin workbook data (Al80Cu20 tracer vs interdiffusivity).

Frozen numbers (do NOT recompute): MAPE tracer 156.5 / inter 6.5,
Fac2 0.00 / 1.00, n 10 / 2, t_ref 983 K, ratio ~3.0x.
"""
import os, csv, json
import pandas as pd

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
os.makedirs(OD, exist_ok=True)

raw = pd.read_csv(os.path.join(B, "data", "melt_diffusion_data.csv"))
al = raw[(raw["x_Cu"].round(2) == 0.20) & (raw["fidelity"] == "HF")].copy()
al["dt"] = al["diff_type"].replace({"interdiffusivity": "inter"})
tracer = al[al["dt"] == "tracer"].sort_values("T_K")
inter = al[al["dt"] == "inter"].sort_values("T_K")
assert len(tracer) == 10 and len(inter) == 2, (len(tracer), len(inter))

T_REF = 983.0
d_tr = float(tracer.loc[(tracer["T_K"] - T_REF).abs().idxmin(), "D_m2s"]) * 1e9
d_in = float(inter.loc[(inter["T_K"] - T_REF).abs().idxmin(), "D_m2s"]) * 1e9
ratio = d_in / d_tr

def w(name, header, rows):
    with open(os.path.join(OD, name), "w", newline="", encoding="utf-8") as f:
        cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)
    return len(rows)

n1 = w("fig6_panelA_tracer.csv", ["x", "y"], [(float(r.T_K), float(r.D_m2s) * 1e9) for r in tracer.itertuples()])
n2 = w("fig6_panelA_inter.csv", ["x", "y"], [(float(r.T_K), float(r.D_m2s) * 1e9) for r in inter.itertuples()])
n3 = w("fig6_panelB_bars.csv", ["x", "value", "group"],
       [(0.0, 156.5, "tracer"), (1.0, 6.5, "inter")])
# arrow shaft only; heads are drawn as filled triangle symbols in the plot script
n4 = w("fig6_arrow_path.csv", ["x", "y"], [(T_REF, d_tr), (T_REF, d_in)])

meta = {"n_tracer": n1, "n_inter": n2, "t_ref": T_REF, "d_tracer": round(d_tr, 6),
        "d_inter": round(d_in, 6), "ratio": round(ratio, 4),
        "ratio_label": "%.1f" % ratio, "mape": [156.5, 6.5], "fac2": [0.00, 1.00], "n": [10, 2]}
with open(os.path.join(OD, "fig6_data_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1)
print(json.dumps(meta))
print("rows: tracer=%d inter=%d bars=%d arrow=%d" % (n1, n2, n3, n4))
