r"""Prepare the FROZEN Fig. S3 Origin workbook data (Al80Cu20 tracer few-shot anchor-k).

SI diagnostic of sparse-neighborhood failure -- k>0 is NOT pure LOGO, NOT a Protocol W
success claim, not PINN/PPINN.

Rules obeyed here:
  * the four bar heights are the frozen DISPLAY values, written literally
    (scripts/publish_figures/_style.py FROZEN["S1_MAPE"] = (178.20, 169.55, 175.27, 142.93);
    the "S1_" key name is the OLD numbering when this figure was still called S1 --
    it IS the current Fig. S3 data, do not confuse it with the current Fig. S1 alphas);
  * the error bars are the hardcoded 5-seed POPULATION std (ddof=0) from the prompt table,
    never ddof=1;
  * outputs/results/AL80_tracer_anchor_sensitivity.csv is read ONLY as a read-only
    provenance cross-check: seeds {0,1,2,42,123} x modes {k0,k1_lowT,k1_highT,k2},
    column MFNN_MAPE_pct.  5-seed means must reproduce 178.203941 / 169.552872 /
    175.266241 / 142.930116 and the ddof=0 stds must match the hardcoded error bars.
    All 20 MFNN_Factor2 values are exactly 0 (reported in the caption only, NEVER drawn).
  * generate_p2_gemini.py is NEVER run.

Writes outputs/origin_data/figs3_bars.csv and outputs/origin_data/figs3_data_meta.json
"""
import os, csv, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
os.makedirs(OD, exist_ok=True)

# ---- frozen display values (hardcoded; the only numbers allowed on the figure) ----
X      = [0.0, 1.0, 2.0, 3.0]                       # bar centres (matplotlib x = np.arange(4))
VAL    = [178.20, 169.55, 175.27, 142.93]           # FROZEN["S1_MAPE"] (old numbering = Fig. S3)
LAB    = ["178.2", "169.6", "175.3", "142.9"]       # one decimal, rounded from the frozen values
ERR    = [29.053385, 35.509400, 32.925206, 35.532553]  # 5-seed POPULATION std, ddof=0, hardcoded
CAT    = ["k = 0", "k = 1 low T", "k = 1 high T", "k = 2"]
MODES  = ["k0", "k1_lowT", "k1_highT", "k2"]
MEANS6 = [178.203941, 169.552872, 175.266241, 142.930116]   # prompt cross-check targets

with open(os.path.join(OD, "figs3_bars.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["x", "value", "err_popstd_ddof0", "bar_label", "category"])
    for i in range(4):
        cw.writerow([X[i], "%.2f" % VAL[i], "%.6f" % ERR[i], LAB[i], CAT[i]])

# ---- read-only provenance cross-check (five seeds, MFNN_MAPE_pct only) ----
import pandas as pd
d = pd.read_csv(os.path.join(B, "outputs", "results", "AL80_tracer_anchor_sensitivity.csv"))
seeds = [0, 1, 2, 42, 123]
chk = []
for i, m in enumerate(MODES):
    q = d[(d["mode"] == m) & (d["seed"].isin(seeds))].sort_values("seed")
    assert len(q) == 5, (m, len(q))
    v = q["MFNN_MAPE_pct"]
    mean, sd0, sd1 = float(v.mean()), float(v.std(ddof=0)), float(v.std(ddof=1))
    assert round(mean, 6) == MEANS6[i], (m, mean)
    assert round(mean, 2) == VAL[i], (m, mean, VAL[i])
    assert abs(sd0 - ERR[i]) < 5e-7, (m, sd0, ERR[i])
    assert abs(round(mean, 2) - 169.55) > 1e-9 or abs(sd1 - 39.700716) < 1e-6  # ddof=1 must NOT be used
    chk.append(dict(mode=m, mean=round(mean, 6), std_ddof0=round(sd0, 6),
                    std_ddof1_NOT_used=round(sd1, 6),
                    seeds=[int(s) for s in q["seed"]],
                    per_seed=[round(float(z), 4) for z in v]))
assert float(d["MFNN_Factor2"].abs().max()) == 0.0, "Factor2 not all zero"
assert len(d) == 20, len(d)

meta = {
    "figure": "Fig. S3 (matplotlib stem FigS3_al80_anchor_k)",
    "role": "SI diagnostic of sparse-neighborhood / few-shot anchor failure on the Al80Cu20 "
            "tracer; k>0 is NOT pure LOGO and NOT a Protocol W success; not PINN/PPINN; "
            "Factor2 = 0 at all k is a caption fact and is NEVER drawn in the figure",
    "bars": [{"x": X[i], "value_pct": VAL[i], "err_pct_popstd_ddof0": ERR[i],
              "bar_label": LAB[i], "category": CAT[i], "mode": MODES[i]} for i in range(4)],
    "provenance": {
        "csv": "outputs/results/AL80_tracer_anchor_sensitivity.csv",
        "frozen_heights": "scripts/publish_figures/_style.py FROZEN['S1_MAPE'] = (178.20, 169.55, 175.27, 142.93) "
                          "(legacy key name: Fig. S3 was numbered S1 then; NOT the current Fig. S1 alphas)",
        "error_bars": "5-seed population std (ddof=0), hardcoded from the prompt table",
        "seeds": seeds, "modes": MODES,
        "generator_never_run": "scripts/publish_figures/generate_p2_gemini.py::figs3_anchor_k()"},
    "read_only_crosscheck": {"per_mode": chk,
                             "all_20_MFNN_Factor2_exactly_zero": True},
    "forbidden_on_figure": ["in-figure suptitle 'Few-shot anchor diagnostic (SI only - not pure LOGO)'",
                            "in-bar 'Factor2 = 0 (all k)' text", "LF_only / HF_only bars",
                            "two-decimal bar labels", "ddof=1 error bars", "a fifth bar",
                            "PINN / PPINN / LOGO-success wording"],
    "geometry": {"x_centers": X, "bar_width_du": 0.6, "xlim": [-0.5, 3.5],
                 "ylim": [0.0, 250.0], "yticks": [0.0, 50.0, 100.0, 150.0, 200.0, 250.0],
                 "xticks": X},
    "recomputed": False,
}
with open(os.path.join(OD, "figs3_data_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1, ensure_ascii=False)

for c in chk:
    print("%-9s mean %.6f  popstd %.6f  (ddof1 %.6f NOT used)  frozen %.2f -> label %s" %
          (c["mode"], c["mean"], c["std_ddof0"], c["std_ddof1_NOT_used"],
           VAL[MODES.index(c["mode"])], LAB[MODES.index(c["mode"])]))
print("FROZEN_DISPLAY_MATCHES_5SEED_CSV = True ; Factor2(all 20 rows) == 0")
print("DONE_FIGS3_DATA")
