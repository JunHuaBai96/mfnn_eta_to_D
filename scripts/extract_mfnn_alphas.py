#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract alpha_1 / alpha_2 from Protocol W MFNN checkpoints (no retrain).

Reads:
  outputs/seed_wg_{0,1,2,42,123}/within_T/mfnn_checkpoint.pt

Usage (from repo root):
  python scripts/extract_mfnn_alphas.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
SEEDS = [0, 1, 2, 42, 123]


def _as_float(x) -> float:
    if isinstance(x, torch.Tensor):
        return float(x.detach().cpu().reshape(-1)[0].item())
    return float(x)


def _extract_one(path: Path) -> dict:
    obj = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(obj, dict):
        raise TypeError(f"{path}: expected dict checkpoint, got {type(obj)}")

    # Prefer top-level floats saved by train.py; fall back to state_dict
    sd = obj.get("mfnn_state_dict") or obj.get("model") or obj.get("state_dict")
    if "alpha_1" in obj:
        a1 = _as_float(obj["alpha_1"])
    elif isinstance(sd, dict) and "alpha_1" in sd:
        a1 = _as_float(sd["alpha_1"])
    else:
        raise KeyError(f"{path}: cannot find alpha_1")

    if "alpha_2" in obj:
        a2 = _as_float(obj["alpha_2"])
    elif isinstance(sd, dict) and "alpha_2" in sd:
        a2 = _as_float(sd["alpha_2"])
    else:
        raise KeyError(f"{path}: cannot find alpha_2")

    # Linear map on [x, y_L]: last weight multiplies y_L (model.py ResidualMFNN.lin)
    lin_w_yL = "N/A"
    lin_bias = "N/A"
    lin_in_dim = "N/A"
    if isinstance(sd, dict) and "lin.weight" in sd:
        w = sd["lin.weight"].detach().cpu().reshape(-1)
        lin_in_dim = int(w.numel())
        lin_w_yL = float(w[-1].item())  # last column = y_L
        if "lin.bias" in sd:
            lin_bias = float(sd["lin.bias"].detach().cpu().reshape(-1)[0].item())

    seed = int(obj.get("seed", path.parents[1].name.split("_")[-1]))
    protocol = str(obj.get("protocol", "unknown"))
    return {
        "seed": seed,
        "protocol": protocol,
        "checkpoint": str(path.relative_to(ROOT)).replace("\\", "/"),
        "alpha_1": a1,
        "alpha_2": a2,
        "lin_weight_yL": lin_w_yL,
        "lin_bias": lin_bias,
        "lin_in_dim": lin_in_dim,
        "abs_alpha_1": abs(a1),
        "abs_alpha_2": abs(a2),
    }


def main() -> None:
    rows = []
    for seed in SEEDS:
        path = ROOT / "outputs" / f"seed_wg_{seed}" / "within_T" / "mfnn_checkpoint.pt"
        if not path.is_file():
            raise FileNotFoundError(path)
        row = _extract_one(path)
        rows.append(row)
        print(
            f"seed={seed:3d}  alpha_1={row['alpha_1']:.6f}  alpha_2={row['alpha_2']:.6f}  "
            f"lin_w_yL={row['lin_weight_yL'] if isinstance(row['lin_weight_yL'], str) else f'{row['lin_weight_yL']:.6f}'}"
        )

    df = pd.DataFrame(rows)
    out_dir = ROOT / "outputs" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "protocol_W_alpha_table.csv"
    df.to_csv(csv_path, index=False)

    a1 = df["alpha_1"].to_numpy(dtype=float)
    a2 = df["alpha_2"].to_numpy(dtype=float)
    # population std (ddof=0), consistent with SEED_WG reporting style
    a1_mean, a1_std = float(np.mean(a1)), float(np.std(a1, ddof=0))
    a2_mean, a2_std = float(np.mean(a2)), float(np.std(a2, ddof=0))

    # Compare |α| means only — magnitudes of mixing weights, not branch outputs
    mean_abs_a1 = float(np.mean(np.abs(a1)))
    mean_abs_a2 = float(np.mean(np.abs(a2)))
    if mean_abs_a2 > mean_abs_a1:
        mix_note = (
            f"五种子上 $|\\alpha_2|$ 均值 ({mean_abs_a2:.4f}) > $|\\alpha_1|$ 均值 ({mean_abs_a1:.4f})，"
            "即 **非线性残差支路的混合权重更大**（仅指 $\\alpha$ 标量，非支路输出范数）。"
        )
    elif mean_abs_a1 > mean_abs_a2:
        mix_note = (
            f"五种子上 $|\\alpha_1|$ 均值 ({mean_abs_a1:.4f}) > $|\\alpha_2|$ 均值 ({mean_abs_a2:.4f})，"
            "即 **线性混合支路的混合权重更大**（仅指 $\\alpha$ 标量，非支路输出范数）。"
        )
    else:
        mix_note = "五种子上 $|\\alpha_1|$ 与 $|\\alpha_2|$ 均值相等。"

    # lin y_L weight summary if numeric
    lin_vals = [r["lin_weight_yL"] for r in rows if isinstance(r["lin_weight_yL"], float)]
    if lin_vals:
        lin_mean = float(np.mean(lin_vals))
        lin_std = float(np.std(lin_vals, ddof=0))
        lin_line = (
            f"- 线性层对 $y_L$ 的权重（`lin.weight` 最后一列）："
            f" mean±std = ${lin_mean:.4f}\\pm{lin_std:.4f}$（$n={len(lin_vals)}$）。\n"
        )
    else:
        lin_line = "- 线性层 $y_L$ 权重：N/A（state_dict 中未找到 `lin.weight`）。\n"

    report = []
    report.append("# Protocol W MFNN $\\alpha_1$, $\\alpha_2$ 提取报告\n\n")
    report.append(
        "只读 checkpoint，**未重训**。来源：`outputs/seed_wg_{0,1,2,42,123}/within_T/mfnn_checkpoint.pt`。\n\n"
    )
    report.append("模型（`model.py`）：\n")
    report.append(
        "$$y_H \\approx \\alpha_1\\,(A[x,y_L]+b) + \\alpha_2\\,F_{\\mathrm{nl}}(x,y_L).$$\n\n"
    )
    report.append("## 逐 seed\n\n")
    report.append(
        "| seed | $\\alpha_1$ | $\\alpha_2$ | `lin.weight`[$y_L$] | `lin.bias` |\n"
        "|---:|---:|---:|---:|---:|\n"
    )
    for _, r in df.iterrows():
        yw = r["lin_weight_yL"]
        lb = r["lin_bias"]
        yw_s = f"{yw:.6f}" if isinstance(yw, float) else "N/A"
        lb_s = f"{lb:.6f}" if isinstance(lb, float) else "N/A"
        report.append(
            f"| {int(r['seed'])} | {r['alpha_1']:.6f} | {r['alpha_2']:.6f} | {yw_s} | {lb_s} |\n"
        )
    report.append("\n## 汇总（population std, ddof=0）\n\n")
    report.append(f"- $\\alpha_1$ = **${a1_mean:.4f}\\pm{a1_std:.4f}$**\n")
    report.append(f"- $\\alpha_2$ = **${a2_mean:.4f}\\pm{a2_std:.4f}$**\n")
    report.append(lin_line)
    report.append(f"\n## 线性混合 vs 非线性残差\n\n{mix_note}\n")
    report.append(
        "\nCSV：`outputs/results/protocol_W_alpha_table.csv`。\n"
    )

    report_path = out_dir / "PROTOCOL_W_ALPHA_REPORT.md"
    report_path.write_text("".join(report), encoding="utf-8")

    print(f"\nalpha_1 = {a1_mean:.4f} ± {a1_std:.4f}")
    print(f"alpha_2 = {a2_mean:.4f} ± {a2_std:.4f}")
    print(f"[wrote] {csv_path}")
    print(f"[wrote] {report_path}")


if __name__ == "__main__":
    main()
