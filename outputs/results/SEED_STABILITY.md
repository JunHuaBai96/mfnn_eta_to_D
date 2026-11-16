# Multi-seed stability (MFNN / baselines)

Seeds: `0, 1, 2, 42, 123`

Data: post HF densify (`melt_diffusion_data.csv`, usable 131 = 55 HF + 76 LF).
Settings: default `train.py` Adam→L-BFGS; LF on **all** LF; HF split by `comp_group`; target `log10 D`.

## MFNN ALL mean ± std (population std)

- **MAPE%**: 67.68 ± 49.54
- **Factor2**: 0.800 ± 0.245
- **R²**: -0.664 ± 0.581
- **n_test**: 14.8 ± 4.5

## Interpretation (important)

Variance is **dominated by which `comp_group`s land in test**, not by optimizer noise:

| seed | HF test groups | MFNN ALL MAPE% | Factor2 |
|------|----------------|----------------|--------|
| 0 | Al80Cu20+Al81.3Cu18.7 | 139.4 | 0.50 |
| 1 | Al85Cu15+PureAl | 20.1 | 1.00 |
| 2 | Al80Cu20+Al81.3Cu18.7 | 115.4 | 0.50 |
| 42 | Al95Cu5+PureAl_impurityNi | 31.0 | 1.00 |
| 123 | Al85Cu15+PureAl_impurityNi | 32.4 | 1.00 |

- When **Al80Cu20 + Al81.3Cu18.7** are held out together (seeds 0,2), models must extrapolate alloy inter/tracer D → MAPE >100%, Factor2=0.5.
- When test is **PureAl / impurity-Ni** dominated (seeds 1,42,123), MFNN MAPE ≈20–32%, Factor2=1.0.
- **Densifying T inside a group does not grow the number of test groups**; Al–Cu / Al–Mg–Si per-system `n` can still be 1–2 for some seeds.
- Al–Ce–Ni label remains **PureAl_impurityNi** (not bulk Al–Ce–Ni alloy).

## ALL by seed × model

```
 seed   model  n   MAPE_pct  Factor2         R2
    0 HF_only 20 180.314295      0.5  -2.204138
    0 LF_only 20 101.910699      0.5  -0.738726
    0    MFNN 20 139.385168      0.5  -1.483615
    1 HF_only 14  16.866901      1.0  -0.403933
    1 LF_only 14  43.713390      1.0  -3.422865
    1    MFNN 14  20.144097      1.0  -0.799713
    2 HF_only 20 132.089335      0.5  -1.366464
    2 LF_only 20  86.379571      0.5  -0.379634
    2    MFNN 20 115.445859      0.5  -1.024812
   42 HF_only 10  20.201997      1.0   0.232843
   42 LF_only 10 229.969861      0.1 -16.185340
   42    MFNN 10  31.033740      1.0  -0.027203
  123 HF_only 10  15.978336      1.0   0.583300
  123 LF_only 10 243.866910      0.1 -17.524114
  123    MFNN 10  32.383847      1.0   0.015390
```

## Baseline ALL MAPE% mean±std

- **LF_only**: MAPE 141.17±80.59%; Factor2 0.440±0.332
- **HF_only**: MAPE 73.09±69.57%; Factor2 0.800±0.245
- **MFNN**: MAPE 67.68±49.54%; Factor2 0.800±0.245

## Files

- `outputs/seed_stability_summary.csv`
- `outputs/seed_<SEED>/`
