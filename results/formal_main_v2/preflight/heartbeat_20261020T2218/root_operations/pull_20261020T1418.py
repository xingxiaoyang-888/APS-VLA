from pathlib import Path
import hashlib,importlib.util,json,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def write(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_terminal20261020T1418_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';ss=sha(sp);s=json.loads(sp.read_text())
 pull=mod('scripts/pull_formal_results.py','b1b141ddb75fd8641d6f5e7f68dbfea462e1fe907ced2f2a98338a1145d77061','root_terminal20261020T1418_puller')
 jobs=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('status') in pull.TERMINAL]
 init=json.loads((R/B/'initial_observation.json').read_bytes());assert sha(R/B/'initial_observation.json')=='cf139e4279216a82e81eddeafe7430c2794a94f1643bb3466b64ec5c8d285f76'
 for jid in ['3049132','3049172','3049622','3049632','3049657','3049679']:
  observed=init['observation']['rows'][jid];assert observed['status']=='COMPLETED' and observed['exit_code']=='0:0' and observed['gpus']==1
  job=next(j for j in jobs if str(j['job_id'])==jid)
  assert job['status']=='COMPLETED' and job['exit_code']=='0:0' and job['elapsed_seconds']==observed['elapsed_seconds']
 report,path=pull.pull(['3049132','3049172','3049622','3049632','3049657','3049679'],timeout=300)
 assert report['status']=='verified_nonweight_snapshot' and not report['missing']
 jr=write(B+'/terminal_jobs_snapshot.json',{'schema':'formal_main_v2','kind':'immutable_terminal_formal_job_snapshot','utc':datetime.now(timezone.utc).isoformat(),'source_state_sha256':ss,'registered_jobs':jobs})
 pr=ref(path)
 output=write(B+'/terminal_pull.json',{'pull':pr,'terminal_jobs_snapshot':jr,'files':len(report['files']),'weights_copied':False,'state_unchanged':sha(sp)==ss})
 assert sha(sp)==ss
 print(json.dumps({'pull':pr,'terminal_jobs_snapshot':jr,'output':output,'files':len(report['files'])}),flush=True)
