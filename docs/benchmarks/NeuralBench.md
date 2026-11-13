# NeuralBench

版本：2026-11-13，基于已读取公开来源。

## 要解决的问题与评价对象

用官方逐任务数值定位REVE的相对弱项与强项，并找候选对照。

## 实验组织

共享FT配方，平均token＋线性头；同一个数据划分，3个训练随机种子；部分认知任务是同被试leave-concept-out。

## 与本赛事的关系

不等于赛事每个种子重新按被试8:1:1划分；不能将image Top-5或clinical-event宏F1当BACC；模型特定训练配方被省略。

## 阅读与复现检查点

记录数据集与任务定义、被试隔离、预处理、适配方式、调参预算、种子作用、指标及预训练重叠处理。相同数据集名称并不足以保证分数可比。

## 来源

- [NeuralBench 原论文（arXiv v1，预印本）](https://arxiv.org/html/2605.08495v1)。
- [NeuralBench 官方逐任务结果，固定提交 fe31393](https://github.com/facebookresearch/neuroai/blob/fe31393affab2590e59b0a7e1457aad1a1da908e/docs/_static/neuralbench-results-data.json)。

[逐项证据与协议边界](评测证据与可比性.md) · [返回索引](README.md)
