# Al80Cu20_tracer 邻域锚点敏感度（few-shot anchor sensitivity / 反事实诊断）

> **范围：仅 SI / Discussion。** 这不是新的主结论实验。k>0 时训练集含 holdout 组内端点 → **不再是纯 LOGO**；**禁止**写成「LOGO 已被修好」。未改冻结 Protocol W 数字；无 Kozlov / 无合成 η；架构仍为 Residual MFNN + diff_type one-hot（与 `run_logo_alcu_difftype_feat.py` 一致）。

- holdout: `Al80Cu20_tracer`（Zhang 网格 tracer，全组 n≈10）
- seeds: [0, 1, 2, 42, 123]
- 模式: `k0`（纯 LOGO） / `k1_lowT` / `k1_highT` / `k2`（两端点回训）
- 历史对照（difftype-feat LOGO seed42 MFNN）: MAPE≈156.49%, Factor2=0, n=10

## 成功判据（SI 叙事）

若 k=1 或 k=2 后 MFNN MAPE 相对 k=0 **断崖下降**且 Factor2 明显回升，支持「邻域 tracer HF 稀疏 / 缺局部尺度锚点」叙事；**不**等于宣称 LOGO 协议已通过。

## MFNN 汇总（跨 seed mean ± std, ddof=0）

| mode | k | n_test | MAPE% | Factor2 | R² | n_seeds |
|------|--:|-------:|------:|--------:|---:|--------:|
| `k0` | 0 | 10 | 178.20 ± 29.05 | 0.000 ± 0.000 | -17.713 ± 3.806 | 5 |
| `k1_lowT` | 1 | 9 | 169.55 ± 35.51 | 0.000 ± 0.000 | -20.864 ± 5.779 | 5 |
| `k1_highT` | 1 | 9 | 175.27 ± 32.93 | 0.000 ± 0.000 | -20.910 ± 5.149 | 5 |
| `k2` | 2 | 8 | 142.93 ± 35.53 | 0.000 ± 0.000 | -20.354 ± 7.022 | 5 |

## 逐 seed 明细（MFNN）

| seed | mode | k | n_test | anchor_T_K | MAPE% | Factor2 | R² |
|-----:|------|--:|-------:|------------|------:|--------:|---:|
| 0 | `k0` | 0 | 10 |  | 174.84 | 0.000 | -17.274 |
| 0 | `k1_highT` | 1 | 9 | 1200.0 | 227.28 | 0.000 | -29.037 |
| 0 | `k1_lowT` | 1 | 9 | 983.0 | 228.08 | 0.000 | -30.380 |
| 0 | `k2` | 2 | 8 | 983.0;1200.0 | 211.01 | 0.000 | -33.823 |
| 1 | `k0` | 0 | 10 |  | 213.09 | 0.000 | -22.281 |
| 1 | `k1_highT` | 1 | 9 | 1200.0 | 185.35 | 0.000 | -22.496 |
| 1 | `k1_lowT` | 1 | 9 | 983.0 | 187.49 | 0.000 | -23.800 |
| 1 | `k2` | 2 | 8 | 983.0;1200.0 | 140.20 | 0.000 | -19.780 |
| 2 | `k0` | 0 | 10 |  | 138.03 | 0.000 | -12.450 |
| 2 | `k1_highT` | 1 | 9 | 1200.0 | 130.83 | 0.000 | -13.961 |
| 2 | `k1_lowT` | 1 | 9 | 983.0 | 128.92 | 0.000 | -14.254 |
| 2 | `k2` | 2 | 8 | 983.0;1200.0 | 112.36 | 0.000 | -14.348 |
| 42 | `k0` | 0 | 10 |  | 156.63 | 0.000 | -14.887 |
| 42 | `k1_highT` | 1 | 9 | 1200.0 | 150.91 | 0.000 | -17.092 |
| 42 | `k1_lowT` | 1 | 9 | 983.0 | 140.14 | 0.000 | -16.067 |
| 42 | `k2` | 2 | 8 | 983.0;1200.0 | 117.45 | 0.000 | -15.329 |
| 123 | `k0` | 0 | 10 |  | 208.42 | 0.000 | -21.672 |
| 123 | `k1_highT` | 1 | 9 | 1200.0 | 181.96 | 0.000 | -21.965 |
| 123 | `k1_lowT` | 1 | 9 | 983.0 | 163.14 | 0.000 | -19.818 |
| 123 | `k2` | 2 | 8 | 983.0;1200.0 | 133.64 | 0.000 | -18.487 |

## HF_only contrast (SI side note)

Some seeds: HF_only Factor2 rises at k=2 (e.g. seed42/1/2 Fac2~0.75-0.875) while MFNN Factor2 stays 0 for all seeds/modes. Anchors help pure HF fit more than residual MFNN on Factor2 hard threshold; does not support cliff-fix MFNN narrative.

| mode | HF_only MAPE% | HF_only Factor2 |
|------|--------------:|----------------:|
| `k0` | 161.95 +/- 39.34 | 0.000 +/- 0.000 |
| `k1_lowT` | 136.95 +/- 22.86 | 0.089 +/- 0.178 |
| `k1_highT` | 137.20 +/- 29.88 | 0.178 +/- 0.181 |
| `k2` | 105.44 +/- 37.24 | 0.575 +/- 0.312 |

## 断崖下降判定

- `k1_lowT`: MAPE 178.2% → 169.6% (Δ=8.7 pp, ratio=0.95); Factor2→0.000; 未达断崖判据
- `k1_highT`: MAPE 178.2% → 175.3% (Δ=2.9 pp, ratio=0.98); Factor2→0.000; 未达断崖判据
- `k2`: MAPE 178.2% → 142.9% (Δ=35.3 pp, ratio=0.80); Factor2→0.000; 未达断崖判据

**诚实失败表述（SI）：** 即便提供极少量局部温度锚点，高密度 Arrhenius 网格与多源异构互扩散背景之间的权重竞争仍可能限制单头残差网络的局部校准；未来可考虑显式 Darken Φ 等物理特征，**而非**改 PINN/双头架构刷分。本实验不改冻结 Protocol W 数字。

## 文件

- `outputs/results/AL80_tracer_anchor_sensitivity.csv`
- `outputs/results/AL80_tracer_anchor_sensitivity_REPORT.md`
- `outputs/figures/fig_si_al80_anchor_k.png`（若生成）
- folds: `outputs/al80_anchor_folds/`
