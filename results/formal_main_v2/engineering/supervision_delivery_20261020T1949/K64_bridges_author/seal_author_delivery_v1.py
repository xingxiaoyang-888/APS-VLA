from pathlib import Path
import json,hashlib,datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p);return {'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def put(n,x):
 p=D/n;p.write_text(x if isinstance(x,str) else json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+'\n');return ref(p)
source=json.loads((D/'source_publication_manifest_v2.json').read_text());plans=json.loads((D/'static_plan_publication_candidate.json').read_text());rows=[]
for p in source['pairs']:
 suite=p['suite'].split('_',1)[1];pol=json.loads((D/suite/'revision02/package/policy_v1.json').read_text());cpu=D/suite/'control_CPU_attempt03/cpu_report.json';report=json.loads(cpu.read_text());assert report['status']=='passed_CPU_control_candidate_only'
 rows.append({'suite':p['suite'],'method_ids':['A64_seed23','B64_seed23'],'candidate_scope':'first full200 development only','canonical_sources':p['files'],'execution_manifest':p['manifest'],'CPU_report':ref(cpu),'checks':report['checks'],'negative_cases':report['negative_cases'],'actual_original_FrozenPlan_rebuilt':True,'actual_original_terminal_science_context_rebuilt':True,'actual_P_scientific_wrapper_verified':True,'actual_P_action_wrapper_acceptance':False,'actual_P_action_wrapper_missing_readiness_rejected':True,'failed_job_id':pol['failure_job_id'],'all_job_ids':pol['all_job_ids'],'allocation_seconds':pol['allocation_seconds'],'all_pair_GPU_seconds_already_accounted':pol['total_GPU_seconds'],'failed_GPU_seconds_already_accounted':pol['failed_GPU_seconds'],'selected_checkpoints':pol['selected_checkpoints'],'historical_source_refs':pol['references'],'plan':next(x for x in plans['pairs'] if x['suite']==p['suite'])})
external=[]
for rel in ['results/formal_main_v2/preflight/heartbeat_20261021T0349/k64_candidate_publication.json','results/formal_main_v2/preflight/heartbeat_20261021T0349/k64_pair_config_dependency_publication.json','results/formal_main_v2/preflight/heartbeat_20261021T0349/k64_static_plan_publication.json']:external.append(ref(R/rel))
for name in ['k64s23_bridge_build','k64s23_bridge_manifests_CPU','k64s23_bridge_manifests_CPU_v2','k64s23_control_build','k64s23_spatial_control_CPU_v1','k64s23_object_control_CPU_v1','k64s23_spatial_control_CPU_v2','k64s23_object_control_CPU_v2','k64s23_actual_server_bytes','k64s23_prepare_static_plans','k64s23_spatial_control_CPU_v3','k64s23_object_control_CPU_v3','k64s23_effective_closure']:
 q=R/('results/formal_main_v2/control_transport/'+name+'_20261020T1949.jsonl')
 if q.exists():external.append(ref(q))
failures=[{'stage':'factory CPU attempt01','cause':'Author assertion expected an exception; original factory correctly returned rc2 blocked JSON. No scientific guard changed.','retained':'attempt01/'},{'stage':'two author source-generation commands','cause':'Nested Python literal quoting SyntaxError before build_control_v1.py and seal_author_delivery_v1.py creation. No source/state/Git/GPU write occurred. Corrected source is preserved.'},{'stage':'control_CPU_attempt01','cause':'Original planner rejected private .local manifest. Revision02 changed only control manifest path to canonical; root exact source-only publication supplied input. Guard unchanged.','retained':'{spatial,object}/control_CPU_attempt01/failure.json'},{'stage':'control_CPU_attempt02','cause':'Original P verifier rejected missing pair configs. Root copied original R/S bytes to P, then attempt03 passed.','retained':'{spatial,object}/control_CPU_attempt02/failure.json'}]
report={'kind':'two_exact_k64_seed23_source_bridge_author_CPU_review','status':'passed_author_CPU_candidate_pending_independent_and_root_runtime_readiness','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pairs':rows,'check_count':sum(x['checks'] for x in rows),'negative_cases':sum(x['negative_cases'] for x in rows),'source_history_factory_CPU':ref(D/'attempt02/summary.json'),'actual_best_resume_server_bytes':ref(D/'actual_server_bytes.json'),'effective_full_input_closure':ref(D/'effective_closure_check.json'),'source_publication_map':ref(D/'source_publication_manifest_v2.json'),'static_plan_map':ref(D/'static_plan_publication_candidate.json'),'preserved_failures':failures,'external_evidence':external,'new_GPU_runs':0,'new_development_trials':0,'cost_added_to_ledger':0,'Slurm_calls_by_author':0,'canonical_state_Git_writes_by_author':False,'source173_unchanged':True,'training_checkpoint_or_scientific_settings_changed':False,'Goal_hold_or_final_release_changed':False,'remaining_gates':['Independent bridge/source/plan review','Root and independent readiness exactly covering new posttraining development gateway and canonical source bridge closure','Actual P action wrapper verify with complete original runtime readiness','Root fresh capacity/pending/token/duplicate reconciliation through new exact-two-development gateway; collect-only gateway forbidden']}
rr=put('author_review.json',report)
put('HANDOFF.md',"""# 两套64 seed23来源桥 CPU候选交付

仅 Spatial64 seed23 / Object64 seed23，A64_seed23、B64_seed23，每套原100开发初态共200条。没有新增训练或科学试验。

最终源码为各套 revision02/package，source_publication_manifest_v2.json 绑定 root 原字节发布。原 factory、planner、FrozenPlan、terminal science_context 与 P 科学 wrapper 均实际重建；每套763检查、38负例。P action wrapper 对缺失真实双审 readiness 仍拒绝，不能将科学 wrapper 通过当作运行准入。

Spatial 保留失败3028522及全部5份分配、总42480 GPU秒，选模A2500/B3500；Object保留失败3028468及全部3份分配、总52868 GPU秒，选模A2500/B4500。全部成本原已记账，本包不累加。8个 best/resume 仅服务器哈希，未复制或反序列化。

原私有 manifest 路径拒绝和缺P配置拒绝均保留。没有放宽原路径/身份/来源守卫，正确发布后重建通过。revision01/package、旧 publication candidate 与所有失败仅为历史；最终只用 revision02 exact pins。

按 static_plan_publication_candidate.json 的 canonical scientific/effective/contract 精确引用继续。两个计划均为development首轮，无resume/stop_after；原开发无重跑。control_modules(evidence) 返回原factory/planner私有实例。gateway_module保留原RUNNING门槛，不能用于已完成controller提交；新posttraining-development gateway只能允许这两个exact effective plan。

完成独审后root绑定canonical descriptor/source_files和新gateway/code-review，签原runtime_readiness，执行真实P action wrapper.verify。共享writer锁、CAS、全模式8GPU容量、exact pending/token/ACK和单pair活动保护保留。正常COMPLETED controller不重启；collect-only gateway不能提交开发。

prepare_static_plans_v1.py为实际原planner/effective构建入口；只读snapshot仅CPU证据，不是锁死旧state的发布权限。control_CPU_v3.py为实际正负例入口；已有输出目录禁止盲目重跑。生产使用root现有gateway以fresh state重新验证。

所有源码、测试、失败、结果均在服务器。全部原引用和SHA见author_review.json与delivery_manifest.json。Goal HOLD及final封存不变。
""")
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json'];assert all(not x['path'].endswith(('.pt','.pth','.safetensors','.bin')) for x in files)
m=put('delivery_manifest.json',{'kind':'immutable_author_candidate_delivery','status':'complete_CPU_candidate_only','root':D.relative_to(R).as_posix(),'files':files,'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'author_review':rr,'external_evidence':external,'author':'/root/devterminal_20261020_1418','canonical_runtime_readiness_pending':True,'GPU_runs':0})
print(json.dumps({'author_review':rr,'delivery_manifest':m,'files':len(files),'bytes':sum(x['bytes'] for x in files)}))
