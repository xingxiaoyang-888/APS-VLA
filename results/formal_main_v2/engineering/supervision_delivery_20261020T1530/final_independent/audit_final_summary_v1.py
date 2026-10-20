from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,copy,sys,os,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/dispatch_independent_20261020T1530/final'
B='results/formal_main_v2/preflight/heartbeat_20261020T2330'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530'
JOBS=['3050870','3050890','3050901','3050916']
checks=[];inputs={}
def guard(event,args):
 if event.startswith(('subprocess.','socket.')) or event in ('os.system','os.posix_spawn','os.fork'):raise RuntimeError('No process/network allowed')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(args[0]).absolute();mode=args[1];flags=args[2] or 0
  writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if writing and not p.is_relative_to(D):raise RuntimeError('Private writes only: '+str(p))
sys.addaudithook(guard)
def h(b):return hashlib.sha256(b).hexdigest()
def check(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
def read(n,pin=None):
 p=R/n;check(p.is_relative_to(R) and p.suffix not in ('.pt','.pth','.bin','.npz','.npy','.hdf5','.h5'),'read nonweight control evidence '+n)
 b=p.read_bytes();sh=h(b);inputs[n]={'sha256':sh,'bytes':len(b)}
 if pin:check(sh==pin,'exact input SHA '+n)
 return b
def rd(n,pin=None):return json.loads(read(n,pin))
def put(n,b):
 p=D/n;p.parent.mkdir(exist_ok=True,parents=True)
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':h(b),'bytes':len(b)}
def dump(n,v):return put(n,(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def ref(n):
 b=read(n);return {'path':n,'sha256':h(b)}
def canon(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()+b'\n'
def diffs(a,b,p=''):
 if isinstance(a,dict) and isinstance(b,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   q=p+'/'+k
   if k not in a or k not in b:out.append(q)
   else:out.extend(diffs(a[k],b[k],q))
  return out
 if a!=b:return [p]
 return []
def main():
 source=read('.local/summarize_20261020T1530.py','7d9dc7df2d9ce2dd20eafde070a836d46c87c7e504a8865b66270db8d98d2115')
 completion=rd(B+'/final_supervision_completion.json','267198f9e14e193b261bf6e000a3d59238e019bf56b9a0468f6cb2bdfdbed924')
 summary=rd(B+'/summary_after_dispatch.json','3bced1812b1002f276f6327674c37779d8747ecbb9e368d8073e7cd9bc32b216')
 intent=rd(completion['intent']['path'],completion['intent']['sha256'])
 beforebytes=read(B+'/final_supervision_state_before.json',completion['state_before_sha256']);before=json.loads(beforebytes)
 check(summary['state_before_sha256']==intent['state_before_sha256']==completion['state_before_sha256'],'all transaction before identities identical')
 check(intent['source']['sha256']==h(source),'intent binds audited root source')
 check(intent['summary']==completion['summary'],'summary identity agrees with intent/completion')
 for n in ['completed_evidence','completed_evidence_post_independent_review','dispatch','dispatch_independent_review','Goal_probe_terminal']:
  x=summary[n];rd(x['path'],x['sha256'])
 post=rd(summary['completed_evidence_post_independent_review']['path'])
 dispatch=rd(summary['dispatch']['path']);dind=rd(summary['dispatch_independent_review']['path']);probe=rd(summary['Goal_probe_terminal']['path'])
 check(post['status'].startswith('passed') and dind['status'].startswith('passed'),'prior independent core and dispatch reviews passed')
 f0=before['formal_main_progress'];ctl=before['autonomous_training_v1'];registry=before['registered_jobs']
 for field,expected in [('root_and_independent_completed_arms',66),('root_and_independent_reviewed_arm_updates',331000),('current_action_development_trial_count',4400),('completed_development_trials',5612),('current_action_development_unique_initial_states',400),('completed_final_trials',0)]:check(f0[field]==expected,'before core '+field)
 for field,expected in [('root_independent_complete',66),('root_independent_updates',331000),('current_action_development_trials',4400),('raw_historical_and_current_accepted_development_trials',5612),('unique_initial_states',400),('new_training_arms_accepted',2),('new_development_trials_accepted',600),('new_development_trials_planned',800),('new_dispatch_trials_accepted',0),('final_completed',0),('final_expected',35200)]:check(summary[field]==expected,'summary '+field)
 check(summary['compatible_development_trials']==summary['current_action_development_trials']+summary['explicit_legacy_equivalent_Long_trials']==5000,'compatible exactly current4400 + explicit legacy600')
 check(not f0['test_opened'] and not f0['global_release_created'] and not summary['final_release'],'sealed final remains closed')
 check(before['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None,'no unresolved pending/reservation in before transaction')
 ids=[str(j['job_id']) for j in registry];check(len(set(ids))==len(ids),'all registered allocation IDs unique')
 check(summary['new_development_job_ids']==JOBS==[x['job_id'] for x in dispatch['submissions']],'four exact development IDs')
 check(dispatch['new_planned_trials']==800 and dispatch['new_completed_trials']==0,'dispatch 800 planned / zero accepted')
 for e in dispatch['submissions']:
  j=next(x for x in registry if str(x['job_id'])==e['job_id'])
  check(j['mode']=='development' and j['suite']==e['suite'] and j['method_ids']==e['method_ids'],'exact registry scientific identity '+e['job_id'])
  check(e['job_id'] not in f0['new_action_development_verified_by_job'],'new dispatch not counted accepted '+e['job_id'])
  check(summary['scheduler']['rows'][e['job_id']]['status']=='RUNNING','recorded snapshot pending terminal '+e['job_id'])
 rows={}
 for line in summary['scheduler']['raw_sacct'].splitlines():
  cols=line.split('|');check(len(cols)==8,'recorded sacct exact8 columns')
  jid,status,exitcode,elapsed,tres,node,name,comment=cols
  check(jid not in rows,'raw accounting ID unique '+jid)
  alloc=dict(x.split('=',1) for x in tres.split(',') if '=' in x)
  gpu=int(alloc.get('gres/gpu','0'));row={'status':status,'exit_code':exitcode,'elapsed_seconds':int(elapsed),'gpus':gpu,'scheduler_name':name,'scheduler_comment':comment,'node':node,'allocation':tres,'job_id':jid}
  rows[jid]=row
 check(rows==summary['scheduler']['rows'],'independently parsed raw sacct exactly matches rows')
 formal=[j for j in registry if j.get('experiment')=='formal_main_v2']
 costs=[{'job_id':str(j['job_id']),'seconds':rows[str(j['job_id'])]['elapsed_seconds'],'gpus':rows[str(j['job_id'])]['gpus'],'GPU_seconds':rows[str(j['job_id'])]['elapsed_seconds']*rows[str(j['job_id'])]['gpus']} for j in formal]
 seconds=sum(x['GPU_seconds'] for x in costs)
 check(seconds==summary['allocated_GPU_seconds']==1966824 and seconds/3600==summary['allocated_GPU_hours']==546.34,'all formal allocations exactly once gives546.34GPUh')
 check(seconds>=before['current_round_cost']['allocated_gpu_seconds'],'cost monotonic')
 check(sum(x['GPU_seconds'] for x in costs if x['job_id']=='3050711')==354,'probe354 seconds included once only')
 queue={}
 for line in summary['scheduler']['raw_squeue'].splitlines():
  jid,status,comment=line.split('|');queue[jid]=(status,comment)
 active=sorted(jid for jid in queue if rows[jid]['gpus']>0)
 check(active==sorted(summary['occupied_job_ids'])==sorted(summary['capacity']['occupied']) and len(active)==6<=8,'raw queue capacity exactly6/8')
 check(not summary['capacity']['unknown'] and not summary['capacity']['findings'],'no capacity unknown/findings')
 check(rows['3034538']['gpus']==0 and rows['3034538']['status']=='RUNNING','controller separate CPU allocation')
 check(summary['owner']['owner_id']==ctl['owner_id'] and summary['owner']['coordinator_job_id']==ctl['controller_job_id']=='3034538','recorded owner bound to unchanged controller')
 check(probe['external_queries']==12 and probe['dummy_control_actions']==120 and probe['policy_control_actions']==0,'bounded probe receipt has12/120/0')
 check(probe['original200_HOLD_unchanged'] and not probe['original_mismatch_reproduced'] and not probe['sealed_values_read'],'probe does not release original200 or final')
 check(summary['Goal256seed17_original200_still_HOLD'] and summary['Goal_probe_cause_undetermined'] and not summary['Object256seed23_bridge_scientifically_admitted'],'downstream blockers retained')
 check(summary['Goal64seed41_machine_nonweights_archived_not_root_accepted'],'machine completion is not root acceptance')
 check(summary['engineering_trials_in_scientific_denominator']==0 and summary['Goal_probe_new_policy_actions']==0,'engineering excluded scientific denominator')
 s=copy.deepcopy(before);f=s['formal_main_progress'];sr=completion['summary'];postref=summary['completed_evidence_post_independent_review'];dindref=summary['dispatch_independent_review']
 entries=copy.deepcopy(dispatch['submissions'])
 for e in entries:e.update(observed_status=rows[e['job_id']]['status'],terminal_review_status='pending_original_raw_consumer_and_independent_review')
 f['nonLong_development_submissions_1530']=entries
 f['root_completed_evidence_integrity_review_20261020T1530']={'status':'passed','independent_review':postref,'accepted_evidence':summary['completed_evidence'],'new_training_groups_accepted':2,'new_development_trials_accepted':600}
 f['Goal_t0_probe_3050711_terminal']={'status':'completed_bounded_engineering_fault_not_reproduced','terminal':summary['Goal_probe_terminal'],'dispatch':ref(B+'/Goal_t0_dispatch/receipt.json'),'GPU_seconds':354,'GPU_cost_already_in_global_total':True,'policy_actions':0,'scientific_release':False,'original200_still_HOLD':True,'cause':'undetermined'}
 f['supervision_integrity_review_20261020T1530']={'status':'pending_final_cross_check','summary':sr,'completed_evidence_post_independent_review':postref,'dispatch_independent_review':dindref,'final_release':False}
 f['parallel_execution']['registered_requested_active_GPU_jobs']=6
 s['current_round_cost'].update(registered_jobs=len(formal),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 s['current_work']=f'66/72 root+independent training,331000 reviewed updates;600 new accepted development,current4400 plus explicit legacyLong600 compatible5000,400 unique initials. Four64 development jobs {JOBS} planned800,0accepted. Goalprobe3050711 completed12query120dummy0policy,fault not reproduced;original200HOLD. Object256s23 bridge unadmitted;Goal64s41 root review pending. 6GPU active,{seconds/3600:.3f}GPUh. Final0/35200sealed.'
 s['next_actions']=[
 'Leave healthy training and four registered64 development jobs to controller and scheduled supervision; no continuous polling or duplicate submission.',
 'At next supervision accept only genuine original consumer and independent terminal receipts; Goal64s41 machine completion is not root completion.',
 'Goal256s17 original200 remainHOLD. Probe3050711 did not reproduce fault and does not clear it; inspect original failing sequence before bounded repair approval.',
 'Object256s23 versioned consumer compatibility candidate is not scientifically admitted; require independent and actual entry/consumer acceptance before deployment.',
 'Preserve Spatial256 B-A+0.333pp CI[-0.667,+1.333],Goal128 negative1.333pp andLong128 negative2.67pp. No tuning,equivalence or unmeasured speed claim.',
 'Keep final35200 and same-checkpoint O2A/components behind registered identity/freeze/release; sealed final values unread.']
 s['next_allowed_action']=s['next_actions'][0]
 for k in ['last_root_supervision_snapshot','last_root_health_check','last_healthy_supervision']:s[k]=sr
 s.update(last_supervision_utc=summary['utc'],updated_utc=summary['utc'],updated_date=datetime.fromisoformat(summary['utc']).astimezone(timezone(timedelta(hours=8))).date().isoformat())
 afterbytes=canon(s)
 check(h(afterbytes)==completion['state_after_sha256'],'independent exact before->after reconstruction matches published SHA')
 check(s['autonomous_training_v1']==before['autonomous_training_v1'] and s['registered_jobs']==before['registered_jobs'],'controller and registry entirely unchanged')
 for k,v in f0.items():
  if k!='parallel_execution':check(f[k]==v,'existing scientific state unchanged '+k)
 p0=copy.deepcopy(f0['parallel_execution']);p1=copy.deepcopy(f['parallel_execution']);p0.pop('registered_requested_active_GPU_jobs',None);p1.pop('registered_requested_active_GPU_jobs',None)
 check(p0==p1,'parallel state only occupied count permitted')
 allowed={'formal_main_progress','current_round_cost','current_work','next_actions','next_allowed_action','last_root_supervision_snapshot','last_root_health_check','last_healthy_supervision','last_supervision_utc','updated_utc','updated_date'}
 for k,v in before.items():
  if k not in allowed:check(s[k]==v,'unchanged protected top '+k)
 actualdiff=diffs(before,s);dump('exact_changed_paths.json',actualdiff)
 check(f['trained_arms']==f0['trained_arms']==68 and f['machine_and_prior_verified_arm_updates']==330000,'machine68/330000 kept distinct and unchanged')
 for k,v in intent['previous_top_fields'].items():check(before.get(k)==v,'intent original top '+k)
 stamp=datetime.fromisoformat(summary['utc']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 brief=f"{stamp}：正式训练已双审66/72组；新增600条开发已验收，当前动作语义4400条、400个唯一初态。四组Spatial/Object64开发已唯一派发800条，尚未终审；当前6个GPU作业，累计546.340GPU小时。Goal探针完成354GPU秒、12次查询/120等待步/0策略动作，未复现原t0差异，原因仍不明，原200条继续HOLD。Object256 seed23来源兼容桥未准入，Goal64 seed41仅机器完成待root终验。最后评测0/35200、封存不变。见[本轮监督](../{B}/summary_after_dispatch.json)。"
 for name,docref in completion['docs'].items():
  data=read(name,docref['sha256']);check(docref['sha256']==intent['documents_after'][name],'document matches intent '+name)
  if name in intent['documents_before']:
   first,sep,rest=data.partition(b'\n');prefix=b'\n'+brief.encode()+b'\n\n';check(rest.startswith(prefix),'only exact brief prepended '+name)
   original=first+sep+rest[len(prefix):];check(h(original)==intent['documents_before'][name],'complete document history preserved '+name)
   put('documents_before/'+Path(name).name,original)
  put('documents_after/'+Path(name).name,data)
 statistics=rd(B+'/Spatial256_root_bootstrap_recomputation.json','30b0e47cf98498d48a84abb119eec376529f4b78c2de0a47fc1db9a66c50a8ba')
 check(statistics['status']=='passed' and statistics['seeds']==[17,23,41] and statistics['bootstrap_repeats']==10000 and statistics['unique_initial_states']==100,'stated Spatial statistics match existing audited bootstrap scope')
 check(round(statistics['means_percent']['A'],3)==98 and round(statistics['means_percent']['B'],3)==98.333 and round(statistics['means_percent']['B_minus_A_pp'],3)==0.333 and [round(x,3) for x in statistics['bootstrap_interval95_pp']['B_minus_A']]==[-0.667,1.333],'stated Spatial point and interval exact rounding')
 read('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
 read('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a')
 check(not summary['scientific_settings_changed'],'no scientific changes claimed')
 # Preserve the prior sealed dispatch package identity, do not modify its inventory.
 read('.local/dispatch_independent_20261020T1530/delivery_manifest.json','f5e19f81c7b074f02598283b1b98a73c9a5050f716db75234e4ca1b1243a90e4')
 put('reconstructed_state_after.json',afterbytes);dump('allocation_cost_recomputation.json',{'registered_formal_allocations':len(formal),'GPU_seconds':seconds,'GPU_hours':seconds/3600,'probe_counted_once':True,'allocations':costs})
 for name in ['final_supervision_intent.json','final_supervision_completion.json','final_supervision_state_before.json','summary_after_dispatch.json']:put('root_evidence/'+name,read(B+'/'+name))
 put('root_evidence/summarize_20261020T1530.py',source)
 report={'schema':'formal_main_v2','kind':'independent_final_summary_transaction_crosscheck','status':'passed','blockers':[],
 'source':intent['source'],'summary':sr,'completion':{'path':B+'/final_supervision_completion.json','sha256':inputs[B+'/final_supervision_completion.json']['sha256']},
 'state_before_sha256':completion['state_before_sha256'],'exact_reconstructed_state_after_sha256':h(afterbytes),
 'root_complete':66,'root_reviewed_updates':331000,'current_accepted_development':4400,'raw_accepted_development':5612,'compatible_development':5000,'unique_initials':400,
 'new_development_planned':800,'new_dispatch_accepted':0,'new_job_ids':JOBS,'recorded_GPU_active_jobs':6,'recorded_GPU_hours':546.34,'probe_GPU_seconds_counted_once':354,
 'controller_registry_and_existing_scientific_state_unchanged':True,'original_Goal200_HOLD_retained':True,'Object_bridge_not_admitted':True,'Goal64seed41_not_root_accepted':True,
 'all_previous_document_bytes_recovered_and_verified':True,'final_release':False,'sealed_values_read':False,'Slurm_or_GPU_poll_performed':False,'new_GPU_jobs':0,'production_writes':0,
 'checks':len(checks),'all_checks_passed':all(c['passed'] for c in checks),
 'limits':['Transaction cross-check reuses prior original-consumer and independent training/development/probe terminal evidence; it is not a new raw GPU or training audit.','Capacity and cost refer to the immutable recorded scheduler snapshot, not a fresh live query.','Controller may advance independently; exact published transaction state was reconstructed, not overwritten or compared to later moving state.','Original Goal mismatch is unreproduced and remains unresolved; no scientific release or retry implied.'],
 'input_hashes':inputs,'changed_paths':actualdiff}
 dump('checks.json',checks);dump('independent_review.json',report)
 print(json.dumps({'status':'passed','checks':len(checks),'report':str(D/'independent_review.json'),'sha256':h((D/'independent_review.json').read_bytes())}))
if __name__=='__main__':
 try:main()
 except Exception as e:
  dump('failed_crosscheck.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'inputs':inputs});raise
