本候选只处理已明确提交的 Long128 seed23 开发作业 3043709，不是重试提交器。

原事务已留下 returncode=0、stdout="3043709\n" 的确切 sbatch ack，随后因为 sacct 暂未包含新 job 而停在 known_job_id pending。原 preflight、sbatch_result、failed_transaction 三份原件按精确 SHA 读取并保留。候选没有任何 Slurm mutation 可调用路径：查询封装仅接受 sacct/squeue/scontrol，submit 方法直接拒绝。

默认模式只读。root 经已审 transport 和本文件确切 SHA 调用：
--candidate-sha256 6e1ce05c0dcde70b7b9fcbd1ffc763b40c2766e6fac4abe1103e1a7350811d06 --output-name root_check_a1.json

仅 root 独立审核后执行登记：在同一参数后追加 --commit --root-reviewed-reconcile，并使用新的 output-name（例如 root_commit_a1.json）。这是将已存在的 job 追加到登记清单，绝不再调用原授权提交入口。

检查在共享 writer 锁内执行：exact pending/ack/argv/token、全部原 preflight 来源、R/P 已发布 invocation SHA、历史 registered_jobs 身份、唯一 stage、controller activation/owner、实际仍被持有的 lifetime lease、当前 Long 预约，以及所有已登记 job 加 3043709 的真实 Slurm 对账。采用原 gateway._job、corroborate_new_job、reconcile_submission 和原 controller.capacity/atomic_json。新 job 固定为 3043709、单 GPU、gpu4001；controller 须真实 RUNNING CPU0 且 node 与 owner 相同。未知/缺行/重复/身份漂移全部拒绝。

不再调用原 NativeIO.preflight（已存在 invocation/output 会正确拒绝），不重新运行科学 plan 或 GPU。完整真实 Slurm 查询由 root check/commit 执行；作者仅做 23 项 CPU 检查，涉及真实当前来源/pending/owner/lease与明确标注的 synthetic scheduler 对账负例，没有声称作者已完成新的实时 Slurm 对账。

提交后的写集合严格限于：追加原 _job 行、清除本次 exact pending、更新全 registry 成本与当前活动 GPU 数、消费本次 Long 预约。其余所有当前 controller 字段/owner/完成与失败记录/历史 job 均保留。作业行沿用原 gateway 的 SUBMITTED 形态；其真实 RUNNING/终态及 GPU 成本保存在 submitted_job_observation 中，由正常 controller 下一 tick 更新 job 状态。

root commit 在 CAS 前保存原始 pending 所对应的新 precommit 对账证据、实际观察和单份 submission 收据，再用原 atomic_json 的 expected SHA 提交。若这些步骤有异常，已有证据与 pending 不会被自动清理，也不自动重试；若 CAS 已成功而后续收据写失败，状态不会回滚或再次提交，需要 root 根据已登记 job 补记。发生任何 partial commit 文件后再次运行会拒绝，避免模糊重放。

本目录候选/测试来源均固定。候选准备、CPU 检查不写真实 state/P/Git，不访问封存值或加载模型。root 新输出可追加本目录，但不改变已冻结作者收据与源码。
