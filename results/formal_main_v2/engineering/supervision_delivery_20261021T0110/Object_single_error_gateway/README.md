# Object 单 policy_error 精确原子 gateway 候选

本包只授权准备原 Object task8/source49/dense 的一次新 linked reset 尝试。旧完整100初态、六方法、600清单、全部历史600条和6713 GPU秒保留；599旧兼容采用不变，current新增0。本包没有Slurm提交、canonical/P发布、state/Git修改、封存值读取或科学trial。原10生产文件由root已发布，参考真实发布收据 ef3aa7cd98966fad4f8701e6a922063e2ea5254f7e235e1f049c41123518dc77；新3文件仍私有候选。

## 已验证范围

verify_cpu.py 通过63正例与100拒绝：held一次提交、原ACK、登记前release保护、BaseException/CAS/未知ACK/未知release各边界、终态或缺link旧行拒重复、真实全模式容量/原owner及已释放lease、source/原599完整证据重建。实际read-only projection保留全301登记的sacct原输出、精确argv、UTC、源stateSHA，原状态行未改。陈旧registry仍标RUNNING但实际终态时，连续两次完整sacct确认全部首次终态行逐字段不变，才查询实际live IDs；缺行、未知状态、squeue错误、活动消失均停止。原 controller.py 原字节不变。v1失败和v2通过原件全部保留；v3通过后补充root与nested pending严格拒绝，v4最终源重跑通过。CPU模型的假job9900001仅测试状态机，不计真实成本。

## 接口及源闭包

新增canonical包 scripts/ops/formal_object_single_error_gateway_v1，只含 gateway.py、build.py、run.slurm。publication_map.json给出精确SHA/字节及R/P目的地。旧10文件原字节闭包在source_closure.json。新gateway身份绑定原10完整依赖、原source173、实际plan/repair、599采用原件+独审、actual P verify、new gateway独审、readiness与唯一不可变invocation。原始frozen loop/实际derived loop仍由原10入口分别记载，不混称。

具体root阶段（用publication_map中的真实SHA替换 GATEWAY_SHA / BUILDER_SHA；全部在R运行并按server transport登记）：

1. 审核本包并等待不同agent的源与CPU独审。root按publication_map逐文件精确安装R/P新3源；旧10不改。所有独审原件先归档工程E，不能用私有JSON替代生产证据。
2. 执行 build.py --phase plan --gateway-sha256 GATEWAY_SHA --builder-sha256 BUILDER_SHA --root-reviewed，审阅输出；加 --publish 才会在共享writer锁下写精确root_repair.json、production_independent.json、plan.json到R/P。source independent为已发生独审原报告的透明schema投影，保留原kind/status/reviewed_by、全部production blockers和原SHA，绝不称新GPU已验收。plan始终验证原完整100/6/600。
3. 根先安装原599验证所需精确非权重证据到P。执行 build.py --phase verify --gateway-sha256 GATEWAY_SHA --builder-sha256 BUILDER_SHA --root-reviewed --publish。实际调用 P/scripts/ops/formal_object_single_error_v1/entry.py --verify --plan P/results/formal_main_v2/execution/object_single_error_v1/plan.json --plan-sha256 <实际raw SHA>。stdout与原wrapper独立重建比对，只写actual_P_verification.json，不分配GPU。
4. 独立gateway报告需 schema=formal_main_v2, kind=Object_single_error_gateway_independent_review, status=passed, review_scope=source_and_CPU_only, scope_sha256=2d63670412abc28d3217242151ebf82f309ea93c1bb0e90478d817cf58d4a7b4, blockers=[], production_sources=<原10map>, gateway_files=<新3map>, gateway_source=<canonical gateway path/bytes/SHA>, GPU_execution_authorized=false。实际P验证和独审都齐后，执行 build.py --phase prepare --gateway-sha256 GATEWAY_SHA --builder-sha256 BUILDER_SHA --root-reviewed --gateway-independent <E归档报告相对路径> --gateway-independent-sha256 <原件SHA> --publish。生成readiness、prepared_invocation、明确exact一次authorization；此时尚未创建真实invocation，也未提交。无独审或实际P验证不能构建该阶段。
5. 根核对具体准备结果、未知pending及全部作业后执行 gateway.py --gateway-sha256 GATEWAY_SHA --authorization-sha256 <实际authorization SHA> 进行readonly preflight。唯一提交为同命令加 --submit --root-reviewed。所有新作业必须由该唯一gateway进入。
6. gateway持共享writer锁+CAS，先持久pending/保留1槽，再写不可变R/P invocation，发唯一sbatch --hold --no-requeue，保存原ACK；核 held job完整name/comment/account/资源/output/入口，fresh全模式容量核验后登记原job，再持久release-attempt并仅一次scontrol release。登记包含统一supervision的 name/job_name/experiment/downstream_gateway.actual_sbatch_argv/request_token=完整comment。完成真实release和完整accounting后才清pending；历史登记不覆写。
7. 不确定结果停止。只能同源+同授权 --reconcile --root-reviewed 读取已保存唯一原ACK，不可删除pending、改token、重发sbatch。release-attempt已存在时绝不再次release；实际仍held则HOLD，实际已释放且完整身份/记账一致才补完登记事务。FAILED/TIMEOUT/PREEMPTED等不重试。没有原ACK不允许靠猜jobid恢复。异常持久原事实、成本和失败。
8. 新raw终验仍必须使用原10中的真实 reviewer/consumer 与同源证据，不能用CPU布尔或无动作合成结果代替。无论成功还是负结果仅这一尝试，不结果驱动重跑，不普通resume。最终封存评测仍关闭。

## 尚未通过的生产门槛

- 本新3源尚未canonical发布，也尚未获本包独立审计；root必须在审计后安装。
- 新plan/repair/readiness尚未发布，实际P新plan --verify尚未运行。
- root明确一次授权/真实原子提交尚未运行；不声称GPU已授权。
- 新唯一trial真实raw尚不存在，完整新终态review/consumer未运行。
- 缺证据/任何未知状态必须HOLD，不能为了补齐600伪造599 ledger或query8。
- stage_plan等Python纯构建函数可由CPU测试注入，仅main的canonical路径、exactSHA、root-reviewed与共享锁准许实际写入。CPU假IO无法被生产CLI选中。

## 重跑

run_verify_final.py 是冻结SHA入口，用既有 live_inputs.json 复算CPU和真实来源，不查询Slurm、不写项目状态或新证据。通过已审server transport并pin该文件SHA执行即可。测试逐条清单及错误原文在 CPU_report.json。所有manifest路径相对R，所有新文件只在服务器。

最终nested pending绑定仅读取完全同SHA原state，记录于live_inputs.json/nested_pending_binding；复用已保存双完整sacct，不再次查询Slurm。
