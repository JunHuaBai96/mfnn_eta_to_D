#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gemini P2 SI figures: polish S2–S4 + new S5 ablation + S6 Protocol G.

Keeps Word-facing stems:
  FigS2_al80_posthoc_shift, FigS3_al80_anchor_k, FigS4_al80_upweight_w
Adds:
  FigS5_difftype_split_ablation  (Gemini-plan S5 role)
  FigS6_protocol_G_variance      (Gemini-plan S2 / Protocol G caution role)

No retrain; frozen numbers only; no PINN; no Kozlov.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _style import (  # noqa: E402
    C,
    FIG_DIR,
    FROZEN,
    JCP_FIG,
    RESULTS,
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


def _pop_std(s: pd.Series) -> float:
    return float(np.std(np.asarray(s, dtype=float), ddof=0))


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
                if ext in ("pdf", "png", "svg"):
                    shutil.copy2(path, JCP_FIG / f"{alt}.{ext}")
    (pack / "README.txt").write_text(
        f"Stem: {stem}\n\nCaption:\n{caption}\n\nLayers:\n{ai_layers}\n",
        encoding="utf-8",
    )
    print("saved", stem)


def figs2_posthoc() -> None:
    apply_style()
    ph = pd.read_csv(RESULTS / "AL80_posthoc_intercept_shift.csv")
    fig, ax = plt.subplots(figsize=(W_SINGLE, 90 / 25.4))
    raw = ph[(ph.model == "MFNN") & (ph.setting.str.startswith("k0_raw"))]
    shift = ph[(ph.model == "MFNN") & (ph.setting.str.startswith("k0_posthoc"))]
    cats = ["Raw held-out\n(no shift)", "Post-hoc B2\nintercept shift"]
    raw_m = float(raw.MAPE_pct.mean())
    raw_s = _pop_std(raw.MAPE_pct)
    sh_m, sh_s = FROZEN["S2_MAPE"]
    delta = float(shift.delta_log10.mean())
    delta_s = _pop_std(shift.delta_log10)
    vals = [raw_m, sh_m]
    errs = [raw_s, sh_s]
    x = np.array([0.0, 0.85])
    ax.bar(
        x,
        vals,
        0.55,
        yerr=errs,
        color=[C["tracer"], C["MFNN"]],
        edgecolor=[C["tracer_stroke"], C["MFNN_stroke"]],
        linewidth=0.6,
        capsize=2.5,
        error_kw=dict(lw=0.8, ecolor=C["ref_dark"]),
    )
    for xi, (v, e) in zip(x, zip(vals, errs)):
        ax.text(xi, v + e + 3, f"{v:.2f}±{e:.2f}%", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_xlim(-0.45, 1.30)
    ax.set_ylabel(r"MFNN MAPE (%)", fontsize=9)
    ax.set_ylim(0, max(vals) + max(errs) + 40)
    ax.text(
        0.5,
        1.02,
        "Oracle / counterfactual (SI only — not LOGO success)",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=C["tracer_stroke"],
        fontweight="bold",
    )
    ax.text(
        0.98,
        0.92,
        rf"$\delta={delta:.3f}\pm{delta_s:.3f}\approx-\log_{{10}}3$",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=7.5,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=C["MFNN_stroke"], lw=0.5),
    )
    box_spines(ax)
    fig.tight_layout()
    cap = (
        "Figure S2 (warehouse stem; Gemini-plan role S4 / oracle). Counterfactual Al80Cu20 "
        "tracer post-hoc intercept shift (SI only). Raw held-out MAPE versus post-hoc B2 shift "
        rf"(frozen ${sh_m:.2f}\pm{sh_s:.2f}\%$). Not Protocol W / LOGO success. Not PINN/PPINN."
    )
    _save(
        fig,
        "FigS4_al80_posthoc_shift",
        cap,
        "L1 none; L2 raw vs shift bars; L3 seed errors; L4 oracle banner",
        also=["fig_si_al80_posthoc_shift", "FigS2_al80_posthoc_shift"],
    )
    plt.close(fig)


def figs3_anchor_k() -> None:
    apply_style()
    sens = pd.read_csv(RESULTS / "AL80_tracer_anchor_sensitivity.csv")
    fig, ax = plt.subplots(figsize=(W_SINGLE, 60 / 25.4))
    modes = ["k0", "k1_lowT", "k1_highT", "k2"]
    labels = [r"$k=0$", r"$k=1$ low $T$", r"$k=1$ high $T$", r"$k=2$"]
    frozen = list(FROZEN["S1_MAPE"])
    stds = []
    for mode in modes:
        sub = sens[sens["mode"] == mode]["MFNN_MAPE_pct"]
        stds.append(_pop_std(sub))
    x = np.arange(len(modes))
    ax.bar(
        x,
        frozen,
        0.6,
        yerr=stds,
        color=C["tracer"],
        edgecolor=C["tracer_stroke"],
        linewidth=0.6,
        capsize=2.5,
        error_kw=dict(lw=0.8, ecolor=C["ref_dark"]),
    )
    for i, v in enumerate(frozen):
        ax.text(i, v + stds[i] + 4, f"{v:.1f}", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel(r"MFNN MAPE (%)", fontsize=9)
    ax.set_ylim(0, 250)
    ax.text(
        0.5,
        1.02,
        "Few-shot anchor diagnostic (SI only — not pure LOGO)",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=C["tracer_stroke"],
        fontweight="bold",
    )
    ax.text(
        0.98,
        0.05,
        r"Factor2 $=0$ (all $k$)",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7,
        color=C["ref_dark"],
    )
    box_spines(ax)
    fig.tight_layout()
    cap = (
        "Figure S3 (Gemini-plan role S3 / few-shot anchor). Al80Cu20 tracer anchor-$k$ "
        "sensitivity; frozen MAPE 178.20 / 169.55 / 175.27 / 142.93%; Factor2 = 0. SI only. "
        "Not PINN/PPINN."
    )
    _save(
        fig,
        "FigS3_al80_anchor_k",
        cap,
        "L1 none; L2 bars; L3 seed errors; L4 SI banner",
        also=["fig_si_al80_anchor_k", "FigS1_al80_anchor_k"],
    )
    plt.close(fig)


def figs4_upweight() -> None:
    apply_style()
    uw = pd.read_csv(RESULTS / "AL80_anchor_upweight_k2.csv")
    fig, ax1 = plt.subplots(figsize=(W_SINGLE, 60 / 25.4))
    ws = [1.0, 5.0, 10.0]
    frozen_mape = list(FROZEN["S3_MAPE"])
    mape_std, f2_m = [], []
    for w in ws:
        sub = uw[uw.w_anchor == w]
        mape_std.append(_pop_std(sub.MFNN_MAPE_pct))
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
    )
    ax1.fill_between(
        ws,
        [m - s for m, s in zip(frozen_mape, mape_std)],
        [m + s for m, s in zip(frozen_mape, mape_std)],
        color=C["tracer"],
        alpha=0.15,
    )
    for w, m in zip(ws, frozen_mape):
        ax1.text(w, m + 6, f"{m:.0f}%", ha="center", fontsize=7.5, color=C["tracer_stroke"])
    ax1.set_xlabel(r"Anchor weight $w$", fontsize=9)
    ax1.set_ylabel(r"MFNN MAPE (%)", fontsize=9, color=C["tracer_stroke"])
    ax1.set_ylim(0, 145)
    ax1.set_xticks(ws)
    ax1.tick_params(axis="y", labelcolor=C["tracer_stroke"])
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
    )
    ax2.set_ylabel(r"Factor2", fontsize=9, color=C["HF_stroke"])
    ax2.set_ylim(0, 1.15)
    ax2.tick_params(axis="y", labelcolor=C["HF_stroke"])
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(C["HF_stroke"])
    ax2.spines["top"].set_visible(False)
    ax1.text(
        0.5,
        1.02,
        r"Counterfactual $k=2$ up-weighting (SI only)",
        transform=ax1.transAxes,
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=C["tracer_stroke"],
        fontweight="bold",
    )
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="center right", fontsize=7)
    ax1.spines["top"].set_visible(False)
    fig.tight_layout()
    cap = (
        "Figure S4. Al80Cu20 tracer $k=2$ anchor up-weighting $w=1\\to5\\to10$ "
        "(frozen MAPE $122\\to48\\to31\\%$). SI counterfactual only; not LOGO success. Not PINN/PPINN."
    )
    _save(
        fig,
        "FigS6_al80_upweight_w",
        cap,
        "L1 none; L2 MAPE/Factor2; L3 MAPE band; L4 SI banner",
        also=["FigS3_al80_upweight_w", "FigS4_al80_upweight_w"],
    )
    plt.close(fig)


def figs5_difftype_split_ablation() -> None:
    """Gemini-plan S5: separate tracer/inter nets vs joint+one-hot (negative result)."""
    apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(W_MID, 62 / 25.4))

    # (a) Al80 stratified MAPE: joint vs separate (FROZEN)
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
    ax.legend(loc="upper right", fontsize=6.5)
    box_spines(ax)
    panel_letter(ax, "a")

    # (b) pool-level mean±std from separate-models report (honest; exclude exploding Al70 for inter)
    ax = axes[1]
    # From LOGO_AlCu_separate_models_REPORT: tracer 99.66±54.55; inter robust 17.96±16.90; joint 39.43±39.71
    cats = ["Separate\ntracer pool", "Separate\ninter (excl. Al70)", "Joint+one-hot\n(13 folds)"]
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
        ax.text(i, m + s + 2, f"{m:.1f}±{s:.1f}", ha="center", va="bottom", fontsize=6.5)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=7)
    ax.set_ylabel(r"Mean LOGO MFNN MAPE (%)", fontsize=8)
    ax.set_ylim(0, 170)
    ax.set_title("Pool-level LOGO means (caution)", fontsize=8)
    ax.text(
        0.02,
        0.98,
        "Al70Cu30_inter explosion\nexcluded from inter mean\n(see separate_models report)",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6,
        color=C["ref_dark"],
    )
    box_spines(ax)
    panel_letter(ax, "b")

    fig.tight_layout(w_pad=1.1)
    cap = (
        "Figure S5 (Gemini-plan role S5 / modality-split ablation). Separate tracer-only and "
        "inter-only residual MFNN pools versus joint training with diff_type one-hot. "
        rf"(a) Stratified $\mathrm{{Al}}_{{80}}\mathrm{{Cu}}_{{20}}$: separate "
        rf"${FROZEN['Al80_tracer_sep']:.0f}\%/{FROZEN['Al80_inter_sep']:.0f}\%$ vs joint "
        rf"${FROZEN['Al80_tracer_joint']:.1f}\%/{FROZEN['Al80_inter_joint']:.1f}\%$. "
        "(b) Pool-level LOGO means (inter mean excludes exploding Al70Cu30_inter fold). "
        "Negative result: splitting does not fix sparse tracer neighborhoods. SI only; not PINN/PPINN."
    )
    _save(
        fig,
        "FigS5_difftype_split_ablation",
        cap,
        "L1 none; L2 ablation bars; L3 errors; L4 caution titles",
        also=["Fig7_ablation_separate_vs_joint"],
    )
    plt.close(fig)


def figs6_protocol_G_variance() -> None:
    """Gemini-plan S2 role: Protocol G caution / seed variance (numbered S6 to avoid Word S2 clash)."""
    apply_style()
    wg = pd.read_csv(RESULTS / "seed_WG_summary.csv")
    fig, axes = plt.subplots(1, 2, figsize=(W_MID, 62 / 25.4))

    ax = axes[0]
    means = [FROZEN["W_MFNN_MAPE"][0], FROZEN["G_MFNN_MAPE"][0]]
    stds = [FROZEN["W_MFNN_MAPE"][1], FROZEN["G_MFNN_MAPE"][1]]
    cols = [C["W"], C["G"]]
    ecs = [C["MFNN_stroke"], C["HF_stroke"]]
    x = np.arange(2)
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
        ax.text(i, m + s + 1.5, f"{m:.2f}±{s:.2f}%", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(["Protocol W\n(primary)", "Protocol G\n(caution)"], fontsize=8)
    ax.set_ylabel(r"MFNN MAPE (%)", fontsize=9)
    ax.set_ylim(0, 55)
    ax.set_title("Mean ± seed std (frozen)", fontsize=8)
    box_spines(ax)
    panel_letter(ax, "a")

    ax = axes[1]
    for proto, color, stroke, mk in [
        ("W", C["W"], C["MFNN_stroke"], "o"),
        ("G", C["G"], C["HF_stroke"], "s"),
    ]:
        sub = wg[(wg.protocol == proto) & (wg.model == "MFNN")].copy()
        sub["seed"] = pd.Categorical(sub.seed, categories=SEEDS, ordered=True)
        sub = sub.sort_values("seed")
        ax.plot(
            range(len(SEEDS)),
            sub.MAPE_pct.values,
            "-o" if mk == "o" else "-s",
            color=color,
            markerfacecolor=color,
            markeredgecolor=stroke,
            markeredgewidth=0.6,
            markersize=5,
            lw=1.25,
            label=f"Protocol {proto}",
        )
    ax.set_xticks(range(len(SEEDS)))
    ax.set_xticklabels([str(s) for s in SEEDS], fontsize=8)
    ax.set_xlabel(r"Seed", fontsize=9)
    ax.set_ylabel(r"MFNN MAPE (%)", fontsize=9)
    ax.set_title("Per-seed trajectories (caution for G)", fontsize=8)
    ax.legend(loc="best", fontsize=7)
    ax.text(
        0.98,
        0.02,
        "G hold-outs are Al–Cu groups;\nlarge seed variance: not a headline claim",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6,
        color=C["ref_dark"],
    )
    box_spines(ax)
    panel_letter(ax, "b")

    fig.tight_layout(w_pad=1.2)
    cap = (
        "Figure S6 (Gemini-plan role S2 / Protocol G variance; numbered S6 because Word SI Fig. S2 "
        "already hosts the post-hoc oracle). Protocol W versus random between-group Protocol G "
        rf"(MFNN MAPE ${FROZEN['W_MFNN_MAPE'][0]}\pm{FROZEN['W_MFNN_MAPE'][1]}\%$ vs "
        rf"${FROZEN['G_MFNN_MAPE'][0]}\pm{FROZEN['G_MFNN_MAPE'][1]}\%$). "
        "(a) Frozen mean±std; (b) per-seed trajectories. Protocol G is cautionary only. Not PINN/PPINN."
    )
    _save(
        fig,
        "FigS2_protocol_G_variance",
        cap,
        "L1 none; L2 W/G bars and seed lines; L3 errors; L4 caution",
        also=["Fig8_protocol_W_vs_G", "FigS6_protocol_G_variance"],
    )
    plt.close(fig)


def main() -> None:
    apply_style()
    figs2_posthoc()
    figs3_anchor_k()
    figs4_upweight()
    figs5_difftype_split_ablation()
    figs6_protocol_G_variance()
    print("P2 SI figures done.")


if __name__ == "__main__":
    main()
