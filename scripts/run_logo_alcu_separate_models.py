#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Train separate Residual MFNN pools (tracer / inter) and run Al-Cu LOGO per pool.

  python scripts/run_logo_alcu_separate_models.py --seed 42

- tracer pool: diff_type in {tracer}; LF+HF
- inter pool: diff_type in {inter, interdiffusivity}; HF only (no LF in current CSV)
- impurity / self NOT in either pool
- Features: 12-D phys only (no diff_type one-hot; redundant within a single-type pool)
- No Kozlov HF eta; D/eta unchanged
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
    NUM_PHYS,
    ensure_training_csv,
    load_csv,
    normalize_diff_type_label,
)
from eval import _metrics  # noqa: E402
from run_logo_alcu import _mean_std, _run_fold, _split_remaining_hf  # noqa: E402
from train import main as train_main, set_seed  # noqa: E402

POOLS = {
    "tracer": {"types": {"tracer"}},
    "inter": {"types": {"inter"}},  # interdiffusivity already normalized → inter
}


def _filter_pool(df: pd.DataFrame, types: set) -> pd.DataFrame:
    dt = df["diff_type"].map(normalize_diff_type_label)
    return df[dt.isin(types)].reset_index(drop=True)


def run_pool_logo(
    pool: str,
    types: set,
    df_all: pd.DataFrame,
    seed: int,
    out: Path,
) -> tuple[pd.DataFrame, list]:
    df_pool = _filter_pool(df_all, types)
    df_lf = df_pool[df_pool["fidelity"].astype(str).str.upper() == "LF"].reset_index(drop=True)
    df_hf = df_pool[df_pool["fidelity"].astype(str).str.upper() == "HF"].reset_index(drop=True)
    hf_alcu = df_hf[df_hf["system"].astype(str) == "Al-Cu"].reset_index(drop=True)
    groups = sorted(hf_alcu["comp_group"].astype(str).unique().tolist())
    print("\n" + "#" * 64)
    print(
        f"POOL={pool} types={sorted(types)} | LF={len(df_lf)} HF={len(df_hf)} "
        f"| Al-Cu LOGO groups ({len(groups)}): {groups}"
    )
    print(f"Features: {NUM_PHYS}-D phys only (no diff_type one-hot)")
    print("#" * 64)

    folds_root = out / f"logo_alcu_separate_{pool}_folds"
    folds_root.mkdir(exist_ok=True)
    rows, meta = [], []
    for g in groups:
        print("\n" + "=" * 60)
        print(f"[{pool}] HOLDOUT {g}")
        print("=" * 60)
        df_te = hf_alcu[hf_alcu["comp_group"].astype(str) == g].reset_index(drop=True)
        # remaining HF from same pool only (any system in pool)
        df_remain = df_hf[df_hf["comp_group"].astype(str) != g].reset_index(drop=True)
        df_tr, df_va = _split_remaining_hf(df_remain, seed=seed)
        print(
            f"[Split] n_test={len(df_te)}; HF train/val={len(df_tr)}/{len(df_va)}; LF={len(df_lf)}"
        )
        if len(df_tr) == 0:
            print("[Warn] empty HF train; skip fold")
            continue
        fold_dir = folds_root / g.replace("/", "_").replace("\\", "_")
        summary = _run_fold(
            df_lf,
            df_tr,
            df_va,
            df_te,
            seed,
            fold_dir,
            include_difftype_onehot=False,
        )
        meta.append({"pool": pool, "holdout_group": g, "n_test": len(df_te)})
        for _, r in summary[summary["system"].astype(str) == "ALL"].iterrows():
            rows.append({
                "pool": pool,
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
    return pd.DataFrame(rows), meta


def optional_within_T_pool(
    pool: str,
    types: set,
    seed: int,
    out: Path,
) -> pd.DataFrame | None:
    """within_T on pool-filtered CSV snapshot (temp write under outputs)."""
    csv_path = ensure_training_csv(str(ROOT / "data"))
    df = load_csv(csv_path)
    df_pool = _filter_pool(df, types)
    if len(df_pool[df_pool.fidelity.str.upper() == "HF"]) < 4:
        print(f"[W] skip pool={pool}: too few HF")
        return None
    tmp = out / f"_tmp_pool_{pool}_data.csv"
    # Write pool CSV; train.main uses ensure_training_csv on data/ — so call protocol directly
    from data import build_feature_matrix, FeatureStandardizer
    from train import _run_one_protocol

    df_lf = df_pool[df_pool.fidelity.str.upper() == "LF"].reset_index(drop=True)
    df_hf = df_pool[df_pool.fidelity.str.upper() == "HF"].reset_index(drop=True)
    # Monkey: _run_one_protocol uses build_feature_matrix without flag → 16-D.
    # For fair W we need 12-D; skip optional W if awkward, or patch temporarily.
    # Simpler: write filtered CSV to data overwrite is bad. Skip using train.main.
    # Implement mini W here with include_difftype_onehot=False via fold-like code.
    from data import split_within_group_T
    import torch
    from train import (
        train_residual_mfnn,
        train_single_fidelity_baseline,
    )

    set_seed(seed)
    df_tr, df_va, df_te, used = split_within_group_T(df_hf, seed=seed)
    if len(df_te) == 0:
        return None
    print(f"[W {pool}] test groups used: {used}; n_te={len(df_te)}")
    fold_dir = out / f"within_T_separate_{pool}"
    summary = _run_fold(
        df_lf, df_tr, df_va, df_te, seed, fold_dir, include_difftype_onehot=False
    )
    # stratify by... all same type; just ALL MFNN
    all_m = summary[(summary.system == "ALL") & (summary.model == "MFNN")]
    rows = [{
        "pool": pool,
        "protocol": "within_T",
        "diff_type_norm": pool,
        "model": "MFNN",
        "MAPE_pct": float(all_m.MAPE_pct.iloc[0]) if len(all_m) else float("nan"),
        "Factor2": float(all_m.Factor2.iloc[0]) if len(all_m) else float("nan"),
        "R2": float(all_m.R2.iloc[0]) if len(all_m) else float("nan"),
        "n": int(all_m.n.iloc[0]) if len(all_m) else 0,
    }]
    return pd.DataFrame(rows)


def write_report(
    summary: pd.DataFrame,
    meta: list,
    joint_path: Path,
    wdfs: list,
    out: Path,
) -> None:
    joint = pd.read_csv(joint_path) if joint_path.is_file() else None
    md: list[str] = []
    md.append("# Al–Cu 分训 Residual MFNN（tracer / inter）+ 分池 LOGO\n\n")
    md.append(
        "两套独立模型：**tracer 池**仅 `diff_type∈{tracer}`；**inter 池**仅 "
        "`{inter, interdiffusivity→inter}`。`impurity` / `self` **未入池**。"
        f"分训子集内特征为 **{NUM_PHYS} 维物理特征**（去掉 diff_type one-hot，避免冗余）。"
        "`--seed 42` 仅控优化器。缺 η drop；未改 D/η；无 Kozlov。\n\n"
    )
    md.append(
        "> 验证「同类型内迁移」是否好于联合+one-hot；仍是 Al–Cu 体系内成分外推。\n\n"
    )

    md.append("## 池规模与折\n\n")
    for pool in ["tracer", "inter"]:
        m = [x for x in meta if x["pool"] == pool]
        md.append(f"### {pool}\n\n")
        md.append("| holdout_group | n_test |\n|---|---:|\n")
        for row in m:
            md.append(f"| {row['holdout_group']} | {row['n_test']} |\n")
        md.append(f"\n共 {len(m)} 折。\n\n")

    md.append("## 与联合+one-hot 对照（Al80）\n\n")
    md.append(
        "| holdout | 联合+one-hot MFNN | 分训池 MFNN |\n|---|---|---|\n"
    )
    for g, pool in [("Al80Cu20_tracer", "tracer"), ("Al80Cu20_inter", "inter")]:
        j = (
            joint[(joint.holdout_group == g) & (joint.model == "MFNN")]
            if joint is not None
            else pd.DataFrame()
        )
        s = summary[
            (summary.pool == pool)
            & (summary.holdout_group == g)
            & (summary.model == "MFNN")
        ]
        js = (
            f"{float(j.MAPE_pct.iloc[0]):.2f}% / Fac2={float(j.Factor2.iloc[0]):.3f} / n={int(j.n.iloc[0])}"
            if len(j)
            else "n/a"
        )
        ss = (
            f"{float(s.MAPE_pct.iloc[0]):.2f}% / Fac2={float(s.Factor2.iloc[0]):.3f} / n={int(s.n.iloc[0])}"
            if len(s)
            else "n/a"
        )
        md.append(f"| `{g}` | {js} | {ss} |\n")
    md.append("\n")

    md.append("## 各池 MFNN mean±std（跨折）\n\n")
    for pool in ["tracer", "inter"]:
        sub = summary[(summary.pool == pool) & (summary.model == "MFNN")]
        md.append(f"- **{pool}**: MAPE {_mean_std(sub['MAPE_pct'])}; "
                  f"Factor2 {_mean_std(sub['Factor2'])}\n")
    if joint is not None:
        jm = joint[joint.model == "MFNN"]
        md.append(
            f"- **联合+one-hot（对照）**: MAPE {_mean_std(jm['MAPE_pct'])}; "
            f"Factor2 {_mean_std(jm['Factor2'])}\n"
        )
    md.append("\n")

    # Verdict
    md.append("## 结论：同类型内迁移是否更好？\n\n")
    def _get(pool, g):
        s = summary[(summary.pool == pool) & (summary.holdout_group == g) & (summary.model == "MFNN")]
        return float(s.MAPE_pct.iloc[0]) if len(s) else float("nan")

    def _j(g):
        if joint is None:
            return float("nan")
        s = joint[(joint.holdout_group == g) & (joint.model == "MFNN")]
        return float(s.MAPE_pct.iloc[0]) if len(s) else float("nan")

    t_sep, t_j = _get("tracer", "Al80Cu20_tracer"), _j("Al80Cu20_tracer")
    i_sep, i_j = _get("inter", "Al80Cu20_inter"), _j("Al80Cu20_inter")
    md.append(
        f"- **tracer→tracer**（`Al80Cu20_tracer`）: 联合 {t_j:.1f}% → 分训 **{t_sep:.1f}%**"
    )
    if t_sep < t_j * 0.7:
        md.append(" — **明显改善**。\n")
    elif t_sep < t_j:
        md.append(" — 有改善。\n")
    else:
        md.append(" — 未明显好于联合。\n")
    md.append(
        f"- **inter→inter**（`Al80Cu20_inter`）: 联合 {i_j:.1f}% → 分训 **{i_sep:.1f}%**"
    )
    if i_sep < i_j * 0.7:
        md.append(" — **明显改善**。\n")
    elif i_sep < i_j:
        md.append(" — 有改善。\n")
    else:
        md.append(" — 未明显好于联合。\n")
    md.append(
        "\n注：当前 CSV **inter 池 LF=0**，MFNN 的 LF 分支无数据；LF_only 指标为 NaN/跳过。"
        "impurity（PureAl_impurityCu / Ni）与 self（PureAl）未入这两套 LOGO。\n\n"
    )

    md.append("## 逐折明细\n\n```\n")
    md.append(summary.sort_values(["pool", "holdout_group", "model"]).to_string(index=False))
    md.append("\n```\n\n")

    if wdfs:
        md.append("## 可选：各池 within_T（MFNN）\n\n```\n")
        md.append(pd.concat(wdfs, ignore_index=True).to_string(index=False))
        md.append("\n```\n\n")

    md.append("## 文件\n\n")
    md.append("- `outputs/LOGO_AlCu_separate_models_summary.csv`\n")
    md.append("- `outputs/LOGO_AlCu_separate_models_REPORT.md`\n")
    md.append("- 对照：`outputs/LOGO_AlCu_difftype_feat_summary.csv`\n")

    path = out / "LOGO_AlCu_separate_models_REPORT.md"
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

    csv_path = ensure_training_csv(str(ROOT / "data"))
    df = load_csv(csv_path)
    print(f"[Data] {csv_path}")

    all_rows, all_meta = [], []
    for pool, cfg in POOLS.items():
        sdf, meta = run_pool_logo(pool, cfg["types"], df, args.seed, out)
        all_rows.append(sdf)
        all_meta.extend(meta)

    summary = pd.concat(all_rows, ignore_index=True)
    summary_path = out / "LOGO_AlCu_separate_models_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"[wrote] {summary_path}")

    wdfs = []
    if not args.skip_within_T:
        for pool, cfg in POOLS.items():
            w = optional_within_T_pool(pool, cfg["types"], args.seed, out)
            if w is not None:
                wdfs.append(w)

    write_report(
        summary,
        all_meta,
        out / "LOGO_AlCu_difftype_feat_summary.csv",
        wdfs,
        out,
    )

    for pool in ["tracer", "inter"]:
        m = summary[(summary.pool == pool) & (summary.model == "MFNN")]
        print(f"MFNN {pool}: {_mean_std(m['MAPE_pct'])}")
    for g, pool in [("Al80Cu20_tracer", "tracer"), ("Al80Cu20_inter", "inter")]:
        s = summary[(summary.pool == pool) & (summary.holdout_group == g) & (summary.model == "MFNN")]
        if len(s):
            r = s.iloc[0]
            print(
                f"  {g}: MAPE={float(r.MAPE_pct):.2f}% Fac2={float(r.Factor2):.3f} n={int(r.n)}"
            )


if __name__ == "__main__":
    main()
