# Object64 seed23 原500恢复后单次连续候选

范围仅 libero_object_k64_seed23。FAILED3028468 的69 GPU秒及 COMPLETED3044017 的5141 GPU秒全部保留，历史合计5210秒。两臂500步、cursor4000；本候选只允许一次 attempt03 从该断点继续至5000，不清除 controller blocked，不改变任何预约，也不做自动失败重试。当前只通过CPU作者验收，未发布、未签新root授权、未提交。

## 最小适配

沿已审Object256候选 admission65a6a6…/gatewaya0f81f…原字节生成，仅改变明确pair、预算、job IDs、费用、三份当前终态证据和新版本/路径/token。原Object metadata wrapper、watched_files、repair_record、数据/初始化/40000样本顺序和科学argv保持；仅target改5000、soft wall改169200秒、注册时间和segment_end改变，再附加独立continuous_admission合同。

新命名空间为 scripts/ops/formal_object64_cuda_continuous_admission_v1/，VERSION=object64-cuda-continuous-admission-v1。原root reviewer使用已经发布的canonical同SHA源码，不伪装为旧.local路径。独审writer当前字段逐一匹配，包括replay=0、unique4000、原500恢复实际冷启动False；冷启动字段描述过去的3044017，不表示未来500→5000丢弃恢复状态。

source_identity_diff.patch 是完整两文件diff。原共享writer锁、state CAS、controller owner/lease、全登记GPU/UNKNOWN、实证CPU0豁免、8槽与所有预约、same-pair唯一、pending-before-publication、发布后强制checkpoint再hash、strict ACK/token corroboration等事务保持原算法。发生模糊结果保留pending，不重发。新调度token为 cti-object64-continuous-v1:<authorizationSHA>；job的startup_recovery明确为新连续调度metadata，不冒称旧原目标授权。

## 已执行的作者检查

- 55项CPU测试：真实旧controller锁/CAS/capacity与identity函数；Slurm、Science、IO仅在私有合成项目替代。测试临时副本可由源和小fixture重建，不作真实GPU证据。
- 实际 Science.prepare：在共享writer锁下只读完整266行registry，保留精确两个本pair job，重跑原未改startup-aware reviewer(False)并逐字段对照已签root，严格复核当前root/独审全部SHA。
- 211份真实P/S非权重metadata/source/raw逐SHA核验。
- 未读取真实checkpoint字节。本次权限限制下，actual_server_resume_checks只消费刚签root/独审相同两份证明；没有运行真实NativeIO，也没有Slurm查询或Gateway.run。提交前root仍必须执行原NativeIO精确双resume SHA与发布后重核，以及实际all-registry/owner/lease/容量门。
- 没有测试失败或原始prepare失败。生成器在真实独审字段确认后保留原replay=0检查，增加明确负例；此前准备版本源保留。收据编排曾因工具字符串语法在远端执行前失败，独立记录且0GPU。所有真实stdout/stderr、XML、完整命令和transport日志均保留。
- 本次只引用新Object64终态收据，未继承旧Object256运维文档证据map；当前服务器文档d7f045…保持不变。任何新证据漂移仍拒绝，不做docs豁免。

## 发布与root后续入口（本轮不执行）

publication_map.json 列出两份候选到canonical R路径的原字节映射。这两文件是控制代码；P原Object wrapper及211份输入已经实际检查，S173不改。未来inv只由已通过root门的事务在pending之后发布到R/P。

独立CPU审核必须为 schema=formal_main_v2、kind=object64_cuda_continuous_admission_independent_CPU_review、status=passed_CPU_review、blockers=[]、files恰好两项canonical源路径及最终SHA。

authorization_draft.json 为 draft_not_authorized，reviewed_by/independent_review/root_review均为空。它不能执行。root应在独审和原字节发布后另签唯一新文件，例如 configs/experiments/formal_main_v2_object64_cuda_continuous_3044017_v1.json；新typed kind为 root_object64_cuda_recovered_continuous_admission_authorization，status必须 approved_exact_once_500_to5000，原两失败/成功账单与当前3refs不可换成旧pair。不得重用3028468原目标授权。

在服务器R经已审 server_control_transport_v1/run_server_control.py、当前bundle SHA 3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149 和新gateway精确SHA运行：
--authorization <root新相对路径> --authorization-sha256 <SHA> --gateway-sha256 <SHA>。
默认无提交；仅root明确增加 --submit --root-reviewed-submit 才能在同锁全部门通过后请求一次1L40、48h、169200软墙、exclude gpu4020、no-requeue。实际sbatch工作目录及stdout/err均为P。满槽、预约、UNKNOWN或pending存在均拒绝，不能为本候选抢占已有作业。

后续5000终态必须按保留全部三个job的startup-aware链重新审核，11节点、每臂40000次使用、earliest-best、部署/selected真实SHA和全部GPU费用齐全后才可计完整训练。软墙未完或新异常不由此网关自动恢复；继承正常controller completed状态仍需单独root流程。无final开放权限。
