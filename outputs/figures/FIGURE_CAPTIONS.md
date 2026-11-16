# Figure captions (J. Comput. Phys. style) — Gemini Lu-style numbering

## Keep / Merge / Relocate map (2026-10-22)

| Gemini ID | Stem (canonical) | Action | Legacy stems retained |
|-----------|------------------|--------|------------------------|
| Main Fig. 1 | `Fig1_mfnn_residual_schema` / `fig1_mfnn_schema` | Keep | same |
| Main Fig. 2 | `Fig2_phase_space_coverage` | New P1 (coverage + eta-D / Sutherland) | `Fig3_dataset_coverage` (warehouse) |
| Main Fig. 3 | `Fig3_protocol_W_parity_metrics` | Merge (bars + parity) | `fig2_protocol_W_metrics`, `fig2c_protocol_W_parity_ensemble`, `Fig2_protocolW_metrics_parity` |
| Main Fig. 4 | `Fig4_protocol_W_residual_topology` | New (P0) | `Fig9_residuals_log10` (related) |
| Main Fig. 5 | `Fig5_arrhenius_representative` | New P1 (inference-only T-grid) | legacy `arrhenius_plot` under `outputs/within_T/` |
| Main Fig. 6 | `Fig6_Al80_tracer_inter` | Relocate from old Fig. 3 | `fig3_Al80_tracer_inter`, `Fig4_Al80_tracer_vs_inter` |
| Main Fig. 7 | `Fig7_LOGO_distance_caution` | P1 upgrade: bars + delta x_Cu (caution) | `Fig7_LOGO_MAPE_bars`, `fig4_LOGO_MAPE_bars`, `Fig5_LOGO_MAPE_by_fold` |

| SI Fig. S1 | `FigS1_alpha_mixing_weights` | Gemini **S1** (α mixing) | `Fig6_alpha_mixing_weights` |
| SI Fig. S2 | `FigS2_protocol_G_variance` | Gemini **S2** (Protocol G variance caution) | legacy `FigS6_protocol_G_variance`, `Fig8_protocol_W_vs_G` |
| SI Fig. S3 | `FigS3_al80_anchor_k` | Gemini **S3** (few-shot anchor) | `FigS1_al80_anchor_k`, `fig_si_al80_anchor_k` |
| SI Fig. S4 | `FigS4_al80_posthoc_shift` | Gemini **S4** (oracle / post-hoc intercept) | legacy `FigS2_al80_posthoc_shift`, `fig_si_al80_posthoc_shift` |
| SI Fig. S5 | `FigS5_difftype_split_ablation` | Gemini **S5** (tracer/inter split ablation) | `Fig7_ablation_separate_vs_joint` |
| SI Fig. S6 (optional) | `FigS6_al80_upweight_w` | **Not** in Gemini core S1–S5 (up-weight extra) | legacy `FigS4_al80_upweight_w`, `FigS3_al80_upweight_w` |

**Strict Gemini SI (2026-10-22):** S1 α; S2 Protocol G caution; S3 anchor; S4 oracle/posthoc; S5 difftype ablation. Optional S6 = upweight only.

Do not delete legacy filenames. Frozen Protocol W / LOGO / α numbers are unchanged.
**Round2–3 caption polish:** duplicate method-boundary clauses removed from figure captions; single residual-MFNN vs PDE-informed-NN boundary retained in Introduction (and Limitations in tex).

---

**Fig. 1.** Schematic of the residual multi-fidelity neural network (MFNN) for predicting high-fidelity liquid diffusivity $D$ from viscosity $\eta$, drawn in the style of Lu et al. (PNAS 2020, Fig. 1). (A) Physical context: a modified Sutherland low-fidelity (LF) prior $D_{\mathrm{LF}}\propto T/(\eta\,r_i(T))$ from viscosity, versus scarce high-fidelity (HF) $D_{\mathrm{exp}}$; the residual MFNN learns a correction from LF toward HF. (B) Single-fidelity NN (HF-only baseline). (C) Composite multi-fidelity NN with linear ($I$) and nonlinear ($\sigma$) branches on $[x,y_L]$. (D) Residual MFNN used in this work: $y_H=\alpha_1(A[x,y_L]+b)+\alpha_2 F_{\mathrm{nl}}(x,y_L)$ with learnable $\alpha_1,\alpha_2$ and a residual link from $y_L$ (red); positivity via $\hat{D}=10^{\hat{y}}$. Features include $(T,\,x,\,\eta)$ and optional diffusion type.

**Fig. 2.** Phase-space coverage and physical context of liquid-alloy diffusivity with honest viscosity pairing (no Kozlov fills). (a) High-fidelity temperature–composition coverage: Al–Cu points by diffusion modality versus $x_{\mathrm{Cu}}$; sparse Al–Mg–Si / Al–Ce–Ni / Al–Ag–Cu HF points shown versus total non-Al solute fraction. (b) Experimental $D$ versus melt viscosity $\eta$ by modality, overlaid with the modified Sutherland low-fidelity prior evaluated at the same $(T,\eta)$ points (plus markers) and a pure-Al Sutherland guide at $T=1000\,\mathrm{K}$ (dashed). File: `Fig2_phase_space_coverage`.

**Fig. 3.** Protocol W (within-composition temperature hold-out; five seeds $0,1,2,42,123$; $n_{\mathrm{test}}=15$ per seed) for residual MFNN versus HF-only and LF-only baselines. (a) Seed-mean $\log_{10}D$ parity with vertical bars showing the across-seed standard deviation; the shaded band is $\pm\log_{10}2$ (factor-of-two). Filled markers: sample present in all five seed test sets; open markers: partial seed overlap (union of test ids). Bar panels use frozen Table metrics and are not recomputed from the scatter. (b) MAPE (%): LF-only $109.6\pm13.13$, HF-only $30.98\pm4.43$, residual MFNN $26.18\pm1.33$. (c) Factor2: LF-only $0.56\pm0.10$, HF-only $0.973\pm0.033$, residual MFNN $0.96\pm0.033$. File: `Fig3_protocol_W_parity_metrics`.

**Fig. 4.** Protocol W residual topology for the residual MFNN (seed-mean predictions over seeds containing each sample_id; union of within_T test points). (a) Absolute $\log_{10}D$ error versus temperature; the dashed line marks $\log_{10}2$ (Factor-of-two threshold). HF-only points are shown for context. (b) Signed residual versus an LF prior proxy $y_L^{\mathrm{proxy}}=\log_{10}\hat{D}_{\mathrm{LF\text{-}only}}$, used because the prediction CSVs do not store an explicit Sutherland $D_{\mathrm{LF}}$ column; shaded band is $\pm\log_{10}2$. Visualizes residual structure only; does not alter frozen Protocol W table metrics. File: `Fig4_protocol_W_residual_topology`.

**Fig. 5.** Representative Arrhenius-style $\log_{10}D$ versus $1000/T$ curves under Protocol W weights (seed 42 checkpoint; **inference only, no retraining**; 12-D features as stored). (a) Pure Al self-diffusion: HF experiments with continuous $T$-grid predictions from residual MFNN, HF-only, LF-only, and the modified Sutherland prior ($\eta(T)$ from honest paired viscosities). (b) $\mathrm{Al}_{80}\mathrm{Cu}_{20}$ Cu-tracer with $\eta(T)$ interpolated from honest Al80Cu20 paired viscosities. Illustrates smoothness of the LF-anchored residual MFNN relative to HF-only; not a LOGO success claim. File: `Fig5_arrhenius_representative`.

**Fig. 6.** Label conflict at composition $\mathrm{Al}_{80}\mathrm{Cu}_{20}$. (a) High-fidelity diffusivity versus temperature: Cu-tracer data (Zhang et al.; open circles) lie systematically below interdiffusivity points (squares) by a factor of $\sim 3$ near $983\,\mathrm{K}$ ($D_{\mathrm{tracer}}\approx 2.35\times 10^{-9}$ vs $D_{\mathrm{inter}}\approx 7.0\times 10^{-9}\,\mathrm{m}^{2}\,\mathrm{s}^{-1}$). Without a $\texttt{diff\_type}$ feature or group split, a single $\texttt{comp\_group}$ cannot fit both scales. (b) Leave-one-group-out (LOGO) MFNN MAPE after splitting groups by $\texttt{diff\_type}$ and adding a one-hot type feature: $\texttt{Al80Cu20\_tracer}$ remains difficult (MAPE $156.5\,\%$, Factor2 $=0$, $n=10$), whereas $\texttt{Al80Cu20\_inter}$ recovers (MAPE $6.5\,\%$, Factor2 $=1$, $n=2$). Relocated from legacy Main Fig. 3. File: `Fig6_Al80_tracer_inter`.

**Fig. 7 (caution).** Al–Cu leave-one-composition-out (LOGO) for residual MFNN after $\texttt{diff\_type}$ splitting and one-hot features (13 folds; metrics from `LOGO_AlCu_difftype_feat_summary.csv`, not recomputed). (a) MAPE by hold-out group (frozen overall mean $39.4\pm39.7\%$). (b) Same fold MAPE versus composition distance $\Delta x_{\mathrm{Cu}}$ to the nearest *distinct* high-fidelity training composition (same-$x$ aliases such as Al81Cu19 / Al81.3Cu18.7 excluded). Large MAPE at small $\Delta x_{\mathrm{Cu}}$ (e.g. $\mathrm{Al}_{80}\mathrm{Cu}_{20}$ tracer) highlights label/neighborhood limits rather than transferable extrapolation success. Not a cross-alloy claim. File: `Fig7_LOGO_distance_caution` (legacy pure-bar `Fig7_LOGO_MAPE_bars` retained).

**Fig. S1.** Protocol W residual-MFNN mixing weights $\alpha_1$ (linear path) and $\alpha_2$ (nonlinear residual path) extracted read-only from five within_T checkpoints (seeds $0,1,2,42,123$). Dashed lines mark frozen seed means $\alpha_1=0.5369\pm0.1200$ and $\alpha_2=0.6525\pm0.0301$ (population std, $\mathrm{ddof}=0$). SI diagnostic only; not a headline claim. File: `FigS1_alpha_mixing_weights`.

**Fig. S2 (caution).** Protocol W versus random between-group Protocol G for residual MFNN (frozen MAPE $26.18\pm1.33\%$ vs $27.36\pm12.88\%$). (a) Mean±seed std; (b) per-seed trajectories. Protocol G is **cautionary only** (Al–Cu hold-outs; large seed variance)—not a headline claim. File: `FigS2_protocol_G_variance` (legacy `FigS6_protocol_G_variance` retained).

**Fig. S3.** Al80Cu20 tracer few-shot anchor-temperature sensitivity ($k=0,1,2$). Frozen MAPE $178.20/169.55/175.27/142.93\%$; Factor2 $=0$ at all $k$. SI diagnostic of sparse-neighborhood failure; $k>0$ is not pure LOGO. File: `FigS3_al80_anchor_k`.

**Fig. S4.** Counterfactual Al80Cu20 tracer post-hoc intercept-shift / oracle diagnostic (frozen shifted MAPE $9.81\pm1.73\%$). SI only; must not be read as Protocol W or LOGO success. File: `FigS4_al80_posthoc_shift` (legacy `FigS2_al80_posthoc_shift` retained as compatibility copy).

**Fig. S5.** Separate tracer-only and inter-only residual MFNN pools versus joint training with $\texttt{diff\_type}$ one-hot (negative ablation). (a) Stratified $\mathrm{Al}_{80}\mathrm{Cu}_{20}$: separate $173\%/11\%$ vs joint $156.5\%/6.5\%$. (b) Pool-level LOGO means (inter mean excludes exploding $\mathrm{Al}_{70}\mathrm{Cu}_{30}$ fold). Splitting does not fix sparse tracer neighborhoods. SI only. File: `FigS5_difftype_split_ablation`.

**Fig. S6 (optional; not Gemini core S1–S5).** Al80Cu20 tracer $k=2$ anchor up-weighting $w=1\to5\to10$ (frozen MAPE $122\to48\to31\%$). SI counterfactual only. File: `FigS6_al80_upweight_w`.
