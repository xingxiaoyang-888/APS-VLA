"""Read-only scheduler/storage capability check inside one registered CPU Slurm job."""
import hashlib,json,os,pathlib,subprocess,datetime,socket
R=pathlib.Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=pathlib.Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
B=R/'results/formal_main_v2/engineering/autonomous_control_cpu_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((B/'registration.json').read_text())
assert os.environ.get('SLURM_JOB_ID') and sha(pathlib.Path(__file__))==reg['probe_sha256']
assert not (B/'result.json').exists()
results=[]
def command(argv):
 env={k:v for k,v in os.environ.items() if not k.startswith('SBATCH_')}
 r=subprocess.run(argv,capture_output=True,text=True,timeout=90,env=env)
 row={'command':argv,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 results.append(row);return r
errors=[]
inventory=json.loads((R/reg['inventory_path']).read_text())
for root in [R,S]:
 for rel,digest in inventory['files'].items():
  if sha(root/rel)!=digest:errors.append('frozen input drift: '+str(root/rel))
r=command(['sacct','-n','-P','-X','--jobs',','.join(reg['job_ids']),'--format=JobIDRaw,State,ExitCode,ElapsedRaw,AllocTRES'])
if r.returncode:errors.append('accounting query failed')
observed={line.split('|')[0] for line in r.stdout.splitlines() if line}
missing=sorted(set(reg['job_ids'])-observed)
if missing:errors.append('registered job accounting missing')
r=command(['squeue','-h','-j',','.join(reg['active_job_ids']),'-o','%i|%T|%j'])
if r.returncode:errors.append('registered active-job queue query failed')
r=command(['sbatch','--test-only','--parsable','--account=p_p15016','--qos=cpu-500_core-l40-8_card-a800-8_card','--partition=L40','--nodes=1','--ntasks=1','--cpus-per-task=7','--gres=gpu:l40:1','--mem=64G','--time=48:00:00','--exclude=gpu4020','--wrap=/bin/true'])
if r.returncode:errors.append('GPU48h scheduler test-only failed')
payload={'schema':'formal_main_v2','kind':'autonomous_scheduler_CPU_capability_probe','status':'passed' if not errors else 'failed','job_id':os.environ['SLURM_JOB_ID'],'node':socket.gethostname(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'probe_sha256':sha(pathlib.Path(__file__)),'registration_sha256':sha(B/'registration.json'),'frozen_files_per_root':len(inventory['files']),'commands':results,'missing_registered_jobs':missing,'errors':errors,'GPU_jobs_submitted':0,'GPU_seconds':0,'model_calls':0,'sealed_state_reads':0}
with (B/'result.json').open('x') as f:json.dump(payload,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in payload.items() if k!='commands'}),flush=True)
raise SystemExit(bool(errors))
