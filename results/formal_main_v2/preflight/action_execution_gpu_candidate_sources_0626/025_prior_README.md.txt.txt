# 单 chunk 执行兼容验收候选（仅 CPU 准备）

此目录没有授予 GPU 运行、下游重新评测或最终集开放权限。根对话须先完成候选独立审计，再固定新登记文件、服务器发布路径及全部 SHA，最后才能提交一次工程作业。

固定 Long → Spatial → Object → Goal；每套件依次 dense、uniform128、A128 seed17、B128 seed17。task0 选择既有 development 面板最小 source index，分别为 0、3、5、7；面板文件和精确行均已哈希登记。A/B 使用各套件已完成 5000 步、11 节点选模且有服务器文件 SHA 证明的 checkpoint。不会读取官方全 50 初态文件或 final 状态。

每格独立设 runtime seed17、env seed0，调用冻结原执行循环（仅通过已审 v2 scope 去除旧动作范围断言），等待10步，预测一次动作 chunk，最多执行8个控制步。若环境提前结束，记录实际步数与未执行尾部。`EnvironmentAudit` 只比较传入 `env.step` 的动作与原 `PolicyChunk` 队列，绝不变换动作；`policy_counters` 以真实 forward pre-hooks 及限定函数计数记录一次视觉编码、VLA、动作头、packing，A/B 另一次 scorer/Top-k。任何失败停止整次尝试，保留原事件，不重试。

实际 GPU 门槛还包括每格实际 OSC 控制器及 bound `scale_action`/`set_goal` 源、`use_delta=true` 和限值。Object 使用其 metadata 合同；Goal 同时使用 metadata 和两个官方组件映射合同。三类 scope 必须产生完整还原证明。只报告工程动作、计数、身份和成本；不计算成功率或延迟，不替换旧600条记录。

`--inspect-cpu` 只验证现有非权重元数据和四行开发初态。CPU 测试运行真实冻结 `PolicyChunk`、观测哈希、执行循环 AST、真实 v2 安装器以及本候选计数钩子；环境、神经模块和控制器均为明确替身，不能证明 GPU/物理环境行为。`gpu_body` 未在 CPU 测试中伪造执行通过。

```powershell
python -B .local/action_execution_gpu_acceptance_candidate_0626/probe.py --project-root F:/CTI-VLA --source-root F:/CTI-VLA --manifest .local/action_execution_gpu_acceptance_candidate_0626/candidate_manifest.json --manifest-sha256 <精确SHA> --inspect-cpu
```

GPU 入口另要求 `--execute-gpu --job-id --script-sha256 --gpu-registration --gpu-registration-sha256`，当前没有可接受的登记文件。预登记 schema 在 `gpu_registration.template.json`：版本 `formal_main_v2_action_execution_compat_gpu_v1`，单 GPU、3600秒、一次、16格，显式禁止自动重试。模板状态为 pending，不能执行。最终 source root 固定服务器的173文件快照；输出必须为独立新作业目录，不允许覆盖。

输出为 `inputs.json`、durable `events.jsonl`、`action_execution_identity.json` 和 `completion.json`。完成状态最多是 `captured_pending_root_review`；全部 Slurm 成本（含失败）由 root 回存后独立记账。没有完整 root/独立实际 GPU 审计，不可把候选、CPU通过或该状态称为生产放行。

首版原字节与40项测试保存在 `cpu_a1`。静查另发现旧 metadata 的完成事件重复提供 suite，会触发首版 journal 的 Python keyword 冲突；这不是 GPU 失败。修订仅允许与活动上下文相等的重复键，冲突或覆盖 journal 身份仍拒绝，原版复现和后续验证单独保存。
