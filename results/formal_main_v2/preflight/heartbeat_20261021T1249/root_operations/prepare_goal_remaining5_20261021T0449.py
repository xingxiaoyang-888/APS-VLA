from pathlib import Path
from datetime import datetime,timezone
import os,json,hashlib,fcntl,importlib.util,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B=R/'results/formal_main_v2/preflight/heartbeat_20261021T1249';E=R/'results/formal_main_v2/engineering/supervision_delivery_20261021T0449'
STATE=R/'results/experiment_supervisor/state.json';SS='d795f666c630ba196f9eba8aae8d5cbed879e10fd596fc95d37c745f281948ba'
D=R/'.local/goal_remaining5_plans_20261021T0449/v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def direct(p):assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);return p
def write(p,raw):
 direct(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 assert p.read_bytes()==raw
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size}
def package(src,pin,dest):
 mp=src/'delivery_manifest.json';assert sha(mp)==pin
 m=json.loads(mp.read_bytes());assert len(m['files'])==m['file_count']
 seen=set();files=[]
 for row in m['files']:
  p=direct(R/row['path']);assert src in p.parents and p.suffix in ('.json','.py','.md','.jsonl')
  assert p not in seen;seen.add(p);raw=p.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
  q=dest/p.relative_to(src);assert not q.exists();files.append((q,raw,row))
 for q,raw,row in files:write(q,raw)
 write(dest/'delivery_manifest_original.json',mp.read_bytes())
 write(dest/'root_publication_mapping.json',enc({'source_manifest':ref(mp),'files':[{'source':row['path'],'destination':str(q.relative_to(R)),'sha256':row['sha256'],'bytes':len(raw)} for q,raw,row in files]}))
 return m
source=R/'.local/goal_remaining5_independent_20261021T0449'
metadata=json.loads((source/'metadata_post_review/independent_review.json').read_bytes())
assert sha(source/'metadata_post_review/independent_review.json')=='b2e01dae3dc6125e2376030d27612769dd78203cfdd5aaacc8170ca399dc669f'
assert metadata['status']=='passed_actual_single_field_metadata_review' and metadata['blockers']==[] and metadata['state_after']['sha256']==SS
proof=source/'plans_canonical/canonical_independent_rebuild.json'
assert sha(proof)=='03bc1262dddbf5413491c08179fdc09c5ebfc61a9b985905d7be0b9924cf62e5'
v=json.loads(proof.read_bytes());assert v['status']=='passed_canonical_original_plan_and_CPU_review' and v['blockers']==[] and v['pair_count']==5 and v['check_count']==550 and not v['actual_new_runtime_P_verified']
mp=source/'plans_canonical/review_publication_map.json';assert sha(mp)=='fd3bd086adbff5751f271e0997d1ff7cc3103e3bc690676a2fd6addf70208f2e'
mapping=json.loads(mp.read_bytes());assert len(mapping['reviews'])==5
keys=['libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41']
assert [row['destination'] for row in mapping['reviews']]==['results/formal_main_v2/execution/goal_remaining5_v1/'+k+'/plan_independent_review.json' for k in keys]
index_path=D/'candidate_index.json';index_pin='638ec6f36339aa3a43a78266a60c58427aa40f22979f442cd740432962a28d3f';assert sha(index_path)==index_pin
index=json.loads(index_path.read_bytes())
path=D/'prepare_after_reviews_v2.py';assert sha(path)=='a633636dc4cdd64f75d32de72dda5dea34804b1253d7658c21dce97091aa7736'
sp=importlib.util.spec_from_file_location('root_prepare_remaining5',path);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__)
with (R/'results/experiment_supervisor/.writer.lock').open('r+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);assert sha(STATE)==SS
 package(source/'metadata_post_review','ba372b5138815882f7e69098205843dc22ee8d9d109084e4d7c10c38b3ca562f',E/'Goal_metadata_independent')
 package(source/'plans_canonical','a78f9025ba6bf22f3485c23253efee2d3a67ee1a1248afd16920d17cd89b11c8',E/'Goal_plan_independent')
 for k,row in zip(keys,mapping['reviews']):
  src=R/row['source'];assert sha(src)==row['sha256'] and src.stat().st_size==row['bytes']
  item=index['pairs'][k];action=json.loads((R/item['execution_contract']['path']).read_bytes())
  m.validate_review(json.loads(src.read_bytes()),item,index,'independent',action['files'])
  for root in [R,P]:assert not (root/row['destination']).exists()
 for row in mapping['reviews']:
  for root in [R,P]:write(root/row['destination'],(R/row['source']).read_bytes())
 assert sha(STATE)==SS
 write(B/'Goal_remaining5_independent_plan_publication.json',enc({'status':'published_original_plan_independent_reviews_only','reviews':mapping['reviews'],'source_manifest':ref(source/'plans_canonical/delivery_manifest.json'),'root_metadata_post_review':ref(E/'Goal_metadata_independent/independent_review.json'),'current_state_sha256':SS,'new_GPU_submissions':0,'actual_P_runtime_verified':False}))
reports=[];t=datetime.now(timezone.utc).isoformat()
for k in keys:
 base=R/('results/formal_main_v2/execution/goal_remaining5_v1/'+k)
 result=m.prepare(index_path=index_path,index_sha=index_pin,pair_key=k,root_sha=sha(base/'plan_root_review.json'),independent_sha=sha(base/'plan_independent_review.json'),prepared_utc=t)
 reports.append(result);print('prepared original metadata',k,flush=True)
with (R/'results/experiment_supervisor/.writer.lock').open('r+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);assert sha(STATE)==SS
 rows=[]
 for report in reports:
  for row in report['private_outputs']:
   src=direct(R/row['source']);assert D in src.parents and sha(src)==row['sha256']
   for root in [R,P]:assert not (root/row['destination']).exists()
 for report in reports:
  for row in report['private_outputs']:
   for root in [R,P]:write(root/row['destination'],(R/row['source']).read_bytes())
   rows.append(row)
  src=D/'prepared'/report['pair_key']/'preparation_record.json'
  write(E/'Goal_prepared_metadata'/report['pair_key']/'preparation_record.json',src.read_bytes())
  for n in ['runtime_readiness.json','prepared_invocation.json']:write(E/'Goal_prepared_metadata'/report['pair_key']/n,(src.parent/n).read_bytes())
 write(B/'Goal_remaining5_prepared_invocations.json',enc({'schema':'formal_main_v2','kind':'Goal_remaining5_true_prepared_original_invocations','status':'prepared_metadata_only_no_submission_authorization','original_wrapper_runtime_readiness_only':True,'original_invocations':[r['original_invocation'] for r in reports],'publication_map':rows,'source_index':ref(index_path),'root_and_independent_original_plan_reviews':True,'actual_new_runtime_P_verified':False,'GPU_execution_authorized':False,'new_GPU_jobs':0,'new_trials':0,'state_sha256':SS}))
 assert sha(STATE)==SS
print(json.dumps({'status':'five_genuine_prepared_invocations_published','receipt':ref(B/'Goal_remaining5_prepared_invocations.json'),'original_invocations':[r['original_invocation'] for r in reports],'new_GPU_jobs':0},sort_keys=True))
