# -*- coding: utf-8 -*-
"""
data.py
CSV loading, anti-leakage split by composition group, Z-score standardization,
and four-system placeholder dataset generation (NOT real experimental values).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import os
import numpy as np
import pandas as pd

from physics import (
    kozlov_alloy_viscosity,
    physics_from_row,
    sutherland_diffusivity,
    effective_radius_ri,
    beta_from_size_ratio,
)

COMP_COLS = ["x_Al", "x_Cu", "x_Ce", "x_Ni", "x_Ag", "x_Mg", "x_Si"]
# Physics/composition block (z-scored) + diff_type one-hot (left as 0/1).
NUM_PHYS = 12  # T, 1/T, eta, log10(eta), 7 comps, r_diff
# Ordered one-hot: tracer | inter | impurity | other (self + unknown)
DIFFTYPE_ONEHOT_ORDER = ("tracer", "inter", "impurity", "other")
NUM_DIFFTYPE = len(DIFFTYPE_ONEHOT_ORDER)  # 4
NUM_FEATURES = NUM_PHYS + NUM_DIFFTYPE  # 16
NUM_CONTINUOUS = NUM_FEATURES  # backward-compat alias for total feature dim


def _species_onehot(name: str) -> List[float]:
    order = ["Al", "Cu", "Ce", "Ni", "Ag", "Mg", "Si"]
    return [1.0 if name == s else 0.0 for s in order]


def diff_type_onehot(diff_type: str) -> List[float]:
    """One-hot over DIFFTYPE_ONEHOT_ORDER. interdiffusivity→inter; self→other."""
    t = normalize_diff_type_label(diff_type)
    if t == "self" or t not in ("tracer", "inter", "impurity"):
        key = "other"
    else:
        key = t
    return [1.0 if key == k else 0.0 for k in DIFFTYPE_ONEHOT_ORDER]


def build_feature_matrix(
    df: pd.DataFrame,
    include_difftype_onehot: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (X, y_log10D, phys_log10D).

    Columns 0–11: T, 1000/T, eta, log10(eta), 7 comps, r_diff (Angstrom).
    If include_difftype_onehot: columns 12–15 one-hot [tracer, inter, impurity, other].
    For single-type pools, set include_difftype_onehot=False (12-D, no redundancy).
    """
    n_feat = NUM_FEATURES if include_difftype_onehot else NUM_PHYS
    if len(df) == 0:
        return (
            np.zeros((0, n_feat), dtype=np.float64),
            np.zeros((0,), dtype=np.float64),
            np.zeros((0,), dtype=np.float64),
        )
    rows_X, rows_y, rows_p = [], [], []
    for _, row in df.iterrows():
        T = float(row["T_K"])
        if pd.isna(row["eta_Pas"]):
            continue  # skip; load_csv should already have dropped these
        eta = float(row["eta_Pas"])
        if not np.isfinite(eta) or eta <= 0:
            continue
        comps = [float(row[c]) for c in COMP_COLS]
        r_d = effective_radius_ri(T, str(row["diff_species"]))
        feat = [
            T,
            1000.0 / max(T, 1.0),
            eta,
            float(np.log10(max(eta, 1e-12))),
            *comps,  # 7
            r_d * 1e10,  # Angstrom-scale
        ]
        if include_difftype_onehot:
            dt = (
                str(row["diff_type"])
                if "diff_type" in row.index and pd.notna(row["diff_type"])
                else "other"
            )
            feat.extend(diff_type_onehot(dt))
        assert len(feat) == n_feat
        D = float(row["D_m2s"])
        y = float(np.log10(max(D, 1e-30)))
        phys = physics_from_row(T, eta, str(row["diff_species"]), str(row.get("solvent_species", "Al")))
        rows_X.append(feat)
        rows_y.append(y)
        rows_p.append(phys.log10_D_phys)
    return np.asarray(rows_X, dtype=np.float64), np.asarray(rows_y, dtype=np.float64), np.asarray(rows_p, dtype=np.float64)


@dataclass
class FeatureStandardizer:
    """Z-score physics/composition columns only; leave diff_type one-hot as 0/1."""

    num_continuous: int = NUM_FEATURES  # total dim (compat)
    num_phys: int = NUM_PHYS
    mean_: Optional[np.ndarray] = None
    std_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> "FeatureStandardizer":
        X = np.asarray(X, dtype=np.float64)
        dim = X.shape[1] if X.ndim == 2 and X.size else self.num_continuous
        self.mean_ = np.zeros(dim)
        self.std_ = np.ones(dim)
        if X.size == 0:
            return self
        n_phys = min(self.num_phys, dim)
        self.mean_[:n_phys] = X[:, :n_phys].mean(axis=0)
        self.std_[:n_phys] = X[:, :n_phys].std(axis=0)
        self.std_[:n_phys][self.std_[:n_phys] < 1e-8] = 1.0
        # one-hot block: mean=0, std=1 (identity)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        assert self.mean_ is not None and self.std_ is not None
        return (np.asarray(X, dtype=np.float64) - self.mean_) / self.std_


DIFFTYPE_SUFFIXES = ("_tracer", "_inter", "_impurity", "_self")


def normalize_diff_type_label(diff_type: str) -> str:
    """Map raw diff_type to LOGO suffix family. interdiffusivity -> inter; impurity stays impurity."""
    t = str(diff_type).strip().lower()
    if t in ("interdiffusivity", "inter_diff", "inter-diffusion", "interdiffusion"):
        return "inter"
    if t in ("impurity", "tracer", "inter", "self"):
        return t
    return t


def _strip_difftype_suffix(name: str) -> str:
    s = str(name)
    for suf in DIFFTYPE_SUFFIXES:
        if s.endswith(suf):
            return s[: -len(suf)]
    return s


def apply_comp_group_difftype_split(df: pd.DataFrame) -> pd.DataFrame:
    """Rewrite comp_group to base_diffType so tracer/inter labels do not collide.

    - Al-Cu: always append _{normalized_diff_type} (impurity kept as _impurity, never merged into tracer/inter).
    - Other systems: only when the same base group mixes multiple normalized types.
    - Hold-out labels only here; feature one-hot is built separately in build_feature_matrix.
    """
    out = df.copy()
    if "diff_type" not in out.columns:
        return out
    if "comp_group_base" not in out.columns:
        out["comp_group_base"] = out["comp_group"].astype(str).map(_strip_difftype_suffix)
    else:
        out["comp_group_base"] = out["comp_group_base"].astype(str).map(_strip_difftype_suffix)

    # Which (system, base) need splitting?
    need: set = set()
    for (sys, base), sub in out.groupby(
        [out["system"].astype(str), out["comp_group_base"].astype(str)]
    ):
        types = {normalize_diff_type_label(t) for t in sub["diff_type"].astype(str)}
        if str(sys) == "Al-Cu" or len(types) > 1:
            need.add((str(sys), str(base)))

    new_names = []
    for _, row in out.iterrows():
        sys = str(row["system"])
        base = str(row["comp_group_base"])
        norm = normalize_diff_type_label(row.get("diff_type", "unknown"))
        if (sys, base) in need:
            new_names.append(f"{base}_{norm}")
        else:
            new_names.append(base)
    out["comp_group"] = new_names
    return out


def load_csv(path: str, drop_missing_eta: bool = True) -> pd.DataFrame:
    """Load training CSV.

    Rows with missing eta_Pas are dropped by default so features stay finite.
    We do NOT silently impute Kozlov/Kaptay viscosity for training — pair measured/
    assessed η offline (see data/eta_fill_report.md) before training.
    """
    df = pd.read_csv(path)
    required = ["system", "fidelity", "T_K", "eta_Pas", "D_m2s", "comp_group", "diff_species"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")
    for c in COMP_COLS:
        if c not in df.columns:
            df[c] = 0.0
    if "solvent_species" not in df.columns:
        df["solvent_species"] = "Al"
    if drop_missing_eta:
        n0 = len(df)
        df = df[pd.to_numeric(df["eta_Pas"], errors="coerce").notna()].reset_index(drop=True)
        n1 = len(df)
        if n1 < n0:
            print(f"[data.load_csv] dropped {n0 - n1} rows with missing eta_Pas (kept {n1}/{n0})")
    return df



def split_within_group_T(
    df: pd.DataFrame,
    seed: int = 42,
    holdout_frac: float = 0.25,
    min_points: int = 3,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, List[str]]:
    """Protocol W: within-comp_group temperature holdout (interpolation).

    For each comp_group with >= min_points HF rows spanning T, hold out
    ~holdout_frac of rows by T (prefer extremes + random mid). Groups with
    fewer points stay entirely in train. Returns train/val/test HF frames and
    list of groups that contributed test points.
    """
    rng = np.random.default_rng(seed)
    tr_parts, va_parts, te_parts = [], [], []
    used_groups: List[str] = []
    for g, sub in df.groupby(df["comp_group"].astype(str), sort=True):
        sub = sub.sort_values("T_K").reset_index(drop=True)
        n = len(sub)
        if n < min_points or sub["T_K"].nunique() < 2:
            tr_parts.append(sub)
            continue
        n_te = max(1, int(round(n * holdout_frac)))
        n_te = min(n_te, n - 2)  # leave >=2 for train
        # Prefer one lowest, one highest, then random remaining
        idx = list(range(n))
        pick = []
        if n_te >= 1:
            pick.append(idx[0])
        if n_te >= 2:
            pick.append(idx[-1])
        mid = [i for i in idx if i not in pick]
        rng.shuffle(mid)
        while len(pick) < n_te and mid:
            pick.append(mid.pop())
        te_idx = set(pick)
        # small val: one mid train point if enough left
        remain = [i for i in idx if i not in te_idx]
        va_idx = set()
        if len(remain) >= 3:
            va_idx.add(remain[len(remain)//2])
        tr_idx = [i for i in remain if i not in va_idx]
        tr_parts.append(sub.iloc[tr_idx])
        if va_idx:
            va_parts.append(sub.iloc[sorted(va_idx)])
        te_parts.append(sub.iloc[sorted(te_idx)])
        used_groups.append(str(g))

    def _cat(parts):
        if not parts:
            return df.iloc[:0].copy()
        return pd.concat(parts, ignore_index=True)

    return _cat(tr_parts), _cat(va_parts), _cat(te_parts), used_groups


def split_by_comp_group(
    df: pd.DataFrame,
    seed: int = 42,
    train_frac: float = 0.6,
    val_frac: float = 0.2,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Leave-composition-group split to reduce leakage across T points of same alloy."""
    rng = np.random.default_rng(seed)
    groups = sorted(df["comp_group"].astype(str).unique().tolist())
    rng.shuffle(groups)
    n = len(groups)
    if n == 1:
        # fall back: random row split if only one group
        idx = np.arange(len(df))
        rng.shuffle(idx)
        n_tr = max(1, int(len(df) * train_frac))
        n_va = max(1, int(len(df) * val_frac)) if len(df) > 2 else 0
        tr = df.iloc[idx[:n_tr]]
        va = df.iloc[idx[n_tr:n_tr + n_va]] if n_va else df.iloc[idx[:0]]
        te = df.iloc[idx[n_tr + n_va:]] if (n_tr + n_va) < len(df) else df.iloc[idx[-1:]]
        return tr.reset_index(drop=True), va.reset_index(drop=True), te.reset_index(drop=True)

    n_tr = max(1, int(round(n * train_frac)))
    n_va = max(1, int(round(n * val_frac))) if n >= 3 else 0
    if n_tr + n_va >= n:
        n_va = max(0, n - n_tr - 1)
    g_tr = set(groups[:n_tr])
    g_va = set(groups[n_tr:n_tr + n_va])
    g_te = set(groups[n_tr + n_va:]) or {groups[-1]}
    # ensure test non-empty and disjoint
    g_te = g_te - g_tr - g_va
    if not g_te:
        # move one from train
        move = next(iter(g_tr))
        g_tr.remove(move)
        g_te.add(move)

    def _sel(gs):
        return df[df["comp_group"].astype(str).isin(gs)].reset_index(drop=True)

    return _sel(g_tr), _sel(g_va), _sel(g_te)


def _row(
    sid: str,
    system: str,
    fidelity: str,
    diff_type: str,
    diff_species: str,
    T: float,
    comps: Dict[str, float],
    eta: float,
    D: float,
    comp_group: str,
) -> dict:
    base = {c: 0.0 for c in COMP_COLS}
    for k, v in comps.items():
        key = f"x_{k}" if not k.startswith("x_") else k
        if key in base:
            base[key] = float(v)
    return {
        "sample_id": sid,
        "system": system,
        "fidelity": fidelity,
        "diff_type": diff_type,
        "diff_species": diff_species,
        "solvent_species": "Al",
        "T_K": float(T),
        **base,
        "eta_Pas": float(eta),
        "D_m2s": float(D),
        "comp_group": comp_group,
        "is_placeholder": True,
    }


def generate_placeholder_dataset(seed: int = 42, n_lf_per_group: int = 12) -> pd.DataFrame:
    """Synthesize four-system placeholder LF/HF tables at realistic orders of magnitude.

    IMPORTANT: All values are placeholders for pipeline smoke tests, not literature data.
    Replace with Chen 2014 / Tang 2015 extracted tables for real experiments.
    """
    rng = np.random.default_rng(seed)
    rows: List[dict] = []
    sid = 1

    configs = [
        # system, diff_type, species, groups of (label, comps)
        ("Al-Cu", "tracer", "Cu", [
            ("Al80Cu20", {"Al": 0.80, "Cu": 0.20}),
            ("Al90Cu10", {"Al": 0.90, "Cu": 0.10}),
            ("Al70Cu30", {"Al": 0.70, "Cu": 0.30}),
            ("Al81.3Cu18.7", {"Al": 0.813, "Cu": 0.187}),
        ]),
        ("Al-Ce-Ni", "tracer", "Ni", [
            ("Al87Ce3Ni10", {"Al": 0.87, "Ce": 0.03, "Ni": 0.10}),
            ("Al77Ce3Ni20", {"Al": 0.77, "Ce": 0.03, "Ni": 0.20}),
            ("Al82Ce5Ni13", {"Al": 0.82, "Ce": 0.05, "Ni": 0.13}),
        ]),
        ("Al-Ag-Cu", "inter", "Ag", [
            ("Al68.6Ag17.6Cu13.8", {"Al": 0.686, "Ag": 0.176, "Cu": 0.138}),
            ("Al75Ag15Cu10", {"Al": 0.75, "Ag": 0.15, "Cu": 0.10}),
            ("Al80Ag10Cu10", {"Al": 0.80, "Ag": 0.10, "Cu": 0.10}),
        ]),
        ("Al-Mg-Si", "tracer", "Si", [
            ("PureAl", {"Al": 1.0}),
            ("Al87.8Si12.2", {"Al": 0.878, "Si": 0.122}),
            ("Al90Mg5Si5", {"Al": 0.90, "Mg": 0.05, "Si": 0.05}),
            ("Al95Mg5", {"Al": 0.95, "Mg": 0.05}),
        ]),
    ]

    for system, diff_type, species, groups in configs:
        for gname, comps in groups:
            T_grid = np.linspace(950.0, 1450.0, n_lf_per_group)
            for T in T_grid:
                eta = kozlov_alloy_viscosity(float(T), comps)
                # mild systematic bias on LF vs a "true" HF generator
                r_d = effective_radius_ri(float(T), species)
                r_s = effective_radius_ri(float(T), "Al")
                beta = beta_from_size_ratio(r_d, r_s)
                D_true = sutherland_diffusivity(float(T), eta, r_d, beta=beta, r_solvent=r_s)
                # LF: physics + small noise
                D_lf = D_true * float(np.exp(rng.normal(0.0, 0.08)))
                rows.append(_row(
                    f"L{sid:04d}", system, "LF", diff_type, species,
                    float(T), comps, eta, D_lf, gname,
                ))
                sid += 1
            # fewer HF points
            T_hf = np.linspace(980.0, 1400.0, 4)
            for T in T_hf:
                eta = kozlov_alloy_viscosity(float(T), comps)
                r_d = effective_radius_ri(float(T), species)
                r_s = effective_radius_ri(float(T), "Al")
                beta = beta_from_size_ratio(r_d, r_s)
                D_true = sutherland_diffusivity(float(T), eta, r_d, beta=beta, r_solvent=r_s)
                # HF: different bias (simulate experiment vs formula mismatch)
                D_hf = D_true * float(np.exp(rng.normal(-0.12, 0.05))) * 1.15
                rows.append(_row(
                    f"H{sid:04d}", system, "HF", diff_type if species != "Al" else "self",
                    species if gname != "PureAl" else "Al",
                    float(T), comps, eta, D_hf, gname,
                ))
                sid += 1

    df = pd.DataFrame(rows)
    return df


def ensure_training_csv(
    data_dir: str,
    prefer_placeholder_template: bool = False,
) -> str:
    """Write melt_diffusion_data.csv if missing; return path."""
    out = os.path.join(data_dir, "melt_diffusion_data.csv")
    template = os.path.join(data_dir, "melt_diffusion_placeholder_16rows.csv")
    if os.path.isfile(out) and not prefer_placeholder_template:
        return out
    if prefer_placeholder_template and os.path.isfile(template):
        df = load_csv(template)
    else:
        df = generate_placeholder_dataset()
    os.makedirs(data_dir, exist_ok=True)
    df.to_csv(out, index=False)
    return out
