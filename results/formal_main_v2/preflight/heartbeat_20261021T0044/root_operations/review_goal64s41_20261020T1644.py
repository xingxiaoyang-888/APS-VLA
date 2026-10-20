from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def write(rel,v):
 p=R/rel
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_terminal1644_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';state_sha=sha(statepath);s=json.loads(statepath.read_text());complete=s['autonomous_training_v1']['completed_pairs']['libero_goal_k64_seed41'];outref=complete['machine_output'];assert sha(R/outref['path'])==outref['sha256']=='c08fb4bcfcab748885f45216b9d800350849854aba39cad76f5d254c634bd587';out=json.loads((R/outref['path']).read_text())
 candidates=[]
 for x in out['evidence_refs']:
  if x['path'].startswith('results/formal_main_v2/pulls/') and x['path'].endswith('/receipt.json'):
   v=json.loads((R/x['path']).read_text())
   if '3043877' in {str(q['job_id']) for q in v['selected_jobs']}:
    assert sha(R/x['path'])==x['sha256'];candidates.append(x)
 assert len(candidates)==1
 normal=mod('scripts/review_formal_segment.py','566408f7f72bd3d878204175573a9c08b01db67be69358ed4a8ac2d0e0603790','root_normal1644')
 result=normal.review('3043877',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',pull_receipt=candidates[0]['path'],verify_server_resume=True,root=R)
 assert result['completed_by_arm']=={'A':5000,'B':5000}
 rp=R/result['output_relative']/'segment_reviews/3043877.json';checks=[]
 pairroot=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal/k64/seed41')
 for arm in ['A','B']:
  receipt=json.loads((R/result['output_relative']/arm/'deployment_receipt.json').read_text())
  assert receipt['training_complete'] and receipt['completed_updates']==5000
  assert [e['update'] for e in receipt['evaluations']]==list(range(0,5001,500))
  target=pairroot/arm/'best.pt';st=target.stat();digest=c.file_sha(target);assert digest==receipt['checkpoint_sha256'] and st==target.stat()
  checks.append(dict(arm=arm,path=str(target),sha256=digest,bytes=st.st_size,selected_update=receipt['metadata']['update'],validation_metric=receipt['metadata']['validation_metric']))
 sr=write(B+'/3043877_selected_server.json',dict(status='verified_actual_server_bytes',job_id='3043877',root_review=ref(rp),checks=checks,weights_copied=False,optimizer_rng_deserialized=False))
 rr=write(B+'/3043877_root_terminal.json',dict(root_review=ref(rp),selected_server=sr,machine_original_outcome=outref,pull=candidates[0],completed_by_arm=result['completed_by_arm'],pair_allocated_GPU_seconds=result['pair_allocated_gpu_seconds'],independent_review_integrated=False))
 assert sha(statepath)==state_sha
 print(json.dumps(dict(status=result['status'],root_review=ref(rp),root_terminal=rr,selected=sr,state_unchanged=True)))
