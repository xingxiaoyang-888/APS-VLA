# Explicit control-only dependency injection for the one Spatial64 seed23 history.
# Original modules are compiled into private namespaces; production globals/files stay unchanged.
from pathlib import Path
from types import ModuleType,SimpleNamespace
import argparse,ast,copy,hashlib,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
VERSION='formal-spatial64s23-source-control-v1'
CANONICAL='scripts/ops/formal_spatial64s23_source_bridge_v1'
PRIVATE='.local/k64_seed23_bridges_20261020T1949/spatial/package'
BASE=Path(__file__).resolve().parent
BRIDGE_SHA='f3c8107c60269d931efae7744f2de2bb0207c6a40b40594a8941f96fc77420d1'
POLICY_SHA='b4d18e84600de25dc193149903492cdda16df11d76e35a9d702c14ca0054b557'
CANONICAL_MANIFEST='results/formal_main_v2/execution/spatial64seed23_source_control_v1_20261020T1949/development.json'
CPU_MANIFEST='.local/k64_seed23_bridges_20261020T1949/spatial/development.json'
MANIFEST=CANONICAL_MANIFEST if BASE.relative_to(R).as_posix()==CANONICAL else CPU_MANIFEST
MANIFEST_SHA='2a2b9687b078771548cbd3828ce08012d6bb536fdf06ec23a88995daadb94b8d'
METHODS=['A64_seed23','B64_seed23']
ORIGINAL={
'scripts/ops/formal_action_deployment_v1/gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a',
'scripts/ops/formal_action_deployment_v1/reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd',
'scripts/ops/formal_action_deployment_v1/consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034',
'scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89',
'scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571',
'scripts/ops/formal_asset_downstream_review.py':'6d9af87498c76cc71459d5441e66eff2a2bde9aa063479519a4d628f44a7d699'}
def require(ok,msg):
 if not ok:raise ValueError(VERSION+': '+msg)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def safe_path(rel):
 p=R/rel
 require(p.is_absolute() and str(p.relative_to(R))==rel and '..' not in Path(rel).parts,'canonical R path required')
 require(not any(x.is_symlink() for x in (p,*p.parents)),'symlink forbidden')
 return p

def closure():
 require(BASE.relative_to(R).as_posix() in (CANONICAL,PRIVATE),'unregistered control package location')
 files=dict(ORIGINAL)
 for name,pin in [('bridge_v2.py',BRIDGE_SHA),('policy_v1.json',POLICY_SHA)]:
  p=BASE/name;require(sha(p.read_bytes())==pin,'pinned package component differs');files[p.relative_to(R).as_posix()]=pin
 files[(BASE/'control.py').relative_to(R).as_posix()]=sha((BASE/'control.py').read_bytes())
 for rel,pin in files.items():require(sha(safe_path(rel).read_bytes())==pin,'control dependency changed:'+rel)
 return files

def descriptor():return {'version':VERSION,'files':closure(),'bridge_sha256':BRIDGE_SHA,'policy_sha256':POLICY_SHA,'scope':{'suite':'libero_spatial','tokens':64,'seed':23,'method_ids':METHODS,'stage':'development','trials':200},'failed_job_id':'3028522','successful_job_ids':['3024716', '3025205', '3043399', '3044479'],'all_pair_GPU_seconds':42480,'retained_failed_GPU_seconds':73,'new_scientific_authority':False}

class EvidenceAdapter:
 def __init__(self,ev):
  self.ev=ev;self.root=self.project=Path(getattr(ev,'project',getattr(ev,'root',''))).resolve();require(self.project==R,'exact R evidence required')
 def relative(self,rel):
  p=Path(rel);return p.relative_to(R).as_posix() if p.is_absolute() else p.as_posix()
 def path(self,rel):return safe_path(self.relative(rel))
 def watch(self,rel):return self.ev.watch(self.relative(rel))
 def read(self,rel):return self.ev.read(self.relative(rel))
 def unchanged(self):return self.ev.unchanged()

def watch_closure(ev):
 e=EvidenceAdapter(ev)
 for rel,pin in closure().items():require(e.watch(rel)==pin,'evidence source drift:'+rel)
 return e

def private_module(rel,pin,*,replacement=None,injections=None):
 path=safe_path(rel);raw=path.read_bytes();require(sha(raw)==pin,'pinned original differs:'+rel);text=raw.decode()
 if replacement:
  for old,new in replacement:
   require(text.count(old)==1,'private derivation target not unique');text=text.replace(old,new,1)
 m=ModuleType('_object23_explicit_'+path.stem+'_'+sha(text.encode())[:16]);m.__file__=str(path);m.__package__=''
 exec(compile(text,str(path)+'::<explicit_object23_control>','exec'),m.__dict__)
 for name,value in (injections or {}).items():m.__dict__[name]=value
 m._object23_derivation={'original':{'path':rel,'sha256':pin},'derived_sha256':sha(text.encode()),'private_namespace':True,'replacements':len(replacement or []),'original_files_changed':False}
 return m

def bridge(ev):
 watch_closure(ev);rel=(BASE/'bridge_v2.py').relative_to(R).as_posix();return private_module(rel,BRIDGE_SHA)

def source_auditor(ev):
 b=bridge(ev);facade=b.auditor(EvidenceAdapter(ev));original=facade.review_source_provenance
 def proof(parent,**kw):
  watch_closure(parent);out=original(parent,**kw)
  require(out.get('suite')=='libero_spatial','source suite differs')
  out['explicit_source_control']=descriptor();return out
 # Only this newly compiled derived instance is changed; the canonical original stays untouched.
 facade.review_source_provenance=proof;facade.derived.review_source_provenance=proof
 facade.job_identity=facade.original.job_identity
 return facade

def scope_args(args):
 require(vars(args)=={'stage':'development','source_inventory':'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','execution_manifest':MANIFEST,'output_relative':None,'freeze_directory':None,'profile_panel':None,'prior_review':None,'collection_review':None,'repair_record':None,'resume':False,'stop_after':None},'only exact first full Spatial64s23 development arguments')
 require(sha(safe_path(MANIFEST).read_bytes())==MANIFEST_SHA,'fixed scientific manifest differs')

def scope_invocation(inv):
 require(inv.get('stage')=='development' and inv.get('suite')=='libero_spatial' and inv.get('method_ids')==METHODS,'only paired Spatial64s23 development')
 require(inv.get('execution_manifest')==str(P/MANIFEST) and inv.get('execution_manifest_sha256')==MANIFEST_SHA,'manifest identity differs')
 require(inv.get('resume') is False and inv.get('prior_job_ids')==[] and inv.get('prior_review') is None and inv.get('stop_after') is None,'no partial, retry, or resumed scope')
 require(inv.get('source_provenance',{}).get('explicit_source_control')==descriptor(),'explicit source control proof missing/different')
 flags=inv.get('argv',[]);require('--sealed-final' not in flags and '--release' not in flags and '--stop-after' not in flags,'forbidden final or prefix')

def control_modules(ev):
 b=bridge(ev);factory,planner=b.control_modules(EvidenceAdapter(ev))
 factory.source_review_module=source_auditor;planner.provenance_helper=source_auditor
 old_plan=planner.plan
 def plan(args,state,*,project=R,helper=None):
  scope_args(args);require(Path(project).resolve()==R and helper in (None,factory),'explicit root and private factory required')
  out=old_plan(args,copy.deepcopy(state),project=R,helper=factory);scope_invocation(out['invocation']);return out
 planner.plan=plan
 old_main=factory.main
 def bounded_main(argv=None):
  prefix=['--project-root',str(R),'development','--suite','libero_spatial','--methods',*METHODS,'--source-inventory','results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','--output']
  require(type(argv) is list and len(argv)==len(prefix)+1 and argv[:-1]==prefix,'factory only exact paired Object development argv')
  rel=argv[-1];require(type(rel) is str and rel.endswith('.json') and (rel.startswith('results/formal_main_v2/execution/') or rel.startswith('.local/k64_seed23_bridges_20261020T1949/spatial/')),'factory output scope differs')
  safe_path(rel);return old_main(argv)
 factory.main=bounded_main
 return factory,planner

GATEWAY='scripts/ops/formal_action_deployment_v1/gateway.py'
REVIEWER='scripts/ops/formal_action_deployment_v1/reviewer.py'
CONSUMER='scripts/ops/formal_action_deployment_v1/consumer.py'

def gateway_module():
 # Original RUNNING-controller capacity gate intentionally unchanged; no post-training submission authority here.
 # Sole FrozenPlan operational substitution: a private source-bound planner.
 changes=[('def source_files(root):return {Path(__file__).resolve().relative_to(root).as_posix():sha(Path(__file__).read_bytes())}',
           'def source_files(root):\n require(Path(root).resolve()==R,"exact source closure root required");return _object23_closure()'),
          ("  planner=load(self.root/PLANNER,PLANNER_SHA,'_downstream0809_original_pure_planner')",'  _,planner=_object23_control(self.e)')]
 g=private_module(GATEWAY,ORIGINAL[GATEWAY],replacement=changes,injections={'_object23_closure':closure,'_object23_control':control_modules})
 original_validate=g.validate_authorization
 def validate(root,ref):
  require(Path(root).resolve()==R,'exact control root');raw=g.Evidence(root).ref(ref)
  require(raw.get('explicit_source_control')==descriptor(),'root authorization must bind source bridge closure')
  scope_args(SimpleNamespace(**raw.get('plan_arguments',{})))
  a,e,p,s,prepared=original_validate(root,ref);scope_invocation(p['invocation']);scope_invocation(s['invocation'])
  require(a['gateway_files']==closure(),'complete gateway source closure required')
  ready=e.ref(a['runtime_readiness'])
  for key in ('root_review','independent_review'):
   review=e.ref(ready[key]);require(review.get('explicit_source_control')==descriptor(),'true per-plan readiness must bind exact bridge: '+key)
  return a,e,p,s,prepared
 g.validate_authorization=validate
 return g

def reviewer_module(ev):
 watch_closure(ev)
 old='    scheduler = load(evidence, OLD_SCHEDULER, PINNED[OLD_SCHEDULER])\n    helper = load(evidence, OLD_HELPER, PINNED[OLD_HELPER])'
 m=private_module(REVIEWER,ORIGINAL[REVIEWER],replacement=[(old,'    helper, scheduler = _object23_control(evidence)')],injections={'_object23_control':control_modules})
 baseline=m.review
 def review(project,**kw):
  require(Path(project).resolve()==R,'exact terminal root')
  job=kw.get('job',{});require(job.get('suite')=='libero_spatial' and job.get('mode')=='development' and job.get('method_ids')==METHODS,'terminal only exact pair/development')
  e=m.Evidence(project);watch_closure(e);inv=e.read_ref(kw['invocation_ref']);scope_invocation(inv)
  result=baseline(project,**kw)
  require(result['source_provenance']['explicit_source_control']==descriptor(),'terminal source bridge mismatch')
  result['explicit_source_control']=descriptor()
  result['audit_source_sha256'].update(closure());result['evidence_sha256'].update(closure())
  e.unchanged();return result
 m.review=review
 return m

def consumer_module(ev):
 watch_closure(ev);m=private_module(CONSUMER,ORIGINAL[CONSUMER]);m._reviewer=reviewer_module;original=m.review_downstream_output
 def consume(evidence,reference,*,expected_stage,suite,run_root=None,require_complete=True):
  require(expected_stage=='development' and suite=='libero_spatial' and require_complete is True,'bridge consumer only full200 Object development')
  validator=reviewer_module(evidence);validator.ref(reference)
  require(reference['path'].startswith('results/formal_main_v2/downstream_reviews/'),'immutable downstream root review required')
  require(evidence.watch(reference['path'])==reference['sha256'],'root review SHA changed')
  watch_closure(evidence);saved=evidence.read(reference['path'])
  require(saved.get('explicit_source_control')==descriptor(),'report lacks exact control binding')
  require(saved.get('source_provenance',{}).get('explicit_source_control')==descriptor(),'saved source lacks bridge')
  return original(evidence,reference,expected_stage=expected_stage,suite=suite,run_root=run_root,require_complete=require_complete)
 m.review_downstream_output=consume
 return m

def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--control-sha256',required=True);p.add_argument('--authorization',required=True);p.add_argument('--authorization-sha256',required=True);p.add_argument('--submit',action='store_true');p.add_argument('--root-reviewed-submit',action='store_true');a=p.parse_args(argv)
 require(BASE.relative_to(R).as_posix()==CANONICAL and Path.cwd().resolve()==R,'private candidate cannot operate production gateway')
 require(sha(Path(__file__).read_bytes())==a.control_sha256,'control entry SHA differs');require(a.submit==a.root_reviewed_submit,'explicit dual root submit flags')
 g=gateway_module();ref={'path':a.authorization,'sha256':a.authorization_sha256};auth,e,plan,scientific,prepared=g.validate_authorization(R,ref)
 c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'_object23_original_controller')
 runner=g.Gateway(R,c,c.Slurm(),g.FrozenPlan(R,auth,e,plan,scientific,prepared),g.NativeIO(R),auth,ref,e)
 print(json.dumps(runner.run(submit=a.submit),sort_keys=True,ensure_ascii=False))
if __name__=='__main__':main()
