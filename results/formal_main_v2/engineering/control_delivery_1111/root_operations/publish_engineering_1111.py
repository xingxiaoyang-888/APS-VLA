from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261019T1911'
O='results/formal_main_v2/engineering/control_delivery_1111'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def write(rel,raw):
 p=R/rel;assert not p.exists() and not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
 return {'path':rel,'sha256':h(p)}
def save(rel,v):return write(rel,(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode())
def copy(src,dst,pin):
 assert h(R/src)==pin
 out=write(dst,(R/src).read_bytes());assert out['sha256']==pin;return out
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_publish1111_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state_path=R/'results/experiment_supervisor/state.json';before=h(state_path);s=c.read_json(state_path);assert s['pending_submission'] is None
 archived=[]
 groups=[('.local/cuda_continuous_admission_independent_1111','delivery_files.json','768fae919506f51c6ff3ca6af94ebe9fe4b0705728ecbb2f2f70c89efb187718','cuda_independent'),('.local/action_mixed_prefix_independent_1111','archive_closure.json','5c58169c094ac6d5c93c43d5c1dd25bfe2732349571e10bf4550683f6a366335','guard_independent')]
 for d,manifest,pin,label in groups:
  assert h(R/d/manifest)==pin;v=c.read_json(R/d/manifest)
  rows=v['files'] if isinstance(v['files'],list) else [{'path':d+'/'+name,**row} for name,row in v['files'].items()]
  rows=rows+[{'path':d+'/'+manifest,'sha256':pin,'bytes':(R/d/manifest).stat().st_size}]
  for row in rows:
   src=row['path'];assert (R/src).is_relative_to(R/d) and (R/src).stat().st_size==row['bytes']
   dst=O+'/'+label+'/'+Path(src).relative_to(d).as_posix();ref=copy(src,dst,row['sha256']);archived.append({'source':src,'archive':dst,'sha256':ref['sha256'],'bytes':row['bytes']})
 mapping=[
 ('.local/cuda_continuous_admission_1111/admission.py','scripts/ops/formal_cuda_continuous_admission_v1/admission.py','65a6a6c22710ba74f43c86589b7acdac7bd3c1b10fd86028d339eb98e3f71dcb'),
 ('.local/cuda_continuous_admission_1111/gateway.py','scripts/ops/formal_cuda_continuous_admission_v1/gateway.py','a0f81f18ccdb6f9b0cd5f5f3f871b3f6ab451809a1c6386e347ea3602abd9792'),
 ('.local/cuda_terminal_review_0943/review_formal_segment_startup.py','scripts/formal_cuda_terminal_review_v1/review_formal_segment_startup.py','ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4'),
 ('.local/cuda_terminal_review_0943/startup_failure_evidence.py','scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py','c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480'),
 ('.local/action_mixed_prefix_guard_1111/reviewer.py','scripts/ops/formal_action_consumption_guard_v1/reviewer.py','843f0336fd4161eb23d512b34935c7fca7d75032aceefe86084a16a7939a642c'),
 ('.local/action_mixed_prefix_guard_1111/consumer.py','scripts/ops/formal_action_consumption_guard_v1/consumer.py','b3f754557646c8e5fa6172fd8a1bcded7e246bbfb4c490502bdc1e3f73e21b31')]
 published=[copy(*row) for row in mapping]
 ind={'path':O+'/cuda_independent/independent_review.json','sha256':'f76915514c16fbf1b911651e60f2f3532c27001444c77f6c097261469de3b064'}
 guardind={'path':O+'/guard_independent/independent_review.json','sha256':'45a3c2ba2897dc559dd0af6685b368a548dcdabd2cc5d327b94373fe4bdc3681'}
 root=save(B+'/cuda_continuous_root_review.json',dict(schema='formal_main_v2',kind='root_CUDA_continuous_admission_source_review',status='passed_CPU_source_and_original_recovery_review',reviewed_by='root',utc=datetime.now(timezone.utc).isoformat(),author_review={'path':O+'/cuda_author/candidate_review.json','sha256':'33b52d49492ef25d1c024b2e0bfa855db0a8d29462349312b63718fc1db9fffa'},independent_review=ind,source_files=published[:4],checks=['single explicit original recovered pair only','all original failure/cost/blocked entries retained','pending before publication; no ambiguous submit retry','checkpoint recheck after invocation publication','all registered job identities and owner lease required','occupied plus existing Spatial reservation plus new GPU at most8','unchanged scientific argv and 173 source bytes'],canonical_real_preflight_in_separate_following_receipt=True,GPU_submitted=False))
 auth=c.read_json(R/'.local/cuda_continuous_admission_1111/authorization_draft.json');auth.update(status='approved_exact_once_500_to5000',reviewed_by='root',independent_review=ind,root_review=root,approved_utc=datetime.now(timezone.utc).isoformat(),user_authorization_basis='User authorized continuous normal training to5000 and bounded engineering repair of three retained CUDA failure pairs; this exact recovered pair passed original-target root and independent review.',mandatory_live_gates='Canonical actual evidence + full registry/owner/lease + unreserved slot; no bypass or automatic failure retry')
 authref=save('configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json',auth)
 g=load('scripts/ops/formal_cuda_continuous_admission_v1/gateway.py','a0f81f18ccdb6f9b0cd5f5f3f871b3f6ab451809a1c6386e347ea3602abd9792','root_continuous1111')
 t=time.monotonic();av,ae=g.validate_authorization(R,authref);science=g.a.Science(R);plan=science.prepare(s,av,authref);actual=g.a.NativeIO().preflight(plan);science.e.unchanged();ae.unchanged();assert h(state_path)==before
 canonical=save(B+'/cuda_continuous_canonical_preflight.json',dict(schema='formal_main_v2',kind='root_real_canonical_path_continuation_preflight',status='passed_readonly_actual_evidence',seconds=time.monotonic()-t,authorization=authref,root_review=root,independent_review=ind,plan=plan,server_preflight=actual,read_evidence_sha256={**science.e.hashes,**ae.hashes},state_sha256=before,state_changed=False,GPU_submitted=False,invocation_published=False,optimizer_rng_deserialized=False))
 guard=save(B+'/action_guard_root_review.json',dict(schema='formal_main_v2',kind='root_transitive_execution_ancestry_guard_review',status='CPU_candidate_published_not_activated',reviewed_by='root',utc=datetime.now(timezone.utc).isoformat(),author_review={'path':O+'/guard_author/candidate_review.json','sha256':'a3232e8db5162725ed24cbb15de770f789b58769ac06a30e382933bfe81ceb8f'},independent_review=guardind,source_files=published[4:],checks=['original O2A full raw consumption preserved','all inherited prefixes exact SHA recursively checked','legacy prefix rejected even after several current ancestors','real original release_global(release=False) fixture only; no final release created','existing 7 runtime source bytes unchanged'],author_CPU_tests=23,independent_CPU_tests=13,actual_O2A_join_verified=False,production_callers_changed=False,original_development_authorization_changed=False,limitations='No production O2A or GPU join. No equivalence exception implemented. New caller integration and real full evidence still required. Existing old prefixes remain blocked for O2A/freeze/final.'))
 readme='# 已恢复 CUDA pair 的一次连续续跑入口\n\n仅适用于 Object256 seed23、原失败3028460与恢复3039258。固定500步真实断点，目标5000、软时限169200秒、48小时分配；11次验证和全部科学源保持原字节。默认只读；实际提交需两个显式标志及完整实时门。\n\n授权：configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json。来源与独审、实际 canonical preflight 在 results/formal_main_v2/preflight/heartbeat_20261019T1911。保留6596 GPU秒历史；两份resume仅先验SHA复核，实际恢复由原训练器完整加载optimizer/RNG/cursor。\n\n正常控制器不接管该失败历史；入口只执行一次，保留blocked与Spatial预留槽。不确定提交保留全局pending，不可删除或重试。若软时限后仍未完成或异常，root重新核验；最终5000须root与独审后显式继承完成身份。不能靠清空blocked重新进入正常控制器。\n'
 write('scripts/ops/formal_cuda_continuous_admission_v1/README.md',readme.encode())
 copy('.local/action_mixed_prefix_guard_1111/README.md','scripts/ops/formal_action_consumption_guard_v1/README.md',h(R/'.local/action_mixed_prefix_guard_1111/README.md'))
 copy('.local/publish_engineering_1111.py',O+'/root_operations/publish_engineering_1111.py',h(Path(__file__)))
 result=save(B+'/engineering_publication.json',dict(schema='formal_main_v2',status='published_and_registered_no_GPU_submission',utc=datetime.now(timezone.utc).isoformat(),published=published,independent_archive=archived,cuda_authorization=authref,cuda_root_review=root,cuda_actual_preflight=canonical,guard_root_review=guard,prior_script_composition_error='Prior inline script did not parse due nested triple-quote; no file writes, subprocesses, or production mutations occurred. Corrected source here.',state_changed=False,GPU_submitted=False,final_release=False))
 assert h(state_path)==before
 print(json.dumps(dict(publication=result,cuda_authorization=authref,canonical_preflight=canonical,guard_root_review=guard,independent_archived_files=len(archived))))
