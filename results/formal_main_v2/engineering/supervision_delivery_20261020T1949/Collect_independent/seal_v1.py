from pathlib import Path
import sys,hashlib,importlib.util,json
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/collect_terminal_independent_20261020T1949')
p=D/'audit_raw_v1.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='07fe8b598f495d25ed0e0aebc651def88679ae8a794afceeb717a7f6581d339f'
spec=importlib.util.spec_from_file_location('collect_seal_helpers',p);a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
R=a.R;B='results/formal_main_v2/preflight/heartbeat_20261021T0349/collect_terminal/'
a.check(a.digest(R/(B+'completion.json'))=='fd468a87dc1c7c90090d8cc3264e3b42110c39c154c5d19dfb5975be4fa8cbf5','root actual completion pin')
completion=a.read(R/(B+'completion.json'))
a.check(completion['status']=='passed_original_review_and_consumer' and completion['state_unchanged'] is True and completion['new_jobs']==completion['new_scientific_trials']==completion['cost_increment_gpu_seconds']==0 and completion['O2A_or_components'] is False and completion['final_release'] is False,'exact engineering completion boundaries')
refs=[completion[k] for k in ['pull','terminal_jobs_snapshot','root_raw_validation','npz_allowlist']]
refs += [r[k] for r in completion['reviewed'] for k in ['root_review','consumer_reconstruction']]
for ref in refs:a.check(a.digest(R/ref['path'])==ref['sha256'],'root ref:'+ref['path'])
jobs=a.read(R/completion['terminal_jobs_snapshot']['path'])['registered_jobs']
for row in completion['reviewed']:
 root=a.read(R/row['root_review']['path']);a.check(root['registered_jobs_at_review']==jobs,row['job_id']+' original complete immutable jobs')
 proof=a.read(R/row['consumer_reconstruction']['path']);ind=a.read(D/(row['job_id']+'_reconstruction_proof.json'))
 for k in ['canonical_rebuilt_without_time_sha256','actual_runtime_review','cost','evidence_sha256']:a.check(proof[k]==ind[k],row['job_id']+' root independent reconstruction:'+k)
allow=a.read(R/completion['npz_allowlist']['path']);raw={x['relative']:x for x in a.read(D/'P_raw_files.json')['files'] if x['relative'].endswith('.npz')}
a.check(len(raw)==len(allow['files'])==60 and sum(x['bytes'] for x in raw.values())==allow['total_bytes']==23678640,'60 original NPZ total bytes')
a.check(set(x['path'] for x in allow['files'])==set(raw),'exact raw NPZ allowlist')
for f in allow['files']:a.check(f['sha256']==raw[f['path']]['sha256'] and f['bytes']==raw[f['path']]['bytes'],'NPZ exact original:'+f['path'])
AM='.local/collect_terminal_20261020T1949/collect_delivery_manifest.json';a.check(a.digest(R/AM)=='897889f47bc402209b73bda69b09401f4174210cf8dedeb0ec929ae16df8e91a','author sealed manifest')
am=a.read(R/AM)
for f in am['files']:a.check(a.digest(R/f['source'])==f['sha256'] and (R/f['source']).stat().st_size==f['bytes'],'author sealed file:'+f['source'])
transports=[];td=D/'transport';td.mkdir(exist_ok=False)
for tag in ['raw_v1','helper_v1','terminal_v1']:
 rel='results/formal_main_v2/control_transport/collect_terminal_independent_20261020T1949_'+tag+'.jsonl';p=R/rel;b=p.read_bytes();events=[json.loads(x) for x in b.splitlines()]
 a.check(events[-1]['event']=='control_end' and events[-1]['returncode']==0 and events[-1]['source173_and_entrypoint_unchanged'] is True,'closed source-stable transport:'+tag)
 q=td/(tag+'.jsonl');q.write_bytes(b);transports.append(dict(original=a.ref(rel),archived=dict(path=str(q.relative_to(R)),sha256=a.digest(q))))
a.save('completion_crosscheck.json',dict(schema='formal_main_v2',kind='independent_collect_root_completion_crosscheck',status='passed',root_completion=a.ref(B+'completion.json'),author_manifest=a.ref(AM),checks_passed=len(a.checks),checks=a.checks,root_consumer_and_independent_rebuilt_identical=True,exact_original_npz_allowlist=True,original_npz_files=60,original_npz_bytes=23678640,scientific_trials_added=0,cost_increment_gpu_seconds=0,final_release=False))
a.save('handoff.json',dict(schema='formal_main_v2',kind='independent_collect_terminal_delivery_handoff',status='passed',reviewed_by='independent',terminal_index=dict(path=str((D/'terminal_independent_index.json').relative_to(R)),sha256=a.digest(D/'terminal_independent_index.json')),raw_checks=2992,helper_checks=115,helper_negative_cases=28,terminal_checks=1454,root_completion_crosschecks=len(a.checks),job_ids=['3053503','3053518'],observations=60,collection_trajectories=20,gpu_seconds=723,gpu_hours=723/3600,cost_increment_gpu_seconds=0,scientific_success_trials_added=0,latency_samples_added=0,final_release=False,all_current_run_audits_passed=True,all_failures_preserved=True,no_new_GPU_or_Slurm_queries=True,no_production_state_or_Git_writes=True,closed_transports=transports,seal_transport_external='results/formal_main_v2/control_transport/collect_terminal_independent_20261020T1949_seal_v1.jsonl',limitation='Collection panels may support later separately authorized/frozen timing. This delivery contains no O2A/component result and grants no global final release.'))
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():files.append(dict(path=p.relative_to(D).as_posix(),source=p.relative_to(R).as_posix(),sha256=a.digest(p),bytes=p.stat().st_size))
a.save('delivery_manifest.json',dict(schema='formal_main_v2',kind='sealed_independent_collect_terminal_delivery',status='passed',source_root=str(D.relative_to(R)),files=files,file_count=len(files),bytes=sum(f['bytes'] for f in files),production_state_writes=False,new_gpu_submissions=0,scientific_success_trials_added=0,latency_samples_added=0,cost_increment_gpu_seconds=0))
print(json.dumps(dict(manifest_sha256=a.digest(D/'delivery_manifest.json'),handoff_sha256=a.digest(D/'handoff.json'),file_count=len(files),bytes=sum(f['bytes'] for f in files),crosschecks=len(a.checks))))
