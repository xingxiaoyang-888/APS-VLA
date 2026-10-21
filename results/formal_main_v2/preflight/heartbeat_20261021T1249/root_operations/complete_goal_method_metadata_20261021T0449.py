from pathlib import Path
import hashlib,importlib.util,json,sys,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B=R/'results/formal_main_v2/preflight/heartbeat_20261021T1249'
BEFORE='54ee7389fe300b4ec553998d91b9bf727ca3231c2066e35a86716559a3c1406d'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def read(rel,pin):p=R/rel;assert h(p)==pin;return json.loads(p.read_text())
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','_metadata_controller')
pins={
 'scripts/ops/formal_goal_full200_gate_v1/config.json':'29bb0fb84ff2dab826a53d5d8170d7ad0347f193f72ddfedc310f05e2a3d3bae',
 'scripts/ops/formal_goal_full200_gate_v1/specification.json':'ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad',
 'results/formal_main_v2/preflight/heartbeat_20261021T1134/Goal3054717_root_acceptance.json':'24adf17380a37cce4c65172dc7d806c2574166b8d29281768708e21d36d73ae3',
 'results/formal_main_v2/engineering/supervision_delivery_20261021T0334/Goal_independent/independent_terminal_review.json':'9f89cee7420fa4c4185370b22a4c52c70cd536048b9bd366d5e70095a044e223',
 'results/formal_main_v2/engineering/goal_full200_20261021T0110/dispatch_admission.json':'7b6b64397f96175e1184c956766739ab8261bcfa71cd0faef0f7e275e85381a5'}
docs={rel:read(rel,pin) for rel,pin in pins.items()}
methods=['A256_seed17','B256_seed17']
config=docs[next(iter(pins))]
spec=docs['scripts/ops/formal_goal_full200_gate_v1/specification.json']
root=docs['results/formal_main_v2/preflight/heartbeat_20261021T1134/Goal3054717_root_acceptance.json']
ad=docs['results/formal_main_v2/engineering/goal_full200_20261021T0110/dispatch_admission.json']
assert config['method_ids']==ad['method_ids']==methods
assert [v['method_id'] for v in spec['method_identities']]==methods
assert set(root['methods'])==set(methods) and root['current_trials']==200 and root['status']=='accepted_new200_only'
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 p=R/'results/experiment_supervisor/state.json';before=p.read_bytes();assert hashlib.sha256(before).hexdigest()==BEFORE
 state=json.loads(before);new=copy.deepcopy(state)
 matches=[j for j in new['registered_jobs'] if j['job_id']=='3054717'];assert len(matches)==1
 j=matches[0];assert 'method_ids' not in j and j['status']=='COMPLETED' and j['exit_code']=='0:0' and j['elapsed_seconds']==2205
 assert j['mode']=='development' and j['suite']=='libero_goal' and j['visual_tokens']==256 and j['training_seed']==17
 assert j['pair_id']==ad['pair_id']==spec['method_identities'][0]['pair_id']==spec['method_identities'][1]['pair_id']
 assert j['invocation_sha256']=='07a265e02fd283603b1ec4c7e555d75d00318e821c824f02dbf419988987dc5b'
 j['method_ids']=methods
 projection=copy.deepcopy(new);next(x for x in projection['registered_jobs'] if x['job_id']=='3054717').pop('method_ids')
 assert projection==state and state['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0
 beforepath=B/'method_ids_supervisor_snapshot_before.json'
 with beforepath.open('xb') as f:f.write(before)
 proposal=dict(schema='formal_main_v2',kind='root_exact_terminal_job_method_metadata_completion',job_id='3054717',state_before_sha256=BEFORE,only_added_field={'method_ids':methods},source_refs=pins,scientific_results_changed=False,original_registration_without_field_retained=str(beforepath.relative_to(R)),no_Slurm_calls=True,why='Original planner conservatively rejects missing methods as ambiguous overlap; populate only existing terminal job exact methods from original configuration, authorization and accepted raw results.',root_reviewed=True)
 with (B/'method_ids_metadata_proposal.json').open('x') as f:json.dump(proposal,f,sort_keys=True,indent=2);f.write('\n')
 c.atomic_json(p,new,BEFORE)
 proposal.update(status='applied_exact_one_field',state_after_sha256=h(p))
 with (B/'method_ids_metadata_receipt.json').open('x') as f:json.dump(proposal,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps({'state_sha256':h(p),'receipt_sha256':h(B/'method_ids_metadata_receipt.json'),'metadata_only':True}))
