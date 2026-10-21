"""Verify the immutable CPU delivery or replay only in one fresh direct R/.local child."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,shutil,subprocess,sys,tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=Path(__file__).parent
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def check(ok,msg):
 if not ok:raise ValueError(msg)
def main():
 a=argparse.ArgumentParser();a.add_argument('--manifest-sha256',required=True);a.add_argument('--replay-to',type=Path);args=a.parse_args()
 m=D/'delivery_manifest.json';check(sha(m)==args.manifest_sha256,'exact delivery manifest');manifest=json.loads(m.read_bytes())
 check(manifest['source_root']==str(D),'exact original source root')
 for row in manifest['files']:
  rel=PurePosixPath(row['path']);check(not rel.is_absolute() and '..' not in rel.parts,'safe delivery member');p=D/rel
  check(p.resolve()==p and p.is_file() and not p.is_symlink(),'real delivery file')
  check(p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'original bytes differ: '+str(rel))
 check(len(manifest['files'])==manifest['file_count'],'manifest count')
 for record in manifest['CPU_archives']:
  members=json.loads((D/record['members_path']).read_bytes())['files']
  with tarfile.open(D/record['archive_path'],'r:gz') as tf:
   actual=tf.getmembers();check(len(actual)==len(members),'archive count')
   for info,row in zip(actual,members):
    check(info.isfile() and info.name==row['path'] and info.size==row['bytes'],'archive exact member identity')
    stream=tf.extractfile(info);h=hashlib.sha256()
    for b in iter(lambda:stream.read(8<<20),b''):h.update(b)
    check(h.hexdigest()==row['sha256'],'archive original bytes')
 if args.replay_to is None:
  print(json.dumps({'status':'passed_frozen_bytes_and_all_CPU_archive_members','file_count':manifest['file_count'],'GPU_submissions':0}));return
 target=args.replay_to
 check(target.is_absolute() and target.resolve()==target and target.parent==R/'.local' and target.name.startswith('goal_remaining5_replay_'),'fresh private direct child required')
 check(not target.exists() and target!=D,'no replay overwrite')
 target.mkdir()
 # The production package remains untouched. Tests execute identical bytes with __file__ in this private child.
 for row in manifest['files']:
  rel=Path(row['path'])
  if rel.parts[0]=='package' or (len(rel.parts)==1 and rel.name.startswith('cpu_') and rel.suffix=='.py'):
   dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True)
   with dst.open('xb') as f:f.write((D/rel).read_bytes())
 tests=['cpu_libero_goal_k256_seed23_v1.py','cpu_libero_goal_k256_seed41_v1.py','cpu_libero_goal_k64_seed17_v1.py','cpu_libero_goal_k64_seed23_v1.py','cpu_libero_goal_k64_seed41_v1.py','cpu_interfaces_v1.py','cpu_outer_v2.py','cpu_raw_consumer_v1.py','cpu_final_interfaces_v5.py']
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
 executions=[]
 for name in tests:
  p=subprocess.run([sys.executable,'-B',str(target/name)],capture_output=True,env=env)
  (target/(name+'.stdout')).write_bytes(p.stdout);(target/(name+'.stderr')).write_bytes(p.stderr)
  executions.append({'entry':name,'sha256':sha(target/name),'returncode':p.returncode})
  if p.returncode:break
 report={'status':'passed_CPU_replay' if len(executions)==len(tests) and all(v['returncode']==0 for v in executions) else 'failed_CPU_replay','executions':executions,'new_GPU_submissions':0,'production_writes':0,'actual_P_or_GPU_verification':False}
 (target/'replay_result.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
 print(json.dumps(report))
 check(report['status']=='passed_CPU_replay','replay failure preserved')
if __name__=='__main__':main()
