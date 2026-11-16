#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
prepare_fig3_origin_data.py

Assemble *plot-ready* data for Fig. 3 (Protocol W parity + metric bars) so the
figure can be redrawn in OriginPro.

HARD CONSTRAINTS
----------------
* NO metric recomputation. MAPE / Factor2 / R2 are transcribed verbatim from the
  frozen Protocol W table (outputs/PAPER_JCP_draft_EN.md).
* Parity points are transcribed verbatim from the already-published
  post-processing table
  outputs/results/protocol_W_parity_ensemble_points.csv
  (no re-averaging, no re-filtering, no retraining).

Outputs (outputs/origin_data/):
  fig3_parity_points.csv          long, semantic (x, y, error, group, subset, ...)
  fig3_parity_series.csv          wide, one x/y/err block per plotted series
  fig3_parity_reference_lines.csv identity line + factor-of-two band
  fig3_metrics_mape.csv           frozen MAPE bars
  fig3_metrics_factor2.csv        frozen Factor2 bars
  fig3_axis_ranges.json           axis geometry + provenance
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
SRC_PARITY = ROOT / "outputs" / "results" / "protocol_W_parity_ensemble_points.csv"
OUT_DIR = ROOT / "outputs" / "origin_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Panel (a): parity points -- transcribed, not recomputed
# ---------------------------------------------------------------------------
raw = pd.read_csv(SRC_PARITY)
print("[in ] %s: %d rows" % (SRC_PARITY.name, len(raw)))

MODEL_LABEL = {"LF_only": "LF-only", "HF_only": "HF-only", "MFNN": "residual MFNN"}
ORDER = ["LF_only", "HF_only", "MFNN"]

pts = pd.DataFrame({
    "x": raw["y_true_log10D"].astype(float),
    "xerr": raw["y_true_log10D_seed_spread"].astype(float),
    "y": raw["pred_log10D_mean"].astype(float),
    "error": raw["pred_log10D_std"].astype(float),
    "group": raw["model"].astype(str),
    "group_label": raw["model"].astype(str).map(MODEL_LABEL),
    "subset": np.where(
        raw["all_five_seeds"].astype(str).str.lower() == "true", "filled", "open"),
    "sample_id": raw["sample_id"].astype(str),
    "system": raw["system"].astype(str),
    "comp_group": raw["comp_group"].astype(str),
    "T_K": raw["T_K"].astype(float),
    "n_seeds": raw["n_seeds"].astype(int),
    "in_factor2": raw["in_factor2"].astype(str),
})
assert len(pts) == len(raw)
assert (pts["xerr"] == 0).all(), "non-zero x spread -> panel (a) is vertical-error only"
pts.to_csv(OUT_DIR / "fig3_parity_points.csv", index=False)
print("[out] fig3_parity_points.csv rows=%d" % len(pts))
print(pts.groupby(["group", "subset"]).size().to_string())

# ---------------------------------------------------------------------------
# 2. Wide, plot-ready series blocks (one block per Origin plot object)
# ---------------------------------------------------------------------------
blocks = {}
series_meta = []
for model in ORDER:
    for subset in ("filled", "open"):
        sub = pts[(pts["group"] == model) & (pts["subset"] == subset)].sort_values("x")
        key = "%s_%s" % (model, subset)
        series_meta.append({"series": key, "group": model, "subset": subset, "n": int(len(sub))})
        blocks["x_" + key] = list(sub["x"])
        blocks["y_" + key] = list(sub["y"])
        blocks["err_" + key] = list(sub["error"])

width = max(len(v) for v in blocks.values())
wide = {k: (v + [np.nan] * (width - len(v))) for k, v in blocks.items()}
ordered_cols = []
for m in series_meta:
    k = m["series"]
    ordered_cols += ["x_" + k, "y_" + k, "err_" + k]
wide_df = pd.DataFrame(wide)[ordered_cols]
wide_df.to_csv(OUT_DIR / "fig3_parity_series.csv", index=False, float_format="%.6f")
print("[out] fig3_parity_series.csv series=%d maxrows=%d" % (len(series_meta), width))
for m in series_meta:
    print("      ", m)

# ---------------------------------------------------------------------------
# 3. Reference geometry: identity line + factor-of-two band
#    x and y share the same numeric limits so y=x is the corner-to-corner diagonal
# ---------------------------------------------------------------------------
LOG10_2 = 0.301030
dmin = min(pts["x"].min(), (pts["y"] - pts["error"]).min())
dmax = max(pts["x"].max(), (pts["y"] + pts["error"]).max())
span = dmax - dmin
lo = float(np.floor((dmin - 0.05 * span) * 20) / 20)
hi = float(np.ceil((dmax + 0.05 * span) * 20) / 20)
xs = np.linspace(lo, hi, 201)
ref = pd.DataFrame({
    "x": xs,
    "identity": xs,
    "band_upper": np.minimum(xs + LOG10_2, hi),
    "band_lower": np.maximum(xs - LOG10_2, lo),
})
ref.to_csv(OUT_DIR / "fig3_parity_reference_lines.csv", index=False, float_format="%.6f")
print("[out] fig3_parity_reference_lines.csv data=[%.4f,%.4f] axis=[%.2f,%.2f]"
      % (dmin, dmax, lo, hi))

# ---------------------------------------------------------------------------
# 4/5. Frozen bar metrics -- transcribed from the Protocol W table
# ---------------------------------------------------------------------------
FROZEN = {
    "MAPE": [("LF-only", 109.6, 13.13, "109.60"),
             ("HF-only", 30.98, 4.43, "30.98"),
             ("MFNN", 26.18, 1.33, "26.18")],
    "Factor2": [("LF-only", 0.56, 0.10, "0.56"),
                ("HF-only", 0.973, 0.033, "0.973"),
                ("MFNN", 0.96, 0.033, "0.96")],
}
COLORS = {"LF-only": "#E69F00", "HF-only": "#0072B2", "MFNN": "#009E73"}  # Okabe-Ito

for metric, fname, ylab in (
    ("MAPE", "fig3_metrics_mape.csv", "Mean absolute percentage error (%)"),
    ("Factor2", "fig3_metrics_factor2.csv", "Factor-of-two accuracy"),
):
    df = pd.DataFrame([
        {"group": g, "value": v, "error": e, "display_label": lab,
         "color": COLORS[g], "y_axis_title": ylab,
         "source": "frozen Protocol W table (transcribed, not recomputed)"}
        for (g, v, e, lab) in FROZEN[metric]])
    df.to_csv(OUT_DIR / fname, index=False)
    print("[out] " + fname)
    print(df[["group", "value", "error", "display_label"]].to_string(index=False))

meta = {
    "parity_axis_limits": [lo, hi],
    "parity_x_tick_step": 0.5,
    "parity_y_tick_step": 0.25,
    "log10_2_band": LOG10_2,
    "n_points_total": int(len(pts)),
    "n_filled": int((pts["subset"] == "filled").sum()),
    "n_open": int((pts["subset"] == "open").sum()),
    "r2_mfnn_annotation": "R2_MFNN = 0.392 +/- 0.094 (frozen; n_test = 15/seed)",
    "okabe_ito": COLORS,
    "provenance": {"parity": str(SRC_PARITY.relative_to(ROOT)),
                   "bars": "outputs/PAPER_JCP_draft_EN.md :: Table (Protocol W)"},
}
(OUT_DIR / "fig3_axis_ranges.json").write_text(
    json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
print("[out] fig3_axis_ranges.json")
print("DONE")
