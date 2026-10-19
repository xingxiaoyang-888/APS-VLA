from pathlib import Path
import copy,hashlib,importlib.util,json,sys,unittest
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/downstream_pending_reconcile_2130');p=D/'reconcile.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='6e1ce05c0dcde70b7b9fcbd1ffc763b40c2766e6fac4abe1103e1a7350811d06'
s=importlib.util.spec_from_file_location('subject2130',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
ctx=m.dependencies();live=json.loads((m.R/ctx['g'].STATE).read_bytes());owner=json.loads((m.R/m.OWNER).read_bytes());assert m.validate_state(live,ctx,owner)
base=copy.deepcopy(live);base['registered_jobs']=copy.deepcopy(ctx['preflight']['registered_jobs'])
snap=copy.deepcopy(ctx['preflight']['scheduler_observation']);snap['rows'][m.JOB]={'job_id':m.JOB,'status':'RUNNING','exit_code':'0:0','elapsed_seconds':60,'allocation':'gres/gpu=1','node':'gpu4001','gpus':1,'scheduler_name':'cti-formal-downstream','scheduler_comment':ctx['token']};snap['queue'][m.JOB]={'status':'RUNNING','comment':ctx['token']}
class Tests(unittest.TestCase):
 def reject_state(self,modify):
  state=copy.deepcopy(base);modify(state)
  with self.assertRaises(ValueError):m.proposed_state(state,ctx,owner,snap)
 def reject_snap(self,modify):
  ss=copy.deepcopy(snap);modify(ss)
  with self.assertRaises(ValueError):m.proposed_state(base,ctx,owner,ss)
 def test_01_real_pending_identity(self):self.assertTrue(m.validate_state(live,ctx,owner))
 def test_02_real_original_evidence_ack(self):self.assertEqual(ctx['g'].parse_ack(type('A',(),ctx['ack'])(),set()),m.JOB)
 def test_03_synthetic_positive_exact_preservation(self):
  before=copy.deepcopy(base);out,cap=m.proposed_state(base,ctx,owner,snap);self.assertEqual(base,before);self.assertEqual(out['registered_jobs'][:-1],base['registered_jobs']);self.assertEqual(out['registered_jobs'][-1],ctx['job']);self.assertIsNone(out['pending_submission']);self.assertEqual(out['autonomous_training_v1']['reserved_GPU_slots'],0);self.assertEqual(out['autonomous_training_v1']['owner_id'],base['autonomous_training_v1']['owner_id']);self.assertEqual(out['autonomous_training_v1']['last_result'],base['autonomous_training_v1']['last_result']);self.assertEqual(len(cap['occupied']),8)
 def test_04_wrong_pending_token(self):self.reject_state(lambda x:x['pending_submission'].update(request_token='foreign'))
 def test_05_wrong_known_job(self):self.reject_state(lambda x:x['pending_submission'].update(known_job_id='3043710'))
 def test_06_missing_pending(self):self.reject_state(lambda x:x.update(pending_submission=None))
 def test_07_wrong_reservation(self):self.reject_state(lambda x:x['autonomous_training_v1'].update(reservation_root_record={'path':'other','sha256':'0'*64}))
 def test_08_consumed_auth(self):self.reject_state(lambda x:x['autonomous_training_v1']['downstream_reservations_consumed'].update({m.AUTH['sha256']:{'job_id':m.JOB}}))
 def test_09_wrong_owner(self):self.reject_state(lambda x:x['autonomous_training_v1'].update(owner_id='replacement'))
 def test_10_wrong_controller(self):self.reject_state(lambda x:x['autonomous_training_v1'].update(controller_job_id='999'))
 def test_11_root_hold(self):self.reject_state(lambda x:x['autonomous_training_v1'].update(root_submission_hold={'reason':'hold'}))
 def test_12_already_registered(self):self.reject_state(lambda x:x['registered_jobs'].append(copy.deepcopy(ctx['job'])))
 def test_13_historical_identity_drift(self):self.reject_state(lambda x:x['registered_jobs'][0].update(name='tampered'))
 def test_14_new_missing_accounting(self):self.reject_snap(lambda x:x['rows'].pop(m.JOB))
 def test_15_CPU_missing_accounting(self):self.reject_snap(lambda x:x['rows'].pop('3034538'))
 def test_16_wrong_queue_token(self):self.reject_snap(lambda x:x['queue'][m.JOB].update(comment='foreign'))
 def test_17_unknown_status(self):self.reject_snap(lambda x:x['rows'][m.JOB].update(status='UNKNOWN'))
 def test_18_wrong_new_GPU(self):self.reject_snap(lambda x:x['rows'][m.JOB].update(gpus=0))
 def test_19_wrong_new_node(self):self.reject_snap(lambda x:x['rows'][m.JOB].update(node='gpu4020'))
 def test_20_controller_not_CPU(self):self.reject_snap(lambda x:x['rows']['3034538'].update(gpus=1))
 def test_21_actual_owner_lease(self):
  own,ev=m.lease_evidence(ctx['g']);self.assertEqual(own,owner);self.assertTrue(ev['exclusive_lock_confirmed_contended'])
 def test_22_failed_original_ack_rejected(self):
  with self.assertRaises(ValueError):ctx['g'].parse_ack(type('A',(),{'returncode':1,'stdout':'3043709\n'})(),set())
 def test_23_original_CAS_refuses_stale_sha(self):
  p=D/'CAS_fixture.json';p.write_bytes(b'{"fixture":true}\n');before=p.read_bytes()
  with self.assertRaises(ValueError):ctx['c'].atomic_json(p,{'would_change':True},'0'*64)
  self.assertEqual(p.read_bytes(),before)
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
with (D/'CPU_test_result.json').open('x') as f:json.dump({'kind':'bounded_reconciliation_CPU_checks','tests_run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'all_passed':r.wasSuccessful(),'real_readonly_context':['exact production pending/source/ack validation','owner identity and held lease probe'],'synthetic_boundary':'Scheduler snapshot test cases are derived from original preflight plus a synthetic known-job row; they are not new Slurm or GPU evidence.','production_state_writes':0,'Slurm_calls':0,'GPU_calls':0},f,indent=2)
sys.exit(0 if r.wasSuccessful() else 1)
