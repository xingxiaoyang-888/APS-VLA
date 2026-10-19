# 正式 CUDA 启动失败恢复登记

2026-10-20 06:00 CST 更新：50/72组机器训练完成，其中48/72组通过root/独立复核，Object64 seed41待审；8卡活动，累计425.456 GPU小时（非最终）。Spatial64 seed23原1500步恢复通过双审，连续5000入口已登记未提交；Long128 seed23开发200条作业3043709运行，提交登记延迟已按原token对账，无重复提交。未新增已验收闭环结果，最终0/35200封存。[本轮收据](../results/formal_main_v2/preflight/heartbeat_20261020T0530/summary.json)。

2026-10-20 03:45 CST 更新：训练48/72组双审通过，新增Object64 seed17 A/B；8卡活动，累计408.551 GPU小时（非最终）。Spatial异常恢复3043399已单次启动，目标1500；下一空槽预留Long128 seed23开发200条。未新增闭环结果，最终0/35200封存。[本轮收据](../results/formal_main_v2/preflight/heartbeat_20261020T0332/summary.json)。

2026-10-20 00:35 CST 快照：正式训练仍为 **46/72组**（Long18、Spatial16、Object10、Goal2），8个GPU作业运行，累计分配 **383.799 GPU小时**，含失败及运行中分配，非最终费用。Object256 seed23的已登记恢复作业3042627在本轮单次日志快照中A已到937步；不将日志进度算作完成验收。

Spatial64 seed23（原3028522）A/B1000步、cursor8000的实际resume字节及授权经root/独审复核，已用writer锁/CAS激活已有精确1槽预约，等待下一真实空槽恢复至1500；正常8卡不取消，原5000调度不变。预约不是额外占用GPU，本轮未提交新作业；实际恢复后仍须复核再准入连续5000。

Spatial开发attempt03仅完成不可执行的准备与审查：作者41项、独立23项CPU检查；原12条终态/25行账本、3022743与3042529合计395 GPU秒完整保留，仅计划剩余588条。既有P侧输入与未改wrapper检查通过，但最新失败审阅、规划及零trial作业费用消费接口尚未接入，新readiness和授权未生成，**保持HOLD_PRODUCTION**。原字段original_scientific_wrapper_executed恒False不能独自证明新child未启动，本案依据精确父verify异常复现、控制流、空产物及未变前缀的组合证据。173冻结文件未改，最终仍0/35200，正常训练交控制器和后续定时监督。[本轮收据](../results/formal_main_v2/preflight/heartbeat_20261020T0021/summary.json)。

2026-10-19 19:45 CST：新增独立入口 scripts/ops/formal_cuda_continuous_admission_v1 与授权 configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json，精确Object256 seed23从A/B500、cursor4000恢复至5000；48小时分配、169200秒软时限，11次验证。作者38项CPU检查、独立20项入口＋3项原控制器pending检查通过；实际canonical原日志重建及211份服务器输入、两resume SHA通过。历史84＋6512＝6596 GPU秒保留；本次只做hash-only预检，完整optimizer/RNG/cursor由实际恢复训练加载验证。当前8满且Spatial保留1槽，未提交；正常控制器不接管异常历史。若该次软时限仍未完成或异常，先root重新复核；完成5000需原始证据root和独审后显式继承。其他两组仍待原目标有界恢复。[本轮收据](../results/formal_main_v2/preflight/heartbeat_20261019T1911/summary.json)。

2026-10-19原目标终态验收：3039258 COMPLETED 0:0，Object256 seed23 A/B均500更新、4000实际唯一窗口、0/500各204窗口硬剪枝验证通过root及独立原始复算。原失败3028460没有初始化/训练checkpoint，故此次resumed=false正确，不能称其恢复了原优化器/RNG。新resume字节SHA已核，下一次实际恢复仍由冻结训练核验证完整状态。费用84+6512=6596 GPU秒，FAILED身份保留；另外两组尚未重提。

新增审核器只修旧失败三份外部证据的原作业归属，当前作业及共享run-root仍走原严格pull校验，33项CPU检查通过。保留初版schema/测试脚本错误及全部日志。3039258日志实际由原wrapper写于R，基于真实sacct WorkDir与原wrapper登记镜像到P，原始日志未改。该恢复未获自动5000例外准入，不能直接清blocked或调用旧手动500续跑。[root](../results/formal_main_v2/libero_object/k256/seed23/training/segment_reviews/3039258.json)；[独审](../results/formal_main_v2/libero_object/k256/seed23/training/segment_reviews/3039258_independent.json)。

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
