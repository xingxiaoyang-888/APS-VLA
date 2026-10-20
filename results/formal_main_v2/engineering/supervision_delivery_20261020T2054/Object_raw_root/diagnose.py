"""Exact Object legacy raw-evidence diagnosis, no result adoption or execution."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,math,os,struct,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/object599_diagnostic_20261020T2054'
RUN='results/formal_main_v2/libero_object/downstream/development/8c843c1d4ee8383c/attempt01'
LEDGER=RUN+'/trials.jsonl';LEDGER_SHA='d93ad5a4eb4ae3edb7a9b20e640a72fe4971ca0e4eeb62eea71acc4d71a257d1'
RUNTIME='src/cti_vla/evaluation/libero_runtime.py';RUNTIME_SHA='2fc1bacbd1268a36f2e31451c70a650be4f8d0c8f6803e7c8b2a3d45f701c781'
ADAPTER='results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py';ADAPTER_SHA='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185'
METHODS=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
EX='libero_object:pick_up_the_chocolate_pudding_and_place_it_in_the_basket:state-0049:env-0:dense'
WATCH={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(rel,pin=None):
 p=R/rel;need(p.resolve()==p,'noncanonical input');b=p.read_bytes();h=sha(b);need(pin is None or h==pin,'source changed '+rel);WATCH[rel]=h;return b
def duplicate_pairs(items):
 d={}
 for k,v in items:need(k not in d,'duplicate JSON key');d[k]=v
 return d
def bad_constant(s):raise ValueError('nonfinite JSON '+s)
def decode(b):return json.loads(b,object_pairs_hook=duplicate_pairs,parse_constant=bad_constant)
def packed(m):
 need(type(m) is list,'array must be list');a=[]
 for r in m:
  need(type(r) is list and len(r)==7,'action dimension')
  for v in r:need(type(v) in (int,float) and math.isfinite(v),'nonfinite action');a.append(float(v))
 return struct.pack('<'+'d'*len(a),*a)
def save(name,data):
 p=D/name;b=json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n'
 with p.open('xb') as f:f.write(b)
 return {'path':str(p.relative_to(R)),'sha256':sha(b)}
def main():
 need(os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R),'server transport required')
 before=time.perf_counter();raw=read(LEDGER,LEDGER_SHA);need(sha((P/LEDGER).read_bytes())==LEDGER_SHA,'P and R raw ledger differ')
 src=read(RUNTIME,RUNTIME_SHA);adapter=read(ADAPTER,ADAPTER_SHA)
 branch=ast.parse('if bool((np.abs(chunk.environment_actions) > 1.00001).any()):\n    raise ValueError("environment action outside normalized controller [-1, 1] range")').body[0]
 tree=ast.parse(src);runtime_fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_episode')
 matches=[n for n in ast.walk(runtime_fn) if isinstance(n,ast.If) and ast.dump(n,include_attributes=False)==ast.dump(branch,include_attributes=False)]
 need(len(matches)==1,'frozen failure branch not unique')
 need(src.count(b'environment action outside normalized controller [-1, 1] range')==1,'failure message not unique')
 need(b'if bool((np.abs(chunk.environment_actions) > 1.00001).any()):' in adapter,'target action adapter does not bind exact old branch')
 root=decode(read('results/formal_main_v2/downstream_reviews/3021844.json'))
 need(root['status']=='passed' and root['scientific_complete'] is True and root['job_id']=='3021844','genuine legacy600 root missing')
 costs=root['cost']['allocations'];need([x['job_id'] for x in costs]==['3021394','3021603','3021844'] and sum(x['gpus']*x['elapsed_seconds'] for x in costs)==6713,'historical allocation cost changed')
 events=Counter();statistics=defaultdict(Counter);states=defaultdict(list);trials=set();records=[];exceptions=[];invocations=[];current=None;pending=None;offset=0
 for n,b in enumerate(raw.splitlines(keepends=True),1):
  need(b.endswith(b'\n'),'unfinished raw ledger line');r=decode(b);event=r['event'];events[event]+=1
  identity={k:r.get(k) for k in ['trial_id','state_trial_id','method','task_id','task_name','source_state_index','initial_state_sha256']}
  ref={'line':n,'byte_offset':offset,'bytes':len(b),'sha256':sha(b)};offset+=len(b)
  if event=='invocation':
   need(pending is None,'invocation during an incomplete trial');current=r['slurm_job_id'];invocations.append(current);continue
  need(current in ['3021394','3021603','3021844'],'unknown allocation')
  need(r['suite']=='libero_object' and r['split']=='development' and r['method'] in METHODS and r['runtime_seed']==17 and r['environment_seed']==0 and r['configured_wait_steps']==10 and r['action_chunk']==8,'original trial configuration changed')
  if event=='start':need(pending is None,'nested trial start');pending=(identity,ref);continue
  need(event=='result' and pending is not None and pending[0]==identity,'unmatched result');startref=pending[1];pending=None
  need(r['trial_id'] not in trials,'duplicate completed trial');trials.add(r['trial_id'])
  chunks=r['chunks'];executed=r['executed_actions'];queue=[];maximum=0.0
  for ci,ch in enumerate(chunks):
   need(ch['control_step']==ci*8 and len(ch['environment_actions'])==8 and len(ch['normalized_actions'])==8,'chunk boundary/shape')
   packed(ch['normalized_actions']);packed(ch['environment_actions'])
   for row in ch['environment_actions']:
    for value in row:need(abs(value)<=1.00001,'retained chunk exceeded old threshold');maximum=max(maximum,abs(value))
   queue.extend(ch['environment_actions'])
  need(len(executed)==r['control_steps'] and packed(queue[:len(executed)])==packed(executed),'recorded queue prefix differs')
  clipped=[[min(1.0,max(-1.0,float(v))) for v in row] for row in queue]
  need(packed(clipped)==packed(queue),'existing controller clipping would change a retained chunk')
  need(len(chunks)>0 and r['wait_steps']==10,'missing t0/wait')
  states[r['state_trial_id']].append({'method':r['method'],'initial_state_sha256':r['initial_state_sha256'],'t0_hash':chunks[0]['observation_sha256'],'task_id':r['task_id']})
  record={**identity,'original_job_id':current,'start':startref,'result':ref,'status':r['status'],'success':r['success'],'chunks':len(chunks),'recorded_actions':len(executed),'executed_float64le_sha256':sha(packed(executed)),'retained_chunks_float64le_sha256':sha(packed(queue)),'retained_chunks_max_abs':maximum,'original_queue_exact':True,'existing_controller_clip_byte_inactive':True,'candidate_only':True,'adopted':False}
  if r['status']=='completed':
   need(r['policy_calls']==len(chunks),'completed trial call count differs');need(r['termination'] in ('environment_success','task_horizon'),'unexpected termination');records.append(record)
   statistics[r['method']].update(completed=1,successes=int(r['success']),chunks=len(chunks),actions=len(executed))
  else:
   need(n==1073 and r['trial_id']==EX and r['status']=='policy_error' and r['error']=='environment action outside normalized controller [-1, 1] range' and r['error_phase']=='policy' and r['control_steps']==56 and r['policy_calls']==8 and len(chunks)==7 and r['success'] is False,'not the unique known invalid attempt')
   exceptions.append({**record,'error':r['error'],'recorded_policy_calls':8,'retained_policy_chunks':7,'rejected_eighth_chunk_recorded':False,'exact_offending_axis_value_recoverable':False,'new_semantics_outcome_unknown':True})
 need(pending is None and invocations==['3021394','3021603','3021844'],'incomplete invocation history')
 need(events==Counter(invocation=3,start=600,result=600) and len(records)==599 and len(exceptions)==1 and len(states)==100,'full ledger coverage')
 for state,rows in states.items():
  need(len(rows)==6 and {x['method'] for x in rows}==set(METHODS),'missing original method/state')
  need(len({x['initial_state_sha256'] for x in rows})==1 and len({x['t0_hash'] for x in rows})==1,'paired initial state or recorded t0 mismatch')
 need(Counter(v[0]['task_id'] for v in states.values())==Counter({i:10 for i in range(10)}),'original task panel differs')
 detail=save('per_trial_raw_audit.json',{'records_completed_candidates':records,'invalid_attempts_preserved':exceptions,'raw_ledger':{'path':LEDGER,'sha256':LEDGER_SHA},'production_reuse_authorized':False})
 report={'schema':'formal_main_v2','kind':'root_bounded_Object_legacy_raw_diagnostic','status':'raw_boundary_audited_not_compatibility_admitted','suite':'libero_object','original_results':600,'completed_raw_candidates':599,'policy_error_attempts_preserved':1,'unique_initial_states':100,'recorded_t0_mismatches':0,'retained_chunks':sum(x['chunks'] for x in records+exceptions),'retained_actions':sum(x['recorded_actions'] for x in records+exceptions),'per_method_completed_only':{k:dict(v) for k,v in statistics.items()},'exception':exceptions[0],'per_trial':detail,'all_original_allocation_GPU_seconds':6713,'all_original_allocations':costs,'new_GPU_seconds':0,'new_scientific_trials':0,'accepted_scientific_trials_added':0,'evidence_sha256':WATCH,'source_finding':'The unique legacy range guard raises before appending query8 to chunks; the receipt binds its message and phase. All retained chunks are finite/in-range and existing controller clipping leaves their float64 bytes unchanged. The actual rejected chunk bytes and new-runtime outcome are absent, not inferred.','limits':['599 raw checks alone do not establish full historical model/controller identity or old/new runtime equivalence. Root and independent acceptance remain required.','No new inference, environment replay, compatibility adoption, selective success denominator or latency reuse.','The old600 raw ledger stays immutable, including its false policy-error result and all6713 GPU seconds.','A new exact exception lineage would need its own engineering-reviewed execution plan; ordinary --resume cannot rerun this ID because the old ledger marks policy_error terminal.'],'candidate_next_gate':['Independently establish genuine old whole-chain review and current target source/controller equivalence for exactly599 complete rows without outcome filtering.','Retain the one objectively different exception as invalid-under-target-semantics, never silently drop or relabel it; register any replacement as an explicitly linked same-state/method attempt.','Before any GPU replacement, require fixed target source/checkpoint/config identity, passive action tracing, duplicate protection and a complete paired development assembly with original100 states.'],'final_release':False,'production_reuse_authorized':False,'GPU_submission_authorized':False,'CPU_wall_seconds':time.perf_counter()-before}
 for rel,h in WATCH.items():need(sha((R/rel).read_bytes())==h,'evidence changed')
 out=save('diagnostic.json',report);print(json.dumps({'report':out,'completed_raw_candidates':599,'policy_error_preserved':1,'accepted_new_trials':0,'new_GPU_jobs':0}))
if __name__=='__main__':main()
