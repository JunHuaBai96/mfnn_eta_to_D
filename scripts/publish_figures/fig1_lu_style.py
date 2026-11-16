#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fig. 1 — Lu et al. (PNAS 2020) style residual MFNN schema for η → D.

Four panels (2×2):
  A  Physical context: modified Sutherland LF prior vs scarce HF D_exp
  B  Single-fidelity NN
  C  Composite multi-fidelity NN (linear + nonlinear)
  D  Residual multi-fidelity NN (this work; α1, α2 + residual link)

Matches model.py ResidualMFNN:
  y_H = α1 * y_lin([x, y_L]) + α2 * F_nl([x, y_L])
Learning in log10 D; positivity via 10^ŷ. Not PINN/PPINN.

Run:
  /workspace/mfnn_venv/bin/python scripts/publish_figures/fig1_lu_style.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.lines import Line2D

# Allow running as script or import
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from _style import (  # noqa: E402
    C,
    W_DOUBLE,
    apply_style,
    save_figure,
)

# Node palette (Lu-like + Okabe–Ito)
IN_FC = "#D5D0E8"       # light purple input
IN_EC = "#6B5B95"
HID_FC = "#FFFFFF"
HID_EC = "#333333"
OUT_L_FC = "#F0C674"    # LF amber (Okabe LF-ish fill)
OUT_L_EC = C["LF_stroke"]
OUT_H_FC = "#7EB6D9"    # HF blue
OUT_H_EC = C["HF_stroke"]
OUT_Y_FC = "#7EB6D9"
SUM_FC = "#FFFFFF"
SUM_EC = "#222222"
RES_COLOR = "#D55E00"   # tracer/Okabe vermillion for residual link
ALPHA_ORANGE = "#E69F00"
NN_BOX_EC = "#888888"


def _arrow(ax, p0, p1, color="#222222", lw=0.7, ms=7, style="-|>", connectionstyle=None, z=1):
    kw = dict(
        arrowstyle=style,
        mutation_scale=ms,
        lw=lw,
        color=color,
        zorder=z,
        shrinkA=0,
        shrinkB=0,
    )
    if connectionstyle:
        kw["connectionstyle"] = connectionstyle
    ax.add_patch(FancyArrowPatch(p0, p1, **kw))


def _node(ax, xy, r, fc, ec, label=None, fontsize=6.5, text_color="#111", lw=0.8, z=3):
    circ = Circle(xy, r, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z)
    ax.add_patch(circ)
    if label is not None:
        ax.text(
            xy[0], xy[1], label, ha="center", va="center",
            fontsize=fontsize, color=text_color, zorder=z + 1,
        )
    return circ


def _dashed_box(ax, xy, w, h, label=None, label_pos="top"):
    rect = FancyBboxPatch(
        xy, w, h,
        boxstyle="round,pad=0.01,rounding_size=0.04",
        linewidth=0.7, edgecolor=NN_BOX_EC, facecolor="none",
        linestyle=(0, (2.2, 1.6)), zorder=0,
    )
    ax.add_patch(rect)
    if label:
        if label_pos == "top":
            ax.text(xy[0] + w / 2, xy[1] + h + 0.08, label,
                    ha="center", va="bottom", fontsize=7, color="#444", fontstyle="italic")
        elif label_pos == "bottom":
            ax.text(xy[0] + w / 2, xy[1] - 0.08, label,
                    ha="center", va="top", fontsize=7, color="#444", fontstyle="italic")
        elif label_pos == "left":
            ax.text(xy[0] - 0.06, xy[1] + h / 2, label,
                    ha="right", va="center", fontsize=7, color="#444", fontstyle="italic", rotation=90)


def _fully_connect(ax, left_nodes, right_nodes, color="#555555", lw=0.35, alpha=0.55):
    for a in left_nodes:
        for b in right_nodes:
            ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, alpha=alpha, zorder=1)


# ---------------------------------------------------------------------------
# Panel A — physical / problem context
# ---------------------------------------------------------------------------
def draw_panel_a(ax) -> None:
    """Physical context: viscosity/LF prior vs scarce HF D_exp.

    No twin y-axis and no mid-panel arrows/labels — avoids gutter occlusion.
    Relationship is conveyed by the two bottom equation callouts only.
    """
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    ax.text(0.15, 5.95, "A", fontsize=11, fontweight="bold", va="top", ha="left")

    # Wide separation between the two mini-plots
    left = ax.inset_axes([0.05, 0.30, 0.34, 0.58])
    T = np.linspace(900, 1400, 80)
    eta = 1.8 * np.exp(2800.0 / T)
    left.plot(T, eta, color=C["LF_stroke"], lw=1.4, label=r"$\eta(T)$")
    left.set_xlabel(r"$T$ (K)", fontsize=7)
    left.set_ylabel(r"$\eta$ (mPa$\cdot$s)", fontsize=7, color=C["LF_stroke"])
    for _s in ("top", "right", "bottom", "left"):
        left.spines[_s].set_visible(True)
    left.tick_params(direction="in", top=True, right=True, labelsize=6, colors="#333")
    left.set_title(r"Viscosity / LF prior", fontsize=8, pad=3, color="#222")
    left.legend(fontsize=6, loc="upper right", frameon=False)

    right = ax.inset_axes([0.60, 0.30, 0.34, 0.58])
    rng = np.random.default_rng(7)
    T_hf = np.array([950, 1000, 1050, 1100, 1150, 1200, 1250, 1300])
    D_true = 2.5e-9 * np.exp(-4500.0 / T_hf) * 1e9
    D_hf = D_true * (1 + 0.12 * rng.normal(size=len(T_hf)))
    right.semilogy(
        T_hf,
        np.clip(D_hf, 1e-2, None),
        "o",
        color=C["HF"],
        ms=5.5,
        markeredgecolor=C["HF_stroke"],
        markeredgewidth=0.6,
        zorder=3,
        label=r"$D_{\mathrm{exp}}$",
    )
    T_line = np.linspace(900, 1350, 60)
    D_lf_line = 0.8 * np.exp(-3800.0 / T_line)
    right.semilogy(
        T_line,
        D_lf_line,
        "--",
        color=C["LF"],
        lw=1.1,
        alpha=0.85,
        label=r"$D_{\mathrm{LF}}$",
        zorder=2,
    )
    right.set_xlabel(r"$T$ (K)", fontsize=7)
    right.set_ylabel(r"$D$ ($10^{-9}\,\mathrm{m}^{2}/\mathrm{s}$)", fontsize=7, color=C["HF_stroke"], labelpad=2)
    for _s in ("top", "right", "bottom", "left"):
        right.spines[_s].set_visible(True)
    right.tick_params(direction="in", top=True, right=True, labelsize=6)
    right.set_title(r"Scarce HF $D_{\mathrm{exp}}$", fontsize=8, pad=3, color="#222")
    right.legend(fontsize=6, loc="lower right", frameon=False)

    ax.text(
        2.4,
        0.42,
        r"Modified Sutherland: $D_{\mathrm{LF}}=\dfrac{k_{\mathrm{B}}T}{c\,\eta\,r_i(T)}$",
        ha="center",
        va="center",
        fontsize=6.5,
        color="#333",
        bbox=dict(boxstyle="round,pad=0.25", fc=C["box_lf"], ec=C["LF"], lw=0.6),
        clip_on=False,
        zorder=6,
    )
    ax.text(
        7.6,
        0.42,
        r"HF targets: $y_{\mathrm{H}}=\log_{10} D_{\mathrm{exp}}$ (sparse)",
        ha="center",
        va="center",
        fontsize=6.5,
        color="#333",
        bbox=dict(boxstyle="round,pad=0.25", fc=C["box_hf"], ec=C["HF"], lw=0.6),
        clip_on=False,
        zorder=6,
    )


# ---------------------------------------------------------------------------
# Shared NN drawing helpers for B/C/D
# ---------------------------------------------------------------------------
def _draw_mlp_column(ax, x, ys, r, kind="hidden"):
    """kind: input | hidden | linear | out_l | out_h | sum"""
    nodes = []
    for y in ys:
        if kind == "input":
            _node(ax, (x, y), r, IN_FC, IN_EC, label=None, fontsize=5.5)
        elif kind == "hidden":
            _node(ax, (x, y), r, HID_FC, HID_EC, label=r"$\sigma$", fontsize=6.5)
        elif kind == "linear":
            _node(ax, (x, y), r, HID_FC, HID_EC, label=r"$I$", fontsize=7.5)
        elif kind == "out_l":
            _node(ax, (x, y), r * 1.15, OUT_L_FC, OUT_L_EC, label=None)
        elif kind == "out_h":
            _node(ax, (x, y), r * 1.15, OUT_H_FC, OUT_H_EC, label=None)
        elif kind == "sum":
            _node(ax, (x, y), r * 1.05, SUM_FC, SUM_EC, label=r"$+$", fontsize=8)
        nodes.append((x, y))
    return nodes


def draw_panel_b(ax) -> None:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    ax.text(0.15, 5.95, "B", fontsize=11, fontweight="bold", va="top", ha="left")
    ax.text(5.0, 5.85, "Single-fidelity NN", ha="center", va="top", fontsize=8.5,
            fontweight="bold", color="#222")

    # Inputs
    in_labels = [r"$T$", r"$x$", r"$\eta$", r"type"]
    in_ys = np.linspace(4.6, 1.4, len(in_labels))
    in_nodes = []
    for lab, y in zip(in_labels, in_ys):
        _node(ax, (1.3, y), 0.28, IN_FC, IN_EC)
        ax.text(0.55, y, lab, ha="right", va="center", fontsize=7, color="#333")
        in_nodes.append((1.3, y))

    h1_ys = np.linspace(4.7, 1.3, 5)
    h2_ys = np.linspace(4.5, 1.5, 4)
    h1 = _draw_mlp_column(ax, 3.4, h1_ys, 0.26, "hidden")
    h2 = _draw_mlp_column(ax, 5.5, h2_ys, 0.26, "hidden")
    out = _draw_mlp_column(ax, 7.6, [3.0], 0.32, "out_h")
    ax.text(7.6, 3.55, r"$y$", ha="center", va="bottom", fontsize=8, color=C["HF_stroke"])
    ax.text(7.6, 2.35, r"$\log_{10} D$", ha="center", va="top", fontsize=6.5, color="#555")

    _fully_connect(ax, in_nodes, h1)
    _fully_connect(ax, h1, h2)
    _fully_connect(ax, h2, out)

    ax.text(5.0, 0.45, r"HF-only baseline (no LF channel)", ha="center", va="center",
            fontsize=6.5, color="#666", style="italic")


def draw_panel_c(ax) -> None:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    ax.text(0.15, 5.95, "C", fontsize=11, fontweight="bold", va="top", ha="left")
    ax.text(5.0, 5.85, "Multi-fidelity NN", ha="center", va="top", fontsize=8.5,
            fontweight="bold", color="#222")

    # Shared inputs (compact)
    in_labels = [r"$x_1$", r"$x_2$"]
    in_ys = [4.2, 2.6]
    in_nodes = []
    for lab, y in zip(in_labels, in_ys):
        _node(ax, (0.9, y), 0.24, IN_FC, IN_EC)
        ax.text(0.35, y, lab, ha="right", va="center", fontsize=7)
        in_nodes.append((0.9, y))

    # NN_L
    _dashed_box(ax, (1.55, 1.55), 2.55, 3.5, label=r"$\mathrm{NN}_L$", label_pos="top")
    l1 = _draw_mlp_column(ax, 2.1, [4.3, 3.4, 2.5], 0.22, "hidden")
    l2 = _draw_mlp_column(ax, 3.2, [3.9, 2.9], 0.22, "hidden")
    yL = _draw_mlp_column(ax, 4.35, [3.4], 0.28, "out_l")[0]
    ax.text(4.35, 3.95, r"$y_L$", ha="center", va="bottom", fontsize=7.5, color=C["LF_stroke"])
    _fully_connect(ax, in_nodes, l1)
    _fully_connect(ax, l1, l2)
    _fully_connect(ax, l2, [yL])

    # NN_H takes [x, y_L]
    _dashed_box(ax, (5.0, 1.1), 4.5, 4.2, label=r"$\mathrm{NN}_H$", label_pos="top")
    # concat inputs into H
    h_in_ys = [4.5, 3.6, 2.7]
    h_in = []
    for i, y in enumerate(h_in_ys):
        _node(ax, (5.55, y), 0.22, IN_FC, IN_EC)
        h_in.append((5.55, y))
    # connections from x and y_L into H inputs
    for a in in_nodes:
        for b in h_in[:2]:
            ax.plot([a[0], b[0]], [a[1], b[1]], color="#888", lw=0.35, alpha=0.5, zorder=1)
    ax.plot([yL[0], h_in[2][0]], [yL[1], h_in[2][1]], color=C["LF"], lw=0.7, alpha=0.8, zorder=1)

    # nonlinear branch
    nl1 = _draw_mlp_column(ax, 6.7, [4.6, 3.9, 3.2], 0.2, "hidden")
    nl2 = _draw_mlp_column(ax, 7.7, [4.25, 3.55], 0.2, "hidden")
    # linear branch
    lin = _draw_mlp_column(ax, 7.2, [2.0], 0.24, "linear")
    _fully_connect(ax, h_in, nl1)
    _fully_connect(ax, nl1, nl2)
    for a in h_in:
        ax.plot([a[0], lin[0][0]], [a[1], lin[0][1]], color="#888", lw=0.35, alpha=0.45, zorder=1)

    # sum → y_H
    plus = _draw_mlp_column(ax, 8.7, [3.1], 0.26, "sum")[0]
    yH = _draw_mlp_column(ax, 9.55, [3.1], 0.28, "out_h")[0]
    ax.text(9.55, 3.65, r"$y_H$", ha="center", va="bottom", fontsize=7.5, color=C["HF_stroke"])
    for src in [nl2[0], nl2[1], lin[0]]:
        _arrow(ax, src, (plus[0] - 0.28, plus[1]), color="#333", lw=0.6, ms=6)
    _arrow(ax, (plus[0] + 0.28, plus[1]), (yH[0] - 0.3, yH[1]), color="#333", lw=0.7, ms=6)

    ax.text(5.0, 0.4, r"Composite MFNN: linear $I$ + nonlinear $\sigma$ on $[x,y_L]$",
            ha="center", va="center", fontsize=6.5, color="#666", style="italic")


def draw_panel_d(ax) -> None:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    ax.text(0.15, 5.95, "D", fontsize=11, fontweight="bold", va="top", ha="left")
    ax.text(5.0, 5.85, "Residual multi-fidelity NN (this work)", ha="center", va="top",
            fontsize=8.5, fontweight="bold", color=C["MFNN_stroke"])

    # Inputs for η→D
    in_labels = [r"$T$", r"$x$", r"$\eta$"]
    in_ys = [4.5, 3.5, 2.5]
    in_nodes = []
    for lab, y in zip(in_labels, in_ys):
        _node(ax, (0.85, y), 0.24, IN_FC, IN_EC)
        ax.text(0.3, y, lab, ha="right", va="center", fontsize=7)
        in_nodes.append((0.85, y))

    # NN_L
    _dashed_box(ax, (1.45, 1.7), 2.4, 3.35, label=r"$\mathrm{NN}_L$", label_pos="top")
    l1 = _draw_mlp_column(ax, 1.95, [4.4, 3.5, 2.6], 0.2, "hidden")
    l2 = _draw_mlp_column(ax, 2.9, [4.0, 3.0], 0.2, "hidden")
    yL = _draw_mlp_column(ax, 3.85, [3.5], 0.28, "out_l")[0]
    ax.text(3.85, 4.05, r"$y_L$", ha="center", va="bottom", fontsize=7.5, color=C["LF_stroke"])
    ax.text(3.85, 2.95, r"$\log_{10} D_{\mathrm{LF}}$", ha="center", va="top", fontsize=5.8, color="#666")
    _fully_connect(ax, in_nodes, l1)
    _fully_connect(ax, l1, l2)
    _fully_connect(ax, l2, [yL])

    # NN_H region
    _dashed_box(ax, (4.55, 0.95), 5.0, 4.45, label=r"$\mathrm{NN}_H$ (residual)", label_pos="top")

    # concat features [x, y_L]
    h_in_ys = [4.7, 3.9, 3.1, 2.3]
    h_in = []
    for y in h_in_ys:
        _node(ax, (5.15, y), 0.2, IN_FC, IN_EC)
        h_in.append((5.15, y))
    for a in in_nodes:
        for b in h_in[:3]:
            ax.plot([a[0], b[0]], [a[1], b[1]], color="#999", lw=0.3, alpha=0.45, zorder=1)
    ax.plot([yL[0], h_in[3][0]], [yL[1], h_in[3][1]], color=C["LF"], lw=0.75, alpha=0.85, zorder=1)

    # Nonlinear path F_nl
    nl1 = _draw_mlp_column(ax, 6.15, [4.85, 4.15, 3.45], 0.18, "hidden")
    nl2 = _draw_mlp_column(ax, 7.05, [4.5, 3.8], 0.18, "hidden")
    _fully_connect(ax, h_in, nl1)
    _fully_connect(ax, nl1, nl2)

    # Linear path I / A[x,y_L]+b
    lin = _draw_mlp_column(ax, 6.6, [1.85], 0.22, "linear")
    for a in h_in:
        ax.plot([a[0], lin[0][0]], [a[1], lin[0][1]], color="#999", lw=0.3, alpha=0.4, zorder=1)

    # Mixing weights (Lu-style α annotations on paths)
    # Intermediate combine nodes
    mix_nl = (7.95, 4.15)
    mix_lin = (7.95, 1.85)
    _node(ax, mix_nl, 0.2, "#FFF4E0", ALPHA_ORANGE, label=None)
    _node(ax, mix_lin, 0.2, "#FFF4E0", ALPHA_ORANGE, label=None)
    ax.text(7.95, 4.55, r"$\alpha_2$", ha="center", va="bottom", fontsize=7.5,
            color=ALPHA_ORANGE, fontweight="bold")
    ax.text(7.95, 1.45, r"$\alpha_1$", ha="center", va="top", fontsize=7.5,
            color=ALPHA_ORANGE, fontweight="bold")
    for src in nl2:
        _arrow(ax, src, (mix_nl[0] - 0.22, mix_nl[1]), color="#333", lw=0.55, ms=5)
    _arrow(ax, (lin[0][0] + 0.22, lin[0][1]), (mix_lin[0] - 0.22, mix_lin[1]),
           color="#333", lw=0.55, ms=5)

    # Final sum and y_H
    plus = _draw_mlp_column(ax, 8.7, [3.0], 0.26, "sum")[0]
    yH = _draw_mlp_column(ax, 9.55, [3.0], 0.28, "out_h")[0]
    ax.text(9.55, 3.55, r"$y_H$", ha="center", va="bottom", fontsize=7.5, color=C["HF_stroke"])
    ax.text(9.55, 2.45, r"$\log_{10}\hat{D}_{\mathrm{HF}}$", ha="center", va="top",
            fontsize=5.8, color="#555")

    _arrow(ax, (mix_nl[0] + 0.22, mix_nl[1]), (plus[0] - 0.1, plus[1] + 0.22),
           color="#333", lw=0.65, ms=6)
    _arrow(ax, (mix_lin[0] + 0.22, mix_lin[1]), (plus[0] - 0.1, plus[1] - 0.22),
           color="#333", lw=0.65, ms=6)
    _arrow(ax, (plus[0] + 0.28, plus[1]), (yH[0] - 0.3, yH[1]), color="#333", lw=0.7, ms=6)

    # RED residual / skip from y_L to final sum (Lu panel D)
    _arrow(
        ax, (yL[0] + 0.3, yL[1] - 0.05), (plus[0] - 0.25, plus[1] + 0.05),
        color=RES_COLOR, lw=1.35, ms=8,
        connectionstyle="arc3,rad=-0.28", z=4,
    )
    ax.text(6.35, 2.55, "residual", fontsize=6.5, color=RES_COLOR, fontstyle="italic",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec=RES_COLOR, lw=0.5, alpha=0.9))

    # Equation annotation
    ax.text(
        5.0, 0.38,
        r"$y_H=\alpha_1\,(A[x,y_L]+b)+\alpha_2\,F_{\mathrm{nl}}(x,y_L)$"
        + r"  ·  $\sigma$=nonlinear, $I$=linear; red=residual link",
        ha="center", va="center", fontsize=6.2, color="#333",
        bbox=dict(boxstyle="round,pad=0.28", fc="#F7FBF9", ec=C["MFNN"], lw=0.7),
    )


def build_figure():
    apply_style()
    # Elsevier full-page width ~180 mm; tall enough for Lu-like density
    fig = plt.figure(figsize=(W_DOUBLE, 155 / 25.4))
    # 2×2 grid with a bit more height for A
    gs = fig.add_gridspec(2, 2, hspace=0.18, wspace=0.12,
                          left=0.02, right=0.98, top=0.96, bottom=0.03)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    # Subtle panel backgrounds for D emphasis
    for ax in (ax_a, ax_b, ax_c, ax_d):
        ax.set_facecolor("white")
    # light green wash behind D
    ax_d.add_patch(Rectangle((0, 0), 10, 6.2, facecolor="#F3FAF7", edgecolor="none", zorder=-1))

    draw_panel_a(ax_a)
    draw_panel_b(ax_b)
    draw_panel_c(ax_c)
    draw_panel_d(ax_d)

    caption = (
        "Lu-style residual multi-fidelity network for η→D. "
        "(A) Modified Sutherland LF prior from viscosity and scarce HF "
        r"$D_{\mathrm{exp}}$. "
        "(B) Single-fidelity NN (HF-only). "
        "(C) Composite MFNN with linear $I$ and nonlinear $\\sigma$ branches on $[x,y_L]$. "
        "(D) Residual MFNN used here: "
        r"$y_H=\alpha_1(A[x,y_L]+b)+\alpha_2 F_{\mathrm{nl}}(x,y_L)$ "
        "with learnable $\\alpha_1,\\alpha_2$ and red residual link from $y_L$; "
        r"positivity via $\hat{D}=10^{\hat{y}}$. Not PINN/PPINN."
    )
    layers = (
        "L1_Background_and_Guides: panel washes, dashed NN_L/NN_H boxes\n"
        "L2_Data_Series: schematic curves (A), node fills (input/LF/HF)\n"
        "L3_ErrorBars_and_Arrows: edges, residual red skip, α mix arrows\n"
        "L4_Typography_and_Math: panel letters, σ/I labels, residual equation"
    )
    save_figure(
        fig,
        "Fig1_mfnn_residual_schema",
        "fig1",
        caption,
        layers,
        legacy_names=["fig1_mfnn_schema"],
    )
    # also keep a dated preview name
    from _style import FIG_DIR
    preview = FIG_DIR / "fig1_lu_style_preview.png"
    fig.savefig(preview, dpi=300)
    print("preview", preview)
    plt.close(fig)
    return caption


if __name__ == "__main__":
    build_figure()
