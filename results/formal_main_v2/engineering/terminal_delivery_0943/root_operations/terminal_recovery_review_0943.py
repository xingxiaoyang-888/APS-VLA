from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def write(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return {'path':rel,'sha256':sha(p)}
def ref(p):
 p=Path(p);return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_recovery_io_controller')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';state_sha=sha(statepath);s=json.loads(statepath.read_text())
 prior=json.loads((R/(B+'/initial_observation.json')).read_text())
 independently_completed=[k for k,v in s['formal_main_progress']['completed_training_pairs'].items() if v.get('independent_review') and v.get('root_review')]
 write(B+'/initial_observation_count_correction.json',{'original':ref(R/(B+'/initial_observation.json')),'field':'root_independent_completed_arms','original_value':prior['root_independent_completed_arms'],'corrected_value':2*len(independently_completed),'reason':'completed_training_pairs includes machine-only entries; require explicit original root_review and independent_review, not dictionary length.','root_independent_pair_keys':independently_completed,'scientific_raw_data_changed':False})
 jobs={str(j['job_id']):j for j in s['registered_jobs']};j=jobs['3039258']
 assert j['status']=='COMPLETED' and j['exit_code']=='0:0' and j['elapsed_seconds']==6512
 cmd=['sacct','-n','-X','-P','-j','3039258','--format=JobIDRaw,State,ExitCode,ElapsedRaw,AllocTRES,JobName,WorkDir%256']
 run=subprocess.run(cmd,capture_output=True,text=True,check=True)
 rows=[x.split('|') for x in run.stdout.splitlines() if x.strip()]
 assert len(rows)==1 and rows[0][:4]==['3039258','COMPLETED','0:0','6512'] and rows[0][-1].strip()==str(R) and rows[0][-2]=='cti-formal'
 wrapper=R/'scripts/server/formal_asset_main.slurm'
 assert sha(wrapper)=='9d54e0486a078a8358c8443bb92db8c8096d9ac3988eff693fa69b250d97c36a'
 assert sha(P/'scripts/server/formal_asset_main.slurm')==sha(wrapper)
 text=wrapper.read_text();assert '#SBATCH --output=results/slurm/%x_%j.out' in text and '#SBATCH --error=results/slurm/%x_%j.err' in text
 mirrored=[]
 for ext in ['out','err']:
  rel='results/slurm/cti-formal_3039258.'+ext;source=R/rel;dest=P/rel
  assert source.is_file() and not source.is_symlink() and not dest.exists()
  st=source.stat();data=source.read_bytes();assert source.stat()==st
  with dest.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  assert sha(dest)==hashlib.sha256(data).hexdigest() and source.stat()==st
  mirrored.append({'source':str(source),'destination':str(dest),'bytes':len(data),'sha256':sha(dest),'source_retained':True})
 mirror=write(B+'/3039258_slurm_log_server_mirror.json',{'utc':datetime.now(timezone.utc).isoformat(),'actual_sacct_argv':cmd,'actual_sacct_stdout':run.stdout,'job_id':'3039258','terminal':True,'source_derivation':'Actual sacct WorkDir R plus immutable submitted SBATCH relative output/error directives and exact job name/id.','scontrol_after_purge_unavailable':True,'sacct_StdOut_field_unsupported':True,'slurm_wrapper':ref(wrapper),'mirrored':mirrored,'raw_bytes_changed':False,'windows_files_written':False})
 pull=mod('scripts/pull_formal_results.py','b1b141ddb75fd8641d6f5e7f68dbfea462e1fe907ced2f2a98338a1145d77061','root_recovery_puller')
 report,path=pull.pull(['3028460','3039258'],timeout=300)
 assert report['status']=='verified_nonweight_snapshot' and not report['missing']
 pr=ref(path);write(B+'/cuda_recovery_pull_v2.json',{'pull':pr,'mirror':mirror,'files':len(report['files'])})
 reviewer=mod('.local/cuda_terminal_review_0943/review_formal_segment_startup.py','9ba2535e4a2d19ebf733aa12872a4be54573341f7a718ba86c654efec0d088dd','root_cuda_reviewer_candidate_0943')
 inv='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
 result=reviewer.review('3039258',source_inventory=inv,pull_receipt=pr['path'],verify_server_resume=False,root=R)
 assert result['status']=='local_passed_remote_required' and result['completed_by_arm']=={'A':500,'B':500}
 cr=write('.local/cuda_terminal_review_0943/actual_local_review.json',result)
 print(json.dumps({'CUDA_candidate_local_review':cr,'pull':pr,'publication_pending_independent_source_review':True}),flush=True)
 complete=s['autonomous_training_v1']['completed_pairs']['libero_object_k256_seed41'];out=json.loads((R/complete['machine_output']['path']).read_text())
 assert sha(R/complete['machine_output']['path'])==complete['machine_output']['sha256']
 candidates=[]
 for x in out['evidence_refs']:
  if x['path'].startswith('results/formal_main_v2/pulls/') and x['path'].endswith('/receipt.json'):
   v=json.loads((R/x['path']).read_text())
   if '3034570' in {str(q['job_id']) for q in v['selected_jobs']}:
    assert sha(R/x['path'])==x['sha256'];candidates.append(x)
 assert len(candidates)==1
 normal=mod('scripts/review_formal_segment.py','566408f7f72bd3d878204175573a9c08b01db67be69358ed4a8ac2d0e0603790','root_normal_reviewer_0943')
 result=normal.review('3034570',source_inventory=inv,pull_receipt=candidates[0]['path'],verify_server_resume=True,root=R)
 assert result['completed_by_arm']=={'A':5000,'B':5000}
 rp=R/result['output_relative']/'segment_reviews/3034570.json';checks=[]
 pairroot=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_object/k256/seed41')
 for arm in ['A','B']:
  receipt=json.loads((R/result['output_relative']/arm/'deployment_receipt.json').read_text())
  assert receipt['training_complete'] and receipt['completed_updates']==5000
  assert [e['update'] for e in receipt['evaluations']]==list(range(0,5001,500))
  target=pairroot/arm/'best.pt';st=target.stat();digest=c.file_sha(target)
  assert digest==receipt['checkpoint_sha256'] and st==target.stat()
  checks.append({'arm':arm,'path':str(target),'sha256':digest,'bytes':st.st_size,'selected_update':receipt.get('selected_update'),'validation_metric':receipt.get('validation_metric')})
 sr=write(B+'/3034570_selected_server.json',{'status':'verified_actual_server_bytes','job_id':'3034570','root_review':ref(rp),'checks':checks,'weights_copied':False,'optimizer_rng_deserialized':False})
 write(B+'/3034570_root_terminal.json',{'root_review':ref(rp),'selected_server':sr,'machine_original_outcome':complete['machine_output'],'pull':candidates[0],'completed_by_arm':result['completed_by_arm'],'pair_allocated_GPU_seconds':result['pair_allocated_gpu_seconds'],'independent_review_pending':True})
 assert sha(statepath)==state_sha
 print(json.dumps({'normal_root_review':ref(rp),'selected':sr,'state_unchanged':True}),flush=True)
