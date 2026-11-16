# -*- coding: utf-8 -*-
"""Scrub residual main-text Fig.8–10 → Gemini SI S2/S4/S5 (or drop)."""
from __future__ import annotations
import re
import shutil
from pathlib import Path

from docx import Document

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")

MD_PATHS = [
    ROOT / "outputs" / "PAPER_JCP_draft_EN.md",
    ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN.md",
]
TEX_PATHS = [
    ROOT / "outputs" / "jcp_submission" / "main.tex",
]
CAPTION_PATHS = [
    ROOT / "outputs" / "figures" / "FIGURE_CAPTIONS.md",
    ROOT / "outputs" / "jcp_submission" / "figures" / "FIGURE_CAPTIONS.md",
]
DOCX_PATHS = [
    ROOT / "outputs" / "PAPER_JCP_draft_EN.docx",
    ROOT / "outputs" / "PAPER_JCP_draft_EN_academic.docx",
    ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN.docx",
    ROOT / "outputs" / "jcp_submission" / "PAPER_JCP_draft_EN_academic.docx",
]

# Ordered plain replacements (exact strings first)
PLAIN = [
    (
        "Fig.~\\ref{fig:ablation}",
        "Fig.~S5",
    ),
    (
        "Fig.~\\ref{fig:WvsG}",
        "Fig.~S2",
    ),
    (
        "Appendix Fig.~\\ref{fig:si_al80_shift}",
        "Fig.~S4",
    ),
    (
        "Fig.~\\ref{fig:si_al80_shift}",
        "Fig.~S4",
    ),
    (
        "**Fig. 8.** Ablation on Al–Cu LOGO. (a) \\(Al_{80}Cu_{20}\\) tracer and interdiffusivity hold-outs for joint residual MFNN with diffusion-type one-hot versus separately trained tracer/inter networks. (b) Unweighted fold-mean MFNN MAPE (separate path excludes pathological MAPE outliers \\(>10^{4}\\)). Separate training does not outperform the joint model.",
        "**Fig. S5.** Ablation on Al–Cu LOGO (SI; Gemini S5). (a) \\(Al_{80}Cu_{20}\\) tracer and interdiffusivity hold-outs for joint residual MFNN with diffusion-type one-hot versus separately trained tracer/inter networks. (b) Unweighted fold-mean MFNN MAPE (separate path excludes pathological MAPE outliers \\(>10^{4}\\)). Separate training does not outperform the joint model. File: `FigS5_difftype_split_ablation`.",
    ),
    (
        "**Fig. 9.** Protocol W versus Protocol G MAPE (mean \\(±\\) population std over seeds \\(\\{0,1,2,42,123\\}\\)). Protocol W remains the primary claim; Protocol G is a cautionary composition-hold-out check.",
        "**Fig. S2 (caution).** Protocol W versus Protocol G MAPE (mean \\(±\\) population std over seeds \\(\\{0,1,2,42,123\\}\\)). Protocol W remains the primary claim; Protocol G is a cautionary composition-hold-out check (SI; Gemini S2). File: `FigS2_protocol_G_variance`.",
    ),
    (
        "**Fig. 10.** Supplementary Information (cf. Figs.~S1–S5; few-shot anchors now Fig.~S3) oracle diagnostic for Al80Cu20_tracer (counterfactual; not a Protocol W metric and not LOGO success). Seed-mean MFNN \\(k{=}0\\) predictions versus a zero-retrain post-hoc logarithmic intercept shift calibrated at a single low-\\(T\\) point (\\(983 K\\)): MAPE on the remaining \\(n{=}9\\) temperatures falls from \\(∼\\)175% (\\(Factor2=0\\)) to \\(∼\\)9.8% (\\(Factor2=1\\)), with \\(\\delta≈ -0.48≈ -\\log_{10} 3\\). Returning the same point to unweighted training does not recover Factor2. Related \\(k{=}2\\) anchor upweighting (\\(w{=}5\\)–\\(10\\)) is summarized in the Discussion; full tables are SI-only.",
        "**Fig. S4.** SI oracle / post-hoc intercept-shift diagnostic for Al80Cu20_tracer (counterfactual; Gemini S4; not a Protocol W metric and not LOGO success). Seed-mean MFNN \\(k{=}0\\) predictions versus a zero-retrain post-hoc logarithmic intercept shift calibrated at a single low-\\(T\\) point (\\(983 K\\)): MAPE on the remaining \\(n{=}9\\) temperatures falls from \\(∼\\)175% (\\(Factor2=0\\)) to \\(∼\\)9.8% (\\(Factor2=1\\)), with \\(\\delta≈ -0.48≈ -\\log_{10} 3\\). Returning the same point to unweighted training does not recover Factor2. Related \\(k{=}2\\) anchor upweighting (\\(w{=}5\\)–\\(10\\)) is SI Fig.~S6 (optional extra; not Gemini core S1–S5); full tables are SI-only. File: `FigS4_al80_posthoc_shift`.",
    ),
]

# Regex fallbacks if unicode dashes / spaces differ
REGEX = [
    (r"\*\*Fig\.\s*8\.\*\*", "**Fig. S5.**"),
    (r"\*\*Fig\.\s*9\.\*\*", "**Fig. S2 (caution).**"),
    (r"\*\*Fig\.\s*10\.\*\*", "**Fig. S4.**"),
    (r"Fig\.~\\ref\{fig:ablation\}", "Fig.~S5"),
    (r"Fig\.~\\ref\{fig:WvsG\}", "Fig.~S2"),
    (r"Appendix Fig\.~\\ref\{fig:si_al80_shift\}", "Fig.~S4"),
    (r"Fig\.~\\ref\{fig:si_al80_shift\}", "Fig.~S4"),
    # bare main-text Fig. 8/9/10 (not Fig. S8 etc., not Fig.18)
    (r"(?<![S\d])Fig\.\s*8\b(?!\d)", "Fig. S5"),
    (r"(?<![S\d])Fig\.\s*9\b(?!\d)", "Fig. S2"),
    (r"(?<![S\d])Fig\.\s*10\b(?!\d)", "Fig. S4"),
    (r"(?<![S\d])Figure\s+8\b(?!\d)", "Fig. S5"),
    (r"(?<![S\d])Figure\s+9\b(?!\d)", "Fig. S2"),
    (r"(?<![S\d])Figure\s+10\b(?!\d)", "Fig. S4"),
]


def patch_text(text: str) -> tuple[str, list[str]]:
    notes = []
    for a, b in PLAIN:
        if a in text:
            n = text.count(a)
            text = text.replace(a, b)
            notes.append(f"plain x{n}: {a[:60]}… → {b[:50]}…")
    for pat, rep in REGEX:
        text2, n = re.subn(pat, rep, text)
        if n:
            notes.append(f"re x{n}: /{pat}/ → {rep}")
            text = text2
    return text, notes


def patch_file(path: Path) -> list[str]:
    if not path.is_file():
        return [f"missing {path}"]
    orig = path.read_text(encoding="utf-8")
    text, notes = patch_text(orig)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        notes.append(f"SAVED {path}")
    else:
        notes.append(f"unchanged {path}")
    return notes


DOCX_PLAIN = [
    ("Fig. 8.", "Fig. S5."),
    ("Fig. 9.", "Fig. S2 (caution)."),
    ("Fig. 10.", "Fig. S4."),
    ("Figure 8", "Fig. S5"),
    ("Figure 9", "Fig. S2"),
    ("Figure 10", "Fig. S4"),
    ("Fig.~8", "Fig.~S5"),
    ("Fig.~9", "Fig.~S2"),
    ("Fig.~10", "Fig.~S4"),
    ("Appendix Fig.", "Fig. S4 / SI"),  # only if paired with oracle — handled by regex below
]

DOCX_RE = [
    (r"(?<![S\d])Fig\.\s*8\b(?!\d)", "Fig. S5"),
    (r"(?<![S\d])Fig\.\s*9\b(?!\d)", "Fig. S2"),
    (r"(?<![S\d])Fig\.\s*10\b(?!\d)", "Fig. S4"),
    (r"(?<![S\d])Figure\s+8\b(?!\d)", "Fig. S5"),
    (r"(?<![S\d])Figure\s+9\b(?!\d)", "Fig. S2"),
    (r"(?<![S\d])Figure\s+10\b(?!\d)", "Fig. S4"),
]


def patch_docx(path: Path) -> list[str]:
    bak = path.with_name(path.stem + "_backup_pre_fig810_scrub.docx")
    notes = []
    if not bak.exists():
        shutil.copy2(path, bak)
        notes.append(f"backup {bak.name}")
    else:
        notes.append(f"backup exists {bak.name}")

    doc = Document(str(path))
    changed = 0
    for i, p in enumerate(doc.paragraphs):
        t = p.text
        if not t:
            continue
        new = t
        for a, b in DOCX_PLAIN:
            if a in new and not (a.startswith("Fig. 8") and "Fig. S" in new):
                # avoid double-replacing already-SI text; plain replace OK for bare Fig. 8.
                new = new.replace(a, b)
        for pat, rep in DOCX_RE:
            new2, n = re.subn(pat, rep, new)
            if n:
                new = new2
        # undo false positives on S8/S9/S10 if any — our lookbehind should prevent
        if new != t:
            if p.runs:
                p.runs[0].text = new
                for r in p.runs[1:]:
                    r.text = ""
            else:
                p.add_run(new)
            changed += 1
            notes.append(f"P{i}: {t[:50]} → {new[:50]}")
    if changed:
        doc.save(str(path))
        notes.append(f"SAVED docx ({changed} paras) {path.name}")
    else:
        notes.append(f"docx no text changes {path.name}")
    return notes


SCAN_PAT = re.compile(
    r"(?<![S\d./_])(?:Fig\.?\s*~?|Figure\s+)(?:8|9|10)\b(?!\d)|"
    r"\*\*Fig\.\s*(?:8|9|10)\.\*\*|"
    r"Fig8_protocol|Fig9_residuals|Fig10_",
    re.I,
)


def scan(path: Path) -> list[str]:
    if not path.is_file():
        return []
    if path.suffix.lower() == ".docx":
        doc = Document(str(path))
        out = []
        for i, p in enumerate(doc.paragraphs):
            t = p.text
            if SCAN_PAT.search(t) and not re.search(r"Fig\.\s*S(?:8|9|10)\b", t):
                # exclude legacy filename mentions in captions map style
                if re.search(r"`Fig[89]_", t) or "legacy" in t.lower():
                    continue
                if re.search(r"(?<![S\d])(?:Fig\.?\s*|Figure\s+)(?:8|9|10)\b", t):
                    out.append(f"P{i}: {t.strip()[:120]}")
        return out
    text = path.read_text(encoding="utf-8")
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if not SCAN_PAT.search(line):
            continue
        # allow legacy filename mapping rows
        if re.search(r"`Fig[89]_|legacy.*Fig[89]|Fig9_residuals_log10 \(related\)|Fig8_protocol_W_vs_G", line):
            if not re.search(r"\*\*Fig\.\s*(?:8|9|10)\.\*\*|(?<![S`\d])Fig\.\s*(?:8|9|10)\.\s", line):
                continue
        if re.search(r"(?<![S`\d_/])(?:Fig\.?\s*~?|Figure\s+)(?:8|9|10)\b(?!\d)|\\*\*Fig\.\s*(?:8|9|10)\.", line):
            out.append(f"L{i}: {line.strip()[:140]}")
    return out


def main():
    report = []
    report.append("=== PRE-SCAN ===")
    for p in MD_PATHS + TEX_PATHS + CAPTION_PATHS + DOCX_PATHS:
        hits = scan(p)
        report.append(f"{p.relative_to(ROOT)}: {len(hits)} hits")
        for h in hits:
            report.append(f"  {h}")

    report.append("=== PATCH MD/TEX ===")
    for p in MD_PATHS + TEX_PATHS:
        for n in patch_file(p):
            report.append(n)

    # captions: only scrub if they claim Main Fig. 8/9/10 as active numbers
    for p in CAPTION_PATHS:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        orig = text
        # no Main Fig. 8-10 rows expected; leave legacy stem notes
        text2, notes = patch_text(text)
        # revert accidental changes to legacy stem tokens in backticks
        # patch_text shouldn't touch Fig8_ stems due to lookbehind on Fig. 8
        if text2 != orig:
            p.write_text(text2, encoding="utf-8")
            report.extend(notes)
            report.append(f"SAVED captions {p}")
        else:
            report.append(f"captions unchanged (legacy map only) {p.name}")

    report.append("=== PATCH DOCX ===")
    for p in DOCX_PATHS:
        for n in patch_docx(p):
            report.append(n)

    report.append("=== POST-SCAN (main-text Fig.8-10) ===")
    any_left = False
    for p in MD_PATHS + TEX_PATHS + CAPTION_PATHS + DOCX_PATHS:
        hits = scan(p)
        # filter caption legacy
        real = []
        for h in hits:
            if "legacy" in h.lower() or "`Fig8_" in h or "`Fig9_" in h or "Fig9_residuals" in h:
                continue
            if re.search(r"(?<![S`\d])(?:Fig\.?\s*|Figure\s+)(?:8|9|10)\b|\*\*Fig\.\s*(?:8|9|10)\.", h):
                real.append(h)
        report.append(f"{p.relative_to(ROOT)}: {len(real)} residual")
        for h in real:
            any_left = True
            report.append(f"  {h}")
    report.append("RESIDUAL_EMPTY" if not any_left else "RESIDUAL_REMAIN")

    logs = ROOT / "outputs" / "_logs"
    logs.mkdir(exist_ok=True)
    out = logs / "fig810_scrub_report.txt"
    out.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
