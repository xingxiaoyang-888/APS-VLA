from pathlib import Path
import ast,hashlib,importlib.util,inspect,json,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_prefix58_independent_20261020T1825/dispatch_v1_blocked';D.mkdir(exist_ok=False)
E=R/'.local/goal_prefix58_dispatch_20261020T1825.py';PIN='1db1f0089d6b267d05cd9bc76aca90b539bdc268ef3e0474f6da5dc77349885c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):
 with (D/n).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write(chr(10))
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
assert sha(E)==PIN
(D/'dispatch_reviewed_copy.py').write_bytes(E.read_bytes())
sp=importlib.util.spec_from_file_location('private_v1_dispatch',E);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
fp=R/'results/formal_main_v2/preflight/heartbeat_20261020T2330/Goal_t0_dispatch/held_identity.json';assert sha(fp)=='b11ab37ac3a9f5b7df4ee7a45e123751731696bebf61b508fd214533f65da7db'
(D/'original_site_held_fixture.json').write_bytes(fp.read_bytes());text=json.loads(fp.read_bytes())['stdout'];old=m.fields(text);new=dict(t.split('=',1) for t in text.split() if '=' in t)
assert old['Partition']=='L40 AllocNode:Sid=logina04:3160037' and new['Partition']=='L40'
assert new['TresPerNode']=='gres:gpu:l40:1'
check=new.copy();check['JobName']=m.NAME;check['Comment']='synthetic-token';caught=None
try:m.actual_identity(check,'3050711','synthetic-token',True)
except RuntimeError as x:caught=str(x)
assert caught=='GPU request differs'
ep=R/'.local/goal_prefix58_repair_20261020T1825/outer_revision03/entry.py';assert sha(ep)=='da3e094a98104d08735d6da6a180b326f79ae077e710880aa9117b39b911e31f'
sp=importlib.util.spec_from_file_location('private_outer_for_bind',ep);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
call=next(n for n in ast.walk(ast.parse(E.read_text())) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='validate_dispatch');assert len(call.args)==5
bind_error=None
try:inspect.signature(e.validate_dispatch).bind(*([None]*5))
except TypeError as x:bind_error=str(x)
assert bind_error and 'reservation_sha' in bind_error
s=json.loads((R/'results/experiment_supervisor/state.json').read_bytes());j=next(v for v in s['registered_jobs'] if str(v['job_id'])=='3049679')
assert j['status']=='COMPLETED' and j['exit_code']=='0:0' and j['elapsed_seconds']==2034
failure=R/'results/formal_main_v2/preflight/heartbeat_20261020T2218/3049679_root_review_failure_20261020T1418.json';assert sha(failure)=='49b226c91f99cd9fd3584ab645992244794f4d720e0128d9ab693e82bcca6793'
put('original_job_facts.json',{'registered_job':j,'root_failure':ref(failure),'meaning':'Slurm success is not scientific acceptance; all200 remain HOLD'})
report={'schema':'formal_main_v2','kind':'independent_Goal_prefix58_dispatch_CPU_review','status':'blocked','entrypoint_sha256':PIN,'blockers':['site parser excludes colon key and contaminates Partition','site GPU TRES uses gres:gpu:l40:1, rejected by v1','validate_dispatch call misses required reservation_sha sixth argument','3049679 scheduler is COMPLETED/0:0; scientific HOLD does not mean Slurm FAILED'],'real_site_fixture':ref(fp),'outer':ref(ep),'source':ref(E),'reproductions':{'old_partition':old['Partition'],'actual_gpu_tres':new['TresPerNode'],'identity_error':caught,'call_bind_error':bind_error},'real_Slurm_operations':0,'real_GPU_execution':False,'canonical_state_changes':0,'main_called':False}
put('independent_review.json',report);print(json.dumps(ref(D/'independent_review.json')))
