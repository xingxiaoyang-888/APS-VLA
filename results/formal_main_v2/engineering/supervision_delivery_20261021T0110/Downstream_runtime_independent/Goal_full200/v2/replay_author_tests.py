"""Bounded consumer-v2 rejection tests; all environment data here are explicit CPU fixtures."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys,traceback,types
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/goal_full200_author_20261021T0110_v2');R=D.parents[1];OLD=R/'.local/goal_full200_author_20261021T0110';K=D/'package'
O=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/downstream_runtime_independent_20261021T0110/Goal_full200/v2/CPU_replay');O.mkdir(exist_ok=False);checks=[];rejections=0;positive=0
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def ck(n,v,detail=None):
 checks.append({'name':n,'passed':bool(v),'detail':detail})
 if not v:raise AssertionError(n)
def load(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def main():
 global rejections,positive
 manifest=json.loads((K/'package_manifest.json').read_bytes())
 ck('only_consumer_v2_source_delta',(D/'source_delta.json').is_file())
 for p,h in manifest['files'].items():ck('new_package/'+p,sha((K/Path(p).name).read_bytes())==h)
 original_manifest=json.loads((OLD/'package/package_manifest.json').read_bytes())
 ck('nine_runtime_sources_unchanged',len([p for p,h in manifest['files'].items() if h==original_manifest['files'][p]])==9)
 c=load(K/'consumer.py','goal200_v2_consumer_test')
 src=OLD/'CPU_full200_v3';fixture=O/'fixture_attempt';fixture.mkdir()
 shutil.copytree(src/'gated',fixture/'observer')
 rawrows=c.jsonl(src/'gated.jsonl');specification=json.loads((K/'specification.json').read_bytes())
 rawgate=c.jsonl(fixture/'observer/gate.jsonl');rawevents=c.jsonl(fixture/'observer/events.jsonl')
 tree=ast.parse((K/'consumer.py').read_text());original=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='reconstruct_gate')
 def derive(no_loader):
  node=copy.deepcopy(original);changes=[]
  for n in ast.walk(node):
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant):
    if n.args[1].value=='CPU fixture forbidden':
     changes.append('require synthetic_CPU_fixture + CPU_fixture_enabled=True')
     n.args[0]=ast.parse("gate[0]['CPU_fixture_enabled'] is True and gate[0]['runtime_context']=='synthetic_CPU_fixture'",mode='eval').body
    if no_loader and n.args[1].value=='complete original loader capture sequence':
     changes.append('CPU fixture has no model loader; explicitly require empty prefix')
     n.args[0]=ast.parse('prefix==[]',mode='eval').body
   if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='expected_schema':
    new=ast.literal_eval(n.value);new['agentview_image']=('uint8',[3,4,3],36);new['robot0_eye_in_hand_image']=('uint8',[3,4,3],36);n.value=ast.parse(repr(new),mode='eval').body
    changes.append('two CPU fixture image dimensions 3x4x3 rather than256x256x3')
  ck('exact_fixture_AST_changes_'+str(no_loader),len(changes)==(3 if no_loader else 2),changes);ast.fix_missing_locations(node)
  ns={**c.__dict__,'OUT':fixture.relative_to(R).as_posix(),'RAW':src/'gated/CPU_raw_observations'}
  readblob=types.FunctionType(c.read_blob.__code__,ns,c.read_blob.__name__,c.read_blob.__defaults__,c.read_blob.__closure__);readblob.__kwdefaults__=c.read_blob.__kwdefaults__
  cache={}
  def cached_blob(ref,*,observation,output_root,read_refs):
   key=(json.dumps(ref,sort_keys=True),observation,str(output_root))
   if key not in cache:
    refs={};raw=readblob(ref,observation=observation,output_root=output_root,read_refs=refs);cache[key]=(raw,refs)
   raw,refs=cache[key];read_refs.update(refs);return raw
  ns['read_blob']=cached_blob
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<explicit CPU consumer fixture>','exec'),ns)
  return ns,changes,sha(ast.dump(node,include_attributes=False).encode())
 ns,changes,derivedsha=derive(True);f=ns['reconstruct_gate']
 def call(rows=rawrows,events=rawevents,gate=rawgate,space=ns):
  prev=space['jsonl']
  def virtual(p):
   if Path(p)==fixture/'observer/events.jsonl':return events
   if Path(p)==fixture/'observer/gate.jsonl':return gate
   return prev(p)
  space['jsonl']=virtual
  try:return space['reconstruct_gate'](R,rows,specification=specification,job_id='CPU_FIXTURE')
  finally:space['jsonl']=prev
 proof=call();positive+=1
 ck('full200_CPU_raw_rebuild',all(proof[k]==v for k,v in {'trials':200,'queries':600,'control_steps':3400,'warmup_steps':2000,'paired_t0_checks':100,'complete_trial_end_witnesses':200}.items()))
 ck('every_phase_and_query_raw_reconstructed',proof['complete_observation_phase_raw_rebuilt'] and proof['all_query_content_rebuilt_from_before_and_after_raw'])
 def reject(name,fragment,rows=rawrows,events=rawevents,gate=rawgate,space=ns):
  global rejections
  try:call(rows,events,gate,space)
  except (ValueError,KeyError,IndexError,AssertionError) as e:
   rejections+=1;ck(name,fragment in str(e),{'error_type':type(e).__name__,'error':str(e)})
  else:ck(name,False,{'unexpected_acceptance':True})
 def event_change(phase,fn):
  events=list(rawevents);i=next(i for i,r in enumerate(events) if r.get('phase')==phase);events[i]=copy.deepcopy(events[i]);fn(events[i]);return events
 def gate_change(kind,fn,step=None):
  gate=list(rawgate);i=next(i for i,r in enumerate(gate) if r.get('event')==kind and (step is None or r.get('control_step')==step));gate[i]=copy.deepcopy(gate[i]);fn(gate[i]);return gate
 def row_change(fn):
  rows=list(rawrows);i=next(i for i,r in enumerate(rows) if r.get('event')=='result');rows[i]=copy.deepcopy(rows[i]);fn(rows[i]);return rows
 # Independently reported exact counterexample: both non-t0 step8 captures empty,
 # every other byte including stale observation SHA, gate and ledger unchanged.
 bad=list(rawevents);changed=[]
 for phase in ('query_before','query_after'):
  i=next(i for i,r in enumerate(bad) if r.get('phase')==phase and r.get('control_step')==8)
  bad[i]=copy.deepcopy(bad[i]);bad[i]['observation_arrays']={};changed.append(i)
 reject('independent_v1_non_t0_both_raw_arrays_empty','required observation phase',events=bad)
 blocker=R/'.local/downstream_runtime_independent_20261021T0110/Goal_full200/counterexample_v1/blocker.json'
 ck('independent_counterexample_pin',sha(blocker.read_bytes())=='371b76c3e4144b45bbc6a28a9e90e6f3d995808b0c400300abb158c6e7e5ba8a')
 write(O/'exact_counterexample_patch.json',{'input_events_sha256':sha((fixture/'observer/events.jsonl').read_bytes()),'changed_indices':changed,'change_only':'observation_arrays set to {} at first non-t0 before/after step8; all other records unchanged','independent_blocker_sha256':sha(blocker.read_bytes()),'old_consumer_v1_was_independently_confirmed_to_accept':True,'consumer_v2_rejected':True,'CPU_fixture':True})
 for phase in ['reset_after','set_init_before','set_init_after','wait_before','wait_after','t0_query_before','t0_query_after','query_before','query_after']:
  reject('empty_five_raw_'+phase,'required observation phase',events=event_change(phase,lambda e:e.update(observation_arrays={})))
  reject('missing_one_raw_'+phase,'required observation phase',events=event_change(phase,lambda e:e['observation_arrays'].pop('robot0_eef_pos')))
 reject('observation_and_missing_flag_conflict','required observation phase',events=event_change('query_before',lambda e:e.update(observation_missing='missing')))
 reject('stale_hash_without_observation','non-observation marker',events=event_change('reset_before',lambda e:e.update(observation_sha256='0'*64)))
 reject('unknown_phase','unknown capture phase',events=event_change('reset_after',lambda e:e.update(phase='unregistered_capture')))
 reject('wrong_dtype','exact actual five-component',events=event_change('query_before',lambda e:e['observation_arrays']['robot0_eef_pos'].update(dtype='float32')))
 reject('wrong_shape','exact actual five-component',events=event_change('query_before',lambda e:e['observation_arrays']['robot0_eef_pos'].update(shape=[1,3])))
 reject('forged_raw_component_SHA','array dtype/shape/byte',events=event_change('query_before',lambda e:e['observation_arrays']['robot0_eef_pos'].update(sha256='0'*64)))
 reject('forged_raw_aggregate','five-component aggregate',events=event_change('query_before',lambda e:e.update(observation_sha256='0'*64)))
 reject('missing_query_content_component','every query content rebuilt',gate=gate_change('query_integrity_passed',lambda e:e['content']['components'].pop('agentview_image'),8))
 reject('forged_query_content_component','every query content rebuilt',gate=gate_change('query_integrity_passed',lambda e:e['content']['components']['agentview_image'].update(sha256='0'*64),8))
 reject('empty_prepost_identity','query mapping and allfive',gate=gate_change('query_integrity_passed',lambda e:e.update(input_identity_before={},input_identity_after={}),8))
 def change_instruction(e):
  e['instruction_utf8_hex']='6368616e676564';e['content']['instruction_utf8_sha256']=sha(bytes.fromhex(e['instruction_utf8_hex']))
 reject('valid_but_changed_non_t0_instruction','original instruction unchanged',gate=gate_change('query_integrity_passed',change_instruction,8))
 reject('query_pointer_change','prepost exact mapping',gate=gate_change('query_integrity_passed',lambda e:e['input_identity_after'].update(mapping_id=1),8))
 reject('false_query_identity_metadata','gate full immutable',gate=gate_change('query_integrity_passed',lambda e:e['trial_identity'].update(task_name='wrong'),8))
 reject('capture_phase_order','complete original capture',events=event_change('wait_before',lambda e:e.update(phase='wait_after')))
 reject('capture_wait_counter','complete original capture',events=event_change('wait_before',lambda e:e.update(wait_steps=1)))
 reject('capture_wrong_ordinal','complete original capture',events=event_change('query_before',lambda e:e.update(ordinal=2)))
 reject('capture_foreign_trial','complete original capture',events=event_change('query_before',lambda e:e['trial_identity'].update(task_id=4)))
 bad=list(rawevents);i=next(i for i,r in enumerate(bad) if r.get('event')=='trial_end');bad[i]=copy.deepcopy(bad[i]);bad[i]['control_steps']=16
 reject('trial_end_wrong_count','trial-end counts',events=bad)
 bad=list(rawevents);i=next(i for i,r in enumerate(bad) if r.get('event')=='trial_end');bad.pop(i)
 reject('trial_end_missing','one original trial-end',events=bad)
 bad=list(rawevents);i=next(i for i,r in enumerate(bad) if r.get('event')=='trial_end');bad.insert(i,copy.deepcopy(bad[i]))
 reject('trial_end_duplicate','complete original capture',events=bad)
 bad=list(rawevents);i=next(i for i,r in enumerate(bad) if r.get('phase')=='query_before');bad.pop(i)
 # Renumber all capture indices so failure cannot be credited only to a missing index.
 count=0
 for n,e in enumerate(bad):
  if 'phase' in e:count+=1;bad[n]={**e,'event_index':count}
 reject('missing_capture_even_if_indices_renumbered','complete original capture',events=bad)
 bad=list(rawgate);i=next(i for i,r in enumerate(bad) if r.get('event')=='query_integrity_passed' and r.get('control_step')==8);bad[i],bad[i+1]=bad[i+1],bad[i]
 reject('query_step_order_swap','complete ordered gate chain',gate=bad)
 bad=list(rawgate);i=next(i for i,r in enumerate(bad) if r.get('event')=='t0_pair_gate');bad[i],bad[i+1]=bad[i+1],bad[i]
 reject('pair_moved_after_policy_query','complete ordered gate chain',gate=bad)
 bad=list(rawgate);i=next(i for i,r in enumerate(bad) if r.get('event')=='policy_step_executed');bad.insert(i,copy.deepcopy(bad[i]))
 reject('extra_step_witness','event totals',gate=bad)
 bad=list(rawgate);i=next(i for i,r in enumerate(bad) if r.get('event')=='policy_step_executed');bad[i]={'event':'unknown','ordinal':1}
 reject('unknown_gate_event','event totals',gate=bad)
 reject('policy_error_retained_not_admitted','whole200 completed',rows=row_change(lambda r:r.update(status='policy_error')))
 reject('no_shrunken_warmup','pertrial original300',rows=row_change(lambda r:r.update(wait_steps=9)))
 reject('no_shrunken_control_count','pertrial original300',rows=row_change(lambda r:r.update(control_steps=301)))
 reject('returned_chunk_change','unchanged returned chunk',rows=row_change(lambda r:r['chunks'][0]['environment_actions'][0].__setitem__(0,99)))
 reject('executed_action_change','original action unchanged',rows=row_change(lambda r:r['executed_actions'][0].__setitem__(0,99)))
 reject('pair_instruction_hash','pair content and instruction',gate=gate_change('t0_pair_gate',lambda e:e.update(instruction_utf8_hex='00')))
 bad=list(rawgate);bad[-1]={**bad[-1],'observer_events':0}
 reject('finish_capture_count','finish totals',gate=bad)
 bad=list(rawgate);bad[-1]={**bad[-1],'event_sha256':'0'*64}
 reject('footer_event_bytes','gate footer binds complete',gate=bad)
 # The complete original eight loader topology is also exercised with explicit
 # synthetic markers using the same synthetic RNG bytes, never actual GPU data.
 native,_,nativesha=derive(False)
 phases=['existing_loader_event:'+x for x in ('asset_metadata_compat_load_start','asset_metadata_compat_load_complete','deployment_base_load_start','goal_component_load_start','goal_component_load_complete','goal_component_load_start','goal_component_load_complete','deployment_base_load_complete')]
 loader=[]
 for phase in phases:
  e=copy.deepcopy(rawevents[0]);e.update(phase=phase,ordinal=None,trial_identity=None);loader.append(e)
 with_loader=loader+list(rawevents);count=0
 for i,e in enumerate(with_loader):
  if 'phase' in e:count+=1;with_loader[i]={**e,'event_index':count}
 gate_loader=[{**e,'capture_event_index':e['capture_event_index']+8} if 'capture_event_index' in e else e for e in rawgate]
 gate_loader[-1]={**gate_loader[-1],'observer_events':count,'event_sha256':sha(b''.join(c.canonical(e)+b'\n' for e in with_loader))}
 nativeproof=call(events=with_loader,gate=gate_loader,space=native);positive+=1
 ck('explicit_CPU_complete_native_loader_topology',nativeproof['trials']==200)
 reject('production_loader_gate_rejects_absent_loader','complete original loader capture',space=native)
 bad=list(with_loader);bad[0],bad[1]=bad[1],bad[0];bad[0]={**bad[0],'event_index':1};bad[1]={**bad[1],'event_index':2}
 reject('native_loader_order','complete original loader capture',events=bad,gate=gate_loader,space=native)
 bad=list(with_loader);bad[0]={**bad[0],'trial_identity':rawevents[0]['trial_identity'],'ordinal':1}
 reject('native_loader_outside_trials','loader capture outside',events=bad,gate=gate_loader,space=native)
 # The production function is never modified or admitted by CPU fixture checks.
 original_ns=dict(native);unmodified=types.FunctionType(c.reconstruct_gate.__code__,original_ns,'unmodified_production',c.reconstruct_gate.__defaults__,c.reconstruct_gate.__closure__);unmodified.__kwdefaults__=c.reconstruct_gate.__kwdefaults__;original_ns['reconstruct_gate']=unmodified
 reject('unmodified_production_rejects_CPU_arrays','exact actual five-component',events=with_loader,gate=gate_loader,space=original_ns)
 write(O/'CPU_raw_reconstruction.json',{'status':'passed_explicit_CPU_algorithm_only','changes':changes,'original_function_AST_sha256':sha(ast.dump(original,include_attributes=False).encode()),'derived_function_AST_sha256':derivedsha,'complete_loader_fixture_function_AST_sha256':nativesha,'proof':proof,'native_loader_proof':nativeproof,'production_function_unmodified':True,'production_admission':False})
 return {'status':'passed_CPU_consumer_v2_with_production_HOLD','checks':checks,'rejections':rejections,'positive_cases':positive,'source_consumer_sha256':sha((K/'consumer.py').read_bytes()),'package_manifest_sha256':sha((K/'package_manifest.json').read_bytes()),'full_original_consumer_interface_unchanged':True,'actual_new_full200_terminal_checked':False,'old200_HOLD':True,'new_scientific_trials':0,'GPU_submissions':0,'Slurm_queries':0,'state_changes':0,'P_changes':0,'final_release':False}
try:r=main()
except BaseException as e:
 r={'status':'failed','checks':checks,'rejections':rejections,'error':str(e),'type':type(e).__name__,'traceback':traceback.format_exc()};write(O/'report.json',r);print(json.dumps({'status':'failed','error':str(e)}));raise
write(O/'report.json',r);print(json.dumps({'status':r['status'],'checks':len(checks),'rejections':rejections,'positive_cases':positive}))
