from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');S=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e');D=R/'.local/k64_seed23_bridges_independent_20261020T1949'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads(p.read_bytes())
def put(rel,obj):
 p=D/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
 return {'path':str(p.relative_to(R)),'sha256':h(p),'bytes':p.stat().st_size}
assert not (D/'delivery_manifest.json').exists()
inv=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';assert h(inv)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926';frozen=j(inv)['files'];assert len(frozen)==173
for rel,pin in frozen.items():assert h(R/rel)==h(S/rel)==pin,rel
pins={
'attempt04/independent_index.json':'0b7b0e4c04a402582b795c2d1162e6a02875ccb08a5ea813a7afa2e93280a524',
'control_runtime_attempt01/independent_gateway_CPU_review.json':'45a86335a1c3224c47e76e162e90958f2437fd0152fe8ee1edbf710bfb10284a',
'control_runtime_attempt01/spatial/independent_plan_review.json':'340d926916ee0cfce38ee9e3ac28bc6434c8f687df383d0a5e25468885952c48',
'control_runtime_attempt01/object/independent_plan_review.json':'b26fa2675233a2dab196ac2851c28669b53fac6252309ed00e48046242dcf88f',
'helper_audit/signer_independent_review.json':'9613b7ac104f84e6f9ef610273f2c70ea98fc24f52cd82b7c1b8558f37599b65',
'dispatch_mock/dispatch_independent_review.json':'88ee27059cd1ae2571ca347c3bf9f4427e74067048795081931eae502951d639',
'post_readiness/post_readiness_index.json':'a8f08a7a3ec0f77d3fc594cbc394ee6a9179777ec621f932bffd654840c62397',
'post_readiness/Spatial/post_readiness_independent.json':'31ef1a9894d37d9a07d99351fc07121d0397fedcc6d7e119ae3df8f66bfcb8de',
'post_readiness/Object/post_readiness_independent.json':'714a5e5468e3366b548617b7fb8f58638830b25aff75062f16c1f560994b9719'}
for rel,pin in pins.items():
 assert h(D/rel)==pin,rel
 r=j(D/rel);assert str(r['status']).startswith('passed') and r.get('blockers',[])==[],rel
transports=[
('k64_source_independent_20261020T1949_v2.jsonl','ffa679e7c224613c96252738030758c9711c9a2a1d27bf88c665067457490c9f',1),
('k64_source_independent_20261020T1949_v3.jsonl','4dcd254a0f78da663057e9508cf914dbbf5a457b09342c638b8b3548b0ccbb6a',1),
('k64_source_independent_20261020T1949_v4_correct_pin.jsonl','2295aa4f3ee71918bf1db90b9556bbcdee6505d912b1041cde9ff39b7c59b6ae',0),
('k64_control_runtime_independent_20261020T1949_v2.jsonl','a6a5bd83a0092b6cec6289ab6efec49c119fcd4c4a8fe50ef90ee5f48acdfdf1',0),
('k64_signer_independent_20261020T1949_v1.jsonl','c75b574119b367bf56ee74249e635c81d444e11d3792d4adadf6d1088e3632c4',0),
('k64_dispatch_independent_20261020T1949_v1.jsonl','87553cc9925497eb23466be6a4c3b0d611c60674d4e2a108baf3418d61f7e5cc',0),
('k64_post_readiness_independent_20261020T1949_v1.jsonl','399c96f25c3a7f69f9a37e07b1164944f397d0d669ad9f8c63184db2c72d3c6f',0)]
tr=[]
for name,pin,rc in transports:
 p=R/'results/formal_main_v2/control_transport'/name;assert h(p)==pin
 rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()];last=rows[-1];assert last['event']=='control_end' and last['returncode']==rc and last['source173_and_entrypoint_unchanged'] is True,last
 q=D/'transport'/name;q.parent.mkdir(exist_ok=True)
 with q.open('xb') as f:f.write(p.read_bytes())
 tr.append({'source':str(p.relative_to(R)),'copy':str(q.relative_to(R)),'sha256':pin,'returncode':rc})
put('transport/copied_transport_provenance.json',tr)
put('preserved_failures_and_limitations.json',{'schema':'formal_main_v2','harness_failures':[{'attempt':'v2','reason':'Independent harness expected source_index; actual canonical development schema uses source_state_index. Corrected harness only; original rejection retained.'},{'attempt':'v3','reason':'Raw nested code object equality differs because derived source shifts line metadata. Corrected to recursive semantic code and original complete Gateway AST comparisons, no lifecycle waiver.'}], 'pre_entry_transport_rejection':{'supplied_sha256':'b6d87fd750e30ccbf99f341893000343235e5ceebebfaf7c7f0e9cb6888207ed48','correct_sha256':'b6d87fd750e30ccbf99f341893000343235e5ceebfaf7c7f0e9cb6888207ed48','error':'ValueError: entrypoint SHA differs','entrypoint_executed':False,'audit_transport_file_created':False},'unexecuted_harness_revisions':['audit_bridges_v1.py','audit_control_runtime_v1.py'],'candidate_source_modified_by_auditor':False,'all_original_attempts_retained':True,'scheduler_snapshot_is_inherited':True,'production_post_readiness_state_claim_is_at_recorded_snapshot_only':True,'real_submission_or_reconciliation_not_audited_in_this_package':True,'actual_GPU_runtime_chain_verified':False,'official_base_weight_bytes_rehashed':False,'selected_checkpoint_bytes_hashed_only':4,'checkpoint_deserialized_or_copied':False})
hand=put('handoff.json',{'schema':'formal_main_v2','kind':'k64_seed23_bridges_control_readiness_independent_delivery','status':'passed_CPU_and_actual_metadata_post_review','reviewed_by':'independent','scope':['libero_spatial_k64_seed23','libero_object_k64_seed23'],'pair_development_trials':200,'total_planned_scientific_trials':400,'scientific_trials_added':0,'reports':{rel:{'path':str((D/rel).relative_to(R)),'sha256':pin} for rel,pin in pins.items()},'checks':{'source':10003,'control_runtime':1653,'signer':27,'dispatch_mock':39,'actual_post_readiness':480},'negative_cases':{'source':128,'control_runtime':37,'signer':37,'dispatch_mock_transaction_cases':9,'dispatch_mock_reentry_rejections':4},'actual_full_P_wrapper_verifications':2,'selected_checkpoint_files_hashed':4,'actual_GPU_runtime_chain_verified':False,'new_GPU_runs':0,'production_state_writes':False,'Git_writes':False,'scientific_settings_or_selection_changed':False,'final_values_read':False,'final_enabled':False,'original_Goal_HOLD_unchanged':True,'original_failed_allocations_and_costs_preserved':True,'frozen_173_R_and_S_unchanged':True,'blockers':[],'scope_limit':'Exact existing source histories and CPU runtime metadata only. Root must reconcile current Slurm and unique submissions; no actual submission evidence is claimed here.','created_utc':datetime.now(timezone.utc).isoformat()})
files=[]
for p in sorted(D.rglob('*')):
 assert not p.is_symlink(),str(p)
 if not p.is_file():continue
 assert p.suffix.lower() not in {'.pt','.pth','.safetensors','.ckpt','.bin','.pyc'},str(p)
 assert p.stat().st_size<100*1024*1024,str(p)
 files.append({'path':str(p.relative_to(R)),'sha256':h(p),'bytes':p.stat().st_size})
manifest={'schema':'formal_main_v2','kind':'independent_delivery_manifest','status':'sealed','source_prefix':str(D.relative_to(R)),'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'files':files,'handoff':hand,'manifest_self_excluded':True,'external_in_progress_seal_transport':'results/formal_main_v2/control_transport/k64_independent_delivery_seal_20261020T1949_v1.jsonl','external_seal_transport_must_be_archived_only_after_control_end':True,'no_weights_or_final_values':True,'created_utc':datetime.now(timezone.utc).isoformat()}
ref=put('delivery_manifest.json',manifest)
print(json.dumps({'manifest':ref,'handoff':hand,'file_count':len(files),'total_bytes':manifest['total_bytes']}))
