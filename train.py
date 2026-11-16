# -*- coding: utf-8 -*-
"""
train.py
Train LF-only / HF-only / Residual MFNN (Adam -> L-BFGS) on the curated CSV tables.
"""

from __future__ import annotations
import os
import random
from typing import Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from data import (
    NUM_FEATURES,
    FeatureStandardizer,
    build_feature_matrix,
    ensure_training_csv,
    load_csv,
    split_by_comp_group,
    split_within_group_T,
)
from model import ResidualMFNN, SingleFidelityNN
from eval import evaluate_by_system
from plot import plot_all_figures


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _to_device_free(*tensors):
    return tensors  # CPU smoke test


def train_single_fidelity_baseline(
    X_tr: torch.Tensor,
    y_tr: torch.Tensor,
    X_val: torch.Tensor,
    y_val: torch.Tensor,
    width: int = 64,
    depth: int = 3,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    adam_epochs: int = 800,
    lbfgs_steps: int = 50,
) -> SingleFidelityNN:
    in_dim = X_tr.shape[1] if X_tr.ndim == 2 and X_tr.shape[0] > 0 else NUM_FEATURES
    model = SingleFidelityNN(in_dim=in_dim, width=width, depth=depth)
    if X_tr.shape[0] == 0:
        return model
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = nn.MSELoss()
    best_state = None
    best_val = float("inf")
    for _ in range(adam_epochs):
        model.train()
        opt.zero_grad()
        pred = model(X_tr)
        loss = loss_fn(pred, y_tr)
        loss.backward()
        opt.step()
        if X_val.shape[0] > 0:
            model.eval()
            with torch.no_grad():
                v = loss_fn(model(X_val), y_val).item()
            if v < best_val:
                best_val = v
                best_state = {k: v_.detach().clone() for k, v_ in model.state_dict().items()}
    if best_state is not None:
        model.load_state_dict(best_state)

    # L-BFGS polish
    model.train()
    opt2 = torch.optim.LBFGS(model.parameters(), lr=0.5, max_iter=20, history_size=20, line_search_fn="strong_wolfe")

    def closure():
        opt2.zero_grad()
        pred = model(X_tr)
        loss = loss_fn(pred, y_tr)
        loss.backward()
        return loss

    for _ in range(max(1, lbfgs_steps // 20)):
        try:
            opt2.step(closure)
        except RuntimeError:
            break
    return model


def train_residual_mfnn(
    X_tr_lf: torch.Tensor,
    y_tr_lf: torch.Tensor,
    X_tr_hf: torch.Tensor,
    y_tr_hf: torch.Tensor,
    phys_tr_hf: torch.Tensor,
    X_val_hf: torch.Tensor,
    y_val_hf: torch.Tensor,
    width: int = 64,
    lr: float = 1e-3,
    adam_epochs: int = 1000,
    lbfgs_steps: int = 40,
    lambda_phys: float = 0.05,
    lambda_lf: float = 1.0,
    lambda_hf: float = 1.0,
) -> ResidualMFNN:
    in_dim = (
        X_tr_lf.shape[1]
        if X_tr_lf.shape[0] > 0
        else (X_tr_hf.shape[1] if X_tr_hf.shape[0] > 0 else NUM_FEATURES)
    )
    model = ResidualMFNN(in_dim=in_dim, width=width)
    if X_tr_lf.shape[0] == 0 and X_tr_hf.shape[0] == 0:
        return model

    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.MSELoss()
    best_state = None
    best_val = float("inf")

    for _ in range(adam_epochs):
        model.train()
        opt.zero_grad()
        loss = torch.tensor(0.0)
        if X_tr_lf.shape[0] > 0:
            pred_lf = model.forward_lf(X_tr_lf)
            loss = loss + lambda_lf * loss_fn(pred_lf, y_tr_lf)
        if X_tr_hf.shape[0] > 0:
            pred_hf = model.forward_hf(X_tr_hf)
            loss = loss + lambda_hf * loss_fn(pred_hf, y_tr_hf)
            # physics residual on HF inputs: pred vs Sutherland log10D
            loss = loss + lambda_phys * loss_fn(pred_hf, phys_tr_hf)
        loss.backward()
        opt.step()

        if X_val_hf.shape[0] > 0:
            model.eval()
            with torch.no_grad():
                v = loss_fn(model.forward_hf(X_val_hf), y_val_hf).item()
            if v < best_val:
                best_val = v
                best_state = {k: v_.detach().clone() for k, v_ in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    # L-BFGS stage on combined objective
    model.train()
    opt2 = torch.optim.LBFGS(model.parameters(), lr=0.4, max_iter=20, history_size=20, line_search_fn="strong_wolfe")

    def closure():
        opt2.zero_grad()
        loss = torch.tensor(0.0, requires_grad=True)
        loss = loss * 0.0
        if X_tr_lf.shape[0] > 0:
            loss = loss + lambda_lf * loss_fn(model.forward_lf(X_tr_lf), y_tr_lf)
        if X_tr_hf.shape[0] > 0:
            pred_hf = model.forward_hf(X_tr_hf)
            loss = loss + lambda_hf * loss_fn(pred_hf, y_tr_hf)
            loss = loss + lambda_phys * loss_fn(pred_hf, phys_tr_hf)
        loss.backward()
        return loss

    for _ in range(max(1, lbfgs_steps // 20)):
        try:
            opt2.step(closure)
        except RuntimeError:
            break
    return model


def _run_one_protocol(
    df_lf: "pd.DataFrame",
    df_hf: "pd.DataFrame",
    protocol: str,
    seed: int,
    out_dir: str,
    make_plots: bool,
) -> "pd.DataFrame":
    """Train LF/HF/MFNN and evaluate under one protocol. protocol in {within_T, between_group}."""
    set_seed(seed)
    os.makedirs(out_dir, exist_ok=True)

    if protocol == "within_T":
        df_tr_hf, df_val_hf, df_te_hf, used = split_within_group_T(df_hf, seed=seed)
        print(f"[Split W] within-group T-holdout groups used for test: {used}")
    elif protocol == "between_group":
        df_tr_hf, df_val_hf, df_te_hf = split_by_comp_group(df_hf, seed=seed)
        used = sorted(df_te_hf["comp_group"].astype(str).unique().tolist())
        print(f"[Split G] leave-comp_group-out test groups: {used}")
    else:
        raise ValueError(f"unknown protocol {protocol}")

    te_groups = set(df_te_hf["comp_group"].astype(str).unique())
    val_groups = set(df_val_hf["comp_group"].astype(str).unique())
    df_tr_lf = df_lf.reset_index(drop=True)
    df_val_lf = df_lf[df_lf["comp_group"].astype(str).isin(val_groups)].reset_index(drop=True)
    if len(df_val_lf) == 0 and len(df_lf) > 0:
        df_val_lf = df_lf.sample(n=min(5, len(df_lf)), random_state=seed).reset_index(drop=True)

    print(f"[Split] protocol={protocol} HF train/val/test = {len(df_tr_hf)}/{len(df_val_hf)}/{len(df_te_hf)}")
    print(f"[Split] LF train/val = {len(df_tr_lf)}/{len(df_val_lf)}")

    if len(df_te_hf) == 0:
        print(f"[Warn] no HF test rows for protocol={protocol}; skip.")
        empty = pd.DataFrame(columns=["system", "model", "MSE", "RMSE", "R2", "MAPE_pct", "Factor2", "n"])
        empty.to_csv(os.path.join(out_dir, "metrics_by_system.csv"), index=False)
        return empty

    X_tr_lf_raw, y_tr_lf, _ = build_feature_matrix(df_tr_lf)
    X_val_lf_raw, y_val_lf, _ = build_feature_matrix(df_val_lf)
    X_tr_hf_raw, y_tr_hf, phys_tr_hf = build_feature_matrix(df_tr_hf)
    X_val_hf_raw, y_val_hf, _ = build_feature_matrix(df_val_hf)
    X_te_hf_raw, y_te_hf, _ = build_feature_matrix(df_te_hf)

    scaler = FeatureStandardizer(num_continuous=NUM_FEATURES).fit(
        np.vstack([X_tr_lf_raw, X_tr_hf_raw]) if len(X_tr_hf_raw) else X_tr_lf_raw
    )

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

    print("[Train] 1/3 LF-only...")
    model_lf = train_single_fidelity_baseline(t_X_tr_lf, t_y_tr_lf, t_X_val_lf, t_y_val_lf)
    print("[Train] 2/3 HF-only...")
    model_hf = train_single_fidelity_baseline(t_X_tr_hf, t_y_tr_hf, t_X_val_hf, t_y_val_hf, weight_decay=5e-3)
    print("[Train] 3/3 Residual MFNN...")
    model_mfnn = train_residual_mfnn(
        t_X_tr_lf, t_y_tr_lf, t_X_tr_hf, t_y_tr_hf, t_phys_tr_hf, t_X_val_hf, t_y_val_hf
    )

    ckpt_path = os.path.join(out_dir, "mfnn_checkpoint.pt")
    torch.save({
        "mfnn_state_dict": model_mfnn.state_dict(),
        "lf_only_state_dict": model_lf.state_dict(),
        "hf_only_state_dict": model_hf.state_dict(),
        "scaler_mean": scaler.mean_,
        "scaler_std": scaler.std_,
        "alpha_1": float(model_mfnn.alpha_1.detach()),
        "alpha_2": float(model_mfnn.alpha_2.detach()),
        "protocol": protocol,
        "seed": seed,
        "test_groups": sorted(te_groups),
    }, ckpt_path)

    model_lf.eval(); model_hf.eval(); model_mfnn.eval()
    with torch.no_grad():
        pred_lf_only = model_lf(t_X_te_hf).numpy()
        pred_hf_only = model_hf(t_X_te_hf).numpy()
        pred_mfnn = model_mfnn.forward_hf(t_X_te_hf).numpy()

    preds_dict = {"LF_only": pred_lf_only, "HF_only": pred_hf_only, "MFNN": pred_mfnn}
    summary_csv = os.path.join(out_dir, "metrics_by_system.csv")
    detail_csv = os.path.join(out_dir, "test_predictions.csv")
    summary_df = evaluate_by_system(df_te_hf, y_te_hf, preds_dict, summary_csv, detail_csv)
    print(f"\n===== Test metrics [{protocol}] =====")
    print(summary_df.to_string(index=False))

    detail_df = pd.read_csv(detail_csv)
    if make_plots:
        # Tag titles via protocol in filenames already separated by folder
        plot_all_figures(detail_df, summary_df, out_dir=out_dir)
    summary_df = summary_df.copy()
    summary_df.insert(0, "seed", seed)
    summary_df.insert(1, "protocol", protocol)
    return summary_df


def _write_eval_summary(out_root: str, within_df: Optional[pd.DataFrame], between_df: Optional[pd.DataFrame]) -> None:
    path = os.path.join(out_root, "EVAL_PROTOCOL_SUMMARY.md")
    lines = []
    lines.append("# Evaluation protocol summary (W vs G)\n\n")
    lines.append("Paper should report **both** protocols. Do not claim LOGO-CV success from W alone.\n\n")
    lines.append("## Protocol W — within-group T-split (interpolation)\n")
    lines.append("- For each `comp_group` with ≥4 HF points spanning T, hold out ~25% of HF by T ")
    lines.append("(prefer lowest/highest T).\n")
    lines.append("- Train on remaining HF + **all LF**.\n")
    lines.append("- Metrics: `outputs/within_T/metrics_by_system.csv` (also copied as `metrics_within_T.csv`).\n")
    lines.append("- Measures temperature interpolation / densification skill, **not** composition extrapolation.\n\n")
    lines.append("## Protocol G — between-group extrapolation (LOGO-style)\n")
    lines.append("- Leave-composition-group-out split on HF (`split_by_comp_group`).\n")
    lines.append("- Metrics: `outputs/between_group/metrics_by_system.csv` (also `metrics_between_group.csv`).\n")
    lines.append("- Measures composition extrapolation; sensitive to which groups are held out.\n\n")

    def _all_mape(df, model="MFNN"):
        if df is None or len(df) == 0:
            return None
        sub = df[(df["system"] == "ALL") & (df["model"] == model)]
        if len(sub) == 0:
            return None
        r = sub.iloc[0]
        return float(r["MAPE_pct"]), float(r["Factor2"]), int(r["n"])

    lines.append("## This run (seed noted in CSVs)\n\n")
    for label, df in [("W within_T", within_df), ("G between_group", between_df)]:
        m = _all_mape(df)
        if m is None:
            lines.append(f"- **{label}**: no metrics\n")
        else:
            mape, f2, n = m
            lines.append(f"- **{label}** MFNN ALL: MAPE={mape:.1f}%, Factor2={f2:.2f}, n={n}\n")
    lines.append("\nCLI: `python train.py --eval both|within_T|between_group [--seed 42]`\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(lines))
    print(f"[Save] {path}")


def main(
    seed: int = 42,
    make_plots: bool = True,
    out_subdir: Optional[str] = None,
    eval_mode: str = "both",
) -> pd.DataFrame:
    set_seed(seed)
    root = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(root, "data")
    out_root = os.path.join(root, "outputs")
    if out_subdir:
        out_root = os.path.join(out_root, out_subdir)
    os.makedirs(out_root, exist_ok=True)

    csv_path = ensure_training_csv(data_dir)
    print(f"[Data] Using CSV: {csv_path} (seed={seed}, eval={eval_mode})")
    df = load_csv(csv_path)
    df_lf = df[df["fidelity"].astype(str).str.upper() == "LF"].reset_index(drop=True)
    df_hf = df[df["fidelity"].astype(str).str.upper() == "HF"].reset_index(drop=True)
    print(f"[Data] LF={len(df_lf)} HF={len(df_hf)} systems={sorted(df['system'].unique().tolist())}")

    modes = []
    if eval_mode == "both":
        modes = ["within_T", "between_group"]
    elif eval_mode in ("within_T", "between_group"):
        modes = [eval_mode]
    else:
        raise ValueError("eval_mode must be within_T | between_group | both")

    within_df = between_df = None
    last = None
    for proto in modes:
        sub = os.path.join(out_root, proto)
        summary = _run_one_protocol(df_lf, df_hf, proto, seed, sub, make_plots)
        last = summary
        # also write canonical names at out_root
        if proto == "within_T":
            within_df = summary
            summary.to_csv(os.path.join(out_root, "metrics_within_T.csv"), index=False)
            # mirror predictions
            src = os.path.join(sub, "test_predictions.csv")
            if os.path.isfile(src):
                import shutil
                shutil.copy2(src, os.path.join(out_root, "test_predictions_within_T.csv"))
        else:
            between_df = summary
            summary.to_csv(os.path.join(out_root, "metrics_between_group.csv"), index=False)
            src = os.path.join(sub, "test_predictions.csv")
            if os.path.isfile(src):
                import shutil
                shutil.copy2(src, os.path.join(out_root, "test_predictions_between_group.csv"))
        # keep backward-compat metrics_by_system as the last run
        summary.to_csv(os.path.join(out_root, "metrics_by_system.csv"), index=False)

    _write_eval_summary(out_root, within_df, between_df)
    print(f"\n[Done] protocol outputs under `{out_root}/`.")
    return last if last is not None else pd.DataFrame()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Train LF/HF/MFNN with W/G eval protocols")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--out-subdir", type=str, default=None, help="optional outputs/<subdir>")
    ap.add_argument(
        "--eval",
        dest="eval_mode",
        type=str,
        default="both",
        choices=["within_T", "between_group", "both"],
        help="Protocol W (within_T), G (between_group), or both (default)",
    )
    args = ap.parse_args()
    main(seed=args.seed, make_plots=not args.no_plots, out_subdir=args.out_subdir, eval_mode=args.eval_mode)
