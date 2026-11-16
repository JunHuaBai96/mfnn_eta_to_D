# -*- coding: utf-8 -*-
"""Export Notion-friendly markdown from PAPER_JCP_draft_EN.md."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(r"C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D")
SRC = ROOT / "outputs" / "PAPER_JCP_draft_EN.md"
CAPS = ROOT / "outputs" / "figures" / "FIGURE_CAPTIONS.md"
REFS_NUM = ROOT / "outputs" / "references" / "REFERENCES_numbered.md"
OUT_DIR = ROOT / "outputs" / "notion"
OUT_MD = OUT_DIR / "PAPER_JCP_draft_EN_notion.md"
OUT_README = OUT_DIR / "README_NOTION_IMPORT.md"
OUT_JCP = ROOT / "outputs" / "jcp_submission" / "notion" / "PAPER_JCP_draft_EN_notion.md"

# Gemini figure stems (relative from outputs/notion/ -> ../figures/)
FIG_LINKS = {
    1: ("Fig1_mfnn_residual_schema", "Main Fig. 1 — residual MFNN schema"),
    2: ("Fig2_phase_space_coverage", "Main Fig. 2 — phase-space coverage"),
    3: ("Fig3_protocol_W_parity_metrics", "Main Fig. 3 — Protocol W parity/metrics"),
    4: ("Fig4_protocol_W_residual_topology", "Main Fig. 4 — Protocol W residual topology"),
    5: ("Fig5_arrhenius_representative", "Main Fig. 5 — Arrhenius representative"),
    6: ("Fig6_Al80_tracer_inter", "Main Fig. 6 — Al80 tracer vs inter"),
    7: ("Fig7_LOGO_distance_caution", "Main Fig. 7 — LOGO caution"),
}
SI_LINKS = {
    1: ("FigS1_alpha_mixing_weights", "Fig. S1 — α mixing weights"),
    2: ("FigS2_protocol_G_variance", "Fig. S2 — Protocol G variance (caution)"),
    3: ("FigS3_al80_anchor_k", "Fig. S3 — Al80 anchor-k"),
    4: ("FigS4_al80_posthoc_shift", "Fig. S4 — oracle / posthoc intercept"),
    5: ("FigS5_difftype_split_ablation", "Fig. S5 — difftype split ablation"),
}


def citation_order(text: str) -> list[str]:
    order, seen = [], set()
    for m in re.finditer(r"\\cite\{([^}]+)\}", text):
        for k in m.group(1).split(","):
            k = k.strip()
            if k and k not in seen:
                seen.add(k)
                order.append(k)
    return order


def load_ref_lines(order: list[str]) -> list[str]:
    """Prefer REFERENCES_numbered.md; else rebuild from its content / order."""
    if REFS_NUM.is_file():
        lines = []
        for ln in REFS_NUM.read_text(encoding="utf-8").splitlines():
            if re.match(r"^\[\d+\]\s", ln.strip()):
                lines.append(ln.strip())
        if lines:
            return lines
    return [f"[{i}] `{k}`" for i, k in enumerate(order, 1)]


def cite_replacer(key_to_n: dict[str, int]):
    def _sub(m: re.Match) -> str:
        keys = [k.strip() for k in m.group(1).split(",") if k.strip()]
        nums = []
        for k in keys:
            if k not in key_to_n:
                # leave visible marker
                nums.append(f"?{k}")
            else:
                nums.append(str(key_to_n[k]))
        # compress ranges lightly not required; join
        if len(nums) == 1:
            return f"[{nums[0]}]"
        return "[" + ",".join(nums) + "]"

    return _sub


def convert_math(text: str, stats: dict) -> str:
    # Protect existing $$ blocks
    dollars = []

    def stash_dd(m):
        dollars.append(m.group(0))
        return f"@@DD{len(dollars)-1}@@"

    text = re.sub(r"\$\$.*?\$\$", stash_dd, text, flags=re.S)

    # \[ ... \] display
    def brack_disp(m):
        stats["bracket_display"] += 1
        inner = m.group(1).strip()
        return f"\n$$\n{inner}\n$$\n"

    text = re.sub(r"\\\[(.*?)\\\]", brack_disp, text, flags=re.S)

    # equation / align environments
    def env_disp(m):
        stats["equation_env"] += 1
        inner = m.group(2).strip()
        # drop \label{...}
        inner = re.sub(r"\\label\{[^}]*\}", "", inner).strip()
        return f"\n$$\n{inner}\n$$\n"

    text = re.sub(
        r"\\begin\{(equation\*?|align\*?|eqnarray\*?)\}(.*?)\\end\{\1\}",
        env_disp,
        text,
        flags=re.S,
    )

    # \( ... \) inline
    def paren_inline(m):
        stats["paren_inline"] += 1
        return f"${m.group(1)}$"

    text = re.sub(r"\\\((.*?)\\\)", paren_inline, text, flags=re.S)

    # Restore $$
    for i, block in enumerate(dollars):
        text = text.replace(f"@@DD{i}@@", block)

    return text


def tidy_latex_commands(text: str, stats: dict) -> str:
    # Common text macros safe for Notion unicode
    repls = [
        (r"\\emph\{([^}]*)\}", r"*\1*"),
        (r"\\textit\{([^}]*)\}", r"*\1*"),
        (r"\\textbf\{([^}]*)\}", r"**\1**"),
        (r"\\mathrm\{([^}]*)\}", r"\\mathrm{\1}"),  # keep inside math
        (r"~", " "),
        (r"\\%", "%"),
        (r"\\&", "&"),
        (r"\\,", " "),
        (r"\\;", " "),
        (r"\\,", " "),
        (r"\\noindent\s*", ""),
        (r"\\appendix\s*", "\n\n"),
        (r"\\label\{[^}]*\}", ""),
        (r"\\ref\{([^}]*)\}", r"[ref:\1]"),
    ]
    # Only apply text-mode replacements outside $...$
    parts = re.split(r"(\$\$[\s\S]*?\$\$|\$[^$]+\$)", text)
    out = []
    for part in parts:
        if part.startswith("$"):
            # inside math: light clean only
            p = part
            p = p.replace("~", " ")
            out.append(p)
        else:
            p = part
            for a, b in repls:
                p2, n = re.subn(a, b, p)
                if n:
                    stats["text_macro"] += n
                    p = p2
            # \section-like already md
            out.append(p)
    return "".join(out)


def inject_figure_links(text: str, stats: dict) -> str:
    """After **Fig. N.** captions, append image path comment/link."""

    def main_fig(m):
        n = int(m.group(1))
        cap = m.group(0)
        if n in FIG_LINKS:
            stem, desc = FIG_LINKS[n]
            stats["fig_links"] += 1
            return (
                f"{cap}\n\n"
                f"<!-- Notion: upload or link --> "
                f"[`../figures/{stem}.png`](../figures/{stem}.png) — {desc}\n"
            )
        return cap

    def si_fig(m):
        n = int(m.group(1))
        cap = m.group(0)
        if n in SI_LINKS:
            stem, desc = SI_LINKS[n]
            stats["fig_links"] += 1
            return (
                f"{cap}\n\n"
                f"<!-- Notion: upload or link --> "
                f"[`../figures/{stem}.png`](../figures/{stem}.png) — {desc}\n"
            )
        return cap

    # Match caption start lines **Fig. 3.** or **Fig. S2 ...
    text = re.sub(
        r"^\*\*Fig\.\s*(\d+)\.[^\n]*$",
        main_fig,
        text,
        flags=re.M,
    )
    text = re.sub(
        r"^\*\*Fig\.\s*S(\d+)[^\n]*$",
        si_fig,
        text,
        flags=re.M,
    )
    return text


def strip_existing_references(text: str) -> str:
    if "## References" in text:
        text = re.split(r"\n## References\n", text, maxsplit=1)[0].rstrip() + "\n"
    return text


def build_notion_header() -> str:
    return (
        "> **Notion export** of the JCP residual-MFNN η→D manuscript. "
        "Inline math: `$...$`; display math: `$$...$$` on their own lines. "
        "Figures: follow links under each caption (paths relative to `outputs/notion/`).\n\n"
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_JCP.parent).mkdir(parents=True, exist_ok=True)

    raw = SRC.read_text(encoding="utf-8")
    stats = {
        "paren_inline": 0,
        "bracket_display": 0,
        "equation_env": 0,
        "cite": 0,
        "text_macro": 0,
        "fig_links": 0,
        "existing_dollar_inline": len(re.findall(r"(?<!\$)\$(?!\$)", raw)) // 2,
    }

    order = citation_order(raw)
    key_to_n = {k: i for i, k in enumerate(order, 1)}
    ref_lines = load_ref_lines(order)
    # Ensure ref_lines length matches order; if REFERENCES_numbered has 23, OK
    if len(ref_lines) != len(order):
        # rebuild simple from numbered file keys by order position
        pass

    text = raw
    # cites first (before math so keys stay)
    text, n_cite = re.subn(r"\\cite\{([^}]+)\}", cite_replacer(key_to_n), text)
    stats["cite"] = n_cite

    text = convert_math(text, stats)
    text = tidy_latex_commands(text, stats)
    text = inject_figure_links(text, stats)
    text = strip_existing_references(text)

    # Append figure index + references
    fig_index = ["\n## Figure files (Gemini stems)\n"]
    for n, (stem, desc) in FIG_LINKS.items():
        fig_index.append(f"- Fig. {n}: [`../figures/{stem}.png`](../figures/{stem}.png) — {desc}")
    for n, (stem, desc) in SI_LINKS.items():
        fig_index.append(f"- Fig. S{n}: [`../figures/{stem}.png`](../figures/{stem}.png) — {desc}")
    fig_index.append("")

    refs_block = ["\n## References\n"]
    for ln in ref_lines:
        # ensure DOI is a markdown link if present as raw URL
        ln2 = re.sub(
            r"(https://doi\.org/[^\s]+)",
            r"[\1](\1)",
            ln,
        )
        refs_block.append(ln2)
        refs_block.append("")

    out = build_notion_header() + text.rstrip() + "\n\n" + "\n".join(fig_index) + "\n" + "\n".join(refs_block)

    # Final hygiene: remove leftover \( \[ as math delimiters
    # (allow in code/comments? shouldn't remain)
    leftover_paren = len(re.findall(r"\\\(", out))
    leftover_brack = len(re.findall(r"\\\[", out))
    stats["leftover_paren"] = leftover_paren
    stats["leftover_brack"] = leftover_brack

    # Self-check frozen numbers / non-PINN
    checks = {
        "26.18": "26.18" in out,
        "1.33": "1.33" in out,
        "non_PINN": ("not a PDE-residual" in out.lower() or "deliberately not a PDE-residual" in out),
        "no_paren_delim": leftover_paren == 0,
        "no_brack_delim": leftover_brack == 0,
    }
    stats["checks"] = checks

    OUT_MD.write_text(out, encoding="utf-8")
    shutil.copy2(OUT_MD, OUT_JCP)

    readme = f"""# Notion import guide

## File
- Main: `outputs/notion/PAPER_JCP_draft_EN_notion.md`
- Copy: `outputs/jcp_submission/notion/PAPER_JCP_draft_EN_notion.md`

## Paste into Notion
1. Open a new Notion page → import or paste Markdown (Notion “Import → Markdown” or paste into an empty page).
2. After paste, scan headings (Abstract → References). Tables usually survive; fix any broken pipes manually.
3. **Equations:** Notion renders `$inline$` and `$$` display blocks. Click a formula block to edit. If a formula shows as raw TeX, select it → “Create equation” / re-type the `$` wrappers.
4. **Figures:** Under each caption there is a relative link to `outputs/figures/Fig*.png`. In Notion, upload the PNG (or drag from Explorer) below the caption and delete the path comment if desired. Absolute project path: `C:\\\\Users\\\\17868\\\\OneDrive\\\\Desktop\\\\mfnn_eta_to_D\\\\outputs\\\\figures\\\\`.
5. **References:** Numbered `[n]` in the text match the References list; DOI URLs are clickable markdown links.

## Conversion notes (this export)
- `\\(...\\)` → `$...$`: {stats['paren_inline']}
- `\\[...\\]` → `$$...$$`: {stats['bracket_display']}
- `equation/align` envs → `$$`: {stats['equation_env']}
- `\\cite{{key}}` → `[n]`: {stats['cite']}
- Figure path annotations: {stats['fig_links']}

## Known Notion limits
Notion’s TeX subset is smaller than full LaTeX (limited macros, no BibTeX); complex `\mathrm`/`\cite`/`\\ref` must stay as `$...$` unicode-friendly math or plain text—re-check any formula that fails to render after paste.
"""
    OUT_README.write_text(readme, encoding="utf-8")
    shutil.copy2(OUT_README, OUT_JCP.parent / "README_NOTION_IMPORT.md")

    # stats sidecar
    (OUT_DIR / "_notion_export_stats.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in stats.items()) + "\n",
        encoding="utf-8",
    )
    print("WROTE", OUT_MD)
    print("WROTE", OUT_JCP)
    print("STATS", stats)


if __name__ == "__main__":
    main()
