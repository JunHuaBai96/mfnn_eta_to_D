# -*- coding: utf-8 -*-
"""Strict Gemini SI S1-S5 renumber + sync captions/tex/md/docx."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
FIG = ROOT / "outputs" / "figures"
WIDTH = Inches(6.0)

PNG = {
    "S1": FIG / "FigS1_alpha_mixing_weights.png",
    "S2": FIG / "FigS2_protocol_G_variance.png",
    "S3": FIG / "FigS3_al80_anchor_k.png",
    "S4": FIG / "FigS4_al80_posthoc_shift.png",
    "S5": FIG / "FigS5_difftype_split_ablation.png",
    "S6": FIG / "FigS6_al80_upweight_w.png",
}

CAPTIONS = {
    "S1": (
        "Fig. S1. Protocol W residual-MFNN mixing weights α1 (linear) and α2 (nonlinear residual) "
        "from five within_T checkpoints (seeds 0,1,2,42,123). Frozen means α1 = 0.5369±0.1200, "
        "α2 = 0.6525±0.0301 (population std, ddof = 0). SI diagnostic only. Not a PINN/PPINN formulation."
    ),
    "S2": (
        "Fig. S2 (caution). Protocol W versus random between-group Protocol G for residual MFNN "
        "(frozen MAPE 26.18±1.33% vs 27.36±12.88%). (a) Mean±seed std; (b) per-seed trajectories. "
        "Protocol G is cautionary only (Al–Cu hold-outs; large seed variance)—not a headline claim. "
        "Not a PINN/PPINN formulation."
    ),
    "S3": (
        "Fig. S3. Al80Cu20 tracer few-shot anchor-temperature sensitivity (k = 0,1,2). "
        "Frozen MAPE 178.20/169.55/175.27/142.93%; Factor2 = 0 at all k. SI diagnostic of sparse "
        "neighborhood failure; k>0 is not pure LOGO. Not a PINN/PPINN formulation."
    ),
    "S4": (
        "Fig. S4. Counterfactual Al80Cu20 tracer post-hoc intercept-shift / oracle diagnostic "
        "(frozen shifted MAPE 9.81±1.73%). SI only; not Protocol W or LOGO success. Not a PINN/PPINN formulation."
    ),
    "S5": (
        "Fig. S5. Separate tracer-only / inter-only residual MFNN pools versus joint+diff_type one-hot "
        "(negative ablation). (a) Al80Cu20: separate 173%/11% vs joint 156.5%/6.5%. "
        "(b) Pool-level LOGO means (inter excludes exploding Al70Cu30). SI only. Not a PINN/PPINN formulation."
    ),
    "S6": (
        "Fig. S6 (optional extra; not in Gemini core S1–S5). Al80Cu20 tracer k=2 anchor up-weighting "
        "w=1→5→10 (frozen MAPE 122→48→31%). SI counterfactual only."
    ),
}


def write_captions() -> None:
    path = FIG / "FIGURE_CAPTIONS.md"
    text = path.read_text(encoding="utf-8")
    # Keep main-text part up to SI map / Fig.S1
    # Find start of SI table rows or **Fig. S1
    # Rewrite from the SI section of the map table through end.

    # Split at "## Keep" keep header+main figs until SI rows
    # Simpler: find "| SI Fig. S1 |" and replace from there to EOF after rebuilding SI part.
    # Also keep main figure captions before **Fig. S1.**

    main_end = text.find("**Fig. S1.**")
    if main_end < 0:
        main_end = text.find("**Fig. S1**")
    if main_end < 0:
        raise SystemExit("cannot find Fig.S1 caption start")

    # Also trim SI rows from map table: find first SI Fig row
    map_si = text.find("| SI Fig. S1 |")
    if map_si < 0:
        map_si = text.find("| SI Fig.")
    head = text[:map_si] if map_si > 0 else text[:main_end]

    # Ensure head ends cleanly before SI map
    head = head.rstrip() + "\n"

    si_map = r'''
| SI Fig. S1 | `FigS1_alpha_mixing_weights` | Gemini **S1** (α mixing) | `Fig6_alpha_mixing_weights` |
| SI Fig. S2 | `FigS2_protocol_G_variance` | Gemini **S2** (Protocol G variance caution) | legacy `FigS6_protocol_G_variance`, `Fig8_protocol_W_vs_G` |
| SI Fig. S3 | `FigS3_al80_anchor_k` | Gemini **S3** (few-shot anchor) | `FigS1_al80_anchor_k`, `fig_si_al80_anchor_k` |
| SI Fig. S4 | `FigS4_al80_posthoc_shift` | Gemini **S4** (oracle / post-hoc intercept) | legacy `FigS2_al80_posthoc_shift`, `fig_si_al80_posthoc_shift` |
| SI Fig. S5 | `FigS5_difftype_split_ablation` | Gemini **S5** (tracer/inter split ablation) | `Fig7_ablation_separate_vs_joint` |
| SI Fig. S6 (optional) | `FigS6_al80_upweight_w` | **Not** in Gemini core S1–S5 (up-weight extra) | legacy `FigS4_al80_upweight_w`, `FigS3_al80_upweight_w` |

**Strict Gemini SI (2026-10-22):** S1 α; S2 Protocol G caution; S3 anchor; S4 oracle/posthoc; S5 difftype ablation. Optional S6 = upweight only.

Do not delete legacy filenames. Frozen Protocol W / LOGO / α numbers are unchanged.
'''

    # Main captions remain in head if they were before map_si — but map_si is before captions.
    # Need main figure captions which are between "---" after map and **Fig.S1**
    # Reconstruct: head (through end of main map rows) + si_map + main fig captions + si captions

    # Extract main figure captions (Fig.1–7) from original
    m_start = text.find("**Fig. 1.**")
    m_end = main_end
    main_caps = text[m_start:m_end].rstrip() + "\n" if m_start >= 0 else ""

    # Head should be title + main map rows only (no SI rows)
    # Rebuild head: everything before first SI row, but that includes main map.
    # Current head ends before SI row — good. Then si_map, then "---", then main_caps, then SI captions.

    si_caps = r'''
---

''' + main_caps + r'''
**Fig. S1.** Protocol W residual-MFNN mixing weights $\alpha_1$ (linear path) and $\alpha_2$ (nonlinear residual path) extracted read-only from five within_T checkpoints (seeds $0,1,2,42,123$). Dashed lines mark frozen seed means $\alpha_1=0.5369\pm0.1200$ and $\alpha_2=0.6525\pm0.0301$ (population std, $\mathrm{ddof}=0$). SI diagnostic only; not a headline claim. Not a PINN/PPINN formulation. File: `FigS1_alpha_mixing_weights`.

**Fig. S2 (caution).** Protocol W versus random between-group Protocol G for residual MFNN (frozen MAPE $26.18\pm1.33\%$ vs $27.36\pm12.88\%$). (a) Mean±seed std; (b) per-seed trajectories. Protocol G is **cautionary only** (Al–Cu hold-outs; large seed variance)—not a headline claim. Not a PINN/PPINN formulation. File: `FigS2_protocol_G_variance` (legacy `FigS6_protocol_G_variance` retained).

**Fig. S3.** Al80Cu20 tracer few-shot anchor-temperature sensitivity ($k=0,1,2$). Frozen MAPE $178.20/169.55/175.27/142.93\%$; Factor2 $=0$ at all $k$. SI diagnostic of sparse-neighborhood failure; $k>0$ is not pure LOGO. Not a PINN/PPINN formulation. File: `FigS3_al80_anchor_k`.

**Fig. S4.** Counterfactual Al80Cu20 tracer post-hoc intercept-shift / oracle diagnostic (frozen shifted MAPE $9.81\pm1.73\%$). SI only; must not be read as Protocol W or LOGO success. Not a PINN/PPINN formulation. File: `FigS4_al80_posthoc_shift` (legacy `FigS2_al80_posthoc_shift` retained as compatibility copy).

**Fig. S5.** Separate tracer-only and inter-only residual MFNN pools versus joint training with $\texttt{diff\_type}$ one-hot (negative ablation). (a) Stratified $\mathrm{Al}_{80}\mathrm{Cu}_{20}$: separate $173\%/11\%$ vs joint $156.5\%/6.5\%$. (b) Pool-level LOGO means (inter mean excludes exploding $\mathrm{Al}_{70}\mathrm{Cu}_{30}$ fold). Splitting does not fix sparse tracer neighborhoods. SI only. Not a PINN/PPINN formulation. File: `FigS5_difftype_split_ablation`.

**Fig. S6 (optional; not Gemini core S1–S5).** Al80Cu20 tracer $k=2$ anchor up-weighting $w=1\to5\to10$ (frozen MAPE $122\to48\to31\%$). SI counterfactual only. File: `FigS6_al80_upweight_w`.
'''

    # Avoid duplicate --- / main caps if head already has ---
    out = head + si_map + si_caps
    # Clean duplicate **Fig. 1** if head somehow included them — head stops at SI map row so OK
    path.write_text(out, encoding="utf-8")
    print("wrote captions")


def patch_text_file(path: Path) -> list[str]:
    if not path.is_file():
        return [f"missing {path}"]
    text = path.read_text(encoding="utf-8")
    orig = text
    notes = []

    # Ordered replacements — careful with chains
    reps = [
        # Protocol G: was S6 -> S2
        (r"Fig\.?\s*S6[^\n]{0,40}Protocol G", "Fig. S2 (Protocol G"),
        (r"Figure S6[^\n]{0,40}Protocol G", "Figure S2 (Protocol G"),
        (r"FigS6_protocol_G_variance", "FigS2_protocol_G_variance"),
        (r"fig:S6_G|fig:protocolG|fig:gvar", "fig:protocolG"),
        # posthoc: was S2 -> S4
        (r"Fig\.?\s*S2[^\n]{0,60}(post-hoc|posthoc|oracle|intercept)", r"Fig. S4 (\1"),
        (r"FigS2_al80_posthoc_shift", "FigS4_al80_posthoc_shift"),
        (r"fig_si_al80_posthoc_shift", "FigS4_al80_posthoc_shift"),
        # upweight: was S4 -> S6 optional
        (r"FigS4_al80_upweight_w", "FigS6_al80_upweight_w"),
        # Generic role notes from temporary scheme
        (r"Gemini-plan role \*\*S4\*\* / oracle; Word keeps label S2", "Gemini **S4** / oracle"),
        (r"Gemini-plan role \*\*S2\*\* / Protocol G variance; numbered S6 to avoid Word S2 clash", "Gemini **S2** / Protocol G variance"),
        (r"numbered S6 to avoid Word S2 clash", "strict Gemini S2"),
        (r"Word/file S2.*=.*Gemini-plan \*\*S4\*\*", "Gemini S4 (oracle)"),
        (r"Word keeps label S2", "strict S4"),
    ]
    for a, b in reps:
        text2, n = re.subn(a, b, text, flags=re.I)
        if n:
            notes.append(f"{path.name}: {n}x /{a[:40]}/")
            text = text2

    # Explicit prose fixes for common patterns in md/tex
    plain = [
        ("Fig. S6 (Gemini-plan role **S2**", "Fig. S2 (Gemini **S2**"),
        ("Fig. S2 (Gemini-plan role **S4**", "Fig. S4 (Gemini **S4**"),
        ("Fig. S2** (Gemini-plan role **S4**", "Fig. S4** (Gemini **S4**"),
        ("`FigS6_protocol_G_variance`", "`FigS2_protocol_G_variance`"),
        ("`FigS2_al80_posthoc_shift`", "`FigS4_al80_posthoc_shift`"),
        ("Figs.~S2–S4", "Figs.~S1–S5"),
        ("Figs. S2–S4", "Figs. S1–S5"),
        ("cf. Figs.~S2–S4", "cf. Figs.~S1–S5"),
    ]
    for a, b in plain:
        if a in text:
            text = text.replace(a, b)
            notes.append(f"{path.name}: replace {a[:50]}")

    if text != orig:
        path.write_text(text, encoding="utf-8")
        notes.append(f"saved {path}")
    else:
        notes.append(f"unchanged {path}")
    return notes


def patch_main_tex() -> list[str]:
    path = ROOT / "outputs" / "jcp_submission" / "main.tex"
    notes = patch_text_file(path)
    text = path.read_text(encoding="utf-8")
    orig = text

    # Ensure SI figure includes exist for S1-S5 if appendix section present
    if "FigS2_protocol_G_variance" not in text and "\\appendix" in text.lower() or True:
        # Add a compact SI figures block before references if not present
        if "FigS2_protocol_G_variance" not in text:
            block = r"""
% --- Strict Gemini SI figures S1-S5 (paths under figures/) ---
% FigS1_alpha_mixing_weights.pdf
% FigS2_protocol_G_variance.pdf
% FigS3_al80_anchor_k.pdf
% FigS4_al80_posthoc_shift.pdf
% FigS5_difftype_split_ablation.pdf
% Optional: FigS6_al80_upweight_w.pdf
"""
            # insert before \begin{thebibliography} or References section
            if "\\begin{thebibliography}" in text:
                text = text.replace("\\begin{thebibliography}", block + "\\begin{thebibliography}", 1)
                notes.append("tex: inserted SI stem comment block")
            elif "\\bibliographystyle" in text:
                text = text.replace("\\bibliographystyle", block + "\\bibliographystyle", 1)
                notes.append("tex: inserted SI stem comment before bibliographystyle")

    # If appendix A still says Fig.S2 for oracle, force S4
    text = re.sub(
        r"(\\caption\{[^}]*?)Fig\.\s*S2([^}]*?(?:oracle|post-hoc|posthoc|intercept))",
        r"\1Fig. S4\2",
        text,
        flags=re.I | re.S,
    )
    text = text.replace("figures/FigS2_al80_posthoc_shift", "figures/FigS4_al80_posthoc_shift")
    text = text.replace("figures/FigS6_protocol_G_variance", "figures/FigS2_protocol_G_variance")

    if text != orig:
        path.write_text(text, encoding="utf-8")
        notes.append("tex saved extra")
    return notes


def insert_paragraph_after(paragraph: Paragraph, text: str = "") -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    if text:
        run = new_para.add_run(text)
        run.font.size = Pt(9)
    return new_para


def clear_drawings(paragraph: Paragraph) -> None:
    for drawing in list(
        paragraph._p.findall(
            ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"
        )
    ):
        parent = drawing.getparent()
        if parent is not None:
            parent.remove(drawing)


def set_picture(paragraph: Paragraph, png: Path) -> None:
    clear_drawings(paragraph)
    for r in paragraph.runs:
        r.text = ""
    run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
    run.add_picture(str(png), width=WIDTH)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def set_caption(paragraph: Paragraph, text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = text
        for r in paragraph.runs[1:]:
            r.text = ""
    else:
        paragraph.add_run(text)
    for r in paragraph.runs:
        r.font.size = Pt(9)


def para_has_image(p: Paragraph) -> bool:
    return bool(
        p._p.findall(
            ".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline"
        )
    )


def find_cap(doc: Document, patterns: list[str]) -> int | None:
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        for pat in patterns:
            if re.search(pat, t, flags=re.I):
                return i
    return None


def find_img_before(doc: Document, cap_i: int) -> int | None:
    for j in range(cap_i - 1, max(-1, cap_i - 6), -1):
        if para_has_image(doc.paragraphs[j]):
            return j
    return None


def replace_or_insert_si(doc: Document, academic: bool) -> list[str]:
    notes = []
    # Body text renumber hints
    for i, p in enumerate(doc.paragraphs):
        t = p.text
        if not t:
            continue
        new = t
        # Temporary scheme cleanups in prose
        new = re.sub(r"Fig\.\s*S6\b(?=[^\n]{0,50}Protocol G)", "Fig. S2", new, flags=re.I)
        new = re.sub(r"Fig\.\s*S2\b(?=[^\n]{0,80}(post-hoc|posthoc|oracle|intercept))", "Fig. S4", new, flags=re.I)
        new = new.replace("Figs. S2–S4", "Figs. S1–S5")
        new = new.replace("Figs.~S2–S4", "Figs.~S1–S5")
        new = new.replace("cf. Figs.~S2–S4", "cf. Figs.~S1–S5")
        if new != t:
            if p.runs:
                p.runs[0].text = new
                for r in p.runs[1:]:
                    r.text = ""
            notes.append(f"body P{i} renum")

    # S1 alpha
    i = find_cap(doc, [r"^Fig\.\s*S1\."])
    if i is not None:
        img = find_img_before(doc, i)
        if img is not None:
            set_picture(doc.paragraphs[img], PNG["S1"])
        set_caption(doc.paragraphs[i], CAPTIONS["S1"])
        notes.append("S1 updated")

    # Current S2 may be posthoc — retarget to Protocol G (S2) image+caption
    i = find_cap(doc, [r"^Fig\.\s*S2\b"])
    if i is not None:
        img = find_img_before(doc, i)
        t = doc.paragraphs[i].text
        if "post-hoc" in t.lower() or "oracle" in t.lower() or "intercept" in t.lower():
            # This was old S2=oracle; will become S4 below — first change label by rewriting after we handle
            pass
        # Force S2 = Protocol G
        if img is not None:
            set_picture(doc.paragraphs[img], PNG["S2"])
        set_caption(doc.paragraphs[i], CAPTIONS["S2"])
        notes.append("S2 -> Protocol G")

    # S3 anchor — keep
    i = find_cap(doc, [r"^Fig\.\s*S3\b"])
    if i is not None:
        img = find_img_before(doc, i)
        if img is not None:
            set_picture(doc.paragraphs[img], PNG["S3"])
        set_caption(doc.paragraphs[i], CAPTIONS["S3"])
        notes.append("S3 anchor")

    # Find old posthoc content now wrongly labeled or need S4
    # After forcing S2 to G, we need S4 posthoc somewhere.
    i4 = find_cap(doc, [r"^Fig\.\s*S4\b"])
    if i4 is not None:
        t = doc.paragraphs[i4].text.lower()
        if "up-weight" in t or "upweight" in t or "w=1" in t:
            # was upweight at S4 — move to optional S6 later; replace this slot with posthoc S4
            img = find_img_before(doc, i4)
            if img is not None:
                set_picture(doc.paragraphs[img], PNG["S4"])
            set_caption(doc.paragraphs[i4], CAPTIONS["S4"])
            notes.append("S4 slot was upweight -> posthoc")
        elif "post-hoc" in t or "oracle" in t or "intercept" in t or True:
            img = find_img_before(doc, i4)
            if img is not None:
                set_picture(doc.paragraphs[img], PNG["S4"])
            set_caption(doc.paragraphs[i4], CAPTIONS["S4"])
            notes.append("S4 posthoc set")
    else:
        # Insert S4 after S3
        i3 = find_cap(doc, [r"^Fig\.\s*S3\b"])
        if i3 is not None:
            img_p = insert_paragraph_after(doc.paragraphs[i3], "")
            set_picture(img_p, PNG["S4"])
            insert_paragraph_after(img_p, CAPTIONS["S4"])
            notes.append("inserted S4 after S3")
        elif academic:
            # appendix end
            for i, p in enumerate(doc.paragraphs):
                if p.text.strip().startswith("Appendix"):
                    img_p = insert_paragraph_after(p, "")
                    set_picture(img_p, PNG["S4"])
                    insert_paragraph_after(img_p, CAPTIONS["S4"])
                    notes.append("inserted S4 after Appendix")
                    break

    # S5 ablation
    i5 = find_cap(doc, [r"^Fig\.\s*S5\b"])
    if i5 is not None:
        img = find_img_before(doc, i5)
        if img is not None:
            set_picture(doc.paragraphs[img], PNG["S5"])
        set_caption(doc.paragraphs[i5], CAPTIONS["S5"])
        notes.append("S5 updated")
    else:
        # insert after S4
        i4 = find_cap(doc, [r"^Fig\.\s*S4\b"])
        if i4 is not None:
            img_p = insert_paragraph_after(doc.paragraphs[i4], "")
            set_picture(img_p, PNG["S5"])
            insert_paragraph_after(img_p, CAPTIONS["S5"])
            notes.append("inserted S5 after S4")

    # Optional S6 upweight: if an upweight caption exists under wrong number, fix; else insert after S5 for academic
    has_s6 = find_cap(doc, [r"^Fig\.\s*S6\b"]) is not None
    up_i = None
    for i, p in enumerate(doc.paragraphs):
        t = p.text.lower()
        if "up-weight" in t or "upweight" in t or "up-weighting" in t:
            if t.strip().startswith("fig."):
                up_i = i
                break
    if up_i is not None:
        img = find_img_before(doc, up_i)
        if img is not None:
            set_picture(doc.paragraphs[img], PNG["S6"])
        set_caption(doc.paragraphs[up_i], CAPTIONS["S6"])
        notes.append("upweight -> S6 optional")
    elif academic and not has_s6:
        i5 = find_cap(doc, [r"^Fig\.\s*S5\b"])
        if i5 is not None:
            img_p = insert_paragraph_after(doc.paragraphs[i5], "")
            set_picture(img_p, PNG["S6"])
            insert_paragraph_after(img_p, CAPTIONS["S6"])
            notes.append("inserted optional S6 upweight")

    # If EN has no S2/S3/S5, insert a short SI block after S1
    if not academic:
        if find_cap(doc, [r"^Fig\.\s*S2\b"]) is None:
            i1 = find_cap(doc, [r"^Fig\.\s*S1\b"])
            if i1 is not None:
                last = doc.paragraphs[i1]
                for key in ["S2", "S3", "S4", "S5"]:
                    img_p = insert_paragraph_after(last, "")
                    set_picture(img_p, PNG[key])
                    last = insert_paragraph_after(img_p, CAPTIONS[key])
                notes.append("EN: inserted S2-S5 after S1")

    return notes


def verify_docx(path: Path) -> list[str]:
    doc = Document(str(path))
    out = []
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if re.match(r"^Fig\.\s*S\d", t):
            img = find_img_before(doc, i) is not None
            out.append(f"{t[:90]} | img_before={img}")
    return out


def scan_residuals() -> list[str]:
    hits = []
    patterns = [
        r"FigS6_protocol_G_variance",
        r"FigS2_al80_posthoc_shift",
        r"FigS4_al80_upweight_w",  # old upweight at S4 stem still may exist as file; flag in text refs only
        r"Word keeps label S2",
        r"numbered S6 to avoid",
        r"Gemini-plan role \*\*S4\*\*.*S2",
        r"Fig\.\s*S6[^\n]{0,40}Protocol G",
        r"Fig\.\s*S2[^\n]{0,60}post-hoc",
    ]
    roots = [
        ROOT / "outputs" / "figures" / "FIGURE_CAPTIONS.md",
        ROOT / "outputs" / "jcp_submission" / "main.tex",
        ROOT / "outputs" / "PAPER_JCP_draft_EN.md",
        ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN.md",
    ]
    for path in roots:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pat in patterns:
            for m in re.finditer(pat, text, flags=re.I):
                # allow legacy mentions in parentheses "legacy `FigS2_al80_posthoc`"
                line = text[max(0, m.start() - 40) : m.end() + 40]
                if "legacy" in line.lower() or "retained" in line.lower() or "compatibility" in line.lower():
                    continue
                if "optional" in line.lower() and "FigS6_al80_upweight" in line:
                    continue
                hits.append(f"{path.name}: ...{line.replace(chr(10),' ')}...")
    return hits


def main() -> None:
    for p in PNG.values():
        if not p.exists():
            raise FileNotFoundError(p)

    write_captions()

    all_notes = []
    all_notes.extend(patch_main_tex())
    for md in [
        ROOT / "outputs" / "PAPER_JCP_draft_EN.md",
        ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN.md",
    ]:
        all_notes.extend(patch_text_file(md))

    # Re-write captions already done; patch_text_file on captions would mess — skip

    docx_paths = [
        ROOT / "outputs" / "PAPER_JCP_draft_EN.docx",
        ROOT / "outputs" / "PAPER_JCP_draft_EN_academic.docx",
        ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN.docx",
        ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN_academic.docx",
    ]
    backups = []
    for path in docx_paths:
        if not path.exists():
            continue
        bak = path.with_name(path.stem + "_backup_pre_gemini_si_strict.docx")
        if not bak.exists():
            shutil.copy2(path, bak)
        backups.append(str(bak))
        doc = Document(str(path))
        academic = "academic" in path.name.lower()
        notes = replace_or_insert_si(doc, academic=academic)
        doc.save(str(path))
        caps = verify_docx(path)
        all_notes.append(f"DOCX {path.name}: {notes}")
        all_notes.append(f"  captions: {caps}")

    # Second pass on captions file already written; ensure no temp scheme left
    # Re-apply write_captions is enough

    residuals = scan_residuals()
    report = ROOT / "outputs" / "_si_strict_s1_s5_report.txt"
    lines = ["SI strict S1-S5 sync report", ""]
    lines.append("Backups:")
    lines.extend("  " + b for b in backups)
    lines.append("")
    lines.append("Notes:")
    lines.extend("  " + n for n in all_notes)
    lines.append("")
    lines.append("Residual old refs (non-legacy):")
    if residuals:
        lines.extend("  " + h for h in residuals)
    else:
        lines.append("  (none)")
    report.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
