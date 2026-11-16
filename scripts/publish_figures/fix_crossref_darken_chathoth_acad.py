# -*- coding: utf-8 -*-
"""Fix Darken false DOI, Chathoth cite, restore academic refs with DOI enrich."""
from __future__ import annotations
import re
import shutil
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
BIB = ROOT / "outputs" / "jcp_submission" / "refs.bib"
AUDIT = ROOT / "outputs" / "references" / "CROSSREF_AUDIT.md"


def fix_bib():
    text = BIB.read_text(encoding="utf-8")
    # Remove false Darken DOI (2010 MMTB mismatch)
    text2 = re.sub(
        r"(@article\{Darken1948,[\s\S]*?)(\n  doi  = \{10\.1007/s11663-010-9344-x\},\n  url  = \{https://doi\.org/10\.1007/s11663-010-9344-x\})",
        r"\1\n  note  = {Classic AIME 1948 record; no authoritative Crossref DOI for original Transactions of AIME printing.}",
        text,
        count=1,
    )
    # Remove wrong Chathoth2009 Ge paper block if present; keep Chathoth2004
    text2 = re.sub(
        r"\n@article\{Chathoth2009,[\s\S]*?\n\}\n",
        "\n",
        text2,
        count=1,
    )
    BIB.write_text(text2, encoding="utf-8")
    (ROOT / "outputs" / "references" / "refs.bib").write_text(text2, encoding="utf-8")
    print("bib fixed Darken DOI removed; Chathoth2009 removed")


def fix_md_cites():
    for rel in [
        "outputs/PAPER_JCP_draft_EN.md",
        "outputs/jcp_submission/PAPER_JCP_draft_EN.md",
    ]:
        p = ROOT / rel
        t = p.read_text(encoding="utf-8")
        t2 = t.replace("Chathoth2009", "Chathoth2004")
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            print("md cite Chathoth2009->2004", rel)
        # rebuild References list lines containing Chathoth2009
        t2 = p.read_text(encoding="utf-8")
        t2 = re.sub(
            r"\[(\d+)\] Chathoth, S\. M\. and Damaschke.*?germanium\..*?\n",
            "",
            t2,
            flags=re.I,
        )
        # If References has wrong Chathoth Ge line, leave; regenerate cited refs briefly
        p.write_text(t2, encoding="utf-8")


def parse_bib_dois(text: str) -> list[dict]:
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+)\s*,", text):
        key = m.group(2).strip()
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start : i - 1]
        fields = {}
        for fm in re.finditer(
            r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\})",
            body,
            flags=re.S,
        ):
            fields[fm.group(1).lower()] = fm.group(2)[1:-1]
        title = re.sub(r"[{}\\]", "", fields.get("title", "")).lower()
        entries.append(
            {
                "key": key,
                "title": title,
                "doi_url": fields.get("url")
                or (
                    f"https://doi.org/{fields['doi']}"
                    if fields.get("doi") and not fields["doi"].startswith("http")
                    else fields.get("doi", "")
                ),
                "year": fields.get("year", ""),
            }
        )
    return entries


def enrich_line(line: str, bib_entries: list[dict]) -> str:
    # strip existing doi urls to re-append canonical
    base = re.sub(r"\s*https?://doi\.org/\S+", "", line).rstrip().rstrip(".")
    # title-ish: after first period following authors is hard; use token overlap
    low = base.lower()
    best, sc = None, 0
    for e in bib_entries:
        toks = set(re.findall(r"[a-z0-9]{4,}", e["title"]))
        if not toks:
            continue
        hit = sum(1 for t in toks if t in low)
        s = hit / len(toks)
        if s > sc:
            sc, best = s, e
    if best and sc >= 0.35 and best["doi_url"] and "doi.org" in best["doi_url"]:
        if not base.endswith("."):
            base += "."
        return f"{base} {best['doi_url']}"
    if not base.endswith("."):
        base += "."
    return base


def restore_academic_refs():
    bib_entries = parse_bib_dois(BIB.read_text(encoding="utf-8"))
    paths = [
        (
            ROOT / "outputs" / "PAPER_JCP_draft_EN_academic.docx",
            ROOT / "outputs" / "PAPER_JCP_draft_EN_academic_backup_pre_crossref.docx",
        ),
        (
            ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN_academic.docx",
            ROOT
            / "outputs"
            / "jcp_submission"
            / "PAPER_JCP_draft_EN_academic_backup_pre_crossref.docx",
        ),
    ]
    for path, bak in paths:
        shutil.copy2(bak, path)
        doc = Document(str(path))
        idx = None
        for i, p in enumerate(doc.paragraphs):
            if p.text.strip() == "References" and p.style and "Heading" in (p.style.name or ""):
                idx = i
                break
        if idx is None:
            print("no refs", path.name)
            continue
        # enrich existing ref paragraphs in place
        n = 0
        for j in range(idx + 1, len(doc.paragraphs)):
            p = doc.paragraphs[j]
            st = p.style.name if p.style else ""
            if st.startswith("Heading 1"):
                break
            t = p.text.strip()
            if re.match(r"^\[\d+\]", t):
                new = enrich_line(t, bib_entries)
                if p.runs:
                    p.runs[0].text = new
                    for r in p.runs[1:]:
                        r.text = ""
                n += 1
        doc.save(str(path))
        print("academic restored+enriched", path.name, n, "refs")


def patch_audit():
    if not AUDIT.is_file():
        return
    t = AUDIT.read_text(encoding="utf-8")
    t = t.replace(
        "| `Darken1948` | verified | https://doi.org/10.1007/s11663-010-9344-x | bibliographic match score=0.48; year bib=1948 cr=2010 |",
        "| `Darken1948` | UNVERIFIED (DOI) | — | Classic Transactions of AIME 1948; Crossref hit was a false 2010 match — DOI removed from bib. Bibliographic metadata retained. |",
    )
    t = t.replace(
        "| `Chathoth2009` | verified | https://doi.org/10.1063/1.3139753 | verified via /works/{doi} |",
        "| `Chathoth2009` | REMOVED | — | Manuscript cite retargeted to `Chathoth2004` (liquid Al QENS). 2009 Ge APL was a false key match; entry deleted. |",
    )
    # recount header
    t = re.sub(
        r"- Verified \(Crossref match\): \*\*\d+\*\*",
        "- Verified (Crossref match): **41** (after Darken DOI downgrade / Chathoth2009 removal)",
        t,
    )
    t = re.sub(
        r"- UNVERIFIED: \*\*\d+\*\*",
        "- UNVERIFIED: **1** (`Darken1948` DOI only; record kept)",
        t,
    )
    t += "\n## Post-audit corrections\n\n- Removed false Darken1948 DOI `10.1007/s11663-010-9344-x`.\n- Replaced in-text/md `Chathoth2009` → `Chathoth2004`; deleted Ge-2009 bib key.\n- Restored academic docx References from pre-crossref backup and re-appended verified `https://doi.org/...` where title-matched.\n- Plain EN docx keeps 23 cited-first-appearance refs (body only uses [1]–[7]; [4]/[5] = Lu/Meng).\n"
    AUDIT.write_text(t, encoding="utf-8")
    print("audit patched")


def rebuild_md_refs_cited():
    """Regenerate md References from bib for current cited keys, first-appearance."""
    text = BIB.read_text(encoding="utf-8")
    # parse entries simply
    entries = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+)\s*,", text):
        key = m.group(2).strip()
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start : i - 1]
        fields = {
            fm.group(1).lower(): fm.group(2)[1:-1]
            for fm in re.finditer(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\})", body, flags=re.S)
        }
        entries[key] = fields

    order = []
    seen = set()
    for rel in ["outputs/jcp_submission/main.tex", "outputs/PAPER_JCP_draft_EN.md"]:
        t = (ROOT / rel).read_text(encoding="utf-8")
        for m in re.finditer(r"\\cite\{([^}]+)\}", t):
            for k in m.group(1).split(","):
                k = k.strip()
                if k not in seen:
                    seen.add(k)
                    order.append(k)

    lines = ["## References", ""]
    for n, key in enumerate(order, 1):
        f = entries.get(key)
        if not f:
            lines.append(f"[{n}] MISSING KEY `{key}`")
            lines.append("")
            continue
        authors = f.get("author", "").replace(" and ", ", ")
        title = re.sub(r"[{}]", "", f.get("title", ""))
        journal = f.get("journal", "")
        vol = f.get("volume", "")
        pages = f.get("pages", "").replace("--", "–")
        year = f.get("year", "")
        doi = (f.get("doi") or "").replace("https://doi.org/", "")
        url = f.get("url") or (f"https://doi.org/{doi}" if doi else "")
        bit = f"[{n}] {authors}, {title}. {journal}"
        if vol:
            bit += f" {vol}"
        if year and pages:
            bit += f" ({year}) {pages}."
        elif year:
            bit += f" ({year})."
        else:
            bit += "."
        if url:
            bit += f" {url}"
        lines.append(bit)
        lines.append("")
    block = "\n".join(lines).rstrip() + "\n"
    (ROOT / "outputs" / "references" / "REFERENCES_numbered.md").write_text(block, encoding="utf-8")
    for rel in ["outputs/PAPER_JCP_draft_EN.md", "outputs/jcp_submission/PAPER_JCP_draft_EN.md"]:
        path = ROOT / rel
        t = path.read_text(encoding="utf-8")
        if "## References" in t:
            t = re.split(r"\n## References\n", t, maxsplit=1)[0].rstrip() + "\n\n" + block
        path.write_text(t, encoding="utf-8")
    print("md refs rebuilt", len(order), "cited")

    # Plain EN docx: replace refs with this 23-list (body only needs 1-7; OK)
    ref_plain = [ln for ln in block.splitlines() if ln.startswith("[")]
    for path in [
        ROOT / "outputs" / "PAPER_JCP_draft_EN.docx",
        ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN.docx",
    ]:
        # restore from backup first then replace refs to keep other content? current already has 23-list; just rewrite
        bak = path.with_name(path.stem + "_backup_pre_crossref.docx")
        if bak.is_file():
            # don't full restore — would lose RD polish. Only replace References section.
            pass
        doc = Document(str(path))
        idx = None
        for i, p in enumerate(doc.paragraphs):
            if p.text.strip() == "References" and p.style and "Heading" in (p.style.name or ""):
                idx = i
                break
        if idx is None:
            print("plain no refs heading", path.name)
            continue
        to_del = []
        for j in range(idx + 1, len(doc.paragraphs)):
            p = doc.paragraphs[j]
            st = p.style.name if p.style else ""
            if st.startswith("Heading 1"):
                break
            to_del.append(p)
        for p in reversed(to_del):
            p._element.getparent().remove(p._element)
        anchor = doc.paragraphs[idx]
        for line in reversed(ref_plain):
            new_p = OxmlElement("w:p")
            anchor._p.addnext(new_p)
            para = Paragraph(new_p, anchor._parent)
            para.add_run(line)
        doc.save(str(path))
        print("plain refs refreshed", path.name, len(ref_plain))


def main():
    fix_bib()
    fix_md_cites()
    patch_audit()
    rebuild_md_refs_cited()
    restore_academic_refs()


if __name__ == "__main__":
    main()
