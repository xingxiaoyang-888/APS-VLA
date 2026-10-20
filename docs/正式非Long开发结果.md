# 正式非Long开发结果

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
