Stem: Fig1_mfnn_residual_schema
Shortname: fig1

Illustrator 4-layer notes:
L1_Background_and_Guides: panel washes, dashed NN_L/NN_H boxes
L2_Data_Series: schematic curves (A), node fills (input/LF/HF)
L3_ErrorBars_and_Arrows: edges, residual red skip, α mix arrows
L4_Typography_and_Math: panel letters, σ/I labels, residual equation

Caption draft:
Lu-style residual multi-fidelity network for η→D. (A) Modified Sutherland LF prior from viscosity and scarce HF $D_{\mathrm{exp}}$. (B) Single-fidelity NN (HF-only). (C) Composite MFNN with linear $I$ and nonlinear $\sigma$ branches on $[x,y_L]$. (D) Residual MFNN used here: $y_H=\alpha_1(A[x,y_L]+b)+\alpha_2 F_{\mathrm{nl}}(x,y_L)$ with learnable $\alpha_1,\alpha_2$ and red residual link from $y_L$; positivity via $\hat{D}=10^{\hat{y}}$. Not PINN/PPINN.

Cleanup: Select>Object>Clipping Masks (keep scatter clip only); ungroup text; svg.fonttype=none so text stays editable.
Export: PDF Press Quality sRGB; PNG 600 ppi Art Optimized.
Style: full box spines + inward ticks (Lu PNAS-like).
