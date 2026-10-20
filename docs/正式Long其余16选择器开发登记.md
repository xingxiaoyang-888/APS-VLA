# 正式Long其余16选择器开发登记

2026-10-20 14:48 CST：62/72训练组双审通过；Object256 seed23 A/B完成5000步，原失败与恢复成本保留。本次Long256 seed17/23新增400条开发双审通过，A/B分别92/95与94/96，配对+3/+2个百分点。当前语义800条共享100初态，旧1212条另列；完整延迟及三seed结论未完成。新开发3047152/3047156/3047163各200条待验收，共8卡活动，累计493.306 GPU小时（非最终）。最终0/35200继续封存，173科学文件不变。[证据](../results/formal_main_v2/preflight/heartbeat_20261020T1426/summary.json)。

2026-10-20 13:48 CST：60/72组训练双审通过；新增Goal128 seed41 A/B各5000步，本次新增9000已审更新。Long128 seed41开发200条双审通过，A95%、B92%、配对−3个百分点；seed23/41同100初态，400条当前语义结果与1212条历史结果分列。Long256 seed17/23新作业3046779/3046798各200条待验收，两次均单次提交。8卡活动，累计485.781 GPU小时（非最终）。未形成完整延迟/三seed结论，最终0/35200封存，173科学文件不变。[证据](../results/formal_main_v2/preflight/heartbeat_20261020T1330/summary.json)。

2026-10-20 12:42 CST：58/72组训练双审通过，新增Goal128 seed23 A/B各5000步、累计11×186验证，均按原规则选3000步；本轮只增加8000已审更新。Long128 seed41原登记200条开发评测已单次启动（3045322），记账延迟按原ACK核对无重发。8卡活动，正式轮累计477.288 GPU小时（非最终）。历史开发1412条保留，新评测待验收；最终0/35200封存。173科学文件不变，非权重结果完整归档，权重仅服务器。[本轮证据](../results/formal_main_v2/preflight/heartbeat_20261020T1228/summary.json)。

2026-10-20 06:46 CST 更新：50/72组训练双审通过，新增Object64 seed41两组；8卡活动，累计431.508 GPU小时（非最终）。Long128 seed23新增200开发trial验收完成，A95%/B92%，配对差−3个百分点；属于100共同初态的单seed开发结果，未完成完整延迟或三seed结论。原记录和负结果保留，最终0/35200封存。[本轮收据](../results/formal_main_v2/preflight/heartbeat_20261020T0632/summary.json)。

2026-10-20 06:00 CST 更新：50/72组机器训练完成，其中48/72组通过root/独立复核，Object64 seed41待审；8卡活动，累计425.456 GPU小时（非最终）。Spatial64 seed23原1500步恢复通过双审，连续5000入口已登记未提交；Long128 seed23开发200条作业3043709运行，提交登记延迟已按原token对账，无重复提交。未新增已验收闭环结果，最终0/35200封存。[本轮收据](../results/formal_main_v2/preflight/heartbeat_20261020T0530/summary.json)。

2026-10-20 03:45 CST 更新：训练48/72组双审通过，新增Object64 seed17 A/B；8卡活动，累计408.551 GPU小时（非最终）。Spatial异常恢复3043399已单次启动，目标1500；下一空槽预留Long128 seed23开发200条。未新增闭环结果，最终0/35200封存。[本轮收据](../results/formal_main_v2/preflight/heartbeat_20261020T0332/summary.json)。

2026-10-20 02:45 CST 监督快照：正式训练仍 **46/72组**（Long18、Spatial16、Object10、Goal2），**8卡运行，累计401.066111 GPU小时**，含失败和运行中分配，非最终成本。本轮完成Long其余16选择器的8份开发运行入口验收：作者42项、独立39项检查，root和另一独审各执行8次真实P端完整wrapper校验。科学方法、原checkpoint、100个共同开发初态及173冻结文件不变；没有新增训练完成量或闭环结果。

8份readiness与一次性提交授权已登记，专属预约均未激活；下一实际空槽仍优先Spatial64seed23的已批准CUDA恢复。恢复预约正确消费后，root按本批顺序、实时容量和唯一请求保护启用开发评测。现有1212条结果及费用保留，最终0/35200封存；正常训练交控制器和下次定时监督。

[本轮收据](../results/formal_main_v2/preflight/heartbeat_20261020T0227/summary.json)。

本次canonical目录：results/formal_main_v2/execution/long_remaining16_action_v1_1827/。每pair包含scientific/effective plan、execution contract、root/independent review、readiness、prepared invocation、单次authorization/reservation和实际P入口check。prepared invocation不等于已登记调用；正式invocation仅在真实提交事务发布。每个reservation只属于其本身计划，不能消费Spatial CUDA预约。旧方案HOLD状态保留如下作为历史，本批新readiness仅适用这16方法的fresh development；旧Long6方法的身份处理、完整O2A和最终release另行验收。

2026-10-20 CST。范围仅为正式矩阵中尚无开发闭环的16个Long选择器，科学计划已通过作者31项CPU检查、独立18项检查和root复核；原规划器使用完整259条登记记录，无过滤。当前为 **HOLD_PRODUCTION**，没有新GPU提交、开发trial或成功率结论。

| 总token | 训练seed | 方法 | 开发trial |
| --- | --- | --- | --- |
| 128 | 23 | A、B | 200 |
| 128 | 41 | A、B | 200 |
| 256 | 17 | A、B | 200 |
| 256 | 23 | A、B | 200 |
| 256 | 41 | A、B | 200 |
| 64 | 17 | A、B | 200 |
| 64 | 23 | A、B | 200 |
| 64 | 41 | A、B | 200 |

各选择器沿用已训练5000步、按原11次validation选择的checkpoint。root核对了Long全部18个selected checkpoint的实际服务器字节；本轮没有重新训练、重新选模或修改方法ID。每方法使用同一固定10任务×10开发初态；16方法共1600条，不能当成1600个独立初态。面板路径为 configs/manifests/formal_main_v2/libero_10/initial_states/development.json，SHA256为46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268。模拟器seed0、runtime seed17、等待10步、chunk8、最大控制步520不变，最终40初态/任务仍封存。

8个A/B pair分片用于适配固定4小时Slurm资源。旧Long600条开发闭环合计10531 GPU秒，仅作实测资源参考，不保证新分片耗时。原600条、原身份与成本全部保留，原dense、3个uniform、A128seed17、B128seed17的新版动作身份迁移另行处理。当前16个方法没有原开发结果，属于原矩阵的缺项补齐；不重命名已有方法或改变账本来绕过重复运行检查。

8份科学manifest已发布至 results/formal_main_v2/execution/long_remaining16_action_v1_1722/。原规划器实际校验和独立重建全部通过；222个科学运行输入在P中逐SHA匹配，其中本轮按原字节补齐16个。下一步仍需每分片的新版动作外层contract、effective plan、readiness、准备调用及root一次性授权；本登记和旧版inner plan均不授权直接执行。运行前重新核实真实空槽、重复提交、已有产物与checkpoint身份；8卡上限包含工程作业，Spatial64seed23恢复的既有下一槽预约优先。

Spatial旧12条＋新588条混合续跑准备保留为历史且仍HOLD_PRODUCTION，不能据此通过整条执行历史的O2A/最终冻结门槛；不继续用该方案代替统一身份验收。全部旧1212条开发结果、失败及成本保留。本轮7对原始终态审计重建只恢复缺少的canonical收据，另经原下游接口独审14个方法；不增加已完成训练组数，也不冒称新增完整训练独审。

[root准备验收](../results/formal_main_v2/preflight/heartbeat_20261020T0122/Long_development_root_preparation.json)；[本轮总收据](../results/formal_main_v2/preflight/heartbeat_20261020T0122/summary.json)；[终态来源验收](../results/formal_main_v2/preflight/heartbeat_20261020T0122/canonical_source_gate_root_acceptance.json)。
