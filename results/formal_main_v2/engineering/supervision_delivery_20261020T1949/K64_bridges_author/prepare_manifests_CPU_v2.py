from pathlib import Path
import os,sys,json,hashlib,importlib.util,io,contextlib,traceback,time,copy,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent;P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
OUT=D/'attempt02';OUT.mkdir(exist_ok=False)
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('CPU only: process/network/Slurm forbidden')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  assert not any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts),'payload I/O forbidden'
  assert p.suffix.lower() not in ('.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init'),'payload I/O forbidden'
  mode,flags=args[1:];writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
  if writing:assert D in p.parents,'only this private package may be written'
sys.addaudithook(guard)
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:f.write(v if isinstance(v,str) else json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n')
def load(p,pin):
 p=Path(p);assert h(p)==pin;sp=importlib.util.spec_from_file_location('k64author_'+p.parent.name+'_'+p.stem,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
checks=[]
def check(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def reject(name,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,RuntimeError) as e:checks.append({'name':name,'passed':True,'rejection':str(e)});return str(e)
 raise AssertionError('Unexpected admission '+name)
class Evidence:
 def __init__(self):self.project=self.root=R;self.files={}
 def path(self,p):p=Path(p);return p if p.is_absolute() else R/p
 def watch(self,p):q=self.path(p);v=h(q);rel=q.relative_to(R).as_posix();assert rel not in self.files or self.files[rel]==v;self.files[rel]=v;return v
 def read(self,p):self.watch(p);return json.loads(self.path(p).read_bytes())
 def unchanged(self):
  for p,v in self.files.items():assert h(R/p)==v
inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes())
for root in [R,S]:
 for p,v in inventory['files'].items():check('original173_before:'+str(root)+':'+p,h(root/p)==v)
with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lk:
 fcntl.flock(lk,fcntl.LOCK_SH);state_raw=(R/'results/experiment_supervisor/state.json').read_bytes()
state=json.loads(state_raw);save(OUT/'state_read_only_snapshot.json',state_raw.decode());save(OUT/'state_reference.json',{'sha256':hashlib.sha256(state_raw).hexdigest(),'CPU_only_not_authorization':True})
results=[]
for pair in json.loads((D/'build_receipt.json').read_bytes())['pairs']:
 short=pair['suite'].removeprefix('libero_');base=D/short;dest=OUT/short;dest.mkdir();ev=Evidence();start=time.monotonic()
 try:
  b=load(R/pair['bridge']['path'],pair['bridge']['sha256']);p=b.policy();factory,planner=b.control_modules(ev)
  out=base/'development.json';argv=['--project-root',str(R),'development','--suite',p['suite'],'--methods',*p['method_ids'],'--source-inventory','results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','--output',out.relative_to(R).as_posix()]
  original=load(R/'scripts/formal_execution_manifests.py','614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89')
  badargv=argv[:-1]+[(dest/'original_factory_rejected_manifest.json').relative_to(R).as_posix()]
  log=io.StringIO()
  with contextlib.redirect_stdout(log):original_rc=original.main(badargv)
  original_result=json.loads(log.getvalue());check(short+':original factory fail closed',original_rc==2 and original_result['status']=='blocked')
  save(dest/'original_factory_rejection.json',{'returncode':original_rc,'result':original_result,'no_scientific_rerun':True})
  log=io.StringIO()
  with contextlib.redirect_stdout(log):rc=factory.main(argv)
  check(short+':candidate factory true source accepted',rc==0);save(dest/'factory_stdout.txt',log.getvalue())
  manifest=json.loads(out.read_bytes());proof=json.loads(Path(str(out)+'.evidence.json').read_bytes())['source_provenance'];save(dest/'source_provenance.json',proof)
  check(short+':original methods and checkpoint rows', [x['identity']['method_id'] for x in manifest['methods']]==p['method_ids'])
  for arm in ['A','B']:
   found=next(x for x in manifest['methods'] if x['identity']['method']==arm);check(short+':actual selected '+arm,found['identity']['checkpoint_sha256']==p['selected_checkpoints'][arm]['sha256'])
   check(short+':all historical jobs '+arm,proof['method_bindings'][arm+'64_seed23']['registered_training_job_ids']==p['all_job_ids'])
  docs={k:b.read_ref(ev,p['references'][k]) for k in ('final_root','final_independent','recovery_root','recovery_independent','failure','recovery_authorization','continuous_authorization')}
  args=dict(p=p,saved=docs['final_root'],independent=docs['final_independent'],recovery_root=docs['recovery_root'],recovery_independent=docs['recovery_independent'],failure=docs['failure'],recovery_authorization=docs['recovery_authorization'],continuous_authorization=docs['continuous_authorization'])
  check(short+':document assertions real inputs',b.validate_documents(**args)==set(p['successful_job_ids']))
  for key,field,val in [('saved','pair_allocated_gpu_seconds',p['total_GPU_seconds']-p['failed_GPU_seconds']),('failure','current_allocation_new_updates',1),('failure','next_sample_cursor',{'A':0,'B':1}),('recovery_authorization','failed_job_id','other'),('continuous_authorization','pair_key','libero_object_k256_seed23'),('independent','historical_failure_preserved_and_rebuilt',False)]:
   bad=copy.deepcopy(args);bad[key][field]=val;reject(short+':reject '+key+'.'+field,lambda bad=bad:b.validate_documents(**bad))
  bad=copy.deepcopy(args);bad['saved']['startup_failure_history']={};reject(short+':reject omitted failed startup',lambda:b.validate_documents(**bad))
  bad=copy.deepcopy(args);bad['independent']['cost']['allocations']=bad['independent']['cost']['allocations'][1:];reject(short+':reject omitted allocation',lambda:b.validate_documents(**bad))
  relevant=[j for j in state['registered_jobs'] if j.get('job_id') in p['all_job_ids']]
  scope=dict(p=p,suite=p['suite'],pair=p['pair'],method_rows=manifest['methods'],relevant=relevant)
  b.scope_guard(**scope)
  bad=copy.deepcopy(scope);bad['relevant']=bad['relevant'][1:];reject(short+':reject shortened registered history',lambda:b.scope_guard(**bad))
  bad=copy.deepcopy(scope);bad['method_rows'][0]['identity']['checkpoint_sha256']='0'*64;reject(short+':reject wrong checkpoint',lambda:b.scope_guard(**bad))
  bad=copy.deepcopy(scope);bad['suite']='libero_goal';reject(short+':reject another suite',lambda:b.scope_guard(**bad))
  facade=b.auditor(ev);save(dest/'source_consumer_derivation.diff',facade.source_diff)
  ev.unchanged();save(dest/'read_evidence.json',ev.files)
  result={'suite':p['suite'],'status':'passed_factory_and_history_CPU_only','manifest':{'path':out.relative_to(R).as_posix(),'sha256':h(out)},'source_provenance':{'path':(dest/'source_provenance.json').relative_to(R).as_posix(),'sha256':h(dest/'source_provenance.json')},'GPU_runs':0,'scientific_trials':0,'Slurm_calls':0,'all_pair_GPU_seconds_retained':p['total_GPU_seconds'],'failed_GPU_seconds_retained':p['failed_GPU_seconds'],'CPU_wall_seconds':time.monotonic()-start}
  save(dest/'report.json',result);results.append(result)
 except BaseException as e:
  failure={'suite':pair['suite'],'status':'failed_CPU_candidate_only','error':str(e),'traceback':traceback.format_exc(),'checks':checks,'GPU_runs':0,'Slurm_calls':0};save(dest/'failure.json',failure);results.append(failure)
for root in [R,S]:
 for p,v in inventory['files'].items():check('original173_after:'+str(root)+':'+p,h(root/p)==v)
save(OUT/'checks.json',checks);save(OUT/'summary.json',{'pairs':results,'status':'passed' if all(r['status'].startswith('passed') for r in results) else 'bounded_failure_retained','check_count':len(checks),'state_mutated':False,'canonical_mutated':False})
print(json.dumps({'pairs':[{k:r[k] for k in ['suite','status','error'] if k in r} for r in results],'checks':len(checks)}))
