"""Read-only original ACK-to-release evidence audit; no scheduler queries or mutations."""
from pathlib import Path
import json,hashlib,sys,os,ast
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/goal_t0_dispatch_independent_20261020T1530';B='results/formal_main_v2/preflight/heartbeat_20261020T2330/Goal_t0_dispatch';J='3050711';PIN='016ddbdc5d638e6271debb124d305dfdd7ccd3ef3d5f9816ac9fe13f4c3a3dda'
checks=[];reads={}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No Slurm/network/process')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  writing=isinstance(args[1],str) and any(x in args[1] for x in 'wax+') or isinstance(args[2],int) and bool(args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
  if writing and D not in p.parents:raise RuntimeError('private writes only')
  if p.suffix in ('.pt','.pth','.bin','.init','.pkl','.pickle','.safetensors') or any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts):raise RuntimeError('No tensors/sealed values')
sys.addaudithook(guard)
def rd(rel,pin=None):
 p=Path(rel);p=p if p.is_absolute() else R/p;b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert pin is None or h==pin;(reads.setdefault(str(p),h));assert reads[str(p)]==h;return b
def js(rel,pin=None):return json.loads(rd(rel,pin))
def ck(name,x):assert x,name;checks.append(name)
def fields(raw):
 out={}
 for x in raw.split():
  if '=' in x:
   k,v=x.split('=',1);assert k not in out;out[k]=v
 return out
rec=js(B+'/receipt.json','cdef52ab3a7fd269aa324e1de99cafacdf662d55559e3c34524a825d714369d4')
job=js(B+'/job_record.json',rec['job_record']['sha256']);intent=js(B+'/reconciliation_intent.json');pending=js(B+'/pending.json','00e8fe4d74ce7615564cbba2a1dfb4922f417ac4c6b0e75a680163d5dcfeb4e5');ack=js(B+'/submission_result.json','5a0dde13a6f15e36c05dae8aa82474a34e304bcc209f29857d53714c65df5a51')
rel=js(B+'/released_identity.json','8e509be60c04fb60517f6ef1a159d5e4e001b9304cb1c64c1ae693beda33b1fc');rc=js(B+'/release_command.json','a5f02be2fb94afa0ec5d933cd07f0a8b26113c2e7f5b1f0b2805f7a94113985c');held0=js(B+'/held_identity.json','b11ab37ac3a9f5b7df4ee7a45e123751731696bebf61b508fd214533f65da7db')
ck('original_single_ack',ack==dict(returncode=0,stderr='',stdout='3050711\n',utc='2026-10-20T15:55:22.667575+00:00'))
ck('pending_preceded_ack',pending['status']=='intent_persisted_before_sbatch' and pending['created_utc']<ack['utc']<intent['utc']<rc['utc']<rel['utc']<rec['utc'])
ck('single_exact_token_bound',pending['request_token']==job['downstream_gateway']['request_token']==rec['request_token']=='cti-goal-t0-probe-v1:'+PIN)
ck('unchanged_sbatch_argv',pending['actual_sbatch_argv']==job['downstream_gateway']['actual_sbatch_argv'])
argv=pending['actual_sbatch_argv'];ck('one_held_norequeue_bounded_gpu_request',argv.count('sbatch')==1 and '--hold' in argv and '--no-requeue' in argv and '--exclude=gpu4020' in argv and '--gres=gpu:l40:1' in argv and '--time=00:30:00' in argv)
for label,raw in [('original_held',held0['stdout']),('reconciled_held',intent['scontrol_held']),('released',rel['stdout'])]:
 f=fields(raw)
 for k,v in dict(JobId=J,JobName='cti-goal-t0-probe',Comment=rec['request_token'],Partition='L40',Requeue='0',Restarts='0',TimeLimit='00:30:00',ExcNodeList='gpu4020',TresPerNode='gres:gpu:l40:1',NumCPUs='7',MinMemoryNode='64G',NumTasks='1',Account='p_p15016',QOS='cpu-500_core-l40-8_card-a800-8_card').items():ck(label+'_'+k,f[k]==v)
 ck(label+'_command',f['Command']==str(P/'results/formal_main_v2/engineering/goal_t0_probe_20261020T1418/source/candidate.slurm') and f['WorkDir']==str(P))
 ck(label+'_held_or_released',f['JobState']=='PENDING' and (f['Reason']=='JobHeldUser' if label!='released' else f['Reason']!='JobHeldUser'))
ck('release_success_confirmed',rc['returncode']==rel['returncode']==0 and not rc['stderr'] and not rel['stderr'])
ck('no_new_submission_during_reconciliation',rec['new_submissions']==0 and rec['kind']=='root_single_engineering_dispatch_exact_ack_reconciliation' and intent['kind']=='exact_ACK_reconciliation_no_new_submission')
ck('all_mode_capacity',intent['capacity']['occupied']==rec['occupied_jobs']==['3043813','3044844',J] and not intent['capacity']['unknown'] and not intent['capacity']['findings'] and rec['maximum_gpu_occupancy']==3)
ck('engineering_only',job['mode']=='engineering' and job['scientific_trials']==0 and not job['final_states_opened'] and not job['automatic_retry'] and job['maximum_attempts']==1 and job['gpus']==1 and job['wall_limit_seconds']==1800 and not rec['scientific_release'] and rec['original200_still_HOLD'] and rec['original_parser_failure_retained'])
rr=js(rec['review']['path'],rec['review']['sha256']);src=rd('.local/reconcile_goal_probe_3050711_20261020T1530.py','b48af39a9c37056ae76da40295c64cff131733c815a11007cf90cd03698e4e3b');ck('review_binds_exact_reconciler',rr['status']=='passed' and rr['entrypoint_sha256']==hashlib.sha256(src).hexdigest() and not rr['blockers'])
for root in [R,P]:rd(root/rec['authorization']['path'],PIN)
ck('reservation_consumed',rec['reserved_GPU_slots']==0 and job['root_reservation']==pending['reservation'])
rd(pending['reservation']['path'],pending['reservation']['sha256'])
journal=rd('results/formal_main_v2/control_transport/heartbeat_20261020T1530_goal_probe_reconcile.jsonl');jr=[json.loads(x) for x in journal.splitlines()];ck('closed_real_transport',jr[-1].get('returncode')==0 or jr[-1].get('exit_code')==0)
statebytes=rd('results/experiment_supervisor/state.json');s=json.loads(statebytes);matches=[j for j in s['registered_jobs'] if str(j['job_id'])==J];ck('exactly_one_current_registry_record',len(matches)==1)
for k in ['stage_key','name','experiment','mode','suite','visual_tokens','training_seed','gpus','source_root','source_sha256','run_root','invocation','invocation_sha256','maximum_attempts','automatic_retry','wall_limit_seconds','scientific_trials','final_states_opened','downstream_gateway','root_reservation','dispatch_review']:ck('current_registry_'+k,matches[0][k]==job[k])
ck('ack_pending_not_left_unresolved',s.get('pending_submission') is None or str(s['pending_submission'].get('job_id'))!=J)
ck('unique_consumed_reservation',sum(str(x.get('job_id'))==J for x in s['autonomous_training_v1']['engineering_probe_reservations_consumed'])==1)
out=dict(schema='formal_main_v2',status='passed_actual_ACK_reconciliation_evidence',entrypoint_sha256=hashlib.sha256(src).hexdigest(),job_id=J,checks=checks,check_count=len(checks),read_evidence=reads,scientific_release=False,actual_GPU_probe_result_reviewed=False,original200_still_HOLD=True,original_parser_failure_retained=True,new_submissions_by_auditor=0,production_modified=False,scheduler_queries_by_auditor=0,state_observation_sha256=hashlib.sha256(statebytes).hexdigest(),limits=['Evidence attests original ACK, registered single identity and scheduler release at recorded times only; not GPU completion or scientific acceptance.','The first dispatcher CPU fixtures missed site scontrol syntax; original failed execution and diagnosis remain in archive.'])
p=D/'actual/actual_reconciliation_review.json';p.write_text(json.dumps(out,sort_keys=True,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(report=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),checks=len(checks))))
