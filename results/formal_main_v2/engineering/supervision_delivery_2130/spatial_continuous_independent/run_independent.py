"""Independent bounded CPU tests and actual read-only Spatial admission bridge."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,importlib.util,json,os,subprocess,sys,time,traceback,contextlib
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
C=R/'.local/spatial_continuous_admission_2130'
PINS={'admission.py':'0e5d2bbdca27640c4784393b3ea6a17969a7c6235bdeeb10b61c4a8ab7546b74','gateway.py':'71af9cf0bce935d00934db8c8198f7f9624fd7194f570e36efd95f77da0634c6','test_continuation.py':'a684c5c449246e66511537ae684fff5cdf5b12e4c5303bb88bab2bc3864a3d7b','actual_prepare_a2.json':'6705874a0d4fc784da3bed7a0bb310044c376c7d5d415213469061674eab2529','authorization_a2_draft.json':'7d1d972b0b37ce7dabef2bfff93580f6f403eac94c4d85bcf75f96023f667721','candidate_review.json':'83a3961f25020d0f1cce9d1287323fc23d882f27102ba25fa8bba93f4198ec30'}
def digest(b):return hashlib.sha256(b).hexdigest()
def save(name,value):
 p=D/name
 assert p.parent==D
 b=json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()+b'
'
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':digest(b),'bytes':len(b)}
def pin_sources():
 for n,h in PINS.items():assert digest((C/n).read_bytes())==h,n
 assert digest((D/'test_independent.py').read_bytes())=='f045a8f3dca3172f06542fe5537cc66ec32a684763dd64c80d8b3feebb8e2df8'
def tests():
 pin_sources()
 cmd=[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','--basetemp',str(D/'pytest_independent_a1'),'--junitxml',str(D/'independent_tests_a1.xml'),str(D/'test_independent.py')]
 save('independent_tests_a1_command.json',{'argv':cmd,'cwd':str(D),'PYTHONDONTWRITEBYTECODE':'1','production_state_or_submission_allowed':False})
 with (D/'independent_tests_a1.log').open('xb') as log:
  r=subprocess.run(cmd,cwd=D,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 save('independent_tests_a1_result.json',{'returncode':r.returncode,'utc':datetime.now(timezone.utc).isoformat()})
 print('TESTS',r.returncode,flush=True)
 if r.returncode:raise RuntimeError('independent tests failed; preserved log')
def actual():
 pin_sources()
 spec=importlib.util.spec_from_file_location('ind_spatial_gateway',C/'gateway.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);a=g.a
 c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'ind_spatial_controller')
 auth=json.loads((C/'authorization_a2_draft.json').read_bytes())
 authref={'path':(C/'authorization_a2_draft.json').relative_to(R).as_posix(),'sha256':PINS['authorization_a2_draft.json']}
 try:g.validate_authorization(R,authref)
 except ValueError as e:rejection=str(e)
 else:raise AssertionError('unsigned draft unexpectedly authorizes')
 assert 'typed' in rejection
 lock=R/'results/experiment_supervisor/.writer.lock';assert lock.exists()
 started=datetime.now(timezone.utc).isoformat()
 with c.exclusive_lock(lock):
  before=c.file_sha(R/a.STATE);state=c.read_json(R/a.STATE)
  assert state.get('pending_submission') is None
  assert not any(j.get('continuous_admission',{}).get('version')==a.VERSION for j in state['registered_jobs'])
  science=a.Science(R);assert science.reviewer is None
  plan=science.prepare(state,auth,authref)
  native=a.NativeIO().preflight(plan)
  author=json.loads((C/'actual_prepare_a2.json').read_bytes())
  norm=copy.deepcopy(plan);norm['invocation']['registered_utc']=author['plan']['invocation']['registered_utc']
  assert norm==author['plan'],'actual independent plan differs beyond fresh timestamp'
  assert native==author['server_metadata'],'actual server identity differs'
  science.e.unchanged();after=c.file_sha(R/a.STATE);assert after==before
  assert (R/a.INVREL).exists() is False and (a.P/a.INVREL).exists() is False
  source173={rel:h for rel,h in plan['inventory']['files'].items()};assert len(source173)==173
  result={'schema':'formal_main_v2','kind':'spatial_continuous_independent_actual_readonly_bridge','status':'passed_actual_metadata_and_original_raw_reconstruction',
   'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),'source_pins':PINS,
   'state_sha256_before':before,'state_sha256_after':after,'state_changed':False,
   'registered_jobs_observed':len(state['registered_jobs']),'pending_submission':None,
   'blocked_pair_preserved':copy.deepcopy(state['autonomous_training_v1']['blocked_pairs'].get(a.PAIR)),
   'controller_snapshot':{k:copy.deepcopy(state['autonomous_training_v1'].get(k)) for k in ['activation','controller_job_id','owner_id','reserved_GPU_slots','reservation_root_record','root_submission_hold']},
   'original_reviewer_used':{'path':a.REVIEWER,'sha256':a.REVIEWER_SHA,'verify_server_resume':False,'synthetic_reviewer_injected':False},
   'four_history':a.history(state),'historical_GPU_seconds':11958,'source173_R_and_S_match':True,
   'actual_plan_equal_author_except_registration_timestamp':True,'retained_finalizations':plan['retained_finalizations'],
   'plan':plan,'server_metadata':native,'evidence_sha256':dict(science.e.hashes),
   'unsigned_draft_rejected':rejection,'authorization_validated':False,'GPU_submitted':False,'Slurm_queried':False,
   'optimizer_or_RNG_deserialized':False,'models_loaded':False,'real_1500_to5000_continuation_run':False,
   'remaining':['Root must publish exact two source bytes and sign a distinct exact-once authorization.','Submission requires fresh shared-lock/CAS full Slurm/lease/capacity/raw/resume gate; CPU controller remains queried and zero-GPU.','This pass does not clear the retained blocked record, consume other reservations, retry failures, or release final evaluation.']}
 ref=save('actual_readonly_bridge_a1.json',result)
 print(json.dumps({'actual_receipt':ref,'server_files':len(native['server_files']),'resume_files':len(native['server_resume_checks']),'evidence_count':len(science.e.hashes)}),flush=True)
def main():
 tests()
 with (D/'actual_readonly_bridge_a1.log').open('x') as log:
  with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
   try:actual()
   except Exception:traceback.print_exc();raise
 print('ACTUAL BRIDGE PASSED',flush=True)
if __name__=='__main__':main()
