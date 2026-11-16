# -*- coding: utf-8 -*-
"""
fix_fig1a_omml_threeline.py
- Re-embed regenerated Fig.1
- Insert/replace key equations as OMML
- Convert all tables to three-line (三线表) style
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn, nsmap
from docx.shared import Inches, Pt, Twips
from docx.text.paragraph import Paragraph

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
OUT = ROOT / "outputs"
FIG = OUT / "figures"
JCP = OUT / "jcp_submission"
FIXED = OUT / "PAPER_JCP_draft_EN_academic_FIXED.docx"
ACADEMIC = OUT / "PAPER_JCP_draft_EN_academic.docx"
FIG1_PNG = FIG / "Fig1_mfnn_residual_schema.png"
WIDTH = Inches(6.0)

M = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _me(tag: str):
    return OxmlElement(f"m:{tag}")


def _mt(text: str, *, sty: str | None = None):
    """Math run with optional style: p=plain, i=italic, b=bold."""
    r = _me("r")
    if sty:
        rPr = _me("rPr")
        st = _me("sty")
        st.set(qn("m:val"), sty)
        rPr.append(st)
        r.append(rPr)
    t = _me("t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.append(t)
    return r


def _msub(base_runs, sub_runs):
    node = _me("sSub")
    e = _me("e")
    for x in base_runs:
        e.append(x)
    sub = _me("sub")
    for x in sub_runs:
        sub.append(x)
    node.append(e)
    node.append(sub)
    return node


def _msup(base_runs, sup_runs):
    node = _me("sSup")
    e = _me("e")
    for x in base_runs:
        e.append(x)
    sup = _me("sup")
    for x in sup_runs:
        sup.append(x)
    node.append(e)
    node.append(sup)
    return node


def _mfrac(num_runs, den_runs):
    node = _me("f")
    num = _me("num")
    for x in num_runs:
        num.append(x)
    den = _me("den")
    for x in den_runs:
        den.append(x)
    node.append(num)
    node.append(den)
    return node


def _md(d_runs):
    """Delimiter parentheses."""
    node = _me("d")
    dPr = _me("dPr")
    beg = _me("begChr"); beg.set(qn("m:val"), "(")
    end = _me("endChr"); end.set(qn("m:val"), ")")
    dPr.append(beg); dPr.append(end)
    node.append(dPr)
    e = _me("e")
    for x in d_runs:
        e.append(x)
    node.append(e)
    return node


def build_omath_sutherland():
    """D_LF = k_B T / (c η r_i(T))"""
    omath = _me("oMath")
    omath.append(_msub([_mt("D", sty="i")], [_mt("LF", sty="p")]))
    omath.append(_mt(" = ", sty="p"))
    num = [
        _msub([_mt("k", sty="i")], [_mt("B", sty="p")]),
        _mt(" ", sty="p"),
        _mt("T", sty="i"),
    ]
    den = [
        _mt("c", sty="i"),
        _mt(" ", sty="p"),
        _mt("η", sty="i"),
        _mt(" ", sty="p"),
        _msub([_mt("r", sty="i")], [_mt("i", sty="i")]),
        _md([_mt("T", sty="i")]),
    ]
    omath.append(_mfrac(num, den))
    return omath


def build_omath_hf_target():
    """y_H = log_10 D_exp"""
    omath = _me("oMath")
    omath.append(_msub([_mt("y", sty="i")], [_mt("H", sty="p")]))
    omath.append(_mt(" = ", sty="p"))
    # log_10
    omath.append(_msub([_mt("log", sty="p")], [_mt("10", sty="p")]))
    omath.append(_mt(" ", sty="p"))
    omath.append(_msub([_mt("D", sty="i")], [_mt("exp", sty="p")]))
    return omath


def build_omath_residual():
    """ŷ_H = α_1 (A[x,y_L]+b) + α_2 F_nl(x,y_L)"""
    omath = _me("oMath")
    omath.append(_msub([_mt("ŷ", sty="i")], [_mt("H", sty="p")]))
    omath.append(_mt(" = ", sty="p"))
    omath.append(_msub([_mt("α", sty="i")], [_mt("1", sty="p")]))
    omath.append(_mt(" ", sty="p"))
    inner1 = [
        _mt("A", sty="i"),
        _mt("[", sty="p"),
        _mt("x", sty="i"),
        _mt(", ", sty="p"),
        _msub([_mt("y", sty="i")], [_mt("L", sty="p")]),
        _mt("]", sty="p"),
        _mt(" + ", sty="p"),
        _mt("b", sty="i"),
    ]
    omath.append(_md(inner1))
    omath.append(_mt(" + ", sty="p"))
    omath.append(_msub([_mt("α", sty="i")], [_mt("2", sty="p")]))
    omath.append(_mt(" ", sty="p"))
    omath.append(_msub([_mt("F", sty="i")], [_mt("nl", sty="p")]))
    omath.append(_md([
        _mt("x", sty="i"),
        _mt(", ", sty="p"),
        _msub([_mt("y", sty="i")], [_mt("L", sty="p")]),
    ]))
    return omath


def build_omath_dlf_prop():
    """D_LF ∝ k_B T / (η r_eff(T))"""
    omath = _me("oMath")
    omath.append(_msub([_mt("D", sty="i")], [_mt("LF", sty="p")]))
    omath.append(_mt(" ∝ ", sty="p"))
    num = [
        _msub([_mt("k", sty="i")], [_mt("B", sty="p")]),
        _mt(" ", sty="p"),
        _mt("T", sty="i"),
    ]
    den = [
        _mt("η", sty="i"),
        _mt(" ", sty="p"),
        _msub([_mt("r", sty="i")], [_mt("eff", sty="p")]),
        _md([_mt("T", sty="i")]),
    ]
    omath.append(_mfrac(num, den))
    return omath


def make_omath_para(omath, align="center") -> OxmlElement:
    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), align)
    pPr.append(jc)
    p.append(pPr)
    # oMathPara wrapper preferred for display equations
    omp = _me("oMathPara")
    omp.append(omath)
    p.append(omp)
    return p


def replace_para_with_omath(paragraph: Paragraph, omath, *, prefix: str = "", suffix: str = "") -> None:
    """Clear paragraph and insert optional prefix text + OMML + suffix."""
    p = paragraph._p
    # clear children except pPr
    pPr = p.find(qn("w:pPr"))
    for child in list(p):
        if child is pPr:
            continue
        p.remove(child)
    if prefix:
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.text = prefix
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        r.append(t)
        p.append(r)
    omp = _me("oMathPara") if not prefix and not suffix else None
    if omp is not None:
        omp.append(omath)
        p.append(omp)
        # center
        if pPr is None:
            pPr = OxmlElement("w:pPr")
            p.insert(0, pPr)
        jc = pPr.find(qn("w:jc"))
        if jc is None:
            jc = OxmlElement("w:jc")
            pPr.append(jc)
        jc.set(qn("w:val"), "center")
    else:
        p.append(omath)
        if suffix:
            r = OxmlElement("w:r")
            t = OxmlElement("w:t")
            t.text = suffix
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            r.append(t)
            p.append(r)


def insert_omath_after(paragraph: Paragraph, omath) -> Paragraph:
    new_p = make_omath_para(omath)
    paragraph._p.addnext(new_p)
    return Paragraph(new_p, paragraph._parent)


def el_has_img(p_el) -> bool:
    return bool(
        p_el.findall(
            ".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline"
        )
    )


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


def set_cell_borders(cell, borders: dict) -> None:
    """borders: edge -> {val, sz, color} or None for nil."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    # remove existing tcBorders
    for old in tcPr.findall(qn("w:tcBorders")):
        tcPr.remove(old)
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        spec = borders.get(edge)
        if not spec:
            el.set(qn("w:val"), "nil")
            el.set(qn("w:sz"), "0")
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), "auto")
        else:
            el.set(qn("w:val"), spec.get("val", "single"))
            el.set(qn("w:sz"), str(spec.get("sz", 8)))
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), spec.get("color", "000000"))
        tcBorders.append(el)
    tcPr.append(tcBorders)


def apply_three_line_table(table) -> None:
    """三线表: thick top, thin under header, thick bottom; no verticals."""
    n_rows = len(table.rows)
    n_cols = len(table.columns)
    THICK = {"val": "single", "sz": 18, "color": "000000"}  # 2.25 pt
    THIN = {"val": "single", "sz": 8, "color": "000000"}    # 1 pt
    for i, row in enumerate(table.rows):
        for cell in row.cells:
            borders = {"top": None, "bottom": None, "left": None, "right": None}
            if i == 0:
                borders["top"] = THICK
                borders["bottom"] = THIN
            if i == n_rows - 1:
                borders["bottom"] = THICK
            set_cell_borders(cell, borders)
    # Also clear table-level borders
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is not None:
        for old in tblPr.findall(qn("w:tblBorders")):
            tblPr.remove(old)
        tblBorders = OxmlElement("w:tblBorders")
        for edge, spec in (
            ("top", THICK),
            ("left", None),
            ("bottom", THICK),
            ("right", None),
            ("insideH", None),
            ("insideV", None),
        ):
            el = OxmlElement(f"w:{edge}")
            if spec is None:
                el.set(qn("w:val"), "nil")
                el.set(qn("w:sz"), "0")
                el.set(qn("w:space"), "0")
                el.set(qn("w:color"), "auto")
            else:
                el.set(qn("w:val"), spec["val"])
                el.set(qn("w:sz"), str(spec["sz"]))
                el.set(qn("w:space"), "0")
                el.set(qn("w:color"), spec["color"])
            tblBorders.append(el)
        tblPr.append(tblBorders)


def reembed_fig1(doc: Document) -> bool:
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip().startswith("Fig. 1."):
            for j in range(i - 1, max(-1, i - 6), -1):
                if el_has_img(doc.paragraphs[j]._p):
                    set_picture(doc.paragraphs[j], FIG1_PNG)
                    return True
    return False


def fix_equations(doc: Document) -> list[str]:
    log = []
    # Replace display equation at para containing D_LF ∝
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t.startswith("D_LF") or t.startswith("DLF"):
            replace_para_with_omath(p, build_omath_sutherland())
            log.append(f"para {i}: Sutherland OMML (replaced D_LF line)")
            # insert HF target equation after it
            insert_omath_after(p, build_omath_hf_target())
            log.append(f"after {i}: HF target OMML inserted")
            break
    # Replace residual MFNN equation
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t.startswith("ŷ_H") or t.startswith("ŷH") or (t.startswith("ŷ") and "α" in t):
            replace_para_with_omath(p, build_omath_residual())
            log.append(f"para {i}: residual MFNN OMML")
            break
    # Fix leftover brace junk from earlier clean
    for p in doc.paragraphs:
        t = p.text
        if "\\0,1,2,42,123\\" in t or "{0,1,2,42,123}" in t.replace(" ", ""):
            nt = t.replace("\\0,1,2,42,123\\", "{0,1,2,42,123}")
            nt = nt.replace("Figs.~3–5", "Figs. 3–5").replace("Figs.~", "Figs. ")
            if nt != t and p.runs:
                p.runs[0].text = nt
                for r in p.runs[1:]:
                    r.text = ""
                log.append("cleaned seed-brace / Figs leftover")
    return log


def main():
    assert FIXED.exists(), FIXED
    assert FIG1_PNG.exists(), FIG1_PNG
    doc = Document(str(FIXED))

    ok = reembed_fig1(doc)
    print("fig1 re-embed:", ok)
    eq_log = fix_equations(doc)
    print("equations:", eq_log)

    for i, table in enumerate(doc.tables):
        apply_three_line_table(table)
        print("three-line table", i)
    print("tables done:", len(doc.tables))

    # save FIXED
    try:
        doc.save(str(FIXED))
        print("saved FIXED")
        saved = FIXED
    except PermissionError:
        alt = OUT / "PAPER_JCP_draft_EN_academic_FIXED2.docx"
        doc.save(str(alt))
        print("FIXED locked; saved", alt)
        saved = alt

    JCP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(saved, JCP / "PAPER_JCP_draft_EN_academic.docx")
    print("synced jcp")

    # try overwrite academic.docx
    try:
        shutil.copy2(saved, ACADEMIC)
        print("overwrote academic.docx")
    except Exception as e:
        print("academic overwrite skip:", e)

    # append log
    logp = OUT / "FORMAT_FIX_LOG.md"
    with logp.open("a", encoding="utf-8") as f:
        f.write(
            f"""

## Fig.1A + OMML + 三线表 ({datetime.now().strftime("%Y-%m-%d %H:%M")} UTC+8)

- Redesigned `draw_panel_a`: removed twin y-axis and mid-gutter arrows/labels; widened plot spacing; bottom equation boxes only.
- Re-exported Fig1 pdf/svg/png; re-embedded into Word: {ok}
- OMML equations: {eq_log}
- All {len(doc.tables)} tables converted to three-line style (thick top / thin header / thick bottom; no verticals)
- Deliverable: `{saved}`
"""
        )
    print("log appended")
    return str(saved)


if __name__ == "__main__":
    print(main())
