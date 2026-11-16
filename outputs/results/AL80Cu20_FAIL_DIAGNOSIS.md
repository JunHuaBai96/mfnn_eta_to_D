# Al80Cu20 LOGO 全挂诊断报告

日期：2026-10-15（UTC+8）  
数据：`data/melt_diffusion_data_from_xiaobai.csv`（与 `melt_diffusion_data.csv` 相同，161 行）  
折预测：`outputs/logo_alcu_folds/Al80Cu20/test_predictions.csv`（自用户机同步副本）  
约束：只分析、不重训、不改训练表、未引入 Kozlov HF η。

---

## 一句话结论

**主因不是成分 OOD，也不是 η 质量，而是同一 `comp_group=Al80Cu20` 内混入了两套物理上不可互换的 D 标签：Zhang Cu-tracer（约 2.3–4.9×10⁻⁹）与 inter/interdiffusivity（约 7–8.9×10⁻⁹）。**  
留出该组时，训练邻域（尤其 `Al81.3Cu18.7`、`Al81Cu19`）几乎全是 **inter 量级**；三模型都系统性预测到 ~8–14×10⁻⁹，于是对 10 个 tracer 点全面高估 2.5–3.4×，仅对 2 个 inter 点表现良好。整体 MAPE≈133–206%、Factor2=2/12≈0.167 由此而来。

---

## 1. Al80Cu20 组内清单（证据）

| sample_id | fid | diff_type | T_K | D (×10⁻⁹) | η (Pa·s) | 来源要点 |
|-----------|-----|-----------|-----|-----------|----------|----------|
| R029 | HF | **inter** | 983 | **7.00** | 0.001801 | Chen Fig.6a 数字化（±~20%） |
| R300 | HF | **tracer** | 983 | **2.35** | 0.001801 | Zhang Arrhenius 加密（D0=1.3e-7, Q=0.34 eV） |
| R017 | HF | tracer | 1000 | 2.51 | 0.001752 | Chen Fig.4b / Zhang |
| R327 | HF | **interdiffusivity** | 1023 | **8.90** | 0.001691 | Geng 2014 冷却修正 DBol |
| R301–R306, R018, R019 | HF | tracer | 1025–1200 | 2.77–4.85 | Schick xCu=0.2 | 同一 Zhang Arrhenius 网格 |
| R035 / R050 | LF | tracer Cu/Al | **1573** | 15.71 | 0.00095 (Plevachuk→Sutherland) | 仅高温 LF，远离 HF T 窗 |

- **HF n=12，LF n=2**（另有 `Al80Cu20_Kozlov` LF 不在本组）。  
- **同温冲突（|ΔT|<5 K）**：
  - 983 K：`R029 inter / R300 tracer = 7.00 / 2.35 ≈ **2.98×**`（η 完全相同）
  - ~1023–1025 K：`R327 interdiffusivity / R301 tracer = 8.90 / 2.77 ≈ **3.21×**`
- 组内 HF：`Dmax/Dmin = 3.79`；**同温最大比 2.98** —— 在全部 Al–Cu HF 组中同温冲突最严重（其它组同温比均为 1.0）。
- Zhang 系列相对 Arrhenius 公式误差 <0.002% → R017–R019、R300–R306 是**同一条 Arrhenius 的加密点**，不是独立实验重复。
- η：Schick 2012 Table1 **exact xCu=0.2**（R327 有完整 provenance；R300 系列同规则配对）。**无 Kozlov HF η。**

---

## 2. 折预测残差：Factor2=0.167 的精确含义

来自 `test_predictions.csv`（LOGO holdout=Al80Cu20）：

| 子集 | n | MFNN MAPE% | MFNN Fac2 | 平均 pred/true |
|------|---|------------|-----------|----------------|
| **inter + interdiffusivity**（R029, R327） | 2 | **6.6** | **1.00** | ~1.0 |
| **tracer**（Zhang 10 点） | 10 | **188.4** | **0.00** | **~2.88** |
| 全组 | 12 | 158.1 | 0.167 | — |

LF_only / HF_only 同样：**仅 R029、R327 落在 Factor2 内**；10 个 tracer 全部高估。

| 模型 | 全组 MAPE% | Fac2 | tracer 平均 pred/true | inter 两行 MAPE% |
|------|------------|------|----------------------|------------------|
| LF_only | 133.0 | 2/12 | 2.57 | 14 / 10 |
| HF_only | 206.5 | 2/12 | 3.44 | 30 / 13 |
| MFNN | 158.1 | 2/12 | 2.88 | **7 / 6** |

**系统性偏差：高估 tracer，不低估；几乎与 T 无关（全温度段 ratio≈2.6–3.2）。**  
MFNN 在两个 inter 点上甚至优于/接近 LF，说明网络并非“坏掉”，而是**学到了邻域的 inter 尺度，无法同时拟合组内冲突标签**。

---

## 3. 为何三模型都挂（机制）

### 3.1 特征不含 `diff_type`

`data.py` / `build_feature_matrix` 的 12 维特征为：  
`T, 1000/T, η, log10(η), x_Al…x_Si, r_diff`。  
**不区分 tracer / inter / impurity。**  
因此 R029 与 R300 在特征空间几乎重合（同 T、同成分、同 η），却要求网络输出相差 ~3× 的 `log10D` —— 组内本身不可拟合；留出后更只能跟训练邻域走。

### 3.2 训练邻域是 inter 主导

Hold-out Al80Cu20 后，Al–Cu HF 训练组 `x_Cu∈[0,0.3]`，**最近邻**：

| 邻组 | x_Cu | n | D 中位 ×10⁻⁹ | 类型 |
|------|------|---|--------------|------|
| Al81.3Cu18.7 | 0.187 | 9 | **10.4** | **全 inter** |
| Al81Cu19 | 0.187 | 1 | 7.5 | inter |
| Al82.9Cu17.1 | 0.171 | 3 | 11.8 | tracer（Dahlborg，量级仍偏高） |
| Al75Cu25 | 0.250 | 3 | 10.5 | tracer |
| Al85Cu15 | 0.150 | 1 | 7.2 | inter |

Al80Cu20 的 **tracer 中位 ≈ 3.7×10⁻⁹**，比最近邻 inter 低约 **2.5–3×**。  
模型外推到 x_Cu=0.2 时，自然落到 ~8–12×10⁻⁹（与邻域一致）→ 对 Zhang tracer 全挂、对 R029/R327 却准。

### 3.3 不是成分 / T OOD

- `x_Cu=0.2` 落在训练 HF 的 `[0, 0.3]` 内，距 Al81.3 仅 Δx≈0.013。  
- HF T∈[983,1200] ⊂ 训练 T∈[973,1373]。  
→ **排除“成分极端 / T 窗外”作为主因。**

### 3.4 不是 η 坏

- 同组同 T 的 R029 与 R300 **η 相同**，D 仍差 3× → 冲突在 **D 标签类型**，不在 η。  
- Schick exact xCu=0.2 为诚实实验粘度配对。  
- Sutherland 物理基线相对 Al80 **tracer** MAPE 中位 ~490%（高估 ~5–7×），相对 **inter** 约 105–142% —— 也说明物理 LF 更接近 inter/自扩散尺度，与 Zhang Cu-tracer 尺度本就不匹配。

### 3.5 LF 额外弱点（次要）

组内仅有的 2 条 LF 在 **1573 K**，与 HF 窗 [983,1200] 差 370+ K；且 R035/R050 的 Cu/Al tracer D 被写成同一 Sutherland 值。  
LF_only 无法在组内提供与 Zhang tracer 对齐的低频监督 → 与 HF_only/MFNN 同向失败。

---

## 4. 文献混合与标签语义

| 来源簇 | 点 | 物理量 | 典型 D@~1000 K |
|--------|----|--------|----------------|
| Zhang / Chen Fig.4b | R017–R019 + R300–R306 | **Cu tracer / self-D** | ~2.5×10⁻⁹ |
| Chen Fig.6a | R029 | **interdiffusivity**（数字化） | 7×10⁻⁹ |
| Geng 2014 | R327 | **Boltzmann 修正 interdiffusivity** | 8.9×10⁻⁹ |

把三者塞进同一 `comp_group` 且用同一回归头，等于要求一个标量 D(x,T,η) 同时拟合两种不可互换的扩散系数。  
**相邻组 `Al81.3Cu18.7` 又是 Zhang inter Arrhenius（D0=3.7e-7, Q=0.33 eV）**，与 Al80 的 tracer Arrhenius（D0=1.3e-7）本就差一个 D0 因子 ~2.8 —— 与观测到的系统性高估比一致。

---

## 5. 根因排序（最可能 → 较次要）

1. **组内 / 邻域的 tracer vs interdiffusivity 标签冲突（主因）**  
   同温 D 差 ~3×；Factor2 仅命中 2 个 inter 点；邻域 Al81.3 全是 inter 量级。  
2. **特征不编码 diff_type**  
   冲突标签在特征空间不可分。  
3. **Al80Cu20 以 Arrhenius 加密 tracer 为主（10/12）**  
   折指标被多数 tracer 点主导；若只评 inter 两行，MFNN MAPE≈6.6%。  
4. **LF 与 HF 的 T 错位 + Sutherland 对 tracer 尺度偏差（加重 LF/MFNN 残差）**  
5. **成分 OOD / η 质量 / 随机 seed** —— **证据不支持为主因**。

---

## 6. 论文可用的修复选项（不改“诚实 η”原则）

按推荐优先级：

| 选项 | 做法 | 对论文的影响 |
|------|------|--------------|
| **A. 拆标签（强烈推荐）** | 将 Al80Cu20 拆成 `Al80Cu20_tracer` 与 `Al80Cu20_inter`（或全局按 `diff_type` 分任务/分头）；LOGO 按子组或只留一种类型 | 消除同组冲突；G 指标可解释 |
| **B. 加权 / 分层报告** | LOGO 汇总时按 `diff_type` 分层；或对加密 Arrhenius 点降权（同一 D0,Q 的网格点不当 10 个独立样本） | 避免 10 个相关点淹没 2 个 inter 点 |
| **C. 特征加 diff_type one-hot** | 在 X 中加入 tracer/inter/impurity | 允许网络学两种尺度（需足够两边样本） |
| **D. 剔除冲突点做消融** | 报告：去掉 R029/R327 或去掉 Zhang 加密后的 LOGO | 作为敏感性分析，证明失败来自标签混合 |
| **E. 不把 Al80Cu20 折当主结论** | 主文用协议 W；G/LOGO 注明本折失败机制 | 诚实表述，避免“G≈20%”误读 |
| **F. 勿用 Kozlov 填 η “拯救”本折** | 本折失败与 η 无关 | 保持 provenance |

**不建议**：仅为拉低 MAPE 而删掉整折且不解释；或把随机 seed G 的 ~20% 写回主结论。

---

## 7. 与其它“差折”对照（简）

- **Al70Cu30**（n=2）：HF_only 爆炸（MAPE~10⁴%），主因更像高 Cu + 稀少样本 + inter 端点，与 Al80 的“组内双标签”机制不同。  
- **Al81.3Cu18.7**（n=9，全 inter）：LF 反而最好 —— 说明单一类型、与物理尺度更一致时，外推可以正常。  
→ 进一步支持：**Al80 独特之处是 tracer+inter 混装 + 邻域 inter 主导。**

---

## 8. 文件与复现

- 本报告：`/workspace/mfnn_eta_to_D/outputs/AL80Cu20_FAIL_DIAGNOSIS.md`
- 数据：`data/melt_diffusion_data_from_xiaobai.csv`
- 折预测：`outputs/logo_alcu_folds/Al80Cu20/test_predictions.csv`（用户机）；箱内副本 `outputs/logo_alcu_folds_Al80Cu20_test_predictions.csv`
- LOGO 总表：`outputs/LOGO_AlCu_summary.csv`（用户机 / 附件）

分析命令摘要：按 `comp_group==Al80Cu20` 过滤；同温 D 比；与邻组 D 中位对比；按 `diff_type` 拆 `test_predictions` 的 MAPE/Factor2。
