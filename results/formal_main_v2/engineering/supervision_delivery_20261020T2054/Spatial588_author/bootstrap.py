from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).resolve().parent
VERSION='formal-spatial588-predispatch-history-v1'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rawrecord(p):
 a=p.stat();b=p.read_bytes();c=p.stat();assert (a.st_size,a.st_mtime_ns,a.st_ino)==(c.st_size,c.st_mtime_ns,c.st_ino)
 return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,d):
 p=D/n
 with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return {'path':p.relative_to(R).as_posix(),'sha256':digest(p)}
state=json.loads((R/'results/experiment_supervisor/state.json').read_text());jobs=[j for j in state['registered_jobs'] if j['job_id'] in ['3022743','3042529']];assert len(jobs)==2
jobs.sort(key=lambda j:int(j['job_id']))
output='results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01'
rawpaths=['results/formal_main_v2/job_receipts/3042529.json','results/slurm/cti-formal-downstream_3042529.out','results/slurm/cti-formal-downstream_3042529.err']
rows={}
for n in rawpaths:
 a=rawrecord(P/n);b=rawrecord(R/n);assert a==b;rows[n]={'runtime':str(P/n),'control':str(R/n),**a}
q=subprocess.run(['sacct','-X','-n','-P','-j','3022743,3042529','--format=JobIDRaw,State,ExitCode,ElapsedRaw,AllocTRES,NodeList'],text=True,capture_output=True);assert q.returncode==0
parsed={}
for line in q.stdout.splitlines():
 if not line.strip():continue
 jid,status,exitcode,secs,allocation,node=line.split('|')[:6];parsed[jid]={'status':status,'exit_code':exitcode,'elapsed_seconds':int(secs),'allocation':allocation,'node':node}
assert set(parsed)=={'3022743','3042529'}
for j in jobs:
 assert all(j[k]==v for k,v in parsed[j['job_id']].items())
assert parsed['3022743']['status']=='COMPLETED' and parsed['3022743']['exit_code']=='0:0' and parsed['3022743']['elapsed_seconds']==393
assert parsed['3042529']['status']=='FAILED' and parsed['3042529']['exit_code']=='1:0' and parsed['3042529']['elapsed_seconds']==2
absence=[]
for folder,pattern in [(P/'results/formal_main_v2/adapter_invocations','3042529_*'),(P/output/'adapter_invocations','3042529_*'),(P/'results/formal_main_v2/action_execution_invocations/3042529','*'),(P/output/'action_execution/3042529','*')]:
 assert not list(folder.glob(pattern));absence.append({'directory':str(folder),'pattern':pattern,'matching_files':[]})
for n,row in rows.items():assert rawrecord(P/n)==rawrecord(R/n)=={k:row[k] for k in ['sha256','bytes']}
snap=put('raw_failure_snapshot.json',{'schema':'formal_main_v2','kind':'formal_predispatch_failure_raw_snapshot','version':VERSION,'status':'author_verified_snapshot_not_root_acceptance','utc':datetime.now(timezone.utc).isoformat(),'job_id':'3042529','jobs':jobs,'accounting':parsed,'raw_sacct':q.stdout,'raw_files':rows,'absence':absence,'weights_copied':False,'sealed_values_read':False,'new_GPU_submissions':0,'new_scientific_trials':0,'ordinary_root_review_fabricated':False})
anchors=[
 'results/formal_main_v2/preflight/heartbeat_20261021T0349/Spatial_pre_dispatch_failure_admission_audit.json',
 'results/formal_main_v2/preflight/heartbeat_20261019T2318/Spatial_dependency_repair.json',
 'results/formal_main_v2/downstream_reviews/3022743.json',
 *rawpaths,
 'results/formal_main_v2/downstream_gateway/55f6c06a83847f8f60850309cdade6991cc70ba3e83451f086632c3d76504cd6/sbatch_result.json',
 *[j['invocation'] for j in jobs],
 'results/formal_main_v2/execution/libero_spatial_development_first_pair_v1.json',
 snap['path']]
prior=json.loads((R/anchors[2]).read_text());anchors += [prior['pull_receipt'],str(Path(prior['pull_receipt']).parent/'inventory_before.json'),str(Path(prior['pull_receipt']).parent/'inventory_after.json')]
repair=json.loads((R/anchors[1]).read_text());anchors.append(repair['independent_diagnosis']['path'])
for key in ['scientific_plan','runtime_readiness','action_execution_contract']:
 anchors.append(jobs[1][key]['path'])
anchors += [output+'/'+n for n in ['config.json','panel.json']]
sourcepaths=['scripts/ops/formal_downstream_supervisor.py','scripts/review_formal_downstream.py','scripts/formal_execution_manifests.py','scripts/ops/formal_action_deployment_v1/reviewer.py','scripts/ops/formal_action_deployment_v1/consumer.py','scripts/ops/formal_action_deployment_v1/contract.py','scripts/ops/formal_action_deployment_v1/wrapper.py','scripts/server/run_formal_downstream.py']
policy={'schema':'formal_main_v2','kind':'exact_predispatch_history_policy','version':VERSION,'suite':'libero_spatial','stage':'development','stage_key':jobs[0]['stage_key'],'run_root':jobs[0]['run_root'],'output_relative':output,'method_ids':jobs[0]['method_ids'],'prior_jobs':jobs,'source_sha256':jobs[0]['source_sha256'],'adapter_sha256':jobs[0]['adapter_sha256'],'manifest':{'path':'results/formal_main_v2/execution/libero_spatial_development_first_pair_v1.json','sha256':jobs[0]['execution_manifest_sha256']},'prefix_review':{'path':'results/formal_main_v2/downstream_reviews/3022743.json','sha256':digest(R/'results/formal_main_v2/downstream_reviews/3022743.json')},'prefix_ledger':{'path':output+'/trials.jsonl',**rawrecord(R/output/'trials.jsonl')},'prefix_report':{'path':output+'/closed_loop_report.json',**rawrecord(R/output/'closed_loop_report.json')},'raw_failure_snapshot':snap,'anchors':{n:digest(R/n) for n in sorted(set(anchors))},'original_sources':{n:digest(R/n) for n in sourcepaths},'all_prior_job_ids':['3022743','3042529'],'executed_prior_job_ids':['3022743'],'predispatch_failed_job_ids':['3042529'],'prefix_completed_trials':12,'remaining_trials':588,'expected_trials':600,'retained_prior_GPU_seconds':395,'retained_failure_GPU_seconds':2,'science_changes':False,'new_GPU_submissions':0}
print(json.dumps(put('policy.json',policy)))
