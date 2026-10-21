from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261021T1249'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('_storage_design_lock',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
design=R/B/'Goal_remaining5_root_design_decision.json';assert h(design)=='728ba315807e6f17990e548b969d31c1721e5f080fc5de10ef8b530918b492fd'
d=json.loads(design.read_text());keys=[r['pair_key'] for r in d['pairs']]
p_parts=dict(results=200*4*2**20,cleanup=200*65536,trial_start=200*4096,report_old_and_tmp=2*16*2**20,config_panel=16*2**20,adapter_pair=16*2**20,outer=1024*65536,terminal=16*2**20)
r_parts=dict(observations=21032*393288,rng=21032*65536,sim=21032*8192,capture_events=21032*16384,gate_events=68032*16384,logs=8*2**30)
pu=sum(p_parts.values());ru=sum(r_parts.values());pr=pu+134217728;rr=ru+1073741824
assert (pu,ru,pr,rr)==(1003782144,19871439680,1137999872,20945181504)
def free(path):
 s=os.statvfs(path);return dict(path=str(path),free_bytes=s.f_bavail*s.f_frsize,st_dev=path.stat().st_dev,quota_checked=False)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=(R/'results/experiment_supervisor/state.json').read_bytes()
 measured={'P':free(P),'R':free(R)}
 assert measured['P']['free_bytes']>=pr*5 and measured['R']['free_bytes']>=rr*5
 if measured['P']['st_dev']==measured['R']['st_dev']:assert min(x['free_bytes'] for x in measured.values())>=(pr+rr)*5
 rec=dict(schema='formal_main_v2',kind='root_Goal_remaining5_dual_root_storage_design',status='layout_and_budget_design_approved_pending_source_GPU_gate',reviewed_by='root',created_utc=datetime.now(timezone.utc).isoformat(),formula_version='goal-remaining5-dual-root-budget-v1',exact_five_pair_keys=keys,
  design={'path':str(design.relative_to(R)),'sha256':h(design)},per_pair=dict(P_parts=p_parts,R_parts=r_parts,P_upper_bytes=pu,P_margin_bytes=134217728,P_required_bytes=pr,R_upper_bytes=ru,R_margin_bytes=1073741824,R_required_bytes=rr),
  aggregate_P_required_bytes=pr*5,aggregate_R_required_bytes=rr*5,measured_free_bytes=measured,
  roots=[dict(pair_key=k,P_output=str(P/'results/formal_main_v2/execution/goal_remaining5_v1'/k/'attempt01'),R_raw=str(R/'results/formal_main_v2/raw_runtime/goal_remaining5_v1'/k/'attempt01'),R_bootstrap_stdout=str(R/'results/slurm'/('cti-goal-r5-k'+str(row['budget'])+'s'+str(row['seed'])+'_%j.out')),R_bootstrap_stderr=str(R/'results/slurm'/('cti-goal-r5-k'+str(row['budget'])+'s'+str(row['seed'])+'_%j.err'))) for k,row in zip(keys,d['pairs'])],
  layout=dict(P='original_run scientific ledger/config/panel/report and bounded outer metadata only',R='raw five-component observations, observer events/gate logs/passive sim/RNG payload, exclusive runtime.stdout/runtime.stderr; separate scheduler bootstrap logs'),
  no_dedup_credit=True,same_device_requires_sum=True,per_login_and_compute_aggregate_check=True,all_five_budget_conservative_even_if_already_consumed=True,
  raw_claim='exact unique per-pair directory; no symlink, no reuse, no overwrite',explicit_runtime_file_limit_bytes=2*2**30,runtime_file_limit_scope='entry process own direct ordinary file writes after distinct O_EXCL stdout/stderr setup; not Slurm daemon bootstrap',
  bootstrap_log_budget='additional conservative 4 GiB per pair, not a daemon-enforced quota',
  actual_disk_reservation=False,quota_verified=False,space_can_change=True,deletion_or_moving_existing_artifacts=False,
  original_control_loop_numeric_and_action_semantics_unchanged_required=True,source_AST_reverse_projection_and_bounded_serialization_audit_required=True,
  source_runtime_verification_completed=False,independent_complete_storage_source_audit_required=True,GPU_execution_authorized=False,new_GPU_jobs=0,scientific_release=False,original200_HOLD=True,final_release=False,state_sha256=hashlib.sha256(before).hexdigest())
 out=R/B/'Goal_remaining5_storage_root_decision.json'
 with out.open('x') as f:json.dump(rec,f,sort_keys=True,indent=2);f.write('\n')
 assert (R/'results/experiment_supervisor/state.json').read_bytes()==before
 print(json.dumps({'path':str(out.relative_to(R)),'sha256':h(out),'P_required_all5':pr*5,'R_required_all5':rr*5,'measured':measured}))
