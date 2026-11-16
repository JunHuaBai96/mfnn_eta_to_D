#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Al80Cu20_tracer few-shot neighborhood-anchor sensitivity (SI diagnostic ONLY).

NOT pure LOGO when k>0. Does NOT change frozen Protocol W numbers.
No Kozlov / no invented eta. Same Residual MFNN + diff_type one-hot as
run_logo_alcu_difftype_feat.py.

  python scripts/run_al80_tracer_anchor_sensitivity.py --seed 42
  python scripts/run_al80_tracer_anchor_sensitivity.py --seeds 0,1,2,42,123
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from data import ensure_training_csv, load_csv  # noqa: E402
from run_logo_alcu import _run_fold, _split_remaining_hf  # noqa: E402

HOLDOUT = "Al80Cu20_tracer"
# Historical difftype-feat LOGO (seed 42): MFNN MAPE ~156.49%, Factor2=0, n=10
K0_MAPE_REF = 156.49
K0_MAPE_TOL = 40.0  # stop if |k0 - ref| exceeds this


def _anchor_masks(df_hold: pd.DataFrame, mode: str) -> tuple[pd.DataFrame, pd.DataFrame, list[float]]:
    """Return (df_anchors, df_test, anchor_T_list) for mode in {k0,k1_lowT,k1_highT,k2}."""
    ordered = df_hold.sort_values("T_K", kind="mergesort").reset_index(drop=True)
    n = len(ordered)
    if n < 3:
        raise RuntimeError(f"holdout {HOLDOUT} has n={n}, need >=3 for k=2")
    low_i, high_i = 0, n - 1
    if mode == "k0":
        return ordered.iloc[:0].copy(), ordered.copy(), []
    if mode == "k1_lowT":
        anc = ordered.iloc[[low_i]]
        te = ordered.drop(index=[low_i]).reset_index(drop=True)
        return anc.reset_index(drop=True), te, [float(anc["T_K"].iloc[0])]
    if mode == "k1_highT":
        anc = ordered.iloc[[high_i]]
        te = ordered.drop(index=[high_i]).reset_index(drop=True)
        return anc.reset_index(drop=True), te, [float(anc["T_K"].iloc[0])]
    if mode == "k2":
        anc = ordered.iloc[[low_i, high_i]]
        te = ordered.drop(index=[low_i, high_i]).reset_index(drop=True)
        return (
            anc.reset_index(drop=True),
            te,
            [float(anc["T_K"].iloc[0]), float(anc["T_K"].iloc[1])],
        )
    raise ValueError(f"unknown mode {mode}")


def _k_from_mode(mode: str) -> int:
    if mode == "k0":
        return 0
    if mode.startswith("k1"):
        return 1
    if mode == "k2":
        return 2
    raise ValueError(mode)


def run_one(
    df_lf: pd.DataFrame,
    df_hf: pd.DataFrame,
    df_hold: pd.DataFrame,
    mode: str,
    seed: int,
    folds_root: Path,
) -> dict:
    k = _k_from_mode(mode)
    df_anc, df_te, t_list = _anchor_masks(df_hold, mode)
    # remaining HF: everything except full holdout group, then add anchors back
    df_remain = df_hf[df_hf["comp_group"].astype(str) != HOLDOUT].reset_index(drop=True)
    if len(df_anc):
        df_remain = pd.concat([df_remain, df_anc], ignore_index=True)
    df_tr, df_va = _split_remaining_hf(df_remain, seed=seed)

    fold_dir = folds_root / f"seed{seed}_{mode}"
    print(
        f"\n=== seed={seed} mode={mode} k={k} "
        f"n_anchor={len(df_anc)} n_test={len(df_te)} "
        f"anchor_T={t_list} HF_tr/va={len(df_tr)}/{len(df_va)} ==="
    )
    summary = _run_fold(
        df_lf, df_tr, df_va, df_te, seed, fold_dir, include_difftype_onehot=True
    )
    all_rows = summary[summary["system"].astype(str) == "ALL"]
    out = {
        "seed": seed,
        "mode": mode,
        "k": k,
        "n_anchor": len(df_anc),
        "n_test": len(df_te),
        "anchor_T_K": ";".join(f"{t:.1f}" for t in t_list) if t_list else "",
    }
    for model in ["LF_only", "HF_only", "MFNN"]:
        sub = all_rows[all_rows["model"] == model]
        if len(sub) == 0:
            out[f"{model}_MAPE_pct"] = np.nan
            out[f"{model}_Factor2"] = np.nan
            out[f"{model}_R2"] = np.nan
            out[f"{model}_n"] = 0
        else:
            r = sub.iloc[0]
            out[f"{model}_MAPE_pct"] = float(r["MAPE_pct"])
            out[f"{model}_Factor2"] = float(r["Factor2"])
            out[f"{model}_R2"] = float(r["R2"])
            out[f"{model}_n"] = int(r["n"])
            print(
                f"  {model}: MAPE={out[f'{model}_MAPE_pct']:.2f}% "
                f"Fac2={out[f'{model}_Factor2']:.3f} "
                f"R2={out[f'{model}_R2']:.3f} n={out[f'{model}_n']}"
            )
    return out


def write_report(df: pd.DataFrame, path: Path, seeds: list[int], stopped: str | None) -> None:
    mfnn = df.copy()
    lines: list[str] = []
    lines.append("# Al80Cu20_tracer 邻域锚点敏感度（few-shot anchor sensitivity / 反事实诊断）\n\n")
    lines.append(
        "> **范围：仅 SI / Discussion。** 这不是新的主结论实验。"
        "k>0 时训练集含 holdout 组内端点 → **不再是纯 LOGO**；"
        "**禁止**写成「LOGO 已被修好」。未改冻结 Protocol W 数字；无 Kozlov / 无合成 η；"
        "架构仍为 Residual MFNN + diff_type one-hot（与 `run_logo_alcu_difftype_feat.py` 一致）。\n\n"
    )
    lines.append(f"- holdout: `{HOLDOUT}`（Zhang 网格 tracer，全组 n≈10）\n")
    lines.append(f"- seeds: {seeds}\n")
    lines.append(
        "- 模式: `k0`（纯 LOGO） / `k1_lowT` / `k1_highT` / `k2`（两端点回训）\n"
    )
    lines.append(
        f"- 历史对照（difftype-feat LOGO seed42 MFNN）: "
        f"MAPE≈{K0_MAPE_REF}%, Factor2=0, n=10\n\n"
    )
    if stopped:
        lines.append(f"## 中止说明\n\n{stopped}\n\n")

    lines.append("## 成功判据（SI 叙事）\n\n")
    lines.append(
        "若 k=1 或 k=2 后 MFNN MAPE 相对 k=0 **断崖下降**且 Factor2 明显回升，"
        "支持「邻域 tracer HF 稀疏 / 缺局部尺度锚点」叙事；"
        "**不**等于宣称 LOGO 协议已通过。\n\n"
    )

    # pivot table: mode x metrics for MFNN, mean over seeds
    lines.append("## MFNN 汇总（跨 seed mean ± std, ddof=0）\n\n")
    lines.append(
        "| mode | k | n_test | MAPE% | Factor2 | R² | n_seeds |\n"
        "|------|--:|-------:|------:|--------:|---:|--------:|\n"
    )
    cliff = False
    k0_mape_mean = None
    for mode in ["k0", "k1_lowT", "k1_highT", "k2"]:
        sub = mfnn[mfnn["mode"] == mode]
        if len(sub) == 0:
            continue
        mape = pd.to_numeric(sub["MFNN_MAPE_pct"], errors="coerce")
        fac = pd.to_numeric(sub["MFNN_Factor2"], errors="coerce")
        r2 = pd.to_numeric(sub["MFNN_R2"], errors="coerce")
        n_te = int(sub["n_test"].iloc[0])
        k = int(sub["k"].iloc[0])
        lines.append(
            f"| `{mode}` | {k} | {n_te} | "
            f"{mape.mean():.2f} ± {mape.std(ddof=0):.2f} | "
            f"{fac.mean():.3f} ± {fac.std(ddof=0):.3f} | "
            f"{r2.mean():.3f} ± {r2.std(ddof=0):.3f} | {len(sub)} |\n"
        )
        if mode == "k0":
            k0_mape_mean = float(mape.mean())

    lines.append("\n## 逐 seed 明细（MFNN）\n\n")
    lines.append(
        "| seed | mode | k | n_test | anchor_T_K | MAPE% | Factor2 | R² |\n"
        "|-----:|------|--:|-------:|------------|------:|--------:|---:|\n"
    )
    for _, r in mfnn.sort_values(["seed", "k", "mode"]).iterrows():
        lines.append(
            f"| {int(r['seed'])} | `{r['mode']}` | {int(r['k'])} | {int(r['n_test'])} | "
            f"{r['anchor_T_K']} | {float(r['MFNN_MAPE_pct']):.2f} | "
            f"{float(r['MFNN_Factor2']):.3f} | {float(r['MFNN_R2']):.3f} |\n"
        )

    # cliff detection
    lines.append("\n## 断崖下降判定\n\n")
    if k0_mape_mean is not None and not stopped:
        for mode in ["k1_lowT", "k1_highT", "k2"]:
            sub = mfnn[mfnn["mode"] == mode]
            if len(sub) == 0:
                continue
            m = float(pd.to_numeric(sub["MFNN_MAPE_pct"], errors="coerce").mean())
            f = float(pd.to_numeric(sub["MFNN_Factor2"], errors="coerce").mean())
            drop = k0_mape_mean - m
            ratio = m / k0_mape_mean if k0_mape_mean > 0 else np.nan
            hit = (drop >= 50.0) or (ratio <= 0.5) or (f >= 0.5 and k0_mape_mean > 80)
            cliff = cliff or hit
            lines.append(
                f"- `{mode}`: MAPE {k0_mape_mean:.1f}% → {m:.1f}% "
                f"(Δ={drop:.1f} pp, ratio={ratio:.2f}); Factor2→{f:.3f}; "
                f"{'**疑似断崖**' if hit else '未达断崖判据'}\n"
            )
        if cliff:
            lines.append(
                "\n**结论（SI）：** 注入 1–2 个同组 tracer 温度端点后误差明显下降，"
                "支持「诚实 η 约束下邻域 tracer HF 稀疏」叙事；"
                "k>0 **不是**纯 LOGO，不可改写主文 LOGO 失败表。\n"
            )
        else:
            lines.append(
                "\n**诚实失败表述（SI）：** 即便提供极少量局部温度锚点，"
                "高密度 Arrhenius 网格与多源异构互扩散背景之间的权重竞争仍可能限制"
                "单头残差网络的局部校准；未来可考虑显式 Darken Φ 等物理特征，"
                "**而非**改 PINN/双头架构刷分。本实验不改冻结 Protocol W 数字。\n"
            )
    else:
        lines.append("未完成完整对比或已中止，见上文。\n")

    lines.append("\n## 文件\n\n")
    lines.append("- `outputs/results/AL80_tracer_anchor_sensitivity.csv`\n")
    lines.append("- `outputs/results/AL80_tracer_anchor_sensitivity_REPORT.md`\n")
    lines.append("- `outputs/figures/fig_si_al80_anchor_k.png`（若生成）\n")
    lines.append("- folds: `outputs/al80_anchor_folds/`\n")

    path.write_text("".join(lines), encoding="utf-8")
    print(f"[wrote] {path}")


def plot_si(df: pd.DataFrame, path: Path) -> None:
    mfnn = df.copy()
    modes = ["k0", "k1_lowT", "k1_highT", "k2"]
    xs, ys, yerr, labels = [], [], [], []
    for i, mode in enumerate(modes):
        sub = mfnn[mfnn["mode"] == mode]
        if len(sub) == 0:
            continue
        mape = pd.to_numeric(sub["MFNN_MAPE_pct"], errors="coerce")
        xs.append(i)
        ys.append(float(mape.mean()))
        yerr.append(float(mape.std(ddof=0)) if len(mape) > 1 else 0.0)
        labels.append(mode)
    if not xs:
        return
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.bar(xs, ys, yerr=yerr, color=["#c44e52", "#4c72b0", "#55a868", "#8172b2"][: len(xs)],
           capsize=4, alpha=0.85)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_ylabel("MFNN MAPE (%)")
    ax.set_title("SI: Al80Cu20_tracer few-shot anchor sensitivity\n(not pure LOGO when k>0)")
    ax.axhline(K0_MAPE_REF, color="gray", ls="--", lw=1, label=f"hist k0 ref {K0_MAPE_REF}%")
    ax.legend(fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)
    print(f"[wrote] {path}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Al80Cu20_tracer few-shot anchor sensitivity (SI only)"
    )
    ap.add_argument("--seed", type=int, default=None, help="Single seed (default 42 if no --seeds)")
    ap.add_argument(
        "--seeds",
        type=str,
        default=None,
        help="Comma-separated seeds, e.g. 0,1,2,42,123",
    )
    ap.add_argument(
        "--modes",
        type=str,
        default="k0,k1_lowT,k1_highT,k2",
        help="Comma-separated modes",
    )
    args = ap.parse_args()
    if args.seeds:
        seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    elif args.seed is not None:
        seeds = [args.seed]
    else:
        seeds = [42]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]

    out = ROOT / "outputs"
    results = out / "results"
    results.mkdir(parents=True, exist_ok=True)
    folds_root = out / "al80_anchor_folds"
    folds_root.mkdir(exist_ok=True)

    csv_path = ensure_training_csv(str(ROOT / "data"))
    print(f"[Data] {csv_path}")
    df = load_csv(csv_path)
    df_lf = df[df["fidelity"].astype(str).str.upper() == "LF"].reset_index(drop=True)
    df_hf = df[df["fidelity"].astype(str).str.upper() == "HF"].reset_index(drop=True)
    df_hold = df_hf[df_hf["comp_group"].astype(str) == HOLDOUT].reset_index(drop=True)
    print(f"[Holdout] {HOLDOUT} n={len(df_hold)} T=[{df_hold['T_K'].min():.0f},{df_hold['T_K'].max():.0f}]")
    if len(df_hold) != 10:
        print(f"[WARN] expected n=10, got {len(df_hold)}")

    rows: list[dict] = []
    stopped: str | None = None

    for seed in seeds:
        for mode in modes:
            row = run_one(df_lf, df_hf, df_hold, mode, seed, folds_root)
            rows.append(row)
            # After first seed's k0, check alignment with historical
            if seed == seeds[0] and mode == "k0":
                mape0 = float(row["MFNN_MAPE_pct"])
                fac0 = float(row["MFNN_Factor2"])
                n0 = int(row["MFNN_n"])
                print(
                    f"[k0 check] MFNN MAPE={mape0:.2f}% Fac2={fac0:.3f} n={n0} "
                    f"(hist ~{K0_MAPE_REF}%, 0, 10)"
                )
                if abs(mape0 - K0_MAPE_REF) > K0_MAPE_TOL or n0 != 10:
                    stopped = (
                        f"k=0 MFNN MAPE={mape0:.2f}% (n={n0}) 与历史 difftype-feat "
                        f"~{K0_MAPE_REF}% / n=10 偏差过大（容差 ±{K0_MAPE_TOL} pp）。"
                        "已停止继续 k>0；请对照 "
                        "`outputs/results/LOGO_AlCu_difftype_feat_REPORT.md` 与 "
                        "`AL80Cu20_FAIL_DIAGNOSIS.md`。"
                    )
                    print(f"[STOP] {stopped}")
                    break
        if stopped:
            break

    df_out = pd.DataFrame(rows)
    csv_out = results / "AL80_tracer_anchor_sensitivity.csv"
    df_out.to_csv(csv_out, index=False)
    print(f"[wrote] {csv_out}")

    report = results / "AL80_tracer_anchor_sensitivity_REPORT.md"
    write_report(df_out, report, seeds if not stopped else [seeds[0]], stopped)

    if not stopped and len(df_out):
        plot_si(df_out, out / "figures" / "fig_si_al80_anchor_k.png")

    print("\n[DONE] SI diagnostic only — frozen Protocol W metrics untouched.")


if __name__ == "__main__":
    main()
