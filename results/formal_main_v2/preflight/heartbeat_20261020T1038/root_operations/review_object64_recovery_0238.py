from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261020T1038'
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
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_recovery_0238_controller')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';state_sha=sha(statepath);s=json.loads(statepath.read_text())
 jobs={str(j['job_id']):j for j in s['registered_jobs']};j=jobs['3044017']
 assert j['status']=='COMPLETED' and j['exit_code']=='0:0' and j['elapsed_seconds']==5141
 cmd=['sacct','-n','-X','-P','-j','3044017','--format=JobIDRaw,State,ExitCode,ElapsedRaw,AllocTRES,JobName,WorkDir%256']
 run=subprocess.run(cmd,capture_output=True,text=True,check=True)
 rows=[x.split('|') for x in run.stdout.splitlines() if x.strip()]
 assert len(rows)==1 and rows[0][:4]==['3044017','COMPLETED','0:0','5141'] and rows[0][-1].strip()==str(R) and rows[0][-2]=='cti-formal'
 wrapper=R/'scripts/server/formal_asset_main.slurm'
 assert sha(wrapper)=='9d54e0486a078a8358c8443bb92db8c8096d9ac3988eff693fa69b250d97c36a'
 assert sha(P/'scripts/server/formal_asset_main.slurm')==sha(wrapper)
 text=wrapper.read_text();assert '#SBATCH --output=results/slurm/%x_%j.out' in text and '#SBATCH --error=results/slurm/%x_%j.err' in text
 mirrored=[]
 for ext in ['out','err']:
  rel='results/slurm/cti-formal_3044017.'+ext;source=R/rel;dest=P/rel
  assert source.is_file() and not source.is_symlink() and not dest.is_symlink()
  st=source.stat();data=source.read_bytes();assert source.stat()==st
  if dest.exists():assert dest.read_bytes()==data
  else:
   with dest.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  assert sha(dest)==hashlib.sha256(data).hexdigest() and source.stat()==st
  mirrored.append({'source':str(source),'destination':str(dest),'bytes':len(data),'sha256':sha(dest),'source_retained':True})
 mirror=write(B+'/3044017_slurm_log_server_mirror.json',{'utc':datetime.now(timezone.utc).isoformat(),'actual_sacct_argv':cmd,'actual_sacct_stdout':run.stdout,'job_id':'3044017','terminal':True,'source_derivation':'Actual sacct WorkDir R plus immutable submitted SBATCH relative output/error directives and exact job name/id.','slurm_wrapper':ref(wrapper),'mirrored':mirrored,'raw_bytes_changed':False,'windows_files_written':False})
 pull=mod('scripts/pull_formal_results.py','b1b141ddb75fd8641d6f5e7f68dbfea462e1fe907ced2f2a98338a1145d77061','root_recovery_0238_puller')
 report,path=pull.pull(['3028468','3044017'],timeout=300)
 assert report['status']=='verified_nonweight_snapshot' and not report['missing']
 pr=ref(path);write(B+'/cuda_recovery_pull.json',{'pull':pr,'mirror':mirror,'files':len(report['files'])})
 print(json.dumps({'pull':pr,'files':len(report['files'])}),flush=True)
 indpath=R/'.local/cuda_recovery_independent_0943/ownership_patch_independent_review.json'
 assert sha(indpath)=='edff54b1d4ff8ace87251378b882190155f7db5b26bf09bf5e360c0bec34abba'
 ind=json.loads(indpath.read_text());assert ind['status']=='passed_CPU_review' and ind['tests']['final_passed']==33 and ind['tests']['final_failed']==0
 assert sha(R/'scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py')=='c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480'
 reviewer=mod('scripts/formal_cuda_terminal_review_v1/review_formal_segment_startup.py','ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4','root_cuda_reviewer_0238')
 result=reviewer.review('3044017',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',pull_receipt=pr['path'],verify_server_resume=True,root=R)
 assert result['status']=='passed' and result['completed_by_arm']=={'A':500,'B':500} and result['pair_allocated_gpu_seconds']==5210
 rr=ref(R/result['output_relative']/'segment_reviews/3044017.json')
 summary=write(B+'/3044017_root_terminal.json',{'root_review':rr,'source_correction_independent':ref(indpath),'pull':pr,'completed_by_arm':result['completed_by_arm'],'original_target_500_recovered':True,'initial_resume_update':0,'initial_sample_cursor':0,'new_sample_cursor':4000,'checkpoint_contents_deserialized':False,'resume_file_hashes_verified':True,'frozen_core_revalidates_optimizer_RNG_cursor_on_next_resume':True,'continuous_5000_admitted':False,'failed_records_retained':True,'failed_GPU_seconds':69,'recovery_GPU_seconds':5141,'pair_GPU_seconds':5210,'new_GPU_jobs':0,'independent_actual_terminal_review_pending':True})
 assert sha(statepath)==state_sha
 print(json.dumps({'root_review':rr,'summary':summary,'state_unchanged':True}),flush=True)
