from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import argparse,ast,copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_remaining5_gateway_independent_20261021T0449'
A=R/'.local/goal_remaining5_dispatch_20261021T0449'
V2='7de77ebb179dfe465e490290ab33ff280109cd28225dcbfe6a9b859a0d5207b3'
V3='45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(path,pin,name):
 b=path.read_bytes();assert sha(b)==pin,(path,'SHA differs')
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m
 exec(compile(b,str(path),'exec',dont_inherit=True),m.__dict__);return m
def save(name,value):
 p=D/name
 with p.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False,sort_keys=True);f.write('\n')
 return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
ap=argparse.ArgumentParser();ap.add_argument('--runtime-manifest',type=Path,required=True);ap.add_argument('--runtime-manifest-sha256',required=True);ap.add_argument('--dispatch-scope',type=Path,required=True);ap.add_argument('--dispatch-scope-sha256',required=True)
args=ap.parse_args()
pkgb=args.runtime_manifest.read_bytes();assert sha(pkgb)==args.runtime_manifest_sha256
pkg=json.loads(pkgb);package=args.runtime_manifest.parent;PKG='scripts/ops/formal_goal_remaining5_gate_v1'
assert pkg['schema']=='formal_main_v2' and pkg['version']=='goal-remaining5-prospective-single-attempt-v1'
for rel,pin in pkg['files'].items():
 path=package/Path(rel).relative_to(PKG);assert path.is_file() and sha(path.read_bytes())==pin,(rel,'final package source changed')
scb=args.dispatch_scope.read_bytes();assert sha(scb)==args.dispatch_scope_sha256
scope=json.loads(scb);assert scope['runtime_manifest_sha256']==args.runtime_manifest_sha256 and scope['runtime_files']==pkg['files']
entry=load(package/'entry.py',pkg['files'][PKG+'/entry.py'],'_independent_final_r5_entry')
consumer=load(package/'consumer.py',pkg['files'][PKG+'/consumer.py'],'_independent_final_r5_consumer')
mods={2:load(A/'gateway.py',V2,'_r5_gateway_v2'),3:load(A/'gateway_v3.py',V3,'_r5_gateway_v3')}
positive=[];negative=[];v2failures=[];proofs={}
def ok(v,label):
 if not v:raise AssertionError(label)
 positive.append(label)
def no(fn,label):
 try:fn()
 except Exception as e:negative.append({'check':label,'type':type(e).__name__,'error':str(e)});return str(e)
 raise AssertionError('accepted forbidden: '+label)
def dispatchers(m):
 raw0=m.raw;read0=m.read
 def rr(p,pin=None):
  if str(p) in [str(root/m.BASE/'scope.json') for root in (m.R,m.P)]:
   assert pin in (None,args.dispatch_scope_sha256);return scb
  return raw0(p,pin)
 def rd(p,pin=None):
  if str(p) in [str(root/m.BASE/'scope.json') for root in (m.R,m.P)]:
   assert pin in (None,args.dispatch_scope_sha256);return copy.deepcopy(scope)
  return read0(p,pin)
 with patch.object(m,'raw',rr),patch.object(m,'read',rd):return {k:m.make_dispatcher(k,args.dispatch_scope_sha256) for k in m.PAIRS}
ds={v:dispatchers(m) for v,m in mods.items()}
def bundle(m,d,key):
 auth_bytes=m.canonical({'CPU_SYNTHETIC_AUTHORIZATION':key})+b'\n';ah=sha(auth_bytes)
 return {'authorization':{'CPU_SYNTHETIC_AUTHORIZATION':key},'authorization_sha256':ah,'invocation_bytes':auth_bytes,
 'authorization_ref':{'path':d.authorization,'bytes':len(auth_bytes),'sha256':ah},'token':'cti-goal-remaining5-v1:'+key+':'+ah,
 'comment':'cti-goal-remaining5-v1:'+key+':'+ah,'admission':{'prepared_utc':'2026-10-21T04:49:00+00:00'},
 'runtime_package':pkg,'sources':{**pkg['files'],m.BASE+'/gateway.py':V3,m.BASE+'/scope.json':args.dispatch_scope_sha256},
 'admission_ref':{'path':str(Path(d.authorization).parent/'dispatch_admission.json'),'bytes':1,'sha256':'f'*64}}
# Run the actual native dispatch_proof body, replacing only effects/observations.
# The entry validation function is loaded unchanged from the final runtime bytes.
# No canonical or P files are created; all observation/auth values here are CPU fixtures.
for key in mods[3].PAIRS:
 ctx=entry.context(key);actual_ctx=consumer.scope.context(key)
 for version in (2,3):
  m=mods[version];d=ds[version][key];b=bundle(m,d,key);res=d.reservation(b);rb=m.canonical(res)+b'\n'
  statehash='6'*64;jid='9970001';registered=d.job_record(jid,b,d.sbatch_argv(b));writes=[]
  fake=SimpleNamespace(bundle=b,read_state=lambda:({},statehash),observe=lambda *a,**k:{'derived':{'occupied':[jid]}})
  raw0=m.raw;load0=m.load
  def raw_virtual(p,pin=None):
   if str(p) in [str(root/Path(d.authorization).parent/'reservation.json') for root in (m.R,m.P)]:
    assert pin in (None,sha(rb));return rb
   return raw0(p,pin)
  def load_virtual(p,pin,name):
   if str(p)==str(m.P/m.PROD/'entry.py'):
    assert pin==pkg['files'][PKG+'/entry.py'];return entry
   return load0(p,pin,name)
  def record_virtual(p,v,allow_identical=False):
   assert str(p) in [str(root/Path(d.authorization).parent/'held_dispatch_record.json') for root in (m.R,m.P)]
   writes.append({'path':str(p),'value':copy.deepcopy(v),'allow_identical':allow_identical})
  with patch.object(m,'raw',raw_virtual),patch.object(m,'load',load_virtual),patch.object(m,'record',record_virtual):
   if version==2:
    error=no(lambda:d.Native.dispatch_proof(fake,jid,{},statehash),key+' original v2 native rejects missing pair_key')
    v2failures.append({'pair_key':key,'source_sha256':V2,'error':error});ok(writes==[],key+' rejected v2 publishes no dispatch')
    continue
   measured=d.Native.dispatch_proof(fake,jid,{},statehash)
  ok(len(writes)==2 and writes[0]['value']==writes[1]['value'],key+' actual v3 native R/P dispatch identical')
  dispatch=writes[0]['value'];ok(dispatch['pair_key']==res['pair_key']==key,key+' actual reservation and dispatch pair bound')
  entry.validate_dispatch(ctx,dispatch,res,b['authorization'],b['authorization_sha256'],jid,sha(rb))
  # terminal_fixture changes only scheduler termination fields; every generated
  # registration identity/mode/output is used unchanged by the real consumer.
  terminal=copy.deepcopy(registered);terminal.update(status='COMPLETED',exit_code='0:0',elapsed_seconds=123)
  consumer.validate_job(actual_ctx,terminal,dispatch);ok(True,key+' actual generated job accepted by final raw consumer precheck')
  proofs[key]={'dispatch':dispatch,'reservation':res,'job_record':registered,'terminal_fixture':terminal,
   'is_CPU_fixture':True,'new_rollout_or_completion_evidence':False}
  for field in ('pair_key','stage_key','job_id','authorization','request_token','capacity_limit_all_GPU_modes','reserved_slots','maximum_attempts','new_submissions','no_requeue','scientific_release','resources','occupied_job_ids','state_after_sha256','reservation'):
   bad=copy.deepcopy(dispatch);bad.pop(field)
   no(lambda bad=bad:entry.validate_dispatch(ctx,bad,res,b['authorization'],b['authorization_sha256'],jid,sha(rb)),key+' reject missing dispatch '+field)
  for field in ('pair_key','stage_key','authorization','reserved_slots','capacity_limit_all_GPU_modes','maximum_wall_seconds','automatic_retry','scientific_release'):
   bad=copy.deepcopy(res);bad.pop(field)
   no(lambda bad=bad:entry.validate_dispatch(ctx,dispatch,bad,b['authorization'],b['authorization_sha256'],jid,sha(rb)),key+' reject missing reservation '+field)
  for field,value in [('stage_key','foreign'),('run_root',registered['attempt_root']),('mode','goal_remaining5_prospective'),('method_ids',list(reversed(registered['method_ids']))),('suite','libero_spatial'),('job_id','9970002'),('gpus',0),('status','FAILED'),('exit_code','1:0'),('elapsed_seconds',-1)]:
   bad=copy.deepcopy(terminal);bad[field]=value;no(lambda bad=bad:consumer.validate_job(actual_ctx,bad,dispatch),key+' reject altered registered '+field)
  for other in mods[3].PAIRS:
   if other==key:continue
   no(lambda other=other:entry.validate_dispatch(entry.context(other),dispatch,res,b['authorization'],b['authorization_sha256'],jid,sha(rb)),key+' reject foreign scope '+other)
 # ABI test of the real new reconcile function. The expensive actual metadata
 # verification is a clearly marked return-value fixture, not a fabricated receipt.
 called=[]
 def verify_fixture(c,manifest,fresh):
  called.append((c.pair_key,manifest,fresh));return {'status':'passed_metadata_source_capacity_only','identity':{'original_fixed200_identity_order':True,'unique_development_states':100},'CPU_FIXTURE':True}
 with patch.object(entry,'_verify',verify_fixture):value=entry.verify_existing_metadata(key,args.runtime_manifest_sha256)
 ok(called==[(key,args.runtime_manifest_sha256,False)] and value['status']=='passed_existing_ACK_metadata_source_only' and value['new_GPU_submission_allowed'] is False and value['new_submission_authorized'] is False,key+' real reconcile API fresh=False and no new GPU')
# Prove v2 -> v3 consists only of the two required immutable context fields.
a=ast.parse((A/'gateway.py').read_text());z=ast.parse((A/'gateway_v3.py').read_text())
removed=0
for n in ast.walk(z):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='dict':
  keys={k.arg for k in n.keywords}
  if 'kind' in keys and any(k.arg=='kind' and isinstance(k.value,ast.Constant) and k.value.value in ('root_goal_remaining5_GPU_slot_reservation','root_goal_remaining5_held_dispatch') for k in n.keywords):
   matched=[k for k in n.keywords if k.arg=='pair_key'];assert len(matched)==1 and isinstance(matched[0].value,ast.Name) and matched[0].value.id=='KEY'
   n.keywords=[k for k in n.keywords if k.arg!='pair_key'];removed+=1
ok(removed==2 and ast.dump(a,include_attributes=False)==ast.dump(z,include_attributes=False),'exactly two pair_key additions; no scientific/scheduler semantic changes')
save('v2_actual_runtime_interface_rejection.json',{'schema':'formal_main_v2','kind':'Goal_remaining5_gateway_v2_actual_runtime_interface_rejection','gateway_sha256':V2,'final_runtime_manifest_sha256':args.runtime_manifest_sha256,'entry_sha256':pkg['files'][PKG+'/entry.py'],'failures':v2failures,'CPU_only':True})
save('cross_interface_CPU_fixtures.json',{'scope_fixture_not_production':True,'proofs':proofs})
report={'schema':'formal_main_v2','kind':'Goal_remaining5_gateway_final_runtime_cross_interface_CPU','status':'passed','gateway_sha256':V3,'package_manifest_sha256':args.runtime_manifest_sha256,
 'scope_sha256':args.dispatch_scope_sha256,'runtime_files':pkg['files'],'dispatch_files':{mods[3].BASE+'/gateway.py':V3,mods[3].BASE+'/scope.json':args.dispatch_scope_sha256},
 'positive_count':len(positive),'negative_count':len(negative),'positive':positive,'negative':negative,'all_five_native_dispatch_proof_actual_function_rebuilt':True,'all_five_real_consumer_validate_job_rebuilt':True,'actual_P_verified':False,'real_raw_terminal_consumer_executed':False,'actual_admission_executed':False,'new_GPU_submissions':0,'new_scientific_trials':0,'production_admitted':False,'scope_of_validation':'actual final source functions on explicit CPU auth/observation fixtures; no actual P/GPU/terminal receipt manufactured'}
print(json.dumps(save('cross_interface_review.json',report),sort_keys=True))
