# Al–Cu 固定 LOGO（leave-one-comp_group-out）

这是协议 G 的**确定性**版本：每个 Al–Cu HF `comp_group` 整组留出作 test，其余 HF + 全部可用 LF 训练。**折的划分不随机**；`--seed 42` 仅控制优化器初始化与剩余组上的 val 抽样。

> **范围：** Al–Cu **体系内成分外推**（不同 `comp_group` / 成分）。不是跨合金体系（Al–Mg–Si / Al–Ce–Ni）外推，也**不是**随机 seed 的 G≈20% 论文结论。

缺 `eta_Pas` 行由 `load_csv` drop；**未**用 Kozlov 填 HF η。

## 折列表

| holdout_group | n_test |
|---------------|--------|
| Al70Cu30 | 2 |
| Al75Cu25 | 3 |
| Al80Cu20 | 12 |
| Al81.3Cu18.7 | 9 |
| Al81Cu19 | 1 |
| Al82.9Cu17.1 | 3 |
| Al85Cu15 | 1 |
| Al87Cu13 | 1 |
| Al90Cu10 | 5 |
| Al95Cu5 | 2 |
| PureAl_impurityCu | 9 |

共 **11** 折。

## ALL 指标 mean ± std（跨折，ddof=0）

### LF_only

- **MAPE%**: 61.64 ± 46.81
- **Factor2**: 0.7545 ± 0.3039
- **R²**: -4.604 ± 6.125
- **n**: 4.364 ± 3.699

### HF_only

- **MAPE%**: 1126 ± 3414
- **Factor2**: 0.7626 ± 0.3731
- **R²**: -42.24 ± 104.1
- **n**: 4.364 ± 3.699

### MFNN

- **MAPE%**: 45.49 ± 48.7
- **Factor2**: 0.8788 ± 0.2668
- **R²**: -2.718 ± 4.091
- **n**: 4.364 ± 3.699

## MFNN 最好 / 最差折

- **最好**: `Al85Cu15` — MAPE=3.11%, Factor2=1.000, n=1
- **最差**: `Al80Cu20` — MAPE=158.13%, Factor2=0.167, n=12

## 逐折明细（ALL）

```
    holdout_group   model     MAPE_pct  Factor2          R2  n
         Al70Cu30 HF_only 11920.712084 0.000000 -317.467697  2
         Al70Cu30 LF_only   107.315909 0.500000   -7.672899  2
         Al70Cu30    MFNN   134.126271 0.500000  -10.538108  2
         Al75Cu25 HF_only    33.778835 1.000000    0.169508  3
         Al75Cu25 LF_only    29.940215 1.000000    0.440855  3
         Al75Cu25    MFNN    14.510970 1.000000    0.859642  3
         Al80Cu20 HF_only   206.502377 0.166667   -7.684165 12
         Al80Cu20 LF_only   133.035712 0.166667   -4.089835 12
         Al80Cu20    MFNN   158.130077 0.166667   -5.372411 12
     Al81.3Cu18.7 HF_only    53.136595 0.333333  -13.487758  9
     Al81.3Cu18.7 LF_only    16.936021 1.000000   -0.136474  9
     Al81.3Cu18.7    MFNN    43.786043 1.000000   -7.078572  9
         Al81Cu19 HF_only    22.312173 1.000000         NaN  1
         Al81Cu19 LF_only    13.031016 1.000000         NaN  1
         Al81Cu19    MFNN    23.784111 1.000000         NaN  1
     Al82.9Cu17.1 HF_only    20.470618 1.000000    0.564758  3
     Al82.9Cu17.1 LF_only    16.899422 1.000000    0.744509  3
     Al82.9Cu17.1    MFNN    18.010606 1.000000    0.719824  3
         Al85Cu15 HF_only    10.356822 1.000000         NaN  1
         Al85Cu15 LF_only    47.741001 1.000000         NaN  1
         Al85Cu15    MFNN     3.107600 1.000000         NaN  1
         Al87Cu13 HF_only    39.155361 1.000000         NaN  1
         Al87Cu13 LF_only     4.612823 1.000000         NaN  1
         Al87Cu13    MFNN    31.003837 1.000000         NaN  1
         Al90Cu10 HF_only    17.265143 1.000000    0.791977  5
         Al90Cu10 LF_only    76.884561 0.800000   -0.709864  5
         Al90Cu10    MFNN    21.211042 1.000000    0.698206  5
          Al95Cu5 HF_only    16.844191 1.000000    0.091507  2
          Al95Cu5 LF_only   114.685262 0.500000  -18.622511  2
          Al95Cu5    MFNN    22.813470 1.000000   -1.106230  2
PureAl_impurityCu HF_only    41.693248 0.888889   -0.895282  9
PureAl_impurityCu LF_only   116.915942 0.333333   -6.782775  9
PureAl_impurityCu    MFNN    29.953819 1.000000    0.075526  9
```

## 非 Al–Cu 体系（可选 LOGO）

- **Al-Ce-Ni**: 仅 1 个 HF 组 (`PureAl_impurityNi`, n=9) — **不足以 LOGO**（leave-one-group-out 需要 ≥2 组）。
- **Al-Mg-Si**: 仅 1 个 HF 组 (`PureAl`, n=13) — **不足以 LOGO**（leave-one-group-out 需要 ≥2 组）。

## 文件

- `outputs/LOGO_AlCu_summary.csv`
- `outputs/LOGO_AlCu_REPORT.md`
- per-fold: `outputs/logo_alcu_folds/<group>/`
