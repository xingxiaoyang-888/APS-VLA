"""Raw reconstruction tests on explicitly labeled CPU-only fixtures."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,shutil,sys,traceback
D=Path(__file__).parent;Q=D/'package';O=D/'CPU_consumer_remaining5_v1';O.mkdir(exist_ok=False);checks=[];negative=0
def load(p,n):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def neg(n,f):
 global negative
 try:f()
 except (ValueError,KeyError,IndexError,TypeError):negative+=1;ck(n,True)
 else:ck(n,False)
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def main():
 c=load(Q/'consumer.py','r5consumer_CPU');e=load(Q/'entry.py','r5entry_CPU')
 original=next(n for n in ast.parse((Q/'consumer.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='reconstruct_gate')
 derived=copy.deepcopy(original);changes=[]
 for n in ast.walk(derived):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant):
   if n.args[1].value=='CPU fixture forbidden':
    n.args[0]=ast.parse("gate[0]['CPU_fixture_enabled'] is True and gate[0]['runtime_context']=='synthetic_CPU_fixture'",mode='eval').body;changes.append('require CPU labels')
   elif n.args[1].value=='complete original loader capture sequence':
    n.args[0]=ast.parse('prefix==[]',mode='eval').body;changes.append('explicit CPU fixtures have no model loader')
  if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='expected_schema':
   schema=ast.literal_eval(n.value);schema['agentview_image']=('uint8',[3,4,3],36);schema['robot0_eye_in_hand_image']=('uint8',[3,4,3],36)
   n.value=ast.parse(repr(schema),mode='eval').body;changes.append('two fixture image shapes only')
 ck('three_explicit_fixture_guard_changes',len(changes)==3)
 ast.fix_missing_locations(derived)
 summaries={}
 for key in e.scope.KEYS:
  ctx=e.context(key);source=D/('CPU_'+key);fixture=O/key;fixture.mkdir()
  shutil.copytree(source/'gated',fixture/'observer')
  spec=json.loads((Q/'pairs'/key/'specification.json').read_bytes());rows=c.jsonl(source/'gated.jsonl')
  cx=SimpleNamespace(**vars(ctx));cx.RAW=fixture
  rawcx=SimpleNamespace(**vars(ctx));rawcx.RAW=source/'gated/CPU_raw_observations'
  ns=dict(c.__dict__);cache={}
  def readblob(unused,ref,*,observation,output_root,read_refs):
   cachekey=(json.dumps(ref,sort_keys=True),observation,str(output_root))
   if cachekey not in cache:
    seen={};data=c.read_blob(rawcx,ref,observation=observation,output_root=output_root,read_refs=seen);cache[cachekey]=(data,seen)
   data,seen=cache[cachekey];read_refs.update(seen);return data
  ns['read_blob']=readblob
  exec(compile(ast.Module(body=[derived],type_ignores=[]),'<CPU-explicit-shape-loader-label-only>','exec'),ns)
  reconstruct=ns['reconstruct_gate']
  result=reconstruct(cx,None,rows,specification=spec,job_id='CPU_FIXTURE')
  ck(key+'_200_100_600_3400',all(result[k]==v for k,v in {'trials':200,'paired_t0_checks':100,'queries':600,'control_steps':3400,'warmup_steps':2000}.items()))
  summaries[key]={k:v for k,v in result.items() if k!='raw_blob_refs'}
  neg(key+'_production_rejects_CPU_shape_labels',lambda:c.reconstruct_gate(cx,None,rows,specification=spec,job_id='CPU_FIXTURE'))
  for name,edit in [
   ('missing_result',lambda v:v.pop()),
   ('duplicate_result',lambda v:v.append(copy.deepcopy(v[-1]))),
   ('wrong_method',lambda v:v[-1].update(method='B256_seed17')),
   ('changed_action',lambda v:v[-1]['executed_actions'][0].__setitem__(0,123.)),
   ('wrong_query_count',lambda v:v[-1].update(policy_calls=4)),
   ('wrong_wait',lambda v:v[-1].update(wait_steps=9)),
   ('horizon301',lambda v:v[-1].update(control_steps=301)),
   ('policy_error',lambda v:v[-1].update(status='policy_error'))]:
   bad=copy.deepcopy(rows);edit(bad);neg(key+'_reject_'+name,lambda bad=bad:reconstruct(cx,None,bad,specification=spec,job_id='CPU_FIXTURE'))
  eventpath=fixture/'observer/events.jsonl';gatepath=fixture/'observer/gate.jsonl'
  originals={p:p.read_bytes() for p in (eventpath,gatepath)}
  events=c.jsonl(eventpath);gates=c.jsonl(gatepath)
  cases=[
   ('missing_non_t0_arrays',eventpath,lambda v:[x['observation_arrays'].clear() for x in v if x.get('control_step')==8 and x.get('phase') in ('query_before','query_after')]),
   ('missing_capture',eventpath,lambda v:v.pop(12)),
   ('swap_capture',eventpath,lambda v:v.__setitem__(slice(11,13),[v[12],v[11]])),
   ('wrong_input_dtype',eventpath,lambda v:next(x for x in v if x.get('phase')=='query_before')['observation_arrays']['agentview_image'].update(dtype='int8')),
   ('missing_query',gatepath,lambda v:v.remove(next(x for x in v if x.get('event')=='query_integrity_passed'))),
   ('query_step_reordered',gatepath,lambda v:v.__setitem__(slice(2,4),[v[3],v[2]])),
   ('missing_pair',gatepath,lambda v:v.remove(next(x for x in v if x.get('event')=='t0_pair_gate'))),
   ('foreign_pair_scope',gatepath,lambda v:v[0].update(pair_key='libero_goal_k256_seed17')),
   ('wrong_prefix_pin',gatepath,lambda v:v[0].update(prefix_sha256='0'*64)),
   ('incomplete_finish',gatepath,lambda v:v[-1].update(exact_paired_t0_checks=99)),
   ('input_pointer_change',gatepath,lambda v:next(x for x in v if x.get('event')=='query_integrity_passed')['input_identity_after'].update(mapping_id=1))]
  for name,path,edit in cases:
   data=copy.deepcopy(events if path==eventpath else gates);edit(data)
   try:
    path.write_bytes(b''.join(c.canonical(x)+b'\n' for x in data))
    neg(key+'_reject_'+name,lambda:reconstruct(cx,None,rows,specification=spec,job_id='CPU_FIXTURE'))
   finally:path.write_bytes(originals[path])
  # Raw completeness/path guard cannot accept the synthetic layout as production.
  neg(key+'_raw_inventory_missing',lambda:c.validate_raw_inventory(ctx,[]))
  job={'job_id':'999999999','status':'COMPLETED','exit_code':'0:0','gpus':1,'elapsed_seconds':1,'stage_key':ctx.stage_key,'run_root':str(e.P/ctx.RUN),'suite':'libero_goal','mode':'development','method_ids':ctx.methods}
  c.validate_job(ctx,job,{'job_id':'999999999'});ck(key+'_job_schema',True)
  for field in ('stage_key','method_ids','run_root','mode','gpus','exit_code'):
   bad=copy.deepcopy(job);bad[field]=None;neg(key+'_job_'+field,lambda bad=bad:c.validate_job(ctx,bad,{'job_id':'999999999'}))
 write(O/'fixture_derivation.json',{'source_sha256':hashlib.sha256((Q/'consumer.py').read_bytes()).hexdigest(),'original_AST_sha256':hashlib.sha256(ast.dump(original,include_attributes=False).encode()).hexdigest(),'derived_AST_sha256':hashlib.sha256(ast.dump(derived,include_attributes=False).encode()).hexdigest(),'changes':changes,'extra_fixture_path_mapping':'explicit ctx for private fixture and read_blob raw component source; all byte/hash checks intact','production_acceptance':False,'summaries':summaries})
 return {'status':'passed_CPU_raw_reconstruction_only','checks':checks,'check_count':len(checks),'rejections':negative,'five_synthetic_panels':5,'new_real_scientific_results':0,'actual_P_or_GPU_verified':False}
try:result=main()
except BaseException as error:
 result={'status':'failed_CPU_raw_consumer','checks':checks,'error':str(error),'traceback':traceback.format_exc()};write(O/'report.json',result);print(json.dumps({'status':result['status'],'error':str(error)}));raise
write(O/'report.json',result);print(json.dumps({k:result[k] for k in ('status','check_count','rejections')}))
