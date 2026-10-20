from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2117'
ROWS=[{"group_key":"libero_goal_k128_seed41","job_id":"3049622","root_reconciliation":{"path":"results/formal_main_v2/preflight/heartbeat_20261020T2117/libero_goal_k128_seed41_3049622_pending_reconciliation.json","sha256":"d84b55c63dcc6d23c8b512dc52715f67e6ec1a44edd2421dbed6e10218b70a08"}},{"group_key":"libero_spatial_k256_seed17","job_id":"3049632","root_reconciliation":{"path":"results/formal_main_v2/preflight/heartbeat_20261020T2117/libero_spatial_k256_seed17_3049632_pending_reconciliation.json","sha256":"7afc72d283e7066cbbbed497800091ebf89bc568b8b9d9f8d63fc5cd9577f05e"}},{"group_key":"libero_object_k256_seed17","job_id":"3049657","root_reconciliation":{"path":"results/formal_main_v2/preflight/heartbeat_20261020T2117/libero_object_k256_seed17_3049657_pending_reconciliation.json","sha256":"63a9e96de512e900538211a221c8a4c86deb8234b8ab6c06ff2918ffe1b1dd02"}},{"group_key":"libero_goal_k256_seed17","job_id":"3049679","root_reconciliation":{"path":"results/formal_main_v2/preflight/heartbeat_20261020T2117/libero_goal_k256_seed17_3049679_pending_reconciliation.json","sha256":"9e5ad6809adde79654a86def8248ef19dfd59c2be8dfaa2bc73bfd8051561db8"}}]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def rd(rel,pin=None):
 if pin:assert h(R/rel)==pin
 return json.loads((R/rel).read_bytes())
def check(rr):return rd(rr['path'],rr['sha256'])
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('dispatch1317ctl',p);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd('results/experiment_supervisor/state.json');ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 index=rd(B+'/nonLong_runtime_readiness_root_index.json','25aaaa0ad47031fbc510380cb2b7093ae100c6951bbac9ed9bd43e0b418907d1')
 assert len({r['job_id'] for r in ROWS})==len(ROWS) and len({r['group_key'] for r in ROWS})==len(ROWS)
 entries=[]
 for row in ROWS:
  q=next(x for x in index['shards'] if x['group_key']==row['group_key']);auth=check(q['authorization']);rec=check(row['root_reconciliation'])
  assert rec['status']=='exact_original_ACK_job_reconciled' and rec['job']['job_id']==row['job_id'] and rec['new_submissions']==0
  assert rec['pending_before']['authorization']==q['authorization'] and rec['pending_before']['automatic_retry'] is False
  jobs=[j for j in s['registered_jobs'] if str(j['job_id'])==row['job_id']];assert len(jobs)==1;job=jobs[0]
  assert job['suite']==q['suite'] and job['method_ids']==q['methods'] and job['mode']=='development'
  assert sum(j.get('stage_key')==job['stage_key'] for j in s['registered_jobs'])==1
  ad='results/formal_main_v2/downstream_gateway/'+q['authorization']['sha256'];ack=rd(ad+'/sbatch_result.json')
  assert ack['stdout']==row['job_id']+'\n' and ack['returncode']==0 and ack['stderr']==''
  assert rd(ad+'/committed.json')['root_reconciliation']==row['root_reconciliation']
  assert ctl['downstream_reservations_consumed'][q['authorization']['sha256']]['job_id']==row['job_id']
  assert h(R/job['invocation'])==h(P/job['invocation'])==job['invocation_sha256']==q['prepared_invocation']['sha256']
  entries.append(dict(**row,suite=q['suite'],budget=q['budget'],seed=q['seed'],method_ids=q['methods'],planned_trials=200,
   completed_trials_accepted=0,unique_initial_states_per_suite=100,authorization=q['authorization'],root_acceptance=q['root_check'],
   pre_execution_independent=ref('results/formal_main_v2/engineering/supervision_delivery_1317/nonLong_plan_independent/post_readiness/post_readiness_independent_review.json'),
   invocation=ref(job['invocation']),submission=ref('results/formal_main_v2/submissions/'+row['job_id']+'.json'),
   exact_original_ACK=ref(ad+'/sbatch_result.json'),original_accounting_delay=ref(ad+'/failed_transaction.json'),
   scientific_terminal_acceptance_pending=True,automatic_retry=False,observed_status_at_reconciliation=rec['scheduler']['rows'][row['job_id']]['status']))
 out=B+'/dispatch_root_report.json'
 report=dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),status='all_selected_requests_registered_once',
  submissions=entries,new_GPU_jobs=len(entries),new_planned_trials=len(entries)*200,new_completed_trials=0,
  state_sha256=before,duplicate_stage_keys=False,exact_ACK_reconciliation_no_resubmissions=True,
  pending=None,reserved_GPU_slots=0,final_release=False,scientific_settings_changed=False,
  excluded_other_projects=True,pre_registered_candidate_order=[q['group_key'] for q in index['shards']])
 with (R/out).open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
 with (R/B/'root_operations/dispatch_1317.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 assert h(sp)==before
 print(json.dumps(dict(status=report['status'],receipt=ref(out),jobs=[r['job_id'] for r in entries])))
