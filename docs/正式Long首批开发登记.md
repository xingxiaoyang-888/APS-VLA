# Long首批正式开发登记

2026-10-17，首对Long128 seed17完成5000步及双重复核后，从真实选中checkpoint生成首批开发清单。计划、CPU整链和root/独立复核均已通过，提交时仍核对最新八作业容量及实际服务器输入。见[CPU集成验收](../results/formal_main_v2/preflight/asset_downstream_consumers_root_acceptance_20261017.json)。

- 六方法：Dense、均匀256／128／64、A128 seed17、B128 seed17。
- 固定原100个开发初态（10任务×10），共600条目标；环境seed0、runtime seed17、等待10步、动作chunk8、最多520控制步。
- A使用4500步选中checkpoint，B使用5000步；实际服务器SHA与报告、部署收据一致。旧四参考清单未执行，保留为历史，不另行重复提交。
- 首作业固定 `stop-after=12`，按原初态优先、方法次序完成前2初态×6方法，用于接口和耗时检查。12条属于同一600目标；之后经过root终态复核，在同目录、同清单和同ledger显式续跑，不重做已完成trial。
- 工程分段仅按实际耗时安排，不依成功率改配置、初态、选模或任务。600条完成后，Long仍须补其余16个方法的1600条开发；不能把首批当作整个Long开发完成。

每次使用一张独占L40、7 CPU、64GiB内存、4小时分配。所有本项目非终态请求合计最多8个；八槽满时不提交。所有失败和恢复成本保留，最终初态仍封存。

原始登记：[执行清单](../results/formal_main_v2/execution/libero_10_development_first_pair_v1.json)、[来源证据](../results/formal_main_v2/execution/libero_10_development_first_pair_v1.json.evidence.json)、[首批登记](../results/formal_main_v2/preflight/long_first_pair_development_registration_v1.json)、[首12条执行计划](../results/formal_main_v2/preflight/long_first_pair_development_plan_v1.json)。计划SHA为 `d8bf3a5a9a4c435d9b81a74083afacdebd8a6d80ec7980fb34fa006b4a84f3d5`。这些文件是运行前配置，不是成功率结果。
