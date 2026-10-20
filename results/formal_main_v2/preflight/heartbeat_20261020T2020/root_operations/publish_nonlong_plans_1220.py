from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D='.local/nonLong_development_plans_1220';E='results/formal_main_v2/engineering/supervision_delivery_1220/nonLong_plan_author';B='results/formal_main_v2/preflight/heartbeat_20261020T2020';T='results/formal_main_v2/execution/nonLong_action_v1_1220'
AUTHOR_MANIFEST_SHA='495f194071bf42efc32cdf65c10375aaa34721b650058e7ac99dc02f26463019'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
def save(rel,x):put(R/rel,(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode());return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('publish1220planctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json')
 assert h(R/D/'delivery_manifest.json')==AUTHOR_MANIFEST_SHA
 m=rd(D+'/delivery_manifest.json');rows=m['files']+[dict(path=D+'/delivery_manifest.json',sha256=AUTHOR_MANIFEST_SHA,bytes=(R/D/'delivery_manifest.json').stat().st_size)]
 copies=[]
 for row in rows:
  rel=Path(row['path']);assert rel.is_relative_to(D) and '..' not in rel.parts and not rel.is_absolute()
  p=R/rel;assert p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes'] and h(p)==row['sha256']
  assert p.stat().st_size<100*(1<<20) and p.suffix not in ['.pt','.pth','.bin','.ckpt','.safetensors','.pyc','.npz','.npy']
  dst=E+'/'+rel.relative_to(D).as_posix();put(R/dst,p.read_bytes())
  copies.append(dict(source=row,archive=ref(dst)))
 deliver=save(B+'/nonLong_plan_author_delivery.json',dict(source_manifest=ref(D+'/delivery_manifest.json'),copies=copies,no_source_transformation=True))
 report=rd(D+'/attempt01/candidate_review.json');assert report['total_planned_trials']==600 and report['source173_unchanged'] and not report['production_files_changed']
 pubs=[]
 for row in report['plans']:
  sub=row['suite']+'_k128_seed'+str(row['seed'])
  for key,name in [('scientific_plan','scientific_plan.json'),('execution_contract','execution_contract.json'),('effective_plan','effective_plan.json')]:
   rr=row[key];assert rr['path']==T+'/'+sub+'/'+name
   src=R/D/'attempt01'/sub/name;assert h(src)==rr['sha256']
   put(R/rr['path'],src.read_bytes());put(P/rr['path'],src.read_bytes())
   pubs.append(rr)
 assert h(R/'results/experiment_supervisor/state.json')==before
 put(R/B/'root_operations/publish_nonlong_plans_1220.py',Path(__file__).read_bytes())
 receipt=save(B+'/nonLong_static_plan_publication.json',dict(status='published_exact_candidate_metadata_only',files=pubs,author_delivery=deliver,state_unchanged=True,GPU_submissions=[],final_release=False))
 print(json.dumps(dict(receipt=receipt,published=len(pubs),archived=len(copies))))
