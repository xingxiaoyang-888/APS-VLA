from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;A=R/'.local/goal_full200_dispatch_20261021T0110';C=R/'.local/goal_full200_author_20261021T0110_v2/package/consumer.py'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def write(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
assert sha((A/'delivery_manifest.json').read_bytes())=='d3d9cfca965d9af267c424431ecaa3a465bbf39366c5eac9d3c105c3fd6d0a80'
m=json.loads((A/'delivery_manifest.json').read_bytes())
for x in m['files']:
 b=(A/x['path']).read_bytes();assert len(b)==x['bytes'] and sha(b)==x['sha256']
assert sha((A/'verify_cpu.py').read_bytes())=='fa8ec0ee7270cfdd0d6767120800b946a696ad03fe263b6f863868aab9a21f88'
test=load(A/'verify_cpu.py','ind_goal_dispatch_CPU_v1');out=io.StringIO();err=io.StringIO();sys.argv=['verify_cpu.py','--verify-saved']
try:
 with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):test.main()
 replay={'status':'passed','stdout':out.getvalue(),'stderr':err.getvalue(),'manifest_sha256':sha((A/'delivery_manifest.json').read_bytes()),'author_files_checked':len(m['files']),'new_Slurm_queries':0,'new_GPU_submissions':0}
except BaseException as e:
 replay={'status':'failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'stdout':out.getvalue(),'stderr':err.getvalue()}
 write(D/'v1_CPU_replay.json',replay);raise
write(D/'v1_CPU_replay.json',replay)
c=load(C,'ind_actual_goal_terminal_contract');g=test.g;b=test.bundle();j=g.job_record('9900001',b,g.sbatch_argv(b));j.update(status='COMPLETED',exit_code='0:0',elapsed_seconds=1800)
try:c.validate_job(j,{'job_id':'9900001'})
except ValueError as e:
 assert str(e)=='exact full200 job scope'
 value={'status':'confirmed_cross_entrypoint_contract_blocker','kind':'Goal_dispatch_v1_terminal_registration_counterexample','source_dispatch_sha256':sha((A/'dispatch.py').read_bytes()),'runtime_consumer_sha256':sha(C.read_bytes()),'CPU_fixture':True,'uses_actual_unmodified_job_record_and_validate_job':True,'fixture_terminal_fields_only':{'status':'COMPLETED','exit_code':'0:0','elapsed_seconds':1800},'actual_registered_mode':j['mode'],'actual_registered_run_root':j['run_root'],'consumer_required_mode':'development','consumer_required_run_root':str(c.P/c.RUN),'error':str(e),'new_GPU_submissions':0,'state_written':False,'production_admitted':False}
else:raise AssertionError('cross entrypoint unexpectedly passed')
write(D/'v1_terminal_contract_blocker.json',value)
print(json.dumps({'CPU_replay':replay['stdout'].strip(),'blocker_sha256':sha((D/'v1_terminal_contract_blocker.json').read_bytes())}))
