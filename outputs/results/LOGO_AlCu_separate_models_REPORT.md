# Al–Cu 分训 Residual MFNN（tracer / inter）+ 分池 LOGO

两套独立模型：**tracer 池**仅 `diff_type∈{tracer}`；**inter 池**仅 `{inter, interdiffusivity→inter}`。`impurity` / `self` **未入池**。分训子集内特征为 **12 维物理特征**（去掉 diff_type one-hot，避免冗余）。`--seed 42` 仅控优化器。缺 η drop；未改 D/η；无 Kozlov。

> 验证「同类型内迁移」是否好于联合+one-hot；仍是 Al–Cu 体系内成分外推。

## 池规模与折

### tracer

| holdout_group | n_test |
|---|---:|
| Al75Cu25_tracer | 3 |
| Al80Cu20_tracer | 10 |
| Al82.9Cu17.1_tracer | 3 |
| Al90Cu10_tracer | 3 |

共 4 折。

### inter

| holdout_group | n_test |
|---|---:|
| Al70Cu30_inter | 2 |
| Al80Cu20_inter | 2 |
| Al81.3Cu18.7_inter | 9 |
| Al81Cu19_inter | 1 |
| Al85Cu15_inter | 1 |
| Al87Cu13_inter | 1 |
| Al90Cu10_inter | 2 |
| Al95Cu5_inter | 2 |

共 8 折。

## 与联合+one-hot 对照（Al80）

| holdout | 联合+one-hot MFNN | 分训池 MFNN |
|---|---|---|
| `Al80Cu20_tracer` | 156.49% / Fac2=0.000 / n=10 | 173.29% / Fac2=0.000 / n=10 |
| `Al80Cu20_inter` | 6.48% / Fac2=1.000 / n=2 | 10.95% / Fac2=1.000 / n=2 |

## 各池 MFNN mean±std（跨折）

- **tracer**（4 折）: MAPE **99.66 ± 54.55**; Factor2 0.417 ± 0.363
- **inter**（8 折，含 Al70Cu30 爆炸折）: MAPE 1.87e+13 ± 4.95e+13（**不可直接引用**）
- **inter 稳健**（排除 `Al70Cu30_inter`）: MAPE **17.96 ± 16.90**; Factor2 **1.000 ± 0**
- **联合+one-hot（对照，13 折）**: MAPE 39.43 ± 39.71; Factor2 0.744 ± 0.396

## 结论：同类型内迁移是否更好？

- **tracer→tracer**（`Al80Cu20_tracer`）: 联合 156.5% → 分训 **173.3%**（Fac2 仍 0）— **未好于联合**；池内 HF 仅 19 点，留出 Al80 后训练 HF≈6–9，样本更紧。
- **inter→inter**（`Al80Cu20_inter`）: 联合 6.5% → 分训 **11.0%**（Fac2=1）— **未好于联合**；其它 inter 折（除 Al70）多数尚可，稳健均值 ~18%。

**总答：** 在本数据规模下，分训**没有**证明「同类型内迁移」明显优于联合+one-hot；`Al80Cu20_tracer` 仍挂。瓶颈更像是 **Al–Cu tracer HF 组太少 / 邻域不足**，而非「缺 one-hot」。

注：当前 CSV **inter 池 LF=0**，MFNN 的 LF 分支无数据；LF_only 跳过（NaN）。tracer 池 LF_only 爆炸因 LF/HF 尺度不一致，勿作主结论。impurity / self **未入池**。

## 逐折明细

```
  pool       holdout_group   model     MAPE_pct  Factor2           R2  n
 inter      Al70Cu30_inter HF_only 2.583819e+03 0.000000  -140.830835  2
 inter      Al70Cu30_inter LF_only          NaN 0.000000          NaN  2
 inter      Al70Cu30_inter    MFNN 1.496066e+14 0.000000 -6776.773998  2
 inter      Al80Cu20_inter HF_only 1.169012e+01 1.000000    -0.350360  2
 inter      Al80Cu20_inter LF_only          NaN 0.000000          NaN  2
 inter      Al80Cu20_inter    MFNN 1.095008e+01 1.000000     0.151009  2
 inter  Al81.3Cu18.7_inter HF_only 8.158669e+03 0.333333  -234.313210  9
 inter  Al81.3Cu18.7_inter LF_only          NaN 0.000000          NaN  9
 inter  Al81.3Cu18.7_inter    MFNN 4.296512e+00 1.000000     0.934714  9
 inter      Al81Cu19_inter HF_only 1.432627e+00 1.000000          NaN  1
 inter      Al81Cu19_inter LF_only          NaN 0.000000          NaN  1
 inter      Al81Cu19_inter    MFNN 2.756682e+00 1.000000          NaN  1
 inter      Al85Cu15_inter HF_only 2.282787e+00 1.000000          NaN  1
 inter      Al85Cu15_inter LF_only          NaN 0.000000          NaN  1
 inter      Al85Cu15_inter    MFNN 8.972386e-01 1.000000          NaN  1
 inter      Al87Cu13_inter HF_only 4.495383e+01 1.000000          NaN  1
 inter      Al87Cu13_inter LF_only          NaN 0.000000          NaN  1
 inter      Al87Cu13_inter    MFNN 3.144558e+01 1.000000          NaN  1
 inter      Al90Cu10_inter HF_only 9.473251e+01 0.500000   -17.268388  2
 inter      Al90Cu10_inter LF_only          NaN 0.000000          NaN  2
 inter      Al90Cu10_inter    MFNN 4.952668e+01 1.000000    -7.265891  2
 inter       Al95Cu5_inter HF_only 2.567119e+01 1.000000    -1.347952  2
 inter       Al95Cu5_inter LF_only          NaN 0.000000          NaN  2
 inter       Al95Cu5_inter    MFNN 2.586126e+01 1.000000    -1.347862  2
tracer     Al75Cu25_tracer HF_only 7.685813e+01 0.666667    -1.671475  3
tracer     Al75Cu25_tracer LF_only 2.103902e+08 0.000000  -655.390973  3
tracer     Al75Cu25_tracer    MFNN 1.307421e+02 0.333333    -3.802983  3
tracer     Al80Cu20_tracer HF_only 1.813791e+02 0.000000   -18.123907 10
tracer     Al80Cu20_tracer LF_only 1.679241e+05 0.000000  -860.993630 10
tracer     Al80Cu20_tracer    MFNN 1.732947e+02 0.000000   -17.071108 10
tracer Al82.9Cu17.1_tracer HF_only 5.949191e+01 0.000000    -4.408348  3
tracer Al82.9Cu17.1_tracer LF_only 5.480999e+10 0.000000 -1217.841934  3
tracer Al82.9Cu17.1_tracer    MFNN 5.110349e+01 0.333333    -2.415426  3
tracer     Al90Cu10_tracer HF_only 6.361173e+01 0.000000    -6.572674  3
tracer     Al90Cu10_tracer LF_only 3.149610e+09 0.000000 -1011.880603  3
tracer     Al90Cu10_tracer    MFNN 4.348225e+01 1.000000    -1.326871  3
```

## 可选：各池 within_T（MFNN）

```
  pool protocol diff_type_norm model  MAPE_pct  Factor2        R2  n
tracer within_T         tracer  MFNN 28.598093      0.8 -0.147398  5
 inter within_T          inter  MFNN  1.763798      1.0  0.995917  2
```

## 文件

- `outputs/LOGO_AlCu_separate_models_summary.csv`
- `outputs/LOGO_AlCu_separate_models_REPORT.md`
- 对照：`outputs/LOGO_AlCu_difftype_feat_summary.csv`
