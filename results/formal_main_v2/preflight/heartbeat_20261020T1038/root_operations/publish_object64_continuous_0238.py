from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1038'
E='results/formal_main_v2/engineering/supervision_delivery_0238'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def rd(rel):return json.loads((R/rel).read_bytes())
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def write(rel,raw):
 p=R/rel;assert not p.exists() and not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
 return ref(rel)
def save(rel,v):return write(rel,(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode())
def cp(src,dst,pin):
 assert h(R/src)==pin
 v=write(dst,(R/src).read_bytes());assert v['sha256']==pin;return v
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','pubObjCont0238')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state_path=R/'results/experiment_supervisor/state.json';before=h(state_path);s=rd('results/experiment_supervisor/state.json');assert s['pending_submission'] is None
 assert h(R/'docs/服务器工作区与GitHub同步.md')=='d7f0455ef4febb536df199653fd323a1cef98ad66732e5b2ea8edfdf06b75343'
 ad='.local/object64_continuous_admission_0238';di='.local/object64_continuous_independent_0238'
 assert h(R/ad/'candidate_review.json')=='a2957441142f668fbea785d89abcaaecb8f4e47dc0f60ea8f8e05cc2a6f97249'
 assert h(R/di/'independent_review.json')=='13c3508eca7aa7dfd2381626e4727d7a7d232d0dd10c146d0ba7729b1fb6f2c4'
 author=rd(ad+'/candidate_review.json');ind=rd(di+'/independent_review.json')
 assert author['status']=='passed_CPU_candidate_not_authorized' and author['tests']['tests']==55 and author['tests']['failures']==author['tests']['errors']==0
 assert ind['status']=='passed_CPU_review' and ind['kind']=='object64_cuda_continuous_admission_independent_CPU_review' and ind['blockers']==[]
 assert ind['files']==author['current_source_files']
 archived=[]
 for d,man,pin,label in [(ad,'archive_manifest.json','58fef43415d0581fa640116bb60224409d19d5be1f00770e92df1730df1e00e4','Object64_continuous_author'),(di,'archive_closure.json','739bad2ba23286a879d0ae667f5657aeffc23009610ae8da261eba9d4214bf30','Object64_continuous_independent')]:
  assert h(R/d/man)==pin
  v=rd(d+'/'+man);rows=v['files']
  if isinstance(rows,dict):rows=[dict(path=d+'/'+name,**row) for name,row in rows.items()]
  rows=rows+[dict(path=d+'/'+man,sha256=pin,bytes=(R/d/man).stat().st_size)]
  for row in rows:
   p=R/row['path'];assert p.is_relative_to(R/d) and p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes']
   dst=E+'/'+label+'/'+p.relative_to(R/d).as_posix()
   out=cp(row['path'],dst,row['sha256']);archived.append(dict(source=row['path'],archive=out['path'],sha256=out['sha256'],bytes=row['bytes']))
 amap=rd(ad+'/publication_map.json');assert h(R/ad/'publication_map.json')=='e118d5be760071fd776beda56f35befb2762fd9850a3d56a61f726adc75df84a'
 published=[]
 for row in amap['source_files']:
  assert row['destination_root']=='R' and row['P_publication_required'] is False
  assert (R/row['candidate']).stat().st_size==row['bytes']
  published.append(cp(row['candidate'],row['canonical'],row['sha256']))
 indref=ref(E+'/Object64_continuous_independent/independent_review.json')
 root=save(B+'/Object64_continuous_root_review.json',dict(schema='formal_main_v2',kind='root_Object64_continuous_admission_source_review',status='passed_CPU_source_and_original_recovery_review',reviewed_by='root',utc=datetime.now(timezone.utc).isoformat(),author_review=ref(E+'/Object64_continuous_author/candidate_review.json'),independent_review=indref,source_files=published,author_tests=55,independent_checks=15,checks=['exact Object64 seed23 only, old Object256 authorization rejected','retain original failed3028468 69s and recovered3044017 5141s; all5210s billed','original500/cursor4000,4000 unique samples,zero replay and correct cold-start recovery proven','same original Object metadata wrapper/runtime compatibility and173 frozen scientific files','same full optimizer/RNG/cursor restore with5000 schedule and11 validation nodes','same one-shot pending/ACK/lease/CAS/capacity transaction, no implicit retry','default readonly and no GPU submission at full8'],canonical_real_preflight_in_following_receipt=True,GPU_submitted=False))
 assert h(R/ad/'authorization_draft.json')=='1f7d8dee653e71299f6d91d57c87554f0af0dd98f0ab40d2f6c16e0bb9fbcca4'
 auth=rd(ad+'/authorization_draft.json');assert auth['status']=='draft_not_authorized' and auth['root_review'] is None and auth['independent_review'] is None
 auth.update(status='approved_exact_once_500_to5000',reviewed_by='root',independent_review=indref,root_review=root,approved_utc=datetime.now(timezone.utc).isoformat())
 authref=save('configs/experiments/formal_main_v2_object64_cuda_continuous_3044017_v1.json',auth)
 g=load('scripts/ops/formal_object64_cuda_continuous_admission_v1/gateway.py','2aaed25efd1d8783ace9ace93a5212f67b52f1d1a6fde1072349d8d8a830f54a','rootObject64Canonical0238')
 t=time.monotonic();av,ae=g.validate_authorization(R,authref);science=g.a.Science(R);plan=science.prepare(s,av,authref);actual=g.a.NativeIO().preflight(plan)
 science.e.unchanged();ae.unchanged();assert h(state_path)==before
 canonical=save(B+'/Object64_continuous_canonical_preflight.json',dict(schema='formal_main_v2',kind='root_real_canonical_path_Object64_continuation_preflight',status='passed_readonly_actual_evidence',seconds=time.monotonic()-t,authorization=authref,root_review=root,independent_review=indref,plan=plan,server_preflight=actual,read_evidence_sha256={**science.e.hashes,**ae.hashes},state_sha256=before,state_changed=False,GPU_submitted=False,invocation_published=False,optimizer_rng_deserialized=False,scheduler_capacity_not_bypassed=True,future_submit_requires_full_live_registry_owner_lease_and_spare_slot=True))
 readme='# Object64 seed23 一次连续续跑入口\n\n仅适用于原失败3028468与恢复3044017，A/B各500步、样本游标4000。失败69秒及恢复5141秒共5210 GPU秒保留。授权见 configs/experiments/formal_main_v2_object64_cuda_continuous_3044017_v1.json。\n\n部署和训练科学源不变；原Object metadata wrapper，5000步全程调度、val0及每500共11次验证。继续前由原训练器完整校验并恢复optimizer、RNG及游标。48小时分配、169200秒正常软时限、每50步checkpoint，不以这次控制修正改变实验规模。\n\n默认只读；root实际提交必须通过已审server_control_transport_v1、确切gateway及授权SHA，显式 --submit --root-reviewed-submit。提交前完整已登记作业、owner/lease、单pair活动、pending、保留预约及最多8 GPU均须现场通过。此历史失败pair仍保留controller blocked记录，不因新授权清空或自动重试。不确定提交保留pending并按原ACK/token对账，禁止删除pending或盲重发。\n\n本轮作者55项与独审15项CPU检查，root已重建真实非权重证据及两resume字节哈希。记录在 results/formal_main_v2/preflight/heartbeat_20261020T1038/Object64_continuous_publication.json。当前没有新GPU提交或最终评测release；正常作业不做本轮内实时轮询。\n'
 write('scripts/ops/formal_object64_cuda_continuous_admission_v1/README.md',readme.encode())
 write(B+'/root_operations/publish_object64_continuous_0238.py',Path(__file__).read_bytes())
 pub=save(B+'/Object64_continuous_publication.json',dict(schema='formal_main_v2',status='published_and_registered_no_GPU_submission',utc=datetime.now(timezone.utc).isoformat(),published=published,archive_copies=archived,author_review=ref(E+'/Object64_continuous_author/candidate_review.json'),independent_review=indref,root_review=root,authorization=authref,canonical_preflight=canonical,state_changed=False,GPU_submitted=False,final_release=False))
 assert h(state_path)==before
 print(json.dumps(dict(status='published_actual_preflight_passed',publication=pub,authorization=authref,canonical_preflight=canonical,archive_files=len(archived))),flush=True)
