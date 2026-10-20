from pathlib import Path
import hashlib,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write(chr(10))
 return ref(p)
assert sha(D/'independent_diagnostic.json')=='3b24bceb78d3354bb5084aa8ebeee5c4d8abe2097a610702f2c22d12f6e23413'
review=json.loads((D/'independent_diagnostic.json').read_bytes());assert review['status']=='passed_evidence_audit_engineering_only' and review['scientific_trials_added']==0 and review['original_goal200_HOLD'] and review['new_Goal_science_HOLD'] and not review['exact_historical_action_replay']
transport=[]
for name,rc in [('goal_prefix58_terminal_independent_20261020T1825_v1.jsonl',1),('goal_prefix58_terminal_independent_20261020T1825_v2.jsonl',0)]:
 source=R/'results/formal_main_v2/control_transport'/name;raw=source.read_bytes();events=[json.loads(x) for x in raw.splitlines()];assert events[0]['event']=='control_start' and events[-1]['event']=='control_end' and events[-1]['returncode']==rc and events[-1]['source173_and_entrypoint_unchanged']
 target=D/'closed_transport'/name;target.parent.mkdir(exist_ok=True)
 with target.open('xb') as f:f.write(raw)
 assert target.read_bytes()==source.read_bytes();transport.append(ref(target))
handoff=put(D/'handoff.json',{'status':'passed_evidence_audit_engineering_only','job_id':'3053440','independent_diagnostic':ref(D/'independent_diagnostic.json'),'metadata_check_count':77984,'metadata_report':ref(D/'metadata_checks.json'),'complete_history_recomputation':ref(D/'independent_history_comparison.json'),'existing_allocation_GPU_seconds_count_once':803,'scientific_trials_added':0,'original_goal200_HOLD':True,'new_Goal_science_HOLD':True,'final_release':False,'exact_historical_action_replay':False,'historical_cause_or_fix_established':False,'all58_trial_and940_query_metadata_checked':True,'all2803_passive_blob_archives_and_original_P_hashes_checked':True,'new_GPU_jobs':0,'new_scheduler_queries':0,'production_state_or_Git_modified':False,'failure_preserved':{'path':ref(D/'failure_v1.json'),'explanation':ref(D/'v1_failure_explanation.json'),'diff':ref(D/'audit_v1_to_v2.diff'),'classification':'audit checker assumed all nine nontrial markers were loader events; actual eight loader plus final returned marker correctly preserved, no production or author change'},'closed_transports':transport,'author_delivery_manifest':review['author_delivery_manifest'],'external_sealing_transport':'results/formal_main_v2/control_transport/goal_prefix58_terminal_independent_20261020T1825_seal_v1.jsonl'})
files=[]
for path in sorted(D.rglob('*')):
 if path.is_file():
  assert not path.is_symlink() and path.stat().st_size<100*1024*1024 and path.suffix.lower() not in ('.pt','.pth','.ckpt','.safetensors','.bin','.npy','.npz');files.append({'path':path.relative_to(D).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
manifest=put(D/'delivery_manifest.json',{'schema':'formal_main_v2','kind':'goal_prefix58_terminal_independent_complete_delivery','status':'sealed','source_root':D.relative_to(R).as_posix(),'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'manifest_excludes_itself':True,'handoff':handoff,'original_failed_checker_and_corrected_source_preserved':True,'contains_weights_or_sealed_values':False,'external_sealing_transport_excluded_while_open':True,'new_GPU_jobs':0,'production_state_changes':0})
for row in files:assert sha(D/row['path'])==row['sha256']
print(json.dumps({'manifest':manifest,'handoff':handoff,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files)}))
