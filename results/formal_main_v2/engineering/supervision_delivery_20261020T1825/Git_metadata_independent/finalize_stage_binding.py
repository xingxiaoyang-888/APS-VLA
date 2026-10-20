from pathlib import Path
import os,json,hashlib,subprocess,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/git_metadata_audit_20261020T1825'
def h(b):return hashlib.sha256(b).hexdigest()
def save(name,v):
 with (D/name).open('x',encoding='utf-8') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lk:
 fcntl.flock(lk,fcntl.LOCK_SH)
 snap=json.loads((D/'staged_snapshot.json').read_bytes());old=(D/'audit.json').read_bytes();assert h(old)=='72650e4a272f7bef0c64e6ab91309a9ab8335de2ccaf9adb31f6e447bf920210'
 raw=subprocess.run(['git','-c','core.quotepath=false','diff','--cached','--name-only','-z'],cwd=R,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),capture_output=True,check=True).stdout
 assert h(raw)==snap['staged_names_sha256'] and raw.decode().split('\0')[:-1]==snap['staged_paths']
 (D/'audit_before_stage_binding.json').open('xb').write(old)
 v=json.loads(old);v['staged_name_sha256']=h(raw);v['staged_names']=snap['staged_paths']
 (D/'audit.json').write_text(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 src=R/'.local/deliver_20261020T1825_v5.py';assert h(src.read_bytes())=='b62127c200461e96d43394076efffb20ebca11fd03c8ffc940a1ec713c72c8e2'
 save('delivery_v5_source_review.json',{'status':'bounded_archive_logic_reviewed_add_exact_index_binding_before_execution','source':{'path':str(src.relative_to(R)),'sha256':h(src.read_bytes())},'findings':['Exact thirteen A-only files are classified through pinned audit; existing originals retained, tar regular members match original R-relative paths and reread SHA/bytes.','Original required list retained as failure history, separate final list preserves other required evidence and original pinned stage guard.','Before execution, bind audit.staged_name_sha256 and staged_names to actual cached names; for each of thirteen compare git show :path to the reviewed original. Parent accepted and will implement new v6, leaving v5 unchanged.'],'executed':False,'new_helper_code_approval':'v6 still requires exact source confirmation; audit approval covers the bounded metadata operation only.'})
 transport='results/formal_main_v2/control_transport/git_metadata_independent_20261020T1825.jsonl';t=(R/transport).read_bytes();rows=[json.loads(x) for x in t.splitlines()];assert rows[-1]['event']=='control_end' and rows[-1]['returncode']==0
 files=[]
 for p in sorted(D.rglob('*')):
  if p.is_file():files.append({'path':p.relative_to(D).as_posix(),'source':p.relative_to(R).as_posix(),'sha256':h(p.read_bytes()),'bytes':p.stat().st_size})
 save('delivery_manifest.json',{'schema':'formal_main_v2','kind':'independent_metadata_delivery_audit','status':'sealed_complete','files':files,'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'transport_reference':{'path':transport,'sha256':h(t),'bytes':len(t)},'index_mutations':0,'state_mutations':0,'Slurm_writes':0,'GPU_jobs':0,'referenced_payloads_opened':False})
 print(json.dumps({'audit_sha256':h((D/'audit.json').read_bytes()),'manifest_sha256':h((D/'delivery_manifest.json').read_bytes()),'staged_name_sha256':h(raw),'file_count':len(files),'bytes':sum(x['bytes'] for x in files)}))
