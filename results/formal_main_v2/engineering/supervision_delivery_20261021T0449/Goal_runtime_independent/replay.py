from pathlib import Path
import hashlib,json,subprocess,sys,os,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
S=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e')
D=Path(__file__).parent;A=R/'.local/goal_remaining5_runtime_20261021T0449';Q=D/'replay'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def main():
 pins=json.loads((D/'pinned_inputs.json').read_bytes());assert sha(A/'package/package_manifest.json')==pins['package_manifest_sha256']
 pm=json.loads((A/'package/package_manifest.json').read_bytes());assert len(pm['files'])==20
 for name,pin in pm['files'].items():
  rel=Path(name).relative_to('scripts/ops/formal_goal_remaining5_gate_v1');assert sha(A/'package'/rel)==pin
 inv=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes())['files'];assert len(inv)==173
 for root in [R,S]:assert all(sha(root/k)==v for k,v in inv.items())
 Q.mkdir(exist_ok=False);originals=D/'original_test_sources';originals.mkdir()
 for rel,pin in pins['package_tree'].items():
  src=A/rel;assert src.is_file() and not src.is_symlink() and sha(src)==pin
  dst=Q/rel;dst.parent.mkdir(parents=True,exist_ok=True)
  with dst.open('xb') as f:f.write(src.read_bytes())
 derivations=[]
 for name,pin in pins['tests'].items():
  b=(A/name).read_bytes();assert hashlib.sha256(b).hexdigest()==pin
  with (originals/name).open('xb') as f:f.write(b)
  change=[]
  if name.startswith('cpu_libero_goal_'):
   old=b'R=D.parents[1]';new=b"R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')"
   assert b.count(old)==1;b=b.replace(old,new);change=['Only fixed server inventory root because independent replay is nested; no scientific/test predicates changed']
  with (Q/name).open('xb') as f:f.write(b)
  derivations.append({'name':name,'original_sha256':pin,'replay_sha256':hashlib.sha256(b).hexdigest(),'changes':change})
 save(D/'replay_derivation.json',{'test_sources':derivations,'production_source_bytes_unchanged':True,'CPU_fixtures_only':True})
 executions=[]
 order=['cpu_libero_goal_k256_seed23_v1.py','cpu_libero_goal_k256_seed41_v1.py','cpu_libero_goal_k64_seed17_v1.py','cpu_libero_goal_k64_seed23_v1.py','cpu_libero_goal_k64_seed41_v1.py','cpu_interfaces_v1.py','cpu_outer_v2.py','cpu_raw_consumer_v1.py','cpu_final_interfaces_v5.py']
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
 for name in order:
  print('START '+name,flush=True)
  p=subprocess.run([sys.executable,'-B',str(Q/name)],capture_output=True,env=env)
  with (D/(name+'.stdout')).open('xb') as f:f.write(p.stdout)
  with (D/(name+'.stderr')).open('xb') as f:f.write(p.stderr)
  executions.append({'entry':name,'sha256':sha(Q/name),'returncode':p.returncode,'stdout_sha256':sha(D/(name+'.stdout')),'stderr_sha256':sha(D/(name+'.stderr'))})
  print('DONE '+name+' '+str(p.returncode)+' '+p.stdout.decode(errors='replace')[-1000:],flush=True)
  if p.returncode:break
 for root in [R,S]:assert all(sha(root/k)==v for k,v in inv.items())
 assert all(sha(A/k)==v for k,v in pins['package_tree'].items())
 report={'status':'passed_independent_CPU_replay' if len(executions)==9 and all(x['returncode']==0 for x in executions) else 'failed_independent_CPU_replay','executions':executions,'source173_verified':True,'author_package_unchanged':True,'actual_P_verified':False,'real_GPU_acceptance':False,'GPU_submissions':0,'Slurm_queries':0,'scientific_results_accepted':0}
 save(D/'replay_report.json',report);print(json.dumps(report),flush=True)
 assert report['status']=='passed_independent_CPU_replay'
try:main()
except BaseException as e:
 save(D/'failure.json',{'error':repr(e),'traceback':traceback.format_exc()});raise
