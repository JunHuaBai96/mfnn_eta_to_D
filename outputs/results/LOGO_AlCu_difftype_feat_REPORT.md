# Al–Cu LOGO + diff_type one-hot 特征

在已拆组（`Al80Cu20_tracer` / `_inter` 等）基础上，特征由 **12→16** 维：物理/成分 12 维 z-score + one-hot `['tracer', 'inter', 'impurity', 'other']` （`interdiffusivity`→inter；`self`/未知→**other**）。网络仍为 Residual MFNN，仅 `in_dim` 随特征变。`--seed 42` 仅控优化器。缺 η drop；未改 D/η；无 Kozlov 填 HF η。

> Al–Cu **体系内**成分外推；对照「仅拆组、无 one-hot」见 `LOGO_AlCu_by_difftype_*`。

## 特征维数

| 块 | 维数 | 说明 |
|---|---:|---|
| 物理/成分 | 12 | T, 1000/T, η, log10η, 7 comps, r_diff；**z-score** |
| diff_type one-hot | 4 | tracer, inter, impurity, other；**不 z-score** |
| **合计** | **16** | 旧版无 one-hot 时为 12 |

## 折列表

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

## 新旧对比（重点 Al80）

| holdout | 仅拆组 MFNN MAPE / Fac2 / n | +one-hot MFNN MAPE / Fac2 / n |
|---|---|---|
| `Al80Cu20_tracer` | 203.24% / 0.000 / 10 | 156.49% / 0.000 / 10 |
| `Al80Cu20_inter` | 28.83% / 1.000 / 2 | 6.48% / 1.000 / 2 |

### 全体 MFNN mean±std

- **仅拆组（无 one-hot）**: 44.11 ± 48.48
- **拆组 + one-hot**: 39.43 ± 39.71

### 是否缓解 inter→tracer？

是：`Al80Cu20_tracer` MAPE 203.2% → **156.5%**（下降明显）； `Al80Cu20_inter` 28.8% → 6.5%。

## ALL 指标 mean ± std（本跑，跨折）

### LF_only

- **MAPE%**: 283.5 ± 190.3
- **Factor2**: 0.2462 ± 0.4162
- **R²**: -55.15 ± 63.79

### HF_only

- **MAPE%**: 398.4 ± 1225
- **Factor2**: 0.7436 ± 0.3956
- **R²**: -26.78 ± 67.41

### MFNN

- **MAPE%**: 39.43 ± 39.71
- **Factor2**: 0.7436 ± 0.3956
- **R²**: -2.952 ± 4.332

## MFNN 最好 / 最差折

- **最好**: `Al81Cu19_inter` — MAPE=1.14%, Fac2=1.000, n=1
- **最差**: `Al80Cu20_tracer` — MAPE=156.49%, Fac2=0.000, n=10

## 逐折明细

```
             holdout_group   model    MAPE_pct  Factor2          R2  n
            Al70Cu30_inter HF_only 4638.991096 0.000000 -228.225487  2
            Al70Cu30_inter LF_only  361.500797 0.000000  -35.254618  2
            Al70Cu30_inter    MFNN   67.313712 1.000000   -3.365388  2
           Al75Cu25_tracer HF_only   37.264313 1.000000   -0.565249  3
           Al75Cu25_tracer LF_only   29.628601 1.000000    0.244394  3
           Al75Cu25_tracer    MFNN   51.188119 0.333333   -2.247837  3
            Al80Cu20_inter HF_only    6.977778 1.000000    0.348770  2
            Al80Cu20_inter LF_only  434.482508 0.000000 -193.518883  2
            Al80Cu20_inter    MFNN    6.475800 1.000000    0.632791  2
           Al80Cu20_tracer HF_only  201.075418 0.000000  -20.712651 10
           Al80Cu20_tracer LF_only  144.095098 0.200000  -13.291995 10
           Al80Cu20_tracer    MFNN  156.486342 0.000000  -14.867429 10
        Al81.3Cu18.7_inter HF_only   41.791370 1.000000   -6.405425  9
        Al81.3Cu18.7_inter LF_only  379.275341 0.000000  -57.768203  9
        Al81.3Cu18.7_inter    MFNN   24.192887 1.000000   -0.950292  9
            Al81Cu19_inter HF_only    6.232704 1.000000         NaN  1
            Al81Cu19_inter LF_only  461.895424 0.000000         NaN  1
            Al81Cu19_inter    MFNN    1.137040 1.000000         NaN  1
       Al82.9Cu17.1_tracer HF_only   54.116268 0.333333   -3.995329  3
       Al82.9Cu17.1_tracer LF_only   24.828103 1.000000    0.405156  3
       Al82.9Cu17.1_tracer    MFNN   48.729114 0.333333   -1.886183  3
            Al85Cu15_inter HF_only   22.819913 1.000000         NaN  1
            Al85Cu15_inter LF_only  359.559560 0.000000         NaN  1
            Al85Cu15_inter    MFNN    4.989942 1.000000         NaN  1
            Al87Cu13_inter HF_only   48.402569 1.000000         NaN  1
            Al87Cu13_inter LF_only  183.490613 0.000000         NaN  1
            Al87Cu13_inter    MFNN   35.141543 1.000000         NaN  1
            Al90Cu10_inter HF_only   17.038560 1.000000   -2.128997  2
            Al90Cu10_inter LF_only  406.691249 0.000000 -100.959799  2
            Al90Cu10_inter    MFNN   24.524160 1.000000   -1.461016  2
           Al90Cu10_tracer HF_only   60.748870 0.333333   -6.005146  3
           Al90Cu10_tracer LF_only   27.999840 1.000000   -0.420164  3
           Al90Cu10_tracer    MFNN   60.687054 0.000000   -5.421188  3
             Al95Cu5_inter HF_only   16.821289 1.000000    0.091753  2
             Al95Cu5_inter LF_only  667.764422 0.000000 -135.964299  2
             Al95Cu5_inter    MFNN   18.781356 1.000000   -0.678736  2
PureAl_impurityCu_impurity HF_only   27.280665 1.000000   -0.190356  9
PureAl_impurityCu_impurity LF_only  203.905790 0.000000  -14.972092  9
PureAl_impurityCu_impurity    MFNN   12.930658 1.000000    0.721486  9
```

## 可选：协议 W（within_T）按类型分层（MFNN）

```
diff_type_norm model  MAPE_pct  Factor2        R2  n
      impurity  MFNN 36.560255 1.000000  0.481155  4
         inter  MFNN 15.008324 1.000000  0.713770  2
          self  MFNN 10.557365 1.000000  0.711823  3
        tracer  MFNN 51.526906 0.400000 -2.161999  5
           ALL  MFNN 33.254592 0.785714 -0.093698 14
```

## 文件

- `outputs/LOGO_AlCu_difftype_feat_summary.csv`
- `outputs/LOGO_AlCu_difftype_feat_REPORT.md`
- 对照：`outputs/LOGO_AlCu_by_difftype_summary.csv`
