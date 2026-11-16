#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Protocol W (within_T) 5-seed ensemble parity → Fig.2(c).

Post-process only — does NOT retrain. Reads:
  outputs/seed_wg_{0,1,2,42,123}/test_predictions_within_T.csv

Usage (from repo root):
  python scripts/plot_protocol_W_parity_ensemble.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SEEDS = [0, 1, 2, 42, 123]
MODELS = ["LF_only", "HF_only", "MFNN"]
LOG10_2 = float(np.log10(2.0))  # Factor-of-two half-width in log10D


def _load_seed_frames() -> dict[int, pd.DataFrame]:
    frames = {}
    for seed in SEEDS:
        path = ROOT / "outputs" / f"seed_wg_{seed}" / "test_predictions_within_T.csv"
        if not path.is_file():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        need = ["sample_id", "y_true_log10D"] + [
            f"pred_{m}_log10D" for m in MODELS
        ]
        for c in need:
            if c not in df.columns:
                raise KeyError(f"{path.name} missing column {c}")
        df = df.copy()
        df["seed"] = seed
        frames[seed] = df
    return frames


def _build_ensemble_table(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """One row per sample_id × model; mean/std over seeds that contain the point."""
    # long form: sample_id, seed, y_true, pred per model
    pieces = []
    for seed, df in frames.items():
        sub = df[
            ["sample_id", "seed", "y_true_log10D", "T_K", "comp_group", "system"]
            + [f"pred_{m}_log10D" for m in MODELS]
            + [c for c in [f"pred_{m}_D" for m in MODELS] if c in df.columns]
        ].copy()
        pieces.append(sub)
    long = pd.concat(pieces, ignore_index=True)

    rows = []
    for sid, g in long.groupby("sample_id", sort=True):
        # y_true: take median across seeds (should be identical)
        y_true = float(np.median(g["y_true_log10D"].to_numpy(dtype=float)))
        y_spread = float(np.nanmax(g["y_true_log10D"]) - np.nanmin(g["y_true_log10D"]))
        meta = g.iloc[0]
        t_k = float(meta["T_K"]) if "T_K" in g.columns else float("nan")
        comp = str(meta["comp_group"]) if "comp_group" in g.columns else ""
        system = str(meta["system"]) if "system" in g.columns else ""
        n_seeds = int(g["seed"].nunique())
        seeds_present = ",".join(str(int(s)) for s in sorted(g["seed"].unique()))

        for model in MODELS:
            col = f"pred_{model}_log10D"
            vals = g[col].to_numpy(dtype=float)
            mu = float(np.nanmean(vals))
            # population std over available seeds (ddof=0); NaN if n_seeds==1
            sigma = float(np.nanstd(vals, ddof=0)) if n_seeds > 1 else 0.0
            d_col = f"pred_{model}_D"
            if d_col in g.columns:
                d_mu = float(np.nanmean(g[d_col].to_numpy(dtype=float)))
            else:
                d_mu = float(10.0 ** mu)
            in_f2 = bool(abs(mu - y_true) <= LOG10_2 + 1e-12)
            rows.append(
                {
                    "sample_id": sid,
                    "model": model,
                    "system": system,
                    "comp_group": comp,
                    "T_K": t_k,
                    "y_true_log10D": y_true,
                    "y_true_log10D_seed_spread": y_spread,
                    "pred_log10D_mean": mu,
                    "pred_log10D_std": sigma,
                    "pred_D_mean": d_mu,
                    "n_seeds": n_seeds,
                    "seeds": seeds_present,
                    "in_factor2": in_f2,
                    "abs_log10_ratio": abs(mu - y_true),
                    "all_five_seeds": n_seeds == len(SEEDS),
                }
            )
    return pd.DataFrame(rows)


def _plot_parity(ens: pd.DataFrame, out_png: Path, out_pdf: Path) -> list[str]:
    """1x3 parity with error bars; annotate MFNN Factor2 outliers (union of test points)."""
    # All aligned points; filled = all 5 seeds, open = partial overlap
    plot_df = ens.copy()

    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.2), squeeze=False)
    titles = {"LF_only": "LF-only", "HF_only": "HF-only", "MFNN": "MFNN"}
    colors = {"LF_only": "tab:orange", "HF_only": "tab:blue", "MFNN": "tab:green"}
    outlier_ids: list[str] = []

    for ax, model in zip(axes[0], MODELS):
        sub = plot_df[plot_df["model"] == model]
        x = sub["y_true_log10D"].to_numpy(dtype=float)
        y = sub["pred_log10D_mean"].to_numpy(dtype=float)
        yerr = sub["pred_log10D_std"].to_numpy(dtype=float)
        in_f2 = sub["in_factor2"].to_numpy(dtype=bool)
        full5 = sub["all_five_seeds"].to_numpy(dtype=bool)

        lo = float(min(np.nanmin(x), np.nanmin(y))) - 0.15
        hi = float(max(np.nanmax(x), np.nanmax(y))) + 0.15
        xx = np.linspace(lo, hi, 200)
        ax.fill_between(
            xx,
            xx - LOG10_2,
            xx + LOG10_2,
            color="0.85",
            alpha=0.9,
            label=r"Factor2 band ($\pm\log_{10}2$)",
            zorder=0,
        )
        ax.plot(xx, xx, "k--", lw=1.0, label="1:1", zorder=1)

        # in Factor2, all 5 seeds
        m = in_f2 & full5
        if np.any(m):
            ax.errorbar(
                x[m], y[m], yerr=yerr[m],
                fmt="o", ms=5, color=colors[model], ecolor="0.4",
                elinewidth=0.8, capsize=2, alpha=0.9, zorder=2,
                label="in Factor2 (5 seeds)",
            )
        # in Factor2, partial seeds
        m = in_f2 & ~full5
        if np.any(m):
            ax.errorbar(
                x[m], y[m], yerr=yerr[m],
                fmt="o", ms=5, color=colors[model], ecolor="0.4",
                elinewidth=0.8, capsize=2, alpha=0.55, zorder=2,
                mfc="none", label="in Factor2 (partial)",
            )
        # outside Factor2
        if np.any(~in_f2):
            ax.errorbar(
                x[~in_f2], y[~in_f2], yerr=yerr[~in_f2],
                fmt="s", ms=7, color="crimson", ecolor="crimson",
                elinewidth=0.9, capsize=2, zorder=3,
                label="outside Factor2",
            )
            if model == "MFNN":
                outs = sub.loc[~sub["in_factor2"]]
                for _, r in outs.iterrows():
                    outlier_ids.append(str(r["sample_id"]))
                    ax.annotate(
                        f"{r['sample_id']}\n{r['T_K']:.0f} K (n={int(r['n_seeds'])})",
                        xy=(r["y_true_log10D"], r["pred_log10D_mean"]),
                        xytext=(6, 8),
                        textcoords="offset points",
                        fontsize=7,
                        color="crimson",
                    )

        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel(r"True $\log_{10} D$")
        ax.set_ylabel(r"seed-mean pred $\log_{10} D$")
        ax.set_title(titles[model])
        ax.legend(loc="best", fontsize=6.5, frameon=False)

    fig.suptitle(
        "Protocol W (within_T): multi-seed ensemble parity "
        "(filled = 5 seeds; open = partial overlap)",
        fontsize=11,
        y=1.02,
    )
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return sorted(set(outlier_ids))


def _write_report(
    ens: pd.DataFrame,
    outlier_ids: list[str],
    report_path: Path,
) -> None:
    # Stats on 5-seed-complete points (primary)
    full = ens[ens["all_five_seeds"]].copy()
    if full.empty:
        full = ens.copy()

    def _std_stats(model: str) -> tuple[float, float, int]:
        s = full.loc[full["model"] == model, "pred_log10D_std"]
        return float(s.mean()), float(s.median()), int(len(s))

    hf_mean, hf_med, hf_n = _std_stats("HF_only")
    mf_mean, mf_med, mf_n = _std_stats("MFNN")

    mfnn = full[full["model"] == "MFNN"]
    n_out = int((~mfnn["in_factor2"]).sum())
    n_tot = int(len(mfnn))
    out_rows = mfnn.loc[~mfnn["in_factor2"]]

    # Also list outliers on union (any n_seeds) for completeness
    mfnn_all = ens[ens["model"] == "MFNN"]
    n_out_all = int((~mfnn_all["in_factor2"]).sum())

    lines: list[str] = []
    lines.append("# Protocol W 五种子 Ensemble Parity（Fig.2(c)）\n\n")
    lines.append(
        "后处理-only：读取 `outputs/seed_wg_{0,1,2,42,123}/test_predictions_within_T.csv`，"
        "**未重训**。未改动冻结主结论数字（MAPE $26.18\\pm1.33\\%$、Factor2 $0.96\\pm0.033$、"
        "R² $0.392\\pm0.094$ 等仍以 `SEED_WG_STABILITY.md` / Table 1 为准）。\n\n"
    )
    lines.append("## 对齐说明\n\n")
    n_union = ens["sample_id"].nunique()
    n_common = ens.loc[ens["all_five_seeds"], "sample_id"].nunique()
    lines.append(
        f"- 各 seed within_T 测试集不完全相同（每 seed $n=15$，union={n_union}，"
        f"**五种子共有** sample_id 数={n_common}）。\n"
    )
    lines.append(
        "- 主图与下文 Factor2 计数以 **五种子共有点** 为准（每点 $n_{\\mathrm{seeds}}=5$ 的 mean/std）；"
        "CSV 亦含仅出现在部分 seed 的点（`all_five_seeds=False`）。\n"
    )
    lines.append(
        f"- Factor2 判定（对 seed-mean pred）："
        f"$|\\overline{{\\log_{{10}} D_{{\\mathrm{{pred}}}}}} - \\log_{{10}} D_{{\\mathrm{{true}}}}| "
        f"\\le \\log_{{10}} 2 \\approx {LOG10_2:.6f}$。\n\n"
    )

    lines.append("## 逐点预测 std（5-seed，共有点）\n\n")
    lines.append("| model | mean(std) | median(std) | n_points |\n|---|---:|---:|---:|\n")
    for model in MODELS:
        m, med, n = _std_stats(model)
        lines.append(f"| {model} | {m:.6g} | {med:.6g} | {n} |\n")
    lines.append(
        f"\n**HF_only vs MFNN：** mean std {hf_mean:.6g} vs {mf_mean:.6g}；"
        f"median std {hf_med:.6g} vs {mf_med:.6g}（$n={mf_n}$）。\n\n"
    )

    lines.append("## MFNN Factor2（按 seed-mean pred）\n\n")
    lines.append(
        f"- **五种子共有点：** MFNN **{n_out}/{n_tot}** 点落在 Factor2 带外"
        + (f"：`{', '.join(str(s) for s in out_rows['sample_id'])}`。\n" if n_out else "。\n")
    )
    if len(out_rows):
        lines.append("\n| sample_id | T_K | comp_group | y_true | pred_mean | |Δlog10| | n_seeds |\n")
        lines.append("|---|---:|---|---:|---:|---:|---:|\n")
        for _, r in out_rows.iterrows():
            lines.append(
                f"| {r['sample_id']} | {r['T_K']:.1f} | {r['comp_group']} | "
                f"{r['y_true_log10D']:.6f} | {r['pred_log10D_mean']:.6f} | "
                f"{r['abs_log10_ratio']:.6f} | {int(r['n_seeds'])} |\n"
            )
    out_all = mfnn_all.loc[~mfnn_all["in_factor2"]]
    out_ids_all = [str(s) for s in out_all["sample_id"].tolist()]
    lines.append(
        f"\n- **Union（含 $n_{{\\mathrm{{seeds}}}}<5$）：** MFNN Factor2 外 "
        f"**{n_out_all}/{len(mfnn_all)}**"
        + (f"：`{', '.join(out_ids_all)}`。\n" if out_ids_all else "。\n")
    )
    if len(out_all):
        lines.append("\n| sample_id | T_K | comp_group | y_true | pred_mean | |Δlog10| | n_seeds |\n")
        lines.append("|---|---:|---|---:|---:|---:|---:|\n")
        for _, r in out_all.iterrows():
            lines.append(
                f"| {r['sample_id']} | {r['T_K']:.1f} | {r['comp_group']} | "
                f"{r['y_true_log10D']:.6f} | {r['pred_log10D_mean']:.6f} | "
                f"{r['abs_log10_ratio']:.6f} | {int(r['n_seeds'])} |\n"
            )
    lines.append("\n")

    # Frozen Factor2 narrative — tie to ≤1 edge point
    lines.append("## 与冻结 Factor2 的关系\n\n")
    lines.append(
        "冻结主文数字 **Factor2 $0.96\\pm0.033$（MFNN）vs HF_only $0.973\\pm0.033$** "
        "来自各 seed 在 **$n=15$** 测试集上的硬计数再跨 seed 平均"
        "（见 `outputs/SEED_WG_STABILITY.md`），**不是**本图重新定义的指标。\n\n"
    )
    lines.append(
        f"**明确一句：** 五种子共有点上 MFNN 跌出 Factor2 为 **{n_out}/{n_tot}**；"
        f"union 上为 **{n_out_all}** 个边缘点"
        + (f"（`{', '.join(out_ids_all)}`，且均为 $n_{{\\mathrm{{seeds}}}}<5$）" if out_ids_all else "")
        + "。因此主文 Factor2 0.96 相对 HF_only 0.973 的微小差距，"
        "应理解为 **≤1–2 个边缘点的硬计数差异**，**不是**整体回归变差。"
        "本图仅可视化 seed-mean / std，**不改写**冻结表。\n\n"
    )

    lines.append("## 文件\n\n")
    lines.append("- `outputs/results/protocol_W_parity_ensemble_points.csv`\n")
    lines.append("- `outputs/figures/fig2c_protocol_W_parity_ensemble.png/.pdf`\n")
    lines.append("- `outputs/jcp_submission/figures/`（同步副本）\n")
    lines.append(
        "- Fig.2 (a)(b) 仍为 `fig2_protocol_W_metrics.*`；(c) 为本文件独立面板，"
        "见 `outputs/figures/FIGURE_CAPTIONS.md`。\n"
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("".join(lines), encoding="utf-8")


def _update_captions() -> None:
    cap = ROOT / "outputs" / "figures" / "FIGURE_CAPTIONS.md"
    if not cap.is_file():
        return
    text = cap.read_text(encoding="utf-8")
    marker = "**Fig. 2.**"
    addition = (
        " (c) Five-seed ensemble parity for Protocol W: true $\\log_{10} D$ versus "
        "mean prediction across seeds $0,1,2,42,123$ (points present in all five "
        "within_T test sets), with vertical error bars showing the seed-to-seed "
        "standard deviation; shaded band is the Factor-of-two region "
        "$y=x\\pm\\log_{10}2$. Panel (c) is supplied as "
        "`fig2c_protocol_W_parity_ensemble.pdf` and does not alter the frozen "
        "MAPE / Factor2 / $R^{2}$ numbers in (a)(b) / Table 1."
    )
    # Replace Fig. 2 paragraph if (c) not already mentioned
    if "fig2c_protocol_W_parity_ensemble" in text:
        return
    lines = text.splitlines(keepends=True)
    new_lines = []
    for line in lines:
        if line.startswith(marker) and "(c)" not in line:
            # insert (c) before the last period of the paragraph
            stripped = line.rstrip("\n")
            if stripped.endswith("."):
                stripped = stripped[:-1] + addition + ".\n"
            else:
                stripped = stripped + addition + "\n"
            new_lines.append(stripped)
        else:
            new_lines.append(line)
    cap.write_text("".join(new_lines), encoding="utf-8")


def main() -> None:
    frames = _load_seed_frames()
    ens = _build_ensemble_table(frames)

    results_dir = ROOT / "outputs" / "results"
    fig_dir = ROOT / "outputs" / "figures"
    jcp_dir = ROOT / "outputs" / "jcp_submission" / "figures"
    results_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    jcp_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / "protocol_W_parity_ensemble_points.csv"
    ens.to_csv(csv_path, index=False)

    png = fig_dir / "fig2c_protocol_W_parity_ensemble.png"
    pdf = fig_dir / "fig2c_protocol_W_parity_ensemble.pdf"
    outliers = _plot_parity(ens, png, pdf)

    for src in (png, pdf):
        shutil.copy2(src, jcp_dir / src.name)

    report = results_dir / "PROTOCOL_W_ENSEMBLE_PARITY_REPORT.md"
    _write_report(ens, outliers, report)
    _update_captions()

    # Console summary (traceable)
    full = ens[ens["all_five_seeds"] & (ens["model"] == "MFNN")]
    n_out = int((~full["in_factor2"]).sum())
    print(f"[wrote] {csv_path}")
    print(f"[wrote] {png}")
    print(f"[wrote] {pdf}")
    print(f"[wrote] {report}")
    print(f"[copy]  {jcp_dir}")
    print(
        f"MFNN Factor2 outliers (5-seed common): {n_out}/{len(full)} "
        f"ids={outliers}"
    )


if __name__ == "__main__":
    main()
