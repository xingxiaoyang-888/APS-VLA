from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T2020';E='results/formal_main_v2/engineering/supervision_delivery_1220'
PACKAGES=[{"base":".local/nonLong_development_plans_independent_1220","manifest":"final_manifest_v2.json","sha256":"ba34b6665ffa19f0b068df647807d28e884f3900b5aef623f7b199271f41f07a","archive":"nonLong_plan_independent"},{"base":".local/nonLong_submission_independent_1220","manifest":"manifest.json","sha256":"eb215cad725c40471d685b58dbdc8649e918a117ec71b5baa52895d0960bae91","archive":"nonLong_submission_independent"}]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
def save(rel,x):
 put(R/rel,(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode());return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('nonlongarchivectl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');out=[]
 for item in PACKAGES:
  base=Path(item['base']);m=base/item['manifest'];assert h(R/m)==item['sha256'];data=json.loads((R/m).read_bytes())
  rows=data['files']+[dict(path=m.as_posix(),sha256=item['sha256'],bytes=(R/m).stat().st_size)];copies=[]
  for row in rows:
   rel=Path(row['path'])
   if not rel.is_relative_to(base):rel=base/rel
   assert rel.is_relative_to(base) and '..' not in rel.parts and not rel.is_absolute()
   src=R/rel;assert not src.is_symlink() and src.is_file() and h(src)==row['sha256'] and src.stat().st_size==row['bytes']
   assert src.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc','.npz','.npy'] and src.stat().st_size<100*(1<<20)
   dst=E+'/'+item['archive']+'/'+rel.relative_to(base).as_posix();put(R/dst,src.read_bytes())
   copies.append(dict(source={**row,'path':rel.as_posix()},archive=ref(dst)))
  out.append(save(B+'/'+item['archive']+'_v2_delivery.json',dict(source_manifest=ref(m.as_posix()),copies=copies,no_source_transformation=True,new_GPU_jobs=0)))
 assert h(R/'results/experiment_supervisor/state.json')==before
 put(R/B/'root_operations/archive_nonlong_final_audits_1220.py',Path(__file__).read_bytes())
 print(json.dumps(dict(status='archived_exact_private_evidence',packages=out,state_unchanged=True)))
