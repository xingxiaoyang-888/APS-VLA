# 正式Long128三种子训练记录

2026-10-18，Long总128 tokens、seed17/23/41的A/B共6组均完成5000更新，原始训练报告、root与独立审计、服务器选中checkpoint SHA全部一致。本页只汇总训练与选模诊断，不更新闭环结论。

| seed | 方法 | 选中更新 | 任务等权硬teacher L1 | 任务等权硬示范 L1 |
|---:|---|---:|---:|---:|
| 17 | A | 4500 | 0.01995340 | 0.02161449 |
| 17 | B | 5000 | 0.01992077 | 0.02153307 |
| 23 | A | 3500 | 0.01941804 | 0.02106928 |
| 23 | B | 4500 | 0.01973708 | 0.02137614 |
| 41 | A | 3500 | 0.01940817 | 0.02105891 |
| 41 | B | 3500 | 0.01987897 | 0.02149173 |

A为动作监督，B在相同A上增加未来监督；示范L1仅作诊断。全部节点均以真实硬剪枝128 tokens（每视角64）验证，按任务等权teacher L1取最小、相同值取较早节点，未重选模型。

每臂40000次窗口使用、40000个实际唯一窗口；合法训练池68819个，覆盖0.581235轮。A/B同seed共享初始化和顺序，三seed分别初始化。同seed两臂80000次使用只涉及40000个窗口；六臂共240000次使用，跨三seed实际并集63769个窗口，不能相加为独立样本。

每臂完成update0及500至5000共11×165窗口验证（10任务等权），六臂合计66次完整验证。所有种子均保留，不挑最好种子；权重仅在服务器。

| seed | 配对训练作业数 | 实际GPU秒 | GPU小时 |
|---:|---:|---:|---:|
| 17 | 10 | 41261 | 11.461389 |
| 23 | 10 | 47006 | 13.057222 |
| 41 | 10 | 46871 | 13.019722 |
| 合计 | 30 | 135138 | 37.538333 |

此费用为三个A/B配对训练作业链的完整分配账单，各作业只计一次；包含加载、缓存、训练、验证和保存。没有训练失败或重放。共享验收及其他工程失败、其他预算/套件、闭环与测速属于项目总账的其他范围，未重复加入本表。内部阶段和缓存计时不相加；A/B共用作业及缓存，不能把整份账单各记给一臂，也不能据此推断B训练更快或八卡完成日期。独立运行缓存成本尚未纳入本页。

teacher L1的B−A在seed17为负、23/41为正，方向不一致；这些只是选中节点上的离线验证差值。训练完成与动作误差均不能证明闭环成功率或成功率—完整推理延迟折中改善。本页未新增闭环或O2A结果，最终初态继续受原全局release门槛约束。

[完整可复算摘要与输入SHA](../results/formal_main_v2/preflight/long128_three_seed_training_summary_v1.json)保存全部11节点指标、30条原始Slurm分配、每seed/arm选中权重的服务器路径及完整SHA。各终态证据：

- seed17：[root](../results/formal_main_v2/libero_10/k128/seed17/training/segment_reviews/3016464.json)、[独立审计](../results/formal_main_v2/libero_10/k128/seed17/training/segment_reviews/3016464_independent.json)、[实际选中SHA](../results/formal_main_v2/libero_10/k128/seed17/training/segment_reviews/3016464_selected_server.json)。
- seed23：[root](../results/formal_main_v2/libero_10/k128/seed23/training/segment_reviews/3021774.json)、[独立审计](../results/formal_main_v2/libero_10/k128/seed23/training/segment_reviews/3021774_independent.json)、[实际选中SHA](../results/formal_main_v2/libero_10/k128/seed23/training/segment_reviews/3021774_selected_server.json)。
- seed41：[root](../results/formal_main_v2/libero_10/k128/seed41/training/segment_reviews/3021781.json)、[独立审计](../results/formal_main_v2/libero_10/k128/seed41/training/segment_reviews/3021781_independent.json)、[实际选中SHA](../results/formal_main_v2/libero_10/k128/seed41/training/segment_reviews/3021781_selected_server.json)。
