# 正式非Long开发结果

2026-10-20 23:05 CST：训练仍64/72组双审，本轮不把刚完成的3043762自动计入。新增5批1000条开发验收；Goal256 seed17原200条因t0观测不一致整批HOLD，保留2034GPU秒。Goal128三seed A97.333%/B96.000%，B−A −1.333pp，95%配对簇bootstrap区间[−3.667,+0.667]pp，无等效或实测加速结论。Spatial/Object128目前仅23/41两seed可比。3个已审256组补位600条（3050192,3050205,3050224），未计完成。当前6GPU占槽、累计540.989GPU小时，Slurm总账只计一次。当前动作验收3800条，加显式兼容Long旧600为4400条，4套件共400唯一初态；含其他旧语义的验收记录5012条另保留。最终0/35200封存。见[汇总](../results/formal_main_v2/preflight/heartbeat_20261020T2218/summary_after_dispatch.json)与[下游阻塞](正式下游阻塞登记_20261020T1418.md)。

本轮新增验收均为每方法100条开发试验，不能作为封存最终成绩。

| 套件 | tokens | seed | A/100 | B/100 | B−A pp | t0交集/预算 | t0 Jaccard |
|---|---:|---:|---:|---:|---:|---:|---:|
| libero_spatial | 128 | 41 | 95 | 96 | +1 | 0.897656 | 0.814863 |
| libero_object | 128 | 41 | 97 | 98 | +1 | 0.835547 | 0.718356 |
| libero_goal | 128 | 41 | 98 | 94 | -4 | 0.767266 | 0.623126 |
| libero_spatial | 256 | 17 | 98 | 99 | +1 | 0.884609 | 0.793495 |
| libero_object | 256 | 17 | 98 | 99 | +1 | 0.859961 | 0.754619 |

128预算：Spatial已验收23/41为97/96与95/96，两seed描述均值A/B均96%；Object为98/99与97/98，均值97.5%/98.5%。历史seed17未通过当前动作语义接纳，不能补成三seed均值或区间。Spatial旧12条、未执行的588补充及Object旧失败记录保留，不纳入当前比较。

Goal三seed见[Goal开发结果](正式Goal主预算开发结果.md)。全部逐任务、逐seed与离线teacher/示范L1见[统计原件](../results/formal_main_v2/engineering/supervision_delivery_20261020T1418/terminal_independent/development_statistics.json)。L1是选中checkpoint的离线硬验证诊断，不是闭环动作误差；开发成败不参与选模。Token重合仅在同t0观测上配对。

5个验收作业11116GPU秒、Goal隔离作业2034GPU秒均已纳入Slurm总账，不重复累加。下面保留历史记录。


2026-10-20 21:51 CST增量：Goal新800条完成双审，seed17/23 A/B两seed均值均97%，仅描述、不代表等效。四参考和逐任务结果见[Goal开发记录](正式Goal主预算开发结果.md)；下方Spatial/Object历史结果保留。

更新：2026-10-20 20:53 CST。固定主预算128、seed23，全部10任务×10开发初态。以下仅为当前动作执行入口的开发诊断，全部种子/预算及完整O2A尚未齐备。最终初态仍封存。

| 套件 | A成功/100 | B成功/100 | B−A (pp) | t0交集/128 | t0 Jaccard | GPU秒 |
|---|---:|---:|---:|---:|---:|---:|
| Spatial | 97 | 96 | -1 | 0.885234 | 0.794666 | 2365 |
| Object | 98 | 99 | +1 | 0.848516 | 0.737785 | 2186 |

400条原始试验共4551GPU秒，已包含在Slurm总账；本轮验收不重复加费。训练成本保留在原训练收据。单seed差异不能证明稳定收益或等效，也不能据此声称成功率—延迟折中改善。t0仅比较相同hash的初始观测，后续轨迹分歧不作同观测配对。

| 套件/臂 | 选中update | 硬验证teacher L1 | 硬验证示范L1 | 验证窗口 |
|---|---:|---:|---:|---:|
| libero_spatial/A | 3500 | 0.02208964 | 0.02283513 | 189 |
| libero_spatial/B | 3000 | 0.02283510 | 0.02359372 | 189 |
| libero_object/A | 4500 | 0.02408605 | 0.02551053 | 204 |
| libero_object/B | 4000 | 0.02459210 | 0.02600229 | 204 |

上表是既定validation选中checkpoint的离线硬剪枝诊断，非闭环动作误差，未用开发成功率重选模。

| 套件 | task_id | A成功/10 | B成功/10 | B−A (pp) |
|---|---:|---:|---:|---:|
| libero_spatial | 0 | 10 | 10 | +0 |
| libero_spatial | 1 | 10 | 10 | +0 |
| libero_spatial | 2 | 10 | 10 | +0 |
| libero_spatial | 3 | 10 | 10 | +0 |
| libero_spatial | 4 | 10 | 10 | +0 |
| libero_spatial | 5 | 8 | 7 | -10 |
| libero_spatial | 6 | 10 | 10 | +0 |
| libero_spatial | 7 | 9 | 9 | +0 |
| libero_spatial | 8 | 10 | 10 | +0 |
| libero_spatial | 9 | 10 | 10 | +0 |
| libero_object | 0 | 10 | 10 | +0 |
| libero_object | 1 | 10 | 10 | +0 |
| libero_object | 2 | 9 | 9 | +0 |
| libero_object | 3 | 10 | 10 | +0 |
| libero_object | 4 | 10 | 10 | +0 |
| libero_object | 5 | 10 | 10 | +0 |
| libero_object | 6 | 10 | 10 | +0 |
| libero_object | 7 | 9 | 10 | +10 |
| libero_object | 8 | 10 | 10 | +0 |
| libero_object | 9 | 10 | 10 | +0 |

完整任务名称、逐初态配对、token重合和原始日志见本轮JSON及原审计。历史Object600和Spatial12仍单列；未证明其语义等价，不能混入当前结果。Long已接受的显式等价600条只复用、不重复执行或加分母。

[本轮诊断](../results/formal_main_v2/preflight/heartbeat_20261020T2020/nonLong_seed23_development_diagnostics.json) · [原始独审](../results/formal_main_v2/downstream_reviews/nonLong_seed23_1220_independent.json) · [计划与提交](../results/formal_main_v2/preflight/heartbeat_20261020T2020/summary_after_dispatch.json)
