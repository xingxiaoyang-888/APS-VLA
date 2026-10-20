from pathlib import Path
import json,hashlib,importlib.util,sys,tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261020T2330';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def cp(src,dst,pin):
 assert src.is_relative_to(R) and (dst.is_relative_to(R) or dst.is_relative_to(P)) and h(src)==pin
 assert not any(x.is_symlink() for x in (src,*src.parents,dst,*dst.parents));assert src.suffix not in ['.pt','.pth','.safetensors','.ckpt','.bin','.pyc','.h5','.hdf5']
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert h(dst)==pin
 else:
  with dst.open('xb') as f:f.write(src.read_bytes())
 return dict(source=dict(path=src.relative_to(R).as_posix(),sha256=pin,bytes=src.stat().st_size),archive=dict(path=dst.relative_to(R).as_posix(),sha256=pin))
def save(rel,d):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(d,f,sort_keys=True,indent=2);f.write('\n')
 return dict(path=rel,sha256=h(p))
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','pack1530ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);copies=[]
 items=[('.local/nonLong64_development_plans_20261020T1530','delivery_manifest.json','c91d6a527d7b8ff674931d212b093d7a115a216191340341ae7788cc0e3d561b','plan_author'),('.local/object256s23_consumer_candidate_20261020T1530','delivery_manifest.json','06319a5f4fb7dc7b1d26741436ee6b4997f23e5d2016de23890f630cb6183d3f','Object_source_bridge_candidate')]
 for root,mn,pin,dest in items:
  srcroot=R/root;mf=srcroot/mn;assert h(mf)==pin;d=json.loads(mf.read_bytes())
  for row in d['files']:
   src=Path(row['path']);src=src if src.is_absolute() else R/src
   copies.append(cp(src,R/E/dest/src.relative_to(srcroot),row['sha256']))
  copies.append(cp(mf,R/E/dest/mn,pin))
 pm=R/'.local/nonLong64_development_plans_20261020T1530/attempt01/publication_map.json';assert h(pm)=='973fac317e38d1147e2cea04a13f1858a9c108456ed23be4bfaaacbeb04282a3';files=json.loads(pm.read_bytes())['files'];assert len(files)==12
 published=[]
 for x in files:
  assert x['suite'] in ['libero_spatial','libero_object'] and x['budget']==64 and x['seed'] in [17,41]
  rel=x['canonical_path'];assert rel.startswith('results/formal_main_v2/execution/nonLong_action_v1_20261020T1530/') and Path(rel).name in ['effective_plan.json','scientific_plan.json','execution_contract.json']
  src=R/x['candidate_path'];assert h(src)==x['sha256'];copies.append(cp(src,R/rel,x['sha256']))
  target=P/rel;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert h(target)==x['sha256']
  else:
   with target.open('xb') as f:f.write(src.read_bytes())
  published.append(dict(path=rel,sha256=h(target)))
 # Recover archival completion only. Previous pack finished; original exception was the absent code-archive directory.
 inputs=json.loads((R/B/'Goal3043877_archive_inputs.json').read_bytes());snap=inputs['snapshot'];assert h(R/snap['path'])==snap['sha256']
 m=load('scripts/ops/nonweight_archive.py','f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2','pack1530codec')
 verified=m.verify(R,snap['path']);assert verified['status']=='verified' and verified['original_bytes']==186620031 and verified['files']==3
 src=R/'.local/archive_Goal3043877_20261020T1530.py';copies.append(cp(src,R/B/'root_operations'/src.name,'782c73e5183f1180a62462241bc140d3a30696ab277de8dc584d5645025dbb94'))
 for rel in ['.local/git_commit_20261020T1418.json','.local/github_push_20261020T1418_verified.json']:
  src=R/rel;copies.append(cp(src,R/E/'previous_delivery'/src.name,h(src)))
 assert h(state)==before
 receipt=save(B+'/plan_static_and_candidate_delivery.json',dict(status='exact_nonweight_archive_and_static_plan_publication_only',copies=copies,static_plan_files=published,state_unchanged=True,new_submissions=0,Goal3043877_archive_verified=verified,previous_archival_exception_retained=True,Goal3043877_root_independent_acceptance=False,Object_bridge_not_admitted=True,final_opened=False))
 print(json.dumps(dict(receipt=receipt,copies=len(copies),static_files=len(published),archive=verified)))
