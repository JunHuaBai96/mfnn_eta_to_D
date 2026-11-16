#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pair measured/assessed viscosity onto HF (and document) rows.

Sources (NO Kozlov / Kaptay model fills):
1. Assael et al. JPCRD 35 (2006) DOI:10.1063/1.2149380 — pure liquid Al
   log10(η/mPa·s) = -0.7324 + 803.49/T
2. Schick, Brillo, Egry, Hallstedt, J Mater Sci 47 (2012) 8145–8152
   DOI:10.1007/s10853-012-6710-x — Al–Cu Arrhenius η∞, EA (Table 1)
3. Chen Fig.3a / Fig.8 digitized experimental η already in LF rows
   (used only as same_comp_diff_T / fig_digitize fallback when Schick unavailable)

Does NOT invent D or η. Leaves blank when no honest match.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
R_GAS = 8.314462618

# Assael 2006
ASSAEL_A1 = 0.7324
ASSAEL_A2 = 803.49
ASSAEL_T_MIN = 933.0
ASSAEL_T_MAX = 1270.0

# Schick et al. 2012 Table 1: η = η∞_mPa * exp(EA_J / (R T))
# EA column in paper is J/mol (verified: reproduces Table 2 η(1500 K)).
# Duplicate xCu=0.1 rows averaged.
SCHICK_ALCU: Dict[float, Tuple[float, float]] = {
    0.0: (0.257, 13100.0),
    0.1: ((0.305 + 0.380) / 2.0, (16014.0 + 15640.0) / 2.0),  # avg of two runs
    0.2: (0.358, 13203.0),
    0.3: (0.233, 23630.0),
    0.5: ((0.228 + 0.169) / 2.0, (33058.0 + 33873.0) / 2.0),
    0.6: (0.195, 40666.0),
    0.7: (0.229, 37789.0),
    0.8: (0.316, 34089.0),
    0.9: (0.517, 25409.0),
    1.0: (0.520, 23570.0),
}


def assael_eta_Pas(T: float) -> float:
    return (10.0 ** (-ASSAEL_A1 + ASSAEL_A2 / float(T))) * 1e-3


def schick_eta_Pas(eta_inf_mPa: float, EA_J: float, T: float) -> float:
    return float(eta_inf_mPa * 1e-3 * math.exp(EA_J / (R_GAS * float(T))))


def schick_params_at_xCu(x_Cu: float) -> Tuple[float, float, str]:
    """Return (η∞_mPa, EA_J, interp_note). Linear in ln(η∞) and EA between table knots."""
    xs = sorted(SCHICK_ALCU.keys())
    if x_Cu in SCHICK_ALCU:
        e, ea = SCHICK_ALCU[x_Cu]
        return e, ea, f"exact_table_xCu={x_Cu}"
    # exact float match tolerance
    for x in xs:
        if abs(x_Cu - x) < 1e-6:
            e, ea = SCHICK_ALCU[x]
            return e, ea, f"exact_table_xCu={x}"
    if x_Cu < xs[0] or x_Cu > xs[-1]:
        raise ValueError(f"x_Cu={x_Cu} outside Schick table")
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        if x0 <= x_Cu <= x1:
            t = (x_Cu - x0) / (x1 - x0)
            e0, ea0 = SCHICK_ALCU[x0]
            e1, ea1 = SCHICK_ALCU[x1]
            ln_e = (1 - t) * math.log(e0) + t * math.log(e1)
            ea = (1 - t) * ea0 + t * ea1
            return math.exp(ln_e), ea, f"lin_interp_ln_eta_inf_and_EA between xCu={x0} and {x1}"
    raise ValueError(f"no bracket for x_Cu={x_Cu}")


def is_pure_al(row: pd.Series) -> bool:
    return float(row.get("x_Al", 0) or 0) >= 0.999


def is_alcu_binary(row: pd.Series) -> bool:
    """Al–Cu binary with negligible other solutes (not ternary Ag/Ce/Ni/Mg/Si)."""
    if str(row["system"]) != "Al-Cu":
        return False
    others = sum(float(row.get(c, 0) or 0) for c in ["x_Ce", "x_Ni", "x_Ag", "x_Mg", "x_Si"])
    return others < 1e-6 and float(row.get("x_Cu", 0) or 0) > 1e-6


def pair_eta_for_row(
    row: pd.Series,
    fig3a_eta_by_xCu: Dict[float, float],
) -> Dict[str, Any]:
    """Decide eta fill for one row that currently lacks eta_Pas (or always re-tag HF)."""
    out = {
        "eta_Pas_filled": np.nan,
        "eta_source": "",
        "eta_T_K_source": np.nan,
        "eta_match_rule": "",
        "eta_confidence": "",
        "eta_fill_notes": "",
    }
    T = float(row["T_K"])
    system = str(row["system"])

    # --- Pure Al (incl. impurity-diffusion rows with x_Al≈1) ---
    if is_pure_al(row):
        eta = assael_eta_Pas(T)
        in_range = ASSAEL_T_MIN <= T <= ASSAEL_T_MAX
        out.update(
            eta_Pas_filled=eta,
            eta_source="Assael_et_al_JPCRD_2006_DOI_10.1063/1.2149380",
            eta_T_K_source=T,
            eta_match_rule="Assael_pure_Al" if in_range else "Assael_pure_Al_extrapolated",
            eta_confidence="high" if in_range else "medium",
            eta_fill_notes=(
                f"log10(eta/mPa·s)=-0.7324+803.49/T; T={T} K; "
                + ("within Assael cited range ~933–1270 K" if in_range else
                   f"T outside Assael range [{ASSAEL_T_MIN},{ASSAEL_T_MAX}] — extrapolation")
            ),
        )
        return out

    # --- Al–Cu binary alloys: Schick 2012 Arrhenius at row T ---
    if is_alcu_binary(row):
        x_Cu = float(row["x_Cu"])
        try:
            e_inf, EA, note = schick_params_at_xCu(x_Cu)
        except ValueError as exc:
            out["eta_fill_notes"] = f"Schick unavailable: {exc}"
            return out
        eta = schick_eta_Pas(e_inf, EA, T)
        exact = "exact_table" in note
        # Prefer Schick over Fig.3a because it gives η at the diffusion T
        out.update(
            eta_Pas_filled=eta,
            eta_source="Schick_Brillo_Egry_Hallstedt_JMaterSci_2012_Table1_DOI_10.1007/s10853-012-6710-x",
            eta_T_K_source=T,
            eta_match_rule="Schick2012_Arrhenius" if exact else "Schick2012_Arrhenius_interp",
            eta_confidence="high" if exact else "medium",
            eta_fill_notes=(
                f"eta=eta_inf*exp(EA/(R*T)); eta_inf={e_inf:.5g} mPa·s; EA={EA:.5g} J/mol; "
                f"x_Cu={x_Cu}; {note}. Experimental oscillating-cup Arrhenius (not Kozlov)."
            ),
        )
        return out

    # --- Al–Ag–Cu: no honest same-comp η at 973 K without Brillo HTHP table ---
    if system == "Al-Ag-Cu":
        out["eta_fill_notes"] = (
            "LEFT BLANK: HF/LF at Al68.6Ag17.6Cu13.8 / 973 K. Chen Fig.8 η is Al-10Ag-(0–90)Cu "
            "at 1220 K (Ag mole fraction and T both mismatch). Brillo HTHP 37 (2008) primary "
            "table not available as numbers here — do not use Kozlov."
        )
        out["eta_match_rule"] = "none_honest_match"
        out["eta_confidence"] = ""
        return out

    # --- A356 / other Al–Mg–Si alloys: no Assael (not pure); no digitized alloy η table ---
    if system == "Al-Mg-Si":
        out["eta_fill_notes"] = (
            "LEFT BLANK: A356 / alloy HF-LF without measured η on same composition. "
            "Pure-Al Assael not applied (x_Al<0.999). No honest experimental η(T) table in-repo."
        )
        out["eta_match_rule"] = "none_honest_match"
        return out

    # --- Al–Ce–Ni true alloys: Griesche η not extracted; leave blank ---
    if system == "Al-Ce-Ni":
        out["eta_fill_notes"] = (
            "LEFT BLANK: true Al–Ce–Ni alloy (not pure-Al Ni-tracer). "
            "Do not fabricate Griesche table; Fig.9 D digitize is low confidence separately."
        )
        out["eta_match_rule"] = "none_honest_match"
        return out

    out["eta_fill_notes"] = "LEFT BLANK: no matching rule"
    out["eta_match_rule"] = "none_honest_match"
    return out


def build_fig3a_lookup(prov: pd.DataFrame) -> Dict[float, float]:
    """Experimental Chen Fig.3a η at 1573 K (exclude Kozlov line)."""
    m = prov[
        (prov["source_fig_or_table"].astype(str).str.contains("Fig.3a", na=False))
        & (~prov["source_fig_or_table"].astype(str).str.contains("Kozlov", na=False))
        & prov["eta_Pas"].notna()
        & (prov["system"] == "Al-Cu")
    ]
    # prefer first occurrence per x_Cu
    lut: Dict[float, float] = {}
    for _, r in m.iterrows():
        x = round(float(r["x_Cu"]), 4)
        if x not in lut:
            lut[x] = float(r["eta_Pas"])
    return lut


def main() -> None:
    prov_path = DATA / "melt_diffusion_data_filled_with_provenance.csv"
    prov = pd.read_csv(prov_path)
    fig3a = build_fig3a_lookup(prov)
    print("Fig.3a experimental x_Cu → eta:", fig3a)

    # Columns to add (correct dtypes)
    if "eta_source" not in prov.columns:
        prov["eta_source"] = pd.Series([pd.NA] * len(prov), dtype="string")
    else:
        prov["eta_source"] = prov["eta_source"].astype("string")
    if "eta_T_K_source" not in prov.columns:
        prov["eta_T_K_source"] = np.nan
    prov["eta_T_K_source"] = pd.to_numeric(prov["eta_T_K_source"], errors="coerce")
    for col in ["eta_match_rule", "eta_confidence", "eta_fill_notes"]:
        if col not in prov.columns:
            prov[col] = pd.Series([pd.NA] * len(prov), dtype="string")
        else:
            prov[col] = prov[col].astype("string")

    fill_log = []
    for idx, row in prov.iterrows():
        had_eta = pd.notna(row["eta_Pas"])
        # Only fill when eta missing; keep existing LF measured/digitized η
        if had_eta:
            # Tag existing experimental/digitized eta provenance lightly if empty
            if not str(row["eta_source"] if pd.notna(row.get("eta_source")) else "").strip():
                src = str(row.get("source_fig_or_table") or "")
                if "Fig.3a" in src and "Kozlov" not in src:
                    prov.at[idx, "eta_source"] = "Chen2014_Fig3a_digitize_exp"
                    prov.at[idx, "eta_T_K_source"] = float(row["T_K"])
                    prov.at[idx, "eta_match_rule"] = "fig_digitize"
                    prov.at[idx, "eta_confidence"] = str(row.get("confidence") or "medium")
                    prov.at[idx, "eta_fill_notes"] = "Pre-existing LF η from Chen Fig.3a experimental digitize; T matches row T (1573 K)."
                elif "Fig.8" in src:
                    prov.at[idx, "eta_source"] = "Chen2014_Fig8_digitize_exp_Brillo"
                    prov.at[idx, "eta_T_K_source"] = float(row["T_K"])
                    prov.at[idx, "eta_match_rule"] = "fig_digitize"
                    prov.at[idx, "eta_confidence"] = str(row.get("confidence") or "medium")
                    prov.at[idx, "eta_fill_notes"] = "Pre-existing LF η from Chen Fig.8 (Brillo Al-Ag-Cu) digitize at 1220 K."
                elif "Assael" in str(row.get("notes") or "") or "Assael" in src:
                    prov.at[idx, "eta_source"] = "preexisting_Assael_style_LF"
                    prov.at[idx, "eta_T_K_source"] = float(row["T_K"])
                    # leave values as stored (slightly below official Assael); do not overwrite
                    prov.at[idx, "eta_match_rule"] = "Assael_style_preexisting"
                    prov.at[idx, "eta_confidence"] = str(row.get("confidence") or "medium")
                    prov.at[idx, "eta_fill_notes"] = (
                        "Pre-existing LF Assael-style η kept as-is (differs ~7–9% from Assael 2006 formula); "
                        "not overwritten. Official Assael used only for newly filled HF pure-Al rows."
                    )
                elif "Kozlov" in src:
                    prov.at[idx, "eta_source"] = "Chen2014_Fig3a_Kozlov_model_line"
                    prov.at[idx, "eta_T_K_source"] = float(row["T_K"])
                    prov.at[idx, "eta_match_rule"] = "model_line_kept_as_LF_feature"
                    prov.at[idx, "eta_confidence"] = "medium"
                    prov.at[idx, "eta_fill_notes"] = (
                        "WARNING: this LF η is paper Kozlov model curve sample, NOT measured. "
                        "Kept only as LF feature already in dataset; NEVER used to fill HF."
                    )
            continue

        decision = pair_eta_for_row(row, fig3a)
        fill_log.append({"sample_id": row["sample_id"], "fidelity": row["fidelity"], **decision})
        if pd.notna(decision["eta_Pas_filled"]):
            prov.at[idx, "eta_Pas"] = float(decision["eta_Pas_filled"])
        if decision.get("eta_T_K_source") is not None and pd.notna(decision.get("eta_T_K_source")):
            prov.at[idx, "eta_T_K_source"] = float(decision["eta_T_K_source"])
        for k in ["eta_source", "eta_match_rule", "eta_confidence", "eta_fill_notes"]:
            v = decision.get(k, "")
            prov.at[idx, k] = "" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)

    # Save full paired provenance-style file
    train_cols = [
        "sample_id", "system", "fidelity", "diff_type", "diff_species", "solvent_species",
        "T_K", "x_Al", "x_Cu", "x_Ce", "x_Ni", "x_Ag", "x_Mg", "x_Si",
        "eta_Pas", "D_m2s", "comp_group", "is_placeholder",
    ]
    prov_extra = [
        "source_paper", "source_fig_or_table", "digitize_method", "confidence", "notes",
        "eta_source", "eta_T_K_source", "eta_match_rule", "eta_confidence", "eta_fill_notes",
    ]
    paired_full = prov[train_cols + prov_extra].copy()
    out_full = DATA / "melt_diffusion_data_eta_paired.csv"
    paired_full.to_csv(out_full, index=False)

    # high/medium only
    hm = paired_full[paired_full["confidence"].isin(["high", "medium"])].copy()
    out_hm = DATA / "melt_diffusion_data_eta_paired_highmed.csv"
    hm.to_csv(out_hm, index=False)

    # Backup + replace training CSV with highmed training columns only
    old = DATA / "melt_diffusion_data.csv"
    backup = DATA / "melt_diffusion_data_before_eta_pair.csv"
    if old.exists() and not backup.exists():
        backup.write_bytes(old.read_bytes())
    elif old.exists():
        # always refresh backup from current if we haven't paired yet; keep first backup
        pass
    if not backup.exists():
        backup.write_bytes(old.read_bytes())
    hm[train_cols].to_csv(old, index=False)

    # Also write a training-ready highmed that DROPS rows still missing eta
    # (train.py / data.py will drop NaN eta; keep full highmed with blanks documented)
    usable = hm[hm["eta_Pas"].notna()].copy()
    usable_path = DATA / "melt_diffusion_data_eta_paired_highmed_usable.csv"
    usable[train_cols].to_csv(usable_path, index=False)

    # --- Report ---
    log_df = pd.DataFrame(fill_log)
    hf_all = paired_full[paired_full.fidelity == "HF"]
    hf_hm = hm[hm.fidelity == "HF"]

    def rate(df):
        n = len(df)
        filled = int(df["eta_Pas"].notna().sum())
        return filled, n, (100.0 * filled / n if n else 0.0)

    lines = []
    lines.append("# η pairing report / 黏度配对报告\n")
    lines.append("## Goal\n")
    lines.append("Fill **measured / assessed** viscosity into HF rows that lacked `eta_Pas`, ")
    lines.append("with explicit provenance. **No Kozlov/Kaptay model η** used for HF fills.\n")
    lines.append("\n## Sources used\n")
    lines.append("| Source | What | DOI / link |\n|--------|------|------------|\n")
    lines.append("| Assael et al. 2006 | Pure liquid Al reference η(T) | 10.1063/1.2149380 |\n")
    lines.append("| Schick et al. 2012 Table 1 | Al–Cu Arrhenius η∞, EA (oscillating cup) | 10.1007/s10853-012-6710-x |\n")
    lines.append("| Chen 2014 Fig.3a / Fig.8 (pre-existing LF) | Digitized experimental η kept on LF rows | paper figures |\n")
    lines.append("| Brillo HTHP 37 (2008) Al–Ag–Cu | **Numbers not obtained** — R030 left blank | cite only |\n")
    lines.append("\nAssael formula: `log10(η/mPa·s) = -0.7324 + 803.49/T` (T in K); η_Pa·s = η_mPa·s × 10⁻³.\n")
    lines.append("Schick: `η = η∞ exp(EA/(R T))` with η∞ in mPa·s, EA in J/mol (Table 1; verified vs their Table 2 at 1500 K).\n")

    lines.append("\n## Output files\n")
    lines.append(f"- `{out_full}` — full provenance + eta_* columns ({len(paired_full)} rows)\n")
    lines.append(f"- `{out_hm}` — confidence ∈ {{high,medium}} ({len(hm)} rows)\n")
    lines.append(f"- `{usable_path}` — highmed with eta present only ({len(usable)} rows)\n")
    lines.append(f"- `{old}` — replaced by highmed training columns (backup: `{backup.name}`)\n")

    lines.append("\n## Counts by system × fidelity (highmed)\n")
    lines.append("| System | HF | LF | HF η filled | LF η present |\n|--------|----|----|-------------|-------------|\n")
    for sys in sorted(hm["system"].unique()):
        sub = hm[hm.system == sys]
        hf = sub[sub.fidelity == "HF"]
        lf = sub[sub.fidelity == "LF"]
        lines.append(
            f"| {sys} | {len(hf)} | {len(lf)} | {hf.eta_Pas.notna().sum()}/{len(hf)} | {lf.eta_Pas.notna().sum()}/{len(lf)} |\n"
        )

    f_hm, n_hm, p_hm = rate(hf_hm)
    lines.append(f"\n**HF highmed fill rate:** {f_hm}/{n_hm} = {p_hm:.1f}%\n")

    lines.append("\n## HF fills by eta_match_rule (highmed)\n")
    lines.append("| eta_match_rule | n | systems |\n|----------------|---|--------|\n")
    filled_hf = hf_hm[hf_hm.eta_Pas.notna()]
    if len(filled_hf):
        for rule, g in filled_hf.groupby("eta_match_rule"):
            lines.append(f"| {rule} | {len(g)} | {', '.join(sorted(g.system.unique()))} |\n")

    lines.append("\n## Remaining HF with empty η (highmed)\n")
    empty_hf = hf_hm[hf_hm.eta_Pas.isna()]
    if empty_hf.empty:
        lines.append("None.\n")
    else:
        lines.append("| sample_id | system | T_K | comp_group | why |\n|-----------|--------|-----|------------|-----|\n")
        for _, r in empty_hf.iterrows():
            why = str(r.get("eta_fill_notes") or "")[:120].replace("|", "/")
            lines.append(f"| {r.sample_id} | {r.system} | {r.T_K} | {r.comp_group} | {why} |\n")

    lines.append("\n## HF fill detail (highmed)\n")
    lines.append("| sample_id | system | T_K | x_Cu | eta_Pas | rule | conf |\n|-----------|--------|-----|------|---------|------|------|\n")
    for _, r in hf_hm.sort_values(["system", "sample_id"]).iterrows():
        eta = f"{r.eta_Pas:.6g}" if pd.notna(r.eta_Pas) else "EMPTY"
        lines.append(
            f"| {r.sample_id} | {r.system} | {r.T_K} | {r.x_Cu} | {eta} | {r.eta_match_rule} | {r.eta_confidence} |\n"
        )

    lines.append("\n## Still empty LF (highmed) — not fabricated\n")
    empty_lf = hm[(hm.fidelity == "LF") & hm.eta_Pas.isna()]
    lines.append(f"n={len(empty_lf)} (Al–Ag–Cu calculated D rows + A356 Tang Fig.4 without η).\n")
    for _, r in empty_lf.iterrows():
        lines.append(f"- {r.sample_id} {r.system} T={r.T_K} {r.comp_group}: {r.eta_fill_notes}\n")

    lines.append("\n## Numbers NOT found / not used\n")
    lines.append("- Brillo et al. HTHP 37 (2008) Al–Ag–Cu viscosity **table numbers** (PDF paywalled / not digitized here).\n")
    lines.append("- Griesche Al–Ce–Ni primary viscosity table.\n")
    lines.append("- Gebhardt / Jones–Bartlett / Lihl historical Al–Cu η tables (Schick supersedes for this work).\n")
    lines.append("- Any Kozlov/Kaptay η for HF pairing (explicitly forbidden).\n")

    lines.append("\n## Multi-system training expectation\n")
    lines.append(
        f"Usable highmed rows with η: {len(usable)} "
        f"(HF={int((usable.fidelity=='HF').sum())}, LF={int((usable.fidelity=='LF').sum())}).\n"
    )
    lines.append("Systems in usable set:\n")
    for sys, g in usable.groupby("system"):
        lines.append(f"- {sys}: n={len(g)} (HF={(g.fidelity=='HF').sum()}, LF={(g.fidelity=='LF').sum()})\n")
    lines.append(
        "Al–Ag–Cu HF R030 remains without η → dropped from feature matrix unless η later filled from Brillo.\n"
        "Al–Ce–Ni in highmed is pure-Al Ni-tracer only (Assael η) — true alloy Fig.9 stays low-confidence excluded.\n"
    )

    lines.append("\n## Leakage note\n")
    lines.append(
        "Schick η(T) for Al–Cu HF is **independent experimental viscosity**, not the Kozlov η used to build "
        "some LF Sutherland D rows. Pure-Al Assael η is the same family as Tang 'converted from viscosity' LF, "
        "but HF D (Kargl/Demmel/Du) are measured diffusivities — pairing η is physically motivated for Stokes–Einstein features.\n"
    )

    report_path = DATA / "eta_fill_report.md"
    report_path.write_text("".join(lines), encoding="utf-8")
    print("Wrote", out_full)
    print("Wrote", out_hm)
    print("Wrote", usable_path)
    print("Wrote", report_path)
    print("Replaced", old, "(backup", backup, ")")
    print("HF highmed fill:", f_hm, "/", n_hm)
    print("Empty HF highmed:", list(empty_hf.sample_id))
    print("Usable systems:\n", usable.groupby(["system", "fidelity"]).size())


if __name__ == "__main__":
    main()
