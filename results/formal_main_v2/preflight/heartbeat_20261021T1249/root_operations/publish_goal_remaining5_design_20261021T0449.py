from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T1249';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0449'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load():
 p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
 sp=importlib.util.spec_from_file_location('_designlock',p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
def rd(rel,pin):assert h(R/rel)==pin;return json.loads((R/rel).read_bytes())
def ref(rel):p=R/rel;return dict(path=rel,sha256=h(p),bytes=p.stat().st_size)
def write(rel,obj):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(obj,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
design_rel='results/formal_main_v2/engineering/supervision_delivery_20261021T0334/Goal_remaining5_design/design.json'
design=rd(design_rel,'5c813e3a6e9429cc46ed9ab52a5543d0cf6302c5e5c1819efd11a501a2fb4e8e')
ind_rel='.local/goal_remaining5_independent_20261021T0449/identity_baseline.json'
ind=rd(ind_rel,'03e0c271f04ca728eece824926c3c9650dcb793d3bc24952070cb7e35a445a5b')
assert ind['status']=='passed_readonly_identity_baseline_production_HOLD' and ind['check_count']==1172 and not ind['GPU_execution_authorized']
accepted_rel='results/formal_main_v2/preflight/heartbeat_20261021T1134/Goal3054717_root_acceptance.json'
acc=rd(accepted_rel,'24adf17380a37cce4c65172dc7d806c2574166b8d29281768708e21d36d73ae3')
assert acc['current_trials']==200 and acc['old200_retained_HOLD']
pairs=[{k:p[k] for k in ('pair_key','pair_id','budget','seed','method_ids')} for p in design['remaining_pairs']]
assert len(pairs)==5 and sum(x['trials'] for x in ind['pairs'])==1000
c=load()
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state_before=(R/'results/experiment_supervisor/state.json').read_bytes()
 dst=R/E/'Goal_identity_baseline/identity_baseline_original.json';dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write((R/ind_rel).read_bytes())
 assert h(dst)=='03e0c271f04ca728eece824926c3c9650dcb793d3bc24952070cb7e35a445a5b'
 proof=write(E+'/Goal_identity_baseline/source_map.json',dict(original=ref(ind_rel),published=ref(str(dst.relative_to(R))),byte_identical=True))
 result=write(B+'/Goal_remaining5_root_design_decision.json',dict(schema='formal_main_v2',kind='root_Goal_remaining5_fixed_design',status='fixed_five_design_adopted_runtime_and_GPU_HOLD',reviewed_by='root',created_utc=datetime.now(timezone.utc).isoformat(),design=ref(design_rel),independent_identity_baseline=ref(str(dst.relative_to(R))),previous_full200_acceptance=ref(accepted_rel),pairs=pairs,maximum_trials_per_pair=200,unique_development_states_per_pair=100,maximum_total_trials=1000,maximum_attempts_per_pair=1,maximum_control_steps_per_pair=60000,maximum_queries_per_pair=7600,runtime_seed=17,environment_seed=0,wait_steps=10,action_chunk=8,max_control_steps=300,fixed_panel=design['common']['development_panel'],selected_checkpoint_identity_not_changed=True,full_original_consumer_required=True,new_entry_AST_and_input_gate_and_CPU_independent_required=True,actual_P_verification_required=True,aggregate_storage_and_exact_ACK_admission_required=True,automatic_retry=False,GPU_execution_authorized=False,new_submissions=0,original200_HOLD=True,final_release=False,scientific_results_added=0,state_sha256=hashlib.sha256(state_before).hexdigest()))
 assert (R/'results/experiment_supervisor/state.json').read_bytes()==state_before
 print(json.dumps(result))
