"""Read-only independent audit of the exact Long collect submission 3047982."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,copy,importlib.util,os,sys,traceback,fcntl,re,ast
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/long_collect_submission_independent_0830'
C='results/formal_main_v2/execution/long_collect_action_v1_0830';B='results/formal_main_v2/preflight/heartbeat_20261020T1630'
AR={'path':C+'/submission_authorization.json','sha256':'e00503d5d79d397a8fc8016cb674c7d9f728c05e8229c3b3fe5e101f36e3f67b'}
AD='results/formal_main_v2/downstream_gateway/'+AR['sha256'];JOB='3047982';TOKEN='cti-downstream-gateway-v1:'+AR['sha256']
PINS={'scripts/ops/formal_action_deployment_v1/gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','scripts/ops/formal_autonomous_training_v1/controller.py':'acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','scripts/ops/formal_action_deployment_v1/wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33','.local/reconcile_Long_collect_0830.py':'8f4938b270c497b683ce351fafb636c14e591c88a3a7cb215da314e3f5f442ea','.local/dispatch_Long_collect_0830.py':'e311d325ddb886617f90b2bbf51876e788247118f71f72f2c48c911b64a2da7c','.local/authorize_Long_collect_0830.py':'db670a6266340c60aa69e9bbd95161c286a4e354d2181257d584d4aac2591034'}
READS={};CHECKS=[]
sys.dont_write_bytecode=True
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('Read-only independent audit cannot spawn, submit, query scheduler or connect')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in {'.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init'}:raise RuntimeError('No payload read')
   writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if writing and D not in p.parents:raise RuntimeError('private audit writes only')
sys.addaudithook(guard)
def chk(ok,name):
 if not ok:raise ValueError(name)
 CHECKS.append(name)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sig(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(rel,pin=None):
 p=Path(rel);p=p if p.is_absolute() else R/p
 chk(p.resolve()==p and (R in p.parents or P in p.parents),'canonical evidence '+str(p))
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest()
 chk(pin is None or h==pin,'raw pin '+str(p));chk(str(p) not in READS or READS[str(p)]==h,'same evidence '+str(p));READS[str(p)]=h
 return raw
def obj(rel,pin=None):return json.loads(read(rel,pin))
def ref(r,root=R):return obj(root/r['path'],r['sha256'])
def load(rel,root=R):
 p=root/rel;read(p,PINS[rel]);sp=importlib.util.spec_from_file_location('audit_'+p.stem+'_'+str(len(sys.modules)),p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
def write(name,v):
 raw=(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();p=D/name
 with p.open('xb') as f:f.write(raw)
 return dict(path=p.relative_to(R).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def main():
 g=load('scripts/ops/formal_action_deployment_v1/gateway.py');c=load('scripts/ops/formal_autonomous_training_v1/controller.py')
 a,e,plan,science,prepared=g.validate_authorization(R,AR)
 ready=ref(a['runtime_readiness']);reservation=ref(a['root_reservation'])
 for rr in [a['prepared_invocation'],a['runtime_readiness'],a['plan'],a['scientific_plan'],prepared['action_execution_contract'],ready['root_review'],ready['independent_review']]:ref(rr);ref(rr,P)
 chk(ready['independent_review']['sha256']=='e4f6635642d93585c4ba7c60a35af03e9ea4260405a0bdb732fe2eef5aabd242','independent readiness immutable publication')
 chk(ready['root_review']['sha256']=='f034996648ce3f739fe22fc3bd2af81f3be5ab5335c9c7754f21f63481ac8411','separate genuine root readiness')
 chk(ready['root_review']!=ready['independent_review'] and ready['allowed_stages']==['collect'] and ready['CPU_readiness_only'] is True and ready['actual_GPU_collect_verified'] is False,'exact CPU collect authorization scope')
 chk(a['automatic_retry'] is False and a['maximum_attempts']==1 and reservation['reserved_slots']==1,'single attempt dedicated one-GPU reservation')
 pre=obj(AD+'/preflight.json','8a755d24b98b89a881356aa3f1e8a7ad913946900fc08b7053aa0c5f5603a4e5')
 ack=obj(AD+'/sbatch_result.json','93997e49094d1bdee742096afd1743dd4c90a2178b2ebf2294143458b91dace2')
 fail=obj(AD+'/failed_transaction.json','263a40fc54452f7d0b86d0041587e06c9b973fb11c428c9198ec2e641a5b7598')
 post=obj(B+'/Long3047982_pending_reconciliation.json','371b146a0cf25bc0ba87a1b0c6064bc900755dbb2e11e21c1b94191a80cb75ab')
 committed=obj(AD+'/committed.json','66cf6aae4e4e1ddc47be36f262376747e381e36dd61e8ada9525402d388fbbf1')
 slot=obj(B+'/Long_collect_slot_activation.json','c1b8177195d60354e38a9b89722953414edd4aeaf568bf00b86accef80260b64')
 observed=obj(AD+'/submitted_job_observation.json','6a8e7578da7c9e2923e1e2fad8f97b12ea4d54e511a6184e99154f2f4b424e27')
 chk(fail['status']=='stopped_requires_root_reconciliation_no_retry' and fail['error']=='post-submit accounting incomplete' and fail['automatic_retry'] is False,'original accounting delay failure retained')
 chk(ack['returncode']==0 and ack['stdout']==JOB+'\n' and ack['stderr']=='','unique original sbatch ACK')
 pending=post['pending_before'];job=post['job'];raw=read(a['prepared_invocation']['path'],a['prepared_invocation']['sha256'])
 chk(raw==read(R/plan['invocation_relative'],a['prepared_invocation']['sha256'])==read(P/plan['invocation_relative'],a['prepared_invocation']['sha256']),'actual P and R invocation raw bytes match prepared exact SHA')
 chk(json.loads(raw)==prepared and prepared['method_ids']==['dense'] and prepared['stage']=='collect' and prepared['suite']=='libero_10' and prepared['prior_job_ids']==[] and prepared['resume'] is False,'fresh Long Dense-only invocation')
 chk(prepared['plan_sha256']==plan['plan_sha256']==sig({k:v for k,v in plan.items() if k!='plan_sha256'}),'canonical plan separately verified')
 bundle=dict(plan=plan,invocation=prepared,invocation_bytes=raw);argv=g.submission_argv(bundle,TOKEN)
 chk(argv==ack['actual_sbatch_argv']==pre['actual_sbatch_argv']==pending['actual_sbatch_argv']==job['downstream_gateway']['actual_sbatch_argv'],'submission command independently reconstructed exact')
 chk(pending['known_job_id']==JOB and pending['authorization']==AR and pending['request_token']==TOKEN and pending['status']=='submitted_identifier_observed','pending bound to exact ACK and token')
 chk(pending['invocation']==pre['invocation_relative']==plan['invocation_relative'] and pending['invocation_sha256']==pre['invocation_sha256']==a['prepared_invocation']['sha256'],'pending original invocation identity')
 chk(pending['automatic_retry'] is False and pending['requested_gpus']==1,'pending cannot retry and counts one slot')
 built=g.Gateway(R,c,None,None,None,a,AR,e)._job(JOB,bundle,TOKEN,argv)
 chk(built==job==committed['job']==obj('results/formal_main_v2/submissions/'+JOB+'.json'),'entire job record reconstructed by unchanged gateway')
 chk(post['new_submissions']==0 and post['automatic_retry'] is False and committed['automatic_retry'] is False and committed['reservation_consumed'] is True,'reconciliation no sbatch request')
 chk(post['exact_reservation_consumed']==a['root_reservation'] and committed['request_token']==TOKEN,'exact dedicated reservation consumed')
 chk(slot['reservation']==a['root_reservation'] and slot['authorization']==AR and slot['reserved_after']==1 and slot['occupied_before']==5 and not slot['new_GPU_submissions'],'own slot separately reserved with five occupied')
 chk(pre['authorization']==AR and pre['plan']==a['plan'] and pre['prepared_invocation']==a['prepared_invocation'],'original preflight same reviewed authority')
 chk(pre['runtime_preflight']['output_exists'] is False,'fresh output absent at actual preflight')
 chk(post['status']=='exact_original_ACK_job_reconciled' and post['final_release_authorized'] is False,'root reconciliation exact and no final release')
 jobs=pre['registered_jobs'];ids=[str(j['job_id']) for j in jobs]
 chk(len(ids)==274 and len(set(ids))==274 and JOB not in ids,'274 unique pre-existing registry identities')
 chk(not any(j.get('stage_key')==prepared['stage_key'] or (j.get('suite')=='libero_10' and j.get('mode')=='collect') for j in jobs),'no existing or overlapping Long collect')
 before_snap=pre['scheduler_observation'];after_snap=post['scheduler']
 chk(set(before_snap['rows'])==set(ids) and set(before_snap['queue'])<=set(ids),'complete preflight accounting coverage')
 after_jobs=jobs+[job]
 caps=g.reconcile_submission(c,after_jobs,after_snap,job,TOKEN,a['controller_job_id'],post['scontrol_corroboration'])
 before_caps=c.capacity(jobs,before_snap,a['controller_job_id'])
 chk(before_caps==pre['capacity'] and len(before_caps['occupied'])==5 and not before_caps['findings'] and not before_caps['unknown'],'original capacity pure reconstruction five')
 chk(caps==post['capacity'] and len(caps['occupied'])==6 and set(caps['occupied'])==set(before_caps['occupied'])|{JOB} and not caps['findings'] and not caps['unknown'],'original reconciliation pure reconstruction five to six')
 chk(after_snap['rows'][a['controller_job_id']]['gpus']==0 and after_snap['rows'][a['controller_job_id']]['status']=='RUNNING','CPU0 controller separate from sixGPU slots')
 chk(after_snap['queue'][JOB]['comment']==TOKEN and after_snap['rows'][JOB]['gpus']==1,'actual scheduler exact token oneGPU')
 for snap,label in [(before_snap,'preflight'),(after_snap,'reconcile')]:
  rows={}
  for line in snap['raw_sacct'].splitlines():
   fields=line.split('|')
   if fields[0] in snap['rows']:
    chk(fields[0] not in rows,'raw accounting unique '+label+' '+fields[0]);rows[fields[0]]=fields
  chk(set(rows)==set(snap['rows']),'raw accounting all parsed records '+label)
  for jid,f in rows.items():
   r=snap['rows'][jid]
   chk(f[1].split()[0].rstrip('+')==r['status'] and f[2]==r['exit_code'] and int(f[3])==r['elapsed_seconds'] and f[4]==r['allocation'] and f[5]==r['node'] and f[6]==r['scheduler_name'] and f[7]==r['scheduler_comment'],'raw accounting exact parsed values '+label+' '+jid)
 chk(observed['observation']==after_snap and observed['request_token']==TOKEN and observed['job_id']==JOB,'preserved submitted observation agrees')
 detail=post['actual_scontrol_detail'];tokens=detail['stdout'].split()
 chk(detail['argv']==['scontrol','show','job','-o',JOB] and detail['returncode']==0 and not detail['stderr'],'actual exact-job scontrol evidence')
 expected={'JobId':JOB,'JobName':'cti-formal-downstream','JobState':'RUNNING','WorkDir':str(P),'Comment':TOKEN,'Requeue':'0','Restarts':'0','ExcNodeList':'gpu4020','TimeLimit':'04:00:00','NumCPUs':'7','StdOut':str(P/'results/slurm/cti-formal-downstream_3047982.out'),'StdErr':str(P/'results/slurm/cti-formal-downstream_3047982.err')}
 for k,v in expected.items():chk(k+'='+v in tokens,'scontrol exact '+k)
 chk(sum(q['comment']==TOKEN for q in after_snap['queue'].values())==1,'one active queue request with exact token')
 for rel,pin in PINS.items():read(rel,pin)
 recsrc=(R/'.local/reconcile_Long_collect_0830.py').read_text()
 chk('c.atomic_json(sp,s,before)' in recsrc and 'assert s==expected' in recsrc and 'g.reconcile_submission(c,jobs,snapshot,job,token' in recsrc,'root bounded source uses original validator expected mutation and CAS')
 chk('scheduler.run(detail_argv)' in recsrc and 'detail_argv=[\'scontrol\'' in recsrc and '.submit(' not in recsrc and "['sbatch'" not in recsrc,'root reconciliation has no submission path')
 dispatch=ast.parse((R/'.local/dispatch_Long_collect_0830.py').read_text())
 submit_literals=[n.value for n in ast.walk(dispatch) if isinstance(n,ast.Constant) and n.value=='--submit']
 chk(len(submit_literals)==1,'dispatch one submit branch no loop')
 chk(not any(isinstance(n,(ast.For,ast.While)) for n in ast.walk(dispatch)),'dispatch no retry loop')
 outer=load('scripts/ops/formal_action_deployment_v1/wrapper.py',P);actual=outer.verify(prepared,project=P)
 chk(actual['readiness']==ready and actual['effective_plan']==plan,'actual P outer wrapper.verify genuine dual readiness and canonical inputs')
 # One short shared-lock snapshot; no production or lock-file content modification.
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
  state_raw=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(state_raw)
  owner=json.loads((R/'results/formal_main_v2/autonomous_training/run_v1/owner.json').read_bytes())
  fcntl.flock(lock,fcntl.LOCK_UN)
 ctl=state['autonomous_training_v1'];state_job=[j for j in state['registered_jobs'] if str(j['job_id'])==JOB]
 chk(len(state_job)==1 and state_job[0]==job,'actual live registry has unique exact submitted job')
 chk(state['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None,'actual pending cleared reservation consumed no root hold')
 chk(ctl['reservation_root_record']==a['root_reservation'],'live reservation identity preserved')
 consumption=ctl['downstream_reservations_consumed'][AR['sha256']]
 chk(consumption==dict(job_id=JOB,reservation=a['root_reservation'],request_token=TOKEN),'exact authority one-time consumption')
 chk(owner==post['controller_owner'] and ctl['owner_id']==owner['owner_id'] and ctl['controller_job_id']==owner['coordinator_job_id']==a['controller_job_id']=='3034538','same controller owner and lease identity')
 with Path(owner['lock']).open('rb') as lock:
  held=False
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 chk(held and post['lifecycle_lease_held'] and slot['lifecycle_lease_held'],'lifecycle lease actually held and original observations preserved')
 chk([str(j['job_id']) for j in state['registered_jobs']]==ids+[JOB],'no omitted or duplicated registry history')
 variable={'status','elapsed_seconds','exit_code','node','allocation'}
 for original,current in zip(jobs,state['registered_jobs'][:-1]):
  chk({k:v for k,v in original.items() if k not in variable}=={k:v for k,v in current.items() if k not in variable},'old registered identity retained '+str(original['job_id']))
 chk(all(j.get('mode')!='final' for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2'),'no registered final evaluation')
 inventory=obj('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 chk(len(inventory['files'])==173,'173 frozen source count')
 for rel,h in inventory['files'].items():read(R/rel,h);read(S/rel,h)
 for rel,h in pre['read_evidence_sha256'].items():read(R/rel,h)
 for path,h in prepared['watched_files'].items():read(Path(path),h)
 e.unchanged()
 for path,h in list(READS.items()):chk(sha(path)==h,'immutable evidence unchanged '+path)
 evidence=write('evidence_sha256.json',READS);checks=write('checks.json',CHECKS)
 report=write('independent_review.json',dict(schema='formal_main_v2',kind='independent_exact_Long_collect_submission_review',status='passed',review_role='independent',reviewer='/root/object64_pending_0333_audit',utc=datetime.now(timezone.utc).isoformat(),job_id=JOB,authorization=AR,request_token=TOKEN,plan=a['plan'],invocation=dict(path=plan['invocation_relative'],sha256=a['prepared_invocation']['sha256']),runtime_readiness=a['runtime_readiness'],root_reconciliation=dict(path=B+'/Long3047982_pending_reconciliation.json',sha256='371b146a0cf25bc0ba87a1b0c6064bc900755dbb2e11e21c1b94191a80cb75ab'),original_failure_preserved='post-submit accounting incomplete',exact_original_ACK_reconciled=True,single_submission=True,automatic_retry=False,original_reconcile_function_passed=True,actual_P_outer_verify_passed=True,source173_unchanged=True,controller_owner=owner,lifecycle_lease_held=held,occupied_before=5,occupied_after=6,capacity_limit=8,dedicated_reserved_slots_before=1,dedicated_reserved_slots_after=0,duplicate_submission_found=False,registered_history_preserved=True,pending_cleared=True,live_state_snapshot_sha256=hashlib.sha256(state_raw).hexdigest(),only_short_read_lock=True,actual_collection_completed_not_claimed=True,final_values_read=False,weights_deserialized=False,new_GPU_calls=0,new_scheduler_queries=0,production_state_or_Git_writes=0,checks_passed=len(CHECKS),evidence=evidence,checks=checks,audit_source=dict(path=Path(__file__).relative_to(R).as_posix(),sha256=sha(__file__)),limits=['Uses original saved scheduler observations; does not refresh normal GPU execution.','CPU submission audit is not actual observation collection acceptance.','Only exact collect authorization; full/components and sealed final remain gated.','Unrelated state mutation safety is bounded by exact root CAS source, preflight registered identities, preserved historical fields and one live short-lock projection; this audit does not fabricate an unavailable full pre-mutation state dump.']))
 rows=[dict(path=p.relative_to(R).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(D.iterdir()) if p.is_file() and p.name!='manifest.json']
 manifest=write('manifest.json',dict(schema='formal_main_v2',kind='independent_collect_submission_manifest',files=rows))
 print(json.dumps(dict(status='passed',report=report,manifest=manifest,checks=len(CHECKS))))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  write('failure_a1.json',dict(error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),passed_checks=len(CHECKS)));raise
