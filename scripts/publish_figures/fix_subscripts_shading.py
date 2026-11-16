# -*- coding: utf-8 -*-
"""Fix Bug1: underscore -> Word subscript; Bug2: clear table header shading."""
from __future__ import annotations

import re
import shutil
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn, nsmap
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
from docx.text.run import Run

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
SRC = ROOT / "outputs" / "PAPER_JCP_draft_EN_academic_FIXED2.docx"
OUT = ROOT / "outputs" / "PAPER_JCP_draft_EN_academic_FIXED3.docx"
ACADEMIC = ROOT / "outputs" / "PAPER_JCP_draft_EN_academic.docx"
JCP = ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN_academic.docx"
JCP_FIXED3 = ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN_academic_FIXED3.docx"
LOG = ROOT / "outputs" / "FORMAT_FIX_LOG.md"

# Identifiers that must NOT be converted (paths, code, CSV cols, etc.)
SKIP_EXACT = {
    "diff_type", "comp_group", "train_test", "seed_idx", "n_train",
    "file_path", "data_dir", "model_ckpt", "fig_dir", "out_dir",
    "HF_path", "LF_path", "csv_path", "xlsx_path",
}

# Prefer converting these science tokens; also allow generic base_sub
SCIENCE_SUBS = {
    "D_LF", "D_HF", "D_exp", "D_LF", "y_L", "y_H", "y_LF", "y_HF",
    "F_L", "F_nl", "F_H", "n_test", "n_train", "r_diff",
    "x_Al", "x_Cu", "x_Ce", "x_Ni", "x_Ag", "x_Mg", "x_Si", "x_Fe", "x_Zn",
    "k_B", "R_2", "alpha_1", "alpha_2", "a_1", "a_2",
    "log_10", "eta_L", "eta_H",
}

# Composition like Al_80
COMP_RE = re.compile(r"\b((?:Al|Cu|Mg|Si|Ce|Ni|Ag|Fe|Zn|Ti)_(\d+(?:\.\d+)?))\b")

# Generic science: single letter / Greek letter base + underscore + alnum
# Avoid matching URLs, paths (no / before), and snake_case multi-word like train_seed
GENERIC_RE = re.compile(
    r"(?<![A-Za-z0-9/\\.\-])"
    r"([A-Za-zΑ-Ωα-ωηδΔγηαβγ])"
    r"_([A-Za-z0-9]+)"
    r"(?![A-Za-z0-9_])"
)

# Multi-char bases we still want: log_10, alpha_1, etc.
MULTI_BASE_RE = re.compile(
    r"(?<![A-Za-z0-9/\\.\-])"
    r"(log|alpha|eta|sigma|omega|rho|phi|psi|theta|NN|MFNN)"
    r"_([A-Za-z0-9]+)"
    r"(?![A-Za-z0-9_])"
)

# R_2 -> R² style (superscript 2 for R-squared)
RSQ_RE = re.compile(r"(?<![A-Za-z0-9])R_2(?![A-Za-z0-9])")


def _w_ns():
    return "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def clear_shading(cell) -> bool:
    """Remove decorative cell shading. Return True if changed."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    changed = False
    for shd in list(tcPr.findall(qn("w:shd"))):
        fill = shd.get(qn("w:fill"))
        if fill and fill.lower() not in ("auto", "ffffff", "none"):
            tcPr.remove(shd)
            changed = True
        elif shd.get(qn("w:val")) and shd.get(qn("w:val")) not in ("nil", "clear"):
            # clear any non-nil shading
            tcPr.remove(shd)
            changed = True
    # Explicit clear shading to override style inheritance
    if changed or True:
        # Always set clear so theme styles don't re-apply blue
        for old in list(tcPr.findall(qn("w:shd"))):
            tcPr.remove(old)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "auto")
        tcPr.append(shd)
        changed = True
    return changed


def _clone_run_rpr(src_r, dst_r):
    """Copy rPr from src run element to dst, then adjust."""
    src_rPr = src_r.find(qn("w:rPr"))
    # remove existing
    for old in list(dst_r.findall(qn("w:rPr"))):
        dst_r.remove(old)
    if src_rPr is not None:
        dst_r.insert(0, deepcopy(src_rPr))
    else:
        rPr = OxmlElement("w:rPr")
        dst_r.insert(0, rPr)


def _ensure_rpr(r):
    rPr = r.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        r.insert(0, rPr)
    return rPr


def _set_vert_align(r, kind: str | None):
    """kind: 'subscript' | 'superscript' | None (remove)."""
    rPr = _ensure_rpr(r)
    for old in list(rPr.findall(qn("w:vertAlign"))):
        rPr.remove(old)
    if kind:
        va = OxmlElement("w:vertAlign")
        va.set(qn("w:val"), kind)
        rPr.append(va)


def _set_t(r, text: str):
    # preserve xml:space
    t = r.find(qn("w:t"))
    if t is None:
        t = OxmlElement("w:t")
        r.append(t)
    if text.startswith(" ") or text.endswith(" ") or "  " in text:
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text


def _make_run_like(template_r, text: str, vert: str | None = None):
    r = OxmlElement("w:r")
    _clone_run_rpr(template_r, r)
    if vert:
        _set_vert_align(r, vert)
    else:
        # clear any inherited vertAlign from template if we want normal
        _set_vert_align(r, None)
    _set_t(r, text)
    return r


def _should_skip_token(full: str) -> bool:
    if full in SKIP_EXACT:
        return True
    # multi-segment snake_case identifiers with lowercase both sides longer than 1
    # e.g. train_seed, within_composition — skip if both parts look like English words > 2 chars
    # and base is multi-letter lowercase
    return False


def find_tokens(text: str) -> list[tuple[int, int, str, str, str]]:
    """Return list of (start, end, base, sub, mode) where mode in ('sub','sup')."""
    spans: list[tuple[int, int, str, str, str]] = []
    occupied = [False] * (len(text) + 1)

    def mark(a, b):
        for i in range(a, b):
            occupied[i] = True

    def free(a, b):
        return not any(occupied[i] for i in range(a, b))

    # R_2 as superscript first
    for m in RSQ_RE.finditer(text):
        if free(m.start(), m.end()):
            spans.append((m.start(), m.end(), "R", "2", "sup"))
            mark(m.start(), m.end())

    for m in COMP_RE.finditer(text):
        if free(m.start(), m.end()):
            base = m.group(1).split("_")[0]
            sub = m.group(2)
            spans.append((m.start(), m.end(), base, sub, "sub"))
            mark(m.start(), m.end())

    for m in MULTI_BASE_RE.finditer(text):
        full = m.group(0)
        if full in SKIP_EXACT or _should_skip_token(full):
            continue
        if free(m.start(), m.end()):
            spans.append((m.start(), m.end(), m.group(1), m.group(2), "sub"))
            mark(m.start(), m.end())

    for m in GENERIC_RE.finditer(text):
        full = m.group(0)
        if full in SKIP_EXACT:
            continue
        # skip long snake_case English identifiers: base single letter is OK;
        # if somehow matched skip known non-science
        if free(m.start(), m.end()):
            spans.append((m.start(), m.end(), m.group(1), m.group(2), "sub"))
            mark(m.start(), m.end())

    spans.sort(key=lambda x: x[0])
    return spans


def rewrite_paragraph_runs(paragraph: Paragraph) -> int:
    """Split underscore tokens into base + subscript runs. Return #conversions."""
    # Work at XML level across runs in the paragraph
    p = paragraph._p
    # Collect plain text mapping to runs is hard when tokens span runs.
    # Strategy: if any run contains a token fully, rewrite that run.
    # Then also merge adjacent runs' text for spanning cases via full rebuild of text runs.

    # First pass: per-run local replacements (most cases)
    n = 0
    runs = list(paragraph.runs)
    if not runs:
        return 0

    # Build full text; if tokens exist, rebuild all text runs from scratch
    full = paragraph.text
    tokens = find_tokens(full)
    if not tokens:
        return 0

    # Preserve non-text elements (drawings, etc.) — only rewrite w:r that have w:t
    # Safer approach: walk each run independently; for spanning, join consecutive text runs.

    # Join all text content into one logical string and replace paragraph text runs
    # Keep first run's rPr as template for normal text.
    template = runs[0]._r

    # Remove existing text runs (keep drawing-only runs)
    text_runs = []
    for r in list(p.findall(qn("w:r"))):
        if r.find(qn("w:t")) is not None and r.find(qn("w:drawing")) is None and r.find(qn("w:pict")) is None:
            text_runs.append(r)

    if not text_runs:
        return 0

    # Use first text run as style template
    template = text_runs[0]

    # Build new run sequence
    new_rs = []
    pos = 0
    for start, end, base, sub, mode in tokens:
        if start > pos:
            new_rs.append(_make_run_like(template, full[pos:start], None))
        new_rs.append(_make_run_like(template, base, None))
        vert = "superscript" if mode == "sup" else "subscript"
        new_rs.append(_make_run_like(template, sub, vert))
        n += 1
        pos = end
    if pos < len(full):
        new_rs.append(_make_run_like(template, full[pos:], None))

    # Insert new runs where first text run was; remove old text runs
    # Find index of first text run among p children
    children = list(p)
    try:
        first_idx = children.index(text_runs[0])
    except ValueError:
        first_idx = len(children)

    for old in text_runs:
        p.remove(old)

    # Recompute insert point: after any pPr
    insert_at = 0
    kids = list(p)
    if kids and kids[0].tag == qn("w:pPr"):
        insert_at = 1
    for i, nr in enumerate(new_rs):
        p.insert(insert_at + i, nr)

    return n


def process_paragraphs(doc: Document) -> int:
    total = 0
    for para in doc.paragraphs:
        total += rewrite_paragraph_runs(para)
    # Also headers/footers
    for section in doc.sections:
        for part in (section.header, section.footer):
            for para in part.paragraphs:
                total += rewrite_paragraph_runs(para)
    return total


def process_tables(doc: Document) -> tuple[int, int]:
    """Return (subscript_conversions, shaded_cleared)."""
    n_sub = 0
    n_shade = 0
    for table in doc.tables:
        for ri, row in enumerate(table.rows):
            for cell in row.cells:
                # shading: clear ALL cells to kill blue header + gray footer
                if clear_shading(cell):
                    n_shade += 1
                for para in cell.paragraphs:
                    n_sub += rewrite_paragraph_runs(para)
    return n_sub, n_shade


def scan_remaining(doc: Document) -> list[tuple[str, str]]:
    hits = []
    pat = re.compile(
        r"(?<![A-Za-z0-9/\\.\-])([A-Za-zΑ-ωηαβγδΔ]|log|alpha|eta)_([A-Za-z0-9]+)\b"
    )
    comp = re.compile(r"\b((?:Al|Cu|Mg|Si|Ce|Ni|Ag|Fe|Zn|Ti)_\d+)\b")
    rsq = re.compile(r"(?<![A-Za-z0-9])R_2(?![A-Za-z0-9])")

    def add(text, where):
        for m in pat.finditer(text):
            if m.group(0) not in SKIP_EXACT:
                hits.append((where, m.group(0)))
        for m in comp.finditer(text):
            hits.append((where, m.group(0)))
        for m in rsq.finditer(text):
            hits.append((where, m.group(0)))

    for i, para in enumerate(doc.paragraphs):
        add(para.text, f"p{i}")
    for ti, t in enumerate(doc.tables):
        for ri, row in enumerate(t.rows):
            for ci, cell in enumerate(row.cells):
                add(cell.text.replace("\n", " "), f"t{ti}r{ri}c{ci}")
    return hits


def main():
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}")
    doc = Document(str(SRC))

    n1 = process_paragraphs(doc)
    n2, n_shade = process_tables(doc)
    # iterate once more for any leftovers after rebuild
    n3 = process_paragraphs(doc)
    n4, _ = process_tables(doc)

    remaining = scan_remaining(doc)
    from collections import Counter
    c = Counter(h[1] for h in remaining)

    # save FIXED3
    doc.save(str(OUT))
    print(f"saved {OUT}")
    print(f"subscript conversions: paras={n1}+{n3} tables={n2}+{n4} total={n1+n2+n3+n4}")
    print(f"shading cleared (cell ops): {n_shade}")
    print(f"remaining science underscores: {len(remaining)}")
    for k, v in c.most_common(30):
        print(f"  leftover {v:3d}  {k}")

    for dest in (ACADEMIC, JCP, JCP_FIXED3):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(OUT, dest)
            print(f"synced {dest}")
        except Exception as e:
            print(f"WARN sync {dest}: {type(e).__name__}: {e}")

    # also try overwrite FIXED2 if unlocked
    try:
        shutil.copy2(OUT, SRC)
        print(f"synced {SRC}")
    except Exception as e:
        print(f"WARN FIXED2 locked: {e}")

    # log
    from datetime import datetime
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"""
## {stamp} — subscript + table de-shade (FIXED3)
- Source: PAPER_JCP_draft_EN_academic_FIXED2.docx
- Output: PAPER_JCP_draft_EN_academic_FIXED3.docx
- Bug1: underscore→Word vertAlign=subscript (R_2→superscript). Conversions≈{n1+n2+n3+n4}. Remaining science hits={len(remaining)} {dict(c)}
- Bug2: cleared w:shd on all table cells (was light-blue D9E2F3 headers / gray footers); 三线表 borders kept.
- Synced academic.docx + jcp_submission when unlocked.
- Frozen numbers unchanged; no retraining.
"""
    with LOG.open("a", encoding="utf-8") as f:
        f.write(entry)
    print("log appended")


if __name__ == "__main__":
    main()
