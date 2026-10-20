"""Independent full-metadata and lossless-blob audit for existing Goal engineering 3053440. No runtime execution."""
from pathlib import Path,PurePosixPath
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib,json,os,sys,tarfile,math,traceback,time,re,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';A=R/'.local/goal_prefix58_terminal_20261020T1825';D=Path(__file__).parent
RUN=P/'results/formal_main_v2/engineering/goal_prefix58_20261020T1825/attempt01';OLD=P/'results/formal_main_v2/libero_goal/downstream/development/5185766bb353c8e6/attempt01';JOB='3053440'
AUTH='195e064794973fbc533dfc6c51afd7ec3fbb942734753c1d7f1a7b9c81687a75';PACKAGE='28b3a3f5a61dd666722915cec86a7d9c4c8d86aaf5b5c35b04f4808aa43ab5d0'
READS={};COUNTS=Counter();CHECKS=[];started=time.process_time();sys.dont_write_bytecode=True
CKROOT=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal/k256/seed17')
ALLOWED_CK={CKROOT/x/'best.pt' for x in ('A','B')}
def hook(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect'):raise RuntimeError('No scheduler, subprocess or network allowed')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,int):return
  p=Path(os.fsdecode(p)).absolute()
  if any('sealed' in part.lower() for part in p.parts):raise RuntimeError('Sealed payload forbidden')
  if p.suffix.lower() in ('.pt','.pth','.ckpt','.safetensors') and p not in ALLOWED_CK:raise RuntimeError('Only two exact selector checkpoint byte hashes allowed')
  if p.suffix.lower()=='.bin' and not (RUN/'observer/blobs') in p.parents:raise RuntimeError('Only exact passive observation blob bytes permitted')
  writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC))
  if writing:assert D in p.parents,'private-only outputs'
 if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.symlink','os.link'):
  for x in args[:2] if event in ('os.rename','os.symlink','os.link') else args[:1]:
   p=Path(os.fsdecode(x)).absolute();assert p==D or D in p.parents,'private-only mutation'
sys.addaudithook(hook)
def ck(ok,msg,category='metadata'):
 if not ok:raise AssertionError(msg)
 COUNTS[category]+=1
 if category not in ('blob','array','hash','source'):CHECKS.append(msg)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def pin(p,expected=None):
 p=Path(p);p=p if p.is_absolute() else R/p;ck(p.resolve()==p and not any(q.is_symlink() for q in (p,*p.parents)),'nonlink path '+str(p),'source');v=sha(p);ck(expected is None or v==expected,'input hash '+str(p),'hash');ck(str(p) not in READS or READS[str(p)]['sha256']==v,'stable source '+str(p),'hash');READS[str(p)]={'sha256':v,'bytes':p.stat().st_size};return p
 def_unused=0

def obj(p,expected=None):return json.loads(pin(p,expected).read_bytes())
def lines(p,expected=None):return [json.loads(x) for x in pin(p,expected).read_bytes().splitlines() if x]
def ref(p):p=Path(p);return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def put(name,x):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write(chr(10))
 return ref(p)
try:
 manifest=obj(A/'delivery_manifest.json','249fb309d591d86dfc8f0e68d6f3045a55059bcdb0e63158a461686ee4f480b8');report=obj(A/'terminal_diagnostic.json','e222987b1ff4b20799f855d9e84be1a11e9e7921b1a83d8f61fa1f00582dc509')
 ck(manifest['file_count']==len(manifest['files'])==47 and manifest['total_bytes']==sum(x['bytes'] for x in manifest['files']),'author exact47 files / total bytes')
 for x in manifest['files']:
  q=PurePosixPath(x['path']);ck(not q.is_absolute() and '..' not in q.parts and x['source']==(A/q).relative_to(R).as_posix(),'author manifest path/source');pin(A/q,x['sha256']);ck((A/q).stat().st_size==x['bytes'],'author file byte length','hash')
 inputs=obj(A/'input_manifest.json');source_map={x['source']:x for x in inputs};ck(len(source_map)==len(inputs),'unique author original inputs')
 for x in inputs:pin(x['source'],x['sha256']);ck(Path(x['source']).stat().st_size==x['bytes'],'actual original input bytes','source')
 for x in obj(A/'copied_files_manifest.json'):
  ck(str(x['source']) in source_map,'all copied outputs have source proof');pin(A/x['copy'],x['sha256']);pin(x['source'],x['sha256']);ck((A/x['copy']).stat().st_size==x['bytes'],'private source-copy bytes','source')
 original_inv=obj(A/'inputs/original_invocation.json','c07489c5e56cc3255b60f5eb6df34146e37e4b60fa7151cc97f8008f402b8803');execution=obj(A/'inputs/original_execution_manifest.json','3b33f2d0e0c924ac919920a2a12b1c0e8cb9e059c58d58a639fd33f4651036c2');pkg=obj(A/'inputs/package_manifest.json',PACKAGE);auth=obj(A/'inputs/root_authorization.json',AUTH)
 for name,h in pkg['files'].items():pin(P/name,h);pin(R/name,h)
 ck(auth['scientific_release'] is False and auth['package_manifest_sha256']==PACKAGE,'actual authorization and package no scientific release')
 cfg=obj(A/'raw/run/original_run/config.json');ck(cfg['manifest']==execution and cfg['manifest']['split']=='development' and cfg['manifest']['suite']=='libero_goal','original manifest entirely preserved')
 ck(execution['environment']=={'action_chunk':8,'environment_seed':0,'max_steps':300,'runtime_seed':17,'wait_steps':10},'environment unchanged')
 ck([m['identity']['method_id'] for m in execution['methods']]==['A256_seed17','B256_seed17'],'exact original A/B256 seed17')
 for method in execution['methods']:
  ident=method['identity'];p=Path(method['checkpoint']);ck(p in ALLOWED_CK and ident['future_head_deployed'] is False and ident['visual_tokens']==256 and ident['training_seed']==17 and ident['training_complete'] is True,'selected checkpoint scientific identity');pin(p,ident['checkpoint_sha256'])
 for source,h in original_inv['watched_files'].items():pin(source,h)
 for source,h in cfg['source_files'].items():pin(S/source,h)
 inventory=obj(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');ck(len(inventory['files'])==173,'exact173 frozen inventory')
 for source,h in inventory['files'].items():pin(R/source,h);pin(S/source,h)
 saved_job=obj(A/'registered_job_observation.json')['job'];ck(saved_job['job_id']==JOB and saved_job['mode']=='engineering' and saved_job['run_root']==str(RUN) and saved_job['invocation_sha256']==AUTH and saved_job['scientific_trials']==0 and saved_job['maximum_attempts']==1 and saved_job['automatic_retry'] is False,'registered exact one-attempt engineering identity')
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH);statebytes=(R/'results/experiment_supervisor/state.json').read_bytes();fcntl.flock(lock,fcntl.LOCK_UN)
 state=json.loads(statebytes);live=[x for x in state['registered_jobs'] if str(x['job_id'])==JOB];ck(len(live)==1 and all(live[0].get(k)==saved_job.get(k) for k in ('job_id','mode','run_root','invocation_sha256','scientific_trials','maximum_attempts')),'registered job unchanged at independent read')
 ck(not state['formal_main_progress']['test_opened'] and not state['formal_main_progress']['global_release_created'],'final still sealed at independent read')
 sacct=pin(A/'sacct.stdout.txt','6842b0770ec997a264ec5be3a10cfc599dbfe3fb61632c53e376365e7648a424').read_text();allocation_rows=[row.split('|') for row in sacct.splitlines() if row];allocation=[r for r in allocation_rows if r[0]==JOB];ck(len(allocation)==1,'deduplicate allocation parent only');row=allocation[0];ck(row[1:5]==['cti-goal-prefix58','COMPLETED','0:0','803'] and row[6]=='gpu4015','stored original successful803sec Slurm allocation');tres=dict(x.split('=',1) for x in row[5].split(','));ck(tres['gres/gpu']=='1' and tres['gres/gpu:l40']=='1' and tres['cpu']=='7','one L40 capacity');ck(report['allocation']['GPU_seconds']==803 and report['allocation']['GPU_hours']==803/3600 and report['allocation']['count_once'] is True,'803sec once, not batch/extern double count')
 comp=obj(A/'raw/run/outer/completion.json');outer=lines(A/'raw/run/outer/events.jsonl');events=lines(A/'raw/run/observer/events.jsonl');ledger=lines(A/'raw/run/original_run/trials.jsonl');trials=[x for x in ledger if x['event']=='result'];starts=[x for x in ledger if x['event']=='start'];oldsource=pin(OLD/'trials.jsonl',source_map[str(OLD/'trials.jsonl')]['sha256']);old=[x for x in lines(oldsource) if x['event']=='result'][:58];ck(old==obj(A/'inputs/original_prefix58_result_rows.json'),'actual original first58 matches derived excerpt')
 ck(len(trials)==len(starts)==len(old)==58 and len(ledger)==117 and [x['event'] for x in ledger]==['invocation']+['start','result']*58,'original ledger exactly58 sequential attempts')
 ck(comp['status']=='returned_58_engineering_only' and comp['exit_code']==0 and comp['errors']==[] and not comp['observer_failed'] and comp['last_observer_abort'] is None and comp['observer_begun']==comp['observer_finished']==58,'outer completion58 with no guard failure')
 ck(comp['original_runtime_restored'] and not comp['original_actions_forced'] and comp['scientific_trials_added']==0 and comp['original_goal200_HOLD'] and comp['new_Goal_science_HOLD'] and not comp['final_release'] and comp['maximum_attempts']==1,'outer scientific HOLD and one-attempt boundaries')
 ck(comp['authorization_sha256']==AUTH and comp['package_manifest_sha256']==PACKAGE and comp['raw_event_sha256']==sha(A/'raw/run/outer/events.jsonl'),'completion seals exact outer event journal')
 ck(len(outer)==23 and [x['seq'] for x in outer]==list(range(23)) and all(x['job_id']==JOB and x['scientific_trials_added']==0 for x in outer),'all23 outer event identities')
 ck(outer[0]['original_argument_changes']=={'output':str(RUN/'original_run'),'stop_after':58} and outer[0]['original_invocation']=={'path':str(P/'results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json'),'sha256':'c07489c5e56cc3255b60f5eb6df34146e37e4b60fa7151cc97f8008f402b8803'},'only original output/stop_after changed')
 ck(outer[-1]['observer_finish']['event_sha256']==sha(A/'raw/run/observer/events.jsonl') and outer[-1]['runtime_proof']['all_source_and_binding_contexts_restored'] and outer[-1]['runtime_proof']['status']=='complete_runtime_structure_only','observer journal and restored runtime source proof')
 proof=next(x['proof'] for x in outer if x['event']=='prefix_observer_scope_enter')
 for name in ('run_episode','trial_loop'):
  z=proof[name];ck(z['original_ast_sha256']==z['stripped_ast_sha256'] and z['original_calls']==z['projected_calls'] and z['original_function_unchanged_after_projection'] and z['original_policy_timer_statements_unchanged'],'observed exact audited AST projection '+name)
 ex=next(x for x in outer if x['event']=='prefix_observer_scope_exit');ck(ex['bindings_intact'] and ex['bindings_restored'] and not ex['runner_raised'],'observer context restored')
 ck(proof['original_execute_and_loading_untouched'] and proof['accepted_action_context_required'],'original loading and accepted action context')
 adapter=lines(A/'raw/adapter/3053440_5a3683e9b92344d7be5c7357122a4ebb.jsonl');ck(adapter[0]['event']=='adapter_start' and adapter[-1]['event']=='adapter_end' and adapter[-1]['status']=='returned' and adapter[-1]['runner_status']=='incomplete' and sum(x['event']=='bindings_restored' for x in adapter)==1,'one original adapter returned bounded incomplete panel')
 captures=[x for x in events if 'event_index' in x];ends=[x for x in events if x.get('event')=='trial_end'];ck(len(events)==1807 and len(captures)==1749 and len(ends)==58,'1807 observer records /1749 captures /58 terminals')
 ck([x['event_index'] for x in captures]==list(range(1,1750)) and all(x.get('scientific_trials_added')==0 for x in events),'monotonic observer record identity')
 nontrial=[x for x in captures if x['ordinal'] is None];ck(len(nontrial)==9 and all(x['phase'].startswith('existing_loader_event:') and x['trial_identity'] is None for x in nontrial[:8]) and [x['event_index'] for x in nontrial[:8]]==list(range(1,9)) and nontrial[-1]['phase']=='original_runner_returned' and nontrial[-1]['event_index']==1749 and nontrial[-1]['trial_identity'] is None,'eight loader markers plus final original-runner-returned guard separately identified')
 ck(all(x['invariants']=={'global_rng_unchanged':True,'object_identity_and_bytes_unchanged':True,'passive_sim_and_environment_rng_unchanged':True} for x in captures),'all capture guards recorded passed, backed by pinned audited source')
 # Independently read archives without filesystem extraction; compare every member to original P bytes.
 blobs=obj(A/'blob_archive_member_manifest.json');members={x['path']:x for x in blobs['members']};ck(len(members)==len(blobs['members'])==2803,'unique2803 archived passive blobs');cache={};seen=set();archive_proofs=[]
 for ar in blobs['archives']:
  pin(A/ar['path'],ar['sha256']);count=0
  with tarfile.open(A/ar['path'],'r|gz') as tf:
   for member in tf:
    name=PurePosixPath(member.name);ck(member.isfile() and not name.is_absolute() and '..' not in name.parts and name.parts[:2]==('observer','blobs') and member.name in members and member.name not in seen,'safe exact archive member','blob');rec=members[member.name];ck(rec['source']==str(RUN/member.name) and rec['bytes']==member.size,'member exactsource and length','blob');raw=tf.extractfile(member).read();v=hashlib.sha256(raw).hexdigest();ck(len(raw)==rec['bytes'] and v==rec['sha256'],'member SHA roundtrip','blob');pin(RUN/member.name,v);ck((RUN/member.name).stat().st_size==len(raw),'actual original P blob byte length','blob');cache[str(name.relative_to('observer'))]=raw;seen.add(member.name);count+=1
  ck(count==ar['members'],'archive member count');archive_proofs.append({'archive':ref(A/ar['path']),'members_verified':count,'actual_P_byte_hashes_verified':True})
 ck(seen==set(members) and sum(len(x) for x in cache.values())==126313589,'all126313589 bytes /2803 blobs preserved')
 references=set();obskeys=('agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos')
 def blobcheck(v):
  p=v['path'];ck(p in cache and len(cache[p])==v['bytes'] and hashlib.sha256(cache[p]).hexdigest()==v['sha256'],'blob reference bytes','blob');references.add(p);return cache[p]
 def recurse(v):
  if isinstance(v,dict):
   if isinstance(v.get('path'),str) and v['path'].startswith('blobs/'):blobcheck(v)
   for y in v.values():recurse(y)
  elif isinstance(v,list):
   for y in v:recurse(y)
 for capture in captures:
  recurse(capture)
  arrays=capture['observation_arrays']
  if arrays:
   ck(set(arrays)==set(obskeys),'exact five passive observed arrays','array');h=hashlib.sha256()
   for key in obskeys:
    m=arrays[key];raw=blobcheck(m['blob']);ck(hashlib.sha256(raw).hexdigest()==m['sha256'] and len(raw)==m['bytes']==math.prod(m['shape'])*{'uint8':1,'float64':8}[m['dtype']],'array shape dtype digest','array');h.update(key.encode());h.update(m['dtype'].encode());h.update(str(tuple(m['shape'])).encode());h.update(raw)
   ck(h.hexdigest()==capture['observation_sha256'],'independent aggregate observation hash','array')
  if 'fields' in capture['sim']:
   for field,m in capture['sim']['fields'].items():
    if isinstance(m,dict) and 'sha256' in m:
     b=capture['sim_array_blobs']['sim.'+field];ck(m['sha256']==b['sha256'] and m['bytes']==b['bytes'],'passive simulator snapshot matches raw blob','array')
 ck(references==set(cache),'all archive blobs referenced without gaps')
 prefix=obj(A/'inputs/package/prefix58.json')['rows'];panel=obj(A/'raw/run/original_run/panel.json');ck(panel['suite']=='libero_goal' and len(panel['states'])==100 and len(prefix)==58,'fixed development panel and prefix')
 panelrows=[]
 for state in panel['states']:
  for method in ('A256_seed17','B256_seed17'):
   panelrows.append({**state,'state_trial_id':state['trial_id'],'trial_id':state['trial_id']+':'+method,'method':method})
 keys=('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method');per=[];pairs=[];phase_order=['trial_begin_before_reseed','reseed_after','factory_before','factory_after','reset_before','reset_after','set_init_before','set_init_after']+['wait_before','wait_after']*10+['t0_query_before','t0_query_after'];grouped=defaultdict(list)
 for cap in captures:
  if cap['ordinal'] is not None:grouped[cap['ordinal']].append(cap)
 for i,(new,previous,start,end,pr,panelrow) in enumerate(zip(trials,old,starts,ends,prefix,panelrows),1):
  ck(all(new[k]==previous[k]==start[k]==end['trial_identity'][k]==pr[k]==panelrow[k] for k in keys),'full original prefix identity '+str(i));cc=grouped[i];ck([c['phase'] for c in cc]==phase_order and all(c['trial_identity']=={k:new[k] for k in keys} for c in cc),'exact30ordered phases '+str(i));ck([c['wait_steps'] for c in cc if c['phase']=='wait_after']==list(range(1,11)),'ten wait actions '+str(i))
  ck(new['suite']=='libero_goal' and new['split']=='development' and new['status']=='completed' and new['wait_steps']==new['configured_wait_steps']==10 and new['action_chunk']==8 and new['environment_seed']==0 and new['runtime_seed']==17 and 0<len(new['executed_actions'])<=300,'unchanged trial settings '+str(i))
  actions=new['executed_actions'];chunks=new['chunks'];ck(new['control_steps']==len(actions) and new['policy_calls']==len(chunks)==math.ceil(len(actions)/8) and [c['control_step'] for c in chunks]==list(range(0,len(actions),8)),'control/query counts and cadence '+str(i))
  ck([a for c in chunks for a in c['environment_actions']][:len(actions)]==actions,'all executed actions exactly from original chunks '+str(i))
  checkpoint=execution['methods'][(i-1)%2]['identity']
  for c in chunks:
   m=c['metadata'];ck(m['action_version']=='libero-oft-boundsq99-gripper-sign-invert-chunk8-v1' and m['packing_version']=='oft-original-positions-v1' and m['future_head_calls']==0 and m['policy_calls']==m['vision_calls']==m['packing_calls']==m['scorer_calls']==1 and m['visual_tokens']==256 and m['per_camera_budgets']==[128,128] and m['selector_checkpoint_sha256']==checkpoint['checkpoint_sha256'] and m['pair_id']==checkpoint['pair_id'] and m['training_seed']==17 and m['suite']=='libero_goal' and m['method']==checkpoint['method'],'original query action/source metadata','query');ids=m['retained_indices'];ck(len(ids)==len(set(ids))==256 and ids==sorted(ids) and sum(0<=x<256 for x in ids)==128 and sum(256<=x<512 for x in ids)==128,'packing exact budget/order','query');ck(len(c['normalized_actions'])==len(c['environment_actions'])==8 and all(len(a)==7 and all(math.isfinite(v) for v in a) for a in c['normalized_actions']+c['environment_actions']),'finite8x7 action arrays','query')
  before,after=cc[-2:];ck(after['observation_sha256']==chunks[0]['observation_sha256']==end['t0_hashes']['t0_query_after'] and before['observation_sha256']==end['t0_hashes']['t0_query_before'],'t0 record/ledger consistency '+str(i))
  adiff=[j for j,(a,b) in enumerate(zip(previous['executed_actions'],actions)) if a!=b];cdiff=[j for j,(a,b) in enumerate(zip(previous['chunks'],chunks)) if {k:v for k,v in a.items() if k!='engineering_seconds'}!={k:v for k,v in b.items() if k!='engineering_seconds'}]
  result={'ordinal':i,'trial_id':new['trial_id'],'t0_original_sha256':previous['chunks'][0]['observation_sha256'],'t0_before_sha256':before['observation_sha256'],'t0_after_sha256':after['observation_sha256'],'predict_changed_t0_arrays':before['observation_arrays']!=after['observation_arrays'],'predict_changed_passive_sim':before['sim']!=after['sim'],'predict_changed_global_rng':before['global_rng']!=after['global_rng'],'old_policy_calls':previous['policy_calls'],'new_policy_calls':new['policy_calls'],'old_executed_actions':len(previous['executed_actions']),'new_executed_actions':len(actions),'actions_exactly_equal':previous['executed_actions']==actions,'first_different_common_action_index':adiff[0] if adiff else None,'different_common_action_count':len(adiff),'chunks_exact_except_timing':not cdiff and len(previous['chunks'])==len(chunks),'first_different_common_chunk_index':cdiff[0] if cdiff else None,'all_common_metadata_equal':all(a['metadata']==b['metadata'] for a,b in zip(previous['chunks'],chunks))};per.append(result)
  if i%2==0:pairs.append({'state_trial_id':new['state_trial_id'],'A_ordinal':i-1,'B_ordinal':i,'A_t0_sha256':per[-2]['t0_before_sha256'],'B_t0_sha256':result['t0_before_sha256'],'equal':per[-2]['t0_before_sha256']==result['t0_before_sha256']})
 ck(per==obj(A/'per_trial_history_comparison.json') and pairs==obj(A/'paired_t0_comparison.json'),'all58 history rows and29 t0 pairs independently match author')
 derived={'actual_policy_queries':sum(t['policy_calls'] for t in trials),'actual_executed_policy_actions':sum(len(t['executed_actions']) for t in trials),'dummy_actions':len(trials)*10,'original_prefix56_queries':sum(t['policy_calls'] for t in old[:56]),'new_prefix56_queries':sum(t['policy_calls'] for t in trials[:56]),'original_prefix56_actions':sum(len(t['executed_actions']) for t in old[:56]),'new_prefix56_actions':sum(len(t['executed_actions']) for t in trials[:56]),'paired_t0_mismatch_count':sum(not p['equal'] for p in pairs),'unique_development_states':len(set(t['state_trial_id'] for t in trials)),'query_before_after_array_changes':[p['ordinal'] for p in per if p['predict_changed_t0_arrays']],'old_vs_new_t0_changed_ordinals':[p['ordinal'] for p in per if p['t0_original_sha256']!=p['t0_before_sha256']],'action_history_changed_ordinals':[p['ordinal'] for p in per if not p['actions_exactly_equal']]}
 ck(all(report[k]==v for k,v in derived.items()),'all diagnostic totals independently rebuilt');ck(derived['actual_policy_queries']==940 and derived['actual_executed_policy_actions']==7302 and derived['unique_development_states']==29 and derived['action_history_changed_ordinals']==[27,30,33,46,57,58] and derived['old_vs_new_t0_changed_ordinals']==[57] and derived['paired_t0_mismatch_count']==0,'bounded observed diagnostic conclusions')
 ck(report['scientific_trials_added']==0 and report['original_goal200_HOLD'] and report['new_Goal_science_HOLD'] and not report['final_release'] and not report['independent_GPU_acceptance_claimed'],'author conclusions no scientific acceptance')
 ck(all(p['predict_changed_t0_arrays'] is False and p['predict_changed_global_rng'] is False and p['predict_changed_passive_sim'] is False for p in per),'no recorded t0 pre/post query mutation in this run')
 missing=Counter(json.dumps(c['sim'].get('environment_rng'),sort_keys=True) for c in captures if 'environment_rng' in c['sim']);ck(set(missing)=={json.dumps({'missing':'no direct NumPy RNG object in env dictionaries'},sort_keys=True)},'environment RNG is explicitly missing, not independently proved identical')
 for path,rec in READS.items():ck(sha(path)==rec['sha256'],'audited source unchanged '+path,'hash')
 details=put('metadata_checks.json',{'counts':dict(COUNTS),'total_checks':sum(COUNTS.values()),'checks':CHECKS,'derived_totals':derived,'passive_archive_proofs':archive_proofs,'missing_environment_rng_record_counts':dict(missing),'author_input_metadata_files_verified':len(inputs),'state_observation_sha256':hashlib.sha256(statebytes).hexdigest(),'evidence_sha256':READS,'CPU_seconds':time.process_time()-started})
 comparison=put('independent_history_comparison.json',{'trials':per,'pairs':pairs})
 verdict=put('independent_diagnostic.json',{'schema':'formal_main_v2','kind':'goal_prefix58_terminal_independent_diagnostic','status':'passed_evidence_audit_engineering_only','reviewed_by':'independent','review_agent':'/root/devplans_audit_20261020_1418','job_id':JOB,'author_terminal_report':ref(A/'terminal_diagnostic.json'),'author_delivery_manifest':ref(A/'delivery_manifest.json'),'authorization_sha256':AUTH,'package_manifest_sha256':PACKAGE,'allocation':{'job_id':JOB,'state':'COMPLETED','exit_code':'0:0','GPU_seconds':803,'GPU_hours':803/3600,'allocation_parent_count':1,'step_allocations_additionally_counted':0},'trial_records_verified':58,'all_policy_query_metadata_verified':940,'all_executed_policy_actions_verified':7302,'dummy_actions_verified':580,'observed_unique_development_states':29,'paired_t0_mismatch_count':0,'observed_t0_before_after_array_changes':[],'old_vs_new_t0_changed_ordinals':[57],'action_history_changed_ordinals':[27,30,33,46,57,58],'exact_historical_action_replay':False,'historical_failure_root_cause_established':False,'historical_failure_repaired':False,'original_goal200_admissible':False,'original_goal200_HOLD':True,'new_Goal_science_HOLD':True,'scientific_trials_added':0,'scientific_release':False,'final_release':False,'formal_O2A_timing_evidence':False,'actual_existing_GPU_engineering_record_verified':True,'new_GPU_launches':0,'new_Slurm_queries':0,'production_state_or_Git_changes':False,'all2803_passive_blob_hashes_verified':True,'archive_roundtrip_and_original_P_bytes_verified':True,'two_selector_checkpoint_bytes_verified':True,'source173_unchanged':True,'independent_live_runtime_replay_performed':False,'blockers_to_archiving_diagnostic':[],'metadata_report':details,'history_comparison':comparison,'audit_source':ref(Path(__file__)),'limitations':['This validates the existing engineering evidence, not scientific correctness or a new GPU rerun.','Original post-query-only t0 data cannot distinguish its cause; the new history differs before ordinal57, so no exact replay or correction claim is allowed.','All observed captured guards and t0 arrays passed; missing direct environment RNG and hidden simulator state are not inferred.','803 GPU-seconds must be charged once as engineering cost; observer I/O timings are not formal O2A.','Goal old200 and new Goal scientific work remain HOLD; no automatic repeat, replacement or final release.']})
 print(json.dumps({'independent_diagnostic':verdict,'metadata_checks':details,'checks':sum(COUNTS.values()),'derived':derived,'CPU_seconds':time.process_time()-started}))
except BaseException as ex:
 put('failure_v2.json',{'status':'failed','error_type':type(ex).__name__,'error':str(ex),'traceback':traceback.format_exc(),'checks_completed':sum(COUNTS.values()),'counts':dict(COUNTS)});raise
