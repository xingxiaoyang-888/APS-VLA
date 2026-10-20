from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,sys,json,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0833'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('object0033identity',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';before=h(statepath);s=c.read_json(statepath);ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0
 rows=[j for j in s['registered_jobs'] if str(j['job_id'])=='3044017'];assert len(rows)==1;j=rows[0]
 authsha='0f8c1eab2e196c544bbf1302d440085abf052bc0bbc32a6dc3d9377bcdb0aec0'
 assert j['segment_end']==500 and j['startup_recovery']['authorization']['sha256']==authsha
 assert ctl['cuda_recovery_reservations_consumed'][authsha]['job_id']=='3044017'
 assert h(R/j['invocation'])==h(P/j['invocation'])==j['invocation_sha256']=='312d66e1932e92111ea6d324709454f6c2e987ebf9a59e7f9cb6933dcf645895'
 result=subprocess.run(['scontrol','show','job','3044017','-o'],capture_output=True,check=True)
 text=result.stdout.decode();fields=dict(x.split('=',1) for x in text.split() if '=' in x)
 assert fields['JobId']=='3044017' and fields['JobName']=='cti-formal'
 assert fields['Comment']=='cti-cuda-recovery-v1:'+authsha and fields['TimeLimit']=='04:00:00'
 assert fields['Command']==str(P/'scripts/server/formal_asset_main.slurm') and fields['Requeue']=='0'
 assert fields['WorkDir']==str(R) and fields['StdOut']==str(R/'results/slurm/cti-formal_3044017.out') and fields['StdErr']==str(R/'results/slurm/cti-formal_3044017.err')
 assert fields['ExcNodeList']=='gpu4020'
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8
 assert obs['rows']['3044017']['status'] in {'RUNNING','PENDING','CONFIGURING'}
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 rawpath=B/'Object64_3044017_scontrol.txt'
 with rawpath.open('xb') as stream:stream.write(result.stdout)
 receipt=dict(schema='formal_main_v2',status='registered_once_and_actual_scheduler_identity_verified',utc=datetime.now(timezone.utc).isoformat(),job_id='3044017',actual_status=obs['rows']['3044017']['status'],actual_state=fields,invocation=j['invocation'],invocation_sha256=j['invocation_sha256'],actual_sbatch_argv=j['startup_recovery']['actual_sbatch_argv'],root_authorization=j['startup_recovery']['authorization'],GPU_allocation_seconds_at_observation=obs['rows']['3044017']['elapsed_seconds']*obs['rows']['3044017']['gpus'],capacity=cap,scheduler=obs,exact_stdout=dict(path=rawpath.relative_to(R).as_posix(),sha256=h(rawpath)),retained_failed_job_id='3028468',retained_failed_GPU_seconds=69,original_target=500,continuous5000_admission=False,actual_logs_remain_in_R_until_exact_terminal_pull_mirror=True,duplicate_submissions=0)
 p=B/'Object64_3044017_submission_identity.json'
 with p.open('x') as stream:json.dump(receipt,stream,sort_keys=True,indent=2);stream.write('\n')
 assert h(statepath)==before
 print(json.dumps(dict(status=receipt['status'],job_id='3044017',actual_status=receipt['actual_status'],occupied=len(cap['occupied']),receipt=p.relative_to(R).as_posix(),sha256=h(p))))
