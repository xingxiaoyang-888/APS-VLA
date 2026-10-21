from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import argparse,copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_remaining5_gateway_independent_20261021T0449';A=R/'.local/goal_remaining5_dispatch_20261021T0449'
V3='45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()+b'\n'
def load(p,pin,name):
 b=p.read_bytes();assert sha(b)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(b,str(p),'exec',dont_inherit=True),m.__dict__);return m
def fixed_from_failure(fn,*args):
 try:fn(*args)
 except ValueError as exc:
  tb=exc.__traceback__
  while tb:
   if tb.tb_frame.f_code is fn.__code__:return copy.deepcopy(tb.tb_frame.f_locals['fixed'])
   tb=tb.tb_next
  raise AssertionError('real schema fixed dict unavailable')
 raise AssertionError('expected schema failure')
ap=argparse.ArgumentParser();ap.add_argument('--runtime-manifest',type=Path,required=True);ap.add_argument('--runtime-manifest-sha256',required=True);ap.add_argument('--dispatch-scope',type=Path,required=True);ap.add_argument('--dispatch-scope-sha256',required=True);a=ap.parse_args()
pb=a.runtime_manifest.read_bytes();assert sha(pb)==a.runtime_manifest_sha256;pkg=json.loads(pb);PKG='scripts/ops/formal_goal_remaining5_gate_v1';package=a.runtime_manifest.parent
for rel,pin in pkg['files'].items():assert sha((package/Path(rel).relative_to(PKG)).read_bytes())==pin
sb=a.dispatch_scope.read_bytes();assert sha(sb)==a.dispatch_scope_sha256;scope=json.loads(sb);assert scope['runtime_files']==pkg['files'] and scope['runtime_manifest_sha256']==a.runtime_manifest_sha256
m=load(A/'gateway_v3.py',V3,'_independent_r5_admission_gateway');e=load(package/'entry.py',pkg['files'][PKG+'/entry.py'],'_independent_r5_admission_entry')
raw_original=m.raw;load_original=m.load;positive=[];negative=[];calls=[]
def ok(v,label):
 if not v:raise AssertionError(label)
 positive.append(label)
def no(fn,label):
 try:fn()
 except Exception as exc:negative.append({'check':label,'type':type(exc).__name__,'error':str(exc)});return
 raise AssertionError('accepted invalid: '+label)
for key in m.PAIRS:
 v={}
 def install(rel,b):
  for root in (m.R,m.P):v[str(root/rel)]=b
 def ref(rel,b):return {'path':rel,'bytes':len(b),'sha256':sha(b)}
 def vr(p,pin=None):
  if str(p) in v:
   b=v[str(p)]
   if pin is not None and sha(b)!=pin:raise ValueError('CPU virtual exact file pin differs')
   return b
  return raw_original(p,pin)
 def vl(p,pin,name):
  if str(p)==str(m.P/m.PROD/'entry.py'):
   assert pin==pkg['files'][PKG+'/entry.py'];return e
  return load_original(p,pin,name)
 install(m.BASE+'/gateway.py',(A/'gateway_v3.py').read_bytes());install(m.BASE+'/scope.json',sb);install(PKG+'/package_manifest.json',pb)
 for rel in pkg['files']:install(rel,(package/Path(rel).relative_to(PKG)).read_bytes())
 ctx=e.context(key);csha=pkg['files'][PKG+'/pairs/'+key+'/config.json'];esha=pkg['files'][PKG+'/entry.py']
 for role in ('root','independent'):
  value=fixed_from_failure(e.check_review,ctx,{},role,a.runtime_manifest_sha256,csha);install(ctx.X+'/'+role+'_readiness.json',enc(value))
 auth=fixed_from_failure(e.validate_authorization,ctx,{},csha,a.runtime_manifest_sha256,esha)
 auth['original_invocation']={'path':str(ctx.ORIGINAL),'sha256':'8'*64}
 for role in ('root','independent'):
  rel=ctx.X+'/'+role+'_readiness.json';auth[role+'_review']={'path':str(m.P/rel),'sha256':sha(v[str(m.R/rel)])}
 ab=enc(auth);install(ctx.X+'/root_authorization.json',ab)
 value={'status':'passed_metadata_source_capacity_only','stage_key':ctx.stage_key,'package_manifest_sha256':a.runtime_manifest_sha256,'config_sha256':csha,
 'new_GPU_submissions':0,'actual_GPU_runtime_verified':False,'GPU_execution_authorized':False,'original200_HOLD':True,'final_release':False,
 'identity':{'original_fixed200_identity_order':True,'unique_development_states':100,'CPU_FIXTURE_ORIGINAL_INVOCATION':key},
 'storage':{'aggregate_pair_keys':list(m.PAIRS),'no_dedup_credit':True}}
 def vp(pair,pin,*,must_be_fresh=True):
  assert pair==key and pin==a.runtime_manifest_sha256;calls.append({'pair':pair,'must_be_fresh':must_be_fresh,'CPU_stub':True});return copy.deepcopy(value)
 with patch.object(m,'raw',vr),patch.object(m,'load',vl),patch.object(e,'verify_published',vp):
  d=m.make_dispatcher(key,a.dispatch_scope_sha256);ad=d.admission_fixed();ad.update(prepared_utc='2026-10-21T04:49:00+00:00',dispatch_files=m.source_map(),runtime_files=pkg['files'],authorization=ref(ctx.X+'/root_authorization.json',ab))
  runtime_review={'status':'passed_source_CPU','package_manifest_sha256':a.runtime_manifest_sha256,'package_files':pkg['files'],'blockers':[],'reviewed_by':'CPU_independent_fixture'}
  dispatch_review={'kind':'Goal_remaining5_atomic_dispatch_independent_review','status':'passed','dispatch_files':m.source_map(),'package_manifest_sha256':a.runtime_manifest_sha256,'runtime_files':pkg['files'],'blockers':[],'review_scope':'source_and_CPU_only','GPU_execution_authorized':False}
  capture={'kind':'Goal_remaining5_actual_P_verification_capture','argv':[str(m.H/'venv/bin/python'),'-B',str(m.P/PKG/'entry.py'),'--pair-key',key,'--verify','--package-manifest-sha256',a.runtime_manifest_sha256],'returncode':0,'runtime_files':pkg['files'],'stdout':json.dumps(value)}
  for field,obj in [('runtime_independent_review',runtime_review),('dispatch_independent_review',dispatch_review),('actual_P_verification',capture)]:
   # These are memory-only structural fixtures. They are never written to the named archive locations.
   rel='results/formal_main_v2/engineering/CPU_NOT_A_REAL_RECEIPT/'+key+'/'+field+'.json';bb=enc(obj);install(rel,bb);ad[field]=ref(rel,bb)
  rel=ctx.X+'/dispatch_admission.json';adb=enc(ad);install(rel,adb)
  checked=d.admission(sha(adb));ok(checked['authorization']==auth and checked['sources']=={**m.source_map(),**pkg['files']},key+' actual admission function complete structural CPU traversal')
  ok(checked['token']=='cti-goal-remaining5-v1:'+key+':'+sha(ab),key+' deterministic original authorization token')
  # Every fixed root binding must be checked by the unchanged admission function.
  for field in d.admission_fixed():
   bad=copy.deepcopy(ad);bad.pop(field);badb=enc(bad);install(rel,badb)
   no(lambda badb=badb:d.admission(sha(badb)),key+' missing root field '+field)
  install(rel,adb)
  for field in ('runtime_files','dispatch_files','authorization'):
   bad=copy.deepcopy(ad);bad[field]={};badb=enc(bad);install(rel,badb);no(lambda badb=badb:d.admission(sha(badb)),key+' bad source/reference '+field)
  install(rel,adb)
  # Different content on P can never pass the same canonical root authorization.
  pkey=str(m.P/ctx.X/'root_authorization.json');original=v[pkey];v[pkey]=b'{}'
  no(lambda:d.admission(sha(adb)),key+' mismatching P authorization');v[pkey]=original
  for field in ('runtime_independent_review','dispatch_independent_review','actual_P_verification'):
   obj=json.loads(v[str(m.R/ad[field]['path'])]);rb=enc(obj)
   targets=(('blockers',['not_reviewed']),) if field!='actual_P_verification' else (('returncode',1),('argv',['wrong']),('runtime_files',{}),('stdout','{}'))
   for f,badval in targets:
    changed=copy.deepcopy(obj);changed[f]=badval;newb=enc(changed);install(ad[field]['path'],newb)
    bad=copy.deepcopy(ad);bad[field]=ref(ad[field]['path'],newb);badb=enc(bad);install(rel,badb)
    no(lambda badb=badb:d.admission(sha(badb)),key+' bad '+field+' '+f)
   install(ad[field]['path'],rb);install(rel,adb)
  for f in ('root_review','independent_review','original_invocation'):
   changed=copy.deepcopy(auth);changed[f]={};newb=enc(changed);install(ctx.X+'/root_authorization.json',newb)
   bad=copy.deepcopy(ad);bad['authorization']=ref(ctx.X+'/root_authorization.json',newb);badb=enc(bad);install(rel,badb)
   no(lambda badb=badb:d.admission(sha(badb)),key+' real entry rejects authorization '+f)
   install(ctx.X+'/root_authorization.json',ab);install(rel,adb)
report={'schema':'formal_main_v2','kind':'Goal_remaining5_atomic_admission_independent_CPU_fixture','status':'passed','source_sha256':V3,'package_manifest_sha256':a.runtime_manifest_sha256,'scope_sha256':a.dispatch_scope_sha256,
 'positive_count':len(positive),'negative_count':len(negative),'positive':positive,'negative':negative,'callbacks':calls,
 'strict_scope':'readiness/root/independent/actual-P result values are memory-only fixtures exercising source and ABI validation; no real receipt or actual_P pass created',
 'actual_P_verified':False,'actual_native_admission_executed':False,'new_GPU_submissions':0,'state_written':False,'canonical_or_P_files_written':False,'production_admitted':False}
p=D/'admission_CPU_review.json'
with p.open('x') as f:json.dump(report,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'positive':len(positive),'negative':len(negative)},sort_keys=True))
