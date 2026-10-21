from pathlib import Path
import hashlib,importlib.util,json,sys,shutil
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=Path(__file__).parent;A=R/'.local/goal_remaining5_runtime_20261021T0449';Q=A/'package'
E='results/formal_main_v2/engineering/supervision_delivery_20261021T0449/Goal_runtime_independent'
MSHA='200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f'
agent='/root/spatial588_recovery_audit_2054';checks=[]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def read(p,pin=None):
 if pin:ck('pin_'+str(p),sha(p)==pin)
 return json.loads(p.read_bytes())
def save(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2,allow_nan=False,ensure_ascii=False);f.write('\n')
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
replay=read(D/'replay_report.json');ck('all_replay_commands_passed',replay['status']=='passed_independent_CPU_replay' and len(replay['executions'])==9 and all(x['returncode']==0 for x in replay['executions']))
edges=read(D/'independent_edges_report.json');ck('own_edges_passed',edges['status']=='passed_independent_source_storage_edge_review' and edges['check_count']==497 and edges['negative_cases']==13)
pm=read(Q/'package_manifest.json',MSHA);am=read(A/'delivery_manifest.json','1db27d51a060e87966e56fe132f9ca9cd323204bddbfb4fa4c8a0791dafbd19f')
ck('author90member_manifest',am['file_count']==90 and len(am['files'])==90)
# Review exact original transport success, not a claimed boolean from the candidate.
jrel='results/formal_main_v2/control_transport/goal_remaining5_runtime_author_bytes_independent_20261021T0449.jsonl';jb=(R/jrel).read_bytes();ck('author_original_verify_log_present',b'passed_frozen_bytes_and_all_CPU_archive_members' in jb and b'd931e893a18eef2ea0037eb325dcbc21ecfc9032fe18316c335464d5e5f0a936' in jb)
reports=[];total=0;refusals=0
CR=D/'CPU_reports';CR.mkdir()
for name in ['CPU_libero_goal_k256_seed23','CPU_libero_goal_k256_seed41','CPU_libero_goal_k64_seed17','CPU_libero_goal_k64_seed23','CPU_libero_goal_k64_seed41','CPU_interfaces_v1','CPU_outer_v2','CPU_consumer_remaining5_v1','CPU_final_interfaces_v5']:
 p=D/'replay'/name/'report.json';v=read(p);ck(name+'_pass',v['status'].startswith('passed') and all(x['passed'] for x in v['checks']) and len(v['checks'])==v['check_count'])
 total+=v['check_count'];refusals+=v.get('rejections',0);dst=CR/(name+'.json')
 with dst.open('xb') as f:f.write(p.read_bytes())
 reports.append({'name':name,'path':dst.relative_to(D).as_posix(),'sha256':sha(dst),'check_count':v['check_count'],'explicit_nonloop_refusals':v.get('rejections',0)})
ck('exact_replayed_counts',total==1365 and refusals==846)
archives=read(D/'archive_final_index.json');ck('ten_full_private_archives',len(archives['CPU_archives'])==10 and all(x['all_members_stream_verified'] for x in archives['CPU_archives']))
spec=importlib.util.spec_from_file_location('_independent_finalize_runtime',Q/'entry.py');e=importlib.util.module_from_spec(spec);sys.modules[spec.name]=e;spec.loader.exec_module(e)
B=R/'results/formal_main_v2/preflight/heartbeat_20261021T1249';actual=read(B/'Goal_remaining5_actual_P_index.json','7e449e03818eda3402871b49cf952941f7590318cf640cd32cac96c2ba1f6fad');capture_refs=[]
for source in actual['captures']:
 p=R/source['path'];v=read(p,source['sha256']);key=v['pair_key'];ctx=e.context(key);o=json.loads(v['stdout'])
 ck(key+'_actualP_exact_argv',v['argv']==['/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python','-B',str(P/e.PKG/'entry.py'),'--pair-key',key,'--verify','--package-manifest-sha256',MSHA])
 ck(key+'_actualP_return_and_source',v['returncode']==0 and v['stderr']=='' and v['runtime_files']==pm['files'] and v['new_GPU_submissions']==0 and v['real_GPU_acceptance'] is False)
 ck(key+'_actualP_identity',o['status']=='passed_metadata_source_capacity_only' and o['pair_key']==key and o['stage_key']==ctx.stage_key and o['config_sha256']==ctx.config_sha and o['package_manifest_sha256']==MSHA)
 ck(key+'_actualP_original_prepared_pin',o['original_invocation']=={'path':str(ctx.ORIGINAL),'sha256':sha(ctx.ORIGINAL)})
 ck(key+'_actualP_fixed_panel',o['identity']['original_fixed200_identity_order'] and o['identity']['panel_is_original_input_not_old_output'] and o['identity']['unique_development_states']==100)
 st=o['storage'];ck(key+'_actualP_allfive_aggregate',st['aggregate_pair_keys']==list(e.scope.KEYS) and st['P_aggregate_required']==5689999360 and st['R_aggregate_required']==104725907520 and len(st['all_paths'])==10 and all(x['free_bytes']>=x['required_bytes'] for x in st['filesystem_checks']))
 ck(key+'_actualP_no_runtime_claim',o['actual_GPU_runtime_verified'] is False and o['GPU_execution_authorized'] is False and o['new_GPU_submissions']==0 and st['new_storage_paths_created'] is False and st['exclusive_claim_required_at_execution'] is True)
 capture_refs.append(source)
ready=[]
for key in e.scope.KEYS:
 ctx=e.context(key)
 v={'schema':'formal_main_v2','kind':'goal_remaining5_single_attempt_CPU_readiness','status':'passed','reviewed_by':'independent','independent_agent':agent,'version':e.VERSION,'pair_key':key,'package_manifest_sha256':MSHA,'config_sha256':ctx.config_sha,'original_chain_preserved':True,'observer_gaps_fixed':True,'paired_input_gate_CPU_passed':True,'pre_policy_pair_equality_gate':True,'all_query_input_integrity_gate':True,'original_policy_error_retained_then_halt':True,'full200_bound_tests_passed':True,'original_typed_raw_consumer_ready':True,'two_root_storage_contract_verified':True,'real_GPU_acceptance':False,'scientific_release':False,'GPU_execution_authorized':False,'actual_R_P_published_sources_verified':True,'actual_P_metadata_source_capacity_capture_reviewed':True,'independent_actual_P_verify_execution':False,'scientific_results_accepted':0,'review_scope':'source_and_CPU_plus_actual_publication_and_root_metadata_verification_capture_only','original_goal200_HOLD':True,'future_raw_terminal_acceptance_required':True,'blockers':[]}
 e.check_review(ctx,v,'independent',MSHA,ctx.config_sha);ck(key+'_exact_runtime_readiness_contract',True);ready.append((ctx,v))
for path,pin in pm['files'].items():
 for root in [R,P]:ck('final_published_'+str(root)+'_'+path,sha(root/path)==pin)
for key in e.scope.KEYS:
 ctx=e.context(key);ck(key+'_still_no_science_attempt',not ctx.RAW.exists() and not ctx.OUTPUT.exists())
report={'schema':'formal_main_v2','kind':'Goal_remaining5_runtime_independent_review','version':e.VERSION,'status':'passed','reviewed_by':'independent','independent_agent':agent,'review_scope':'independent source and CPU replay, raw algorithm and bounded interfaces, actual R/P source equality and root actual-P metadata/source/capacity captures','package_manifest_sha256':MSHA,'package_manifest':{'path':e.PKG+'/package_manifest.json','sha256':MSHA},'package_files':pm['files'],'production_sources':pm['files'],'source_count':20,'pair_keys':list(e.scope.KEYS),'author_delivery_manifest':ref(A/'delivery_manifest.json'),'replay_report':ref(D/'replay_report.json'),'additional_edges':ref(D/'independent_edges_report.json'),'CPU_reports':reports,'CPU_replay_checks':1365,'CPU_replay_explicit_nonloop_refusals':846,'independent_source_storage_edge_checks':497,'independent_additional_refusals':13,'final_binding_checks':checks,'final_binding_check_count':len(checks),'total_counted_checks':1365+497+len(checks),'source173_verified':True,'original_package_byte_identity_verified':True,'original_loop_and_AST_preserved':True,'actual_R_P_publication_verified':True,'root_actual_P_capture_refs':capture_refs,'independent_actual_P_verify_execution':False,'actual_P_metadata_source_capacity_capture_reviewed':True,'actual_GPU_runtime_verified':False,'real_GPU_acceptance':False,'GPU_execution_authorized':False,'scientific_results_accepted':0,'new_GPU_submissions':0,'Slurm_queries':0,'production_writes':0,'old_defects_preserved_and_reproduced':['c267 ACK-only still demanded five-pair fresh capacity','completion/parent guards measured different bytes than indented output','scope.py imported before exact SHA verification'],'storage':{'P_required_per_pair':1137999872,'P_required_all_five':5689999360,'R_required_per_pair':20945181504,'R_required_all_five':104725907520,'same_device_combined_requirement':110415906880,'no_dedup_or_expected_release_credit':True,'record_newline_and_abort_overhead_covered_by_margin':True,'quota_not_proven':True,'actual_compute_node_recheck_and_exclusive_claim_required':True,'separate_runtime_stdout_stderr_2GiB_RLIMIT_each':True,'Slurm_bootstrap_4GiB_budget_not_claimed_Python_RLIMIT_enforced':True},'raw_consumer_scope':'Five CPU fixture reconstructions independently rerun with exact declared image/loader/CPU-label adaptations; production rejects CPU labels; no future real raw terminal review claimed. Original typed raw consumer guard order and all query pre/post five-component bytes retained.','remaining_production_gates':['Distinct root/independent readiness, exact pair root authorization and independent atomic gateway admission under current writer lock/CAS.','Compute node verifies all-five filesystem budget and exclusive own R raw/P attempt claim with no retry.','Each new real terminal requires canonical original scientific/raw consumer reconstruction and independent terminal review before accepting any results.'],'original_goal200_HOLD':True,'old_cause_identified':False,'final_sealed':True,'scientific_release':False,'blockers':[]}
reportpath=D/'independent_review.json';save(reportpath,report);publication=[]
for ctx,v in ready:
 v['review_evidence']={'path':E+'/independent_review.json','sha256':sha(reportpath)}
 p=D/(ctx.pair_key+'_independent_readiness.json');save(p,v)
 publication.append({'source':p.relative_to(R).as_posix(),'destination':(ctx.BASE/'independent_readiness.json').relative_to(P).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
save(D/'review_publication_map.json',{'schema':'formal_main_v2','review_evidence':{'path':E+'/independent_review.json','sha256':sha(reportpath)},'publish_evidence_before_readiness':True,'source_root':str(D),'publication_map':publication,'GPU_execution_authorized':False})
(D/'README.md').write_text('本包为独立源/CPU 与实际发布元数据审计。全部 5 个完整原循环 CPU、接口/容量/原始字节重建和最终边界复跑均完成。独立报告按分项记录检查数，不把作者通过当成独立结果。原三项缺陷的源和 CPU 反例保留。真实 P 验证由 root 执行；本审计逐 SHA 核其原捕获及实际 R/P 20 源，不称再次执行。所有真实未来 GPU 原始产物仍须原 consumer 和独审终验。旧 200 HOLD，封存最终值未读，未更 state/Git/生产源，未查 Slurm 或提交 GPU。\n大量 CPU 原件以 archives 下十份精确 tar+成员表交付，服务器散件均保留；数据均是合成 CPU 样本，不是权重或科学结果。\n',encoding='utf8')
excluded=[D/'replay'/x for x in ['CPU_libero_goal_k256_seed23','CPU_libero_goal_k256_seed41','CPU_libero_goal_k64_seed17','CPU_libero_goal_k64_seed23','CPU_libero_goal_k64_seed41','CPU_interfaces_v1','CPU_outer_v2','CPU_consumer_remaining5_v1','CPU_final_interfaces_v5']]+[D/'independent_edge_outputs']
files=[]
for p in sorted(D.rglob('*')):
 if any(root==p or root in p.parents for root in excluded):continue
 assert not p.is_symlink()
 if p.is_file():files.append({'path':p.relative_to(D).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
manifest={'schema':'formal_main_v2','kind':'Goal_remaining5_runtime_independent_delivery','source_root':str(D),'status':'frozen','file_count':len(files),'files':files,'CPU_archives':archives['CPU_archives'],'loose_CPU_originals_retained_not_duplicated_in_delivery':True,'report_sha256':sha(reportpath),'package_manifest_sha256':MSHA,'production_writes':0,'GPU_submissions':0}
save(D/'delivery_manifest.json',manifest)
print(json.dumps({'report':ref(reportpath),'manifest':ref(D/'delivery_manifest.json'),'file_count':len(files),'total_counted_checks':report['total_counted_checks'],'readiness':publication},ensure_ascii=False),flush=True)
