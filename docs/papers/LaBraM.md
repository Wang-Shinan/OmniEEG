# LaBraM：研究问题、架构与训练逻辑

> 版本：2026-11-13 / 论文笔记 v0.1。正文基于已保存原文及公开评测；尚未完成代码逐层核验或本地复现。统一记号见[阅读约定](../process/文档维护与阅读约定.md)。

## 研究出发点

EEG数据量有限且格式不同，直接训练大模型缺乏统一学习目标。作者希望从跨数据集信号中建立神经词表，用离散目标降低直接波形重建的困难，并使骨干学习具有频谱意义的表示。

## 从输入到输出的架构

第一阶段训练神经tokenizer。EEG被切成逐通道时间patch，时间encoder产生连续向量；codebook将其映射为离散神经码。decoder预测patch的频谱信息，促使离散码保留可供频谱重建的内容。

第二阶段训练LaBraM。输入patch embedding与通道/时间位置表示结合；部分位置被mask。Transformer依据可见上下文，预测原tokenizer对这些位置产生的离散码，而不是直接回归每个原始采样点。

$$z_i=\operatorname{Quantize}(E_{tok}(x_i)),\qquad
\mathcal L_{mask}=-\sum_{i\in\mathcal M}\log p_\theta(z_i\mid x_{visible}).$$

第一式的tokenizer与第二阶段的骨干不是同一训练对象。下游取骨干表示，接任务头并按协议冻结或微调。

## 训练目标与阶段

神经词表通过频谱预测和量化约束训练；骨干的masked code prediction是交叉熵。需查codebook使用率、tokenizer预训练数据与下游重叠，以及固定导联词表对未知位置的处理。它在某任务获胜不能单独证明VQ胜过连续表征，还要控制数据和适配配方。

## 实验告诉了我们什么

NeuralBench平均排名4.39，接近REVE4.22；c-VEP87.600%对79.093%，image Top-5 87.650%对84.750%，SSVEP96.488%对96.071%。三类指标分别解释，不能混合。

这些结果的协议和具体源表见[评测证据](../benchmarks/评测证据与可比性.md)。整模型优于另一模型，只能支持该完整设置下的比较；模块作用需要相应消融。

## 局限和仍需核对的问题

原模型预训练语料、tokenizer及导联词表均可能影响结果；离散目标需要额外训练阶段，未证明优于其它连续目标。

实现核对时重点记录：预处理、实际token形状、位置表示、mask与loss的作用位置、checkpoint版本、可训练模块及读出接口。没有核验到的层数、配置或实现差异不补成确定事实。

## 原文与证据

- [LaBraM（ICLR 2024，核对 arXiv v1）](https://arxiv.org/html/2405.18765v1)：tokenizer、神经频谱量化、masked code prediction。
- [NeuralBench 官方逐任务结果，固定提交 fe31393](https://github.com/facebookresearch/neuroai/blob/fe31393affab2590e59b0a7e1457aad1a1da908e/docs/_static/neuralbench-results-data.json)：results；36 项 EEG 任务。
- [NeuralBench 官方模型参数与 mean_rank 数据](https://github.com/facebookresearch/neuroai/blob/fe31393affab2590e59b0a7e1457aad1a1da908e/docs/_static/neuralbench-model-scatter-data.json)：models。

- [原始资料目录](../../research/reve_route_20261113/sources/)
- [返回论文索引](README.md)
