# 多 seed 稳定性：协议 W（within_T）vs G（between_group）

Seeds: `[0, 1, 2, 42, 123]`

命令等价于对各 seed 执行 `python train.py --eval both --seed <SEED>` （本脚本写入 `outputs/seed_wg_<SEED>/` 以免覆盖）。缺 η 行仍 drop；**未**用 Kozlov 填 HF η。

> **声明：** 不得把单一 seed 的 G≈20% MAPE 当作最终论文结论；G 强烈依赖留出的 `comp_group`，须报告 mean±std 与 hold-out 组成。

## MFNN ALL：W / G 的 mean ± std（总体标准差 ddof=0）

### W (within_T)

- **MAPE%**: 26.18 ± 1.334
- **Factor2**: 0.96 ± 0.03266
- **R²**: 0.3919 ± 0.09403
- **n** (test): 15 ± 0

### G (between_group)

- **MAPE%**: 27.36 ± 12.88
- **Factor2**: 0.7909 ± 0.2565
- **R²**: -0.7659 ± 2.1
- **n** (test): 9 ± 1.265

## 各 seed × 协议 × 模型（ALL 行）

```
 seed protocol   model   MAPE_pct  Factor2        R2  n
    0        G HF_only  28.534741 1.000000  0.266748  8
    0        G LF_only  81.107760 0.625000 -1.134282  8
    0        G    MFNN  17.371446 1.000000  0.741849  8
    0        W HF_only  38.603355 0.933333  0.130475 15
    0        W LF_only 122.295407 0.533333 -2.502884 15
    0        W    MFNN  25.759821 0.933333  0.474812 15
    1        G HF_only  17.301981 1.000000  0.212265 10
    1        G LF_only  21.795593 1.000000 -0.540496 10
    1        G    MFNN  13.464178 1.000000  0.438119 10
    1        W HF_only  30.071247 1.000000  0.326577 15
    1        W LF_only  96.189401 0.733333 -1.916295 15
    1        W    MFNN  23.981770 0.933333  0.477524 15
    2        G HF_only  47.682342 0.500000 -2.034037  8
    2        G LF_only  30.561153 1.000000  0.473345  8
    2        G    MFNN  40.324631 0.500000 -1.024226  8
    2        W HF_only  29.789694 1.000000  0.224199 15
    2        W LF_only 111.917640 0.466667 -3.153194 15
    2        W    MFNN  27.614428 1.000000  0.305519 15
   42        G HF_only  38.953868 0.750000 -0.308871  8
   42        G LF_only  98.037353 0.500000 -1.741332  8
   42        G    MFNN  20.407325 1.000000  0.769034  8
   42        W HF_only  31.573153 0.933333  0.306234 15
   42        W LF_only 124.817147 0.466667 -2.667255 15
   42        W    MFNN  27.526907 0.933333  0.448713 15
  123        G HF_only  50.838734 0.363636 -7.999742 11
  123        G LF_only  33.246825 0.909091 -0.832662 11
  123        G    MFNN  45.237544 0.454545 -4.754413 11
  123        W HF_only  24.851519 1.000000  0.328004 15
  123        W LF_only  92.746201 0.600000 -2.700579 15
  123        W    MFNN  26.034135 1.000000  0.252941 15
```

## 协议 G：每个 seed 的 hold-out 体系 / 是否仅 Al-Cu

G 随留出 `comp_group` 变化：同一模型在「软」hold-out（纯 Al / 杂质）与「硬」hold-out（高 Cu 合金组）上 MAPE 可差一个数量级。

| seed | G systems | G comp_groups | only Al-Cu? | n_test |
|------|-----------|---------------|-------------|--------|
| 0 | Al-Cu | Al75Cu25,Al90Cu10 | True | 8 |
| 1 | Al-Cu | Al81.3Cu18.7,Al85Cu15 | True | 10 |
| 2 | Al-Cu | Al75Cu25,Al90Cu10 | True | 8 |
| 42 | Al-Cu | Al75Cu25,Al90Cu10 | True | 8 |
| 123 | Al-Cu | Al81.3Cu18.7,Al95Cu5 | True | 11 |

## 各 seed 的 MFNN ALL MAPE% / Factor2（W vs G）

| seed | W MAPE% | W Fac2 | G MAPE% | G Fac2 | G only Al-Cu |
|------|---------|--------|---------|--------|--------------|
| 0 | 25.76 | 0.933 | 17.37 | 1.000 | True |
| 1 | 23.98 | 0.933 | 13.46 | 1.000 | True |
| 2 | 27.61 | 1.000 | 40.32 | 0.500 | True |
| 42 | 27.53 | 0.933 | 20.41 | 1.000 | True |
| 123 | 26.03 | 1.000 | 45.24 | 0.455 | True |

## 基线 ALL MAPE mean±std（对照）

### Protocol W

- **LF_only**: MAPE 109.6 ± 13.13; Factor2 0.56 ± 0.09978
- **HF_only**: MAPE 30.98 ± 4.433; Factor2 0.9733 ± 0.03266
- **MFNN**: MAPE 26.18 ± 1.334; Factor2 0.96 ± 0.03266

### Protocol G

- **LF_only**: MAPE 52.95 ± 30.61; Factor2 0.8068 ± 0.2061
- **HF_only**: MAPE 36.66 ± 12.4; Factor2 0.7227 ± 0.2581
- **MFNN**: MAPE 27.36 ± 12.88; Factor2 0.7909 ± 0.2565

## 文件

- `outputs/seed_WG_summary.csv`
- `outputs/SEED_WG_STABILITY.md`
- per-seed: `outputs/seed_wg_<SEED>/metrics_within_T.csv`, `metrics_between_group.csv`
