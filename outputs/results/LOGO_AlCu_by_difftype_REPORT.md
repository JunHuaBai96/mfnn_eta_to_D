# Al–Cu LOGO（按 diff_type 拆组后）

将同 `comp_group` 内冲突的 tracer / inter（含 interdiffusivity→inter）拆成 `Al80Cu20_tracer` / `Al80Cu20_inter` 等；**杂质**用 `_impurity`，不并入 tracer/inter。特征**未**加 diff_type one-hot（仅消除 hold-out 标签冲突）。LOGO 折不随机；`--seed 42` 仅控优化器/val。缺 η 仍 drop；无 Kozlov 填 HF η。

> 仍是 **Al–Cu 体系内成分外推**，不是跨合金体系；也不是随机 seed 的 G≈20%。

备份：`data/melt_diffusion_data_backup_before_difftype.csv`

## 拆组验证

### Al80Cu20 HF 拆后

| new comp_group | diff_types | n | D min–max (×1e-9) |
|---|---|---:|---|
| Al80Cu20_inter | inter,interdiffusivity | 2 | 7.00–8.90 |
| Al80Cu20_tracer | tracer | 10 | 2.35–4.85 |

同温不再把 tracer 与 inter 放在同一 hold-out 组。

**解读：** 拆组消除了「同一折内标签打架」；`Al80Cu20_inter` 折 Fac2=1.0；但 `Al80Cu20_tracer` 留出时训练邻域仍以 inter 量级为主，tracer 折仍偏高——说明仅改标签不够，后续可加 diff_type 特征。

## 折列表（新）

| holdout_group | n_test |
|---|---:|
| Al70Cu30_inter | 2 |
| Al75Cu25_tracer | 3 |
| Al80Cu20_inter | 2 |
| Al80Cu20_tracer | 10 |
| Al81.3Cu18.7_inter | 9 |
| Al81Cu19_inter | 1 |
| Al82.9Cu17.1_tracer | 3 |
| Al85Cu15_inter | 1 |
| Al87Cu13_inter | 1 |
| Al90Cu10_inter | 2 |
| Al90Cu10_tracer | 3 |
| Al95Cu5_inter | 2 |
| PureAl_impurityCu_impurity | 9 |

共 **13** 折。

## 新旧对比（MFNN）

- **旧 LOGO（混类型标签）** MFNN MAPE%: 45.49 ± 48.7；最差折 `Al80Cu20` = 158.1% (n=12 混合 tracer+inter)
- **新 LOGO（按 diff_type 拆组）** MFNN MAPE%: 44.11 ± 48.48

### 原 Al80Cu20 拆开后两折

| holdout | model | MAPE% | Factor2 | n |
|---|---|---:|---:|---:|
| Al80Cu20_tracer | LF_only | 154.39 | 0.000 | 10 |
| Al80Cu20_tracer | HF_only | 174.59 | 0.000 | 10 |
| Al80Cu20_tracer | MFNN | 203.24 | 0.000 | 10 |
| Al80Cu20_inter | LF_only | 11.92 | 1.000 | 2 |
| Al80Cu20_inter | HF_only | 27.67 | 1.000 | 2 |
| Al80Cu20_inter | MFNN | 28.83 | 1.000 | 2 |

旧混合折（MAPE≈158%、Fac2=0.167）不可再当作唯一结论；请分别引用 `_tracer` / `_inter`。

## ALL 指标 mean ± std（新 LOGO，跨折）

### LF_only

- **MAPE%**: 82.49 ± 72.62
- **Factor2**: 0.6026 ± 0.4507
- **R²**: -11.38 ± 15.47

### HF_only

- **MAPE%**: 42.88 ± 41.52
- **Factor2**: 0.859 ± 0.2846
- **R²**: -3.641 ± 5.273

### MFNN

- **MAPE%**: 44.11 ± 48.48
- **Factor2**: 0.8846 ± 0.2878
- **R²**: -3.871 ± 6.334

## MFNN 最好 / 最差折（新）

- **最好**: `Al90Cu10_tracer` — MAPE=17.16%, Fac2=1.000, n=3
- **最差**: `Al80Cu20_tracer` — MAPE=203.24%, Fac2=0.000, n=10

## 逐折明细

```
             holdout_group   model   MAPE_pct  Factor2         R2  n
            Al70Cu30_inter HF_only  79.539300 0.500000  -4.818528  2
            Al70Cu30_inter LF_only 134.004107 0.500000 -10.570558  2
            Al70Cu30_inter    MFNN  78.279443 0.500000  -4.577370  2
           Al75Cu25_tracer HF_only  17.182511 1.000000   0.629508  3
           Al75Cu25_tracer LF_only  31.058967 1.000000   0.332372  3
           Al75Cu25_tracer    MFNN  20.765017 1.000000   0.610929  3
            Al80Cu20_inter HF_only  27.668641 1.000000  -7.222384  2
            Al80Cu20_inter LF_only  11.915318 1.000000   0.032313  2
            Al80Cu20_inter    MFNN  28.833785 1.000000  -7.441682  2
           Al80Cu20_tracer HF_only 174.591400 0.000000 -17.235631 10
           Al80Cu20_tracer LF_only 154.390065 0.000000 -14.610273 10
           Al80Cu20_tracer    MFNN 203.236088 0.000000 -20.992327 10
        Al81.3Cu18.7_inter HF_only  38.967003 0.777778  -5.873176  9
        Al81.3Cu18.7_inter LF_only  13.274432 1.000000   0.380216  9
        Al81.3Cu18.7_inter    MFNN  39.441727 1.000000  -5.481292  9
            Al81Cu19_inter HF_only  20.597110 1.000000        NaN  1
            Al81Cu19_inter LF_only  14.218676 1.000000        NaN  1
            Al81Cu19_inter    MFNN  28.173631 1.000000        NaN  1
       Al82.9Cu17.1_tracer HF_only  27.491541 1.000000   0.138310  3
       Al82.9Cu17.1_tracer LF_only  16.814023 1.000000   0.717836  3
       Al82.9Cu17.1_tracer    MFNN  22.756072 1.000000   0.559476  3
            Al85Cu15_inter HF_only  19.137885 1.000000        NaN  1
            Al85Cu15_inter LF_only  52.409731 1.000000        NaN  1
            Al85Cu15_inter    MFNN  19.814585 1.000000        NaN  1
            Al87Cu13_inter HF_only  46.831628 1.000000        NaN  1
            Al87Cu13_inter LF_only   9.569393 1.000000        NaN  1
            Al87Cu13_inter    MFNN  41.921181 1.000000        NaN  1
            Al90Cu10_inter HF_only  18.247674 1.000000  -0.273268  2
            Al90Cu10_inter LF_only 140.252976 0.000000 -29.082946  2
            Al90Cu10_inter    MFNN  23.992736 1.000000  -1.516603  2
           Al90Cu10_tracer HF_only  18.294208 1.000000   0.578572  3
           Al90Cu10_tracer LF_only 116.946573 0.333333  -3.252835  3
           Al90Cu10_tracer    MFNN  17.159889 1.000000   0.728980  3
             Al95Cu5_inter HF_only  25.978395 1.000000  -1.425862  2
             Al95Cu5_inter LF_only 243.639806 0.000000 -49.352550  2
             Al95Cu5_inter    MFNN  19.027406 1.000000  -0.693406  2
PureAl_impurityCu_impurity HF_only  42.915138 0.888889  -0.903008  9
PureAl_impurityCu_impurity LF_only 133.832618 0.000000  -8.348526  9
PureAl_impurityCu_impurity    MFNN  30.052425 1.000000   0.095071  9
```

## 可选：协议 W（within_T）按 diff_type 分层（MFNN）

```
diff_type_norm model  MAPE_pct  Factor2        R2  n
      impurity  MFNN 17.314427 1.000000  0.861453  4
         inter  MFNN 32.173949 1.000000 -0.739356  2
          self  MFNN  5.661654 1.000000  0.924703  3
        tracer  MFNN 47.224871 0.800000 -0.233607  5
           ALL  MFNN 27.622495 0.928571  0.496501 14
```

W 是组内温度插值，与 LOGO 成分外推不同；仅作主文对照。

## 文件

- `outputs/LOGO_AlCu_by_difftype_summary.csv`
- `outputs/LOGO_AlCu_by_difftype_REPORT.md`
- 旧对照：`outputs/LOGO_AlCu_summary.csv`
- 备份：`data/melt_diffusion_data_backup_before_difftype.csv`
