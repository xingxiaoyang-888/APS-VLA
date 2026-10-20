from pathlib import Path
import hashlib,json,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1038'
I='.local/object64_recovery_independent_0238/independent_review.json'
N='results/formal_main_v2/libero_object/k64/seed23/training/segment_reviews/3044017_independent.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(s):return dict(path=s,sha256=h(R/s))
def rd(s):return json.loads((R/s).read_bytes())
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('pub0238',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json')
 assert h(R/I)=='25c78029fa2b5456ea07cf596e518356f96f5acba252b6fe4ef6bc1a5e7b97b0'
 i=rd(I);rr=i['root_review'];assert h(R/rr['path'])==rr['sha256']=='2bffb9a9194b4c1b434b0c79491d165ce6f14d12305f3ebe9b6f4843af288d84'
 assert i['status']=='passed_original_target_recovery_only' and i['completed_by_arm']=={'A':500,'B':500}
 assert i['all173_source_R_and_S_match'] and i['same_full40000_sampling_order'] and i['historical_failure_preserved']
 assert i['cost']['all_pair_allocated_GPU_seconds']==5210 and i['cost']['retained_FAILED_GPU_seconds']==69 and i['cost']['successful_recovery_GPU_seconds']==5141
 assert not i['new_submission_authorized'] and not i['continuous5000_admission_authorized'] and not i['final_release_authorized']
 for a in ['A','B']:
  x=i['arms'][a];assert x['completed_updates']==500 and x['cursor']==x['actual_samples']==x['unique_samples']==4000
  assert x['resumed_from_existing_checkpoint'] is False and [v['update'] for v in x['validation']]==[0,500] and all(v['windows']==204 for v in x['validation'])
 for rel,pin in i['read_evidence_sha256'].items():
  p=Path(rel) if Path(rel).is_absolute() else R/rel
  assert h(p)==pin,rel
 with (R/N).open('xb') as f:f.write((R/I).read_bytes())
 assert h(R/N)==h(R/I)
 result=dict(status='original500_root_and_independent_review_published',canonical=ref(N),source=ref(I),root_review=rr,completed_by_arm={'A':500,'B':500},new_reviewed_updates=1000,new_complete_groups=0,new_submission_authorized=False,continuous5000_admission_authorized=False,state_changed=False,weights_copied=False)
 with (R/B/'Object3044017_independent_publication.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
 with (R/B/'root_operations/publish_object64_independent_0238.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 assert h(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps(result),flush=True)
