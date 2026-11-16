# JCP submission package (elsarticle)

Manuscript skeleton for *Journal of Computational Physics* (Elsevier `elsarticle`).

## Source of truth

- **LaTeX:** `main.tex` + `refs.bib` + `figures/*.pdf` are the submission sources.
- Word/Markdown drafts (`PAPER_JCP_draft_EN*.docx`, `PAPER_JCP_draft_EN.md`) are authoring copies only. Do **not** submit the broken `PAPER_JCP_draft_EN.docx` to the journal; regenerate from LaTeX if a Word track is needed.
- Cover letter: `COVER_LETTER.md` / `.tex` / `.txt` (affiliation and `ycui@njtech.edu.cn` filled).

## Contents

| File | Role |
|------|------|
| `main.tex` | Manuscript body |
| `refs.bib` | Bibliography |
| `figures/` | Fig. 1–9 and SI Fig. S1–S3 (PDF) |
| `COVER_LETTER.*` | Cover letter drafts |
| `SUBMIT_CHECKLIST.md` | Pre-submission checklist |
| `PAPER_JCP_draft_EN*.docx` / `.md` | Optional authoring copies (not for editors) |

## Compile

```bash
cd outputs/jcp_submission
latexmk -pdf main.tex
```

Or: `pdflatex` → `bibtex` → `pdflatex` ×2. Requires TeX Live / MiKTeX with `elsarticle` and `elsarticle-num`.

## Editor zip (exclude)

When packaging for editors/reviewers, **exclude**:

- `_archive_private/` (local working backups)
- `.venv/`
- duplicate legacy figure stems under `figures/` if both `fig2_...` and `Fig2_...` exist (keep the `FigN_*.pdf` set referenced by `main.tex`)
- Word authoring copies unless the journal explicitly requests DOCX

## Frozen Protocol W metrics (do not edit)

- MFNN: MAPE \(26.18\pm 1.33\%\), Factor2 \(0.96\pm 0.033\), \(R^2=0.392\pm 0.094\)
- HF-only: MAPE \(30.98\pm 4.43\%\), Factor2 \(0.973\pm 0.033\), \(R^2=0.263\pm 0.076\)
- LF-only: MAPE \(109.6\pm 13.13\%\), Factor2 \(0.56\pm 0.10\), \(R^2=-2.588\pm 0.399\)
- \(n_{\mathrm{test}}=15\), seeds \(\{0,1,2,42,123\}\)

Document class: `\documentclass[review,12pt]{elsarticle}`.

## Word manuscript track (important)

Use **only**:
- `outputs/jcp_submission/PAPER_JCP_draft_EN_academic.docx` (canonical Word draft; tables are native Word tables)
- A synced copy also lives at `outputs/PAPER_JCP_draft_EN_academic.docx` (same content)

Do **not** open `PAPER_JCP_draft_EN.docx` — that file was a broken LaTeX→Word conversion with pipe/markdown fake tables and has been moved to `_archive_private/backups/`. Prefer LaTeX `main.tex` for journal submission.
