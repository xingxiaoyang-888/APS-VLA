from pathlib import Path
from types import SimpleNamespace
import ast,hashlib,importlib.util,json,sys,traceback
D=Path(__file__).parent;Q=D/'package';O=D/'CPU_final_interfaces_v5';O.mkdir(exist_ok=False)
checks=[];negative=0
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def neg(n,f,base=False):
 global negative
 try:f()
 except BaseException as ex:
  if isinstance(ex,(AssertionError,KeyboardInterrupt,SystemExit)):raise
  if base:ck(n+'_BaseException_not_ordinary_Exception',not isinstance(ex,Exception))
  negative+=1;ck(n,True)
 else:ck(n,False)
def load(p,n):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def main():
 e=load(Q/'entry.py','r5_final_entry');c=load(Q/'consumer.py','r5_final_consumer')
 for module,name in [(e,'scope_module'),(c,'_scope')]:
  ck(name+'_exact_positive',getattr(module,name)().KEYS==e.scope.KEYS)
  tree=ast.parse((Q/('entry.py' if module is e else 'consumer.py')).read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
  source=ast.unparse(ast.Module(body=[node],type_ignores=[]))
  target=O/name;target.mkdir();sentinel=target/'EXECUTED';(target/'scope.py').write_text("from pathlib import Path\nPath("+repr(str(sentinel))+").write_text('BAD')\n")
  ns={'Path':Path,'hashlib':hashlib,'importlib':importlib,'__file__':str(target/'entry.py')}
  exec(compile(source,str(target/'bounded_function.py'),'exec'),ns)
  neg(name+'_altered_scope_before_import',ns[name]);ck(name+'_no_executed_marker',not sentinel.exists())
 # Only CPU test substitutions, never source/production writes.
 ctx=e.context(e.scope.KEYS[0]);calls=[]
 e._verify_sources=lambda ctx,pin:(calls.append('sources') or {'files':{e.PKG+'/storage.py':'x'}})
 e.prepare_original=lambda ctx:(calls.append('original') or ({'proof':'original'},None,None,SimpleNamespace()))
 e.read=lambda p,pin=None:{'rows':['fixed200']}
 e.validate_prefix=lambda ctx,inv,legacy,prefix:(calls.append('identity') or {'fixed200':True})
 e.ref=lambda p:{'path':str(p),'sha256':'a'*64};e.sha=lambda p:'b'*64
 def storage_load(*args):
  calls.append('storage_loaded')
  def fail(*a,**kw):calls.append(('fresh_capacity',kw));raise ValueError('CPU_fixture_no_free_bytes')
  return SimpleNamespace(verify_storage=fail)
 e.load=storage_load
 v=e.verify_existing_metadata(ctx.pair_key,'c'*64)
 ck('existing_ACK_validates_source_original_identity',calls==['sources','original','identity'])
 ck('existing_ACK_never_claims_freshcapacity_or_submission',v['status']=='passed_existing_ACK_metadata_source_only' and v['new_GPU_submission_allowed'] is False and v['storage']['fresh_submission_capacity_verified'] is False and v['storage']['new_storage_paths_created'] is False)
 calls.clear();neg('fresh_submit_still_fails_allfive_capacity',lambda:e.verify_published(ctx.pair_key,'c'*64))
 ck('fresh_called_strict_capacity',calls[:4]==['sources','original','identity','storage_loaded'] and calls[-1][1]=={'must_be_fresh':True,'aggregate_pair_keys':e.scope.KEYS})
 for indent in [None,2]:
  v={'nested':[{'nonascii':'原始观测','quote':'"\n\\'}]*3};raw=(json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=indent)+'\n').encode()
  ck('exact_encoding_'+str(indent),e.bounded_json_bytes(v,len(raw),indent=indent)==raw)
  ck('newline_in_bound_'+str(indent),raw[-1:]==b'\n')
  neg('one_byte_over_'+str(indent),lambda:e.bounded_json_bytes(v,len(raw)-1,indent=indent),True)
 for n,value,indent,limit in [('outer',{'x':'a'*65536},None,65536),('completion',{'x':['']*2000000},2,8*1024*1024),('nonfinite',{'x':float('nan')},2,65536)]:
  p=O/(n+'.json')
  def bounded_write():
   raw=e.bounded_json_bytes(value,limit,indent=indent)
   with p.open('xb') as f:f.write(raw)
  neg(n+'_reject_before_any_write',bounded_write,True);ck(n+'_no_partial_new_file',not p.exists())
 source=(Q/'entry.py').read_text()
 ck('completion_writes_guarded_bytes',"complete_raw=bounded_json_bytes(complete,8*1024*1024,indent=2)" in source and "f.write(complete_raw)" in source)
 ck('parent_writes_guarded_bytes',"parent_raw=bounded_json_bytes(parent,8*1024*1024,indent=2)" in source and "f.write(parent_raw)" in source)
 ck('outer_writes_guarded_bytes',"raw = bounded_json_bytes(row,65536)" in source and "with eventpath.open('ab')" in source)
 before=ast.parse((Q/'consumer.py.pre_scope_pin_v5').read_text());after=ast.parse((Q/'consumer.py').read_text())
 before.body=[n for n in before.body if not isinstance(n,ast.FunctionDef) or n.name!='_scope'];after.body=[n for n in after.body if not isinstance(n,ast.FunctionDef) or n.name!='_scope']
 ck('consumer_raw_algorithm_exact_AST_unchanged_since146tests',ast.dump(before,include_attributes=False)==ast.dump(after,include_attributes=False))
 for key in e.scope.KEYS:
  real=e.context(key)
  ck(key+'_no_actual_output_created',not real.RAW.exists() and not real.OUTPUT.exists())
 return {'status':'passed_CPU_final_bounded_interface_corrections','checks':checks,'check_count':len(checks),'rejections':negative,'source_files':{n:hashlib.sha256((Q/n).read_bytes()).hexdigest() for n in ['entry.py','consumer.py','scope.py']},'production_writes':0,'GPU_submissions':0}
try:r=main()
except BaseException as ex:
 with (O/'failure.json').open('x') as f:json.dump({'error':repr(ex),'traceback':traceback.format_exc(),'checks':checks},f,indent=2)
 raise
with (O/'report.json').open('x') as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:r[k] for k in ['status','check_count','rejections']}))
