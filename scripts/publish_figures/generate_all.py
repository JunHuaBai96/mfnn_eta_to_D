#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate Fig1–Fig9 + FigS1–S3 to JCP/Elsevier figure style.

Data-backed only. Frozen headline numbers from FROZEN. Does not retrain.
Run from repo root:
  python scripts/publish_figures/generate_all.py
"""
from __future__ import annotations

import math
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.patches import FancyBboxPatch as FBox

from _style import (
    VECTOR_PACK,
    C,
    DATA,
    FIG_DIR,
    FROZEN,
    JCP_FIG,
    RESULTS,
    ROOT,
    W_DOUBLE,
    W_FIG4,
    W_FIG5,
    W_MID,
    W_SINGLE,
    apply_style,
    despine,
    box_spines,
    panel_letter,
    save_figure,
)

SEEDS = [0, 1, 2, 42, 123]
MODELS = ["LF_only", "HF_only", "MFNN"]
MODEL_LABELS = {"LF_only": "LF-only", "HF_only": "HF-only", "MFNN": "MFNN"}
MODEL_COLORS = {"LF_only": C["LF"], "HF_only": C["HF"], "MFNN": C["MFNN"]}
MODEL_STROKES = {"LF_only": C["LF_stroke"], "HF_only": C["HF_stroke"], "MFNN": C["MFNN_stroke"]}
MODALITY_COLORS = {
    "tracer": C["tracer"],
    "inter": C["inter"],
    "impurity": C["impurity"],
    "self": C["self"],
}


def _pop_std(s: pd.Series) -> float:
    return float(np.std(s.to_numpy(dtype=float), ddof=0))


# ---------------------------------------------------------------------------
# Fig1 — Residual MFNN schema (Lu PNAS 2020 style, 4-panel)
# ---------------------------------------------------------------------------
def fig1_schema() -> None:
    """Delegate to fig1_lu_style.py (node diagrams B–D + physical panel A)."""
    from fig1_lu_style import build_figure
    build_figure()


# Fig2 — Protocol W metrics + parity
# ---------------------------------------------------------------------------
def fig2_protocolW() -> None:
    apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(W_DOUBLE, 60 / 25.4))
    order = ["LF_only", "HF_only", "MFNN"]
    x = np.arange(len(order))
    width = 0.62

    # Frozen means/std for display
    mape_m = [FROZEN["W_LF_MAPE"][0], FROZEN["W_HF_MAPE"][0], FROZEN["W_MFNN_MAPE"][0]]
    mape_s = [FROZEN["W_LF_MAPE"][1], FROZEN["W_HF_MAPE"][1], FROZEN["W_MFNN_MAPE"][1]]
    f2_m = [FROZEN["W_LF_F2"][0], FROZEN["W_HF_F2"][0], FROZEN["W_MFNN_F2"][0]]
    f2_s = [FROZEN["W_LF_F2"][1], FROZEN["W_HF_F2"][1], FROZEN["W_MFNN_F2"][1]]
    colors = [MODEL_COLORS[m] for m in order]
    strokes = [MODEL_STROKES[m] for m in order]
    labels = [MODEL_LABELS[m] for m in order]

    # (a) MAPE
    ax = axes[0]
    bars = ax.bar(x, mape_m, width, yerr=mape_s, color=colors, edgecolor=strokes,
                  linewidth=0.6, capsize=2.5, error_kw=dict(lw=0.8, ecolor=C["ref_dark"]))
    for i, (v, s) in enumerate(zip(mape_m, mape_s)):
        ax.text(i, v + s + 4, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Mean absolute\npercentage error (%)", fontsize=8)
    ax.set_ylim(0, 145)
    box_spines(ax)
    panel_letter(ax, "a")

    # (b) Factor2 — place annotations carefully to avoid errorbar collision
    ax = axes[1]
    ax.bar(x, f2_m, width, yerr=f2_s, color=colors, edgecolor=strokes,
           linewidth=0.6, capsize=2.5, error_kw=dict(lw=0.8, ecolor=C["ref_dark"]))
    for i, (v, s) in enumerate(zip(f2_m, f2_s)):
        # put label above error bar with enough clearance; LF lower bar gets space above
        y_ann = min(v + s + 0.06, 1.12)
        if i == 0:
            y_ann = v + s + 0.08
        ax.text(i, y_ann, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Factor-of-two\naccuracy", fontsize=8)
    ax.set_ylim(0, 1.25)
    ax.axhline(1.0, color=C["ref"], lw=0.7, ls="--", zorder=0)
    box_spines(ax)
    panel_letter(ax, "b")

    # (c) parity from ensemble CSV (MFNN only for clarity + all three markers)
    ax = axes[2]
    pts = pd.read_csv(RESULTS / "protocol_W_parity_ensemble_points.csv")
    # band ±log10(2)
    lims = [-9.2, -7.6]
    ax.fill_between(lims, [l - math.log10(2) for l in lims], [l + math.log10(2) for l in lims],
                    color=C["band"], alpha=0.45, zorder=0, label=r"$\pm\log_{10}2$")
    ax.plot(lims, lims, color=C["ref_dark"], lw=0.9, ls="-", zorder=1, label="1:1")

    marker_map = {"LF_only": "s", "HF_only": "^", "MFNN": "o"}
    for m in order:
        sub = pts[pts.model == m]
        ax.scatter(
            sub.y_true_log10D, sub.pred_log10D_mean,
            s=28 if m == "MFNN" else 22,
            c=MODEL_COLORS[m], edgecolors=MODEL_STROKES[m], linewidths=0.5,
            marker=marker_map[m], alpha=0.85, zorder=3 if m == "MFNN" else 2,
            label=MODEL_LABELS[m],
        )
    r2m, r2s = FROZEN["W_MFNN_R2"]
    ax.text(0.04, 0.96, rf"$R^2_{{\mathrm{{MFNN}}}}={r2m:.3f}\pm{r2s:.3f}$",
            transform=ax.transAxes, fontsize=7.5, va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=C["MFNN_stroke"], lw=0.5, alpha=0.9))
    ax.set_xlabel(r"$\log_{10} D_{\mathrm{true}}$", fontsize=9)
    ax.set_ylabel(r"$\log_{10} \hat{D}$", fontsize=9)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect("equal", adjustable="box")
    ax.legend(loc="lower right", fontsize=6.5, handletextpad=0.3, borderpad=0.2)
    # keep spines for parity (square)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    panel_letter(ax, "c", x=-0.18)

    fig.tight_layout(w_pad=1.2)
    layers = (
        "L1_Background_and_Guides: Factor2=1 dashed; parity 1:1 and ±log10(2) band\n"
        "L2_Data_Series: bars and scatter markers by model color\n"
        "L3_ErrorBars_and_Arrows: 5-seed error bars\n"
        "L4_Typography_and_Math: (a)(b)(c), axis labels, bar annotations, R² callout"
    )
    save_figure(
        fig, "Fig2_protocolW_metrics_parity", "fig2",
        "Protocol W (5 seeds, $n_{\\mathrm{test}}=15$): (a) mean absolute percentage error (MAPE), (b) Factor-of-two accuracy, "
        "(c) ensemble $\\log_{10}D$ parity with $\\pm\\log_{10}2$ band.",
        layers,
        legacy_names=["fig2_protocol_W_metrics", "fig2c_protocol_W_parity_ensemble"],
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# Fig3 — Dataset coverage
# ---------------------------------------------------------------------------
def fig3_dataset() -> None:
    apply_style()
    df = pd.read_csv(DATA / "melt_diffusion_data_eta_paired_highmed_usable.csv")
    fig, axes = plt.subplots(1, 3, figsize=(W_DOUBLE, 58 / 25.4))

    # (a) system counts
    ax = axes[0]
    vc = df["system"].value_counts()
    y = np.arange(len(vc))
    ax.barh(y, vc.values, color=C["MFNN"], edgecolor=C["MFNN_stroke"], linewidth=0.6, height=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels(vc.index.tolist(), fontsize=8)
    ax.set_xlabel(r"Number of samples", fontsize=9)
    for i, v in enumerate(vc.values):
        ax.text(v + 1, i, str(v), va="center", fontsize=8)
    ax.set_xlim(0, vc.values.max() * 1.18)
    box_spines(ax)
    panel_letter(ax, "a", x=-0.2)

    # (b) Al–Cu T vs x_Cu by modality
    ax = axes[1]
    alu = df[df.system == "Al-Cu"].copy()
    # impurity in pure Al has x_Cu=0; for Al-Cu alloys use x_Cu
    for dt, mk in [("tracer", "o"), ("inter", "s"), ("impurity", "^"), ("self", "D")]:
        sub = alu[alu.diff_type == dt]
        if sub.empty:
            continue
        ax.scatter(
            sub.x_Cu * 100, sub.T_K, s=28, marker=mk,
            c=MODALITY_COLORS.get(dt, C["ref"]),
            edgecolors={"tracer": C["tracer_stroke"], "inter": C["inter_stroke"],
                        "impurity": C["impurity_stroke"], "self": C["ref_dark"]}[dt],
            linewidths=0.5, alpha=0.9, label=dt,
        )
    ax.set_xlabel(r"$x_{\mathrm{Cu}}$ (at.\%)", fontsize=9)
    ax.set_ylabel(r"$T$ (K)", fontsize=9)
    ax.legend(fontsize=6.5, loc="best")
    box_spines(ax)
    panel_letter(ax, "b")

    # (c) η–D log–log, colored by modality (NO Kozlov synthetics)
    ax = axes[2]
    for dt, mk in [("tracer", "o"), ("inter", "s"), ("impurity", "^"), ("self", "D")]:
        sub = df[df.diff_type == dt]
        if sub.empty:
            continue
        ax.scatter(
            sub.eta_Pas, sub.D_m2s, s=22, marker=mk,
            c=MODALITY_COLORS.get(dt, C["ref"]),
            edgecolors={"tracer": C["tracer_stroke"], "inter": C["inter_stroke"],
                        "impurity": C["impurity_stroke"], "self": C["ref_dark"]}[dt],
            linewidths=0.4, alpha=0.85, label=dt,
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\eta$ (Pa\,s)", fontsize=9)
    ax.set_ylabel(r"$D$ (m$^2$\,s$^{-1}$)", fontsize=9)
    ax.legend(fontsize=6.5, loc="best")
    box_spines(ax)
    panel_letter(ax, "c")

    fig.tight_layout(w_pad=1.0)
    layers = (
        "L1_Background_and_Guides: none\n"
        "L2_Data_Series: bars and modality-colored scatter\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: (a)(b)(c), axis labels, legends"
    )
    save_figure(
        fig, "Fig3_dataset_coverage", "fig3",
        "Dataset coverage: (a) samples by system, (b) Al–Cu $T$–$x_{\\mathrm{Cu}}$ by "
        "diffusion modality, (c) experimental $\\eta$–$D$ pairs (no synthetic Kozlov fill).",
        layers,
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# Fig4 — Al80 tracer vs inter
# ---------------------------------------------------------------------------
def fig4_al80() -> None:
    apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(W_FIG4, 65 / 25.4))

    # (a) schematic gap bars for LOGO MAPE
    ax = axes[0]
    cats = [r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$" + "\ntracer",
            r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$" + "\ninter"]
    vals = [FROZEN["Al80_tracer_MAPE"], FROZEN["Al80_inter_MAPE"]]
    cols = [C["tracer"], C["inter"]]
    ecs = [C["tracer_stroke"], C["inter_stroke"]]
    x = np.arange(2)
    ax.bar(x, vals, width=0.55, color=cols, edgecolor=ecs, linewidth=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v + 4, f"{v:.1f}%", ha="center", va="bottom", fontsize=8)
    # ~3× gap arrow annotation (conceptual MAPE gap, not physical D)
    ax.annotate(
        r"$\sim 3\times$ MAPE gap",
        xy=(0, vals[0]), xytext=(0.55, 110),
        fontsize=7.5, color=C["ref_dark"],
        arrowprops=dict(arrowstyle="-|>", color=C["ref_dark"], lw=0.8),
    )
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylabel(r"LOGO MAPE (%)", fontsize=9)
    ax.set_ylim(0, 185)
    box_spines(ax)
    panel_letter(ax, "a")

    # (b) Factor2 comparison
    ax = axes[1]
    f2 = [0.0, 1.0]  # from LOGO CSV: tracer Factor2=0, inter=1
    ax.bar(x, f2, width=0.55, color=cols, edgecolor=ecs, linewidth=0.6)
    for i, v in enumerate(f2):
        ax.text(i, v + 0.04, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylabel(r"Factor2", fontsize=9)
    ax.set_ylim(0, 1.25)
    ax.axhline(1.0, color=C["ref"], lw=0.7, ls="--", zorder=0)
    box_spines(ax)
    panel_letter(ax, "b")

    fig.tight_layout(w_pad=1.4)
    layers = (
        "L1_Background_and_Guides: Factor2=1 dashed\n"
        "L2_Data_Series: tracer/inter bars\n"
        "L3_ErrorBars_and_Arrows: ~3× gap callout arrow\n"
        "L4_Typography_and_Math: (a)(b), chemical formulae, percentages"
    )
    save_figure(
        fig, "Fig4_Al80_tracer_vs_inter", "fig4",
        r"Al$_{80}$Cu$_{20}$ LOGO conflict: tracer MAPE $156.5\%$ (Factor2 $=0$, $n=10$) "
        r"vs interdiffusivity $6.5\%$ (Factor2 $=1$, $n=2$).",
        layers,
        legacy_names=["fig3_Al80_tracer_inter"],
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# Fig5 — LOGO MAPE by fold
# ---------------------------------------------------------------------------
def _pretty_fold(name: str) -> str:
    """Chemical formulae, no ASCII underscores."""
    mapping = {
        "Al70Cu30_inter": r"$\mathrm{Al}_{70}\mathrm{Cu}_{30}$ (inter)",
        "Al75Cu25_tracer": r"$\mathrm{Al}_{75}\mathrm{Cu}_{25}$ (tracer)",
        "Al80Cu20_inter": r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$ (inter)",
        "Al80Cu20_tracer": r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$ (tracer)",
        "Al81.3Cu18.7_inter": r"$\mathrm{Al}_{81.3}\mathrm{Cu}_{18.7}$ (inter)",
        "Al81Cu19_inter": r"$\mathrm{Al}_{81}\mathrm{Cu}_{19}$ (inter)",
        "Al82.9Cu17.1_tracer": r"$\mathrm{Al}_{82.9}\mathrm{Cu}_{17.1}$ (tracer)",
        "Al85Cu15_inter": r"$\mathrm{Al}_{85}\mathrm{Cu}_{15}$ (inter)",
        "Al87Cu13_inter": r"$\mathrm{Al}_{87}\mathrm{Cu}_{13}$ (inter)",
        "Al90Cu10_inter": r"$\mathrm{Al}_{90}\mathrm{Cu}_{10}$ (inter)",
        "Al90Cu10_tracer": r"$\mathrm{Al}_{90}\mathrm{Cu}_{10}$ (tracer)",
        "Al95Cu5_inter": r"$\mathrm{Al}_{95}\mathrm{Cu}_{5}$ (inter)",
        "PureAl_impurityCu_impurity": r"Pure Al + Cu (impurity)",
    }
    return mapping.get(name, name.replace("_", " "))


def fig5_logo() -> None:
    apply_style()
    logo = pd.read_csv(RESULTS / "LOGO_AlCu_difftype_feat_summary.csv")
    m = logo[logo.model == "MFNN"].copy()
    m = m.sort_values("MAPE_pct", ascending=True)
    fig, ax = plt.subplots(figsize=(W_FIG5, 105 / 25.4))
    y = np.arange(len(m))
    colors, ecs = [], []
    for g in m.holdout_group:
        if "tracer" in g:
            colors.append(C["tracer"]); ecs.append(C["tracer_stroke"])
        elif "inter" in g:
            colors.append(C["inter"]); ecs.append(C["inter_stroke"])
        else:
            colors.append(C["impurity"]); ecs.append(C["impurity_stroke"])
    ax.barh(y, m.MAPE_pct.values, color=colors, edgecolor=ecs, linewidth=0.6, height=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels([_pretty_fold(g) for g in m.holdout_group], fontsize=7.5)
    for i, (v, n) in enumerate(zip(m.MAPE_pct.values, m.n.values)):
        ax.text(v + 2, i, f"{v:.1f}%  (n={int(n)})", va="center", fontsize=7)
    mean, std = FROZEN["LOGO_mean"]
    ax.axvline(mean, color=C["ref_dark"], lw=1.0, ls="--", zorder=0)
    ax.text(mean + 1.5, len(m) - 0.3, rf"Mean ${mean:.1f}\pm{std:.1f}\%$",
            fontsize=7.5, color=C["ref_dark"], va="top")
    ax.set_xlabel(r"MAPE (%)", fontsize=9)
    ax.set_xlim(0, 200)
    # legend proxies
    handles = [
        Rectangle((0, 0), 1, 1, fc=C["tracer"], ec=C["tracer_stroke"], lw=0.6, label="tracer"),
        Rectangle((0, 0), 1, 1, fc=C["inter"], ec=C["inter_stroke"], lw=0.6, label="inter"),
        Rectangle((0, 0), 1, 1, fc=C["impurity"], ec=C["impurity_stroke"], lw=0.6, label="impurity"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=7)
    box_spines(ax)
    fig.tight_layout()
    layers = (
        "L1_Background_and_Guides: mean dashed vertical\n"
        "L2_Data_Series: modality-colored horizontal bars\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: fold chemical formulae, MAPE labels, legend"
    )
    save_figure(
        fig, "Fig5_LOGO_MAPE_by_fold", "fig5",
        "Al–Cu LOGO (13 folds, split + one-hot): MFNN MAPE by hold-out group. "
        rf"Overall mean ${mean}\\pm{std}\\%$.",
        layers,
        legacy_names=["fig4_LOGO_MAPE_bars"],
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# Fig6 — alpha mixing weights
# ---------------------------------------------------------------------------
def fig6_alpha() -> None:
    apply_style()
    a = pd.read_csv(RESULTS / "protocol_W_alpha_table.csv")
    fig, ax = plt.subplots(figsize=(W_SINGLE, 60 / 25.4))
    seeds = a.seed.astype(str).tolist()
    x = np.arange(len(seeds))
    w = 0.38
    ax.bar(x - w / 2, a.alpha_1, w, color=C["LF"], edgecolor=C["LF_stroke"],
           linewidth=0.6, label=r"$\alpha_1$ (linear)")
    ax.bar(x + w / 2, a.alpha_2, w, color=C["MFNN"], edgecolor=C["MFNN_stroke"],
           linewidth=0.6, label=r"$\alpha_2$ (nonlinear)")
    a1m, a1s = FROZEN["alpha1"]
    a2m, a2s = FROZEN["alpha2"]
    ax.axhline(a1m, color=C["LF_stroke"], lw=0.9, ls="--", alpha=0.8)
    ax.axhline(a2m, color=C["MFNN_stroke"], lw=0.9, ls="--", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"seed {s}" for s in seeds], fontsize=7.5, rotation=0)
    ax.set_ylabel(r"Mixing weight", fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper left", fontsize=7)
    ax.text(
        0.98, 0.05,
        rf"$\alpha_1={a1m:.4f}\pm{a1s:.4f}$" + "\n" + rf"$\alpha_2={a2m:.4f}\pm{a2s:.4f}$",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=7,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=C["ref"], lw=0.5),
    )
    box_spines(ax)
    fig.tight_layout()
    layers = (
        "L1_Background_and_Guides: mean dashed lines for α1/α2\n"
        "L2_Data_Series: per-seed α bars\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: legend, mean±std callout"
    )
    save_figure(
        fig, "Fig6_alpha_mixing_weights", "fig6",
        rf"Protocol W learned mixing weights: "
        rf"$\alpha_1={a1m:.4f}\pm{a1s:.4f}$, $\alpha_2={a2m:.4f}\pm{a2s:.4f}$.",
        layers,
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# Fig7 — ablation separate vs joint
# ---------------------------------------------------------------------------
def fig7_ablation() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(W_SINGLE, 62 / 25.4))
    # groups: tracer / inter ; within each: separate vs joint
    labels = ["tracer", "inter"]
    sep = [FROZEN["Al80_tracer_sep"], FROZEN["Al80_inter_sep"]]
    joint = [FROZEN["Al80_tracer_joint"], FROZEN["Al80_inter_joint"]]
    x = np.arange(2)
    w = 0.35
    b1 = ax.bar(x - w / 2, sep, w, color=C["ref"], edgecolor=C["ref_dark"],
                linewidth=0.6, label="Separate networks")
    b2 = ax.bar(x + w / 2, joint, w,
                color=[C["tracer"], C["inter"]],
                edgecolor=[C["tracer_stroke"], C["inter_stroke"]],
                linewidth=0.6, label="Joint MFNN (LOGO)")
    for bars in (b1, b2):
        for rect in bars:
            h = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, h + 3, f"{h:.0f}%",
                    ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([
        r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$" + "\ntracer",
        r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$" + "\ninter",
    ], fontsize=8)
    ax.set_ylabel(r"MAPE (%)", fontsize=9)
    ax.set_ylim(0, 210)
    ax.legend(loc="upper right", fontsize=7)
    box_spines(ax)
    fig.tight_layout()
    layers = (
        "L1_Background_and_Guides: none\n"
        "L2_Data_Series: separate (gray) vs joint (modality colors)\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: bar labels, legend"
    )
    save_figure(
        fig, "Fig7_ablation_separate_vs_joint", "fig7",
        r"Ablation: modality-separate nets ($\approx 173\%$ / $\approx 11\%$) vs "
        r"joint LOGO MFNN ($156.5\%$ / $6.5\%$) on Al$_{80}$Cu$_{20}$.",
        layers,
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# Fig8 — Protocol W vs G
# ---------------------------------------------------------------------------
def fig8_W_vs_G() -> None:
    apply_style()
    wg = pd.read_csv(RESULTS / "seed_WG_summary.csv")
    fig, axes = plt.subplots(1, 2, figsize=(W_MID, 62 / 25.4))

    # (a) summary bars MFNN only
    ax = axes[0]
    means = [FROZEN["W_MFNN_MAPE"][0], FROZEN["G_MFNN_MAPE"][0]]
    stds = [FROZEN["W_MFNN_MAPE"][1], FROZEN["G_MFNN_MAPE"][1]]
    cols = [C["W"], C["G"]]
    ecs = [C["MFNN_stroke"], C["HF_stroke"]]
    x = np.arange(2)
    ax.bar(x, means, 0.55, yerr=stds, color=cols, edgecolor=ecs, linewidth=0.6,
           capsize=2.5, error_kw=dict(lw=0.8, ecolor=C["ref_dark"]))
    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(i, m + s + 1.5, f"{m:.2f}±{s:.2f}%", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(["Protocol W", "Protocol G"], fontsize=8)
    ax.set_ylabel(r"MFNN MAPE (%)", fontsize=9)
    ax.set_ylim(0, 55)
    box_spines(ax)
    panel_letter(ax, "a")

    # (b) seed trajectories
    ax = axes[1]
    for proto, color, stroke, mk in [
        ("W", C["W"], C["MFNN_stroke"], "o"),
        ("G", C["G"], C["HF_stroke"], "s"),
    ]:
        sub = wg[(wg.protocol == proto) & (wg.model == "MFNN")].copy()
        # order by SEEDS
        sub["seed"] = pd.Categorical(sub.seed, categories=SEEDS, ordered=True)
        sub = sub.sort_values("seed")
        ax.plot(range(len(SEEDS)), sub.MAPE_pct.values, "-o" if mk == "o" else "-s",
                color=color, markerfacecolor=color, markeredgecolor=stroke,
                markeredgewidth=0.6, markersize=5, lw=1.25, label=f"Protocol {proto}")
    ax.set_xticks(range(len(SEEDS)))
    ax.set_xticklabels([str(s) for s in SEEDS], fontsize=8)
    ax.set_xlabel(r"Seed", fontsize=9)
    ax.set_ylabel(r"MFNN MAPE (%)", fontsize=9)
    ax.legend(loc="best", fontsize=7)
    box_spines(ax)
    panel_letter(ax, "b")

    fig.tight_layout(w_pad=1.2)
    layers = (
        "L1_Background_and_Guides: none\n"
        "L2_Data_Series: W/G bars and seed trajectories\n"
        "L3_ErrorBars_and_Arrows: 5-seed error bars on (a)\n"
        "L4_Typography_and_Math: (a)(b), annotations"
    )
    wm, ws = FROZEN["W_MFNN_MAPE"]
    gm, gs = FROZEN["G_MFNN_MAPE"]
    save_figure(
        fig, "Fig8_protocol_W_vs_G", "fig8",
        rf"Protocol W ({wm:.2f}±{ws:.2f}\%) vs random group Protocol G "
        rf"({gm:.2f}±{gs:.2f}\%): G is cautionary only.",
        layers,
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# Fig9 — residuals
# ---------------------------------------------------------------------------
def fig9_residuals() -> None:
    apply_style()
    pts = pd.read_csv(RESULTS / "protocol_W_parity_ensemble_points.csv")
    m = pts[pts.model == "MFNN"].copy()
    # Prefer true T from melt table via sample_id if available
    melt = pd.read_csv(DATA / "melt_diffusion_data_eta_paired_highmed_usable.csv")
    if "sample_id" in m.columns and "sample_id" in melt.columns:
        m = m.merge(melt[["sample_id", "T_K", "eta_Pas"]], on="sample_id", how="left", suffixes=("", "_m"))
        if "T_K_m" in m.columns:
            m["T_K"] = m["T_K"].fillna(m["T_K_m"])
    m["resid"] = m.pred_log10D_mean - m.y_true_log10D
    # y_L: use LF_only prediction as proxy for y_L on same samples
    lf = pts[pts.model == "LF_only"][["sample_id", "pred_log10D_mean"]].rename(
        columns={"pred_log10D_mean": "y_L"}
    )
    m = m.merge(lf, on="sample_id", how="left")

    fig, axes = plt.subplots(1, 2, figsize=(W_MID, 58 / 25.4))
    band = math.log10(2)  # 0.3010

    ax = axes[0]
    ax.axhspan(-band, band, color=C["band"], alpha=0.45, zorder=0)
    ax.axhline(0, color=C["ref_dark"], lw=0.8)
    ax.scatter(m.T_K, m.resid, s=32, c=C["MFNN"], edgecolors=C["MFNN_stroke"],
               linewidths=0.5, zorder=2)
    ax.set_xlabel(r"$T$ (K)", fontsize=9)
    ax.set_ylabel(r"$\log_{10}\hat{D}-\log_{10}D_{\mathrm{true}}$", fontsize=9)
    ax.text(0.98, 0.95, r"$\pm 0.301$ dex (Factor2)", transform=ax.transAxes,
            ha="right", va="top", fontsize=7, color=C["ref_dark"])
    box_spines(ax)
    panel_letter(ax, "a")

    ax = axes[1]
    ax.axhspan(-band, band, color=C["band"], alpha=0.45, zorder=0)
    ax.axhline(0, color=C["ref_dark"], lw=0.8)
    ax.scatter(m.y_L, m.resid, s=32, c=C["MFNN"], edgecolors=C["MFNN_stroke"],
               linewidths=0.5, zorder=2)
    ax.set_xlabel(r"$y_L=\log_{10}D_{\mathrm{LF}}$", fontsize=9)
    ax.set_ylabel(r"$\log_{10}\hat{D}-\log_{10}D_{\mathrm{true}}$", fontsize=9)
    ax.text(0.02, 0.95, r"$n_{\mathrm{test}}=15$", transform=ax.transAxes,
            ha="left", va="top", fontsize=7.5)
    box_spines(ax)
    panel_letter(ax, "b")

    fig.tight_layout(w_pad=1.2)
    layers = (
        "L1_Background_and_Guides: ±0.301 dex Factor2 band, zero line\n"
        "L2_Data_Series: MFNN residual scatter\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: (a)(b), n_test callout"
    )
    save_figure(
        fig, "Fig9_residuals_log10", "fig9",
        r"Protocol W MFNN residuals vs $T$ and vs $y_L$ ($n_{\mathrm{test}}=15$), "
        r"with $\pm\log_{10}2$ Factor2 bounds.",
        layers,
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# FigS1 — anchor k sensitivity (SI / Oracle)
# ---------------------------------------------------------------------------
def figS1_anchor_k() -> None:
    apply_style()
    sens = pd.read_csv(RESULTS / "AL80_tracer_anchor_sensitivity.csv")
    fig, ax = plt.subplots(figsize=(W_SINGLE, 60 / 25.4))
    modes = ["k0", "k1_lowT", "k1_highT", "k2"]
    labels = [r"$k=0$", r"$k=1$ low $T$", r"$k=1$ high $T$", r"$k=2$"]
    frozen = list(FROZEN["S1_MAPE"])
    # also show seed spread from CSV for MFNN
    means, stds = [], []
    for mode in modes:
        sub = sens[sens["mode"] == mode]["MFNN_MAPE_pct"]
        means.append(float(sub.mean()))
        stds.append(_pop_std(sub))
    # Use frozen values for annotations; error bars from CSV
    x = np.arange(len(modes))
    ax.bar(x, frozen, 0.6, yerr=stds, color=C["tracer"], edgecolor=C["tracer_stroke"],
           linewidth=0.6, capsize=2.5, error_kw=dict(lw=0.8, ecolor=C["ref_dark"]))
    for i, v in enumerate(frozen):
        ax.text(i, v + stds[i] + 4, f"{v:.1f}", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel(r"MFNN MAPE (%)", fontsize=9)
    ax.set_ylim(0, 250)
    ax.text(
        0.5, 1.02, "Oracle / Counterfactual diagnostic (SI only)",
        transform=ax.transAxes, ha="center", va="bottom", fontsize=7.5,
        color=C["tracer_stroke"], fontweight="bold",
    )
    # Factor2 = 0 note
    ax.text(0.98, 0.05, r"Factor2 $=0$ (all $k$)", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7, color=C["ref_dark"])
    box_spines(ax)
    fig.tight_layout()
    layers = (
        "L1_Background_and_Guides: none\n"
        "L2_Data_Series: unified tracer-color bars\n"
        "L3_ErrorBars_and_Arrows: seed error bars\n"
        "L4_Typography_and_Math: Oracle banner, k labels"
    )
    save_figure(
        fig, "FigS1_al80_anchor_k", "figS1",
        "SI: Al80 tracer anchor-$k$ sensitivity (Oracle). "
        "MAPE 178.20 / 169.55 / 175.27 / 142.93%; Factor2 = 0.",
        layers,
        legacy_names=["fig_si_al80_anchor_k"],
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# FigS2 — posthoc intercept shift B2
# ---------------------------------------------------------------------------
def figS2_posthoc() -> None:
    apply_style()
    ph = pd.read_csv(RESULTS / "AL80_posthoc_intercept_shift.csv")
    fig, ax = plt.subplots(figsize=(W_MID, 60 / 25.4))
    # Compare raw vs posthoc for MFNN (aggregate lowT+highT heldouts)
    raw = ph[(ph.model == "MFNN") & (ph.setting.str.startswith("k0_raw"))]
    shift = ph[(ph.model == "MFNN") & (ph.setting.str.startswith("k0_posthoc"))]
    cats = ["Raw held-out\n(no shift)", "Post-hoc B2\nintercept shift"]
    # Use frozen 9.81 for shifted; raw from CSV mean
    raw_m = float(raw.MAPE_pct.mean())
    raw_s = _pop_std(raw.MAPE_pct)
    sh_m, sh_s = FROZEN["S2_MAPE"]
    # delta from CSV
    delta = float(shift.delta_log10.mean())
    delta_s = _pop_std(shift.delta_log10)

    vals = [raw_m, sh_m]
    errs = [raw_s, sh_s]
    x = np.arange(2)
    ax.bar(x, vals, 0.55, yerr=errs, color=[C["tracer"], C["MFNN"]],
           edgecolor=[C["tracer_stroke"], C["MFNN_stroke"]], linewidth=0.6,
           capsize=2.5, error_kw=dict(lw=0.8, ecolor=C["ref_dark"]))
    for i, (v, e) in enumerate(zip(vals, errs)):
        ax.text(i, v + e + 3, f"{v:.2f}±{e:.2f}%", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylabel(r"MFNN MAPE (%)", fontsize=9)
    ax.set_ylim(0, max(vals) + max(errs) + 40)
    ax.text(
        0.5, 1.02, "Oracle / Counterfactual diagnostic (SI only)",
        transform=ax.transAxes, ha="center", va="bottom", fontsize=7.5,
        color=C["tracer_stroke"], fontweight="bold",
    )
    ax.text(
        0.98, 0.92,
        rf"$\delta={delta:.3f}\pm{delta_s:.3f}\approx-\log_{{10}}3$",
        transform=ax.transAxes, ha="right", va="top", fontsize=7.5,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=C["MFNN_stroke"], lw=0.5),
    )
    box_spines(ax)
    fig.tight_layout()
    layers = (
        "L1_Background_and_Guides: none\n"
        "L2_Data_Series: raw vs B2 bars\n"
        "L3_ErrorBars_and_Arrows: seed error bars\n"
        "L4_Typography_and_Math: Oracle banner, δ callout — DO NOT promote 9.81% to main text"
    )
    save_figure(
        fig, "FigS2_al80_posthoc_shift", "figS2",
        rf"SI Oracle B2: post-hoc intercept shift yields MAPE ${sh_m:.2f}\pm{sh_s:.2f}\%$ "
        rf"($\delta\approx-\log_{{10}}3$). Not a deployable protocol.",
        layers,
        legacy_names=["fig_si_al80_posthoc_shift"],
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# FigS3 — upweight w sensitivity
# ---------------------------------------------------------------------------
def figS3_upweight() -> None:
    apply_style()
    uw = pd.read_csv(RESULTS / "AL80_anchor_upweight_k2.csv")
    fig, ax1 = plt.subplots(figsize=(W_SINGLE, 60 / 25.4))
    ws = [1.0, 5.0, 10.0]
    frozen_mape = list(FROZEN["S3_MAPE"])
    mape_std, f2_m, f2_s = [], [], []
    for w in ws:
        sub = uw[uw.w_anchor == w]
        mape_std.append(_pop_std(sub.MFNN_MAPE_pct))
        f2_m.append(float(sub.MFNN_Factor2.mean()))
        f2_s.append(_pop_std(sub.MFNN_Factor2))

    ax1.plot(ws, frozen_mape, "-o", color=C["tracer"], markerfacecolor=C["tracer"],
             markeredgecolor=C["tracer_stroke"], markersize=6.5, lw=1.4, label="MAPE")
    ax1.fill_between(ws,
                     [m - s for m, s in zip(frozen_mape, mape_std)],
                     [m + s for m, s in zip(frozen_mape, mape_std)],
                     color=C["tracer"], alpha=0.15)
    for w, m in zip(ws, frozen_mape):
        ax1.text(w, m + 6, f"{m:.0f}%", ha="center", fontsize=7.5, color=C["tracer_stroke"])
    ax1.set_xlabel(r"Anchor weight $w$", fontsize=9)
    ax1.set_ylabel(r"MFNN MAPE (%)", fontsize=9, color=C["tracer_stroke"])
    ax1.set_ylim(0, 145)
    ax1.set_xticks(ws)
    ax1.tick_params(axis="y", labelcolor=C["tracer_stroke"])

    ax2 = ax1.twinx()
    ax2.plot(ws, f2_m, "-s", color=C["HF"], markerfacecolor=C["HF"],
             markeredgecolor=C["HF_stroke"], markersize=6, lw=1.4, label="Factor2")
    ax2.set_ylabel(r"Factor2", fontsize=9, color=C["HF_stroke"])
    ax2.set_ylim(0, 1.15)
    ax2.tick_params(axis="y", labelcolor=C["HF_stroke"])
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(C["HF_stroke"])
    ax2.spines["top"].set_visible(False)

    ax1.text(
        0.5, 1.02, "Counterfactual $k=2$ sensitivity (SI only)",
        transform=ax1.transAxes, ha="center", va="bottom", fontsize=7.5,
        color=C["tracer_stroke"], fontweight="bold",
    )
    # combined legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="center right", fontsize=7)
    ax1.spines["top"].set_visible(False)
    fig.tight_layout()
    layers = (
        "L1_Background_and_Guides: none\n"
        "L2_Data_Series: MAPE (tracer) and Factor2 (HF-blue) dual axis\n"
        "L3_ErrorBars_and_Arrows: MAPE band from seeds\n"
        "L4_Typography_and_Math: Counterfactual banner — DO NOT promote 31% as LOGO success"
    )
    save_figure(
        fig, "FigS3_al80_upweight_w", "figS3",
        "SI Counterfactual: $k=2$ anchor upweight $w=1\\to5\\to10$ "
        "MAPE $122\\to48\\to31\\%$. Not a claimed LOGO result.",
        layers,
    )
    plt.close(fig)


# ---------------------------------------------------------------------------
# Pack index + main
# ---------------------------------------------------------------------------
def write_pack_index() -> None:
    VECTOR_PACK.mkdir(parents=True, exist_ok=True)
    stems = [
        "Fig1_mfnn_residual_schema",
        "Fig2_protocolW_metrics_parity",
        "Fig3_dataset_coverage",
        "Fig4_Al80_tracer_vs_inter",
        "Fig5_LOGO_MAPE_by_fold",
        "Fig6_alpha_mixing_weights",
        "Fig7_ablation_separate_vs_joint",
        "Fig8_protocol_W_vs_G",
        "Fig9_residuals_log10",
        "FigS1_al80_anchor_k",
        "FigS2_al80_posthoc_shift",
        "FigS3_al80_upweight_w",
    ]
    lines = [
        "# figures_vector index (JCP/Elsevier figure style)",
        "",
        "Each folder contains PDF + SVG + PNG + README.txt (Illustrator 4-layer notes).",
        "Prefer **SVG** for Adobe Illustrator editing (`svg.fonttype=none`).",
        "",
        "| Stem | Role |",
        "| --- | --- |",
    ]
    roles = {
        "Fig1_mfnn_residual_schema": "Architecture schema (mid width)",
        "Fig2_protocolW_metrics_parity": "Protocol W metrics + parity (double)",
        "Fig3_dataset_coverage": "Dataset coverage (double)",
        "Fig4_Al80_tracer_vs_inter": "Al80 tracer vs inter (main)",
        "Fig5_LOGO_MAPE_by_fold": "LOGO MAPE by fold",
        "Fig6_alpha_mixing_weights": "α mixing weights (single)",
        "Fig7_ablation_separate_vs_joint": "Ablation separate vs joint",
        "Fig8_protocol_W_vs_G": "Protocol W vs G",
        "Fig9_residuals_log10": "Residuals vs T / y_L",
        "FigS1_al80_anchor_k": "SI Oracle anchor-k",
        "FigS2_al80_posthoc_shift": "SI Oracle B2 9.81%",
        "FigS3_al80_upweight_w": "SI Counterfactual upweight 31%",
    }
    for s in stems:
        lines.append(f"| `{s}/` | {roles.get(s, '')} |")
    lines += [
        "",
        "## Frozen numbers (do not alter)",
        "- Protocol W MFNN: 26.18±1.33% / Factor2 0.96±0.033 / R² 0.392±0.094",
        "- SI 9.81% and 31% stay in FigS2/FigS3 only",
        "",
    ]
    (VECTOR_PACK / "README_INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    (VECTOR_PACK / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote pack index")


def main() -> None:
    apply_style()
    fig1_schema()
    fig2_protocolW()
    fig3_dataset()
    fig4_al80()
    fig5_logo()
    fig6_alpha()
    fig7_ablation()
    fig8_W_vs_G()
    fig9_residuals()
    figS1_anchor_k()
    figS2_posthoc()
    figS3_upweight()
    write_pack_index()
    print("ALL FIGURES DONE")


if __name__ == "__main__":
    main()
