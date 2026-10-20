"""Bounded supplementary original gateway support-source review.
No canonical, P, state, Git or scheduler writes. The previous scoped review
and all previously failed fixture records are retained unchanged.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,traceback,xml.etree.ElementTree as ET
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/spatial_gateway_independent_20261020T2253'
A='results/formal_main_v2/engineering/action_deployment_candidates_0809/'
checks=[];reads={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(path,pin=None):
 assert path.resolve()==path and not any(x.is_symlink() for x in (path,*path.parents))
 b=path.read_bytes();assert pin is None or sha(b)==pin
 reads[str(path)]={'sha256':sha(b),'bytes':len(b)};return b
def ok(name,v):
 assert v,name
 checks.append({'name':name,'passed':True})
def save(name,x):
 p=D/name
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes())}
try:
 current_ref={'path':'.local/spatial_gateway_independent_20261020T2253/independent_review.json','sha256':'e488430128bfbecc1e3ca846764dd6620ebea405d90ffb06063b1d09bdce69b2'}
 current=json.loads(read(R/current_ref['path'],current_ref['sha256']))
 rel='scripts/ops/formal_action_deployment_v1/gateway.py';pin='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
 old=read(R/rel,pin)
 ok('original support gateway R/P byte equality',read(P/rel,pin)==old)
 legacy_ref={'path':A+'action_gateway_consumers_independent_0809/gateway_independent_review.json','sha256':'c232149639a1e6335189610aebba19830e1a3c8bfe9b932d1398566f10cd2b4f'}
 legacy=json.loads(read(R/legacy_ref['path'],legacy_ref['sha256']))
 ok('old independent scope directly binds exact original gateway',legacy['kind']==current['kind'] and legacy['status']=='passed_CPU_review' and legacy['review_role']=='independent' and legacy['blockers']==[] and legacy['files']=={rel:pin})
 for source,p in legacy['evidence_sha256'].items():
  target=R/(A+source[len('.local/'):] if source.startswith('.local/') else source)
  read(target,p)
  ok('retained original independent evidence '+source,True)
 xml=R/(A+'action_gateway_consumers_independent_0809/pytest_gateway_final.xml')
 suites=ET.fromstring(xml.read_bytes())
 nodes=[suites] if suites.tag=='testsuite' else list(suites.iter('testsuite'))
 stats={k:sum(int(x.attrib.get(k,0)) for x in nodes) for k in ('tests','failures','errors','skipped')}
 ok('original independent raw XML confirms96 historical passes',stats=={'tests':96,'failures':0,'errors':0,'skipped':0})
 ok('new audit does not claim historical suite was rerun',legacy['checks']['total_passed']==96)
 newrel='scripts/ops/formal_action_deployment_posttraining_spatial588_v1/gateway.py'
 new=read(R/newrel,'aba5868a8dc4e480262177785b2e62123d014046624f37924248721a9575c99c')
 ot=ast.parse(old);nt=ast.parse(new)
 def top(t,n):return next(x for x in t.body if isinstance(x,(ast.ClassDef,ast.FunctionDef)) and x.name==n)
 for n in ['relative','stable','Evidence','NativeIO','parse_ack','registered_comment','check_observed_identity','corroborate_new_job','submission_argv','reconcile_submission']:
  ok('old/new core unchanged AST '+n,ast.dump(top(ot,n),include_attributes=False)==ast.dump(top(nt,n),include_attributes=False))
 for n in ['run','_cas','__init__']:
  of=next(x for x in top(ot,'Gateway').body if isinstance(x,ast.FunctionDef) and x.name==n)
  nf=next(x for x in top(nt,'Gateway').body if isinstance(x,ast.FunctionDef) and x.name==n)
  ok('old/new Gateway core unchanged AST '+n,ast.dump(of,include_attributes=False)==ast.dump(nf,include_attributes=False))
 ef=json.loads(read(R/'results/formal_main_v2/execution/spatial588_pre_dispatch_v1/effective_plan.json','17bfd4d6f5b69ae6dc18fe9cc36256baeb60f0aa4586fbb4c6de5391c93123b5'))
 ok('old gateway is pinned support not selected GPU wrapper',ef['invocation']['support_files'][rel]==pin and ef['invocation']['wrapper']=='scripts/ops/formal_action_deployment_v1/wrapper.py')
 completed={**current['files'],rel:pin}
 ready_path=R/'results/formal_main_v2/execution/spatial588_pre_dispatch_v1/runtime_readiness.json'
 ready=json.loads(read(ready_path));covered=dict(completed)
 for role,ref in ready['component_reviews'].items():
  rv=json.loads(read(R/ref['path'],ref['sha256']))
  ok('unchanged component independently passed '+role,rv['schema']=='formal_main_v2' and rv['kind']=='formal_downstream_action_component_independent_CPU_review' and rv['component']==role and rv['status']=='passed_CPU_review' and not rv.get('blockers'))
  for name,h in rv.get('files',{}).items():
   ok('component source no conflict '+name,name not in covered or covered[name]==h);read(R/name,h);covered[name]=h
 for name,h in ready['support_files'].items():
  if name.startswith('scripts/ops/formal_action_deployment_v1/'):
   ok('exact component closure fully covered '+name,covered.get(name)==h)
 for name,row in reads.items():assert sha(Path(name).read_bytes())==row['sha256'],name
 supplement=save('original_gateway_support_evidence.json',{'schema':'formal_main_v2','kind':'original_gateway_exact_support_source_independent_supplement','status':'passed_CPU_review','check_count':len(checks),'checks':checks,'files':{rel:pin},'source_evidence':reads,'original_independent_ref':legacy_ref,'historical_test_XML':stats,'historical_tests_rerun_this_turn':False,'core_AST_same_as_new_independently_tested_state_machine':True,'new_real_submissions':0,'new_GPU_seconds':0})
 out=copy.deepcopy(current)
 out.update(files=completed,check_count=current['check_count']+len(checks),version='Spatial588_gateway_independent_complete_support_closure_v2',supersedes_for_exact_authorization=current_ref,additional_original_gateway_support_review=supplement,prior_checks=current['check_count'],additional_support_checks=len(checks),historical_original_gateway_CPU_results='96 prior independent cases verified from pinned raw logs/XML, inherited rather than rerun',production_blockers=[{'id':'SP588_NEW_OUTER_PREFLIGHT','reason':'Root must complete exact readiness/prepared actual new P outer verification and immutable full authorization preflight.'},{'id':'SP588_EXACT_AUTH_AND_CAPACITY','reason':'Fresh all-mode eight-slot/controller/lease/pending and one-attempt root authorization remain mandatory; old failed authorization is retained and never reused.'},{'id':'SP588_TERMINAL_CONSUMER','reason':'All600 raw rows still require original typed consumer plus independent terminal review, preserving12legacy+588current and all costs.'}],canonical_source_scope_is_install_projection=False,actual_new_canonical_P_verified=True,actual_new_canonical_P_scope='Source and metadata only; see separate actual_P_independent_review 1ce88ed0152402a3b1c73a1fe1a70b4ae1b65ff6269a967efb2efd270914ee7b. New outer remains pending.',production_admission=False,utc=datetime.now(timezone.utc).isoformat())
 out['limitations']=[x for x in current['limitations'] if 'entire production authorization' not in x]+['Existing96 independent CPU test results are explicitly inherited and raw verified, while this turn tests only new source closure and previously reported242 exact-gateway checks.','No runtime/GPU action setting or deployment gateway source was changed; only this independently verified support-source coverage was added.']
 ref=save('independent_review_v2.json',out)
 files=sorted(p for p in D.rglob('*') if p.is_file() and not p.is_symlink())
 man=save('delivery_manifest_v4.json',{'schema':'formal_main_v2','kind':'Spatial588_complete_gateway_support_closure_independent_delivery','status':'passed_scoped_review','production_submission_authorized':False,'review':ref,'file_count':len(files),'files':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in files],'new_GPU_seconds':0})
 print(json.dumps({'review':ref,'manifest':man,'checks':len(checks),'file_count':len(files)}))
except BaseException as exc:
 save('original_support_failure_a1.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':checks,'new_GPU_seconds':0})
 raise
