#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fixed Al-Cu leave-one-comp_group-out (LOGO) for protocol G.

Deterministic folds: each Al-Cu HF comp_group is held out once as test.
--seed only controls optimizer / val row sample, not which group is held out.

  python scripts/run_logo_alcu.py
  python scripts/run_logo_alcu.py --seed 42

Does NOT modify data; does NOT Kozlov-fill HF eta (load_csv drops missing eta).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data import (  # noqa: E402
    NUM_FEATURES,
    NUM_PHYS,
    FeatureStandardizer,
    build_feature_matrix,
    ensure_training_csv,
    load_csv,
)
from eval import evaluate_by_system  # noqa: E402
from train import (  # noqa: E402
    set_seed,
    train_residual_mfnn,
    train_single_fidelity_baseline,
)


def _split_remaining_hf(
    df_remain: pd.DataFrame,
    seed: int,
    val_group_frac: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """From non-holdout HF: hold ~val_group_frac of remaining groups as val (seed-controlled)."""
    groups = sorted(df_remain["comp_group"].astype(str).unique().tolist())
    if len(groups) <= 1:
        # row-level val fallback
        if len(df_remain) < 3:
            return df_remain.reset_index(drop=True), df_remain.iloc[:0].copy()
        rng = np.random.default_rng(seed)
        idx = np.arange(len(df_remain))
        rng.shuffle(idx)
        n_va = max(1, len(df_remain) // 5)
        return (
            df_remain.iloc[idx[n_va:]].reset_index(drop=True),
            df_remain.iloc[idx[:n_va]].reset_index(drop=True),
        )
    rng = np.random.default_rng(seed)
    order = groups.copy()
    rng.shuffle(order)
    n_va = max(1, int(round(len(order) * val_group_frac))) if len(order) >= 3 else 0
    if n_va >= len(order):
        n_va = max(0, len(order) - 1)
    g_va = set(order[:n_va])
    g_tr = set(order[n_va:])
    tr = df_remain[df_remain["comp_group"].astype(str).isin(g_tr)].reset_index(drop=True)
    va = df_remain[df_remain["comp_group"].astype(str).isin(g_va)].reset_index(drop=True)
    if len(tr) == 0:
        # ensure non-empty train
        tr, va = va, tr
    return tr, va


def _run_fold(
    df_lf: pd.DataFrame,
    df_tr_hf: pd.DataFrame,
    df_val_hf: pd.DataFrame,
    df_te_hf: pd.DataFrame,
    seed: int,
    fold_dir: Path,
    include_difftype_onehot: bool = True,
) -> pd.DataFrame:
    """Train LF/HF/MFNN like train._run_one_protocol; return ALL-row metrics per model."""
    set_seed(seed)
    fold_dir.mkdir(parents=True, exist_ok=True)
    n_feat = NUM_FEATURES if include_difftype_onehot else NUM_PHYS
    oh = include_difftype_onehot

    val_groups = set(df_val_hf["comp_group"].astype(str).unique())
    df_tr_lf = df_lf.reset_index(drop=True)  # all available LF
    df_val_lf = df_lf[df_lf["comp_group"].astype(str).isin(val_groups)].reset_index(drop=True)
    if len(df_val_lf) == 0 and len(df_lf) > 0:
        df_val_lf = df_lf.sample(n=min(5, len(df_lf)), random_state=seed).reset_index(drop=True)

    X_tr_lf_raw, y_tr_lf, _ = build_feature_matrix(df_tr_lf, include_difftype_onehot=oh)
    X_val_lf_raw, y_val_lf, _ = build_feature_matrix(df_val_lf, include_difftype_onehot=oh)
    X_tr_hf_raw, y_tr_hf, phys_tr_hf = build_feature_matrix(df_tr_hf, include_difftype_onehot=oh)
    X_val_hf_raw, y_val_hf, _ = build_feature_matrix(df_val_hf, include_difftype_onehot=oh)
    X_te_hf_raw, y_te_hf, _ = build_feature_matrix(df_te_hf, include_difftype_onehot=oh)

    stack = (
        np.vstack([X_tr_lf_raw, X_tr_hf_raw])
        if len(X_tr_lf_raw) and len(X_tr_hf_raw)
        else (X_tr_hf_raw if len(X_tr_hf_raw) else X_tr_lf_raw)
    )
    scaler = FeatureStandardizer(num_continuous=n_feat, num_phys=min(NUM_PHYS, n_feat)).fit(stack)
    t_X_tr_lf = torch.tensor(scaler.transform(X_tr_lf_raw), dtype=torch.float32)
    t_y_tr_lf = torch.tensor(y_tr_lf, dtype=torch.float32)
    t_X_tr_hf = torch.tensor(scaler.transform(X_tr_hf_raw), dtype=torch.float32)
    t_y_tr_hf = torch.tensor(y_tr_hf, dtype=torch.float32)
    t_phys_tr_hf = torch.tensor(phys_tr_hf, dtype=torch.float32)
    t_X_val_lf = torch.tensor(scaler.transform(X_val_lf_raw), dtype=torch.float32)
    t_y_val_lf = torch.tensor(y_val_lf, dtype=torch.float32)
    t_X_val_hf = torch.tensor(scaler.transform(X_val_hf_raw), dtype=torch.float32)
    t_y_val_hf = torch.tensor(y_val_hf, dtype=torch.float32)
    t_X_te_hf = torch.tensor(scaler.transform(X_te_hf_raw), dtype=torch.float32)

    skip_lf = len(X_tr_lf_raw) == 0
    if skip_lf:
        model_lf = None
        print("[Train] LF_only skipped (no LF in pool)")
    else:
        model_lf = train_single_fidelity_baseline(t_X_tr_lf, t_y_tr_lf, t_X_val_lf, t_y_val_lf)
    model_hf = train_single_fidelity_baseline(
        t_X_tr_hf, t_y_tr_hf, t_X_val_hf, t_y_val_hf, weight_decay=5e-3
    )
    model_mfnn = train_residual_mfnn(
        t_X_tr_lf, t_y_tr_lf, t_X_tr_hf, t_y_tr_hf, t_phys_tr_hf, t_X_val_hf, t_y_val_hf
    )

    if model_lf is not None:
        model_lf.eval()
    model_hf.eval()
    model_mfnn.eval()
    with torch.no_grad():
        preds = {
            "HF_only": model_hf(t_X_te_hf).numpy(),
            "MFNN": model_mfnn.forward_hf(t_X_te_hf).numpy(),
        }
        if model_lf is not None:
            preds["LF_only"] = model_lf(t_X_te_hf).numpy()
        else:
            preds["LF_only"] = np.full(len(y_te_hf), np.nan, dtype=np.float64)

    summary = evaluate_by_system(
        df_te_hf,
        y_te_hf,
        preds,
        str(fold_dir / "metrics_by_system.csv"),
        str(fold_dir / "test_predictions.csv"),
    )
    return summary


def _mean_std(s: pd.Series) -> str:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if len(x) == 0:
        return "n/a"
    return f"{x.mean():.4g} ± {x.std(ddof=0):.4g}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Al-Cu fixed LOGO (leave-one-comp_group-out)")
    ap.add_argument("--seed", type=int, default=42, help="Optimizer / val split seed only")
    ap.add_argument("--system", type=str, default="Al-Cu", help="Primary LOGO system")
    args = ap.parse_args()
    seed = args.seed
    target_system = args.system

    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    folds_root = out / "logo_alcu_folds"
    folds_root.mkdir(exist_ok=True)

    csv_path = ensure_training_csv(str(ROOT / "data"))
    print(f"[Data] {csv_path} (LOGO seed={seed} for optimizer only)")
    df = load_csv(csv_path)
    df_lf = df[df["fidelity"].astype(str).str.upper() == "LF"].reset_index(drop=True)
    df_hf = df[df["fidelity"].astype(str).str.upper() == "HF"].reset_index(drop=True)

    hf_sys = df_hf[df_hf["system"].astype(str) == target_system].reset_index(drop=True)
    groups = sorted(hf_sys["comp_group"].astype(str).unique().tolist())
    print(f"[LOGO] {target_system} HF comp_groups ({len(groups)}): {groups}")

    rows = []
    fold_meta = []
    for g in groups:
        print("\n" + "=" * 60)
        print(f"HOLDOUT {g}")
        print("=" * 60)
        df_te = hf_sys[hf_sys["comp_group"].astype(str) == g].reset_index(drop=True)
        # remaining HF: all systems except this holdout group
        df_remain = df_hf[df_hf["comp_group"].astype(str) != g].reset_index(drop=True)
        df_tr, df_va = _split_remaining_hf(df_remain, seed=seed)
        print(
            f"[Split] holdout={g} n_test={len(df_te)}; "
            f"HF train/val={len(df_tr)}/{len(df_va)}; LF={len(df_lf)}"
        )
        fold_dir = folds_root / g.replace("/", "_").replace("\\", "_")
        summary = _run_fold(df_lf, df_tr, df_va, df_te, seed, fold_dir)
        fold_meta.append({"holdout_group": g, "n_test": len(df_te)})
        all_rows = summary[summary["system"].astype(str) == "ALL"]
        for _, r in all_rows.iterrows():
            rows.append({
                "holdout_group": g,
                "model": r["model"],
                "MAPE_pct": r["MAPE_pct"],
                "Factor2": r["Factor2"],
                "R2": r["R2"],
                "n": int(r["n"]),
            })
        print(all_rows[["model", "MAPE_pct", "Factor2", "R2", "n"]].to_string(index=False))

    summary_df = pd.DataFrame(rows)
    summary_path = out / "LOGO_AlCu_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    # --- Markdown report ---
    md: list[str] = []
    md.append("# Al–Cu 固定 LOGO（leave-one-comp_group-out）\n\n")
    md.append(
        "这是协议 G 的**确定性**版本：每个 Al–Cu HF `comp_group` 整组留出作 test，"
        "其余 HF + 全部可用 LF 训练。**折的划分不随机**；"
        f"`--seed {seed}` 仅控制优化器初始化与剩余组上的 val 抽样。\n\n"
    )
    md.append(
        "> **范围：** Al–Cu **体系内成分外推**（不同 `comp_group` / 成分）。"
        "不是跨合金体系（Al–Mg–Si / Al–Ce–Ni）外推，也**不是**随机 seed 的 G≈20% 论文结论。\n\n"
    )
    md.append("缺 `eta_Pas` 行由 `load_csv` drop；**未**用 Kozlov 填 HF η。\n\n")

    md.append("## 折列表\n\n")
    md.append("| holdout_group | n_test |\n|---------------|--------|\n")
    for m in fold_meta:
        md.append(f"| {m['holdout_group']} | {m['n_test']} |\n")
    md.append(f"\n共 **{len(fold_meta)}** 折。\n\n")

    md.append("## ALL 指标 mean ± std（跨折，ddof=0）\n\n")
    for model in ["LF_only", "HF_only", "MFNN"]:
        sub = summary_df[summary_df["model"] == model]
        md.append(f"### {model}\n\n")
        md.append(f"- **MAPE%**: {_mean_std(sub['MAPE_pct'])}\n")
        md.append(f"- **Factor2**: {_mean_std(sub['Factor2'])}\n")
        md.append(f"- **R²**: {_mean_std(sub['R2'])}\n")
        md.append(f"- **n**: {_mean_std(sub['n'])}\n\n")

    mfnn = summary_df[summary_df["model"] == "MFNN"].copy()
    mfnn["MAPE_pct"] = pd.to_numeric(mfnn["MAPE_pct"], errors="coerce")
    best = mfnn.loc[mfnn["MAPE_pct"].idxmin()]
    worst = mfnn.loc[mfnn["MAPE_pct"].idxmax()]
    md.append("## MFNN 最好 / 最差折\n\n")
    md.append(
        f"- **最好**: `{best['holdout_group']}` — MAPE={best['MAPE_pct']:.2f}%, "
        f"Factor2={best['Factor2']:.3f}, n={int(best['n'])}\n"
    )
    md.append(
        f"- **最差**: `{worst['holdout_group']}` — MAPE={worst['MAPE_pct']:.2f}%, "
        f"Factor2={worst['Factor2']:.3f}, n={int(worst['n'])}\n\n"
    )

    md.append("## 逐折明细（ALL）\n\n")
    md.append("```\n")
    md.append(summary_df.sort_values(["holdout_group", "model"]).to_string(index=False))
    md.append("\n```\n\n")

    # Optional: other systems
    md.append("## 非 Al–Cu 体系（可选 LOGO）\n\n")
    other = df_hf[df_hf["system"].astype(str) != target_system]
    for sys, sub in other.groupby(other["system"].astype(str)):
        n_g = sub["comp_group"].astype(str).nunique()
        if n_g >= 2:
            md.append(f"- **{sys}**: {n_g} 个 HF `comp_group` — 可另跑 LOGO（本脚本未默认执行）。\n")
        else:
            gname = sub["comp_group"].astype(str).iloc[0]
            md.append(
                f"- **{sys}**: 仅 1 个 HF 组 (`{gname}`, n={len(sub)}) — "
                f"**不足以 LOGO**（leave-one-group-out 需要 ≥2 组）。\n"
            )
    md.append("\n")

    md.append("## 文件\n\n")
    md.append("- `outputs/LOGO_AlCu_summary.csv`\n")
    md.append("- `outputs/LOGO_AlCu_REPORT.md`\n")
    md.append("- per-fold: `outputs/logo_alcu_folds/<group>/`\n")

    report_path = out / "LOGO_AlCu_REPORT.md"
    report_path.write_text("".join(md), encoding="utf-8")

    print(f"\n[wrote] {summary_path}")
    print(f"[wrote] {report_path}")
    print(f"MFNN MAPE%: {_mean_std(mfnn['MAPE_pct'])}")
    print(
        f"MFNN worst fold: {worst['holdout_group']} "
        f"MAPE={worst['MAPE_pct']:.2f}% Factor2={worst['Factor2']:.3f}"
    )


if __name__ == "__main__":
    main()
