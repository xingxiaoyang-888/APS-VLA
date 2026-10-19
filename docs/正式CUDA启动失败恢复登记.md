# 正式 CUDA 启动失败恢复登记

2026-10-19 15:56：首个登记失败3028460通过专属预约、全登记容量和双次现场证据检查，由root单次提交为3039258；实际gpu4010、1张L40、4小时、no-requeue、exclude gpu4020，目标仍500步。A已出现正常训练更新，完整恢复验收未完成；终态复核后才另行版本化5000准入。旧失败及blocked历史不变，3028468/3028522尚未提交，未激活第二CUDA预约。[本轮凭据](../results/formal_main_v2/preflight/heartbeat_20261019T1347/summary.json)。

本登记仅处理3个已保留的CUDA启动失败，不改变方法、5000步总调度、每500步验证、数据、选模或最终集门槛。当前正常训练由CPU控制器3034538持续运行；异常恢复由root通过独立入口单次提交。

| 原失败作业 | Pair | 经原始证据核验的起点 | 本次唯一恢复目标 | 保留失败成本 |
|---|---|---|---|---|
| 3028460 | Object256 seed23 | A/B均0步，cursor0 | A/B各500步 | 84 GPU秒 |
| 3028468 | Object64 seed23 | A/B均0步，cursor0 | A/B各500步 | 69 GPU秒 |
| 3028522 | Spatial64 seed23 | A/B均1000步，cursor8000 | A/B各1500步 | 73 GPU秒 |

当前状态：服务器恢复入口已通过46项作者CPU检查、20项独立检查；root重核1094份独审引用，已登记三个精确原目标的单次恢复。尚未提交、未激活任何CUDA专用槽位；226 GPU秒及FAILED/blocked历史完整保留。检查时两Object checkpoint根仍不存在；Spatial双resume实际SHA与1000步边界一致，未加载tensor。不能据此声称GPU恢复成功或节点硬件故障已证明。

三份授权分别为 [3028460](../configs/experiments/formal_main_v2_cuda_single_recovery_3028460_v1.json)、[3028468](../configs/experiments/formal_main_v2_cuda_single_recovery_3028468_v1.json)、[3028522](../configs/experiments/formal_main_v2_cuda_single_recovery_3028522_v1.json)。[root整合收据](../results/formal_main_v2/preflight/heartbeat_20261019T0340/cuda_recovery_gateway_root_review.json)绑定全部修复记录、预约、作者/独审和源码哈希。每个请求只准一次、1张L40、Slurm4小时、原soft wall12600秒，保留完整优化器/RNG/样本游标，使用原wrapper和--resume，排除gpu4020且不重排队。

共享writer锁与CAS保护全部状态事务。先查询全部登记作业；只有登记及账单同时确认0GPU的CPU作业不计槽，未知状态、pending、同pair活动或满8槽均阻断。root必须先激活该请求自己的预约，再完成默认完整检查；不能使用动作验收v4的预约。检查原P输出全集、冻结P/S来源、Object根缺失或Spatial两resume的SHA，并在哈希核验后重新查询容量。

提交顺序为持久化pending、独占发布新invocation、sbatch、记录唯一新job ID、登记receipt和state，最后消费预约。模糊响应、旧ID、写入失败和不确定状态保留pending与完整原始记录，不清除后重发。root统一提交，健康作业不取消。

唯一存储适配是Spatial旧root边界收据仅存R：只允许canonical proof绑定的精确previous_boundary_review路径、SHA和字节数在R验证，不豁免任何运行产物目录。历史词法路径检查及该存储问题的首次版本和修正证据全部保留。

真实恢复完成后必须先回存非权重结果、核验终态和完整恢复/验证/选模证据；失败则停止该pair。接入自动连续5000仍须验证实际成功产物并进行单独版本化准入，不能直接清除历史阻断或让旧production reviewer忽略失败。最终集、动作执行GPU门槛均不受此登记放宽。

操作入口及全部字段见[服务器恢复入口说明](../results/formal_main_v2/engineering/cuda_recovery_autonomous_1940/README.md)。执行源保留在服务器R/.local/cuda_recovery_autonomous_1940；Git可见归档是原字节副本。入口gateway.py SHA为c97b66100a0a21a722b17e32129b7a220fac7b2b2cb8b9cc9678b88f605476c3，必须通过已审server_control_transport_v1及精确SHA运行。权重/checkpoint只留服务器，非权重证据同步GitHub。
