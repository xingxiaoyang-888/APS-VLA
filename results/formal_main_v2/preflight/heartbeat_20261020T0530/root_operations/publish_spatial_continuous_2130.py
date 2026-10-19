from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0530'
C='scripts/ops/formal_spatial_cuda_continuous_admission_v1'
E='results/formal_main_v2/engineering/supervision_delivery_2130'
AUTHOR=E+'/spatial_continuous_author'
AR='configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v1.json'
PINS={'admission.py':'0e5d2bbdca27640c4784393b3ea6a17969a7c6235bdeeb10b61c4a8ab7546b74','gateway.py':'71af9cf0bce935d00934db8c8198f7f9624fd7194f570e36efd95f77da0634c6'}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()+b'\n'
def write(rel,raw):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
 return dict(path=rel,sha256=h(p))
def save(rel,x):return write(rel,canonical(x))
def load(p,pin,name):
 assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
parser=argparse.ArgumentParser();parser.add_argument('--independent-review',required=True);parser.add_argument('--independent-review-sha256',required=True);args=parser.parse_args()
ip=R/args.independent_review;assert ip.is_relative_to(R/'.local/spatial_continuous_admission_independent_2130') and h(ip)==args.independent_review_sha256
ind=json.loads(ip.read_bytes())
assert ind['schema']=='formal_main_v2' and ind['kind']=='spatial_cuda_continuous_admission_independent_CPU_review' and ind['status']=='passed_CPU_review' and ind['blockers']==[]
assert ind['files']=={C+'/'+n:v for n,v in PINS.items()}
assert h(R/AUTHOR/'candidate_review.json')=='83a3961f25020d0f1cce9d1287323fc23d882f27102ba25fa8bba93f4198ec30'
draft=R/AUTHOR/'authorization_a2_draft.json';assert h(draft)=='7d1d972b0b37ce7dabef2bfff93580f6f403eac94c4d85bcf75f96023f667721'
c=load(R/'scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','spatial_root_publish_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';state_sha=h(statepath);state=json.loads(statepath.read_bytes())
 assert state['pending_submission'] is None and not state['formal_main_progress']['test_opened'] and not state['formal_main_progress']['global_release_created']
 assert state['formal_main_progress']['root_and_independent_completed_arms']==48
 for n,pin in PINS.items():
  original=R/AUTHOR/n;assert h(original)==pin;compile(original.read_bytes(),C+'/'+n,'exec');write(C+'/'+n,original.read_bytes())
 ir=write(E+'/spatial_continuous_independent/independent_review.json',ip.read_bytes())
 auth=json.loads(draft.read_bytes());assert auth['status']=='draft_not_authorized' and auth['independent_review'] is None and auth['reviewed_by'] is None
 auth.update(status='approved_exact_once_1500_to5000',reviewed_by='root',reviewed_utc=datetime.now(timezone.utc).isoformat(),independent_review=ir,author_review=dict(path=AUTHOR+'/candidate_review.json',sha256=h(R/AUTHOR/'candidate_review.json')))
 authref=save(AR,auth)
 g=load(R/C/'gateway.py',PINS['gateway.py'],'spatial_root_publish_gateway')
 checked,ev=g.validate_authorization(R,authref);assert checked==auth
 science=g.a.Science(R);plan=science.prepare(state,auth,authref);server=g.a.NativeIO().preflight(plan)
 science.e.unchanged();ev.unchanged()
 d=g.load(R/g.IDENTITY,g.IDENTITY_SHA,'spatial_root_publish_identity')
 snapshot=c.Slurm(timeout=45).observe(state['registered_jobs']);caps=c.capacity(state['registered_jobs'],snapshot,'3034538')
 assert not caps['unknown'] and not caps['findings']
 for row in state['registered_jobs']:
  jid=str(row['job_id']);d.check_observed_identity(row,snapshot['rows'][jid],snapshot['queue'].get(jid),c.TERMINAL)
 owner=g.controller_owner(R,state,snapshot,auth)
 assert len(caps['occupied'])+state['autonomous_training_v1'].get('reserved_GPU_slots',0)==8,'capacity changed; reassess before next action'
 try:g.capacity_gate(c,d,state,snapshot,auth,ev)
 except ValueError as exc:
  assert str(exc)=='no unreserved GPU capacity; never consume Spatial reservation';capacity_error=str(exc)
 else:raise AssertionError('full capacity should block new submission')
 assert h(statepath)==state_sha and not (R/plan['invocation_relative']).exists() and not (g.a.P/plan['invocation_relative']).exists()
 raw_review=save(B+'/Spatial_continuous_root_actual_preflight.json',dict(schema='formal_main_v2',kind='actual_root_metadata_admission',utc=datetime.now(timezone.utc).isoformat(),authorization=authref,original_raw_reconstructed=plan['original_raw_reconstructed'],server_preflight=server,read_evidence_sha256={**science.e.hashes,**ev.hashes},controller_owner=owner,scheduler=snapshot,capacity=caps,capacity_gate_for_submission='blocked_at_eight_slots',capacity_error=capacity_error,state_sha256=state_sha,state_changed=False,invocation_published=False,weights_deserialized=False,new_GPU_submissions=[]))
 receipt=save(B+'/Spatial_continuous_root_admission.json',dict(schema='formal_main_v2',kind='root_spatial_continuous_admission',utc=datetime.now(timezone.utc).isoformat(),status='approved_for_one_future_capacity_checked_submission',authorization=authref,root_actual_preflight=raw_review,author_review=auth['author_review'],independent_review=ir,canonical_sources=auth['gateway_files'],new_GPU_submissions=[],history_preserved=['3024716','3025205','3028522','3043399'],historical_GPU_seconds=11958,completed_before={'A':1500,'B':1500},cursor_before={'A':12000,'B':12000},target_updates_per_arm=5000,normal_validation_schedule_preserved=list(range(0,5001,500)),single_new_attempt=True,automatic_retry=False,invocation_published=False,controller_and_reservations_changed=False,capacity_at_review=len(caps['occupied']),gate_before_actual_submission='full canonical gateway requires a new locked capacity/owner/history/source/raw/resume check; review is not a cached capacity waiver',no_final_release=True))
 readme='# Spatial64 seed23 continuous restoration\n\nRoot approved the exact recovered A/B1500-to5000 continuation after author45 CPU checks, independent review and real original raw/P/S/resume verification. No GPU was submitted during publication because all8 slots were occupied. Configuration: '+AR+'; root receipt: '+receipt['path']+'.\n\nUse only the pinned gateway at a genuine unreserved free slot. It must repeat all registry/owner/lease/history/raw/checkpoint checks. One attempt, no automatic retry, original failed73 GPU seconds retained, original5000 schedule and11 validations unchanged. No final release.\n\nThe author note below is preserved as the earlier prepublication record.\n\n'+(R/AUTHOR/'README.md').read_text()
 write(C+'/README.md',readme.encode())
 write(B+'/root_operations/publish_spatial_continuous_2130.py',Path(__file__).read_bytes())
 print(json.dumps(dict(status='published_and_root_admitted_not_submitted',authorization=authref,root_admission=receipt,occupied=len(caps['occupied']),state_unchanged=True)))
