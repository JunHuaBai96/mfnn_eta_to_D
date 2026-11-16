#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Split Al-Cu (and mixed) comp_groups by diff_type, then re-run Al-Cu LOGO.

  python scripts/run_logo_alcu_by_difftype.py --seed 42

- Backs up CSV if not already backed up
- Rewrites data/melt_diffusion_data.csv with Al80Cu20_tracer / Al80Cu20_inter etc.
- interdiffusivity -> inter suffix; impurity never merged into tracer/inter
- No diff_type one-hot in features (label disambiguation only)
- No Kozlov HF eta fill
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from data import (  # noqa: E402
    apply_comp_group_difftype_split,
    ensure_training_csv,
    load_csv,
    normalize_diff_type_label,
)
from run_logo_alcu import (  # noqa: E402
    _mean_std,
    _run_fold,
    _split_remaining_hf,
)
from train import set_seed  # noqa: E402


def _rewrite_csv(csv_path: Path) -> dict:
    raw = pd.read_csv(csv_path)
    before_groups = sorted(raw["comp_group"].astype(str).unique().tolist())
    # Count mixed before
    mixed = []
    for (sys, g), sub in raw.groupby([raw["system"].astype(str), raw["comp_group"].astype(str)]):
        types = {normalize_diff_type_label(t) for t in sub["diff_type"].astype(str)}
        if len(types) > 1:
            mixed.append((sys, g, sorted(types), len(sub)))

    new = apply_comp_group_difftype_split(raw)
    after_groups = sorted(new["comp_group"].astype(str).unique().tolist())
    new.to_csv(csv_path, index=False)

    # Verify no Al-Cu base still mixes types under same new name
    df_chk = load_csv(str(csv_path), drop_missing_eta=True)
    still_mixed = []
    for g, sub in df_chk.groupby(df_chk["comp_group"].astype(str)):
        types = {normalize_diff_type_label(t) for t in sub["diff_type"].astype(str)}
        if len(types) > 1:
            still_mixed.append((g, sorted(types)))

    al80 = df_chk[
        (df_chk["system"].astype(str) == "Al-Cu")
        & (df_chk["comp_group"].astype(str).str.startswith("Al80Cu20"))
    ]
    return {
        "before_n_groups": len(before_groups),
        "after_n_groups": len(after_groups),
        "mixed_before": mixed,
        "still_mixed": still_mixed,
        "al80_new": al80.groupby(["comp_group", "diff_type"]).size().to_dict(),
        "al_cu_hf_groups": sorted(
            df_chk[
                (df_chk.fidelity.str.upper() == "HF") & (df_chk.system.astype(str) == "Al-Cu")
            ]["comp_group"]
            .astype(str)
            .unique()
            .tolist()
        ),
    }


def _run_logo(seed: int, out: Path) -> pd.DataFrame:
    from data import ensure_training_csv as _ens

    csv_path = _ens(str(ROOT / "data"))
    print(f"[Data] {csv_path} (LOGO-by-difftype seed={seed} optimizer only)")
    df = load_csv(csv_path)
    df_lf = df[df["fidelity"].astype(str).str.upper() == "LF"].reset_index(drop=True)
    df_hf = df[df["fidelity"].astype(str).str.upper() == "HF"].reset_index(drop=True)
    hf_sys = df_hf[df_hf["system"].astype(str) == "Al-Cu"].reset_index(drop=True)
    groups = sorted(hf_sys["comp_group"].astype(str).unique().tolist())
    print(f"[LOGO] Al-Cu HF new groups ({len(groups)}): {groups}")

    folds_root = out / "logo_alcu_by_difftype_folds"
    folds_root.mkdir(exist_ok=True)
    rows = []
    fold_meta = []
    for g in groups:
        print("\n" + "=" * 60)
        print(f"HOLDOUT {g}")
        print("=" * 60)
        df_te = hf_sys[hf_sys["comp_group"].astype(str) == g].reset_index(drop=True)
        df_remain = df_hf[df_hf["comp_group"].astype(str) != g].reset_index(drop=True)
        df_tr, df_va = _split_remaining_hf(df_remain, seed=seed)
        print(
            f"[Split] holdout={g} n_test={len(df_te)}; "
            f"HF train/val={len(df_tr)}/{len(df_va)}; LF={len(df_lf)}"
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
    return pd.DataFrame(rows), fold_meta


def _optional_within_T(seed: int, out: Path) -> pd.DataFrame | None:
    try:
        from train import main as train_main
    except Exception as e:
        print(f"[Warn] skip within_T: {e}")
        return None
    print("\n[Optional] Protocol W within_T (seed=%s)..." % seed)
    train_main(
        seed=seed,
        make_plots=False,
        out_subdir="within_T_after_difftype",
        eval_mode="within_T",
    )
    # Stratify test preds by diff_type if present
    pred_path = out / "within_T_after_difftype" / "within_T" / "test_predictions.csv"
    if not pred_path.is_file():
        pred_path = out / "within_T_after_difftype" / "test_predictions_within_T.csv"
    if not pred_path.is_file():
        return None
    detail = pd.read_csv(pred_path)
    if "diff_type" not in detail.columns or "pred_MFNN_log10D" not in detail.columns:
        return None
    from eval import _metrics

    rows = []
    for dt, sub in detail.groupby(detail["diff_type"].astype(str).map(normalize_diff_type_label)):
        y = sub["y_true_log10D"].to_numpy()
        p = sub["pred_MFNN_log10D"].to_numpy()
        m = _metrics(y, p)
        rows.append({
            "diff_type_norm": dt,
            "model": "MFNN",
            "MAPE_pct": m["MAPE_pct"],
            "Factor2": m["Factor2"],
            "R2": m["R2"],
            "n": len(sub),
        })
    # ALL
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
    wdf.to_csv(out / "within_T_by_difftype_summary.csv", index=False)
    return wdf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--skip-rewrite", action="store_true", help="CSV already split")
    ap.add_argument("--skip-within-T", action="store_true")
    args = ap.parse_args()
    seed = args.seed
    set_seed(seed)

    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    data_dir = ROOT / "data"
    csv_path = Path(ensure_training_csv(str(data_dir)))

    backup = data_dir / "melt_diffusion_data_backup_before_difftype.csv"
    if not backup.is_file():
        shutil.copy2(csv_path, backup)
        print(f"[Backup] {backup}")
    else:
        print(f"[Backup] already exists: {backup}")

    if not args.skip_rewrite:
        info = _rewrite_csv(csv_path)
        print(f"[Split] groups {info['before_n_groups']} -> {info['after_n_groups']}")
        print(f"[Split] mixed before: {info['mixed_before']}")
        print(f"[Split] Al80 new: {info['al80_new']}")
        print(f"[Split] still_mixed after load: {info['still_mixed']}")
        assert not info["still_mixed"], "diff_type still mixed within a comp_group"
    else:
        info = {"al_cu_hf_groups": []}

    summary_df, fold_meta = _run_logo(seed, out)
    summary_path = out / "LOGO_AlCu_by_difftype_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    wdf = None if args.skip_within_T else _optional_within_T(seed, out)

    # --- Report ---
    old_path = out / "LOGO_AlCu_summary.csv"
    old = pd.read_csv(old_path) if old_path.is_file() else None

    md: list[str] = []
    md.append("# Al–Cu LOGO（按 diff_type 拆组后）\n\n")
    md.append(
        "将同 `comp_group` 内冲突的 tracer / inter（含 interdiffusivity→inter）拆成 "
        "`Al80Cu20_tracer` / `Al80Cu20_inter` 等；**杂质**用 `_impurity`，不并入 tracer/inter。"
        "特征**未**加 diff_type one-hot（仅消除 hold-out 标签冲突）。"
        f"LOGO 折不随机；`--seed {seed}` 仅控优化器/val。缺 η 仍 drop；无 Kozlov 填 HF η。\n\n"
    )
    md.append(
        "> 仍是 **Al–Cu 体系内成分外推**，不是跨合金体系；也不是随机 seed 的 G≈20%。\n\n"
    )
    md.append(
        f"备份：`data/melt_diffusion_data_backup_before_difftype.csv`\n\n"
    )

    md.append("## 拆组验证\n\n")
    df_now = load_csv(str(csv_path))
    al80 = df_now[
        (df_now.system.astype(str) == "Al-Cu")
        & (df_now.comp_group.astype(str).str.startswith("Al80Cu20"))
        & (df_now.fidelity.str.upper() == "HF")
    ]
    md.append("### Al80Cu20 HF 拆后\n\n")
    md.append("| new comp_group | diff_types | n | D min–max (×1e-9) |\n|---|---|---:|---|\n")
    for g, sub in al80.groupby(al80.comp_group.astype(str)):
        dts = ",".join(sorted(sub.diff_type.astype(str).unique()))
        dmin, dmax = sub.D_m2s.min() * 1e9, sub.D_m2s.max() * 1e9
        md.append(f"| {g} | {dts} | {len(sub)} | {dmin:.2f}–{dmax:.2f} |\n")
    md.append("\n同温不再把 tracer 与 inter 放在同一 hold-out 组。\n\n")

    md.append("## 折列表（新）\n\n")
    md.append("| holdout_group | n_test |\n|---|---:|\n")
    for m in fold_meta:
        md.append(f"| {m['holdout_group']} | {m['n_test']} |\n")
    md.append(f"\n共 **{len(fold_meta)}** 折。\n\n")

    md.append("## 新旧对比（MFNN）\n\n")
    if old is not None:
        old_m = old[old.model == "MFNN"].copy()
        old_m["MAPE_pct"] = pd.to_numeric(old_m["MAPE_pct"], errors="coerce")
        new_m = summary_df[summary_df.model == "MFNN"].copy()
        new_m["MAPE_pct"] = pd.to_numeric(new_m["MAPE_pct"], errors="coerce")
        md.append(
            f"- **旧 LOGO（混类型标签）** MFNN MAPE%: "
            f"{_mean_std(old_m['MAPE_pct'])}；最差折 `Al80Cu20` = "
            f"{float(old_m.loc[old_m.holdout_group=='Al80Cu20','MAPE_pct'].iloc[0]):.1f}% "
            f"(n=12 混合 tracer+inter)\n"
        )
        md.append(
            f"- **新 LOGO（按 diff_type 拆组）** MFNN MAPE%: {_mean_std(new_m['MAPE_pct'])}\n"
        )
    else:
        new_m = summary_df[summary_df.model == "MFNN"].copy()
        new_m["MAPE_pct"] = pd.to_numeric(new_m["MAPE_pct"], errors="coerce")
        md.append(f"- 新 MFNN MAPE%: {_mean_std(new_m['MAPE_pct'])}\n")

    md.append("\n### 原 Al80Cu20 拆开后两折\n\n")
    md.append("| holdout | model | MAPE% | Factor2 | n |\n|---|---|---:|---:|---:|\n")
    for g in ["Al80Cu20_tracer", "Al80Cu20_inter"]:
        sub = summary_df[summary_df.holdout_group == g]
        if len(sub) == 0:
            md.append(f"| {g} | — | (无此折) | — | — |\n")
            continue
        for _, r in sub.iterrows():
            md.append(
                f"| {g} | {r['model']} | {float(r['MAPE_pct']):.2f} | "
                f"{float(r['Factor2']):.3f} | {int(r['n'])} |\n"
            )
    md.append(
        "\n旧混合折不可再当作唯一结论；请分别引用 `_tracer` / `_inter` 两折。\n\n"
    )

    md.append("## ALL 指标 mean ± std（新 LOGO，跨折）\n\n")
    for model in ["LF_only", "HF_only", "MFNN"]:
        sub = summary_df[summary_df.model == model]
        md.append(f"### {model}\n\n")
        md.append(f"- **MAPE%**: {_mean_std(sub['MAPE_pct'])}\n")
        md.append(f"- **Factor2**: {_mean_std(sub['Factor2'])}\n")
        md.append(f"- **R²**: {_mean_std(sub['R2'])}\n\n")

    mfnn = summary_df[summary_df.model == "MFNN"].copy()
    mfnn["MAPE_pct"] = pd.to_numeric(mfnn["MAPE_pct"], errors="coerce")
    best = mfnn.loc[mfnn["MAPE_pct"].idxmin()]
    worst = mfnn.loc[mfnn["MAPE_pct"].idxmax()]
    md.append("## MFNN 最好 / 最差折（新）\n\n")
    md.append(
        f"- **最好**: `{best['holdout_group']}` — MAPE={best['MAPE_pct']:.2f}%, "
        f"Fac2={best['Factor2']:.3f}, n={int(best['n'])}\n"
    )
    md.append(
        f"- **最差**: `{worst['holdout_group']}` — MAPE={worst['MAPE_pct']:.2f}%, "
        f"Fac2={worst['Factor2']:.3f}, n={int(worst['n'])}\n\n"
    )

    md.append("## 逐折明细\n\n```\n")
    md.append(summary_df.sort_values(["holdout_group", "model"]).to_string(index=False))
    md.append("\n```\n\n")

    if wdf is not None:
        md.append("## 可选：协议 W（within_T）按 diff_type 分层（MFNN）\n\n")
        md.append("```\n" + wdf.to_string(index=False) + "\n```\n\n")
        md.append("W 是组内温度插值，与 LOGO 成分外推不同；仅作主文对照。\n\n")

    md.append("## 文件\n\n")
    md.append("- `outputs/LOGO_AlCu_by_difftype_summary.csv`\n")
    md.append("- `outputs/LOGO_AlCu_by_difftype_REPORT.md`\n")
    md.append("- 旧对照：`outputs/LOGO_AlCu_summary.csv`\n")

    report_path = out / "LOGO_AlCu_by_difftype_REPORT.md"
    report_path.write_text("".join(md), encoding="utf-8")
    print(f"\n[wrote] {summary_path}")
    print(f"[wrote] {report_path}")
    print(f"MFNN MAPE%: {_mean_std(mfnn['MAPE_pct'])}")
    for g in ["Al80Cu20_tracer", "Al80Cu20_inter"]:
        sub = summary_df[(summary_df.holdout_group == g) & (summary_df.model == "MFNN")]
        if len(sub):
            r = sub.iloc[0]
            print(
                f"  {g}: MAPE={float(r.MAPE_pct):.2f}% Fac2={float(r.Factor2):.3f} n={int(r.n)}"
            )


if __name__ == "__main__":
    main()
