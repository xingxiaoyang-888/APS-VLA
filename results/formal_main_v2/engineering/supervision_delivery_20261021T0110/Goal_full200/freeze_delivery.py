"""Freeze exact server-only candidate and complete CPU originals; no production operations."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,io,json,tarfile
D=Path(__file__).parent;K=D/'package';A=D/'archives';A.mkdir(exist_ok=False)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def write(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def row(p):return {'path':p.relative_to(D).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
for n,status,count in [('CPU_full200_v3','passed_CPU_source_candidate_only',86),('CPU_outer_v3','passed_CPU_outer_contract_and_actual_original_metadata',872),('CPU_consumer_v2','passed_CPU_typed_consumer_components_not_new_terminal',22)]:
 v=json.loads((D/n/'report.json').read_bytes());assert v['status']==status and len(v['checks'])==count and all(c['passed'] for c in v['checks'])
for n in ['CPU_outer_v1','CPU_consumer_v1']:assert json.loads((D/n/'report.json').read_bytes())['status']=='failed'
package=json.loads((K/'package_manifest.json').read_bytes());assert len(package['files'])==10 and all(sha(K/Path(k).name)==v for k,v in package['files'].items())
install=[]
for p in sorted(K.iterdir()):
 assert p.is_file() and not p.is_symlink()
 install.append({'source':p.relative_to(D).as_posix(),'destination':'scripts/ops/formal_goal_full200_gate_v1/'+p.name,'sha256':sha(p),'bytes':p.stat().st_size})
write(D/'install_files.json',{'schema':'formal_main_v2','kind':'goal_full200_exact_private_to_canonical_mapping','production_installed':False,'files':install,'root_and_independent_actual_install_review_required':True})
archives=[]
for directory in sorted(D.glob('CPU_*')):
 assert directory.is_dir() and not directory.is_symlink()
 members=[];files=[]
 for p in sorted(directory.rglob('*')):
  assert not p.is_symlink()
  if p.is_file():
   assert p.suffix not in {'.pt','.pth','.ckpt','.safetensors','.pkl','.pickle','.npy','.npz'}
   assert p.suffix!='.bin' or (len(p.stem)==64 and all(c in '0123456789abcdef' for c in p.stem))
   b=p.read_bytes();members.append({'path':p.relative_to(directory).as_posix(),'sha256':digest(b),'bytes':len(b)});files.append(p)
 archive=A/(directory.name+'.tar.gz')
 with archive.open('xb') as raw:
  with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz:
   with tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as tf:
    for p,m in zip(files,members):
     b=p.read_bytes();assert digest(b)==m['sha256'] and len(b)==m['bytes']
     info=tarfile.TarInfo(m['path']);info.size=len(b);info.mode=0o644;info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';tf.addfile(info,io.BytesIO(b))
 # Read every retained byte from archive, no extraction and no trusted file omission.
 with tarfile.open(archive,'r:gz') as tf:
  ar=tf.getmembers();assert [x.name for x in ar]==[x['path'] for x in members]
  for a,m in zip(ar,members):
   assert a.isfile() and not a.issym() and not a.islnk();b=tf.extractfile(a).read();assert digest(b)==m['sha256'] and len(b)==m['bytes']
 idx=A/(directory.name+'.members.json');write(idx,{'schema':'formal_main_v2','kind':'exact_CPU_raw_archive_members','source_private_directory':str(directory),'scope':'synthetic_CPU_outputs_or_readonly_original_metadata_tests; not science/new GPU','archive':row(archive),'file_count':len(members),'files':members,'originals_retained':True})
 archives.append({'archive':row(archive),'members':row(idx),'file_count':len(members)})
report={'schema':'formal_main_v2','kind':'goal_full200_production_entry_author_candidate','status':'passed_CPU_candidate_with_production_HOLD','reviewed_by':'author','author_agent':'/root/goal_cpu_gate_2054','package_manifest_sha256':sha(K/'package_manifest.json'),'config_sha256':sha(K/'config.json'),'package_files':package['files'],'source_scientific_identity_unchanged':True,'source173_roots_verified':['R','R/snapshots/formal_main_v2_run_564be0995e','P/snapshots/formal_main_v2_run_564be0995e'],'tests':{'original_full200_final':{'report':row(D/'CPU_full200_v3/report.json'),'checks':86},'outer_actual_original_metadata':{'report':row(D/'CPU_outer_v3/report.json'),'checks':872,'rejections':275,'positive_cases':7},'typed_consumer_components':{'report':row(D/'CPU_consumer_v2/report.json'),'checks':22,'rejections':15,'new_actual_terminal_checked':False}},'retained_failures':[row(D/'CPU_outer_v1/report.json'),row(D/'CPU_consumer_v1/report.json')],'archives':archives,'CPU_scope_blockers':[],'production_blockers':['different-agent candidate review and exact root canonical R/P install/closure/readiness not yet performed','native once-only held-submit/pending/ACK/CAS/release adapter requires separate root and independent verification','actual compute-node write/space/exclusive RAW claim and real full200 execution not yet performed','future complete new raw original typed consumer plus independent terminal and root scientific adoption still required'],'production_ready':False,'production_admitted':False,'GPU_execution_authorized':False,'old200_HOLD':True,'old_cause_identified':False,'old_failure_repaired':False,'GPU_submissions':0,'Slurm_queries':0,'state_changes':0,'Git_changes':0,'P_changes':0,'new_scientific_trials':0,'final_release':False}
write(D/'author_report.json',report)
# Delivery manifest includes all source/history and exact archives; loose CPU
# binaries are represented only by the explicit immutable archive member map.
out=[]
for p in sorted(D.rglob('*')):
 if p.is_dir():continue
 assert not p.is_symlink()
 rel=p.relative_to(D).as_posix()
 if rel.split('/')[0].startswith('CPU_'):continue
 assert p.suffix not in {'.bin','.pt','.pth','.ckpt','.safetensors','.pkl','.pickle','.npy','.npz'}
 out.append(row(p))
m={'schema':'formal_main_v2','kind':'goal_full200_author_delivery_manifest','source_root':str(D),'file_count':len(out),'files':out,'CPU_raw_all_in_exact_archives':True,'original_private_CPU_outputs_retained':True,'production_source_file_count':10,'production_installed':False,'scientific_results_added':0,'GPU_submissions':0,'sealed_values_read':False}
write(D/'delivery_manifest.json',m)
print(json.dumps({'manifest':str(D/'delivery_manifest.json'),'manifest_sha256':sha(D/'delivery_manifest.json'),'file_count':len(out),'author_report_sha256':sha(D/'author_report.json'),'package_manifest_sha256':sha(K/'package_manifest.json'),'archives':len(archives),'archive_raw_files':sum(x['file_count'] for x in archives)},sort_keys=True))
