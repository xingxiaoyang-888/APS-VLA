from pathlib import Path
import hashlib,json,numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T1727'
refpath='results/formal_main_v2/downstream_reviews/3047982.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(R/refpath)=='45e76fbb32159d53dc7be7e5ca6b25d4d52815d44d0234063f30a69500567479'
review=json.loads((R/refpath).read_bytes());assert review['stage']=='collect' and review['scientific_complete'] and review['observations']==30 and review['completed_collection_trajectories']==10
base=Path(review['run_root']).relative_to('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA').as_posix()
expected=[base+f'/task{t:02d}/{phase}.npz' for t in range(10) for phase in ['first','middle','last']]
assert sorted(expected)==sorted(p for p in review['files'] if p.endswith('.npz'))
schema={'agentview_image':('|u1',[256,256,3]),'robot0_eye_in_hand_image':('|u1',[256,256,3]),'robot0_eef_pos':('<f8',[3]),'robot0_eef_quat':('<f8',[4]),'robot0_gripper_qpos':('<f8',[2])}
rows=[]
for name in expected:
 p=R/name;assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(R)
 pin=sha(p);assert pin==review['files'][name]==review['panel']['artifact_sha256'][str(Path(name).relative_to(base))]
 assert p.stat().st_size==394644
 with np.load(p,allow_pickle=False) as z:
  assert len(z.files)==5 and set(z.files)==set(schema)
  arrays={}
  for key,(dtype,shape) in schema.items():
   a=z[key];assert a.dtype.str==dtype and list(a.shape)==shape and not a.dtype.hasobject and np.isfinite(a).all()
   arrays[key]=dict(dtype=dtype,shape=shape)
 rows.append(dict(path=name,sha256=pin,bytes=p.stat().st_size,array_schema=arrays))
assert sum(row['bytes'] for row in rows)==11839320
out=dict(schema='formal_main_v2',kind='exact_collected_development_observation_NPZ_delivery_allowlist',status='passed',root_collect_review=dict(path=refpath,sha256=sha(R/refpath)),files=rows,observations=30,tasks=10,total_bytes=11839320,no_object_arrays=True,numpy_allow_pickle=False,only_raw_two_camera_images_and_current_robot_proprio=True,no_model_weights=True,no_sealed_or_final_initial_state_payload=True,no_data_transformation=True,files_below_Git100MiB=True,one_off_allowlist_not_general_NPZ_permission=True,independent_scientific_acceptance_still_required=True)
p=B/'observation_npz_delivery_allowlist.json'
with p.open('x') as f:json.dump(out,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(path=p.relative_to(R).as_posix(),sha256=sha(p),files=30,total_bytes=11839320)))
