# CTI-VLA

Counterfactual Token Influence for Efficient Vision-Language-Action Policies。

CTI-VLA 是独立研究项目，项目根目录为 F:/CTI-VLA。冻结 OpenVLA-OFT，使用与部署相同的真实 token 删除生成集合条件标签，仅训练轻量选择器和条件编码器。模型权重及训练 checkpoint 保存在服务器。

2026-10-14：G0 工程验收通过，90 观测与 45 开发闭环完成，15 组官方 dense 配对误差为 0。主 G1 完成 90 观测诊断与 12 条教师选择路径；128-token 下分阶段教师落后于静态排序，当前方案 no-go，暂缓扩大标注/训练。事先登记的 3 观测小步长诊断也已完成，仍无稳定主预算优势，详见 [实验进度](docs/实验进度.md) 和 [首轮结论](docs/G1首轮实验结论.md)。尚无正式闭环成功率、加速或方法收益结论；旧 DIWA 数字只作为历史资料。

## 阅读入口

- [研究方案](docs/研究方案.md)：研究问题、方法与实验设计。
- [完整实验计划](docs/完整实验计划.md)：分阶段实验、基线与消融、数据隔离、闭环统计、测速成本和停止条件。
- [实验进度](docs/实验进度.md)：当前阶段、实际作业与验收证据；未完成的实验单独标明。
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
- 语言、归一化 proprio、相机/patch 位置和分视角集合摘要进入选择器；signed 回归、分相机分阶段 Top-k。
- 教师无梯度真实删除，训练仅消费 detached 特征；新标签缓存不兼容旧均值替换标签。
- LIBERO 按完整轨迹内容 ID 划分，覆盖时间早中晚。时间阶段不等同于抓取/接触等语义阶段。
- 标注调度、轻量训练恢复、选择器开发闭环和完整 observation-to-action profiler 已实现并经过 CPU 审计；G1 科学门槛未通过，尚未运行正式训练与训练后性能评测。

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
