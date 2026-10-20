"""Read-only server Git delivery audit. Binding is supplied after verified push."""
from pathlib import Path,PurePosixPath
import hashlib,json,os,re,subprocess,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/final_delivery_independent_1032'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
INV_SHA='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
B='results/formal_main_v2/preflight/heartbeat_20261020T1832/'
ENV=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):
 p=subprocess.run(['git','-c','core.quotePath=false','-C',str(R),*args],env=ENV,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert p.returncode==0,p.stderr.decode(errors='replace')
 return p.stdout
def safe(path):
 p=PurePosixPath(path)
 assert not p.is_absolute() and str(p)==path and '..' not in p.parts and '\\' not in path
 assert not any(x in p.suffixes for x in ['.pt','.pth','.ckpt','.bin','.safetensors','.pkl','.pickle','.h5','.hdf5','.init','.pruned_init'])
 return path
class Tree:
 def __init__(self,commit):
  assert re.fullmatch('[0-9a-f]{40}',commit);self.commit=commit;self.rows={};self.cache={}
  for row in git('ls-tree','-r','-z',commit).split(b'\0'):
   if not row:continue
   head,name=row.split(b'\t',1);mode,typ,oid=head.decode().split();path=name.decode()
   assert mode in ('100644','100755') and typ=='blob'
   self.rows[path]=(mode,oid)
  self.reader=subprocess.Popen(['git','-C',str(R),'cat-file','--batch'],env=ENV,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 def blob(self,path):
  safe(path);assert path in self.rows,path
  if path in self.cache:return self.cache[path]
  oid=self.rows[path][1];self.reader.stdin.write(oid.encode()+b'\n');self.reader.stdin.flush()
  h=self.reader.stdout.readline().decode().strip().split();assert h[:2]==[oid,'blob'];size=int(h[2]);assert size<=100*(1<<20)
  b=self.reader.stdout.read(size);assert len(b)==size and self.reader.stdout.read(1)==b'\n'
  assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid
  if size<=1<<20:self.cache[path]=b
  return b
 def ref(self,ref):
  b=self.blob(ref['path']);assert sha(b)==ref['sha256'],ref['path']
  if 'bytes' in ref:assert len(b)==ref['bytes']
  return b
 def close(self):
  self.reader.stdin.close();tail=self.reader.stdout.read();errors=self.reader.stderr.read();rc=self.reader.wait()
  assert rc==0 and not tail,errors
def audit(cfg):
 started=time.monotonic();commit=cfg['commit'];base=cfg['base_commit']
 assert git('rev-parse','HEAD').decode().strip()==commit
 assert git('diff','--cached','--name-only')==b''
 push_path=R/safe(cfg['verified_push_ref']['path']);push_raw=push_path.read_bytes()
 assert sha(push_raw)==cfg['verified_push_ref']['sha256']
 push=json.loads(push_raw);assert push['operation']=='push'
 assert push['local_head']==push['remote_head_after']==commit and push['remote_head_before']==base
 assert push['credentials_persisted'] is False
 tree=Tree(commit)
 try:
  inv_raw=tree.blob(INV);assert sha(inv_raw)==INV_SHA
  inv=json.loads(inv_raw);assert len(inv['files'])==173
  for path,pin in inv['files'].items():assert sha(tree.blob(path))==pin==sha((R/path).read_bytes()),path
  req_raw=tree.ref(cfg['required_files_ref']);req=json.loads(req_raw)
  assert req['schema']=='cti_nonweight_archive_stage_v1' and req['kind']=='required_files'
  required={r['path']:r for r in req['files']};assert len(required)==len(req['files'])
  for ref in req['files']:tree.ref(ref)
  for ref in cfg['mandatory_refs']:tree.ref(ref)
  rows=git('diff','--name-status','--no-renames','--no-ext-diff','--no-textconv','-z',base,commit).split(b'\0')
  assert rows[-1]==b'' and (len(rows)-1)%2==0
  changes={rows[i+1].decode():rows[i].decode() for i in range(0,len(rows)-1,2)}
  assert all(v in ('A','M') for v in changes.values()),changes
  assert not set(inv['files'])&set(changes)
  assert set(changes)==set(required)|{cfg['required_files_ref']['path']}|set(cfg.get('extra_commit_paths',[]))
  for name in changes:
   safe(name)
   assert Path(name).suffix.lower() not in ('.npz','.npy'),name
  logs=[]
  for ref in cfg['closed_transport_refs']:
   b=tree.ref(ref);events=[json.loads(x) for x in b.splitlines()]
   assert events[0]['event']=='control_start' and events[-1]['event']=='control_end'
   assert events[-1]['source173_and_entrypoint_unchanged'] is True
   logs.append({'path':ref['path'],'sha256':sha(b),'returncode':events[-1]['returncode']})
  archive_files=0
  for ref in cfg['archive_delivery_refs']:
   value=json.loads(tree.ref(ref))
   for row in value['copies']:
    a,s=row['archive'],row['source'];b=tree.ref(a)
    assert sha(b)==s['sha256'] and len(b)==s['bytes']
    archive_files+=1
  acceptance=json.loads(tree.blob(B+'Long22_development_root_acceptance.json'))
  assert acceptance['compatible_development_trials']==2200 and acceptance['unique_initial_state_clusters']==100
  assert acceptance['current_wrapper_actual_trials']==1600 and acceptance['legacy_equivalent_trials']==600
  assert acceptance['final_release'] is False and acceptance['final_state_values_read'] is False
  assert acceptance['full_latency_executed'] is False
  stats=json.loads(tree.blob(B+'Long22_development_statistics.json'))
  assert stats['configuration']['bootstrap_seed']==20261016 and stats['configuration']['bootstrap_repeats']==10000
  assert stats['total_method_instances']==22 and stats['unique_initial_state_clusters']==100
  assert stats['budgets']['128']['mean_B_minus_A']<0 and stats['budgets']['128']['CI95_B_minus_A'][1]<0
  assert all(stats['budgets']['128']['per_seed'][str(s)]['B_minus_A']<0 for s in [17,23,41])
  for ref in [acceptance['independent_statistics'],acceptance['legacy_compatibility_proof'],acceptance['root_statistics']]:tree.ref(ref)
  documents={}
  for path in cfg['doc_paths']:
   text=tree.blob(path).decode();documents[path]={'sha256':sha(text.encode()),'bytes':len(text.encode())}
   assert '开发' in text and ('最终' in text or '封存' in text)
  for ref in cfg['job_delivery_refs']:tree.ref(ref)
  # Assertions refer to committed snapshots only, never the live controller state.
  for item in cfg.get('json_assertions',[]):
   val=json.loads(tree.blob(item['path']))
   for part in item['keys']:val=val[part]
   assert val==item['expected'],item
  assert git('rev-parse','HEAD').decode().strip()==commit
  assert git('diff','--cached','--name-only')==b''
  result={'schema':'formal_main_v2','kind':'independent_exact_commit_delivery_review','status':'passed','commit':commit,'base_commit':base,'verified_push_receipt':cfg['verified_push_ref'],'remote_SHA_scope':'Pinned successful authenticated root push receipt; independent reviewer did not obtain credentials or issue authenticated remote commands.','frozen_source_files_in_commit_and_current_R':173,'required_files':len(required),'changed_paths':len(changes),'archive_copy_files_verified':archive_files,'closed_transport':logs,'new_nonLong_jobs':cfg['new_job_ids'],'job_delivery_refs':cfg['job_delivery_refs'],'Long_development_trials':2200,'Long_unique_initial_states':100,'all_three_seeds_and_primary_negative_preserved':True,'legacy_execution_version_preserved':True,'final_trials':0,'O2A_or_final_result_claimed':False,'documents':documents,'state_Git_Slurm_mutations':False,'credentials_accessed':False,'new_GPU_seconds':0,'CPU_wall_seconds':time.monotonic()-started}
  return result
 finally:tree.close()
