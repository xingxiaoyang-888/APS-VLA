from pathlib import Path
import json,hashlib,sys,traceback,ast
from datetime import datetime,timezone
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
O=R/'.local/object_single_error_independent_20261020T2358'
X='results/formal_main_v2/execution/object_single_error_v1'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T2253/Object599_independent'
A='results/formal_main_v2/engineering/supervision_delivery_20261020T2156/Object_author'
RUN='results/formal_main_v2/libero_object/downstream/development/8c843c1d4ee8383c/attempt01'
CELL='libero_object:pick_up_the_chocolate_pudding_and_place_it_in_the_basket:state-0049:env-0:dense'
ACTION='9a5f5935100bb04bf8fb91f6405b94efc93de236b3a75896d0f08cdb2aa1ee02'
SHA=lambda b:hashlib.sha256(b).hexdigest()
checks=[];watched={}
def ck(b,name,details=None):
 if not b: raise AssertionError(name)
 checks.append({'name':name,**({'details':details} if details is not None else {})})
def read(rel,want=None):
 p=R/rel
 ck(p.resolve()==p and p.is_file(),'resolved_regular:'+rel)
 s1=p.stat();b=p.read_bytes();s2=p.stat();ck((s1.st_size,s1.st_mtime_ns,s1.st_ino)==(s2.st_size,s2.st_mtime_ns,s2.st_ino),'stable:'+rel)
 if want:ck(SHA(b)==want,'pin:'+rel)
 watched[rel]={'path':rel,'sha256':SHA(b),'bytes':len(b)}
 return b
def j(rel,want=None):return json.loads(read(rel,want))
def publish(name,x):
 raw=(json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode()
 with (O/name).open('xb') as f:f.write(raw)
 return {'path':(O/name).relative_to(R).as_posix(),'bytes':len(raw),'sha256':SHA(raw)}
def io(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('No subprocess/network')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes)) and ((mode and any(v in mode for v in 'wax+')) or (isinstance(flags,int) and flags & (1|2|64|512|1024))):
   if not Path(path).resolve().is_relative_to(O):raise RuntimeError('Write outside independent private directory')
 if event in ('os.remove','os.rename','os.mkdir','os.rmdir','os.chmod','os.symlink','os.link'):
  for value in args[:2 if event in ('os.rename','os.link') else 1]:
   if isinstance(value,(str,bytes)) and not Path(value).resolve().is_relative_to(O):raise RuntimeError('Mutation outside independent private directory')
sys.addaudithook(io)
try:
 review=j('.local/object_single_error_independent_20261020T2358/independent_review.json','7aefd070fe5e437c7e8c0636db7301efeb9bd5cb0484665921b70aad5d6c6481')
 helper=read('.local/adopt_object599_20261020T2358_v2.py','d75bb2764916a7806ce8b222d878a568cb865409251d3b2134977b9134ccf2f4')
 tree=ast.parse(helper);ck(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('system','Popen','run','submit','cancel') for n in ast.walk(tree)),'root_helper_no_scheduler_or_subprocess_calls')
 ck(b"with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock')" in helper and b"assert h(sp)==state_before" in helper,'root_helper_shared_lock_and_readonly_state_assertions')
 adoption=j(X+'/root_legacy_adoption.json','c431646cbac00f461177e95361fb8d31d66c78bcfbbfc2b5c766edb8eabd6d24')
 rb=read(X+'/legacy599_adoption_rows.jsonl','ac792e8d88f251f097f3f0e110e6c32aa45dbacd103404c0189b3bebf56ccb5e');rows=[json.loads(x) for x in rb.splitlines()]
 record=j('results/formal_main_v2/preflight/heartbeat_20261021T0758/Object599_root_evidence_review.json','296853f0f3c61b07dd0e222c419472e96bab52df9c8f0b02d80c80d7b316e84d')
 ck(adoption['status']=='passed_legacy599_only' and adoption['reviewed_by']=='root','root_599_only_role_status')
 ck(adoption['legacy_equivalent_trials']==599 and adoption['raw_historical_trials']==600 and adoption['retained_policy_errors']==1,'typed_599_600_counts')
 for key in ('whole600_admitted','GPU_execution_authorized','final_release','final_allowed'):
  ck(adoption[key] is False,'not_admitted:'+key)
 for key in ('new_scientific_trials','new_GPU_seconds','current_wrapper_generated_trials'):
  ck(adoption[key]==0,'zero:'+key)
 ck(adoption['typed_whole600_consumer_pending'] is True and adoption['rejected_query8_unknown'] is True,'remaining_consumer_and_unknown_query8')
 ck(adoption['legacy_gpu_seconds']==6713 and record['all_original_GPU_seconds']==6713,'old_cost_once_6713')
 ck(adoption['actual_old_controller_instance_capture'] is False,'source_history_not_capture')
 ck(len(rows)==599 and len(rb)==521380 and rb.endswith(b'\n'),'exact599complete_rows')
 for rel,want in ((E+'/delivery_manifest_original.json','08dd6ededfa12ba7827784cb0809db0c57128ffc880df831a977e558bded10f3'),(A+'/stage1_delivery_manifest_original.json','9020eb66c1746924379106baf19cd5d50318bf4283370b900785acba596c1992')):
  m=j(rel,want);prefix=Path(rel).parent.as_posix();source=m.get('root','.local/object_legacy_integration_20261020T2156')
  paths=[]
  for v in m['files']:
   q=prefix+'/'+Path(v['path']).relative_to(source).as_posix();b=read(q,v['sha256']);ck(len(b)==v['bytes'],'archive_size:'+q);paths.append(q)
  ck(len(paths)==len(set(paths))==({'17':17,'39':39}.get(str(len(paths)),0)),'exact_archive_cardinality:'+prefix)
 proof=j(E+'/independent_review.json','62c0a39784953b14f061ae7d161813f5e4bbfa5c8db39297e7047327b28463f7')
 proofs=[json.loads(x) for x in read(E+'/per_trial_independent_599.jsonl','ddba2cf9b392fd49e445d8a264605bc0832de5196c0c39d3a7c950160d186155').splitlines()]
 byproof={x['trial_id']:x for x in proofs};ck(len(byproof)==599,'unique599_priorproof')
 manifest=j('results/formal_main_v2/execution/libero_object_development_first_pair_v1.json','34062573869c7b947fbd3c37b09da476bec673e8e16fc4ea49c6ce8c5932db5a')
 config=j(RUN+'/config.json','ccbb680ade2c6cab783568ea34f2fd3d3ae9abb69a62e7088f53d7150dad27a5')
 panel=j(RUN+'/panel.json','6b7e6dd9fb5b6351ee47c7bb30eab911e7c144d700cd88f7e5162641738b2d6a')
 methods=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
 ck([x['identity']['method_id'] for x in manifest['methods']]==methods and config['manifest']==manifest and len(panel['states'])==100,'full100x6_original_manifest')
 expected={s['trial_id']+':'+method:(s,method) for s in panel['states'] for method in methods};ck(len(expected)==600,'unique600_frozen_cells')
 raw=read(RUN+'/trials.jsonl','d93ad5a4eb4ae3edb7a9b20e640a72fe4971ca0e4eeb62eea71acc4d71a257d1')
 for rel in (RUN+'/trials.jsonl',RUN+'/config.json',RUN+'/panel.json'):
  ck(SHA((P/rel).read_bytes())==watched[rel]['sha256'],'actualP_originalbytes:'+rel)
 lines=raw.splitlines(keepends=True);offsets=[];at=0;starts={};results={};jobs=[];jobfor={}
 for i,line in enumerate(lines):
  offsets.append(at);at+=len(line);v=json.loads(line)
  if v['event']=='invocation':jobs.append(v['slurm_job_id']);current=v['slurm_job_id']
  elif v['event']=='start':ck(v['trial_id'] not in starts,'unique_start:'+v['trial_id']);starts[v['trial_id']]=v
  elif v['event']=='result':ck(v['trial_id'] not in results and v['trial_id'] in starts,'unique_started_result:'+v['trial_id']);results[v['trial_id']]=v;jobfor[v['trial_id']]=current
  else:raise AssertionError('Unexpected original event')
 ck(set(results)==set(starts)==set(expected),'all600_original_pairing')
 ck(jobs==['3021394','3021603','3021844'],'exact_original_invocations')
 ck(len({v['trial_id'] for v in rows})==599 and {v['trial_id'] for v in rows}==set(expected)-{CELL},'exact599_original_results_only')
 counts={'trials':0,'chunks':0,'actions':0};success=0;summary=[]
 for entry in rows:
  tid=entry['trial_id'];p=byproof[tid];s,method=expected[tid];r=results[tid]
  ck(r['status']=='completed' and type(r['success']) is bool and r['method']==method,'completed_original_cell:'+tid)
  for what in ('start','result'):
   loc=entry[what];i=loc['line']-1
   ck(loc==p[what] and offsets[i]==loc['byte_offset'] and len(lines[i])==loc['bytes'] and SHA(lines[i])==loc['sha256'],'exact_source_line:'+tid+':'+what)
   item=json.loads(lines[i]);ck(item['event']==what and item['trial_id']==tid,'source_event:'+tid+':'+what)
  actions=np.asarray(r['executed_actions'],dtype='<f8');ck(actions.shape==(r['control_steps'],7) and np.isfinite(actions).all(),'finite_action_shape:'+tid)
  pieces=[]
  for k,chunk in enumerate(r['chunks']):
   a=np.asarray(chunk['environment_actions'],dtype='<f8')
   ck(a.shape==(8,7) and np.isfinite(a).all() and chunk['control_step']==8*k,'chunk_queue_shape_order:'+tid+':'+str(k))
   ck(np.clip(a,-1.,1.).tobytes()==a.tobytes(),'controller_clip_bytes_unchanged:'+tid+':'+str(k))
   pieces.append(a)
  queue=np.concatenate(pieces,axis=0);ck(queue[:len(actions)].tobytes()==actions.tobytes() and len(queue)-len(actions)<8,'actual_executed_prefix_exact:'+tid)
  digest=SHA(actions.tobytes())
  ck(digest==p['old_runtime_replay']['executed_f64le_sha256']==p['current_runtime_replay']['executed_f64le_sha256'],'old_current_executed_digest:'+tid)
  canonical=dict(trial_id=tid,start=p['start'],result=p['result'],source_job_id=jobfor[tid],initial_state_sha256=s['initial_state_sha256'],old_executed_f64le_sha256=digest,current_executed_f64le_sha256=digest,target_action_semantics_sha256=ACTION,origin='legacy_equivalent',method=method,success=r['success'],status='completed')
  ck(entry==canonical,'canonical599_reference_row_exact:'+tid)
  ck(r['initial_state_sha256']==s['initial_state_sha256'] and r['environment_seed']==0 and r['runtime_seed']==17 and r['wait_steps']==r['configured_wait_steps']==10 and r['action_chunk']==8,'identity_environment_reset:'+tid)
  counts['trials']+=1;counts['chunks']+=len(r['chunks']);counts['actions']+=len(actions);success+=int(r['success'])
  summary.append({'trial_id':tid,'executed_f64le_sha256':digest,'chunks':len(r['chunks']),'actions':len(actions),'success':r['success']})
 ck(counts==adoption['counts']==proof['counts']=={'trials':599,'chunks':11720,'actions':91945},'all599_totals')
 ck(success==adoption['root_rechecked_success_count']==520,'all599_success520_negative79_preserved')
 failed=results[CELL];ck(failed['status']=='policy_error' and failed['success'] is False and failed['policy_calls']==8 and len(failed['chunks'])==7 and len(failed['executed_actions'])==56,'original_failure_unchanged_no_query8_invention')
 alloc=adoption['legacy_allocations'];ck([(x['job_id'],x['elapsed_seconds'],x['gpus'],x['status'],x['exit_code']) for x in alloc]==[('3021394',386,1,'COMPLETED','0:0'),('3021603',1401,1,'COMPLETED','0:0'),('3021844',4926,1,'COMPLETED','0:0')],'all_original_allocations_once')
 ck(len({x['job_id'] for x in alloc})==3 and sum(x['elapsed_seconds']*x['gpus'] for x in alloc)==6713,'unique_cost_without_rebilling')
 for k in ('legacy_independent_review','legacy_independent_per_trial','author_compatibility_proof','legacy_raw','original_root_review','original_manifest','original_panel','original_config'):
  v=adoption[k];b=read(v['path'],v['sha256']);ck(len(b)==v['bytes'],'canonical_bound_ref:'+k)
 ck(adoption['rows']==adoption['legacy599_adoption_rows']==record['rows'],'same_canonical599_ref')
 ck(record['adoption']==watched[X+'/root_legacy_adoption.json'],'root_evidence_exact_adoption_ref')
 inv=j('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 ck(len(inv['files'])==173,'173_inventory_count')
 for rel,want in inv['files'].items():
  for base in (R,P/'snapshots/formal_main_v2_run_564be0995e',R/'snapshots/formal_main_v2_run_564be0995e'):
   ck(SHA((base/rel).read_bytes())==want,'173_source_bytes:'+str(base/rel))
 for rel,v in watched.items():ck(SHA((R/rel).read_bytes())==v['sha256'],'final_input_stability:'+rel)
 per=publish('canonical599_independent_rows.json',summary)
 report={'schema':'formal_main_v2','kind':'Object599_canonical_root_adoption_independent_review','status':'passed_legacy599_only','reviewed_by':'independent_goal_cpu_gate_2054','utc':datetime.now(timezone.utc).isoformat(),'root_adoption':watched[X+'/root_legacy_adoption.json'],'adoption_rows':watched[X+'/legacy599_adoption_rows.jsonl'],'root_helper':watched['.local/adopt_object599_20261020T2358_v2.py'],'root_evidence':watched['results/formal_main_v2/preflight/heartbeat_20261021T0758/Object599_root_evidence_review.json'],'counts':counts,'successes':success,'negative_outcomes':599-success,'original_trials_retained':600,'original_policy_error_retained':1,'unknown_query8_not_invented':True,'original_GPU_allocations':alloc,'original_GPU_seconds_once':6713,'new_GPU_seconds':0,'new_GPU_submissions':0,'new_scientific_trials':0,'Slurm_queries':0,'whole600_admitted':False,'production_admitted':False,'final_release':False,'checked_canonical_adoption_reference_view_only':True,'independent_action_queue_and_controller_clip_byte_reconstruction':True,'full_runtime_replay_inherited_not_repeated':True,'frozen173_three_roots_verified':True,'all599_exact_raw_start_result_and_executed_byte_links_verified':True,'source_archive_files_verified':{'author':17,'independent':39},'state_canonical_P_Git_writes':0,'audit_checks_passed':len(checks),'per_trial_reconstruction':per,'checks':checks,'inputs':list(watched.values()),'CPU_candidate_blocker_update':{'B5_root_adoption_single_authorization':'Root canonical legacy599-only adoption is now verified; exact one-cell full-reset production chain, current-source/actual-P readiness, one root submission authorization and actual terminal consumers remain separate required gates. Frozen CPU report records its pre-adoption scope and is not rewritten.'},'remaining_gate_ids':['B1_native_transaction','B2_full_execution_closure','B3_distinct_derived_provenance','B4_actual_terminal_consumer','B5_single_authorization_and_terminal_release']}
 ref=publish('canonical599_adoption_addendum.json',report);print(json.dumps({'status':report['status'],'checks':len(checks),'report':ref,'production_admitted':False}))
except BaseException as exc:
 ref=publish('canonical599_audit_v1_failure.json',{'error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc(),'passed_checks':checks,'utc':datetime.now(timezone.utc).isoformat()});print(json.dumps(ref));raise
