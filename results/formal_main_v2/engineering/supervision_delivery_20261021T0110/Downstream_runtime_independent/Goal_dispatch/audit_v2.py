from pathlib import Path
import ast,contextlib,copy,hashlib,importlib.util,io,json,subprocess,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=Path(__file__).parent
A=R/'.local/goal_full200_dispatch_20261021T0110_v2'
V1=R/'.local/goal_full200_dispatch_20261021T0110'
K=R/'.local/goal_full200_author_20261021T0110_v2/package'
E=R/'results/formal_main_v2/engineering/supervision_delivery_20261021T0110'
checks=[];rejects=[];external_calls=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def h(p):return sha(p.read_bytes())
def read(p):return json.loads(p.read_bytes())
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def reject(fn,label):
 try:fn()
 except (ValueError,AssertionError) as e:
  rejects.append(dict(check=label,error_type=type(e).__name__,error=str(e)));return
 raise AssertionError('accepted invalid fixture: '+label)
def write(n,v):
 with (D/n).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def no_external(*args,**kwargs):
 external_calls.append(repr(args[0] if args else kwargs));raise AssertionError('independent CPU audit forbids external subprocess')
def manifest(p,pin):
 ok(h(p)==pin,'manifest SHA '+str(p.relative_to(R)))
 m=read(p);ok(m['file_count']==len(m['files']),'manifest count '+p.parent.name)
 for row in m['files']:
  f=R/row['path']
  ok(f.resolve()==f and f.is_relative_to(p.parent),'safe member '+row['path'])
  ok(f.stat().st_size==row['bytes'] and h(f)==row['sha256'],'member bytes '+row['path'])
 return m
def main():
 m=manifest(A/'delivery_manifest.json','797026fc869be61ff200cd2998449e54a5b5aa26bb2b5912bd836c773a8c1287')
 old=manifest(V1/'delivery_manifest.json','d3d9cfca965d9af267c424431ecaa3a465bbf39366c5eac9d3c105c3fd6d0a80')
 ok(h(A/'verify_cpu.py')=='e0f0407b5fbe41d3796e330e7d227c53098ed5b34e215ef2f48065d89f9fcc2a','exact CPU replay source')
 expected=(V1/'dispatch.py').read_text()
 edits=[
 ("return (j.get('mode')==MODE or j.get('stage_key')==STAGE","return (j.get('goal_dispatch_mode')==MODE or j.get('mode')==MODE or j.get('stage_key')==STAGE"),
 ("experiment=EXPERIMENT,mode=MODE,","experiment=EXPERIMENT,mode='development',goal_dispatch_mode=MODE,"),
 ("run_root=str(P/OUT),invocation=AUTH","run_root=str(P/OUT/'original_run'),attempt_root=str(P/OUT),invocation=AUTH")]
 for oldtext,newtext in edits:
  ok(expected.count(oldtext)==1,'one bounded production edit '+oldtext);expected=expected.replace(oldtext,newtext)
 ok(expected==(A/'dispatch.py').read_text(),'production v2 contains only exact registration and duplicate edits')
 for n in ['scope.json','prepare_admission.py','saved_real_observation.json']:
  ok((A/n).read_bytes()==(V1/n).read_bytes(),'unchanged '+n)
 ok((A/'v1_terminal_contract_blocker.json').read_bytes()==(D/'v1_terminal_contract_blocker.json').read_bytes(),'original independent v1 counterexample preserved')
 test=load(A/'verify_cpu.py','ind_goal_dispatch_CPU_v2')
 out=io.StringIO();err=io.StringIO();argv0=sys.argv;run0=subprocess.run
 try:
  sys.argv=['verify_cpu.py','--verify-saved'];subprocess.run=no_external
  with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):test.main()
 finally:sys.argv=argv0;subprocess.run=run0
 replay=read(A/'CPU_report.json')
 ok(len(test.positive)==94 and len(test.negative)==187,'replayed 94 positive and 187 refusal cases')
 ok(replay['positive']==test.positive and replay['negative']==test.negative,'complete reconstructed CPU outcomes exact')
 ok(not external_calls,'no external scheduler or other subprocess called')
 write('v2_CPU_replay.json',dict(status='passed',stdout=out.getvalue(),stderr=err.getvalue(),author_CPU_report_sha256=h(A/'CPU_report.json'),positive_count=94,negative_count=187,source_module_main_replayed=True,fixture_not_real_GPU=True,external_calls=external_calls))
 g=test.g;c=load(K/'consumer.py','ind_actual_Goal_terminal_registration_v2')
 ok(h(K/'consumer.py')=='c12a6a5b99c4e34ff19f535a4725fecd9fcabc70ba1f37dc2c6c32c979ad3c4b','unmodified actual consumer source')
 b=test.bundle();j=g.job_record('9900311',b,g.sbatch_argv(b));disp={'job_id':'9900311'}
 reject(lambda:c.validate_job(j,disp),'actual terminal consumer rejects initial pending registration')
 terminal=copy.deepcopy(j);terminal.update(status='COMPLETED',exit_code='0:0',elapsed_seconds=123)
 c.validate_job(terminal,disp);ok(True,'actual consumer accepts real job_record shape plus explicitly synthetic terminal accounting only')
 for key,value in [('mode',g.MODE),('run_root',str(P/g.OUT)),('status','FAILED'),('exit_code','1:0'),('stage_key','another_stage'),('job_id','9900312'),('suite','libero_object'),('gpus',2),('elapsed_seconds',-1)]:
  x=copy.deepcopy(terminal);x[key]=value;reject(lambda x=x:c.validate_job(x,disp),'actual consumer rejects '+key+' mutation')
 ok(g.duplicate(j),'new native development record remains duplicate protected')
 ok(g.duplicate({'goal_dispatch_mode':g.MODE,'status':'FAILED'}),'typed partial failed history blocks another submit')
 ok(not g.duplicate({'mode':'development','stage_key':'unrelated','run_root':'unrelated'}),'unrelated development row is not this attempt')
 for submit in [False,True]:
  f=test.Fake();b2=test.bundle();b2['reconcile_existing']=True
  reject(lambda:g.Transaction(f,b2).run(submit=submit),'existing ACK metadata cannot authorize fresh path '+str(submit))
  ok(f.sbatch_calls==0 and f.release_calls==0,'existing ACK refusal performs no scheduler mutation '+str(submit))
 f=test.Fake('dispatch_proof')
 try:g.Transaction(f,test.bundle()).run(submit=True)
 except test.Interruption:pass
 else:raise AssertionError('BaseException not propagated at runtime dispatch proof')
 ok(f.release_calls==0 and f.sbatch_calls==1 and f.state['pending_submission'] is not None,'BaseException at real proof boundary preserves pending and never releases')
 contract=dict(status='passed_actual_unchanged_consumer_schema_CPU',uses_actual_unmodified_job_record_and_validate_job=True,fixture_terminal_fields_only={'status':'COMPLETED','exit_code':'0:0','elapsed_seconds':123},mode=j['mode'],goal_dispatch_mode=j['goal_dispatch_mode'],run_root=j['run_root'],attempt_root=j['attempt_root'],GPU_terminal_acceptance=False,independent_refusals=rejects)
 write('v2_terminal_contract.json',contract)
 scope=read(A/'scope.json');pub=read(A/'publication_map.json');package=read(K/'package_manifest.json')
 ok(h(K/'package_manifest.json')==g.RUNTIME_MANIFEST_SHA=='2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec','runtime v2 manifest exact')
 ok(scope['runtime_files']==package['files'] and len(package['files'])==10,'full runtime 10 source closure')
 for n,pin in package['files'].items():ok(h(K/Path(n).name)==pin,'runtime source '+n)
 ok(h(A/'dispatch.py')==pub['files'][g.BASE+'/dispatch.py'] and h(A/'scope.json')==pub['files'][g.BASE+'/scope.json'],'two published dispatch source map')
 i2=R/'.local/integrate_goal_full200_20261021T0110_v2.py';i3=R/'.local/integrate_goal_full200_20261021T0110_v3.py'
 ok(h(i2)=='8b7a2f0202222eb759507cba9a691a03aec02bf692eaa1dbf2b51115285d0b01','prior integration helper exact')
 ok(h(i3)=='1c27de743e7862aef6a618f937ac0a356b993c834ebb1b5a4cc3c90224627f7b','integration v3 exact')
 text=i3.read_text();ok(i2.read_text().replace('row["destination"]','row["path"]',2)==text,'integration v3 only corrects first runtime two field accesses')
 compile(text,str(i3),'exec');tree=ast.parse(text)
 ok(not any(isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value in ('sbatch','scontrol','squeue','sacct') for n in ast.walk(tree)),'integration helper has no scheduler command')
 inst=read(E/'Goal_full200_v2/install_files.json');dmap=read(E/'Goal_full200_dispatch_v2/publication_map.json')
 ok(len(inst['files'])==11 and len(dmap['install_files'])==2,'integration exactly 11 runtime plus 2 dispatch entries')
 install=[]
 for row in inst['files']:
  ok('path' in row and 'destination' not in row,'runtime row path schema '+row['source'])
  p=E/'Goal_full200_v2'/row['source'];ok(h(p)==row['sha256'] and p.stat().st_size==row['bytes'],'archived runtime install content '+row['path'])
  install.append(dict(destination=row['path'],sha256=row['sha256']))
 for row in dmap['install_files']:
  p=E/'Goal_full200_dispatch_v2'/Path(row['source']).name;ok(h(p)==row['sha256'] and p.stat().st_size==row['bytes'],'archived dispatch install content '+row['destination'])
  install.append(dict(destination=row['destination'],sha256=row['sha256']))
 ok(len({x['destination'] for x in install})==13,'no install target overlaps')
 checks_static={
 'shared_writer_lock':'with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):',
 'CAS_state_before':'assert h(st)==a.expected_state_sha256',
 'pending_and_reservation':'state["autonomous_training_v1"]["reserved_GPU_slots"]==0',
 'source173':'assert len(inventory["files"])==173',
 'no_overwrite':'assert not (root/n).exists(),n',
 'actual_P_verify':'str(P/PROD/"entry.py"),"--verify","--package-manifest-sha256",MSHA',
 'root_authorization_validator':'e.validate_authorization(auth,',
 'actual_entry_readiness_validator':'e.check_review(ind,"independent",MSHA',
 'admission_stdout_builder':'"--actual-P-verification",B+"/Goal_actual_P_capture.json","--root-reviewed"',
 'no_GPU_scientific_authorization':'scientific_release=False,original_goal200_HOLD=True,new_Goal_science_HOLD=True',
 }
 for label,needle in checks_static.items():ok(needle in text,'root integration static contract '+label)
 ok(text.count('assert h(st)==a.expected_state_sha256')==2,'root integration CAS before and after')
 e=load(K/'entry.py','ind_Goal_runtime_readiness_schema_only')
 runtime_review=read(R/'.local/downstream_runtime_independent_20261021T0110/Goal_full200/final_independent_review.json')
 readiness=read(R/'.local/downstream_runtime_independent_20261021T0110/Goal_full200/independent_readiness.json')
 e.check_review(readiness,'independent',g.RUNTIME_MANIFEST_SHA,package['files'][g.PROD+'/config.json'])
 ok(runtime_review['package_files']==package['files'] and runtime_review['blockers']==[],'runtime independent existing receipt matches integration input schema')
 write('integration_v3_static_review.json',dict(status='passed_static_contract_only',entrypoint=str(i3.relative_to(R)),entrypoint_sha256=h(i3),previous_unexecuted_helper_sha256=h(i2),fixed_blocker='Runtime install map uses path; dispatcher map continues destination.',install_file_count=13,install_files=install,checks=list(checks_static),actual_install_performed=False,actual_P_verified=False,root_authorization_written=False,Slurm_commands=0,requires_root_current_state_CAS=True))
 inv=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
 ok(h(inv)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926','173 inventory SHA')
 inventory=read(inv);ok(len(inventory['files'])==173,'173 source files')
 for root in [R,P/'snapshots/formal_main_v2_run_564be0995e',R/'snapshots/formal_main_v2_run_564be0995e']:
  for n,pin in inventory['files'].items():ok(h(root/n)==pin,'unchanged frozen source '+str(root/n))
 for author,mm in [(A,m),(V1,old)]:
  for row in mm['files']:ok(h(R/row['path'])==row['sha256'],'author package unchanged after CPU '+row['path'])
 report=dict(schema='formal_main_v2',kind='Goal_full200_atomic_dispatch_independent_review',status='passed',reviewed_by='independent',
  reviewed_by_agent='/root/spatial588_recovery_audit_2054',review_scope='source_and_CPU_only',blockers=[],
  author_manifest=dict(path=str((A/'delivery_manifest.json').relative_to(R)),sha256=h(A/'delivery_manifest.json')),
  dispatch_files=pub['files'],package_manifest_sha256=g.RUNTIME_MANIFEST_SHA,runtime_files=package['files'],
  scope_sha256=h(A/'scope.json'),config_sha256=package['files'][g.PROD+'/config.json'],
  package_manifest=dict(path=str((K/'package_manifest.json').relative_to(R)),sha256=h(K/'package_manifest.json')),
  independent_checks=len(checks),independent_rejections=len(rejects),author_CPU_rebuilt={'positive':94,'negative':187,'exact_saved_report':True},
  original_v1_blocker_retained=dict(path=str((D/'v1_terminal_contract_blocker.json').relative_to(R)),sha256=h(D/'v1_terminal_contract_blocker.json'),resolved_by_exact_v2_registration_change=True),
  true_original_consumer_validate_job_used=True,terminal_fixture_is_CPU_only=True,
  integration_review=dict(path=str((D/'integration_v3_static_review.json').relative_to(R)),sha256=h(D/'integration_v3_static_review.json')),
  safeguards_verified=['original ACK and single release ordering','unknown ACK and BaseException fail closed with durable pending','shared writer lock and CAS','all modes eight GPU and same pair/Goal overlap protection','existing ACK source-only metadata cannot authorize fresh submission or readiness','full fixed200 identity and unmodified original consumer schema','same original 1643 engineering GPU seconds retained','fresh runtime and two filesystem gates remain required','separate raw scientific consumer terminal acceptance still required'],
  source173_verified=True,source173_roots=[str(R),str(P/'snapshots/formal_main_v2_run_564be0995e'),str(R/'snapshots/formal_main_v2_run_564be0995e')],
  GPU_execution_authorized=False,actual_P_verified=False,production_ready=False,production_admitted=False,
  remaining_production_gates=['root exact13 source publication and fresh actual P metadata/source/capacity proof','root readiness and exact one-attempt authorization plus admission','native held original ACK, unique registration, actual runtime dispatch proof, then at most one release','future real original raw200/observer/gate/runtime terminal reconstruction and independent review before scientific adoption'],
  old_Goal200_HOLD=True,other_Goal1000_HOLD=True,final_sealed=True,new_Slurm_queries=0,new_GPU_submissions=0,new_GPU_seconds=0,new_scientific_trials=0,state_written=False,canonical_or_P_written=False,
  audit_artifacts={n:h(D/n) for n in ['v2_CPU_replay.json','v2_terminal_contract.json','integration_v3_static_review.json']})
 write('v2_independent_checks.json',dict(status='passed',checks=checks,rejections=rejects,external_calls=external_calls))
 report['checks_sha256']=h(D/'v2_independent_checks.json');write('final_independent_review.json',report)
 print(json.dumps(dict(status=report['status'],checks=len(checks),independent_rejections=len(rejects),review_sha256=h(D/'final_independent_review.json'),integration_sha256=h(D/'integration_v3_static_review.json'))))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  write('v2_audit_failure.json',dict(error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),checks=checks,rejections=rejects,external_calls=external_calls,production_mutation=False));raise
