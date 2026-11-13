# BrainOmni：研究问题、架构与训练逻辑

> 版本：2026-11-13 / 论文笔记 v0.1。正文基于已保存原文及公开评测；尚未完成代码逐层核验或本地复现。统一记号见[阅读约定](../process/文档维护与阅读约定.md)。

## 研究出发点

EEG与MEG传感器布局、类型和方向不同，单靠统一通道名称难以建立共同表示。作者希望先将不同传感器测量压缩到共享的潜在源表示，再在这一表示上学习可迁移的离散token模型。

## 从输入到输出的架构

第一阶段是BrainTokenizer。

- SEANet式时间encoder提取各传感器的时间特征 $Z_{time}$。
- Sensor Encoder编码三维位置、方向和类型，产生传感器embedding V。
- 一组可学习query执行cross-attention：K由时间特征和传感器信息结合形成，V侧使用时间特征，将可变C个传感器压缩为固定 $C'$ 个潜在源，输出约为 $B\times C'\times W\times D$。
- 残差向量量化RVQ逐级量化剩余误差，获得离散码。
- 重建器从量化的潜在源恢复传感器特征，再经时间decoder重建信号。

第二阶段在这些离散表示上训练BrainOmni骨干，通过掩码预测学习潜在源之间的时空关系。与直接对观测通道做Transformer相比，tokenizer已完成可变传感器到固定潜在源的变换。

“潜在源”是模型学习到的变量，不能直接解释为已完成物理可识别的源定位。

## 训练目标与阶段

Tokenizer损失结合时域、频域、相关性和量化约束；第二阶段预测离散码，使用分类式目标。原文比较EEG-only、MEG-only与联合预训练，并消融传感器embedding。需分别评估物理元数据、通道压缩和额外模态的作用，赛事官方EEG语料不能直接复制联合语料收益。

## 实验告诉了我们什么

OmniEEG跨被试LP正文将其列为平均排名第一；原论文提供传感器编码和EEG/MEG联合训练消融。NeuralBench首版未纳入。

这些结果的协议和具体源表见[评测证据](../benchmarks/评测证据与可比性.md)。整模型优于另一模型，只能支持该完整设置下的比较；模块作用需要相应消融。

## 局限和仍需核对的问题

传感器元数据及两阶段tokenizer增加实施成本；EEG/MEG联合语料的收益不等于本赛事仅官方EEG语料的收益。

实现核对时重点记录：预处理、实际token形状、位置表示、mask与loss的作用位置、checkpoint版本、可训练模块及读出接口。没有核验到的层数、配置或实现差异不补成确定事实。

## 原文与证据

- [BrainOmni（NeurIPS 2025，核对 arXiv v1）](https://arxiv.org/html/2505.18185v1)：§2；Tables 2、5、6、8。
- [OmniEEG-Bench（arXiv v1，预印本）](https://arxiv.org/html/2606.00815v1)：§3–4；Supplementary Tables 4、5、7；附录 E、H。

- [原始资料目录](../../research/reve_route_20261113/sources/)
- [返回论文索引](README.md)
