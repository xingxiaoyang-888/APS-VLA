# 正式非Long开发结果

## 2026-10-21 本轮终态验收（2026-10-21T04:21:51.652827+00:00）

训练72/72组、36pair、360000更新保持完成。Object3054409的新1条与599条兼容历史来源通过原科学consumer、限定四日志补充及不同代理终审，形成完整600条视图；原policy_error与全部601次尝试保留，未伪造599条新ledger。Goal3054717的新固定200条通过完整输入/动作及原consumer独审，仅接纳本次新数据；旧200与旧原因仍HOLD，另1000条待精确工程准入。

完整开发验收7800/8800＝6589 current＋Long600、Spatial12、Object599兼容来源，仍400唯一初态。本轮实际新增验收201条，另599历史条进入完整批次；不是新增800个试验或初态。历史目录7801条含原Object错误，不能作当前分母。Object逻辑600为521成功/79正常失败；Goal256 seed17 A97/100、B96/100，仅开发单seed描述，非最终有效性、等效或加速结论。

273唯一正式分配累计1994468 GPU秒（554.018889小时），0请求槽、0实际活动GPU，当前登记集合成本已终态。Object旧6713＋新326＝7039秒，Goal新2205秒均在总账各计一次。新Goal开发证据35076成员归档24卷并恢复核验，原文件及失败均保留。173冻结文件不变，本轮无新GPU提交。

下一步为Goal剩余五pair（256的23/41；64的17/23/41）补齐独立计划、来源与单次提交准入，并处理Goal固定30观测；已完成作业不重跑。88身份与四套件完整收据/最终清单未全冻结，O2A未开放，最终0/35200仍封存。

证据：[本轮汇总](../results/formal_main_v2/preflight/heartbeat_20261021T1134/final_summary.json)；[下游登记](正式下游阻塞登记_20261021T0334.md)。


2026-10-21 00:13 CST：Goal64 seed17 A/B 已完成原 root 与独立终验，新增2组及10000已审更新，累计66/72组、331000更新。新增三批600条开发已验收（3050192/3050205/3050224）：当前动作4400条；含其他旧语义的全部验收5612条，显式兼容Long旧600另合为5000条。四套件仍为400个唯一开发初态。当前3个GPU作业占槽，累计545.144GPU小时，全部登记Slurm分配只计一次。此完成结果事务不提交作业，也不把之后的新派发或工程探针计为完成。Goal工程诊断已登记、待终审，原Goal256 seed17的200条HOLD保留；Object256 seed23兼容桥仍未科学准入。最终0/35200，封存门槛不变。见[本轮接纳收据](../results/formal_main_v2/preflight/heartbeat_20261020T2330/completed_evidence_integration_1530.json)。

本轮均为开发诊断；选模继续只用原validation。完整历史结果保留。

| 套件 | tokens | seed | A/100 | B/100 | B−A pp | t0交集/预算 | t0 Jaccard |
|---|---:|---:|---:|---:|---:|---:|---:|
| libero_spatial | 256 | 23 | 99 | 97 | -2 | 0.907539 | 0.831072 |
| libero_spatial | 256 | 41 | 97 | 99 | +2 | 0.886719 | 0.796753 |
| libero_object | 256 | 41 | 97 | 98 | +1 | 0.882070 | 0.789309 |

Spatial256三seed：17为98/99，23为99/97，41为97/99。均值A98.000%、B98.333%、B−A +0.333pp；种子样本SD分别1.000、1.155、2.082pp。固定10000次任务内初态簇bootstrap（seed20261016），每簇携带完整三seed。95%区间A[95.667,99.667]%、B[96.667,99.667]%、B−A[−0.667,+1.333]pp。100个唯一初态不能当作300个；区间跨零不意味着等效。

Object256仅已有17和41：98/99、97/98，描述均值A97.5%、B98.5%，B−A +1pp。seed23下游来源兼容仍待准入，不补造三seed均值或置信区间。

没有同checkpoint完整O2A结果，本轮不宣称剪枝折中改善、等效或实测加速，也未按Dense区间完成−2pp实用目标判断。未来误差和硬验证L1只作诊断。

三批开发6678GPU秒、Goal64训练60721GPU秒均属于已有Slurm分配；接受证据不增加这些成本第二次。[完整逐任务/逐seed/离线L1](../results/formal_main_v2/engineering/supervision_delivery_20261020T1530/terminal_independent/development_statistics.json)，[root重算](../results/formal_main_v2/preflight/heartbeat_20261020T2330/Spatial256_root_bootstrap_recomputation.json)。root重用并独立执行审计方算法，输出字节相同源自确定性计算，不声称算法另行独立实现。


2026-10-20 23:12 CST：训练仍64/72组双审，本轮不把刚完成的3043762自动计入。新增5批1000条开发验收；Goal256 seed17原200条因t0观测不一致整批HOLD，保留2034GPU秒。Goal128三seed A97.333%/B96.000%，B−A −1.333pp，95%配对簇bootstrap区间[−3.667,+0.667]pp，无等效或实测加速结论。Spatial/Object128目前仅23/41两seed可比。3个已审256组补位600条（3050192,3050205,3050224），未计完成。当前6GPU占槽、累计541.732GPU小时，Slurm总账只计一次。当前动作验收3800条，加显式兼容Long旧600为4400条，4套件共400唯一初态；含其他旧语义的验收记录5012条另保留。最终0/35200封存。见[汇总](../results/formal_main_v2/preflight/heartbeat_20261020T2218/summary_after_dispatch.json)与[下游阻塞](正式下游阻塞登记_20261020T1418.md)。

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
