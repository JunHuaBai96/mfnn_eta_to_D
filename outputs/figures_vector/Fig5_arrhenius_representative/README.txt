Stem: Fig5_arrhenius_representative

Caption draft:
Figure 5. Representative Arrhenius-style $\log_{10}D$ versus $1000/T$ curves under Protocol W weights (seed 42 checkpoint; inference only, no retraining; 12-D features as stored in the checkpoint). (a) Pure Al self-diffusion: HF experiments with continuous $T$-grid predictions from residual MFNN, HF-only, LF-only, and the modified Sutherland prior ($\eta(T)$ from honest paired viscosities, Assael fallback if needed). (b) $\mathrm{Al}_{80}\mathrm{Cu}_{20}$ Cu-tracer with $\eta(T)$ interpolated from honest Al80Cu20 paired viscosities. Curves illustrate smoothness of the LF-anchored residual MFNN relative to HF-only; not a LOGO success claim. Not a PINN/PPINN formulation. File: `Fig5_arrhenius_representative`.

Layers:
L1_Background_and_Guides: none
L2_Data_Series: exp scatter + model/prior curves
L3_ErrorBars_and_Arrows: none
L4_Typography_and_Math: (a)(b), legends
