#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout-only fixes for Fig3, Fig4, Fig6, FigS5, FigS6 (Lu box; no number changes)."""
from __future__ import annotations

import math
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

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
    box_spines,
    panel_letter,
)

SEEDS = [0, 1, 2, 42, 123]
MODEL_LABELS = {"LF_only": "LF-only", "HF_only": "HF-only", "MFNN": "residual MFNN"}
MODEL_COLORS = {"LF_only": C["LF"], "HF_only": C["HF"], "MFNN": C["MFNN"]}
MODEL_STROKES = {"LF_only": C["LF_stroke"], "HF_only": C["HF_stroke"], "MFNN": C["MFNN_stroke"]}
LOG10_2 = math.log10(2.0)


def _save(fig, stem: str, caption: str, ai_layers: str, also: list[str] | None = None) -> None:
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
        if also:
            for alt in also:
                shutil.copy2(path, FIG_DIR / f"{alt}.{ext}")
                shutil.copy2(path, JCP_FIG / f"{alt}.{ext}")
    (pack / "README.txt").write_text(
        f"Stem: {stem}\n\nCaption:\n{caption}\n\nLayers:\n{ai_layers}\n",
        encoding="utf-8",
    )
    print("saved", stem)


def fig3_protocol_W_parity_metrics() -> None:
    """Equal-height panels via fixed axes; short horizontal tick labels; frozen bars."""
    apply_style()
    # Fixed axes positions => identical heights (avoid tight-bbox reshaping)
    fig = plt.figure(figsize=(W_DOUBLE, 2.55))
    ax_a = fig.add_axes([0.08, 0.22, 0.28, 0.68])
    ax_b = fig.add_axes([0.48, 0.22, 0.22, 0.68])
    ax_c = fig.add_axes([0.76, 0.22, 0.22, 0.68])
    axes = [ax_a, ax_b, ax_c]

    order = ["LF_only", "HF_only", "MFNN"]
    # Short horizontal labels (Lu 0°); full names live in panel (a) legend
    labels = ["LF-only", "HF-only", "MFNN"]
    colors = [MODEL_COLORS[m] for m in order]
    strokes = [MODEL_STROKES[m] for m in order]
    marker_map = {"LF_only": "s", "HF_only": "^", "MFNN": "o"}

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
    )
    ax.plot(lims, lims, color=C["ref_dark"], lw=0.9, zorder=1)
    for m in order:
        sub = pts[pts.model == m].copy()
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
            )
    r2m, r2s = FROZEN["W_MFNN_R2"]
    ax.text(
        0.04, 0.96,
        rf"$R^2_{{\mathrm{{MFNN}}}}={r2m:.3f}\pm{r2s:.3f}$" + "\n"
        + r"(frozen; $n_{\mathrm{test}}=15$/seed)",
        transform=ax.transAxes, fontsize=6.5, va="top", ha="left",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=C["MFNN_stroke"], lw=0.5, alpha=0.92),
    )
    ax.set_xlabel(r"$\log_{10} D_{\mathrm{true}}$", fontsize=9)
    ax.set_ylabel(r"$\log_{10} \hat{D}$ (seed mean)", fontsize=9)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    handles = [
        Line2D([0], [0], marker=marker_map[m], color="none",
               markerfacecolor=MODEL_COLORS[m], markeredgecolor=MODEL_STROKES[m],
               markersize=6, label=MODEL_LABELS[m])
        for m in order
    ]
    handles.append(
        Line2D([0], [0], marker="o", color="none", markerfacecolor="none",
               markeredgecolor=C["ref_dark"], markersize=6, label="partial seed overlap")
    )
    ax.legend(handles=handles, loc="lower right", fontsize=5.5,
              handletextpad=0.25, borderpad=0.2, frameon=False)
    box_spines(ax)
    panel_letter(ax, "a", x=-0.16)

    ax = axes[1]
    x = np.array([0.0, 1.35, 2.7])
    width = 0.7
    mape_m = [FROZEN["W_LF_MAPE"][0], FROZEN["W_HF_MAPE"][0], FROZEN["W_MFNN_MAPE"][0]]
    mape_s = [FROZEN["W_LF_MAPE"][1], FROZEN["W_HF_MAPE"][1], FROZEN["W_MFNN_MAPE"][1]]
    ax.bar(x, mape_m, width, yerr=mape_s, color=colors, edgecolor=strokes,
           linewidth=0.6, capsize=2.5, error_kw=dict(lw=0.8, ecolor=C["ref_dark"]))
    for i, (v, s) in enumerate(zip(mape_m, mape_s)):
        ax.text(i, v + s + 4, f"{v:.2f}", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_xlim(-0.7, 3.4)
    ax.set_ylabel("Mean absolute\npercentage error (%)", fontsize=8)
    ax.set_ylim(0, 145)
    box_spines(ax)
    panel_letter(ax, "b")

    ax = axes[2]
    f2_m = [FROZEN["W_LF_F2"][0], FROZEN["W_HF_F2"][0], FROZEN["W_MFNN_F2"][0]]
    f2_s = [FROZEN["W_LF_F2"][1], FROZEN["W_HF_F2"][1], FROZEN["W_MFNN_F2"][1]]
    ax.bar(x, f2_m, width, yerr=f2_s, color=colors, edgecolor=strokes,
           linewidth=0.6, capsize=2.5, error_kw=dict(lw=0.8, ecolor=C["ref_dark"]))
    for i, (v, s) in enumerate(zip(f2_m, f2_s)):
        y_ann = v + s + 0.06
        if i == 0:
            y_ann = v + s + 0.08
        ax.text(i, min(y_ann, 1.15), f"{v:.3g}", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_xlim(-0.7, 3.4)
    ax.set_ylabel("Factor-of-two\naccuracy", fontsize=8)
    ax.set_ylim(0, 1.25)
    ax.axhline(1.0, color=C["ref"], lw=0.7, ls="--", zorder=0)
    box_spines(ax)
    panel_letter(ax, "c")

    # Bypass global tight bbox so fixed axes stay aligned
    for ext_stem in ("Fig3_protocol_W_parity_metrics",):
        pass
    cap = (
        "Figure 3. Protocol W parity + frozen MAPE/Factor2. "
        "Layout fix: fixed equal-height axes; short MFNN tick labels. "
        "Frozen metrics unchanged."
    )
    layers = (
        "L1_Background_and_Guides: factor-of-two band, 1:1 line, Factor2=1 dashed\n"
        "L2_Data_Series: parity markers by model; MAPE/Factor2 bars\n"
        "L3_ErrorBars_and_Arrows: seed-std on parity; frozen std on bars\n"
        "L4_Typography_and_Math: (a)(b)(c), R2 callout, bar annotations"
    )
    # Custom save without tight crop
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    JCP_FIG.mkdir(parents=True, exist_ok=True)
    pack = VECTOR_PACK / "Fig3_protocol_W_parity_metrics"
    pack.mkdir(parents=True, exist_ok=True)
    stem = "Fig3_protocol_W_parity_metrics"
    for ext in ("pdf", "svg", "png"):
        kw = {"dpi": 600, "bbox_inches": None, "pad_inches": 0.02} if ext == "png" else {"bbox_inches": None, "pad_inches": 0.02}
        path = FIG_DIR / f"{stem}.{ext}"
        fig.savefig(path, **kw)
        import shutil as _sh
        _sh.copy2(path, pack / f"{stem}.{ext}")
        _sh.copy2(path, JCP_FIG / f"{stem}.{ext}")
    (pack / "README.txt").write_text(
        f"Stem: {stem}\n\nCaption:\n{cap}\n\nLayers:\n{layers}\n", encoding="utf-8"
    )
    print("saved", stem)
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
    """Legend moved off data; Lu box unchanged numbers."""
    apply_style()
    long = _load_seed_predictions()
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
    lf = ens[ens.model == "LF_only"][["sample_id", "pred_log10D_mean"]].rename(
        columns={"pred_log10D_mean": "y_L_proxy"}
    )
    mfnn = ens[ens.model == "MFNN"].merge(lf, on="sample_id", how="left")
    hf = ens[ens.model == "HF_only"].merge(lf, on="sample_id", how="left")

    fig, axes = plt.subplots(1, 2, figsize=(W_MID, 58 / 25.4))

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
    ax.set_ylabel(
        r"$|\Delta\log_{10} D|=|\log_{10}\hat{D}-\log_{10}D_{\mathrm{true}}|$",
        fontsize=8,
    )
    # Factor2 note + legend in upper-right whitespace (away from low-T high-error points)
    ax.text(
        0.98,
        0.72,
        r"dashed: $\log_{10}2\approx0.301$" + "\n(Factor2)",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.5,
        color=C["ref_dark"],
    )
    ax.legend(loc="upper right", fontsize=6.5, frameon=False, borderpad=0.2)
    box_spines(ax)
    panel_letter(ax, "a")

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
    ax.set_ylabel(
        r"$\log_{10}\hat{D}_{\mathrm{MFNN}}-\log_{10}D_{\mathrm{true}}$", fontsize=8
    )
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
        "Figure 4. Protocol W residual topology. Layout fix: panel (a) legend moved to "
        "upper-right to clear low-T markers. Frozen Protocol W metrics unchanged."
    )
    layers = (
        "L1_Background_and_Guides: Factor2 threshold / ±band, zero line\n"
        "L2_Data_Series: MFNN (and HF in a) residual scatters\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: (a)(b), proxy note"
    )
    _save(fig, "Fig4_protocol_W_residual_topology", cap, layers)
    plt.close(fig)


def fig6_al80_label_conflict() -> None:
    """Rebuild Fig.6 with closed Lu box + mathtext ticks (frozen MAPEs)."""
    apply_style()
    raw = pd.read_csv(ROOT / "data" / "melt_diffusion_data.csv")
    al80 = raw[(raw["x_Cu"].round(2) == 0.20) & (raw["fidelity"] == "HF")].copy()
    al80["diff_type_norm"] = al80["diff_type"].replace(
        {"interdiffusivity": "inter", "inter": "inter", "tracer": "tracer"}
    )
    tracer = al80[al80["diff_type_norm"] == "tracer"].sort_values("T_K")
    inter = al80[al80["diff_type_norm"] == "inter"].sort_values("T_K")

    fig, axes = plt.subplots(1, 2, figsize=(W_MID, 60 / 25.4))

    ax = axes[0]
    ax.scatter(
        tracer["T_K"], tracer["D_m2s"] * 1e9,
        s=36, c=C["tracer"], edgecolors=C["tracer_stroke"],
        linewidths=0.6, marker="o", zorder=2, label="Cu tracer (Zhang et al.)",
    )
    ax.scatter(
        inter["T_K"], inter["D_m2s"] * 1e9,
        s=42, c=C["inter"], edgecolors=C["inter_stroke"],
        linewidths=0.6, marker="s", zorder=3, label="Interdiffusivity",
    )
    t_ref = 983.0
    d_tr = float(tracer.loc[(tracer["T_K"] - t_ref).abs().idxmin(), "D_m2s"]) * 1e9
    d_in = float(inter.loc[(inter["T_K"] - t_ref).abs().idxmin(), "D_m2s"]) * 1e9
    ratio = d_in / d_tr
    ax.annotate(
        "", xy=(t_ref, d_in), xytext=(t_ref, d_tr),
        arrowprops=dict(arrowstyle="<->", color=C["ref"], lw=1.0),
    )
    ax.text(
        t_ref + 12, 0.5 * (d_in + d_tr),
        rf"$\sim{ratio:.1f}\times$", fontsize=8, color=C["ref_dark"], va="center", ha="left",
    )
    ax.set_xlabel(r"Temperature $T$ (K)", fontsize=9)
    ax.set_ylabel(r"$D$ ($10^{-9}\,\mathrm{m}^{2}\,\mathrm{s}^{-1}$)", fontsize=9)
    ax.legend(loc="lower right", fontsize=6.5, frameon=False)
    box_spines(ax)
    panel_letter(ax, "a")

    ax = axes[1]
    cats = [
        r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$" + "\ntracer",
        r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$" + "\ninter",
    ]
    mape = [FROZEN["Al80_tracer_MAPE"], FROZEN["Al80_inter_MAPE"]]
    f2 = [0.0, 1.0]
    n = [10, 2]
    cols = [C["tracer"], C["inter"]]
    ecs = [C["tracer_stroke"], C["inter_stroke"]]
    x = np.arange(2)
    ax.bar(x, mape, width=0.55, color=cols, edgecolor=ecs, linewidth=0.6)
    for i, (m, f, ni) in enumerate(zip(mape, f2, n)):
        ax.text(
            i, (m - 42 if m >= 100 else m + 8), f"MAPE={m:.1f}%\nFac2={f:.2f}\nn={ni}",
            ha="center", va=("top" if m >= 100 else "bottom"), fontsize=6.5, color=("white" if m >= 100 else C["ref_dark"]),
        )
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylabel(r"MFNN MAPE (%)", fontsize=9)
    ax.set_ylim(0, 230)
    ax.text(
        0.5, -0.22, "Same composition; incompatible $D$ scales",
        transform=ax.transAxes, ha="center", va="top", fontsize=7,
        style="italic", color=C["ref"],
    )
    box_spines(ax)
    panel_letter(ax, "b")

    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.20, top=0.86, wspace=0.35)
    fig.suptitle(
        r"Label conflict at $\mathrm{Al}_{80}\mathrm{Cu}_{20}$: tracer vs interdiffusivity",
        fontsize=9, fontweight="bold", color=C["ref_dark"], y=0.98,
    )
    cap = (
        r"Fig. 6. Label conflict at $\mathrm{Al}_{80}\mathrm{Cu}_{20}$. "
        r"(a) HF $D$ versus $T$: Cu-tracer below interdiffusivity by "
        rf"$\sim{ratio:.1f}\times$ near 983 K. "
        r"(b) LOGO MFNN MAPE after diff_type split + one-hot: "
        rf"tracer ${FROZEN['Al80_tracer_MAPE']:.1f}\%$ (Factor2 $=0$, $n=10$) versus "
        rf"inter ${FROZEN['Al80_inter_MAPE']:.1f}\%$ (Factor2 $=1$, $n=2$). "
        "Layout fix: closed Lu box + mathtext labels."
    )
    layers = (
        "L1 guides: 3x arrow\n"
        "L2 data: tracer/inter scatter + MAPE bars\n"
        "L3 none\n"
        "L4 typography"
    )
    _save(fig, "Fig6_Al80_tracer_inter", cap, layers, also=["fig3_Al80_tracer_inter"])
    plt.close(fig)


def figs5_difftype_split_ablation() -> None:
    """Move Al70 note below axes so it cannot cover 99.7±54.5."""
    apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(W_MID, 68 / 25.4))

    ax = axes[0]
    labels = [
        r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$" + "\ntracer",
        r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$" + "\ninter",
    ]
    sep = [FROZEN["Al80_tracer_sep"], FROZEN["Al80_inter_sep"]]
    joint = [FROZEN["Al80_tracer_joint"], FROZEN["Al80_inter_joint"]]
    x = np.arange(2)
    w = 0.35
    ax.bar(
        x - w / 2,
        sep,
        w,
        color=C["ref"],
        edgecolor=C["ref_dark"],
        linewidth=0.6,
        label="Separate pools (12-D)",
    )
    ax.bar(
        x + w / 2,
        joint,
        w,
        color=[C["tracer"], C["inter"]],
        edgecolor=[C["tracer_stroke"], C["inter_stroke"]],
        linewidth=0.6,
        label="Joint + diff_type one-hot",
    )
    for bars in ax.containers:
        for rect in bars:
            h = rect.get_height()
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                h + 3,
                f"{h:.1f}%",
                ha="center",
                va="bottom",
                fontsize=7,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel(r"MFNN MAPE (%)", fontsize=9)
    ax.set_ylim(0, 210)
    ax.set_title("Al80 hold-outs (negative ablation)", fontsize=8)
    ax.legend(loc="upper right", fontsize=6.5, frameon=False)
    box_spines(ax)
    panel_letter(ax, "a")

    ax = axes[1]
    cats = [
        "Separate\ntracer pool",
        "Separate\ninter (excl. Al70)",
        "Joint+one-hot\n(13 folds)",
    ]
    means = [99.66, 17.96, FROZEN["LOGO_mean"][0]]
    stds = [54.55, 16.90, FROZEN["LOGO_mean"][1]]
    cols = [C["tracer"], C["inter"], C["MFNN"]]
    ecs = [C["tracer_stroke"], C["inter_stroke"], C["MFNN_stroke"]]
    x = np.arange(3)
    ax.bar(
        x,
        means,
        0.55,
        yerr=stds,
        color=cols,
        edgecolor=ecs,
        linewidth=0.6,
        capsize=2.5,
        error_kw=dict(lw=0.8, ecolor=C["ref_dark"]),
    )
    for i, (m, s) in enumerate(zip(means, stds)):
        if i == 0:
            ax.text(i + 0.28, m + s + 8, f"{m:.1f}±{s:.1f}", ha="left", va="bottom", fontsize=6.5)
        else:
            ax.text(i, m + s + 4, f"{m:.1f}±{s:.1f}", ha="center", va="bottom", fontsize=6.5)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=7)
    ax.set_ylabel(r"Mean LOGO MFNN MAPE (%)", fontsize=8)
    ax.set_ylim(0, 175)
    ax.set_title("Pool-level LOGO means (caution)", fontsize=8)
    # NOTE below axes — no interior overlap with bar labels
    ax.text(
        0.5,
        -0.30,
        r"Note: $\mathrm{Al}_{70}\mathrm{Cu}_{30}$ inter explosion excluded from inter mean"
        "\n(see separate_models report)",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=6,
        color=C["ref_dark"],
    )
    box_spines(ax)
    panel_letter(ax, "b")

    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.22, top=0.90, wspace=0.32)
    cap = (
        "Figure S5. Separate tracer/inter residual MFNN pools versus joint + one-hot "
        "(negative ablation). Layout fix: Al70 note moved below panel (b). "
        "Frozen Al80 MAPEs unchanged."
    )
    _save(
        fig,
        "FigS5_difftype_split_ablation",
        cap,
        "L1 none; L2 ablation bars; L3 errors; L4 caution",
        also=["Fig7_ablation_separate_vs_joint"],
    )
    plt.close(fig)


def figs6_al80_upweight() -> None:
    """Closed top spine; MAPE labels clear of markers/edge."""
    apply_style()
    uw = pd.read_csv(RESULTS / "AL80_anchor_upweight_k2.csv")
    fig, ax1 = plt.subplots(figsize=(W_SINGLE, 62 / 25.4))
    ws = [1.0, 5.0, 10.0]
    frozen_mape = list(FROZEN["S3_MAPE"])
    mape_std, f2_m = [], []
    for w in ws:
        sub = uw[uw.w_anchor == w]
        mape_std.append(float(np.std(np.asarray(sub.MFNN_MAPE_pct, dtype=float), ddof=0)))
        f2_m.append(float(sub.MFNN_Factor2.mean()))
    ax1.plot(
        ws,
        frozen_mape,
        "-o",
        color=C["tracer"],
        markerfacecolor=C["tracer"],
        markeredgecolor=C["tracer_stroke"],
        markersize=6.5,
        lw=1.4,
        label="MAPE",
        zorder=3,
    )
    ax1.fill_between(
        ws,
        [m - s for m, s in zip(frozen_mape, mape_std)],
        [m + s for m, s in zip(frozen_mape, mape_std)],
        color=C["tracer"],
        alpha=0.15,
        zorder=1,
    )
    # Place labels clear of markers and top spine
    for w, m in zip(ws, frozen_mape):
        if w == 1.0:
            ax1.annotate(
                f"{m:.0f}%",
                xy=(w, m),
                xytext=(w + 0.55, m - 8),
                fontsize=7.5,
                color=C["tracer_stroke"],
                ha="left",
                va="center",
                arrowprops=dict(arrowstyle="-", color=C["tracer_stroke"], lw=0.5),
            )
        else:
            ax1.text(
                w,
                m + 7,
                f"{m:.0f}%",
                ha="center",
                va="bottom",
                fontsize=7.5,
                color=C["tracer_stroke"],
            )
    ax1.set_xlabel(r"Anchor weight $w$", fontsize=9)
    ax1.set_ylabel(r"MFNN MAPE (%)", fontsize=9, color=C["tracer_stroke"])
    ax1.set_ylim(0, 150)
    ax1.set_xticks(ws)
    ax1.tick_params(axis="y", labelcolor=C["tracer_stroke"], direction="in", left=True, right=False)

    ax2 = ax1.twinx()
    ax2.plot(
        ws,
        f2_m,
        "-s",
        color=C["HF"],
        markerfacecolor=C["HF"],
        markeredgecolor=C["HF_stroke"],
        markersize=6,
        lw=1.4,
        label="Factor2",
        zorder=2,
    )
    ax2.set_ylabel(r"Factor2", fontsize=9, color=C["HF_stroke"])
    ax2.set_ylim(0, 1.15)
    ax2.tick_params(axis="y", labelcolor=C["HF_stroke"], direction="in", right=True, left=False)

    # Full closed box on primary; twin keeps top/right
    for side in ("top", "right", "bottom", "left"):
        ax1.spines[side].set_visible(True)
        ax1.spines[side].set_linewidth(0.75)
        ax1.spines[side].set_color("#333333")
    ax2.spines["top"].set_visible(True)
    ax2.spines["top"].set_linewidth(0.75)
    ax2.spines["top"].set_color("#333333")
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_linewidth(0.75)
    ax2.spines["right"].set_color(C["HF_stroke"])
    ax2.spines["left"].set_visible(False)
    ax2.spines["bottom"].set_visible(False)

    ax1.text(
        0.5,
        1.04,
        r"Counterfactual $k=2$ up-weighting (SI only)",
        transform=ax1.transAxes,
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=C["tracer_stroke"],
        fontweight="bold",
        clip_on=False,
    )
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="center right", fontsize=7, frameon=False)
    ax1.tick_params(axis="x", direction="in", top=True, bottom=True)
    fig.subplots_adjust(left=0.16, right=0.84, bottom=0.16, top=0.86)
    cap = (
        "Figure S6. Al80Cu20 tracer $k=2$ anchor up-weighting $w=1\\to5\\to10$ "
        "(frozen MAPE $122\\to48\\to31\\%$). Layout fix: closed top spine; MAPE labels nudged. "
        "SI counterfactual only."
    )
    _save(
        fig,
        "FigS6_al80_upweight_w",
        cap,
        "L1 none; L2 MAPE/Factor2; L3 MAPE band; L4 SI banner",
        also=["FigS3_al80_upweight_w", "FigS4_al80_upweight_w"],
    )
    plt.close(fig)


def main() -> None:
    apply_style()
    fig3_protocol_W_parity_metrics()
    fig4_protocol_W_residual_topology()
    fig6_al80_label_conflict()
    figs5_difftype_split_ablation()
    figs6_al80_upweight()
    print("Layout fixes done for Fig3/4/6/S5/S6.")


if __name__ == "__main__":
    main()
