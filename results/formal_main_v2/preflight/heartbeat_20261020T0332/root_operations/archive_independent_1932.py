from pathlib import Path
import hashlib,json,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0332';ARCH='results/formal_main_v2/engineering/terminal_delivery_1932'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cp(n,out,pin):
 p=R/n;q=R/out;assert h(p)==pin and not p.is_symlink();q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as f:f.write(p.read_bytes())
 assert h(q)==pin;return dict(source=n,path=out,sha256=pin,bytes=q.stat().st_size)
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('archive_ind1932_ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 man='.local/terminal_independent_1932/delivery_files.json';assert h(R/man)=='bc084498e36190adf4a2aef7446e5e017a0b264465aa16650d7a5a61a8241f8e';v=json.loads((R/man).read_text());rows=[]
 for row in v['files']:
  src=row['path'];assert src.startswith('.local/terminal_independent_1932/');assert (R/src).stat().st_size==row['bytes']
  rows.append(cp(src,ARCH+'/independent/'+Path(src).name,row['sha256']))
 rows.append(cp(man,ARCH+'/independent/delivery_files.json',h(R/man)))
 target='results/formal_main_v2/libero_object/k64/seed17/training/segment_reviews/3037054_independent.json'
 rows.append(cp('.local/terminal_independent_1932/3037054_independent_review.json',target,'f14b26c65a7a337dd629d2ae87ca10d94e9ad31d96dffcfb0e6cbf39188fefd7'))
 with (R/B/'terminal_independent_archive_map.json').open('x') as f:json.dump(dict(schema='formal_main_v2',files=rows,originals_retained=True,weights_copied=False),f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(status='independent_receipt_archived',files=len(rows),path=target,sha256=h(R/target))))
