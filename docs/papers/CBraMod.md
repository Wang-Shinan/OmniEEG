# CBraMod：研究问题、架构与训练逻辑

> 版本：2026-11-13 / 论文笔记 v0.1。正文基于已保存原文及公开评测；尚未完成代码逐层核验或本地复现。统一记号见[阅读约定](../process/文档维护与阅读约定.md)。

## 研究出发点

作者认为，EEG的空间依赖与时间依赖具有不同结构。将所有通道×时间patch平铺后统一做dense attention，没有显式区分这两类关系；固定绝对位置编码又不利于变化的输入布局。其出发点是把这种差异写入骨干结构。

## 从输入到输出的架构

输入 $X\in\mathbb R^{B\times C\times T}$ 被切为1秒patch，排列为通道×时间网格，而非立即丢掉两个轴。

1. **Patch encoder：**局部时域卷积提取波形模式，频域编码提供谱信息，两种表征共同形成patch embedding。时域编码器使用多层1D卷积、GroupNorm和GELU。时频融合的精确张量实现需对照代码核验。
2. **ACPE：**对 $H\in\mathbb R^{B\times C\times N\times D}$ 的通道—时间网格施加二维depthwise卷积，得到条件位置编码并加回H。卷积核在通道轴较长、时间轴较短，体现两轴的非对称设计。它依赖网格排列，不能自动等同于物理坐标不变性。
3. **空间attention：**固定某个时间patch，在C个通道之间计算关系。
4. **时间attention：**固定某个通道，在N个时间patch之间计算关系。
5. **合并：**两类attention并行分配不同heads，拼接后投影，再经过残差和前馈网络。多层堆叠后，两轴信息可以间接传播。

按注意力矩阵规模估算，两个轴分别计算的主要复杂度为 $O(NC^2+CN^2)$，对照全token注意力的 $O(C^2N^2)$。这是结构复杂度分析，不是实测加速比。

论文预训练配置为19通道、30秒、200Hz，共570个patch；骨干12层、200维、8个heads，空间与时间各分配一半。

## 训练目标与阶段

随机mask部分patch，通过重建头恢复被遮挡波形。预训练表示再用于下游任务适配。

重要消融包括预训练有无、数据清洗、时域/频域输入、位置编码形式和attention结构。空间/时间两路的合理性要结合这些对照看，不能仅从整模型的排名归因。

TUEG原始规模约27000小时，但过滤后实际训练数据约9000小时；记录“原语料规模”和“实际使用规模”时必须分开。

## 实验告诉了我们什么

NeuralBench：睡眠分期72.926% 对 REVE 71.181%；睡眠觉醒59.458% 对55.725%。OmniEEG 的部分情绪/SSVEP LP条目也更强，但与NeuralBench的设置不同。

这些结果的协议和具体源表见[评测证据](../benchmarks/评测证据与可比性.md)。整模型优于另一模型，只能支持该完整设置下的比较；模块作用需要相应消融。

## 局限和仍需核对的问题

不能由完整模型胜出认定单个attention模块有因果贡献；NeuralBench SSVEP表现远弱于REVE且离散度大，不能将其当成通用替代。

实现核对时重点记录：预处理、实际token形状、位置表示、mask与loss的作用位置、checkpoint版本、可训练模块及读出接口。没有核验到的层数、配置或实现差异不补成确定事实。

## 原文与证据

- [CBraMod（ICLR 2025，核对 arXiv v1）](https://arxiv.org/html/2412.07236v1)：Criss-cross、ACPE、时频输入及预训练消融。
- [NeuralBench 官方逐任务结果，固定提交 fe31393](https://github.com/facebookresearch/neuroai/blob/fe31393affab2590e59b0a7e1457aad1a1da908e/docs/_static/neuralbench-results-data.json)：results；36 项 EEG 任务。
- [OmniEEG-Bench（arXiv v1，预印本）](https://arxiv.org/html/2606.00815v1)：§3–4；Supplementary Tables 4、5、7；附录 E、H。

- [原始资料目录](../../research/reve_route_20261113/sources/)
- [返回论文索引](README.md)
