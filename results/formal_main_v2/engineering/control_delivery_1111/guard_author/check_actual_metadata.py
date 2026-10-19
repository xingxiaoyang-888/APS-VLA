"""Real immutable metadata rejection diagnostics, never a raw successful review."""
from pathlib import Path
import datetime, hashlib, importlib.util, json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/action_mixed_prefix_guard_1111'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('actual_mixed_prefix_precondition',D/'reviewer.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
spec=importlib.util.spec_from_file_location('actual_mixed_prefix_base',R/g.UPSTREAM_REVIEWER)
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
e=b.Evidence(R); g.upstreams(e)
observed=[]
known=[('libero_10','3019954','cde7e784bced622a6a30169af1f3c34ece8b710da8a6d65ab804454457c5d9ba'),
('libero_spatial','3022743','9e14b86a1e556c53ef1cbd8c7bdc1733c3d5eb744f62ffee8df9395645816650'),
('libero_object','3021844','004a810edd7f097bbeec755315beed11bbfa86640a78ffd75ef0ff78a769ee37')]
for suite,jid,checksum in known:
 ref={'path':'results/formal_main_v2/downstream_reviews/'+jid+'.json','sha256':checksum}
 report=e.read_ref(ref)
 try:g._require_current_ancestry(e,b,ref,report,suite=suite)
 except ValueError as exc:
  reason=str(exc)
  if not reason.startswith('Unresolved legacy execution'):raise
 else:raise AssertionError('Known old metadata must not pass')
 observed.append({'suite':suite,'job_id':jid,'root_review':ref,'existing_execution_version':report.get('execution_version',g.OLD_VERSION),
   'scientific_complete_in_original':report.get('scientific_complete'),'completed_trials_in_original':report.get('completed_trials'),
   'check':'metadata_precondition_only_not_raw_reconstruction','outcome':'rejected','reason':reason})
transref={'path':'results/formal_main_v2/execution/action_spatial_resume_0943/transition.json',
 'sha256':'95da28cbfd0968d38e5e92b9468c331b377cccf88ec3bfcdb342b4ce2f1a43a1'}
trans=e.read_ref(transref)
assert trans['from_version']==g.OLD_VERSION and trans['to_version']==g.EXECUTION_VERSION
assert trans['prior_review']==known[1][1].join(['results/formal_main_v2/downstream_reviews/','.json'])
inventory_path='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
inventory=e.read(inventory_path)
assert len(inventory['files'])==173
source=Path(inventory['source_root_server'])
for name,checksum in inventory['files'].items():
 b.relative(name)  # sealed/weight payloads fail before I/O
 assert e.watch(name)==checksum, name
 p=source/name
 assert p.resolve()==p and not p.is_symlink()
 assert digest(p)==checksum, name
pins={}
for name in ['runtime_scope.py','contract.py','entry.py','wrapper.py','gateway.py','reviewer.py','consumer.py']:
 relative='scripts/ops/formal_action_deployment_v1/'+name;pins[relative]=e.watch(relative)
e.unchanged()
value={'schema':'formal_main_v2','kind':'mixed_prefix_actual_metadata_rejection_diagnostic',
 'status':'expected_rejections_verified','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'observations':observed,'planned_transition':transref,
 'future_spatial_result_implication':'If the registered development resume completes, its unchanged preserved legacy prefix remains ineligible for guarded O2A/freeze; this is an ancestry implication, not a completed new result.',
 'frozen_R_and_S_files_verified':173,'source_root_server':str(source),'approved_7_sources':pins,
 'files':dict(sorted(e.files.items())),'script_sha256':digest(Path(__file__)),
 'actual_new_runtime_complete_development_results_audited':0,'actual_O2A_join_verified':False,
 'raw_successful_review_produced':False,'state_read_or_written':False,'GPU_or_Slurm_called':False,
 'sealed_values_read':False,'checkpoint_payloads_read':False,'scientific_trials_replayed':False,
 'activation_written':False,'final_release':False}
(D/'actual_metadata_rejections.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':value['status'],'old_roots':len(observed),'R_S':173,'files':len(e.files),'output_sha256':digest(D/'actual_metadata_rejections.json')},sort_keys=True))
