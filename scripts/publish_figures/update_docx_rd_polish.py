# -*- coding: utf-8 -*-
"""Section-aligned Results/Discussion prose update for academic docx."""
from __future__ import annotations
import re
import shutil
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
POLISHED = (ROOT / "scripts" / "publish_figures" / "rd_polished.md").read_text(encoding="utf-8")

DOCXS = [
    ROOT / "outputs" / "PAPER_JCP_draft_EN_academic.docx",
    ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN_academic.docx",
]

# Map docx Heading-2 startswith -> polished ### title
SECTION_MAP = [
    ("Within-composition temperature generalization", "Within-composition temperature generalization (Protocol W)"),
    ("Resolution of tracer versus interdiffusivity", "Resolution of tracer versus interdiffusivity conflicts at $\\mathrm{Al}_{80}\\mathrm{Cu}_{20}$"),
    ("Leave-one-composition-out evaluation", "Leave-one-composition-out evaluation within Al–Cu"),
    ("Ablation on separate networks", "Ablation on separate networks and random group splits (Protocol G)"),
    ("Physics-guided", "Physics-guided residual correction under Protocol W"),
    ("Thermodynamic", "Thermodynamic and neighborhood limits on composition transfer"),
    ("Counterfactual", "Counterfactual slope–intercept diagnostics (SI only)"),
    ("Methodological scope", "Methodological scope, limitations, and outlook"),
]

HEADING_RENAME = {
    "Physics-guided manifold regularization under Protocol W": "Physics-guided residual correction under Protocol W",
    "Thermodynamic origin of composition-extrapolation limits": "Thermodynamic and neighborhood limits on composition transfer",
    "Counterfactual slope–intercept and weight-dilution diagnostics": "Counterfactual slope–intercept diagnostics (SI only)",
    "Counterfactual slope-intercept and weight-dilution diagnostics": "Counterfactual slope–intercept diagnostics (SI only)",
}


def has_drawing(p) -> bool:
    return bool(
        p._p.findall(
            ".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline"
        )
    )


def set_para_text(p, text: str) -> None:
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(text)


def insert_after(paragraph: Paragraph, text: str) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    para = Paragraph(new_p, paragraph._parent)
    para.add_run(text)
    return para


def parse_polished_sections(md: str) -> dict[str, list[str]]:
    """### title -> list of body paragraphs (no fig/table captions, no tables)."""
    sections: dict[str, list[str]] = {}
    cur = None
    buf: list[str] = []

    def flush():
        nonlocal buf, cur
        if cur is None:
            buf = []
            return
        text = "\n".join(buf).strip()
        if text:
            sections.setdefault(cur, []).append(text)
        buf = []

    for line in md.splitlines():
        if line.startswith("### "):
            flush()
            cur = line[4:].strip()
            continue
        if line.startswith("## "):
            flush()
            cur = None
            continue
        if line.startswith("**Fig.") or line.startswith("**Table") or line.startswith("|"):
            flush()
            continue
        if not line.strip():
            flush()
            continue
        buf.append(line)
    flush()
    return sections


def is_protected(t: str) -> bool:
    if not t:
        return True
    if t.startswith("Fig.") or t.startswith("Table") or t.startswith("|"):
        return True
    if re.match(r"^\d+\.\s+\S+", t):  # numbered H1
        return True
    return False


def update_one(path: Path, restore_bak: Path | None) -> list[str]:
    notes = []
    bak = path.with_name(path.stem + "_backup_pre_rd_polish.docx")
    if restore_bak and restore_bak.is_file():
        shutil.copy2(restore_bak, path)
        notes.append(f"restored from {restore_bak.name}")
    elif not bak.exists():
        shutil.copy2(path, bak)
        notes.append(f"backup {bak.name}")
    else:
        # restore clean backup before rewrite
        shutil.copy2(bak, path)
        notes.append(f"restored from {bak.name}")

    doc = Document(str(path))
    polished_secs = parse_polished_sections(POLISHED)
    notes.append("polished keys: " + " | ".join(polished_secs.keys()))

    # Rename headings
    for p in doc.paragraphs:
        t = p.text.strip()
        if t in HEADING_RENAME:
            set_para_text(p, HEADING_RENAME[t])
            notes.append(f"retitle {t}")

    # Build index of heading2 paragraphs inside Results/Discussion
    paras = list(doc.paragraphs)
    # find Results / Discussion / Conclusions indices
    i_res = i_disc = i_conc = None
    for i, p in enumerate(paras):
        t = p.text.strip()
        if i_res is None and "Results" in t and p.style and "Heading 1" in p.style.name:
            i_res = i
        elif i_disc is None and "Discussion" in t and p.style and "Heading 1" in p.style.name:
            i_disc = i
        elif i_conc is None and "Conclusions" in t and p.style and "Heading 1" in p.style.name:
            i_conc = i
    notes.append(f"H1 idx res={i_res} disc={i_disc} conc={i_conc}")
    if None in (i_res, i_disc, i_conc):
        notes.append("HEADING_FAIL")
        return notes

    # Collect H2 indices in RD range
    h2 = []
    for i in range(i_res + 1, i_conc):
        p = paras[i]
        if p.style and p.style.name.startswith("Heading 2"):
            h2.append(i)
    h2.append(i_conc)  # sentinel

    for a, b in zip(h2[:-1], h2[1:]):
        title = paras[a].text.strip()
        # match polished section
        target_key = None
        for prefix, key in SECTION_MAP:
            if title.startswith(prefix) or key.startswith(title[:40]):
                # fuzzy: polished key contains prefix words
                for pk in polished_secs:
                    if pk.startswith(prefix) or prefix in pk or title[:30] in pk or pk[:30] in title:
                        target_key = pk
                        break
                if target_key:
                    break
        if not target_key:
            # try direct
            for pk in polished_secs:
                if pk.lower().split("(")[0].strip() in title.lower() or title.lower().split("(")[0].strip() in pk.lower():
                    target_key = pk
                    break
        if not target_key:
            notes.append(f"NO_MATCH for heading '{title}'")
            continue
        bodies = polished_secs[target_key]
        # prose slots in (a,b)
        slots = []
        for i in range(a + 1, b):
            p = paras[i]
            t = p.text.strip()
            if has_drawing(p):
                continue
            if is_protected(t):
                continue
            # skip short table notes?
            slots.append(i)
        notes.append(f"'{title}' -> '{target_key}': {len(slots)} slots / {len(bodies)} bodies")
        n = min(len(slots), len(bodies))
        for k in range(n):
            set_para_text(paras[slots[k]], bodies[k])
        # clear extras
        for j in slots[n:]:
            set_para_text(paras[j], "")
            notes.append(f"cleared P{j}")
        # insert overflow after last used slot or after heading
        if len(bodies) > n:
            anchor = paras[slots[n - 1]] if n else paras[a]
            for extra in bodies[n:]:
                anchor = insert_after(anchor, extra)
                notes.append(f"inserted under '{title}'")
            # refresh paras list after inserts — important for subsequent sections
            paras = list(doc.paragraphs)
            # rebuild h2 indices roughly by re-scanning (only safe if we process in order and re-find)
            # Simpler: re-find all h2 after each section with inserts
            # Break and restart? For simplicity, recompute h2 from scratch mid-loop is messy.
            # Instead: if we inserted, re-locate next headings by text.
            # We'll re-get paragraph list; next iteration uses stale indices — FIX by re-finding after inserts.

    # Because inserts invalidate indices, do a second pass? Better rewrite loop properly.
    doc.save(str(path))
    notes.append(f"saved {path.name} (pass1)")
    return notes


def update_one_v2(path: Path) -> list[str]:
    """Restore backup, then process sections from bottom to top so inserts don't shift earlier indices."""
    notes = []
    bak = path.with_name(path.stem + "_backup_pre_rd_polish.docx")
    if bak.is_file():
        shutil.copy2(bak, path)
        notes.append(f"restored {bak.name}")
    else:
        shutil.copy2(path, bak)
        notes.append(f"backup {bak.name}")

    doc = Document(str(path))
    polished_secs = parse_polished_sections(POLISHED)

    for p in doc.paragraphs:
        t = p.text.strip()
        if t in HEADING_RENAME:
            set_para_text(p, HEADING_RENAME[t])

    def h1_idx(name_substr):
        for i, p in enumerate(doc.paragraphs):
            if p.style and "Heading 1" in p.style.name and name_substr in p.text:
                return i
        return None

    i_res, i_disc, i_conc = h1_idx("Results"), h1_idx("Discussion"), h1_idx("Conclusions")
    notes.append(f"H1 {i_res},{i_disc},{i_conc}")

    # collect H2 in range
    h2_titles = []
    for i, p in enumerate(doc.paragraphs):
        if i <= i_res or i >= i_conc:
            continue
        if p.style and p.style.name.startswith("Heading 2"):
            h2_titles.append(p.text.strip())

    # process from last H2 to first
    for title in reversed(h2_titles):
        # find current index of this title
        a = None
        for i, p in enumerate(doc.paragraphs):
            if p.text.strip() == title and p.style and p.style.name.startswith("Heading 2"):
                a = i
                break
        if a is None:
            notes.append(f"missing heading now {title}")
            continue
        # next heading (H1 or H2) after a
        b = None
        for j in range(a + 1, len(doc.paragraphs)):
            st = doc.paragraphs[j].style.name if doc.paragraphs[j].style else ""
            if st.startswith("Heading 1") or st.startswith("Heading 2"):
                b = j
                break
        if b is None:
            b = len(doc.paragraphs)

        target_key = None
        for prefix, _ in SECTION_MAP:
            if title.startswith(prefix):
                for pk in polished_secs:
                    if pk.startswith(prefix) or prefix[:20] in pk:
                        target_key = pk
                        break
            if target_key:
                break
        if not target_key:
            notes.append(f"NO_MATCH '{title}'")
            continue
        bodies = polished_secs[target_key]
        slots = []
        for i in range(a + 1, b):
            p = doc.paragraphs[i]
            t = p.text.strip()
            if has_drawing(p) or is_protected(t):
                continue
            slots.append(i)
        notes.append(f"'{title}'<-'{target_key[:40]}': slots={len(slots)} bodies={len(bodies)}")
        n = min(len(slots), len(bodies))
        for k in range(n):
            set_para_text(doc.paragraphs[slots[k]], bodies[k])
        for j in slots[n:]:
            set_para_text(doc.paragraphs[j], "")
        if len(bodies) > n:
            anchor = doc.paragraphs[slots[n - 1]] if n else doc.paragraphs[a]
            # insert in reverse so order preserved when using addnext repeatedly... 
            # insert first overflow after anchor, then next after that, etc.
            for extra in bodies[n:]:
                anchor = insert_after(anchor, extra)
            notes.append(f"inserted {len(bodies)-n} under '{title}'")

    doc.save(str(path))
    notes.append(f"saved {path.name}")
    return notes


def main():
    for p in DOCXS:
        print("===", p.name, "===")
        for n in update_one_v2(p):
            print(" ", n)


if __name__ == "__main__":
    main()
