from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,subprocess,sys,traceback
D=Path(__file__).parent;Q=D/'package';O=D/'CPU_outer_v2';O.mkdir(exist_ok=False);checks=[];negative=0
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def neg(n,f):
 global negative
 try:f()
 except BaseException as ex:
  if isinstance(ex,(AssertionError,KeyboardInterrupt,SystemExit)):raise
  negative+=1;ck(n,True)
 else:ck(n,False)
def main():
 e=load(Q/'entry.py','outer_new');c=e.context(e.scope.KEYS[0])
 calls=[]
 def append(p,v):calls.append(('append',p,v));return 'old append return'
 def publish(p,v):calls.append(('publish',p,v));return 'old publish return'
 legacy=SimpleNamespace(append=append,publish=publish)
 path=e.P/'results/formal_main_v2/adapter_invocations'/('999999999_'+'a'*32+'.json')
 value={'normal':'source only','nonascii':'原始资料'}
 with e.bounded_adapter_scope(c,legacy,'999999999') as seen:
  ck('old_append_exact_same_object_and_return',legacy.append(path.with_suffix('.jsonl'),value)=='old append return' and calls[-1][2] is value)
  ck('old_publish_exact_same_object_and_return',legacy.publish(path,value)=='old publish return' and calls[-1][2] is value)
 ck('bindings_restored_success',legacy.append is append and legacy.publish is publish and seen['append_calls']==seen['publish_calls']==1)
 for name,action in [
  ('bad_job',lambda:legacy.append(path.with_name('1_'+'a'*32+'.jsonl'),value)),
  ('bad_suffix',lambda:legacy.append(path.with_suffix('.bin'),value)),
  ('wrong_root',lambda:legacy.append(O/'file.jsonl',value)),
  ('oversize_append',lambda:legacy.append(path.with_suffix('.jsonl'),{'error':'x'*4194304})),
  ('oversize_publish',lambda:legacy.publish(path,{'error':'x'*4194304})),
  ('duplicate_publish',lambda:(legacy.publish(path,value),legacy.publish(path,value)))]:
  count=len(calls)
  try:
   with e.bounded_adapter_scope(c,legacy,'999999999'):neg(name,action)
  finally:ck(name+'_restored',legacy.append is append and legacy.publish is publish)
  if name!='duplicate_publish':ck(name+'_stopped_before_original_write',len(calls)==count)
 with e.bounded_adapter_scope(c,legacy,'999999999') as seen:
  seen['append_calls']=1024
  neg('event_count_guard',lambda:legacy.append(path.with_suffix('.jsonl'),value))
 ck('BaseException_not_swallowed_by_scientific_loop',issubclass(e.MetadataBoundAbort,BaseException) and not issubclass(e.MetadataBoundAbort,Exception))
 original=e._verify
 try:
  calls2=[]
  def fake(ctx,pin,fresh):calls2.append((ctx.pair_key,pin,fresh));return {'status':'passed_metadata_source_capacity_only'}
  e._verify=fake;v=e.verify_existing_metadata(c.pair_key,'f'*64)
  ck('ACK_readonly_no_new_fresh_claim',calls2==[(c.pair_key,'f'*64,False)] and v['status']=='passed_existing_ACK_metadata_source_only' and v['new_GPU_submission_allowed'] is False)
 finally:e._verify=original
 # Verify fresh identities from original input panel without constructing an old run_root.
 original_import=e.load(e.LEGACY,'actual_legacy_sourceonly',e.LSHA)
 for key in e.scope.KEYS:
  ctx=e.context(key);prefix=json.loads((Q/'pairs'/key/'specification.json').read_bytes())['rows']
  p=e.validate_prefix(ctx,{'run_root':'/never/create/old/output'},original_import,prefix)
  ck(key+'_fresh_panel_input',p['original_fixed200_identity_order'] and p['panel_is_original_input_not_old_output'])
 # Child process owns only private CPU output; parent keeps its normal descriptors.
 logdir=O/'CPU_runtime_logs';logdir.mkdir()
 code="""from pathlib import Path
from types import SimpleNamespace
import importlib.util,json,os,resource
p=Path(%r);s=importlib.util.spec_from_file_location('entry_child',p);e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
c=SimpleNamespace(RAW=Path(%r))
v=e.redirect_runtime_output(c)
os.write(1,b'CPU stdout retained\\n');os.write(2,b'CPU stderr retained\\n')
print(json.dumps({'limit':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'paths':v}),flush=True)
try:e.redirect_runtime_output(c)
except FileExistsError:print('EXCLUSIVE_REFUSED',flush=True)
else:raise AssertionError('duplicate log path accepted')
"""%(str(Q/'entry.py'),str(logdir))
 child=subprocess.run([sys.executable,'-B','-c',code],capture_output=True,text=True)
 ck('private_log_redirect_child_return',child.returncode==0)
 out=(logdir/'runtime.stdout').read_text();err=(logdir/'runtime.stderr').read_text()
 ck('separate_runtime_logs_original_prefix_retained','CPU stdout retained' in out and 'EXCLUSIVE_REFUSED' in out and err=='CPU stderr retained\n')
 ck('RLIMIT_applies_own_runtime_files_only','2147483648' in out)
 ck('P_and_R_real_attempts_not_created',all(not e.context(k).OUTPUT.exists() and not e.context(k).RAW.exists() for k in e.scope.KEYS))
 return {'status':'passed_CPU_outer_bounded_metadata_only','checks':checks,'check_count':len(checks),'rejections':negative,'production_writes':0,'GPU_submissions':0,'new_science':0}
try:result=main()
except BaseException as ex:
 result={'status':'failed_CPU_outer','checks':checks,'error':str(ex),'traceback':traceback.format_exc()}
 with (O/'report.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({'status':result['status'],'error':str(ex)}));raise
with (O/'report.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:result[k] for k in ('status','check_count','rejections')}))
