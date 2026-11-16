"""Prepare Origin plotting data for Main Fig.4 (Protocol W residual topology).

Re-derives ONLY the plot coordinates already used by the matplotlib figure
(scripts/publish_figures/generate_p0_gemini.py::fig4_protocol_W_residual_topology)
from the stored per-seed prediction CSVs.
No metric is recomputed (no MAPE / Factor2 / R2), nothing is retrained,
and no frozen Protocol W number is touched.
"""
import json
import math
import os

import numpy as np
import pandas as pd

BASE = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OUTD = os.path.join(BASE, "outputs", "origin_data")
SEEDS = [0, 1, 2, 42, 123]
LOG10_2 = math.log10(2.0)
COLS = ["sample_id", "T_K", "y_true_log10D", "pred_LF_only_log10D",
        "pred_HF_only_log10D", "pred_MFNN_log10D"]


def load_long():
    pieces = []
    for s in SEEDS:
        p = os.path.join(BASE, "outputs", "seed_wg_%d" % s, "test_predictions_within_T.csv")
        df = pd.read_csv(p)
        missing = [c for c in COLS if c not in df.columns]
        if missing:
            raise KeyError("%s missing %s" % (p, missing))
        sub = df[COLS].copy()
        sub["seed"] = s
        pieces.append(sub)
    return pd.concat(pieces, ignore_index=True)


def main():
    os.makedirs(OUTD, exist_ok=True)
    long = load_long()
    rows = []
    for sid, g in long.groupby("sample_id", sort=True):
        y_true = float(np.median(g["y_true_log10D"].to_numpy(float)))
        t_k = float(np.median(g["T_K"].to_numpy(float)))
        n_seeds = int(g["seed"].nunique())
        for model, col in [("LF_only", "pred_LF_only_log10D"),
                          ("HF_only", "pred_HF_only_log10D"),
                          ("MFNN", "pred_MFNN_log10D")]:
            mu = float(np.nanmean(g[col].to_numpy(float)))
            rows.append({"sample_id": sid, "model": model, "T_K": t_k,
                         "y_true_log10D": y_true, "pred_log10D_mean": mu,
                         "abs_err": abs(mu - y_true), "resid": mu - y_true,
                         "n_seeds": n_seeds})
    ens = pd.DataFrame(rows)
    lf = ens[ens.model == "LF_only"][["sample_id", "pred_log10D_mean"]].rename(
        columns={"pred_log10D_mean": "y_L_proxy"})
    mfnn = ens[ens.model == "MFNN"].merge(lf, on="sample_id", how="left")
    hf = ens[ens.model == "HF_only"].merge(lf, on="sample_id", how="left")

    # ---- panel A: |err| vs T  (MFNN primary, HF-only for context) ----
    a = mfnn[["sample_id", "T_K", "abs_err"]].copy()
    a["group"] = "MFNN"
    a = a.rename(columns={"T_K": "x", "abs_err": "y"}).sort_values("x")
    a.to_csv(os.path.join(OUTD, "fig4_panelA_mfnn.csv"), index=False)

    b = hf[["sample_id", "T_K", "abs_err"]].copy()
    b["group"] = "HF_only"
    b = b.rename(columns={"T_K": "x", "abs_err": "y"}).sort_values("x")
    b.to_csv(os.path.join(OUTD, "fig4_panelA_hf.csv"), index=False)

    # ---- panel B: signed residual vs LF-only proxy ----
    c = mfnn[["sample_id", "y_L_proxy", "resid"]].copy()
    c["group"] = "MFNN"
    c = c.rename(columns={"y_L_proxy": "x", "resid": "y"}).sort_values("x")
    c.to_csv(os.path.join(OUTD, "fig4_panelB_mfnn.csv"), index=False)

    # ---- guides (geometric only, value = log10(2) already frozen in code) ----
    ax_lim = [921.5, 1394.5]
    bx_lim = [-8.16873, -7.42695]
    g1 = pd.DataFrame({"part": ["dash_log10_2"] * 2,
                       "x": ax_lim, "y": [LOG10_2, LOG10_2]})
    g1.to_csv(os.path.join(OUTD, "fig4_panelA_guides.csv"), index=False)
    g2 = pd.DataFrame({
        "part": ["band_upper"] * 2 + ["band_lower"] * 2 + ["zero"] * 2,
        "x": bx_lim * 3,
        "y": [LOG10_2, LOG10_2, -LOG10_2, -LOG10_2, 0.0, 0.0]})
    g2.to_csv(os.path.join(OUTD, "fig4_panelB_guides.csv"), index=False)

    ranges = {
        "log10_2": LOG10_2,
        "a": {"xf": ax_lim[0], "xt": ax_lim[1], "yf": -0.018772, "yt": 0.410093,
              "x_ticks": [1000.0, 1100.0, 1200.0, 1300.0],
              "y_ticks": [0.0, 0.1, 0.2, 0.3, 0.4]},
        "b": {"xf": bx_lim[0], "xt": bx_lim[1], "yf": -0.332661, "yt": 0.363732,
              "x_ticks": [-8.0, -7.8, -7.6],
              "y_ticks": [-0.2, 0.0, 0.2]},
        "n_samples": int(mfnn.shape[0]),
    }
    with open(os.path.join(OUTD, "fig4_axis_ranges.json"), "w", encoding="utf-8") as f:
        json.dump(ranges, f, indent=1)

    print("samples=%d  A(xf,xt,yf,yt)=%.4f %.4f %.6f %.6f  B=%.5f %.5f %.6f %.6f"
          % (ranges["n_samples"], ax_lim[0], ax_lim[1], ranges["a"]["yf"], ranges["a"]["yt"],
             bx_lim[0], bx_lim[1], ranges["b"]["yf"], ranges["b"]["yt"]))
    print("A y data range %.6f..%.6f | B x data %.6f..%.6f B y %.6f..%.6f"
          % (a.y.min(), max(a.y.max(), b.y.max()), c.x.min(), c.x.max(), c.y.min(), c.y.max()))
    print("DONE_PREP")


if __name__ == "__main__":
    main()
