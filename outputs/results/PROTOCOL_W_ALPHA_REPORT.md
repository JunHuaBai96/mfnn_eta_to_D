# Protocol W MFNN $\alpha_1$, $\alpha_2$ 提取报告

只读 checkpoint，**未重训**。来源：`outputs/seed_wg_{0,1,2,42,123}/within_T/mfnn_checkpoint.pt`。

模型（`model.py`）：
$$y_H \approx \alpha_1\,(A[x,y_L]+b) + \alpha_2\,F_{\mathrm{nl}}(x,y_L).$$

## 逐 seed

| seed | $\alpha_1$ | $\alpha_2$ | `lin.weight`[$y_L$] | `lin.bias` |
|---:|---:|---:|---:|---:|
| 0 | 0.470874 | 0.626507 | 0.359007 | 0.101664 |
| 1 | 0.598942 | 0.631532 | 0.301596 | -0.274295 |
| 2 | 0.336369 | 0.708841 | -0.125291 | 0.018866 |
| 42 | 0.602101 | 0.637701 | 0.071454 | -0.348543 |
| 123 | 0.676134 | 0.657815 | 0.099586 | -0.084817 |

## 汇总（population std, ddof=0）

- $\alpha_1$ = **$0.5369\pm0.1200$**
- $\alpha_2$ = **$0.6525\pm0.0301$**
- 线性层对 $y_L$ 的权重（`lin.weight` 最后一列）： mean±std = $0.1413\pm0.1737$（$n=5$）。

## 线性混合 vs 非线性残差

五种子上 $|\alpha_2|$ 均值 (0.6525) > $|\alpha_1|$ 均值 (0.5369)，即 **非线性残差支路的混合权重更大**（仅指 $\alpha$ 标量，非支路输出范数）。

CSV：`outputs/results/protocol_W_alpha_table.csv`。
