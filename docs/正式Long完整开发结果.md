# Long 完整开发结果

2026-10-20 19:03 CST：训练 **62/72组双审完成**（Long18、Spatial16、Object16、Goal12），5卡运行，累计 **517.320 GPU小时**（全部登记分配，非最终）。Long等价证明与统计复核没有额外GPU作业；后续非Long开发批次另记成本。

Long旧600通过root与独立来源/动作审查，并由新显式CPU证明入口实际验收，无需重跑。旧执行版本保留；不冒称历史实例哈希捕获，10531GPU秒早已计账。Long全部22个部署实例的开发结果现可汇总：**1600条新版实际执行＋600条旧版等价证明＝2200条，仍只有100个唯一初态**。原2812条历史与新记录全部保留，另612条历史记录未因此准入。

| 总tokens | A三seed均值 | B三seed均值 | B−A | 95%配对区间 |
|---:|---:|---:|---:|---:|
| 256 | 92.67% | 95.00% | +2.33pp | [-1.00, 6.00]pp |
| 128 | 95.67% | 93.00% | -2.67pp | [-4.33, -1.00]pp |
| 64 | 87.33% | 90.33% | +3.00pp | [-0.33, 6.33]pp |

主预算128的均值为负；256与64的区间跨零，不能据此声称稳定收益或等效。Dense94%；均匀256/128/64为91%/77%/39%，均各100条共享参考，不复制为三seed。以上全部是开发结果，无O2A实测加速结论。

正常训练交自动控制器；下一步准备其他套件已验收组的并行开发任务。全局consumer接入、88身份/四套件冻结、完整O2A与最终release仍未完成；最终0/35200封存，173科学文件不变。

[本轮证据](../results/formal_main_v2/preflight/heartbeat_20261020T1832/summary.json)，[Long完整开发汇总](正式Long完整开发结果.md)。

## 逐种子结果

| 总tokens | seed | A成功率 | B成功率 | B−A |
|---:|---:|---:|---:|---:|
| 256 | 17 | 92% | 95% | +3pp |
| 256 | 23 | 94% | 96% | +2pp |
| 256 | 41 | 92% | 94% | +2pp |
| 128 | 17 | 97% | 95% | -2pp |
| 128 | 23 | 95% | 92% | -3pp |
| 128 | 41 | 95% | 92% | -3pp |
| 64 | 17 | 87% | 88% | +1pp |
| 64 | 23 | 85% | 89% | +4pp |
| 64 | 41 | 90% | 94% | +4pp |

## 证据与统计范围

Long开发历史分配共35,408GPU秒（9.836小时），已含在项目总账，本轮不重复加算。任务内初态为簇，每次抽样携带完整三seed；10任务等权、每任务10开发初态，bootstrap10000次，seed20261016，95%百分位区间。报告seed标准差ddof=1，未把重复seed算作新初态。逐任务成功数、A/B配对不一致计数、对Dense/均匀的差值及区间见原始统计JSON。旧600的每条映射绑定原始chunk/执行动作、checkpoint、初态、执行版本及真实Slurm成本；新API无future头、模拟器重放、GPU提交或final授权。

[统计原件](../results/formal_main_v2/preflight/heartbeat_20261020T1832/Long22_development_statistics.json)、[独立统计验收](../results/formal_main_v2/engineering/supervision_delivery_1032/Long22_statistics_independent/independent_review.json)、[逐初态向量](../results/formal_main_v2/preflight/heartbeat_20261020T1832/Long22_paired_development_states.json)、[全部bootstrap抽样结果](../results/formal_main_v2/preflight/heartbeat_20261020T1832/Long22_bootstrap_draws.json)、[旧600显式证明](../results/formal_main_v2/preflight/heartbeat_20261020T1832/Long_legacy600_development_compatibility_proof.json)。

此前未能证实历史源码连续性的审计保留；本轮用安装包全量字节与早于旧作业的inode ctime补足来源连续性，推断范围按普通文件系统语义明确登记。没有将来源推断写成旧运行时实例测量。新显式接口当前仅用于这600条开发证明；通用全局冻结消费者未被改写。所有结果仍须遵守最终冻结与评测规则。
