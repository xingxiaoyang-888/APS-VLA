# 自动连续训练协调器操作说明

仅新增控制层；173 个科学文件、四套件基座/数据/初始化、5000 更新、batch8、每500完整验证、每50断点与选模规则不变。原 wrapper 保持原字节，sbatch 显式48小时、runner目标5000/软时限169200秒。真实GPU同源验收由 root 的继承收据提供，本次 CPU 测试不冒称新增 GPU 验收。

## 模块与权限

- controller.py：唯一进程 lease、共享 writer lock、全部登记作业核对、8 GPU/每pair单活动、pending-before-sbatch、状态CAS与完整事件日志。
- backend.py（候选名 formal_backend.py）：原pull/reviewer与执行适配桥接；不调用原refresh，不再次取得 writer lock，不改监督state。
- worker.py：原pull函数+原review(False)完整重建，SHA读取已登记两resume（最终另两best），不加载tensor。机器封装保留原 status=local_passed_remote_required，明确非人工/非独立收据。
- execution.py：train64 的已独审纯执行适配；只有执行目标/时限变化。
- root 负责发布原字节、激活配置、0GPU CPU Slurm服务登记/启动、Git同步。协调器没有Git认证，不控制非本项目作业，不释放final。

## 激活

正式文件放 scripts/ops/formal_autonomous_training_v1，activation 的 path+SHA 使用实际发布路径。候选本身不能激活。必需字段：

schema=formal_main_v2；kind=autonomous_training_root_activation；
version=cti-autonomous-training-controller-v1；
status=approved_for_registered_continuous_training；
control_root=R；runtime_root=P；controller_sha256；
backend、worker、execution_adapter、registration、execution_authorization；
cpu_preflight、cpu_preflight_root、controller_independent_review、execution_independent_review、
inherited_scientific_admission（以上均 {path,sha256}）；
gpu_evidence_mode=inherited_same_source_F00_F01_F03_and_completed5000；
controller_run_root=results/formal_main_v2/autonomous_training/run_v1；
poll_seconds=60；final_release_authorized=false；
limits={max_gpu_jobs:8,total_pairs:36,total_selectors:72,target_updates:5000,
wall_seconds:172800,soft_wall_seconds:169200,validation_every_updates:500,
checkpoint_every_updates:50,excluded_nodes:[gpu4020]}。

独立CPU收据必须精确kind/status、无blockers，files涵盖实际发布四源码SHA。root可把既有14对完成项预置到 autonomous_training_v1.completed_pairs，以 inherited_root_and_independent_review 明确标来源；evidence_refs绑定旧root/ind/selected及当前继承收据，不能生成伪机器重算记录。

controller --activation REL --activation-sha256 SHA --check-only 只读验证全部激活/源码/继承selected SHA，不写state、不起服务、不提交。CPU服务不传此flag。
--once 仍有生产副作用：实际占lease/writer锁、核Slurm、可能回存/机器审计/发布invocation/提交至多一个job。必须是登记gpus0且activationSHA相同的CPU Slurm作业。

服务建议 root 已决定的 intel、1 CPU、16GiB、7天、0GPU。实际新GPU TimeLimit 由 root 首次 scontrol 读取对账；本候选保存真实提交argv，不把argv当实测TimeLimit。

## 事务与监督

生命周期锁：<controller_run_root>/controller.lease.lock，fcntl flock进程全程持有；第二实例拒绝。owner.json记录owner_id/pid/hostname/coordinator_job_id/activationSHA。锁文件不能unlink重建。
共享短事务锁：results/experiment_supervisor/.writer.lock。heartbeat/人工操作须使用同锁，不得直接覆盖state。正常锁竞争下个周期再试，不是科学失败。

每周期先查询所有登记ID。UNKNOWN/缺行/短暂不可见及不确定提交不能当空槽。已明确登记gpus0且实测分配0的CPU作业不占GPU；其它所有模式GPU包括engineering/development占槽。已失败pair默认hold，只有root另行审核修复才能迁入。
Slurm新job保持cti-formal名称，comment=cti-auto-v1:<完整token>，固定--exclude=gpu4020；不影响已健康运行作业。
任何sbatch前state原子fsync pending，保存token/真实argv/完整plan。超时、异常、非0或模糊响应保留pending，永不自动重发。即使已返回jobID但state写失败也保留原pending。root须结合精确comment/token与Slurm事实处理后才能清除；“未看到”不能直接重试。
后台原pull仅独立.pull.lock，无state写；原False reviewer在同一外层锁内工作。controller先CAS保存真实终态，子worker据精确registry SHA校验；子进程前后state不变，最后controller再CAS提交控制状态。

机器验收正常partial仅允许原clean softwall路径，保持真实A/B不齐和已完成A跳过；FAILED/TIMEOUT/PREEMPTED/缺journal不自动续。最终完成必须两臂5000、11完整验证、原选模/部署收据、实际bestSHA；不会5500或扩矩阵。
blocked_pairs保存history SHA，相同失败不每分钟重做重型审计；修复后root在writer锁内清除此pair阻断才重新审核。已完成证据小文件每次hash；大raw文件缓存最多300秒，stat变化立即重hash，每次实际提交前强制全部evidence SHA。共享FS时间戳可能粗，缓存期内同size/同时间戳大raw改写不保证即时发现；最终/提交门必须完整hash，非权限安全边界。

formal_main_progress保留原人工completed entry，自动新增项明确machine；更新trained_arms/verified progress/active tracking。全部实际分配GPU秒唯一计总账，不叠加phase。训练完成服务退出，不扩大范围。

root需要临时为工程作业留槽时，在writer锁+state CAS内写：
autonomous_training_v1.root_submission_hold={
 enabled:true,reason:"明确原因",root_record:{path:"新root登记.json",sha256:"实际SHA"},
 requested_utc:"实际UTC"
}
或 reserved_GPU_slots:1 与 reservation_root_record:{path,sha256}。
这只暂停新训练提交，健康作业继续，终态仍机器复核；工程请求登记后root释放hold/reserve，工程GPU本身计入8槽。服务不接受任意shell命令。

SIGTERM/SIGINT停止新cycle并释放kernel锁；既有GPU继续。重启同activation/run_root，重新登记新CPUjob，pending保持，不会重发。服务7天终止或异常时root监督明确重启；不是无期限login daemon。

## 日志与测试

events/index.json列顺序固定64MiB sealed chunks及SHA/bytes/首末序号/末事件SHA；每行带sequence和前一事件SHA，active chunk完整保留。重启验证整链，截断/矛盾失败不裁剪。无事件过滤；root可按已有codec交付，不把凭据写入日志。

作者历史：attempt01原30过；attempt02 44过1真实缓存失效；attempt03修后45过。缓存失败的source/XML/log保留，没有伪称fixture问题。Object续跑首个check-only因metadata历史与当前pull均被读到，原“只有一个pull”假设拒绝；修为精确选择含当前job的已SHA绑定pull，历史证据仍由原review完整核验。False reviewer无evidence_sha256字段，桥接捕获实际原Evidence实例hashes，summary不改。
真实read-only 5路径：fresh Goal256 seed23、Object64 seed41 resume500、Object/Goal/Spatial128 seed17 complete5000；0提交、0invocation发布、无state更改。backend支持 --output-directory .local/autonomous_training_v1/audit/唯一目录供独审；生产review_pair(check_only=False)会写原pull/results和机器收据，需root授权，仍本函数不会发布invocation/sbatch。

## Root activation launcher

`activate.py --activation REL --activation-sha256 SHA --wrapper scripts/ops/formal_autonomous_training_v1/service.slurm --wrapper-sha256 SHA` verifies without submission. Add `--submit` only for the first registered root activation. It holds the CPU allocation until pending intent and actual job ID are durably registered, releases both filesystem locks, then calls `scontrol release` for that exact job. Never rerun after an ambiguous response. Existing CPU probe3034099 stores actual output in R and an exact-byte nonweight mirror in P for the original puller; the amendment is retained.
