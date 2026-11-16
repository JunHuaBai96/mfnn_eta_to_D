# Protocol W 五种子 Ensemble Parity（Fig.2(c)）

后处理-only：读取 `outputs/seed_wg_{0,1,2,42,123}/test_predictions_within_T.csv`，**未重训**。未改动冻结主结论数字（MAPE $26.18\pm1.33\%$、Factor2 $0.96\pm0.033$、R² $0.392\pm0.094$ 等仍以 `SEED_WG_STABILITY.md` / Table 1 为准）。

## 对齐说明

- 各 seed within_T 测试集不完全相同（每 seed $n=15$，union=21，**五种子共有** sample_id 数=13）。
- 主图展示 **union** 全部对齐点（实心=$n_{\mathrm{seeds}}=5$，空心=部分重叠）；逐点 std 表以 **五种子共有点** 统计；Factor2 分别报告共有点与 union。CSV 含全部点（`all_five_seeds` 列）。
- Factor2 判定（对 seed-mean pred）：$|\overline{\log_{10} D_{\mathrm{pred}}} - \log_{10} D_{\mathrm{true}}| \le \log_{10} 2 \approx 0.301030$。

## 逐点预测 std（5-seed，共有点）

| model | mean(std) | median(std) | n_points |
|---|---:|---:|---:|
| LF_only | 0.0396031 | 0.0355727 | 13 |
| HF_only | 0.0290621 | 0.0209504 | 13 |
| MFNN | 0.0198865 | 0.0187057 | 13 |

**HF_only vs MFNN：** mean std 0.0290621 vs 0.0198865；median std 0.0209504 vs 0.0187057（$n=13$）。

## MFNN Factor2（按 seed-mean pred）

- **五种子共有点：** MFNN **0/13** 点落在 Factor2 带外。

- **Union（含 $n_{\mathrm{seeds}}<5$）：** MFNN Factor2 外 **2/21**：`R017, R301`。

| sample_id | T_K | comp_group | y_true | pred_mean | |Δlog10| | n_seeds |
|---|---:|---|---:|---:|---:|---:|
| R017 | 1000.0 | Al80Cu20 | -8.599575 | -8.274177 | 0.325399 | 2 |
| R301 | 1025.0 | Al80Cu20 | -8.557782 | -8.226076 | 0.331706 | 1 |

## 与冻结 Factor2 的关系

冻结主文数字 **Factor2 $0.96\pm0.033$（MFNN）vs HF_only $0.973\pm0.033$** 来自各 seed 在 **$n=15$** 测试集上的硬计数再跨 seed 平均（见 `outputs/SEED_WG_STABILITY.md`），**不是**本图重新定义的指标。

**明确一句：** 五种子共有点上 MFNN 跌出 Factor2 为 **0/13**；union 上为 **2** 个边缘点（`R017, R301`，且均为 $n_{\mathrm{seeds}}<5$）。因此主文 Factor2 0.96 相对 HF_only 0.973 的微小差距，应理解为 **≤1–2 个边缘点的硬计数差异**，**不是**整体回归变差。本图仅可视化 seed-mean / std，**不改写**冻结表。

## 文件

- `outputs/results/protocol_W_parity_ensemble_points.csv`
- `outputs/figures/fig2c_protocol_W_parity_ensemble.png/.pdf`
- `outputs/jcp_submission/figures/`（同步副本）
- Fig.2 (a)(b) 仍为 `fig2_protocol_W_metrics.*`；(c) 为本文件独立面板，见 `outputs/figures/FIGURE_CAPTIONS.md`。
