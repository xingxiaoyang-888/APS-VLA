from pathlib import Path
import argparse,hashlib,json,tarfile
D=Path(__file__).parent

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(8<<20),b''):h.update(x)
 return h.hexdigest()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
p=argparse.ArgumentParser();p.add_argument('--phase',choices=['partial','final'],required=True);args=p.parse_args()
out=D/'archives';out.mkdir(exist_ok=True);rows=[]
names=['replay/CPU_libero_goal_k256_seed23','replay/CPU_libero_goal_k256_seed41','replay/CPU_libero_goal_k64_seed17','replay/CPU_libero_goal_k64_seed23','replay/CPU_libero_goal_k64_seed41','replay/CPU_interfaces_v1','replay/CPU_outer_v2','replay/CPU_consumer_remaining5_v1','replay/CPU_final_interfaces_v5','independent_edge_outputs']
for rel in names:
 src=D/rel
 if rel.startswith('replay/') and not (src/'report.json').exists():
  assert args.phase=='partial';continue
 if rel.startswith('replay/'):
  r=json.loads((src/'report.json').read_bytes());assert r['status'].startswith('passed')
 archive=out/(src.name+'.tar.gz');members=out/(src.name+'.members.json')
 if archive.exists():
  assert members.exists();ms=json.loads(members.read_bytes())['files']
 else:
  ms=[]
  for path in sorted(src.rglob('*')):
   assert not path.is_symlink()
   if path.is_file():ms.append({'path':path.relative_to(src).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
  with tarfile.open(archive,'x:gz',compresslevel=1) as tf:
   for x in ms:tf.add(src/x['path'],arcname=x['path'],recursive=False)
  save(members,{'source_root':str(src),'CPU_fixture_only':True,'files':ms,'file_count':len(ms)})
 # Independent stream reconstruction, compare complete member order and bytes.
 with tarfile.open(archive,'r:gz') as tf:
  actual=tf.getmembers();assert len(actual)==len(ms)
  for a,b in zip(actual,ms):
   assert a.isfile() and a.name==b['path'] and a.size==b['bytes']
   h=hashlib.sha256();stream=tf.extractfile(a)
   for x in iter(lambda:stream.read(8<<20),b''):h.update(x)
   assert h.hexdigest()==b['sha256'] and sha(src/b['path'])==b['sha256']
 rows.append({'source_root':str(src),'archive_path':archive.relative_to(D).as_posix(),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'members_path':members.relative_to(D).as_posix(),'members_sha256':sha(members),'file_count':len(ms),'original_bytes':sum(x['bytes'] for x in ms),'all_members_stream_verified':True})
 print(src.name+' '+str(len(ms))+' verified',flush=True)
save(D/('archive_'+args.phase+'_index.json'),{'status':'passed_private_CPU_archive_reconstruction','phase':args.phase,'CPU_archives':rows,'source_raw_originals_retained':True,'scientific_results_added':0})
