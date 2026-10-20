"""Independent post-apply reconstruction of original Goal64s41 root mutation."""
from pathlib import Path
from datetime import datetime,timezone
import copy,fcntl,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/Goal64s41_integration_independent_20261020T1644';V=R/'.local/Goal64s41_integration_preview_20261020T1644';B='results/formal_main_v2/preflight/heartbeat_20261021T0044'
p=D/'audit_preview.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='badb32fdc75f7bfec04fc3302a64d616ef5a17702c8ff4050db4dbc288a17b22'
spec=importlib.util.spec_from_file_location('Goal41PostShared1644',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
check,raw,rd,rr,h=m.check,m.raw,m.rd,m.rr,m.hbytes
INTENT_SHA='d0dabd20a709dd2f9d37ef2426f2677883758dc0e63b82614397573e6c9f6c64';COMPLETE_SHA='777c488ca02ee6e34ba5395c350e7abfcd98fc697263d552b88880fec94e1837';SUMMARY_SHA='c2db3e60218e486bae15faa5f7480527379f9525deea893ac2fc13038bbf11f6'
def pretty(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def compact(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def put(p,data):
 with p.open('xb') as f:f.write(data)
def main():
 preview=rd(D/'preview_independent_review.json','dc5588333a9a7862aa4cfcd60ab21c54b011aebc0f169e0604671e51804977f6');check(preview['status']=='passed' and preview['post_apply_verification_performed'] is False,'actual independent preview only')
 intent=rd(B+'/integration_intent.json',INTENT_SHA);completion=rd(B+'/integration_completion.json',COMPLETE_SHA);summary=rd(B+'/summary.json',SUMMARY_SHA)
 check(intent['code']['path']==m.CODE and intent['code']['sha256']==m.CODE_SHA,'same reviewed root mutation source');raw(m.CODE,m.CODE_SHA)
 check(intent['summary']==completion['summary']=={'path':B+'/summary.json','sha256':SUMMARY_SHA},'actual completion summary precise')
 check(completion['status']=='root_applied_pending_post_independent_crosscheck' and completion['final_sealed'] is True and completion['new_GPU_jobs']==0 and completion['new_development_accepted']==0 and completion['new_completed_arms']==2 and completion['new_reviewed_updates']==10000,'exact applied scope')
 before_bytes=raw(B+'/integration_state_before.json',intent['before_sha256']);old=json.loads(before_bytes)
 check(completion['state_before_sha256']==intent['before_sha256']==summary['state_before_sha256'],'actual CAS before proof')
 va=rd(V/'state_after.json',preview['state_after_sha256'])
 expected=copy.deepcopy(old);f=expected['formal_main_progress'];vf=va['formal_main_progress']
 f['completed_training_pairs'][m.PAIR]=copy.deepcopy(vf['completed_training_pairs'][m.PAIR]);f['root_and_independent_completed_arms']=68;f['root_and_independent_reviewed_arm_updates']=341000
 f['integration_20261020T1644_accepted']=intent['summary'];f['supervision_integrity_review_20261020T1644']=copy.deepcopy(vf['supervision_integrity_review_20261020T1644']);f['supervision_integrity_review_20261020T1644']['summary']=intent['summary']
 expected['last_root_supervision_snapshot']=intent['summary'];expected['last_supervision_utc']=expected['updated_utc']=summary['utc'];expected['current_work']=va['current_work'];expected['next_actions']=va['next_actions']
 check(h(pretty(expected))==intent['after_sha256'],'independently reconstructed exact pretty after identity')
 check(h(compact(expected))==completion['state_after_sha256'],'original controller compact serialization exact applied identity')
 ind=rd(m.IND,m.IND_SHA);root=rr(summary['root_review']);selected=rr(summary['selected_server']);obs=rr(summary['observation'])
 result=m.validate_core(old,expected,summary,intent,ind,root,selected,obs)
 raw(completion['independent']['path'],m.IND_SHA);check(completion['independent']==summary['independent_review'],'actual canonical independent report byteidentical')
 raw('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
  state_bytes=(R/'results/experiment_supervisor/state.json').read_bytes()
  fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
 put(D/'state_observed_after_apply.json',state_bytes);state=rd(D/'state_observed_after_apply.json')
 check(state['formal_main_progress']==expected['formal_main_progress'],'actual post formal acceptance exactly reconstructed')
 check(state['pending_submission']==expected['pending_submission'],'actual pending unchanged')
 allowed_runtime={'autonomous_training_v1','registered_jobs','updated_utc','current_round_cost'}
 for key,value in expected.items():
  if key not in allowed_runtime:check(state[key]==value,'actual post preserved '+key)
 old_jobs={str(j['job_id']):j for j in expected['registered_jobs']};now_jobs={str(j['job_id']):j for j in state['registered_jobs']};check(set(now_jobs)==set(old_jobs) and len(now_jobs)==len(state['registered_jobs']),'actual same full job identityset no newjobs')
 runtime_diff={}
 for jid,job in old_jobs.items():
  change={k:{'before':job.get(k),'after':now_jobs[jid].get(k)} for k in set(job)|set(now_jobs[jid]) if job.get(k)!=now_jobs[jid].get(k)}
  if change:
   check(jid=='3034538' and set(change)=={'elapsed_seconds'} and now_jobs[jid]['elapsed_seconds']>=job['elapsed_seconds'] and job['gpus']==0,'legitimate CPU-controller elapsed-only later tick')
   runtime_diff[jid]=change
 a=expected['autonomous_training_v1'];z=state['autonomous_training_v1'];cdiff={k:[a.get(k),z.get(k)] for k in set(a)|set(z) if a.get(k)!=z.get(k)}
 check(set(cdiff)<= {'last_tick_utc'},'subsequent controller change restricted to observed heartbeat')
 if cdiff:check(datetime.fromisoformat(z['last_tick_utc'])>=datetime.fromisoformat(a['last_tick_utc']),'later controller tick monotonic')
 check(state['current_round_cost']==expected['current_round_cost'],'actual cost object unchanged byintegration')
 check(sum((j.get('elapsed_seconds') or 0)*(j.get('gpus') or 0) for j in state['registered_jobs'])==state['current_round_cost']['allocated_gpu_seconds'],'post actual allocation sum still original ledger')
 docs=[]
 for rel,sha in intent['doc_before'].items():
  olddoc=raw(V/'documents_before'/Path(rel).name,sha);newdoc=raw(rel,intent['doc_after'][rel]);cr=completion['documents'][rel]
  check(cr['sha256']==intent['doc_after'][rel] and cr['bytes']==len(newdoc) and cr['path']==rel,'actual doc completion '+rel)
  head,sep,body=olddoc.decode().partition('\n');h2,s2,b2=newdoc.decode().partition('\n');check(head==h2 and sep==s2=='\n' and newdoc.endswith(body.encode()),'actual full document history preserved '+rel)
  prefix=b2[:-len(body)] if body else b2
  check(prefix.startswith('\n') and prefix.endswith('\n\n') and prefix.count('Goal64 seed41')==1,'actual single current paragraph '+rel)
  for term in ['68/72','341000','A选3500','B选3000','11次完整验证','59575','不重复加账','4400','5000','400唯一初态','HOLD','尚未准入','0/35200封存']:check(term in prefix,'actual doc fact '+rel+' '+term)
  docs.append(cr)
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');check(len(inventory['files'])==173,'all173 afterintegration')
 for rel,sha in inventory['files'].items():raw(rel,sha);check(m.snapshot_hash(m.S/rel)==sha,'actual snapshot unchanged '+rel)
 raw(Path(__file__))
 for rel,sha in m.readmap.items():check(h((R/rel).read_bytes())==sha,'post evidence stable '+rel)
 out={'schema':'formal_main_v2','kind':'independent_Goal64s41_integration_post_review','status':'passed','reviewed_utc':datetime.now(timezone.utc).isoformat(),'code':intent['code'],'preview_review':{'path':str((D/'preview_independent_review.json').relative_to(R)),'sha256':'dc5588333a9a7862aa4cfcd60ab21c54b011aebc0f169e0604671e51804977f6'},'actual_intent':{'path':B+'/integration_intent.json','sha256':INTENT_SHA},'actual_completion':{'path':B+'/integration_completion.json','sha256':COMPLETE_SHA},'actual_summary':intent['summary'],'actual_before_sha256':intent['before_sha256'],'reconstructed_pretty_after_sha256':intent['after_sha256'],'reconstructed_controller_compact_after_sha256':completion['state_after_sha256'],'observed_state':{'path':str((D/'state_observed_after_apply.json').relative_to(R)),'sha256':h(state_bytes)},'later_controller_tick_differences':{'registered_jobs':runtime_diff,'autonomous_training_v1':cdiff},'result':result,'documents':docs,'all173_R_S_unchanged':True,'post_review_status_not_mutated_by_subagent':True,'root_may_mark_only_bound_postreview_passed':True,'weights_copied':False,'final_states_read':False,'canonical_state_docs_Git_Slurm_mutated':False,'checks':m.checks,'check_count':len(m.checks),'read_evidence_sha256':dict(sorted(m.readmap.items()))}
 put(D/'post_independent_review.json',pretty(out))
 print(json.dumps({'path':str((D/'post_independent_review.json').relative_to(R)),'sha256':h((D/'post_independent_review.json').read_bytes()),'checks':len(m.checks),'status':'passed','result':result,'later_controller_tick':{'registered_jobs':runtime_diff,'autonomous_training_v1':cdiff}}))
if __name__=='__main__':main()
