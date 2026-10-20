from pathlib import Path
from types import SimpleNamespace,ModuleType,CodeType
import ast,argparse,copy,hashlib,json,os,sys,time,traceback,difflib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).parent;OUT=D/'attempt02';sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
CANDIDATE=R/'.local/object_bridge_production_20261020T1644/revision02/package/control.py';PIN='f869c673992cc881f849e4d86c56925e2b609028397efbeefe6524f0b684157b';CHECKS=[];READS={};NEG=[]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('Independent CPU only; no process/network/Slurm')
 if event=='open':
  name,mode,flags=args
  if isinstance(name,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(name));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts):raise RuntimeError('Sealed/weight payload access forbidden')
   if p.suffix.lower() in ('.pt','.pth','.bin','.safetensors','.pkl','.pickle','.ckpt','.init','.pruned_init'):raise RuntimeError('Payload access forbidden')
   writing=isinstance(mode,str) and any(x in mode for x in 'wax+') or isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
   if writing and OUT not in p.parents:raise RuntimeError('Private audit output only:'+str(p))
sys.addaudithook(guard)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,value,detail=None):
 CHECKS.append(dict(name=name,passed=bool(value),detail=detail))
 if not value:raise AssertionError(name)
def reject(name,fn,contains=None):
 try:fn()
 except (ValueError,KeyError,TypeError,RuntimeError,AssertionError) as e:
  if contains is not None:check(name+' reason',contains in str(e),str(e))
  NEG.append(dict(name=name,error_type=type(e).__name__,error=str(e)));check(name,True);return
 raise AssertionError('Unexpected admission:'+name)
def write(name,v):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);raw=v if isinstance(v,bytes) else (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()}
def load(p,pin):
 p=Path(p);raw=p.read_bytes();check('load pin:'+p.name,hashlib.sha256(raw).hexdigest()==pin);READS[p.relative_to(R).as_posix()]=pin;m=ModuleType('ind_'+p.stem+'_'+pin[:12]);m.__file__=str(p);exec(compile(raw,str(p),'exec'),m.__dict__);return m
class E:
 def __init__(self):self.root=self.project=R;self.files={}
 def path(self,p):p=Path(p);return p if p.is_absolute() else R/p
 def watch(self,p):
  q=self.path(p);h=sha(q);k=q.relative_to(R).as_posix();check('stable evidence:'+k,k not in self.files or self.files[k]==h);self.files[k]=h;return h
 def read(self,p):self.watch(p);return json.loads(self.path(p).read_bytes())
 def unchanged(self):
  for k,h in self.files.items():check('unchanged:'+k,sha(R/k)==h)
def semantic(fn):
 def sem(co):return (co.co_code,co.co_names,co.co_varnames,co.co_argcount,co.co_posonlyargcount,co.co_kwonlyargcount,tuple(sem(x) if isinstance(x,CodeType) else x for x in co.co_consts))
 return sem(fn.__code__)
def same_functions(a,b,exclude):
 names=[]
 for name,value in vars(b).items():
  if callable(value) and hasattr(value,'__code__') and name not in exclude:
   check('unchanged code:'+b.__name__+'.'+name,semantic(getattr(a,name))==semantic(value));names.append(name)
 return names

def main():
 OUT.mkdir(exist_ok=False);t=time.monotonic();c=load(CANDIDATE,PIN);ev=E();closure=c.closure();write('reviewed_control.py',CANDIDATE.read_bytes());write('closure.json',closure)
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes());check('173 exact count',len(inventory['files'])==173)
 for root in [R,S]:
  for rel,pin in inventory['files'].items():check('173 before:'+str(root)+':'+rel,sha(root/rel)==pin)
 check('closure control pinned',closure[CANDIDATE.relative_to(R).as_posix()]==PIN and len(closure)==9)
 for rel,pin in closure.items():check('exact original or explicit dependency:'+rel,sha(R/rel)==pin)
 check('descriptor exact scope',c.descriptor()['scope']==dict(suite='libero_object',tokens=256,seed=23,method_ids=['A256_seed23','B256_seed23'],stage='development',trials=200))
 check('retained cost',c.descriptor()['all_pair_GPU_seconds']==58917 and c.descriptor()['retained_failed_GPU_seconds']==84)
 reject('private entry cannot operate production',lambda:c.main(['--control-sha256',PIN,'--authorization','fake.json','--authorization-sha256','0'*64,'--submit','--root-reviewed-submit']),contains='private candidate')
 reject('outside evidence root',lambda:c.EvidenceAdapter(SimpleNamespace(project=R.parent)))
 for rel in ['../x','/tmp/x','a/../x','./x','a//x']:
  reject('noncanonical path:'+rel,lambda rel=rel:c.safe_path(rel))
 oldbase=c.BASE
 try:
  c.BASE=D;reject('unregistered relocation',c.closure)
 finally:c.BASE=oldbase
 snapshot=R/'.local/object256s23_consumer_candidate_20261020T1530/runtime_check01/author_state_snapshot.json';check('immutable state snapshot pin',sha(snapshot)=='303d0e953ef966fa53787f46b19152f697c2d211640a7f3f8813754776d05430');state=json.loads(snapshot.read_bytes());base=copy.deepcopy(state)
 args=json.loads((R/'.local/object256s23_consumer_candidate_20261020T1530/runtime_check01/plan_arguments.json').read_bytes());write('input_snapshot_reference.json',{'path':snapshot.relative_to(R).as_posix(),'sha256':sha(snapshot),'fresh_capacity_authorization':False});write('plan_arguments.json',args)
 factory,planner=c.control_modules(ev)
 for key,values in {'stage':['final','collect','full','components'], 'resume':[True], 'stop_after':[1], 'execution_manifest':['other.json'], 'source_inventory':['other.json'],'output_relative':['results/other'],'prior_review':['results/prior.json']}.items():
  for value in values:
   bad=dict(args);bad[key]=value;reject('planner scope '+key+'='+str(value),lambda bad=bad:planner.plan(SimpleNamespace(**bad),state,project=R))
 for argv in [None,[],['freeze'],['--project-root',str(R),'final'],['--project-root',str(R),'development','--suite','libero_goal']]:reject('factory scope '+str(argv),lambda argv=argv:factory.main(argv))
 science=planner.plan(SimpleNamespace(**args),state,project=R);check('planner state not mutated',state==base);sciref=write('scientific_plan.json',science)
 sc=copy.deepcopy(science['invocation']);c.scope_invocation(sc);check('no future deployment',sc['method_ids']==c.METHODS)
 method_manifest=json.loads((R/c.MANIFEST).read_bytes());check('manifest SHA fixed',sha(R/c.MANIFEST)==c.MANIFEST_SHA);check('environment unchanged',method_manifest['environment']==dict(action_chunk=8,environment_seed=0,max_steps=280,runtime_seed=17,wait_steps=10))
 check('paired methods and256',[(x['identity']['method_id'],x['identity']['training_seed'],x['identity']['visual_tokens'],x['identity']['future_head_deployed']) for x in method_manifest['methods']]==[(x,23,256,False) for x in c.METHODS])
 panel=json.loads((R/method_manifest['development_panel']).read_bytes());check('panel exact SHA',sha(R/method_manifest['development_panel'])==method_manifest['development_panel_sha256']);write('panel_metadata.json',panel)
 source=sc['source_provenance'];check('explicit source proof',source['explicit_source_control']==c.descriptor());check('source startup cost',source['startup_failure_source_bridge']['all_pair_GPU_seconds']==58917 and source['startup_failure_source_bridge']['retained_failed_GPU_seconds']==84)
 for mid in c.METHODS:check('all three allocations retained:'+mid,set(source['method_bindings'][mid]['registered_training_job_ids'])=={'3028460','3039258','3042627'})
 for key,values in {'stage':['final','collect'], 'suite':['libero_goal'], 'method_ids':[['A256_seed23'],['B256_seed23','A256_seed23'],['A256_seed41','B256_seed41']], 'execution_manifest_sha256':['0'*64], 'resume':[True], 'prior_job_ids':[['3028460']], 'prior_review':[{}],'stop_after':[1]}.items():
  for value in values:
   bad=copy.deepcopy(sc);bad[key]=value;reject('invocation '+key+'='+str(value),lambda bad=bad:c.scope_invocation(bad))
 for flag in ['--sealed-final','--release','--stop-after']:
  bad=copy.deepcopy(sc);bad['argv'].append(flag);reject('forbidden argv:'+flag,lambda bad=bad:c.scope_invocation(bad))
 for key in list(c.descriptor()):
  bad=copy.deepcopy(sc);bad['source_provenance']['explicit_source_control'].pop(key);reject('missing descriptor:'+key,lambda bad=bad:c.scope_invocation(bad))
 g=c.gateway_module();gb=load(R/c.GATEWAY,c.ORIGINAL[c.GATEWAY]);function_names=same_functions(g,gb,{'source_files','validate_authorization'})
 for cls in ['NativeIO','Gateway','Evidence']:
  for name,fn in vars(getattr(gb,cls)).items():
   if callable(fn) and hasattr(fn,'__code__'):check('unchanged class:'+cls+'.'+name,semantic(getattr(getattr(g,cls),name))==semantic(fn))
 check('gateway exact derived closure',g.source_files(R)==closure)
 expected=(R/c.GATEWAY).read_text().replace("  planner=load(self.root/PLANNER,PLANNER_SHA,'_downstream0809_original_pure_planner')",'  _,planner=_object23_control(self.e)',1)
 n1=next(n for n in ast.parse(expected).body if isinstance(n,ast.ClassDef) and n.name=='FrozenPlan');n2=ast.parse((R/c.GATEWAY).read_text());write('gateway_allowed_derivation.json',{'only_FrozenPlan_prepare_change':'replace exact private planner loader with explicit source-bound pair','source_files_changed_to_closure':True,'unchanged_top_level_functions':function_names})
 pre='scripts/ops/formal_action_deployment_v1/';ct=load(R/(pre+'contract.py'),'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19');rt=load(R/(pre+'runtime_scope.py'),'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53');runtime=rt.make_contract(project_root=R,source_root=S,suite='libero_object',stage='development')
 files={p:sha(R/p) for p in ct.EXPECTED_NEW_FILES};files[ct.ACTION_ADAPTER]=ct.ACTION_SHA
 action=dict(schema=ct.SCHEMA,kind='formal_action_execution_contract',version=ct.VERSION,status='candidate_pending_root_readiness',scientific_settings_changed=False,final_evaluation_enabled=False,files=files,runtime_contract=runtime,GPU_acceptance=ct.GPU_REFS,source_inventory={'path':ct.INVENTORY,'sha256':ct.INVENTORY_SHA},transition=None);aref=write('execution_contract.json',action)
 effective=ct.effective_plan(science,scientific_plan_ref=sciref,execution_contract_ref=aref,execution_contract=action);eref=write('effective_plan.json',effective)
 prepared={**effective['invocation'],'registered_utc':'2026-10-20T16:44:00+00:00','plan_sha256':effective['plan_sha256'],'runtime_readiness':None};pref=write('prepared_CPU_fixture_not_authorization.json',prepared)
 auth={'scientific_plan':sciref,'plan_arguments':args,'runtime_readiness':None,'prepared_invocation':pref};bundle=g.FrozenPlan(R,auth,g.Evidence(R),effective,science,prepared).prepare(copy.deepcopy(state));check('actual FrozenPlan exact rebuild',bundle['plan']==effective and bundle['invocation']==prepared and bundle['invocation_bytes']==(R/pref['path']).read_bytes())
 reject('original unbridged prepare fails',lambda:gb.FrozenPlan(R,auth,gb.Evidence(R),effective,science,prepared).prepare(copy.deepcopy(state)),contains='metadata history')
 authref=write('missing_root_authority_fixture.json',{'explicit_source_control':c.descriptor(),'plan_arguments':args});reject('bridge binding alone not root authorization',lambda:g.validate_authorization(R,authref),contains='typed root authorization')
 missing=copy.deepcopy(science);missing['invocation']['source_provenance'].pop('explicit_source_control');reject('missing proof not admitted',lambda:c.scope_invocation(missing['invocation']))
 oldwrapper=load(P/'scripts/server/run_formal_downstream.py','f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24');check('actual P old metadata wrapper',oldwrapper.verify(sc)['mode']=='evaluate' if isinstance(oldwrapper.verify(sc),dict) else oldwrapper.verify(sc).mode=='evaluate')
 wrapper=load(P/(pre+'wrapper.py'),'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33');reject('actual P action wrapper lacks real readiness',lambda:wrapper.verify(effective['invocation'],project=P),contains='readiness')
 reviewer=c.reviewer_module(ev);rb=load(R/c.REVIEWER,c.ORIGINAL[c.REVIEWER]);same_functions(reviewer,rb,{'review'})
 se=reviewer.Evidence(R);old=reviewer.load(se,reviewer.OLD_REVIEW,reviewer.PINNED[reviewer.OLD_REVIEW]);h,sch=c.control_modules(se);pi=effective['invocation'];job={k:pi[k] for k in ['stage_key','suite','method_ids','run_root','source_sha256','adapter_sha256','execution_manifest_sha256']};job.update(mode='development',source_provenance_sha256=sch.signature(pi['source_provenance']),job_id='CPU_ONLY_NOT_SLURM',status='NOT_RUN',gpus=0)
 value,_=reviewer.science_context(se,old,sch,h,job,pi,state['registered_jobs'],science,action,lambda *a,**k:(_ for _ in ()).throw(AssertionError('No downstream reference in first stage')));check('actual terminal source chain same proof',value['source_provenance']==source)
 # Invoke the actual terminal top-level review far enough to prove its helper reload
 # reaches the explicit bridge. The marker prevents any raw trial/result admission.
 class WiringMarker(RuntimeError):pass
 def marker(evidence):raise WiringMarker('actual terminal helper injection reached')
 actual_control=reviewer._object23_control;reviewer._object23_control=marker
 wirejob=dict(job,invocation=pref['path'],invocation_sha256=pref['sha256'],experiment='formal_main_v2')
 try:reject('actual reviewer injection reached',lambda:reviewer.review(R,job=wirejob,invocation_ref=pref,pull_ref={'path':'results/formal_main_v2/CPU_no_pull.json','sha256':'0'*64},registered_jobs=[wirejob],expected_contract_ref=aref),contains='actual terminal helper injection reached')
 finally:reviewer._object23_control=actual_control
 for mode in ['final','collect','full','components']:reject('terminal scope:'+mode,lambda mode=mode:reviewer.review(R,job=dict(job,mode=mode)))
 consumer=c.consumer_module(ev);check('consumer direct same reviewer binding',consumer._reviewer is c.reviewer_module)
 cb=load(R/c.CONSUMER,c.ORIGINAL[c.CONSUMER]);same_functions(consumer,cb,{'_reviewer','review_downstream_output'})
 for stage,suite,full in [('final','libero_object',True),('development','libero_goal',True),('development','libero_object',False)]:reject('consumer scope:'+str((stage,suite,full)),lambda stage=stage,suite=suite,full=full:consumer.review_downstream_output(ev,{},expected_stage=stage,suite=suite,require_complete=full))
 noauth=write('missing_consumer_binding_fixture.json',dict(stage='development',source_provenance={'suite':'libero_object'}));reject('consumer missing explicit source binding',lambda:consumer.review_downstream_output(ev,noauth,expected_stage='development',suite='libero_object'),contains='binding')
 for root in [R,S]:
  for rel,pin in inventory['files'].items():check('173 after:'+str(root)+':'+rel,sha(root/rel)==pin)
 ev.unchanged();se.unchanged();check('state input remains same',sha(snapshot)=='303d0e953ef966fa53787f46b19152f697c2d211640a7f3f8813754776d05430');write('negative_tests.json',NEG);write('read_evidence.json',{'independent':ev.files,'terminal_source':se.files,'loaded':READS})
 report=dict(status='passed_CPU_candidate_pending_root_canonical_publication_and_real_readiness',candidate={'path':CANDIDATE.relative_to(R).as_posix(),'sha256':PIN},files=closure,checks=len(CHECKS),negative_cases=len(NEG),results=CHECKS,blockers=[],deployment_prerequisites=['Root publishes exact three package files at canonical path; rebuild all source proofs/plans under canonical paths','Root performs actual P wrapper/readiness/selected checkpoint verification and independent postpublication review','Original complete typed root authorization, dedicated reservation, live capacity/lease/CAS/pending/duplicate guards still required'],actual_FrozenPlan_rebuilt=True,actual_terminal_source_chain_rebuilt=True,terminal_raw_trial_reviewed=False,actual_GPU=False,production_published=False,science_trials_accepted=0,Slurm_calls=0,weights_or_sealed_values_read=False,root_state_or_Git_writes=False,all_pair_GPU_seconds=58917,failed_GPU_seconds_retained=84,CPU_wall_seconds=time.monotonic()-t)
 write('independent_review.json',report);print(json.dumps({k:report[k] for k in ['status','checks','negative_cases','candidate','blockers','CPU_wall_seconds']},sort_keys=True))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if OUT.exists():write('failure.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':CHECKS,'negatives':NEG,'GPU_runs':0,'Slurm_calls':0})
  raise
