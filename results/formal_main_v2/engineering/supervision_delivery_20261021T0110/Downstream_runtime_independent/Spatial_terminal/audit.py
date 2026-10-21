from pathlib import Path
import json,hashlib,importlib.util,sys,collections,math,traceback,datetime,subprocess
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/downstream_runtime_independent_20261021T0110/Spatial_terminal';B='results/formal_main_v2/preflight/heartbeat_20261021T0910'
checks=[]
def need(v,m):
 if not v:raise AssertionError(m)
 checks.append(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel,pin):
 p=R/rel;need(sha(p)==pin,'sha '+rel);return json.loads(p.read_text())
def load(rel,pin,name):
 p=R/rel;need(sha(p)==pin,'source '+rel);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def save(name,j):
 p=D/name
 with p.open('x') as f:json.dump(j,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size}
def main():
 start=sha(R/'results/experiment_supervisor/state.json')
 final=read(B+'/Spatial3054201_terminal_v2/completion.json','d071b418ab0f188acabc2fbb5ce8ab0aae66e8c4ab0550e8f5a0c60a6404c3cb')
 root=read('results/formal_main_v2/downstream_reviews/3054201.json','c4452ea92281151bf485f41777257392edf008e48f6268c78be9cfc17f115b92')
 obs=read(B+'/terminal_observation_from_Object_preflight.json','89820eb12808cce09c4882c7ce17d189b44b8e01c460299663a32fd0c64e3c94')['observation']
 c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','_spatial_ind_controller')
 parsed=c.parse_sacct(obs['raw_sacct'],set(obs['rows']));need(parsed==obs['rows'],'all saved301 accounting reparsed')
 current=parsed['3054201'];need(current['status']=='COMPLETED' and current['exit_code']=='0:0' and current['gpus']==1 and current['elapsed_seconds']==6635,'real target clean6635GPU seconds')
 jobs=root['registered_jobs_at_review'];by={str(j['job_id']):j for j in jobs};need(len(by)==len(jobs),'unique terminal register')
 literal={r.split('|')[0]:r.split('|')[1] for r in obs['raw_sacct'].splitlines() if r}
 for jid,seconds,status,exitcode in [('3022743',393,'COMPLETED','0:0'),('3042529',2,'FAILED','1:0'),('3054201',6635,'COMPLETED','0:0')]:
  need(by[jid]['raw_status']==literal[jid] and c.state_name(literal[jid])==status and parsed[jid]['status']==status and parsed[jid]['exit_code']==exitcode and parsed[jid]['elapsed_seconds']==seconds,'literal original allocation '+jid)
 pull=read(root['pull_ref']['path'],'ca9d4e64b02abde022ecb6ac83c4653be0c0882485bd0f73478f69570f3e8a60')
 need(pull['final_evidence'] and pull['requested_job_ids']==['3054201'] and not pull['weights_copied'] and not pull['sealed_initial_states_copied'],'exact final nonweight pull')
 for row in pull['files']:
  rel=row['relative'];need(not Path(rel).is_absolute() and '..' not in Path(rel).parts,'safe pull relative')
  for base in (R,P):need(sha(base/rel)==row['sha256'] and (base/rel).stat().st_size==row['bytes'],'actual R/P raw mirror '+rel)
 rr=load('scripts/ops/formal_action_deployment_v1/reviewer.py','9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','_spatial_ind_rawreview')
 control=load('scripts/ops/formal_spatial588_predispatch_v1/control.py','e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683','_spatial_ind_typedcontrol')
 ev=rr.Evidence(R);consumer=control.consumer_module(ev)
 rebuilt=consumer.review_downstream_output(ev,final['root_review'],expected_stage='development',suite='libero_spatial',run_root=root['run_root'],require_complete=True)
 clean=lambda v:{k:x for k,x in v.items() if k!='reviewed_utc'}
 need(clean(rebuilt)==clean(root),'independent original typed consumer fully reconstructs root result');ev.unchanged()
 run='results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01';ledger=R/run/'trials.jsonl';raw=ledger.read_bytes()
 need(hashlib.sha256(raw).hexdigest()=='75e58983b797bf11bbaeb0788a19c05ce90c4f34c804ed0978f5015801da7204','actual ledger bytes')
 need(hashlib.sha256(raw[:592887]).hexdigest()=='3a175dbc5dd7a23cd2c3c8385cb6ff3c525f09d4e607ff32a69a10869672a2f9','original592887-byte12prefix unchanged')
 rows=[json.loads(x) for x in raw.splitlines()];need(collections.Counter(x['event'] for x in rows)=={'invocation':2,'start':600,'result':600},'exact ledger event counts')
 byjob=collections.Counter();starts={};results=[];identity=('trial_id','state_trial_id','method','task_id','task_name','source_state_index','initial_state_sha256','run_signature','runtime_seed','environment_seed','action_chunk','configured_wait_steps','split','suite')
 invocation=None;inv=[];lineage=[]
 for row in rows:
  if row['event']=='invocation':
   need(not starts,'no unfinished trial at invocation boundary');invocation=row['slurm_job_id'];inv.append(invocation);continue
  tid=row['trial_id']
  if row['event']=='start':need(tid not in starts and not any(x['trial_id']==tid for x in results),'no duplicated trial start');starts[tid]=row;continue
  need(tid in starts,'result has start');s=starts.pop(tid)
  need(all(row[k]==s[k] for k in identity),'start/result exact identity '+tid)
  need(row['runtime_seed']==17 and row['environment_seed']==0 and row['action_chunk']==8 and row['wait_steps']==row['configured_wait_steps']==10 and row['split']=='development' and row['suite']=='libero_spatial','fixed scientific settings '+tid)
  need(row['status']=='completed' and type(row['success'])is bool and row['termination'] in ('environment_success','task_horizon') and row['success']==(row['termination']=='environment_success'),'all ordinary negative outcomes retained '+tid)
  chunks=row['chunks'];actions=np.array(row['executed_actions'],dtype=np.float64)
  need(actions.shape==(row['control_steps'],7) and np.isfinite(actions).all(),'finite executed action shape '+tid)
  need(len(chunks)==row['policy_calls']==math.ceil(row['control_steps']/8),'query cadence '+tid)
  envchunks=[]
  for qi,ch in enumerate(chunks):
   env=np.array(ch['environment_actions'],dtype=np.float64);norm=np.array(ch['normalized_actions'],dtype=np.float64)
   need(ch['control_step']==8*qi and env.shape==norm.shape==(8,7) and np.isfinite(env).all() and np.isfinite(norm).all(),'finite unchanged chunk '+tid+' q'+str(qi));envchunks.append(env)
  need(np.array_equal(np.concatenate(envchunks,axis=0)[:len(actions)],actions),'executed actions equal original chunk slices '+tid)
  need(row['success'] or row['control_steps']==300,'ordinary horizon retained '+tid)
  results.append(row);byjob[invocation]+=1;lineage.append(dict(trial_id=tid,job_id=invocation,method=row['method'],task_id=row['task_id'],success=row['success'],control_steps=row['control_steps'],policy_calls=row['policy_calls']))
 need(not starts and inv==['3022743','3054201'] and dict(byjob)=={'3022743':12,'3054201':588},'separate executed/allocation histories no fabricated3042529 invocation')
 methods=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'];need({r['method'] for r in results}==set(methods),'six original methods')
 summary={}
 for method in methods:
  part=[r for r in results if r['method']==method];need(len(part)==100 and len({r['state_trial_id'] for r in part})==100,'100states per method '+method)
  per={str(t):{'trials':sum(r['task_id']==t for r in part),'successes':sum(r['success'] for r in part if r['task_id']==t)} for t in range(10)}
  need(all(v['trials']==10 for v in per.values()),'ten per task '+method)
  summary[method]={'trials':100,'successes':sum(r['success'] for r in part),'per_task':per}
  need(summary[method]['successes']==root['reconstructed_summary']['methods'][method]['successes'],'root method count '+method)
 states={r['state_trial_id'] for r in results};need(len(states)==100,'original100unique states')
 for st in states:
  part=[r for r in results if r['state_trial_id']==st];need(len(part)==6 and len({r['initial_state_sha256'] for r in part})==1,'paired state identities '+st)
 cost=root['cost'];need(cost['all_attempt_gpu_seconds']==7030 and cost['current_gpu_seconds']==6635 and [r['job_id'] for r in cost['allocations']]==['3022743','3042529','3054201'],'all allocations exactly once')
 need(root['final_release']is False and root['final_state_values_read']is False and root['execution_lineage']['eligible_for_current_action_global_freeze']is False,'global final/profiling not inferred')
 need((R/(B+'/Spatial3054201_terminal/failure.json')).is_file(),'first root metadata failure retained')
 invj=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text());need(len(invj['files'])==173,'173inventory')
 for rel,pin in invj['files'].items():
  for base in (R,Path(invj['source_root_server'])):need(sha(base/rel)==pin,'frozen173 '+str(base/rel))
 rawsum=save('raw_trial_lineage_and_counts.json',{'summary':summary,'lineage':lineage,'raw_sha256':sha(ledger),'executed_job_counts':dict(byjob),'negative_task_outcomes':sum(not r['success'] for r in results),'total_policy_calls':sum(r['policy_calls'] for r in results),'total_control_steps':sum(r['control_steps'] for r in results)})
 report=dict(schema='formal_main_v2',kind='Spatial588_real_terminal_independent_review',status='passed_real_raw_terminal_review',reviewed_by='independent',blockers=[],job_id='3054201',root_review=final['root_review'],root_completion_sha256='d071b418ab0f188acabc2fbb5ce8ab0aae66e8c4ab0550e8f5a0c60a6404c3cb',terminal_observation_sha256='89820eb12808cce09c4882c7ce17d189b44b8e01c460299663a32fd0c64e3c94',
 original_typed_consumer_rebuilt=True,original_legacy_prefix_preserved=True,completed_trials=600,legacy_compatible_trials=12,current_wrapper_trials=588,newly_executed_trials=588,unique_initial_states=100,methods=summary,cost=cost,
 source173_verified=True,actual_R_P_nonweight_hashes_verified=True,raw_lineage=rawsum,checks=checks,check_count=len(checks),scientific_trials_added_by_auditor=0,state_written=False,Slurm_queries=0,new_GPU_jobs=[],final_release=False,final_sealed=True,profiling_authorized=False,eligible_for_current_action_global_freeze=False,state_sha256_before=start,state_sha256_after=sha(R/'results/experiment_supervisor/state.json'),
 helper_v2_static_review=dict(entrypoint_sha256='1bacc36841b7f42a374436146deda321c65cc08807dbdd0aa1e5cd41cc5ceb6b',scope='Only literal raw_status from unchanged savedraw, exact prior verified pull reuse and new evidence directory; original guards unchanged'),
 acceptance_scope='Exactly original600 Spatial development, typed12legacy compatible+588current. Retain393+2+6635 cost. Root may count588 newly executed only; no final release/profile inference.')
 print(json.dumps(save('independent_review.json',report),sort_keys=True))
try:main()
except BaseException as e:
 save('failure.json',dict(type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks=checks,new_GPU_jobs=[],state_written=False));raise
