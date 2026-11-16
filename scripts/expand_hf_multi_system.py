#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Honest multi-system HF densification from published Arrhenius already in Chen/Tang notes.

Adds ONLY:
  - Zhang Cu-tracer Al80Cu20 (Chen Fig.4b / fill_report): D0=1.3e-7, Q=0.34 eV
  - Zhang interdiffusivity Al81.3Cu18.7 (Chen Fig.6 [60]): D0=3.7e-7, Q=0.33 eV
  - Demmel Al self-D (Tang Table1 / Fig.1a medium): Ea=274 meV, D0 anchored to Kargl@1020K

η pairing: Schick 2012 for Al–Cu; Assael 2006 for PureAl. NO Kozlov HF η.

REFUSED (documented, not invented):
  - Chen Fig.9 Al–Ce–Ni alloy clouds (low digitize, no alloy η → unusable)
  - Tang Fig.3b Petrscu Al–Si (low magnitude-estimate, no honest alloy η)
  - Al–Ag–Cu R030 (D known, Brillo η missing)
"""
from __future__ import annotations

import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
R_GAS = 8.314462618
EV_TO_J = 96485.0

# Import Schick / Assael from existing pairing script
import importlib.util

_spec = importlib.util.spec_from_file_location("pair_eta", DATA.parent / "scripts" / "pair_eta_to_hf.py")
_pair = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_pair)


def arrhenius(D0: float, Q_J: float, T: float) -> float:
    return float(D0 * math.exp(-Q_J / (R_GAS * float(T))))


def assael_eta(T: float) -> Tuple[float, str]:
    eta = _pair.assael_eta_Pas(T)
    rule = "Assael_pure_Al"
    if T < _pair.ASSAEL_T_MIN or T > _pair.ASSAEL_T_MAX:
        rule = "Assael_pure_Al_extrapolated"
    return eta, rule


def schick_eta(x_Cu: float, T: float) -> Tuple[float, str, str]:
    e, ea, note = _pair.schick_params_at_xCu(x_Cu)
    eta = _pair.schick_eta_Pas(e, ea, T)
    rule = "Schick2012_Arrhenius" if "exact" in note else "Schick2012_Arrhenius_interp"
    return eta, rule, note


def blank_row_template(base: Dict[str, Any]) -> Dict[str, Any]:
    cols = [
        "sample_id", "system", "fidelity", "diff_type", "diff_species", "solvent_species",
        "T_K", "x_Al", "x_Cu", "x_Ce", "x_Ni", "x_Ag", "x_Mg", "x_Si",
        "eta_Pas", "D_m2s", "comp_group", "is_placeholder",
        "source_paper", "source_fig_or_table", "digitize_method", "confidence", "notes",
        "eta_source", "eta_match_rule", "eta_fill_notes",
    ]
    out = {c: "" for c in cols}
    out.update(base)
    for c in ["x_Al", "x_Cu", "x_Ce", "x_Ni", "x_Ag", "x_Mg", "x_Si"]:
        out.setdefault(c, 0.0)
        if out[c] == "" or out[c] is None:
            out[c] = 0.0
    out["is_placeholder"] = False
    out["fidelity"] = "HF"
    out["solvent_species"] = "Al"
    return out


def existing_keys(df: pd.DataFrame) -> Set[Tuple]:
    keys = set()
    for _, r in df.iterrows():
        keys.add((
            str(r.get("comp_group", "")),
            str(r.get("diff_species", "")),
            str(r.get("fidelity", "")).upper(),
            round(float(r["T_K"]), 1),
            str(r.get("diff_type", "")),
        ))
    return keys


def build_new_rows(existing: Set[Tuple]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    sid = 300  # R300+

    # --- 1) Zhang Cu tracer Al80Cu20 ---
    D0_tr = 1.3e-7
    Q_tr = 0.34 * EV_TO_J
    temps_tr = [983, 1025, 1050, 1075, 1125, 1150, 1200]  # skip 1000,1100,1175 already present
    for T in temps_tr:
        key = ("Al80Cu20", "Cu", "HF", float(T), "tracer")
        if key in existing:
            continue
        eta, rule, note = schick_eta(0.20, T)
        rows.append(blank_row_template({
            "sample_id": f"R{sid:03d}",
            "system": "Al-Cu",
            "diff_type": "tracer",
            "diff_species": "Cu",
            "T_K": float(T),
            "x_Al": 0.80,
            "x_Cu": 0.20,
            "eta_Pas": eta,
            "D_m2s": arrhenius(D0_tr, Q_tr, T),
            "comp_group": "Al80Cu20",
            "source_paper": "Chen2014(+Zhang et al. Cu tracer cited Fig.4/refs); densified Arrhenius",
            "source_fig_or_table": "Chen Fig.4b literature Arrhenius densify",
            "digitize_method": "published_Arrhenius_D0_1.3e-7_Q_0.34eV_T_grid",
            "confidence": "high",
            "notes": (
                "HF densify of Zhang Cu-tracer Arrhenius in Al-20at%Cu "
                "(D0=1.3e-7 m2/s, Q=0.34 eV) already used for R017–R019; η=Schick2012 xCu=0.2."
            ),
            "eta_source": "Schick_Brillo_Egry_Hallstedt_JMaterSci_2012_Table1",
            "eta_match_rule": rule,
            "eta_fill_notes": note,
        }))
        existing.add(key)
        sid += 1

    # --- 2) Zhang interdiffusivity Al81.3Cu18.7 ---
    D0_int = 3.7e-7
    Q_int = 0.33 * EV_TO_J
    temps_int = [1000, 1050, 1100, 1150]  # skip 983,1023,1073,1123,1173
    for T in temps_int:
        key = ("Al81.3Cu18.7", "Cu", "HF", float(T), "inter")
        if key in existing:
            continue
        eta, rule, note = schick_eta(0.187, T)
        rows.append(blank_row_template({
            "sample_id": f"R{sid:03d}",
            "system": "Al-Cu",
            "diff_type": "inter",
            "diff_species": "Cu",
            "T_K": float(T),
            "x_Al": 0.813,
            "x_Cu": 0.187,
            "eta_Pas": eta,
            "D_m2s": arrhenius(D0_int, Q_int, T),
            "comp_group": "Al81.3Cu18.7",
            "source_paper": "Chen2014(+Zhang[60] Arrhenius fit densify)",
            "source_fig_or_table": "Chen Fig.6b Al-18.7at%Cu Arrhenius densify",
            "digitize_method": "published_Arrhenius_D0_3.7e-7_Q_0.33eV_T_grid",
            "confidence": "high",
            "notes": (
                "HF densify of Zhang interdiffusivity Arrhenius Al-18.7at%Cu "
                "(D0=3.7e-7 m2/s, Q=0.33 eV); anchors R020–R024 kept. η=Schick interp xCu=0.187."
            ),
            "eta_source": "Schick_Brillo_Egry_Hallstedt_JMaterSci_2012_Table1",
            "eta_match_rule": rule,
            "eta_fill_notes": note,
        }))
        existing.add(key)
        sid += 1

    # --- 3) Demmel PureAl self-D densify (medium) ---
    Q_dem = 0.274 * EV_TO_J
    D_anchor = 7.9e-9
    T_anchor = 1020.0
    D0_dem = D_anchor / math.exp(-Q_dem / (R_GAS * T_anchor))
    temps_dem = [960, 1000, 1040, 1080, 1120]  # avoid existing Demmel/Kargl T
    for T in temps_dem:
        key = ("PureAl", "Al", "HF", float(T), "self")
        if key in existing:
            continue
        # also skip if any PureAl HF at same T already (Kargl/Demmel)
        conflict = False
        for k in list(existing):
            if k[0] == "PureAl" and k[1] == "Al" and k[2] == "HF" and k[3] == float(T):
                conflict = True
                break
        if conflict:
            continue
        eta, rule = assael_eta(T)
        rows.append(blank_row_template({
            "sample_id": f"R{sid:03d}",
            "system": "Al-Mg-Si",
            "diff_type": "self",
            "diff_species": "Al",
            "T_K": float(T),
            "x_Al": 1.0,
            "eta_Pas": eta,
            "D_m2s": arrhenius(D0_dem, Q_dem, T),
            "comp_group": "PureAl",
            "source_paper": "Tang2015(+Demmel2011 PRB Ea=274 meV; D0 anchored to Kargl@1020K)",
            "source_fig_or_table": "Tang Table1 / Fig.1a (Demmel Arrhenius densify)",
            "digitize_method": "Demmel_Ea_274meV_D0_anchored_Kargl1020_T_grid",
            "confidence": "medium",
            "notes": (
                "Medium HF densify: Demmel Ea=274 meV with D0 fixed so D(1020K)=Kargl 7.9e-9. "
                "Not Demmel raw table; PureAl self-D under Al-Mg-Si pipeline label. η=Assael pure Al."
            ),
            "eta_source": "Assael_JPCRD_2006",
            "eta_match_rule": rule,
            "eta_fill_notes": "pure Al Assael correlation",
        }))
        existing.add(key)
        sid += 1

    return rows


def merge_into(path: Path, new_rows: List[Dict[str, Any]], keep_extra: bool) -> pd.DataFrame:
    df = pd.read_csv(path)
    add = pd.DataFrame(new_rows)
    # align columns
    for c in df.columns:
        if c not in add.columns:
            add[c] = "" if df[c].dtype == object else (False if c == "is_placeholder" else float("nan"))
    add = add.reindex(columns=list(df.columns) + [c for c in add.columns if c not in df.columns], fill_value="")
    # only keep columns that exist in df for lean training csv
    if not keep_extra:
        add = add[[c for c in df.columns]]
    else:
        for c in add.columns:
            if c not in df.columns:
                df[c] = ""
        add = add[df.columns]
    out = pd.concat([df, add], ignore_index=True)
    return out


def write_report(n_new: int, by_sys: Dict[str, int], before: Dict, after: Dict, refused: List[str]) -> None:
    path = DATA / "HF_EXPAND_MULTI_SYSTEM_REPORT.md"
    lines = []
    lines.append("# 真实多体系 HF 扩展报告（诚实 Arrhenius 加密）\n")
    lines.append(f"日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}（箱内 UTC+8）\n")
    lines.append("\n## 新增 HF（仅已发表 Arrhenius 加密 + 诚实 η）\n")
    lines.append(f"- **合计新增：{n_new} 行**（sample_id 自 R300 起）\n")
    for k, v in by_sys.items():
        lines.append(f"- {k}: **{v}**\n")
    lines.append("\n### 明细\n")
    lines.append("| 系列 | 参数 | 新增 T (K) | η | confidence |\n")
    lines.append("|------|------|------------|---|------------|\n")
    lines.append("| Al80Cu20 Cu tracer (Zhang/Chen Fig.4b) | D0=1.3e-7, Q=0.34 eV | 983,1025,1050,1075,1125,1150,1200 | Schick xCu=0.2 | high |\n")
    lines.append("| Al81.3Cu18.7 inter (Zhang/Chen Fig.6) | D0=3.7e-7, Q=0.33 eV | 1000,1050,1100,1150 | Schick interp 0.187 | high |\n")
    lines.append("| PureAl self (Demmel Ea / Tang) | Ea=274 meV, D0@Kargl1020 | 960,1000,1040,1080,1120 | Assael | medium |\n")
    lines.append("\n## 计数前后（high/medium 训练表）\n")
    lines.append("| | 前 | 后 |\n|--|----|----|\n")
    lines.append(f"| 总行 | {before['n']} | {after['n']} |\n")
    lines.append(f"| HF | {before['hf']} | {after['hf']} |\n")
    lines.append(f"| usable(有η) | {before['usable']} | {after['usable']} |\n")
    lines.append(f"| usable HF | {before['usable_hf']} | {after['usable_hf']} |\n")
    lines.append("\n### usable system × fidelity（后）\n\n```\n")
    lines.append(after["usable_table"])
    lines.append("\n```\n")
    lines.append("\n## 刻意拒绝 / 仍阻塞\n\n")
    for r in refused:
        lines.append(f"- {r}\n")
    lines.append("\n## 文件\n")
    lines.append("- `data/melt_diffusion_data.csv`（训练主表）\n")
    lines.append("- `data/melt_diffusion_data_eta_paired_highmed.csv`\n")
    lines.append("- `data/melt_diffusion_data_eta_paired.csv`（全量溯源）\n")
    lines.append("- `data/melt_diffusion_data_eta_paired_highmed_usable.csv`\n")
    lines.append("- 备份：`data/backup_before_hf_expand_20261015_1405/`\n")
    lines.append("- 脚本：`scripts/expand_hf_multi_system.py`\n")
    path.write_text("".join(lines), encoding="utf-8")
    print(f"[report] {path}")


def main() -> None:
    highmed = DATA / "melt_diffusion_data_eta_paired_highmed.csv"
    full = DATA / "melt_diffusion_data_eta_paired.csv"
    train = DATA / "melt_diffusion_data.csv"

    df0 = pd.read_csv(highmed)
    before = {
        "n": len(df0),
        "hf": int((df0.fidelity.astype(str).str.upper() == "HF").sum()),
        "usable": int(pd.to_numeric(df0.eta_Pas, errors="coerce").notna().sum()),
        "usable_hf": int(
            ((df0.fidelity.astype(str).str.upper() == "HF") & pd.to_numeric(df0.eta_Pas, errors="coerce").notna()).sum()
        ),
    }

    keys = existing_keys(df0)
    # also block against train csv keys
    keys |= existing_keys(pd.read_csv(train))
    new_rows = build_new_rows(keys)
    by_sys: Dict[str, int] = {}
    for r in new_rows:
        by_sys[r["system"]] = by_sys.get(r["system"], 0) + 1
    print(f"[expand] new rows={len(new_rows)} by_system={by_sys}")

    # merge into all three CSVs
    df_hm = merge_into(highmed, new_rows, keep_extra=True)
    df_full = merge_into(full, new_rows, keep_extra=True)
    # lean train: only columns of current train csv
    df_tr = pd.read_csv(train)
    add_lean = pd.DataFrame(new_rows)
    for c in df_tr.columns:
        if c not in add_lean.columns:
            add_lean[c] = False if c == "is_placeholder" else ("" if df_tr[c].dtype == object else float("nan"))
    add_lean = add_lean[df_tr.columns]
    df_tr2 = pd.concat([df_tr, add_lean], ignore_index=True)

    df_hm.to_csv(highmed, index=False)
    df_full.to_csv(full, index=False)
    df_tr2.to_csv(train, index=False)
    # also sync after_ni_lf style snapshot
    shutil.copy(train, DATA / "melt_diffusion_data_after_hf_expand.csv")

    usable = df_hm[pd.to_numeric(df_hm.eta_Pas, errors="coerce").notna()].copy()
    # usable lean cols
    lean_cols = list(df_tr.columns)
    usable[lean_cols].to_csv(DATA / "melt_diffusion_data_eta_paired_highmed_usable.csv", index=False)

    after = {
        "n": len(df_hm),
        "hf": int((df_hm.fidelity.astype(str).str.upper() == "HF").sum()),
        "usable": len(usable),
        "usable_hf": int((usable.fidelity.astype(str).str.upper() == "HF").sum()),
        "usable_table": usable.groupby(["system", "fidelity"]).size().unstack(fill_value=0).to_string(),
    }
    refused = [
        "Chen Fig.9 Griesche Al–Ce–Ni **合金**云图：仍为 low digitize（±0.15–0.25 log10），且无合金实验 η → 升 medium 也无法进入 usable；**未升档、未编造**。",
        "Tang Fig.3b Petrscu Al–12.2at%Si：原文无绝对 D 表，现有为 magnitude-estimate low；无诚实 Al–Si η；**未升档**。",
        "Al–Ag–Cu R030：D=4.4e-9 已知，Brillo 2008 η 表数字仍缺；**η 继续空白，未 Kozlov 填**。",
        "未把 Fe/Mn/Zn 杂质（Chen Table3）拉进四体系管线（超出当前 system 标签）。",
        "Fig.6a 其它成分（Al95Cu5 等）仅有 983 K 数字化点，无发表 Arrhenius → **未编造 T 序列**。",
    ]
    write_report(len(new_rows), by_sys, before, after, refused)
    print("[done] usable HF", after["usable_hf"], "total usable", after["usable"])
    print(after["usable_table"])


if __name__ == "__main__":
    main()
