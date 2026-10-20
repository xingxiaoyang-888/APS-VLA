"""Compact metadata inventory; no scheduler, tensor, sealed-state or production writes."""
import hashlib,json,os,sys,re
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/remaining_development_inventory_20261020T1825'
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
READS={}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No process/network/Slurm')
 if event=='open':
  name,mode,flags=args
  if isinstance(name,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(name));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'}:raise RuntimeError('Forbidden data')
   wr=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
   if wr and D not in p.parents:raise RuntimeError('Private output only')
sys.addaudithook(guard)
def raw(rel,pin=None):
 p=Path(rel);p=p if p.is_absolute() else R/p;b=p.read_bytes();hh=hashlib.sha256(b).hexdigest();assert pin is None or hh==pin,(rel,hh,pin)
 if str(p) in READS:assert READS[str(p)]['sha256']==hh
 READS[str(p)]={'path':p.relative_to(R).as_posix() if R in p.parents else str(p),'sha256':hh,'bytes':len(b)};return b

def ref(rel,pin=None):raw(rel,pin);p=Path(rel);p=p if p.is_absolute() else R/p;return dict(READS[str(p)])
def js(rel,pin=None):return json.loads(raw(rel,pin))
def reference(v,pin=None):
 if isinstance(v,str):return ref(v,pin)
 assert isinstance(v,dict) and 'path' in v and 'sha256' in v;return ref(v['path'],v['sha256'])
def out(name,value):
 p=D/name;b=value.encode() if isinstance(value,str) else (json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
from cti_vla.evaluation.formal_trials import selector_instance_identity,expected_method_ids
from cti_vla.evaluation.teacher_diagnostics import json_signature
state=js('results/experiment_supervisor/state.json');state_ref=ref('results/experiment_supervisor/state.json');f=state['formal_main_progress'];assert f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000
reg=js('configs/experiments/formal_main_v2.json');regref=ref('configs/experiments/formal_main_v2.json');invref=ref('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
methods=expected_method_ids();assert len(methods)==22
jobs=[j for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2'];devjobs=[j for j in jobs if j.get('mode')=='development'];accepted={};proofs={}
for jid,v in f['new_action_development_verified_by_job'].items():
 suite=v.get('suite','libero_10');rr=reference(v['root_review']);ir=reference(v['independent_review']);r=js(rr['path'],rr['sha256']);assert r['status']=='passed' and r['scientific_complete'] and r['completed_trials']==v['completed_trials']
 ids=sorted(v['successes']);assert len(ids)*100==v['completed_trials'];proofs[jid]={'suite':suite,'methods':ids,'root_review':rr,'independent_review':ir,'trials':v['completed_trials']}
 for mid in ids:assert (suite,mid) not in accepted;accepted[(suite,mid)]=dict(status='accepted_current_action',trials=100,job_ids=[jid],proof=jid)
longproof=reference(f['Long22_development_statistics']['root_acceptance']) if 'root_acceptance' in f['Long22_development_statistics'] else ref('results/formal_main_v2/preflight/heartbeat_20261020T1832/Long22_development_root_acceptance.json','62e95ee07f7dc6ba80a21dff177c0106279f8b462930de5074d7561ccecf5254')
longlegacy=reference(f['Long_legacy6_equivalence_followup']['real_development_compatibility_proof']);assert f['Long_legacy6_equivalence_followup']['production_reuse_authorized'] and f['Long_legacy6_equivalence_followup']['original600_reused']
first6=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
for mid in first6:assert ('libero_10',mid) not in accepted;accepted[('libero_10',mid)]=dict(status='accepted_explicit_exact_legacy600_equivalence',trials=100,root_acceptance=longproof,proof=longlegacy)
assert sum(x['trials'] for x in accepted.values())==5800
snapshot={'state_source':state_ref,'recorded_utc':datetime.now(timezone.utc).isoformat(),'root_training_arms':72,'reviewed_updates':360000,'current_semantics_development':f['current_action_development_trial_count'],'compatible_Long_legacy':600,'accepted_compatible_total':5800,'global_unique_development_initial_states':f['current_action_development_unique_initial_states'],'final_trials':f['completed_final_trials'],'global_release_created':f['global_release_created'],'test_opened':f['test_opened'],'registered_development_jobs':[{k:j.get(k) for k in ('job_id','suite','status','exit_code','elapsed_seconds','method_ids','invocation','invocation_sha256','run_root','stage_key')} for j in devjobs]}
assert snapshot['current_semantics_development']==5200 and snapshot['final_trials']==0 and snapshot['global_release_created'] is False and snapshot['test_opened'] is False
out('state_metadata_projection.json',snapshot)
probe=js(str((D/'original_source_consumer_probe_summary.json').relative_to(R)));probe_ref=ref(str((D/'original_source_consumer_probe_summary.json').relative_to(R)))
probes={x['label']:x for x in probe['results']}
source_refs={rel:ref(rel) for rel in ['scripts/formal_execution_manifests.py','scripts/ops/formal_downstream_supervisor.py','scripts/ops/formal_asset_downstream_review.py','scripts/ops/formal_action_deployment_v1/contract.py','scripts/ops/formal_action_deployment_v1/gateway.py','scripts/ops/formal_action_deployment_v1/entry.py','scripts/ops/formal_action_deployment_v1/wrapper.py','scripts/ops/formal_object256s23_source_bridge_v1/control.py','scripts/ops/formal_object256s23_source_bridge_v1/bridge_v2.py','scripts/ops/formal_object256s23_source_bridge_v1/policy_v1.json','src/cti_vla/evaluation/formal_profiling.py']}
rows=[];summary={};history={};panels={};sources=reg['suites']
for suite in ('libero_10','libero_spatial','libero_object','libero_goal'):
 panelrel=sources[suite]['initial_states_root']+'/development.json';panel=js(panelrel);assert len(panel['states'])==100 and Counter(x['task_id'] for x in panel['states'])=={i:10 for i in range(10)}
 fixed=[min((x for x in panel['states'] if x['task_id']==i),key=lambda x:x['source_state_index']) for i in range(10)]
 panels[suite]={'development_panel':ref(panelrel),'fixed_collection_initial_states':[{'task_id':x['task_id'],'source_state_index':x['source_state_index'],'trial_id':x['trial_id'],'initial_state_sha256':x['initial_state_sha256']} for x in fixed],'selection_rule':'Registered minimum source_state_index per task; collect one dense trajectory, take first/middle/last distinct actual post-wait pre-action observations.','registered_collection_jobs':[j['job_id'] for j in jobs if j.get('suite')==suite and j.get('mode')=='collect'],'actual_audited_observation_panel':None}
 if suite=='libero_10':
  lc=f['Long_fixed_observation_collection'];panels[suite]['actual_audited_observation_panel']=lc
 if suite=='libero_goal':continue
 base_manifest_rel=f'results/formal_main_v2/execution/{suite}_development_first_pair_v1.json';bm=js(base_manifest_rel);bmref=ref(base_manifest_rel);baseline={x['identity']['method_id']:x for x in bm['methods']}
 if suite!='libero_10':
  prefix='spatial' if suite=='libero_spatial' else 'object';reconstructed=raw(str((D/(prefix+'_first6_metadata_manifest.json')).relative_to(R)));assert reconstructed==raw(base_manifest_rel)
  oldjid='3022743' if suite=='libero_spatial' else '3021844';oldjob=next(j for j in devjobs if j['job_id']==oldjid);reportrel=Path(oldjob['run_root']).relative_to(P).as_posix()+'/closed_loop_report.json';old=js(reportrel)
  history[suite]={'legacy_methods':first6,'original_manifest':bmref,'factory_byte_identical':True,'original_closed_loop_report':ref(reportrel),'historical_trials':old['completed_trials'],'historical_unique_initials':old['unique_initial_states'],'trials_per_method':{mid:x['trials'] for mid,x in old['methods'].items()},'current_semantics_accepted_trials':0,'active_reuse_equivalence':False,'prior_root_review':ref(f'results/formal_main_v2/downstream_reviews/{oldjid}.json'),'legacy_policy_error_retained':suite=='libero_object'}
 for mid in methods:
  existing=[j for j in devjobs if j['suite']==suite and mid in j['method_ids']];admitted=accepted.get((suite,mid));row={'suite':suite,'method_id':mid,'original_registration':regref,'source_inventory':invref,'model_root_server':sources[suite]['model_root_server'],'model_manifest':ref(sources[suite]['model_manifest'],sources[suite]['model_manifest_sha256']),'acceptance_root':ref(f'results/formal_main_v2/{suite}/acceptance/root_review.json'),'development_panel':panels[suite]['development_panel'],'required_development_trials':100,'existing_development_jobs':[{'job_id':j['job_id'],'recorded_status':j['status'],'invocation':ref(j['invocation'],j['invocation_sha256'])} for j in existing],'accepted':admitted,'may_rerun_accepted_trials':False}
  if mid in ('dense','uniform256','uniform128','uniform64'):
   ident=baseline[mid]['identity'];row.update(visual_tokens=ident['visual_tokens'],training_seed=None,identity=ident,selector_checkpoint=None,original_execution_manifest=bmref)
  else:
   m=re.fullmatch(r'([AB])(256|128|64)_seed(17|23|41)',mid);arm,budget,seed=m[1],int(m[2]),int(m[3]);pair=next(x for x in reg['pairs'] if (x['suite'],x['visual_tokens'],x['seed'])==(suite,budget,seed));pairkey=f'{suite}_k{budget}_seed{seed}';cp=f['completed_training_pairs'][pairkey];base=Path(pair['run_root_server']).relative_to(P).as_posix()+'/training';receipt=js(base+'/'+arm+'/deployment_receipt.json');meta=receipt['metadata'];report=js(base+'/'+arm+'/training_report.json');assert report['training_updates_completed']==5000
   ident=selector_instance_identity({**meta,'selector_checkpoint_sha256':receipt['checkpoint_sha256'],'deployment_receipt_sha256':json_signature(receipt),'f01_report_sha256':receipt['f01_report_sha256']})
   nested=cp.get('terminal_root_and_independent_review',{});ind=reference(cp['independent_review'],cp.get('independent_review_sha256')) if cp.get('independent_review') else reference(nested['independent_review'])
   rrrel=base+'/segment_reviews/'+str(js(base+'/training_summary.json')['job_id'])+'.json';tr=js(rrrel);assert tr['status']=='passed' and tr['completed_by_arm']=={'A':5000,'B':5000}
   row.update(visual_tokens=budget,training_seed=seed,identity=ident,pair_id=pairkey,pair_config=ref(pair['path'],pair['sha256']),selector_checkpoint={'path':report['best_checkpoint'],'sha256':receipt['checkpoint_sha256'],'selected_update':meta['update'],'payload_rehashed_by_inventory':False},deployment_receipt=ref(base+'/'+arm+'/deployment_receipt.json'),training_root=ref(rrrel),training_independent=ind,all_training_jobs=[{'job_id':j['job_id'],'status':j['status'],'exit_code':j['exit_code'],'GPU_seconds':j['elapsed_seconds']*j['gpus']} for j in tr['registered_pair_jobs_at_review']],startup_failure_job_ids=sorted(tr.get('startup_failure_history',{})),ordinary_runtime_metadata_job_ids=sorted(tr.get('runtime_compatibility_history',{})),training_cost_already_recorded=tr['pair_allocated_gpu_seconds'])
  if admitted:row['readiness']='complete_accepted_do_not_rerun'
  elif suite=='libero_object' and mid in ('A256_seed23','B256_seed23'):row['readiness']='3052166_submitted_once_root_terminal_passed_independent_pending_do_not_submit';row['terminal_root_pending_independent']=ref('results/formal_main_v2/downstream_reviews/3052166.json','25de882d1e6e087e2d2f15ac0c4ad1e008d176ddd425d1851b31c136047d3713')
  elif mid in ('A64_seed23','B64_seed23'):row['readiness']='separate_startup_history_source_bridge_required';row['original_consumer_probe']=probes[('spatial' if suite=='libero_spatial' else 'object')+'64seed23']['output_ref'];row['existing_Object256_bridge_applicable']=False
  elif mid in first6:
   row['readiness']='legacy12_preserved_explicit_failure_repair_and_resume588_required' if suite=='libero_spatial' else 'legacy600_equivalence_requires_per_chunk_and_error_case_audit_no_rerun';row['historical_trials_for_method']=history[suite]['trials_per_method'][mid];row['source_factory_passed']=True;row['source_pass_is_submission_authorization']=False
  else:raise AssertionError((suite,mid))
  rows.append(row)
 current=[r for r in rows if r['suite']==suite];summary[suite]={'instances':22,'accepted_instances':sum(r['accepted'] is not None for r in current),'accepted_trials':sum(r['accepted']['trials'] if r['accepted'] else 0 for r in current),'unaccepted_instances':[r['method_id'] for r in current if not r['accepted']],'unaccepted_required_trials':100*sum(r['accepted'] is None for r in current)}
assert {k:v['accepted_trials'] for k,v in summary.items()}=={'libero_10':2200,'libero_spatial':1400,'libero_object':1200}
assert len(rows)==66 and sum(x['unaccepted_required_trials'] for x in summary.values())==1800
out('instance_inventory.json',{'schema':'formal_main_v2','scope':'nonGoal_development_inventory_at_exact_root_state','state_source':state_ref,'rows':rows,'summary':summary,'accepted_job_proofs':proofs,'historical_unaccepted_current_semantics':history,'new_submissions':0,'new_GPU_seconds':0})
formal_profile_jobs=[{k:j.get(k) for k in ('job_id','mode','suite','status','invocation','invocation_sha256')} for j in jobs if j.get('mode') in ('collect','full','components')]
assert not any(j['mode'] in ('full','components') for j in formal_profile_jobs)
out('profiling_gate_and_panels.json',{'schema':'formal_main_v2','registration':regref,'profiling_settings':reg['profiling'],'panels':panels,'registered_formal_profiling_jobs':formal_profile_jobs,'full_and_components_require_all88_global_freeze':True,'full_and_components_require_final_root_release_file':False,'explanation':'Original planner calls release_global(release=False) for full/components and validates88 frozen identities plus all four development receipts. Only final stage requires root_release.json. Dense-only collect has no global-freeze flag and can precede it. This inventory opens no sealed values.','gate_evidence':[{'source':source_refs['scripts/ops/formal_downstream_supervisor.py'],'lines':[286,314,319]},{'source':source_refs['src/cti_vla/evaluation/formal_profiling.py'],'lines':[45,54,61,68]},{'source':source_refs['scripts/formal_execution_manifests.py'],'lines':[722,745,778]}],'global_freeze_available':False,'full_O2A_completed':False,'components_completed':False,'Long_legacy_bridge_scope_not_extended_to_global_consumers':True,'Object256s23_bridge_scope_not_extended_to_profile_or_global_consumers':True})
nextsteps=[
 {'priority':1,'scope':'Object256seed23','action':'Await independent terminal audit of unique job3052166; do not submit again. Root already passed2165GPU-second200trial outcome; inventory does not adopt it.','original_submission':ref('results/formal_main_v2/submissions/3052166.json')},
 {'priority':2,'scope':'Spatial old6 methods','action':'Keep12 historical trials (two per method) and failed3042529 allocation. Root must consume newest failed-attempt audit, binding repair record, legacy-prefix transition and explicit resume588; do not issue fresh600 or overlapping subset.','manifest':ref('results/formal_main_v2/execution/libero_spatial_development_first_pair_v1.json'),'prior_transition':ref('results/formal_main_v2/execution/action_spatial_resume_0943/transition.json'),'prior_readiness':ref('results/formal_main_v2/execution/action_spatial_resume_0943/runtime_readiness.json'),'dependency_repair':ref('results/formal_main_v2/preflight/heartbeat_20261019T2318/Spatial_dependency_repair.json'),'implementation_gate':{'source':source_refs['scripts/ops/formal_downstream_supervisor.py'],'lines':[438,445,460,466,470,509]}},
 {'priority':3,'scope':'Object old6 methods','action':'Use the already accepted Long exact-trial inactive-range-guard equivalence procedure as a template only: audit all old chunks, selectedidentity, environment and typed controller map. One historical Dense policy_error precludes presuming600 ordinary completed equivalent trials. Separate that exact exception and retain its cost; no successful-trial-only selection and no fresh rerun by this inventory.','manifest':ref('results/formal_main_v2/execution/libero_object_development_first_pair_v1.json'),'Long_accepted_rule_reference':longlegacy,'Long_no_general_reuse_scope':f['Long_legacy6_equivalence_followup']['reuse_scope']},
 {'priority':4,'scope':'Spatial64seed23 and Object64seed23','action':'Each needs its own independently reviewed startup-history source consumer bridge, including original failed raw receipt/pull ownership and full billed allocations. Spatial original factory fails at verified-pull ownership for3028522; Object fails ordinary metadata coverage of3028468. Never omit failures, fabricate normal metadata, or reuse Object256s23 exact bridge.','actual_probes':probe_ref},
 {'priority':5,'scope':'O2A','action':'Collect Spatial/Object fixed dense observation panels via original collect entry after perplan registration/readiness; Goal collection stays under suite HOLD unless separately accepted engineering scope. Full and component timing wait for all88 global freeze and exact same checkpoints. Long30panel already accepted and must not be recollected.','existing_collect_root_helper':ref('.local/dispatch_Long_collect_0830.py'),'prior_collect_science':ref('results/formal_main_v2/execution/long_collect_action_v1_0830/scientific_plan.json')}
]
out('minimum_next_actions.json',{'status':'inventory_not_submission_authority','actions':nextsteps,'ordinary_source_factory_helper':source_refs['scripts/formal_execution_manifests.py'],'original_plan_prepare_template':ref('.local/nonLong64_development_plans_20261020T1530/prepare_four_plans_v1.py'),'no_immediately_unconditionally_submittable_unrun_development_group':True,'no_new_framework_required':True,'original_gateway_unchanged':source_refs['scripts/ops/formal_action_deployment_v1/gateway.py']})
lines=['# 非Goal开发覆盖只读盘点','', '状态口径：72/72训练已双审；当前动作语义5200条＋明确兼容Long600条＝5800条，400唯一初态。下列按盘点时已登记接纳状态，3052166虽然root终审通过仍等待独审，不擅自增加分母。','', '|套件|已接纳实例/22|已接纳开发条数|尚未准入|','|---|---:|---:|---|']
for suite,v in summary.items():lines.append(f"|{suite}|{v['accepted_instances']}/22|{v['accepted_trials']}|{', '.join(v['unaccepted_instances']) or '无；不得重跑'}|")
lines+=['','未准入非Goal总1800条：Object256s23已有唯一作业200；Spatial旧12需经失败修复和原续跑588，再接纳完整600；Object旧600需逐chunk/环境等价审查，其中1条Dense policy_error必须单列；两套件64s23各200需独立startup来源桥。未准入不等于全都需要新跑。','', '原factory对Spatial/Object旧6方法均通过并重建完全相同manifest，但原planner禁止重叠子集和完整组重复提交。实际64s23原消费失败分别是Spatial失败3028522的pull ownership、Object失败3028468没有普通runtime metadata，原因不同。现Object256s23桥只认3028460→3039258→3042627的确切链，不能泛化。','', '完整O2A及组件计时必须有全部88实例、四套件开发收据的global_freeze；它们验证freeze但不要求先签final root_release。dense-only观测collect可提前；Long已双审30观测，其余套件只有固定100开发初态与确定性抽取规则，尚无实际collect产物。Goal科学HOLD继续；无完整延迟结果。','', '精确路径、SHA、每一实例的checkpoint和源链见instance_inventory.json；原入口与最小下一步见minimum_next_actions.json。所有权重均未读取/复制；无Slurm调用、无GPU、无state/Git/canonical写入，唯执行transport按既有规定新增不可覆盖审计日志。']
out('REPORT.md','\n'.join(lines)+'\n')
out('read_evidence_manifest.json',{'schema':'formal_main_v2','files':sorted(READS.values(),key=lambda x:x['path']),'state_snapshot_is_metadata_projection_not_atomic_claim':True,'no_payload_read':True})
files=[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(D.iterdir()) if p.is_file() and p.name!='inventory_manifest.json']
print(json.dumps(out('inventory_manifest.json',{'schema':'formal_main_v2','status':'completed_readonly_inventory','files':files,'new_GPU_seconds':0,'Slurm_mutations':0,'state_mutations':0,'Git_mutations':0,'scientific_release':False,'summary':summary}),ensure_ascii=False))
