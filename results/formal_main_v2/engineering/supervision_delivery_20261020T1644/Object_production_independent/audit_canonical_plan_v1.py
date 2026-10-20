from pathlib import Path
from types import ModuleType,SimpleNamespace
import sys,os,json,hashlib,copy,time,traceback,collections
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).parent;OUT=D/'plan';sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')];CHECKS=[]
def guard(event,args):
 if event in ('subprocess.Popen','socket.connect','os.system'):raise RuntimeError('CPU metadata only')
 if event=='open':
  n,m,flags=args
  if isinstance(n,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(n));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix in ('.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.init','.pruned_init'):raise RuntimeError('No weights or final payload')
   writing=isinstance(m,str) and any(x in m for x in 'wax+') or isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC))
   if writing and OUT not in p.parents:raise RuntimeError('Own private output only')
sys.addaudithook(guard)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,ok):
 CHECKS.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
class E:
 root=project=R
 def __init__(self):self.files={}
 def path(self,p):p=Path(p);return p if p.is_absolute() else R/p
 def watch(self,p):
  q=self.path(p);k=q.relative_to(R).as_posix();h=sha(q);check('stable:'+k,k not in self.files or self.files[k]==h);self.files[k]=h;return h
 def read(self,p):self.watch(p);return json.loads(self.path(p).read_bytes())
 def ref(self,r):check('exact ref',set(r)=={'path','sha256'});check('ref SHA:'+r['path'],self.watch(r['path'])==r['sha256']);return self.read(r['path'])
 def unchanged(self):
  for k,h in self.files.items():check('unchanged:'+k,sha(R/k)==h)
def load(p,pin):
 check('source:'+str(p),sha(p)==pin);m=ModuleType('plan_ind_'+p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def write(name,v):
 p=OUT/name
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def main():
 OUT.mkdir(exist_ok=False);t=time.monotonic();ev=E();c=load(R/'scripts/ops/formal_object256s23_source_bridge_v1/control.py','09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f')
 bundle_ref={'path':'.local/object_bridge_production_20261020T1644/production_candidates01/plan_bundle.json','sha256':'52368d3b96e72ec4deb601949a7133579327818a6a7e963ca4657892bb36dfad'};bundle=ev.ref(bundle_ref)
 pubref={'path':'results/formal_main_v2/preflight/heartbeat_20261021T0044/Object_static_plan_publication.json','sha256':'06a98ba334a64761e795d0c6fea74feae5e769571f1c4c0bea1473812fac2a9a'};pub=ev.ref(pubref)
 for row in bundle['canonical_files']:
  check('canonical exact source/dest '+row['destination'],ev.watch(row['source'])==ev.watch(row['destination'])==row['sha256']);check('canonical size '+row['destination'],(R/row['destination']).stat().st_size==row['bytes'])
 science=ev.ref(bundle['scientific_plan']);effective=ev.ref(bundle['effective_plan']);action=ev.ref(bundle['execution_contract']);args=ev.ref(bundle['plan_arguments']);c.scope_args(SimpleNamespace(**args));c.scope_invocation(science['invocation']);c.scope_invocation(effective['invocation'])
 check('author science equals independently rebuilt bytes',bundle['scientific_plan']['sha256']==sha(D/'canonical/scientific_plan.json')=='5628402ad34bb0479c49f300bd5cbd9db94a4af52a17b56418e7ab22c393340c')
 snapshotref={k:bundle['root_snapshot'][k] for k in ('path','sha256')};state=ev.ref(snapshotref);before=copy.deepcopy(state);f,pl=c.control_modules(ev);rebuilt=pl.plan(SimpleNamespace(**args),state,project=R)
 check('independent actual current canonical plan rebuilt',rebuilt==science and state==before)
 ct=load(R/'scripts/ops/formal_action_deployment_v1/contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19')
 ct.validate_effective(science,effective,scientific_plan_ref=bundle['scientific_plan'],execution_contract_ref=bundle['execution_contract'],execution_contract=action)
 check('exact effective plan hash',effective['plan_sha256']==bundle['plan_sha256']=='2c28c6def19c9f4abc98dbe10f3435ec712791786a2e54b48c7f4feec28070f0')
 manifest=ev.ref(bundle['manifest']);panel=ev.ref({'path':manifest['development_panel'],'sha256':manifest['development_panel_sha256']});counts=collections.Counter(x['task_id'] for x in panel['states']);check('ten fixed tasks by ten dev initial states',counts=={i:10 for i in range(10)});check('100 unique existing development trials',len({x['trial_id'] for x in panel['states']})==len(panel['states'])==100 and panel['split']=='development')
 check('source closure canonical exact',bundle['explicit_source_control']==c.descriptor()==science['invocation']['source_provenance']['explicit_source_control']);check('two matched256seed23 methods',bundle['method_ids']==c.METHODS and bundle['budget']==256 and bundle['seed']==23)
 check('all failure cost preserved',bundle['all_pair_GPU_seconds']==58917 and bundle['failed_GPU_seconds_retained']==84)
 check('no formal prior development in snapshot',not any(j.get('experiment')=='formal_main_v2' and j.get('mode')=='development' and j.get('suite')=='libero_object' and set(j.get('method_ids',[]))&set(c.METHODS) for j in state['registered_jobs']))
 for base in [R,P]:check('no existing output '+str(base),not (base/effective['output_relative']).exists());check('no existing invocation '+str(base),not (base/effective['invocation_relative']).exists())
 for path,pin in action['files'].items():check('unchanged action runtime source '+path,ev.watch(path)==pin)
 for path,pin in c.closure().items():check('complete control closure '+path,ev.watch(path)==pin)
 check('no actual readiness claimed',bundle['runtime_readiness'] is None and bundle['prepared_invocation'] is None and bundle['root_authorization'] is None and not bundle['actual_P_outer_wrapper_positive_verify'])
 ev.unchanged();evidence=write('checked_evidence.json',ev.files)
 report={'schema':'formal_main_v2','kind':'object256s23_source_control_plan_independent_CPU_review','status':'passed','blockers':[],'execution_version':'formal-downstream-action-v1','production_chain_complete':True,'production_chain_scope':'metadata/source/consumer closure only; actual GPU and true P readiness not yet validated','actual_GPU_runtime_chain_verified':False,'actual_P_readiness_verified':False,'scientific_plan':bundle['scientific_plan'],'effective_plan':bundle['effective_plan'],'action_execution_contract':bundle['execution_contract'],'plan_arguments':bundle['plan_arguments'],'plan_sha256':effective['plan_sha256'],'suite':'libero_object','allowed_stages':['development'],'methods':c.METHODS,'method_ids':c.METHODS,'prior_job_ids':[],'resume':False,'expected_trials':200,'unique_development_initial_states':100,'runtime_sources':action['files'],'explicit_source_control':c.descriptor(),'files':c.closure(),'source_publication':pubref,'root_snapshot':snapshotref,'bundle':bundle_ref,'checks':CHECKS,'evidence':evidence,'actual_GPU_runs':0,'Slurm_calls':0,'weights_read':False,'final_state_values_read':False,'final_release':False,'all_pair_GPU_seconds':58917,'retained_failed_GPU_seconds':84,'all173_science_unchanged_prior_canonical_review':{'path':(D/'canonical/independent_review.json').relative_to(R).as_posix(),'sha256':'7aa343615dd29a10fa67bef165f31b47897d31bf9e3b4ce5ca154c8f584e91d4'},'CPU_wall_seconds':time.monotonic()-t}
 ref=write('independent_plan_review.json',report);print(json.dumps({'status':'passed','checks':len(CHECKS),'report':ref,'production_chain_scope':report['production_chain_scope']}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if OUT.exists():write('failure.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':CHECKS})
  raise
