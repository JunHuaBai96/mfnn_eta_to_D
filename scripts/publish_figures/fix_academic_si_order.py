# -*- coding: utf-8 -*-
"""Restore academic docx from pre_gemini_si_strict backup; rebuild SI S1-S5(+S6) after S1."""
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


def insert_after(paragraph: Paragraph, text: str = "") -> Paragraph:
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


def is_si_caption(t: str) -> bool:
    return bool(re.match(r"^Fig\.\s*S\d", t.strip(), flags=re.I))


def remap_body_only(doc: Document) -> list[str]:
    notes = []
    for i, p in enumerate(doc.paragraphs):
        t = p.text
        if not t or is_si_caption(t):
            continue
        new = t
        new = re.sub(r"Fig\.\s*S6\b(?=[^\n]{0,50}Protocol G)", "Fig. S2", new, flags=re.I)
        new = re.sub(
            r"Fig\.\s*S2\b(?=[^\n]{0,80}(post-hoc|posthoc|oracle|intercept))",
            "Fig. S4",
            new,
            flags=re.I,
        )
        new = new.replace("Figs. S2–S4", "Figs. S1–S5")
        new = new.replace("Figs.~S2–S4", "Figs.~S1–S5")
        new = new.replace("cf. Figs.~S2–S4", "cf. Figs.~S1–S5")
        if new != t:
            if p.runs:
                p.runs[0].text = new
                for r in p.runs[1:]:
                    r.text = ""
            notes.append(f"body P{i} renum")
    return notes


def delete_paragraph(paragraph: Paragraph) -> None:
    el = paragraph._element
    parent = el.getparent()
    if parent is not None:
        parent.remove(el)


def rebuild_si_after_s1(doc: Document) -> list[str]:
    """Keep/update S1; remove all later SI fig blocks; insert S2-S6 in order after S1."""
    notes = []
    i1 = find_cap(doc, [r"^Fig\.\s*S1\."])
    if i1 is None:
        notes.append("ERROR: no S1")
        return notes

    img1 = find_img_before(doc, i1)
    if img1 is not None:
        set_picture(doc.paragraphs[img1], PNG["S1"])
    set_caption(doc.paragraphs[i1], CAPTIONS["S1"])
    notes.append("S1 updated")

    # Collect indices of SI captions S2+ and their preceding images (re-scan each time after deletes)
    # Safer: walk paragraphs after S1 and delete SI image+caption pairs until non-SI content.
    # Because deleting shifts indices, collect element refs first.
    to_delete = []
    paras = list(doc.paragraphs)
    for idx in range(i1 + 1, len(paras)):
        t = paras[idx].text.strip()
        if is_si_caption(t):
            # mark caption
            to_delete.append(paras[idx])
            # mark image before if within 5 paras and after previous SI
            for j in range(idx - 1, max(i1, idx - 6), -1):
                if para_has_image(paras[j]):
                    to_delete.append(paras[j])
                    break
        elif t.startswith("Fig. S") or re.match(r"^Fig\.\s*S\d", t, re.I):
            to_delete.append(paras[idx])
    # unique preserve order
    seen = set()
    uniq = []
    for p in to_delete:
        pid = id(p._p)
        if pid not in seen:
            seen.add(pid)
            uniq.append(p)
    for p in uniq:
        delete_paragraph(p)
    notes.append(f"removed {len(uniq)} old SI paragraphs after S1")

    # Re-find S1 after deletes
    i1 = find_cap(doc, [r"^Fig\.\s*S1\."])
    if i1 is None:
        notes.append("ERROR: S1 lost after delete")
        return notes
    anchor = doc.paragraphs[i1]

    # Insert S2..S6 as (blank?, image, caption) after S1 — insert in reverse so order is S2..S6
    for key in ["S6", "S5", "S4", "S3", "S2"]:
        cap_p = insert_after(anchor, "")
        set_caption(cap_p, CAPTIONS[key])
        img_p = insert_after(anchor, "")
        set_picture(img_p, PNG[key])
        notes.append(f"inserted {key}")

    return notes


def process_academic(path: Path, backup: Path) -> list[str]:
    notes = [f"restore from {backup.name}"]
    shutil.copy2(backup, path)
    doc = Document(str(path))
    notes.extend(remap_body_only(doc))
    notes.extend(rebuild_si_after_s1(doc))
    doc.save(str(path))
    # verify order
    caps = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if is_si_caption(t):
            img = False
            # find prior image among live paras — approximate via previous sibling walk
            caps.append(t[:70])
    notes.append("captions_order=" + " | ".join(caps))
    return notes


def main():
    pairs = [
        (
            ROOT / "outputs" / "PAPER_JCP_draft_EN_academic.docx",
            ROOT / "outputs" / "PAPER_JCP_draft_EN_academic_backup_pre_gemini_si_strict.docx",
        ),
        (
            ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN_academic.docx",
            ROOT
            / "outputs"
            / "jcp_submission"
            / "PAPER_JCP_draft_EN_academic_backup_pre_gemini_si_strict.docx",
        ),
    ]
    for path, bak in pairs:
        print("===", path.name, "===")
        for n in process_academic(path, bak):
            print(" ", n)


if __name__ == "__main__":
    main()
