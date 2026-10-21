from pathlib import Path
import copy,hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).parent;X=D/'gateway_attempt01'
checks=[]
def sh(b):return hashlib.sha256(b).hexdigest()
def ck(n,v,detail=None):
 checks.append({'name':n,'passed':bool(v),'detail':detail})
 if not v:raise AssertionError(n)
def write(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sh(p.read_bytes())}
def load(p,n):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def main():
 capture=read(D/'original_transaction_capture.json');statebytes=(D/'state_at_committed.json').read_bytes()
 ck('frozen committed state exact',sh(statebytes)==capture['state_sha256']=='b37d2469bd25d54fed2a61cfdc22fe7b882f52e85f929412977f4c8b8dd4e81c')
 ck('exact12 immutable captured facts',len(capture['files'])==12 and len({r['source'] for r in capture['files']})==12)
 for x in capture['files']:
  b=(R/x['private']).read_bytes();ck('captured '+x['source'],len(b)==x['bytes'] and sh(b)==x['sha256'] and b==(R/x['source']).read_bytes())
 src=R/'scripts/ops/formal_object_single_error_gateway_v1/gateway.py';ck('actual audited gateway source',sh(src.read_bytes())=='8471bba1419a9e0ca31f84e7e55ff232cd6fb0fcb4bcb89320140ea76292d727')
 g=load(src,'ind_Object_actual_gateway');c=g.controller();state=json.loads(statebytes)
 # These verify only exact immutable source/metadata/checkpoint identities; no scheduler or new invocation.
 b=g.authorization('c4554b5032284526495a973f3ca58ab054dc907595d34520eeec0852dd92842d')
 pre=read(X/'preflight.json');pending=read(X/'pending.json');held=read(X/'registered_held.json');rel=read(X/'reconciled_release.json');committed=read(X/'committed.json');ack=read(X/'sbatch_result.json');release=read(X/'release_attempt.json')
 ck('original authorization and sources',pre['authorization']==b['authorization_ref'] and pre['sources']==b['sources'])
 ck('exact original immutable invocation bytes',sh(b['invocation_bytes'])==pre['invocation_sha256']==pending['invocation_sha256']=='b7e8469b22a82838594a15208cc1f11d294d5950c5c2cd97c2ab7eb20688bf20')
 for r in (R,P):ck('runtime invocation '+str(r),(r/g.INV).read_bytes()==b['invocation_bytes'])
 argv=g.sbatch_argv(b);ck('all original argv exact',argv==ack['actual_sbatch_argv']==pre['actual_sbatch_argv']==pending['actual_sbatch_argv'])
 oldjobs=[j for j in state['registered_jobs'] if str(j['job_id'])!='3054409'];oldids={str(j['job_id']) for j in oldjobs}
 jid=g.parse_ack(ack,oldids);ck('one literal original ACK',jid=='3054409' and ack['stdout']=='3054409\n' and ack['returncode']==0)
 expected=g.job_record(jid,b,argv);ck('original registration rebuilt',held['job']==expected)
 post=rel['observation']['observation']['rows'][jid]
 wanted={**expected,**{k:post[k] for k in ('status','exit_code','elapsed_seconds','allocation','node')}}
 actual=[j for j in state['registered_jobs'] if str(j['job_id'])==jid]
 ck('captured registered row exact including original provenance',actual==[wanted])
 ck('no duplicate registered job ID',len(state['registered_jobs'])==len({str(j['job_id']) for j in state['registered_jobs']})==302)
 ck('single same-mode/stage/cell/output record',len([j for j in state['registered_jobs'] if g.duplicate(j)])==1)
 base=copy.deepcopy(state);base['registered_jobs']=oldjobs
 base['current_round_cost'].update(registered_jobs=271,allocated_gpu_seconds=1991937,allocated_gpu_hours=1991937/3600)
 base['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=0
 ck('exact root state before intent reconstructed',sh((json.dumps(base,ensure_ascii=False,indent=2)+'\n').encode())==pre['state_sha256'],{'expected':pre['state_sha256'],'computed':sh((json.dumps(base,ensure_ascii=False,indent=2)+'\n').encode())})
 # Registry projections bind every old row, not just the new pair.
 for view,st,allow in ((pre['observation'],base,None),(read(X/'held_capacity_before_registration.json'),{**base,'registered_jobs':oldjobs+[expected]},jid),(rel['observation'],{**state,'registered_jobs':oldjobs+[expected]},jid)):
  ob=view['observation'];ids=[str(j['job_id']) for j in st['registered_jobs']]
  parsed=c.parse_sacct(ob['raw_sacct'],ids);ck('saved raw sacct exact '+str(allow),parsed==ob['rows'])
  # Capacity and name/comment/active identity revalidation consume saved raw, never live Slurm.
  derived=g.normalized_projection(c,st,ob,view['details'],allow_job=allow)
  ck('all-mode original projection reconstruct '+str(allow),derived==view['derived'])
  ck('real lease observed available '+str(allow),view['lease']['lease_available_measured'] is True and view['lease']['lease_path']=='results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock')
  for row in derived['registered_projection']:
   j=next(j for j in st['registered_jobs'] if str(j['job_id'])==row['job_id'])
   ck('registered original row '+row['job_id']+' '+str(allow),row['registration_sha256']==g.sha(g.canonical(j)))
  for row in view['scontrol_queries']:
   ck('saved active scontrol fields '+str(allow),row['returncode']==0 and g.fields(row['stdout'])==view['details'][row['argv'][-1]])
 for name,isheld in (('held_identity.json',True),('released_identity.json',False)):
  o=read(X/name);ck('raw fields '+name,g.fields(o['stdout'])==o['fields'] and o['returncode']==0)
  g.validate_new_identity(expected,b,o['fields'],isheld);ck('strict resource/comment/source '+name,True)
  ck('raw command includes exact invocation '+name,'Command='+str(P/g.BASE/'run.slurm')+' '+sh(b['invocation_bytes'])+' WorkDir=' in o['stdout'])
 g.validate_new_identity(expected,b,rel['actual']['fields'],False);ck('reconciled raw fields',g.fields(rel['actual']['stdout'])==rel['actual']['fields'])
 release_result=read(X/'release_result.json')
 ck('one release fact exact',release_result=={'argv':['scontrol','release',jid],'returncode':0,'stdout':'','stderr':''})
 ck('release follows exact held registration',release['job_id']==jid and release['state_sha256']==held['state_sha256'] and release['submission_token']==b['token'] and release['argv']==['scontrol','release',jid])
 ck('reconcile binds original release attempt',rel['original_release_attempt']==release)
 ck('state clears pending only after reconciled running identity',state['pending_submission'] is None and state['autonomous_training_v1']['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0 and post['status']=='RUNNING' and post['elapsed_seconds']==67)
 ck('committed raw state pin',committed=={'status':'original_ACK_reconciled_no_resubmission','job_id':jid,'state_sha256':sh(statebytes),'automatic_retry':False})
 ck('original failure retained',read(X/'failed_transaction.json')['error']=='missing registered allocation' and read(X/'failed_transaction.json')['automatic_retry'] is False)
 formal=[j for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2'];secs=sum(rel['observation']['observation']['rows'][str(j['job_id'])]['elapsed_seconds']*rel['observation']['observation']['rows'][str(j['job_id'])]['gpus'] for j in formal)
 ck('actual snapshot cost unique272',len(formal)==272 and secs==1992004==state['current_round_cost']['allocated_gpu_seconds'])
 ck('all older allocations unchanged cost',secs-pre['observation']['derived']['allocated_formal_GPU_seconds']==67 and pre['observation']['derived']['original_GPU_seconds']==6713)
 for id,sec in zip(g.OLD_IDS,g.OLD_SECONDS):
  row=rel['observation']['observation']['rows'][id];ck('full old attempt retained '+id,row['elapsed_seconds']==sec and row['gpus']==1)
 progress=state['formal_main_progress'];ck('all formal final still sealed',progress['completed_final_trials']==0 and progress['test_opened'] is False and progress['global_release_created'] is False)
 notes=['Captured current_round_cost numerical total is correct, but inherited final:true, All271 terminal scope and old observation pointer are stale. Root has acknowledged and will update metadata in final snapshot; this transaction review is not final delivery or live cost.',
        'Only saved original submission/release/accounting evidence inspected. No new Slurm query or GPU/output poll. 67 seconds is the frozen observation slice, not completed cost.',
        'Original failure record covers immediate accounting delay; subsequent transition error remains root transport evidence. A single durable ACK and single durable release are proved by exact source transaction plus original facts, not by fabricating a new attempt.',
        'New Object trial raw terminal/adoption remains unreviewed; prior599 and the original policy_error are retained; no scientific result is added by this audit.']
 report={'schema':'formal_main_v2','kind':'Object_single_error_actual_transaction_independent_review','status':'passed_original_ACK_single_release_transaction','blockers':[],'reviewed_by':'independent','job_id':jid,'original_sbatch_ACK':'3054409\n','state_sha256':sh(statebytes),'checks':checks,'check_count':len(checks),'actual_saved_observation':ref(X/'reconciled_release.json'),'all_prior_rows_and_costs_preserved':True,'all_mode_capacity_limit':8,'occupied_at_saved_observation':[jid],'formal_allocation_count':272,'allocated_GPU_seconds_at_saved_observation':1992004,'new_allocation_GPU_seconds_at_saved_observation':67,'submission_count':1,'release_count':1,'resubmission_count':0,'repeated_release_count':0,'pending_cleared_after_original_reconciliation':True,'scientific_terminal_admitted':False,'scientific_trials_added_by_review':0,'final_sealed':True,'Slurm_queries':0,'GPU_submissions_by_reviewer':0,'P_changes_by_reviewer':0,'state_changes_by_reviewer':0,'notes':notes,'facts':capture['files'],'source_gateway':ref(src)}
 write(D/'independent_review.json',report);print(json.dumps({'status':report['status'],'checks':len(checks),'sha256':sh((D/'independent_review.json').read_bytes())}))
try:main()
except BaseException as e:
 write(D/'audit_failure.json',{'error':str(e),'error_type':type(e).__name__,'checks':checks,'traceback':traceback.format_exc()});raise
