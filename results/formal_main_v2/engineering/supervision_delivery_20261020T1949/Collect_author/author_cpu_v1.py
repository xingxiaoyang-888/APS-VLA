from pathlib import Path
import hashlib,importlib.util,sys,copy,json,time,traceback,os
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/collect_terminal_20261020T1949')
p=D/'checks_v1.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='737ef40d686992a3adb22d872a2cfead6d74492a986dfe712a57e7bf63a5d276'
spec=importlib.util.spec_from_file_location('collect_checks_1949_v1',p);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
O=D/'author_attempt01';O.mkdir(exist_ok=False)
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('author CPU check cannot start commands or network')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes)):
   q=Path(os.fsdecode(p)).absolute();writing=any(x in str(mode or '') for x in 'wax+') or isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
   if writing and O not in q.parents:raise RuntimeError('write outside private author attempt')
   if q.suffix.lower() in ('.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init') or any(x.lower() in ('sealed','sealed_final','checkpoints','weights') for x in q.parts):raise RuntimeError('weight or sealed payload forbidden')
   if q==c.R/'results/experiment_supervisor/state.json':raise RuntimeError('author validation uses only pinned two-job extraction')
sys.addaudithook(guard)
start=time.perf_counter();cpu=time.process_time();rejects=[]
def reject(label,fn):
 try:fn()
 except (ValueError,AssertionError,KeyError,TypeError) as exc:rejects.append({'label':label,'type':type(exc).__name__,'message':str(exc)})
 else:raise AssertionError('negative unexpectedly accepted: '+label)
try:
 value=c.inputs();report=c.inspect_raw(value,c.P)
 j=value['selected_registered_jobs'][0]
 for field,bad in [('mode','final'),('suite','libero_goal'),('job_id','3053440'),('status','FAILED'),('exit_code','1:0'),('elapsed_seconds',362),('gpus',2),('method_ids',['A64s17']),('prior_job_ids',['1']),('resume',True),('run_root',j['run_root']+'/../bad')]:
  m=copy.deepcopy(j);m[field]=bad;reject('job '+field,lambda m=m:c.validate_job(m,m))
 altered=copy.deepcopy(j);altered['source_provenance_sha256']='0'*64;reject('original job binding',lambda:c.validate_job(altered,j))
 state={'task_id':0,'source_state_index':3};item={'phase':'first','control_step':0,'observation_id':'task00:state0003:step0000','arrays':{'path':'first.npz','sha256':'0'*64}}
 for field,bad in [('phase','last'),('control_step',1),('observation_id','task00:state0004:step0000')]:
  m=copy.deepcopy(item);m[field]=bad;reject('observation '+field,lambda m=m:c.check_phase(m,0,'first',state))
 m=copy.deepcopy(item);m['arrays']['path']='../first.npz';reject('NPZ path escape',lambda:c.check_phase(m,0,'first',state))
 arrays={k:c.np.zeros(shape,dtype=dt) for k,(dt,shape) in c.SHAPES.items()}
 c.check_arrays(arrays)
 a=dict(arrays);a['unexpected']=c.np.zeros(1);reject('extra array',lambda:c.check_arrays(a))
 a=dict(arrays);a['robot0_eef_pos']=c.np.zeros(3,dtype='float32');reject('float dtype change',lambda:c.check_arrays(a))
 a=dict(arrays);a['robot0_eef_pos']=c.np.array([float('nan'),0,0]);reject('nonfinite input',lambda:c.check_arrays(a))
 a=dict(arrays);a['robot0_eef_pos']=c.np.zeros(4);reject('proprio shape change',lambda:c.check_arrays(a))
 c.write(O/'raw_validation.json',report)
 c.write(O/'CPU_report.json',dict(status='passed',negative_cases=rejects,negative_count=len(rejects),real_P_output_files=106,real_P_observations=60,real_P_NPZ_bytes=report['total_original_npz_bytes'],root_helper_executed=False,original_root_review_or_consumer_executed=False,private_writes_only=True,new_scientific_trials=0,new_gpu_submissions=0,wall_seconds=time.perf_counter()-start,CPU_seconds=time.process_time()-cpu))
 print(json.dumps({'status':'passed','report':str((O/'raw_validation.json').relative_to(c.R)),'report_sha256':c.sha(O/'raw_validation.json'),'CPU_report_sha256':c.sha(O/'CPU_report.json'),'negative_count':len(rejects),'jobs':[{k:v for k,v in x.items() if k not in ('tasks','dense_identity','checkpoint_metadata','environment')} for x in report['jobs']]}))
except BaseException as exc:
 c.write(O/'failure.json',dict(status='failed_author_check',type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),negative_cases=rejects,wall_seconds=time.perf_counter()-start,CPU_seconds=time.process_time()-cpu,root_helper_executed=False,new_gpu_submissions=0));raise
