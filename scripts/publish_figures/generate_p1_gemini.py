#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gemini P1 figures: Main Fig.2, Fig.5, Fig.7 (distance caution).

Reuses publish_figures/_style.py. No retrain; frozen numbers unchanged.
Run from repo root:
  .venv/Scripts/python.exe scripts/publish_figures/generate_p1_gemini.py
"""
from __future__ import annotations

import math
import re
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
ROOT = _HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _style import (  # noqa: E402
    C,
    DATA,
    FIG_DIR,
    FROZEN,
    JCP_FIG,
    RESULTS,
    VECTOR_PACK,
    W_DOUBLE,
    W_MID,
    apply_style,
    despine,
    box_spines,
    panel_letter,
)
from data import (  # noqa: E402
    NUM_PHYS,
    FeatureStandardizer,
    build_feature_matrix,
)
from model import ResidualMFNN, SingleFidelityNN  # noqa: E402
from physics import (  # noqa: E402
    assael_pure_al_viscosity,
    physics_from_row,
)

SEEDS = [0, 1, 2, 42, 123]
MODEL_COLORS = {"LF_only": C["LF"], "HF_only": C["HF"], "MFNN": C["MFNN"]}
MODEL_STROKES = {"LF_only": C["LF_stroke"], "HF_only": C["HF_stroke"], "MFNN": C["MFNN_stroke"]}
MODALITY_COLORS = {
    "tracer": C["tracer"],
    "inter": C["inter"],
    "impurity": C["impurity"],
    "self": C["self"],
}
MODALITY_STROKES = {
    "tracer": C["tracer_stroke"],
    "inter": C["inter_stroke"],
    "impurity": C["impurity_stroke"],
    "self": C["ref_dark"],
}


def _save(fig, stem: str, caption: str, ai_layers: str) -> None:
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
        f"Stem: {stem}\n\nCaption draft:\n{caption}\n\nLayers:\n{ai_layers}\n",
        encoding="utf-8",
    )
    print("saved", stem)


def _load_usable() -> pd.DataFrame:
    return pd.read_csv(DATA / "melt_diffusion_data_eta_paired_highmed_usable.csv")


def fig2_phase_space_coverage() -> None:
    apply_style()
    df = _load_usable()
    hf = df[df.fidelity == "HF"].copy()
    fig, axes = plt.subplots(1, 2, figsize=(W_DOUBLE, 62 / 25.4))

    # (a) composition–temperature coverage
    ax = axes[0]
    alu = hf[hf.system == "Al-Cu"]
    for dt, mk in [("tracer", "o"), ("inter", "s"), ("impurity", "^"), ("self", "D")]:
        sub = alu[alu.diff_type == dt]
        if sub.empty:
            continue
        ax.scatter(
            sub.x_Cu * 100.0,
            sub.T_K,
            s=30,
            marker=mk,
            c=MODALITY_COLORS.get(dt, C["ref"]),
            edgecolors=MODALITY_STROKES.get(dt, C["ref_dark"]),
            linewidths=0.5,
            alpha=0.9,
            label=f"Al–Cu {dt}",
            zorder=3,
        )
    # sparse multi-component: plot vs max non-Al fraction
    other = hf[hf.system != "Al-Cu"].copy()
    if not other.empty:
        other = other.copy()
        other["x_solute"] = other[["x_Cu", "x_Ce", "x_Ni", "x_Ag", "x_Mg", "x_Si"]].sum(axis=1)
        sys_colors = {
            "Al-Mg-Si": "#56B4E9",
            "Al-Ce-Ni": "#CC79A7",
            "Al-Ag-Cu": "#E69F00",
        }
        for sys_name, g in other.groupby("system"):
            ax.scatter(
                g.x_solute * 100.0,
                g.T_K,
                s=36,
                marker="x",
                c=sys_colors.get(sys_name, C["ref"]),
                linewidths=0.9,
                alpha=0.85,
                label=f"{sys_name} (sparse)",
                zorder=2,
            )
    ax.set_xlabel(r"$x_{\mathrm{Cu}}$ or solute fraction (at.%)", fontsize=8)
    ax.set_ylabel(r"$T$ (K)", fontsize=9)
    ax.legend(fontsize=5.5, loc="best", ncol=1, frameon=False)
    ax.text(
        0.02,
        0.02,
        "honest $\\eta$-paired HF only\n(no Kozlov fill)",
        transform=ax.transAxes,
        fontsize=6.5,
        va="bottom",
        ha="left",
        color=C["ref_dark"],
    )
    box_spines(ax)
    panel_letter(ax, "a")

    # (b) experimental D vs η + modified Sutherland prior on same points
    ax = axes[1]
    phys_D, phys_eta = [], []
    for _, row in hf.iterrows():
        if not (np.isfinite(row.eta_Pas) and row.eta_Pas > 0 and np.isfinite(row.D_m2s)):
            continue
        phys = physics_from_row(
            float(row.T_K),
            float(row.eta_Pas),
            str(row.diff_species),
            str(row.solvent_species) if pd.notna(row.solvent_species) else "Al",
        )
        phys_D.append(phys.D_phys)
        phys_eta.append(float(row.eta_Pas))
    for dt, mk in [("tracer", "o"), ("inter", "s"), ("impurity", "^"), ("self", "D")]:
        sub = hf[hf.diff_type == dt]
        if sub.empty:
            continue
        ax.scatter(
            sub.eta_Pas,
            sub.D_m2s,
            s=26,
            marker=mk,
            c=MODALITY_COLORS.get(dt, C["ref"]),
            edgecolors=MODALITY_STROKES.get(dt, C["ref_dark"]),
            linewidths=0.45,
            alpha=0.9,
            label=f"exp. {dt}",
            zorder=3,
        )
    ax.scatter(
        phys_eta,
        phys_D,
        s=18,
        marker="+",
        c=C["LF"],
        linewidths=0.8,
        alpha=0.75,
        label="modified Sutherland LF prior",
        zorder=2,
    )
    # guide: eta^{-1} trend at fixed T~1000 K for visual context (not a fit)
    eta_line = np.logspace(
        np.log10(max(hf.eta_Pas.min() * 0.9, 1e-4)),
        np.log10(hf.eta_Pas.max() * 1.05),
        50,
    )
    # representative pure-Al Sutherland at 1000 K for slope context
    d_guide = [
        physics_from_row(1000.0, float(e), "Al", "Al").D_phys for e in eta_line
    ]
    ax.plot(
        eta_line,
        d_guide,
        color=C["LF_stroke"],
        lw=1.0,
        ls="--",
        alpha=0.7,
        label=r"Sutherland guide ($T=1000\,\mathrm{K}$, Al)",
        zorder=1,
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\eta$ (Pa$\cdot$s)", fontsize=9)
    ax.set_ylabel(r"$D$ (m$^{2}\,$s$^{-1}$)", fontsize=9)
    ax.legend(fontsize=5.5, loc="upper right", frameon=False, bbox_to_anchor=(1.0, 1.0), borderaxespad=0.2)
    box_spines(ax)
    panel_letter(ax, "b")

    fig.tight_layout(w_pad=1.2)
    cap = (
        "Figure 2. Phase-space coverage and physical context of liquid-alloy diffusivity "
        "with honest viscosity pairing (no Kozlov fills). (a) High-fidelity temperature–composition "
        "coverage: Al–Cu points by diffusion modality versus $x_{\\mathrm{Cu}}$; sparse "
        "Al–Mg–Si / Al–Ce–Ni / Al–Ag–Cu HF points shown versus total non-Al solute fraction. "
        "(b) Experimental $D$ versus melt viscosity $\\eta$ by modality, overlaid with the "
        "modified Sutherland low-fidelity prior evaluated at the same $(T,\\eta)$ points "
        "(plus markers) and a pure-Al Sutherland guide at $T=1000\\,\\mathrm{K}$ (dashed). "
        "Not a PINN/PPINN formulation. File: `Fig2_phase_space_coverage`."
    )
    layers = (
        "L1_Background_and_Guides: Sutherland guide curve\n"
        "L2_Data_Series: coverage scatter; exp vs prior on eta-D\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: (a)(b), legends"
    )
    _save(fig, "Fig2_phase_space_coverage", cap, layers)
    plt.close(fig)


def _eta_interpolator(comp_mask: pd.Series, df: pd.DataFrame):
    """Linear interp eta(T) from all honest-paired rows of a composition mask."""
    sub = df.loc[comp_mask].dropna(subset=["T_K", "eta_Pas"]).copy()
    sub = sub[sub.eta_Pas > 0].sort_values("T_K")
    if len(sub) == 0:
        return None
    T = sub.T_K.to_numpy(dtype=float)
    eta = sub.eta_Pas.to_numpy(dtype=float)
    # unique T
    _, idx = np.unique(T, return_index=True)
    T, eta = T[idx], eta[idx]
    if len(T) == 1:
        return lambda tt: np.full_like(np.asarray(tt, dtype=float), eta[0], dtype=float)
    return lambda tt: np.interp(np.asarray(tt, dtype=float), T, eta, left=eta[0], right=eta[-1])


def _load_protocol_w_models(seed: int = 42):
    ck_path = ROOT / "outputs" / f"seed_wg_{seed}" / "within_T" / "mfnn_checkpoint.pt"
    ck = torch.load(ck_path, map_location="cpu", weights_only=False)
    in_dim = int(np.asarray(ck["scaler_mean"]).shape[0])
    assert in_dim == 12
    scaler = FeatureStandardizer(num_continuous=NUM_PHYS, num_phys=NUM_PHYS)
    scaler.mean_ = np.asarray(ck["scaler_mean"], dtype=np.float64)
    scaler.std_ = np.asarray(ck["scaler_std"], dtype=np.float64)
    mfnn = ResidualMFNN(in_dim=in_dim)
    mfnn.load_state_dict(ck["mfnn_state_dict"])
    mfnn.eval()
    hf = SingleFidelityNN(in_dim=in_dim)
    hf.load_state_dict(ck["hf_only_state_dict"])
    hf.eval()
    lf = SingleFidelityNN(in_dim=in_dim)
    lf.load_state_dict(ck["lf_only_state_dict"])
    lf.eval()
    return scaler, mfnn, hf, lf


def _predict_grid(template_row: pd.Series, Ts: np.ndarray, eta_of_T, scaler, mfnn, hf, lf):
    rows = []
    for T in Ts:
        r = template_row.copy()
        r["T_K"] = float(T)
        r["eta_Pas"] = float(eta_of_T(T))
        rows.append(r)
    grid = pd.DataFrame(rows)
    X, _, phys = build_feature_matrix(grid, include_difftype_onehot=False)
    Xs = scaler.transform(X)
    with torch.no_grad():
        t = torch.tensor(Xs, dtype=torch.float32)
        pred = {
            "LF_only": lf(t).numpy(),
            "HF_only": hf(t).numpy(),
            "MFNN": mfnn.forward_hf(t).numpy(),
            "Sutherland": phys,
        }
    return pred


def fig5_arrhenius_representative() -> None:
    """Inference-only T-grid curves from Protocol W seed-42 checkpoint (12-D)."""
    apply_style()
    df = _load_usable()
    scaler, mfnn, hf, lf = _load_protocol_w_models(42)

    panels = []
    # Panel A: PureAl self-diffusion
    pure = df[(df.comp_group == "PureAl") & (df.diff_type == "self") & (df.fidelity == "HF")].sort_values("T_K")
    eta_fn = _eta_interpolator((df.comp_group == "PureAl"), df)
    if eta_fn is None:
        eta_fn = lambda tt: np.array([assael_pure_al_viscosity(float(t)) for t in np.atleast_1d(tt)], dtype=float)
    Ts = np.linspace(float(pure.T_K.min()) - 10, float(pure.T_K.max()) + 10, 40)
    pred = _predict_grid(pure.iloc[0], Ts, eta_fn, scaler, mfnn, hf, lf)
    panels.append(("a", r"Pure Al self-diffusion", pure, Ts, pred))

    # Panel B: Al80Cu20 tracer
    al80 = df[(df.comp_group == "Al80Cu20") & (df.diff_type == "tracer") & (df.fidelity == "HF")].sort_values("T_K")
    eta_fn80 = _eta_interpolator((df.comp_group == "Al80Cu20"), df)
    if len(al80) and eta_fn80 is not None:
        Ts80 = np.linspace(float(al80.T_K.min()) - 10, float(al80.T_K.max()) + 10, 40)
        pred80 = _predict_grid(al80.iloc[0], Ts80, eta_fn80, scaler, mfnn, hf, lf)
        panels.append(("b", r"$\mathrm{Al}_{80}\mathrm{Cu}_{20}$ Cu-tracer", al80, Ts80, pred80))
    else:
        panels.append(None)

    n = 2
    fig, axes = plt.subplots(1, n, figsize=(W_DOUBLE, 60 / 25.4))
    if n == 1:
        axes = [axes]

    for ax, panel in zip(axes, panels):
        if panel is None:
            ax.axis("off")
            continue
        letter, title, exp, Ts, pred = panel
        # Arrhenius axes: 1000/T vs log10 D
        x_exp = 1000.0 / exp.T_K.to_numpy(dtype=float)
        y_exp = np.log10(np.clip(exp.D_m2s.to_numpy(dtype=float), 1e-30, None))
        ax.scatter(
            x_exp,
            y_exp,
            s=36,
            c=C["ref_dark"],
            edgecolors="white",
            linewidths=0.4,
            zorder=5,
            label="HF experiment",
        )
        xg = 1000.0 / Ts
        ax.plot(xg, pred["Sutherland"], color=C["LF"], ls=":", lw=1.2, label="modified Sutherland prior")
        ax.plot(xg, pred["LF_only"], color=C["LF"], ls="--", lw=1.2, label="LF-only NN")
        ax.plot(xg, pred["HF_only"], color=C["HF"], ls="-.", lw=1.2, label="HF-only NN")
        ax.plot(xg, pred["MFNN"], color=C["MFNN"], ls="-", lw=1.4, label="residual MFNN")
        ax.set_xlabel(r"$1000/T$ (K$^{-1}$)", fontsize=9)
        ax.set_ylabel(r"$\log_{10} D$ ($D$ in m$^{2}$ s$^{-1}$)", fontsize=8)
        ax.set_title(title, fontsize=8)
        ax.legend(fontsize=5.5, loc="best", frameon=False)
        box_spines(ax)
        panel_letter(ax, letter)

    fig.tight_layout(w_pad=1.2)
    cap = (
        "Figure 5. Representative Arrhenius-style $\\log_{10}D$ versus $1000/T$ curves under "
        "Protocol W weights (seed 42 checkpoint; inference only, no retraining; 12-D features "
        "as stored in the checkpoint). (a) Pure Al self-diffusion: HF experiments with continuous "
        "$T$-grid predictions from residual MFNN, HF-only, LF-only, and the modified Sutherland "
        "prior ($\\eta(T)$ from honest paired viscosities, Assael fallback if needed). "
        "(b) $\\mathrm{Al}_{80}\\mathrm{Cu}_{20}$ Cu-tracer with $\\eta(T)$ interpolated from "
        "honest Al80Cu20 paired viscosities. Curves illustrate smoothness of the LF-anchored "
        "residual MFNN relative to HF-only; not a LOGO success claim. Not a PINN/PPINN formulation. "
        "File: `Fig5_arrhenius_representative`."
    )
    layers = (
        "L1_Background_and_Guides: none\n"
        "L2_Data_Series: exp scatter + model/prior curves\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: (a)(b), legends"
    )
    _save(fig, "Fig5_arrhenius_representative", cap, layers)
    plt.close(fig)


def _parse_x_cu(holdout_group: str) -> float:
    g = str(holdout_group)
    if g.startswith("PureAl"):
        return 0.0
    m = re.search(r"Cu([0-9]+(?:\.[0-9]+)?)", g)
    if not m:
        m = re.search(r"Cu([0-9]+(?:\.[0-9]+)?)", g.replace("_", ""))
    if m:
        return float(m.group(1)) / 100.0
    raise ValueError(f"cannot parse x_Cu from {holdout_group}")


def _holdout_base_comp(holdout_group: str) -> str:
    """Strip modality suffix -> base composition key used in data.comp_group."""
    g = str(holdout_group)
    for suf in ("_tracer", "_inter", "_impurity"):
        if g.endswith(suf):
            # PureAl_impurityCu_impurity -> PureAl_impurityCu in data? check
            base = g[: -len(suf)]
            return base
    return g


def fig7_logo_distance_caution() -> None:
    apply_style()
    logo = pd.read_csv(RESULTS / "LOGO_AlCu_difftype_feat_summary.csv")
    m = logo[logo.model == "MFNN"].copy()
    df = _load_usable()
    hf = df[(df.fidelity == "HF") & (df.system == "Al-Cu")].copy()
    # map each Al-Cu HF comp_group to mean x_Cu
    group_x = hf.groupby("comp_group")["x_Cu"].mean().to_dict()
    # also PureAl impurity from full HF
    hf_all = df[df.fidelity == "HF"]
    for g, val in hf_all.groupby("comp_group")["x_Cu"].mean().items():
        group_x.setdefault(g, float(val))

    rows = []
    for _, r in m.iterrows():
        hold = str(r.holdout_group)
        base = _holdout_base_comp(hold)
        # Prefer measured mean x_Cu from HF table when available
        x_h = float(group_x[base]) if base in group_x else _parse_x_cu(hold)
        # Distinct training compositions: drop same name and same x_Cu (e.g. Al81Cu19 == Al81.3)
        train_xs = []
        for gname, xv in group_x.items():
            if gname == base or gname.startswith(base + "_"):
                continue
            if not (("Cu" in gname) or gname.startswith("PureAl")):
                continue
            xv = float(xv)
            if abs(xv - x_h) < 1e-4:
                continue  # same composition under another label
            train_xs.append(xv)
        # unique x values
        train_xs = sorted(set(train_xs))
        if not train_xs:
            dx = float("nan")
            nn = float("nan")
        else:
            arr = np.asarray(train_xs, dtype=float)
            j = int(np.argmin(np.abs(arr - x_h)))
            nn = float(arr[j])
            dx = float(abs(x_h - nn))
        rows.append(
            {
                "holdout_group": hold,
                "MAPE_pct": float(r.MAPE_pct),
                "n": int(r.n),
                "x_Cu_holdout": x_h,
                "x_Cu_nn_train": nn,
                "delta_x_Cu": dx,
                "Factor2": float(r.Factor2) if pd.notna(r.Factor2) else np.nan,
            }
        )
    dist = pd.DataFrame(rows)
    dist_path = RESULTS / "LOGO_AlCu_delta_xCu_from_summary.csv"
    dist.to_csv(dist_path, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(W_DOUBLE, 70 / 25.4), gridspec_kw={"width_ratios": [1.25, 1.0]})

    # (a) LOGO MAPE bars (caution) — sorted
    ax = axes[0]
    mm = m.sort_values("MAPE_pct", ascending=True)
    y = np.arange(len(mm))
    colors, ecs = [], []
    for g in mm.holdout_group:
        if "tracer" in g:
            colors.append(C["tracer"]); ecs.append(C["tracer_stroke"])
        elif "inter" in g:
            colors.append(C["inter"]); ecs.append(C["inter_stroke"])
        else:
            colors.append(C["impurity"]); ecs.append(C["impurity_stroke"])
    ax.barh(y, mm.MAPE_pct.values, color=colors, edgecolor=ecs, linewidth=0.6, height=0.72)
    ax.set_yticks(y)

    def _pretty(name: str) -> str:
        # mathtext subscripts (Arial lacks Unicode subscript glyphs)
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
            "PureAl_impurityCu_impurity": "Pure Al + Cu (impurity)",
        }
        return mapping.get(name, name.replace("_", " "))

    ax.set_yticklabels([_pretty(g) for g in mm.holdout_group], fontsize=6.5)
    for i, (v, n) in enumerate(zip(mm.MAPE_pct.values, mm.n.values)):
        ax.text(v + 2, i, f"{v:.1f}% (n={int(n)})", va="center", fontsize=6)
    mean, std = FROZEN["LOGO_mean"]
    ax.axvline(mean, color=C["ref_dark"], lw=1.0, ls="--", zorder=0)
    ax.set_xlabel(r"MAPE (%)", fontsize=9)
    ax.set_xlim(0, 210)
    # Place mean callout in empty space to the right of short bars (bottom of panel)
    ax.tick_params(axis="x", labelrotation=0)
    ax.set_title(rf"LOGO MAPE by hold-out (caution); mean ${mean:.1f}\pm{std:.1f}\%$ frozen", fontsize=7.5)
    handles = [
        Rectangle((0, 0), 1, 1, fc=C["tracer"], ec=C["tracer_stroke"], lw=0.6, label="tracer"),
        Rectangle((0, 0), 1, 1, fc=C["inter"], ec=C["inter_stroke"], lw=0.6, label="inter"),
        Rectangle((0, 0), 1, 1, fc=C["impurity"], ec=C["impurity_stroke"], lw=0.6, label="impurity"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.55, -0.14), ncol=3, fontsize=6.5, frameon=False, borderaxespad=0)
    box_spines(ax)
    panel_letter(ax, "a", x=-0.22)

    # (b) MAPE vs Δx_Cu
    ax = axes[1]
    for _, r in dist.iterrows():
        g = r.holdout_group
        if "tracer" in g:
            col, ec, mk = C["tracer"], C["tracer_stroke"], "o"
        elif "inter" in g:
            col, ec, mk = C["inter"], C["inter_stroke"], "s"
        else:
            col, ec, mk = C["impurity"], C["impurity_stroke"], "^"
        ax.scatter(
            r.delta_x_Cu * 100.0,
            r.MAPE_pct,
            s=42,
            marker=mk,
            c=col,
            edgecolors=ec,
            linewidths=0.6,
            zorder=3,
        )
    ax.axhline(mean, color=C["ref_dark"], lw=0.9, ls="--", zorder=0)
    ax.set_xlabel(r"$\Delta x_{\mathrm{Cu}}$ to nearest train composition (at.%)", fontsize=8)
    ax.set_ylabel(r"LOGO MFNN MAPE (%)", fontsize=9)
    ax.set_title(r"Error vs composition distance (caution)", fontsize=8)
    ax.text(
        0.98,
        0.98,
        "not a success claim\nnearest-neighbor $|\\Delta x_{\\mathrm{Cu}}|$\nin training pool",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.5,
        color=C["ref_dark"],
    )
    box_spines(ax)
    panel_letter(ax, "b")

    fig.tight_layout(w_pad=1.0)
    cap = (
        "Figure 7 (caution). Al–Cu leave-one-composition-out (LOGO) for residual MFNN after "
        "$\\texttt{diff\\_type}$ splitting and one-hot features (13 folds; metrics from "
        "`LOGO_AlCu_difftype_feat_summary.csv`, not recomputed). (a) MAPE by hold-out group "
        f"(frozen overall mean ${mean}\\pm{std}\\%$). (b) Same fold MAPE versus composition "
        "distance $\\Delta x_{\\mathrm{Cu}}$ to the nearest other high-fidelity training "
        "composition. Large MAPE at small $\\Delta x_{\\mathrm{Cu}}$ (e.g. "
        "$\\mathrm{Al}_{80}\\mathrm{Cu}_{20}$ tracer) highlights label/neighborhood limits "
        "rather than a transferable extrapolation success. Not a cross-alloy claim and not a "
        "PINN/PPINN formulation. File: `Fig7_LOGO_distance_caution` "
        "(legacy pure-bar `Fig7_LOGO_MAPE_bars` retained)."
    )
    layers = (
        "L1_Background_and_Guides: frozen mean line\n"
        "L2_Data_Series: LOGO bars; MAPE vs delta x_Cu\n"
        "L3_ErrorBars_and_Arrows: none\n"
        "L4_Typography_and_Math: (a)(b), caution titles"
    )
    _save(fig, "Fig7_LOGO_distance_caution", cap, layers)
    plt.close(fig)


def main() -> None:
    apply_style()
    fig2_phase_space_coverage()
    fig5_arrhenius_representative()
    fig7_logo_distance_caution()
    print("P1 Gemini figures done.")


if __name__ == "__main__":
    main()
