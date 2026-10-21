"""Private CPU contract tests. No production output/claim, state, Git or Slurm."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,sys,traceback
D=Path(__file__).parent;Q=D/'package';O=D/'CPU_interfaces_v1';O.mkdir(exist_ok=False);checks=[];negative=0
def load(p,n):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def ck(name,v):
 checks.append({'name':name,'passed':bool(v)})
 if not v:raise AssertionError(name)
def neg(name,f):
 global negative
 try:f()
 except BaseException as e:
  if isinstance(e,(AssertionError,KeyboardInterrupt,SystemExit)):raise
  negative+=1;ck(name,True)
 else:ck(name,False)
def value_from(fn,name,env):
 n=next(n for n in ast.parse((Q/'entry.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name==fn)
 assignment=next(x for x in n.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id==name)
 return eval(compile(ast.Expression(assignment.value),'<explicit CPU structure fixture>','eval'),env)
def main():
 e=load(Q/'entry.py','new_entry_cpu');s=load(Q/'storage.py','new_storage_cpu');g=load(Q/'paired_input_gate_v1.py','new_gate_cpu')
 for key in e.scope.KEYS:
  ctx=e.context(key);c=copy.deepcopy(ctx.config);e.validate_config(ctx,c);ck(key+'_config_accept',True)
  for field in c:
   if field=='schema_note':continue
   z=copy.deepcopy(c);z[field]=None
   neg(key+'_reject_config_'+field,lambda z=z:e.validate_config(ctx,z))
  cfg=ctx.config_sha;manifest='a'*64;entry='b'*64
  env={**e.__dict__,'ctx':ctx,'config_sha':cfg,'manifest_sha':manifest,'entry_sha':entry}
  a=value_from('validate_authorization','fixed',env)
  a.update(root_review={'path':str(ctx.BASE/'root_readiness.json'),'sha256':'c'*64},independent_review={'path':str(ctx.BASE/'independent_readiness.json'),'sha256':'d'*64},original_invocation={'path':str(ctx.ORIGINAL),'sha256':'e'*64})
  e.validate_authorization(ctx,a,cfg,manifest,entry);ck(key+'_auth_structure_accept',True)
  for field in a:
   z=copy.deepcopy(a);z[field]=None
   neg(key+'_reject_auth_'+field,lambda z=z:e.validate_authorization(ctx,z,cfg,manifest,entry))
  for foreign in e.scope.KEYS:
   if foreign!=key:neg(key+'_foreign_'+foreign,lambda foreign=foreign:e.validate_authorization(e.context(foreign),a,cfg,manifest,entry))
  for role in ('root','independent'):
   env.update(role=role);review=value_from('check_review','fixed',env)
   e.check_review(ctx,review,role,manifest,cfg)
   for field in review:
    z=copy.deepcopy(review);z[field]=None
    neg(key+'_'+role+'_review_'+field,lambda z=z,role=role:e.check_review(ctx,z,role,manifest,cfg))
  env.update(auth_sha='f'*64,job='999999999')
  d=value_from('validate_dispatch','fixed',env);env['fixed']=d
  res=value_from('validate_dispatch','rf',env)
  d.update(occupied_job_ids=['999999999'],state_after_sha256='1'*64,reservation={'path':str(ctx.RESERVATION),'sha256':'2'*64})
  e.validate_dispatch(ctx,d,res,a,'f'*64,'999999999','2'*64)
  for field in d:
   z=copy.deepcopy(d);z[field]=None
   neg(key+'_dispatch_'+field,lambda z=z:e.validate_dispatch(ctx,z,res,a,'f'*64,'999999999','2'*64))
  for field in res:
   z=copy.deepcopy(res);z[field]=None
   neg(key+'_reservation_'+field,lambda z=z:e.validate_dispatch(ctx,d,z,a,'f'*64,'999999999','2'*64))
  ck(key+'_runtime_seed_not_training_seed',c['runtime_seed']==17 and c['environment_seed']==0)
 for key in ('libero_goal_k256_seed17','libero_goal_k128_seed17','libero_object_k64_seed23','../libero_goal_k64_seed17','libero_goal_k64_seed17/'):
  neg('forbidden_pair_'+key,lambda key=key:e.context(key))
 ctx=e.context(e.scope.KEYS[0])
 capacity=s.verify_storage(ctx);ck('actual_login_five_budget_readonly',capacity['P_aggregate_required']==5689999360 and capacity['R_aggregate_required']==104725907520 and capacity['no_dedup_credit'])
 (O/'actual_login_capacity.json').write_text(json.dumps(capacity,indent=2)+'\n')
 original=s.inspect
 try:
  def fake(p,n):return {'path':str(p),'st_dev':1,'required_bytes':n,'free_bytes':5689999360+104725907520-1}
  s.inspect=fake;neg('same_filesystem_combined_not_individual',lambda:s.verify_storage(ctx))
  s.inspect=lambda p,n:{'path':str(p),'st_dev':1,'required_bytes':n,'free_bytes':5689999360+104725907520}
  ck('same_filesystem_exact_combined',s.verify_storage(ctx)['filesystem_checks'][0]['required_bytes']==110415906880)
  s.inspect=lambda p,n:{'path':str(p),'st_dev':1 if str(p).startswith(str(s.R)) else 2,'required_bytes':n,'free_bytes':5*n-1}
  neg('aggregate_five_cannot_reuse_single_free',lambda:s.verify_storage(ctx))
  neg('cannot_budget_one_pair_only',lambda:s.verify_storage(ctx,aggregate_pair_keys=[ctx.pair_key]))
 finally:s.inspect=original
 # Exact frozen ledger serializer is checked before its append. Private rows only.
 row={'event':'result','unicode':'开发 observation','escaped':'\\n\\t"x"'}
 guard=g.PairedInputGate(ctx,O/'guard_positive',allow_cpu_fixture=True)
 ledger=SimpleNamespace(run_signature='a'*64)
 before=copy.deepcopy(row);guard.guard_ledger_event(row,ledger)
 ck('normal_guard_keeps_exact_row',row==before and not guard.dead)
 fn=next(n for n in ast.walk(ast.parse((Q/'paired_input_gate_v1.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name=='guard_ledger_event')
 serial=next(n for n in ast.walk(fn) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='encoded' for t in n.targets))
 encoded=eval(compile(ast.Expression(serial.value),'<exact normal serializer>','eval'),{'row':row,'ledger':ledger,'json':json})
 ck('same_original_utf8_newline_serializer',encoded==(json.dumps({**row,'run_signature':ledger.run_signature},ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n').encode())
 for kind,cap in [('start',4096),('cleanup_error',65536),('result',4194304)]:
  ob=g.PairedInputGate(ctx,O/('guard_'+kind),allow_cpu_fixture=True);test={'event':kind,'error':'x'*(cap+1)}
  neg('prewrite_excess_'+kind,lambda ob=ob,test=test:ob.guard_ledger_event(test,ledger))
  ck('failclosed_latch_'+kind,ob.dead and ob.last_gate_abort['reason']=='original ledger row exceeds prewrite storage bound')
  ck('guard_does_not_append_'+kind,not (O/('guard_'+kind)/'trials.jsonl').exists())
  neg('guard_dead_no_retry_'+kind,lambda ob=ob:ob.guard_ledger_event(row,ledger))
 # Production entry refuses all private paths before any invocation or GPU.
 neg('private_entry_cannot_production_verify',lambda:e.verify_published(ctx.pair_key,'a'*64))
 neg('metadata_reconcile_not_production_private',lambda:e.verify_existing_metadata(ctx.pair_key,'a'*64))
 return {'status':'passed_CPU_interfaces_and_capacity_only','checks':checks,'check_count':len(checks),'rejections':negative,'GPU_submissions':0,'production_writes':0,'actual_P_verified':False}
try:result=main()
except BaseException as ex:
 result={'status':'failed_CPU_interfaces','checks':checks,'error':str(ex),'traceback':traceback.format_exc()}
 with (O/'report.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({'status':result['status'],'error':str(ex)}));raise
with (O/'report.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:result[k] for k in ('status','check_count','rejections')}))
