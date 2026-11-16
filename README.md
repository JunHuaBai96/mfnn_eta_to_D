# mfnn_eta_to_D — Residual multi-fidelity NN (η → D)

Physics-guided residual multi-fidelity neural network that maps melt viscosity η to liquid diffusivity D, using a Sutherland-type low-fidelity prior and scarce high-fidelity experimental D.

黏度 η → 扩散系数 D 的残差多保真神经网络（Residual MFNN）：低保真用改性 Sutherland 先验，高保真用实验 D 校正。

## Quick layout / 目录

| Purpose | Path |
|---------|------|
| Train / evaluate | `train.py`, `model.py`, `data.py`, `physics.py`, `eval.py`, `plot.py` |
| Datasets | `data/` |
| Experiment & figure scripts | `scripts/` (`run_*.py`, `publish_figures/`) |
| JCP LaTeX submission | `outputs/jcp_submission/` (`main.tex`, `refs.bib`, cover letter, `figures/`) |
| Publication figures (PDF/PNG/SVG) | `outputs/figures/` |
| Illustrator-editable vector pack | `outputs/figures_vector/` (SVG preferred) |
| Metrics & reports | `outputs/results/` |
| Word / Markdown drafts | `outputs/PAPER_JCP_draft_EN*.docx`, `outputs/PAPER_JCP_draft_EN.md` |

## Install & run / 安装与运行

```bash
cd mfnn_eta_to_D
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
python train.py
```

Primary training table: `data/melt_diffusion_data.csv` (paired η–D rows also under `data/melt_diffusion_data_eta_paired*.csv`).

Reproducibility scripts (examples):

```bash
python scripts/run_seed_stability.py
python scripts/run_logo_alcu_by_difftype.py
python scripts/extract_mfnn_alphas.py
python scripts/publish_figures/generate_all.py
```

## Journal submission / 投稿包

- Manuscript: `outputs/jcp_submission/main.tex` + `refs.bib`
- Figures for `\includegraphics`: `outputs/jcp_submission/figures/`
- Compile notes: `outputs/jcp_submission/README.md`
- Cover letter: `outputs/jcp_submission/COVER_LETTER.md` (fill affiliation / email before send)

Headline Protocol W numbers (frozen; five seeds `{0,1,2,42,123}`, \(n_{\mathrm{test}}=15\)):

- Residual MFNN: MAPE **26.18 ± 1.33%**, Factor2 **0.96 ± 0.033**, R² **0.392 ± 0.094**

## Data & code availability

Training CSVs, fold definitions, training/evaluation scripts, aggregated metrics, and publication figures are openly available at https://github.com/JunHuaBai96/mfnn_eta_to_D. Experimental D and η values retain their literature provenance columns in the data tables; cite the original sources listed in `refs.bib`.


## Note for attachers / 打包说明

Do **not** include `_archive_private/` when zipping for editors or reviewers. That folder holds local working backups only.

## Authoring note

`outputs/jcp_submission/main.tex` is the source of truth for the manuscript. Prefer it over Word drafts when packaging for editors; see `outputs/jcp_submission/SUBMIT_CHECKLIST.md`.

## Word manuscript track (important)

Use **only**:
- `outputs/jcp_submission/PAPER_JCP_draft_EN_academic.docx` (canonical Word draft; tables are native Word tables)
- A synced copy also lives at `outputs/PAPER_JCP_draft_EN_academic.docx` (same content)

Do **not** open `PAPER_JCP_draft_EN.docx` — that file was a broken LaTeX→Word conversion with pipe/markdown fake tables and has been moved to `_archive_private/backups/`. Prefer LaTeX `main.tex` for journal submission.
