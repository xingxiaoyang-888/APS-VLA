from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T1426'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def write(rel,v):
 p=R/rel
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_terminal0626_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';state_sha=sha(statepath);s=json.loads(statepath.read_text())
 pullref={'path':'results/formal_main_v2/pulls/20261020T063613Z_083e58f82fa4/receipt.json','sha256':'3d76d0eb99b1418c6a64974e3f7b84d5636f04005880ce8d4a5ff86b530547e3'}
 assert sha(R/pullref['path'])==pullref['sha256']
 assert sha(R/'scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py')=='c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480'
 candidates=[pullref]
 normal=mod('scripts/formal_cuda_terminal_review_v1/review_formal_segment_startup.py','ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4','root_normal0626')
 result=normal.review('3042627',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',pull_receipt=candidates[0]['path'],verify_server_resume=True,root=R)
 assert result['completed_by_arm']=={'A':5000,'B':5000}
 rp=R/result['output_relative']/'segment_reviews/3042627.json';checks=[]
 pairroot=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_object/k256/seed23')
 for arm in ['A','B']:
  receipt=json.loads((R/result['output_relative']/arm/'deployment_receipt.json').read_text())
  assert receipt['training_complete'] and receipt['completed_updates']==5000
  assert [e['update'] for e in receipt['evaluations']]==list(range(0,5001,500))
  target=pairroot/arm/'best.pt';st=target.stat();digest=c.file_sha(target);assert digest==receipt['checkpoint_sha256'] and st==target.stat()
  checks.append(dict(arm=arm,path=str(target),sha256=digest,bytes=st.st_size,selected_update=receipt['metadata']['update'],validation_metric=receipt['metadata']['validation_metric']))
 sr=write(B+'/3042627_selected_server.json',dict(status='verified_actual_server_bytes',job_id='3042627',root_review=ref(rp),checks=checks,weights_copied=False,optimizer_rng_deserialized=False))
 rr=write(B+'/3042627_root_terminal.json',dict(root_review=ref(rp),selected_server=sr,machine_original_outcome=None,verification_origin='root_startup_consumer_original_failure_and_recovery_preserved',pull=candidates[0],completed_by_arm=result['completed_by_arm'],pair_allocated_GPU_seconds=result['pair_allocated_gpu_seconds'],independent_review_integrated=False))
 assert sha(statepath)==state_sha
 print(json.dumps(dict(status=result['status'],root_review=ref(rp),root_terminal=rr,selected=sr,state_unchanged=True)))
