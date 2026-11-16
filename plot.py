# -*- coding: utf-8 -*-
"""
plot.py
Parity, Arrhenius-style, eta-D, and per-system MAPE bar charts.
Titles use plain Unicode (no broken HTML/LaTeX entity escapes).
"""

from __future__ import annotations
import os
from typing import Optional
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_all_figures(
    detail_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    out_dir: str = "outputs",
) -> None:
    os.makedirs(out_dir, exist_ok=True)
    models = [c.replace("pred_", "").replace("_log10D", "") for c in detail_df.columns if c.startswith("pred_") and c.endswith("_log10D")]

    # Parity plot
    fig, axes = plt.subplots(1, len(models), figsize=(4.2 * max(len(models), 1), 4), squeeze=False)
    y_true = detail_df["y_true_log10D"].to_numpy()
    for ax, name in zip(axes[0], models):
        yp = detail_df[f"pred_{name}_log10D"].to_numpy()
        ax.scatter(y_true, yp, c="tab:blue", alpha=0.75, edgecolors="k", linewidths=0.3)
        lo = min(y_true.min(), yp.min())
        hi = max(y_true.max(), yp.max())
        ax.plot([lo, hi], [lo, hi], "r--", lw=1)
        ax.set_xlabel(r"True $\log_{10} D$")
        ax.set_ylabel(r"Predicted $\log_{10} D$")
        ax.set_title(f"Parity: {name}")
        ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "parity_plot.png"), dpi=150)
    plt.close(fig)

    # Arrhenius-style: log10 D vs 1000/T
    if "T_K" in detail_df.columns:
        fig, ax = plt.subplots(figsize=(6, 4))
        invT = 1000.0 / detail_df["T_K"].to_numpy()
        ax.scatter(invT, y_true, label="True HF", marker="o")
        if "MFNN" in models:
            ax.scatter(invT, detail_df["pred_MFNN_log10D"], label="MFNN", marker="x")
        ax.set_xlabel(r"$1000/T$ (K$^{-1}$)")
        ax.set_ylabel(r"$\log_{10} D$ (m$^2$/s)")
        ax.set_title("Arrhenius-style plot (test HF)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "arrhenius_plot.png"), dpi=150)
        plt.close(fig)

    # eta-D
    if "eta_Pas" in detail_df.columns:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(detail_df["eta_Pas"], detail_df["D_true"], label="True HF", marker="o")
        if "MFNN" in models:
            ax.scatter(detail_df["eta_Pas"], detail_df["pred_MFNN_D"], label="MFNN", marker="x")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(r"$\eta$ (Pa·s)")
        ax.set_ylabel(r"$D$ (m$^2$/s)")
        ax.set_title(r"$\eta$ → $D$ (test HF)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "eta_D_plot.png"), dpi=150)
        plt.close(fig)

    # MAPE by system for MFNN if present
    sub = summary_df[summary_df["system"] != "ALL"].copy()
    if "MFNN" in sub["model"].values:
        m = sub[sub["model"] == "MFNN"]
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(m["system"].astype(str), m["MAPE_pct"].astype(float), color="tab:green")
        ax.set_ylabel("MAPE (%)")
        ax.set_title("Per-system MAPE (MFNN)")
        ax.tick_params(axis="x", rotation=20)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "mape_by_system.png"), dpi=150)
        plt.close(fig)
