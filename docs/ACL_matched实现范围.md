# ACL matched adaptation 骨架

2026-10-14。状态：**CPU 合成检查通过，尚未训练或复现正式基线**。实现位于 [`src/cti_vla_baselines/acl_matched.py`](../src/cti_vla_baselines/acl_matched.py)，独立于冻结的 CTI/G1/D1 代码。方法 ID 固定为 `acl-matched-teacher-cti-conditions-staged-adaptation-v1`，不使用 `acl-native` 名称。

官方来源固定为 `du-owen/VLA-ACL@40b7a7a17f2f5a15acab0564ba1e304bcf6d150d`；本地源码干净。沿用并逐函数核对 [LapSum/黑图门控](https://github.com/du-owen/VLA-ACL/blob/40b7a7a17f2f5a15acab0564ba1e304bcf6d150d/src/openvla-oft/prismatic/training/scorer_train_utils.py#L68)。作者使用投影前视觉 Transformer scorer 与默认 0.5 GT + 0.5 teacher；本适配使用 CTI 条件 scorer、teacher-only loss 和当前集合 S，这是明确的受控变体。完整匹配约束见 [基线协议](基线复现与匹配协议.md)；源码调查见 [readiness](../results/baselines/readiness.json)。

已经实现：

- 每相机 LapSum 的阈值求解及官方 VJP；黑图门 `sX + sqrt(1-s²)b` 保留作者 detached 黑图系数。稳定 CDF 写法仅避免未选中指数分支溢出，普通输入已与固定作者函数比较 forward/VJP。
- `FrozenDifferentiableOFTPolicy` 复用原文本构建、`OFTPackedBatch`、原位置编号和动作切片；只开放输入特征梯度，VLA/projector/head 保持 frozen/eval。原 CTI teacher 的 no_grad 方法未改动。
- `join_cached_observation` 读取已验证 G2 缓存，绑定 raw/black、条件、prompt、完整教师动作、版本和原 observation 文件 SHA；按真实 train episode 和固定 obs-S 检查，拒绝其他 split。raw 特征必须经过冻结 projector 后与 CTI 缓存一致。
- `matched_loss`、`train_matched_step` 只优化同一个 `ConditionalInfluenceEstimator` 类；16 个 set-record 梯度累积、AdamW 参数必须恰为 scorer 参数。`matched_epoch_batches` 保留 CTI 每观测两条集合记录及相同 Python shuffle 序列。正式配置仍须固定与 CTI 相同的 hidden=256、种子、学习率、训练轮数和选模频率。
- `select_matched` 直接复用共同分阶段硬选择：512→256→128→64、相机等额、原索引打破平分。软训练的物理长度仍为当前 S，软预算只有 S 的一半；不能把训练序列长度当成推理压缩率。

9 项 CPU 用例通过：数学 forward/VJP 与数值差分、detached 门系数、冻结参数/输入梯度、原位置和动作 parity、语言/proprio/集合条件参数梯度、补充缓存身份、原始特征投影、预算和 optimizer 守卫。测试仅创建合成数据与小模型，不是模型训练结果。上游源码存在时额外执行 pinned 函数对照；仓库分发不包含 `external` 时该项明确跳过。

独立复现仍缺以下步骤，当前不能启动正式 ACL 训练：

1. **服务器 raw/black 特征生产器。**当前 G2 仅保存 projected features。必须用同 checkpoint、真实双视角与预处理产出 raw features，以及真实全黑 RGB 经相同视觉流水线得到的 black features；不能用零向量、相机均值或 projected 黑图替代。当前 receipt 只能绑定提供的 tensor，不能证明它来自正确黑图变换。
2. **真实 OFT 梯度与数值验收。**合成骨干证明接口保留梯度和位置，但尚未在固定 BF16 OFT 上验证 dense/packed parity、非零 scorer 梯度、完整 VLA 参数无梯度及 GPU 数值稳定性。输入 API 的私有文本 helper 依赖当前固定源码。
3. **正式训练与恢复 driver。**需服务器限定 checkpoint、不可变权重前后 hash、实际 source/runtime、完整 906 train/189 validation、统一 task×stage macro 选模、优化器/RNG 恢复和各 seed。温度调度实现存在，结束步数必须在运行前登记；此骨架不代替完整 driver，也不保存任何 checkpoint。
4. **完整成本与部署 adapter。**现有计数器仅记录进程内 student/projector/backward/optimizer 工作，未提供抗中断 journal、checkpointing 重算计数或完整 GPU 账单。共享教师缓存须同时报告增量与独立运行成本。部署必须接共同 raw observation→action 评测与 profiler；缓存特征 forward 的时间不能当端到端延迟。
5. **原生 ACL 单独复现。**作者 scorer/权重、原生动作目标与控制器仍须隔离环境和不可变 overlay 独立验证；其公开训练成员未知，不能声称遵循本项目的 episode 划分。本 adaptation 不替代 native 行。

没有安装新依赖、下载/复制模型权重、提交 GPU 或改动冻结实现。许可证及来源随独立模块保存；已完成内容不预写成功率、速度或成本收益。
