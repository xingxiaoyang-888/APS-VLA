from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
B=R/'results/formal_main_v2/preflight/heartbeat_20261019T1609'
E=R/'results/formal_main_v2/engineering/action_deployment_candidates_0809'
PREFIX='scripts/ops/formal_action_deployment_v1/'
SOURCES={
 'runtime_scope.py':('.local/action_deployment_runtime_0809/runtime.py','6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53'),
 'contract.py':('.local/action_downstream_integration_0809/contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19'),
 'wrapper.py':('.local/action_downstream_integration_0809/wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33'),
 'entry.py':('.local/action_downstream_integration_0809/entry.py','2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19'),
 'gateway.py':('.local/action_downstream_gateway_0809/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'),
 'reviewer.py':('.local/action_downstream_consumers_0809/reviewer.py','9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd'),
 'consumer.py':('.local/action_downstream_consumers_0809/consumer.py','16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034')}
AUDITS={
 '.local/action_deployment_chain_independent_0809/independent_review.json':'11faf80f66e35172eb8b155a3a6514b43d58c7ba5613496b36fd7b55e05691cd',
 '.local/action_gateway_consumers_independent_0809/gateway_independent_review.json':'c232149639a1e6335189610aebba19830e1a3c8bfe9b932d1398566f10cd2b4f',
 '.local/action_gateway_consumers_independent_0809/raw_consumer_independent_review.json':'3f815f3a48755e16e01219eb7f24c2b3fcb84e65d769d1e0a1d141a84d769479'}
TYPED={
 '.local/action_deployment_chain_independent_0809/runtime_component_independent_projection.json':'927cb53f1b06d01c0d49ea86449d0aeb62aa6ec6285045e6d9d6d3c4ea77abc4',
 '.local/action_deployment_chain_independent_0809/wrapper_component_independent_projection.json':'14bfa92531e1e895ffe0da595b508810e1454333d74db5fbcc12acb1cf1ae146'}
DIRECTORIES=('action_deployment_runtime_0809','action_downstream_integration_0809','action_downstream_gateway_0809','action_downstream_consumers_0809','action_deployment_independent_0809','action_gateway_consumers_independent_0809','action_deployment_chain_independent_0809')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for v in iter(lambda:f.read(8<<20),b''):h.update(v)
 return h.hexdigest()
def raw(path):
 assert path.resolve()==path and path.is_file()
 before=path.stat();data=path.read_bytes();after=path.stat()
 assert (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)
 return data
def put(path,data):
 assert path.resolve()==path and not path.exists();path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 assert path.read_bytes()==data
 return {'path':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
def obj(path,value):return put(path,(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def ref(path):return {'path':path.relative_to(R).as_posix(),'sha256':sha(path)}
def pin(path,expected):assert sha(path)==expected,(str(path),sha(path),expected)
def frozen():
 q=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';pin(q,'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 v=json.loads(q.read_bytes());assert len(v['files'])==173
 for rel,h in v['files'].items():pin(R/rel,h);pin(S/rel,h)
 return dict(files_per_root=173,roots=[str(R),str(S)],all_unchanged=True,inventory=ref(q))
def prepend(path,text):
 old=path.read_text();first,rest=old.split('\n',1);path.write_text(first+'\n\n'+text+'\n'+rest,encoding='utf-8')
assert os.name=='posix' and Path(__file__).resolve()==R/'.local/deliver_action_candidates_0809.py'
controller=R/'scripts/ops/formal_autonomous_training_v1/controller.py';pin(controller,'acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
sys.path.insert(0,str(controller.parent));sp=importlib.util.spec_from_file_location('action_candidate_delivery_controller',controller);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state_path=R/'results/experiment_supervisor/state.json';state_sha=sha(state_path);state=json.loads(raw(state_path))
 untouched=json.dumps({k:state[k] for k in ('autonomous_training_v1','pending_submission','registered_jobs')},sort_keys=True)
 before=frozen();coverage={}
 for rel,h in AUDITS.items():
  pin(R/rel,h);v=json.loads(raw(R/rel));assert v['review_role']=='independent' and v['status'] in ('passed_CPU_review','passed_CPU_independent_candidate_review')
  assert not v.get('blockers') and v.get('production_chain_complete',False) is False
  coverage.update(v['files'])
 for rel,h in TYPED.items():pin(R/rel,h)
 for name,(source,h) in SOURCES.items():
  pin(R/source,h);assert coverage.get(source,coverage.get(PREFIX+name))==h
  compile(raw(R/source),str(R/source),'exec')
 copied=[];omitted=[]
 for directory in DIRECTORIES:
  folder=R/'.local'/directory;assert folder.is_dir()
  for path in sorted(folder.iterdir()):
   if path.is_dir():omitted.append({'path':path.relative_to(R).as_posix(),'reason':'reconstructible test fixture/cache, retained on server'});continue
   assert path.suffix not in ('.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pyc')
   data=raw(path);assert len(data)<10_000_000
   dest=put(E/directory/path.name,data);copied.append({'origin_path':path.relative_to(R).as_posix(),**dest})
 archive=obj(E/'archive_manifest.json',{'schema':'formal_main_v2','kind':'action_deployment_candidate_archive','status':'immutable_nonweight_copy','files':copied,'excluded_directories':omitted,'originals_deleted':False,'reconstruction':'For .local evidence references use origin_path plus SHA to select archived bytes. Earlier versions retain recorded filenames/SHAs; no old receipt is rewritten. Nested synthetic fixtures are regenerated from retained tests/commands, never real scientific evidence.'})
 published={}
 for name,(source,h) in SOURCES.items():
  target=R/PREFIX/name;put(target,raw(R/source));pin(target,h);published[PREFIX+name]=h
 readme="""# Versioned action deployment candidates

formal-downstream-action-v1 has CPU component author and independent reviews. Seven files are published in the server control repository only. They are not activated in the runtime directory. No per-plan readiness or GPU reservation is issued here.

The immutable inner v1 plan describes scientific inputs; the outer invocation, parent/child journals and consumer use their actual new execution identity. All 173 frozen files, training settings, model/checkpoint identities, panels and timing boundaries remain unchanged.

- runtime_scope: one base per fresh process, exact original metadata/Goal scopes, raw finite 8x7 actions preserved; no future head deployed.
- contract/wrapper/entry: exact source and readiness checks, unchanged legacy runner, separate runtime journal. Development resumes hash only trials.jsonl and closed_loop_report.json before running; all other evidence remains immutable afterward.
- gateway: original pure scientific planner, common writer lock/CAS, controller lease and full capacity accounting, durable pending token, exact queue or scontrol identity. No retry on ambiguity.
- reviewer/consumer: original scientific parsers, complete new action provenance, old receipts consumed through their exact original chain, failures and prior ledger bytes retained. Only exact final_registry metadata is allowed; sealed values and final execution are refused.

Before use, build and independently audit a real unchanged stage plan, source/asset/checkpoint/panel evidence, and explicit root/independent readiness; register a bound reservation and use the gateway. Do not call the old CLI or manually clear pending/history. New-to-new continuation still needs a versioned planning adapter if the original planner cannot rebuild its prior new-version review. Old development receipts are not automatically equivalent to new action semantics for O2A.

Evidence and failed test histories are in results/formal_main_v2/engineering/action_deployment_candidates_0809/archive_manifest.json. Test fixtures explicitly replace GPU and some upstream evidence; CPU pass is not an actual GPU chain, scientific completion, success rate or latency result. Already accepted v4 16-cell GPU engineering is reused, not repeated.
"""
 put(R/PREFIX/'README.md',readme.encode())
 stamp=datetime.now(timezone.utc).isoformat()
 accepted={rel: {'path':next(x['path'] for x in copied if x['origin_path']==rel),'sha256':h} for rel,h in {**AUDITS,**TYPED}.items()}
 integration=obj(B/'action_candidate_root_integration.json',{'schema':'formal_main_v2','kind':'action_deployment_candidate_root_integration','reviewed_by':'root','utc':stamp,'status':'CPU_components_independently_reviewed_control_repo_published_not_activated','execution_version':'formal-downstream-action-v1','canonical_sources':published,'independent_reviews':accepted,'archive':archive,'author_tests':{'runtime':90,'contract':19,'wrapper_reject_paths':9,'gateway_latest_full_independent_replay':78,'consumers':62},'independent_tests':{'runtime_and_entry_new_cases':20,'gateway_new_cases':18,'consumer_new_cases':18},'limits':['Whole actual new GPU wrapper/runtime/consumer chain not executed.','No per-plan production readiness, P publication, GPU reservation, Slurm submission or scientific hold release.','New-to-new planning continuation and old-to-new development action equivalence are separate pending audits.','Old policy_error terminal outcomes remain retained; no repeats or outcome replacement.'],'frozen_before':before,'frozen_after':frozen(),'production_chain_complete':False,'activated':False,'new_GPU_jobs':0,'scientific_settings_changed':False,'final_evaluation_enabled':False})
 pin(B/'observation_after_CPU_integration.json','84786788c1269479565d336d52ae8982e4b6b4e65ae76cd63a8380a253f43dfb')
 pin(B/'active_training_log_observation.json','b64ef65d2a1d169c2ac68641728904b2dd07af302a3ae5ab11ba7a96cf65ec01')
 summary={'schema':'formal_main_v2','kind':'root_supervision_summary','utc':stamp,'observation':ref(B/'observation_after_CPU_integration.json'),'training_log_excerpts':ref(B/'active_training_log_observation.json'),'action_candidate_integration':integration,'trained_arms_observed':42,'matrix_arms':72,'GPU_jobs_observed':8,'formal_allocated_GPU_seconds_as_of_observation':1163942,'formal_GPU_hours_as_of_observation':1163942/3600,'all_project_registered_GPU_seconds_as_of_observation':1184785,'development_trials_retained':1212,'final_trials':0,'controller_normal_training_unchanged':True,'recovery_3039258':'Current attempt A500 report observed; B entered training. Pair target500 not yet terminal accepted.','new_GPU_jobs':0,'weights_copied':False,'local_project_writes':False,'new_scientific_results':False,'next':['Allow healthy automatic training to5000 with every500 validation and max8 GPUs.','Review recovery3039258 only when terminal; retain all three failure histories.','Build actual per-plan action deployment checks and explicit readiness; no duplicate16-cell engineering.','Keep final35200 trials sealed until original global release gates.']}
 summary_ref=obj(B/'summary.json',summary)
 doc="""# 正式动作执行入口接入记录

2026-10-19：formal-downstream-action-v1 七个运行与审核文件已完成组件 CPU 交叉审查，发布到服务器控制仓库。**尚未启用运行目录的新入口，没有新增GPU作业或科学闭环。** v4四套件16格真实工程验收沿用原收据，本轮不重跑；它不等于完整生产入口或成功率/延迟结果。

运行层仅移除与官方原始动作不一致的幅值拒绝，保留8×7形状、有限值、动作原值和部署路径；训练、未来目标、损失、预算、checkpoint与初态面板不变。每进程只加载一次官方基座，元数据/Goal适配上下文和函数绑定退出后恢复。完整计时与组件计时均使用新版本身份。

提交层使用原纯科学规划函数和共享writer锁/CAS；计入所有登记GPU及工程槽，确认CPU控制器owner/lease；提交前持久登记token，真实Slurm对账后才结束pending。sacct空comment必须由精确squeue或scontrol身份补证，不清除不确定提交后重试。

续跑只把同一输出的trials.jsonl和closed_loop_report.json作为开跑前前缀核验项，其余证据运行后仍逐SHA核对。旧科学计划、原日志前缀、成功及policy_error终态全部保留，不重做已终态初态。审核消费新版本的真实父子入口和动作日志；旧收据继续由完整旧审核链解释，不伪装成新运行。

CPU证据：运行层作者90项；根入口19项合同、9项拒绝边界；提交层最终78项及独立18项；消费者作者62项及独立18项。另有运行层/入口20项独立检查。测试中的GPU和部分上游证据替身均有标注，不当作真实训练、闭环或整链生产放行。两处消费者兼容问题（精确final_registry元数据路径、原Evidence接口）已修并复核，失败日志及原版本均保留。

剩余工作是为具体固定开发清单生成真实计划，核对全部来源与checkpoint、发布精确运行文件并签发独立/root就绪证据后，经新网关单次执行。后续新版本续跑若原planner无法消费新review，应另做版本化接入；旧开发结果与新动作语义的等价映射也须另审，不能直接用于O2A放行。本候选不开放final，35200条最终评测仍受原全局release约束。

全部源码、测试、作者与独审、失败原件通过[归档清单](../results/formal_main_v2/engineering/action_deployment_candidates_0809/archive_manifest.json)按来源路径和SHA复原。可重建pytest临时副本不进Git，服务器原件未删；173冻结文件原字节未变。[根接入记录](../results/formal_main_v2/preflight/heartbeat_20261019T1609/action_candidate_root_integration.json)。
"""
 put(R/'docs/正式动作执行入口接入记录.md',doc.encode())
 progress="""2026-10-19本次监督：已验收训练仍 **42/72组**；16:52 CST真实Slurm快照为7个正常连续训练＋1个CUDA原目标恢复，共8卡，控制器owner/lease正常，无pending、重复pair或未知状态。正式轮累计 **323.317222 GPU小时**（含运行中和失败，非最终账单）。运行日志摘录确认正常作业持续更新；恢复3039258的A已完成原500步，B已开始，尚未验收共同500。

新动作执行、提交与原始结果审核入口完成组件CPU交叉审查，七文件已发布到控制仓库；实际新整链尚未运行，不放行新增科学闭环，不重复v4的16格GPU工程验收。修复了Slurm空comment对账、四套件续跑的精确日志前缀分区及两处旧审核接口兼容，全部失败原件保留。173冻结文件、训练设置和科学面板不变，原1212开发记录保留，最终0/35200封存。见[接入记录](正式动作执行入口接入记录.md)与[本轮凭据](../results/formal_main_v2/preflight/heartbeat_20261019T1609/summary.json)。正常训练交自动控制器；下次定时监督处理异常终态和具体评测计划，当前无新增GPU提交。
"""
 for rel in ('docs/实验进度.md','docs/完整实验计划.md','docs/正式主实验规划.md'):prepend(R/rel,progress)
 prepend(R/'docs/正式主实验阶段结论.md','本次仅完成动作部署和结果审核的CPU组件接入与独审，没有新增正式成功率或完整延迟结果。42/72组已验收、8卡运行（16:52 CST快照），323.317222 GPU小时为运行中账单。不能据工程通过或离线损失判断未来监督有效；完整新运行证据与最终全局release仍待完成。[接入边界](正式动作执行入口接入记录.md)。\n')
 issue=state['formal_main_progress']['downstream_action_range_issue']
 issue['status']='v4_GPU_passed_new_deployment_CPU_components_published_actual_plan_readiness_pending'
 issue['new_rollouts_held']=True;issue['server_action_deployment_candidate']={k:integration[k] for k in ('path','sha256')}
 issue['candidate_runtime_sources']=published;issue['production_chain_complete']=False
 state['last_supervision_utc']=stamp;state['last_root_supervision_snapshot']=summary_ref
 state['current_work']='正常训练由CPU控制器自动连续至5000；新动作部署七文件CPU组件交叉审查并回存，实际具体计划及新整链运行待验收；CUDA恢复3039258待终态。'
 state['next_actions']=summary['next']
 assert untouched==json.dumps({k:state[k] for k in ('autonomous_training_v1','pending_submission','registered_jobs')},sort_keys=True)
 c.atomic_json(state_path,state,state_sha)
 record=obj(B/'state_and_docs_update.json',{'schema':'formal_main_v2','kind':'root_candidate_delivery_state_update','state_before_sha256':state_sha,'state_after_sha256':sha(state_path),'untouched_fields':['autonomous_training_v1','pending_submission','registered_jobs'],'summary':summary_ref,'documents':[ref(R/x) for x in ('docs/实验进度.md','docs/完整实验计划.md','docs/正式主实验规划.md','docs/正式主实验阶段结论.md','docs/正式动作执行入口接入记录.md')],'frozen_check':frozen(),'new_GPU_jobs':0,'activated':False})
 print(json.dumps({'summary':summary_ref,'integration':integration,'archive':archive,'canonical_files':published,'copied_artifacts':len(copied),'state_update':record},ensure_ascii=False))
