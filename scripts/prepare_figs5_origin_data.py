r"""Prepare the FROZEN Fig. S5 Origin data (split-trained tracer/inter pools vs joint+one-hot).

SI NEGATIVE ablation only: separate training did NOT beat joint + diff_type one-hot.
Not success wording, not PINN/PPINN, no HF_only/LF_only bars, no Factor2, no n on the
figure, no retraining, no re-evaluation, no re-running of generate_p2_gemini.py.

Rules obeyed here:
  * the figure shows ONLY the frozen display numbers, written literally below:
      (a) 173.0 / 156.5 / 11.0 / 6.5 %   (no error bars)
      (b) 99.7+/-54.5, 18.0+/-16.9, 39.4+/-39.7  (population std, ddof=0)
    the (b) bar heights are the frozen 99.66 / 17.96 / 39.4 (third bar uses the frozen
    39.4, NOT the REPORT float 39.43);
  * outputs/results/LOGO_AlCu_separate_models_summary.csv and
    LOGO_AlCu_separate_models_REPORT.md are read ONLY as a read-only cross-check;
    the exploding Al70Cu30_inter fold (~1.50e14 % MFNN) is EXCLUDED from the inter
    pool mean and is never drawn;
  * ddof=1 (sample std, ~62.99 / ~18.25) is FORBIDDEN and asserted against;
  * the 13-fold joint mean is never recomputed: 39.4+/-39.7 is FROZEN["LOGO_mean"].

Writes outputs/origin_data/figs5_a_bars.csv, figs5_b_bars.csv, figs5_data_meta.json
"""
import os, csv, json, statistics as st

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
os.makedirs(OD, exist_ok=True)
PM = "\u00b1"   # plus-minus, display only

# ---- (a) Al80 hold-outs: frozen display values (FROZEN in scripts/publish_figures/_style.py)
A_ROWS = [
    dict(group="tracer", series="separate", x=-0.175, value=173.0, label="173.0%",
         fill="#7F7F7F", edge="#333333", frozen="FROZEN['Al80_tracer_sep']"),
    dict(group="tracer", series="joint",    x=0.175,  value=156.5, label="156.5%",
         fill="#D55E00", edge="#994300", frozen="FROZEN['Al80_tracer_joint']"),
    dict(group="inter",  series="separate", x=0.825,  value=11.0,  label="11.0%",
         fill="#7F7F7F", edge="#333333", frozen="FROZEN['Al80_inter_sep']"),
    dict(group="inter",  series="joint",    x=1.175,  value=6.5,   label="6.5%",
         fill="#56B4E9", edge="#1B5E82", frozen="FROZEN['Al80_inter_joint']"),
]
# ---- (b) pool-level LOGO means: frozen heights + frozen display, ddof=0 law
B_ROWS = [
    dict(name="Separate tracer pool", x=0.0, value=99.66, err=54.55,
         display="99.7" + PM + "54.5", fill="#D55E00", edge="#994300",
         source="REPORT 'tracer (4 folds): 99.66 +/- 54.55'"),
    dict(name="Separate inter (excl. Al70)", x=1.0, value=17.96, err=16.90,
         display="18.0" + PM + "16.9", fill="#56B4E9", edge="#1B5E82",
         source="REPORT 'inter robust (excl. Al70Cu30_inter): 17.96 +/- 16.90'"),
    dict(name="Joint+one-hot (13 folds)", x=2.0, value=39.4, err=39.7,
         display="39.4" + PM + "39.7", fill="#009E73", edge="#006B4E",
         source="FROZEN['LOGO_mean'] = (39.4, 39.7) (same as main-text Fig.7)"),
]

with open(os.path.join(OD, "figs5_a_bars.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["group", "series", "x_center", "value_pct", "label", "fill", "edge", "frozen_key"])
    for r in A_ROWS:
        cw.writerow([r["group"], r["series"], r["x"], r["value"], r["label"], r["fill"], r["edge"], r["frozen"]])
with open(os.path.join(OD, "figs5_b_bars.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["name", "x_center", "value_pct", "err_pct", "display", "fill", "edge", "source"])
    for r in B_ROWS:
        cw.writerow([r["name"], r["x"], r["value"], r["err"], r["display"], r["fill"], r["edge"], r["source"]])

# ---- read-only provenance cross-check (MFNN rows only, ddof=0, Al70Cu30_inter excluded)
CSVP = os.path.join(B, "outputs", "results", "LOGO_AlCu_separate_models_summary.csv")
rows = [r for r in csv.DictReader(open(CSVP, encoding="utf-8")) if r["model"] == "MFNN"]
tr = [float(r["MAPE_pct"]) for r in rows if r["pool"] == "tracer"]
it = [(r["holdout_group"], float(r["MAPE_pct"])) for r in rows if r["pool"] == "inter"]
it2 = [v for g, v in it if g != "Al70Cu30_inter"]
tr_m, tr_s = st.mean(tr), st.pstdev(tr)
it_m, it_s = st.mean(it2), st.pstdev(it2)
tr_s1, it_s1 = st.stdev(tr), st.stdev(it2)
chk = dict(tracer_folds=[round(v, 4) for v in tr], tracer_mean=round(tr_m, 4),
           tracer_std_ddof0=round(tr_s, 4),
           inter_folds_excluded="Al70Cu30_inter=%.4e" % max(v for g, v in it if g == "Al70Cu30_inter"),
           inter_folds_kept=[round(v, 4) for v in it2], inter_mean=round(it_m, 4),
           inter_std_ddof0=round(it_s, 4),
           forbidden_ddof1=dict(tracer=round(tr_s1, 4), inter=round(it_s1, 4)))
assert (round(tr_m, 2), round(tr_s, 2)) == (99.66, 54.55), chk
assert (round(it_m, 2), round(it_s, 2)) == (17.96, 16.90), chk
assert round(tr_s1, 2) != 54.55 and round(it_s1, 2) != 16.90
print("cross-check OK: tracer %.4f+/-%.4f (ddof=0) | inter excl Al70 %.4f+/-%.4f (ddof=0)" %
      (tr_m, tr_s, it_m, it_s))
print("forbidden ddof=1 values (NOT drawn): %.2f / %.2f" % (tr_s1, it_s1))

meta = dict(
    figure="Fig. S5 (matplotlib stem FigS5_difftype_split_ablation; PNG SHA256 884e4ac8...)",
    role="SI negative ablation: separate tracer/inter pools vs joint + diff_type one-hot. "
         "Splitting does NOT beat joint+one-hot; NOT PINN/PPINN; no retraining; nothing recomputed.",
    panel_a=dict(xlim=[-0.5, 1.5], ylim=[0.0, 210.0], yticks=[0.0, 50.0, 100.0, 150.0, 200.0],
                 group_centres=[0.0, 1.0], bar_width_du=0.35,
                 separate_offset=-0.175, joint_offset=0.175,
                 categories=["Al80Cu20 tracer", "Al80Cu20 inter"],
                 bars=A_ROWS, no_error_bars=True),
    panel_b=dict(xlim=[-0.4, 2.4], ylim=[0.0, 190.0],
                 yticks=[0.0, 25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 175.0],
                 bar_centres=[0.0, 1.0, 2.0], bar_width_du=0.55, bars=B_ROWS,
                 err_law="population std ddof=0",
                 clip_note="Joint+one-hot lower cap (-0.3) is below 0: stem clipped at 0, no lower cap (as in the frozen stem render)"),
    frozen_display=dict(a=["173.0%", "156.5%", "11.0%", "6.5%"],
                        b=["99.7" + PM + "54.5", "18.0" + PM + "16.9", "39.4" + PM + "39.7"]),
    provenance=dict(
        style_py="scripts/publish_figures/_style.py FROZEN: Al80_tracer_sep=173.0, Al80_inter_sep=11.0, "
                 "Al80_tracer_joint=156.5, Al80_inter_joint=6.5, LOGO_mean=(39.4, 39.7)",
        report="outputs/results/LOGO_AlCu_separate_models_REPORT.md",
        csv="outputs/results/LOGO_AlCu_separate_models_summary.csv (model==MFNN only)"),
    read_only_crosscheck=chk,
    forbidden=dict(
        values=[173.29, 156.49, 10.95, 6.48, 39.43, 39.71, 62.99, 18.25, 1.50e14],
        strings=["negative ablation on figure", "Factor2", "n=", "HF_only", "LF_only",
                 "Al70Cu30_inter drawn", "PINN", "PPINN", "Note text below (b)",
                 "caution in panel title", "173%", "173.3"],
        reason="frozen DISPLAY rounding is the law; ddof=1 is forbidden; the exploding fold is never drawn"),
    recomputed=False)
json.dump(meta, open(os.path.join(OD, "figs5_data_meta.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print("frozen (a):", meta["frozen_display"]["a"])
print("frozen (b):", meta["frozen_display"]["b"])
print("DONE_FIGS5_DATA")
