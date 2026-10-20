"""Independent CPU terminal audit for exactly two already-finished development jobs.
No scheduler access, state changes, Git, or model inference. Checkpoint bytes hashed on server only.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter,defaultdict
import argparse,hashlib,importlib.util,json,math,os,sys,traceback
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/k64_terminal_independent_20261020T2054'
B='results/formal_main_v2/preflight/heartbeat_20261021T0454'
TRANSPORT='3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149'
REVIEWER='scripts/ops/formal_action_deployment_v1/reviewer.py'
PINS={REVIEWER:'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd',
 'scripts/ops/formal_action_deployment_v1/consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034',
 '.local/review_k64_pair_terminals_20261020T2054.py':'66b9e495f6f69a843b089f3f2e65561843adf6bd21b4094c1462ff10192540be',
 '.local/spatial588_recovery_independent_20261020T2054/k64_terminal_helper_static_review.json':'dc9293a70093da347b2c73395ac1d902abba20ebe8177bd9bc2c39a010c2cc17',
 'scripts/ops/formal_spatial64s23_source_bridge_v1/control.py':'edab3f3917b57daf1867134bc8179a73673bfc4a1e61bfda5118d76fd64458f3',
 'scripts/ops/formal_object64s23_source_bridge_v1/control.py':'cf1058afd83073e0ef30c977e88c34f124f56adcfe9487b837ecaedaf6578767',
 'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json':'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'}
TARGETS={'3053875':{'suite':'libero_spatial','root_sha':'ee00999e50f845b88f22c45f8d5164d232fd1b53ae1f9cf588bdb0aa8ea4da43','completion_sha':'3d564ad4e35f75a445127dd2af14c753c8edae3193c0595e0b23aa81628eed95','invocation_sha':'bf18ea0e4c3f1782005f26195058dae9cc5e63c7c7b7e7f3434514293831fbb4','gpu_seconds':2283,'max_steps':220,'training_job_ids':['3024716','3025205','3028522','3043399','3044479'],'failed_training_job':'3028522','all_pair_GPU_seconds':42480,'retained_failed_GPU_seconds':73,'best_updates':{'A':2500,'B':3500}},
 '3053894':{'suite':'libero_object','root_sha':'afedb854ad6e2559b876ba86bf805309ff948e9f086da10232699fa5bfe91d0f','completion_sha':'ec6f1628cd53c727293031b7fb89c1d1ec94da507fba2313ae2d742ed31832f2','invocation_sha':'b9a415b055f6d3d46035e9c9d4d03302762699577bc53808a6f122c889cd824d','gpu_seconds':2175,'max_steps':280,'training_job_ids':['3028468','3044017','3044844'],'failed_training_job':'3028468','all_pair_GPU_seconds':52868,'retained_failed_GPU_seconds':69,'best_updates':{'A':2500,'B':4500}}}
METHODS=['A64_seed23','B64_seed23']
CHECKS=[];WATCHED={}
def require(ok,message):
 if not ok:raise ValueError(message)
def check(ok,message):
 require(ok,message);CHECKS.append(message)
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def sha(b):return hashlib.sha256(b).hexdigest()
def watch(rel,pin=None):
 p=Path(rel);p=p if p.is_absolute() else R/p
 require(p==p.resolve() and not p.is_symlink(),'noncanonical evidence '+str(p))
 require(p.is_relative_to(R) or p.is_relative_to(P) or p.is_relative_to('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints'),'outside project evidence')
 require('final_sealed' not in str(p) and p.name!='state.json','no mutable or sealed values')
 actual=digest(p)
 require(pin is None or actual==pin,'evidence SHA mismatch '+str(p))
 require(str(p) not in WATCHED or WATCHED[str(p)]==actual,'evidence changed during audit')
 WATCHED[str(p)]=actual;return p

def reference(p):
 p=Path(p);return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p),'sha256':digest(p)}
def read(ref):return json.loads(watch(ref['path'],ref['sha256']).read_text())
def load(rel):
 p=watch(rel,PINS[rel]);name='_ind_k64_'+sha(rel.encode())[:16]
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m

def save(name,data):
 p=D/('v2_'+name)
 require(p.parent==D,'private output only')
 with p.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return reference(p)
def clean(v):return {k:x for k,x in v.items() if k!='reviewed_utc'}
def close(a,b):return math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12)
def valid_indices(v):
 require(type(v) is list and len(v)==64 and all(type(x) is int for x in v),'64 integer indices')
 require(v==sorted(set(v)) and 0<=min(v) and max(v)<512 and sum(x<256 for x in v)==32,'equal cameras sorted original positions')
 return set(v)
def frozen_sources():
 inv=read({'path':'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','sha256':PINS['results/formal_main_v2/source/formal_main_v2_run_564be0995e.json']})
 check(len(inv['files'])==173,'173 frozen source entries')
 for rel,pin in inv['files'].items():
  watch(R/rel,pin);watch(Path(inv['source_root_server'])/rel,pin)
 return {'inventory':reference(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'),'files':len(inv['files']),'R_and_original_S_exact':True}

def offline(rr,manifest,jid,t):
 diagnostics={};vals={};reports={}
 for item in manifest['methods']:
  mid=item['identity']['method_id'];arm=mid[0];binding=rr['source_provenance']['method_bindings'][mid]
  check(binding['identity']==item['identity'] and binding['registered_training_job_ids']==t['training_job_ids'],jid+' '+mid+' own source bridge complete training history')
  report=read(binding['training_report']);receipt=read(binding['deployment_receipt']);reports[mid]=report
  check(report['training_updates_completed']==5000 and report['committed_samples']==40000 and report['vla_parameters_unchanged'] is True,jid+' '+mid+' full training and frozen VLA')
  check(report['best_update']==t['best_updates'][arm] and report['best_checkpoint_sha256']==item['identity']['checkpoint_sha256'],jid+' '+mid+' selected checkpoint exact')
  checkpoint=watch(item['checkpoint'],item['identity']['checkpoint_sha256'])
  check(str(checkpoint)==report['best_checkpoint'],jid+' '+mid+' checkpoint path hashed server-only')
  evals=report['evaluations'];check([x['update'] for x in evals]==list(range(0,5001,500)),jid+' '+mid+' all 11 selection nodes')
  best=min(evals,key=lambda x:(x['validation_metric'],x['update']))
  check(best['update']==report['best_update'] and best['validation_metric']==report['best_validation_metric'],jid+' '+mid+' unchanged earliest-min selection')
  vp=R/Path(best['artifact_path']).relative_to(P);v=read({'path':vp.relative_to(R).as_posix(),'sha256':best['artifact_sha256']});watch(best['artifact_path'],best['artifact_sha256']);vals[mid]=v
  obs=v['observations'];check(v['arm']==arm and v['update']==best['update'] and v['tasks']==10 and len(obs)==v['windows'],jid+' '+mid+' selected validation artifact exact')
  grouped=defaultdict(list)
  for x in obs:
   require(math.isfinite(x['teacher_l1']) and math.isfinite(x['demonstration_l1']) and x['teacher_l1']>=0 and x['demonstration_l1']>=0,'finite validation L1')
   valid_indices(x['retained_indices']);a=np.asarray(x['normalized_actions'],dtype=np.float64);require(a.shape==(8,7) and np.isfinite(a).all(),'validation action shape/finite');grouped[str(x['task_id'])].append(x)
  require(set(grouped)==set(map(str,range(10))),'all validation tasks')
  for tid,rows in grouped.items():
   for field in ['teacher_l1','demonstration_l1']:require(close(np.mean([x[field] for x in rows]),v['per_task'][tid][field]),'per-task validation mean')
   require(len(rows)==v['per_task'][tid]['windows'],'per-task validation count')
  macro=float(np.mean([np.mean([x['teacher_l1'] for x in grouped[str(tid)]]) for tid in range(10)]));demo=float(np.mean([np.mean([x['demonstration_l1'] for x in grouped[str(tid)]]) for tid in range(10)]))
  require(close(macro,v['validation_metric']) and close(macro,report['best_validation_metric']) and close(demo,v['demonstration_l1']),'selected L1 aggregate reproduced')
  diagnostics[mid]={'training_report':binding['training_report'],'deployment_receipt':binding['deployment_receipt'],'checkpoint':reference(checkpoint),'best_update':report['best_update'],'task_macro_hard_teacher_l1':macro,'task_macro_demonstration_l1':demo,'window_weighted_demonstration_l1_diagnostic':float(np.mean([x['demonstration_l1'] for x in obs])),'window_weighted_teacher_l1':float(np.mean([x['teacher_l1'] for x in obs])),'per_task':v['per_task'],'selected_validation':reference(vp),'validation_windows':len(obs),'all_selection_nodes':evals,'new_inference':False}
 check(reports[METHODS[0]]['initial_scorer_sha256']==reports[METHODS[1]]['initial_scorer_sha256'] and reports[METHODS[0]]['sample_order_sha256']==reports[METHODS[1]]['sample_order_sha256'],jid+' A/B matched initialization and sample order retained')
 a,b=[vals[m]['observations'] for m in METHODS]
 check([(x['window_id'],x['episode_id'],x['task_id']) for x in a]==[(x['window_id'],x['episode_id'],x['task_id']) for x in b],jid+' same selected-checkpoint validation panel for A/B')
 pairs=[]
 for x,y in zip(a,b):
  aa,bb=valid_indices(x['retained_indices']),valid_indices(y['retained_indices']);n=len(aa&bb)
  pairs.append({'window_id':x['window_id'],'episode_id':x['episode_id'],'task_id':x['task_id'],'A_teacher_l1':x['teacher_l1'],'B_teacher_l1':y['teacher_l1'],'A_demonstration_l1':x['demonstration_l1'],'B_demonstration_l1':y['demonstration_l1'],'intersection_tokens':n,'intersection_over_budget':n/64,'jaccard':n/len(aa|bb)})
 pairref=save(jid+'_offline_validation_pairs.json',{'scope':'diagnostic from existing validation artifacts only, no new inference or selection','pairs':pairs})
 diagnostics['token_overlap']={'rows':len(pairs),'mean_intersection_over_budget':float(np.mean([x['intersection_over_budget'] for x in pairs])),'mean_jaccard':float(np.mean([x['jaccard'] for x in pairs])),'per_task':{str(tid):{'windows':sum(x['task_id']==tid for x in pairs),'mean_intersection_over_budget':float(np.mean([x['intersection_over_budget'] for x in pairs if x['task_id']==tid])),'mean_jaccard':float(np.mean([x['jaccard'] for x in pairs if x['task_id']==tid]))} for tid in range(10)},'paired_records':pairref}
 return diagnostics

def raw(rr,manifest,run,jid,t):
 panelpath=run/'panel.json';panel=json.loads(watch(panelpath).read_text());canonical=watch(manifest['development_panel'],manifest['development_panel_sha256'])
 check(digest(panelpath)==digest(canonical),jid+' actual panel equals preregistered development panel')
 states=panel['states'];check(panel['split']=='development' and len(states)==100 and Counter(s['task_id'] for s in states)==Counter({i:10 for i in range(10)}),jid+' fixed 100 development states and all ten tasks')
 check(len({s['trial_id'] for s in states})==100 and len({(s['task_id'],s['source_state_index'],s['initial_state_sha256']) for s in states})==100,jid+' unique initial state identities')
 path=watch(run/'trials.jsonl');blob=path.read_bytes();lines=blob.splitlines(keepends=True);events=[json.loads(x) for x in lines]
 check(len(events)==401 and events[0]['event']=='invocation' and events[0]['slurm_job_id']==jid and Counter(e['event'] for e in events)==Counter(invocation=1,start=200,result=200),jid+' one invocation and exact 200 start/result pairs')
 check(all(e['run_signature']==rr['run_signature'] for e in events),jid+' raw run signature exact')
 results=[];records=[];offsets=[];at=0
 for line in lines:offsets.append(at);at+=len(line)
 chunkcount=actioncount=clipchanged=outold=0;maxabs=0.0;by_state=defaultdict(dict)
 ids={x['identity']['method_id']:x['identity'] for x in manifest['methods']}
 expected=[(s,m) for s in states for m in METHODS]
 for i,(s,mid) in enumerate(expected):
  sn=1+2*i;rn=sn+1;start,result=events[sn],events[rn]
  identity={'action_chunk':8,'configured_wait_steps':10,'environment_seed':0,'initial_state_sha256':s['initial_state_sha256'],'method':mid,'runtime_seed':17,'source_state_index':s['source_state_index'],'split':'development','state_trial_id':s['trial_id'],'suite':t['suite'],'task_id':s['task_id'],'task_name':s['task_name'],'trial_id':s['trial_id']+':'+mid,'run_signature':rr['run_signature']}
  require(start['event']=='start' and result['event']=='result' and all(start.get(k)==v and result.get(k)==v for k,v in identity.items()),'exact start/result identity and fixed method order')
  require(result['status']=='completed' and type(result['success']) is bool and result['wait_steps']==10,'completed scientific row and wait count')
  n=result['control_steps'];chunks=result['chunks'];require(type(n) is int and 0<n<=t['max_steps'],'bounded control steps')
  require(result['policy_calls']==len(chunks)==math.ceil(n/8),'exact queue query cadence')
  require((result['success'] and result['termination']=='environment_success') or (not result['success'] and result['termination']=='task_horizon' and n==t['max_steps']),'terminal status exactly consistent')
  envs=[];chunkrows=[];rowclip=0;rowout=0
  for ci,c in enumerate(chunks):
   env=np.asarray(c['environment_actions'],dtype=np.float64);norm=np.asarray(c['normalized_actions'],dtype=np.float64);meta=c['metadata'];ident=ids[mid]
   require(env.shape==norm.shape==(8,7) and np.isfinite(env).all() and np.isfinite(norm).all(),'chunk finite [8,7]')
   require(c['control_step']==8*ci and len(c['observation_sha256'])==64,'chunk original cadence/hash')
   require(math.isfinite(c['engineering_seconds']) and 0<=c['engineering_seconds']<=60,'retained engineering elapsed/watchdog')
   required={'action_version':'libero-oft-boundsq99-gripper-sign-invert-chunk8-v1','diagnostic_indices_recorded':True,'future_head_calls':0,'inputs_version':'libero-oft-eval-rotate180-jpeg-lanczos3-crop09-boundsq99-v1','language_cache':'disabled','method':mid[0],'packing_calls':1,'packing_version':'oft-original-positions-v1','pair_id':ident['pair_id'],'per_camera_budgets':[32,32],'policy_calls':1,'schema':'formal_main_v2','scorer_calls':1,'selector_checkpoint_sha256':ident['checkpoint_sha256'],'suite':t['suite'],'training_seed':23,'vision_calls':1,'visual_tokens':64}
   require(all(meta.get(k)==v for k,v in required.items()),'every chunk deployment/checkpoint/packing metadata exact')
   valid_indices(meta['retained_indices']);require(set(np.unique(env[:,-1])).issubset({-1.0,1.0}),'binary inverted gripper commands')
   clipped=np.clip(env,-1.0,1.0);nc=int(np.count_nonzero(env!=clipped));no=int(np.count_nonzero(np.abs(env)>1.00001));rowclip+=nc;rowout+=no;maxabs=max(maxabs,float(np.abs(env).max()))
   chunkrows.append({'chunk_index':ci,'observation_sha256':c['observation_sha256'],'environment_actions_f64le_sha256':sha(env.astype('<f8').tobytes()),'controller_clipped_f64le_sha256':sha(clipped.astype('<f8').tobytes()),'normalized_actions_f64le_sha256':sha(norm.astype('<f8').tobytes()),'retained_indices':meta['retained_indices'],'controller_clip_changed_scalar_values':nc,'original_obsolete_gate_exceedances':no,'engineering_seconds':c['engineering_seconds']})
   envs.append(env)
  actions=np.asarray(result['executed_actions'],dtype=np.float64);queued=np.concatenate(envs,axis=0)[:n]
  require(actions.shape==(n,7) and np.isfinite(actions).all() and actions.tobytes()==queued.tobytes(),'actual recorded pre-controller commands equal exact chunk queue prefix')
  require(np.clip(actions,-1,1).tobytes()==np.concatenate([np.clip(x,-1,1) for x in envs],axis=0)[:n].tobytes(),'existing controller clip of queue and recorded commands identical')
  results.append(result);by_state[s['trial_id']][mid]=result;chunkcount+=len(chunks);actioncount+=n;clipchanged+=rowclip;outold+=rowout
  records.append({'trial_id':result['trial_id'],'state_trial_id':s['trial_id'],'task_id':s['task_id'],'method':mid,'success':result['success'],'termination':result['termination'],'control_steps':n,'start_line':sn+1,'result_line':rn+1,'start_offset':offsets[sn],'result_offset':offsets[rn],'start_raw_sha256':sha(lines[sn]),'result_raw_sha256':sha(lines[rn]),'chunks':chunkrows,'executed_commands_f64le_sha256':sha(actions.astype('<f8').tobytes()),'controller_clipped_executed_commands_f64le_sha256':sha(np.clip(actions,-1,1).astype('<f8').tobytes()),'queue_prefix_exact':True})
 check(len({x['trial_id'] for x in results})==200,jid+' all 200 result identities unique, all chunks/action prefixes verified')
 successes={m:sum(x['success'] for x in results if x['method']==m) for m in METHODS};per_task={};paired=[];token=[]
 for state in states:
  sid=state['trial_id'];a,b=[by_state[sid][m] for m in METHODS];ca,cb=a['chunks'][0],b['chunks'][0]
  require(ca['observation_sha256']==cb['observation_sha256'],'paired current t0 hash mismatch')
  aa,bb=valid_indices(ca['metadata']['retained_indices']),valid_indices(cb['metadata']['retained_indices']);inter=len(aa&bb)
  paired.append({'state_trial_id':sid,'task_id':state['task_id'],'A_success':a['success'],'B_success':b['success'],'B_minus_A':int(b['success'])-int(a['success'])})
  token.append({'state_trial_id':sid,'task_id':state['task_id'],'recorded_t0_observation_sha256':ca['observation_sha256'],'A_indices':ca['metadata']['retained_indices'],'B_indices':cb['metadata']['retained_indices'],'intersection_tokens':inter,'intersection_over_budget':inter/64,'jaccard':inter/len(aa|bb)})
 for tid in range(10):
  ps=[x for x in paired if x['task_id']==tid];per_task[str(tid)]={'initial_states':10,'A_successes':sum(x['A_success'] for x in ps),'B_successes':sum(x['B_success'] for x in ps),'B_minus_A_pp':10*sum(x['B_minus_A'] for x in ps)}
  for mid,field in [(METHODS[0],'A_successes'),(METHODS[1],'B_successes')]:
   expected_task=rr['reconstructed_summary']['methods'][mid]['per_task'][str(tid)]
   require(expected_task=={'trials':10,'successes':per_task[str(tid)][field],'success_rate':per_task[str(tid)][field]/10},'per-task summary must rebuild')
 check(successes=={m:rr['reconstructed_summary']['methods'][m]['successes'] for m in METHODS} and paired==rr['reconstructed_summary']['paired_AB']['k64_seed23']['results'],jid+' all paired and per-task outcomes reconstruct exactly')
 check(chunkcount==rr['reconstructed_summary']['cost']['known_policy_calls'],jid+' all policy calls accounted')
 rec=save(jid+'_raw_trial_audit.json',{'raw_ledger':reference(path),'scope':'all 200 original results; no actions/status changed; controller clip recomputed CPU only, not inferred simulator trajectory','rows':records})
 pairref=save(jid+'_paired_development.json',{'raw_ledger':reference(path),'unique_initial_states':100,'outcomes':paired,'t0_tokens':token,'recorded_t0_scope':'Original observer hashes after policy returns. Equality is verified for these recorded hashes, not proof of pre-policy input immutability.'})
 discordance={'A_only':sum(x['A_success'] and not x['B_success'] for x in paired),'B_only':sum(x['B_success'] and not x['A_success'] for x in paired),'both_success':sum(x['A_success'] and x['B_success'] for x in paired),'both_failure':sum(not x['A_success'] and not x['B_success'] for x in paired)}
 return {'trials':200,'unique_initial_states':100,'successes':successes,'B_minus_A_pp':successes[METHODS[1]]-successes[METHODS[0]],'discordance':discordance,'per_task':per_task,'raw_ledger':reference(path),'raw_start_result_pairs_exact':True,'full_action_chunks':chunkcount,'executed_control_actions':actioncount,'raw_trial_audit':rec,'paired_development':pairref,'t0_token_diagnostics':{'unique_initial_states':100,'all_recorded_t0_hashes_equal':True,'mean_intersection_over_budget':float(np.mean([x['intersection_over_budget'] for x in token])),'mean_jaccard':float(np.mean([x['jaccard'] for x in token])),'per_task':{str(tid):{'mean_intersection_over_budget':float(np.mean([x['intersection_over_budget'] for x in token if x['task_id']==tid])),'mean_jaccard':float(np.mean([x['jaccard'] for x in token if x['task_id']==tid]))} for tid in range(10)},'scope':'Recorded t0 after original policy call only; later diverged trajectory observations are not compared as matched inputs.'},'action_clip_diagnostics':{'all_chunk_and_executed_arrays_finite':True,'all_queue_prefixes_float64_byte_exact':True,'all_controller_clipped_queue_prefixes_byte_exact':True,'changed_predicted_scalar_values':clipchanged,'old_gate_exceedances':outold,'max_abs_predicted_environment_command':maxabs,'amplitude_not_an_adoption_gate':'Accepted action-v1 retains finite physical commands and existing simulator controller clipping. This audit neither clamps stored actions nor applies the obsolete [-1,1] rejection.'}}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--job-id',choices=list(TARGETS),required=True);arg=ap.parse_args();jid=arg.job_id;t=TARGETS[jid]
 require(os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R) and os.environ.get('CTI_SERVER_CONTROL_MANIFEST_SHA256')==TRANSPORT,'exact reviewed server transport required')
 for rel,pin in PINS.items():watch(rel,pin)
 original=load(REVIEWER);control_rel='scripts/ops/formal_'+t['suite'].replace('libero_','')+'64s23_source_bridge_v1/control.py';control=load(control_rel)
 completion_ref={'path':B+'/terminal_'+jid+'/completion.json','sha256':t['completion_sha']};done=read(completion_ref);rootref={'path':'results/formal_main_v2/downstream_reviews/'+jid+'.json','sha256':t['root_sha']};rr=read(rootref)
 check(done['root_review']==rootref and done['full_consumer_rebuilt'] is True and done['accepted_new_trials']==0,jid+' root terminal transaction complete but independent acceptance not presumed')
 check(rr['status']=='passed' and rr['scientific_complete'] is True and rr['completed_trials']==200 and rr['stage']=='development' and rr['suite']==t['suite'],jid+' actual root scientific scope')
 snap=read(done['snapshot']);job=next(x for x in snap['registered_jobs'] if x['job_id']==jid);observed=snap['observation']['rows'][jid]
 check(job==next(x for x in rr['registered_jobs_at_review'] if x['job_id']==jid) and job['gpus']==1 and job['method_ids']==METHODS and job['prior_job_ids']==[] and job['resume'] is False,jid+' same one original terminal allocation and no prior attempts')
 check(observed['status']==job['status']=='COMPLETED' and observed['exit_code']==job['exit_code']=='0:0' and observed['elapsed_seconds']==job['elapsed_seconds']==t['gpu_seconds'],jid+' exact Slurm terminal and GPU seconds')
 check(rr['cost']['all_attempt_gpu_seconds']==rr['cost']['current_gpu_seconds']==t['gpu_seconds'] and len(rr['cost']['allocations'])==1 and rr['cost']['allocations'][0]['job_id']==jid,jid+' GPU allocation counted once')
 inv=read(rr['invocation_ref']);check(rr['invocation_ref']['sha256']==t['invocation_sha'] and inv['method_ids']==METHODS and inv['resume'] is False and inv['prior_job_ids']==[],jid+' original pinned invocation')
 check(rr['explicit_source_control']==rr['source_provenance']['explicit_source_control']==control.descriptor(),jid+' exact own-pair source bridge, no foreign substitution')
 desc=control.descriptor();check(desc['failed_job_id']==t['failed_training_job'] and desc['all_pair_GPU_seconds']==t['all_pair_GPU_seconds'] and desc['retained_failed_GPU_seconds']==t['retained_failed_GPU_seconds'],jid+' failed training history and cost preserved without recount')
 frozen=frozen_sources();run=R/Path(rr['run_root']).relative_to(P)
 for rel,pin in rr['files'].items():
  watch(rel,pin)
  if Path(rel).is_relative_to(run.relative_to(R)):watch(P/rel,pin)
 check(True,jid+' all pulled output file SHAs and original P raw bytes match')
 cfg=json.loads((run/'config.json').read_text());manifest=cfg['manifest']
 check(manifest['suite']==t['suite'] and manifest['split']=='development' and [x['identity']['method_id'] for x in manifest['methods']]==METHODS and manifest['environment']=={'action_chunk':8,'environment_seed':0,'max_steps':t['max_steps'],'runtime_seed':17,'wait_steps':10},jid+' exact science/environment configuration')
 rawproof=raw(rr,manifest,run,jid,t);off=offline(rr,manifest,jid,t)
 # The approved own-pair consumer calls and checks the whole original reviewer, not a projected summary.
 ev=original.Evidence(R);consumer=control.consumer_module(ev)
 rebuilt=consumer.review_downstream_output(ev,rootref,expected_stage='development',suite=t['suite'],run_root=rr['run_root'],require_complete=True)
 check(clean(rebuilt)==clean(rr),jid+' full original source-specific consumer reconstructs every field except review UTC')
 ev.unchanged()
 reconstruction=save(jid+'_full_consumer_reconstruction.json',rebuilt)
 for path,pin in WATCHED.items():require(digest(path)==pin,'read evidence changed before completion '+path)
 report={'schema':'formal_main_v2','kind':'independent_terminal_development_review','status':'passed','review_role':'independent','reviewed_utc':datetime.now(timezone.utc).isoformat(),'job_id':jid,'suite':t['suite'],'seed':23,'visual_tokens':64,'root_review':rootref,'root_completion':completion_ref,'terminal_snapshot':done['snapshot'],'full_original_consumer_reconstruction_passed':True,'full_original_consumer_reconstruction':reconstruction,'source_bridge':control.descriptor(),'frozen_sources':frozen,'offline_validation_diagnostics':off,'allocated_gpu_seconds':t['gpu_seconds'],'training_cost_recounted':False,'checks':CHECKS,'evidence_sha256':WATCHED,'new_GPU_jobs':0,'state_written':False,'Git_operations':False,'final_release':False,'sealed_final_values_read':False,'weights_copied':False,'checkpoint_content_deserialized':False,'checkpoint_bytes_hashed_on_server_only':True,'entrypoint':reference(Path(__file__).resolve()),**rawproof}
 out=save(jid+'_independent_review.json',report);print(json.dumps({'review':out,'successes':rawproof['successes'],'discordance':rawproof['discordance'],'chunks':rawproof['full_action_chunks'],'actions':rawproof['executed_control_actions'],'GPU_seconds':t['gpu_seconds'],'checks':len(CHECKS)},sort_keys=True),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  out=D/('failure_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
  with out.open('x') as f:json.dump({'status':'blocked_independent_audit','exception':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc(),'checks_completed':CHECKS,'new_GPU_jobs':0,'state_written':False,'automatic_retry':False},f,indent=2);f.write('\n')
  raise
