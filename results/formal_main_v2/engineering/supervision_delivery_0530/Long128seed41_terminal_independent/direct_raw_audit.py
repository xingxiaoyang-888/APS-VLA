"""Independent direct raw audit; no submission, result publication or model loading."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter,defaultdict
import hashlib,importlib.util,json,sys,copy
import numpy as np
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).resolve().parent
BASE='results/formal_main_v2/libero_10/downstream/development/428eafaeb10a5ce3/attempt01'
INV='results/formal_main_v2/invocations/libero_10_development_428eafaeb10a5ce3_attempt01.json';INV_SHA='2a7e9f4fbaf9947eec17807ca21c351a2e0c12fb512e5bd3f9619502e1db0afc'
seen={}
def need(ok,msg):
 if not ok:raise ValueError(msg)
def raw(p,pin=None):
 p=Path(p);before=p.stat();b=p.read_bytes();after=p.stat()
 need((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'unstable input '+str(p))
 h=hashlib.sha256(b).hexdigest();need(pin is None or h==pin,'SHA mismatch '+str(p))
 need(str(p) not in seen or seen[str(p)]['sha256']==h,'changed '+str(p));seen[str(p)]={'sha256':h,'bytes':len(b)}
 return b
def read(p,pin=None):return json.loads(raw(p,pin),parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def save(name,v):
 p=D/name;b=json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+bytes([10])
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def main():
 inv=read(R/INV,INV_SHA);need(raw(P/INV,INV_SHA)==raw(R/INV,INV_SHA),'P/R invocation')
 need(inv['stage']=='development' and inv['suite']=='libero_10' and inv['method_ids']==['A128_seed41','B128_seed41'],'science scope')
 need(inv['prior_job_ids']==[] and inv['prior_review'] is None and inv['resume'] is False,'fresh ancestry required')
 need(not any(x in inv['argv'] for x in ['--sealed-final','--release','--future-observation','--executed-actions']),'forbidden inputs')
 co=read(R/inv['action_execution_contract']['path'],inv['action_execution_contract']['sha256'])
 runtime_name='scripts/ops/formal_action_deployment_v1/runtime_scope.py'
 for rel,h in {**co['files'],**co['runtime_contract']['dependencies'],**co['GPU_acceptance']}.items():
  need(raw(P/rel,h)==raw(R/rel,h),'source P/R '+rel)
 inventory=read(R/co['source_inventory']['path'],co['source_inventory']['sha256'])
 need(len(inventory['files'])==173,'173 count')
 for rel,h in inventory['files'].items():raw(R/rel,h);raw(Path(inv['source_root'])/rel,h)
 sp=importlib.util.spec_from_file_location('long3045322_actual_runtime',R/runtime_name);runtime=importlib.util.module_from_spec(sp);sp.loader.exec_module(runtime)
 prefix=P/BASE/'action_execution/3045322'
 identity=read(prefix/'identity.json');complete=read(prefix/'completion.json');events_bytes=raw(prefix/'events.jsonl')
 events=[json.loads(x) for x in events_bytes.splitlines()]
 need(len(events)==13 and all(x['seq']==i for i,x in enumerate(events)),'13 contiguous runtime events')
 for x in events+[identity,complete]:
  need(x['job_id']=='3045322' and x['invocation_sha256']==INV_SHA and x['version']=='formal-downstream-action-v1','runtime job identity')
  need(x['action_execution_contract']==inv['action_execution_contract'] and x['runtime_readiness']==inv['runtime_readiness'],'runtime contract/readiness')
 structural=runtime.verify_runtime_events(events,co['runtime_contract'])
 need(structural['synthetic_input'] is False and structural['original_base_loads']==1 and structural['all_source_and_binding_contexts_restored'] is True,'runtime restoration')
 need(complete['events_sha256']==hashlib.sha256(events_bytes).hexdigest() and complete['identity_sha256']==seen[str(prefix/'identity.json')]['sha256'],'completion hashes')
 need(complete['status']=='returned' and complete['exit_code']==0 and complete['errors']==[] and complete['runner_status']=='completed','clean runtime end')
 need(complete['wall_seconds']<=3466,'runtime wall')
 manifest=read(Path(inv['execution_manifest']),inv['execution_manifest_sha256']);config=read(P/BASE/'config.json');panel=read(P/BASE/'panel.json');report=read(P/BASE/'closed_loop_report.json')
 need(config['manifest']==manifest,'manifest raw config')
 need(raw(P/BASE/'panel.json',manifest['development_panel_sha256'])==raw(R/manifest['development_panel'],manifest['development_panel_sha256']),'registered development panel')
 need(manifest['environment']=={'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':520},'environment fixed')
 need(panel['split']=='development' and len(panel['states'])==100 and Counter(s['task_id'] for s in panel['states'])==Counter({i:10 for i in range(10)}),'100 fixed task states')
 states={s['trial_id']:s for s in panel['states']};methods={m['identity']['method_id']:m['identity'] for m in manifest['methods']}
 need(set(methods)=={'A128_seed41','B128_seed41'},'two methods only')
 for mid,ident in methods.items():
  need(ident['training_complete'] is True and ident['future_head_deployed'] is False and ident['training_seed']==41 and ident['visual_tokens']==128,'deployment training')
 ledger=raw(P/BASE/'trials.jsonl',report['trials_jsonl_sha256']);need(ledger.endswith(bytes([10])),'truncated ledger')
 rows=[json.loads(x,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON'))) for x in ledger.splitlines()]
 need(Counter(x['event'] for x in rows)==Counter({'invocation':1,'start':200,'result':200}),'exact invocation/start/result ledger')
 need(rows[0]['event']=='invocation' and rows[0]['slurm_job_id']=='3045322','raw invocation owner')
 starts={};results={};per_task={m:{str(i):{'successes':0,'trials':0} for i in range(10)} for m in methods};first_obs={};chunks_count=0;controls=0;over_bound=0;max_abs=0.;attempt_sum=0.;wall_sum=0.;retained={}
 for row in rows:
  need(row['run_signature']==report['provenance']['run_signature'],'run signature')
  if row['event']=='invocation':continue
  mid=row['method'];sid=row['state_trial_id'];tid=row['trial_id'];need(mid in methods and sid in states and tid==sid+':'+mid,'trial identity')
  st=states[sid]
  for k in ['initial_state_sha256','task_id','task_name','source_state_index']:need(row[k]==st[k],'state mismatch '+k)
  for k,v in {'suite':'libero_10','split':'development','environment_seed':0,'runtime_seed':17,'action_chunk':8,'configured_wait_steps':10}.items():need(row[k]==v,'trial setting '+k)
  if row['event']=='start':
   need(tid not in starts and tid not in results,'duplicate trial start');starts[tid]=row;continue
  need(tid in starts and tid not in results,'orphan/duplicate result');results[tid]=row
  need(row['status']=='completed' and type(row['success']) is bool and row['wait_steps']==10,'trial status/wait')
  n=row['control_steps'];need(type(n) is int and 0<n<=520,'control horizon')
  need((row['success'] and row['termination']=='environment_success') or (not row['success'] and n==520 and row['termination']=='task_horizon'),'outcome/termination')
  need([x['control_step'] for x in row['chunks']]==list(range(0,n,8)) and row['policy_calls']==len(row['chunks']),'chunk cadence')
  predicted=[]
  for ch in row['chunks']:
   meta=ch['metadata'];ident=methods[mid]
   for k,v in {'suite':'libero_10','method':ident['method'],'visual_tokens':128,'per_camera_budgets':[64,64],'policy_calls':1,'vision_calls':1,'packing_calls':1,'scorer_calls':1,'future_head_calls':0,'language_cache':'disabled','selector_checkpoint_sha256':ident['checkpoint_sha256'],'pair_id':ident['pair_id'],'training_seed':41,'packing_version':'oft-original-positions-v1','action_version':'libero-oft-boundsq99-gripper-sign-invert-chunk8-v1'}.items():need(meta.get(k)==v,'deployment chunk '+k)
   kept=meta['retained_indices'];need(len(kept)==128 and kept==sorted(set(kept)) and all(type(x)is int and 0<=x<512 for x in kept) and sum(x<256 for x in kept)==64,'hard token identity')
   arrays=[np.asarray(ch[k],dtype=np.float64) for k in ('normalized_actions','environment_actions')]
   need(all(x.shape==(8,7) and np.isfinite(x).all() for x in arrays),'finite 8x7')
   env=arrays[1];max_abs=max(max_abs,float(np.max(np.abs(env))));over_bound+=int(np.any(np.abs(env)>1.00001));predicted.append(env);chunks_count+=1
  need(row['chunks'],'no chunks')
  obs=row['chunks'][0]['observation_sha256'];need(first_obs.setdefault(sid,obs)==obs,'paired initial observations')
  retained[(sid,mid)]=set(row['chunks'][0]['metadata']['retained_indices'])
  executed=np.asarray(row['executed_actions'],dtype=np.float64)
  need(executed.shape==(n,7) and np.isfinite(executed).all() and np.array_equal(executed,np.concatenate(predicted)[:n]),'actual executed actions differ from returned chunks')
  controls+=n;attempt_sum+=row['attempt_wall_seconds'];wall_sum+=row['wall_seconds']
  per_task[mid][str(row['task_id'])]['trials']+=1;per_task[mid][str(row['task_id'])]['successes']+=int(row['success'])
 expected={sid+':'+mid for sid in states for mid in methods};need(set(results)==set(starts)==expected,'full fixed200 coverage')
 successes={mid:sum(int(r['success']) for r in results.values() if r['method']==mid) for mid in methods}
 pairs=Counter((int(results[sid+':A128_seed41']['success']),int(results[sid+':B128_seed41']['success'])) for sid in states)
 for mid in methods:need(report['methods'][mid]['trials']==100 and report['methods'][mid]['successes']==successes[mid] and report['methods'][mid]['success_rate']==successes[mid]/100,'reported success')
 need(report['paired_AB']['k128_seed41']['B_minus_A_success_rate']==(successes['B128_seed41']-successes['A128_seed41'])/100,'reported paired difference')
 for mid in methods:
  for task,x in per_task[mid].items():
   expected=dict(x,success_rate=x['successes']/x['trials']);need(report['methods'][mid]['per_task'][task]==expected,'raw per task outcome')
 for task in map(str,range(10)):
  diff=(per_task['B128_seed41'][task]['successes']-per_task['A128_seed41'][task]['successes'])/10
  need(report['paired_AB']['k128_seed41']['per_task'][task]=={'B_minus_A':diff,'pairs':10},'raw paired per task difference')
 need(report['completed_trials']==report['expected_trials']==200 and report['unique_initial_states']==100 and report['test_opened'] is False and report['checkpoint_unchanged'] is True,'summary scope')
 need(report['cost']['known_policy_calls']==report['cost']['policy_calls_total']==chunks_count and report['cost']['recorded_result_attempts']==200 and report['cost']['unfinished_attempts_unknown_cost']==0,'raw attempt cost')
 need(abs(report['cost']['known_attempt_wall_seconds']-attempt_sum)<1e-7 and abs(report['cost']['known_wall_seconds']-wall_sum)<1e-7,'wall reconstruction')
 overlaps=[len(retained[(sid,'A128_seed41')]&retained[(sid,'B128_seed41')])/128 for sid in states]
 for p,h in list(seen.items()):raw(p,h['sha256'])
 result={'schema':'formal_main_v2','kind':'Long3045322_independent_direct_raw_audit','status':'passed_direct_raw_pending_root_transport_and_exact_consumer',
  'utc':datetime.now(timezone.utc).isoformat(),'job_id':'3045322','invocation':{'path':INV,'sha256':INV_SHA},'fixed_trials':200,'unique_development_initial_states':100,
  'fresh_ancestry':True,'prior_job_ids':[],'scientific_settings_changed':False,'synthetic_fixture':False,
  'successes':successes,'per_task':per_task,'paired_outcomes':{str(k):v for k,v in pairs.items()},'B_minus_A_success_rate':(successes['B128_seed41']-successes['A128_seed41'])/100,
  'raw_policy_calls':chunks_count,'executed_control_steps':controls,'finite_environment_action_max_abs':max_abs,'chunks_with_environment_abs_above_1':over_bound,
  'no_action_clipping_introduced':True,'executed_actions_exactly_match_chunk_prefixes':True,'future_head_calls':0,'deployment_runtime_structure':structural,
  'initial_observation_token_overlap_mean':float(np.mean(overlaps)),'token_overlap_scope':'only100 identical paired initial observations; not same later states and not a replacement for full diagnostics',
  'declared_current_GPU_seconds_pending_pull_accounting':3466,'nested_execution_wall_seconds':complete['wall_seconds'],'cost_counts_allocation_once':True,
  'test_opened':False,'final_release':False,'weights_loaded':False,'state_modified':False,'P_modified':False,
  'read_files':seen}
 rr=save('direct_raw_audit_a1.json',result);print(json.dumps({'receipt':rr,'successes':successes,'pairs':result['paired_outcomes'],'policy_calls':chunks_count,'files':len(seen)}))
if __name__=='__main__':main()
