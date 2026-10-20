"""Independent Object599: no inference, simulator, Slurm, checkpoint/final values, production writes or admission."""
import ast,copy,hashlib,json,math,os,random,sys,time,types,zipfile,tarfile,subprocess,textwrap
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/object599_independent_20261020T2253';A=R/'.local/object_legacy_integration_20261020T2156';E=R/'results/formal_main_v2/engineering/supervision_delivery_20261020T2156/Object_author'
MANSHA='9020eb66c1746924379106baf19cd5d50318bf4283370b900785acba596c1992';CANDSHA='6fe1247dcb1fc211fc226f6de8d225e8757a97efd774b244431b37329b074bb2'
RUN='results/formal_main_v2/libero_object/downstream/development/8c843c1d4ee8383c/attempt01';OLDROOT='results/formal_main_v2/downstream_reviews/3021844.json';MAN='results/formal_main_v2/execution/libero_object_development_first_pair_v1.json'
TARGET='results/formal_main_v2/execution/object_collect_action_v1_20261020T1825/execution_contract.json';NEWROOT='results/formal_main_v2/downstream_reviews/3053518.json';INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';REG='configs/experiments/formal_main_v2_action_execution_compat_v1.json'
ADAPTER='results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py';V4='results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/3039197/events.jsonl'
SEM='9a5f5935100bb04bf8fb91f6405b94efc93de236b3a75896d0f08cdb2aa1ee02';JOBS=['3021394','3021603','3021844'];METHODS=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
BAD='libero_object:pick_up_the_chocolate_pudding_and_place_it_in_the_basket:state-0049:env-0:dense'
PINS={OLDROOT:'004a810edd7f097bbeec755315beed11bbfa86640a78ffd75ef0ff78a769ee37',MAN:'34062573869c7b947fbd3c37b09da476bec673e8e16fc4ea49c6ce8c5932db5a',INV:'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926',REG:'0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe',TARGET:'dde9c5437348cf202c02af9933b1bcab42ee9c10b6b05932b7ed11a565710eaa',NEWROOT:'a6fee864f172a895ffe7be3ff7a44f4ecd340eb6b9368afbf7f08d819fc2df65',ADAPTER:'b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',V4:'54f92fbd0354bae27b95f17c5193c186cb387781f223e7af1655ea825a84459c',RUN+'/trials.jsonl':'d93ad5a4eb4ae3edb7a9b20e640a72fe4971ca0e4eeb62eea71acc4d71a257d1',RUN+'/config.json':'ccbb680ade2c6cab783568ea34f2fd3d3ae9abb69a62e7088f53d7150dad27a5',RUN+'/panel.json':'6b7e6dd9fb5b6351ee47c7bb30eab911e7c144d700cd88f7e5162641738b2d6a','results/setup/after_libero_freeze.txt':'8bac807b631bb9c9691df977eae1b26f202b6a2d8d4a440153a74bb96b7a9b06','configs/assets/libero_wheels_transfer.json':'bfd7901791c5858e405188cfc1e917fdd3db73a277a2468dd94b8d620ec0cb23','configs/requirements-libero.txt':'d255285a470c034692b493904ca8335847e58ffec6388775ddef7ccc8419987c','scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89','scripts/ops/formal_action_deployment_v1/consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
SEEN={};COUNTS=Counter();START=time.perf_counter();CPU=time.process_time()
def ck(v,label):
 if not v:raise AssertionError(label)
 COUNTS[label]+=1
def sha(b):return hashlib.sha256(b).hexdigest()
def filehash(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sig(o):return sha(canon(o))
def unique(xs):
 o={}
 for k,v in xs:
  if k in o:raise ValueError('duplicate JSON key')
  o[k]=v
 return o
def decode(b):
 def bad(x):raise ValueError('nonfinite JSON')
 return json.loads(b,object_pairs_hook=unique,parse_constant=bad)
def path(x):return Path(x) if Path(x).is_absolute() else R/x
def watch(x,h=None):
 p=path(x);ck(p.resolve()==p,'canonical_path');a=filehash(p);ck(h is None or a==h,'evidence_SHA');k=str(p.relative_to(R)) if R in p.parents else str(p);v={'sha256':a,'bytes':p.stat().st_size};ck(k not in SEEN or SEEN[k]==v,'stable_evidence');SEEN[k]=v;return {'path':k,**v}
def read(x,h=None):watch(x,h);return path(x).read_bytes()
def obj(x,h=None):return decode(read(x,h))
def out(name,o,jl=False):
 b=b''.join(canon(v)+b'\n' for v in o) if jl else json.dumps(o,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2).encode()+b'\n'
 with (D/name).open('xb') as f:f.write(b)
 return {'path':str((D/name).relative_to(R)),'sha256':sha(b),'bytes':len(b)}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('no process/network')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if any('sealed' in q.lower() or q.lower() in ('weights','checkpoints') for q in p.parts) or set(p.suffixes)&{'.pt','.pth','.ckpt','.safetensors','.pkl','.pickle','.pruned_init','.init'} or (p.name=='panel.json' and 'final' in p.parts) or p.name=='init_states_test.json':raise RuntimeError('forbidden value path')
  mode,flags=args[1:3];w=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if w:ck(p.parent==D,'private_write_only')
def load(p,name):
 p=path(p);m=types.ModuleType(name);m.__file__=str(p);m.__package__='';sys.modules[name]=m;exec(compile(read(p),str(p),'exec',dont_inherit=True),m.__dict__);return m
def b64(v):
 a=np.array(v,dtype='<f8');ck(a.ndim==2 and a.shape[1]==7 and np.isfinite(a).all(),'finite_action_shape');return a.tobytes(order='C')
def rng():
 a=np.random.get_state();return sig([random.getstate(),a[0],a[1].tolist(),int(a[2]),int(a[3]),float(a[4])])
def astr(x):return ast.dump(x,include_attributes=False)
def lr(n,off,b):return {'line':n,'byte_offset':off,'bytes':len(b),'sha256':sha(b)}
def main():
 ck(Path(__file__).parent==D,'private_entrypoint');anchor='5c15d256796661cfd91375ac4721356d1e1888dc';gitrows=[]
 for rel in ['results/setup/after_libero_freeze.txt','configs/assets/libero_wheels_transfer.json','configs/requirements-libero.txt']:
  b=subprocess.run(['git','-C',str(R),'show',anchor+':'+rel],check=True,capture_output=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}).stdout;ck(sha(b)==PINS[rel],'historical_git_blob');gitrows.append({'commit':anchor,'path':rel,'sha256':sha(b)})
 t=subprocess.run(['git','-C',str(R),'show','-s','--format=%cI',anchor],check=True,capture_output=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}).stdout.decode().strip();ck(t.startswith('2026-10-14'),'historical_git_time')
 sys.dont_write_bytecode=True;sys.addaudithook(guard)
 am=obj(A/'stage1_delivery_manifest.json',MANSHA);ck(am['frozen_stage1'] and am['GPU_seconds']==0 and am['accepted_scientific_trials_added']==0 and am['all_original_GPU_seconds']==6713 and am['no_production_changes'],'author_CPU_no_admission');archive=[]
 ck(len(am['files'])==17 and len({x['path'] for x in am['files']})==17,'author17files')
 for f in am['files']:
  p=R/f['path'];ck(p.parent==A,'author_private_scope');x=watch(p,f['sha256']);y=watch(E/p.name,f['sha256']);ck(x['bytes']==y['bytes']==f['bytes'],'exact_archive_bytes');archive.append(y)
 ck(read(E/'stage1_delivery_manifest_original.json')==read(A/'stage1_delivery_manifest.json'),'exact_archive_manifest')
 for k,v in PINS.items():watch(k,v)
 original=obj(OLDROOT);config=obj(RUN+'/config.json');manifest=obj(MAN);panel=obj(RUN+'/panel.json');candidate=obj(A/'Object599_candidate.json',CANDSHA);contract=obj(TARGET);newroot=obj(NEWROOT)
 ck(config['manifest']==manifest,'original_manifest');ck(manifest['environment']=={'action_chunk':8,'environment_seed':0,'max_steps':280,'runtime_seed':17,'wait_steps':10},'Object_environment')
 ck(original['raw_invocation_job_ids']==JOBS and original['completed_trials']==600 and original['scientific_complete'],'original600history');ck(original['source_provenance']['shared_projection']==newroot['source_provenance']['shared_projection'],'old_current_Object_source_projection');ck(newroot['status']=='passed' and newroot['action_semantics_sha256']==SEM,'actual_current_Object_target')
 for rel,h in {**contract['files'],**contract['GPU_acceptance'],**contract['runtime_contract']['dependencies']}.items():watch(rel,h)
 rc=contract['runtime_contract'];ck(sig({'execution_version':'formal-downstream-action-v1','files':contract['files'],'runtime_contract_without_stage':{k:v for k,v in rc.items() if k!='stage'},'GPU_acceptance':contract['GPU_acceptance'],'source_inventory':contract['source_inventory']})==SEM,'semantic_digest');ck(rc['suite']=='libero_object' and rc['source_root']==str(S) and rc['source_sha256']==original['source_sha256'],'current_source_scope')
 inv=obj(INV);ck(len(inv['files'])==173,'source173')
 for rel,h in inv['files'].items():
  for root in [R,S,R/'snapshots/formal_main_v2_run_564be0995e']:watch(root/rel,h)
 helper=load('scripts/formal_execution_manifests.py','_ind_object_helper');consumer=load('scripts/ops/formal_action_deployment_v1/consumer.py','_ind_object_consumer');ev=helper.Evidence(R);rebuilt=consumer.review_downstream_output(ev,{'path':OLDROOT,'sha256':PINS[OLDROOT]},expected_stage='development',suite='libero_object');ev.unchanged();ck(rebuilt['completed_trials']==600 and rebuilt['cost']['all_attempt_gpu_seconds']==6713,'original_consumer_whole600')
 oldcheck=out('original_consumer_reconstruction_v5.json',{'status':'passed','root':{'path':OLDROOT,'sha256':PINS[OLDROOT]},'completed_old_terminal_trials':600,'cost':rebuilt['cost'],'evidence_sha256':ev.files,'new_GPU_or_admission':False})
 ids={x['identity']['method_id']:x['identity'] for x in manifest['methods']};ck(list(ids)==METHODS and candidate['method_identities']==ids,'six_method_identity_map')
 for item in manifest['methods']:
  ident=item['identity'];ck(ident['suite']=='libero_object' and ident['model_revision']=='4c89574e1c538b6c102f43f0526d60a9d3650148' and ident['frozen_model_sha256']=='33285a7643de7073e41bd2062cbbc80b4df8fddff915c0a86a13d0bbae48edce' and ident['stats_key']=='libero_object_no_noops' and not ident['future_head_deployed'],'official_Object_base')
  if 'checkpoint' in item:
   ck(config['watched_files'][item['checkpoint']]==ident['checkpoint_sha256'],'original_checkpoint');rec=obj(item['receipt'],config['watched_files'][str(P/item['receipt'])]);ck(rec['checkpoint_sha256']==ident['checkpoint_sha256'] and rec['training_complete'] and rec['completed_updates']==5000 and len(rec['evaluations'])==11,'checkpoint_receipt');best=min(rec['evaluations'],key=lambda x:(x['validation_metric'],x['update']));ck(best['update']==rec['metadata']['update'] and best['validation_metric']==rec['metadata']['validation_metric'],'unchanged11node_selection');tr=obj(str(Path(item['receipt']).with_name('training_report.json')));ck(tr['best_checkpoint_sha256']==ident['checkpoint_sha256'] and tr['best_update']==best['update'] and tr['best_validation_metric']==best['validation_metric'] and tr['evaluations']==rec['evaluations'],'finalized_checkpoint_training_report')
 ck(panel['suite']=='libero_object' and panel['split']=='development' and len(panel['states'])==100,'100dev_only');watch(manifest['development_panel'],manifest['development_panel_sha256']);ck(read(manifest['development_panel'])==read(RUN+'/panel.json'),'panel_bytes');stateby={s['trial_id']:s for s in panel['states']};ck(len(stateby)==100 and Counter(x['task_id'] for x in stateby.values())=={i:10 for i in range(10)},'10states_each10tasks')
 for state in stateby.values():
  v=np.asarray(state['initial_state'],dtype='<f8');h=hashlib.sha256(b'cti-vla:libero-init-state:v1\x00');h.update(np.asarray(v.shape,dtype='<i8').tobytes());h.update(v.tobytes());ck(h.hexdigest()==state['initial_state_sha256'],'state_vector_identity')
 history=[];first=None
 for job in JOBS:
  ps=list((R/RUN/'adapter_invocations').glob(job+'_*.json'));ck(len(ps)==1,'one_old_adapter_per_job');ar=obj(ps[0],original['files'][str(ps[0].relative_to(R))]);jl=ps[0].with_suffix('.jsonl');events=[decode(b) for b in read(jl,ar['events_sha256']).splitlines()];off=[e for e in events if e['event']=='official_source_verified'];ck(len(off)==2,'old_actual_archives')
  for e in off:
   key='libero' if e['path'].endswith('/LIBERO') else 'openvla_oft';ck(e['verification']==config['source_verification'][key],'old_archives_allfiles');tt=datetime.fromisoformat(e['utc']).timestamp();first=tt if first is None else min(first,tt)
  ck(ar['verified_frozen_file_count']==173 and ar['frozen_source_unchanged'] and ar['old_ledger_prefix_unchanged'],'old_source_prefix_verified');err=read('results/slurm/cti-formal-downstream_'+job+'.err').decode();ck('/share/home/u15016/XXY_CVPR/CTI-VLA/venv/lib/python3.11/site-packages/robosuite' in err and 'No private macro file found' in err,'old_venv_no_macro_override');history.append({'job_id':job,'adapter':watch(ps[0]),'journal':watch(jl),'official_events':off})
 transfer=obj('configs/assets/libero_wheels_transfer.json');site=R.parent/'venv/lib/python3.11/site-packages';wheelrows=[];wheelmembers=[]
 for base in ['robosuite','mujoco']:
  fs=[f for f in transfer['files'] if f['path'].startswith(base+'-') and f['path'].endswith('.whl')];ck(len(fs)==1,'one_frozen_wheel');f=fs[0];wp=P/'external/wheels-libero'/f['path'];watch(wp,f['sha256']);count=0
  with zipfile.ZipFile(wp) as z:
   for name in z.namelist():
    if not name.startswith(base+'/') or name.endswith('/'):continue
    b=z.read(name);installed=site/name;w=watch(installed,sha(b));st=installed.stat();ck(st.st_ctime<first and st.st_mtime<first,'installed_before_old_Object');wheelmembers.append({**w,'wheel':f['path'],'member':name,'ctime_ns':st.st_ctime_ns,'mtime_ns':st.st_mtime_ns});count+=1
  wheelrows.append({'wheel':f['path'],'sha256':f['sha256'],'matched_members':count})
 ck(not (site/'robosuite/macros_private.py').exists(),'no_current_macros');freeze=read(P/'results/setup/after_libero_freeze.txt',PINS['results/setup/after_libero_freeze.txt']).decode();install=read(P/'results/setup/install_libero_local_attempt4.log').decode();ck(all((w['wheel'].split('-')[0]+' @ file://'+str(P/'external/wheels-libero'/w['wheel'])+'#sha256='+w['sha256']) in freeze.splitlines() for w in wheelrows) and 'runtime_imports_passed' in install and 'Successfully installed libero-0.1.0' in install and '2026-10-14' in install,'prejob_install')
 lp=P/'external/libero-8f1084e.tar';watch(lp,config['source_verification']['libero']['archive_sha256'])
 with tarfile.open(lp) as z:
  ns=[n for n in z.getmembers() if n.name.endswith('/libero/libero/envs/env_wrapper.py') or n.name=='libero/libero/envs/env_wrapper.py'];ck(len(ns)==1,'frozen_LIBERO_wrapper');lb=z.extractfile(ns[0]).read();watch(P/'external/LIBERO/libero/libero/envs/env_wrapper.py',sha(lb));ck(b'OSC_POSE' in lb and b'load_controller_config' in lb,'same_LIBERO_controller_factory')
 evaluator=read('scripts/eval_formal_selector_libero.py').decode();fn={n.name:n for n in ast.walk(ast.parse(evaluator)) if isinstance(n,ast.FunctionDef) and n.name in ['factory','reseed']};ck(set(fn)=={'factory','reseed'},'factory_reseed_present');rn=ast.parse('def reseed():\n random.seed(17)\n np.random.seed(17)\n torch.manual_seed(17)\n').body[0];ck(astr(fn['reseed'])==astr(rn),'exact_Python_Numpy_Torch_reseed');factory=ast.get_source_segment(evaluator,fn['factory']);ck('env.seed(0)' in factory and 'camera_heights=256, camera_widths=256' in factory and 'OffScreenRenderEnv' in factory,'same_environment_factory')
 src=read('src/cti_vla/evaluation/formal_trials.py').decode();node=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='evaluate_formal_trials');ts=ast.get_source_segment(src,node);ck(ts.index('reseed()')<ts.index('env, instruction = environment_factory(state)')<ts.index('result = run_episode('),'exact_per_trial_reseed_call_order')
 runtime=load(S/'src/cti_vla/evaluation/libero_runtime.py','_ind_Object_runtime');adapter=load(ADAPTER,'_ind_Object_adapter');old,new,branchproof=adapter.derive_function(runtime,read(S/'src/cti_vla/evaluation/libero_runtime.py'));oldnode=next(n for n in ast.parse(read(S/'src/cti_vla/evaluation/libero_runtime.py')).body if isinstance(n,ast.FunctionDef) and n.name=='run_episode');newnode=copy.deepcopy(oldnode);removed=[];branch=ast.parse('if bool((np.abs(chunk.environment_actions) > 1.00001).any()):\n raise ValueError("environment action outside normalized controller [-1, 1] range")').body[0]
 def prune(n):
  for fld,v in ast.iter_fields(n):
   if isinstance(v,list):
    for c in list(v):
     if isinstance(c,ast.AST):
      if astr(c)==astr(branch):removed.append(c);v.remove(c)
      else:prune(c)
   elif isinstance(v,ast.AST):prune(v)
 prune(newnode);ck(len(removed)==1,'exact_single_pure_branch');ck(not any(isinstance(n,ast.Call) and any(w in ast.unparse(n.func) for w in ['random','seed','torch']) for n in ast.walk(removed[0])),'branch_no_RNG');ck(branchproof['original_function_ast_sha256']==sig(astr(oldnode)) and branchproof['replacement_function_ast_sha256']==sig(astr(newnode)) and branchproof==candidate['single_removed_branch_AST_proof'],'independent_full_AST_proof')
 v4={m:defaultdict(list) for m in ['dense','uniform128','A128_seed17','B128_seed17']}
 for e in [decode(b) for b in read(V4).splitlines()]:
  if e.get('suite')=='libero_object' and e.get('method_id') in v4:v4[e['method_id']][e['event']].append(e)
 osc=obj(site/'robosuite/controllers/config/osc_pose.json');ck(osc['control_delta'] and osc['type']=='OSC_POSE' and osc['input_max']==1 and osc['input_min']==-1,'wheel_default_controller');controllers=[]
 for m,es in v4.items():
  ck(len(es['cell_start'])==len(es['actual_controller_verified'])==len(es['policy_chunk'])==1,'one_actual_Object_cell');st=es['cell_start'][0];c=es['actual_controller_verified'][0]['controller'];ck(st['identity']==ids[m] and st['runtime_seed']==17 and st['environment_seed']==0,'actual_same_Object_model_RNG');ck(c['actual_use_delta'] and c['actual_delta_branch_enabled'] and c['configured_control_delta'] and c['set_goal_dispatches_to_bound_scale_action'],'actual_delta_controller');ck(c['limits']=={'input_max':[1.]*6,'input_min':[-1.]*6,'output_max':osc['output_max'],'output_min':osc['output_min']},'actual_controller_limits')
  for name,fr in c['methods'].items():
   ss=read(fr['path'],fr['sha256']).decode();nn=next(n for n in ast.walk(ast.parse(ss)) if isinstance(n,ast.FunctionDef) and n.name==name);ck(''.join(ss.splitlines(keepends=True)[nn.lineno-1:nn.end_lineno]).replace('\r\n','\n')==fr['source'] and astr(nn)==astr(ast.parse('class _Captured:\n'+fr['source']).body[0].body[0]),'actual_bound_source_exact_universal_newlines')
  controllers.append({'method':m,'state_identity':st['state_identity'],'runtime_rng_sha256':st['runtime_rng_sha256'],'limits':c['limits'],'bound_methods':{k:{x:v for x,v in z.items() if x!='source'} for k,z in c['methods'].items()}})
 # Independently parse complete original ledger with byte offsets; no author per-trial values drive this loop.
 raw={};starts={};refs={};jobmap={};invs=[];job=None;active=None;offset=0;per_task=defaultdict(Counter);traces=[];chunks=[];failures=[];t0=defaultdict(set)
 for line,b in enumerate(path(RUN+'/trials.jsonl').open('rb'),1):
  ck(b.endswith(b'\n'),'complete_raw_line');ref=lr(line,offset,b);offset+=len(b);row=decode(b);ck(row['run_signature']==original['run_signature'],'run_signature')
  if row['event']=='invocation':ck(active is None and row['slurm_job_id'] not in invs,'invocation_unique');job=row['slurm_job_id'];invs.append(job);continue
  if row['event']=='start':ck(active is None and job in JOBS,'known_start');active=row;starts[row['trial_id']]=ref;continue
  ck(row['event']=='result' and active is not None,'paired_result');tid=row['trial_id'];ck(tid not in raw,'unique_terminal')
  for k in ['action_chunk','configured_wait_steps','environment_seed','initial_state_sha256','method','run_signature','runtime_seed','source_state_index','split','state_trial_id','suite','task_id','task_name','trial_id']:ck(row[k]==active[k],'start_result_identity')
  active=None;raw[tid]=row;refs[tid]=ref;jobmap[tid]=job;state=stateby[row['state_trial_id']];ck(row['suite']=='libero_object' and row['split']=='development' and row['environment_seed']==0 and row['runtime_seed']==17 and row['wait_steps']==row['configured_wait_steps']==10 and row['action_chunk']==8,'raw_environment');ck(row['initial_state_sha256']==state['initial_state_sha256'] and row['task_id']==state['task_id'] and row['task_name']==state['task_name'] and row['source_state_index']==state['source_state_index'],'raw_fixed_state')
  ident=ids[row['method']];queue=[];mds=[]
  for ix,ch in enumerate(row['chunks']):
   ck(ch['control_step']==8*ix and len(ch['normalized_actions'])==len(ch['environment_actions'])==8,'full8_contiguous_chunks');a=np.asarray(ch['environment_actions'],dtype='<f8');nb=b64(ch['normalized_actions']);ab=b64(ch['environment_actions']);ck(bool((np.abs(a)<=1.00001).all()),'all_emitted_old_branch_false');ck(np.clip(a,-1.,1.).tobytes()==ab and np.clip(a[:,:6],-1.,1.).tobytes()==a[:,:6].tobytes(),'clip7_clip6_bytes_unchanged')
   md=ch['metadata'];ck(md['suite']=='libero_object' and md['method']==ident['method'] and md['visual_tokens']==ident['visual_tokens'] and md['future_head_calls']==0 and md['vision_calls']==md['packing_calls']==md['policy_calls']==1 and md['language_cache']=='disabled','chunk_method_metadata');ck(md['inputs_version']==runtime.INPUTS_VERSION and md['action_version']==runtime.ACTION_VERSION and md['packing_version']=='oft-original-positions-v1' and md['per_camera_budgets']==[ident['visual_tokens']//2]*2,'chunk_preprocess_packing')
   idx=md['retained_indices'];ck(len(idx)==len(set(idx))==ident['visual_tokens'] and all(type(x) is int and 0<=x<512 for x in idx) and sum(x<256 for x in idx)==ident['visual_tokens']//2,'token_indices')
   if ident['method'] in ['A','B']:ck(md['selector_checkpoint_sha256']==ident['checkpoint_sha256'],'actual_chunk_checkpoint')
   queue.extend(ch['environment_actions']);mds.append(sig(md));chunks.append({'trial_id':tid,'chunk_index':ix,'environment_f64le_sha256':sha(ab),'normalized_f64le_sha256':sha(nb),'metadata_sha256':sig(md),'observation_sha256':ch['observation_sha256']})
  ck(len(row['executed_actions'])==row['control_steps'] and b64(queue[:row['control_steps']])==b64(row['executed_actions']),'exact_queue_to_executed');ck(row['chunks'] and row['control_steps']<=280,'bounded_nonempty');t0[row['state_trial_id']].add(row['chunks'][0]['observation_sha256']);per_task[str(row['task_id'])].update(trials=1,chunks=len(row['chunks']),actions=row['control_steps'],success=int(row['success']),policy_errors=int(row['status']=='policy_error'))
  if row['status']!='completed':failures.append(tid);continue
  ck(row['policy_calls']==len(row['chunks'])==math.ceil(row['control_steps']/8),'completed_chunks_count');ck(row['termination']==('environment_success' if row['success'] else 'task_horizon') and (row['success'] or row['control_steps']==280),'terminal_semantics')
  # CPU boundary replay uses actual fixed initial vector and recorded chunks, never model/simulator inference.
  obs={'agentview_image':np.zeros((2,2,3),dtype=np.uint8),'robot0_eye_in_hand_image':np.zeros((2,2,3),dtype=np.uint8),'robot0_eef_pos':np.zeros(3),'robot0_eef_quat':np.array([0.,0.,0.,1.]),'robot0_gripper_qpos':np.zeros(2)}
  class Boundary:
   def __init__(self):self.actions=[];self.initial=None;self.resets=0
   def reset(self):self.resets+=1;return obs
   def set_init_state(self,v):self.initial=np.asarray(v,dtype='<f8').tobytes();return obs
   def step(self,a):self.actions.append(list(a));return obs,0.,bool(row['success'] and len(self.actions)==10+row['control_steps']),{}
  class Recorded:
   def reset(self):self.index=0
   def __call__(self,o,text):
    ch=row['chunks'][self.index];self.index+=1;return runtime.PolicyChunk(np.asarray(ch['normalized_actions'],dtype=np.float32),np.asarray(ch['environment_actions'],dtype=np.float64),ch['metadata'])
  pair=[]
  for fun in [old,new]:
   env=Boundary();pr=Recorded();before=rng();o=fun(env,pr,'CPU recorded actions only',state['initial_state'],wait_steps=10,max_steps=280,policy_watchdog_seconds=60.)
   ck(before==rng(),'CPU_Python_Numpy_RNG_unchanged');ck(env.resets==1 and env.initial==np.asarray(state['initial_state'],dtype='<f8').tobytes(),'CPU_reset_initial_vector')
   for k in ['status','success','termination','policy_calls','control_steps','wait_steps']:ck(o[k]==row[k],'CPU_terminal_original')
   ck(b64(env.actions[:10])==b64([list(runtime.DUMMY_ACTION)]*10),'CPU_waits_original');ck(b64(env.actions[10:])==b64(row['executed_actions'])==b64(o['executed_actions']),'CPU_boundary_actions_original');ck(len(o['chunks'])==len(row['chunks']),'CPU_complete_chunks')
   for x,y in zip(o['chunks'],row['chunks']):ck(x['control_step']==y['control_step'] and b64(x['normalized_actions'])==b64(y['normalized_actions']) and b64(x['environment_actions'])==b64(y['environment_actions']) and x['metadata']==y['metadata'],'CPU_complete_chunk_equivalence')
   pair.append({'executed_f64le_sha256':sha(b64(env.actions[10:])),'all_wait_and_control_actions_f64le_sha256':sha(b64(env.actions)),'python_numpy_RNG_unchanged':True,'new_GPU_or_simulator_execution':False})
  ck(pair[0]==pair[1],'CPU_old_current_equivalence');traces.append({'trial_id':tid,'source_job_id':job,'start':starts[tid],'result':ref,'task_id':row['task_id'],'source_state_index':row['source_state_index'],'method':row['method'],'status':row['status'],'success':row['success'],'initial_state_sha256':row['initial_state_sha256'],'full_chunks':len(row['chunks']),'control_steps':row['control_steps'],'all_emitted_f64le_sha256':sha(b64(queue)),'metadata_sequence_sha256':sig(mds),'old_runtime_replay':pair[0],'current_runtime_replay':pair[1]})
 ck(invs==JOBS and active is None,'all_old_invocations_closed');ck(list(raw)==[s['trial_id']+':'+m for s in panel['states'] for m in METHODS] and len(raw)==600,'all600_fixed_cells_order');ck(len(traces)==599 and failures==[BAD],'599plus1exception');ck(all(len(v)==1 for v in t0.values()) and len(t0)==100,'same_t0_across_methods100states')
 failed=raw[BAD];ck(failed['status']=='policy_error' and failed['success'] is False and failed['error']=='environment action outside normalized controller [-1, 1] range' and failed['termination']=='ValueError' and failed['error_phase']=='policy' and failed['policy_calls']==8 and len(failed['chunks'])==7 and failed['control_steps']==56,'exact_failed_semantics');ck(jobmap[BAD]=='3021844' and failed['task_id']==8 and failed['source_state_index']==49 and failed['method']=='dense','exact_failed_identity')
 ledger=runtime.TrialLedger.__new__(runtime.TrialLedger);ledger.events=[failed];ck(BAD in ledger.completed(),'ordinaryresume_skips_policyerror')
 normal={'trials':len(traces),'chunks':sum(x['full_chunks'] for x in traces),'actions':sum(x['control_steps'] for x in traces)};allcounts={'trials':len(raw),'chunks':sum(len(x['chunks']) for x in raw.values()),'actions':sum(x['control_steps'] for x in raw.values())};ck(normal=={'trials':599,'chunks':11720,'actions':91945} and allcounts=={'trials':600,'chunks':11727,'actions':92001},'independent_totals')
 author_rows=[decode(b) for b in read(A/'per_trial_599.jsonl').splitlines()];ab={x['trial_id']:x for x in author_rows};ck(len(ab)==599,'author_unique599')
 for x in traces:
  y=ab[x['trial_id']]
  for k,v in x.items():ck(y[k]==v,'author_trial_recomputed')
  ck(y['method_identity']==ids[x['method']] and not y['reuse_authorized'] and y['clip_changed_all7']==y['clip_changed_arm6']==0 and y['all_chunks_finite_old_threshold'] and y['old_execution_version']=='formal-downstream-root-v1' and y['target_action_semantics_sha256']==SEM,'author_trial_semantics')
 ck([decode(b) for b in read(A/'per_chunk_all600.jsonl').splitlines()]==chunks,'author_all600chunks_recomputed')
 fa=obj(A/'failed_trial_retained.json');ck(fa['result']==refs[BAD] and fa['start']==starts[BAD] and fa['executed_float64le_sha256']==sha(b64(failed['executed_actions'])) and fa['rejected_eighth_chunk_recorded'] is False and fa['new_semantics_outcome_unknown'] is True and fa['exact_offending_axis_value_recoverable'] is False,'author_failure_exact')
 alloc=original['cost']['allocations'];ck([x['job_id'] for x in alloc]==JOBS and [x['elapsed_seconds'] for x in alloc]==[386,1401,4926] and all(x['gpus']==1 and x['status']=='COMPLETED' and x['exit_code']=='0:0' for x in alloc) and sum(x['gpus']*x['elapsed_seconds'] for x in alloc)==6713,'all6713seconds_once')
 comparisons=[]
 for m,e in v4.items():
  st=e['cell_start'][0]['state_identity'];row=raw[st['trial_id']+':'+m];ch=e['policy_chunk'][0];same=b64(ch['environment_actions'])==b64(row['chunks'][0]['environment_actions']);ck(same,'actual_Object_current_firstchunk_equal');comparisons.append({'method':m,'state_trial_id':st['trial_id'],'same_first_chunk':same,'actual_current_controls':8,'not_whole_trajectory_capture':True})
 tb={x['trial_id']:x for x in traces}
 def validate(c,rows,f):
  ck(c==candidate,'immutable_candidate_semantics');ck(c['kind']=='Object_legacy599_source_trace_candidate' and c['suite']=='libero_object' and c['split']=='development' and c['legacy_root']=={'path':OLDROOT,'sha256':PINS[OLDROOT]} and c['raw_ledger']=={'path':RUN+'/trials.jsonl','sha256':PINS[RUN+'/trials.jsonl']},'typed_exact_old_scope');ck(c['target']['action_semantics_sha256']==SEM and c['target']['contract']=={'path':TARGET,'sha256':PINS[TARGET]} and c['method_identities']==ids,'typed_exact_current_identity');ck(c['historical_jobs_once']==JOBS and c['historical_GPU_seconds']==6713 and c['original_allocations']==alloc,'typed_complete_cost');ck(c['old_invocation_ran_current_wrapper'] is False and c['old_controller_instance_hash_recorded'] is False and c['old_RNG_dump_recorded'] is False and c['production_reuse_authorized'] is False and c['final_release'] is False and c['new_GPU_seconds']==0 and c['accepted_scientific_trials_added']==0,'typed_no_invented_execution');ck(len(rows)==599 and len({x['trial_id'] for x in rows})==599 and {x['trial_id'] for x in rows}==set(raw)-{BAD},'typed_full599_set')
  for x in rows:ck(x==tb[x['trial_id']],'typed_exact_trial_trace')
  ck(f==fa and f['trial_id']==BAD and f['status']=='policy_error' and f['success'] is False and not f['rejected_eighth_chunk_recorded'] and not f['adopted'],'typed_failed_original_retained')
 validate(candidate,traces,fa);negatives=[]
 mutations=['missing_trial','duplicate_trial','extra_failed_trial','changed_action_hash','changed_chunk_hash','changed_outcome','changed_source_job','wrong_task','wrong_initial_state','wrong_method','wrong_pair_checkpoint','wrong_model','wrong_source','wrong_config','wrong_target_semantics','wrong_stage','wrong_suite','fake_old_current_wrapper','fake_old_controller_capture','fake_old_RNG_capture','invent_failed_chunk','failed_as_success','drop_failed','cost_drop_job','cost_lower','production_admitted','final_release','extra_GPU','changed_raw_hash']
 for name in mutations:
  c=copy.deepcopy(candidate);rows=copy.deepcopy(traces);f=copy.deepcopy(fa)
  if name=='missing_trial':rows.pop()
  elif name=='duplicate_trial':rows[-1]=copy.deepcopy(rows[0])
  elif name=='extra_failed_trial':rows.append(copy.deepcopy(rows[0]));rows[-1]['trial_id']=BAD
  elif name=='changed_action_hash':rows[0]['current_runtime_replay']['executed_f64le_sha256']='0'*64
  elif name=='changed_chunk_hash':rows[0]['all_emitted_f64le_sha256']='0'*64
  elif name=='changed_outcome':rows[0]['success']=not rows[0]['success']
  elif name=='changed_source_job':rows[0]['source_job_id']='3042529'
  elif name=='wrong_task':rows[0]['task_id']=8
  elif name=='wrong_initial_state':rows[0]['initial_state_sha256']='0'*64
  elif name=='wrong_method':rows[0]['method']='B128_seed17'
  elif name=='wrong_pair_checkpoint':c['method_identities']['A128_seed17']['checkpoint_sha256']='0'*64
  elif name=='wrong_model':c['method_identities']['dense']['frozen_model_sha256']='0'*64
  elif name=='wrong_source':c['method_identities']['dense']['source_sha256']='0'*64
  elif name=='wrong_config':c['method_identities']['dense']['config_sha256']='0'*64
  elif name=='wrong_target_semantics':c['target']['action_semantics_sha256']='0'*64
  elif name=='wrong_stage':c['split']='final'
  elif name=='wrong_suite':c['suite']='libero_spatial'
  elif name=='fake_old_current_wrapper':c['old_invocation_ran_current_wrapper']=True
  elif name=='fake_old_controller_capture':c['old_controller_instance_hash_recorded']=True
  elif name=='fake_old_RNG_capture':c['old_RNG_dump_recorded']=True
  elif name=='invent_failed_chunk':f['rejected_eighth_chunk_recorded']=True
  elif name=='failed_as_success':f['status']='completed';f['success']=True
  elif name=='drop_failed':f={}
  elif name=='cost_drop_job':c['historical_jobs_once'].pop(0)
  elif name=='cost_lower':c['historical_GPU_seconds']=4926
  elif name=='production_admitted':c['production_reuse_authorized']=True
  elif name=='final_release':c['final_release']=True
  elif name=='extra_GPU':c['new_GPU_seconds']=1
  elif name=='changed_raw_hash':c['raw_ledger']['sha256']='0'*64
  try:validate(c,rows,f)
  except (AssertionError,KeyError,ValueError):negatives.append({'case':name,'rejected':True})
  else:raise AssertionError('mutation admitted '+name)
 for k,v in SEEN.items():ck(filehash(path(k))==v['sha256'],'evidence_unchanged_end')
 proofref=out('per_trial_independent_599.jsonl',traces,True);chunkref=out('per_chunk_independent_all600.jsonl',chunks,True);wheelref=out('installed_wheel_members.json',wheelmembers)
 hist=out('historical_controller_reconstruction.json',{'Git_anchor':{'commit':anchor,'commit_time':t,'files':gitrows},'old_Object_actual_journals':history,'wheels':wheelrows,'installed_members':wheelref,'matched_members':len(wheelmembers),'installed_ctime_mtime_before_first_old_job':True,'old_controller_instance_hash_recorded':False,'old_RNG_dump_recorded':False,'historical_basis':'Source-derived from Object own archive journals, pre-job Git installation evidence, exact current wheel bytes and earlier unchanged ctime/mtime. Not a retrospective capture of old controller instances.','actual_current_Object_cells':controllers,'bounded_first_chunk_comparisons':comparisons,'factory_source':factory,'reseed_source':ast.get_source_segment(evaluator,fn['reseed']),'full_AST_proof':branchproof})
 fr=out('failed_trial_independent.json',{'trial_id':BAD,'raw_ledger':{'path':RUN+'/trials.jsonl','sha256':PINS[RUN+'/trials.jsonl']},'job_id':jobmap[BAD],'start':starts[BAD],'result':refs[BAD],'task_id':8,'source_state_index':49,'method':'dense','initial_state_sha256':failed['initial_state_sha256'],'status':'policy_error','success':False,'recorded_chunks':7,'recorded_actions':56,'policy_calls':8,'rejected_query8_chunk_unknown':True,'offending_axis_value_unknown':True,'ordinary_resume_skips':True,'original6713seconds_retained_once':True,'new_outcome_unknown':True})
 design={'schema':'formal_main_v2','kind':'Object_single_policy_error_linked_correction_CPU_design_requirements','status':'design_only_HOLD_no_execution_authority','legacy_failure':fr,'registration':{'path':REG,'sha256':PINS[REG]},'fixed_cell':{'suite':'libero_object','split':'development','task_id':8,'source_state_index':49,'method':'dense','trial_id':BAD,'initial_state_sha256':failed['initial_state_sha256']},'scientific_environment':manifest['environment'],'method_identity':ids['dense'],'target_action_semantics_sha256':SEM,'requirements':['Explicit root adoption of independent599 proof with canonical source/controller receipts; no adoption by this design.','Separate exact one-cell invocation, fresh output and append-only ledger. Link immutable old failed start/result SHA, all3 old job IDs, current semantics and unique submission token/comment. Never edit old600 or inject invocation/result into old ledger.','Fresh reset of same original fixed initial vector: seed17/env0/wait10/chunk8/horizon280 unchanged. Old56 steps are provenance, not a simulator checkpoint. No fabricated query8 or guessed offending value.','At most one explicit new execution after exact gateway/runtime/reviewer/consumer CPU audit and real-P --verify. Enforce all-mode8slots, no duplicate logical-cell active job, terminal controller lease, writer.lock/CAS, exact pending/ACK reconciliation. Failed/timeout/preempted/unknown submits HOLD, no automatic retry.','Keep old policy_error and new outcome separately. Typed assembly may map599compatible legacy cells plus one accepted current correction to original600 logical cells only after root+independent terminal review. Preserve original600 summary and raw. New failures remain failures, never retry until successful.','Before/after recheck old raw-prefix hash, exact manifests and current source/officialObject base/controller identities. No checkpoint reselection/scientific changes. Diagnostics only prospective; old query8 remains unknown.','Count original386+1401+4926=6713seconds once at shared allocation level plus each new allocation once, including loading/failed jobs. Never attach6713 to each compatible row. No new independent initial state.','No final-state, final-release, profile or wider cell access. All72/16/four-suite freeze and fullO2A gates remain.'],'negative_tests_required':['ordinaryresume skips policyerror','wrongcell/suite/stage/method','changedstate/RNG/environment/model/source','missingfailure or fabricatedquery8','discarded/doublecountedcost','duplicateattempt/ACK/token','unknownactive/pending/lease/capacity','wrongactionsemantics','outcomeselection/autoretry','final/profile/sealedaccess'],'new_GPU_seconds':0,'new_scientific_trials':0,'production_or_P_change':False}
 dr=out('single_error_correction_design.json',design);checks=out('check_summary.json',{'positive_assertions_by_category':dict(COUNTS),'positive_assertion_count':sum(COUNTS.values()),'negative_cases':negatives,'negative_count':len(negatives),'author_files_verified':17,'canonical_archive_files_verified':18});evidence=out('evidence_inventory.json',SEEN)
 report={'schema':'formal_main_v2','kind':'Object599_legacy_compatibility_independent_review','status':'passed','reviewed_by':'independent_agent_object599_20261020T2253','author_stage1_manifest_sha256':MANSHA,'compatibility_proof_sha256':CANDSHA,'scope':{'suite':'libero_object','split':'development','normal_legacy_trials':599,'raw_historical_trials':600,'retained_policy_errors':1,'methods':METHODS,'fixed_unique_development_states':100,'tasks':10},'counts':normal,'retained_all_counts':allcounts,'all_original_GPU_seconds':6713,'original_jobs':JOBS,'per_task_original':{k:dict(v) for k,v in sorted(per_task.items(),key=lambda q:int(q[0]))},'same_t0_across_methods_all100':True,'source173_verified':True,'source_model_checkpoint_initial_state_controller_RNG_verified':True,'actual_old_controller_instance_capture':False,'old_RNG_dump_required':False,'historical_environment_basis':'Object-specific source chain and immutable wheel/install evidence; not invented old-instance capture.','new_rollout_or_inference':False,'CPU_replay_scope':'Recorded chunks exercised through both pinned loops on fake environment/observation boundary; not LIBERO or policy rerun.','source_history':hist,'per_trial_proof':proofref,'per_chunk_proof':chunkref,'original_consumer':oldcheck,'failure':fr,'single_failure_design':dr,'checks':checks,'evidence':evidence,'archived_author_files':archive,'blockers':[],'admission_conditions':['Root explicit adoption must bind this independent receipt and canonical author/provenance archive; identify599 as legacy-equivalent, never current-wrapper generated.','Separately audited exact typed consumer preserves599 compatible +1unresolved mapping within original600 cells, original failure and6713seconds. This review does not install/execute that consumer.','Only after separately registered one-cell correction and root/independent terminal receipt may corrected600 logical view be assembled; prior failure remains. No whole600 compatibility admission now.','Global final-release, four-suite development receipts and completeO2A freeze gates remain closed.'],'whole600_compatibility_admitted':False,'production_reuse_authorized':False,'final_release':False,'final_state_values_read':False,'new_scientific_trials':0,'new_GPU_seconds':0,'CPU_seconds':time.process_time()-CPU,'wall_seconds':time.perf_counter()-START}
 rr=out('independent_review.json',report);print(json.dumps({'review':rr,'counts':normal,'all_counts':allcounts,'assertions':sum(COUNTS.values()),'negative_cases':len(negatives),'wheel_members':len(wheelmembers),'status':'passed'}),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  import traceback
  out('failure_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json',{'status':'failed','error':str(exc),'traceback':traceback.format_exc(),'checks_completed':dict(COUNTS),'new_GPU_seconds':0});raise
