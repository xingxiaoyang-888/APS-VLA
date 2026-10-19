"""Restore only byte-identical frozen source path aliases from canonical Git files.
No Slurm/state/GPU/checkpoint/test-value access. Original server provenance is
recorded separately in3043709_source_snapshot_mirror.json; this is reconstruction,
not a claim of new original-server verification.
"""
from pathlib import Path
import argparse,hashlib,json,os
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
PIN='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
MIRROR='snapshots/formal_main_v2_run_564be0995e'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(root,name):
 p=Path(name)
 assert not p.is_absolute() and '..' not in p.parts and '\\' not in name
 full=root/p;assert full.resolve()==full
 assert all(not q.is_symlink() for q in [full,*full.parents] if q==root or root in q.parents)
 return full
def restore(root,verify_only=False):
 root=Path(root).resolve();inv=safe(root,INV);assert digest(inv)==PIN
 rows=json.loads(inv.read_text())['files'];assert len(rows)==173
 prepared=[];existing=0
 for name,pin in sorted(rows.items()):
  source=safe(root,name);dest=safe(root,MIRROR+'/'+name)
  assert source.is_file() and source.suffix in {'.py','.json','.md','.toml','.slurm','.sh','.txt'}
  raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()==pin
  if dest.exists():assert dest.is_file() and digest(dest)==pin;existing+=1
  else:
   assert not verify_only,'Missing expected source mirror: '+str(dest)
   prepared.append((dest,raw,pin))
 for dest,raw,pin in prepared:
  safe(root,dest.relative_to(root).as_posix());dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  assert digest(dest)==pin
 return {'status':'verified_exact_canonical_source_mirror','files':len(rows),'already_present':existing,'new_source_aliases':len(prepared),'original_server_provenance_reverified':False,'weights_or_sealed_values_read':False}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--project-root',type=Path,required=True);parser.add_argument('--verify-only',action='store_true')
 args=parser.parse_args();print(json.dumps(restore(args.project_root,args.verify_only)))
