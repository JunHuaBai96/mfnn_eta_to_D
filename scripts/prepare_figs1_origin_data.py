r"""Prepare the FROZEN Fig. S1 Origin data (Protocol W residual-MFNN mixing weights).

SI diagnostic of the five within_T checkpoint alphas -- NOT a headline result,
NOT PINN/PPINN, NOT a LOGO-success claim.

Rules obeyed here:
  * the ten bar heights are hardcoded EXACTLY from the prompt table (raw float64
    values, never rounded before drawing);
  * the two dashed lines sit at the FROZEN DISPLAY means 0.5369 / 0.6525
    (_style.py FROZEN["alpha1"]=(0.5369,0.1200), FROZEN["alpha2"]=(0.6525,0.0301));
    the population (ddof=0) stds 0.1200 / 0.0301 are caption facts only -- NO number
    box, NO error bar is drawn in the figure;
  * outputs/results/protocol_W_alpha_table.csv is read ONLY as a read-only
    cross-check: seeds {0,1,2,42,123} columns alpha_1/alpha_2.  The 5-seed means must
    reproduce 0.5368839383125306 / 0.6524791240692138 (round 4 = frozen display) and
    the ddof=0 stds must reproduce 0.12004888099169429 / 0.03012236319782594;
    ddof=1 (0.1342 / 0.0337) must NOT match the frozen display.
  * nothing is re-extracted: scripts/extract_mfnn_alphas.py and
    scripts/publish_figures/generate_p0_gemini.py are NEVER run.

Writes outputs/origin_data/figs1_alpha_bars.csv and outputs/origin_data/figs1_data_meta.json
"""
import os, csv, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
os.makedirs(OD, exist_ok=True)

# ---- frozen per-seed bar heights (hardcoded from the prompt table, raw precision) ----
SEEDS = [0, 1, 2, 42, 123]                       # left-to-right order on the category axis
XC    = [0.0, 1.0, 2.0, 3.0, 4.0]                # EQUALLY SPACED centres, NOT numeric seeds
A1    = [0.4708741307258606, 0.5989418029785156, 0.3363686800003052,
         0.6021012663841248, 0.6761338114738464]
A2    = [0.6265072822570801, 0.6315324306488037, 0.7088405489921570,
         0.6377006173133850, 0.6578147411346436]
# ---- frozen DISPLAY values for the two dashed lines (_style.py FROZEN, ddof=0) ----
MEAN1, STD1 = 0.5369, 0.1200                     # FROZEN["alpha1"]
MEAN2, STD2 = 0.6525, 0.0301                     # FROZEN["alpha2"]

with open(os.path.join(OD, "figs1_alpha_bars.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["group", "seed", "x_center", "alpha_1", "alpha_2"])
    for i in range(5):
        cw.writerow([i + 1, SEEDS[i], XC[i], repr(A1[i]), repr(A2[i])])

# ---- read-only provenance cross-check (five seeds only) ----
import pandas as pd
d = pd.read_csv(os.path.join(B, "outputs", "results", "protocol_W_alpha_table.csv"))
q = d[d["seed"].isin(SEEDS) & (d["protocol"] == "within_T")].sort_values("seed")
q = q.set_index("seed")
chk = []
for i, s in enumerate(SEEDS):
    r = q.loc[s]
    assert float(r["alpha_1"]) == A1[i], (s, r["alpha_1"], A1[i])
    assert float(r["alpha_2"]) == A2[i], (s, r["alpha_2"], A2[i])
    chk.append(dict(seed=int(s), alpha_1=A1[i], alpha_2=A2[i]))
m1 = float(q.loc[SEEDS, "alpha_1"].mean()); m2 = float(q.loc[SEEDS, "alpha_2"].mean())
s01 = float(q.loc[SEEDS, "alpha_1"].std(ddof=0)); s02 = float(q.loc[SEEDS, "alpha_2"].std(ddof=0))
s11 = float(q.loc[SEEDS, "alpha_1"].std(ddof=1)); s12 = float(q.loc[SEEDS, "alpha_2"].std(ddof=1))
assert round(m1, 16) == 0.5368839383125306, m1
assert round(m2, 16) == 0.6524791240692138, m2
assert abs(s01 - 0.12004888099169429) < 1e-15, s01
assert abs(s02 - 0.03012236319782594) < 1e-15, s02
assert round(m1, 4) == MEAN1 and round(m2, 4) == MEAN2
assert round(s01, 4) == STD1 and round(s02, 4) == STD2
assert round(s11, 4) != STD1 and round(s12, 4) != STD2          # ddof=1 must NOT be the display std

meta = {
    "figure": "Fig. S1 (matplotlib stem FigS1_alpha_mixing_weights)",
    "role": "SI diagnostic of the residual-MFNN mixing weights alpha_1 (linear) / alpha_2 "
            "(nonlinear residual) at five within_T checkpoints (seeds 0,1,2,42,123); "
            "NOT a headline result, NOT PINN/PPINN, NOT a LOGO-success claim",
    "bars": [{"group": i + 1, "seed": SEEDS[i], "x_center": XC[i],
              "alpha_1": A1[i], "alpha_2": A2[i]} for i in range(5)],
    "frozen_display": {"alpha1_mean": MEAN1, "alpha1_std_pop_ddof0": STD1,
                       "alpha2_mean": MEAN2, "alpha2_std_pop_ddof0": STD2,
                       "source": "scripts/publish_figures/_style.py FROZEN['alpha1'], FROZEN['alpha2'] "
                                 "(NOT FROZEN['S1_MAPE'], which belongs to the current Fig. S3)"},
    "drawn": ["ten bars (raw per-seed values, alpha_1 left / alpha_2 right in each group)",
              "two horizontal dashed guide lines at 0.5369 and 0.6525"],
    "never_drawn": ["mean+/-std number box (the matplotlib defect being fixed)",
                    "error bars", "a two-bar mean summary", "LF/HF comparison bars",
                    "PINN/PPINN/LOGO wording", "a sixth group"],
    "provenance": {"csv": "outputs/results/protocol_W_alpha_table.csv",
                   "seeds": SEEDS,
                   "never_run": ["scripts/extract_mfnn_alphas.py",
                                 "scripts/publish_figures/generate_p0_gemini.py",
                                 "scripts/publish_figures/generate_p2_gemini.py",
                                 "scripts/publish_figures/generate_all.py"]},
    "read_only_crosscheck": {"per_seed": chk,
                             "mean_alpha1": m1, "mean_alpha2": m2,
                             "std_ddof0_alpha1": s01, "std_ddof0_alpha2": s02,
                             "std_ddof1_NOT_used_alpha1": s11, "std_ddof1_NOT_used_alpha2": s12},
    "geometry": {"x_centers": XC, "bar_width_du": 0.38,
                 "xlim": [-0.618, 4.618], "ylim": [0.0, 1.05],
                 "yticks": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                 "note": "xlim/ylim measured off the frozen matplotlib PDF (29.2265..234.6231 pt frame, "
                         "39.2305 pt per category unit, 135.04 pt per weight unit)"},
    "recomputed": False,
}
with open(os.path.join(OD, "figs1_data_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1, ensure_ascii=False)

print("per-seed exact CSV match for", SEEDS)
print("mean a1 %.16f -> frozen %.4f ; mean a2 %.16f -> frozen %.4f" % (m1, MEAN1, m2, MEAN2))
print("ddof0 std a1 %.16f -> %.4f ; a2 %.16f -> %.4f" % (s01, STD1, s02, STD2))
print("ddof1 std (NOT used) a1 %.4f ; a2 %.4f" % (s11, s12))
print("DONE_FIGS1_DATA")
