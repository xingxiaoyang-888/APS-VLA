from pathlib import Path
import fcntl,hashlib,json,os,sys,importlib.util
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225';BASE='results/formal_main_v2/engineering/goal_prefix58_20261020T1825';PKG='scripts/ops/formal_goal_prefix58_observer_v2'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def safe(p):assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);return p
def put(p,raw):
 safe(p);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw;return
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def jout(p,v):put(p,(json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
def ref(p):return {'path':str(p.relative_to(R)),'sha256':h(p)}
mp=R/'.local/goal_prefix58_repair_20261020T1825/publication_manifest.json';assert h(mp)=='13719a2fbe281552bfe67bc0a45c9afc802cecc968435e85be8253ef19944c35';manifest=read(mp)
ip=R/'.local/goal_prefix58_independent_20261020T1825/outer_attempt01/independent_readiness.json';assert h(ip)=='660a2f543e7f64ce0105e50dcd908d55bf9db4ee7b73aedb7994738b424ae057';ind=read(ip)
assert h(R/'.local/goal_prefix58_independent_20261020T1825/attempt02/independent_review.json')=='5f538a213504f3fdab8c230f5ce8bbdb7b4e1670ec4d2cd418561cfc593941ff'
assert h(R/'.local/goal_prefix58_independent_20261020T1825/outer_attempt01/independent_review.json')=='4caacdb76c40a9c635f9a926bff3b6fd3b8cb53681fd21f05489800a2eebf7df'
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read(sp);f=s['formal_main_progress'];assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==72 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 invfile=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';assert h(invfile)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926';inventory=read(invfile);assert len(inventory['files'])==173
 for root in [R,S]:
  for rel,pin in inventory['files'].items():assert h(safe(root/rel))==pin
 for row in manifest['files']:
  src=safe(R/row['source']);assert h(src)==row['sha256'] and src.stat().st_size==row['bytes'];assert row['destination'].startswith(PKG+'/') and row['destination_roots']==['R','P']
  for root in [R,P]:put(root/row['destination'],src.read_bytes());assert h(root/row['destination'])==row['sha256']
 source=safe(P/PKG/'entry.py');spec=importlib.util.spec_from_file_location('g58_root_published',source);entry=importlib.util.module_from_spec(spec);sys.modules[spec.name]=entry;spec.loader.exec_module(entry)
 config=read(P/PKG/'config.json');entry.validate_config(config);msha=h(P/PKG/'package_manifest.json');csha=h(P/PKG/'config.json');entry.check_review(ind,'independent',msha,csha)
 inv,wrapper,ctx,legacy=entry.prepare_original();prefix=entry.validate_prefix(inv,legacy,read(P/PKG/'prefix58.json')['rows'])
 import torch
 assert not torch.cuda.is_initialized() and not (P/BASE/'attempt01').exists()
 rootreview={'schema':'formal_main_v2','kind':'goal_prefix58_single_attempt_CPU_readiness','status':'passed','reviewed_by':'root','version':entry.VERSION,'package_manifest_sha256':msha,'config_sha256':csha,'original_chain_preserved':True,'observer_gaps_fixed':True,'real_GPU_acceptance':False,'scientific_release':False,'published_source_manifest':ref(mp),'independent_review':ref(ip),'root_checks':['exact original invocation/wrapper/source/checkpoint bytes','actual published P config and six-file closure','original fixed first58 identities in state-major order','source review of original contexts and AST whitelist; passive guards before and after journal','173 frozen files in control and runtime snapshot unchanged','root/independent CPU roles distinct; all Goal science and final HOLD retained','CUDA not initialized; no attempt output and no Slurm submission'],'prefix_proof':prefix,'utc':datetime.now(timezone.utc).isoformat()}
 entry.check_review(rootreview,'root',msha,csha)
 for root in [R,P]:jout(root/BASE/'root_readiness.json',rootreview);put(root/BASE/'independent_readiness.json',ip.read_bytes())
 auth={'schema':'formal_main_v2','kind':'root_goal_prefix58_single_attempt_authorization','version':entry.VERSION,'status':'approved','reviewed_by':'root','stage_key':entry.STAGE,'config_sha256':csha,'package_manifest_sha256':msha,'entrypoint_sha256':h(source),'maximum_gpu_jobs':1,'maximum_attempts':1,'maximum_wall_seconds':1800,'counts_against_8_GPU_slots':True,'automatic_retry':False,'scientific_release':False,'original_goal200_HOLD':True,'new_Goal_science_HOLD':True,'maximum_trials':58,'resources':entry.RESOURCES,'dispatch_record_path':str(entry.DISPATCH),'reservation_path':str(entry.RESERVATION),'root_review':{'path':str(P/BASE/'root_readiness.json'),'sha256':h(P/BASE/'root_readiness.json')},'independent_review':{'path':str(P/BASE/'independent_readiness.json'),'sha256':h(P/BASE/'independent_readiness.json')}}
 entry.validate_authorization(auth,csha,msha,h(source))
 for root in [R,P]:jout(root/BASE/'root_authorization.json',auth)
 assert h(sp)==before
 receipt={'schema':'formal_main_v2','status':'published_root_CPU_verified_single_attempt_authorized_not_submitted','package_manifest':ref(R/PKG/'package_manifest.json'),'files':manifest['files'],'root_readiness':ref(R/BASE/'root_readiness.json'),'independent_readiness':ref(R/BASE/'independent_readiness.json'),'authorization':ref(R/BASE/'root_authorization.json'),'state_before_sha256':before,'state_unchanged':True,'GPU_jobs_submitted':0,'real_GPU_acceptance':False,'scientific_release':False,'utc':datetime.now(timezone.utc).isoformat()}
 jout(B/'Goal_prefix58_publication.json',receipt);print(json.dumps({'publication':ref(B/'Goal_prefix58_publication.json'),'authorization':ref(R/BASE/'root_authorization.json')}))
