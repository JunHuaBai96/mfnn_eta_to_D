"""Shared JCP/Elsevier journal style (Okabe-Ito colour palette)."""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "outputs" / "figures"
VECTOR_PACK = ROOT / "outputs" / "figures_vector"
JCP_FIG = ROOT / "outputs" / "jcp_submission" / "figures"
RESULTS = ROOT / "outputs" / "results"
DATA = ROOT / "data"

# Semantic palette (Okabe–Ito derived) — fill / stroke
C = {
    "MFNN": "#009E73",
    "MFNN_stroke": "#006B4E",
    "HF": "#0072B2",
    "HF_stroke": "#004D7A",
    "LF": "#E69F00",
    "LF_stroke": "#A87300",
    "tracer": "#D55E00",
    "tracer_stroke": "#994300",
    "inter": "#56B4E9",
    "inter_stroke": "#1B5E82",
    "impurity": "#CC79A7",
    "impurity_stroke": "#8F4B70",
    "self": "#7F7F7F",
    "ref": "#7F7F7F",
    "ref_dark": "#333333",
    "band": "#E5E5E5",
    "W": "#009E73",
    "G": "#0072B2",
    # Fig1 boxes
    "box_in": "#F4F6F8",
    "box_in_ec": "#4A5568",
    "box_lf": "#FFF8EB",
    "box_lf_ec": "#E69F00",
    "box_mfnn": "#E6F6F2",
    "box_mfnn_ec": "#009E73",
    "box_mfnn_title": "#006B4E",
    "box_hf": "#EBF5FB",
    "box_hf_ec": "#0072B2",
}

# Canvas widths (inches)
MM = 1.0 / 25.4
W_SINGLE = 88 * MM   # 3.46 in
W_MID = 135 * MM     # 5.31 in
W_DOUBLE = 180 * MM  # 7.09 in
W_FIG4 = 160 * MM    # checklist override
W_FIG5 = 140 * MM

# Frozen headline numbers (do not recompute for annotations)
FROZEN = {
    "W_MFNN_MAPE": (26.18, 1.33),
    "W_MFNN_F2": (0.96, 0.033),
    "W_MFNN_R2": (0.392, 0.094),
    "W_HF_MAPE": (30.98, 4.43),
    "W_HF_F2": (0.973, 0.033),
    "W_HF_R2": (0.263, 0.076),
    "W_LF_MAPE": (109.6, 13.13),
    "W_LF_F2": (0.56, 0.10),
    "W_LF_R2": (-2.588, 0.399),
    "alpha1": (0.5369, 0.1200),
    "alpha2": (0.6525, 0.0301),
    "LOGO_mean": (39.4, 39.7),
    "Al80_tracer_MAPE": 156.5,
    "Al80_inter_MAPE": 6.5,
    "Al80_tracer_joint": 156.5,
    "Al80_inter_joint": 6.5,
    "Al80_tracer_sep": 173.0,
    "Al80_inter_sep": 11.0,
    "G_MFNN_MAPE": (27.36, 12.88),
    "G_MFNN_F2": (0.791, 0.257),
    "S1_MAPE": (178.20, 169.55, 175.27, 142.93),
    "S2_MAPE": (9.81, 1.73),
    "S3_MAPE": (122.0, 48.0, 31.0),
}


def apply_style() -> None:
    """Lu et al. PNAS-like axes: full box frame + inward ticks on all four sides."""
    mpl.rcParams.update(
        {
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "mathtext.fontset": "stixsans",
            "axes.linewidth": 0.75,
            "xtick.major.width": 0.75,
            "ytick.major.width": 0.75,
            "xtick.minor.width": 0.5,
            "ytick.minor.width": 0.5,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "xtick.minor.visible": False,
            "ytick.minor.visible": False,
            "lines.linewidth": 1.25,
            "patch.linewidth": 0.6,
            "legend.frameon": False,
            "figure.dpi": 300,
            "savefig.dpi": 600,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#333333",
            "axes.labelcolor": "#222222",
            "axes.titlesize": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "font.size": 8,
            "axes.spines.top": True,
            "axes.spines.right": True,
            "axes.spines.bottom": True,
            "axes.spines.left": True,
            "axes.grid": False,
        }
    )


def panel_letter(ax, letter: str, x: float = -0.12, y: float = 1.05) -> None:
    ax.text(
        x,
        y,
        f"({letter})",
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        va="bottom",
        ha="left",
        clip_on=False,
    )


def box_spines(ax, *, ticks: bool = True) -> None:
    """Full rectangular frame + inward ticks on all four sides (Lu PNAS style)."""
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_linewidth(0.75)
        ax.spines[side].set_color("#333333")
    if ticks:
        ax.tick_params(
            axis="both",
            which="major",
            direction="in",
            top=True,
            right=True,
            bottom=True,
            left=True,
            labelsize=8,
            length=3.5,
            width=0.75,
        )
        ax.tick_params(
            axis="both",
            which="minor",
            direction="in",
            top=True,
            right=True,
            bottom=True,
            left=True,
            length=2.0,
            width=0.5,
        )
        for lab in ax.get_xticklabels():
            lab.set_rotation(0)
        for lab in ax.get_yticklabels():
            lab.set_rotation(0)


def despine(ax, top=True, right=True) -> None:
    """Deprecated for new figures — prefer box_spines. Kept for compatibility."""
    # Lu-style request: keep full box; ignore top/right removal flags.
    box_spines(ax)


def save_figure(fig, stem: str, shortname: str, caption: str, ai_layers: str, legacy_names=None) -> None:
    """Save PDF+SVG+PNG to figures/, AI pack, and jcp_submission/figures."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    JCP_FIG.mkdir(parents=True, exist_ok=True)
    pack = VECTOR_PACK / stem
    pack.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg", "png"):
        kw = {"dpi": 600} if ext == "png" else {}
        fig.savefig(FIG_DIR / f"{stem}.{ext}", **kw)
        fig.savefig(pack / f"{stem}.{ext}", **kw)
        if ext == "pdf":
            fig.savefig(JCP_FIG / f"{stem}.pdf")
        if ext == "png":
            fig.savefig(JCP_FIG / f"{stem}.png", dpi=600)
    readme = (
        f"Stem: {stem}\nShortname: {shortname}\n\n"
        f"Illustrator 4-layer notes:\n{ai_layers}\n\n"
        f"Caption draft:\n{caption}\n\n"
        "Cleanup: Select>Object>Clipping Masks (keep scatter clip only); "
        "ungroup text; svg.fonttype=none so text stays editable.\n"
        "Export: PDF Press Quality sRGB; PNG 600 ppi Art Optimized.\n"
        "Style: full box spines + inward ticks (Lu PNAS-like).\n"
    )
    (pack / "README.txt").write_text(readme, encoding="utf-8")
    if legacy_names:
        for name in legacy_names:
            for ext in ("pdf", "png", "svg"):
                src = FIG_DIR / f"{stem}.{ext}"
                if not src.exists():
                    continue
                shutil.copy2(src, FIG_DIR / f"{name}.{ext}")
                if ext in ("pdf", "png"):
                    shutil.copy2(src, JCP_FIG / f"{name}.{ext}")
    print("saved", stem)
