# -*- coding: utf-8 -*-
"""Update Word drafts to Gemini figure numbering with PNG embeds."""
from __future__ import annotations

import re
import shutil
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
FIG = ROOT / "outputs" / "figures"
WIDTH = Inches(6.3)

PNG = {
    "1": FIG / "Fig1_mfnn_residual_schema.png",
    "2": FIG / "Fig2_phase_space_coverage.png",
    "3": FIG / "Fig3_protocol_W_parity_metrics.png",
    "4": FIG / "Fig4_protocol_W_residual_topology.png",
    "5": FIG / "Fig5_arrhenius_representative.png",
    "6": FIG / "Fig6_Al80_tracer_inter.png",
    "7": FIG / "Fig7_LOGO_distance_caution.png",
    "S1": FIG / "FigS1_alpha_mixing_weights.png",
    "S2": FIG / "FigS2_al80_posthoc_shift.png",
    "S3": FIG / "FigS3_al80_anchor_k.png",
    "A1": FIG / "figA1_oracle_Al80_tracer.png",
}

CAPTIONS = {
    "1": (
        "Fig. 1. Schematic of the residual multi-fidelity neural network (MFNN) for predicting "
        "high-fidelity liquid diffusivity D from viscosity η (Lu et al., PNAS 2020 style). "
        "(A) Modified Sutherland LF prior versus scarce HF D_exp. (B) HF-only NN. "
        "(C) Composite MFNN. (D) Residual MFNN used here with learnable α1, α2; positivity via "
        "10^ŷ. Not a PINN/PPINN formulation."
    ),
    "2": (
        "Fig. 2. Phase-space coverage and physical context with honest viscosity pairing (no Kozlov fills). "
        "(a) HF temperature–composition coverage (Al–Cu by modality; sparse multi-component versus "
        "non-Al solute fraction). (b) Experimental D versus η with modified Sutherland LF prior at the "
        "same (T, η) and a pure-Al Sutherland guide at T = 1000 K. Not a PINN/PPINN formulation."
    ),
    "3": (
        "Fig. 3. Protocol W (five seeds 0,1,2,42,123; n_test = 15/seed) for residual MFNN versus "
        "HF-only and LF-only. (a) Seed-mean log10 D parity with across-seed std and ±log10 2 band. "
        "(b) MAPE (%): LF-only 109.6±13.13, HF-only 30.98±4.43, residual MFNN 26.18±1.33. "
        "(c) Factor2: 0.56±0.10, 0.973±0.033, 0.96±0.033 (frozen table values). Not a PINN/PPINN formulation."
    ),
    "4": (
        "Fig. 4. Protocol W residual topology for the residual MFNN (seed-mean predictions). "
        "(a) Absolute log10 D error versus T (dashed: log10 2). (b) Signed residual versus LF-only "
        "proxy for y_L. Does not alter frozen Protocol W metrics. Not a PINN/PPINN formulation."
    ),
    "5": (
        "Fig. 5. Representative Arrhenius-style log10 D versus 1000/T using Protocol W seed-42 weights "
        "(inference only; no retraining). (a) Pure Al self-diffusion; (b) Al80Cu20 Cu-tracer. "
        "Curves: residual MFNN, HF-only, LF-only, and modified Sutherland prior with honest η(T). "
        "Not a LOGO success claim; not a PINN/PPINN formulation."
    ),
    "6": (
        "Fig. 6. Label conflict at Al80Cu20. (a) HF D versus T: Cu-tracer below interdiffusivity by ~3× "
        "near 983 K. (b) LOGO MFNN MAPE after diff_type split + one-hot: Al80Cu20_tracer 156.5% "
        "(Factor2 = 0, n = 10) versus Al80Cu20_inter 6.5% (Factor2 = 1, n = 2)."
    ),
    "7": (
        "Fig. 7 (caution). Al–Cu LOGO MFNN after diff_type split + one-hot (13 folds). "
        "(a) MAPE by hold-out (frozen mean 39.4±39.7%). (b) MAPE versus Δx_Cu to the nearest distinct "
        "HF training composition. Composition-extrapolation caution within Al–Cu only—not a headline "
        "success claim and not a cross-alloy transfer result. Not a PINN/PPINN formulation."
    ),
    "S1": (
        "Fig. S1. Protocol W residual-MFNN mixing weights α1 (linear) and α2 (nonlinear residual) "
        "from five within_T checkpoints. Frozen means α1 = 0.5369±0.1200, α2 = 0.6525±0.0301 "
        "(population std, ddof = 0). SI diagnostic only."
    ),
    "S2": (
        "Fig. S2. Counterfactual Al80Cu20 tracer post-hoc intercept-shift / oracle diagnostic "
        "(SI only; not a Protocol W metric and not LOGO success)."
    ),
    "S3": (
        "Fig. S3. Few-shot Al80Cu20 tracer anchor-temperature sensitivity (SI diagnostic of sparse "
        "neighborhood failure; not a main-text claim)."
    ),
}


def insert_paragraph_after(paragraph: Paragraph, text: str = "", style: str | None = None) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    if style is not None:
        try:
            new_para.style = style
        except Exception:
            pass
    if text:
        run = new_para.add_run(text)
        run.font.size = Pt(9)
    return new_para


def clear_paragraph_drawings(paragraph: Paragraph) -> None:
    for drawing in list(
        paragraph._p.findall(
            ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"
        )
    ):
        parent = drawing.getparent()
        if parent is not None:
            parent.remove(drawing)
    # also remove empty remnant runs that only held drawings
    for r in list(paragraph._p.findall(qn("w:r"))):
        if not "".join(r.itertext()).strip() and r.find(qn("w:drawing")) is None:
            # keep runs with pict/object? if completely empty of text and no drawing left, ok to keep one
            pass


def set_paragraph_picture(paragraph: Paragraph, png: Path, width=WIDTH) -> None:
    clear_paragraph_drawings(paragraph)
    # remove all text runs content
    for r in list(paragraph.runs):
        r.text = ""
    # ensure at least one run
    if paragraph.runs:
        run = paragraph.runs[0]
    else:
        run = paragraph.add_run()
    run.add_picture(str(png), width=width)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def set_caption_text(paragraph: Paragraph, text: str) -> None:
    # replace all run texts with a single caption
    if paragraph.runs:
        paragraph.runs[0].text = text
        for r in paragraph.runs[1:]:
            r.text = ""
    else:
        paragraph.add_run(text)
    for r in paragraph.runs:
        if r.font.size is None:
            r.font.size = Pt(9)


def para_has_image(paragraph: Paragraph) -> bool:
    return bool(
        paragraph._p.findall(
            ".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline"
        )
    )


def find_caption_index(doc: Document, patterns: list[str]) -> int | None:
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        for pat in patterns:
            if re.search(pat, t, flags=re.I):
                return i
    return None


def find_image_before_caption(doc: Document, cap_i: int) -> int | None:
    for j in range(cap_i - 1, max(-1, cap_i - 6), -1):
        if para_has_image(doc.paragraphs[j]):
            return j
    return None


def replace_body_refs(doc: Document, academic: bool) -> list[str]:
    notes = []
    # ordered careful replacements on paragraph text (not captions we just set)
    repls = [
        # Protocol W figure number: old Fig.2 -> Fig.3
        (r"(Table\s*3;\s*)Fig\.\s*2\b", r"\1Fig. 3"),
        (r"(Table\s*1;\s*)Fig\.\s*2\b", r"\1Fig. 3"),
        (r"Fig\.\s*2 shows protocol W", "Fig. 3 shows protocol W"),
        (r"Fig\.\s*2\)", "Fig. 3)"),  # rare
        # Al80: old Fig.3 -> Fig.6
        (r"Fig\.\s*3 contrasts Al80", "Fig. 6 contrasts Al80"),
        (r"(at Al.?80.?Cu.?20[^.]*?)Fig\.\s*3\b", r"\1Fig. 6"),
        # LOGO: old Fig.4 -> Fig.7
        (r"(Table\s*5 and )Fig\.\s*4\b", r"\1Fig. 7"),
        (r"Fig\.\s*4 summarize Al", "Fig. 7 summarize Al"),
        (r"Fig\.\s*4 summarizes Al", "Fig. 7 summarizes Al"),
        # Appendix A.1 -> Fig. S2
        (r"Fig\.\s*A\.1\b", "Fig. S2"),
        (r"Figure A\.1\b", "Fig. S2"),
    ]
    for i, p in enumerate(doc.paragraphs):
        t = p.text
        if not t:
            continue
        # skip pure caption lines we manage separately
        if re.match(r"^(Fig\.|Figure)\s*(\d+|S\d+|A\.1)\b", t.strip()):
            # still allow A.1 rename if not yet updated
            if re.match(r"^(Fig\.|Figure)\s*A\.1\b", t.strip()):
                new = re.sub(r"^(Fig\.|Figure)\s*A\.1\b", "Fig. S2", t.strip())
                # keep rest of caption after first sentence start
                if t.strip().startswith("Fig. A.1") or t.strip().startswith("Figure A.1"):
                    set_caption_text(p, CAPTIONS["S2"])
                    notes.append(f"P{i}: caption A.1 -> S2")
            continue
        orig = t
        new = t
        for a, b in repls:
            new = re.sub(a, b, new)
        if new != orig:
            # rewrite runs carefully
            if p.runs:
                p.runs[0].text = new
                for r in p.runs[1:]:
                    r.text = ""
            else:
                p.add_run(new)
            notes.append(f"P{i}: body ref updated")
    return notes


def insert_figure_after(paragraph: Paragraph, png: Path, caption: str) -> Paragraph:
    """Insert image paragraph then caption paragraph after `paragraph`. Returns caption para."""
    img_p = insert_paragraph_after(paragraph, "")
    set_paragraph_picture(img_p, png)
    cap_p = insert_paragraph_after(img_p, caption)
    return cap_p


def process_academic(doc: Document) -> dict:
    report = {"replaced": [], "inserted": [], "notes": []}

    # --- Fig.1 ---
    cap1 = find_caption_index(doc, [r"^Fig\.\s*1\.\s*Schematic", r"^Fig\.\s*1\.\s*Schematic of the residual"])
    if cap1 is None:
        cap1 = find_caption_index(doc, [r"^Fig\.\s*1\."])
    img1 = find_image_before_caption(doc, cap1) if cap1 is not None else None
    if img1 is not None:
        set_paragraph_picture(doc.paragraphs[img1], PNG["1"])
        set_caption_text(doc.paragraphs[cap1], CAPTIONS["1"])
        report["replaced"].append("Fig.1 <- Fig1_mfnn_residual_schema.png")
    else:
        report["notes"].append("Fig.1 image not found")

    # --- Insert Fig.S1 after alpha table mention / Table 1 if present ---
    # Prefer after paragraph mentioning mixing weights table
    s1_anchor = None
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t.startswith("Table 1.") and "mixing weights" in t.lower():
            s1_anchor = i
            break
    if s1_anchor is not None and "Fig. S1" not in "\n".join(x.text for x in doc.paragraphs):
        # insert after the table object is hard; insert after the Table 1 caption paragraph
        insert_figure_after(doc.paragraphs[s1_anchor], PNG["S1"], CAPTIONS["S1"])
        report["inserted"].append("Fig.S1 <- FigS1_alpha_mixing_weights.png (after Table 1 caption)")

    # --- Insert Fig.2 after data provenance / before Evaluation protocols ---
    # Anchor: paragraph starting with "Rows lacking" or "Each sample carries" — insert after HF diffusivities paragraph block end
    if "Fig. 2. Phase-space" not in "\n".join(p.text for p in doc.paragraphs):
        anchor = None
        for i, p in enumerate(doc.paragraphs):
            if p.text.strip().startswith("Each sample carries a composition-group label"):
                anchor = i
                break
        if anchor is None:
            for i, p in enumerate(doc.paragraphs):
                if p.text.strip().startswith("Data provenance"):
                    anchor = i
                    break
        if anchor is not None:
            insert_figure_after(doc.paragraphs[anchor], PNG["2"], CAPTIONS["2"])
            report["inserted"].append("Fig.2 <- Fig2_phase_space_coverage.png")
            # refresh indices by re-finding later figures from captions

    # Re-scan for old Protocol W / Al80 / LOGO captions (numbers may have shifted after inserts)
    # Current state may still say Fig. 2 Protocol W — replace image+caption -> Fig.3
    cap_pw = find_caption_index(doc, [r"^Fig\.\s*2\.\s*Protocol W", r"^Fig\.\s*3\.\s*Protocol W"])
    if cap_pw is not None:
        img = find_image_before_caption(doc, cap_pw)
        if img is not None:
            set_paragraph_picture(doc.paragraphs[img], PNG["3"])
        set_caption_text(doc.paragraphs[cap_pw], CAPTIONS["3"])
        report["replaced"].append("Fig.3 (was Protocol W slot) <- Fig3_protocol_W_parity_metrics.png")

        # Insert Fig.4 and Fig.5 after this caption if not present
        joined = "\n".join(p.text for p in doc.paragraphs)
        if "Fig. 4. Protocol W residual" not in joined:
            # after caption paragraph
            cap4 = insert_figure_after(doc.paragraphs[cap_pw], PNG["4"], CAPTIONS["4"])
            report["inserted"].append("Fig.4 <- Fig4_protocol_W_residual_topology.png")
            # Fig.5 after Fig.4 caption — need fresh reference: last inserted is caption of Fig4
            # find it again
            cap4_i = find_caption_index(doc, [r"^Fig\.\s*4\.\s*Protocol W residual"])
            if cap4_i is not None and "Fig. 5. Representative Arrhenius" not in "\n".join(
                p.text for p in doc.paragraphs
            ):
                insert_figure_after(doc.paragraphs[cap4_i], PNG["5"], CAPTIONS["5"])
                report["inserted"].append("Fig.5 <- Fig5_arrhenius_representative.png")

    # Al80: caption still Fig. 3 Label conflict OR already Fig.6
    cap_al = find_caption_index(
        doc, [r"^Fig\.\s*3\.\s*Label conflict", r"^Fig\.\s*6\.\s*Label conflict"]
    )
    if cap_al is not None:
        img = find_image_before_caption(doc, cap_al)
        if img is not None:
            set_paragraph_picture(doc.paragraphs[img], PNG["6"])
        set_caption_text(doc.paragraphs[cap_al], CAPTIONS["6"])
        report["replaced"].append("Fig.6 <- Fig6_Al80_tracer_inter.png")

    # LOGO
    cap_logo = find_caption_index(
        doc,
        [
            r"^Fig\.\s*4\.\s*Al",
            r"^Fig\.\s*7 \(caution\)",
            r"^Fig\.\s*7\.\s*Al",
            r"^Fig\.\s*7 \(caution\)\.",
        ],
    )
    # also match "Fig. 4. Al–Cu LOGO"
    if cap_logo is None:
        for i, p in enumerate(doc.paragraphs):
            t = p.text.strip()
            if "LOGO MFNN MAPE" in t and t.startswith("Fig."):
                cap_logo = i
                break
    if cap_logo is not None:
        img = find_image_before_caption(doc, cap_logo)
        if img is not None:
            set_paragraph_picture(doc.paragraphs[img], PNG["7"])
        set_caption_text(doc.paragraphs[cap_logo], CAPTIONS["7"])
        report["replaced"].append("Fig.7 <- Fig7_LOGO_distance_caution.png")

    # Appendix oracle -> S2 image (prefer posthoc; fallback A1 png)
    cap_a = find_caption_index(
        doc, [r"^Fig\.\s*A\.1", r"^Fig\.\s*S2\.", r"^Figure A\.1"]
    )
    if cap_a is not None:
        img = find_image_before_caption(doc, cap_a)
        png = PNG["S2"] if PNG["S2"].exists() else PNG["A1"]
        if img is not None:
            set_paragraph_picture(doc.paragraphs[img], png)
        set_caption_text(doc.paragraphs[cap_a], CAPTIONS["S2"])
        report["replaced"].append(f"Fig.S2 <- {png.name}")

        # Insert S3 after S2 if missing
        if "Fig. S3." not in "\n".join(p.text for p in doc.paragraphs):
            cap_s2 = find_caption_index(doc, [r"^Fig\.\s*S2\."])
            if cap_s2 is not None:
                insert_figure_after(doc.paragraphs[cap_s2], PNG["S3"], CAPTIONS["S3"])
                report["inserted"].append("Fig.S3 <- FigS3_al80_anchor_k.png")

    report["notes"].extend(replace_body_refs(doc, academic=True))

    # Fix Protocol W prose if still says Fig. 2 for metrics
    for i, p in enumerate(doc.paragraphs):
        t = p.text
        if "Protocol W" in t and "Fig. 2" in t and "coverage" not in t.lower():
            # likely the results sentence
            if "five random seeds" in t or "improves upon" in t or "MAPE" in t:
                new = t.replace("Fig. 2", "Fig. 3")
                if new != t:
                    if p.runs:
                        p.runs[0].text = new
                        for r in p.runs[1:]:
                            r.text = ""
                    report["notes"].append(f"P{i}: Protocol W ref Fig.2->3")

    # Mention Fig.2/4/5 lightly if missing in Protocol W results paragraph
    for i, p in enumerate(doc.paragraphs):
        t = p.text
        if t.startswith("Under Protocol W, the residual MFNN improves"):
            if "Fig. 4" not in t:
                new = t
                # ensure Fig. 3 mentioned
                new = re.sub(r"Fig\.\s*2\b", "Fig. 3", new)
                if "Fig. 3" in new and "Figs." not in new:
                    new = new.replace("Fig. 3)", "Figs. 3–5)")
                    new = new.replace("Fig. 3;", "Figs. 3–5;")
                    new = new.replace("; Fig. 3.", "; Figs. 3–5.")
                    new = new.replace("(Table 3; Fig. 3)", "(Table 3; Figs. 3–5)")
                if new != t and p.runs:
                    p.runs[0].text = new
                    for r in p.runs[1:]:
                        r.text = ""
                    report["notes"].append(f"P{i}: expanded to Figs. 3-5")
            break

    # Coverage mention near Fig.1 prose
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t.startswith("Fig. 1 illustrates") and "Fig. 2" not in t:
            new = t.rstrip(".") + ". Fig. 2 summarizes honest η-paired HF coverage and the Sutherland prior context."
            if p.runs:
                p.runs[0].text = new
                for r in p.runs[1:]:
                    r.text = ""
            report["notes"].append(f"P{i}: added Fig.2 coverage mention")
            break

    return report


def process_plain_en(doc: Document) -> dict:
    """Non-academic EN draft: short 'Figure N.' captions."""
    report = {"replaced": [], "inserted": [], "notes": []}

    # Build list of (img_i, cap_i, kind) by scanning
    # Fig.1
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip().startswith("Fig. 1.") and "Schematic" in p.text:
            img = find_image_before_caption(doc, i)
            if img is not None:
                set_paragraph_picture(doc.paragraphs[img], PNG["1"])
            set_caption_text(doc.paragraphs[i], CAPTIONS["1"])
            report["replaced"].append("Fig.1 <- Fig1_mfnn_residual_schema.png")
            break

    # Insert Fig.2 after dataset summary section
    if "Fig. 2. Phase-space" not in "\n".join(x.text for x in doc.paragraphs):
        anchor = None
        for i, p in enumerate(doc.paragraphs):
            if p.text.strip().startswith("3.1. Dataset summary") or p.text.strip().startswith(
                "After η-pairing"
            ) or p.text.strip().startswith("After η-pairing") or "usable table is Al" in p.text:
                if "usable table is Al" in p.text or p.text.strip().startswith("After"):
                    anchor = i
                    break
        if anchor is not None:
            insert_figure_after(doc.paragraphs[anchor], PNG["2"], CAPTIONS["2"])
            report["inserted"].append("Fig.2 <- Fig2_phase_space_coverage.png")

    # Protocol W: look for "Figure 2." short caption OR Fig.2 Protocol
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t in ("Figure 2.", "Fig. 2.") or t.startswith("Fig. 2. Protocol"):
            img = find_image_before_caption(doc, i)
            if img is not None:
                set_paragraph_picture(doc.paragraphs[img], PNG["3"])
            set_caption_text(doc.paragraphs[i], CAPTIONS["3"])
            report["replaced"].append("Fig.3 <- Fig3_protocol_W_parity_metrics.png")
            # insert 4 and 5 after
            if "Fig. 4. Protocol W residual" not in "\n".join(x.text for x in doc.paragraphs):
                insert_figure_after(doc.paragraphs[i], PNG["4"], CAPTIONS["4"])
                report["inserted"].append("Fig.4 <- Fig4_protocol_W_residual_topology.png")
                cap4 = find_caption_index(doc, [r"^Fig\.\s*4\.\s*Protocol W residual"])
                if cap4 is not None:
                    insert_figure_after(doc.paragraphs[cap4], PNG["5"], CAPTIONS["5"])
                    report["inserted"].append("Fig.5 <- Fig5_arrhenius_representative.png")
            break

    # Al80 Figure 3.
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t in ("Figure 3.", "Fig. 3.") or t.startswith("Fig. 3. Label"):
            # only if not already residual/protocol captions
            img = find_image_before_caption(doc, i)
            # Heuristic: if nearby prose mentions Al80
            nearby = " ".join(doc.paragraphs[j].text for j in range(max(0, i - 5), min(len(doc.paragraphs), i + 2)))
            if "Al80" in nearby or "Al₈₀" in nearby or "tracer" in nearby.lower() or t.startswith("Fig. 3. Label"):
                if img is not None:
                    set_paragraph_picture(doc.paragraphs[img], PNG["6"])
                set_caption_text(doc.paragraphs[i], CAPTIONS["6"])
                report["replaced"].append("Fig.6 <- Fig6_Al80_tracer_inter.png")
                break

    # LOGO Figure 4.
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t in ("Figure 4.", "Fig. 4.") or "LOGO" in t and t.startswith("Fig. 4"):
            nearby = " ".join(doc.paragraphs[j].text for j in range(max(0, i - 6), min(len(doc.paragraphs), i + 2)))
            if "LOGO" in nearby or "leave-one" in nearby.lower() or t in ("Figure 4.", "Fig. 4."):
                # avoid replacing residual Fig.4
                if "residual topology" in t:
                    continue
                img = find_image_before_caption(doc, i)
                if img is not None:
                    set_paragraph_picture(doc.paragraphs[img], PNG["7"])
                set_caption_text(doc.paragraphs[i], CAPTIONS["7"])
                report["replaced"].append("Fig.7 <- Fig7_LOGO_distance_caution.png")
                break

    # SI S1 after alpha discussion if any
    joined = "\n".join(p.text for p in doc.paragraphs)
    if "Fig. S1." not in joined:
        for i, p in enumerate(doc.paragraphs):
            if "alpha_1" in p.text or "α1" in p.text or "mixing weights" in p.text.lower():
                insert_figure_after(doc.paragraphs[i], PNG["S1"], CAPTIONS["S1"])
                report["inserted"].append("Fig.S1 <- FigS1_alpha_mixing_weights.png")
                break

    report["notes"].extend(replace_body_refs(doc, academic=False))
    # plain EN specific
    for i, p in enumerate(doc.paragraphs):
        t = p.text
        if "Fig. 2 shows protocol W" in t:
            new = t.replace("Fig. 2 shows protocol W", "Fig. 3 shows protocol W")
            if p.runs:
                p.runs[0].text = new
                for r in p.runs[1:]:
                    r.text = ""
            report["notes"].append(f"P{i}: EN Fig.2->3 shows")
        if "Fig. 3 contrasts Al80" in t:
            new = t.replace("Fig. 3 contrasts Al80", "Fig. 6 contrasts Al80")
            if p.runs:
                p.runs[0].text = new
                for r in p.runs[1:]:
                    r.text = ""
            report["notes"].append(f"P{i}: EN Fig.3->6 Al80")
    return report


def verify(doc: Document) -> list[str]:
    found = []
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if re.match(r"^Fig\.\s*(\d+|S\d+)\b", t):
            stem = "?"
            img_i = find_image_before_caption(doc, i)
            if img_i is not None:
                # cannot easily get filename; mark has_img
                stem = "IMG"
            m = re.match(r"^(Fig\.\s*(?:\d+|S\d+)(?:\s*\(caution\))?)\.", t)
            label = m.group(1) if m else t[:40]
            found.append(f"{label} @P{i} img={'yes' if img_i is not None else 'no'} :: {t[:90]}")
    return found


def main() -> None:
    for rel in PNG.values():
        if not rel.exists():
            raise FileNotFoundError(rel)

    targets = [
        ROOT / "outputs" / "PAPER_JCP_draft_EN.docx",
        ROOT / "outputs" / "PAPER_JCP_draft_EN_academic.docx",
        ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN.docx",
        ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN_academic.docx",
    ]
    targets = [p for p in targets if p.exists()]

    summary = []
    for path in targets:
        backup = path.with_name(path.stem + "_backup_pre_gemini_figs.docx")
        if not backup.exists():
            shutil.copy2(path, backup)
        else:
            # refresh backup once from current before edit? user asked backup before change
            # if backup exists from prior run, keep it; still edit current
            pass

        doc = Document(str(path))
        academic = "academic" in path.name.lower()
        if academic:
            rep = process_academic(doc)
        else:
            rep = process_plain_en(doc)
        doc.save(str(path))

        # re-open verify
        doc2 = Document(str(path))
        caps = verify(doc2)
        summary.append(
            {
                "path": str(path),
                "backup": str(backup),
                "report": rep,
                "captions_now": caps,
                "n_inline": len(doc2.inline_shapes),
            }
        )
        print("===", path.name, "===")
        print("backup:", backup.name)
        print("replaced:", rep["replaced"])
        print("inserted:", rep["inserted"])
        print("n_inline:", len(doc2.inline_shapes))
        for c in caps:
            print(" ", c)

    out = ROOT / "outputs" / "_docx_gemini_fig_update_report.txt"
    lines = []
    for s in summary:
        lines.append(s["path"])
        lines.append("  backup: " + s["backup"])
        lines.append("  replaced: " + "; ".join(s["report"]["replaced"]))
        lines.append("  inserted: " + "; ".join(s["report"]["inserted"]))
        lines.append("  n_inline: " + str(s["n_inline"]))
        for c in s["captions_now"]:
            lines.append("  " + c)
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
