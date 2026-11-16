# Al80Cu20_tracer 事后截距校准（post-hoc intercept shift / B2）

> **范围：仅 SI / 机制诊断。** 标题必须是「事后截距校准 / post-hoc intercept shift」。**不是**纯 LOGO 成功；**禁止**写成「LOGO 已被修好」或「100%」。零重训：只读取 `outputs/al80_anchor_folds/seed*_k0/test_predictions.csv`。未改冻结 Protocol W 数字。

## 方法

对每个 seed 的 k0（纯 LOGO）预测：在锚点温度 $T_{\mathrm{anchor}}=983\,\mathrm{K}$（及敏感性对照 $1200\,\mathrm{K}$）上计算 $\delta = y_{\mathrm{true}} - \hat{y}_H^{(k0)}$（$\log_{10} D$ 空间），再对**其余** $n=9$ 个温度点做零自由度平移：$\hat{y}^{\mathrm{shifted}}=\hat{y}^{(k0)}+\delta$。对照：同 9 点上的 raw k0，以及实验 B 已跑的 `k1_lowT` / `k1_highT` 重训指标。

## MFNN 汇总（5-seed mean ± std, ddof=0；评估点 = 去掉锚点后的 9 点）

| setting | MAPE% | Factor2 | R² | mean δ (log10) |
|---------|------:|--------:|---:|---------------:|
| k0 raw (held-out 9 @ drop 983K) | 175.20 ± 28.78 | 0.000 ± 0.000 | -21.788 ± 4.692 | 0.0000 ± 0.0000 |
| k0 + post-hoc shift @ 983K | 9.81 ± 1.73 | 1.000 ± 0.000 | 0.689 ± 0.123 | -0.4822 ± 0.0463 |
| B retrain k1_lowT (n=9) | 169.55 ± 35.51 | 0.000 ± 0.000 | -20.864 ± 5.779 | — |
| k0 raw (held-out 9 @ drop 1200K) | 180.62 ± 29.39 | 0.000 ± 0.000 | -21.750 ± 4.603 | 0.0000 ± 0.0000 |
| k0 + post-hoc shift @ 1200K | 9.40 ± 2.23 | 1.000 ± 0.000 | 0.763 ± 0.101 | -0.4068 ± 0.0447 |

## 逐 seed（MFNN，锚点 983 K）

| seed | δ | k0_raw MAPE | k0_raw Fac2 | shift MAPE | shift Fac2 | B k1_lowT MAPE | B k1_lowT Fac2 |
|-----:|--:|------------:|------------:|-----------:|-----------:|---------------:|---------------:|
| 0 | -0.4781 | 171.97 | 0.000 | 9.55 | 1.000 | 228.08 | 0.000 |
| 1 | -0.5316 | 210.09 | 0.000 | 8.83 | 1.000 | 187.49 | 0.000 |
| 2 | -0.4077 | 136.07 | 0.000 | 7.68 | 1.000 | 128.92 | 0.000 |
| 42 | -0.4628 | 152.90 | 0.000 | 12.87 | 1.000 | 140.14 | 0.000 |
| 123 | -0.5307 | 204.98 | 0.000 | 10.14 | 1.000 | 163.14 | 0.000 |

## 判读（诚实）

- **事后截距平移有效（机制洞见，非 LOGO 成功）**：去掉 983 K 后的 9 点上，MAPE 175.2% → 9.8%；Factor2 0.000 → 1.000。
- 这表明：在当前 k0 预测上，**温度斜率大体可用**，主要误差更像 $\log_{10} D$ 轴上的系统性截距/尺度偏移（可用 Darken 类热力学因子作**展望**，勿写「已证明 100%」）。
- 与实验 B 的 `k1_lowT` 重训对比：若 shift ≫ retrain，说明 **单点放回未加权 MSE 会被背景稀释**；事后平移没有梯度竞争，故更易对齐。
- **标签**：事后物理机制拆解 / **仅限 SI** / **不是**纯 LOGO 协议结果。

## 冻结声明

- Protocol W 主文数字：**未改动**。
- 无 Kozlov / 无补 η / 无架构修改 / 无重训。

## 文件

- `scripts/run_al80_posthoc_intercept_shift.py`
- `outputs/results/AL80_posthoc_intercept_shift.csv`
- `outputs/results/AL80_posthoc_intercept_shift_REPORT.md`
- `outputs/figures/fig_si_al80_posthoc_shift.png`（若生成）
