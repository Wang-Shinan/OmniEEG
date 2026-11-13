# EEGPT：研究问题、架构与训练逻辑

> 版本：2026-11-13 / 论文笔记 v0.1。正文基于已保存原文及公开评测；尚未完成代码逐层核验或本地复现。统一记号见[阅读约定](../process/文档维护与阅读约定.md)。

## 研究出发点

这里阅读的是NeurIPS2024的对齐型EEGPT。作者认为，低信噪比EEG的原始波形重建可能诱使模型学习不稳定细节，希望通过较完整上下文产生的潜在表征，为掩码输入提供更抽象的监督。

## 从输入到输出的架构

模型包含局部时空embedding、context encoder、predictor、目标分支与reconstructor。

EEG按通道和时间形成patch。局部embedding结合通道身份和时间片段；分层网络分别处理空间聚合与时间关系。context encoder仅接收可见部分，predictor利用可见表示和位置信息预测被遮挡部分的潜在表示。目标分支从较完整输入产生对齐目标；其参数通过动量方式更新，目标侧停止直接反向传播。

重建分支另外恢复信号，避免表示只满足对齐而完全脱离原始输入。因而数据流包含两种监督：对原始信号的重建，以及对目标encoder表示的预测。

$$\mathcal L=\lambda_a\mathcal L_{align}+\lambda_r\mathcal L_{recon}.$$

这里的公式只是损失组成示意，系数及归一化应以论文/实现为准；不可把它描述成单独的纯JEPA或普通单路MAE。

## 训练目标与阶段

预训练后冻结或适配encoder，并使用任务侧适配组件与读出头。公开checkpoint规格包含256Hz、58通道、4秒配置；本赛200Hz输入如何转换必须明确。后续代码级核验应定位context/target的更新、mask的空间和时间选择以及所谓linear probing中实际可训练的模块。

## 实验告诉了我们什么

AdaBrain跨被试表：EEGPT在BCI-IV-2A为25.81%，LaBraM54.98%；EEGMAT61.66%，CBraMod88.89%。说明原论文的优点不能无条件转移到不同适配协议。

这些结果的协议和具体源表见[评测证据](../benchmarks/评测证据与可比性.md)。整模型优于另一模型，只能支持该完整设置下的比较；模块作用需要相应消融。

## 局限和仍需核对的问题

公开checkpoint有58通道/256Hz/4秒规格，包装适配重要；其线性探测实现含适配组件，不能与其它模型的纯线性头混为一谈。

实现核对时重点记录：预处理、实际token形状、位置表示、mask与loss的作用位置、checkpoint版本、可训练模块及读出接口。没有核验到的层数、配置或实现差异不补成确定事实。

## 对本项目的启发

若频谱/读出改进仍不足，才将teacher表征预测作为后备目标；本轮不叠加EMA教师以增加变量。

上述启发是待验证判断。当前研究问题见[REVE改进假设](../research/REVE改进假设.md)，不能把本笔记中的作者模型和我们的改造方案视为同一个模型。

## 原文与证据

- [EEGPT: Pretrained Transformer…（NeurIPS 2024）](https://proceedings.neurips.cc/paper_files/paper/2024/file/4540d267eeec4e5dbd9dae9448f0b739-Paper-Conference.pdf)：§2、附录；BINE022/EEGPT，对齐型 EEGPT。
- [AdaBrain-Bench 官方结果表](https://github.com/Jamine-W/AdaBrain-Bench)：Cross-Subject Transfer；当前表未包含 REVE。

- [原始资料目录](../../research/reve_route_20261113/sources/)
- [返回论文索引](README.md)
