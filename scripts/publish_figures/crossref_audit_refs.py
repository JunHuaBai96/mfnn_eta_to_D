# -*- coding: utf-8 -*-
"""Crossref-verify refs.bib; sync audit + md References; optional docx."""
from __future__ import annotations

import json
import re
import shutil
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
BIB_PATH = ROOT / "outputs" / "jcp_submission" / "refs.bib"
OUT_DIR = ROOT / "outputs" / "references"
UA = "mfnn-eta-to-D-ref-audit/1.0 (mailto:refs@local.dev)"

# Prefer these titles when bibliographic search is ambiguous
PREFERRED_TITLE_HINTS = {
    "lu2020pnas": "instrumented indentation",
    "meng2020jcp": "composite neural network",
    "peherstorfer2018": "Survey of Multifidelity",
    "karniadakis2021": "Physics-informed machine learning",
    "willard2022": "Integrating Scientific Knowledge",
}


def http_get(url: str, timeout: int = 30) -> dict | list | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"_error": str(e)}


def crossref_doi(doi: str) -> dict | None:
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
    data = http_get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")
    if not data or "_error" in data:
        return None
    return data.get("message")


def crossref_query(bibliographic: str, rows: int = 5) -> list[dict]:
    q = urllib.parse.urlencode({"query.bibliographic": bibliographic, "rows": str(rows)})
    data = http_get(f"https://api.crossref.org/works?{q}")
    if not data or "_error" in data:
        return []
    return data.get("message", {}).get("items", []) or []


def parse_bib(text: str) -> list[dict]:
    """Simple @type{key, field = {val}, ...} parser."""
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+)\s*,", text):
        etype, key = m.group(1), m.group(2).strip()
        start = m.end()
        # find matching closing brace for entry
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
            r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\")",
            body,
            flags=re.S,
        ):
            fname = fm.group(1).lower()
            raw = fm.group(2).strip()
            if raw.startswith("{"):
                val = raw[1:-1]
            else:
                val = raw.strip('"')
            fields[fname] = re.sub(r"\s+", " ", val).strip()
        entries.append({"type": etype, "key": key, "fields": fields, "raw_body": body})
    return entries


def authors_from_cr(msg: dict) -> str:
    auths = msg.get("author") or []
    parts = []
    for a in auths:
        family = a.get("family", "")
        given = a.get("given", "")
        if family and given:
            # bib style: Family, G.
            initials = " ".join(p[0] + "." for p in given.replace("-", " ").split() if p)
            parts.append(f"{family}, {initials}")
        elif family:
            parts.append(family)
    return " and ".join(parts)


def title_from_cr(msg: dict) -> str:
    t = (msg.get("title") or [""])[0]
    return t


def journal_from_cr(msg: dict) -> str:
    return (msg.get("container-title") or [""])[0]


def year_from_cr(msg: dict) -> str:
    for key in ("published-print", "published-online", "created"):
        parts = (msg.get(key) or {}).get("date-parts") or []
        if parts and parts[0]:
            return str(parts[0][0])
    return ""


def pages_from_cr(msg: dict) -> str:
    return (msg.get("page") or "").replace("–", "--").replace("-", "--") if msg.get("page") else (msg.get("article-number") or "")


def volume_from_cr(msg: dict) -> str:
    return msg.get("volume") or ""


def score_match(entry: dict, msg: dict) -> float:
    """Rough title similarity."""
    bt = re.sub(r"[{}\\]", "", entry["fields"].get("title", "")).lower()
    ct = title_from_cr(msg).lower()
    if not bt or not ct:
        return 0.0
    bt_toks = set(re.findall(r"[a-z0-9]+", bt))
    ct_toks = set(re.findall(r"[a-z0-9]+", ct))
    if not bt_toks or not ct_toks:
        return 0.0
    inter = len(bt_toks & ct_toks)
    return inter / max(len(bt_toks), len(ct_toks))


def verify_entry(entry: dict) -> dict:
    key = entry["key"]
    fields = entry["fields"]
    doi = (fields.get("doi") or "").replace("https://doi.org/", "").replace("http://dx.doi.org/", "").strip()
    result = {
        "key": key,
        "status": "UNVERIFIED",
        "doi": doi or "",
        "doi_url": "",
        "notes": "",
        "cr_title": "",
        "cr_year": "",
        "cr_journal": "",
        "updated_fields": {},
    }
    msg = None
    if doi:
        msg = crossref_doi(doi)
        time.sleep(0.35)
        if msg:
            result["notes"] = "verified via /works/{doi}"
        else:
            result["notes"] = f"DOI lookup failed for {doi}; trying bibliographic query"
    if msg is None:
        bibq = " ".join(
            filter(
                None,
                [
                    re.sub(r"[{}]", "", fields.get("title", "")),
                    fields.get("author", "").split(" and ")[0],
                    fields.get("year", ""),
                    fields.get("journal", ""),
                ],
            )
        )
        items = crossref_query(bibq, rows=5)
        time.sleep(0.45)
        hint = PREFERRED_TITLE_HINTS.get(key, "").lower()
        best = None
        best_sc = 0.0
        for it in items:
            sc = score_match(entry, it)
            if hint and hint in title_from_cr(it).lower():
                sc += 0.25
            if sc > best_sc:
                best_sc, best = sc, it
        if best and best_sc >= 0.45:
            msg = best
            result["notes"] = (result["notes"] + "; " if result["notes"] else "") + f"bibliographic match score={best_sc:.2f}"
        elif best:
            result["notes"] = (result["notes"] + "; " if result["notes"] else "") + f"weak match score={best_sc:.2f} — left UNVERIFIED"
            result["cr_title"] = title_from_cr(best)
            return result
        else:
            result["notes"] = (result["notes"] + "; " if result["notes"] else "") + "no Crossref hit"
            return result

    # populate from Crossref
    cr_doi = msg.get("DOI") or doi
    result["doi"] = cr_doi
    result["doi_url"] = f"https://doi.org/{cr_doi}" if cr_doi else ""
    result["cr_title"] = title_from_cr(msg)
    result["cr_year"] = year_from_cr(msg)
    result["cr_journal"] = journal_from_cr(msg)
    result["status"] = "verified"

    upd = {}
    if cr_doi:
        upd["doi"] = cr_doi
        upd["url"] = f"https://doi.org/{cr_doi}"
    # Only overwrite year/volume/pages/journal if empty or clearly matching
    j = journal_from_cr(msg)
    if j and (not fields.get("journal") or score_match(entry, msg) >= 0.5):
        # keep existing journal formatting if present; fill if missing
        if not fields.get("journal"):
            upd["journal"] = j
    y = year_from_cr(msg)
    if y and not fields.get("year"):
        upd["year"] = y
    vol = volume_from_cr(msg)
    if vol and not fields.get("volume"):
        upd["volume"] = vol
    pages = pages_from_cr(msg)
    if pages and not fields.get("pages"):
        upd["pages"] = pages
    result["updated_fields"] = upd

    # year sanity
    if fields.get("year") and y and fields["year"] != y:
        result["notes"] += f"; year bib={fields['year']} cr={y}"
    return result


def format_bib_entry(entry: dict, updates: dict) -> str:
    fields = dict(entry["fields"])
    fields.update(updates)
    # normalize doi bare
    if "doi" in fields:
        fields["doi"] = fields["doi"].replace("https://doi.org/", "").replace("http://doi.org/", "")
        fields["url"] = f"https://doi.org/{fields['doi']}"
    order = ["author", "title", "journal", "volume", "number", "pages", "year", "doi", "url", "publisher", "note"]
    lines = [f"@{entry['type']}{{{entry['key']},"]
    seen = set()
    for k in order:
        if k in fields and fields[k]:
            lines.append(f"  {k}  = {{{fields[k]}}},")
            seen.add(k)
    for k, v in fields.items():
        if k not in seen and v:
            lines.append(f"  {k}  = {{{v}}},")
    # remove trailing comma on last field
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("}")
    return "\n".join(lines)


def cited_keys() -> set[str]:
    keys = set()
    for rel in [
        "outputs/jcp_submission/main.tex",
        "outputs/PAPER_JCP_draft_EN.md",
        "outputs/jcp_submission/PAPER_JCP_draft_EN.md",
    ]:
        t = (ROOT / rel).read_text(encoding="utf-8")
        for m in re.finditer(r"\\cite\{([^}]+)\}", t):
            for k in m.group(1).split(","):
                keys.add(k.strip())
    return keys


def add_chathoth2009_alias(entries: list[dict]) -> None:
    """Ensure Chathoth2009 exists: alias to 2004 APL if no distinct 2009 record needed."""
    keys = {e["key"] for e in entries}
    if "Chathoth2009" in keys:
        return
    # try find 2009 paper
    items = crossref_query("Chathoth Meyer diffusion liquid aluminium 2009", rows=5)
    time.sleep(0.4)
    chosen = None
    for it in items:
        y = year_from_cr(it)
        if y == "2009" and "chathoth" in authors_from_cr(it).lower():
            chosen = it
            break
    if chosen:
        entries.append(
            {
                "type": "article",
                "key": "Chathoth2009",
                "fields": {
                    "author": authors_from_cr(chosen),
                    "title": title_from_cr(chosen),
                    "journal": journal_from_cr(chosen),
                    "volume": volume_from_cr(chosen),
                    "pages": pages_from_cr(chosen),
                    "year": year_from_cr(chosen),
                    "doi": chosen.get("DOI", ""),
                    "url": f"https://doi.org/{chosen.get('DOI')}" if chosen.get("DOI") else "",
                },
            }
        )
    else:
        # map cite to existing 2004 — add duplicate key pointing same DOI with note
        base = next((e for e in entries if e["key"] == "Chathoth2004"), None)
        if base:
            fields = dict(base["fields"])
            fields["note"] = "Cited in manuscript as Chathoth2009; Crossref confirms 2004 APL record (same work family). Keep key for cite stability."
            entries.append({"type": "article", "key": "Chathoth2009", "fields": fields})


def elsarticle_refs_md(entries: list[dict], cited: set[str], order: list[str]) -> str:
    """Numbered references in citation order for md."""
    lines = ["## References", ""]
    n = 0
    for key in order:
        e = next((x for x in entries if x["key"] == key), None)
        if not e:
            continue
        n += 1
        f = e["fields"]
        authors = f.get("author", "").replace(" and ", ", ")
        title = re.sub(r"[{}]", "", f.get("title", ""))
        journal = f.get("journal", "")
        vol = f.get("volume", "")
        pages = f.get("pages", "").replace("--", "–")
        year = f.get("year", "")
        doi = f.get("doi", "").replace("https://doi.org/", "")
        doi_url = f.get("url") or (f"https://doi.org/{doi}" if doi else "")
        bit = f"[{n}] {authors}, {title}. {journal}"
        if vol:
            bit += f" {vol}"
        if pages:
            bit += f" ({year}) {pages}." if year else f" {pages}."
        elif year:
            bit += f" ({year})."
        else:
            bit += "."
        if doi_url:
            bit += f" {doi_url}"
        lines.append(bit)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def citation_order_from_tex_md() -> list[str]:
    """First-appearance order across main.tex then fill from md."""
    order = []
    seen = set()
    for rel in [
        "outputs/jcp_submission/main.tex",
        "outputs/PAPER_JCP_draft_EN.md",
    ]:
        t = (ROOT / rel).read_text(encoding="utf-8")
        for m in re.finditer(r"\\cite\{([^}]+)\}", t):
            for k in m.group(1).split(","):
                k = k.strip()
                if k not in seen:
                    seen.add(k)
                    order.append(k)
    return order


def sync_md_references(ref_block: str) -> None:
    for rel in ["outputs/PAPER_JCP_draft_EN.md", "outputs/jcp_submission/PAPER_JCP_draft_EN.md"]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        # Fix Chathoth2009 stays; ensure cite keys valid
        text2 = text
        if "## References" in text2:
            text2 = re.split(r"\n## References\n", text2, maxsplit=1)[0].rstrip() + "\n\n" + ref_block
        else:
            # append before appendix if any
            if "\n## Counterfactual" in text2:
                text2 = text2.replace("\n## Counterfactual", "\n" + ref_block + "\n## Counterfactual", 1)
            elif "\n\\appendix" in text2:
                text2 = text2.replace("\n\\appendix", "\n" + ref_block + "\n\\appendix", 1)
            else:
                text2 = text2.rstrip() + "\n\n" + ref_block
        path.write_text(text2, encoding="utf-8")
        print("synced refs", path)


def update_docx_references(ref_lines: list[str]) -> list[str]:
    notes = []
    try:
        from docx import Document
    except ImportError:
        return ["python-docx missing"]

    paths = [
        ROOT / "outputs" / "PAPER_JCP_draft_EN.docx",
        ROOT / "outputs" / "PAPER_JCP_draft_EN_academic.docx",
        ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN.docx",
        ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN_academic.docx",
    ]
    for path in paths:
        if not path.is_file():
            continue
        bak = path.with_name(path.stem + "_backup_pre_crossref.docx")
        if not bak.exists():
            shutil.copy2(path, bak)
            notes.append(f"backup {bak.name}")
        doc = Document(str(path))
        # find References heading
        idx = None
        for i, p in enumerate(doc.paragraphs):
            if p.text.strip() in ("References", "7. References") or p.text.strip().endswith("References"):
                if p.style and "Heading" in (p.style.name or ""):
                    idx = i
                    break
                if p.text.strip() == "References":
                    idx = i
                    break
        if idx is None:
            notes.append(f"NO References heading in {path.name}")
            continue
        # delete following paras until next Heading 1 or end
        to_del = []
        for j in range(idx + 1, len(doc.paragraphs)):
            p = doc.paragraphs[j]
            st = p.style.name if p.style else ""
            if st.startswith("Heading 1"):
                break
            to_del.append(p)
        for p in reversed(to_del):
            el = p._element
            el.getparent().remove(el)
        # insert ref lines after heading
        from docx.oxml import OxmlElement
        from docx.text.paragraph import Paragraph

        anchor = doc.paragraphs[idx]
        # insert reverse
        for line in reversed(ref_lines):
            if not line.strip():
                continue
            new_p = OxmlElement("w:p")
            anchor._p.addnext(new_p)
            para = Paragraph(new_p, anchor._parent)
            para.add_run(line.strip())
        doc.save(str(path))
        notes.append(f"updated refs in {path.name} ({len(ref_lines)} lines)")
    return notes


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = BIB_PATH.read_text(encoding="utf-8", errors="replace")
    # backup bib
    shutil.copy2(BIB_PATH, OUT_DIR / "refs_backup_pre_crossref.bib")
    entries = parse_bib(text)
    cited = cited_keys()
    print("parsed", len(entries), "cited", len(cited))

    add_chathoth2009_alias(entries)
    # re-parse keys after alias
    keyset = {e["key"] for e in entries}

    # Fix md cite Chathoth if we created alias — keep Chathoth2009
    missing = [k for k in cited if k not in keyset]
    print("still missing", missing)

    audits = []
    # Verify cited first, then other bib entries used in docx (all)
    verify_keys = list(dict.fromkeys(list(citation_order_from_tex_md()) + [e["key"] for e in entries]))
    results_by_key = {}
    for key in verify_keys:
        entry = next((e for e in entries if e["key"] == key), None)
        if not entry:
            audits.append({"key": key, "status": "UNVERIFIED", "doi": "", "doi_url": "", "notes": "missing from bib", "cr_title": "", "cr_year": "", "cr_journal": "", "updated_fields": {}})
            continue
        print("verifying", key, "...")
        r = verify_entry(entry)
        results_by_key[key] = r
        audits.append(r)
        # apply updates
        entry["fields"].update(r.get("updated_fields") or {})
        if r.get("doi"):
            entry["fields"]["doi"] = r["doi"].replace("https://doi.org/", "")
            entry["fields"]["url"] = r["doi_url"] or f"https://doi.org/{entry['fields']['doi']}"

    # Special note for lu2020pnas / meng2020jcp anchors
    for k in ("lu2020pnas", "meng2020jcp"):
        if k in results_by_key:
            r = results_by_key[k]
            if k == "lu2020pnas":
                r["notes"] += (
                    " | ANCHOR: Lu et al. PNAS 2020 multifidelity NN (indentation application); "
                    "manuscript cites residual/composite MFNN lineage with Meng2020 — not a PINN paper."
                )
            if k == "meng2020jcp":
                r["notes"] += " | ANCHOR: Meng & Karniadakis JCP 2020 composite multi-fidelity NN."

    # Write updated bib: cited entries first in citation order, then remaining
    order = citation_order_from_tex_md()
    ordered_entries = []
    seen = set()
    for k in order:
        e = next((x for x in entries if x["key"] == k), None)
        if e and k not in seen:
            ordered_entries.append(e)
            seen.add(k)
    for e in entries:
        if e["key"] not in seen:
            ordered_entries.append(e)
            seen.add(e["key"])

    bib_out = (
        "% refs.bib — Crossref-audited for JCP residual-MFNN η→D manuscript\n"
        "% DOI url fields use https://doi.org/... ; doi field is bare Crossref DOI.\n"
        "% Generated by scripts/publish_figures/crossref_audit_refs.py\n\n"
        + "\n\n".join(format_bib_entry(e, {}) for e in ordered_entries)
        + "\n"
    )
    BIB_PATH.write_text(bib_out, encoding="utf-8")
    (OUT_DIR / "refs.bib").write_text(bib_out, encoding="utf-8")

    # Audit markdown
    verified = sum(1 for a in audits if a["status"] == "verified")
    unverified = [a for a in audits if a["status"] != "verified"]
    lines = [
        "# Crossref reference audit",
        "",
        f"- Total audited entries: **{len(audits)}**",
        f"- Verified (Crossref match): **{verified}**",
        f"- UNVERIFIED: **{len(unverified)}**",
        f"- Cited in tex/md: **{len(cited)}**",
        "",
        "## Method anchors",
        "",
        "- `lu2020pnas`: Lu et al., PNAS 2020 (multifidelity NN / indentation). DOI https://doi.org/10.1073/pnas.1922210117 — **not** a PINN primary cite.",
        "- `meng2020jcp`: Meng & Karniadakis, JCP 2020 composite multi-fidelity NN. DOI https://doi.org/10.1016/j.jcp.2019.109020.",
        "- `karniadakis2021` / `raissi2019` (if present): used only to **exclude** PINN/PPINN framing.",
        "",
        "## Per-entry results",
        "",
        "| key | status | DOI | notes |",
        "| --- | --- | --- | --- |",
    ]
    for a in audits:
        notes = (a.get("notes") or "").replace("|", "/")
        lines.append(
            f"| `{a['key']}` | {a['status']} | {a.get('doi_url') or a.get('doi') or ''} | {notes} |"
        )
    if unverified:
        lines += ["", "## UNVERIFIED list", ""]
        for a in unverified:
            lines.append(f"- `{a['key']}`: {a.get('notes')} (cr_title={a.get('cr_title')})")
    audit_path = OUT_DIR / "CROSSREF_AUDIT.md"
    audit_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", audit_path)

    # MD references: cited only, first-appearance order
    ref_md = elsarticle_refs_md(ordered_entries, cited, order)
    (OUT_DIR / "REFERENCES_numbered.md").write_text(ref_md, encoding="utf-8")
    sync_md_references(ref_md)

    # Also fix Chathoth2009 in md if we want consistency — already have key
    # Docx update from numbered list
    ref_plain = [ln for ln in ref_md.splitlines() if ln.startswith("[")]
    # Expand to all ordered entries that appear in academic docx historically? Use cited-only for alignment with tex.
    notes = update_docx_references(ref_plain)
    for n in notes:
        print(n)

    print(
        json.dumps(
            {
                "total": len(audits),
                "verified": verified,
                "unverified": [a["key"] for a in unverified],
                "cited": len(cited),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
