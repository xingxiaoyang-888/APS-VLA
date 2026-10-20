from pathlib import Path
import ast,datetime,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/delivery_independent_20261020T2054'
D.mkdir(parents=True,exist_ok=True)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
checks=[]
def ck(name,condition):
 if not condition:raise ValueError(name)
 checks.append({'check':name,'passed':True})
helper=R/'.local/finalize_supervision_20261020T2054.py';b=helper.read_bytes()
ck('exact_root_helper',h(helper)=='55fb0c81b06f75c08629f9c5ba9a53f87ce3f5f1d66614e2b46d59d49ab9121f')
tree=ast.parse(b.decode());calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
ck('static_helper_does_not_submit_cancel_or_execute_shell',not any(any(x in c for x in ['sbatch','scancel','subprocess','os.system','Popen','exec_command']) for c in calls))
ck('static_helper_writer_lock_and_CAS', 'c.exclusive_lock' in calls and 'c.atomic_json' in calls and "expected_sha=before" in b.decode())
ck('static_no_complete_CPU_admission', all(x in b.decode() for x in ["x['not_runtime_admission']","'CPU_work_is_not_GPU_acceptance':True","'Spatial_legacy12_compatibility_proven':False","'Object599_compatibility_adopted':False"]))
sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd('results/experiment_supervisor/state.json')
ck('exact_preintegration_state',before=='75c2409fad6ea5fabf5d1275ecd11cffa2b752867c1b8905dce7a55c1480a934')
inv=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json')
ck('frozen_inventory173',len(inv['files'])==173)
for rel,pin in inv['files'].items():ck('frozen R/S '+rel,h(R/rel)==h(S/rel)==pin)
jobs=s['registered_jobs'];ck('unique_all_registered_job_ids',len(jobs)==len({x['job_id'] for x in jobs}))
formal=[j for j in jobs if j.get('experiment')=='formal_main_v2'];ck('269_formal_jobs',len(formal)==269)
f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
ck('training_complete_unchanged',f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000 and len(ctl['completed_pairs'])==36)
ck('final_gate_closed',f['completed_final_trials']==0 and f['test_opened'] is False and f['global_release_created'] is False)
ck('no_training_restart',ctl['root_confirmed_normal_training_exit']['restart_needed'] is False)
target={'3053875':('libero_spatial',2283,'ee00999e50f845b88f22c45f8d5164d232fd1b53ae1f9cf588bdb0aa8ea4da43'),'3053894':('libero_object',2175,'afedb854ad6e2559b876ba86bf805309ff948e9f086da10232699fa5bfe91d0f')}
reportjobs={};projected=s['current_round_cost']['allocated_gpu_seconds']
for jid,(suite,cost,pin) in target.items():
 rel='results/formal_main_v2/downstream_reviews/'+jid+'.json';rr=rd(rel);j=next(x for x in jobs if x['job_id']==jid)
 ck(jid+' exact_root_review',h(R/rel)==pin and rr['job_id']==jid and rr['suite']==suite and rr['stage']=='development')
 ck(jid+' actual200_raw',rr['status']=='passed' and rr['scientific_complete'] and rr['completed_trials']==rr['expected_trials']==200 and rr['raw_invocation_job_ids']==[jid])
 ck(jid+' exact_pair_first_invocation',j['method_ids']==['A64_seed23','B64_seed23'] and j['prior_job_ids']==[] and j['resume'] is False and jid not in f['new_action_development_verified_by_job'])
 ck(jid+' cost_not_duplicated',rr['cost']['current_gpu_seconds']==rr['cost']['all_attempt_gpu_seconds']==cost and len(rr['cost']['allocations'])==1 and rr['cost']['allocations'][0]['job_id']==jid)
 ck(jid+' no_final_or_weights',rr['final_release'] is False and rr['final_state_values_read'] is False and rr['weights_read'] is False)
 sourcebridge={k:v for k,v in rr['audit_source_sha256'].items() if '_source_bridge_v1/' in k}
 ck(jid+' pair_specific_source_bridge',len(sourcebridge)==3 and all('formal_'+suite.removeprefix('libero_')+'64s23_source_bridge_v1/' in k for k in sourcebridge))
 for relsrc,pinsrc in sourcebridge.items():ck(jid+' unchanged_bridge '+relsrc,h(R/relsrc)==pinsrc)
 stats={k:x['successes'] for k,x in rr['reconstructed_summary']['methods'].items()}
 ck(jid+' actual_successes',stats=={'A64_seed23':96,'B64_seed23':97})
 projected+=cost-j['elapsed_seconds']*j['gpus']
 reportjobs[jid]={'review':{'path':rel,'sha256':pin},'suite':suite,'trials':200,'successes':stats,'source_bridge':sourcebridge,'cost_GPU_seconds':cost,'registered_cost_replaced':j['elapsed_seconds']*j['gpus']}
ck('projection_global_cost_no_double_add',projected==1984462 and projected-s['current_round_cost']['allocated_gpu_seconds']==3672)
ck('projection_development_counts',f['current_action_development_trial_count']==5400 and sum(x['completed_trials'] for x in f['new_action_development_verified_by_job'].values())==5400 and f['completed_development_trials']==6612)
ck('state_unchanged_during_readonly_audit',h(sp)==before)
out={'schema':'formal_main_v2','kind':'independent_root_delivery_static_precheck','status':'passed_static_and_existing_artifact_checks','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewed_helper':{'path':str(helper.relative_to(R)),'sha256':h(helper)},'source173_R_and_snapshot_unchanged':True,'original_state_sha256':before,'checks':checks,'check_count':len(checks),'jobs':reportjobs,'projected_current_action_trials':5800,'projected_compatible_Long_trials':600,'projected_compatible_total':6400,'projected_historical_count':7012,'projected_GPU_seconds':1984462,'new_terminal_allocation_GPU_seconds':4458,'newly_accounted_delta_GPU_seconds':3672,'production_state_Git_or_Slurm_mutations':False,'sealed_final_values_read':False,'limitations':['Root integration helper not executed by this auditor.','Final independent terminal receipt/CPU archives/large-file packages and postintegration state/docs still require exact-artifact audit.','Spatial588 author role disclosed; its CPU algorithm is independently reviewed by the separate spatial588 recovery auditor, not self-certified here.']}
p=D/'static_precheck.json'
with p.open('x',encoding='utf-8') as fh:fh.write(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':out['status'],'check_count':len(checks),'report':str(p.relative_to(R)),'sha256':h(p),'source173_unchanged':True,'projected_GPU_seconds':projected}))
