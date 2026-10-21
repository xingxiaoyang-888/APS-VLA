"""Offline independent reconstruction of five real held/ACK/register/release transactions."""
import sys,json,hashlib,copy,datetime,importlib.util,traceback
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/goal_remaining5_ACK_independent_20261021T0449'
KEYS=['libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41']
IDS=['3057505','3057510','3057515','3057526','3057533']
PKG='scripts/ops/formal_goal_remaining5_gate_v1';GATE='scripts/ops/formal_goal_remaining5_dispatch_v1'
GPIN='45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b';SPIN='f44e8cf97e0a9456782ea57ffeb4c4f39e47058b51c320b3947c73bd1a6cf27b'
MPIN='200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f'
FINAL='58e4ff5cd74c07c667a942119d2ed2de80059efb294ad8f21d192cdbe14bdac7'
BASE='.local/goal_remaining5_plans_20261021T0449/v2/build_state_snapshot.json';BASEPIN='d795f666c630ba196f9eba8aae8d5cbed879e10fd596fc95d37c745f281948ba'
LATER='results/formal_main_v2/preflight/heartbeat_20261021T1249/post_dispatch_observation.json'
LATERPIN='2bfccdc44ce0fd488be0d50bc76092aa071c07517d8ae9dccee2160e5bb6fcd2'
CHECKS=[];NEG=[]
def need(ok,text):
 if not ok:raise ValueError(text)
 CHECKS.append(text)
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(p,pin=None,size=None):
 p=Path(p);need(p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]),'canonical nonlink '+str(p))
 a=p.stat();b=p.read_bytes();z=p.stat();need((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'stable bytes '+str(p))
 if pin:need(sha(b)==pin,'pinned bytes '+str(p))
 if size is not None:need(len(b)==size,'pinned size '+str(p))
 return b
def read(p,pin=None):return json.loads(raw(p,pin))
def ref(p):b=raw(p);return dict(path=str(Path(p).relative_to(R)),bytes=len(b),sha256=sha(b))
def canonical(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def statehash(v):return sha(canonical(v)+b'\n')
def put(name,v):
 b=(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with (D/name).open('xb') as f:f.write(b)
 return dict(path=str((D/name).relative_to(R)),bytes=len(b),sha256=sha(b))
def load(p,pin,name):
 raw(p,pin);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def reject(label,fn):
 try:fn()
 except (ValueError,AssertionError,KeyError,TypeError,IndexError) as e:NEG.append(dict(label=label,error_type=type(e).__name__,message=str(e)[:180]));return
 raise ValueError('negative accepted '+label)
class SavedScheduler:
 def __init__(self,queries):self.queries=copy.deepcopy(queries);self.i=0
 def run(self,argv):
  need(self.i<len(self.queries),'saved query exists')
  q=self.queries[self.i];self.i+=1;need(q['argv']==argv,'offline replay exact query argv')
  return SimpleNamespace(returncode=q['returncode'],stdout=q['stdout'],stderr=q['stderr'])
def replay_observation(g,c,d,state,saved,allow_job=None):
 o=saved['observation'];fake=SavedScheduler(o['queries'])
 rebuilt=g.actual_observation(c,fake,state['registered_jobs'])
 need(fake.i==len(fake.queries) and rebuilt==o,'saved complete sacct/squeue parse and identity reconstruction')
 need(len(saved['scontrol_queries'])==len(saved['details']),'complete saved active scontrol set')
 for q in saved['scontrol_queries']:
  need(q['returncode']==0 and q['stderr']=='','saved scontrol succeeded')
  need(q['argv'][:4]==['scontrol','show','job','-o'] and len(q['argv'])==5,'exact saved scontrol query')
  jid=q['argv'][4];need(g.fields(q['stdout'])==saved['details'][jid],'raw scontrol parsed fields')
 derived=d.normalized_projection(c,state,o,saved['details'],allow_job=allow_job)
 need(derived==saved['derived'],'complete saved state projection including all-mode capacity and cost')
 lease=saved['lease'];need(lease['lease_available_measured'] is True and lease['owner_sha256']==g.OWNER_SHA and lease['lease_path']==g.LEASE,'saved controller lifecycle lease measurement')
 need(raw(R/g.OWNER,g.OWNER_SHA) is not None,'actual owner identity still pinned')
 st=(R/g.LEASE).stat();need(st.st_dev==lease['lease_device'] and st.st_ino==lease['lease_inode'],'same lifecycle lease file identity')
 need(len(derived['occupied'])+derived['reserved_GPU_slots']<=8,'all-mode slot limit')
 return derived
def main():
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 inv=read(D/'evidence_inventory.json')
 for r in inv['files']:raw(R/r['path'],r['sha256'],r['bytes'])
 state=read(R/BASE,BASEPIN);state0=copy.deepcopy(state);final=read(D/'post_submit_state.json',FINAL)
 g=load(R/GATE/'gateway.py',GPIN,'ack_review_gateway');c=g.controller()
 mp=read(R/PKG/'package_manifest.json',MPIN);need(len(mp['files'])==20,'runtime complete20')
 for rel,pin in {**mp['files'],GATE+'/gateway.py':GPIN,GATE+'/scope.json':SPIN}.items():
  need(raw(R/rel,pin)==raw(P/rel,pin),'actual R/P closure '+rel)
 e=load(P/PKG/'entry.py',mp['files'][PKG+'/entry.py'],'ack_review_runtime')
 need(len(state['registered_jobs'])==303 and len(final['registered_jobs'])==308,'exact five new registered rows')
 need(final['registered_jobs'][:303]==state['registered_jobs'],'all303 historical registration rows original bytes/objects')
 results=[];previous_hash=BASEPIN;previous_end=0
 for ordinal,(key,jid) in enumerate(zip(KEYS,IDS),1):
  X='results/formal_main_v2/execution/goal_remaining5_v1/'+key;A=R/X/'dispatch_attempt01'
  names=['committed.json','failed_transaction.json','held_capacity_before_registration.json','held_identity.json','pending.json','post_release_observation.json','preflight.json','registered_held.json','release_attempt.json','release_result.json','released_identity.json','sbatch_result.json']
  need({p.name for p in A.iterdir()}==set(names),'one exact transaction evidence set '+key)
  f={n:read(A/n) for n in names}
  authb=raw(R/X/'root_authorization.json');auth=json.loads(authb);ah=sha(authb)
  admb=raw(R/X/'dispatch_admission.json');adm=json.loads(admb)
  need(raw(P/X/'root_authorization.json',ah)==authb and raw(P/X/'dispatch_admission.json',sha(admb))==admb,'actual auth/admission R/P')
  d=g.make_dispatcher(key,SPIN);ctx=e.context(key)
  e.validate_authorization(ctx,auth,mp['files'][PKG+'/pairs/'+key+'/config.json'],MPIN,mp['files'][PKG+'/entry.py'])
  for role in ['root','independent']:
   rr=auth[role+'_review'];rp=Path(rr['path']);rel=rp.relative_to(P)
   need(raw(rp,rr['sha256'])==raw(R/rel,rr['sha256']),'readiness R/P exact')
   e.check_review(ctx,read(rp),role,MPIN,ctx.config_sha)
  token='cti-goal-remaining5-v1:'+key+':'+ah
  bundle=dict(admission=adm,authorization=auth,authorization_ref=ref(R/X/'root_authorization.json'),authorization_sha256=ah,
    admission_ref=ref(R/X/'dispatch_admission.json'),token=token,comment=token,invocation_bytes=authb,runtime_package=mp,
    sources={**g.source_map(),**mp['files']})
  argv=d.sbatch_argv(bundle)
  pending=f['pending.json'];ack=f['sbatch_result.json'];failed=f['failed_transaction.json'];reg=f['registered_held.json']
  need(f['preflight.json']['state_sha256']==previous_hash and statehash(state)==previous_hash,'continuous state hash before next submission')
  need(f['preflight.json']['actual_sbatch_argv']==argv and f['preflight.json']['sources']==bundle['sources'] and f['preflight.json']['authorization']==bundle['authorization_ref'],'preflight identity closure')
  beforederived=replay_observation(g,c,d,state,f['preflight.json']['observation'])
  need(beforederived['occupied']==IDS[:ordinal-1],'pre-submit occupied IDs exactly previous releases')
  need(ack['actual_sbatch_argv']==argv and d.parse_ack(ack,set(str(j['job_id']) for j in state['registered_jobs']))==jid,'single original held sbatch ACK')
  need(ack['returncode']==0 and ack['stdout']==jid+'\n' and ack['stderr']=='','exact original ACK bytes')
  need(pending['actual_sbatch_argv']==argv and pending['authorization']==bundle['authorization_ref'] and pending['invocation_sha256']==ah and pending['submission_token']==pending['slurm_comment']==token,'durable pending exact source/token')
  need(pending['status']=='before_sbatch' and pending['requested_gpus']==1 and pending['automatic_retry'] is False,'before-submit pending scope')
  need(failed['status']=='HOLD_reconcile_original_ACK_only' and failed['automatic_retry'] is False and failed['error']=='missing registered allocation' and failed['error_type']=='ValueError','retained accounting-delay stop, not training failure')
  # Reconstruct only the mutations present in the reviewed native transaction.
  state['pending_submission']=copy.deepcopy(pending);state['autonomous_training_v1']['reserved_GPU_slots']=1
  state['pending_submission'].update(status='original_ACK_saved',known_job_id=jid)
  expected_job=d.job_record(jid,bundle,argv);need(reg['job']==expected_job,'registered original job matches final source constructor')
  state['registered_jobs'].append(copy.deepcopy(expected_job));preview=copy.deepcopy(state);preview['autonomous_training_v1']['reserved_GPU_slots']=0
  heldderived=replay_observation(g,c,d,preview,f['held_capacity_before_registration.json'],allow_job=jid)
  need(heldderived['occupied']==IDS[:ordinal],'held job included before registration/release')
  state['pending_submission'].update(status='registered_held_release_not_issued',known_job_id=jid);state['autonomous_training_v1']['reserved_GPU_slots']=0
  need(statehash(state)==reg['state_sha256'],'exact held-registration CAS hash')
  for name,held in [('held_identity.json',True),('released_identity.json',False)]:
   v=f[name];need(v['argv']==['scontrol','show','job','-o',jid] and v['returncode']==0 and v['stderr']=='','saved new job scontrol '+name)
   fields=g.fields(v['stdout']);need(fields==v['fields'],'raw new job fields match')
   d.validate_new_identity(expected_job,bundle,fields,held)
  res=read(R/X/'reservation.json');resbytes=canonical(res)+b'\n'
  need(res==d.reservation(bundle) and raw(P/X/'reservation.json')==raw(R/X/'reservation.json')==resbytes,'exact persistent reservation R/P')
  dispatch=read(R/X/'held_dispatch_record.json');need(raw(P/X/'held_dispatch_record.json')==raw(R/X/'held_dispatch_record.json'),'actual held dispatch R/P')
  e.validate_dispatch(ctx,dispatch,res,auth,ah,jid,sha(resbytes))
  need(dispatch['actual_sbatch_argv']==argv and dispatch['source_files']==bundle['sources'] and dispatch['state_after_sha256']==reg['state_sha256'],'held runtime full-source/registered-state chain')
  need(dispatch['original_sbatch_ACK_fact']==X+'/dispatch_attempt01/sbatch_result.json' and dispatch['request_token']==token,'held runtime original ACK reference')
  ra=f['release_attempt.json'];rr=f['release_result.json']
  need(ra['job_id']==jid and ra['argv']==rr['argv']==['scontrol','release',jid] and ra['submission_token']==token and ra['state_sha256']==reg['state_sha256'],'one original release attempt bound to held CAS')
  need(rr['returncode']==0 and rr['stdout']==rr['stderr']=='','single release acknowledgement')
  # Exact transport execution history: one submit stopped, one original-ACK reconcile succeeded.
  short=key.removeprefix('libero_goal_').replace('_seed','s')
  logs=[]
  for mode,code in [('submit',1),('reconcile',0)]:
   lp=R/'results/formal_main_v2/control_transport'/(mode+'_goal_r5_'+short+'_20261021T0449.jsonl')
   events=[json.loads(x) for x in raw(lp).splitlines()];need(len(events)==2,'exact start/end transport pair')
   st,en=events;cmd=['/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python','-B',str(R/GATE/'gateway.py'),'--pair-key',key,'--dispatch-sha256',GPIN,'--scope-sha256',SPIN,'--admission-sha256',sha(admb),'--'+mode,'--root-reviewed']
   need(st['event']=='control_start' and en['event']=='control_end' and st['command']==cmd and st['entrypoint_sha256']==GPIN and en['returncode']==code and en['source173_and_entrypoint_unchanged'] is True,'exact '+mode+' execution and unchanged source')
   need(st['time_ns']<en['time_ns'] and st['pid']==en['pid'],'transport temporal identity')
   logs.append((st,en))
  seconds=lambda value:datetime.datetime.fromisoformat(value).timestamp()
  need(previous_end<logs[0][0]['time_ns']<logs[0][1]['time_ns']<logs[1][0]['time_ns']<logs[1][1]['time_ns'],'serial submit/reconcile transaction sequence')
  need(logs[0][0]['time_ns']/1e9<=seconds(pending['created_utc'])<seconds(ack['started_utc'])<=seconds(ack['returned_utc'])<seconds(failed['utc'])<=logs[0][1]['time_ns']/1e9,'pending before sbatch ACK then protected failure')
  need(logs[1][0]['time_ns']/1e9<=seconds(ra['utc'])<=logs[1][1]['time_ns']/1e9,'first release occurred only within original-ACK reconcile')
  previous_end=logs[1][1]['time_ns']
  state['pending_submission']['status']='release_attempt_persisted'
  postderived=replay_observation(g,c,d,state,f['post_release_observation.json'],allow_job=jid)
  need(postderived['occupied']==IDS[:ordinal],'post-release slots exactly once per requested GPU')
  postrow=f['post_release_observation.json']['observation']['rows'][jid]
  for k in ['status','exit_code','elapsed_seconds','allocation','node']:state['registered_jobs'][-1][k]=postrow[k]
  state['pending_submission']=None
  state['current_round_cost']['registered_jobs']=sum(j.get('experiment')=='formal_main_v2' for j in state['registered_jobs'])
  state['current_round_cost']['allocated_gpu_seconds']=postderived['allocated_formal_GPU_seconds']
  state['current_round_cost']['allocated_gpu_hours']=postderived['allocated_formal_GPU_seconds']/3600
  state['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(postderived['occupied'])
  state['autonomous_training_v1']['occupied_job_ids']=postderived['occupied']
  committed=f['committed.json'];need(committed['job_id']==jid and committed['status']=='submitted_once_registered_then_released' and committed['automatic_retry'] is False,'recorded single transaction commit')
  need(statehash(state)==committed['state_sha256'],'exact committed-state CAS reconstruction')
  previous_hash=committed['state_sha256']
  bad=copy.deepcopy(ack);bad['stdout']=IDS[0]+'\n'+jid+'\n'
  reject('multiple ACK forbidden '+key,lambda:d.parse_ack(bad,set()))
  bad=copy.deepcopy(f['released_identity.json']['fields']);bad['Comment']='foreign'
  reject('wrong release comment '+key,lambda:d.validate_new_identity(expected_job,bundle,bad,False))
  bad=copy.deepcopy(dispatch);bad['pair_key']=KEYS[(ordinal)%5]
  reject('cross-pair held dispatch '+key,lambda:e.validate_dispatch(ctx,bad,res,auth,ah,jid,sha(resbytes)))
  results.append(dict(pair_key=key,job_id=jid,authorization_sha256=ah,token=token,submit_count=1,release_count=1,original_ACK=jid+'\n',protected_failure=failed,preflight_state_sha256=f['preflight.json']['state_sha256'],registered_held_state_sha256=reg['state_sha256'],committed_state_sha256=committed['state_sha256'],occupied_before=beforederived['occupied'],occupied_held=heldderived['occupied'],occupied_after=postderived['occupied'],GPU_seconds_at_commit=postderived['allocated_formal_GPU_seconds'],scientific_results_accepted=0))
 need(previous_hash==FINAL and state==final,'exact five-transaction state equals saved root final bytes')
 need(final['pending_submission'] is None and final['autonomous_training_v1']['reserved_GPU_slots']==0 and final['autonomous_training_v1'].get('pending_submission') is None,'both pending clear after real commits; reserve0')
 need(final['registered_jobs'][:303]==state0['registered_jobs'],'all old registrations retained')
 need(final['formal_main_progress']['test_opened'] is False and final['formal_main_progress']['global_release_created'] is False and final['formal_main_progress']['completed_final_trials']==0,'final remains sealed in real state')
 later=read(R/LATER,LATERPIN);need(later['state_sha256']==FINAL and later['all_running_costs_are_lower_bounds'] is True and later['new_trials_accepted']==0 and later['scientific_acceptance_inferred'] is False,'last saved observation scope')
 fake=SavedScheduler(later['observation']['queries']);rebuilt=g.actual_observation(c,fake,final['registered_jobs'])
 need(rebuilt==later['observation'] and fake.i==len(fake.queries),'last saved accounting replay')
 caps=c.capacity(final['registered_jobs'],rebuilt,'3034538');need(caps==later['capacity'] and caps['occupied']==IDS and not caps['unknown'] and not caps['findings'],'last saved all-mode5 capacity')
 for q in later['scontrol_queries']:
  need(q['returncode']==0 and q['stderr']=='' and g.fields(q['stdout'])==later['active_details'][q['argv'][-1]],'last saved raw active details')
 for j in final['registered_jobs']:
  jid=str(j['job_id'])
  if jid in IDS:g.validate_live_identity(j,later['active_details'][jid],rebuilt['queue'][jid])
 total=sum(rebuilt['rows'][str(j['job_id'])]['elapsed_seconds']*rebuilt['rows'][str(j['job_id'])]['gpus'] for j in final['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 need(total==later['formal_GPU_seconds']==1995402 and later['formal_unique_allocations']==278,'278 original allocations once and saved1995402GPU seconds')
 need([rebuilt['rows'][j]['elapsed_seconds'] for j in IDS]==[260,225,194,142,113] and all(rebuilt['rows'][j]['status']=='RUNNING' for j in IDS),'last saved five running rows, no repoll')
 report=dict(schema='formal_main_v2',kind='Goal_remaining5_real_ACK_release_independent_review',status='passed_real_transaction_evidence',reviewed_by='spatial588_recovery_author_2054',review_scope='saved original ACK/token/held/CAS/one-release/capacity evidence; no live polling or scientific result reads',blockers=[],source_scope=dict(gateway_sha256=GPIN,scope_sha256=SPIN,runtime_package_sha256=MPIN),baseline_state_sha256=BASEPIN,state_sha256=FINAL,exact_state_transition_reconstructed=True,historical303_registration_rows_unchanged=True,real_submissions_verified=5,original_ACK_reconciliations_verified=5,real_release_attempts_verified=5,new_submissions_by_reviewer=0,new_releases_by_reviewer=0,live_scheduler_queries_by_reviewer=0,scientific_results_read=False,scientific_results_accepted=0,final_sealed=True,pending_after=None,reserved_GPU_slots_after=0,checks=len(CHECKS),negative_checks=len(NEG),negative_results=NEG,pairs=results,last_saved_observation=ref(R/LATER),GPU_seconds_last_saved=total,GPU_hours_last_saved=total/3600,GPU_cost_is_running_lower_bound=True,legacy_display_fields_require_root_refresh=['current_round_cost.final','current_round_cost.scope','current_round_cost.observation'],notes=['All five first submits stopped after retained original ACK because new sacct row was not yet visible; one later original-ACK reconcile per pair performed the first and only release.','Submission/release counts bind the complete saved audit directory, exact two transport executions per pair, immutable source control flow, unique registered IDs and saved complete registered queue/accounting; no claim of new independent live scheduler observation is made.','The old current_round_cost final/scope display text remains inherited in the exact post-submit state and must be refreshed in the next root documentation transaction; actual cost is a running lower bound.'],started_utc=started,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 rr=put('independent_review.json',report)
 with (D/'README.md').open('x') as f:f.write('Initial checker completed exact five state reconstructions but accessed an absent optional autonomous pending key as mandatory; v2 uses the same .get semantics as the reviewed gateway, preserving the initial failure. Independent offline audit of five real held submissions and original-ACK reconciliations. Replays only preserved scheduler responses; never queries Slurm. Every state transition is rebuilt from the genuine pre-submission state and exact saved pending/job/cost evidence to the root final SHA. Five accounting-delay failures are retained and distinguished from GPU execution failures. All science remains pending terminal consumers.\n')
 mr=put('delivery_manifest.json',dict(schema='formal_main_v2',root=str(D.relative_to(R)),file_count=7,files=[ref(D/n) for n in ['audit_transactions.py','failed_review.json','audit_transactions_v2.py','evidence_inventory.json','post_submit_state.json','independent_review.json','README.md']]))
 print(json.dumps(dict(status=report['status'],checks=len(CHECKS),negative_checks=len(NEG),review=rr,manifest=mr)))
if __name__=='__main__':
 try:main()
 except BaseException as e:put('failed_review_v2.json',dict(status='failed',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks_so_far=len(CHECKS)));raise
