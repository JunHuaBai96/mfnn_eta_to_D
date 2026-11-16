"""Prepare the FROZEN Fig. S4 Origin workbook data (Al80Cu20 post-hoc intercept shift).

SI mechanism diagnostic only -- NOT LOGO success, NOT a Protocol W metric, not PINN/PPINN.

Rules obeyed here:
  * the figure values are the frozen DISPLAY numbers, written literally; nothing is
    recomputed from the per-seed CSV for the drawing;
  * the CSV is read ONLY as a read-only provenance cross-check, and ONLY the 983 K
    MFNN rows (settings k0_raw_heldout_lowT_983 / k0_posthoc_shift_lowT_983, the five
    seeds 0/1/2/42/123).  The *_highT_1200 rows are the report's sensitivity control
    and are deliberately NOT read for this figure, and LF_only / HF_only are skipped;
  * the buggy helper scripts/publish_figures/generate_p2_gemini.py::figs2_posthoc()
    (it averages the 983 K and 1200 K rows together -> 177.91 / -0.444) is NEVER run.

Writes outputs/origin_data/figs4_bars.csv and outputs/origin_data/figs4_data_meta.json
"""
import os, csv, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
os.makedirs(OD, exist_ok=True)

# ---- frozen display values (hardcoded; the only numbers allowed on the figure) ----
RAW_MEAN, RAW_ERR = 175.20, 28.78      # report: k0 raw (held-out 9 @ drop 983K)
SH_MEAN, SH_ERR = 9.81, 1.73           # FROZEN["S2_MAPE"]; report: k0 + post-hoc shift @ 983K
DELTA_TXT = "\u03b4 = \u22120.482 \u00b1 0.046 \u2248 \u2212log\u2081\u2080 3"   # body-text wording

with open(os.path.join(OD, "figs4_bars.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["x", "value", "err", "caption"])
    cw.writerow([0.00, RAW_MEAN, RAW_ERR, "Raw held-out (no shift)"])
    cw.writerow([0.85, SH_MEAN, SH_ERR, "Post-hoc B2 intercept shift"])

# ---- read-only provenance cross-check (983 K, MFNN, five seeds) ----
import pandas as pd
d = pd.read_csv(os.path.join(B, "outputs", "results", "AL80_posthoc_intercept_shift.csv"))
seeds = [0, 1, 2, 42, 123]
def pull(setting):
    q = d[(d["model"] == "MFNN") & (d["setting"] == setting) & (d["seed"].isin(seeds))]
    assert len(q) == 5, (setting, len(q))
    q = q.sort_values("seed")
    return (float(q["MAPE_pct"].mean()), float(q["MAPE_pct"].std(ddof=0)),
            float(q["delta_log10"].mean()), float(q["delta_log10"].std(ddof=0)),
            [int(s) for s in q["seed"]], [round(v, 4) for v in q["MAPE_pct"]])
raw_chk = pull("k0_raw_heldout_lowT_983")
sh_chk = pull("k0_posthoc_shift_lowT_983")

meta = {
    "figure": "Fig. S4 (matplotlib stem FigS4_al80_posthoc_shift)",
    "role": "SI mechanism diagnostic; oracle / counterfactual; NOT LOGO success, "
            "NOT a Protocol W metric; not PINN/PPINN; 1200 K sensitivity control NOT drawn",
    "bars": [
        {"x": 0.00, "value_pct": RAW_MEAN, "err_pct": RAW_ERR, "name": "Raw held-out (no shift)"},
        {"x": 0.85, "value_pct": SH_MEAN, "err_pct": SH_ERR, "name": "Post-hoc B2 intercept shift"}],
    "delta_annotation": DELTA_TXT,
    "provenance": {
        "report": "outputs/results/AL80_posthoc_intercept_shift_REPORT.md",
        "csv": "outputs/results/AL80_posthoc_intercept_shift.csv",
        "frozen_shift": "scripts/publish_figures/_style.py FROZEN['S2_MAPE'] = (9.81, 1.73)",
        "body_text": "175.20 \u00b1 28.78 % / 9.81 \u00b1 1.73 % / \u03b4 = \u22120.482 \u00b1 0.046 \u2248 \u2212log\u2081\u2080 3",
        "evaluation_set": "MFNN, anchor 983 K, the 9 held-out temperatures, 5-seed mean +/- std (ddof=0)"},
    "read_only_crosscheck": {
        "k0_raw_heldout_lowT_983": {"mape_mean": round(raw_chk[0], 4), "mape_std_ddof0": round(raw_chk[1], 4),
                                     "seeds": raw_chk[4], "per_seed_mape": raw_chk[5]},
        "k0_posthoc_shift_lowT_983": {"mape_mean": round(sh_chk[0], 4), "mape_std_ddof0": round(sh_chk[1], 4),
                                      "delta_mean": round(sh_chk[2], 4), "delta_std_ddof0": round(sh_chk[3], 4),
                                      "seeds": sh_chk[4], "per_seed_mape": sh_chk[5]},
        "display_rounding": {"raw": "%.2f+/-%.2f" % (RAW_MEAN, RAW_ERR),
                             "shift": "%.2f+/-%.2f" % (SH_MEAN, SH_ERR),
                             "delta": "3 dp (\u22120.482+/-0.046), report keeps 4 dp (\u22120.4822+/-0.0463)"}},
    "forbidden": {"values": [177.91, 29.22, -0.444, 0.059],
                  "reason": "generate_p2_gemini.py::figs2_posthoc() mixes the 983 K and 1200 K rows",
                  "not_drawn_1200K": {"raw": "180.62 +/- 29.39", "shift": "9.40 +/- 2.23",
                                      "delta": "-0.4068 +/- 0.0447"}},
    "geometry": {"x_centers": [0.0, 0.85], "bar_width_du": 0.55, "xlim": [-0.45, 1.30],
                 "ylim": [0.0, 250.0], "yticks": [0.0, 50.0, 100.0, 150.0, 200.0],
                 "xticks": [0.0, 0.85]},
    "recomputed": False,
}
with open(os.path.join(OD, "figs4_data_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1, ensure_ascii=False)

print(json.dumps(meta["read_only_crosscheck"], indent=1, ensure_ascii=True))
print("frozen display -> raw %.2f +/- %.2f %% | shift %.2f +/- %.2f %%" %
      (RAW_MEAN, RAW_ERR, SH_MEAN, SH_ERR))
print("cross-check    -> raw %.4f +/- %.4f | shift %.4f +/- %.4f | delta %.4f +/- %.4f" %
      (raw_chk[0], raw_chk[1], sh_chk[0], sh_chk[1], sh_chk[2], sh_chk[3]))
ok = (abs(round(raw_chk[0], 2) - RAW_MEAN) < 1e-9 and abs(round(raw_chk[1], 2) - RAW_ERR) < 1e-9 and
      abs(round(sh_chk[0], 2) - SH_MEAN) < 1e-9 and abs(round(sh_chk[1], 2) - SH_ERR) < 1e-9 and
      abs(round(sh_chk[2], 3) + 0.482) < 1e-9 and abs(round(sh_chk[3], 3) - 0.046) < 1e-9)
print("FROZEN_DISPLAY_MATCHES_983K_CSV =", ok)
assert ok, "frozen display values disagree with the 983 K MFNN rows"
print("DONE_FIGS4_DATA")
