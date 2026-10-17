# CTI-VLA

Counterfactual Token Influence for Efficient Vision-Language-Action Policies。

CTI-VLA 是独立研究项目，项目根目录为 F:/CTI-VLA。当前主线 G1-F 检验未来状态辅助监督能否改善视觉 token 剪枝：冻结 OpenVLA-OFT，训练轻量 DIE 选择器，允许软门控梯度经过冻结 VLA；未来预测头仅在训练使用。模型权重及训练 checkpoint 保存在服务器。

当前执行[正式主实验 formal_main_v2](docs/正式主实验规划.md)：四套件、总256／128／64 tokens、seed17／23／41、A/B共72组，各5000更新。按[并行登记](docs/正式并行执行登记.md)最多8个独立单GPU作业同步推进；四套件自身GPU验收均已通过。分段结果与完整完成组数见[最新进度](docs/实验进度.md)。全部checkpoint及四套件开发结果冻结并通过root全局release后才开放最终初态，目前仍封存。

2026-10-15：Long seed17/23/41有界对照全部完成，动作监督A与动作＋未来监督B的闭环成功数依次为26/27、26/27、27/29（每组30）；三seed均值87.78%/92.22%，B−A为+4.44个百分点。相同30个开发初态跨seed重复，不能算90个独立初态；B离线动作误差均略差。见 [三种子实验结论](docs/G1-F-Long三种子实验结论.md)。本轮停止，不自动扩大，test封存；这些是开发结果，不是正式test或任务难度机制证明。

历史路线保留：G0工程验收通过；原逐token删除标签G1及小步长诊断未通过继续条件，暂缓扩大。Spatial G1-F首轮未观察到未来监督增量。完整历史见 [实验进度](docs/实验进度.md)，旧DIWA数字仍只作为历史资料。

## 阅读入口

- [研究方案](docs/研究方案.md)：研究问题、方法与实验设计。
- [完整实验计划](docs/完整实验计划.md)：分阶段实验、基线与消融、数据隔离、闭环统计、测速成本和停止条件。
- [实验进度](docs/实验进度.md)：当前阶段、实际作业与验收证据；未完成的实验单独标明。
- [Long三种子结果](docs/G1-F-Long三种子实验结论.md)：逐seed/任务成功率、配对分析、动作误差、token重合及完整新增成本。
- [迁移与运行](docs/迁移与运行.md)：当前实现、数据模型来源及运行入口。
- [模型审计](docs/迁移审计_packing.md)、[数据审计](docs/迁移审计_data.md)、[方法审计](docs/迁移审计_method.md)：修正与来源 SHA256。
- [工作对比与方法解释](docs/工作对比与方法解释.md)：软门控、真实删除与集合条件。
- [项目规范](AGENTS.md)；[DIWA 历史审计](docs/历史参考/DIWA_工作审计_2026-10-11.md)。

## 本地验证

```bash
python -m pip install -e ".[test]"
python -m pytest -q -p no:cacheprovider
python scripts/smoke_conditional_pipeline.py --output results/smoke/conditional_synthetic.json
```

最后一条使用合成小模型，验证接口、signed 标签、缓存与训练边界，不代表真实机器人实验。

## 实现边界

- 统一原序 gather、原位置编号、attention mask 和动作切片；OFT 必须使用固定的双向 SDPA fork。
- 当前DIE只读取当前观测、语言和归一化proprio；部署一次硬Top-k，两视角等额，总256／128／64 tokens，未来头移除；128为主要比较预算。
- 当前特征、完整教师动作与未来目标detach；软门控损失允许经过冻结VLA回传至DIE，VLA参数不更新。实际执行动作只供训练期未来头使用，未来信息不得进入部署输入。
- 旧signed删除标签回归及分阶段Top-k保留为历史实现，暂缓扩大；旧标签缓存不兼容均值替换标签。
- LIBERO 按完整轨迹内容 ID 划分，覆盖时间早中晚。时间阶段不等同于抓取/接触等语义阶段。
- G1-F小规模开发结果独立归档，不充当正式主表。当前授权限于formal_main_v2已登记矩阵，最终评测须先满足全局release；不扩大方法、任务、预算或超参数搜索。

## 目录

| 路径 | 用途 |
|---|---|
| docs/ | 方案、调研、方法说明及规范补充 |
| docs/历史参考/ | DIWA 历史材料；不作为 CTI-VLA 已完成结果 |
| src/cti_vla/ | CTI-VLA 独立实现 |
| configs/ | 实验配置、数据划分、服务器模型来源与版本记录 |
| scripts/ | 数据处理、标注、训练和评测入口 |
| tests/ | 必要的实现与行为测试 |
| data/ | 非权重数据、特征缓存和教师标签 |
| results/ | 日志、指标、图表和实验总结 |

F:/DIWA 保留历史工程。CTI-VLA 的新资料、规范和代码统一在本目录维护，不再沿用“DIWA v2”的名称。
