"""Verify frozen package + every archived CPU byte without extraction or mutation."""
from pathlib import Path
import hashlib,json,tarfile
D=Path(__file__).parent
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 m=json.loads((D/'delivery_manifest.json').read_bytes());assert len(m['files'])==m['file_count']
 for r in m['files']:
  p=D/r['path'];assert p.resolve()==p and not p.is_symlink();b=p.read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
 report=json.loads((D/'author_report.json').read_bytes());assert report['status']=='passed_CPU_candidate_with_production_HOLD' and not report['production_ready'] and not report['GPU_execution_authorized']
 rawcount=0
 for a in report['archives']:
  ix=json.loads((D/a['members']['path']).read_bytes());assert ix['file_count']==len(ix['files'])
  with tarfile.open(D/a['archive']['path'],'r:gz') as tf:
   members=tf.getmembers();assert len(members)==len(ix['files'])
   for member,row in zip(members,ix['files']):
    assert member.isfile() and not member.issym() and not member.islnk() and member.name==row['path'];b=tf.extractfile(member).read();assert len(b)==row['bytes'] and sha(b)==row['sha256'];rawcount+=1
 for name,ct in [('CPU_full200_v3',86),('CPU_outer_v3',872),('CPU_consumer_v2',22)]:
  with tarfile.open(D/'archives'/(name+'.tar.gz'),'r:gz') as tf:r=json.loads(tf.extractfile('report.json').read())
  assert len(r['checks'])==ct and all(x['passed'] for x in r['checks'])
 return {'status':'frozen_author_candidate_bytes_verified','delivery_files':m['file_count'],'raw_CPU_files':rawcount,'production_admitted':False,'new_GPU_submissions':0,'old200_HOLD':True}
if __name__=='__main__':print(json.dumps(main(),sort_keys=True))
