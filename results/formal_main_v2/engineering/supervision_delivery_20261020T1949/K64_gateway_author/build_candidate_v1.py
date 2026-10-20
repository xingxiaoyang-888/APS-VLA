'''Build only the two explicit post-training64s23 development gateway candidates.
Requires actual published canonical controls and exact published plans; no placeholders.
This builder never runs a gateway or writes production/state/Git/Slurm.
'''
from pathlib import Path
import ast,difflib,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/collect_terminal_20261020T1949/development_gateway'
BASE='scripts/ops/formal_action_deployment_posttraining_v1/gateway.py'
BASE_SHA='4a11a62e817cd96523cd8f06aa0c3c71e12208f1b3a6b487799160915e59ec83'
SUITES=('libero_spatial','libero_object')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:f.write(raw)
def main():
 inputs=json.loads((D/'canonical_inputs.json').read_text());assert set(inputs)==set(SUITES)
 assert sha(R/BASE)==BASE_SHA
 allowed={}
 for suite in SUITES:
  row=inputs[suite]
  for label in ('control','effective_plan','scientific_plan'):
   ref=row[label];assert set(ref)=={'path','sha256'} and sha(R/ref['path'])==ref['sha256']
  assert row['control']['path']==f'scripts/ops/formal_{suite.removeprefix("libero_")}64s23_source_bridge_v1/control.py'
  plan=json.loads((R/row['effective_plan']['path']).read_text());scientific=json.loads((R/row['scientific_plan']['path']).read_text())
  for p in (plan,scientific):
   assert p['invocation']['suite']==suite and p['invocation']['stage']=='development' and p['invocation']['method_ids']==['A64_seed23','B64_seed23']
   assert p['invocation']['resume'] is False and p['invocation']['prior_job_ids']==[] and p['invocation']['prior_review'] is None and p['invocation']['stop_after'] is None
  allowed[suite]={**row['effective_plan'],'plan_sha256':plan['plan_sha256'],'scientific_plan':row['scientific_plan'],'method_ids':['A64_seed23','B64_seed23'],'control':row['control']}
 text=(R/BASE).read_text();original=text
 def replace(old,new):
  nonlocal text
  assert text.count(old)==1,old[:150];text=text.replace(old,new,1)
 replace("VERSION='formal-downstream-server-gateway-v2-completed-training-collect'","VERSION='formal-downstream-server-gateway-v3-completed-training-k64s23-development'")
 tree=ast.parse(text)
 node=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COMPLETED_COLLECTION_PLANS' for t in x.targets))
 replace(ast.get_source_segment(text,node),'SCOPED_DEVELOPMENT_PLANS = '+repr(allowed))
 replace("def source_files(root):return {Path(__file__).resolve().relative_to(root).as_posix():sha(Path(__file__).read_bytes())}",'''def source_files(root):
 require(Path(root).resolve()==R,'exact scoped development control root required')
 files={Path(__file__).resolve().relative_to(root).as_posix():sha(Path(__file__).read_bytes()),COMPLETED_COLLECT_BASE['path']:COMPLETED_COLLECT_BASE['sha256']}
 for suite,allowed in SCOPED_DEVELOPMENT_PLANS.items():
  control=load(R/allowed['control']['path'],allowed['control']['sha256'],'_completed64_source_closure_'+suite)
  for rel,pin in control.closure().items():
   require(rel not in files or files[rel]==pin,'source bridge closure conflict');files[rel]=pin
 for rel,pin in files.items():require(stable(no_links(R/rel))['sha256']==pin,'scoped gateway source closure changed')
 return files''')
 replace(' e=Evidence(root);a=e.ref(ref)\n'," e=Evidence(root);a=e.ref(ref)\n _exact_development_authorization(a)\n")
 replace(' return a,e,plan,scientific,prepared\n', ''' control=_exact_development_plan(root,a,plan,scientific)
 require(a.get('explicit_source_control')==control.descriptor(),'authorization omits exact pair source bridge')
 for field in ('root_review','independent_review'):
  require(e.ref(ready[field]).get('explicit_source_control')==control.descriptor(),'true runtime readiness omits exact pair source bridge: '+field)
 return a,e,plan,scientific,prepared
''')
 replace("  plan=self.plan;inv=plan['invocation'];e=self.e\n","  plan=self.plan;inv=plan['invocation'];e=self.e\n  _exact_development_plan(self.root,self.a,plan,self.scientific)\n")
 replace("  planner=load(self.root/PLANNER,PLANNER_SHA,'_downstream0809_original_pure_planner')","  _,planner=_exact_development_control(self.root,inv).control_modules(e)")
 replace('def completed_training_collect_gate(c,state,snap,a,plan,cpus):','def completed_training_development_gate(c,state,snap,a,plan,cpus):')
 replace(" inv=plan.get('invocation',{});suite=inv.get('suite');allowed=COMPLETED_COLLECTION_PLANS.get(suite)"," inv=plan.get('invocation',{});suite=inv.get('suite');allowed=SCOPED_DEVELOPMENT_PLANS.get(suite)")
 replace(" require(inv.get('stage')=='collect' and allowed is not None,'completed controller only permits two exact Spatial/Object collect plans')"," require(inv.get('stage')=='development' and allowed is not None and inv.get('method_ids')==allowed['method_ids'],'completed controller only permits two exact Spatial/Object64s23 development plans')\n _exact_development_authorization(a);_exact_development_control(R,inv)")
 replace("'completed-controller exact collect plan reference differs'","'completed-controller exact development plan reference differs'")
 replace("'completed-training collect bridge cannot authorize final evaluation'","'completed-training development bridge cannot authorize final evaluation'")
 replace("'published exact collect plan differs'","'published exact development plan differs'")
 replace("kind='completed_training_exact_collect_capacity_gate'","kind='completed_training_exact_k64s23_development_capacity_gate'")
 replace('exact_collection_plan=plan_ref','exact_development_plan=plan_ref')
 replace("caps['completed_training_collect_gate']=completed_training_collect_gate(c,state,snap,a,plan,cpus)","caps['completed_training_development_gate']=completed_training_development_gate(c,state,snap,a,plan,cpus)")
 helper=r'''
# Explicit control-only dependency injection for these two already authorized pairs.
COMPLETED_COLLECT_BASE={'path':'scripts/ops/formal_action_deployment_posttraining_v1/gateway.py','sha256':'4a11a62e817cd96523cd8f06aa0c3c71e12208f1b3a6b487799160915e59ec83'}
def _exact_development_authorization(a):
 matches=[v for v in SCOPED_DEVELOPMENT_PLANS.values() if a.get('plan')=={k:v[k] for k in ('path','sha256')}]
 require(len(matches)==1,'only two exact development plan references; no target-plan I/O before this check')
 allowed=matches[0]
 require(a.get('scientific_plan')==allowed['scientific_plan'],'exact scientific plan reference differs')
 args=a.get('plan_arguments',{})
 require(args.get('stage')=='development' and args.get('resume') is False and args.get('prior_review') is None and args.get('repair_record') is None and args.get('stop_after') is None,'only first complete fixed development request')
 return allowed

def _exact_development_control(root,inv):
 require(Path(root).resolve()==R,'exact server root')
 allowed=SCOPED_DEVELOPMENT_PLANS.get(inv.get('suite'))
 require(allowed is not None and inv.get('stage')=='development' and inv.get('method_ids')==allowed['method_ids'],'only paired Spatial/Object64s23 development')
 require(inv.get('resume') is False and inv.get('prior_job_ids')==[] and inv.get('prior_review') is None and inv.get('stop_after') is None,'no partial/retry/resume scope')
 control=load(R/allowed['control']['path'],allowed['control']['sha256'],'_completed64_source_control_'+inv['suite'])
 control.scope_invocation(inv)
 return control

def _exact_development_plan(root,a,plan,scientific):
 allowed=_exact_development_authorization(a)
 require(plan.get('plan_sha256')==allowed['plan_sha256'],'exact effective plan content differs')
 control=_exact_development_control(root,plan.get('invocation',{}))
 control.scope_args(SimpleNamespace(**a['plan_arguments']))
 control.scope_invocation(scientific.get('invocation',{}))
 require(scientific.get('invocation',{}).get('suite')==plan['invocation']['suite'],'scientific/effective source bridge suite differs')
 return control
'''
 replace("if __name__=='__main__':main()",helper+"\nif __name__=='__main__':main()")
 compile(text,'bounded-development-gateway','exec',dont_inherit=True)
 oldast={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(original).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
 newast={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(text).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
 changed=[x for x in oldast if oldast[x]!=newast.get(x)]
 assert set(changed)=={'source_files','validate_authorization','FrozenPlan','capacity_gate','completed_training_collect_gate'}
 O=D/'revision01';O.mkdir(exist_ok=False);write(O/'gateway.py',text)
 write(O/'source.diff',''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile=BASE,tofile='scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py')))
 report={'status':'candidate_generated_not_executed','baseline':{'path':BASE,'sha256':BASE_SHA},'canonical_inputs':{'path':str((D/'canonical_inputs.json').relative_to(R)),'sha256':sha(D/'canonical_inputs.json')},'new_source':{'path':str((O/'gateway.py').relative_to(R)),'sha256':sha(O/'gateway.py')},'expected_canonical_path':'scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py','AST_unchanged_original_definitions':[x for x in oldast if x not in changed],'AST_changed_original_definitions':changed,'Gateway_lifecycle_AST_unchanged':oldast['Gateway']==newast['Gateway'],'NativeIO_AST_unchanged':oldast['NativeIO']==newast['NativeIO'],'candidate_not_published':True,'actual_P_readiness_not_done':True,'root_authorization_created':False,'new_GPU_submissions':0}
 write(O/'source_derivation.json',json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
