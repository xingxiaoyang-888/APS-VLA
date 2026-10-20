"""Independent read-only canonical k64 seed23 source bridge audit. No submission."""
from pathlib import Path
from types import SimpleNamespace
import sys,os,json,hashlib,copy,ast,importlib.util,contextlib,io,traceback,time,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/k64_seed23_bridges_independent_20261020T1949';A=R/'.local/k64_seed23_bridges_20261020T1949'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';INV_SHA='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
PUBLICATION='results/formal_main_v2/preflight/heartbeat_20261021T0349/k64_candidate_publication.json';PUB_SHA='1656f5c931545c0b0b2ae987202dbf1ae3281ccf2c71b900a30bf2f8a55f3949'
MAP_SHA='ec56fca197dcbb6de668761081852be973aba6ab61673edf4c961d29390973aa'
EXPECT={'spatial':{'control':'edab3f3917b57daf1867134bc8179a73673bfc4a1e61bfda5118d76fd64458f3','bridge':'678b6c57fbf6e188eced6d42bfa158862c1f185bced034027e535a4316804c87','total':42480,'failed':73,'selected':{'A':2500,'B':3500},'jobs':['3024716','3025205','3028522','3043399','3044479']},'object':{'control':'cf1058afd83073e0ef30c977e88c34f124f56adcfe9487b837ecaedaf6578767','bridge':'04c596f8b86569d7476f504fcf5519c205b0fc7eb2e0bd6de953fa47f5bc6735','total':52868,'failed':69,'selected':{'A':2500,'B':4500},'jobs':['3028468','3044017','3044844']}}
READS={};CHECKS=[];NEG=[];REPORTS=[]
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event.startswith(('subprocess.','socket.')) or event in ('os.system','os.posix_spawn','os.fork'):raise RuntimeError('audit forbids process/network/Slurm')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).absolute();mode=args[1];flags=args[2] or 0
  if p.suffix.lower() in {'.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init','.npz','.h5','.hdf5'} or any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts):raise RuntimeError('no weights/data/sealed access '+str(p))
  writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if writing and not p.is_relative_to(D):raise RuntimeError('private writes only '+str(p))
sys.addaudithook(guard)
def sha(b):return hashlib.sha256(b).hexdigest()
def check(ok,label):
 CHECKS.append({'name':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
def read(path,pin=None):
 p=Path(path);p=p if p.is_absolute() else R/p;b=p.read_bytes();h=sha(b)
 check(pin is None or pin==h,'exact byte SHA '+str(p));check(str(p) not in READS or READS[str(p)]==h,'stable input '+str(p));READS[str(p)]=h;return b
def rd(path,pin=None):return json.loads(read(path,pin))
def write(path,val):
 p=D/path;p.parent.mkdir(parents=True,exist_ok=True);b=val if isinstance(val,bytes) else (json.dumps(val,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b)}
def load(path,pin=None,name=None):
 p=Path(path);p=p if p.is_absolute() else R/p;b=read(p,pin);n=name or 'k64ind_'+p.stem+'_'+sha(str(p).encode())[:12];spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;exec(compile(b,str(p),'exec'),m.__dict__);return m
class Evidence:
 def __init__(self):self.project=self.root=R;self.files={};self.hashes=self.files;self.forbidden_paths=set()
 def path(self,n):
  p=Path(n);p=p if p.is_absolute() else R/p;check('..' not in p.parts and p.resolve()==p.absolute() and p.is_relative_to(R),'safe R evidence '+str(n));return p
 def watch(self,n):
  p=self.path(n);b=read(p);self.files[p.relative_to(R).as_posix()]=sha(b);return sha(b)
 def read(self,n):p=self.path(n);self.watch(p);return json.loads(p.read_bytes())
 def relative(self,n):return self.path(n).relative_to(R).as_posix()
 def unchanged(self):
  for n,pin in self.files.items():check(sha((R/n).read_bytes())==pin,'unchanged evidence '+n)
def neg(label,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,AssertionError) as e:NEG.append({'name':label,'type':type(e).__name__,'message':str(e),'passed':True});return
 raise AssertionError(label+' accepted invalid input')
def capture(path,fn):
 buff=io.StringIO()
 with contextlib.redirect_stdout(buff),contextlib.redirect_stderr(buff):result=fn()
 write(path,buff.getvalue().encode());return result

def run_pair(short,state,inventory):
 t=time.monotonic();e=EXPECT[short];suite='libero_'+short;out=short+'/';base='scripts/ops/formal_'+short+'64s23_source_bridge_v1/'
 c=load(base+'control.py',e['control']);b=load(base+'bridge_v2.py',e['bridge']);p=b.policy();read(base+'policy_v1.json',b.POLICY_SHA256)
 for ref in p['references'].values():read(ref['path'],ref['sha256'])
 check(p['all_job_ids']==e['jobs'] and sum(p['allocation_seconds'].values())==e['total'] and p['failed_GPU_seconds']==e['failed'],'fixed individual allocation history '+short)
 check({a:r['update'] for a,r in p['selected_checkpoints'].items()}==e['selected'],'fixed earliest selection '+short)
 manifest=rd(c.MANIFEST,c.MANIFEST_SHA);read(P/c.MANIFEST,c.MANIFEST_SHA);read(S/p['pair']['path'],p['pair']['sha256']);read(P/p['pair']['path'],p['pair']['sha256'])
 panel=rd(manifest['development_panel'],manifest['development_panel_sha256']);check(panel['suite']==suite and panel['split']=='development' and len(panel['states'])==100 and len(panel['task_catalog'])==10,'fixed development100/tasks10 '+short)
 check(len({(x['task_id'],x['source_index']) for x in panel['states']})==100,'unique development initial IDs '+short)
 docs={k:rd(p['references'][v]['path'],p['references'][v]['sha256']) for k,v in [('saved','final_root'),('independent','final_independent'),('recovery_root','recovery_root'),('recovery_independent','recovery_independent'),('failure','failure'),('recovery_authorization','recovery_authorization'),('continuous_authorization','continuous_authorization')]}
 jobs=docs['saved']['registered_pair_jobs_at_review'];scope={'suite':suite,'pair':p['pair'],'method_rows':manifest['methods'],'relevant':jobs}
 b.scope_guard(p,**scope);check(b.validate_documents(p,**docs)==set(p['successful_job_ids']),'real original documents accepted '+short)
 failed=next(j for j in jobs if j['job_id']==p['failure_job_id']);fv=load(p['references']['failure_verifier']['path'],p['references']['failure_verifier']['sha256']);ev=Evidence();rebuilt=fv.require_saved(ev,job=failed,saved=docs['failure']);ev.unchanged();check(rebuilt==docs['failure'],'original failure verifier full rebuild '+short)
 for key,val in [('elapsed_seconds',0),('status','COMPLETED'),('source_sha256','0'*64),('invocation_sha256','0'*64),('segment_end',999)]:
  x=copy.deepcopy(failed);x[key]=val;neg(short+' original failure '+key,lambda x=x:fv.require_saved(Evidence(),job=x,saved=docs['failure']))
 scopes=[('wrong suite',lambda x:x.update(suite='libero_goal')),('budget',lambda x:x['pair'].update(visual_tokens=256)),('seed',lambda x:x['pair'].update(seed=17)),('AB order',lambda x:x['method_rows'].reverse()),('missing B',lambda x:x['method_rows'].pop()),('missing failed',lambda x:x['relevant'].__setitem__(slice(None),[j for j in x['relevant'] if j['job_id']!=p['failure_job_id']])),('duplicate allocation',lambda x:x['relevant'].append(copy.deepcopy(x['relevant'][0]))),('GPU count',lambda x:x['relevant'][0].update(gpus=2)),('cost omit',lambda x:x['relevant'][0].update(elapsed_seconds=0)),('checkpoint',lambda x:x['method_rows'][0]['identity'].update(checkpoint_sha256='0'*64)),('source root',lambda x:x['relevant'][0].update(run_root='/wrong'))]
 for label,change in scopes:
  x=copy.deepcopy(scope);change(x);neg(short+' scope '+label,lambda x=x:b.scope_guard(p,**x))
 muts=[('failure omission',lambda x:x['saved']['startup_failure_history'].clear()),('final incomplete',lambda x:x['saved']['completed_by_arm'].update(B=4500)),('bill incomplete',lambda x:x['saved'].update(pair_allocated_gpu_seconds=e['total']-e['failed'])),('ind missing',lambda x:x['independent'].update(status='pending')),('ind root swap',lambda x:x['independent']['root_review'].update(sha256='0'*64)),('no rebuild',lambda x:x['independent'].update(historical_failure_preserved_and_rebuilt=False)),('AB order',lambda x:x['independent'].update(same_AB_initialization_and_full40000_order=False)),('source',lambda x:x['independent'].update({p['independent_source_flag']:False})),('cost duplicate',lambda x:x['independent']['cost']['allocations'].append(copy.deepcopy(x['independent']['cost']['allocations'][0]))),('failed cost',lambda x:x['independent']['cost'].update({p['independent_failed_cost_key']:0})),('recovery target',lambda x:x['recovery_root']['completed_by_arm'].update(A=499)),('recovery ind',lambda x:x['recovery_independent'].update(status='pending')),('failed updates',lambda x:x['failure'].update(current_allocation_new_updates=1)),('failed initialization',lambda x:x['failure'].update(current_allocation_arm_initializations=1)),('failed cursor',lambda x:x['failure']['next_sample_cursor'].update(B=8)),('recoveryauth target',lambda x:x['recovery_authorization'].update(original_target=123)),('continuous pair',lambda x:x['continuous_authorization'].update(pair_key='libero_goal_k64_seed23')),('continuous search',lambda x:x['continuous_authorization'].update(scientific_settings_changed=True)),('continuous target',lambda x:x['continuous_authorization'].update(target_updates_per_arm=10000)),('missing validation',lambda x:x['independent']['arms']['B']['validation'].pop()),('cursor incomplete',lambda x:x['independent']['arms']['B'].update(cursor=39992)),('chosen step',lambda x:x['independent']['arms']['B'].update(selected_update=5000,earliest_selected_update=5000)),('selected SHA',lambda x:x['independent']['arms']['A'].update(best_sha256='0'*64,best={'sha256':'0'*64}))]
 muts += [('fabricated metadata',lambda x:x['saved'].update(runtime_compatibility_history={p['failure_job_id']:{}}))]
 for label,change in muts:
  x=copy.deepcopy(docs);change(x);neg(short+' evidence '+label,lambda x=x:b.validate_documents(p,**x))
 orig=read(p['references']['original_consumer']['path'],p['references']['original_consumer']['sha256']).decode();derived=b.derived_source(orig);aa=ast.parse(orig).body;bb=ast.parse(derived).body;check(len(aa)==len(bb),'top-level AST shape unchanged '+short)
 changed=[getattr(a,'name',type(a).__name__) for a,z in zip(aa,bb) if ast.dump(a,include_attributes=False)!=ast.dump(z,include_attributes=False)];check(changed==['_root_pull','_pair_source'],'only operational ownership/history AST changes '+short)
 fac=b.auditor(Evidence());write(out+'consumer_derivation.diff',fac.source_diff.encode())
 basefac=load(p['references']['original_factory']['path'],p['references']['original_factory']['sha256']);args=lambda n:['--project-root',str(R),'development','--suite',suite,'--methods',*p['method_ids'],'--source-inventory',INV,'--output',(D/(out+n)).relative_to(R).as_posix()]
 rc=capture(out+'original_factory_rejection.log',lambda:basefac.main(args('rejected.json')));check(rc==2 and not (D/out/'rejected.json').exists(),'original factory rejected historic source '+short)
 factory,planner=b.control_modules(basefac.Evidence(R));rc=capture(out+'bridge_factory.log',lambda:factory.main(args('development.json')));check(rc==0,'original factory through exact bridge '+short)
 check(read(D/(out+'development.json'))==read(c.MANIFEST,c.MANIFEST_SHA),'scientific execution byte-identical '+short)
 gen=rd(D/(out+'development.json.evidence.json'));registration=rd('configs/experiments/formal_main_v2.json');kwargs={'registration':registration,'suite':suite,'inventory':inventory,'method_rows':manifest['methods'],'jobs':gen['source_provenance']['registered_source_jobs']}
 rebuilt=fac.review_source_provenance(basefac.Evidence(R),**kwargs);check(rebuilt==gen['source_provenance'],'source proof independently reconstructed '+short)
 neg(short+' original source rejects',lambda:fac.original.review_source_provenance(basefac.Evidence(R),**kwargs))
 for key,val in [('method_id','A256_seed23'),('future_head_deployed',True),('training_complete',False),('frozen_model_sha256','0'*64)]:
  x=copy.deepcopy(kwargs);x['method_rows'][0]['identity'][key]=val;neg(short+' original science validator '+key,lambda x=x:fac.review_source_provenance(basefac.Evidence(R),**x))
 cf,cp=c.control_modules(Evidence());planargs={'stage':'development','source_inventory':INV,'execution_manifest':c.MANIFEST,'output_relative':None,'freeze_directory':None,'profile_panel':None,'prior_review':None,'collection_review':None,'repair_record':None,'resume':False,'stop_after':None}
 for label,delta in [('final',{'stage':'final'}),('resume',{'resume':True}),('prefix',{'stop_after':1}),('other manifest',{'execution_manifest':c.CPU_MANIFEST}),('extra key',{'extra':True})]:
  neg(short+' canonical planner '+label,lambda delta=delta:cp.plan(SimpleNamespace(**{**planargs,**delta}),state,project=R,helper=cf))
 science=cp.plan(SimpleNamespace(**planargs),state,project=R,helper=cf);sr=write(out+'canonical_scientific_plan.json',science);inv=science['invocation'];c.scope_invocation(inv)
 check(inv['source_provenance']['explicit_source_control']==c.descriptor(),'canonical source descriptor matches closure '+short)
 check(inv['method_ids']==p['method_ids'] and inv['resume'] is False and inv['prior_job_ids']==[],'fresh exact pair development scope '+short)
 for n in [science['output_relative'],science['invocation_relative']]:check(not (R/n).exists() and not (P/n).exists(),'no duplicate output '+n)
 check(not any(j.get('mode')=='development' and j.get('suite')==suite and set(j.get('method_ids',[]))&set(p['method_ids']) for j in state['registered_jobs']),'no registered paired development '+short)
 for label,delta in [('otherstage',{'stage':'final'}),('method',{'method_ids':['dense']}),('resume',{'resume':True}),('priorjob',{'prior_job_ids':['3053503']}),('prefix',{'stop_after':1}),('sealedargv',{'argv':['--sealed-final']})]:
  x=copy.deepcopy(inv);x.update(delta);neg(short+' invocation '+label,lambda x=x:c.scope_invocation(x))
 own=load(P/'scripts/server/run_formal_downstream.py','f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24');checked=own.verify(inv);check(checked.mode=='evaluate','actual P scientific wrapper verifies metadata '+short)
 # Runtime lifecycle code is inherited unchanged; no Slurm object is instantiated.
 g=c.gateway_module();og=load(c.GATEWAY,c.ORIGINAL[c.GATEWAY]);check(g.Gateway.run.__code__.co_code==og.Gateway.run.__code__.co_code and g.Gateway.run.__code__.co_consts==og.Gateway.run.__code__.co_consts,'gateway run/pending/ACK lifecycle bytecode unchanged '+short)
 for name in ['capacity_gate','duplicate_gate']:
  if hasattr(g.Gateway,name):
   x=getattr(g.Gateway,name);y=getattr(og.Gateway,name);check(x.__code__.co_code==y.__code__.co_code and x.__code__.co_consts==y.__code__.co_consts,'original '+name+' bytecode unchanged '+short)
 cconsumer=c.consumer_module(Evidence())
 for ref in [None,{}, {'path':'results/formal_main_v2/downstream_reviews/fake.json'}, {'path':'../outside.json','sha256':'0'*64},{'path':'results/experiment_supervisor/state.json','sha256':'0'*64}]:
  class NoTarget(Evidence):
   def __init__(self):super().__init__();self.target_reads=0
   def read(self,n):self.target_reads+=1;raise RuntimeError('unexpected target read')
  target=NoTarget()
  neg(short+' malformed terminal ref '+repr(ref),lambda ref=ref,target=target:cconsumer.review_downstream_output(target,ref,expected_stage='development',suite=suite))
  check(target.target_reads==0,short+' invalid terminal reference had zero target reads')
 for stage in ['final','collect','timing']:
  neg(short+' terminal stage '+stage,lambda stage=stage:cconsumer.review_downstream_output(Evidence(),{},expected_stage=stage,suite=suite))
 cf_source=c.source_auditor(Evidence());canonical=cf_source.review_source_provenance(basefac.Evidence(R),**kwargs);check(canonical==inv['source_provenance'],'canonical original consumer rebuilds planner proof '+short)
 report={'schema':'cti-vla-independent-review-v1','kind':'k64_seed23_source_bridge_independent_CPU_review','status':'passed_CPU_source_and_metadata_review','suite':suite,'method_ids':p['method_ids'],'selected_updates':e['selected'],'all_pair_GPU_seconds':e['total'],'retained_failed_GPU_seconds':e['failed'],'original_failure_rebuilt':True,'source173_unchanged':True,'canonical_scientific_plan':sr,'scientific_plan_sha256':science['plan_sha256'],'explicit_source_control':c.descriptor(),'actual_P_original_wrapper_metadata_verified':True,'actual_GPU_runtime_chain_verified':False,'live_checkpoint_bytes_read_by_this_audit':False,'final_enabled':False,'scientific_trials_added':0,'new_GPU_runs':0,'admission_limitations':['Completed-controller submission requires separately reviewed gateway','Action runtime readiness and root authorization must be exact and independently post-verified before any dispatch'],'blockers':[],'wall_seconds':time.monotonic()-t}
 ref=write(out+'independent_CPU_review.json',report);REPORTS.append(ref)

def main():
 t=time.monotonic();publication=rd(PUBLICATION,PUB_SHA);mapping=rd(A/'source_publication_manifest_v2.json',MAP_SHA)
 for pair in mapping['pairs']:
  for row in pair['files']+[pair['manifest']]:
   original=read(row['source'],row['sha256']);check(len(original)==row['bytes'],'publication bytes length');check(original==read(row['path'],row['sha256']),'published source exact candidate')
  read(P/pair['manifest']['path'],pair['manifest']['sha256'])
 inventory=rd(INV,INV_SHA);check(len(inventory['files'])==173,'frozen inventory173')
 for root in (R,S):
  for n,h in inventory['files'].items():read(root/n,h)
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH);raw=(R/'results/experiment_supervisor/state.json').read_bytes();fcntl.flock(lock,fcntl.LOCK_UN)
 state= json.loads(raw);state_ref=write('state_read_only_snapshot.json',raw)
 for short in EXPECT:run_pair(short,state,inventory)
 for root in (R,S):
  for n,h in inventory['files'].items():check(sha((root/n).read_bytes())==h,'frozen final unchanged '+str(root/n))
 refs=write('read_inputs.json',READS);checks=write('checks.json',CHECKS);negref=write('expected_rejections.json',NEG)
 report={'status':'passed_CPU_source_and_metadata_review','reviewed_by':'independent','pair_reports':REPORTS,'checks':len(CHECKS),'negative_cases':len(NEG),'read_inputs':refs,'checks_ref':checks,'negative_ref':negref,'state_snapshot':state_ref,'publication':{'path':PUBLICATION,'sha256':PUB_SHA},'canonical_source_publication_map':{'path':str((A/'source_publication_manifest_v2.json').relative_to(R)),'sha256':MAP_SHA},'new_GPU_runs':0,'scientific_trials_added':0,'state_writes':False,'checkpoint_bytes_read':False,'final_values_read':False,'root_runtime_admission_granted':False,'blockers':[],'wall_seconds':time.monotonic()-t}
 print(json.dumps(write('independent_index.json',report),sort_keys=True))
try:main()
except BaseException as e:
 write('failure_v2.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc(),'checks':CHECKS,'expected_rejections':NEG,'read_inputs':READS});raise
