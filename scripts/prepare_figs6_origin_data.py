r"""Prepare the FROZEN Fig. S6 Origin workbook data (Al80Cu20 tracer, fixed k=2
anchor-reweighting w=1->5->10, dual axes: left MFNN MAPE, right Factor2).

SI counterfactual / mechanism diagnostic only -- NOT LOGO success, NOT a Protocol W
metric, not PINN/PPINN.

Rules obeyed here:
  * the figure values are the frozen DISPLAY numbers, written literally: the three
    MAPE points are FROZEN["S3_MAPE"] = (122.0, 48.0, 31.0) shown as 122% / 48% / 31%
    (key name S3_MAPE is a legacy numbering artefact in scripts/publish_figures/_style.py);
  * the band half-widths are the 5-seed POPULATION std (ddof=0), written to the same
    two decimals the report prints: 14.89 / 4.16 / 7.91 (NOT the ddof=1 sample std
    16.65 / 4.65 / 8.85);
  * Factor2 points are 0.15 / 1.0 / 1.0 (report 0.150/1.000/1.000), drawn WITHOUT
    numbers, WITHOUT error bars and WITHOUT a band, exactly like the frozen figure;
  * the CSV/REPORT are read ONLY as a read-only provenance cross-check; nothing on the
    figure is recomputed;
  * scripts/run_al80_anchor_upweight_k2.py and scripts/publish_figures/generate_p2_gemini.py
    are NEVER run by this pipeline.

Writes outputs/origin_data/figs6_mape.csv, figs6_factor2.csv, figs6_data_meta.json
and figs6_untouched_baseline.json (sha256 of everything this redraw may NOT modify).
"""
import os, csv, json, hashlib

B = r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D"
OD = os.path.join(B, "outputs", "origin_data")
os.makedirs(OD, exist_ok=True)

# ---- frozen display values (hardcoded; the only numbers allowed on the figure) ----
W = [1, 5, 10]
MAPE_PTS = [122.0, 48.0, 31.0]                 # FROZEN["S3_MAPE"] (legacy key name)
MAPE_LBL = ["122%", "48%", "31%"]
BAND_HALF = [14.89, 4.16, 7.91]                # report pop std, 2 dp
F2_PTS = [0.15, 1.0, 1.0]                      # right axis; NOT annotated on the figure

with open(os.path.join(OD, "figs6_mape.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["w", "mape_pt", "label", "band_lo", "band_hi", "band_half"])
    for i in range(3):
        cw.writerow([W[i], MAPE_PTS[i], MAPE_LBL[i],
                     round(MAPE_PTS[i] - BAND_HALF[i], 2), round(MAPE_PTS[i] + BAND_HALF[i], 2),
                     BAND_HALF[i]])
with open(os.path.join(OD, "figs6_factor2.csv"), "w", newline="", encoding="utf-8") as f:
    cw = csv.writer(f)
    cw.writerow(["w", "factor2"])
    for i in range(3):
        cw.writerow([W[i], F2_PTS[i]])

# ---- read-only provenance cross-check (five seeds 0/1/2/42/123) ----
import pandas as pd
d = pd.read_csv(os.path.join(B, "outputs", "results", "AL80_anchor_upweight_k2.csv"))
assert sorted(set(int(s) for s in d["seed"])) == [0, 1, 2, 42, 123]
chk = {}
for i, w in enumerate(W):
    q = d[d["w_anchor"] == w]
    assert len(q) == 5
    chk[w] = dict(mean=round(float(q["MFNN_MAPE_pct"].mean()), 4),
                  std_pop=round(float(q["MFNN_MAPE_pct"].std(ddof=0)), 4),
                  std_sample=round(float(q["MFNN_MAPE_pct"].std(ddof=1)), 4),
                  f2_mean=round(float(q["MFNN_Factor2"].mean()), 4))
ok = (round(chk[1]["std_pop"], 2) == 14.89 and round(chk[5]["std_pop"], 2) == 4.16 and round(chk[10]["std_pop"], 2) == 7.91 and
      chk[1]["f2_mean"] == 0.15 and chk[5]["f2_mean"] == 1.0 and chk[10]["f2_mean"] == 1.0)
assert ok, ("cross-check disagrees with the frozen table -> STOP, do not alter 122/48/31", chk)

meta = {
    "figure": "Fig. S6 (matplotlib stem FigS6_al80_upweight_w; fn figs4_upweight() is a legacy name)",
    "role": "SI counterfactual / mechanism diagnostic, fixed k=2; NOT LOGO success, "
            "NOT a Protocol W metric; not PINN/PPINN; HF_only/LF_only NOT drawn",
    "mape": [{"w": W[i], "point": MAPE_PTS[i], "label": MAPE_LBL[i], "band_half": BAND_HALF[i],
              "band": [round(MAPE_PTS[i] - BAND_HALF[i], 2), round(MAPE_PTS[i] + BAND_HALF[i], 2)]}
             for i in range(3)],
    "factor2": [{"w": W[i], "point": F2_PTS[i], "annotated": False} for i in range(3)],
    "provenance": {
        "report": "outputs/results/AL80_anchor_upweight_k2_REPORT.md",
        "csv": "outputs/results/AL80_anchor_upweight_k2.csv",
        "frozen_mape": "scripts/publish_figures/_style.py FROZEN['S3_MAPE'] = (122.0, 48.0, 31.0)",
        "word_caption": "frozen MAPE 122->48->31% (FIXED30 wording; not modified this round)",
        "band_std": "5-seed population std (ddof=0), report 2 dp"},
    "read_only_crosscheck": chk,
    "forbidden": {"values": ["122.10", "47.89", "31.30", "16.65", "4.65", "8.85", "0.300", "-16.262",
                              "-3.165", "-1.092", "0.150", "1.000 as annotation"],
                  "reason": "unrounded means / ddof=1 stds / R2 / +-0.300 / Factor2 numbers are not drawn"},
    "geometry": {"xlim": [0.55, 10.45], "ylim_left": [0.0, 160.0], "ylim_right": [0.0, 1.15],
                 "ylim_note": "left axis raised 150->160 only as annotation-avoidance headroom; "
                              "0/25/.../150 major ticks and the 150 tick are retained, "
                              "right axis keeps 0..1.15 with y=1.0 markers unclipped",
                 "xticks": W, "yticks_left": [0, 25, 50, 75, 100, 125, 150],
                 "yticks_right": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]},
    "recomputed": False,
}
with open(os.path.join(OD, "figs6_data_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1, ensure_ascii=False)

# ---- untouched baseline: sha256 of everything this redraw must not modify ----
def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
watch = []
for stem in ["FigS6_al80_upweight_w", "FigS3_al80_upweight_w", "FigS4_al80_upweight_w",
             "FigS6_protocol_G_variance"]:
    for ext in ("png", "pdf", "svg"):
        watch.append(os.path.join("outputs", "figures", stem + "." + ext))
for ext in ("png", "pdf", "svg"):
    watch.append(os.path.join("outputs", "jcp_submission", "figures", "FigS6_al80_upweight_w." + ext))
for s in ["scripts/publish_figures/generate_p2_gemini.py", "scripts/publish_figures/_style.py",
          "scripts/run_al80_anchor_upweight_k2.py"]:
    watch.append(s)
for stem in ["Fig1_mfnn_residual_schema", "Fig2_phase_space_coverage", "Fig3_protocol_W_parity_metrics",
             "Fig4_protocol_W_residual_topology", "Fig5_arrhenius_representative",
             "Fig6_Al80_tracer_inter", "Fig7_LOGO_distance_caution",
             "FigS1_alpha_mixing_weights", "FigS2_protocol_G_variance", "FigS3_al80_anchor_k",
             "FigS4_al80_posthoc_shift", "FigS5_difftype_split_ablation"]:
    for ext in ("opju", "pdf", "png", "svg"):
        watch.append(os.path.join("outputs", "figures_origin", stem + "." + ext))
watch.append(os.path.join("outputs", "PAPER_JCP_draft_EN_academic_FIXED30.docx"))
base = {}
for rel in watch:
    p = os.path.join(B, rel.replace("/", os.sep))
    st = os.stat(p) if os.path.exists(p) else None
    base[rel] = dict(sha256=sha(p), bytes=(st.st_size if st else None),
                     mtime_ns=(st.st_mtime_ns if st else None))
with open(os.path.join(OD, "figs6_untouched_baseline.json"), "w", encoding="utf-8") as f:
    json.dump(base, f, indent=1)

print("cross-check:", json.dumps(chk, indent=1))
print("frozen display -> 122% (122.0 +/- 14.89) | 48% (48.0 +/- 4.16) | 31% (31.0 +/- 7.91) ; F2 0.15/1.0/1.0 no ink")
print("baseline files recorded:", len(base))
print("DONE_FIGS6_DATA")

