# UniMind：研究问题、架构与训练逻辑

> 版本：2026-11-13 / 论文笔记 v0.1。正文基于已保存原文及公开评测；尚未完成代码逐层核验或本地复现。统一记号见[阅读约定](../process/文档维护与阅读约定.md)。

## 研究出发点

不同任务需要从同一EEG表示中提取不同信息。作者将瓶颈定位在EEG与LLM之间的连接器：一个固定聚合方式可能压掉任务相关模式，因此设计时空分离的查询与自适应query选择。

## 从输入到输出的架构

输入先经预训练LaBraM，得到 $E\in\mathbb R^{B\times(CN+1)\times D_e}$，含class token。

**NLC连接器**分别重排token以便沿时间和空间访问。时间query在每个通道的时间序列上cross-attend，输出 $B\times n_t\times C\times D_e$；空间query在每个时间位置的通道集合上cross-attend，输出 $B\times n_s\times N\times D_e$。两者展平、拼接class token，再映射到LLM的embedding维度。

**TQS**为时间和空间各维护query pool。router根据EEG embedding产生分数，以Top-K选择输入相关query，并与静态query拼接。这里的“task-aware”由输入表示驱动，不等于用真实测试标签选择分支。

神经embedding与分隔符、任务指令拼接后交给冻结InternLM2.5-7B生成标签文本。LaBraM、连接器与router的可训练设置须和被冻结的LLM区分。

## 训练目标与阶段

使用条件生成的交叉熵进行多任务训练。连接器与query选择均有同文消融。若移除LLM、只把query用于REVE读出，这是我们的新实验条件，不能沿用原论文的提升数字。作者版本还明确指出完全未见被试和新任务泛化未得到充分研究。

## 实验告诉了我们什么

同文消融平均BACC为65.77→68.38（NLC）→70.67（NLC+TQS）。但作者明确未研究完全未见被试与新任务；不能直接支持赛事的跨被试收益。

这些结果的协议和具体源表见[评测证据](../benchmarks/评测证据与可比性.md)。整模型优于另一模型，只能支持该完整设置下的比较；模块作用需要相应消融。

## 局限和仍需核对的问题

完整系统依赖外部预训练LLM和EEG编码器；7B配置资源较重。模块消融没有直接证明移植到REVE且移除LLM后仍然有效。

实现核对时重点记录：预处理、实际token形状、位置表示、mask与loss的作用位置、checkpoint版本、可训练模块及读出接口。没有核验到的层数、配置或实现差异不补成确定事实。

## 原文与证据

- [UniMind（核对 arXiv v1，引用该版本）](https://arxiv.org/html/2506.18962v1)：§2–3；Tables 1–3、7；Limitations。

- [原始资料目录](../../research/reve_route_20261113/sources/)
- [返回论文索引](README.md)
