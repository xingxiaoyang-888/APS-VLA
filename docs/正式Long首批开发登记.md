# Long首批正式开发登记

## 2026-10-17 首12条真实验收与续跑登记

作业3016981完成，完整分配437 GPU秒。原始25行ledger包含12条终态，恰为固定前2个开发初态×6方法；491次策略调用、硬预算、packing、单次前向、动作队列及A/B选中checkpoint身份均通过root和独立复核。两条达到控制步上限仍未成功的试次完整保留。当前为12/600，不能据这两个初态判断整体成功率或加速收益，最终评测仍封存。

根审计器最初将既有评测入口正常生成的`.evaluation.lock`误判为异常排除。修正仅允许development/final下精确run目录的该锁及精确排除原因，其他缺失、SHA、来源和最终面板检查保持。50项聚焦CPU测试及独立审核通过；173冻结文件未变，原GPU作业未重跑。旧157项CPU验收保留其原源码身份，不声称在修正版本重新执行。见[修正附录](../results/formal_main_v2/preflight/downstream_lock_root_acceptance_20261017.json)。

已登记下一段显式resume、新增上限120条，正常完成后累计132/600，保持同一清单、目录、初态顺序和原ledger。分段大小仅根据已测试次耗时和原4小时时限确定，不依据成功率。首12条原始9份文件已逐字节归档，旧437 GPU秒继续计账。提交前核对203个服务器输入及两份选中checkpoint实际SHA，并受8个活动请求上限约束。

证据：[真实根审计](../results/formal_main_v2/downstream_reviews/3016981.json)、[独立复核](../results/formal_main_v2/preflight/long_first_development_real_independent_20261017.json)、[原始字节归档](../results/formal_main_v2/preflight/long_first_development_raw_v1/receipt.json)、[续跑登记](../results/formal_main_v2/preflight/long_first_pair_development_registration_v2.json)、[续跑独审](../results/formal_main_v2/preflight/long_first_pair_development_plan_independent_v2.json)。

续跑已于18:31提交作业3017161，18:36日志确认新增调用已开始；仍以已审核的12条计完成数，下一终态需同目录全历史回存和复核。

## 原始登记（保留）

2026-10-17，首对Long128 seed17完成5000步及双重复核后，从真实选中checkpoint生成首批开发清单。计划、CPU整链和root/独立复核均已通过，提交时仍核对最新八作业容量及实际服务器输入。见[CPU集成验收](../results/formal_main_v2/preflight/asset_downstream_consumers_root_acceptance_20261017.json)。

- 六方法：Dense、均匀256／128／64、A128 seed17、B128 seed17。
- 固定原100个开发初态（10任务×10），共600条目标；环境seed0、runtime seed17、等待10步、动作chunk8、最多520控制步。
- A使用4500步选中checkpoint，B使用5000步；实际服务器SHA与报告、部署收据一致。旧四参考清单未执行，保留为历史，不另行重复提交。
- 首作业固定 `stop-after=12`，按原初态优先、方法次序完成前2初态×6方法，用于接口和耗时检查。12条属于同一600目标；之后经过root终态复核，在同目录、同清单和同ledger显式续跑，不重做已完成trial。
- 工程分段仅按实际耗时安排，不依成功率改配置、初态、选模或任务。600条完成后，Long仍须补其余16个方法的1600条开发；不能把首批当作整个Long开发完成。

每次使用一张独占L40、7 CPU、64GiB内存、4小时分配。所有本项目非终态请求合计最多8个；八槽满时不提交。所有失败和恢复成本保留，最终初态仍封存。

原始登记：[执行清单](../results/formal_main_v2/execution/libero_10_development_first_pair_v1.json)、[来源证据](../results/formal_main_v2/execution/libero_10_development_first_pair_v1.json.evidence.json)、[首批登记](../results/formal_main_v2/preflight/long_first_pair_development_registration_v1.json)、[首12条执行计划](../results/formal_main_v2/preflight/long_first_pair_development_plan_v1.json)。计划SHA为 `d8bf3a5a9a4c435d9b81a74083afacdebd8a6d80ec7980fb34fa006b4a84f3d5`。这些文件是运行前配置，不是成功率结果。
