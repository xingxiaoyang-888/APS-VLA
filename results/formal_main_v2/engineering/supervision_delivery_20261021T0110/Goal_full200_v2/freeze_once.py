"""One-time private v2 freeze; no production install, state, Git or Slurm access."""
from pathlib import Path
import ast,hashlib,json,tarfile
D=Path(__file__).parent;R=D.parents[1];OLD=R/'.local/goal_full200_author_20261021T0110';K=D/'package'
assert not (D/'delivery_manifest.json').exists()
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p,root=D):
 b=p.read_bytes();return {'path':p.relative_to(root).as_posix(),'sha256':sha(b),'bytes':len(b)}
def write(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
test=json.loads((D/'CPU_consumer_v2/report.json').read_bytes());assert test['status']=='passed_CPU_consumer_v2_with_production_HOLD' and len(test['checks'])==74 and all(x['passed'] for x in test['checks']) and test['rejections']==56 and test['positive_cases']==2
assert sha((K/'consumer.py').read_bytes())=='c12a6a5b99c4e34ff19f535a4725fecd9fcabc70ba1f37dc2c6c32c979ad3c4b'
assert sha((K/'package_manifest.json').read_bytes())=='2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec'
oldmanifest=OLD/'delivery_manifest.json';assert sha(oldmanifest.read_bytes())=='56c590f04b514de9bd3a4dcde0fcba93aa7dafe7f739f651c1ee97a1e99b0f53'
for row in json.loads(oldmanifest.read_bytes())['files']:
 b=(OLD/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
package=json.loads((K/'package_manifest.json').read_bytes());prior=json.loads((OLD/'package/package_manifest.json').read_bytes())
assert len(package['files'])==10 and [p for p in package['files'] if package['files'][p]!=prior['files'][p]]==['scripts/ops/formal_goal_full200_gate_v1/consumer.py']
for p,h in package['files'].items():assert sha((K/Path(p).name).read_bytes())==h
a=ast.parse((OLD/'package/consumer.py').read_bytes());b=ast.parse((K/'consumer.py').read_bytes())
outside=lambda t:[ast.dump(n,include_attributes=False) for n in t.body if not(isinstance(n,ast.FunctionDef) and n.name=='reconstruct_gate')]
assert outside(a)==outside(b)
# Source-only factual inspection of the genuine already-completed 58 record.
oldraw=R/'results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156/attempt01/observer/events.jsonl'
blob=oldraw.read_bytes();events=[json.loads(x) for x in blob.splitlines()]
loaders=[e for e in events if e.get('phase','').startswith('existing_loader_event:')]
names=['existing_loader_event:'+x for x in ('asset_metadata_compat_load_start','asset_metadata_compat_load_complete','deployment_base_load_start','goal_component_load_start','goal_component_load_complete','goal_component_load_start','goal_component_load_complete','deployment_base_load_complete')]
assert [x['phase'] for x in loaders]==names and all(x['ordinal'] is None and x['trial_identity'] is None for x in loaders) and events[:8]==loaders
write(D/'actual_old58_loader_topology.json',{'status':'source_and_archived_actual_record_topology_checked','raw_source':{'path':oldraw.relative_to(R).as_posix(),'sha256':sha(blob),'bytes':len(blob)},'loader_phase_order':names,'all_eight_before_original_first_trial':True,'original_terminal_witnesses':sum(x.get('event')=='trial_end' for x in events),'actual_new_full200_GPU_test':False,'new_scientific_trials':0})
# All CPU outputs, including synthetic binary bytes, are exact per-member tar.
archive_dir=D/'archives';archive_dir.mkdir(exist_ok=False)
source=D/'CPU_consumer_v2';members=[ref(p,source) for p in sorted(source.rglob('*')) if p.is_file()]
assert all(not(p.is_symlink()) for p in source.rglob('*'))
archive=archive_dir/'CPU_consumer_v2.tar.gz'
with tarfile.open(archive,'x:gz') as t:
 for row in members:t.add(source/row['path'],arcname=row['path'],recursive=False)
with tarfile.open(archive,'r:gz') as t:
 for row in members:
  v=t.extractfile(row['path']).read();assert len(v)==row['bytes'] and sha(v)==row['sha256']
memberpath=archive_dir/'CPU_consumer_v2.members.json'
write(memberpath,{'scope':'all exact private CPU fixtures/outputs only; no real model weights','files':members,'file_count':len(members)})
archives=[{'archive':ref(archive),'members':ref(memberpath),'file_count':len(members)}]
install=[{'source':'package/'+Path(p).name,'path':p,'sha256':h,'bytes':(K/Path(p).name).stat().st_size} for p,h in package['files'].items()]
install.append({'source':'package/package_manifest.json','path':'scripts/ops/formal_goal_full200_gate_v1/package_manifest.json','sha256':sha((K/'package_manifest.json').read_bytes()),'bytes':(K/'package_manifest.json').stat().st_size})
write(D/'install_files.json',{'kind':'Goal_full200_v2_exact_install_projection_not_installed','file_count':11,'files':install,'actual_P_installed':False})
prior_refs={n:{'path':str(OLD/n),'sha256':sha((OLD/n).read_bytes()),'bytes':(OLD/n).stat().st_size} for n in ['delivery_manifest.json','author_report.json','package/package_manifest.json','CPU_full200_v3/report.json','CPU_outer_v3/report.json','CPU_consumer_v2/report.json']}
report={'schema':'formal_main_v2','kind':'goal_full200_production_entry_author_candidate','status':'passed_CPU_consumer_v2_candidate_with_production_HOLD','reviewed_by':'author','author_agent':'/root/goal_cpu_gate_2054','package_manifest_sha256':sha((K/'package_manifest.json').read_bytes()),'package_files':package['files'],'config_sha256':package['files']['scripts/ops/formal_goal_full200_gate_v1/config.json'],'CPU_scope_blockers':[],'production_ready':False,'production_admitted':False,'GPU_execution_authorized':False,'production_blockers':['different-agent final v2 source/raw-counterexample review still required','root canonical R/P publication and actual published outer verify/capacity/source readiness still required','separately audited single-ACK held/pending/CAS/release dispatcher and exact root authorization still required','actual compute-node capacity/exclusive RAW claim and the one prospective full200 GPU attempt not performed','complete future actual raw original typed consumer plus different-agent terminal and root adoption required'],'v1_defect':{'independent_report':ref(D/'independent_v1_blocker.json'),'specific_gap':'empty raw arrays on both non-t0 captures could pass v1 consumer; v1 not production admitted','old_frozen_package_unchanged':True,'new_rejection':'all nine observation phases require complete raw five components; all queries reconstruct content; whole ordered capture/trial_end/gate chains and footer raw hash required'},'source_delta':ref(D/'source_delta.json'),'only_changed_production_source':'consumer.py','changed_function':'reconstruct_gate','other_consumer_AST_unchanged':True,'nine_runtime_source_bytes_unchanged':True,'tests':{'v2_actual':{'report':ref(D/'CPU_consumer_v2/report.json'),'checks':74,'rejections':56,'positive_cases':2,'scope':'actual CPU algorithm only, synthetic observations and no production fixture bypass'},'inherited_v1_original_loop':{'checks':86,'report':prior_refs['CPU_full200_v3/report.json'],'repeated_for_v2':False},'inherited_v1_outer_metadata':{'checks':872,'rejections':275,'report':prior_refs['CPU_outer_v3/report.json'],'repeated_for_v2':False},'v1_consumer_retained_not_sufficient':{'checks':22,'rejections':15,'report':prior_refs['CPU_consumer_v2/report.json'],'known_independent_gap_retained':True}},'prior_delivery':prior_refs,'archives':archives,'actual_new_full200_terminal_checked':False,'old200_HOLD':True,'old_cause_identified':False,'old_failure_repaired':False,'new_scientific_trials':0,'GPU_submissions':0,'Slurm_queries':0,'P_changes':0,'state_changes':0,'Git_changes':0,'final_release':False}
write(D/'author_report.json',report)
readme="""# Goal full200 v2 consumer candidate

This private package supersedes the v1 consumer candidate only. The v1 package and all its original CPU results remain unchanged. An independent counterexample found that both non-t0 capture arrays could be empty while stale hashes were accepted. No v1 GPU or scientific admission is implied. The independently recorded counterexample is copied byte for byte here.

Only consumer.py / reconstruct_gate changes. All nine execution source files, the full original100 development states × A/B256seed17 order, checkpoints, original300 control steps plus10 warmup steps, chunk8, 200/60000/7600 bounds, watchdog60 and the fixed storage decision are unchanged. The old200 stays wholly HOLD; prospective new200 cannot establish the cause of the old mismatch.

The v2 consumer requires all five raw components on every observation phase, reconstructs query before/after signatures from actual blob bytes, checks exact trial/capture/trial_end/gate order, binds all100 pairs and each step to original records, verifies the real eight-loader prefix, and binds the complete event journal hash. Raw success=False completed episodes remain ordinary original outcomes. No result is deleted, rewritten or relabeled.

The focused CPU suite passes74 checks, including56 rejection cases and2 positives. Its only explicit in-memory fixture adaptations are CPU labels,3×4×3 synthetic images, and absence of native loader events in the ordinary CPU trace. A second positive uses the exact eight-loader topology with synthetic marker data. Production source still rejects CPU fixtures. All fixture bytes and outputs are archived with exact per-member hashes; there are no model weights. Prior86 original-loop and872 outer checks are inherited, not represented as newly rerun. The prior22 consumer checks remain as evidence of the original coverage gap.

Read author_report.json for exact previous pins, scope and outstanding gates. install_files.json is an11-file canonical path projection, not an installation. package/package_manifest.json binds all10 source files. The native held/pending/CAS/ACK/release dispatcher is a separately audited root task; this runtime does not submit Slurm jobs or mutate state.

Root integration sequence remains: archive both v1 and v2 exact deliveries; obtain different-agent v2 review including the independent counterexample; bind dispatcher to final v2 package/config/full10 source map; publish exact11 files to canonical R and P under approved root procedures; run the published P entry --verify with exact package manifest; independently review actual P source/runtime/capacity evidence and fresh root/independent readiness; then a separate exact root authorization/reservation/held-dispatch may allow one submission. No arbitrary replays are allowed. Actual compute-node storage checks, exclusive claim, full200 execution and raw original terminal consumer have not happened.

Only raw five-component observation blobs may use the explicitly chosen server path:
 /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01
P still holds attempt metadata, control/outer/gate journals and sim/RNG bytes. Root storage decision7542920320810275798d8fa7ebf2cd85d7b8b4f60ead315638a261b6ecef44de is unchanged. Worst-case required R9345375040 bytes and P5157355520 bytes include1 GiB margins each; all record ceilings remain enforced without truncation. Login statvfs cannot establish compute-node permissions or quota. No actual attempt directories were created.

verify_saved.py reads the final delivery and tar members without extraction or mutation. cpu_consumer_v2.py must not be rerun against its existing output directory; a reviewer can make a private, explicitly recorded output-path derivation. All tools are run via the audited server_control_transport_v1 and exact entry SHA. No canonical/P/state/Git/Slurm writes, new trials, or final-release changes are made by this author package.
"""
with (D/'README.md').open('x') as f:f.write(readme)
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and not p.relative_to(D).as_posix().startswith('CPU_consumer_v2/')]
manifest={'schema':'formal_main_v2','kind':'Goal_full200_v2_author_delivery_manifest','source_root':str(D),'status':'frozen_CPU_candidate_not_production_admission','file_count':len(files),'files':files,'archives':archives,'package_manifest_sha256':sha((K/'package_manifest.json').read_bytes()),'previous_frozen_delivery':prior_refs['delivery_manifest.json'],'new_GPU_submissions':0,'new_scientific_trials':0,'old200_HOLD':True,'final_release':False}
write(D/'delivery_manifest.json',manifest)
print(json.dumps({'file_count':len(files),'manifest_sha256':sha((D/'delivery_manifest.json').read_bytes()),'author_report_sha256':sha((D/'author_report.json').read_bytes()),'package_manifest_sha256':manifest['package_manifest_sha256'],'archive_members':len(members)}))
