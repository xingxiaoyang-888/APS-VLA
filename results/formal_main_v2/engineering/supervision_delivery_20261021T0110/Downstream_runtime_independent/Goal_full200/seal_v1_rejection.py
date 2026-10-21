from pathlib import Path
import json,hashlib,tarfile
D=Path(__file__).parent;R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');A=R/'.local/goal_full200_author_20261021T0110'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
report={'schema':'formal_main_v2','kind':'Goal_full200_v1_independent_source_CPU_review','status':'blocked_raw_consumer_integrity','author_manifest_sha256':sha(A/'delivery_manifest.json'),'package_manifest_sha256':sha(D/'package/package_manifest.json'),'production_ready':False,'production_admitted':False,'GPU_execution_authorized':False,'blockers':['non-t0 query before/after arrays can both be erased while v1 raw consumer accepts full200; source guard correction required'], 'confirmed_counterexample':{'path':str((D/'counterexample_v1/blocker.json').relative_to(R)),'sha256':sha(D/'counterexample_v1/blocker.json')},'author_archived_raw_bytes_verified':{'path':str((D/'v1_archive_and_input_verification.json').relative_to(R)),'sha256':sha(D/'v1_archive_and_input_verification.json')},'independent_replayed_tests':[],'state_written':False,'Slurm_queries':0,'new_GPU_jobs':[],'old200_HOLD':True,'final_sealed':True}
for d,n,neg in [('CPU_full200_v3',86,None),('CPU_outer_v3',872,275),('CPU_consumer_v2',22,15)]:
 p=D/d/'report.json';j=json.loads(p.read_bytes());assert len(j['checks'])==n and all(x['passed'] for x in j['checks']);report['independent_replayed_tests'].append({'path':str(p.relative_to(R)),'sha256':sha(p),'checks':n,'negative':neg})
write(D/'v1_independent_review.json',report)
for name in ('CPU_full200_v3','CPU_outer_v3','CPU_consumer_v2','counterexample_v1'):
 root=D/name;members=[];target=D/(name+'.independent.tar.gz')
 with tarfile.open(target,'x:gz',compresslevel=6) as tf:
  for p in sorted(root.rglob('*')):
   if p.is_dir():continue
   assert p.is_file() and not p.is_symlink() and p.resolve()==p
   rel=p.relative_to(root).as_posix();tf.add(p,arcname=rel,recursive=False);members.append({'path':rel,'sha256':sha(p),'bytes':p.stat().st_size})
 write(D/(name+'.independent.members.json'),{'kind':'independent_CPU_not_GPU','file_count':len(members),'files':members,'archive_sha256':sha(target),'archive_bytes':target.stat().st_size})
print(json.dumps({'status':'v1_rejection_and_all_CPU_raw_preserved','review_sha256':sha(D/'v1_independent_review.json')}))
