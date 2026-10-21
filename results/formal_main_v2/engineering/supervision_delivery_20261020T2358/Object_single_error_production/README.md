# Object 单 policy_error 生产接线候选（CPU，HOLD）

此包没有提交权限。原 600 条完整保留，599 条旧动作等价性采用来自 root 已冻结逐行证据；原 task 8 / source state 49 / dense 的失败及其未知第 8 次 query 均保留。候选仅允许该逻辑 trial 从原初态完整 reset 后执行一次新的关联尝试，不是普通 resume，不复制或合成 599 条 completed ledger。完整 100-state / 六方法科学清单和原选定 checkpoint 不变。新负结果仍是终态，不按结果重试。

## 实际完成的验证

最终 CPU 报告为 cpu_final.json；此前 cpu_attempt02.json（13 正例 / 48 拒绝）、cpu_attempt03.json（14 / 66）和 failure_cpu_attempt01.json 原件保留。早期报告绑定当时源码，不作为最终源码通过记录。

verify_cpu.py 实际重建原 173 源、全部旧 600 raw、599 采用表和独审、真实原 P wrapper.verify 的输入门槛、原 planner 科学清单/source/checkpoint 校验，以及旧作业 3021844 的完整原 consumer（原 adapter 两 binding、输入/pull/轨迹/summary/全部 6713 GPU 秒）。这不是新 GPU 重跑。

新 raw parser 的 CPU 正例使用真实保存的原失败轨迹，放在明确标为 CPU_FIXTURE_NOT_ACTUAL 的独立三行 envelope 内；不补第 8 query。空动作成功、动作字节变化、错模型/source/checkpoint watch、错初态/方法/seed、额外结果、错误引用和合成 consumer flags 被拒绝。新运行 journal 的 code 对照测试是结构测试；编译为 canonical co_filename 是静态投影，不是实际 P 安装或执行证明。

## 实现边界

- entry.py 的 __main__ bootstrap 仅用标准库先检查精确 P 路径、计划/调用原字节 SHA 和全部新入口源码，再导入项目模块。
- wrapper.py 先验证真实原第一次调用。实际科学参数仅 output 新目录、移除原 stop_after=12；完整原科学清单仍为 600，显式 typed iterator 的执行白名单只有该 1 条。
- execution.py 在未修改的原 adapter.run / execute 内安装单条 iterator；原 adapter 保留其原 frozen loop 身份，另外 iterator journal 记录真正 derived loop 身份。真实 run_episode/alias/observation/PolicyChunk、六个实际 FormalRolloutPolicy、token policy 方法、原 factory/reseed/on_result、执行 guard 都做独立代码闭包核对。
- 一个永久 once_claim 与原六方法 stage locks 阻止本入口二次运行。失败也不清 claim。执行前核实际环境 ID 与 root 唯一登记、原 ACK/token/comment、invocation 原字节 SHA。
- reviewer.py 在完整原旧输入校验后显式作新 output 的内存分析投影；原旧 invocation 从不改写。调用原 runtime_inputs / adapters / rollout / allocation_cost，只使用已接受的 current-action 轨迹验证派生。原 summary 必须仍是 1/600、scientific_complete=false。真实 typed action/iterator/completion/identity 全部由 pull SHA 绑定并重建；synthetic_input / synthetic_fixture 明确拒绝。consumer 重新执行真实 raw 证明，不能由布尔 passed 声明替代。
- 新参考视图若将来完成，可表达 599 legacy-equivalent + 1 current，但保持旧 600 原记录与旧 error，全部尝试 601；原 6713 秒与新完整 Slurm 分配分别只计一次。当前包不接纳新一条，也不改变已接纳计数。

## 尚未完成，严格 HOLD

1. native atomic gateway missing。gateway_contract.py 只有无写谓词；submit 永远抛 HOLD。未来唯一 gateway 必须从实际 state.registered_jobs 重建 registered_projection，查询全部 CTI 模式真实 Slurm name/comment/account/partition/output，真实 probe 原控制器生命周期 lease，在共享 writer.lock 与 CAS 内完成持久 pending / 唯一 token / 原 ACK 对账。当前纯投影不构成真实容量或 lease 证明。
2. canonical R/P 尚未安装此包；新 actual-P --verify 尚未运行。原 P wrapper 的通过不是新入口通过。
3. 新 root repair、完整新入口独审、精确未来 gateway 独审与 root readiness 尚未完成。既有 599 root/独审只采用旧 599，不授权新 GPU。
4. 尚无新单条真实 GPU raw，因此新 typed terminal 全链未实际贯通。未来必须以新真实注册、pull allowlist、adapter 两 binding、action/iterator journals、checkpoint/input 身份执行 reviewer.review 及 consume，再由独立 agent 终审。不得用当前 CPU envelope 当成新结果。
5. 未读取封存 final、没有新推理/模拟器调用、新 trial 或 GPU 秒。最终全局 release 不变。

## 精确发布与调用

publication_map.json 列出全部 10 个生产文件原字节到 R 与 P 下 scripts/ops/formal_object_single_error_v1/ 的映射。只能由 root 按独审采用后安装；本包没有安装脚本。

只读 CPU 重建（由审计方通过已审 transport 和 verify_saved.py 的精确 SHA 执行）：

    python -B scripts/ops/server_control_transport_v1/run_server_control.py --bundle-manifest-sha256 3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149 --entrypoint .local/object_single_error_production_20261020T2358/verify_saved.py --entrypoint-sha256 <delivery_manifest 中 SHA> --audit-relative results/formal_main_v2/control_transport/<独立唯一审计名>.jsonl

未来 root 安装、生成 exact plan、取得完整源码独审和 repair 后的 actual-P 验证入口：

    /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B /ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/scripts/ops/formal_object_single_error_v1/entry.py --verify --plan /ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/formal_main_v2/execution/object_single_error_v1/plan.json --plan-sha256 <真实原字节 SHA>

production_contract.json 给出确切字段名/角色/路径；没有预写 passed receipt。immutable invocation 在 sbatch 前生成，不包含未知 job_id，Slurm 返回后只登记原 ACK，不能改 invocation bytes。root 为新 gateway 评审和真实 P 验证闭合后，才可能一次提交 --run；本包没有可提交命令。

所有写入仅本私有目录及已审 transport 唯一 journal；无 state/Git/P/Slurm 写。delivery_manifest.json 不把自身列入 files，报告其自身 SHA 给 root。
