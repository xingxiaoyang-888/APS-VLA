# CUDA 启动失败：原目标单次恢复候选

当前只有 CPU 候选，未提交 Slurm、未消耗 GPU、未修改生产 state。五个原恢复/科学审计模块保持原字节；冻结 173 文件及正在运行的控制器不变。当前 8 GPU 满额不会通过容量门，不抢占健康作业。

## 范围

|原失败|pair|保留事实|唯一恢复目标|
|---|---|---|---|
|3028460|Object256 seed23|FAILED 1:0；84 GPU 秒；A/B 0，cursor 0|500|
|3028468|Object64 seed23|FAILED 1:0；69 GPU 秒；A/B 0，cursor 0|500|
|3028522|Spatial64 seed23|FAILED 1:0；73 GPU 秒；A/B 1000，cursor 8000|1500|

总失败成本 226 GPU 秒保留。原 5000 科学退火/每 500 validation 不变；本入口仅恢复到原登记边界，--resume、soft wall 12600 秒、Slurm 4 小时、1 L40、--exclude=gpu4020 --no-requeue。不清除 blocked_pairs，不授予连续 5000 准入，不修改最终集封存或动作执行门槛。恢复完成后仍须原完整终态/修复审计；承接连续模式需要单独版本化审批和执行层支持。

## 文件与接口

gateway.py 默认只检查，调用真实已登记 sacct/squeue、原失败与科学计划重建、同服务器 P/S 文件散列，以及两个固定 resume 的 SHA；不加载 tensor。它在共享 .writer.lock 内完成检查。root 真正调用该检查时才会读 checkpoint 字节做 SHA；本轮作者 CPU 测试没有读真实 checkpoint。

evidence.py 只复用原五模块的纯检查/组装入口，不调用旧 execute_root/refresh/submit。Object 继续原 metadata 合同，Spatial 不引入该适配。唯一 R-only metadata 是 failure proof 的精确 previous_boundary_review：在 R 校验 SHA 和 bytes 后不要求 P 原始输出也有该收据；绝不豁免整个 segment_reviews 目录。

authorization_*.template.json、reservation_*.template.json、repair_*.template.json 均为不能执行的草案，含 draft 状态和占位字段，不表示 root 已批准。它们不是人工或独立审计结果。

## root 最小集成顺序

1. 读取作者证据与新的独立 CPU 收据。独立收据必须 exact kind=cuda_startup_server_recovery_gateway_independent_CPU_review、status=passed_CPU_review，files 含实际被执行的 gateway/evidence 路径及 SHA。若将源码复制到 Git 可见新目录，必须原字节复制两文件，并请独审补核目的路径；不能用旧路径收据冒充新路径。原五模块仍使用它们已恢复的精确路径和 SHA。
2. 每次只选一个已登记失败 ID。由 root 复核对应 canonical proof，生成新的 repair JSON：填 status=reviewed，保持模板中失败全集/原目标/原五模块映射/runtime 合同；以最终原始 JSON 字节 SHA 命名 <SHA>.json。不改历史 proof。
3. 完成新的 root authorization（status=approved_for_exactly_one_original_target_recovery），填真实独立收据、repair 的 ref、当前 controller job ID 和执行两源路径/SHA。其余科学字段固定。先移除 root_reservation，用 gateway.intent_sha(auth) 算 canonical intent（排序、紧凑 JSON、UTF-8、末尾换行）。
4. 新建专属于该失败 ID 的 reservation root record，status=approved_for_named_single_recovery，含最终 authorization 相对路径、上一步 intent SHA。再把 reservation 原始字节的 path/SHA 写入 authorization，最后算 authorization 原始字节 SHA。这避免相互散列成环。记录只能预约 CUDA 本请求；旧 v3 reservation 不得代用。
5. root 在现有共享 .writer.lock 的 CAS 事务内将 autonomous_training_v1.reserved_GPU_slots=1、reservation_root_record=该新 ref。不清空任何未知 pending、不改变 FAILED 或 blocked，也不取消健康 GPU。控制器会保留随后空出的一个 GPU 槽；root/控制器共用同一文件 inode 锁。
6. root 先运行下方默认检查。要求所有登记作业都有本次 sacct/squeue 对账；UNKNOWN/缺行/过渡态保守阻断，只有登记 0 GPU 且实际账单 0 GPU 才豁免槽位。确认少于 8 个 GPU 请求、同 pair 无活动、自己预约仍匹配、原 P 输出无新增/漂移、实际 resume SHA 一致。
7. 核查默认输出和精确 argv 后，root 才可添加双显式提交旗标。该调用再次在同锁内做完整检查与两次容量快照。提交后仅在新 ID 已确定且终态登记 CAS 持久化后消费预约；失败历史及费用原样保留。root 后续按实际分配验收，不把本 CPU 结果称为恢复成功。

示例（必须替换 root 实际批准 ref 与 SHA；现在不得执行提交）：

    cd /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo
    /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B .local/cuda_recovery_autonomous_1940/gateway.py --authorization ROOT_APPROVED_RELATIVE_JSON --authorization-sha256 ROOT_APPROVED_SHA256 --gateway-sha256 CANDIDATE_GATEWAY_SHA256

只有 root 验收默认检查后，才追加 --submit --root-reviewed-submit。

## 事务与异常

真实提交顺序：原始 preflight → durable pending → R/P 新 invocation 原子独占发布 → sbatch → 原始响应 → known job ID durable pending → 新 submission receipt → 最终 registry CAS → committed receipt。audit 路径为 results/formal_main_v2/startup_recoveries/<failed>/<authorizationSHA>/。

任何 publication、超时、坏/旧 ACK、CAS 漂移或记录失败都会保留已产生证据和 pending，不吞异常、不重发。已有 audit 或 invocation 亦拒绝重入。若 sbatch 结果不确定，root 必须按保存的完整实际 argv/comment/invocation SHA 和 scheduler 事实人工对账，不能清 pending 后再次调用猜测重试。known ID 后最终 CAS 失败也必须按该 ID 对账。空 audit 目录表示事务曾开始，不能当未提交证据。

本候选不自动重启或后台运行。production controller 对未知 pending 的现有阻断保持；正常 GPU 继续。

## CPU 验证与限制

- a1：38 通过；含隔离 fake Slurm/IO 的故障注入及真实 canonical 非权重重建。
- a2：3 通过；真实三份 Science.prepare 恰等原 invocation，仅 timestamp/repair 与必要的显式 resume 不同。容量使用明确合成的 terminal-only 投影，不代表真实空槽。
- a3：46 通过；含以上用例与精确 R-only previous review 的正/负例。
- runtime_nonweight_check.json：真实 P 三份原始目录 3/3/21 文件逐 SHA/bytes 匹配；只读取非权重，未查真实 free slot 或 checkpoint。
- 新独审单独记录。历史旧五模块 39 项测试是旧证据，不冒称覆盖本候选。
- 首次词法缺口与 Spatial R-only metadata 问题、旧源码均保留。本候选不证明节点整体损坏或方法有效，也不证明任何恢复已运行。
