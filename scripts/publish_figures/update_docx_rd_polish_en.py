# -*- coding: utf-8 -*-
"""Sync polished Results/Discussion into plain EN docx (non-academic)."""
from __future__ import annotations
import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
POLISHED = (ROOT / "scripts" / "publish_figures" / "rd_polished.md").read_text(encoding="utf-8")

DOCXS = [
    ROOT / "outputs" / "PAPER_JCP_draft_EN.docx",
    ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN.docx",
]

# Plain EN H2 title (startswith) -> polished ### key prefix
RESULTS_MAP = [
    ("3.2. Within-composition", "Within-composition temperature generalization"),
    ("3.3. Effect of resolving", "Resolution of tracer versus interdiffusivity"),
    ("3.4. Leave-one-composition-out", "Leave-one-composition-out evaluation"),
    ("3.5. Ablation", "Ablation on separate networks"),  # body[0]
    ("3.6. Random between-group", "Ablation on separate networks"),  # body[1]
]

DISCUSSION_TITLES = [
    ("Physics-guided residual correction under Protocol W", "Physics-guided residual correction"),
    ("Thermodynamic and neighborhood limits on composition transfer", "Thermodynamic and neighborhood limits"),
    ("Counterfactual slope–intercept diagnostics (SI only)", "Counterfactual slope"),
    ("Methodological scope, limitations, and outlook", "Methodological scope"),
]


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


def insert_after(paragraph: Paragraph, text: str = "", style: str | None = None) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    para = Paragraph(new_p, paragraph._parent)
    if style:
        try:
            para.style = style
        except Exception:
            pass
    if text:
        para.add_run(text)
    return para


def delete_para(p) -> None:
    el = p._element
    parent = el.getparent()
    if parent is not None:
        parent.remove(el)


def wordify(text: str) -> str:
    """Light md/LaTeX → Word-friendly for plain EN."""
    t = text
    t = t.replace("Fig.~", "Fig. ")
    t = t.replace("Figs.~", "Figs. ")
    t = t.replace("Protocol~W", "Protocol W")
    t = t.replace("Protocol~G", "Protocol G")
    t = t.replace("Table~\\ref{tab:protocolW}", "Table 1")
    t = t.replace("Table~\\ref{tab:logo}", "Table 2")
    t = t.replace("Tables~\\ref{tab:logo}--\\ref{tab:al80_strat}", "Tables 2 and the stratified Al80 hold-out table")
    t = t.replace("Table~\\ref{tab:al80_strat}", "the stratified Al80 hold-out table")
    t = t.replace("Fig.~\\ref{fig:protocolW}", "Fig. 3")
    # leftover Table~\ref etc.
    t = re.sub(r"Table~\\ref\{[^}]+\}", "Table", t)
    t = re.sub(r"Figs?\.~\\ref\{[^}]+\}", "Fig.", t)
    # keep math $...$ as-is (plain EN already mixes)
    return t


def parse_polished_sections(md: str) -> dict[str, list[str]]:
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
            sections.setdefault(cur, []).append(wordify(text))
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


def is_protected(t: str, style: str) -> bool:
    if has_drawing_text := False:
        pass
    if not t:
        return True
    if t.startswith("Fig.") or t.startswith("Table"):
        return True
    if style.startswith("Heading"):
        return True
    return False


def find_h1(doc, substr: str) -> int | None:
    for i, p in enumerate(doc.paragraphs):
        if p.style and "Heading 1" in p.style.name and substr in p.text:
            return i
    return None


def update_docx(path: Path) -> list[str]:
    notes = []
    bak = path.with_name(path.stem + "_backup_pre_rd_polish_en.docx")
    if not bak.exists():
        shutil.copy2(path, bak)
        notes.append(f"backup {bak.name}")
    else:
        notes.append(f"backup exists {bak.name}")
        # always restore from EN-specific backup for clean apply
        shutil.copy2(bak, path)
        notes.append("restored from EN backup")

    doc = Document(str(path))
    secs = parse_polished_sections(POLISHED)
    notes.append("keys: " + " | ".join(k[:40] for k in secs))

    i_res = find_h1(doc, "Results")
    i_disc = find_h1(doc, "Discussion")
    i_lim = find_h1(doc, "Limitations")
    if None in (i_res, i_disc, i_lim):
        notes.append(f"H1 fail res={i_res} disc={i_disc} lim={i_lim}")
        return notes
    notes.append(f"H1 Results={i_res} Discussion={i_disc} Limitations={i_lim}")

    # --- Results H2 sections (process bottom-up) ---
    h2 = []
    for i, p in enumerate(doc.paragraphs):
        if i <= i_res or i >= i_disc:
            continue
        if p.style and p.style.name.startswith("Heading 2"):
            h2.append((i, p.text.strip()))

    for title in reversed([t for _, t in h2]):
        # locate current index
        a = None
        for i, p in enumerate(doc.paragraphs):
            if p.text.strip() == title and p.style and p.style.name.startswith("Heading 2"):
                a = i
                break
        if a is None:
            notes.append(f"missing H2 {title}")
            continue
        b = None
        for j in range(a + 1, len(doc.paragraphs)):
            st = doc.paragraphs[j].style.name if doc.paragraphs[j].style else ""
            if st.startswith("Heading 1") or st.startswith("Heading 2"):
                b = j
                break
        if b is None:
            b = len(doc.paragraphs)

        # dataset summary: leave unchanged
        if title.startswith("3.1"):
            notes.append("keep 3.1 Dataset summary")
            continue

        bodies = None
        which = None
        for prefix, pkey in RESULTS_MAP:
            if title.startswith(prefix.split(".")[0] + ".") or title.startswith(prefix):
                # match polished key
                for pk, vals in secs.items():
                    if pk.startswith(pkey) or pkey in pk:
                        if prefix.startswith("3.5"):
                            bodies = [vals[0]] if vals else []
                            which = "ablation-para0"
                        elif prefix.startswith("3.6"):
                            bodies = [vals[1]] if len(vals) > 1 else vals
                            which = "ablation-para1"
                        else:
                            bodies = vals
                            which = pk
                        break
                break
        if not bodies:
            notes.append(f"NO bodies for '{title}'")
            continue

        # collect replaceable slots (Normal / List Bullet, no fig/table/img)
        slots = []
        for i in range(a + 1, b):
            p = doc.paragraphs[i]
            t = p.text.strip()
            st = p.style.name if p.style else ""
            if has_drawing(p):
                continue
            if is_protected(t, st):
                continue
            if st.startswith("List"):
                slots.append(i)  # will clear bullets
                continue
            slots.append(i)

        notes.append(f"'{title}' [{which}]: slots={len(slots)} bodies={len(bodies)}")
        # Prefer Normal slots for writing; clear list bullets
        normal_slots = []
        list_slots = []
        for i in slots:
            st = doc.paragraphs[i].style.name if doc.paragraphs[i].style else ""
            if st.startswith("List"):
                list_slots.append(i)
            else:
                normal_slots.append(i)

        n = min(len(normal_slots), len(bodies))
        for k in range(n):
            set_para_text(doc.paragraphs[normal_slots[k]], bodies[k])
        for j in normal_slots[n:]:
            # clear leftover notebook lines like "Fig. 3 shows protocol W..."
            old = doc.paragraphs[j].text.strip()
            if old.startswith("Fig. 3 shows") or old.startswith("Fig. 6 contrasts") or old.startswith("LOGO results are reported"):
                set_para_text(doc.paragraphs[j], "")
                notes.append(f"cleared leftover P{j}")
            elif "Without diff_type" in old or "With diff_type" in old or old.startswith("**Without") or old.startswith("**With"):
                set_para_text(doc.paragraphs[j], "")
                notes.append(f"cleared old LOGO lead P{j}")
            elif old.startswith("After splitting by diff_type") or old.startswith("Thus the former") or old.startswith("Before splitting"):
                set_para_text(doc.paragraphs[j], "")
                notes.append(f"cleared old Al80 P{j}")
            else:
                set_para_text(doc.paragraphs[j], "")
                notes.append(f"cleared extra P{j}: {old[:50]}")
        for j in list_slots:
            set_para_text(doc.paragraphs[j], "")
            notes.append(f"cleared bullet P{j}")

        if len(bodies) > n:
            anchor = doc.paragraphs[normal_slots[n - 1]] if n else doc.paragraphs[a]
            for extra in bodies[n:]:
                anchor = insert_after(anchor, extra)
            notes.append(f"inserted {len(bodies)-n} under '{title}'")

    # --- Discussion: replace Normal blocks with H2 + polished bodies ---
    # Re-find indices after Results edits
    i_disc = find_h1(doc, "Discussion")
    i_lim = find_h1(doc, "Limitations")
    # Delete existing Normal paragraphs between Discussion and Limitations (keep none)
    # Collect elements to delete (bottom-up)
    to_del = []
    for i in range(i_disc + 1, i_lim):
        p = doc.paragraphs[i]
        st = p.style.name if p.style else ""
        if has_drawing(p):
            continue
        if st.startswith("Heading"):
            continue
        to_del.append(p)
    for p in reversed(to_del):
        delete_para(p)
        notes.append("removed old Discussion para")

    # Insert H2 + bodies after Discussion heading (reverse order so final order correct)
    disc_h = None
    for p in doc.paragraphs:
        if p.style and "Heading 1" in p.style.name and "Discussion" in p.text:
            disc_h = p
            break
    if disc_h is None:
        notes.append("Discussion heading lost")
        doc.save(str(path))
        return notes

    # Build blocks in reverse for addnext chain
    blocks: list[tuple[str, str]] = []  # (kind, text) kind heading|body
    for title, pkey in DISCUSSION_TITLES:
        bodies = None
        for pk, vals in secs.items():
            if pk.startswith(pkey) or pkey in pk:
                bodies = vals
                break
        if not bodies:
            notes.append(f"missing discussion {pkey}")
            continue
        for b in reversed(bodies):
            blocks.append(("body", b))
        blocks.append(("heading", title))

    anchor = disc_h
    # insert in reverse so first block ends up first
    for kind, text in blocks:
        if kind == "heading":
            np = insert_after(anchor, text, style="Heading 2")
        else:
            np = insert_after(anchor, text)
        # wait: addnext puts immediately after anchor; inserting reverse means last inserted is first after heading
        # So we should insert reverse-order items each as addnext(disc_h) — first insert becomes closest... 
        # Actually: A.addnext(B) then A.addnext(C) => A, C, B. So reverse insert of [h1,b1,b2,h2,...] 
        # Better: insert sequentially updating anchor forward.
        pass

    # Redo properly: forward insert
    # First we already deleted old content; disc_h next should be Limitations.
    # Clear any accidental leftovers between disc and lim again if inserts above messed up.
    # Re-implement Discussion insert cleanly:

    # Remove anything we just may have inserted incorrectly — reload approach:
    doc.save(str(path))  # noop mid — actually fix below by re-open pattern

    # Simpler approach for Discussion without the botched reverse:
    return _finish_discussion(path, notes, secs)


def _finish_discussion(path: Path, notes: list[str], secs: dict) -> list[str]:
    """Re-open and ensure Discussion is H2+prose from polished."""
    doc = Document(str(path))
    i_disc = find_h1(doc, "Discussion")
    i_lim = find_h1(doc, "Limitations")
    # delete between again
    to_del = []
    for i in range(i_disc + 1, i_lim):
        p = doc.paragraphs[i]
        if has_drawing(p):
            continue
        st = p.style.name if p.style else ""
        if st.startswith("Heading 1"):
            continue
        to_del.append(p)
    for p in reversed(to_del):
        delete_para(p)

    disc_h = doc.paragraphs[find_h1(doc, "Discussion")]
    anchor = disc_h
    for title, pkey in DISCUSSION_TITLES:
        bodies = None
        for pk, vals in secs.items():
            if pk.startswith(pkey) or pkey in pk:
                bodies = vals
                break
        if not bodies:
            notes.append(f"disc miss {pkey}")
            continue
        anchor = insert_after(anchor, title, style="Heading 2")
        for b in bodies:
            anchor = insert_after(anchor, b)
        notes.append(f"Discussion + {title}: {len(bodies)} paras")

    doc.save(str(path))
    notes.append(f"saved {path.name}")
    return notes


def verify(path: Path) -> list[str]:
    doc = Document(str(path))
    out = []
    blob = "\n".join(p.text for p in doc.paragraphs)
    checks = [
        ("26.18", "26.18" in blob),
        ("1.33", "1.33" in blob),
        ("30.98", "30.98" in blob),
        ("39.43", "39.43" in blob),
        ("Fig. 3", "Fig. 3" in blob or "Fig.~3" in blob),
        ("Fig. 7", "Fig. 7" in blob),
        ("Fig. S2", "Fig. S2" in blob or "Fig.~S2" in blob),
        ("Fig. S5", "Fig. S5" in blob or "Fig.~S5" in blob),
        ("not a PDE-residual", "not a PDE-residual" in blob or "deliberately not a PDE-residual" in blob),
        ("no PINN claim as method", "PINN" in blob),  # should appear as negation
    ]
    for name, ok in checks:
        out.append(f"check {name}: {'OK' if ok else 'FAIL'}")
    # PINN should only appear as exclusion
    for i, p in enumerate(doc.paragraphs):
        t = p.text
        if "PINN" in t and "not" not in t.lower() and "nor" not in t.lower() and "PPINN exclusion" not in t and "regarding PPINN" not in t:
            # limitations bullet may say PPINN exclusion - ok
            if "exclusion" in t or "not a PDE" in t or "deliberately not" in t:
                continue
            out.append(f"PINN_WARN P{i}: {t[:100]}")
    # structure sample
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        st = p.style.name if p.style else ""
        if "Heading" in st and ("Results" in t or "Discussion" in t or t.startswith("3.") or t.startswith("4.") or "Physics-guided" in t or "Thermodynamic" in t or "Counterfactual" in t or "Methodological" in t):
            out.append(f"struct {i} [{st}] {t[:80]}")
    return out


def main():
    for p in DOCXS:
        print("===", p.name, "===")
        # Fix update_docx: Results only then call finish — rewrite main flow cleanly
        notes = update_results_only(p)
        for n in notes:
            print(" ", n)
        print(" verify:")
        for n in verify(p):
            print(" ", n)


def update_results_only(path: Path) -> list[str]:
    notes = []
    bak = path.with_name(path.stem + "_backup_pre_rd_polish_en.docx")
    if not bak.exists():
        shutil.copy2(path, bak)
        notes.append(f"backup {bak.name}")
    else:
        shutil.copy2(bak, path)
        notes.append(f"restored {bak.name}")

    doc = Document(str(path))
    secs = parse_polished_sections(POLISHED)

    i_res = find_h1(doc, "Results")
    i_disc = find_h1(doc, "Discussion")
    notes.append(f"H1 Results={i_res} Discussion={i_disc}")

    h2_titles = []
    for i, p in enumerate(doc.paragraphs):
        if i_res < i < i_disc and p.style and p.style.name.startswith("Heading 2"):
            h2_titles.append(p.text.strip())

    for title in reversed(h2_titles):
        a = next(
            (
                i
                for i, p in enumerate(doc.paragraphs)
                if p.text.strip() == title and p.style and p.style.name.startswith("Heading 2")
            ),
            None,
        )
        if a is None:
            continue
        b = next(
            (
                j
                for j in range(a + 1, len(doc.paragraphs))
                if (doc.paragraphs[j].style.name if doc.paragraphs[j].style else "").startswith(
                    "Heading"
                )
            ),
            len(doc.paragraphs),
        )
        if title.startswith("3.1"):
            notes.append("keep 3.1")
            continue

        bodies = None
        tag = ""
        if title.startswith("3.2"):
            for pk, vals in secs.items():
                if pk.startswith("Within-composition"):
                    bodies, tag = vals, pk
                    break
        elif title.startswith("3.3"):
            for pk, vals in secs.items():
                if pk.startswith("Resolution of tracer"):
                    bodies, tag = vals, pk
                    break
        elif title.startswith("3.4"):
            for pk, vals in secs.items():
                if pk.startswith("Leave-one-composition-out"):
                    bodies, tag = vals, pk
                    break
        elif title.startswith("3.5"):
            for pk, vals in secs.items():
                if pk.startswith("Ablation on separate"):
                    bodies, tag = [vals[0]], "ablation0"
                    break
        elif title.startswith("3.6"):
            for pk, vals in secs.items():
                if pk.startswith("Ablation on separate"):
                    bodies, tag = ([vals[1]] if len(vals) > 1 else vals), "ablation1"
                    break
        if not bodies:
            notes.append(f"no bodies {title}")
            continue

        normal_slots, list_slots = [], []
        for i in range(a + 1, b):
            p = doc.paragraphs[i]
            t = p.text.strip()
            st = p.style.name if p.style else ""
            if has_drawing(p) or is_protected(t, st):
                continue
            if st.startswith("List"):
                list_slots.append(i)
            else:
                normal_slots.append(i)

        notes.append(f"{title} <- {tag}: Nslots={len(normal_slots)} Lslots={len(list_slots)} bodies={len(bodies)}")
        n = min(len(normal_slots), len(bodies))
        for k in range(n):
            set_para_text(doc.paragraphs[normal_slots[k]], bodies[k])
        for j in normal_slots[n:]:
            set_para_text(doc.paragraphs[j], "")
            notes.append(f"cleared P{j}")
        for j in list_slots:
            set_para_text(doc.paragraphs[j], "")
            notes.append(f"cleared bullet P{j}")
        if len(bodies) > n:
            anchor = doc.paragraphs[normal_slots[n - 1]] if n else doc.paragraphs[a]
            for extra in bodies[n:]:
                anchor = insert_after(anchor, extra)
            notes.append(f"inserted {len(bodies)-n}")

    doc.save(str(path))
    # Discussion rebuild
    return _finish_discussion(path, notes, secs)


if __name__ == "__main__":
    main()
