# -*- coding: utf-8 -*-
"""
eval.py
Per-system metrics in log space (MSE, RMSE, R^2) and physical space (MAPE, Factor-of-2).
"""

from __future__ import annotations
from typing import Dict
import numpy as np
import pandas as pd


def _metrics(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> Dict[str, float]:
    y_true_log = np.asarray(y_true_log, dtype=float).ravel()
    y_pred_log = np.asarray(y_pred_log, dtype=float).ravel()
    if len(y_true_log) == 0:
        return {"MSE": np.nan, "RMSE": np.nan, "R2": np.nan, "MAPE_pct": np.nan, "Factor2": np.nan}
    err = y_pred_log - y_true_log
    mse = float(np.mean(err ** 2))
    rmse = float(np.sqrt(mse))
    ss_res = float(np.sum(err ** 2))
    ss_tot = float(np.sum((y_true_log - np.mean(y_true_log)) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 1e-16 else float("nan")
    D_t = 10.0 ** y_true_log
    D_p = 10.0 ** y_pred_log
    mape = float(np.mean(np.abs(D_p - D_t) / np.clip(np.abs(D_t), 1e-30, None)) * 100.0)
    ratio = D_p / np.clip(D_t, 1e-30, None)
    fac2 = float(np.mean((ratio >= 0.5) & (ratio <= 2.0)))
    return {"MSE": mse, "RMSE": rmse, "R2": r2, "MAPE_pct": mape, "Factor2": fac2}


def evaluate_by_system(
    df_te: pd.DataFrame,
    y_te_log: np.ndarray,
    preds_dict: Dict[str, np.ndarray],
    summary_csv: str,
    detail_csv: str,
) -> pd.DataFrame:
    y_te_log = np.asarray(y_te_log, dtype=float).ravel()
    detail = df_te.reset_index(drop=True).copy()
    detail["y_true_log10D"] = y_te_log
    detail["D_true"] = 10.0 ** y_te_log
    for name, pred in preds_dict.items():
        pred = np.asarray(pred, dtype=float).ravel()
        detail[f"pred_{name}_log10D"] = pred
        detail[f"pred_{name}_D"] = 10.0 ** pred

    rows = []
    systems = sorted(detail["system"].astype(str).unique().tolist())
    for sys in systems + ["ALL"]:
        mask = np.ones(len(detail), dtype=bool) if sys == "ALL" else (detail["system"].astype(str) == sys).to_numpy()
        for name, pred in preds_dict.items():
            pred = np.asarray(pred, dtype=float).ravel()
            m = _metrics(y_te_log[mask], pred[mask])
            rows.append({"system": sys, "model": name, **m, "n": int(mask.sum())})
    summary = pd.DataFrame(rows)
    summary.to_csv(summary_csv, index=False)
    detail.to_csv(detail_csv, index=False)
    return summary
