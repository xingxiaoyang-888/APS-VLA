from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,os,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
B='results/formal_main_v2/preflight/heartbeat_20261021T0454';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2054'
TARGETS={'3053875':('libero_spatial',2283,'ee00999e50f845b88f22c45f8d5164d232fd1b53ae1f9cf588bdb0aa8ea4da43'),'3053894':('libero_object',2175,'afedb854ad6e2559b876ba86bf805309ff948e9f086da10232699fa5bfe91d0f')}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
 if not ok:raise ValueError(msg)
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return {'path':n,'sha256':h(R/n)}
def bound(v):
 need(set(v)>={'path','sha256'} and not Path(v['path']).is_absolute() and '..' not in Path(v['path']).parts,'invalid evidence ref');need(h(R/v['path'])==v['sha256'],'evidence drift '+v['path']);return rd(v['path'])
def save(n,v,raw=False):
 p=R/n;need(p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]),'symlink');p.parent.mkdir(parents=True,exist_ok=True);data=v if raw else (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(data)
 return ref(n)
def module(rel,pin,name):
 p=R/rel;need(h(p)==pin,'source drift '+rel);sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--inputs',required=True);ap.add_argument('--inputs-sha256',required=True);args=ap.parse_args();inputs=bound({'path':args.inputs,'sha256':args.inputs_sha256})
need(os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R),'pinned server transport required')
ind=bound(inputs['independent_terminal']);need(inputs['independent_terminal']['sha256']=='4f95cad2dac8f8e6a69806445658824b42ebf1104e4849cec0a5c12028f20c7b' and ind['status']=='passed' and ind['kind']=='independent_development_terminal_pair_batch' and not ind['sealed_final_values_read'] and not ind['state_written'] and ind['new_GPU_jobs']==0 and not ind['checkpoint_bytes_copied'],'independent terminal incomplete')
for jid,v in ind['jobs'].items():
 need(v['frozen_sources']['R_and_original_S_exact'] and v['frozen_sources']['files']==173 and not v['state_written'] and not v['Git_operations'] and not v['weights_copied'] and not v['checkpoint_content_deserialized'] and v['new_GPU_jobs']==0 and v['visual_tokens']==64,'independent per-job source/scope invalid')
 need(v['kind']=='independent_terminal_development_review' and v['job_id']==jid and h(R/v['raw_ledger']['path'])==h(P/v['raw_ledger']['path'])==v['raw_ledger']['sha256'],'real server raw ledger required')
 need(v['root_review']['sha256']==TARGETS[jid][2] and v['allocated_gpu_seconds']==TARGETS[jid][1],'independent exact source/cost binding')
need(set(ind['jobs'])==set(TARGETS) and ind['totals']['allocated_gpu_seconds']==4458 and ind['totals']['trials']==400,'exact two independent jobs required')
for name,rr in inputs['CPU_archive_receipts'].items():
 x=bound(rr);need(x['status']=='immutable_nonweight_package_archived' and x['state_unchanged'] and x['GPU_jobs_added']==0 and x['not_runtime_admission'],'CPU archive is not scientific admission')
need(set(inputs['CPU_archive_receipts'])=={'Spatial588_author','Spatial588_independent','Goal_CPU_author','Goal_CPU_independent','Object_raw_root','Object_raw_independent'},'exact CPU evidence inventory required')
c=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','rootfinal2054ctl')
g=module('scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py','873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb','rootfinal2054gateway')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 need(before=='75c2409fad6ea5fabf5d1275ecd11cffa2b752867c1b8905dce7a55c1480a934','state CAS baseline changed; inspect before action')
 need(s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None and not ctl['blocked_pairs'],'pending, hold or blocked condition')
 need((f['root_and_independent_completed_arms'],f['root_and_independent_reviewed_arm_updates'],f['current_action_development_trial_count'],f['completed_development_trials'])==(72,360000,5400,6612),'unexpected counters')
 need(len(ctl['completed_pairs'])==36 and ctl['last_result']['status']=='training_matrix_complete' and ctl['root_confirmed_normal_training_exit']['restart_needed'] is False,'normal completed training must remain closed')
 need(f['completed_final_trials']==0 and f['test_opened'] is False and f['global_release_created'] is False,'final must be sealed')
 snap=c.Slurm().observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],snap,ctl['controller_job_id']);need(not cap['unknown'] and not cap['findings'] and not cap['occupied'],'unexpected active or unknown capacity')
 for j in s['registered_jobs']:g.check_observed_identity(j,snap['rows'][j['job_id']],snap['queue'].get(j['job_id']),c.TERMINAL)
 need(snap['rows']['3034538']['status']=='COMPLETED' and snap['rows']['3034538']['exit_code']=='0:0' and snap['rows']['3034538']['gpus']==0,'controller terminal changed')
 inv=bound({'path':'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','sha256':'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'});need(len(inv['files'])==173,'source inventory count')
 for rel,pin in inv['files'].items():need(h(R/rel)==h(S/rel)==pin,'frozen source drift '+rel)
 need(not (R/B/'final_summary.json').exists(),'immutable final transaction exists')
 save(B+'/state_before.json',sp.read_bytes(),True)
 ir=save('results/formal_main_v2/downstream_reviews/3053875_3053894_independent.json',(R/inputs['independent_terminal']['path']).read_bytes(),True)
 entries={}
 for jid,(suite,cost,pin) in TARGETS.items():
  job=next(j for j in s['registered_jobs'] if j['job_id']==jid);v=ind['jobs'][jid];rr=bound({'path':'results/formal_main_v2/downstream_reviews/'+jid+'.json','sha256':pin});o=snap['rows'][jid]
  need(jid not in f['new_action_development_verified_by_job'] and job['suite']==suite and job['method_ids']==['A64_seed23','B64_seed23'] and job['prior_job_ids']==[] and job['resume'] is False,'duplicate or wrong registered pair')
  need(o['status']=='COMPLETED' and o['exit_code']=='0:0' and o['elapsed_seconds']==cost and o['gpus']==1,'exact allocation required')
  need(rr['status']=='passed' and rr['scientific_complete'] and rr['completed_trials']==200 and rr['raw_invocation_job_ids']==[jid] and not rr['final_release'] and not rr['final_state_values_read'] and not rr['weights_read'],'root terminal review scope')
  need(v['trials']==200 and v['unique_initial_states']==100 and v['suite']==suite and v['seed']==23 and v['full_original_consumer_reconstruction_passed'] and v['raw_start_result_pairs_exact'],'full independent reconstruction required')
  need(v['successes']=={k:x['successes'] for k,x in rr['reconstructed_summary']['methods'].items()}=={'A64_seed23':96,'B64_seed23':97} and v['B_minus_A_pp']==1,'statistics must derive from exact raw')
  need(rr['cost']['current_gpu_seconds']==rr['cost']['all_attempt_gpu_seconds']==cost and len(rr['cost']['allocations'])==1,'single allocation cost')
  entry=dict(job_id=jid,suite=suite,seed=23,visual_tokens=64,completed_trials=200,unique_initial_states=100,successes=v['successes'],B_minus_A_percentage_points=v['B_minus_A_pp'],paired_outcomes=v['discordance'],per_task=v['per_task'],root_review=ref('results/formal_main_v2/downstream_reviews/'+jid+'.json'),independent_review=ir,independent_review_scope='Exact report member selected by job_id; full pair-specific original consumer plus independent raw audit',raw_ledger=v['raw_ledger'],GPU_seconds=cost,GPU_cost_scope='Full single allocation; global cost recomputed by unique registered allocation, not added twice.',full_action_chunks=v['full_action_chunks'],executed_control_actions=v['executed_control_actions'],offline_validation_diagnostics=v['offline_validation_diagnostics'],t0_token_diagnostics=v['t0_token_diagnostics'],O2A_complete=False,scientific_final_release=False)
  entries[jid]=entry;f['new_action_development_verified_by_job'][jid]=entry
 need(sum(e['completed_trials'] for e in f['new_action_development_verified_by_job'].values())==5800,'new trial sum')
 bysuite={};counts={}
 for e in f['new_action_development_verified_by_job'].values():
  rr=bound(e['root_review']);states=bysuite.setdefault(rr['suite'],set());counts[rr['suite']]=counts.get(rr['suite'],0)+e['completed_trials']
  for pair in rr['reconstructed_summary']['paired_AB'].values():states.update(x['state_trial_id'] for x in pair['results'])
 need({k:len(v) for k,v in bysuite.items()}=={k:100 for k in ['libero_10','libero_spatial','libero_object','libero_goal']},'unique state count changed')
 need(counts=={'libero_10':1600,'libero_spatial':1600,'libero_object':1600,'libero_goal':1000},'suite counts')
 f.update(current_action_development_trial_count=5800,completed_development_trials=7012)
 changes=[]
 for job in s['registered_jobs']:
  if job.get('experiment')!='formal_main_v2':continue
  o=snap['rows'][job['job_id']];changed={}
  for key in ['status','exit_code','elapsed_seconds','allocation','node']:
   if job.get(key)!=o[key]:changed[key]={'before':job.get(key),'after':o[key]};job[key]=o[key]
  if changed:changes.append({'job_id':job['job_id'],'fields':changed})
 need({v['job_id'] for v in changes}.issubset(set(TARGETS)),'unrelated job changed')
 need([j for j in s['registered_jobs'] if j.get('experiment')!='formal_main_v2']==[j for j in old['registered_jobs'] if j.get('experiment')!='formal_main_v2'],'nonproject records changed')
 formal=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'];secs=sum(snap['rows'][j['job_id']]['elapsed_seconds']*snap['rows'][j['job_id']]['gpus'] for j in formal)
 need(len(formal)==269 and secs==1984462,'unexpected global allocation cost')
 s['current_round_cost']={'allocated_gpu_hours':secs/3600,'allocated_gpu_seconds':secs,'registered_jobs':len(formal),'historical_jobs_excluded':True,'final':True,'scope':'All currently registered formal_main_v2 allocations once, including loading/cache/engineering/failed attempts; future work not included.'}
 ctl['occupied_job_ids']=[];f['parallel_execution'].update(registered_requested_active_GPU_jobs=0,actual_running_allocated_GPUs=0,status='training_complete_downstream_acceptance_gates_pending')
 utc=datetime.now(timezone.utc).isoformat()
 nextactions=['Spatial588: integrate independently reviewed typed pre-dispatch failure chain; first prove retained12 action bytes and full old/current model/controller/state/RNG identity compatibility; then new exact gateway, canonical repair and actual P runtime readiness, no fabricated3042529 invocation.', 'Object old600: preserve599 complete plus1 range-policy-error; separately prove599 full historical source/controller compatibility; exact linked replacement of the exception needs reviewed engineering and duplicate protection, no normal-resume shortcut or denominator deletion.', 'Goal: integrate and independently verify passive first-policy paired-input gate through the exact production outer/source closure; only after explicit engineering gate consider one bounded registered58-prefix diagnostic, no automatic rerun or old200 adoption.', 'Long/Spatial/Object fixed30 each are accepted; no recollection. Freeze all72 selectors+16 references+all4 suite development receipts before full O2A/components.', 'Final35200 remain sealed until root global release; no training restart, checkpoint reselection, scientific-setting changes or new scope.']
 summary={'schema':'formal_main_v2','status':'two_k64seed23_development_pairs_root_and_independent_accepted','utc':utc,'training_arms':72,'training_pairs':36,'reviewed_arm_updates':360000,'new_development_accepted':400,'current_action_development_trials':5800,'compatible_legacy_Long_trials':600,'compatible_development_trials':6400,'planned_development_trials':8800,'all_historical_accepted_development_trials':7012,'unaccepted_original_attempts_retained':True,'unique_development_initial_states':400,'new_unique_initial_states':0,'new_GPU_jobs':[],'active_registered_GPU_jobs':[],'allocated_GPU_seconds':secs,'allocated_GPU_hours':secs/3600,'new_terminal_jobs_full_GPU_seconds':4458,'newly_accounted_GPU_seconds':secs-old['current_round_cost']['allocated_gpu_seconds'],'cost_final_for_current_registered_set':True,'controller_completed_normally':True,'controller_restarted':False,'accepted_fixed_observations_including_Long':90,'accepted_development':entries,'independent_terminal':ir,'engineering_CPU_evidence':inputs['CPU_archive_receipts'],'CPU_work_is_not_GPU_acceptance':True,'Goal_original200_and_new_science_HOLD':True,'Spatial_legacy12_compatibility_proven':False,'Object599_compatibility_adopted':False,'scientific_effect_conclusion':'Two matched seed23 development pairs each have B-A +1pp; no final or efficacy/equivalence claim. Other seeds retained and full timing/final evaluation pending.','final_trials':0,'final_total':35200,'final_sealed':True,'global_release':False,'O2A_released':False,'frozen_source_files_unchanged':173,'observation':snap,'capacity':cap,'state_before':before,'next_actions':nextactions}
 sr=save(B+'/final_summary.json',summary);f['latest_new_action_development_verified']=sr;f['integration_20261020T2054_accepted']=sr;f['downstream_followups_20261020T2054']=sr;s['last_root_supervision_snapshot']=sr
 for v in f['k64seed23_development_registration_20261020T1949'].values():
  if v['job_id'] in entries:v.update(status='root_and_independent_terminal_accepted',scheduler_status='COMPLETED',accepted_new_trials=200,terminal_review=entries[v['job_id']]['root_review'],independent_terminal=ir)
 s.update(stage='formal_main_v2_development_and_profiling_preparation',current_work='72/72 training arms and360000 updates complete; no controller restart. Current-action5800 plus compatible Long600=6400/8800 accepted development trials on400 unique states. Spatial/Object64seed23 each A96/B97 on100 fixed development states; no final effect conclusion. Remaining legacy/Goal gates pending. Final0/35200 sealed.',next_actions=nextactions,next_allowed_action='Integrate bounded Spatial/Object legacy provenance and Goal CPU gate only through original readiness and independent acceptance; no new engineering/science GPU until exact gate, no repeat completed work.',last_supervision_utc=utc,updated_utc=utc)
 paragraph=f"2026-10-21 本轮终审：正式训练72/72组、360000更新保持完成。Spatial3053875和Object3053894的64-token／seed23各200条开发记录通过本pair来源桥的原consumer及独立逐条审查；两套件均A=96/100、B=97/100，分别2283和2175 GPU秒，共1.238 GPU小时。此为开发结果，不作为最终收益结论。当前动作5800＋兼容Long600＝6400/8800条已验收，400唯一开发初态；既有历史计数7012，未通过的原尝试另完整保留。当前GPU作业0，正式累计{secs/3600:.3f} GPU小时，所有已登记分配只计一次。Spatial588恢复完成区分真实前置失败的CPU候选及独审，旧12条的当前动作兼容和新入口验收仍未完成。Object旧600明确为599正常完成＋1越界policy_error，失败动作chunk未保存，不能整批采纳。Goal配对初始输入门控完成CPU验证与独审候选，尚未做新生产GPU验收，原200和新增科学开发继续HOLD。固定开发观测仍90；完整O2A和分项计时等待全部身份及四套件开发收据冻结；最终0/35200继续封存。见[本轮汇总](../{B}/final_summary.json)。\n\n"
 for name in ['实验进度','完整实验计划','正式主实验规划','正式主实验阶段结论','正式自动连续训练执行登记']:
  p=R/'docs'/(name+'.md');original=p.read_bytes();need(paragraph.encode() not in original,'duplicate doc update');p.write_bytes(paragraph.encode()+original)
 blockers='# 正式下游阻塞登记\n\n'+paragraph+'| 套件 | 兼容开发验收 | 剩余门槛 |\n|---|---:|---|\n| Long | 2200/2200 | 固定30观测已验收，等待全局身份冻结后测速 |\n| Spatial | 1600/2200 | 保留旧12；588待精确恢复，旧12兼容与新P入口双审未通过 |\n| Object | 1600/2200 | 旧599正常＋1policy_error，完整兼容和显式异常尝试链未通过 |\n| Goal | 1000/2200 | 原200及另1000继续HOLD；CPU输入门控不能代替真实GPU验收 |\n\n## 明确的下一步\n\n'+ '\n\n'.join(str(i+1)+'. '+a for i,a in enumerate(nextactions))+'\n\n本轮没有新GPU提交、训练控制器重启、选模变更或封存值读取。两项64seed23已终验，禁止重复提交；此前两个固定观测采集亦不重复。完整原始记录、失败、CPU候选及负例一并保留，CPU synthetic仅为工程证据。\n'
 (R/'docs/正式下游阻塞登记_20261020T2054.md').write_text(blockers)
 need(f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs'] and ctl['completed_pairs']==old['autonomous_training_v1']['completed_pairs'],'training identity altered')
 c.atomic_json(sp,s,expected_sha=before)
 save(B+'/state_update_receipt.json',{'status':'root_integrated_exact400_and_engineering_evidence','before':before,'after':h(sp),'summary':sr,'inputs':ref(args.inputs),'new_scientific_development_trials':400,'new_initial_states':0,'new_GPU_jobs':0,'registered_job_changes':changes,'preserved_nonformal_records':sum(j.get('experiment')!='formal_main_v2' for j in s['registered_jobs']),'all_source173_unchanged':True,'final_sealed':True})
 print(json.dumps({'status':'accepted400','compatible_development':6400,'training_arms':72,'active_GPU_jobs':0,'GPU_hours':secs/3600,'summary':sr}))
