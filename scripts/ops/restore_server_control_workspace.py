from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,os
ROOT=Path(__file__).resolve().parents[2]
PRE='results/formal_main_v2/preflight/server_storage_migration_20261019'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def safe(rel):
 p=PurePosixPath(rel)
 assert not p.is_absolute() and '..' not in p.parts and str(p)==rel,rel
 dest=ROOT.joinpath(*p.parts)
 assert ROOT.resolve() in dest.resolve().parents,rel
 return dest
def restore():
 inventory=json.loads((ROOT/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes())
 for rel,h in inventory['files'].items():assert sha(safe(rel))==h,rel
 batch=json.loads((ROOT/'results/formal_main_v2/preflight/parallel_review_batch_20261018T0840.json').read_bytes())
 rows=[dict(source=k,archive=v['path'],sha256=v['sha256'],bytes=v['bytes']) for k,v in batch['audit_source_archive_map'].items()]
 rows+=json.loads((ROOT/'results/experiment_supervisor/handoff_20261018T1417.json').read_bytes())['source_archive']
 extras={
 '.local/review_selected_pair_server.py':'results/formal_main_v2/preflight/parallel_review_batch_20261018T0626tail_sources/052_review_selected_pair_server.py.txt',
 '.local/reconcile_parallel_progress_20261018.py':'results/formal_main_v2/preflight/parallel_review_batch_20261018T0626tail_sources/050_reconcile_parallel_progress_20261018.py.txt',
 '.local/fill_fresh_spatial_pair_0452.py':'results/formal_main_v2/preflight/parallel_review_batch_20261018T0626tail_sources/044_fill_fresh_spatial_pair_0452.py.txt',
 '.local/fill_fresh_formal_asset_pair_0826.py':'results/formal_main_v2/preflight/fill_fresh_formal_asset_pair_0826.py.txt',
 '.local/scheduler_node_exclusion_0840/adapter.py':'results/formal_main_v2/engineering/node_exclusion_v1/scheduler_node_exclusion_0840/adapter.py'}
 for src,arc in extras.items():rows.append(dict(source=src,archive=arc,sha256=sha(safe(arc)),bytes=safe(arc).stat().st_size))
 for row in json.loads(safe(PRE+'/inputs/manifest.json').read_bytes()):
  rows.append(dict(source=row['source'],archive=PRE+'/inputs/'+row['archive_name'],sha256=row['sha256'],bytes=row['bytes']))
 seen={}
 for row in rows:
  assert row['source'] not in seen or seen[row['source']]==row['sha256']
  seen[row['source']]=row['sha256']
  src=safe(row['archive']);dest=safe(row['source'])
  assert src.stat().st_size==row['bytes'] and sha(src)==row['sha256'],row['archive']
  if dest.exists():assert sha(dest)==row['sha256'],row['source']
  else:
   assert row['source'].startswith('.local/') or row['source']=='results/formal_main_v2/preflight/disk_compression_20261018T1421.json',row['source']
   dest.parent.mkdir(parents=True,exist_ok=True)
   with dest.open('xb') as h:h.write(src.read_bytes());h.flush();os.fsync(h.fileno())
  assert sha(dest)==row['sha256'],row['source']
 codec=ROOT/'scripts/ops/nonweight_archive.py'
 assert sha(codec)=='f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2'
 snap='results/formal_main_v2/nonweight_archives/v1/snapshots/long_dev600_20261018.json'
 cmd=[sys.executable,'-B',str(codec),'restore','--project-root',str(ROOT),'--snapshot',snap,'--snapshot-sha256','ac7e4dce68abeddb147dd412f83afffbc5041715868547d6f60811e5fca137f0']
 p=subprocess.run(cmd,capture_output=True,text=True)
 assert p.returncode==0,p.stderr
 raw=json.loads(p.stdout)
 for rel,h in inventory['files'].items():assert sha(safe(rel))==h,rel
 receipt=dict(schema='server_control_workspace_restore_v1',utc=datetime.now(timezone.utc).isoformat(),status='passed',root=str(ROOT),mapped_paths=len(seen),frozen_sources_verified=len(inventory['files']),restored_files=[dict(source=k,sha256=v) for k,v in seen.items()],raw_archive=raw,synthetic_inputs_are_CPU_only_not_real_registration=True,submitted_jobs=0,opened_final_states=False)
 receipt_path=safe(PRE+'/restore_receipt.json')
 if not receipt_path.exists():receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in receipt.items() if k not in ('restored_files','raw_archive')},ensure_ascii=False))
if __name__=='__main__':restore()
