# G1-F Long 首轮执行登记

2026-10-14，查看任何 Long 模型输出与闭环结果前登记。问题是：在本轮 LIBERO-Long 开发协议中，增加未来视觉状态监督是否改善视觉 token 剪枝。Spatial 负结果保留；即使 Long 上出现收益，也不等于已证明此前由任务难度限制。

## 固定资产与对照

- Long 基座为官方 [OpenVLA-OFT LIBERO-10](https://huggingface.co/moojink/openvla-7b-oft-finetuned-libero-10)，revision `95220f9a3421a7ff12d4218e73d09ade830fa9a3`；Long 与 LIBERO-10 是该发布的同一 suite。
- 数据为 [modified_libero_rlds](https://huggingface.co/datasets/openvla/modified_libero_rlds/tree/6ce6aaaaabdbe590b1eef5cd29c0d33f14a08551/libero_10_no_noops)，revision `6ce6aaaaabdbe590b1eef5cd29c0d33f14a08551`，`libero_10_no_noops/1.0.0`。上游 metadata 声明 379 episodes、32 shards；需真实校验后才能作为可运行资产。
- A/B 从相同 seed17 初始 DIE 重新训练，不载入 Spatial 选择器。整个 Long VLA 冻结，梯度可经冻结 VLA 回传到软门控 DIE。
- A 为 0.5×完整教师动作 L1＋0.5×真实示范动作 L1；B 仅增加 0.1×未来视觉表征 MSE。未来头、表征投影与归一化方案沿用 Spatial 首轮，使用 Long 基座的冻结特征及动作归一化统计。

机器可读设置：[g1_future_long_v1.json](../configs/experiments/g1_future_long_v1.json)。仍为 100 次更新、有效 batch8、90 train 窗口、60 validation 窗口；每视角保留64 tokens，未来跨度8次实际执行的保留控制动作。相同初始化、训练顺序、门控、验证频率和最小硬验证 teacher L1 选模；不做超参数搜索。部署移除未来头，一次硬 Top-k、一次 packed VLA 前向。

## 数据与跨度审计

先清点所有 episode 的内容身份和元数据，按完整 episode、任务分层、seed17 固定 70/15/15 train/validation/test。划分清点只作元数据/压缩内容身份读取；test 图像不解码、不送模型、不用于决策。选定每任务3条 train（seed117）与2条 validation（seed517），各取首/中/末合法起点；90/60 的样本数不能用重复尾帧凑齐。

窗口为 `obs[t] + executed_actions[t:t+8] → obs[t+8]`，全部来自同一轨迹；不足跨度窗口排除并记录。原 no-op 重放执行前跳过空动作，8表示保留控制动作数，不冒充原始时间戳。未来图像只用于 detached target；实际动作只供训练期未来头，不能进入部署选择器。

对已选 train/validation 窗口记录轨迹长度及8步占比、机器人末端位置/姿态表示变化、夹爪状态变化、两视角当前到未来的图像变化。分开说明哪些量是数值代理；不把像素变化或机器人状态变化直接当成对象状态、子任务完成或语义阶段切换。保持原预测跨度，不根据这些诊断调整配置。

## 在结果前固定的开发评测

固定 LIBERO 源码 `8f1084e3132a39270c3a13ebe37270a43ece2a01`、OFT 源码 `e4287e94541f459edc4feabc4e181f537cd569a8`。选择 `libero_10` 的任务索引 **0、3、5**，仅按预定索引选取，不根据模型表现挑任务。任务名、源文件与签名见 [任务登记](../configs/manifests/long_initial_states_v1/development_tasks.json)。

每任务官方50个初态按固定 seed417/原身份规则划为10开发、40封存最终初态；只运行已登记的10开发初态。比较完整模型、A、B，共 **30配对初态、90条rollout**，统一环境seed0、等待10步、动作chunk8。Long 最大控制步使用固定官方 OFT 的 **520**（`run_libero_eval.py` 的 `LIBERO_10` 定义），不误用 Spatial 的220。

先完成 Long 自己的原始输入/官方 dense 输出一致性检查，再验收梯度、无信息泄漏、冻结参数及硬 packing。只有这些工程验收通过才执行100步训练；不把 Spatial G0 或 F01 报告当作 Long 验收。

主指标为配对闭环成功数与逐任务结果；同时报告硬剪枝 teacher/示范动作误差、A/B 保留集合交集占比和全部登记 GPU 成本。未来预测误差与跨度变化只作诊断。本轮不新增专门延迟实验，不引入均匀剪枝、仅未来监督或新的鲁棒性矩阵。

## 结束规则

无论是否有收益，首轮90条开发评测完成后汇报，**不自动扩大 seed、数据、预算或模块，也不开启 test**。出现工程失败时只做有界修复并保留失败成本；不得为了提高成功率更换任务、初态、选模指标或时长上限。

Long 上的增量是本次配置在这3个开发任务上的证据；任务套件、VLA基座和示范数据同时变化，无法据此把 Spatial 与 Long 的差别唯一归因于任务难度。
