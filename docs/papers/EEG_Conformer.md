# EEG Conformer：研究问题、架构与训练逻辑

> 版本：2026-11-13 / 论文笔记 v0.1。正文基于已保存原文及公开评测；尚未完成代码逐层核验或本地复现。统一记号见[阅读约定](../process/文档维护与阅读约定.md)。

## 研究出发点

将卷积擅长的局部时空模式与attention的长程关系建模结合，希望在保留EEG局部归纳偏置的同时捕获更长时间范围的信息。

## 从输入到输出的架构

前端先用时间卷积和跨通道空间卷积编码EEG，通过池化将高采样率信号压缩为token序列，再投影到Transformer的embedding维度。

Transformer对这些卷积token进行多头自注意力；残差、归一化和前馈层反复更新表示。token已由卷积提取，不能把这里的输入与REVE每通道的原始波形patch简单视为相同。

最后将序列表示送入分类模块。网络的局部前端、时间压缩程度和分类头均可能贡献成绩；要验证“attention有用”，需与同前端但更简单读出的模型比较。

原论文还提出Class Activation Topography用于分析分类相关头皮空间模式。可视化与脑区因果作用是不同层面的证据。

## 训练目标与阶段

原始方法以任务监督训练。比较时记录受试者划分、token数和数据增强，尤其不能把被试内高准确率与跨被试基础模型分数相减。实际实现的卷积核、池化步长和分类头维度尚需按官方代码核对。

## 实验告诉了我们什么

NeuralBench癫痫检测84.253%对REVE77.608%；mental imagery28.914%对25.581%。不要将mental imagery与官方motor imagery赛道直接等同。

这些结果的协议和具体源表见[评测证据](../benchmarks/评测证据与可比性.md)。整模型优于另一模型，只能支持该完整设置下的比较；模块作用需要相应消融。

## 局限和仍需核对的问题

其作者原表和赛事跨被试划分不同；整段压缩和分类头设置亦影响可比性。

实现核对时重点记录：预处理、实际token形状、位置表示、mask与loss的作用位置、checkpoint版本、可训练模块及读出接口。没有核验到的层数、配置或实现差异不补成确定事实。

## 原文与证据

- [EEG Conformer（TNSRE 2023，作者仓库）](https://github.com/eeyhsong/EEG-Conformer)：卷积 tokenization 与 Transformer；原论文 DOI 10.1109/TNSRE.2022.3230250。
- [NeuralBench 官方逐任务结果，固定提交 fe31393](https://github.com/facebookresearch/neuroai/blob/fe31393affab2590e59b0a7e1457aad1a1da908e/docs/_static/neuralbench-results-data.json)：results；36 项 EEG 任务。

- [原始资料目录](../../research/reve_route_20261113/sources/)
- [返回论文索引](README.md)
