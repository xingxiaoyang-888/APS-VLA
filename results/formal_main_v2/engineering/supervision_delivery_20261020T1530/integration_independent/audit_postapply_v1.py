"""Read-only independent post-apply verification; only writes private audit evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,importlib.util,os,sys,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/completed_integration_independent_20261020T1530';B='results/formal_main_v2/preflight/heartbeat_20261020T2330';checks=[];evidence={}
def guard(event,args):
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes,os.PathLike)) and ((isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))):assert Path(p).resolve().is_relative_to(D),'write outside audit'
 elif event.startswith('subprocess') or event in ['os.system','os.posix_spawn']:raise RuntimeError('no process or scheduler calls')
 elif event in ['os.mkdir','os.remove','os.rmdir','os.rename','os.replace']:
  for p in (args[:2] if event in ['os.rename','os.replace'] else args[:1]):assert Path(p).resolve().is_relative_to(D),'mutation outside audit'
sys.addaudithook(guard)
def ck(n,v):
 assert v,n;checks.append(n)
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):return digest(p.read_bytes())
def read(rel,pin=None):
 p=R/rel;b=p.read_bytes();h=digest(b)
 if pin:ck('exact:'+rel,h==pin)
 evidence[rel]=h;return json.loads(b)
def putraw(n,b):
 p=D/n
 with p.open('xb') as f:f.write(b)
 return {'path':str(p.relative_to(R)),'sha256':digest(b),'bytes':len(b)}
def put(n,v):return putraw(n,(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
intent=read(B+'/integration_1530_intent.json','c3e0f7665ecccb3165aeed79a97a2d3a9998e6d1247553ae398f871ad430bbc5')
completion=read(B+'/integration_1530_completion.json','36bb998b131d0d86cda0624b8f0d632c69238c73c0b0d87eccc298f2e43b1e5a')
summary=read(B+'/completed_evidence_integration_1530.json','ca8c64984a37a75e88ae47cb5e641b10f2b238f4ded1f1b73a1a8db772482822')
old=read(B+'/integration_1530_state_before.json',intent['state_before_sha256']);ck('same_intent_completion_before',completion['state_before_sha256']==intent['state_before_sha256']==summary['state_before_sha256'])
for k,r in intent['inputs'].items():read(r['path'],r['sha256'])
for rel,pin in intent['writes'].items():ck('published_write:'+rel,sha(R/rel)==pin)
ck('source_matches_independently_reviewed_v2',intent['source']['sha256']=='c05d049e4d56d82708a64e05802ca9281f91f191d3e510ccbbc54550a8d25219')
source=B+'/root_operations/integrate_1530_v2.py';ck('published_source_exact',sha(R/source)==intent['source']['sha256'])
spec=importlib.util.spec_from_file_location('post1530_pure_candidate',R/source);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
d=m.inputs();applied,summ,out=m.prepare(old,intent['state_before_sha256'],d,summary['scheduler'],summary['capacity'],summary['utc'])
ck('pure_transform_reconstructs_actual_summary',summ==summary)
pretty=m.rawjson(applied);compact=(json.dumps(applied,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
ck('intent_pretty_candidate_exact',digest(pretty)==intent['state_candidate_sha256'])
ck('actual_atomic_state_encoding_exact',digest(compact)==completion['state_after_sha256'])
ck('controller_serialization_source',sha(R/'scripts/ops/formal_autonomous_training_v1/controller.py')=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
ck('reconstructed_root_operation_bytes',out[source]==(R/source).read_bytes())
for rel,b in out.items():ck('reconstructed_published_output:'+rel,digest(b)==intent['writes'][rel])
ck('preserve_actual_controller_pending_registry',all(applied[k]==old[k] for k in ['autonomous_training_v1','pending_submission','registered_jobs']))
f=applied['formal_main_progress'];p=old['formal_main_progress'];ck('actual66and331000',f['root_and_independent_completed_arms']==66 and f['root_and_independent_reviewed_arm_updates']==331000)
ck('actual400_4400_5612_5000',f['current_action_development_unique_initial_states']==400 and f['current_action_development_trial_count']==4400 and f['completed_development_trials']==5612 and summary['compatible_current_and_explicit_legacy_trials']==5000)
ck('actual_machine_fields_preserved',f['trained_arms']==p['trained_arms'] and f['machine_and_prior_verified_arm_updates']==p['machine_and_prior_verified_arm_updates'] and f['automatic_machine_verified_pairs']==p['automatic_machine_verified_pairs'])
ck('hold_and_final_retained','3049679' not in f['new_action_development_verified_by_job'] and f['nonLong_development_submissions_1317']==p['nonLong_development_submissions_1317'] and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'] and not summary['Object256seed23_bridge_scientifically_admitted'])
raw={}
for line in summary['scheduler']['raw_sacct'].splitlines():
 a=line.split('|');jid=a[0]
 if jid.isdecimal():
  ck('raw_cost_row_unique:'+jid,jid not in raw);alloc=dict(t.split('=',1) for t in a[4].split(',') if '=' in t);raw[jid]=(int(a[3]),int(alloc.get('gres/gpu','0')))
ids=[str(j['job_id']) for j in old['registered_jobs']];ck('actual_registry_unique',len(ids)==len(set(ids)))
secs=sum(raw[str(j['job_id'])][0]*raw[str(j['job_id'])][1] for j in old['registered_jobs'] if j.get('experiment')=='formal_main_v2')
ck('actual_cost_recomputed_once',secs==summary['allocated_GPU_seconds']==applied['current_round_cost']['allocated_gpu_seconds'] and summary['acceptance_allocation_seconds_not_added_again']==67399)
ck('acceptance_no_new_submission',summary['new_GPU_jobs_by_integration']==0 and completion['new_GPU_jobs_by_integration']==0 and completion['new_dispatch_trials_accepted']==0)
for rel,pin in intent['previous_document_sha256'].items():
 preview=(R/'.local/integration_candidate_20261020T1530/preview_95f917f55464'/rel).read_bytes();post=(R/rel).read_bytes()
 first,_,_ = post.partition(b'\n');old_doc_candidates=[post[:len(first)+1]+post[pos+2:] for pos in []]
 # The earlier independent review verified the original history; both previews prepend a variable brief before the same historical suffix.
 old_file=None
 lines=post.splitlines(keepends=True)
 for i in range(1,len(lines)):
  b=lines[0]+b''.join(lines[i:])
  if digest(b)==pin:old_file=b;break
 ck('historical_doc_bytes_restored:'+rel,old_file is not None)
 ck('preaudit_historical_body_in_post:'+rel,preview.endswith(old_file.partition(b'\n')[2]) and post.endswith(old_file.partition(b'\n')[2]))
with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
 fcntl.flock(lock,fcntl.LOCK_SH);live_raw=(R/'results/experiment_supervisor/state.json').read_bytes();live=json.loads(live_raw)
livef=live['formal_main_progress']
for k in ['root_and_independent_completed_arms','root_and_independent_reviewed_arm_updates','completed_development_trials','current_action_development_trial_count','current_action_development_unique_initial_states','current_action_development_unique_initial_states_by_suite','new_action_development_verified_by_job','nonLong_development_submissions_1418','integration_20261020T1530_accepted']:
 ck('live_core_unchanged:'+k,livef[k]==f[k])
ck('live_goal_training_accepted',livef['completed_training_pairs']['libero_goal_k64_seed17']==f['completed_training_pairs']['libero_goal_k64_seed17'])
ck('live_final_closed',not livef['test_opened'] and not livef['global_release_created'] and livef['completed_final_trials']==0)
oldids=set(ids);liveids={str(j['job_id']) for j in live['registered_jobs']};ck('later_registry_did_not_drop_old_jobs',oldids<=liveids)
ck('live_cost_not_regressed',live['current_round_cost']['allocated_gpu_seconds']>=secs)
statecopy=putraw('applied_state_exact_reconstructed.json',compact);livecopy=putraw('post_review_live_state.json',live_raw)
report={'schema':'formal_main_v2','kind':'independent_postapply_completed_evidence_integration_review','status':'passed_applied_core','utc':datetime.now(timezone.utc).isoformat(),'checks_passed':len(checks),'checks':checks,'root_intent':{'path':B+'/integration_1530_intent.json','sha256':evidence[B+'/integration_1530_intent.json']},'root_completion':{'path':B+'/integration_1530_completion.json','sha256':evidence[B+'/integration_1530_completion.json']},'root_summary':{'path':B+'/completed_evidence_integration_1530.json','sha256':evidence[B+'/completed_evidence_integration_1530.json']},'actual_state_transition_reconstructed_from_intent_bound_before':statecopy,'live_state_capture':livecopy,'actual_apply_machine_count':f['trained_arms'],'actual_apply_machine_updates':f['machine_and_prior_verified_arm_updates'],'counts':{'completed_groups':66,'reviewed_updates':331000,'accepted_new_development':600,'current_action':4400,'raw_accepted':5612,'compatible':5000,'unique_initials':400},'actual_apply_raw_sacct_GPU_seconds':secs,'accepted_allocations_not_readded_seconds':67399,'later_registered_job_ids':sorted(liveids-oldids),'live_controller_may_advance_separately':True,'apply_used_original_compact_controller_JSON_encoding':True,'Goal200_HOLD_excluded':True,'Object256s23_bridge_scientifically_admitted':False,'source173_revalidated_via_pure_inputs':True,'final_sealed':True,'new_GPU_jobs_by_auditor':0,'state_mutations_by_auditor':False,'top_level_narrative_refresh_still_separate_root_responsibility':True,'evidence_sha256':evidence}
r=put('postapply_review.json',report);files=[{'path':str(x.relative_to(R)),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(D.iterdir()) if x.is_file() and x.name!='complete_manifest.json'];man=put('complete_manifest.json',{'schema':'formal_main_v2','kind':'pre_and_post_independent_completed_evidence_integration_delivery','files':files,'postapply_review':r,'private_only':True,'new_GPU_jobs':0})
print(json.dumps({'report':r,'manifest':man,'checks_passed':len(checks),'GPU_seconds':secs,'later_registered_job_ids':sorted(liveids-oldids)}))
