#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gemini-numbered P0 figures (Main Fig.3, Fig.4, SI Fig.S1).

Reuses publish_figures/_style.py tokens and FROZEN numbers.
Does NOT retrain; does NOT overwrite legacy Fig2/Fig6/Fig9/FigS1_al80 stems.
Run from repo root:
  .venv\\Scripts\\python.exe scripts/publish_figures/generate_p0_gemini.py
"""
from __future__ import annotations

import math
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# Allow running as script from repo root or from this folder
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _style import (  # noqa: E402
    C,
    FIG_DIR,
    FROZEN,
    JCP_FIG,
    RESULTS,
    ROOT,
    VECTOR_PACK,
    W_DOUBLE,
    W_MID,
    W_SINGLE,
    apply_style,
    despine,
    box_spines,
    panel_letter,
)

SEEDS = [0, 1, 2, 42, 123]
MODELS = ["LF_only", "HF_only", "MFNN"]
MODEL_LABELS = {"LF_only": "LF-only", "HF_only": "HF-only", "MFNN": "residual MFNN"}
MODEL_COLORS = {"LF_only": C["LF"], "HF_only": C["HF"], "MFNN": C["MFNN"]}
MODEL_STROKES = {"LF_only": C["LF_stroke"], "HF_only": C["HF_stroke"], "MFNN": C["MFNN_stroke"]}
LOG10_2 = math.log10(2.0)


def _save(fig, stem: str, caption: str, ai_layers: str) -> None:
    """Save png/pdf/svg to figures/, vector pack, and jcp_submission/figures/."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    JCP_FIG.mkdir(parents=True, exist_ok=True)
    pack = VECTOR_PACK / stem
    pack.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg", "png"):
        kw = {"dpi": 600} if ext == "png" else {}
        path = FIG_DIR / f"{stem}.{ext}"
        fig.savefig(path, **kw)
        shutil.copy2(path, pack / f"{stem}.{ext}")
        shutil.copy2(path, JCP_FIG / f"{stem}.{ext}")
    (pack / "README.txt").write_text(
        f"Stem: {stem}\n\nCaption draft:\n{caption}\n\n"
        f"Illustrator layers:\n{ai_layers}\n",
        encoding="utf-8",
    )
    print("saved", stem, "->", FIG_DIR, "and", JCP_FIG)


def fig3_protocol_W_parity_metrics() -> None:
    """Gemini Main Fig.3: (a) parity ensemble, (b) MAPE, (c) Factor2 — FROZEN bars."""
    apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(W_DOUBLE, 62 / 25.4))
    order = ["LF_only", "HF_only", "MFNN"]
    labels = [MODEL_LABELS[m] for m in order]
    colors = [MODEL_COLORS[m] for m in order]
    strokes = [MODEL_STROKES[m] for m in order]
    marker_map = {"LF_only": "s", "HF_only": "^", "MFNN": "o"}

    # (a) ensemble parity with seed-std error bars (MFNN primary; all three overlaid)
    ax = axes[0]
    pts = pd.read_csv(RESULTS / "protocol_W_parity_ensemble_points.csv")
    lims = [-9.2, -7.6]
    ax.fill_between(
        lims,
        [l - LOG10_2 for l in lims],
        [l + LOG10_2 for l in lims],
        color=C["band"],
        alpha=0.45,
        zorder=0,
        label=r"factor-of-two band",
    )
    ax.plot(lims, lims, color=C["ref_dark"], lw=0.9, zorder=1, label="1:1")

    for m in order:
        sub = pts[pts.model == m].copy()
        # filled = all five seeds; open = partial overlap
        full = sub[sub.all_five_seeds == True]  # noqa: E712
        part = sub[sub.all_five_seeds == False]  # noqa: E712
        for chunk, face in ((full, MODEL_COLORS[m]), (part, "none")):
            if chunk.empty:
                continue
            ax.errorbar(
                chunk.y_true_log10D,
                chunk.pred_log10D_mean,
                yerr=chunk.pred_log10D_std,
                fmt="none",
                ecolor=MODEL_STROKES[m],
                elinewidth=0.6,
                capsize=1.5,
                alpha=0.75,
                zorder=2,
            )
            ax.scatter(
                chunk.y_true_log10D,
                chunk.pred_log10D_mean,
                s=30 if m == "MFNN" else 22,
                facecolors=face,
                edgecolors=MODEL_STROKES[m],
                linewidths=0.6,
                marker=marker_map[m],
                alpha=0.9,
                zorder=3 if m == "MFNN" else 2,
                label=MODEL_LABELS[m] if face != "none" else None,
            )

    r2m, r2s = FROZEN["W_MFNN_R2"]
    ax.text(
        0.04,
        0.96,
        rf"$R^2_{{\mathrm{{MFNN}}}}={r2m:.3f}\pm{r2s:.3f}$"
        + "\n"
        + r"(frozen; $n_{\mathrm{test}}=15$/seed)",
        transform=ax.transAxes,
        fontsize=6.5,
        va="top",
        ha="left",
        bbox=dict(
            boxstyle="round,pad=0.2",
            fc="white",
            ec=C["MFNN_stroke"],
            lw=0.5,
            alpha=0.92,
        ),
    )
    ax.set_xlabel(r"$\log_{10} D_{\mathrm{true}}$", fontsize=9)
    ax.set_ylabel(r"$\log_{10} \hat{D}$ (seed mean)", fontsize=9)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect("equal", adjustable="box")
    # custom legend: models + open=partial
    handles = [
        Line2D(
            [0],
            [0],
            marker=marker_map[m],
            color="none",
            markerfacecolor=MODEL_COLORS[m],
            markeredgecolor=MODEL_STROKES[m],
            markersize=6,
            label=MODEL_LABELS[m],
        )
        for m in order
    ]
    handles.append(
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="none",
            markeredgecolor=C["ref_dark"],
            markersize=6,
            label="partial seed overlap",
        )
    )
    ax.legend(
        handles=handles,
        loc="lower right",
        fontsize=5.5,
        handletextpad=0.25,
        borderpad=0.2,
        frameon=False,
    )
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    panel_letter(ax, "a", x=-0.18)

    # (b) MAPE — FROZEN only
    ax = axes[1]
    x = np.arange(len(order))
    width = 0.62
    mape_m = [FROZEN["W_LF_MAPE"][0], FROZEN["W_HF_MAPE"][0], FROZEN["W_MFNN_MAPE"][0]]
    mape_s = [FROZEN["W_LF_MAPE"][1], FROZEN["W_HF_MAPE"][1], FROZEN["W_MFNN_MAPE"][1]]
    ax.bar(
        x,
        mape_m,
        width,
        yerr=mape_s,
        color=colors,
        edgecolor=strokes,
        linewidth=0.6,
        capsize=2.5,
        error_kw=dict(lw=0.8, ecolor=C["ref_dark"]),
    )
    for i, (v, s) in enumerate(zip(mape_m, mape_s)):
        ax.text(i, v + s + 4, f"{v:.2f}", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Mean absolute\npercentage error (%)", fontsize=8)
    ax.set_ylim(0, 145)
    box_spines(ax)
    panel_letter(ax, "b")

    # (c) Factor2 — FROZEN only
    ax = axes[2]
    f2_m = [FROZEN["W_LF_F2"][0], FROZEN["W_HF_F2"][0], FROZEN["W_MFNN_F2"][0]]
    f2_s = [FROZEN["W_LF_F2"][1], FROZEN["W_HF_F2"][1], FROZEN["W_MFNN_F2"][1]]
    ax.bar(
        x,
        f2_m,
        width,
        yerr=f2_s,
        color=colors,
        edgecolor=strokes,
        linewidth=0.6,
        capsize=2.5,
        error_kw=dict(lw=0.8, ecolor=C["ref_dark"]),
    )
    for i, (v, s) in enumerate(zip(f2_m, f2_s)):
        y_ann = v + s + 0.06
        if i == 0:
            y_ann = v + s + 0.08
        ax.text(i, min(y_ann, 1.15), f"{v:.3g}", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Factor-of-two\naccuracy", fontsize=8)
    ax.set_ylim(0, 1.25)
    ax.axhline(1.0, color=C["ref"], lw=0.7, ls="--", zorder=0)
    box_spines(ax)
    panel_letter(ax, "c")

    fig.tight_layout(w_pad=1.15)
    cap = (
        "Figure 3. Protocol W (within-composition temperature hold-out; five seeds "
        r"$0,1,2,42,123$; $n_{\mathrm{test}}=15$ per seed) for residual MFNN versus "
        "HF-only and LF-only baselines. (a) Seed-mean $\\log_{10}D$ parity with "
        "vertical bars showing the across-seed standard deviation; the shaded band is "
        r"$\pm\log_{10}2$ (factor-of-two). Filled markers: sample present in all five "
        "seed test sets; open markers: partial seed overlap (union of test ids). "
        "Bar panels use frozen Table metrics and are not recomputed from the scatter. "
        f"(b) MAPE (%): LF-only ${FROZEN['W_LF_MAPE'][0]}\\pm{FROZEN['W_LF_MAPE'][1]}$, "
        f"HF-only ${FROZEN['W_HF_MAPE'][0]}\\pm{FROZEN['W_HF_MAPE'][1]}$, "
        f"residual MFNN ${FROZEN['W_MFNN_MAPE'][0]}\\pm{FROZEN['W_MFNN_MAPE'][1]}$. "
        f"(c) Factor2: LF-only ${FROZEN['W_LF_F2'][0]}\\pm{FROZEN['W_LF_F2'][1]}$, "
        f"HF-only ${FROZEN['W_HF_F2'][0]}\\pm{FROZEN['W_HF_F2'][1]}$, "
        f"residual MFNN ${FROZEN['W_MFNN_F2'][0]}\\pm{FROZEN['W_MFNN_F2'][1]}$. "
        "Not a PINN/PPINN formulation."
    )
    layers = (
        "L1_Background_and_Guides: factor-of-two band, 1:1 line, Factor2=1 dashed\n"
        "L2_Data_Series: parity markers by model; MAPE/Factor2 bars\n"
        "L3_ErrorBars_and_Arrows: seed-std on parity; frozen std on bars\n"
        "L4_Typography_and_Math: (a)(b)(c), R2 callout, bar annotations"
    )
    _save(fig, "Fig3_protocol_W_parity_metrics", cap, layers)
    plt.close(fig)


def _load_seed_predictions() -> pd.DataFrame:
    pieces = []
    for seed in SEEDS:
        path = ROOT / "outputs" / f"seed_wg_{seed}" / "test_predictions_within_T.csv"
        df = pd.read_csv(path)
        need = [
            "sample_id",
            "T_K",
            "y_true_log10D",
            "pred_LF_only_log10D",
            "pred_HF_only_log10D",
            "pred_MFNN_log10D",
        ]
        missing = [c for c in need if c not in df.columns]
        if missing:
            raise KeyError(f"{path} missing {missing}")
        sub = df[need].copy()
        sub["seed"] = seed
        pieces.append(sub)
    return pd.concat(pieces, ignore_index=True)


def fig4_protocol_W_residual_topology() -> None:
    """Gemini Main Fig.4: |Δlog10D| vs T; residual vs LF-only proxy for D_LF."""
    apply_style()
    long = _load_seed_predictions()
    # Ensemble per sample_id (mean over seeds that contain the point)
    rows = []
    for sid, g in long.groupby("sample_id", sort=True):
        y_true = float(np.median(g["y_true_log10D"].to_numpy(dtype=float)))
        t_k = float(np.median(g["T_K"].to_numpy(dtype=float)))
        n_seeds = int(g["seed"].nunique())
        for model, col in [
            ("LF_only", "pred_LF_only_log10D"),
            ("HF_only", "pred_HF_only_log10D"),
            ("MFNN", "pred_MFNN_log10D"),
        ]:
            vals = g[col].to_numpy(dtype=float)
            mu = float(np.nanmean(vals))
            rows.append(
                {
                    "sample_id": sid,
                    "model": model,
                    "T_K": t_k,
                    "y_true_log10D": y_true,
                    "pred_log10D_mean": mu,
                    "abs_err": abs(mu - y_true),
                    "resid": mu - y_true,
                    "n_seeds": n_seeds,
                }
            )
    ens = pd.DataFrame(rows)
    # LF proxy on same sample_ids
    lf = ens[ens.model == "LF_only"][["sample_id", "pred_log10D_mean"]].rename(
        columns={"pred_log10D_mean": "y_L_proxy"}
    )
    mfnn = ens[ens.model == "MFNN"].merge(lf, on="sample_id", how="left")
    hf = ens[ens.model == "HF_only"].merge(lf, on="sample_id", how="left")

    fig, axes = plt.subplots(1, 2, figsize=(W_MID, 58 / 25.4))

    # (a) |Δlog10D| vs T — MFNN primary, HF light for context
    ax = axes[0]
    ax.axhline(LOG10_2, color=C["ref"], lw=0.8, ls="--", zorder=0)
    ax.scatter(
        hf.T_K,
        hf.abs_err,
        s=22,
        c=C["HF"],
        edgecolors=C["HF_stroke"],
        linewidths=0.4,
        alpha=0.55,
        marker="^",
        zorder=1,
        label="HF-only",
    )
    ax.scatter(
        mfnn.T_K,
        mfnn.abs_err,
        s=32,
        c=C["MFNN"],
        edgecolors=C["MFNN_stroke"],
        linewidths=0.5,
        zorder=2,
        label="residual MFNN",
    )
    ax.set_xlabel(r"$T$ (K)", fontsize=9)
    ax.set_ylabel(r"$|\Delta\log_{10} D|=|\log_{10}\hat{D}-\log_{10}D_{\mathrm{true}}|$", fontsize=8)
    ax.text(
        0.98,
        0.95,
        r"dashed: $\log_{10}2\approx0.301$ (Factor2)",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.5,
        color=C["ref_dark"],
    )
    ax.legend(loc="upper left", fontsize=6.5)
    box_spines(ax)
    panel_letter(ax, "a")

    # (b) residual vs LF-only proxy (stand-in for D_LF / y_L)
    ax = axes[1]
    ax.axhspan(-LOG10_2, LOG10_2, color=C["band"], alpha=0.45, zorder=0)
    ax.axhline(0, color=C["ref_dark"], lw=0.8)
    ax.scatter(
        mfnn.y_L_proxy,
        mfnn.resid,
        s=32,
        c=C["MFNN"],
        edgecolors=C["MFNN_stroke"],
        linewidths=0.5,
        zorder=2,
        label="residual MFNN",
    )
    ax.set_xlabel(
        r"$y_{L}^{\mathrm{proxy}}=\log_{10}\hat{D}_{\mathrm{LF\text{-}only}}$",
        fontsize=8,
    )
    ax.set_ylabel(r"$\log_{10}\hat{D}_{\mathrm{MFNN}}-\log_{10}D_{\mathrm{true}}$", fontsize=8)
    ax.text(
        0.02,
        0.95,
        "LF-only prediction as\nSutherland $D_{\\mathrm{LF}}$ proxy\n"
        r"(no explicit $y_L$ column)",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.5,
        color=C["ref_dark"],
    )
    box_spines(ax)
    panel_letter(ax, "b")

    fig.tight_layout(w_pad=1.2)
    cap = (
        "Figure 4. Protocol W residual topology for the residual MFNN "
        "(seed-mean predictions over seeds containing each sample_id; "
        "union of within_T test points). "
        r"(a) Absolute $\log_{10}D$ error versus temperature; the dashed line marks "
        r"$\log_{10}2$ (Factor-of-two threshold). HF-only points are shown for context. "
        r"(b) Signed residual versus an LF prior proxy $y_L^{\mathrm{proxy}}=\log_{10}"
        r"\hat{D}_{\mathrm{LF\text{-}only}}$, used because the prediction CSVs do not store "
        "an explicit Sutherland $D_{\\mathrm{LF}}$ column; shaded band is "
        r"$\pm\log_{10}2$. This figure visualizes residual structure only and does not "
        "alter frozen Protocol W table metrics. Not a PINN/PPINN formulation."
    )
    layers = (
        "L1_Background_and_Guides: Factor2 threshold / ±band, zero line\n"
        "L2_Data_Series: MFNN (and HF in a) residual scatters\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: (a)(b), proxy note"
    )
    _save(fig, "Fig4_protocol_W_residual_topology", cap, layers)
    plt.close(fig)


def figs1_alpha_mixing_weights() -> None:
    """Gemini SI Fig.S1 — alpha1/alpha2; FROZEN means in callout."""
    apply_style()
    a = pd.read_csv(RESULTS / "protocol_W_alpha_table.csv")
    fig, ax = plt.subplots(figsize=(W_SINGLE, 60 / 25.4))
    seeds = a.seed.astype(str).tolist()
    x = np.arange(len(seeds))
    w = 0.38
    ax.bar(
        x - w / 2,
        a.alpha_1,
        w,
        color=C["LF"],
        edgecolor=C["LF_stroke"],
        linewidth=0.6,
        label=r"$\alpha_1$ (linear)",
    )
    ax.bar(
        x + w / 2,
        a.alpha_2,
        w,
        color=C["MFNN"],
        edgecolor=C["MFNN_stroke"],
        linewidth=0.6,
        label=r"$\alpha_2$ (nonlinear residual)",
    )
    a1m, a1s = FROZEN["alpha1"]
    a2m, a2s = FROZEN["alpha2"]
    ax.axhline(a1m, color=C["LF_stroke"], lw=0.9, ls="--", alpha=0.85)
    ax.axhline(a2m, color=C["MFNN_stroke"], lw=0.9, ls="--", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([f"seed {s}" for s in seeds], fontsize=7.5, rotation=0)
    ax.set_ylabel(r"Mixing weight", fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper left", fontsize=7)
    ax.text(
        0.98,
        0.98,
        rf"$\alpha_1={a1m:.4f}\pm{a1s:.4f}$"
        + "\n"
        + rf"$\alpha_2={a2m:.4f}\pm{a2s:.4f}$",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=7,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=C["ref"], lw=0.5, alpha=0.95),
        zorder=5,
    )
    box_spines(ax)
    fig.tight_layout()
    cap = (
        "Figure S1. Protocol W residual-MFNN mixing weights $\\alpha_1$ (linear path) "
        "and $\\alpha_2$ (nonlinear residual path) extracted read-only from five "
        r"within_T checkpoints (seeds $0,1,2,42,123$). Dashed lines mark frozen seed "
        rf"means $\alpha_1={a1m:.4f}\pm{a1s:.4f}$ and $\alpha_2={a2m:.4f}\pm{a2s:.4f}$ "
        r"(population std, $\mathrm{ddof}=0$). SI diagnostic only; not a headline claim. "
        "Not a PINN/PPINN formulation. "
        "(Gemini SI Fig.S1; warehouse Keep: also retained as Fig6_alpha_mixing_weights.)"
    )
    layers = (
        "L1_Background_and_Guides: mean dashed lines\n"
        "L2_Data_Series: per-seed alpha bars\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: legend, frozen mean±std callout"
    )
    _save(fig, "FigS1_alpha_mixing_weights", cap, layers)
    for ext in ("pdf", "svg", "png"):
        src = FIG_DIR / f"FigS1_alpha_mixing_weights.{ext}"
        if src.exists():
            shutil.copy2(src, FIG_DIR / f"Fig6_alpha_mixing_weights.{ext}")
            shutil.copy2(src, JCP_FIG / f"Fig6_alpha_mixing_weights.{ext}")
    plt.close(fig)


def main() -> None:
    apply_style()
    fig3_protocol_W_parity_metrics()
    fig4_protocol_W_residual_topology()
    figs1_alpha_mixing_weights()
    print("P0 Gemini figures done.")


if __name__ == "__main__":
    main()
