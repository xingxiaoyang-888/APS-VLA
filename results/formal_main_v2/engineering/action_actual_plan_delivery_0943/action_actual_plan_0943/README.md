# Spatial 首个新动作执行版本开发计划草案

本目录仅准备真实开发计划与 root 签发材料。没有提交 Slurm、预约 GPU、写生产 state、发布 P、加载模型或打开 final 状态。本轮所有上游科学证据均为真实原件，没有以合成 fixture 代替。

## 固定范围

- 原 suite：libero_spatial。方法顺序：dense、uniform256、uniform128、uniform64、A128_seed17、B128_seed17。
- 仍使用原 100 个开发初态、原环境参数与同一持久输出目录。原 12 条终态保留，仅追加 588 个尚未终态的 trial ID；stop_after=None，resume=true。
- 原作业 3022743 的 393 GPU 秒保留一次。policy_error 仍是终态，不能因新动作入口重跑。Object 原 600 已全部终态且包含一条 policy_error，不是本次续跑目标。
- 只允许 development。禁止 collect/full/components、global freeze 与 final。旧 12 条不能改标为新执行语义，也未证明其与新入口结果等价；后续 O2A/冻结需另外的明确等价证明与消费者门槛。
- 计划资源保持原值：1 L40、7 CPU、64G、04:00:00；没有为本次准备改训练、方法或评测预算。

## 已执行的真实只读核验

原 formal_downstream_supervisor.plan 在真实 state 快照、真实来源/选择器收据与原 raw 上成功重建，311 条来源引用。独立代理另用同一快照重建了完全相同的计划。

prepare_runtime_and_prefix.py 重核 R/S 各 173 个冻结文件、运行合同及继承的 v4 四套件 16 格 GPU 工程验收、R/P 四个旧前缀文件；从原始 JSONL 得到 12 个终态、588 个不重叠剩余 ID。没有再次运行 GPU 工程验收。

root 已另签正式前缀转换：
results/formal_main_v2/execution/action_spatial_resume_0943/transition.json
SHA 95da28cbfd0968d38e5e92b9468c331b377cccf88ec3bfcdb342b4ce2f1a43a1。
该转换只准保留原 12 条并追加 588，不是 readiness 或提交授权。

freeze_actual_outer_plan.py 调原 converter，对原计划仅变更已登记的运营身份字段；科学 argv、source_provenance、method/checkpoint、输出、旧账单和资源保持相同。仅 trials.jsonl 与 closed_loop_report.json 从运行后 immutable watches 移到开跑前精确 SHA 核验，原 root_evidence 与前缀证据均保留。

root 发布 9 个缺失运行文件后，check_runtime_publication_readonly.py 调原 runtime.validate_contract(project=P) 及 NativeIO.preflight：20 个运行依赖全部字节一致，218 个现有 P/S 输入通过；8 个明确计划/审阅元数据等待最终发布。此检查没有调用 Gateway.run、Slurm、容量查询或生产锁，不是完整 readiness。

## 固定文件与 SHA

- scientific_plan.json：43a521e2b1c5b7f8ceff442ce655dde5cae73dfde0f9f7598f65fa57446b4a94
- 原科学 plan 内容签名：e3421a9476decda68fbcef721b359445515c88da216771517fa97719ed2182b1
- execution_contract.json：b63689d9f3fb3dece0c2fee8c219ad94cd8e1e694962afdb2cd66a40bf551bc0
- effective_plan.json：a56ff9e12b6ddad13e3e6ee4b78f5181ffa3ead3f8df8c620370e00c95d2eb3b
- 新 plan 内容签名：18dd81107df46cd7e3de7180177799cf749c5dc9106d4a3d9980681eba590265
- runtime_readiness_draft.json：3dbf2a4eac17d1f33766a2d8cbc5b89280bf223de8ec52293214e44afd805738
- dependency_closure.json：b36a3dde881d3de9d48d3ad439b0b38f4189cec5ea10648ce1b9e9e580983a76
- plan_preparation_review.json：d385b5417f887552486545ad1c6ee2a1063877dd4b4abce9efe0149e78f563c2
- runtime_post_publication_readonly_check.json：8948b78f892bd17e5012d525180d0e2b5451a135407c163c964f64c604c77712

前三份完整计划材料的拟发布目录为 results/formal_main_v2/execution/action_spatial_resume_0943/。本目录的计划已引用该 canonical 目的路径，但本代理没有复制过去。

## readiness 和 prepared invocation 仍为草案

runtime_readiness_draft.json 的 status 是 draft_pending_plan_independent_and_root_readiness，reviewed_by/root_review/independent_review 未签；production_chain_complete=false、raw_consumer_ready=false，因此原 gate 必须拒绝。原组件独审只绑定已审组件，不能冒充逐计划生产链放行。

root 需要在真实独审通过后单独签每计划 root/independent 证据，两者 status=passed、execution_version=formal-downstream-action-v1、runtime_sources 完全等于本执行合同的 8 个直接文件，production_chain_complete=true；该声明只限本次 development，不是已产生新的科学结果。

最终 readiness 必须保留 allowed_stages=[development]、final_evaluation_enabled=false、O2A_enabled=false、global_freeze_enabled=false，并绑定本 effective/scientific plan 文件 SHA、plan 内容签名与全部 support_files。其 runtime_publication_files 增补实际 root/independent 计划收据，不能包含 readiness 自身。实际签发后 hash 必然与 draft 不同。

prepared_invocation_template.json 的 registered_utc/runtime_readiness 为 null，不能直接执行。root 应原样保留 effective invocation，只在签发时填当前真实带时区 registered_utc、plan_sha256、实际 readiness path/SHA。不得增加 argv、替换 method、改变 resume/输出，或预创建正式 invocation 目的文件；后者由网关 pending 成功后唯一发布。

## root reservation 的精确合同与无环顺序

reservation_root_record_draft.json 是字段模板，不是已预约。原代码要求的字段为：

- schema=formal_main_v2
- kind=root_downstream_GPU_slot_reservation
- status=approved_for_exact_downstream_request（仅 root 实际批准后填写）
- controller_job_id=3034538（提交前重核仍为实际 controller owner）
- reserved_slots=1
- capacity_limit_all_GPU_modes=8
- automatic_retry=false
- stage_key=libero_spatial_development_8c843c1d4ee8383c
- plan={canonical effective_plan path, exact file SHA}
- authorization_path=results/formal_main_v2/execution/action_spatial_resume_0943/submission_authorization.json
- authorization_intent_sha256=原 gateway.intent_sha(完整最终 authorization)

intent_sha 只从 authorization 删除顶层 root_reservation 后对规范 JSON 求 SHA，不删除 readiness/plan/prepared/source 等字段。次序为：真实逐计划审阅→readiness→prepared invocation→完整授权但暂未填 reservation→求 intent→签 reservation→将其 path/SHA 填回 authorization→求最终 authorization SHA。这样无自身哈希环。

原 gateway 逐字要求 state.autonomous_training_v1.reserved_GPU_slots==1 且 reservation_root_record==当前授权的 root_reservation；不能消耗旧 CUDA 预约。规划快照里 reserved_GPU_slots=0，但仍保留旧 CUDA reservation_root_record，这是历史记录，不是本请求权利。root 预约时须持既有 .writer.lock，重新读 state/CAS，确认没有其他未消费预约或 pending，再只登记本请求的 1 个未来槽。不能覆盖他人的有效预约或取消健康训练。本代理没有执行这些操作。

网关成功提交后仅将 reserved_GPU_slots 置 0，并把当前授权 SHA、reservation、真实 job/token 记入 downstream_reservations_consumed。它保留全部旧登记与 controller 字段。未知 Slurm 或模糊 ACK 保留 pending，不能自动重试。

## 最终只读 CLI（当前未执行）

完成上述 canonical R 发布、root 签发、独占预约后，由 root 在 R 执行下列默认只读模式，AUTH_SHA 必须取实际最终授权原字节，不能取本 draft 的 SHA：

```bash
cd /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo
/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B \
  scripts/ops/formal_action_deployment_v1/gateway.py \
  --authorization results/formal_main_v2/execution/action_spatial_resume_0943/submission_authorization.json \
  --authorization-sha256 "$AUTH_SHA" \
  --gateway-sha256 8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a
```

故意没有 --submit 与 --root-reviewed-submit。默认模式仍要求真实专属预约、全登记 Slurm 对账、CPU0 owner/lease、未知状态拒绝、活动 GPU<8、完整原 planner 重建与 P/S preflight。当前若 8 卡全满，应明确拒绝并等待后续监督；不得用本准备结果代替现场容量证明。

root 若未来决定执行，须独立验证同一授权与最新容量，再显式使用网关两项提交开关。本说明没有执行或授权该操作。
