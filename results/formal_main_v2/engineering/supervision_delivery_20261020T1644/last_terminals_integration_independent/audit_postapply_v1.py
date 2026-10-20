from pathlib import Path
import ast,copy,fcntl,hashlib,json,os,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/last_terminal_integration_independent_20261020T1644';O=D/'post';V=R/'.local/last_terminals_integration_preview_20261020T1644';B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0044';S=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e')
CP='293c2d0b5f64ed6a722b33706d5fb63ad7c96c6b03f90a1d015f132557fa67cf';SP='90c214ae6a1e28356823ed26585dd869c8edca1568c54452679ae9a251229422';IP='3a6dff995475283d000a78dbc7fae7f0d5e7d1c48d67712d37138da04e106ade';PP='df89bc8aabb9ec3805276d7dd0a361fcf2ea7e62c158df6a3187ea3c8ce8697f'
start=time.process_time();wall=time.monotonic();checks=[]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('external process or network forbidden')
 if event=='open':
  path=args[0]
  if not isinstance(path,(str,bytes,os.PathLike)):return
  p=Path(path).absolute();mode=args[1];flags=args[2];writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
  if writing and not p.is_relative_to(D):raise RuntimeError('write outside private audit directory')
  if 'sealed' in p.name.lower() or p.suffix=='.pruned_init':raise RuntimeError('sealed state forbidden')
 if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.replace'):
  for arg in args[:2] if event in ('os.rename','os.replace') else args[:1]:
   if isinstance(arg,(str,bytes,os.PathLike)) and not Path(arg).absolute().is_relative_to(D):raise RuntimeError('mutation outside private audit directory')
sys.addaudithook(guard)
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2)+'\n').encode()
def compact(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n').encode()
def hs(b):return hashlib.sha256(b).hexdigest()
def h(p):return hs(p.read_bytes())
def ck(n,b):
 checks.append(dict(name=n,passed=bool(b)))
 if not b:raise AssertionError(n)
def read(p,pin=None):
 raw=p.read_bytes()
 if pin:ck('pin '+p.relative_to(R).as_posix(),hs(raw)==pin)
 return json.loads(raw)
def write(n,v,raw=False):
 p=O/n;assert p.is_relative_to(D);p.parent.mkdir(parents=True,exist_ok=True);b=v if raw else enc(v)
 with p.open('xb') as f:f.write(b)
 return dict(source=p.relative_to(R).as_posix(),path=p.relative_to(D).as_posix(),sha256=hs(b),bytes=len(b))
def diff(x,y,p=()):
 if x==y:return []
 if isinstance(x,dict) and isinstance(y,dict):
  out=[]
  for k in sorted(x.keys()|y.keys()):
   if k not in x:out.append(dict(path=list(p+(k,)),kind='add',after=y[k]))
   elif k not in y:out.append(dict(path=list(p+(k,)),kind='remove',before=x[k]))
   else:out+=diff(x[k],y[k],p+(k,))
  return out
 return [dict(path=list(p),kind='change',before=x,after=y)]
def apply_reviewed_delta(x,y,z):
 if x==y:return copy.deepcopy(z)
 if isinstance(x,dict) and isinstance(y,dict):
  out=copy.deepcopy(z)
  for k in x.keys()-y.keys():ck('removed baseline exact '+k,out[k]==x[k]);del out[k]
  for k in y:
   if k not in x:ck('added field absent '+k,k not in out);out[k]=copy.deepcopy(y[k])
   else:out[k]=apply_reviewed_delta(x[k],y[k],out[k])
  return out
 ck('changed baseline exact',z==x);return copy.deepcopy(y)
def main():
 pre=read(D/'preapply_review.json',PP);ck('preaudit passed',pre['status']=='passed_exact_preview_only_not_applied')
 receipt=read(B/'last_terminals_integration_completion.json',CP);intent=read(B/'last_terminals_integration_intent.json',IP);summary=read(B/'last_terminals_integration.json',SP)
 vb=read(V/'state_before.json',pre['preview']['state_before_sha256']);va=read(V/'state_after.json',pre['preview']['state_after_sha256']);vs=read(V/'summary.json',pre['preview']['summary_sha256']);vi=read(V/'intent.json',pre['preview']['intent_sha256'])
 before_raw=(B/'last_terminals_state_before.json').read_bytes();before=json.loads(before_raw);ck('fresh locked before matches both receipts',hs(before_raw)==intent['state_before_sha256']==receipt['state_before_sha256'])
 ck('source unchanged',intent['source']==vi['source'] and h(R/intent['source']['path'])==intent['source']['sha256'])
 ck('actual summary differs only recorded UTC and current cost',{k:v for k,v in summary.items() if k not in ('utc','allocated_GPU_hours')}=={k:v for k,v in vs.items() if k not in ('utc','allocated_GPU_hours')} and summary['allocated_GPU_hours']==before['current_round_cost']['allocated_gpu_hours'])
 ck('summary exact reference',receipt['summary']==dict(path=(B/'last_terminals_integration.json').relative_to(R).as_posix(),sha256=SP))
 expected=apply_reviewed_delta(vb,va,before);summary_path=receipt['summary']['path'];count=[0]
 def replace_summary(v):
  if isinstance(v,dict):
   if v.get('path')==summary_path and 'sha256' in v:ck('preview summary pin exact before replace',v['sha256']==pre['preview']['summary_sha256']);v['sha256']=SP;count[0]+=1
   for value in v.values():replace_summary(value)
  elif isinstance(v,list):
   for value in v:replace_summary(value)
 replace_summary(expected);ck('all four summary references updated',count[0]==4)
 ck('independent pretty intent hash',hs(enc(expected))==intent['state_after_sha256'])
 ck('independent compact actual writer hash',hs(compact(expected))==receipt['state_after_sha256'])
 controller=R/'scripts/ops/formal_autonomous_training_v1/controller.py';ck('original CAS writer pin',h(controller)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
 ct=ast.parse(controller.read_text());canon=next(n for n in ct.body if isinstance(n,ast.FunctionDef) and n.name=='canonical');ck('actual writer compact encoding confirmed','separators=(\',\', \':\')' in ast.unparse(canon))
 publications=[]
 for p,pin in intent['publications'].items():
  ck('actual published bytes '+p,h(R/p)==pin)
  if p==summary_path:ck('new summary publication exact',pin==SP)
  else:ck('reviewed publication unchanged '+p,pin==vi['publications'][p])
  publications.append(dict(path=p,sha256=pin,bytes=(R/p).stat().st_size))
 ck('exact four publications',len(publications)==4 and set(intent['publications'])==set(vi['publications']))
 ck('registry and allocation preserved in transaction',expected['registered_jobs']==before['registered_jobs'] and expected['current_round_cost']==before['current_round_cost'])
 ck('unchanged unrelated transaction top-level',all(expected[k]==v for k,v in before.items() if k not in ('formal_main_progress','autonomous_training_v1','last_root_supervision_snapshot','current_work','next_actions')))
 ctl=expected['autonomous_training_v1'];oldctl=before['autonomous_training_v1'];ck('owner lease and all unrelated controller fields preserved',all(ctl[k]==v for k,v in oldctl.items() if k not in ('completed_pairs','blocked_pairs')))
 ck('36 complete no blocked, inherited provenance',len(ctl['completed_pairs'])==36 and not ctl['blocked_pairs'] and all(ctl['completed_pairs'][p]['new_machine_review_claimed'] is False for p in ('libero_object_k256_seed23','libero_spatial_k64_seed23','libero_object_k64_seed23')))
 admissions={x['pair']:x for x in summary['controller_completion_admissions']};ck('original blocked retained verbatim',all(admissions[k]['retained_original_block']==v for k,v in oldctl['blocked_pairs'].items()))
 fp=expected['formal_main_progress'];ck('72 full and exact totals',(fp['root_and_independent_completed_arms'],fp['root_and_independent_reviewed_arm_updates'],fp['current_action_development_trial_count'],fp['completed_development_trials'],fp['current_action_development_unique_initial_states'])==(72,360000,5200,6412,400))
 ck('Goal hold final seal and no new GPU',summary['Goal_original200_HOLD'] and summary['all_new_Goal_scientific_HOLD'] and not fp['test_opened'] and not fp['global_release_created'] and fp['completed_final_trials']==0 and receipt['new_GPU_jobs']==0 and '3049679' not in fp['new_action_development_verified_by_job'])
 ck('existing downstream once',sum(str(x['job_id'])=='3052166' for x in expected['registered_jobs'])==1)
 identities=read(D/'selected72_identities.json',pre['actual_selected72_identity_evidence']['sha256'])
 for row in identities['identities']:
  ck('still exact deployment receipt '+row['pair']+row['arm'],h(R/row['deployment_receipt']['path'])==row['deployment_receipt']['sha256'])
  for key in ('root_review','independent_review'):ck('actual canonical original '+row['pair']+row['arm']+key,h(R/row[key]['path'])==row[key]['sha256'])
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lk:
  fcntl.flock(lk,fcntl.LOCK_SH);live_raw=(R/'results/experiment_supervisor/state.json').read_bytes();fcntl.flock(lk,fcntl.LOCK_UN)
 live=json.loads(live_raw);ld=diff(expected,live);allowed={('autonomous_training_v1','allocated_gpu_seconds_observed'),('autonomous_training_v1','last_tick_utc'),('autonomous_training_v1','last_result','completed_pairs'),('autonomous_training_v1','last_result','completed_selectors'),('autonomous_training_v1','last_result','status'),('current_round_cost','allocated_gpu_hours'),('current_round_cost','allocated_gpu_seconds'),('registered_jobs',)}
 ck('post live changes only controller accounting and normal completion',all(tuple(x['path']) in allowed for x in ld))
 lr={str(x['job_id']):x for x in live['registered_jobs']};er={str(x['job_id']):x for x in expected['registered_jobs']};ck('live job identities unchanged',set(lr)==set(er) and len(lr)==len(live['registered_jobs']))
 for jid,row in er.items():
  change=diff(row,lr[jid]);ck('only elapsed observation '+jid,not change or (jid in ('3034538','3052166') and all(x['path']==['elapsed_seconds'] and x['after']>=x['before'] for x in change)))
 delta=sum((lr[j]['elapsed_seconds']-er[j]['elapsed_seconds'])*er[j].get('gpus',0) for j in er);ck('live GPU growth solely registered allocation elapsed',live['current_round_cost']['allocated_gpu_seconds']==expected['current_round_cost']['allocated_gpu_seconds']+delta and live['current_round_cost']['allocated_gpu_hours']==live['current_round_cost']['allocated_gpu_seconds']/3600 and live['autonomous_training_v1']['allocated_gpu_seconds_observed']==live['current_round_cost']['allocated_gpu_seconds'])
 result=live['autonomous_training_v1']['last_result'];ck('observed normal completion no failure claim',result in (expected['autonomous_training_v1']['last_result'],dict(completed_pairs=36,completed_selectors=72,status='training_matrix_complete')))
 frozen=read(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')['files'];ck('173 frozen unchanged R and S',len(frozen)==173 and all(h(base/p)==pin for base in (R,S) for p,pin in frozen.items()))
 state_ref=write('independently_reconstructed_transaction_state.json',compact(expected),True);live_ref=write('live_readonly_snapshot.json',live_raw,True);diff_ref=write('exact_actual_transaction_diff.json',dict(changes=diff(before,expected),post_controller_observation_changes=ld,transaction_GPU_cost_delta=0,subsequent_GPU_observed_delta=delta))
 report=dict(schema='formal_main_v2',kind='independent_last_terminals_postapply_review',status='passed_actual_transaction_and_publication',root_completion=dict(path=(B/'last_terminals_integration_completion.json').relative_to(R).as_posix(),sha256=CP),summary=dict(path=summary_path,sha256=SP),intent=dict(path=(B/'last_terminals_integration_intent.json').relative_to(R).as_posix(),sha256=IP),preapply_review=dict(source=(D/'preapply_review.json').relative_to(R).as_posix(),sha256=PP),actual_before_sha256=hs(before_raw),actual_after_compact_sha256=hs(compact(expected)),intent_after_pretty_sha256=hs(enc(expected)),encoding_note='The unchanged controller atomic_json writes compact canonical JSON, while root candidate intent hashes indented JSON. Independent reconstruction matches both exact byte identities.',publications=publications,transaction_state=state_ref,live_snapshot=live_ref,exact_diff=diff_ref,checks=checks,check_count=len(checks),training_arms=72,reviewed_updates=360000,current_development=5200,compatible_development=5800,historical_development=6412,unique_initial_states=400,final_trials=0,Goal_original200_HOLD=True,new_Goal_science_HOLD=True,controller_observed_last_result=result,controller_training_complete_is_normal=True,no_controller_restart_performed=True,existing_3052166_single_registration=True,new_GPU_jobs=0,production_state_written=False,Git_or_Slurm_calls=0,CPU_seconds=time.process_time()-start,wall_seconds=time.monotonic()-wall,limits='Readonly audit; observed training_matrix_complete is a controller state result, not an independent Slurm exit-status claim. No scientific release, Goal admission, or new GPU execution authorized.')
 print(json.dumps(dict(report=write('postapply_review.json',report),checks=len(checks),CPU_seconds=report['CPU_seconds'])))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('failure_v1.json',dict(status='post_review_failed',error=str(e),type=type(e).__name__,traceback=traceback.format_exc(),checks=checks,CPU_seconds=time.process_time()-start));raise
