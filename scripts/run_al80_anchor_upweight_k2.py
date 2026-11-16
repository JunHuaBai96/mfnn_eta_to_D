# -*- coding: utf-8 -*-
"""B1: Al80Cu20_tracer k=2 anchor up-weighting (SI diagnostic).

w_anchor in {5, 10}; w=1 baseline taken from existing experiment B CSV (no retrain).
Does NOT change Protocol W. Architecture unchanged.

  python scripts/run_al80_anchor_upweight_k2.py --seeds 42
  python scripts/run_al80_anchor_upweight_k2.py --seeds 0,1,2,42,123
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from data import (  # noqa: E402
    NUM_FEATURES,
    NUM_PHYS,
    FeatureStandardizer,
    build_feature_matrix,
    ensure_training_csv,
    load_csv,
)
from train import set_seed  # noqa: E402
from eval import evaluate_by_system  # noqa: E402
from model import ResidualMFNN, SingleFidelityNN  # noqa: E402
from run_al80_tracer_anchor_sensitivity import _anchor_masks  # noqa: E402
from run_logo_alcu import _split_remaining_hf  # noqa: E402

HOLDOUT = "Al80Cu20_tracer"


def _weighted_mse(pred: torch.Tensor, target: torch.Tensor, w: torch.Tensor | None) -> torch.Tensor:
    err2 = (pred - target) ** 2
    if w is None:
        return err2.mean()
    w = w.view_as(err2)
    return (err2 * w).sum() / w.sum().clamp_min(1e-12)


def train_sf_weighted(
    X_tr, y_tr, X_val, y_val, w_tr=None, weight_decay=1e-4, lr=1e-3, adam_epochs=1000, lbfgs_steps=40
):
    model = SingleFidelityNN(in_dim=X_tr.shape[1], width=64)
    if X_tr.shape[0] == 0:
        return model
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    best_state, best_val = None, float("inf")
    for _ in range(adam_epochs):
        model.train()
        opt.zero_grad()
        loss = _weighted_mse(model(X_tr), y_tr, w_tr)
        loss.backward()
        opt.step()
        if X_val.shape[0] > 0:
            model.eval()
            with torch.no_grad():
                v = ((model(X_val) - y_val) ** 2).mean().item()
            if v < best_val:
                best_val = v
                best_state = {k: v_.detach().clone() for k, v_ in model.state_dict().items()}
    if best_state is not None:
        model.load_state_dict(best_state)
    model.train()
    opt2 = torch.optim.LBFGS(model.parameters(), lr=0.4, max_iter=20, history_size=20, line_search_fn="strong_wolfe")

    def closure():
        opt2.zero_grad()
        loss = _weighted_mse(model(X_tr), y_tr, w_tr)
        loss.backward()
        return loss

    for _ in range(max(1, lbfgs_steps // 20)):
        try:
            opt2.step(closure)
        except RuntimeError:
            break
    return model


def train_mfnn_weighted(
    X_tr_lf, y_tr_lf, X_tr_hf, y_tr_hf, phys_tr_hf, X_val_hf, y_val_hf, w_hf=None,
    lr=1e-3, adam_epochs=1000, lbfgs_steps=40, lambda_phys=0.05, lambda_lf=1.0, lambda_hf=1.0,
):
    in_dim = X_tr_lf.shape[1] if X_tr_lf.shape[0] > 0 else X_tr_hf.shape[1]
    model = ResidualMFNN(in_dim=in_dim, width=64)
    if X_tr_lf.shape[0] == 0 and X_tr_hf.shape[0] == 0:
        return model
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    best_state, best_val = None, float("inf")
    for _ in range(adam_epochs):
        model.train()
        opt.zero_grad()
        loss = torch.tensor(0.0)
        if X_tr_lf.shape[0] > 0:
            loss = loss + lambda_lf * ((model.forward_lf(X_tr_lf) - y_tr_lf) ** 2).mean()
        if X_tr_hf.shape[0] > 0:
            pred_hf = model.forward_hf(X_tr_hf)
            loss = loss + lambda_hf * _weighted_mse(pred_hf, y_tr_hf, w_hf)
            # physics term: same weights as HF supervision (anchors matter)
            loss = loss + lambda_phys * _weighted_mse(pred_hf, phys_tr_hf, w_hf)
        loss.backward()
        opt.step()
        if X_val_hf.shape[0] > 0:
            model.eval()
            with torch.no_grad():
                v = ((model.forward_hf(X_val_hf) - y_val_hf) ** 2).mean().item()
            if v < best_val:
                best_val = v
                best_state = {k: v_.detach().clone() for k, v_ in model.state_dict().items()}
    if best_state is not None:
        model.load_state_dict(best_state)
    model.train()
    opt2 = torch.optim.LBFGS(model.parameters(), lr=0.4, max_iter=20, history_size=20, line_search_fn="strong_wolfe")

    def closure():
        opt2.zero_grad()
        loss = torch.tensor(0.0, requires_grad=True) * 0.0
        if X_tr_lf.shape[0] > 0:
            loss = loss + lambda_lf * ((model.forward_lf(X_tr_lf) - y_tr_lf) ** 2).mean()
        if X_tr_hf.shape[0] > 0:
            pred_hf = model.forward_hf(X_tr_hf)
            loss = loss + lambda_hf * _weighted_mse(pred_hf, y_tr_hf, w_hf)
            loss = loss + lambda_phys * _weighted_mse(pred_hf, phys_tr_hf, w_hf)
        loss.backward()
        return loss

    for _ in range(max(1, lbfgs_steps // 20)):
        try:
            opt2.step(closure)
        except RuntimeError:
            break
    return model


def _anchor_weight_vector(df_tr: pd.DataFrame, df_anc: pd.DataFrame, w_anchor: float) -> np.ndarray:
    """Weight=w_anchor for rows matching anchor sample_id (or T_K+comp_group), else 1."""
    w = np.ones(len(df_tr), dtype=np.float64)
    if len(df_anc) == 0:
        return w
    if "sample_id" in df_tr.columns and "sample_id" in df_anc.columns:
        anc_ids = set(df_anc["sample_id"].astype(str))
        for i, sid in enumerate(df_tr["sample_id"].astype(str)):
            if sid in anc_ids:
                w[i] = w_anchor
    else:
        anc_T = set(float(t) for t in df_anc["T_K"].tolist())
        for i, (t, g) in enumerate(zip(df_tr["T_K"], df_tr["comp_group"].astype(str))):
            if g == HOLDOUT and any(abs(float(t) - at) < 0.51 for at in anc_T):
                w[i] = w_anchor
    return w


def run_one(df_lf, df_hf, df_hold, seed: int, w_anchor: float, folds_root: Path) -> dict:
    df_anc, df_te, t_list = _anchor_masks(df_hold, "k2")
    df_remain = df_hf[df_hf["comp_group"].astype(str) != HOLDOUT].reset_index(drop=True)
    # Force k=2 anchors into TRAIN (some seeds otherwise park them in val).
    df_tr, df_va = _split_remaining_hf(df_remain, seed=seed)
    if len(df_anc):
        df_tr = pd.concat([df_tr, df_anc], ignore_index=True)
    w_np = _anchor_weight_vector(df_tr, df_anc, w_anchor)
    n_up = int((w_np > 1.0 + 1e-9).sum())

    fold_dir = folds_root / f"seed{seed}_k2_w{int(w_anchor)}"
    fold_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"\n=== seed={seed} k2 w_anchor={w_anchor} n_upweighted={n_up} "
        f"n_test={len(df_te)} anchor_T={t_list} HF_tr/va={len(df_tr)}/{len(df_va)} ==="
    )

    set_seed(seed)
    oh = True
    n_feat = NUM_FEATURES
    val_groups = set(df_va["comp_group"].astype(str).unique())
    df_tr_lf = df_lf.reset_index(drop=True)
    df_val_lf = df_lf[df_lf["comp_group"].astype(str).isin(val_groups)].reset_index(drop=True)
    if len(df_val_lf) == 0 and len(df_lf) > 0:
        df_val_lf = df_lf.sample(n=min(5, len(df_lf)), random_state=seed).reset_index(drop=True)

    X_tr_lf_raw, y_tr_lf, _ = build_feature_matrix(df_tr_lf, include_difftype_onehot=oh)
    X_val_lf_raw, y_val_lf, _ = build_feature_matrix(df_val_lf, include_difftype_onehot=oh)
    X_tr_hf_raw, y_tr_hf, phys_tr_hf = build_feature_matrix(df_tr, include_difftype_onehot=oh)
    X_val_hf_raw, y_val_hf, _ = build_feature_matrix(df_va, include_difftype_onehot=oh)
    X_te_hf_raw, y_te_hf, _ = build_feature_matrix(df_te, include_difftype_onehot=oh)

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
    t_phys = torch.tensor(phys_tr_hf, dtype=torch.float32)
    t_X_val_lf = torch.tensor(scaler.transform(X_val_lf_raw), dtype=torch.float32)
    t_y_val_lf = torch.tensor(y_val_lf, dtype=torch.float32)
    t_X_val_hf = torch.tensor(scaler.transform(X_val_hf_raw), dtype=torch.float32)
    t_y_val_hf = torch.tensor(y_val_hf, dtype=torch.float32)
    t_X_te = torch.tensor(scaler.transform(X_te_hf_raw), dtype=torch.float32)
    t_w = torch.tensor(w_np, dtype=torch.float32)

    model_lf = train_sf_weighted(t_X_tr_lf, t_y_tr_lf, t_X_val_lf, t_y_val_lf)
    model_hf = train_sf_weighted(t_X_tr_hf, t_y_tr_hf, t_X_val_hf, t_y_val_hf, w_tr=t_w, weight_decay=5e-3)
    model_mfnn = train_mfnn_weighted(
        t_X_tr_lf, t_y_tr_lf, t_X_tr_hf, t_y_tr_hf, t_phys, t_X_val_hf, t_y_val_hf, w_hf=t_w
    )

    model_lf.eval(); model_hf.eval(); model_mfnn.eval()
    with torch.no_grad():
        preds = {
            "LF_only": model_lf(t_X_te).numpy(),
            "HF_only": model_hf(t_X_te).numpy(),
            "MFNN": model_mfnn.forward_hf(t_X_te).numpy(),
        }
    summary = evaluate_by_system(
        df_te, y_te_hf, preds,
        str(fold_dir / "metrics_by_system.csv"),
        str(fold_dir / "test_predictions.csv"),
    )
    all_rows = summary[summary["system"].astype(str) == "ALL"]
    out = {
        "seed": seed,
        "mode": "k2",
        "w_anchor": w_anchor,
        "n_anchor": len(df_anc),
        "n_upweighted_in_train": n_up,
        "n_test": len(df_te),
        "anchor_T_K": ";".join(f"{t:.1f}" for t in t_list),
    }
    for model in ["LF_only", "HF_only", "MFNN"]:
        sub = all_rows[all_rows["model"] == model]
        r = sub.iloc[0]
        out[f"{model}_MAPE_pct"] = float(r["MAPE_pct"])
        out[f"{model}_Factor2"] = float(r["Factor2"])
        out[f"{model}_R2"] = float(r["R2"])
        out[f"{model}_n"] = int(r["n"])
    print(
        f"  MFNN MAPE={out['MFNN_MAPE_pct']:.2f}% Fac2={out['MFNN_Factor2']:.3f} | "
        f"HF_only MAPE={out['HF_only_MAPE_pct']:.2f}% Fac2={out['HF_only_Factor2']:.3f}"
    )
    return out


def write_report(df: pd.DataFrame, path: Path) -> None:
    lines = []
    lines.append("# Al80Cu20_tracer k=2 锚点重加权（anchor up-weighting / B1）\n\n")
    lines.append(
        "> **仅 SI。** 固定 k=2 划分；仅提高 2 个 tracer 锚点在 HF MSE 中的样本权重。"
        "w=1 基线来自已有实验 B（未重跑）。**不是**纯 LOGO；不改 Protocol W。\n\n"
    )
    lines.append("## MFNN 汇总（mean ± std, ddof=0）\n\n")
    lines.append("| w_anchor | n_seeds | MAPE% | Factor2 | R² |\n")
    lines.append("|--------:|--------:|------:|--------:|---:|\n")
    for w in sorted(df["w_anchor"].unique()):
        sub = df[df["w_anchor"] == w]
        lines.append(
            f"| {w:g} | {len(sub)} | "
            f"{sub['MFNN_MAPE_pct'].mean():.2f} ± {sub['MFNN_MAPE_pct'].std(ddof=0):.2f} | "
            f"{sub['MFNN_Factor2'].mean():.3f} ± {sub['MFNN_Factor2'].std(ddof=0):.3f} | "
            f"{sub['MFNN_R2'].mean():.3f} ± {sub['MFNN_R2'].std(ddof=0):.3f} |\n"
        )
    lines.append("\n## 逐 seed（MFNN）\n\n")
    lines.append("| seed | w | MAPE% | Factor2 | R² | HF_only Fac2 |\n")
    lines.append("|-----:|--:|------:|--------:|---:|-------------:|\n")
    for _, r in df.sort_values(["seed", "w_anchor"]).iterrows():
        lines.append(
            f"| {int(r['seed'])} | {r['w_anchor']:g} | {r['MFNN_MAPE_pct']:.2f} | "
            f"{r['MFNN_Factor2']:.3f} | {r['MFNN_R2']:.3f} | {r['HF_only_Factor2']:.3f} |\n"
        )
    # judgment vs w=1
    w1 = df[np.isclose(df["w_anchor"], 1.0)]
    w10 = df[np.isclose(df["w_anchor"], 10.0)]
    lines.append("\n## 判读\n\n")
    if len(w1) and len(w10):
        f1, f10 = float(w1["MFNN_Factor2"].mean()), float(w10["MFNN_Factor2"].mean())
        m1, m10 = float(w1["MFNN_MAPE_pct"].mean()), float(w10["MFNN_MAPE_pct"].mean())
        if f10 >= 0.5 and m10 < 100:
            lines.append(
                f"- **重加权有效**：w=1 → w=10 时 MFNN Factor2 {f1:.3f} → {f10:.3f}，"
                f"MAPE {m1:.1f}% → {m10:.1f}%。支持「未加权 MSE 中锚点被邻域淹没」假设；"
                "仍属 SI 诊断，**不是** LOGO 协议成功。\n"
            )
        else:
            lines.append(
                f"- **重加权未充分恢复**：w=10 时 MAPE {m10:.1f}% / Factor2 {f10:.3f}"
                f"（相对 w=1 的 {m1:.1f}% / {f1:.3f}）。"
                "即便提高锚点权重，共享 y_L 的同成分 inter 冲突或邻域尺度统治仍可能压制局部校准"
                "（与 B2 事后截距平移形成对照）。\n"
            )
    lines.append("\n- Protocol W：**未改动**。无架构修改。\n")
    lines.append("\n## 文件\n\n")
    lines.append("- `scripts/run_al80_anchor_upweight_k2.py`\n")
    lines.append("- `outputs/results/AL80_anchor_upweight_k2.csv`\n")
    lines.append("- `outputs/results/AL80_anchor_upweight_k2_REPORT.md`\n")
    path.write_text("".join(lines), encoding="utf-8")
    print(f"[wrote] {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=str, default="0,1,2,42,123")
    ap.add_argument("--weights", type=str, default="5,10", help="w_anchor values to train (w=1 from B CSV)")
    args = ap.parse_args()
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    weights = [float(x) for x in args.weights.split(",") if x.strip()]

    out = ROOT / "outputs"
    results = out / "results"
    results.mkdir(parents=True, exist_ok=True)
    folds_root = out / "al80_anchor_upweight_folds"
    folds_root.mkdir(exist_ok=True)

    csv_path = ensure_training_csv(str(ROOT / "data"))
    df = load_csv(csv_path)
    df_lf = df[df["fidelity"].astype(str).str.upper() == "LF"].reset_index(drop=True)
    df_hf = df[df["fidelity"].astype(str).str.upper() == "HF"].reset_index(drop=True)
    df_hold = df_hf[df_hf["comp_group"].astype(str) == HOLDOUT].reset_index(drop=True)

    rows = []
    # w=1 baseline from existing B
    b_csv = results / "AL80_tracer_anchor_sensitivity.csv"
    if b_csv.is_file():
        bdf = pd.read_csv(b_csv)
        for seed in seeds:
            sub = bdf[(bdf["seed"] == seed) & (bdf["mode"] == "k2")]
            if len(sub) == 0:
                continue
            r = sub.iloc[0]
            rows.append(
                {
                    "seed": seed,
                    "mode": "k2",
                    "w_anchor": 1.0,
                    "n_anchor": int(r["n_anchor"]),
                    "n_upweighted_in_train": 0,
                    "n_test": int(r["n_test"]),
                    "anchor_T_K": r["anchor_T_K"],
                    "LF_only_MAPE_pct": float(r["LF_only_MAPE_pct"]),
                    "LF_only_Factor2": float(r["LF_only_Factor2"]),
                    "LF_only_R2": float(r["LF_only_R2"]),
                    "LF_only_n": int(r["LF_only_n"]),
                    "HF_only_MAPE_pct": float(r["HF_only_MAPE_pct"]),
                    "HF_only_Factor2": float(r["HF_only_Factor2"]),
                    "HF_only_R2": float(r["HF_only_R2"]),
                    "HF_only_n": int(r["HF_only_n"]),
                    "MFNN_MAPE_pct": float(r["MFNN_MAPE_pct"]),
                    "MFNN_Factor2": float(r["MFNN_Factor2"]),
                    "MFNN_R2": float(r["MFNN_R2"]),
                    "MFNN_n": int(r["MFNN_n"]),
                    "source": "B_baseline_csv",
                }
            )

    for seed in seeds:
        for w in weights:
            row = run_one(df_lf, df_hf, df_hold, seed, w, folds_root)
            row["source"] = "trained"
            rows.append(row)

    df_out = pd.DataFrame(rows)
    csv_out = results / "AL80_anchor_upweight_k2.csv"
    df_out.to_csv(csv_out, index=False)
    print(f"[wrote] {csv_out}")
    write_report(df_out, results / "AL80_anchor_upweight_k2_REPORT.md")
    print("[DONE] B1 upweight — Protocol W untouched.")


if __name__ == "__main__":
    main()
