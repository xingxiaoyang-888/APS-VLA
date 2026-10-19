from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,importlib.util,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261020T0530'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def save(rel,raw):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('Longstart2130ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statep=R/'results/experiment_supervisor/state.json';before=h(statep);s=json.loads(statep.read_text());assert s['pending_submission'] is None
 js=[j for j in s['registered_jobs'] if str(j['job_id'])=='3043709'];assert len(js)==1;j=js[0]
 inv=json.loads((R/j['invocation']).read_text());assert h(R/j['invocation'])==h(P/j['invocation'])==j['invocation_sha256']=='2bf41d87718038e41f35d52b90506a3e973a7270869278157fb953d8238a7f84'
 assert inv['stage']=='development' and inv['method_ids']==['A128_seed23','B128_seed23'] and inv['version']=='formal-downstream-action-v1'
 run=subprocess.run(['scontrol','show','job','-o','3043709'],capture_output=True,text=True,check=True)
 assert 'JobId=3043709 ' in run.stdout and 'JobName=cti-formal-downstream ' in run.stdout and 'JobState=RUNNING ' in run.stdout and 'Comment=cti-downstream-gateway-v1:6e574361d66aaba7869b536082d9c605106bdaf2ec428f3ccb46ea986c8ef37a ' in run.stdout
 runtime=P/'results/formal_main_v2/action_execution_invocations/3043709'
 ip=runtime/'identity.json';st=ip.stat();raw=ip.read_bytes();assert ip.stat()==st;identity=json.loads(raw)
 assert identity['job_id']=='3043709' and identity['invocation_sha256']==j['invocation_sha256'] and identity['execution_manifest_sha256']==j['execution_manifest_sha256']
 assert identity['scientific_settings_changed'] is False and identity['expected_base_load_calls']==1
 ir=save(B+'/Long3043709_action_identity.json',raw)
 ep=runtime/'events.jsonl'
 with ep.open('rb') as f:raw=f.read(min(ep.stat().st_size,1<<20))
 raw=raw[:raw.rfind(b'\n')+1];events=[json.loads(x) for x in raw.splitlines()]
 assert events and [x['seq'] for x in events]==list(range(len(events))) and all(x['job_id']=='3043709' and x['invocation_sha256']==j['invocation_sha256'] for x in events)
 assert any(x['event']=='legacy_adapter_start' for x in events)
 er=save(B+'/Long3043709_action_events_prefix.jsonl',raw)
 with ep.open('rb') as f:assert f.read(len(raw))==raw
 logs=[]
 for ext in ['out','err']:
  p=P/f'results/slurm/cti-formal-downstream_3043709.{ext}'
  with p.open('rb') as f:data=f.read(min(p.stat().st_size,16384))
  dst=save(B+'/Long3043709_startup_prefix.'+ext,data)
  with p.open('rb') as f:assert f.read(len(data))==data
  logs.append(dict(source=str(p),snapshot=dst,prefix_bytes=len(data),live_prefix=True))
 v=dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),kind='actual_new_action_development_startup_observation',status='registered_GPU_child_and_scientific_adapter_started_not_terminal',job_id='3043709',methods=inv['method_ids'],planned_trials=200,version=inv['version'],source_invocation=ref(j['invocation']),actual_scontrol=run.stdout,identity=ir,event_prefix=er,event_names=[x['event'] for x in events],prefix_events=len(events),logs=logs,pending_resolved_without_resubmission=True,new_sbatch_calls=0,formal_training_complete=48,new_closed_loop_results_accepted=0,complete_runtime_chain_claimed=False,success_rate_claimed=False,final_states_opened=False)
 out=save(B+'/Long3043709_startup_observation.json',(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
 assert h(statep)==before
 print(json.dumps(dict(status=v['status'],receipt=out,events=v['event_names'],state_unchanged=True)))
