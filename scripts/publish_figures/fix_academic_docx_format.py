# -*- coding: utf-8 -*-
"""
fix_academic_docx_format.py
Repair JCP academic Word draft:
  - move SI S1–S6 out of Methods (before Fig.1) to Supplementary section
  - move Table 1 (alpha) next to its caption
  - convert leftover LaTeX ($...$, \\cite, \\ref, \\mathrm, Al--) to clean Word text
  - replace regenerated figure images
Does NOT change frozen Protocol W / LOGO / alpha numbers.
"""
from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
FIG = ROOT / "outputs" / "figures"
OUT = ROOT / "outputs"
JCP = ROOT / "outputs" / "jcp_submission"
ACADEMIC = OUT / "PAPER_JCP_draft_EN_academic.docx"
PLAIN = OUT / "PAPER_JCP_draft_EN.docx"
WIDTH = Inches(6.0)

# Cite keys -> numbers as used in THIS academic docx bibliography
CITE = {
    "assael2006": 1,
    "schick2012": 2,
    "tang2015": 3,
    "lu2020pnas": 4,
    "meng2020jcp": 5,
    "andersson2002": 6,
    "meyer2010prb": 7,
    "zhang2010prl": 8,
    "geng2014": 9,
    "einstein1905": 12,
    "sutherland1905": 13,
    "chen2014": 14,
    "demmel2018": 15,
    "peherstorfer2018": 18,
    "willard2022": 26,
    "karniadakis2021": 28,
    "Meyer2006AP": 31,
    "Chathoth2004": 32,
    "Brillo2011": 33,
    "Darken1948": 34,
    "Manning1961": 35,
    "Belova2005": 36,
    "ward2016": 41,
}

REF_MAP = {
    "tab:protocolW": "Table 3",
    "tab:logo": "Table 5",
    "tab:al80_strat": "Table 4",
    "tab:alpha": "Table 1",
    "tab:protocols": "Table 2",
    "fig:schema": "Fig. 1",
    "fig:coverage": "Fig. 2",
    "fig:protocolW": "Fig. 3",
    "fig:residual": "Fig. 4",
    "fig:arrhenius": "Fig. 5",
    "fig:al80": "Fig. 6",
    "fig:logo": "Fig. 7",
    "fig:alpha": "Fig. S1",
    "fig:protocolG": "Fig. S2",
}

FIG_REPLACE = {
    "Fig. 1.": "Fig1_mfnn_residual_schema.png",
    "Fig. 2.": "Fig2_phase_space_coverage.png",
    "Fig. 3.": "Fig3_protocol_W_parity_metrics.png",
    "Fig. 4.": "Fig4_protocol_W_residual_topology.png",
    "Fig. 5.": "Fig5_arrhenius_representative.png",
    "Fig. 6.": "Fig6_Al80_tracer_inter.png",
    "Fig. 7": "Fig7_LOGO_distance_caution.png",
    "Fig. S1.": "FigS1_alpha_mixing_weights.png",
    "Fig. S2": "FigS2_protocol_G_variance.png",
    "Fig. S3.": "FigS3_al80_anchor_k.png",
    "Fig. S4.": "FigS4_al80_posthoc_shift.png",
    "Fig. S5.": "FigS5_difftype_split_ablation.png",
    "Fig. S6": "FigS6_al80_upweight_w.png",
}


def backup(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = path.with_name(path.stem + f"_backup_pre_format_fix_{ts}" + path.suffix)
    shutil.copy2(path, dest)
    return dest


def body_children(doc: Document):
    return list(doc.element.body.iterchildren())


def is_tbl(el) -> bool:
    return el.tag == qn("w:tbl")


def is_p(el) -> bool:
    return el.tag == qn("w:p")


def el_text(el) -> str:
    return "".join(t.text or "" for t in el.findall(".//" + qn("w:t")))


def el_has_img(el) -> bool:
    return bool(
        el.findall(
            ".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline"
        )
    )


def cite_repl(m: re.Match) -> str:
    keys = [k.strip() for k in m.group(1).split(",")]
    nums = []
    missing = []
    for k in keys:
        if k in CITE:
            nums.append(CITE[k])
        else:
            missing.append(k)
    if missing:
        print("WARN missing cite keys:", missing)
    nums = sorted(set(nums))
    if not nums:
        return m.group(0)
    return "[" + ",".join(str(n) for n in nums) + "]"


def latex_math_to_unicode(s: str) -> str:
    """Convert common $...$ / LaTeX fragments to readable Unicode scientific text."""

    def math_inner(expr: str) -> str:
        e = expr
        e = e.replace(r"\,", " ").replace(r"\;", " ").replace(r"\!", "")
        e = e.replace(r"\ ", " ")
        e = e.replace(r"\pm", "±").replace(r"\approx", "≈").replace(r"\sim", "~")
        e = e.replace(r"\times", "×").replace(r"\cdot", "·").replace(r"\propto", "∝")
        e = e.replace(r"\rightarrow", "→").replace(r"\to", "→").replace(r"\mapsto", "↦")
        e = e.replace(r"\eta", "η").replace(r"\alpha", "α").replace(r"\Phi", "Φ")
        e = e.replace(r"\delta", "δ").replace(r"\Delta", "Δ")
        e = e.replace(r"\%", "%")
        e = e.replace(r"\log", "log").replace(r"\mathrm", "")
        e = e.replace(r"\texttt", "").replace(r"\text", "")
        e = e.replace(r"\hat{D}", "D̂").replace(r"\hat{y}", "ŷ")
        # Al_{80}Cu_{20} patterns after \mathrm stripped: {Al}_{80}{Cu}_{20}
        e = re.sub(r"\{([A-Za-z]+)\}_\{([^}]+)\}", lambda m: m.group(1) + _sub(m.group(2)), e)
        e = re.sub(r"([A-Za-z]+)_\{([^}]+)\}", lambda m: m.group(1) + _sub(m.group(2)), e)
        e = re.sub(r"\^\{([^}]+)\}", lambda m: _sup(m.group(1)), e)
        e = re.sub(r"_\{([^}]+)\}", lambda m: _sub(m.group(1)), e)
        # leftover braces from \mathrm{...}
        e = e.replace("{", "").replace("}", "")
        e = e.replace(r"\ ", " ")
        # clean double spaces
        e = re.sub(r"\s+", " ", e).strip()
        return e

    # Replace $...$ (non-greedy, no nested)
    out = []
    i = 0
    while i < len(s):
        if s[i] == "$":
            j = s.find("$", i + 1)
            if j == -1:
                out.append(s[i:])
                break
            out.append(math_inner(s[i + 1 : j]))
            i = j + 1
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


_SUB_MAP = str.maketrans(
    {
        "0": "₀",
        "1": "₁",
        "2": "₂",
        "3": "₃",
        "4": "₄",
        "5": "₅",
        "6": "₆",
        "7": "₇",
        "8": "₈",
        "9": "₉",
        "+": "₊",
        "-": "₋",
        "=": "₌",
        "(": "₍",
        ")": "₎",
        "a": "ₐ",
        "e": "ₑ",
        "i": "ᵢ",
        "o": "ₒ",
        "r": "ᵣ",
        "u": "ᵤ",
        "v": "ᵥ",
        "x": "ₓ",
        "n": "ₙ",
        "t": "ₜ",
        "s": "ₛ",
        "L": "ₗ",
        "H": "ₕ",
        ".": ".",
    }
)
_SUP_MAP = str.maketrans(
    {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
        "+": "⁺",
        "-": "⁻",
        "n": "ⁿ",
    }
)


def _sub(s: str) -> str:
    return "".join(ch.translate(_SUB_MAP) if ch in _SUB_MAP else ch for ch in s)


def _sup(s: str) -> str:
    return "".join(ch.translate(_SUP_MAP) if ch in _SUP_MAP else ch for ch in s)


def clean_paragraph_text(t: str) -> str:
    if not t:
        return t
    orig = t

    # citations
    t = re.sub(r"~?\\cite\{([^}]+)\}", cite_repl, t)
    t = re.sub(r"\\cite\{([^}]+)\}", cite_repl, t)

    # refs
    def ref_repl(m):
        key = m.group(1)
        return REF_MAP.get(key, key)

    t = re.sub(r"Table~\\ref\{([^}]+)\}", lambda m: REF_MAP.get(m.group(1), "Table"), t)
    t = re.sub(r"Fig(?:ure)?~\\ref\{([^}]+)\}", lambda m: REF_MAP.get(m.group(1), "Fig."), t)
    t = re.sub(r"Figs?\.~\\ref\{([^}]+)\}", lambda m: REF_MAP.get(m.group(1), "Fig."), t)
    t = re.sub(r"Tables~\\ref\{([^}]+)\}--\\ref\{([^}]+)\}", lambda m: f"{REF_MAP.get(m.group(1),'Table')}–{REF_MAP.get(m.group(2),'Table')}", t)
    t = re.sub(r"\\ref\{([^}]+)\}", ref_repl, t)

    # Protocol~/Figure~/Table~ non-breaking spaces
    t = t.replace("Protocol~W", "Protocol W").replace("Protocol~G", "Protocol G")
    t = t.replace("Figure~", "Figure ").replace("Table~", "Table ").replace("Fig.~", "Fig. ")
    t = t.replace("Secs.~", "Secs. ").replace("Sec.~", "Sec. ")

    # en-dashes
    t = t.replace("Al--Cu--", "Al–Cu–").replace("Al--Cu", "Al–Cu")
    t = t.replace("Stokes--Einstein", "Stokes–Einstein")
    t = t.replace("---", "—").replace("--", "–")

    # failed section refs
    t = t.replace("Sec.the corresponding section", "Sec. 2")
    t = re.sub(r"\(Sec\.\)\s*$", "", t)
    t = t.replace("(Sec.).", ".")
    t = t.replace("(Sec.)", "")

    # math dollars
    if "$" in t:
        t = latex_math_to_unicode(t)

    # leftover latex commands outside dollars
    t = t.replace(r"\mathrm", "").replace(r"\pm", "±").replace(r"\%", "%")
    t = t.replace(r"\eta", "η").replace(r"\alpha", "α").replace(r"\Phi", "Φ")
    t = t.replace(r"\log_{10}", "log₁₀").replace(r"\log", "log")
    t = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", t)  # \cmd{...} -> ...
    t = re.sub(r"\\[a-zA-Z]+", "", t)

    # common underscore-as-subscript in prose (not in citations)
    replacements = [
        (r"\bD\(T,x_i\)", "D(T, xᵢ)"),
        (r"\bη\(T,x_i\)", "η(T, xᵢ)"),
        (r"\{xi\}", "{xᵢ}"),
        (r"\bx_i\b", "xᵢ"),
        (r"\byL\b", "y_L"),
        (r"\byH\b", "y_H"),
        (r"\bDLF\b", "D_LF"),
        (r"\bDHF\b", "D_HF"),
        (r"\bFnl\b", "F_nl"),
        (r"\bFL\b", "F_L"),
        (r"\bntest\b", "n_test"),
        (r"\bn_test\b", "n_test"),
        (r"log₁₀η", "log₁₀ η"),
        (r"\bxAl\b", "x_Al"),
        (r"\bxCu\b", "x_Cu"),
        (r"\bxCe\b", "x_Ce"),
        (r"\bxNi\b", "x_Ni"),
        (r"\bxAg\b", "x_Ag"),
        (r"\bxMg\b", "x_Mg"),
        (r"\bxSi\b", "x_Si"),
        (r"\brdiff\b", "r_diff"),
        (r"Al80Cu20", "Al₈₀Cu₂₀"),
        (r"Al80", "Al₈₀"),
        (r"ŷH", "ŷ_H"),
        (r"ŷH", "ŷ_H"),
        (r"D̂=10\^\(ŷH\)", "D̂ = 10^(ŷ_H)"),
        (r"D̂=10\^\(ŷ_H\)", "D̂ = 10^(ŷ_H)"),
    ]
    for pat, rep in replacements:
        t = re.sub(pat, rep, t)

    # tidy spaces
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" \.", ".", t)
    t = re.sub(r" ,", ",", t)
    return t


def set_run_text(paragraph: Paragraph, text: str) -> None:
    """Replace paragraph text preserving first run style if present."""
    if not paragraph.runs:
        paragraph.add_run(text)
        return
    paragraph.runs[0].text = text
    for r in paragraph.runs[1:]:
        r.text = ""


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


def move_si_and_table(doc: Document) -> dict:
    """Move misplaced SI blocks + alpha table into correct positions."""
    body = doc.element.body
    children = list(body.iterchildren())
    # Identify elements by text
    si_caps = {}
    si_imgs = {}
    fig1_illustrates = None
    table1_caption = None
    alpha_table = None
    references = None
    appendix = None

    for el in children:
        if el.tag == qn("w:sectPr"):
            continue
        txt = el_text(el).strip()
        if is_tbl(el) and txt.startswith("Seed") and "α" in txt:
            alpha_table = el
        if is_p(el):
            if txt.startswith("Table 1. Protocol W MFNN mixing"):
                table1_caption = el
            if txt.startswith("Fig. 1 illustrates"):
                fig1_illustrates = el
            if txt.startswith("References"):
                references = el
            if txt.startswith("Appendix A"):
                appendix = el
            for k in ("S1", "S2", "S3", "S4", "S5", "S6"):
                if txt.startswith(f"Fig. {k}") or txt.startswith(f"Fig. {k} "):
                    si_caps[k] = el
                # also "Fig. S1." etc
                if re.match(rf"Fig\. S{k[-1]}\b", txt):
                    si_caps[k] = el

    # Find image paragraphs immediately before each SI caption
    children = list(body.iterchildren())
    for k, cap in si_caps.items():
        try:
            idx = children.index(cap)
        except ValueError:
            continue
        for j in range(idx - 1, max(-1, idx - 4), -1):
            el = children[j]
            if is_p(el) and el_has_img(el):
                si_imgs[k] = el
                break

    report = {
        "si_caps": list(si_caps.keys()),
        "si_imgs": list(si_imgs.keys()),
        "alpha_table": alpha_table is not None,
        "table1_caption": table1_caption is not None,
        "fig1_illustrates": fig1_illustrates is not None,
        "references": references is not None,
    }

    # Detach SI img+cap elements (keep order S1..S6)
    si_block = []
    for k in ("S1", "S2", "S3", "S4", "S5", "S6"):
        if k in si_imgs:
            si_block.append(si_imgs[k])
        if k in si_caps:
            si_block.append(si_caps[k])
    for el in si_block:
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)

    # Move alpha table right after Table 1 caption
    if alpha_table is not None and table1_caption is not None:
        parent = alpha_table.getparent()
        if parent is not None:
            parent.remove(alpha_table)
        table1_caption.addnext(alpha_table)

    # Insert Supplementary Information heading + SI block before References
    anchor = references if references is not None else (appendix if appendix is not None else None)
    if anchor is not None and si_block:
        # Create heading paragraph
        from docx.oxml import OxmlElement

        heading = OxmlElement("w:p")
        # insert before references
        anchor.addprevious(heading)
        hp = Paragraph(heading, anchor.getparent())
        run = hp.add_run("Supplementary Information")
        run.bold = True
        run.font.size = Pt(14)
        # insert SI elements before References, after heading
        prev = heading
        for el in si_block:
            prev.addnext(el)
            prev = el
        report["si_moved_before"] = "References"
    else:
        report["si_moved_before"] = None
        print("WARN: could not place SI block")

    return report


def replace_figures(doc: Document) -> list[str]:
    updated = []
    paras = doc.paragraphs
    for i, p in enumerate(paras):
        t = p.text.strip()
        for prefix, fname in FIG_REPLACE.items():
            if t.startswith(prefix):
                # image should be previous non-empty / image para
                png = FIG / fname
                if not png.exists():
                    print("WARN missing png", png)
                    continue
                for j in range(i - 1, max(-1, i - 6), -1):
                    if el_has_img(paras[j]._p):
                        set_picture(paras[j], png)
                        updated.append(f"{prefix} <- {fname}")
                        break
                break
    return updated


def clean_all_paragraphs(doc: Document) -> int:
    n = 0
    for p in doc.paragraphs:
        t = p.text
        if not t:
            continue
        new = clean_paragraph_text(t)
        if new != t:
            set_run_text(p, new)
            n += 1
    # also clean tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    t = p.text
                    if not t:
                        continue
                    new = clean_paragraph_text(t)
                    if new != t:
                        set_run_text(p, new)
                        n += 1
    return n


def main():
    assert ACADEMIC.exists(), ACADEMIC
    b1 = backup(ACADEMIC)
    print("backup academic:", b1)
    if PLAIN.exists():
        b2 = backup(PLAIN)
        print("backup plain:", b2)

    doc = Document(str(ACADEMIC))
    rep = move_si_and_table(doc)
    print("float move:", rep)
    n = clean_all_paragraphs(doc)
    print("paragraphs cleaned:", n)
    figs = replace_figures(doc)
    print("figures replaced:", figs)

    # residual scan
    leftovers = []
    for i, p in enumerate(doc.paragraphs):
        t = p.text
        if any(x in t for x in ["\\cite", "\\ref", "\\mathrm", "\\pm", "\\%", "Al--", "$\\", "Protocol~"]):
            leftovers.append((i, t[:160]))
        elif "$" in t and ("_" in t or "\\" in t):
            leftovers.append((i, t[:160]))
    print("leftover count:", len(leftovers))
    for item in leftovers[:20]:
        print(" LEFT", item)

    doc.save(str(ACADEMIC))
    # sync jcp_submission
    JCP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ACADEMIC, JCP / ACADEMIC.name)
    print("synced", JCP / ACADEMIC.name)

    # lightly clean plain EN if it has same latex leftovers
    if PLAIN.exists():
        d2 = Document(str(PLAIN))
        n2 = clean_all_paragraphs(d2)
        # do NOT move SI in plain unless same structure - check for Fig. S6 before Fig. 1
        texts = [p.text for p in d2.paragraphs]
        if any(t.startswith("Fig. S6") for t in texts) and any(t.startswith("Fig. 1 illustrates") for t in texts):
            try:
                move_si_and_table(d2)
            except Exception as e:
                print("plain SI move skip:", e)
        figs2 = replace_figures(d2)
        d2.save(str(PLAIN))
        shutil.copy2(PLAIN, JCP / PLAIN.name)
        print("plain cleaned paras:", n2, "figs:", len(figs2))

    log = OUT / "FORMAT_FIX_LOG.md"
    log.write_text(
        f"""# Format fix log

**Time (UTC+8):** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Backups
- `{b1.name}`

## Figures regenerated (Lu-like box + inward ticks; occlusion fixes)
- Fig1_mfnn_residual_schema
- Fig2_phase_space_coverage
- Fig3_protocol_W_parity_metrics / Fig4_protocol_W_residual_topology
- Fig5_arrhenius_representative
- Fig7_LOGO_distance_caution
- FigS1_alpha_mixing_weights (+ Fig6_alpha_mixing_weights copy)
- FigS2_protocol_G_variance, FigS3_al80_anchor_k, FigS4_al80_posthoc_shift, FigS5_difftype_split_ablation, FigS6_al80_upweight_w

## Word repairs (`PAPER_JCP_draft_EN_academic.docx`)
- Float move: {rep}
- Paragraphs cleaned: {n}
- Figures re-embedded: {figs}
- Leftover LaTeX-like scans: {len(leftovers)}

## Style
- `_style.apply_style`: spines top/right True; tick direction in; xtick.top/ytick.right True
- `box_spines(ax)` helper; `despine` now aliases to box_spines

## Frozen numbers
- Unchanged (Protocol W / LOGO / α / Al80)

## WARN / remaining
{chr(10).join("- " + repr(x) for x in leftovers[:15]) or "- none"}
""",
        encoding="utf-8",
    )
    print("wrote", log)


if __name__ == "__main__":
    main()
