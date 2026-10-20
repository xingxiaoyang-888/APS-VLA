from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0349';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1949'
ALLOWED={'.local/k64_seed23_bridges_20261020T1949':'K64_bridges_author','.local/k64_seed23_bridges_independent_20261020T1949':'K64_bridges_independent','.local/collect_terminal_20261020T1949/development_gateway':'K64_gateway_author','.local/git_delivery_audit_20261020T1949':'Git_delivery_independent'}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_bytes())
def cp(p,q,pin,size):
 assert p.resolve()==p and q.resolve()==q and not any(x.is_symlink() for x in [p,*p.parents,q,*q.parents]);assert h(p)==pin and p.stat().st_size==size and p.is_file();q.parent.mkdir(parents=True,exist_ok=True)
 if q.exists():assert h(q)==pin and q.stat().st_size==size
 else:q.open('xb').write(p.read_bytes())
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
a=argparse.ArgumentParser();a.add_argument('--manifest',required=True);a.add_argument('--sha256',required=True);args=a.parse_args();assert h(R/args.manifest)==args.sha256;m=rd(R/args.manifest);root=m.get('source_root',m.get('root',m.get('source_prefix')));assert root in ALLOWED and args.manifest.startswith(root+'/');rows=m['files'];assert len(rows)==m['file_count']
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('archive1949ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');intent=[];names=set()
 for row in rows:
  source=row.get('source',row['path'] if row['path'].startswith(root+'/') else root+'/'+row['path']);assert source.startswith(root+'/');name=source[len(root)+1:];assert name and not Path(name).is_absolute() and '..' not in Path(name).parts and name not in names;names.add(name)
  assert Path(name).suffix.lower() not in ['.pt','.pth','.ckpt','.safetensors','.h5','.hdf5','.init','.pruned_init'];assert row['bytes']<100*(1<<20)
  intent.append((R/source,R/E/ALLOWED[root]/name,row['sha256'],row['bytes']))
 for p,q,pin,size in intent:cp(p,q,pin,size)
 dst=R/E/ALLOWED[root]/'delivery_manifest_original.json';cp(R/args.manifest,dst,args.sha256,(R/args.manifest).stat().st_size)
 assert h(R/'results/experiment_supervisor/state.json')==before
 receipt={'status':'immutable_nonweight_package_archived','manifest':{'path':args.manifest,'sha256':args.sha256},'destination':dst.relative_to(R).as_posix(),'file_count':len(rows),'bytes':sum(r['bytes'] for r in rows),'state_unchanged':True,'GPU_jobs_added':0,'not_runtime_admission':True}
 save(R/B/(ALLOWED[root]+'_archive.json'),receipt);print(json.dumps(receipt))
