# Evaluation protocol summary (W vs G)

Paper should report **both** protocols. Do not claim LOGO-CV success from W alone.

## Protocol W — within-group T-split (interpolation)
- For each `comp_group` with ≥4 HF points spanning T, hold out ~25% of HF by T (prefer lowest/highest T).
- Train on remaining HF + **all LF**.
- Metrics: `outputs/within_T/metrics_by_system.csv` (also copied as `metrics_within_T.csv`).
- Measures temperature interpolation / densification skill, **not** composition extrapolation.

## Protocol G — between-group extrapolation (LOGO-style)
- Leave-composition-group-out split on HF (`split_by_comp_group`).
- Metrics: `outputs/between_group/metrics_by_system.csv` (also `metrics_between_group.csv`).
- Measures composition extrapolation; sensitive to which groups are held out.

## This run (seed noted in CSVs)

- **W within_T** MFNN ALL: MAPE=33.3%, Factor2=0.79, n=14
- **G between_group**: no metrics

CLI: `python train.py --eval both|within_T|between_group [--seed 42]`
