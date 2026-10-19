# CUDA恢复后单次连续准入候选

仅 Object256 seed23：保留 FAILED3028460（84GPU秒）与 COMPLETED3039258（6512GPU秒），从A/B500、cursor4000继续至5000。此次为控制层候选，尚无root新授权/发布/提交；CPU成功不是GPU运行完成。

## 入口与依赖

主两文件可原字节发布到 `scripts/ops/formal_cuda_continuous_admission_v1/{admission,gateway}.py`。控制根固定R；不按主文件位置猜根。
原字节辅助审核器需发布到 `scripts/formal_cuda_terminal_review_v1/{review_formal_segment_startup,startup_failure_evidence}.py`，SHA固定ee0ef…/c07c…；该两级目录保持它们原有parents[2]==R。主逻辑仅允许这一次已记录同SHA路径迁移，比较原raw重建时仅映射审核器来源路径，其他科学字段不豁免。历史失败/独审中的.local bundle仍作为不可变原始证据读取，不从其执行代码；需保留既有Git归档/可恢复映射，不能改旧收据隐藏路径。

API：
- `Science.prepare(state, auth, auth_ref)`：实际调用原ee0ef reviewer只读重建，严格恰两历史job、6596秒、原root/独审SHA及500边界；不写收据，不查询远端/Slurm。
- `NativeIO.preflight/recheck`：本服务器P/S173、精确run_root文件集合及两resume SHA/bytes；仅hash，不torch反序列化。发布后recheck强制执行，已发布inv也必须精确同SHA。
- `Gateway.run(submit=False)`：默认只读，真实all-registry Slurm观测、共享.writer.lock、CAS、controller owner/activation/hostname和已持有lease、CPU0实际分配、UNKNOWN拒绝、occupied+reserved+1<=8、exactpair无活动、全global pending与已发布inv检查。
- `--submit --root-reviewed-submit`：必须新的typed root授权+本候选实际独审source绑定；先durable pending，才R/P独占发布inv与一次sbatch。ACK全串、旧ID拒绝、新ID写回CAS后用真实queue或scontrol精确comment/name验证，再commit。任何不确定保留pending，不自动重发。原controller看到非空pending只停止提交，不解释此新kind。

新inv保留原科学argv/watch/runtime6/repair_record历史引用；仅改注册时间、两工程参数target5000/softwall169200、segment_end，加独立continuous_admission合同。仍原A再B、初始化/全40000顺序、5000退火/11验证、每50checkpoint，全部数学与源字节不变。repair_record只描述原已完成的恢复。job另加明确新kind/version的startup_recovery调度metadata，使旧registered_comment读到实际新token；不冒称旧目标500授权、不伪装autonomous_control。

实际sbatch仍原metadata wrapper，48h、--no-requeue、exclude gpu4020，显式chdir=P与P/results/slurm/%x_%j.out/.err。正常wrapper资源保持1L40/7CPU/64G。不会消费/修改任何reservation、重启服务或清blocked。

## root未来操作（本轮不执行）

1. 审核作者/独审，发布四源码原字节；历史bundle保留。用author_manifest核精确SHA。
2. 新root授权使用authorization_draft.json所示全字段；签署是root实际新声明，不能把旧恢复授权或作者测试改名当许可。独审引用必须是真实typed收据。只有root将status改为approved_exact_once_500_to5000后另存新文件才可准入。
3. 在R运行：
   python -B scripts/ops/formal_cuda_continuous_admission_v1/gateway.py --authorization <新root相对路径> --authorization-sha256 <SHA> --gateway-sha256 <固定SHA>
   这是只读检查；满槽/保留槽将拒绝。需要真实提交时root在同命令增加两个submit标志。不得提前创建inv/私自挪用Spatial预约。
4. 当前root独审500只授权原500成功。未来job正常5000完成后，先真实全历史pull、ee0ef startup-aware完整重建、actual两best SHA以及独立审计，保留所有三job成本。软墙/新异常/非5000不得视为complete，也不由本网关自动恢复。
5. **未来完成继承不在本候选执行范围。** root可在上述真实终态双审后共享writer/CAS、无pending/无活动本pair时，显式签终态继承记录，将真root+ind+selected/full history refs放入controller.completed_pairs的complete条目（completed_by_arm5000、11节点、selected_checkpoints_verified，verification_kind明确root_and_independent_after_startup_recovery），并先登记formal_main_progress.completed_training_pairs同类型结果，避免原controller._save给新增条目默认machine标签。不要填machine verified_pairs或伪称自动审核；只在此真实5000事实成立后解除该pair旧block。原controller后续只验证completed evidence_refs、计入36对完成，不重新提交。该root继承操作须另行审阅/执行，本候选既不写它也不预填passed。

## 已做验证及边界

pytest_a1=32过；pytest_a2=38过，均临时SERVER项目、fake Slurm和事务Science；真实controller锁/CAS/capacity及既有token核验运行。NativeIO用微小synthetic文件测试篡改/完整恢复，不复制真实checkpoint。typed_gate测试使用真实源码字节与显著合成上游proof，不作真实root签名。

real_prepare_a1.json另使用真实state/原root+独审/raw，原ee0ef只读重建通过（12.995秒）；当时新授权尚不存在且结果明确authorization_validated=false。actual_server_input_check_a1.json用当前NativeIO核真实P/S与两resume byte SHA通过，无模型加载。它不等于新的root准入；传输/完整新GPU调用尚未执行。原173/metadata wrapper/已登记源未改，候选不产生新科学结果。
