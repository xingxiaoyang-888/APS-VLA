from pathlib import Path
import argparse,ast,copy,datetime,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/delivery_independent_20261020T2054';B='results/formal_main_v2/preflight/heartbeat_20261021T0454';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2054'
ap=argparse.ArgumentParser();ap.add_argument('--state-sha256',required=True);a=ap.parse_args()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(p):return {'path':str(p.relative_to(R)),'sha256':h(p),'bytes':p.stat().st_size}
checks=[]
def ck(name,ok):
 if not ok:raise ValueError(name)
 checks.append({'check':name,'passed':True})
def bound(rr):
 ck('bound '+rr['path'],h(R/rr['path'])==rr['sha256'])
 return rd(rr['path'])
sp=R/'results/experiment_supervisor/state.json';ck('expected_integrated_state',h(sp)==a.state_sha256)
s=rd('results/experiment_supervisor/state.json');old=rd(B+'/state_before.json');f=s['formal_main_progress'];of=old['formal_main_progress'];ctl=s['autonomous_training_v1']
ck('exact_preintegration_state',h(R/B/'state_before.json')=='75c2409fad6ea5fabf5d1275ecd11cffa2b752867c1b8905dce7a55c1480a934')
inputsref={'path':B+'/finalization_inputs.json','sha256':'087032399c40b42a500c2f1e06c31f076761dee6d1535c7858a960292b237e22'}
inputs=bound(inputsref);summ=bound(s['last_root_supervision_snapshot'])
ck('summary_scope',s['last_root_supervision_snapshot']['path']==B+'/final_summary.json' and summ['new_development_accepted']==400 and summ['compatible_development_trials']==6400 and summ['current_action_development_trials']==5800)
ck('final_and_profiling_closed',not f['test_opened'] and not f['global_release_created'] and f['completed_final_trials']==0 and summ['final_sealed'] and not summ['global_release'] and not summ['O2A_released'])
ck('no_new_GPU_or_training',summ['new_GPU_jobs']==[] and summ['active_registered_GPU_jobs']==[] and not summ['controller_restarted'] and ctl['root_confirmed_normal_training_exit']['restart_needed'] is False)
ck('training72_360000_unchanged',f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000 and f['completed_training_pairs']==of['completed_training_pairs'] and ctl['completed_pairs']==old['autonomous_training_v1']['completed_pairs'])
ck('controller_state_changes_limited', {k:v for k,v in ctl.items() if k!='occupied_job_ids'}=={k:v for k,v in old['autonomous_training_v1'].items() if k!='occupied_job_ids'} and ctl['occupied_job_ids']==[])
ck('no_pending_or_slots_or_hold',s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None)
current=f['new_action_development_verified_by_job'];previous=of['new_action_development_verified_by_job']
targets={'3053875':('libero_spatial',2283,'ee00999e50f845b88f22c45f8d5164d232fd1b53ae1f9cf588bdb0aa8ea4da43'),'3053894':('libero_object',2175,'afedb854ad6e2559b876ba86bf805309ff948e9f086da10232699fa5bfe91d0f')}
ck('only_two_new_admissions',set(current)-set(previous)==set(targets) and all(current[k]==v for k,v in previous.items()))
ck('trial_counts_only400_added',f['current_action_development_trial_count']==5800 and sum(v['completed_trials'] for v in current.values())==5800 and f['completed_development_trials']==of['completed_development_trials']+400==7012)
before_jobs={j['job_id']:j for j in old['registered_jobs']};after_jobs={j['job_id']:j for j in s['registered_jobs']}
ck('no_duplicate_or_new_registered_jobs',len(after_jobs)==len(s['registered_jobs']) and set(after_jobs)==set(before_jobs))
for jid,j in after_jobs.items():
 if jid not in targets:ck('unchanged_allocation '+jid,j==before_jobs[jid])
 else:
  changed={k for k in set(j)|set(before_jobs[jid]) if j.get(k)!=before_jobs[jid].get(k)}
  ck('only_terminal_fields '+jid,changed<= {'status','exit_code','elapsed_seconds','allocation','node'} and j['status']=='COMPLETED' and j['exit_code']=='0:0' and j['elapsed_seconds']==targets[jid][1])
formal=[j for j in after_jobs.values() if j.get('experiment')=='formal_main_v2'];actual_cost=sum(j['elapsed_seconds']*j['gpus'] for j in formal)
ck('all269_cost_once',len(formal)==269 and actual_cost==1984462 and s['current_round_cost']['allocated_gpu_seconds']==actual_cost and s['current_round_cost']['final'] is True and summ['newly_accounted_GPU_seconds']==3672)
ind=bound(inputs['independent_terminal']);ck('independent_actual_terminal',ind['status']=='passed' and ind['review_role']=='independent' and set(ind['jobs'])==set(targets) and ind['totals']['allocated_gpu_seconds']==4458 and ind['totals']['trials']==400)
jobs_report={};seen_suite_states={}
for jid,(suite,cost,pin) in targets.items():
 e=current[jid];v=ind['jobs'][jid];rr=bound(e['root_review']);ck('exact root '+jid,e['root_review']['sha256']==pin and rr['job_id']==jid and rr['suite']==suite)
 ck('original consumer and raw passes '+jid,v['full_original_consumer_reconstruction_passed'] and v['raw_start_result_pairs_exact'] and v['status']=='passed' and v['root_review']==e['root_review'])
 ck('source-specific review binds '+jid,v['source_bridge'] and v['frozen_sources']['R_and_original_S_exact'] and v['frozen_sources']['files']==173 and not v['state_written'] and not v['Git_operations'] and not v['weights_copied'] and v['new_GPU_jobs']==0)
 ck('cost binding '+jid,e['GPU_seconds']==v['allocated_gpu_seconds']==rr['cost']['all_attempt_gpu_seconds']==rr['cost']['current_gpu_seconds']==cost and len(rr['cost']['allocations'])==1)
 lr=v['raw_ledger'];ck('actual P/R raw '+jid,h(R/lr['path'])==h(P/lr['path'])==lr['sha256'] and e['raw_ledger']==lr)
 raw=[json.loads(z) for z in (R/lr['path']).read_bytes().splitlines()]
 results=[x for x in raw if x.get('event')=='result'];starts=[x for x in raw if x.get('event')=='start']
 ck('exact200 result/start '+jid,len(results)==len(starts)==200 and len({x['trial_id'] for x in results})==200 and {x['trial_id'] for x in starts}=={x['trial_id'] for x in results})
 ck('development only '+jid,all(x['split']=='development' and x['suite']==suite and x['status']=='completed' and x['action_chunk']==8 and x['configured_wait_steps']==10 for x in results))
 paired={}
 for x in results:
  paired.setdefault(x['state_trial_id'],{})[x['method']]=x
 ck('same100 paired states '+jid,len(paired)==100 and all(set(z)=={'A64_seed23','B64_seed23'} for z in paired.values()))
 outcomes={'both_success':0,'both_failure':0,'A_only':0,'B_only':0};successes={'A64_seed23':0,'B64_seed23':0}
 for z in paired.values():
  aa=z['A64_seed23'];bb=z['B64_seed23']
  ck('paired identity '+jid+aa['state_trial_id'],all(aa[k]==bb[k] for k in ['initial_state_sha256','environment_seed','runtime_seed','source_state_index','task_id','task_name']))
  av=aa['success'];bv=bb['success'];outcomes['both_success' if av and bv else 'A_only' if av else 'B_only' if bv else 'both_failure']+=1
  successes['A64_seed23']+=int(av);successes['B64_seed23']+=int(bv)
 ck('raw statistics '+jid,successes==e['successes']==v['successes']=={'A64_seed23':96,'B64_seed23':97} and outcomes==e['paired_outcomes']==v['discordance']=={'both_success':95,'both_failure':2,'A_only':1,'B_only':2})
 ck('ten tasks ten states '+jid,{t:sum(next(iter(z.values()))['task_id']==t for z in paired.values()) for t in range(10)}=={t:10 for t in range(10)})
 jobs_report[jid]={'suite':suite,'root_review':e['root_review'],'independent_review':e['independent_review'],'raw_ledger':lr,'trials':200,'unique_development_states':100,'successes':successes,'paired_outcomes':outcomes,'GPU_seconds':cost}
for e in current.values():
 rr=bound(e['root_review'])
 for pair in rr['reconstructed_summary']['paired_AB'].values():
  seen_suite_states.setdefault(rr['suite'],set()).update(x['state_trial_id'] for x in pair['results'])
ck('400_unique_not_expanded',set(seen_suite_states)=={'libero_10','libero_spatial','libero_object','libero_goal'} and all(len(v)==100 for v in seen_suite_states.values()) and summ['unique_development_initial_states']==400 and summ['new_unique_initial_states']==0)
ck('CPU_not_accepted_as_science',summ['CPU_work_is_not_GPU_acceptance'] and summ['Goal_original200_and_new_science_HOLD'] and not summ['Spatial_legacy12_compatibility_proven'] and not summ['Object599_compatibility_adopted'])
source=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');ck('source_count173',len(source['files'])==173)
for rel,pin in source['files'].items():ck('source173 '+rel,h(R/rel)==h(S/rel)==pin)
docrows=[]
for entry in rd('.local/delivery_independent_20261020T2054/docs_baseline.json')['files']:
 b=(R/entry['path']).read_bytes()
 ck('previous_doc_bytes_retained '+entry['path'],hashlib.sha256(b[-entry['bytes']:]).hexdigest()==entry['sha256'])
 if not entry['path'].endswith('1949.md'):
  prefix=b[:-entry['bytes']].decode()
  ck('new_doc_provenance_limits '+entry['path'],all(x in prefix for x in ['72/72','360000','6400/8800','5800','7012','400唯一','551.239','0/35200','未完成','CPU','HOLD']))
 docrows.append(ref(R/entry['path']))
block=R/'docs/正式下游阻塞登记_20261020T2054.md';text=block.read_text()
ck('blocker_doc_all_four_suites',all(x in text for x in ['2200/2200','1600/2200','1000/2200','588','599','policy_error','原200','HOLD','0/35200']))
docrows.append(ref(block))
reports={}
for name,pin in [('static_precheck.json','001eb994b8cab42733012cf750b61fc5dc6c342bc993cfb8519981bc75aae760'),('all9_archive_review.json','f71ad80ee225d8bccaa4cfb21310f785c30a857a3927dd3a5e492d0c396e3f2d'),('CPU_archives_review.json','50317dbe3380ed689fb71bd58e797c3b41a99a62e2c409ffda6e8e5193861287')]:
 ck('prior audit '+name,h(D/name)==pin);reports[name]=ref(D/name)
packages=rd('.local/delivery_independent_20261020T2054/CPU_archives_review.json')['packages']
for q in packages:
 ck('inputs CPU receipt '+q['name'],inputs['CPU_archive_receipts'][q['name']]['path']==q['receipt']['path'] and inputs['CPU_archive_receipts'][q['name']]['sha256']==q['receipt']['sha256'])
 for item in q['files']:ck('CPU archived file unchanged '+item['archive']['path'],h(R/item['archive']['path'])==item['archive']['sha256'])
kr=bound(inputs['K64_terminal_archive']);km=bound(kr['manifest']);ck('K64 original manifest copied',h(R/kr['destination'])==kr['manifest']['sha256'])
kfiles=[]
for item in km['files']:
 src=R/item['path'];relative=src.relative_to(R/km['root']);dst=(R/kr['destination']).parent/relative
 ck('K64 archived private report '+str(relative),h(src)==h(dst)==item['sha256'] and src.stat().st_size==dst.stat().st_size==item['bytes'])
 kfiles.append(ref(dst))
ck('K64 archived26',len(kfiles)==26)
helperpins={'.local/finalize_supervision_20261020T2054_v2.py':'7457146c81414f9528eac2b620eb2a8a2f877f47561142178c41a0dafbeacc15','.local/deliver_20261020T2054.py':'663e343120bbb91a8a2e4f600514e4aad2f6ab33358ea953c6855a5e35071b34'}
for rel,pin in helperpins.items():ck('reviewed_root_helper '+rel,h(R/rel)==pin)
ck('audit_did_not_change_state',h(sp)==a.state_sha256)
out={'schema':'formal_main_v2','kind':'independent_final_delivery_review','status':'passed_final_delivery_review','blockers':[],'review_role':'independent_final_artifact_audit','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source173_verified':True,'final_sealed':True,'state_sha256':a.state_sha256,'final_summary':s['last_root_supervision_snapshot'],'inputs':inputsref,'checks':checks,'check_count':len(checks),'jobs':jobs_report,'current_action_development_trials':5800,'compatible_Long_trials':600,'compatible_development_trials':6400,'all_historical_count':7012,'unique_development_initial_states':400,'allocated_GPU_seconds':actual_cost,'new_GPU_submissions':0,'new_scientific_admissions':400,'new_unique_initial_states':0,'production_state_Git_or_Slurm_mutations':False,'sealed_final_values_read':False,'CPU_candidates_not_runtime_admitted':True,'private_reports_exactly_archived_in_E':True,'K64_archived_files':kfiles,'documents':docrows,'supporting_audits':reports,'CPU_archived_packages':[{'name':q['name'],'manifest':q['manifest'],'receipt':q['receipt'],'files':[x['archive'] for x in q['files']]} for q in packages],'root_helpers':helperpins,'scope_limits':['No final outcomes or complete O2A release.','No GPU submission or Git mutation performed by this auditor.','No independent self-certification of Spatial588 algorithm: final copied package uses the separately authored independent review.','No claim that retained legacy12 matches the current action runtime.']}
p=D/'final_review.json'
with p.open('x',encoding='utf-8') as fh:json.dump(out,fh,ensure_ascii=False,sort_keys=True,indent=2);fh.write('\n')
print(json.dumps({'status':out['status'],'state_sha256':a.state_sha256,'check_count':len(checks),'report':ref(p),'blockers':[]}))
