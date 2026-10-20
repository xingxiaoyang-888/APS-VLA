from pathlib import Path
import datetime,gzip,hashlib,json,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_independent_20261020T2054'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json';PIN='1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509'
def h(p):
 z=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):z.update(b)
 return z.hexdigest()
def blob(n):return subprocess.run(['git','show','HEAD:'+n],cwd=R,capture_output=True,check=True).stdout
def ck(ok,msg):
 if not ok:raise ValueError(msg)
snapbytes=(R/SNAP).read_bytes();ck(hashlib.sha256(snapbytes).hexdigest()==PIN,'snapshot hash')
ck(blob(SNAP)==snapbytes,'snapshot already committed')
snap=json.loads(snapbytes);ck(len(snap['files'])==9,'nine files')
codec='scripts/ops/nonweight_archive.py';guard='scripts/ops/check_nonweight_archive_stage.py'
ck(h(R/codec)=='f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2','codec SHA')
ck(h(R/guard)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6','guard SHA')
rows=[];chunks=0
for row in snap['files']:
 mr=row['manifest'];mb=(R/mr['path']).read_bytes()
 ck(len(mb)==mr['bytes'] and hashlib.sha256(mb).hexdigest()==mr['sha256'],'manifest bytes/hash')
 ck(blob(mr['path'])==mb,'manifest committed')
 m=json.loads(mb);ck(m['original_bytes']==row['bytes'] and m['original_sha256']==row['sha256'],'original identity')
 rebuilt=hashlib.sha256();offset=0
 for i,c in enumerate(m['chunks']):
  ck(c['index']==i and c['offset']==offset,'chunk order')
  cb=(R/c['path']).read_bytes();ck(len(cb)==c['compressed_bytes'] and hashlib.sha256(cb).hexdigest()==c['compressed_sha256'],'compressed chunk')
  ck(blob(c['path'])==cb,'chunk committed')
  raw=gzip.decompress(cb);ck(len(raw)==c['raw_bytes'] and hashlib.sha256(raw).hexdigest()==c['raw_sha256'],'raw chunk')
  rebuilt.update(raw);offset+=len(raw);chunks+=1
 ck(offset==row['bytes'] and rebuilt.hexdigest()==row['sha256'],'lossless complete reconstruction')
 ck((R/row['path']).stat().st_size==row['bytes'] and h(R/row['path'])==row['sha256'],'server raw equals reconstruction')
 rows.append({'path':row['path'],'bytes':offset,'sha256':rebuilt.hexdigest(),'chunk_count':len(m['chunks']),'manifest':mr,'raw_server_bytes_equal':True,'all_package_objects_exist_in_HEAD':True,'reconstructed_in_memory_only':True})
out={'schema':'formal_main_v2','kind':'independent_existing_nonweight_package_check','status':'passed_existing_all9_lossless_archives','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot':{'path':SNAP,'sha256':PIN},'files':rows,'file_count':9,'chunk_count':chunks,'total_raw_bytes':sum(v['bytes'] for v in rows),'Git_read_only':True,'production_state_Git_or_Slurm_mutations':False,'sealed_final_values_read':False,'codec':{'path':codec,'sha256':h(R/codec)},'stage_guard':{'path':guard,'sha256':h(R/guard)}}
p=D/'all9_archive_review.json'
with p.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'status':out['status'],'files':9,'chunks':chunks,'raw_bytes':out['total_raw_bytes'],'report':str(p.relative_to(R)),'sha256':h(p)}))
