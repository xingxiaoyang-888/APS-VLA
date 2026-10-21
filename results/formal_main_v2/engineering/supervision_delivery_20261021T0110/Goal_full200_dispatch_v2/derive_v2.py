from pathlib import Path
import hashlib,json,shutil
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
OLD=R/'.local/goal_full200_dispatch_20261021T0110';D=R/'.local/goal_full200_dispatch_20261021T0110_v2'
D.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(OLD/'delivery_manifest.json')=='d3d9cfca965d9af267c424431ecaa3a465bbf39366c5eac9d3c105c3fd6d0a80'
for name in ['dispatch.py','scope.json','verify_cpu.py','prepare_admission.py','saved_real_observation.json','README.md']:
 with (D/name).open('xb') as f:f.write((OLD/name).read_bytes())
p=D/'dispatch.py';t=p.read_text()
assert "mode=MODE,\n  stage_key=STAGE" in t
t=t.replace("mode=MODE,\n  stage_key=STAGE","mode='development',goal_dispatch_mode=MODE,\n  stage_key=STAGE",1)
t=t.replace("run_root=str(P/OUT),invocation=AUTH","run_root=str(P/OUT/'original_run'),attempt_root=str(P/OUT),invocation=AUTH",1)
t=t.replace("return (j.get('mode')==MODE or j.get('stage_key')==STAGE","return (j.get('goal_dispatch_mode')==MODE or j.get('mode')==MODE or j.get('stage_key')==STAGE",1)
p.write_text(t)
v=D/'verify_cpu.py';s=v.read_text().replace(".local/goal_full200_dispatch_20261021T0110'",".local/goal_full200_dispatch_20261021T0110_v2'")
helper="""def real_terminal_registration_checks():
 cp=R/'.local/goal_full200_author_20261021T0110_v2/package/consumer.py'
 assert hashlib.sha256(cp.read_bytes()).hexdigest()=='c12a6a5b99c4e34ff19f535a4725fecd9fcabc70ba1f37dc2c6c32c979ad3c4b'
 spec=importlib.util.spec_from_file_location('_real_Goal_full200_consumer_registration_CPU',cp)
 consumer=importlib.util.module_from_spec(spec);sys.modules[spec.name]=consumer
 exec(compile(cp.read_bytes(),str(cp),'exec'),consumer.__dict__)
 b=bundle();j=g.job_record('9920002',b,g.sbatch_argv(b));d={'job_id':'9920002'}
 ok(j['mode']=='development' and j['run_root']==str(g.P/g.OUT/'original_run') and j['goal_dispatch_mode']==g.MODE,'native registration uses unchanged original consumer schema plus typed stage identity')
 no(lambda:consumer.validate_job(j,d),'real consumer rejects initial pending registration as terminal')
 terminal=copy.deepcopy(j);terminal.update(status='COMPLETED',exit_code='0:0',elapsed_seconds=123)
 consumer.validate_job(terminal,d)
 ok(True,'real unchanged consumer accepts native registration with explicitly synthetic future accounting fixture only')
 for key,value in [('status','FAILED'),('exit_code','1:0'),('gpus',2),('elapsed_seconds',-1),('job_id','9920003'),('stage_key','other'),('run_root',str(g.P/g.OUT)),('suite','libero_object'),('mode',g.MODE)]:
  x=copy.deepcopy(terminal);x[key]=value
  no(lambda x=x:consumer.validate_job(x,d),'real original terminal consumer rejects registered '+key)
 ok(g.duplicate(j),'native development registration still duplicate-protected by typed exact scope')
 ok(not g.duplicate({'mode':'development','stage_key':'other_old_development','run_root':'other_old_run'}),'other historical development rows are not mislabeled this prospective attempt')
 for row in [{'goal_dispatch_mode':g.MODE},{'stage_key':g.STAGE},{'logical_trial_id':g.CELL},{'invocation':g.AUTH},{'run_root':str(g.P/g.OUT/'original_run')},{'name':g.NAME}]:
  ok(g.duplicate(row),'partial same-attempt identity blocks repeat '+str(next(iter(row))))
"""
s=s.replace('def main():\n',helper+'\ndef main():\n',1).replace('reconcile_metadata_checks()\n','reconcile_metadata_checks();real_terminal_registration_checks()\n',1)
v.write_text(s)
readme=D/'README.md';text=readme.read_text()
text+='\n## Dispatcher v2 registration correction\n\nThe frozen v1 dispatcher d3d9cfca... was independently rejected for a real terminal interface mismatch. v2 only changes registration to mode=development and run_root=attempt01/original_run, retaining goal_dispatch_mode=goal_full200_prospective plus stage/pair/token identity. Duplicate detection recognizes the typed marker and exact attempt identities; it does not classify all historical development jobs as duplicates. The runtime consumer is unchanged. Added CPU tests call its actual validate_job with the actual new registration and explicitly synthetic future accounting fields; this is not an actual terminal outcome or new GPU evidence. The original v1 package and independent blocker are preserved.\n'
readme.write_text(text)
blocker=R/'.local/downstream_runtime_independent_20261021T0110/Goal_dispatch/v1_terminal_contract_blocker.json'
assert sha(blocker)=='1fbe795af4b68d11b27ec4ce4814ab480eeecbacb75686c0fc81f6cf1598a5b1'
with (D/'v1_terminal_contract_blocker.json').open('xb') as f:f.write(blocker.read_bytes())
derivation=dict(schema='formal_main_v2',kind='Goal_dispatch_v2_registration_contract_derivation',
 prior_manifest=dict(path=str((OLD/'delivery_manifest.json').relative_to(R)),sha256=sha(OLD/'delivery_manifest.json')),
 blocker=dict(path=str(blocker.relative_to(R)),sha256=sha(blocker)),prior_source_sha256=sha(OLD/'dispatch.py'),new_source_sha256=sha(p),
 changes=['Registry mode development and original_run root match unchanged real terminal consumer.',
 'Preserve typed goal_dispatch_mode and exact stage/pair/token; detect duplicate without excluding all unrelated development.',
 'Call unchanged actual consumer.validate_job in CPU fixtures, keeping synthetic future accounting distinct.'],
 runtime_unchanged=True,state_writes=0,Slurm_submissions=0)
(D/'derivation.json').write_text(json.dumps(derivation,sort_keys=True,indent=2)+'\n')
files={'scripts/ops/formal_goal_full200_dispatch_v1/'+n:sha(D/n) for n in ('dispatch.py','scope.json')}
pub=dict(schema='formal_main_v2',kind='Goal_full200_exact_dispatch_publication_map',source_root=str(D.relative_to(R)),
 files=files,install_files=[dict(source=str((D/n).relative_to(R)),destination='scripts/ops/formal_goal_full200_dispatch_v1/'+n,bytes=(D/n).stat().st_size,sha256=sha(D/n)) for n in ('dispatch.py','scope.json')],
 runtime_separate_package_manifest_sha256='2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec',production_admitted=False,actual_P_verified=False)
(D/'publication_map.json').write_text(json.dumps(pub,sort_keys=True,indent=2)+'\n')
pins=dict(dispatch=sha(p),scope=sha(D/'scope.json'),verify_cpu=sha(v),prepare_admission=sha(D/'prepare_admission.py'),runtime_package_manifest='2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec')
(D/'final_pins.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n')
print(json.dumps(pins,sort_keys=True))
