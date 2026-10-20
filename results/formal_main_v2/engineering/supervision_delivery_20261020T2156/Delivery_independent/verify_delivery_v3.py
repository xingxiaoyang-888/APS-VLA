"""Independent frozen delivery evidence check. No live scheduler queries or GPU work."""
from pathlib import Path
from datetime import datetime
import ast,collections,hashlib,json,math,os,re,sys,tarfile,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/delivery_independent_20261020T2156';B='results/formal_main_v2/preflight/heartbeat_20261021T0556';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2156';J='3054127'
STATE='63c74e7e591283409a792a7597fdb9bf99d1936ff1311e123bd687a83237a51f';SUMMARY='49a7791b1eeb5e8539cc1c27acf30fafdd09e2f7f284abd651e2e8b0b46c5bc4';UPDATE='559399babebfd6c29ecbfdff04d68ca0259750fc591e5c1b9c6e7fa98fbce241';DPIN='d3a8a445f5d0d13dfd93440256a8567fabfbb82a598bec6deb363bfd8b09ca17';MPIN='7e7da3f5b514102f08d105677e1dff504989aaf6c647f320405526d1fd2982ec'
checks=[];refs={};start=time.perf_counter();ct=time.process_time()
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for z in iter(lambda:f.read(8<<20),b''):h.update(z)
 return h.hexdigest()
def watch(p,pin=None):
 h=sha(p)
 if pin is not None:ck('SHA:'+str(p),h==pin)
 if str(p) in refs:ck('same_evidence:'+str(p),refs[str(p)]['sha256']==h)
 refs[str(p)]={'path':str(p),'sha256':h,'bytes':p.stat().st_size};return refs[str(p)]
def rd(p,pin=None):watch(p,pin);return json.loads(p.read_bytes())
def rr(ref):
 p=Path(ref['path']);return rd(p if p.is_absolute() else R/p,ref['sha256'])
def save(name,obj):
 p=D/name
 with p.open('x') as f:json.dump(obj,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def guard(ev,args):
 if ev in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('No scheduler/process/network commands in delivery audit')
 if ev=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if any('sealed' in n.lower() for n in p.parts) or ('final' in p.parts and p.name=='panel.json'):raise RuntimeError('Cannot read sealed values')
  mode,flags=args[1:3];w=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if w and not p.is_relative_to(D):raise RuntimeError('Only private delivery audit writes allowed')
def archive(name,manifest_name,pin,private_root):
 ar=R/E/name;m=rd(ar/manifest_name,pin);fs=m['files'];expected={}
 if isinstance(fs,list):
  for row in fs:expected[str(Path(row['path']).relative_to(private_root))]={'bytes':row['bytes'],'sha256':row['sha256']}
 else:expected=fs
 packed={};tar_path=ar/'CPU_synthetic_binary_evidence.tar.gz'
 if tar_path.exists():
  ix=rd(ar/'CPU_synthetic_binary_members.json');watch(tar_path,ix['archive']['sha256']);ck('archive_synthetic_only_'+name,ix['archive']['synthetic_CPU_only'] and ix['archive']['no_weights_or_sealed_values'])
  with tarfile.open(tar_path,'r:gz') as tar:
   for member in tar:
    ck('safe_regular_tar_member_'+name+':'+member.name,member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts and member.name not in packed)
    b=tar.extractfile(member).read();packed[member.name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
  ck('tar_index_exact_'+name,packed=={x['name']:{'bytes':x['bytes'],'sha256':x['sha256']} for x in ix['files']})
  ck('tar_count_'+name,len(packed)==ix['archive']['members'])
 for rel,x in expected.items():
  if rel in packed:ck('packed_original_'+name+':'+rel,packed[rel]==x)
  else:
   p=ar/rel;watch(p,x['sha256']);ck('archive_size_'+name+':'+rel,p.stat().st_size==x['bytes'])
 ck('no_extra_packed_'+name,set(packed)<=set(expected));return {'files':len(expected),'packed':len(packed),'manifest_sha256':pin}
def main():
 sys.dont_write_bytecode=True;os.environ['CUDA_VISIBLE_DEVICES']='';sys.addaudithook(guard)
 st=rd(R/'results/experiment_supervisor/state.json',STATE);q=rd(R/B/'final_summary.json',SUMMARY);update=rd(R/B/'state_and_document_update.json',UPDATE);f=st['formal_main_progress'];ctl=st['autonomous_training_v1']
 ck('summary_state_CAS_bound',update['state_after_sha256']==STATE and update['state_before_sha256']==q['state_before_sha256'] and update['summary']==st['last_root_supervision_snapshot'] and st['last_root_supervision_snapshot']=={'path':B+'/final_summary.json','sha256':SUMMARY})
 ck('science_not_added',q['new_development_accepted']==update['new_scientific_trials']==0 and q['new_unique_initial_states']==0 and q['compatible_development_trials']==6400 and q['planned_development_trials']==8800 and q['all_historical_accepted_development_trials']==f['completed_development_trials']==7012)
 ck('final_HOLD',q['final_sealed'] and q['final_trials']==f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'] and not q['global_release'] and not q['O2A_released'] and q['final_total']==35200)
 pairs=f['completed_training_pairs'];ck('36_pairs72arms',len(pairs)==36 and f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000)
 train_updates=0;selected=[];pairsigs=set()
 for pair,pv in pairs.items():
  match=re.fullmatch(r'(libero_(?:10|spatial|object|goal))_k(256|128|64)_seed(17|23|41)',pair);ck('registered_pair_key_'+pair,match is not None);sig=(match[1],int(match[2]),int(match[3]));ck('unique_scientific_pair_'+pair,sig not in pairsigs);pairsigs.add(sig)
  ck('state_completed_pair_'+pair,pv['trained_arms']==2 and pv['allowed_next_segment_end'] is None)
  if 'root_review' in pv:
   root=rd(R/pv['root_review'],pv['root_review_sha256']);ind=rd(R/pv['independent_review'],pv['independent_review_sha256']);ck('direct_original_root_independent_'+pair,root['status']=='passed' and ind['status'] in ['passed','passed_complete_training_only'] and root['completed_by_arm']=={'A':5000,'B':5000} and root['allowed_next_segment_end'] is None and root['continuation']=='formal_training_complete_no_extension')
   train_updates+=sum(root['completed_by_arm'].values());selected.extend(pv['selected_checkpoints']);ck('selected_AB_'+pair,{x['arm'] for x in pv['selected_checkpoints']}=={'A','B'})
  else:
   terminal=pv['terminal_root_and_independent_review'];root=rr(terminal['root_review']);ind=rr(terminal['independent_review']);changes=[x for x in root['changes'] if x['pair_key']==pair]
   ck('machine_origin_preserved_plus_actual_independent_'+pair,pv['verification_kind']=='machine_automatic_not_independent' and terminal['machine_origin_unchanged'] and root['status']=='accepted_training_integrity_not_scientific_efficacy' and ind['status']=='passed' and ind['pair_key']==pair and ind['completed_by_arm']==terminal['completed_by_arm']==pv['completed_by_arm']=={'A':5000,'B':5000} and ind['allowed_next_training_update'] is None and ind['original_raw_validator_rebuilt_exactly'])
   ck('root_explicit_pair_adoption_'+pair,len(changes)==1 and changes[0]['common_update']==5000 and changes[0]['independent_review']==terminal['independent_review'] and not root['scientific_success_or_latency_inferred'])
   train_updates+=sum(ind['completed_by_arm'].values());best=[x for x in ind['actual_checkpoint_checks'] if x['filename']=='best.pt'];selected.extend(best);ck('actual_independent_selected_AB_'+pair,{x['arm'] for x in best}=={'A','B'} and all(x['sha256']==ind['arms'][x['arm']]['best_checkpoint_sha256'] for x in best))
 ck('entire_registered_matrix',pairsigs=={(suite,k,seed) for suite in ['libero_10','libero_spatial','libero_object','libero_goal'] for k in [256,128,64] for seed in [17,23,41]} and train_updates==360000 and len(selected)==72)
 dev=0;devjobs=f['new_action_development_verified_by_job'];ck('no_engineering_in_science',J not in devjobs)
 for jid,x in devjobs.items():
  root=rr(x['root_review']);ind=rr(x['independent_review']);ck('verified_dev_'+jid,root['status']=='passed' and ind['status']=='passed' and root['completed_trials']==x['completed_trials'] and root['scientific_complete'] and not root['final_release'] and not root['final_state_values_read']);dev+=root['completed_trials']
 long=f['Long_legacy6_equivalence_followup'];rr(long['root_acceptance']);rr(long['real_development_compatibility_proof']);ck('Long600_only_compatible_legacy',long['original600_reused'] and long['production_reuse_authorized'] and not long['original600_rerun'] and long['actual_new_wrapper_trials_added']==0 and q['compatible_legacy_Long_trials']==600)
 ck('current5800_plus600_compatible6400',dev==f['current_action_development_trial_count']==q['current_action_development_trials']==5800 and dev+600==6400 and q['unique_development_initial_states']==400 and q['accepted_fixed_observations_including_Long']==90)
 prev=rr(f['downstream_followups_20261020T2054']);ck('previous_science_counts_preserved',prev['compatible_development_trials']==6400 and prev['current_action_development_trials']==5800 and prev['final_trials']==0)
 # Parse frozen raw sacct independently; no actual Slurm query is made.
 obs=q['observation'];raw={}
 for line in obs['raw_sacct'].splitlines():
  parts=line.split('|');jid=parts[0]
  ck('no_duplicate_raw_allocation_'+jid,jid not in raw);gpu=re.search(r'(?:^|,)gres/gpu=(\d+)(?:,|$)',parts[4]);raw[jid]={'seconds':int(parts[3]),'gpus':int(gpu.group(1)) if gpu else 0,'state':parts[1],'exit':parts[2]}
 formal=[j for j in st['registered_jobs'] if j.get('experiment')=='formal_main_v2'];ids=[str(j['job_id']) for j in formal];ck('270_unique_formal_allocations',len(ids)==len(set(ids))==270 and q['registered_formal_allocations']==270)
 costrows=[]
 for j in formal:
  jid=str(j['job_id']);v=raw[jid];r=obs['rows'][jid];ck('parsed_observation_cost_'+jid,v['seconds']==r['elapsed_seconds'] and v['gpus']==r['gpus']);costrows.append({'job_id':jid,'seconds':v['seconds'],'gpus':v['gpus'],'GPU_seconds':v['seconds']*v['gpus']})
 total=sum(x['GPU_seconds'] for x in costrows);ck('cost_sum_once',total==1984679==q['allocated_GPU_seconds']==st['current_round_cost']['allocated_gpu_seconds'] and math.isclose(q['allocated_GPU_hours'],total/3600,abs_tol=1e-12) and not st['current_round_cost']['final'])
 before=rd(R/B/'Goal_paired_dispatch/scheduler_before.json');beforeids=set(before['observation']['rows']);ck('exact_one_new_registered_allocation',set(obs['rows'])-beforeids=={J} and q['new_GPU_jobs']==update['new_GPU_jobs']==[J] and q['newly_accounted_GPU_seconds']==217)
 ck('controller_complete_cpu_no_restart',raw['3034538']['state']=='COMPLETED' and raw['3034538']['exit']=='0:0' and raw['3034538']['gpus']==0 and q['controller_lease_released'] and before['controller_lease_released'] and not q['controller_restarted'])
 ck('capacity_and_pending_clean',st['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None and ctl['occupied_job_ids']==q['active_registered_GPU_jobs']==q['capacity']['occupied']==[J] and not q['capacity']['unknown'] and not q['capacity']['findings'] and len(q['capacity']['occupied'])<=8 and not before['capacity']['occupied'])
 # Exact retained ACK, held registration and released token; no current-job polling.
 dp=R/B/'Goal_paired_dispatch';receipt=rd(dp/'receipt.json','6036de7bc77d6c0552dc6aa3f87a753ad731d94142c913851c731e4a90d8ab3b');ack=rd(dp/'submission_result.json');pending=rd(dp/'pending.json');held=rd(dp/'held_identity.json');released=rd(dp/'released_identity.json');releasecmd=rd(dp/'release_command.json');hreg=rd(dp/'held_dispatch_record.json');jobdoc=rr(receipt['job_record']);res=rd(dp/'reservation.json');storage=rd(dp/'storage_at_dispatch.json')
 ck('ACK_one_original_job',ack['returncode']==0 and ack['stdout']==J+'\n' and ack['stderr']=='' and receipt['job_id']==J and receipt['status']=='registered_and_release_verified' and receipt['state_after_sha256']==q['state_before_sha256'])
 auth=rr(receipt['authorization']);authsha=receipt['authorization']['sha256'];token='cti-goal-paired-input-v1:'+authsha;ck('same_unique_token',token==receipt['request_token']==pending['request_token']==hreg['request_token']==obs['queue'][J]['comment'])
 jobs=[j for j in st['registered_jobs'] if j.get('stage_key')=='goal_paired_input_gate_20261020T2156'];ck('one_registered_goal_stage',len(jobs)==1 and str(jobs[0]['job_id'])==J and jobs[0]['mode']=='engineering' and jobs[0]['scientific_trials']==0 and jobs[0]['maximum_attempts']==1 and not jobs[0]['automatic_retry'] and jobs[0]['gpus']==1 and jobs[0]['wall_limit_seconds']==1800)
 ck('argv_matches_original_intent',jobs[0]['downstream_gateway']['actual_sbatch_argv']==pending['actual_sbatch_argv'] and '--hold' in pending['actual_sbatch_argv'] and '--no-requeue' in pending['actual_sbatch_argv'] and pending['status']=='intent_persisted_before_sbatch')
 for name,record in [('held',held),('released',released)]:
  ck(name+'_successful_command',record['returncode']==0);fields=dict(re.findall(r'(\w+)=([^\s]*)',record['stdout']))
  ck(name+'_exact_job_identity',fields['JobId']==J and fields['JobName']=='cti-goal-paired-input' and fields['Comment']==token and fields['Requeue']==fields['Restarts']=='0' and fields['Command']==str(P/'scripts/ops/formal_goal_paired_input_gate_v1/run.slurm') and fields['WorkDir']==str(S) and fields['TresPerNode']=='gres:gpu:l40:1')
  ck(name+'_hold_state',fields['Reason']=='JobHeldUser' if name=='held' else fields['Reason']!='JobHeldUser')
 ck('dispatch_order_and_release',pending['created_utc']<ack['utc']<held['utc']<released['utc']<receipt['utc'] and releasecmd['returncode']==0 and hreg['status']=='held_registered_before_release' and hreg['new_submissions']==1 and hreg['maximum_attempts']==1)
 ck('disk_recording_kept',storage['required_free_including_1GiB_margin']==4363621114 and storage['actual_free_bytes']>=4363621114 and not storage['recording_reduced'])
 ck('Goal_HOLD_preserved',auth['original_goal200_HOLD'] and auth['new_Goal_science_HOLD'] and not auth['scientific_release'] and receipt['Goal_original200_HOLD'] and receipt['all_new_Goal_science_HOLD'] and q['Goal_original200_and_new_science_HOLD'] and q['Goal_paired_input_engineering']['scientific_trials_added']==0 and not q['Goal_paired_input_engineering']['terminal_evidence_reviewed'])
 for field,role in [('root_review','root'),('independent_review','independent')]:
  review=rr(auth[field]);ck('authorization_'+role+'_passed',review['status']=='passed' and review['reviewed_by']==role and review['package_manifest_sha256']==MPIN and review['scientific_release'] is False)
 ck('distinct_root_independent_readiness',auth['root_review']['sha256']!=auth['independent_review']['sha256'])
 for n in ['root_authorization.json','independent_readiness.json','root_readiness.json','reservation.json','held_dispatch_record.json']:
  rel='results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156/'+n;rp=dp/n if n in ['reservation.json','held_dispatch_record.json'] else R/rel;ck('R_P_exact_'+n,sha(rp)==sha(P/rel));watch(rp);watch(P/rel)
 dr=rr(receipt['dispatch_review']);ck('v3_dispatch_review',dr['status']=='passed' and dr['entrypoint_sha256']==DPIN and not dr['blockers']);watch(R/dr['entrypoint'],DPIN)
 # Source package and original 173 scientific files still byte-identical, no weights copied.
 pk='scripts/ops/formal_goal_paired_input_gate_v1';m=rd(R/pk/'package_manifest.json',MPIN);watch(P/pk/'package_manifest.json',MPIN)
 for rel,pin in m['files'].items():watch(R/rel,pin);watch(P/rel,pin)
 inventory=rd(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')['files'];ck('173_exact_count',len(inventory)==173)
 for base in [R,S,R/'snapshots/formal_main_v2_run_564be0995e']:
  for rel,pin in inventory.items():watch(base/rel,pin)
 # Exact nonweight archives of approved CPU proofs; no claims of production adoption.
 archives={}
 for name,mname,pin,private in [('Goal_author','delivery_manifest_original.json','96cf89b08102278f6311c652842326ac10b1466944e8e5b08b1e8c160e9650e1','.local/goal_gate_integration_20261020T2156'),('Goal_independent','delivery_manifest_original.json','4f7d5fdfd684123d7e4693ff5bf21aec5ff436ebee9f95ef559fa0152eeb0ed6','.local/goal_paired_independent_20261020T2156'),('K64_stats_independent','delivery_manifest_original.json','9a354bdba95b85002bbbf223efabd7cd6c8385c51f159bae88d029e9bca6db67','.local/k64_stats_independent_20261020T2156'),('Object_author','stage1_delivery_manifest_original.json','9020eb66c1746924379106baf19cd5d50318bf4283370b900785acba596c1992','.local/object_legacy_integration_20261020T2156')]:archives[name]=archive(name,mname,pin,private)
 for ref in q['engineering_CPU_evidence'].values():rr(ref)
 ck('Spatial_Object_legacy_not_adopted',not q['Spatial_legacy12_production_adopted'] and not q['Spatial588_new_GPU_submission'] and not q['Object599_compatibility_adopted'] and q['Object_original_policy_error_retained'])
 stats=rr(q['development_k64_statistics']);statsind=rr(q['development_k64_statistics_independent']);ck('k64_independent_exact',statsind['status']=='passed' and not statsind['blockers'] and statsind['root_statistics_sha256']==q['development_k64_statistics']['sha256'] and statsind['check_count']==235 and not statsind['root_intermediate_pairs_used_for_reconstruction'])
 ck('k64_dev_scope',stats['development_only'] and stats['same_initial_state_carries_all_three_seeds'] and stats['task_stratified_bootstrap_repeats']==10000 and stats['bootstrap_seed']==20261016 and all(v['unique_state_clusters']==100 and v['trials']==600 for v in stats['suite_results'].values()))
 for dr in update['documents']:
  watch(R/dr['path'],dr['sha256']);text=(R/dr['path']).read_text();ck('doc_correct_current_summary_'+dr['path'],'6400/8800' in text and '最终0/35200' in text and '3054127' in text and '1984679' in text and '不是最终效果、等效或加速证据' in text)
 # Static Git candidate review; deliberately do not import this top-level executable script.
 gitpath=R/'.local/deliver_20261020T2156.py';watch(gitpath,'40e2ee06b48d913a9f1663ef57070f73c9dfc2f17a98033b00652981301b5949');git=gitpath.read_text();ast.parse(git)
 for phrase in ["with c.exclusive_lock", "git('diff','--cached','--name-only').stdout==b''", "audit['state_sha256']==h(R/'results/experiment_supervisor/state.json')", "assert not unknown", "p.stat().st_size<100*(1<<20)", "guard.check(R,SNAP,SSHA,RAW,required)", "frozen_files_verified_in_worktree_and_index", "index_guard':'passed'", "BASE='cd39cf3ef3781fbebf5614bd3f3c54e34de869ee'"]:ck('Git_static_guard:'+phrase,phrase in git)
 ck('Git_no_push_or_force',not any(x in git for x in ["git('push'",'--force','--amend','reset --hard']))
 watch(R/'scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6')
 for path,x in refs.items():ck('final_stable:'+path,sha(Path(path))==x['sha256'])
 evidence=save('evidence.json',{'files':list(refs.values()),'archives':archives,'allocation_costs_once':costrows,'selected_checkpoint_metadata_count':len(selected),'checkpoint_bytes_read':False,'scope':'Frozen snapshot at UTC22:29:33. No current job status polling.'})
 report={'schema':'formal_main_v2','status':'passed_final_delivery_review','blockers':[],'state_sha256':STATE,'summary_sha256':SUMMARY,'source173_verified':True,'source173_locations':['R','P/frozen_snapshot','R/frozen_snapshot_mirror'],'final_sealed':True,'final_trials':0,'final_release':False,'compatible_development_trials':6400,'planned_development_trials':8800,'current_action_trials':5800,'compatible_Long600':True,'training_arms':72,'training_pairs':36,'training_updates':360000,'registered_formal_allocations':270,'allocated_GPU_seconds':total,'allocated_GPU_hours':total/3600,'active_registered_GPU_jobs_snapshot':[J],'new_GPU_jobs':[J],'new_scientific_trials':0,'Goal_original200_and_new_science_HOLD':True,'Object599_compatibility_adopted':False,'Spatial12_compatibility_adopted':False,'snapshot_utc':q['utc'],'no_live_Slurm_queries':True,'new_GPU_seconds':0,'state_Git_Slurm_P_mutations':0,'independent_source':'/root/spatial588_recovery_audit_2054','evidence':evidence,'checks':checks,'check_count':len(checks),'Git_candidate_static_review':'passed under exact manifest, same-state and index checks at execution; no commit/push performed by this audit','excluded_scope':'Spatial phase2/phase2_v2 CPU candidates were not independently reviewed here and are not production admission. Object replacement stage2 not implemented. Goal running outcome not inspected.','CPU_seconds':time.process_time()-ct,'wall_seconds':time.perf_counter()-start}
 ref=save('independent_delivery_review.json',report);print(json.dumps({'review':ref,'state_sha256':STATE,'check_count':len(checks),'GPU_seconds':total}),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:save('failure_'+str(time.time_ns())+'.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':checks});raise
