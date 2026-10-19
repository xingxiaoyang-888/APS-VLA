from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import sys,os,json,hashlib,importlib.util,copy,time,contextlib,io,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/action_actual_plan_independent_0943';A=R/'.local/action_actual_plan_0943'
sys.dont_write_bytecode=True
read_paths=set()
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('Independent planner forbids process/network')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   if 'sealed' in str(p).lower() or p.suffix.lower() in {'.pt','.pth','.safetensors','.ckpt','.bin','.pkl','.pickle','.pruned_init','.init'}:raise RuntimeError('Independent planner forbids weight/sealed payload: '+str(p))
   writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
   if writing and D not in p.parents:raise RuntimeError('Independent planner write outside audit: '+str(p))
   if not writing and str(p).startswith(str(R)):read_paths.add(str(p))
sys.addaudithook(guard)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
plan_path=A/'scientific_plan.json';assert sha(plan_path)=='43a521e2b1c5b7f8ceff442ce655dde5cae73dfde0f9f7598f65fa57446b4a94'
expected=json.loads(plan_path.read_bytes());arguments=json.loads((A/'plan_arguments.json').read_bytes());state=json.loads((A/'state_at_planning.json').read_bytes())
assert arguments['stage']=='development' and arguments['resume'] is True and arguments['stop_after'] is None
assert arguments['freeze_directory'] is None and arguments['collection_review'] is None and arguments['profile_panel'] is None
path=R/'scripts/ops/formal_downstream_supervisor.py';assert sha(path)=='f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571'
spec=importlib.util.spec_from_file_location('independent_actual_scientific_planner_0943',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
start=time.monotonic();capture=io.StringIO();report={'schema':'formal_main_v2','kind':'independent_actual_original_scientific_plan_reconstruction','started_utc':datetime.now(timezone.utc).isoformat(),'original_planner':{'path':str(path.relative_to(R)),'sha256':sha(path)},'scientific_plan':{'path':str(plan_path.relative_to(R)),'sha256':sha(plan_path)},'arguments_ref':{'path':str((A/'plan_arguments.json').relative_to(R)),'sha256':sha(A/'plan_arguments.json')},'state_snapshot_ref':{'path':str((A/'state_at_planning.json').relative_to(R)),'sha256':sha(A/'state_at_planning.json')},'synthetic_inputs':False,'models_loaded':False,'state_written':False,'GPU_jobs_submitted':0,'final_values_read':False}
try:
 with contextlib.redirect_stdout(capture),contextlib.redirect_stderr(capture):actual=m.plan(SimpleNamespace(**arguments),copy.deepcopy(state),project=R)
 assert actual==expected,'Original real planner result differs from frozen author plan'
 checks=[]
 for rel,expected_sha in actual['invocation']['root_evidence_sha256'].items():
  observed=sha(R/rel);assert observed==expected_sha,rel;checks.append({'path':rel,'sha256':observed})
 for absolute,expected_sha in actual['invocation']['watched_files'].items():
  observed=sha(Path(absolute));assert observed==expected_sha,absolute;checks.append({'path':absolute,'sha256':observed})
 assert not (R/actual['invocation_relative']).exists(),'Invocation already published in R'
 assert not (Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')/actual['invocation_relative']).exists(),'Invocation already published in P'
 report.update(status='passed_readonly_reconstruction',actual_plan_sha256=actual['plan_sha256'],full_plan_equal=True,evidence_rehashed=checks,method_ids=actual['invocation']['method_ids'],prior_job_ids=actual['invocation']['prior_job_ids'],expected_total_trials=600,original_terminal_trials=12,remaining_trial_ids=588,old_prefix_equivalence_claimed=False,authorized_scope=['development'])
except BaseException as exc:
 report.update(status='failed_readonly_reconstruction',error_type=type(exc).__name__,error=str(exc),trace=traceback.format_exc())
report['seconds']=time.monotonic()-start
report['read_paths_sha256']=[{'path':p,'sha256':sha(Path(p))} for p in sorted(list(read_paths)) if Path(p).is_file() and str(D) not in p]
(D/'actual_original_plan_reconstruction.log').write_text(capture.getvalue())
raw=(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode();out=D/'actual_original_plan_reconstruction.json';out.write_bytes(raw)
print(json.dumps({'status':report['status'],'seconds':report['seconds'],'evidence_rehashed_count':len(report.get('evidence_rehashed',[])),'read_ref_count':len(report['read_paths_sha256']),'sha256':hashlib.sha256(raw).hexdigest(),'error':report.get('error')},ensure_ascii=False))
if report['status']!='passed_readonly_reconstruction':raise SystemExit(1)
