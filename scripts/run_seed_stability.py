#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run train.py across seeds; summarize W (within_T) and G (between_group) ALL metrics.

Usage:
  python scripts/run_seed_stability.py
  python scripts/run_seed_stability.py --eval both
  python scripts/run_seed_stability.py --eval between_group   # legacy single-protocol
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from train import main as train_main  # noqa: E402

SEEDS = [0, 1, 2, 42, 123]
PROTO_LABEL = {"within_T": "W", "between_group": "G"}


def _all_rows(metrics_csv: Path, seed: int, protocol: str) -> pd.DataFrame:
    if not metrics_csv.is_file():
        return pd.DataFrame()
    df = pd.read_csv(metrics_csv)
    df = df[df["system"].astype(str) == "ALL"].copy()
    if df.empty:
        return df
    # train.py may already have written seed/protocol columns
    df["seed"] = seed
    df["protocol"] = PROTO_LABEL.get(protocol, protocol)
    cols = ["seed", "protocol", "model", "MAPE_pct", "Factor2", "R2", "n"]
    for c in cols:
        if c not in df.columns:
            df[c] = float("nan") if c != "model" else ""
    return df[cols]


def _g_holdout_info(seed_dir: Path) -> dict:
    """Inspect G test set: systems / comp_groups / Al-Cu-only flag."""
    pred = seed_dir / "test_predictions_between_group.csv"
    if not pred.is_file():
        pred = seed_dir / "between_group" / "test_predictions.csv"
    if not pred.is_file():
        return {
            "g_systems": "",
            "g_groups": "",
            "g_only_AlCu": None,
            "g_n": 0,
        }
    te = pd.read_csv(pred)
    systems = sorted(te["system"].astype(str).unique().tolist())
    groups = sorted(te["comp_group"].astype(str).unique().tolist())
    only_alcu = systems == ["Al-Cu"]
    return {
        "g_systems": ",".join(systems),
        "g_groups": ",".join(groups),
        "g_only_AlCu": bool(only_alcu),
        "g_n": int(len(te)),
    }


def _mean_std(series: pd.Series) -> str:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return "n/a"
    return f"{s.mean():.4g} ± {s.std(ddof=0):.4g}"


def run_wg(seeds: list[int]) -> None:
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    long_rows: list[pd.DataFrame] = []
    holdout_rows: list[dict] = []

    for seed in seeds:
        print("\n" + "=" * 60)
        print(f"SEED {seed}  --eval both")
        print("=" * 60)
        seed_dir = out / f"seed_wg_{seed}"
        train_main(
            seed=seed,
            make_plots=(seed == 42),
            out_subdir=f"seed_wg_{seed}",
            eval_mode="both",
        )
        for proto, fname in [
            ("within_T", "metrics_within_T.csv"),
            ("between_group", "metrics_between_group.csv"),
        ]:
            long_rows.append(_all_rows(seed_dir / fname, seed, proto))
        info = _g_holdout_info(seed_dir)
        info["seed"] = seed
        holdout_rows.append(info)
        print(
            f"[G hold-out seed={seed}] systems={info['g_systems']} "
            f"groups={info['g_groups']} only_AlCu={info['g_only_AlCu']} n={info['g_n']}"
        )

    summary = pd.concat([r for r in long_rows if len(r)], ignore_index=True)
    summary_path = out / "seed_WG_summary.csv"
    summary.to_csv(summary_path, index=False)

    hold_df = pd.DataFrame(holdout_rows)

    md: list[str] = []
    md.append("# 多 seed 稳定性：协议 W（within_T）vs G（between_group）\n\n")
    md.append(f"Seeds: `{seeds}`\n\n")
    md.append(
        "命令等价于对各 seed 执行 `python train.py --eval both --seed <SEED>` "
        f"（本脚本写入 `outputs/seed_wg_<SEED>/` 以免覆盖）。"
        "缺 η 行仍 drop；**未**用 Kozlov 填 HF η。\n\n"
    )
    md.append(
        "> **声明：** 不得把单一 seed 的 G≈20% MAPE 当作最终论文结论；"
        "G 强烈依赖留出的 `comp_group`，须报告 mean±std 与 hold-out 组成。\n\n"
    )

    md.append("## MFNN ALL：W / G 的 mean ± std（总体标准差 ddof=0）\n\n")
    for proto, label in [("W", "W (within_T)"), ("G", "G (between_group)")]:
        sub = summary[
            (summary["protocol"] == proto) & (summary["model"].astype(str) == "MFNN")
        ]
        md.append(f"### {label}\n\n")
        md.append(f"- **MAPE%**: {_mean_std(sub['MAPE_pct'])}\n")
        md.append(f"- **Factor2**: {_mean_std(sub['Factor2'])}\n")
        md.append(f"- **R²**: {_mean_std(sub['R2'])}\n")
        md.append(f"- **n** (test): {_mean_std(sub['n'])}\n\n")

    md.append("## 各 seed × 协议 × 模型（ALL 行）\n\n")
    md.append("```\n")
    md.append(
        summary.sort_values(["seed", "protocol", "model"]).to_string(index=False)
    )
    md.append("\n```\n\n")

    md.append("## 协议 G：每个 seed 的 hold-out 体系 / 是否仅 Al-Cu\n\n")
    md.append(
        "G 随留出 `comp_group` 变化：同一模型在「软」hold-out（纯 Al / 杂质）与"
        "「硬」hold-out（高 Cu 合金组）上 MAPE 可差一个数量级。\n\n"
    )
    md.append("| seed | G systems | G comp_groups | only Al-Cu? | n_test |\n")
    md.append("|------|-----------|---------------|-------------|--------|\n")
    for _, r in hold_df.iterrows():
        md.append(
            f"| {r['seed']} | {r['g_systems']} | {r['g_groups']} | "
            f"{r['g_only_AlCu']} | {r['g_n']} |\n"
        )
    md.append("\n")

    # Per-seed MFNN MAPE for W and G side by side
    md.append("## 各 seed 的 MFNN ALL MAPE% / Factor2（W vs G）\n\n")
    md.append("| seed | W MAPE% | W Fac2 | G MAPE% | G Fac2 | G only Al-Cu |\n")
    md.append("|------|---------|--------|---------|--------|--------------|\n")
    for seed in seeds:
        w = summary[(summary.seed == seed) & (summary.protocol == "W") & (summary.model == "MFNN")]
        g = summary[(summary.seed == seed) & (summary.protocol == "G") & (summary.model == "MFNN")]
        h = hold_df[hold_df.seed == seed].iloc[0] if len(hold_df[hold_df.seed == seed]) else None
        wm = float(w["MAPE_pct"].iloc[0]) if len(w) else float("nan")
        wf = float(w["Factor2"].iloc[0]) if len(w) else float("nan")
        gm = float(g["MAPE_pct"].iloc[0]) if len(g) else float("nan")
        gf = float(g["Factor2"].iloc[0]) if len(g) else float("nan")
        only = h["g_only_AlCu"] if h is not None else ""
        md.append(f"| {seed} | {wm:.2f} | {wf:.3f} | {gm:.2f} | {gf:.3f} | {only} |\n")
    md.append("\n")

    md.append("## 基线 ALL MAPE mean±std（对照）\n\n")
    for proto in ["W", "G"]:
        md.append(f"### Protocol {proto}\n\n")
        for model in ["LF_only", "HF_only", "MFNN"]:
            sub = summary[(summary.protocol == proto) & (summary.model == model)]
            md.append(
                f"- **{model}**: MAPE {_mean_std(sub['MAPE_pct'])}; "
                f"Factor2 {_mean_std(sub['Factor2'])}\n"
            )
        md.append("\n")

    md.append("## 文件\n\n")
    md.append("- `outputs/seed_WG_summary.csv`\n")
    md.append("- `outputs/SEED_WG_STABILITY.md`\n")
    md.append("- per-seed: `outputs/seed_wg_<SEED>/metrics_within_T.csv`, `metrics_between_group.csv`\n")

    md_path = out / "SEED_WG_STABILITY.md"
    md_path.write_text("".join(md), encoding="utf-8")
    print(f"\n[wrote] {summary_path}")
    print(f"[wrote] {md_path}")

    mfnn_w = summary[(summary.protocol == "W") & (summary.model == "MFNN")]
    mfnn_g = summary[(summary.protocol == "G") & (summary.model == "MFNN")]
    print(f"\nMFNN W MAPE%: {_mean_std(mfnn_w['MAPE_pct'])}")
    print(f"MFNN W Factor2: {_mean_std(mfnn_w['Factor2'])}")
    print(f"MFNN G MAPE%: {_mean_std(mfnn_g['MAPE_pct'])}")
    print(f"MFNN G Factor2: {_mean_std(mfnn_g['Factor2'])}")


def run_legacy_single(seeds: list[int]) -> None:
    """Original single-protocol path (default train / between_group only)."""
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    rows = []
    for seed in seeds:
        print("\n" + "=" * 60)
        print(f"SEED {seed}")
        print("=" * 60)
        summary = train_main(seed=seed, make_plots=(seed == 42), out_subdir=f"seed_{seed}")
        for _, r in summary.iterrows():
            d = r.to_dict()
            d["seed"] = seed
            rows.append(d)

    all_df = pd.DataFrame(rows)
    cols = ["seed"] + [c for c in all_df.columns if c != "seed"]
    all_df = all_df[cols]
    all_df.to_csv(out / "seed_stability_summary.csv", index=False)
    print(f"[wrote] {out / 'seed_stability_summary.csv'}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Multi-seed W/G stability")
    ap.add_argument(
        "--eval",
        dest="eval_mode",
        default="both",
        choices=["both", "within_T", "between_group", "legacy"],
        help="both=W+G summary (default); legacy=old seed_stability_summary path",
    )
    ap.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    args = ap.parse_args()
    if args.eval_mode == "both":
        run_wg(args.seeds)
    elif args.eval_mode == "legacy":
        run_legacy_single(args.seeds)
    else:
        # single protocol via train_main
        out = ROOT / "outputs"
        out.mkdir(exist_ok=True)
        long_rows = []
        for seed in args.seeds:
            seed_dir_name = f"seed_{args.eval_mode}_{seed}"
            train_main(
                seed=seed,
                make_plots=False,
                out_subdir=seed_dir_name,
                eval_mode=args.eval_mode,
            )
            fname = (
                "metrics_within_T.csv"
                if args.eval_mode == "within_T"
                else "metrics_between_group.csv"
            )
            long_rows.append(_all_rows(out / seed_dir_name / fname, seed, args.eval_mode))
        summary = pd.concat(long_rows, ignore_index=True)
        summary.to_csv(out / "seed_WG_summary.csv", index=False)
        print(f"[wrote] {out / 'seed_WG_summary.csv'}")


if __name__ == "__main__":
    main()
