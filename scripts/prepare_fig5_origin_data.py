r"""Prepare the Fig.5 Origin workbook data (representative Arrhenius panels).

House twin of prepare_fig2_origin_data.py / prepare_fig6_origin_data.py.

NOTHING is re-derived here beyond what
scripts/publish_figures/generate_p1_gemini.py::fig5_arrhenius_representative() already
does with the same frozen inputs:

  * source   : data/melt_diffusion_data_eta_paired_highmed_usable.csv
  * models   : outputs/seed_wg_42/within_T/mfnn_checkpoint.pt  (Protocol W, seed 42,
               12-D, INFERENCE ONLY -- no retraining, no frozen-metric change)
  * panel (a): PureAl self-diffusion HF rows; T grid = linspace(Tmin-10, Tmax+10, 40)
  * panel (b): Al80Cu20 Cu-tracer HF rows; same grid recipe on that subset
  * curves   : modified Sutherland prior / LF-only NN / HF-only NN / residual MFNN,
               all evaluated on the SAME 40-point grid, in (1000/T, log10 D) coordinates
  * eta(T)   : _eta_interpolator over the honest-paired rows of the composition group
               (Assael fallback for pure Al, exactly as the reference script)

The reference axes are rebuilt in memory (Agg, never saved) only so that the Origin
panels can use the SAME axis limits and the SAME tick values as the frozen figure.
Frozen numbers are untouched; this file only reshapes existing rows.
"""
import os, csv, json, sys
import numpy as np
import pandas as pd

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
sys.path.insert(0, B)
sys.path.insert(0, os.path.join(B, "scripts", "publish_figures"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from generate_p1_gemini import (          # noqa: E402  (module import is side-effect free)
    _load_usable,
    _eta_interpolator,
    _load_protocol_w_models,
    _predict_grid,
)
from physics import assael_pure_al_viscosity   # noqa: E402

OD = os.path.join(B, "outputs", "origin_data")
os.makedirs(OD, exist_ok=True)
SEED = 42


def w(name, header, rows):
    with open(os.path.join(OD, name), "w", newline="", encoding="utf-8") as f:
        cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)
    return len(rows)


def num(v):
    return "%.10f" % float(v)


df = _load_usable()
scaler, mfnn, hf, lf = _load_protocol_w_models(SEED)

panels = {}

# ---------------------------------------------------------------- panel (a)
pure = df[(df.comp_group == "PureAl") & (df.diff_type == "self") & (df.fidelity == "HF")].sort_values("T_K")
eta_fn = _eta_interpolator((df.comp_group == "PureAl"), df)
if eta_fn is None:
    eta_fn = lambda tt: np.array([assael_pure_al_viscosity(float(t)) for t in np.atleast_1d(tt)], dtype=float)
Ts = np.linspace(float(pure.T_K.min()) - 10, float(pure.T_K.max()) + 10, 40)
pred = _predict_grid(pure.iloc[0], Ts, eta_fn, scaler, mfnn, hf, lf)
panels["a"] = dict(title="Pure Al self-diffusion", exp=pure, Ts=Ts, pred=pred)

# ---------------------------------------------------------------- panel (b)
al80 = df[(df.comp_group == "Al80Cu20") & (df.diff_type == "tracer") & (df.fidelity == "HF")].sort_values("T_K")
eta_fn80 = _eta_interpolator((df.comp_group == "Al80Cu20"), df)
Ts80 = np.linspace(float(al80.T_K.min()) - 10, float(al80.T_K.max()) + 10, 40)
pred80 = _predict_grid(al80.iloc[0], Ts80, eta_fn80, scaler, mfnn, hf, lf)
panels["b"] = dict(title="Al80Cu20 Cu-tracer", exp=al80, Ts=Ts80, pred=pred80)

# ---------------------------------------------------------------- reference axis geometry
# Rebuild the frozen figure in memory (Agg, never written) purely to read the limits/ticks
# that matplotlib chose for the published PNG, so the Origin redraw keeps "the same
# coordinates".  Coordinates only -- no data, no metrics are recomputed here.
ref_axes = {}
for tag, P in panels.items():
    fig, ax = plt.subplots(1, 1, figsize=(7.09, 2.36))
    exp = P["exp"]; Ts = P["Ts"]; predp = P["pred"]
    x_exp = 1000.0 / exp.T_K.to_numpy(dtype=float)
    y_exp = np.log10(np.clip(exp.D_m2s.to_numpy(dtype=float), 1e-30, None))
    ax.scatter(x_exp, y_exp, s=36, c="#333333", edgecolors="white", linewidths=0.4, zorder=5)
    xg = 1000.0 / Ts
    ax.plot(xg, predp["Sutherland"], color="#E69F00", ls=":", lw=1.2)
    ax.plot(xg, predp["LF_only"], color="#E69F00", ls="--", lw=1.2)
    ax.plot(xg, predp["HF_only"], color="#0072B2", ls="-.", lw=1.2)
    ax.plot(xg, predp["MFNN"], color="#009E73", ls="-", lw=1.4)
    fig.tight_layout()
    ref_axes[tag] = dict(xlim=[float(v) for v in ax.get_xlim()],
                         ylim=[float(v) for v in ax.get_ylim()],
                         xticks=[float(v) for v in ax.get_xticks()],
                         yticks=[float(v) for v in ax.get_yticks()])
    plt.close(fig)

# ---------------------------------------------------------------- write CSVs
counts = {}
for tag, P in panels.items():
    exp = P["exp"]; Ts = P["Ts"]; predp = P["pred"]
    x_exp = 1000.0 / exp.T_K.to_numpy(dtype=float)
    y_exp = np.log10(np.clip(exp.D_m2s.to_numpy(dtype=float), 1e-30, None))
    o = np.argsort(x_exp)
    counts["%s_exp" % tag] = w("fig5_%s_exp.csv" % tag, ["x", "y"],
                               [(num(x_exp[i]), num(y_exp[i])) for i in o])
    xg = 1000.0 / Ts                      # T-ascending grid -> x descending, as in the draft
    for key, pre in (("Sutherland", "prior"), ("LF_only", "lf"), ("HF_only", "hf"), ("MFNN", "mfnn")):
        counts["%s_%s" % (tag, pre)] = w("fig5_%s_%s.csv" % (tag, pre), ["x", "y"],
                                         [(num(a), num(b)) for a, b in zip(xg, predp[key])])

meta = dict(
    seed=SEED,
    checkpoint=os.path.join("outputs", "seed_wg_%d" % SEED, "within_T", "mfnn_checkpoint.pt"),
    inference_only=True,
    feature_dim=12,
    grid_points=40,
    panels={},
)
for tag, P in panels.items():
    exp = P["exp"]; Ts = P["Ts"]
    xg = 1000.0 / Ts
    clip = np.clip(exp.D_m2s.to_numpy(dtype=float), 1e-30, None)
    meta["panels"][tag] = dict(
        title=P["title"],
        n_exp=counts["%s_exp" % tag],
        T_K_range=[float(exp.T_K.min()), float(exp.T_K.max())],
        grid_T_range=[float(Ts[0]), float(Ts[-1])],
        x_range=[float(min(xg)), float(max(xg))],
        y_ranges={k: [float(np.min(P["pred"][k])), float(np.max(P["pred"][k]))]
                  for k in ("Sutherland", "LF_only", "HF_only", "MFNN")},
        y_exp_range=[float(np.min(np.log10(clip))), float(np.max(np.log10(clip)))],
        reference_axes=ref_axes[tag],
    )
with open(os.path.join(OD, "fig5_data_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1)
print(json.dumps(meta, indent=1))
