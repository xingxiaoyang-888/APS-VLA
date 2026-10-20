from pathlib import Path
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2117'
IR={'path':'results/formal_main_v2/engineering/supervision_delivery_1317/integration_independent/independent_review.json','sha256':'7128c96f5c3b08ff14d9c9add90e33e3f61889aeed27d887bfc68c26c575dc66'}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_bytes())
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('auditaccept1317ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd(sp);old=copy.deepcopy(s)
 assert h(R/IR['path'])==IR['sha256'];report=rd(R/IR['path']);assert report['status']=='passed'
 summary=B+'/summary_after_dispatch.json'
 assert h(R/summary)=='91a102f6f2ea3edfc0cf7441b1bd72a40f1f90e7040fe064c8aaf7d6aafb6037'
 assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 f=s['formal_main_progress'];assert f['completed_development_trials']==4012 and f['current_action_development_trial_count']==2800
 assert f['root_and_independent_completed_arms']==64 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 key='supervision_integrity_review_1317';assert key not in f
 f[key]=dict(status='passed',independent_review=IR,summary={'path':summary,'sha256':h(R/summary)},submission_independent_integration_review_pending=False,
  historical_summary_pending_flag_preserved_as_its_creation_time=True,scientific_terminal_reviews_unchanged=True)
 out=B+'/integration_independent_root_acceptance.json'
 proof=dict(status='root_recorded_passed_independent_submission_and_integration_review',state_before_sha256=before,record=f[key],
  no_new_submissions=True,no_fresh_Slurm_query=True,no_results_recomputed=True,no_training_or_final_release_changes=True)
 with (R/out).open('x') as stream:json.dump(proof,stream,sort_keys=True,indent=2);stream.write('\n')
 with (R/B/'root_operations/record_1317_audit_acceptance.py').open('xb') as stream:stream.write(Path(__file__).read_bytes())
 expected=copy.deepcopy(old);expected['formal_main_progress'][key]=f[key];assert s==expected
 c.atomic_json(sp,s,before)
 print(json.dumps(dict(status=proof['status'],receipt=dict(path=out,sha256=h(R/out)),state_sha256=h(sp))))
