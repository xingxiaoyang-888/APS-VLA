from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0833'
E='results/formal_main_v2/engineering/supervision_delivery_0033'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def rd(rel):return json.loads((R/rel).read_bytes())
def cp(src,dst,pin):
 p=R/src;assert p.is_file() and not p.is_symlink() and h(p)==pin
 q=R/dst;q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as f:f.write(p.read_bytes())
 assert h(q)==pin
 return dict(source=ref(src),archive=ref(dst))
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','publishctl0033')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';state_sha=h(statepath);state=rd('results/experiment_supervisor/state.json')
 assert state['pending_submission'] is None
 packs=[
 ('.local/spatial_continuous_doc_binding_0033','archive_manifest.json','52d1eee2ea00486c4b3133ebffef8661d713d551d6f08eb64258e2a05776892b','Spatial_doc_binding_author'),
 ('.local/spatial_continuous_doc_binding_independent_0033','archive_closure.json','69afd4a4d1cac7ff27ed336fe15f944fcc229643ce652ba71116b23ae81467a2','Spatial_doc_binding_independent')]
 copies=[];external=[]
 for base,manifest,pin,dest in packs:
  mr=base+'/'+manifest;assert h(R/mr)==pin;rows=rd(mr)['files']+[dict(path=mr,sha256=pin,bytes=(R/mr).stat().st_size)]
  for row in rows:
   src=row['path'];p=R/src;assert h(p)==row['sha256'] and p.stat().st_size==row['bytes']
   if src.startswith(base+'/'):
    suffix=Path(src).relative_to(base).as_posix();copies.append(cp(src,E+'/'+dest+'/'+suffix,row['sha256']))
   else:
    assert src.startswith('results/formal_main_v2/control_transport/');external.append(ref(src))
 pub='.local/spatial_continuous_doc_binding_0033/publication_map.json'
 assert h(R/pub)=='5df5db17aaa2ece8826c40ed8fd0a491eb187cb27e69f8fa54e002e164e3aea6'
 for row in rd(pub)['files']:copies.append(cp(row['candidate'],row['canonical'],row['sha256']))
 auth=rd('.local/spatial_continuous_doc_binding_0033/authorization_a1_draft.json')
 auth.update(status='approved_exact_once_1500_to5000',reviewed_by='root',reviewed_utc=datetime.now(timezone.utc).isoformat(),
  independent_review=ref(E+'/Spatial_doc_binding_independent/independent_review.json'),
  author_review=ref(E+'/Spatial_doc_binding_author/candidate_review.json'),
  historical_document_binding=ref('results/formal_main_v2/engineering/spatial_continuous_doc_binding_v2/document_binding.json'),
  previous_version_authorization=ref('configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v1.json'),
  reason='Exact byte-bound operational document history bridge; all original scientific, raw, optimizer/RNG/cursor, capacity, pending/CAS and one-attempt gates retained.')
 ar=save('configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v2.json',auth)
 g=load('scripts/ops/formal_spatial_cuda_continuous_admission_v2/gateway.py','4f552abcc05d72ff84975e360ea28a624a4744febb8518e2fc71839fe47d5864','spatialv2root0033')
 validated,ev=g.validate_authorization(R,ar)
 science=g.a.Science(R);plan=science.prepare(state,validated,ar);actual=g.a.NativeIO().preflight(plan)
 science.e.unchanged();ev.unchanged();assert h(statepath)==state_sha
 proof=save(B+'/Spatial_v2_root_publication_and_prepare.json',dict(schema='formal_main_v2',status='published_and_root_raw_preflight_passed',utc=datetime.now(timezone.utc).isoformat(),authorization=ar,copies=copies,external_transport=external,root_state_unchanged_sha256=state_sha,original_raw_reconstructed=plan['original_raw_reconstructed'],read_evidence_sha256=plan['evidence_sha256'],actual_server_read_only=actual,all173_scientific_unchanged=True,old_gate_failure=ref(B+'/Spatial_continuous_check/execution.json'),source_version_change_only='Exact historical operational-document byte binding',new_invocation_published=False,GPU_submitted=False,capacity_claimed=False,final_release_authorized=False))
 readme='# Spatial64 seed23 连续恢复 v2\n\n仅修正原独审收据引用的运维文档历史版本。绑定完整新旧字节、Git身份和确切旧收据；当前文档继续哈希校验。173个科学文件、损失、数据、优化器/RNG/游标、5000步调度、11次验证及原提交事务均不变。\n\n'+f'新授权：{ar["path"]}，SHA {ar["sha256"]}。root实际原始复核：{proof["path"]}。独审与失败记录保存在 {E} 及本轮preflight。\n\n执行必须先核控制器所有权/lease、全部登记Slurm身份、pending与容量。使用 gateway.py 的只读检查后才能带双提交标志执行一次。不能消耗其他保留槽或自动重试；无空槽时留待下次监督。本验收未运行GPU或恢复张量。\n'
 p=R/'scripts/ops/formal_spatial_cuda_continuous_admission_v2/README.md'
 with p.open('x') as f:f.write(readme)
 print(json.dumps(dict(status='published_and_preflight_passed',authorization=ar,root_receipt=proof,archived=len(copies),server_metadata=len(actual['server_files']),no_GPU_submission=True)))
