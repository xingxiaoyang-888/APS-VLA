from pathlib import Path
import hashlib,json,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0530';A='results/formal_main_v2/engineering/supervision_delivery_2130/terminal_independent'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archiveTerminal2130ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 prefix='.local/cuda_terminal_independent_2130/';m=R/prefix/'delivery_files.json';assert h(m)=='d88465c314c9b83a205670ec4fccb86d0c188b2c0b154c00c2cdff2f9cc8f30c';v=json.loads(m.read_text());rows=[]
 for row in [*v['files'],dict(path=prefix+'delivery_files.json',sha256=h(m),bytes=m.stat().st_size)]:
  src=row['path'];assert src.startswith(prefix);tail=src[len(prefix):];assert '..' not in Path(tail).parts and not Path(tail).is_absolute()
  p=R/src;q=R/A/tail;assert not p.is_symlink() and h(p)==row['sha256'] and p.stat().st_size==row['bytes']
  assert p.suffix not in ['.pt','.pth','.bin','.safetensors','.pyc','.ckpt'] and p.stat().st_size<100*(1<<20)
  q.parent.mkdir(parents=True,exist_ok=True)
  with q.open('xb') as f:f.write(p.read_bytes())
  assert h(q)==row['sha256'];rows.append(dict(source=src,path=q.relative_to(R).as_posix(),sha256=row['sha256'],bytes=row['bytes']))
 out=B+'/terminal_independent_archive_map.json'
 with (R/out).open('x') as f:json.dump(dict(schema='formal_main_v2',files=rows,originals_retained=True,weights_copied=False,git_identical_blobs_deduplicate=True),f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(status='archived_independent_terminal_package',files=len(rows),bytes=sum(x['bytes'] for x in rows),archive_map=dict(path=out,sha256=h(R/out)))))
