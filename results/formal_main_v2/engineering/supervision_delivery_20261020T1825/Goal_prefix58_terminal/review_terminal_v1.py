"""Read-only terminal diagnostics for registered Goal engineering job3053440.
No imports of model/runtime, no GPU or Slurm mutation, no science acceptance.
All copied output is nonweight development evidence in the exact recorded subtree.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from collections import Counter
import json, hashlib, math, fcntl, subprocess, time, tarfile, gzip, traceback, re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/goal_prefix58_terminal_20261020T1825'
RUN=P/'results/formal_main_v2/engineering/goal_prefix58_20261020T1825/attempt01'
BASE=RUN.parent; PKG=P/'scripts/ops/formal_goal_prefix58_observer_v2'
OLD=P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01'
JOB='3053440'; AUTH='195e064794973fbc533dfc6c51afd7ec3fbb942734753c1d7f1a7b9c81687a75'; PACKAGE='28b3a3f5a61dd666722915cec86a7d9c4c8d86aaf5b5c35b04f4808aa43ab5d0'
OBS=('agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos')
IDS=('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method')
checks=[]; copied=[]; inputs={}
def check(ok,msg):
 if not ok:raise ValueError(msg)
 checks.append(msg)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def js(p):return json.loads(Path(p).read_bytes())
def write(rel,value):
 p=D/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(value,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def pin(p,expected=None):
 p=Path(p);check(p.is_file() and not p.is_symlink() and p.resolve()==p,'safe input '+str(p));s=sha(p)
 if expected:check(s==expected,'pin '+str(p))
 v={'source':str(p),'sha256':s,'bytes':p.stat().st_size};inputs[str(p)]=v;return v
def copy(p,rel,expected=None):
 v=pin(p,expected);target=D/rel;target.parent.mkdir(parents=True,exist_ok=True)
 with Path(p).open('rb') as a,target.open('xb') as b:
  while True:
   raw=a.read(8<<20)
   if not raw:break
   b.write(raw)
 check(sha(target)==v['sha256'] and target.stat().st_size==v['bytes'],'exact private copy '+rel)
 copied.append({**v,'copy':rel});return v

def main():
 start=time.perf_counter();cpu=time.process_time()
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH);raw=(R/'results/experiment_supervisor/state.json').read_bytes();state= json.loads(raw);jobs=state['registered_jobs'];job=jobs[JOB] if isinstance(jobs,dict) else next(x for x in jobs if str(x['job_id'])==JOB);fcntl.flock(lock,fcntl.LOCK_UN)
 check(job['mode']=='engineering' and job['run_root']==str(RUN) and job['invocation_sha256']==AUTH and job['scientific_trials']==0 and job['maximum_attempts']==1,'exact registered engineering identity')
 write('registered_job_observation.json',{'state_sha256':hashlib.sha256(raw).hexdigest(),'job':job,'read_under_shared_writer_lock':True,'not_a_state_update':True})
 q=subprocess.run(['sacct','-n','-P','-j',JOB,'--format=JobIDRaw,JobName,State,ExitCode,ElapsedRaw,AllocTRES,NodeList'],capture_output=True,check=True)
 (D/'sacct.stdout.txt').write_bytes(q.stdout);(D/'sacct.stderr.txt').write_bytes(q.stderr)
 rows=[x.split('|') for x in q.stdout.decode().splitlines() if x];row=next(x for x in rows if x[0]==JOB)
 check(row[2]=='COMPLETED' and row[3]=='0:0' and int(row[4])==803 and row[6]=='gpu4015','actual successful803second allocation')
 check('gres/gpu=1' in row[5] and 'cpu=7' in row[5],'actual one GPU seven CPU allocation')
 allocation={'job_id':JOB,'status':row[2],'exit_code':row[3],'elapsed_seconds':int(row[4]),'alloc_tres':row[5],'node':row[6],'GPU_seconds':803,'GPU_hours':803/3600,'count_once':True}
 auth=js(BASE/'root_authorization.json');copy(BASE/'root_authorization.json','inputs/root_authorization.json',AUTH)
 package=js(PKG/'package_manifest.json');copy(PKG/'package_manifest.json','inputs/package_manifest.json',PACKAGE)
 for rel,pinvalue in package['files'].items():copy(P/rel,'inputs/package/'+Path(rel).name,pinvalue)
 check(auth['package_manifest_sha256']==PACKAGE and auth['scientific_release'] is False,'authorization package and no release')
 for role in ('root','independent'):
  rr=auth[role+'_review'];check(Path(rr['path'])==BASE/(role+'_readiness.json'),'exact new readiness path '+role);copy(Path(rr['path']),'inputs/'+role+'_readiness.json',rr['sha256'])
 for rel in ['reservation.json','held_dispatch_record.json']:copy(BASE/rel,'inputs/'+rel)
 dispatch=js(BASE/'held_dispatch_record.json');check(dispatch['job_id']==JOB and dispatch['authorization']['sha256']==AUTH and dispatch['new_submissions']==1,'one original ACK and token')
 cfg=js(PKG/'config.json');pref=js(PKG/'prefix58.json')['rows'];invp=Path(cfg['original_invocation']['path']);inv=js(invp);copy(invp,'inputs/original_invocation.json',cfg['original_invocation']['sha256'])
 execution=js(inv['execution_manifest']);copy(Path(inv['execution_manifest']),'inputs/original_execution_manifest.json',inv['execution_manifest_sha256'])
 checkpoint_proofs=[]
 for m in execution['methods']:
  x=pin(Path(m['checkpoint']),m['identity']['checkpoint_sha256']);checkpoint_proofs.append({**x,'copied':False,'method_id':m['identity']['method_id']})
 write('checkpoint_identity_recheck.json',checkpoint_proofs)
 source_pins={}
 for p,s in inv['watched_files'].items():source_pins[p]=pin(Path(p),s)['sha256']
 write('original_source_and_watched_files_recheck.json',source_pins)
 for p in sorted(RUN.rglob('*')):
  if p.is_file() and not p.is_relative_to(RUN/'observer/blobs'):copy(p,'raw/run/'+str(p.relative_to(RUN)))
 for suffix in ('out','err'):copy(P/('results/slurm/cti-goal-prefix58_'+JOB+'.'+suffix),'raw/slurm/'+JOB+'.'+suffix)
 adapters=sorted((P/'results/formal_main_v2/adapter_invocations').glob(JOB+'_*'));check(len(adapters)==2 and {p.suffix for p in adapters}=={'.json','.jsonl'},'one adapter invocation pair')
 for p in adapters:copy(p,'raw/adapter/'+p.name)
 adapter_rows=[json.loads(x) for x in next(p for p in adapters if p.suffix=='.jsonl').read_text().splitlines()]
 check(adapter_rows[-1]['event']=='adapter_end' and adapter_rows[-1]['status']=='returned' and adapter_rows[-1]['runner_status']=='incomplete','original adapter returned bounded incomplete panel')
 check(sum(x['event']=='adapter_start' for x in adapter_rows)==1 and sum(x['event']=='bindings_restored' for x in adapter_rows)==1,'one adapter start and restored')
 check(adapter_rows[0]['identity']['verified_frozen_file_count']==173 and adapter_rows[0]['identity']['frozen_source_sha256']==job['source_sha256'],'original frozen173 identity bound')
 completion=js(RUN/'outer/completion.json');outer=[json.loads(x) for x in (RUN/'outer/events.jsonl').read_text().splitlines()];events=[json.loads(x) for x in (RUN/'observer/events.jsonl').read_text().splitlines()]
 ledger=[json.loads(x) for x in (RUN/'original_run/trials.jsonl').read_text().splitlines()];trials=[x for x in ledger if x.get('event')=='result'];starts=[x for x in ledger if x.get('event')=='start'];oldraw=(OLD/'trials.jsonl').read_bytes();old=[json.loads(x) for x in oldraw.splitlines() if x];old=[x for x in old if x.get('event')=='result'][:58]
 pin(OLD/'trials.jsonl');write('inputs/original_prefix58_result_rows.json',old)
 check(len(trials)==len(starts)==len(pref)==58 and len(ledger)==117,'exact58start/result rows and one invocation')
 check(completion['status']=='returned_58_engineering_only' and completion['exit_code']==0 and completion['errors']==[] and not completion['observer_failed'] and completion['last_observer_abort'] is None,'outer successful and no observer abort')
 check(completion['observer_begun']==completion['observer_finished']==58 and completion['original_runtime_restored'] is True,'outer58 and contexts restored')
 check(completion['authorization_sha256']==AUTH and completion['package_manifest_sha256']==PACKAGE and completion['raw_event_sha256']==sha(RUN/'outer/events.jsonl'),'outer exact identity/hash')
 check(completion['scientific_trials_added']==0 and completion['original_goal200_HOLD'] and completion['new_Goal_science_HOLD'] and not completion['final_release'] and not completion['original_actions_forced'],'zero scientific trials and HOLD maintained')
 check([x['seq'] for x in outer]==list(range(23)) and all(x['job_id']==JOB and x['scientific_trials_added']==0 for x in outer),'outer contiguous23 event identity')
 finish=outer[-1];check(finish['event']=='engineering_prefix_returned' and finish['observer_finish']['event_sha256']==sha(RUN/'observer/events.jsonl'),'observer journal terminal hash')
 check(finish['runtime_proof']['all_source_and_binding_contexts_restored'] and finish['runtime_proof']['status']=='complete_runtime_structure_only','original runtime structure proof')
 proof=next(x for x in outer if x['event']=='prefix_observer_scope_enter')['proof']
 check(proof['original_execute_and_loading_untouched'] and not proof['scientific_settings_changed'] and proof['accepted_action_context_required'],'observer overlay original execution context')
 for name in ('run_episode','trial_loop'):
  z=proof[name];check(z['stripped_ast_sha256']==z['original_ast_sha256'] and z['original_function_unchanged_after_projection'] and z['projected_calls']==z['original_calls'],'overlay original AST projection '+name)
 exitrow=next(x for x in outer if x['event']=='prefix_observer_scope_exit');check(exitrow['bindings_intact'] and exitrow['bindings_restored'] and not exitrow['runner_raised'],'observer overlay exit restored')
 check(not any('Traceback (most recent call last)' in (P/('results/slurm/cti-goal-prefix58_'+JOB+'.'+suffix)).read_text() for suffix in ('out','err')),'no fatal traceback in Slurm logs')
 captures=[x for x in events if 'event_index' in x];ends=[x for x in events if x.get('event')=='trial_end']
 check(len(captures)==1749 and len(ends)==58 and len(events)==1807,'1749 captures and58 terminal journal records')
 check([x['event_index'] for x in captures]==list(range(1,1750)),'capture event index continuous')
 check(all(x.get('scientific_trials_added')==0 for x in events),'all observer records engineering only')
 check(all(x['invariants']=={'global_rng_unchanged':True,'object_identity_and_bytes_unchanged':True,'passive_sim_and_environment_rng_unchanged':True} for x in captures),'all1749 recorded passive guards passed')
 check(not any(x.get('event')=='observer_abort' for x in events),'no observer abort journal')
 refs={}
 def scan(value):
  if isinstance(value,dict):
   if isinstance(value.get('path'),str) and value['path'].startswith('blobs/'):
    path=PurePosixPath(value['path']);check(len(path.parts)==2 and '..' not in path.parts and re.fullmatch('[0-9a-f]{64}\\.(bin|rng\\.json)',path.name) is not None,'safe exact blob reference')
    record={'path':str(path),'sha256':value['sha256'],'bytes':value['bytes']}
    if str(path) in refs:check(refs[str(path)]==record,'consistent repeated blob reference')
    refs[str(path)]=record
   for v in value.values():scan(v)
  elif isinstance(value,list):
   for v in value:scan(v)
 for x in captures:scan(x)
 blob_files=sorted((RUN/'observer/blobs').iterdir());check({str(p.relative_to(RUN/'observer')) for p in blob_files}==set(refs),'all raw blobs referenced exactly with no extras or gaps')
 raw_cache={}
 for rel,v in refs.items():
  p=RUN/'observer'/rel;check(p.is_file() and not p.is_symlink() and sha(p)==v['sha256'] and p.stat().st_size==v['bytes'],'blob bytes verified '+rel);raw_cache[rel]=p.read_bytes()
 for x in captures:
  arrays=x['observation_arrays']
  if not arrays:continue
  check(set(arrays)==set(OBS),'five exact observation arrays')
  h=hashlib.sha256()
  for key in OBS:
   m=arrays[key];b=raw_cache[m['blob']['path']];check(len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256'],'array bytes agree with descriptor')
   check(math.prod(m['shape'])*{'uint8':1,'float64':8}[m['dtype']]==m['bytes'],'array shape/dtype byte count')
   h.update(key.encode());h.update(m['dtype'].encode());h.update(str(tuple(m['shape'])).encode());h.update(b)
  check(h.hexdigest()==x['observation_sha256'],'recomputed aggregate observation hash')
 phases=['trial_begin_before_reseed','reseed_after','factory_before','factory_after','reset_before','reset_after','set_init_before','set_init_after']+[phase for i in range(10) for phase in ('wait_before','wait_after')]+['t0_query_before','t0_query_after']
 per=[];paired=[];t0_by_trial={}
 for n,(t,o,prefrow,st,end) in enumerate(zip(trials,old,pref,starts,ends),1):
  check(all(t[k]==o[k]==prefrow[k]==st[k]==end['trial_identity'][k] for k in IDS),'exact original prefix identity '+str(n))
  check(t['environment_seed']==0 and t['runtime_seed']==17 and t['wait_steps']==10 and t['action_chunk']==8 and t['status']=='completed','fixed completed environment settings '+str(n))
  cc=[x for x in captures if x['ordinal']==n];check([x['phase'] for x in cc]==phases,'all ordered reset/wait/t0 markers '+str(n))
  check([x['wait_steps'] for x in cc if x['phase']=='wait_after']==list(range(1,11)),'ten actual wait markers '+str(n))
  before,after=cc[-2:];check(after['observation_sha256']==t['chunks'][0]['observation_sha256']==end['t0_hashes']['t0_query_after'],'postquery hash equals original ledger '+str(n));t0_by_trial[n]=before['observation_sha256']
  action_diff=[i for i,(a,b) in enumerate(zip(o['executed_actions'],t['executed_actions'])) if a!=b]
  chunkdiff=[i for i,(a,b) in enumerate(zip(o['chunks'],t['chunks'])) if {k:v for k,v in a.items() if k!='engineering_seconds'}!={k:v for k,v in b.items() if k!='engineering_seconds'}]
  per.append({'ordinal':n,'trial_id':t['trial_id'],'t0_original_sha256':o['chunks'][0]['observation_sha256'],'t0_before_sha256':before['observation_sha256'],'t0_after_sha256':after['observation_sha256'],'predict_changed_t0_arrays':before['observation_arrays']!=after['observation_arrays'],'predict_changed_passive_sim':before['sim']!=after['sim'],'predict_changed_global_rng':before['global_rng']!=after['global_rng'],'old_policy_calls':o['policy_calls'],'new_policy_calls':t['policy_calls'],'old_executed_actions':len(o['executed_actions']),'new_executed_actions':len(t['executed_actions']),'actions_exactly_equal':o['executed_actions']==t['executed_actions'],'first_different_common_action_index':action_diff[0] if action_diff else None,'different_common_action_count':len(action_diff),'chunks_exact_except_timing':o['chunks']==t['chunks'] if False else not chunkdiff and len(o['chunks'])==len(t['chunks']),'first_different_common_chunk_index':chunkdiff[0] if chunkdiff else None,'all_common_metadata_equal':all(a['metadata']==b['metadata'] for a,b in zip(o['chunks'],t['chunks']))})
  if n%2==0:paired.append({'state_trial_id':t['state_trial_id'],'A_ordinal':n-1,'B_ordinal':n,'A_t0_sha256':t0_by_trial[n-1],'B_t0_sha256':t0_by_trial[n],'equal':t0_by_trial[n-1]==t0_by_trial[n]})
 write('per_trial_history_comparison.json',per);write('paired_t0_comparison.json',paired)
 # Archive only exact nonweight passive blobs, in deterministic lossless parts.
 members=[{'source':str(p),'path':str(p.relative_to(RUN)),'sha256':sha(p),'bytes':p.stat().st_size} for p in blob_files]
 groups=[];group=[];size=0
 for member in members:
  if group and size+member['bytes']>64*1024*1024:groups.append(group);group=[];size=0
  group.append(member);size+=member['bytes']
 if group:groups.append(group)
 archives=[]
 for i,group in enumerate(groups,1):
  rel='arrays_archive/goal_prefix58_3053440_passive_blobs_part%02d.tar.gz'%i;target=D/rel;target.parent.mkdir(exist_ok=True)
  with target.open('xb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0,compresslevel=6) as gz,tarfile.open(fileobj=gz,mode='w|',format=tarfile.USTAR_FORMAT) as tar:
   for member in group:
    info=tarfile.TarInfo(member['path']);info.size=member['bytes'];info.mtime=0;info.mode=0o644;info.uid=info.gid=0
    with Path(member['source']).open('rb') as stream:tar.addfile(info,stream)
  check(target.stat().st_size<100*1024*1024,'archive under100MiB '+rel)
  with tarfile.open(target,'r|gz') as tar:
   count=0
   for mi in tar:
    expected=group[count];check(mi.isfile() and mi.name==expected['path'] and mi.size==expected['bytes'],'archive member exact path/size');stream=tar.extractfile(mi);h=hashlib.sha256();n=0
    for b in iter(lambda:stream.read(8<<20),b''):h.update(b);n+=len(b)
    check(n==expected['bytes'] and h.hexdigest()==expected['sha256'],'archive member stream roundtrip');count+=1
   check(count==len(group),'archive exact member count')
  archives.append({'path':rel,'sha256':sha(target),'bytes':target.stat().st_size,'members':len(group)})
 write('blob_archive_member_manifest.json',{'kind':'lossless_nonweight_development_passive_blob_archive','source_root':str(RUN),'members':members,'archives':archives,'all_members_stream_verified':True,'original_sources_retained':True,'weights_included':False,'sealed_values_included':False})
 for v in inputs.values():check(sha(v['source'])==v['sha256'],'source still unchanged '+v['source'])
 report={'schema':'formal_main_v2','kind':'goal_prefix58_read_only_terminal_diagnostic','status':'complete_engineering_evidence_mismatch_not_reproduced' if all(p['equal'] for p in paired) else 'complete_engineering_evidence_paired_mismatch_present','reviewer':'/root/devplans_20261020_1418','review_role':'original_observer_author_terminal_analysis_not_independent_acceptance','created_utc':datetime.now(timezone.utc).isoformat(),'job_id':JOB,'allocation':allocation,'authorization_sha256':AUTH,'package_manifest_sha256':PACKAGE,'observer_capture_records':1749,'trial_end_records':58,'raw_observer_jsonl_records':1807,'dummy_actions':580,'actual_policy_queries':sum(x['policy_calls'] for x in trials),'actual_executed_policy_actions':sum(len(x['executed_actions']) for x in trials),'original_prefix56_queries':sum(x['policy_calls'] for x in old[:56]),'new_prefix56_queries':sum(x['policy_calls'] for x in trials[:56]),'original_prefix56_actions':sum(len(x['executed_actions']) for x in old[:56]),'new_prefix56_actions':sum(len(x['executed_actions']) for x in trials[:56]),'paired_t0_mismatch_count':sum(not x['equal'] for x in paired),'query_before_after_array_changes':[x['ordinal'] for x in per if x['predict_changed_t0_arrays']],'old_vs_new_t0_changed_ordinals':[x['ordinal'] for x in per if x['t0_original_sha256']!=x['t0_before_sha256']],'action_history_changed_ordinals':[x['ordinal'] for x in per if not x['actions_exactly_equal']],'endpoint_rows':per[-2:],'unique_development_states':29,'original_runtime_contexts_restored':True,'observed_overlay_AST_projection_preserved':True,'all_capture_blob_hashes_and_aggregate_hashes_verified':True,'raw_blobs':len(members),'raw_blob_bytes':sum(x['bytes'] for x in members),'archives':archives,'original_runner_status':'incomplete:58 of200 original panel, expected for engineering stop_after58','scientific_trials_added':0,'original_goal200_HOLD':True,'new_Goal_science_HOLD':True,'final_release':False,'independent_GPU_acceptance_claimed':False,'GPU_launches_by_this_analysis':0,'Slurm_mutations':0,'production_state_changes':0,'limitations':['Historical actions were recomputed, not forced; observed common policy/action traces are compared explicitly and differ. Same identities and query totals do not prove identical prior history.','The old A97bfd36f hash was recorded only after prediction; old raw pre/post arrays are unavailable, so this run cannot identify the old discrepancy cause.','This run observed no before/after t0 array change and no paired mismatch; this does not prove the original failure repaired or authorize accepting/replacing the held200.','Native simulator fields and direct dictionary RNG were read passively. No direct NumPy environment RNG was found; missing data is explicitly recorded and no hidden simulator state is inferred.','Observer copies and disk I/O perturb wall time. The803 allocated GPU seconds are full engineering cost, not formal O2A latency.','The original ledger retains outcomes but none is used for admission or new scientific counts.'],'next_step':'Keep original200 and new Goal science HOLD. Root and an independent reviewer should verify this sealed terminal package and the exact trace difference report before choosing any further bounded engineering experiment; no rerun or scientific release is proposed automatically.','CPU_process_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-start,'check_count':len(checks)}
 write('input_manifest.json',list(inputs.values()));write('copied_files_manifest.json',copied);write('checks.json',checks);write('terminal_diagnostic.json',report)
 print(json.dumps({k:report[k] for k in ['status','allocation','paired_t0_mismatch_count','query_before_after_array_changes','old_vs_new_t0_changed_ordinals','action_history_changed_ordinals','raw_blobs','raw_blob_bytes','archives','check_count','CPU_process_seconds','wall_seconds']},sort_keys=True))
if __name__=='__main__':
 try:main()
 except BaseException as error:
  failure={'error_type':type(error).__name__,'error':str(error),'traceback':traceback.format_exc(),'checks_completed':len(checks),'GPU_launches':0,'Slurm_mutations':0}
  write('attempt01_failure.json',failure);raise
