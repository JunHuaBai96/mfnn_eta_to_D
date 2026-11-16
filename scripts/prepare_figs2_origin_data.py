r"""Prepare the FROZEN Fig. S2 Origin workbook data (Protocol W vs random between-group G).

SI caution diagnostic only -- Protocol G is NOT a headline result, NOT a replacement for
Protocol W, not PINN/PPINN, and Factor2 is deliberately NOT drawn (the body text already
carries G's 0.791 +/- 0.257).

Rules obeyed here:
  * the (a) bar heights, error bars and bar-top annotations are the frozen DISPLAY numbers
    (FROZEN["W_MFNN_MAPE"] / FROZEN["G_MFNN_MAPE"] in scripts/publish_figures/_style.py),
    written literally; nothing on the figure is recomputed, and the spread is the frozen
    POPULATION std (ddof=0), never switched to a sample std;
  * the (b) per-seed MAPEs are the ten hardcoded values of the redraw prompt;
    outputs/results/seed_WG_summary.csv is read ONLY as a read-only cross-check of the
    MFNN W/G rows for seeds 0/1/2/42/123.  LF_only / HF_only rows are never read;
  * scripts/publish_figures/generate_p2_gemini.py is NEVER run (its main() repaints several
    SI figures, including the buggy figs2_posthoc() that feeds Fig. S4 wrong numbers).

Writes outputs/origin_data/figs2_a_bars.csv, figs2_b_traj.csv, figs2_data_meta.json
"""
import os, csv, json

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
os.makedirs(OD, exist_ok=True)

# ---- frozen display values (hardcoded; the only numbers allowed on panel (a)) ----
W_MEAN, W_ERR = 26.18, 1.33     # FROZEN["W_MFNN_MAPE"]   -- Protocol W (primary)
G_MEAN, G_ERR = 27.36, 12.88    # FROZEN["G_MFNN_MAPE"]   -- Protocol G (caution)

# ---- frozen per-seed trajectories (hardcoded; panel (b), categorical x) ----
SEEDS = [0, 1, 2, 42, 123]
W_TRAJ = [25.759821, 23.981770, 27.614428, 27.526907, 26.034135]
G_TRAJ = [17.371446, 13.464178, 40.324631, 20.407325, 45.237544]
assert len(SEEDS) == len(W_TRAJ) == len(G_TRAJ) == 5

with open(os.path.join(OD, "figs2_a_bars.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["x", "value", "err", "caption"])
    cw.writerow([0.00, W_MEAN, W_ERR, "Protocol W|(primary)"])
    cw.writerow([1.00, G_MEAN, G_ERR, "Protocol G|(caution)"])

with open(os.path.join(OD, "figs2_b_traj.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["xcat", "seed", "protocol", "mape"])
    for i, s in enumerate(SEEDS):
        cw.writerow([i, s, "W", "%.6f" % W_TRAJ[i]])
    for i, s in enumerate(SEEDS):
        cw.writerow([i, s, "G", "%.6f" % G_TRAJ[i]])

# ---- read-only provenance cross-check (MFNN, protocols W/G, the five seeds) ----
import pandas as pd
d = pd.read_csv(os.path.join(B, "outputs", "results", "seed_WG_summary.csv"))
def pull(proto):
    q = d[(d["model"] == "MFNN") & (d["protocol"] == proto) & (d["seed"].isin(SEEDS))]
    assert len(q) == 5, (proto, len(q))
    q = q.sort_values("seed")
    return ([int(s) for s in q["seed"]], [round(v, 6) for v in q["MAPE_pct"]],
            float(q["MAPE_pct"].mean()), float(q["MAPE_pct"].std(ddof=0)))
w_chk = pull("W")
g_chk = pull("G")

meta = {
    "figure": "Fig. S2 (matplotlib stem FigS2_protocol_G_variance; script role figs6_...)",
    "role": "SI caution diagnostic: Protocol G seed variance. NOT a headline claim, "
            "NOT a replacement for Protocol W, not PINN/PPINN, no Factor2 on the figure, "
            "no LF_only/HF_only series drawn",
    "bars": [
        {"x": 0.0, "value_pct": W_MEAN, "err_pct": W_ERR, "name": "Protocol W (primary)"},
        {"x": 1.0, "value_pct": G_MEAN, "err_pct": G_ERR, "name": "Protocol G (caution)"}],
    "trajectories": [
        {"protocol": "W", "seeds": SEEDS, "mape_pct": W_TRAJ},
        {"protocol": "G", "seeds": SEEDS, "mape_pct": G_TRAJ}],
    "provenance": {
        "frozen_w": "scripts/publish_figures/_style.py FROZEN['W_MFNN_MAPE'] = (26.18, 1.33)",
        "frozen_g": "scripts/publish_figures/_style.py FROZEN['G_MFNN_MAPE'] = (27.36, 12.88)",
        "crosscheck_csv": "outputs/results/seed_WG_summary.csv (model==MFNN, protocol W/G, "
                          "seeds 0/1/2/42/123, read-only)",
        "body_wording": "26.18 +/- 1.33 %% (W) vs 27.36 +/- 12.88 %% (G); the caution sentence "
                        "lives in the Word caption, NOT in the figure",
        "spread_definition": "5-seed mean +/- population std (ddof=0)"},
    "read_only_crosscheck": {
        "W": {"seeds": w_chk[0], "mape_pct": w_chk[1], "mean": round(w_chk[2], 4),
              "std_ddof0": round(w_chk[3], 4), "display": "%.2f+/-%.2f" % (W_MEAN, W_ERR)},
        "G": {"seeds": g_chk[0], "mape_pct": g_chk[1], "mean": round(g_chk[2], 4),
              "std_ddof0": round(g_chk[3], 4), "display": "%.2f+/-%.2f" % (G_MEAN, G_ERR)}},
    "geometry": {"a_xlim": [-0.4, 1.4], "a_ylim": [0.0, 55.0], "bar_width_du": 0.55,
                 "a_xticks": [0.0, 1.0], "a_yticks": [0.0, 10.0, 20.0, 30.0, 40.0, 50.0],
                 "b_xlim_categorical_du": [-0.3, 4.3], "b_ylim": [10.0, 50.0],
                 "b_xticks": [0, 1, 2, 3, 4], "b_xlabels": ["0", "1", "2", "42", "123"],
                 "b_yticks": [10.0, 20.0, 30.0, 40.0, 50.0]},
    "forbidden_on_figure": ["Factor2", "LF_only", "HF_only",
                            "G hold-outs are Al-Cu groups; large seed variance: "
                            "not a headline claim"],
    "recomputed": False,
}
with open(os.path.join(OD, "figs2_data_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1, ensure_ascii=False)

print(json.dumps(meta["read_only_crosscheck"], indent=1, ensure_ascii=True))
ok = (w_chk[1] == [round(v, 6) for v in W_TRAJ] and g_chk[1] == [round(v, 6) for v in G_TRAJ] and
      w_chk[0] == SEEDS and g_chk[0] == SEEDS and
      abs(round(w_chk[2], 2) - W_MEAN) < 1e-9 and abs(round(w_chk[3], 2) - W_ERR) < 1e-9 and
      abs(round(g_chk[2], 2) - G_MEAN) < 1e-9 and abs(round(g_chk[3], 2) - G_ERR) < 1e-9)
print("frozen display -> W %.2f+/-%.2f %% | G %.2f+/-%.2f %%" % (W_MEAN, W_ERR, G_MEAN, G_ERR))
print("cross-check    -> W %.4f+/-%.4f  | G %.4f+/-%.4f  (ddof=0)" %
      (w_chk[2], w_chk[3], g_chk[2], g_chk[3]))
print("FROZEN_DISPLAY_MATCHES_SEED_WG_CSV =", ok)
assert ok, "frozen display values disagree with seed_WG_summary.csv"
print("DONE_FIGS2_DATA")
