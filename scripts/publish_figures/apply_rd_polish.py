# -*- coding: utf-8 -*-
"""Apply polished Results/Discussion to both EN.md and sync main.tex prose."""
from __future__ import annotations
import re
import shutil
from pathlib import Path

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")

def replace_section(text: str, start_h: str, end_h: str, new_body: str) -> str:
    """Replace from ## start_h through just before ## end_h."""
    # new_body includes the ## Results / ## Discussion headers
    i0 = text.find(start_h)
    if i0 < 0:
        raise SystemExit(f"missing {start_h!r}")
    i1 = text.find(end_h, i0 + 1)
    if i1 < 0:
        raise SystemExit(f"missing end {end_h!r}")
    return text[:i0] + new_body.rstrip() + "\n\n" + text[i1:]


def split_polished(polished: str) -> tuple[str, str]:
    i = polished.find("## Discussion")
    if i < 0:
        raise SystemExit("no Discussion in polished")
    return polished[:i].rstrip() + "\n", polished[i:].rstrip() + "\n"


def patch_md(path: Path, results: str, discussion: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_section(text, "## Results", "## Discussion", results)
    text = replace_section(text, "## Discussion", "## Conclusions", discussion)
    path.write_text(text, encoding="utf-8")
    print("patched", path)


# --- TeX prose sync (keep floats/tables; replace surrounding prose) ---
TEX_RESULTS_PROSE = r'''
\subsection{Within-composition performance (primary)}
\label{sec:protocolW}

Protocol~W evaluates within-composition temperature hold-out on a fixed test pool of $n_{\mathrm{test}}=15$ points and five random seeds $\{0,1,2,42,123\}$ (Table~\ref{tab:protocolW}; Figs.~\ref{fig:protocolW}, \ref{fig:residuals}, and~\ref{fig:arrhenius}). Relative to the matched HF-only baseline, the residual MFNN reduces MAPE from $30.98\pm 4.43\%$ to $26.18\pm 1.33\%$ and compresses the seed-to-seed MAPE standard deviation by approximately $70\%$ ($4.43\to 1.33$), while raising $R^{2}$ on $\log_{10} D$ from $0.263\pm 0.076$ to $0.392\pm 0.094$. Factor2 remains near saturation for both MFNN ($0.96\pm 0.033$) and HF-only ($0.973\pm 0.033$). On a fifteen-point test pool the Factor2 difference corresponds to at most one discrete sample across seeds ($1/15\approx 0.067$); the operative gains are therefore continuous accuracy and run-to-run stability rather than Factor2. The LF-only network $F_{\mathrm{L}}$, trained on Sutherland $\log_{10} D_{\mathrm{LF}}$ targets, is not competitive (MAPE $109.6\pm 13.13\%$, Factor2 $0.56\pm 0.10$, $R^{2}=-2.588\pm 0.399$), consistent with systematic magnitude offsets between the physics prior and high-fidelity labels. Learned mixing weights remain nonzero under Protocol~W and are reported in the Supplementary Information (Fig.~S1). Residual structure (Fig.~\ref{fig:residuals}) and representative Arrhenius-style trajectories under a frozen Protocol~W checkpoint (Fig.~\ref{fig:arrhenius}; seed~42, inference only) place the residual MFNN between the LF prior and the HF-only fit without altering frozen headline metrics. This within-composition temperature generalization is the primary quantitative claim of the paper.
'''

TEX_AL80 = r'''
\subsection{Effect of resolving tracer vs interdiffusion labels (Al80Cu20)}
\label{sec:al80}

Before stratification by diffusion type, leave-one-group-out of mixed $\mathrm{Al}_{80}\mathrm{Cu}_{20}$ fails for label-semantic rather than purely compositional reasons. At nearly the same temperature, Cu-tracer diffusivities (Zhang et al.~\cite{zhang2010prl}; $\sim 2.3$--$4.9\times 10^{-9}\,\mathrm{m}^{2}\,\mathrm{s}^{-1}$) conflict with interdiffusivities ($\sim 7$--$8.9\times 10^{-9}\,\mathrm{m}^{2}\,\mathrm{s}^{-1}$) by a factor of approximately three, while the feature vector originally omitted diffusion type and training neighbors at nearby $x_{\mathrm{Cu}}$ remain inter-dominated. Viscosity pairing follows Schick et al.~\cite{schick2012}; missing $\eta$ rows are dropped, and no Kozlov-type silent fill of high-fidelity viscosity is employed.

After partitioning by diffusion type (still without a one-hot type feature), LOGO on the subgroups yields MFNN MAPE $\sim$28.8\% with Factor2 $=1$ for the interdiffusivity hold-out ($n=2$), versus MAPE $\sim$203\% with Factor2 $=0$ for the tracer hold-out ($n=10$). The mixed-group failure therefore concentrates on the dense Zhang tracer grid; interdiffusivity points at the same composition are comparatively well predicted once both scales are no longer forced onto a single scalar head (Fig.~\ref{fig:al80}). Under the one-hot setting of Sec.~\ref{sec:logo}, the stratified $\mathrm{Al}_{80}\mathrm{Cu}_{20}$ folds reach MAPE $6.48\%$ (Factor2 $=1$, $n=2$) for interdiffusivity and MAPE $156.49\%$ (Factor2 $=0$, $n=10$) for tracer.
'''

TEX_LOGO_LEAD = r'''
\subsection{Leave-one-composition-out on Al--Cu}
\label{sec:logo}

Without a diffusion-type one-hot (12 features; 13 folds after subgrouping), MFNN MAPE is $44.11\pm 48.48\%$ across Al--Cu LOGO folds, with large variance driven by hard tracer hold-outs. With diffusion-type one-hot features (16 features; 13 folds), overall MAPE improves to $39.43\pm 39.71\%$. Stratified $\mathrm{Al}_{80}\mathrm{Cu}_{20}$ hold-outs under the one-hot setting are:
'''

TEX_LOGO_TAIL = r'''
One-hot encoding improves the interdiffusivity fold and reduces overall LOGO MAPE, but does not recover the tracer fold when neighboring high-fidelity labels remain mostly inter-scale. Table~\ref{tab:logo} and Fig.~\ref{fig:logo} summarize the comparison. LOGO results are reported as Al--Cu--internal composition transfer only and are presented as a cautionary check rather than a headline claim.
'''

TEX_ABLATION = r'''
\subsection{Ablation: separate tracer / inter models}
\label{sec:ablation}

Training separate networks on tracer-only and inter-only pools does not outperform the joint residual MFNN with a diffusion-type one-hot (Fig.~S5): Al80 tracer MAPE remains $\sim$173\% and Al80 inter $\sim$11\%. The tracer pool is sparse in neighboring compositions with honestly paired $\eta$; the inter pool can lack usable LF targets in some folds. An inter-only LOGO subset that excludes a pathological Al70Cu30 fold yields a more stable $\sim$18$\pm$17\% MAPE and is retained only as a sensitivity check. Separate training is therefore a negative ablation: the bottleneck is neighborhood sparsity of tracer high-fidelity labels under honest viscosity pairing, not the joint residual architecture.
'''

TEX_G = r'''
\subsection{Random between-group protocol (caution)}
\label{sec:protocolG}

Protocol~G (random between-group splits, same five seeds; Fig.~S2) yields MFNN MAPE $27.36\pm 12.88\%$ and Factor2 $0.791\pm 0.257$. All seed hold-outs in this suite are Al--Cu groups, so seed-to-seed variance is dominated by which compositions enter the test set. Single-seed MAPE near $\sim$20\% is therefore not interpreted as final extrapolation performance. Protocol~G is reported strictly as a cautionary check in the Supplementary Information; the primary quantitative claim remains Protocol~W.
'''

TEX_DISCUSSION = r'''
\section{Discussion}
\label{sec:discussion}

\subsection{Physics-guided residual correction under Protocol W}

Under the primary within-composition temperature hold-out, residual multi-fidelity correction improves both mean accuracy and seed stability relative to HF-only (Table~\ref{tab:protocolW}; Figs.~\ref{fig:protocolW}--\ref{fig:arrhenius}). In small-sample liquid-metal diffusivity regimes, unconstrained single-fidelity networks are sensitive to weight initialization when fitting sparse temperature series. Although the LF-only network exhibits large systematic magnitude offsets---reflecting idealized Stokes--Einstein / Sutherland radius and slip/stick assumptions~\cite{sutherland1905,demmel2018}---it encodes the physically expected monotonic $\log_{10} D$--$T$ topology governed by melt viscosity $\eta(T)$. Anchoring the predictor to the continuous $\log_{10} D_{\mathrm{LF}}$ manifold and restricting the high-fidelity branch to a smooth residual correction therefore functions as a physics-guided regularizer in the knowledge-integration sense of Willard et al.~\cite{willard2022}: initialization variance is suppressed without discarding the low-fidelity prior.

This construction follows residual multi-fidelity learning~\cite{lu2020pnas,peherstorfer2018} and the composite multi-fidelity network of Meng and Karniadakis~\cite{meng2020jcp}: high-fidelity correction atop a cheap, continuous prior. LF-only denotes the network $F_{\mathrm{L}}$ trained on Sutherland-generated $\log_{10} D_{\mathrm{LF}}$ from the modified map of Chen et al.~\cite{chen2014} and related Tang multicomponent practice~\cite{tang2015}. Its large Protocol~W MAPE shows that systematic residuals against high-fidelity $D$ are expected once tracer/inter definitions, radius assumptions, and alloy chemistry enter. The residual MFNN retains that map as an explicit LF channel rather than discarding physics. The present $\eta\to D$ model is deliberately not a PDE-residual physics-informed neural network (PINN) or parallel-in-time PINN (PPINN)~\cite{karniadakis2021}: scientific content enters through the LF diffusivity channel, not through a governing-equation residual loss.

\subsection{Thermodynamic and neighborhood limits on composition transfer}

Leave-one-composition-out on Al--Cu is limited by label semantics and neighborhood structure, not merely by $x_{\mathrm{Cu}}$ distance. Mixed $\mathrm{Al}_{80}\mathrm{Cu}_{20}$ folds juxtapose Cu-tracer and interdiffusivity high-fidelity labels at nearly the same temperature---a factor-of-three conflict already quantified in Sec.~\ref{sec:al80} and Fig.~\ref{fig:al80}---while features originally omitted diffusion type. After subgrouping and one-hot encoding, overall LOGO improves and the interdiffusivity fold becomes tractable, yet the tracer fold remains failed because training neighbors at nearby $x_{\mathrm{Cu}}$ are inter-dominated (Tables~\ref{tab:logo}; Fig.~\ref{fig:logo}). Separate tracer/inter networks likewise do not outperform the joint model with one-hot features (Fig.~S5). LOGO is therefore reported strictly as Al--Cu--internal composition transfer under stratified labels, not as evidence of robust cross-composition or cross-system generalization.

\subsection{Counterfactual slope--intercept diagnostics (SI only)}

To separate Arrhenius slope error from thermodynamic scale error on the failed Al80Cu20 tracer fold, two counterfactual oracle diagnostics that access held-out composition labels were examined; they are not valid evaluation protocols. A single post-hoc logarithmic offset anchored at $983\,\mathrm{K}$ ($\delta = -0.482\pm 0.046\approx -\log_{10} 3$), applied to frozen $k{=}0$ LOGO predictions, reduces residual error on the remaining nine temperatures from $175.20\pm 28.78\%$ (Factor2 $=0$) to $9.81\pm 1.73\%$ (Factor2 $=1.0$; Fig.~S4), whereas returning that same point to unweighted training ($k{=}1$) leaves MAPE near $\sim$170\% (Factor2 $=0$). Separately, under a $k{=}2$ endpoint-anchor setting, increasing the loss weight of the two tracer anchors from $w=1$ to $5$ and $10$ progressively lowers MAPE ($122\%\to 48\%\to 31\%$) and restores Factor2 ($0.15\to 1.0\to 1.0$; optional Fig.~S6). These checks indicate that the modified-Sutherland LF channel already captures the correct temperature slope, while LOGO failure arises from an unmodeled thermodynamic scale offset ($\sim 3\times$ tracer-versus-inter gap), consistent with the absence of an explicit Darken thermodynamic factor $\Phi$~\cite{Darken1948}, compounded by gradient dilution of sparse tracer anchors under unweighted MSE. The diagnostics isolate failure mechanics only; they do not constitute LOGO generalization or a substitute for Protocol~W.

\subsection{Methodological scope, limitations, and outlook}

The primary quantitative claim is within-composition temperature generalization under Protocol~W ($n_{\mathrm{test}}=15$). Protocol~G (Fig.~S2) and Al--Cu LOGO (Fig.~\ref{fig:logo}) are cautionary checks of between-group and within-system transfer: LOGO remains Al--Cu--internal, with successful interdiffusivity folds coexisting with failed tracer hold-outs, and no cross-system LOGO is claimed. Counterfactual intercept and anchor-weighting diagnostics use held-out group information to isolate slope-versus-intercept mechanics; they are oracle sensitivity checks and are not valid leave-composition generalization protocols, nor do they alter Protocol~W headlines.

Tracer and interdiffusivity labels are not interchangeable; one-hot encoding and separate models do not remedy sparse tracer neighborhoods with honest $\eta$. Missing viscosity samples are dropped, and Kozlov alloy viscosity is never used as a silent high-fidelity $\eta$ fill. Densified Arrhenius temperature grids~\cite{zhang2010prl} inflate sample counts relative to independent experiments, and usable coverage remains Al--Cu--dominated, with Al--Mg--Si and Al--Ce--Ni too thin for system-level leave-one-out claims. Moderate Protocol~W $R^{2}$ on $\log_{10} D$ reflects the small heterogeneous test pool; MAPE and Factor2 remain the primary metrics, consistent with the broader lesson that composition-aware materials property models remain data-limited outside dense neighborhoods~\cite{ward2016}.

Progress on Protocol~G and on tracer LOGO folds would require more tracer high-fidelity points at neighboring compositions paired with measured or Assael/Schick-class $\eta$~\cite{assael2006,schick2012}, denser inter/tracer coverage at shared compositions, and---eventually---thicker Al--Mg--Si / Al--Ce--Ni tables before any cross-system leave-one-out claim is warranted. A Darken-type thermodynamic factor $\Phi$~\cite{Darken1948} is a natural direction for the intercept/scale mismatch diagnosed above, without altering the residual MFNN architecture or Protocol~W claims. Coupling such a corrected diffusivity model to CALPHAD mobility / DICTRA-type kinetic workflows~\cite{andersson2002,tang2015} remains a longer-term application target once tracer neighborhoods thicken.
'''


def replace_between(text: str, start_pat: str, end_pat: str, new: str) -> str:
    m0 = re.search(start_pat, text)
    m1 = re.search(end_pat, text)
    if not m0 or not m1 or m1.start() <= m0.start():
        raise SystemExit(f"bounds fail: {start_pat} / {end_pat}")
    return text[: m0.start()] + new.rstrip() + "\n\n" + text[m1.start() :]


def patch_tex(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    # Replace protocol W prose (from subsection to table)
    text = replace_between(
        text,
        r"\\subsection\{Within-composition performance \(primary\)\}",
        r"\\begin\{table\}\[t\]\s*\n\\centering\s*\n\\caption\{Protocol W",
        TEX_RESULTS_PROSE + "\n",
    )
    # Al80 subsection prose before figure
    text = replace_between(
        text,
        r"\\subsection\{Effect of resolving tracer vs interdiffusion labels \(Al80Cu20\)\}",
        r"\\begin\{figure\}\[t\]\s*\n\\centering\s*\n\\includegraphics\[width=\\linewidth\]\{figures/Fig6_Al80_tracer_inter",
        TEX_AL80 + "\n",
    )
    # LOGO lead before center tabular / or before Without - replace from subsection to \begin{center} or tabular
    text = replace_between(
        text,
        r"\\subsection\{Leave-one-composition-out on Al--Cu\}",
        r"\\begin\{center\}",
        TEX_LOGO_LEAD + "\n",
    )
    # After stratified center block, before Table logo - replace the one-hot paragraph
    # Find "One-hot encoding improves" through before \begin{table} tab:logo OR after center
    text2, n = re.subn(
        r"One-hot encoding improves the inter fold.*?Fig\.~\\ref\{fig:logo\} shows LOGO MAPE bars across configurations\.\s*",
        TEX_LOGO_TAIL.lstrip() + "\n",
        text,
        count=1,
        flags=re.S,
    )
    if n:
        text = text2
        print("tex LOGO tail replaced")
    else:
        # alternate: between end of center and begin{table} tab:logo
        m = re.search(
            r"(\\end\{center\}\s*)(.*?)(\\begin\{table\}\[t\]\s*\n\\centering\s*\n\\caption\{Al--Cu leave-one-composition-out)",
            text,
            flags=re.S,
        )
        if m:
            text = text[: m.start(2)] + TEX_LOGO_TAIL + "\n" + text[m.start(3) :]
            print("tex LOGO tail via center")
        else:
            print("WARN: LOGO tail not found")

    # Remove duplicate LOGO sentence after fig:logo if present
    text = re.sub(
        r"LOGO results are reported as Al--Cu--internal composition extrapolation only; they are not claimed as cross-system generalization\.\s*",
        "",
        text,
        count=1,
    )

    text = replace_between(
        text,
        r"\\subsection\{Ablation: separate tracer / inter models\}",
        r"\\subsection\{Random between-group protocol \(caution\)\}",
        TEX_ABLATION + "\n",
    )
    text = replace_between(
        text,
        r"\\subsection\{Random between-group protocol \(caution\)\}",
        r"%% =+\s*\n\\section\{Discussion\}",
        TEX_G + "\n\n%% ============================================================\n",
    )
    # Discussion through Limitations
    text = replace_between(
        text,
        r"\\section\{Discussion\}",
        r"\\section\{Limitations\}",
        TEX_DISCUSSION + "\n\n%% ============================================================\n",
    )
    path.write_text(text, encoding="utf-8")
    print("patched", path)


def main():
    # polished path: prefer workspace, else scripts copy
    pol_path = ROOT / "scripts" / "publish_figures" / "rd_polished.md"
    if not pol_path.is_file():
        pol_path = Path("/workspace/rd_polished.md")
    polished = pol_path.read_text(encoding="utf-8")
    results, discussion = split_polished(polished)
    for rel in [
        "outputs/PAPER_JCP_draft_EN.md",
        "outputs/jcp_submission/PAPER_JCP_draft_EN.md",
    ]:
        patch_md(ROOT / rel, results, discussion)
    patch_tex(ROOT / "outputs" / "jcp_submission" / "main.tex")
    # self-check frozen numbers
    checks = [
        "26.18\\pm 1.33",
        "30.98\\pm 4.43",
        "0.96\\pm 0.033",
        "0.973\\pm 0.033",
        "0.392\\pm 0.094",
        "109.6\\pm 13.13",
        "-2.588\\pm 0.399",
        "39.43\\pm 39.71",
        "27.36\\pm 12.88",
        "Fig.~S5",
        "Fig.~S2",
        "Fig.~S4",
        "Fig.~S1",
    ]
    for rel in [
        "outputs/PAPER_JCP_draft_EN.md",
        "outputs/jcp_submission/PAPER_JCP_draft_EN.md",
        "outputs/jcp_submission/main.tex",
    ]:
        t = (ROOT / rel).read_text(encoding="utf-8")
        # extract Results+Discussion only for PINN count in discussion
        miss = [c for c in checks if c not in t and c.replace("\\", "") not in t.replace("\\", "")]
        # simpler
        miss = []
        for c in checks:
            if c not in t:
                # try unescaped variants in md
                alt = c.replace("\\pm", "±").replace("\\%", "%").replace("\\mathrm{test}", "test")
                if c not in t and alt not in t:
                    # md uses $\pm$
                    if c.replace("\\pm", "\\pm ") not in t and f"${c}$" not in t:
                        if c not in t:
                            miss.append(c)
        print(rel, "missing", miss if miss else "OK")
        bad = re.findall(r"\*\*Fig\.\s*(?:8|9|10)\.\*\*|(?<![S`\d])Fig\.\s*(?:8|9|10)\b", t)
        print(rel, "fig810", bad[:5] if bad else "clean")
        if "PINN" in t[t.find("## Results") if "## Results" in t else 0 :]:
            pass


if __name__ == "__main__":
    main()
