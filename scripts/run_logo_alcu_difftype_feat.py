#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Al-Cu LOGO with diff_type one-hot features (after comp_group split).

  python scripts/run_logo_alcu_difftype_feat.py --seed 42

Compares to outputs/LOGO_AlCu_by_difftype_summary.csv (split only, no one-hot).
No Kozlov HF eta; does not modify D/eta values.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from data import (  # noqa: E402
    DIFFTYPE_ONEHOT_ORDER,
    NUM_DIFFTYPE,
    NUM_FEATURES,
    NUM_PHYS,
    ensure_training_csv,
    load_csv,
    normalize_diff_type_label,
)
from eval import _metrics  # noqa: E402
from run_logo_alcu import _mean_std, _run_fold, _split_remaining_hf  # noqa: E402
from train import main as train_main, set_seed  # noqa: E402


def run_logo(seed: int, out: Path) -> tuple[pd.DataFrame, list]:
    csv_path = ensure_training_csv(str(ROOT / "data"))
    print(f"[Data] {csv_path} (difftype-feat LOGO seed={seed})")
    print(
        f"[Feat] dim={NUM_FEATURES} = {NUM_PHYS} phys + {NUM_DIFFTYPE} one-hot "
        f"{list(DIFFTYPE_ONEHOT_ORDER)} (self/unknown→other); one-hot not z-scored"
    )
    df = load_csv(csv_path)
    df_lf = df[df["fidelity"].astype(str).str.upper() == "LF"].reset_index(drop=True)
    df_hf = df[df["fidelity"].astype(str).str.upper() == "HF"].reset_index(drop=True)
    hf_sys = df_hf[df_hf["system"].astype(str) == "Al-Cu"].reset_index(drop=True)
    groups = sorted(hf_sys["comp_group"].astype(str).unique().tolist())
    print(f"[LOGO] Al-Cu HF groups ({len(groups)}): {groups}")

    folds_root = out / "logo_alcu_difftype_feat_folds"
    folds_root.mkdir(exist_ok=True)
    rows, fold_meta = [], []
    for g in groups:
        print("\n" + "=" * 60)
        print(f"HOLDOUT {g}")
        print("=" * 60)
        df_te = hf_sys[hf_sys["comp_group"].astype(str) == g].reset_index(drop=True)
        df_remain = df_hf[df_hf["comp_group"].astype(str) != g].reset_index(drop=True)
        df_tr, df_va = _split_remaining_hf(df_remain, seed=seed)
        print(
            f"[Split] n_test={len(df_te)}; HF train/val={len(df_tr)}/{len(df_va)}; LF={len(df_lf)}"
        )
        fold_dir = folds_root / g.replace("/", "_").replace("\\", "_")
        summary = _run_fold(df_lf, df_tr, df_va, df_te, seed, fold_dir)
        fold_meta.append({"holdout_group": g, "n_test": len(df_te)})
        for _, r in summary[summary["system"].astype(str) == "ALL"].iterrows():
            rows.append({
                "holdout_group": g,
                "model": r["model"],
                "MAPE_pct": r["MAPE_pct"],
                "Factor2": r["Factor2"],
                "R2": r["R2"],
                "n": int(r["n"]),
            })
            print(
                f"  {r['model']}: MAPE={float(r['MAPE_pct']):.2f}% "
                f"Fac2={float(r['Factor2']):.3f} n={int(r['n'])}"
            )
    return pd.DataFrame(rows), fold_meta


def optional_within_T(seed: int, out: Path) -> pd.DataFrame | None:
    print("\n[Optional] within_T with same features...")
    train_main(
        seed=seed,
        make_plots=False,
        out_subdir="within_T_difftype_feat",
        eval_mode="within_T",
    )
    pred = out / "within_T_difftype_feat" / "within_T" / "test_predictions.csv"
    if not pred.is_file():
        pred = out / "within_T_difftype_feat" / "test_predictions_within_T.csv"
    if not pred.is_file():
        return None
    detail = pd.read_csv(pred)
    rows = []
    for dt, sub in detail.groupby(
        detail["diff_type"].astype(str).map(normalize_diff_type_label)
    ):
        m = _metrics(sub["y_true_log10D"].to_numpy(), sub["pred_MFNN_log10D"].to_numpy())
        rows.append({
            "diff_type_norm": dt,
            "model": "MFNN",
            "MAPE_pct": m["MAPE_pct"],
            "Factor2": m["Factor2"],
            "R2": m["R2"],
            "n": len(sub),
        })
    m = _metrics(
        detail["y_true_log10D"].to_numpy(),
        detail["pred_MFNN_log10D"].to_numpy(),
    )
    rows.append({
        "diff_type_norm": "ALL",
        "model": "MFNN",
        "MAPE_pct": m["MAPE_pct"],
        "Factor2": m["Factor2"],
        "R2": m["R2"],
        "n": len(detail),
    })
    wdf = pd.DataFrame(rows)
    wdf.to_csv(out / "within_T_difftype_feat_by_type.csv", index=False)
    return wdf


def write_report(
    summary_df: pd.DataFrame,
    fold_meta: list,
    prev_path: Path,
    wdf: pd.DataFrame | None,
    out: Path,
) -> None:
    prev = pd.read_csv(prev_path) if prev_path.is_file() else None
    new_m = summary_df[summary_df.model == "MFNN"].copy()
    new_m["MAPE_pct"] = pd.to_numeric(new_m["MAPE_pct"], errors="coerce")

    md: list[str] = []
    md.append("# Al–Cu LOGO + diff_type one-hot 特征\n\n")
    md.append(
        f"在已拆组（`Al80Cu20_tracer` / `_inter` 等）基础上，特征由 **{NUM_PHYS}→{NUM_FEATURES}** 维："
        f"物理/成分 {NUM_PHYS} 维 z-score + one-hot `{list(DIFFTYPE_ONEHOT_ORDER)}` "
        f"（`interdiffusivity`→inter；`self`/未知→**other**）。"
        "网络仍为 Residual MFNN，仅 `in_dim` 随特征变。`--seed 42` 仅控优化器。"
        "缺 η drop；未改 D/η；无 Kozlov 填 HF η。\n\n"
    )
    md.append("> Al–Cu **体系内**成分外推；对照「仅拆组、无 one-hot」见 `LOGO_AlCu_by_difftype_*`。\n\n")

    md.append("## 特征维数\n\n")
    md.append("| 块 | 维数 | 说明 |\n|---|---:|---|\n")
    md.append(f"| 物理/成分 | {NUM_PHYS} | T, 1000/T, η, log10η, 7 comps, r_diff；**z-score** |\n")
    md.append(
        f"| diff_type one-hot | {NUM_DIFFTYPE} | {', '.join(DIFFTYPE_ONEHOT_ORDER)}；**不 z-score** |\n"
    )
    md.append(f"| **合计** | **{NUM_FEATURES}** | 旧版无 one-hot 时为 12 |\n\n")

    md.append("## 折列表\n\n| holdout_group | n_test |\n|---|---:|\n")
    for m in fold_meta:
        md.append(f"| {m['holdout_group']} | {m['n_test']} |\n")
    md.append(f"\n共 **{len(fold_meta)}** 折。\n\n")

    md.append("## 新旧对比（重点 Al80）\n\n")
    md.append("| holdout | 仅拆组 MFNN MAPE / Fac2 / n | +one-hot MFNN MAPE / Fac2 / n |\n|---|---|---|\n")
    for g in ["Al80Cu20_tracer", "Al80Cu20_inter"]:
        new_row = summary_df[(summary_df.holdout_group == g) & (summary_df.model == "MFNN")]
        old_row = (
            prev[(prev.holdout_group == g) & (prev.model == "MFNN")]
            if prev is not None
            else pd.DataFrame()
        )
        if len(old_row):
            o = old_row.iloc[0]
            old_s = f"{float(o.MAPE_pct):.2f}% / {float(o.Factor2):.3f} / {int(o.n)}"
        else:
            old_s = "n/a"
        if len(new_row):
            n = new_row.iloc[0]
            new_s = f"{float(n.MAPE_pct):.2f}% / {float(n.Factor2):.3f} / {int(n.n)}"
        else:
            new_s = "n/a"
        md.append(f"| `{g}` | {old_s} | {new_s} |\n")
    md.append("\n")

    if prev is not None:
        old_m = prev[prev.model == "MFNN"].copy()
        old_m["MAPE_pct"] = pd.to_numeric(old_m["MAPE_pct"], errors="coerce")
        md.append("### 全体 MFNN mean±std\n\n")
        md.append(f"- **仅拆组（无 one-hot）**: {_mean_std(old_m['MAPE_pct'])}\n")
        md.append(f"- **拆组 + one-hot**: {_mean_std(new_m['MAPE_pct'])}\n\n")

        # tracer improvement narrative
        def _mape(df, g):
            s = df[(df.holdout_group == g) & (df.model == "MFNN")]
            return float(s.MAPE_pct.iloc[0]) if len(s) else float("nan")

        t_old, t_new = _mape(prev, "Al80Cu20_tracer"), _mape(summary_df, "Al80Cu20_tracer")
        i_old, i_new = _mape(prev, "Al80Cu20_inter"), _mape(summary_df, "Al80Cu20_inter")
        md.append("### 是否缓解 inter→tracer？\n\n")
        if t_new < t_old * 0.85:
            md.append(
                f"是：`Al80Cu20_tracer` MAPE {t_old:.1f}% → **{t_new:.1f}%**（下降明显）；"
            )
        elif t_new < t_old:
            md.append(
                f"部分：`Al80Cu20_tracer` MAPE {t_old:.1f}% → **{t_new:.1f}%**（略降）；"
            )
        else:
            md.append(
                f"有限/未缓解：`Al80Cu20_tracer` MAPE {t_old:.1f}% → **{t_new:.1f}%**；"
            )
        md.append(f" `Al80Cu20_inter` {i_old:.1f}% → {i_new:.1f}%。\n\n")

    md.append("## ALL 指标 mean ± std（本跑，跨折）\n\n")
    for model in ["LF_only", "HF_only", "MFNN"]:
        sub = summary_df[summary_df.model == model]
        md.append(f"### {model}\n\n")
        md.append(f"- **MAPE%**: {_mean_std(sub['MAPE_pct'])}\n")
        md.append(f"- **Factor2**: {_mean_std(sub['Factor2'])}\n")
        md.append(f"- **R²**: {_mean_std(sub['R2'])}\n\n")

    best = new_m.loc[new_m["MAPE_pct"].idxmin()]
    worst = new_m.loc[new_m["MAPE_pct"].idxmax()]
    md.append("## MFNN 最好 / 最差折\n\n")
    md.append(
        f"- **最好**: `{best['holdout_group']}` — MAPE={best['MAPE_pct']:.2f}%, "
        f"Fac2={float(best['Factor2']):.3f}, n={int(best['n'])}\n"
    )
    md.append(
        f"- **最差**: `{worst['holdout_group']}` — MAPE={worst['MAPE_pct']:.2f}%, "
        f"Fac2={float(worst['Factor2']):.3f}, n={int(worst['n'])}\n\n"
    )

    md.append("## 逐折明细\n\n```\n")
    md.append(summary_df.sort_values(["holdout_group", "model"]).to_string(index=False))
    md.append("\n```\n\n")

    if wdf is not None:
        md.append("## 可选：协议 W（within_T）按类型分层（MFNN）\n\n```\n")
        md.append(wdf.to_string(index=False))
        md.append("\n```\n\n")

    md.append("## 文件\n\n")
    md.append("- `outputs/LOGO_AlCu_difftype_feat_summary.csv`\n")
    md.append("- `outputs/LOGO_AlCu_difftype_feat_REPORT.md`\n")
    md.append("- 对照：`outputs/LOGO_AlCu_by_difftype_summary.csv`\n")

    path = out / "LOGO_AlCu_difftype_feat_REPORT.md"
    path.write_text("".join(md), encoding="utf-8")
    print(f"[wrote] {path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--skip-within-T", action="store_true")
    args = ap.parse_args()
    set_seed(args.seed)
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)

    summary_df, fold_meta = run_logo(args.seed, out)
    summary_path = out / "LOGO_AlCu_difftype_feat_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"[wrote] {summary_path}")

    wdf = None if args.skip_within_T else optional_within_T(args.seed, out)
    write_report(
        summary_df,
        fold_meta,
        out / "LOGO_AlCu_by_difftype_summary.csv",
        wdf,
        out,
    )

    mfnn = summary_df[summary_df.model == "MFNN"]
    print(f"\nMFNN MAPE%: {_mean_std(mfnn['MAPE_pct'])}")
    for g in ["Al80Cu20_tracer", "Al80Cu20_inter"]:
        sub = mfnn[mfnn.holdout_group == g]
        if len(sub):
            r = sub.iloc[0]
            print(
                f"  {g}: MAPE={float(r.MAPE_pct):.2f}% Fac2={float(r.Factor2):.3f} n={int(r.n)}"
            )


if __name__ == "__main__":
    main()
