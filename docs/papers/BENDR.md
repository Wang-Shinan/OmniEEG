# BENDR：研究问题、架构与训练逻辑

> 版本：2026-11-13 / 论文笔记 v0.1。正文基于已保存原文及公开评测；尚未完成代码逐层核验或本地复现。统一记号见[阅读约定](../process/文档维护与阅读约定.md)。

## 研究出发点

作者借鉴语音自监督学习：先将高频采样的连续信号压缩成表示序列，再要求模型根据上下文预测被遮挡的局部表示，以利用大量无标签EEG。

## 从输入到输出的架构

卷积encoder对多通道EEG进行时间下采样，生成连续向量序列 $b_1,\dots,b_N$。该步骤已包含局部时间模式和通道混合。

部分向量位置被mask，Transformer contextualizer根据周围表示产生上下文化输出 $c_t$。在masked位置，模型需要让 $c_t$ 更接近真实 $b_t$，而不是从同序列采样的负例。

$$\ell_t=-\log\frac{\exp(\operatorname{sim}(c_t,b_t)/\tau)}{\sum_{b\in\mathcal N_t\cup\{b_t\}}\exp(\operatorname{sim}(c_t,b)/\tau)}.$$

它不是恢复原始波形的普通MSE自编码器，也不同于依赖VQ词表的离散token预测。下游可以使用不同部分的网络，必须说明是卷积表示还是完整contextualized表示。

## 训练目标与阶段

在预训练语料上优化掩码对比预测，再以任务标签适配。负例选择和局部卷积共同影响表征。论文与benchmark的参数规模差异可能来自采用不同网络子集，因此参数量和输出接口必须成对记录。

## 实验告诉了我们什么

NeuralBench病理检测81.753%对REVE78.044%，但整体平均排名10.08。不同文献中参数数目可能只计算卷积encoder或完整contextualizer，不应直接混用。

这些结果的协议和具体源表见[评测证据](../benchmarks/评测证据与可比性.md)。整模型优于另一模型，只能支持该完整设置下的比较；模块作用需要相应消融。

## 局限和仍需核对的问题

固定通道布局适配、较大完整模型和不同学习率会影响迁移；其局部优势不足以证明整体更优。

实现核对时重点记录：预处理、实际token形状、位置表示、mask与loss的作用位置、checkpoint版本、可训练模块及读出接口。没有核验到的层数、配置或实现差异不补成确定事实。

## 对本项目的启发

借鉴局部卷积和对比预测作为参照；本轮以轻量局部分支优先于完整BENDR复现。

上述启发是待验证判断。当前研究问题见[REVE改进假设](../research/REVE改进假设.md)，不能把本笔记中的作者模型和我们的改造方案视为同一个模型。

## 原文与证据

- [BENDR（Frontiers 2021）](https://pmc.ncbi.nlm.nih.gov/articles/PMC8261053/)：卷积表征与 masked contrastive prediction。
- [NeuralBench 官方逐任务结果，固定提交 fe31393](https://github.com/facebookresearch/neuroai/blob/fe31393affab2590e59b0a7e1457aad1a1da908e/docs/_static/neuralbench-results-data.json)：results；36 项 EEG 任务。
- [NeuralBench 原论文（arXiv v1，预印本）](https://arxiv.org/html/2605.08495v1)：§2.4、§2.6、§3，附录 C–F。

- [原始资料目录](../../research/reve_route_20261113/sources/)
- [返回论文索引](README.md)
