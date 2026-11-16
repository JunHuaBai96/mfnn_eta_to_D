# Cover letter — Journal of Computational Physics

**To:** The Editors, *Journal of Computational Physics*  
**From:** Junhua Bai, Guanglong Xu, Fuwen Chen, Yuwen Cui*  
**Affiliation:** Tech Institute for Advanced Materials & College of Materials Science and Engineering, Nanjing Tech University, Nanjing 211816, China  
**Corresponding author:** Yuwen Cui  
**Email:** ycui@njtech.edu.cn  
**Date:** 20 October 2026  

**Re:** Submission of the manuscript  
*Residual multi-fidelity neural network correction of a Sutherland-type η→D map for Al-dominated liquid alloys*

---

Dear Editors,

Please find enclosed our manuscript for consideration in *Journal of Computational Physics*.

Liquid diffusivities in multicomponent melts are scarce relative to viscosity, while classical Stokes–Einstein / Sutherland maps leave systematic residuals against experiment. We submit a residual multi-fidelity neural network (MFNN) that corrects a modified Sutherland η→D prior toward high-fidelity experimental diffusivities for Al-dominated liquid alloys. The residual formulation follows Lu et al. (*Proc. Natl. Acad. Sci. U.S.A.* 117, 7052, 2020) and extends the composite multi-fidelity network of Meng and Karniadakis (*J. Comput. Phys.* 401, 109020, 2020). This work uses only that multi-fidelity regression idea; it is physics-guided and does **not** employ PDE-residual PINN training or Meng’s parallel-in-time PPINN framework.

**Primary contributions.**

1. **Physics-guided residual multi-fidelity learning for η→D.** Under within-composition temperature hold-out (Protocol W; five seeds; *n*_test = 15), the residual MFNN attains MAPE 26.18 ± 1.33%, Factor2 0.96 ± 0.033, and *R*² 0.392 ± 0.094, improving continuous accuracy and compressing seed-to-seed MAPE standard deviation by ~70% relative to HF-only (MAPE 30.98 ± 4.43%, Factor2 0.973 ± 0.033, *R*² 0.263 ± 0.076), while far exceeding the LF-only network trained on Sutherland-generated log₁₀ *D*_LF targets (MAPE 109.6 ± 13.13%, *R*² −2.588 ± 0.399).

2. **Strict data provenance without synthetic leakage.** We enforce pairing exclusively with measured or recommended viscosity correlations (e.g., Assael and Schick compilations), explicitly excluding empirical Kozlov alloy viscosity fills that would otherwise introduce silent target leakage.

3. **Thermodynamic diagnosis of composition-transfer boundaries.** Through modality-stratified leave-one-composition-out (LOGO) benchmarks within Al–Cu (MAPE = 39.43 ± 39.71%), we isolate why interdiffusivity folds recover once diffusion modalities are encoded whereas tracer folds remain bounded by a ~3× thermodynamic scale offset (Darken factor) and neighborhood sparsity.

All data tables, training scripts, and multi-seed evaluation protocols are provided to ensure full reproducibility. This manuscript is original, has not been published previously, and is not under consideration elsewhere. All authors have approved the manuscript and declare no competing interests. This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

Suggested topical fit: multi-fidelity / scientific machine learning; computational materials transport.

Thank you for your consideration.

Sincerely,  

Yuwen Cui  
Corresponding author  
Tech Institute for Advanced Materials & College of Materials Science and Engineering, Nanjing Tech University, Nanjing 211816, China  
Email: ycui@njtech.edu.cn  

On behalf of: Junhua Bai, Guanglong Xu, Fuwen Chen, Yuwen Cui  

---

**Manuscript files (submission package):** `main.tex`, `refs.bib`, Figs. 1–9 (PDF) plus SI figures, Highlights, Keywords. Prefer the LaTeX sources over any Word authoring copies.
