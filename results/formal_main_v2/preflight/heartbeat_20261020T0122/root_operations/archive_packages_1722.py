from pathlib import Path
import hashlib,json,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261020T0122'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
groups=[
 ('long_candidate','.local/long_development_1722/final_delivery_files.json','8801e3fe823d90354287d3b9e7731e9853d1f9a3a82c768656effdeefda94cdc',''),
 ('delivery_gap','.local/delivery_gap_1722/archive_closure.json','93b2ffc66036767f276bc4edd2ca2dd563b56755818fe8903e0c07715a4801ab','.local/delivery_gap_1722'),
 ('canonical_requests','.local/canonical_review_alias_1722/archive_closure.json','9f17c41ee89dea26f38d3c3524872f23f5f3bfa27da9e54345cad7711df2030d','.local/canonical_review_alias_1722')]
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archive1722ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
out=[]
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 for name,index,pin,base in groups:
  p=R/index;assert h(p)==pin
  rows=json.loads(p.read_text())['files'];assert isinstance(rows,list)
  rows=rows+[dict(path=Path(index).name if base else index,sha256=pin,bytes=p.stat().st_size)]
  files=[]
  for row in rows:
   rel=(Path(base)/row['path']).as_posix() if base else row['path']
   src=R/rel;assert R in src.parents and '..' not in src.parts and not src.is_symlink()
   assert not set(src.parts)&{'.git','__pycache__','.pytest_cache'} and src.suffix not in {'.pt','.pth','.safetensors','.bin','.ckpt','.npy','.npz'}
   assert src.is_file() and h(src)==row['sha256'] and src.stat().st_size==row['bytes'] and row['bytes']<100*(1<<20)
   mapped=rel.removeprefix('.local/') if not base else row['path'];dst=B/'packages'/name/mapped
   assert B in dst.parents and not dst.is_symlink();dst.parent.mkdir(parents=True,exist_ok=True)
   if dst.exists():assert h(dst)==row['sha256']
   else:
    with dst.open('xb') as f:f.write(src.read_bytes())
   assert h(dst)==row['sha256']
   files.append(dict(source=rel,path=dst.relative_to(R).as_posix(),sha256=h(dst),bytes=dst.stat().st_size))
  out.append(dict(package=name,source_manifest=dict(path=index,sha256=pin),files=files))
 p=B/'package_delivery_first.json'
 with p.open('x') as f:json.dump(dict(schema='formal_main_v2',packages=out,source_bytes_preserved=True,weights_copied=False,failed_attempts_retained=True),f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(path=p.relative_to(R).as_posix(),sha256=h(p),packages=len(out),files=sum(len(x['files']) for x in out))))
