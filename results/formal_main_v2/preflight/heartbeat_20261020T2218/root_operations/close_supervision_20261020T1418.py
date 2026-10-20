from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,importlib.util,sys,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1418'
IND=dict(path=E+'/integration_independent/applied_integration_independent_review.json',sha256='366107ca5d32669aadfaf346c3ff4d1b86c178811f246ff76b505a42eeb4b309')
PREVIEW=dict(path=E+'/integration_independent/preview_integration_independent_review.json',sha256='c80ff2f5aa29054cfa07fdc6f6bd7a57fd6ce58091a0d252b9800d134f770fb6')
SUMMARY=dict(path=B+'/summary_after_dispatch.json',sha256='095f250254b8b7ba51a25322c45ef45ce8f4937b1d162b96d51f2f55c8f1e58f')
PROBE=dict(path=B+'/Goal_t0_probe_candidate_delivery.json',sha256='99679e834f879d5ce7ee1e3e3d9f61dda31c66f168367aad3cefcec651d7acac')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def check(rr):
 assert h(R/rr['path'])==rr['sha256'];return rd(rr['path'])
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('close1418ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
ind=check(IND);pre=check(PREVIEW);summary=check(SUMMARY);probe=check(PROBE)
assert ind['status']=='passed' and ind['actual_root_apply_verified'] and not ind['blocking_findings'] and ind['checks_passed']==101
assert ind['accepted_new_development_trials']==1000 and ind['current_action_trials']==3800 and ind['raw_accepted_trials']==5012
assert ind['held_Goal256_trials']==200 and ind['compatible_current_and_explicit_legacy']==4400 and ind['training_accepted64_72']
assert ind['final_completed']==0 and not ind['final_release'] and not ind['sealed_final_values_read'] and ind['unique_initials']==400
assert ind['source173_R_S_unchanged'] and ind['GPU_seconds_snapshot']==summary['allocated_GPU_seconds']==1950237
assert pre['status']=='passed' and probe['new_GPU_jobs']==0 and probe['real_GPU_acceptance'] is False
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 path=R/'results/experiment_supervisor/state.json';before=h(path);s=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress']
 key='supervision_integrity_review_20261020T1418';assert key not in f
 assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 assert s['last_root_supervision_snapshot']==SUMMARY and f['root_and_independent_completed_arms']==64 and f['root_and_independent_reviewed_arm_updates']==321000
 assert f['completed_development_trials']==5012 and f['current_action_development_trial_count']==3800 and f['completed_final_trials']==0
 assert not f['test_opened'] and not f['global_release_created']
 assert '3049679' not in f['new_action_development_verified_by_job']
 assert sum(row['completed_trials_accepted'] for row in f['nonLong_development_submissions_1418'])==0
 completion=rd(B+'/integration_1418_completion.json');assert completion['summary']==SUMMARY
 for rel,rr in completion['documents'].items():assert h(R/rel)==rr['sha256']
 now=datetime.now(timezone.utc).isoformat()
 value=dict(status='passed',utc=now,independent_review=IND,pre_integration_independent_review=PREVIEW,
  root_accepted_summary=SUMMARY,submission_independent_integration_review_pending=False,
  new_training_groups_accepted=0,new_development_trials_accepted=1000,current_action_trials=3800,
  held_unaccepted_Goal_trials=200,new_submitted_trials_accepted=0,final_release=False,
  immutable_summary_records_its_original_pending_time=True,no_original_guard_waived=True)
 f[key]=value
 f['Goal_t0_probe_candidate_unreviewed']=dict(status='awaiting_root_and_independent_audit_GPU_not_run',delivery=PROBE,
  handoff=dict(path=E+'/Goal_t0_probe_candidate/handoff.json',sha256='774051f9132e194296d9d84978e69f9622a229ef912f990ce96bf7def7f3d984'),
  GPU_jobs=0,scientific_retry_authorized=False)
 out=R/B/'root_supervision_integrity_closure.json'
 proof=dict(**value,state_before_sha256=before,controller_registry_unchanged=True,new_GPU_submissions=0,
  Goal_probe_candidate=f['Goal_t0_probe_candidate_unreviewed'])
 with out.open('x') as stream:json.dump(proof,stream,sort_keys=True,indent=2);stream.write('\n')
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 expected=copy.deepcopy(old);expected['formal_main_progress'][key]=copy.deepcopy(value);expected['formal_main_progress']['Goal_t0_probe_candidate_unreviewed']=copy.deepcopy(f['Goal_t0_probe_candidate_unreviewed'])
 assert s==expected
 c.atomic_json(path,s,before)
 print(json.dumps(dict(status='root_and_independent_integration_closed',receipt=dict(path=out.relative_to(R).as_posix(),sha256=h(out)),state_sha256=h(path),training64_72=True,current_trials=3800,held200=True,final_release=False)))
