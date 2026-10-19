"""Independent read-only audit of exact CUDA recovery job3039258.
Writes only this private audit directory. No tensor deserialization, scheduler,
Git or state writes; no new continuation authorization.
"""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,ast,hashlib,importlib.util,json,math,os,random,re,stat,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
H=Path('/share/home/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/cuda_recovery_independent_0943'
REL='results/formal_main_v2/libero_object/k256/seed23/training'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
AUTH='configs/experiments/formal_main_v2_cuda_single_recovery_3028460_v1.json'
PIN='2399d0f5b92b7ffe1d007d1df6fb1914b2c9765099bb8948bc9027873c6041ec'
SOURCE='dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
readmap={};servermap={}
def need(ok,msg):
 if not ok:raise ValueError(msg)
def sig(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def safe(rel):
 need(isinstance(rel,str) and rel and not rel.startswith('/') and '..' not in rel.split('/') and '\\' not in rel,'relative path')
 q=Path(rel)
 need(not any(x in {'test','sealed','final','weights','checkpoints'} or 'sealed' in x.lower() for x in q.parts),'forbidden evidence path')
 need(q.suffix not in {'.pt','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'},'tensor/state path')
 need(not any(x in rel.lower() for x in ['init_state','initial_state','final_state','test_state']) or q.suffix=='.py','state value forbidden')
 return q
def raw(rel,expected=None):
 p=R/safe(rel)
 need(p.resolve()==p and not p.is_symlink(),'noncanonical evidence')
 data=p.read_bytes();sha=hashlib.sha256(data).hexdigest()
 need(expected is None or sha==expected,'SHA mismatch '+rel)
 need(rel not in readmap or readmap[rel]==sha,'changed '+rel);readmap[rel]=sha
 return data
def read(rel,expected=None):return json.loads(raw(rel,expected))
def shafile(p):
 need(p.resolve()==p and not p.is_symlink(),'noncanonical server file')
 with p.open('rb') as f:
  a=os.fstat(f.fileno());need(stat.S_ISREG(a.st_mode),'not regular')
  h=hashlib.sha256()
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
  z=os.fstat(f.fileno())
  need((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'changed during hash')
 need((z.st_ino,z.st_size,z.st_mtime_ns)==tuple(getattr(p.stat(),k) for k in ['st_ino','st_size','st_mtime_ns']),'replaced after hash')
 servermap[str(p)]=h.hexdigest()
 return {'path':str(p),'sha256':h.hexdigest(),'bytes':z.st_size,'exists':True}
def jrows(rel):
 data=raw(rel);need(data.endswith(b'\n'),'truncated journal')
 rows=[json.loads(x) for x in data.splitlines()]
 need(all(isinstance(x,dict) for x in rows),'bad journal row')
 return rows
def close(a,b,msg='number'):
 need(type(a) in (int,float) and math.isfinite(a) and math.isclose(a,b,rel_tol=1e-7,abs_tol=1e-9),msg)
def load(rel):
 p=R/safe(rel);raw(rel)
 m=importlib.util.module_from_spec(importlib.util.spec_from_file_location('audit_'+p.stem,p))
 sys.modules[m.__name__]=m;m.__spec__.loader.exec_module(m);return m
class Evidence:
 root=R
 def read(self,p):return read(str(p.relative_to(R)) if isinstance(p,Path) else p)
 def watch(self,p):
  rel=str(p.relative_to(R)) if isinstance(p,Path) else p;raw(rel);return readmap[rel]
def main(args):
 rootrel=REL+'/segment_reviews/3039258.json'
 root=read(rootrel,args.root_review_sha256)
 need(root['status']=='passed' and root['job_id']=='3039258' and root['completed_by_arm']=={'A':500,'B':500},'root recovery boundary')
 need(root['suite']=='libero_object' and root['visual_tokens']==256 and root['seed']==23 and root['requested_segment_end']==500,'root pair')
 need(root['source_sha256']==SOURCE and root['pair_allocated_gpu_seconds']==6596,'root source/cost')
 need(root['completed_training_receipts']==[] or root['completed_training_receipts']=={},'not a final5000 receipt')
 inv=read(INV,'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 need(len(inv['files'])==173 and inv['source_sha256']==SOURCE,'inventory')
 for rel,sha in inv['files'].items():
  raw(rel,sha);need(shafile(S/rel)['sha256']==sha,'actual frozen source '+rel)
 auth=read(AUTH,PIN)
 need(auth['original_target']==500 and auth['maximum_new_attempts']==1 and auth['resume'] is True,'target scope')
 need(auth['continuous5000_admission_authorized'] is False and auth['automatic_retry'] is False,'no new scope')
 for rel,sha in {**auth['original_recovery_files'],**auth['gateway_files']}.items():raw(rel,sha)
 for key in ['canonical_publication','root_reservation','repair_record','independent_review','node_exclusion','controller_activation']:
  rr=auth[key];raw(rr['path'],rr['sha256'])
 jobs=root['registered_pair_jobs_at_review']
 need(len(jobs)==2 and {str(j['job_id']) for j in jobs}=={'3028460','3039258'},'exact failed+recovery history')
 byid={str(j['job_id']):j for j in jobs};oldj=byid['3028460'];job=byid['3039258']
 need((oldj['status'],oldj['exit_code'],oldj['elapsed_seconds'],oldj['gpus'])==('FAILED','1:0',84,1),'failed bill preserved')
 need((job['status'],job['exit_code'],job['elapsed_seconds'],job['gpus'],job['node'])==('COMPLETED','0:0',6512,1,'gpu4010'),'terminal recovery bill')
 need(job['startup_recovery']['authorization']=={'path':AUTH,'sha256':PIN} and job['startup_recovery']['failed_job_id']=='3028460','recovery binding')
 sbatch=job['startup_recovery']['actual_sbatch_argv']
 for item in ['--no-requeue','--time=04:00:00','--exclude=gpu4020']:need(item in sbatch,'sbatch bound '+item)
 original=read(oldj['invocation'],oldj['invocation_sha256']);current=read(job['invocation'],job['invocation_sha256'])
 need({k for k in set(original)|set(current) if original.get(k)!=current.get(k)}=={'argv','registered_utc','repair_record'},'only explicit recovery differences')
 need(current['argv']==original['argv']+['--resume'],'science argv unchanged')
 need(current['argv'][current['argv'].index('--stop-after-updates')+1]=='500','original target')
 need(current['argv'][current['argv'].index('--max-wall-seconds')+1]=='12600','original wall')
 need(current['repair_record']==str(R/auth['repair_record']['path']),'repair bound')
 need(current.get('runtime_compatibility')==job['runtime_compatibility']==oldj['runtime_compatibility'],'same metadata adapter')
 for rel,sha in job['runtime_compatibility']['files'].items():
  raw(rel,sha);need(shafile(P/rel)['sha256']==sha,'runtime source on P')
 failuremod=load('.local/cuda_startup_recovery_0840/startup_failure_evidence.py')
 failure=failuremod.require_saved(Evidence(),job=oldj)
 need(failure['completed_by_arm']=={'A':0,'B':0} and failure['next_sample_cursor']=={'A':0,'B':0},'historical no updates')
 need(failure['current_allocation_arm_initializations']==0 and failure['current_allocation_new_updates']==0,'failed before initialization')
 need(all(x['exists'] is False for x in failure['server_resume_checks']),'historical no checkpoint')
 need(root['startup_failure_history']['3028460']==failure,'root preserves exact failed proof')
 configrel='configs/experiments/formal_main_v2/libero_object_k256_seed23.json'
 config=read(configrel,inv['files'][configrel])
 need(read(REL+'/registered_config.json')==config,'exact run config')
 need(config['seed']==23 and config['tokens_per_camera']==128 and config['training']['updates']==5000 and config['training']['effective_batch']==8,'formal configuration')
 need(config['selection']['updates']==list(range(0,5001,500)),'11-node original selection')
 gate=read('results/formal_main_v2/libero_object/acceptance/root_review.json')
 need(gate['status']=='passed' and gate['suite']=='libero_object' and gate['source_sha256']==SOURCE,'own accepted GPU')
 for name,sha in gate['files'].items():raw(gate['output_relative']+'/'+name,sha)
 f00=read(gate['output_relative']+'/input_acceptance.json')
 for rel,sha in gate['source_files'].items():raw(rel,sha)
 protocol=read(config['data']['protocol'])
 manifest=read(config['data']['windows'])
 sys.path.insert(0,str(R/'src'))
 from cti_vla.data.formal_windows import load_formal_protocol,load_formal_windows
 checked_protocol=load_formal_protocol(R/config['data']['protocol'],project_root=R)
 checked_manifest=load_formal_windows(R/config['data']['windows'],checked_protocol)
 need(checked_manifest==manifest,'full legal windows validation')
 train=manifest['train_window_ids'];val=manifest['validation_window_ids'];lookup={r['window_id']:r for r in manifest['windows']}
 need(len(train)==44068 and len(set(train))==len(train) and len(val)==204 and len(set(val))==204,'full Object pools')
 need(not set(train)&set(val),'split overlap')
 need(not {lookup[x]['episode_id'] for x in train}&{lookup[x]['episode_id'] for x in val},'episode overlap')
 rng=random.Random(23);order=[]
 while len(order)<40000:
  epoch=list(train);rng.shuffle(epoch);order.extend(epoch)
 order=order[:40000]
 constants={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(raw('src/cti_vla/training/formal_future.py').decode()).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith('FORMAL_')}
 reports={};initial_rows={};summaries={};resumechecks=[]
 for arm in ['A','B']:
  base=REL+'/'+arm;report=read(base+'/progress_report.json');reports[arm]=report
  for key,value in {'schema':'formal_main_v2','arm':arm,'training_updates_completed':500,'next_sample_cursor':4000,'committed_samples':4000,'attempted_forward_backward_samples_completed':4000,'unique_committed_windows':4000,'train_pool_windows':44068,'planned_updates':5000,'vla_parameters_unchanged':True,'final_deployment_receipt_emitted':False,'status':'checkpointed','stop_reason':'registered_engineering_segment_boundary','job_ids':['3039258']}.items():need(report.get(key)==value,'report '+arm+' '+key)
  need(report['frozen_model_sha256']==f00['frozen_model_sha256'],'same frozen model')
  identity=report['identity']
  need(identity['training_source_files']==gate['source_files'] and identity['pair_config_sha256']==sig(config) and identity['training_config_sha256']==sig({**config,'arm':arm}),'training identity')
  for key,rel in [('window_manifest_sha256',config['data']['windows']),('data_protocol_sha256',config['data']['protocol']),('input_acceptance_sha256',gate['output_relative']+'/input_acceptance.json'),('f01_report_sha256',gate['output_relative']+'/f01_k256.json'),('resume_acceptance_sha256',gate['output_relative']+'/resume_acceptance.json'),('resume_journal_sha256',gate['output_relative']+'/f03_calls.jsonl')]:need(identity[key]==readmap[rel],'data/gate identity '+key)
  need(identity['training_version']==constants['FORMAL_TRAINING_VERSION'] and identity['training_numerics']==constants['FORMAL_NUMERICS'],'training numerics')
  savedorder=read(base+'/training_order.json')
  need(savedorder['samples']==order and savedorder['order_sha256']==sig(order)==report['sample_order_sha256'],'entire fixed order')
  need(savedorder['train_pool_sha256']==sig(train) and savedorder['initial_scorer_sha256']==report['initial_scorer_sha256'],'pool/initial')
  bytask=defaultdict(list)
  for wid in order[:4000]:bytask[str(lookup[wid]['task_id'])].append(wid)
  sampling={t:{'samples':len(ids),'unique_windows':len(set(ids)),'unique_episodes':len({lookup[i]['episode_id'] for i in ids}),'phase_sample_counts':dict(Counter(lookup[i]['phase'] for i in ids))} for t,ids in bytask.items()}
  need(sampling==report['committed_sampling_by_task'],'full actual sampling')
  paths=sorted((R/base/'attempts').glob('*/cost_events.jsonl'));need(len(paths)==1,'one clean arm attempt only')
  path=paths[0];attempt=path.parent.name;rows=jrows(path.relative_to(R).as_posix())
  start=rows[0]
  need(start['event']=='attempt_start' and start['resumed'] is False and start['completed_update']==0 and start['next_sample_cursor']==0 and start['identity']==identity,'fresh exact start after no-update failure')
  need(all(r['job_id']=='3039258' and r['attempt_id']==attempt for r in rows),'job/attempt identity')
  need(all(a['attempt_elapsed_seconds']<=b['attempt_elapsed_seconds'] for a,b in zip(rows,rows[1:])),'monotonic journal')
  cur=0;active=None;micro=0;sample=False;validating=None;ended=False;commits=[];evaluations=[];seenval={};sample_ids=[];grad=[];updatesec=[]
  for r in rows[1:]:
   e=r['event'];need(not ended,'work after attempt_end')
   if e=='update_start':
    need(active is None and validating is None and r['update']==cur+1,'sequential update')
    if cur%50==0:need(commits and commits[-1]['completed_update']==cur,'50-step durable commit')
    active=cur+1;micro=0;need(r['window_ids']==order[(active-1)*8:active*8],'actual batch order')
   elif e in ['sample_start','sample_end']:
    need(active is not None and micro<8 and r['update']==active and r['micro_batch_index']==micro and r['window_id']==order[(active-1)*8+micro],'actual sample')
    need((e=='sample_start')!=sample,'sample pair')
    sample=e=='sample_start'
    if not sample:micro+=1;sample_ids.append(r['window_id'])
   elif e=='update_end':
    need(active==r['update'] and micro==8 and not sample and r['forward_backward_samples']==8,'exact eight gradients per update')
    close(r['alpha'],.1+.95*(1+math.cos(math.pi*(active-1)/4999)),'5000 alpha')
    for k in ['grad_norm','loss','action_loss','teacher_l1','demonstration_l1','seconds']:need(math.isfinite(r[k]) and r[k]>=0,'finite objective')
    close(r['action_loss'],.5*(r['teacher_l1']+r['demonstration_l1']),'A objective')
    close(r['loss'],r['action_loss']+(0 if arm=='A' else .1*r['future_mse']),'matched B auxiliary')
    grad.append(r['grad_norm']);updatesec.append(r['seconds']);cur=active;active=None
   elif e=='validation_start':
    need(active is None and validating is None and r['update']==cur and cur in [0,500] and r['windows']==204,'validation complete registered node');validating=cur
   elif e=='validation_end':
    need(validating==r['update'] and r['window_forwards']==204,'validation pairing')
    vr=base+'/attempts/'+attempt+'/validation_'+str(validating).zfill(5)+'.json';v=read(vr,r['artifact_sha256'])
    need(v['arm']==arm and v['update']==validating and v['job_id']=='3039258' and v['attempt_id']==attempt and v['windows']==204 and v['tasks']==10 and v['metric']=='task_macro_hard_validation_teacher_l1','validation identity')
    obs=v['observations'];need([x['window_id'] for x in obs]==val,'all204 ordered windows')
    task=defaultdict(list)
    for x in obs:
     ref=lookup[x['window_id']];need(x['episode_id']==ref['episode_id'] and x['task_id']==ref['task_id'],'window identity')
     ix=x['retained_indices'];need(len(ix)==256 and ix==sorted(set(ix)) and all(type(i)==int and 0<=i<512 for i in ix) and sum(i<256 for i in ix)==128,'hard256 sorted packing')
     actions=x['normalized_actions'];need(len(actions)==8 and all(len(a)==7 for a in actions) and all(math.isfinite(y) for a in actions for y in a),'finite8x7')
     need(x['teacher_l1']>=0 and x['demonstration_l1']>=0,'nonnegative error');task[str(x['task_id'])].append(x)
    metric=sum(sum(x['teacher_l1'] for x in xs)/len(xs) for xs in task.values())/10
    expert=sum(sum(x['demonstration_l1'] for x in xs)/len(xs) for xs in task.values())/10
    close(v['validation_metric'],metric);close(r['validation_metric'],metric);close(v['demonstration_l1'],expert)
    for t,xs in task.items():
     need(v['per_task'][t]['windows']==len(xs),'per task count')
     for key in ['teacher_l1','demonstration_l1']:close(v['per_task'][t][key],sum(x[key] for x in xs)/len(xs))
    close(v['window_weighted_teacher_l1_diagnostic'],sum(x['teacher_l1'] for x in obs)/204)
    seenval[validating]=v;evaluations.append({'update':validating,'teacher_l1':metric,'expert_l1':expert,'windows':204,'artifact_sha256':readmap[vr]});validating=None
   elif e=='checkpoint_commit':
    need(active is None and validating is None and r['completed_update']==cur and re.fullmatch('[a-f0-9]{64}',r['resume_sha256']),'checkpoint commit')
    commits.append(r)
   elif e=='attempt_end':
    need(active is None and validating is None and cur==500 and commits[-1]['completed_update']==500 and r['status']=='checkpointed' and r['completed_update']==500,'clean committed stop');ended=True
   else:raise ValueError('unknown training event '+e)
  need(ended and cur==500 and sample_ids==order[:4000] and len(sample_ids)==4000 and len(set(sample_ids))==4000,'no skipped/replayed work')
  need(set(r['completed_update'] for r in commits)==set(range(0,501,50)) and commits[-1]['resume_sha256']==report['resume_sha256'],'all durable checkpoints')
  need(len(grad)==500 and max(grad)>0,'gradient evidence')
  need([e['update'] for e in report['evaluations']]==[0,500],'selection prefix')
  for ev in report['evaluations']:
   v=seenval[ev['update']];need(ev['artifact_path']==str(P/base/'attempts'/attempt/('validation_'+str(ev['update']).zfill(5)+'.json')),'selection raw')
   need(ev['artifact_sha256']==evaluations[ev['update']//500]['artifact_sha256'],'selection SHA');close(ev['validation_metric'],v['validation_metric'])
  initial_rows[arm]=[{k:x[k] for k in ['window_id','episode_id','task_id','teacher_l1','demonstration_l1','retained_indices','normalized_actions']} for x in seenval[0]['observations']]
  expected=H/'checkpoints/formal_main_v2/libero_object/k256/seed23'/arm/'resume.pt'
  need(report['resume_checkpoint']==str(expected),'resume scope')
  sc=shafile(expected);sc['arm']=arm;need(sc['sha256']==report['resume_sha256'],'real resume hash')
  need(sc==next(x for x in root['server_resume_checks'] if x['arm']==arm),'root same actual resume proof');resumechecks.append(sc)
  summaries[arm]={'completed_updates':500,'actual_samples':4000,'unique_samples':4000,'cursor':4000,'resumed_from_existing_checkpoint':False,'validation':evaluations,'earliest_current_best_update':min(evaluations,key=lambda e:(e['teacher_l1'],e['update']))['update'],'gradient_range':[min(grad),max(grad)],'resume_sha256':sc['sha256'],'journal_rows':len(rows),'checkpoint_commits':len(commits),'updates_wall_seconds_nested_diagnostic':sum(updatesec),'replayed_or_uncommitted_samples':0}
 need(initial_rows['A']==initial_rows['B'] and reports['A']['initial_scorer_sha256']==reports['B']['initial_scorer_sha256'],'matched initialization/initial hard behavior')
 pairprogress=read(REL+'/training_progress.json')
 need(pairprogress['arms']==reports and pairprogress['job_id']=='3039258' and pairprogress['pair_complete'] is False and pairprogress['test_opened'] is False and pairprogress['checkpoint_unchanged'] is True,'pair engineering stop')
 finals=list((R/REL/'finalizations').glob('3039258_*.json'));need(len(finals)==1,'one finalization')
 fin=read(finals[0].relative_to(R).as_posix())
 need(fin['status']=='verified' and fin['kind']=='engineering_segment' and fin['result_sha256']==readmap[REL+'/training_progress.json'] and fin['checkpoint_unchanged'] is True,'source/base finalization')
 need(fin['source_files']==gate['source_files']==pairprogress['source_files'],'same producer sources')
 cachepaths=list((R/REL/'cache_events').glob('*.jsonl'));need(len(cachepaths)==1,'one cache journal')
 counts=Counter();cache_identity=reports['A']['identity']['cache_identity']
 need(cache_identity==reports['B']['identity']['cache_identity'],'same cache namespace')
 cv=ast.parse(raw('src/cti_vla/training/formal_records.py').decode())
 cversion=next(ast.literal_eval(n.value) for n in cv.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='FORMAL_CACHE_VERSION')
 namespace=sig({'cache_version':cversion,**cache_identity})
 for row in jrows(cachepaths[0].relative_to(R).as_posix()):
  need(row['job_id']=='3039258' and row['cache_identity_sha256']==namespace,'cache source/job');counts[row['event']]+=1
 need(dict(counts)==root['cache_event_counts'],'root exact cache count')
 pull=read(args.pull,args.pull_sha256)
 need(pull['status']=='verified_nonweight_snapshot' and pull.get('final_evidence') is True and pull.get('weights_copied') is False and pull.get('sealed_initial_states_copied') is False,'verified pull')
 before=read(str(Path(args.pull).parent/'inventory_before.json'),pull['inventory_sha256']);after=read(str(Path(args.pull).parent/'inventory_after.json'))
 need(before==after,'stable double inventory')
 for when in ['accounting_before','accounting_after']:
  for jid,expected in [('3028460',('FAILED','1:0',84)),('3039258',('COMPLETED','0:0',6512))]:
   bill=pull[when]['jobs'][jid];need(tuple(bill[k] for k in ['status','exit_code','elapsed_seconds'])==expected,'actual Slurm bill retained')
   need(dict(x.split('=',1) for x in bill['allocation'].split(',') if '=' in x).get('gres/gpu')=='1','one allocated GPU')
 inventory_rows={x['relative']:x for x in before['files']}
 need(len(inventory_rows)==len(before['files']),'no duplicate inventory')
 files=pull['files'];need(len({f['relative'] for f in files})==len(files),'unique pull files')
 for row in files:
  rel=row['relative'];data=raw(rel,row['sha256']);need(len(data)==row['bytes'],'pull byte count')
  original=inventory_rows[rel]
  need(all(row[k]==original[k] for k in ['path','sha256','bytes','job_ids']),'pull/inventory identities')
  if rel in ['results/formal_main_v2/job_receipts/3028460.json','results/slurm/cti-formal_3028460.out','results/slurm/cti-formal_3028460.err']:
   need('3028460' in row['job_ids'] and row['sha256']==failure['evidence_bundle'][rel]['sha256'],'old failed-only original ownership')
  else:need('3039258' in row['job_ids'],'current/shared run membership')
  need(row['path']==str(P/rel),'exact P origin')
  need(shafile(P/rel)['sha256']==row['sha256'],'live terminal P raw bytes unchanged')
 for rel,sha in root['files'].items():raw(rel,sha)
 for rel,sha in root.get('evidence_sha256',{}).items():
  if rel=='results/experiment_supervisor/state.json':continue
  raw(rel,sha)
 # Root's saved metadata proof is additionally cross-linked to raw actual receipt.
 receipt=read('results/formal_main_v2/job_receipts/3039258.json')
 need(receipt['exit_code']==0 and receipt['runner_exit_code']==0 and receipt['errors']==[] and receipt['loader_restored'] is True and receipt['source_inputs_unchanged'] is True,'successful restored metadata scope')
 need(receipt['invocation_sha256']==job['invocation_sha256'] and receipt['runtime_compatibility']==job['runtime_compatibility'],'same wrapper execution')
 events=jrows(REL+'/compatibility/3039258/compatibility_events.jsonl')
 need(len(events)==6,'successful metadata exact6 events')
 for rel,sha in list(readmap.items()):need(hashlib.sha256((R/rel).read_bytes()).hexdigest()==sha,'input drift')
 raw(str(Path(__file__).relative_to(R)))
 out={'schema':'formal_main_v2','kind':'CUDA_original_target_recovery_independent_review','version':'cuda-recovery-independent-0943-v1','status':'passed_original_target_recovery_only','created_utc':datetime.now(timezone.utc).isoformat(),'job_id':'3039258','failed_job_id':'3028460','suite':'libero_object','visual_tokens':256,'seed':23,'original_target':500,'root_review':{'path':rootrel,'sha256':args.root_review_sha256},'pull':{'path':args.pull,'sha256':args.pull_sha256},'arms':summaries,'all173_source_R_and_S_match':True,'same_full40000_sampling_order':True,'same_initial_scorer_sha256':reports['A']['initial_scorer_sha256'],'actual_server_resume_checks':resumechecks,'cost':{'retained_FAILED_GPU_seconds':84,'successful_recovery_GPU_seconds':6512,'all_pair_allocated_GPU_seconds':6596,'nested_cache_training_phases_added_to_bill':False},'cache_event_counts':dict(counts),'metadata_events':len(events),'limits':['Prior failure had no arm initialization/update/checkpoint, so resumed=false is correct; this is not observed restoration of a preexisting optimizer/RNG state.','Resume file bytes independently hashed; tensor/optimizer/RNG contents were not deserialized and frozen trainer must validate them upon any separately authorized future resume.','This is original500 target recovery, not full5000 completion and not autonomous5000 admission.'],'continuous5000_admission_authorized':False,'new_submission_authorized':False,'scientific_matrix_completed_arms_added':0,'final_release_authorized':False,'weights_copied_or_deserialized':False,'state_or_Git_writes':False,'historical_failure_preserved':True,'read_evidence_sha256':dict(sorted(readmap.items())),'server_read_evidence_sha256':dict(sorted(servermap.items()))}
 dest=D/'independent_review.json'
 with dest.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')
 print(json.dumps({'status':out['status'],'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'arms':summaries,'cost':out['cost'],'read_refs':len(readmap),'server_refs':len(servermap)},ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root-review-sha256',required=True);p.add_argument('--pull',required=True);p.add_argument('--pull-sha256',required=True)
 main(p.parse_args())
