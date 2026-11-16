"""Prepare the Fig.2 Origin workbook data (phase-space coverage + D-vs-eta panel).

House twin of prepare_fig6_origin_data.py.  NOTHING is re-derived here beyond what
scripts/publish_figures/generate_p1_gemini.py::fig2_phase_space_coverage() already
does with the same frozen inputs:

  * source      : data/melt_diffusion_data_eta_paired_highmed_usable.csv, fidelity == HF
  * panel (a)   : Al-Cu rows by diff_type vs x_Cu (at.%);  other systems vs the total
                  non-Al solute fraction (x_Cu+x_Ce+x_Ni+x_Ag+x_Mg+x_Si), marker "x"
  * panel (b)   : every HF row by diff_type, eta_Pas vs D_m2s, PLUS the modified
                  Sutherland low-fidelity prior D_phys evaluated at the SAME
                  (T, eta, species) rows, PLUS the pure-Al T=1000 K guide curve on the
                  same eta grid as the reference script.
  * panel (b) is emitted in log10 coordinates (u = log10 eta, v = log10 D) so the
    Origin axes are plain linear axes, exactly as in the Fig.6 panel-A recipe.

Frozen numbers are untouched; this file only reshapes existing rows.
"""
import os, csv, json
import numpy as np
import pandas as pd
import sys

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
sys.path.insert(0, B)
from physics import physics_from_row                      # noqa: E402

OD = os.path.join(B, "outputs", "origin_data")
os.makedirs(OD, exist_ok=True)

SOLUTES = ["x_Cu", "x_Ce", "x_Ni", "x_Ag", "x_Mg", "x_Si"]
MODALITIES = ["tracer", "inter", "impurity", "self"]
SPARSE_SYSTEMS = ["Al-Ce-Ni", "Al-Mg-Si", "Al-Ag-Cu"]

df = pd.read_csv(os.path.join(B, "data", "melt_diffusion_data_eta_paired_highmed_usable.csv"))
hf = df[df.fidelity == "HF"].copy()
hf["x_solute"] = hf[SOLUTES].sum(axis=1) * 100.0

def w(name, header, rows):
    with open(os.path.join(OD, name), "w", newline="", encoding="utf-8") as f:
        cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)
    return len(rows)

def num(v):
    return "%.10f" % float(v)

# ---------------------------------------------------------------- panel (a)
a_counts = {}
alu = hf[hf.system == "Al-Cu"]
for dt in MODALITIES:
    sub = alu[alu.diff_type == dt].sort_values(["x_Cu", "T_K"])
    a_counts[dt] = w("fig2_a_%s.csv" % dt, ["x", "y"],
                     [(num(r.x_Cu * 100.0), num(r.T_K)) for r in sub.itertuples()])
for sysname in SPARSE_SYSTEMS:
    sub = hf[hf.system == sysname].sort_values(["x_solute", "T_K"])
    a_counts[sysname] = w("fig2_a_%s.csv" % sysname.lower().replace("-", ""),
                          ["x", "y"], [(num(r.x_solute), num(r.T_K)) for r in sub.itertuples()])

# ---------------------------------------------------------------- panel (b)
b_counts = {}
for dt in MODALITIES:
    sub = hf[hf.diff_type == dt].sort_values("eta_Pas")
    b_counts[dt] = w("fig2_b_%s.csv" % dt, ["x", "y"],
                     [(num(np.log10(r.eta_Pas)), num(np.log10(r.D_m2s))) for r in sub.itertuples()])

pr_u, pr_v = [], []
for r in hf.itertuples():
    if not (np.isfinite(r.eta_Pas) and r.eta_Pas > 0 and np.isfinite(r.D_m2s)):
        continue
    solvent = str(r.solvent_species) if pd.notna(r.solvent_species) else "Al"
    phys = physics_from_row(float(r.T_K), float(r.eta_Pas), str(r.diff_species), solvent)
    pr_u.append(float(r.eta_Pas)); pr_v.append(float(phys.D_phys))
order = np.argsort(pr_u)
b_counts["prior"] = w("fig2_b_prior.csv", ["x", "y"],
                      [(num(np.log10(pr_u[i])), num(np.log10(pr_v[i]))) for i in order])

# guide: identical grid and identical formula to the reference script
eta_line = np.logspace(np.log10(max(hf.eta_Pas.min() * 0.9, 1e-4)),
                       np.log10(hf.eta_Pas.max() * 1.05), 50)
d_guide = np.array([physics_from_row(1000.0, float(e), "Al", "Al").D_phys for e in eta_line])
gu, gv = np.log10(eta_line), np.log10(d_guide)
lin = np.polyfit(gu, gv, 1)
resid = np.abs(np.polyval(lin, gu) - gv).max()
b_counts["guide"] = w("fig2_b_guide.csv", ["x", "y"], [(num(a), num(b)) for a, b in zip(gu, gv)])

meta = {
    "n_HF_rows": int(len(hf)),
    "panel_a_counts": a_counts,
    "panel_b_counts": b_counts,
    "panel_a_x_range": [float(hf.x_Cu.min() * 100.0), float(hf.x_solute.max())],
    "panel_a_T_range": [float(hf.T_K.min()), float(hf.T_K.max())],
    "panel_b_u_range": [float(np.log10(hf.eta_Pas.min())), float(np.log10(hf.eta_Pas.max()))],
    "panel_b_v_exp_range": [float(np.log10(hf.D_m2s.min())), float(np.log10(hf.D_m2s.max()))],
    "panel_b_v_prior_range": [float(np.log10(min(pr_v))), float(np.log10(max(pr_v)))],
    "guide_slope_in_loglog": float(lin[0]),
    "guide_max_resid_pt": float(resid),
    "guide_u_range": [float(gu[0]), float(gu[-1])],
    "guide_v_range": [float(gv.min()), float(gv.max())],
    "sparse_systems_present": [s for s in SPARSE_SYSTEMS if a_counts.get(s, 0) > 0],
    "al_cu_modalities_present": [d for d in MODALITIES if a_counts.get(d, 0) > 0],
}
with open(os.path.join(OD, "fig2_data_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1)
print(json.dumps(meta, indent=1))
