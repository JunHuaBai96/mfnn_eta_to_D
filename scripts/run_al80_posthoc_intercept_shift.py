# -*- coding: utf-8 -*-
"""B2: post-hoc single-anchor intercept shift on Al80Cu20_tracer (ZERO retraining).

SI-only diagnostic. NOT pure LOGO success. Does NOT change Protocol W frozen numbers.

  python scripts/run_al80_posthoc_intercept_shift.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eval import _metrics  # noqa: E402

HOLDOUT = "Al80Cu20_tracer"
SEEDS = [0, 1, 2, 42, 123]
MODELS = ["LF_only", "HF_only", "MFNN"]
T_LOW = 983.0
T_HIGH = 1200.0
T_TOL = 0.51  # match float T_K


def _pred_col(model: str) -> str:
    return f"pred_{model}_log10D"


def _load_k0(seed: int) -> pd.DataFrame:
    path = ROOT / "outputs" / "al80_anchor_folds" / f"seed{seed}_k0" / "test_predictions.csv"
    if not path.is_file():
        raise FileNotFoundError(f"missing k0 preds: {path}")
    df = pd.read_csv(path)
    df = df[df["comp_group"].astype(str) == HOLDOUT].copy()
    if len(df) == 0:
        # fallback: all rows in file are holdout
        df = pd.read_csv(path)
    df = df.sort_values("T_K", kind="mergesort").reset_index(drop=True)
    return df


def _pick_anchor(df: pd.DataFrame, T_anchor: float) -> pd.Series:
    mask = np.isclose(df["T_K"].to_numpy(dtype=float), T_anchor, atol=T_TOL)
    if not mask.any():
        # nearest
        idx = int(np.argmin(np.abs(df["T_K"].to_numpy(dtype=float) - T_anchor)))
        return df.iloc[idx]
    return df.loc[mask].iloc[0]


def _heldout(df: pd.DataFrame, T_anchor: float) -> pd.DataFrame:
    mask = ~np.isclose(df["T_K"].to_numpy(dtype=float), T_anchor, atol=T_TOL)
    return df.loc[mask].reset_index(drop=True)


def _row_metrics(
    seed: int,
    model: str,
    setting: str,
    T_anchor: float,
    delta: float,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_full_k0: int,
) -> dict:
    m = _metrics(y_true, y_pred)
    return {
        "seed": seed,
        "model": model,
        "setting": setting,
        "T_anchor_K": T_anchor,
        "delta_log10": delta,
        "n_test": int(len(y_true)),
        "n_k0_full": n_full_k0,
        "MAPE_pct": m["MAPE_pct"],
        "Factor2": m["Factor2"],
        "R2": m["R2"],
        "RMSE_log": m["RMSE"],
    }


def run_b2() -> pd.DataFrame:
    rows: list[dict] = []
    detail_rows: list[dict] = []

    for seed in SEEDS:
        df0 = _load_k0(seed)
        n_full = len(df0)
        for T_anchor, tag in [(T_LOW, "lowT_983"), (T_HIGH, "highT_1200")]:
            anc = _pick_anchor(df0, T_anchor)
            T_used = float(anc["T_K"])
            held = _heldout(df0, T_used)
            y_true_h = held["y_true_log10D"].to_numpy(dtype=float)
            y_true_a = float(anc["y_true_log10D"])

            for model in MODELS:
                col = _pred_col(model)
                if col not in df0.columns:
                    continue
                pred_a = float(anc[col])
                delta = y_true_a - pred_a
                pred_h_raw = held[col].to_numpy(dtype=float)
                pred_h_shift = pred_h_raw + delta

                # (a) raw k0 on the same 9 held-out temps
                rows.append(
                    _row_metrics(
                        seed, model, f"k0_raw_heldout_{tag}", T_used, 0.0, y_true_h, pred_h_raw, n_full
                    )
                )
                # (b) post-hoc shift
                rows.append(
                    _row_metrics(
                        seed,
                        model,
                        f"k0_posthoc_shift_{tag}",
                        T_used,
                        delta,
                        y_true_h,
                        pred_h_shift,
                        n_full,
                    )
                )

                if model == "MFNN":
                    for i, r in held.iterrows():
                        detail_rows.append(
                            {
                                "seed": seed,
                                "T_anchor_K": T_used,
                                "tag": tag,
                                "sample_id": r.get("sample_id", ""),
                                "T_K": float(r["T_K"]),
                                "y_true_log10D": float(r["y_true_log10D"]),
                                "pred_k0_log10D": float(r[col]),
                                "pred_shifted_log10D": float(r[col]) + delta,
                                "delta_log10": delta,
                            }
                        )

    # (c) compare to existing k1_lowT / k1_highT from B CSV (same n_test=9)
    b_csv = ROOT / "outputs" / "results" / "AL80_tracer_anchor_sensitivity.csv"
    if b_csv.is_file():
        bdf = pd.read_csv(b_csv)
        for seed in SEEDS:
            for mode, tag in [("k1_lowT", "lowT_983"), ("k1_highT", "highT_1200")]:
                sub = bdf[(bdf["seed"] == seed) & (bdf["mode"] == mode)]
                if len(sub) == 0:
                    continue
                r = sub.iloc[0]
                for model in MODELS:
                    rows.append(
                        {
                            "seed": seed,
                            "model": model,
                            "setting": f"B_retrain_{mode}",
                            "T_anchor_K": float(str(r["anchor_T_K"]).split(";")[0])
                            if mode == "k1_lowT"
                            else float(str(r["anchor_T_K"]).split(";")[-1]),
                            "delta_log10": np.nan,
                            "n_test": int(r["n_test"]),
                            "n_k0_full": 10,
                            "MAPE_pct": float(r[f"{model}_MAPE_pct"]),
                            "Factor2": float(r[f"{model}_Factor2"]),
                            "R2": float(r[f"{model}_R2"]),
                            "RMSE_log": np.nan,
                        }
                    )

    out = pd.DataFrame(rows)
    detail = pd.DataFrame(detail_rows)
    return out, detail


def _agg(df: pd.DataFrame, model: str, setting: str) -> dict:
    sub = df[(df["model"] == model) & (df["setting"] == setting)]
    if len(sub) == 0:
        return {}
    return {
        "n_seeds": len(sub),
        "MAPE_mean": float(sub["MAPE_pct"].mean()),
        "MAPE_std": float(sub["MAPE_pct"].std(ddof=0)),
        "Fac2_mean": float(sub["Factor2"].mean()),
        "Fac2_std": float(sub["Factor2"].std(ddof=0)),
        "R2_mean": float(sub["R2"].mean()),
        "R2_std": float(sub["R2"].std(ddof=0)),
        "delta_mean": float(sub["delta_log10"].mean()) if sub["delta_log10"].notna().any() else np.nan,
        "delta_std": float(sub["delta_log10"].std(ddof=0)) if sub["delta_log10"].notna().any() else np.nan,
    }


def write_report(df: pd.DataFrame, path: Path) -> None:
    m_raw = _agg(df, "MFNN", "k0_raw_heldout_lowT_983")
    m_sh = _agg(df, "MFNN", "k0_posthoc_shift_lowT_983")
    m_k1 = _agg(df, "MFNN", "B_retrain_k1_lowT")
    m_raw_h = _agg(df, "MFNN", "k0_raw_heldout_highT_1200")
    m_sh_h = _agg(df, "MFNN", "k0_posthoc_shift_highT_1200")

    cliff = False
    if m_raw and m_sh:
        # cliff-like: Factor2 rises a lot AND MAPE drops substantially
        fac_jump = m_sh["Fac2_mean"] - m_raw["Fac2_mean"]
        mape_drop = m_raw["MAPE_mean"] - m_sh["MAPE_mean"]
        cliff = (m_sh["Fac2_mean"] >= 0.5) and (mape_drop >= 50.0)

    lines = []
    lines.append("# Al80Cu20_tracer 事后截距校准（post-hoc intercept shift / B2）\n\n")
    lines.append(
        "> **范围：仅 SI / 机制诊断。** 标题必须是「事后截距校准 / post-hoc intercept shift」。"
        "**不是**纯 LOGO 成功；**禁止**写成「LOGO 已被修好」或「100%」。"
        "零重训：只读取 `outputs/al80_anchor_folds/seed*_k0/test_predictions.csv`。"
        "未改冻结 Protocol W 数字。\n\n"
    )
    lines.append("## 方法\n\n")
    lines.append(
        "对每个 seed 的 k0（纯 LOGO）预测：在锚点温度 "
        r"$T_{\mathrm{anchor}}=983\,\mathrm{K}$（及敏感性对照 $1200\,\mathrm{K}$）上计算 "
        r"$\delta = y_{\mathrm{true}} - \hat{y}_H^{(k0)}$（$\log_{10} D$ 空间），"
        "再对**其余** $n=9$ 个温度点做零自由度平移："
        r"$\hat{y}^{\mathrm{shifted}}=\hat{y}^{(k0)}+\delta$。"
        "对照：同 9 点上的 raw k0，以及实验 B 已跑的 `k1_lowT` / `k1_highT` 重训指标。\n\n"
    )

    def fmt(a: dict) -> str:
        if not a:
            return "N/A"
        return (
            f"MAPE {a['MAPE_mean']:.2f} ± {a['MAPE_std']:.2f}% ; "
            f"Factor2 {a['Fac2_mean']:.3f} ± {a['Fac2_std']:.3f} ; "
            f"R² {a['R2_mean']:.3f} ± {a['R2_std']:.3f}"
        )

    lines.append("## MFNN 汇总（5-seed mean ± std, ddof=0；评估点 = 去掉锚点后的 9 点）\n\n")
    lines.append("| setting | MAPE% | Factor2 | R² | mean δ (log10) |\n")
    lines.append("|---------|------:|--------:|---:|---------------:|\n")
    for label, a in [
        ("k0 raw (held-out 9 @ drop 983K)", m_raw),
        ("k0 + post-hoc shift @ 983K", m_sh),
        ("B retrain k1_lowT (n=9)", m_k1),
        ("k0 raw (held-out 9 @ drop 1200K)", m_raw_h),
        ("k0 + post-hoc shift @ 1200K", m_sh_h),
    ]:
        if not a:
            continue
        dlt = f"{a['delta_mean']:.4f} ± {a['delta_std']:.4f}" if np.isfinite(a.get("delta_mean", np.nan)) else "—"
        lines.append(
            f"| {label} | {a['MAPE_mean']:.2f} ± {a['MAPE_std']:.2f} | "
            f"{a['Fac2_mean']:.3f} ± {a['Fac2_std']:.3f} | "
            f"{a['R2_mean']:.3f} ± {a['R2_std']:.3f} | {dlt} |\n"
        )

    lines.append("\n## 逐 seed（MFNN，锚点 983 K）\n\n")
    lines.append("| seed | δ | k0_raw MAPE | k0_raw Fac2 | shift MAPE | shift Fac2 | B k1_lowT MAPE | B k1_lowT Fac2 |\n")
    lines.append("|-----:|--:|------------:|------------:|-----------:|-----------:|---------------:|---------------:|\n")
    for seed in SEEDS:
        def get(setting, col):
            sub = df[(df["seed"] == seed) & (df["model"] == "MFNN") & (df["setting"] == setting)]
            if len(sub) == 0:
                return np.nan
            return float(sub.iloc[0][col])

        dlt = get("k0_posthoc_shift_lowT_983", "delta_log10")
        lines.append(
            f"| {seed} | {dlt:.4f} | "
            f"{get('k0_raw_heldout_lowT_983','MAPE_pct'):.2f} | {get('k0_raw_heldout_lowT_983','Factor2'):.3f} | "
            f"{get('k0_posthoc_shift_lowT_983','MAPE_pct'):.2f} | {get('k0_posthoc_shift_lowT_983','Factor2'):.3f} | "
            f"{get('B_retrain_k1_lowT','MAPE_pct'):.2f} | {get('B_retrain_k1_lowT','Factor2'):.3f} |\n"
        )

    lines.append("\n## 判读（诚实）\n\n")
    if cliff and m_sh and m_raw:
        lines.append(
            f"- **事后截距平移有效（机制洞见，非 LOGO 成功）**：去掉 983 K 后的 9 点上，"
            f"MAPE {m_raw['MAPE_mean']:.1f}% → {m_sh['MAPE_mean']:.1f}%；"
            f"Factor2 {m_raw['Fac2_mean']:.3f} → {m_sh['Fac2_mean']:.3f}。\n"
            "- 这表明：在当前 k0 预测上，**温度斜率大体可用**，主要误差更像 "
            r"$\log_{10} D$ 轴上的系统性截距/尺度偏移（可用 Darken 类热力学因子作**展望**，"
            "勿写「已证明 100%」）。\n"
            "- 与实验 B 的 `k1_lowT` 重训对比：若 shift ≫ retrain，说明 "
            "**单点放回未加权 MSE 会被背景稀释**；事后平移没有梯度竞争，故更易对齐。\n"
            "- **标签**：事后物理机制拆解 / **仅限 SI** / **不是**纯 LOGO 协议结果。\n"
        )
    elif m_sh and m_raw:
        mape_drop = m_raw["MAPE_mean"] - m_sh["MAPE_mean"]
        fac_jump = m_sh["Fac2_mean"] - m_raw["Fac2_mean"]
        lines.append(
            f"- **部分改善 / 未达「断崖式 Factor2 恢复」**：MAPE {m_raw['MAPE_mean']:.1f}% → "
            f"{m_sh['MAPE_mean']:.1f}%（Δ={mape_drop:.1f} pp）；"
            f"Factor2 {m_raw['Fac2_mean']:.3f} → {m_sh['Fac2_mean']:.3f}（Δ={fac_jump:.3f}）。\n"
        )
        if mape_drop > 20 and m_sh["Fac2_mean"] < 0.5:
            lines.append(
                "- 单点对数截距平移能消掉一部分均值偏移，但 Factor2 仍偏低："
                "说明除截距外，**局部有效斜率/异方差残差**仍在；"
                "inter 主导邻域可能不仅抬高截距，还通过非线性分支扭曲局部 Arrhenius 斜率。\n"
            )
        elif mape_drop <= 20:
            lines.append(
                "- 截距平移收益有限：误差不全是全局常数偏移；"
                "残差斜率畸变或点间异方差仍主导。\n"
            )
        lines.append(
            "- **标签**：事后截距校准诊断 / 仅限 SI；**禁止**包装成 LOGO 已修好。\n"
        )
    else:
        lines.append("- 缺少汇总统计，请检查 k0 预测文件。\n")

    lines.append("\n## 冻结声明\n\n")
    lines.append("- Protocol W 主文数字：**未改动**。\n")
    lines.append("- 无 Kozlov / 无补 η / 无架构修改 / 无重训。\n\n")
    lines.append("## 文件\n\n")
    lines.append("- `scripts/run_al80_posthoc_intercept_shift.py`\n")
    lines.append("- `outputs/results/AL80_posthoc_intercept_shift.csv`\n")
    lines.append("- `outputs/results/AL80_posthoc_intercept_shift_REPORT.md`\n")
    lines.append("- `outputs/figures/fig_si_al80_posthoc_shift.png`（若生成）\n")

    path.write_text("".join(lines), encoding="utf-8")
    print(f"[wrote] {path}")


def plot_fig(df: pd.DataFrame, path: Path) -> None:
    settings = [
        ("k0_raw_heldout_lowT_983", "k0 raw\n(9 pts)"),
        ("k0_posthoc_shift_lowT_983", "k0+shift\n@983K"),
        ("B_retrain_k1_lowT", "B k1_lowT\nretrain"),
    ]
    xs, mape_y, mape_e, fac_y, fac_e, labels = [], [], [], [], [], []
    for i, (s, lab) in enumerate(settings):
        a = _agg(df, "MFNN", s)
        if not a:
            continue
        xs.append(i)
        mape_y.append(a["MAPE_mean"])
        mape_e.append(a["MAPE_std"])
        fac_y.append(a["Fac2_mean"])
        fac_e.append(a["Fac2_std"])
        labels.append(lab)
    if not xs:
        return
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.8))
    colors = ["#c44e52", "#4c72b0", "#8172b2"]
    axes[0].bar(xs, mape_y, yerr=mape_e, color=colors[: len(xs)], capsize=4, alpha=0.85)
    axes[0].set_xticks(xs)
    axes[0].set_xticklabels(labels, fontsize=8)
    axes[0].set_ylabel("MFNN MAPE (%)")
    axes[0].set_title("Post-hoc intercept shift (SI)")
    axes[1].bar(xs, fac_y, yerr=fac_e, color=colors[: len(xs)], capsize=4, alpha=0.85)
    axes[1].set_xticks(xs)
    axes[1].set_xticklabels(labels, fontsize=8)
    axes[1].set_ylabel("MFNN Factor2")
    axes[1].set_ylim(0, 1.05)
    axes[1].set_title("Not pure LOGO; zero retrain")
    fig.suptitle("Al80Cu20_tracer: k0 + single-anchor δ shift @ 983 K", fontsize=11)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)
    print(f"[wrote] {path}")


def main() -> None:
    results = ROOT / "outputs" / "results"
    results.mkdir(parents=True, exist_ok=True)
    df, detail = run_b2()
    csv_path = results / "AL80_posthoc_intercept_shift.csv"
    df.to_csv(csv_path, index=False)
    print(f"[wrote] {csv_path}")
    detail_path = results / "AL80_posthoc_intercept_shift_detail_MFNN.csv"
    detail.to_csv(detail_path, index=False)
    print(f"[wrote] {detail_path}")
    write_report(df, results / "AL80_posthoc_intercept_shift_REPORT.md")
    plot_fig(df, ROOT / "outputs" / "figures" / "fig_si_al80_posthoc_shift.png")

    # quick console summary
    for s in [
        "k0_raw_heldout_lowT_983",
        "k0_posthoc_shift_lowT_983",
        "B_retrain_k1_lowT",
        "k0_posthoc_shift_highT_1200",
    ]:
        a = _agg(df, "MFNN", s)
        if a:
            print(
                f"[MFNN {s}] MAPE={a['MAPE_mean']:.2f}±{a['MAPE_std']:.2f} "
                f"Fac2={a['Fac2_mean']:.3f}±{a['Fac2_std']:.3f} "
                f"delta={a.get('delta_mean', np.nan)}"
            )
    print("[DONE] B2 post-hoc intercept shift — Protocol W untouched.")


if __name__ == "__main__":
    main()
