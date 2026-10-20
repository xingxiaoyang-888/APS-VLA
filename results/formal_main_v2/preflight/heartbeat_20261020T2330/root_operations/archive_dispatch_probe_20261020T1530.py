from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2330';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p.relative_to(R)) if p.is_relative_to(R) else str(p),sha256=h(p),bytes=p.stat().st_size)
def cp(src,dst,pin):
 assert (src.is_relative_to(R) or src.is_relative_to(P)) and dst.is_relative_to(R) and h(src)==pin
 assert not any(z.is_symlink() for z in [src,*src.parents,dst,*dst.parents])
 assert src.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5')
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert dst.read_bytes()==src.read_bytes()
 else:
  with dst.open('xb') as f:f.write(src.read_bytes())
 return dict(source=ref(src),archive=ref(dst))
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archivedispatchprobe1530ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');copies=[]
 for name,mn,pin,dest in [('.local/dispatch_independent_20261020T1530','delivery_manifest.json','f5e19f81c7b074f02598283b1b98a73c9a5050f716db75234e4ca1b1243a90e4','dispatch_independent'),('.local/goal_probe_terminal_20261020T1530','manifest.json','8afb04c2d24d3a28c9f2eb3c250d56b9892f129d707224981650db6afb7d14a4','Goal_probe_terminal')]:
  root=R/name;mf=root/mn;assert h(mf)==pin
  for row in json.loads(mf.read_bytes())['files']:
   src=Path(row['path']);src=src if src.is_absolute() else R/src;rel=src.relative_to(root);assert src.stat().st_size==row['bytes']
   copies.append(cp(src,R/E/dest/rel,row['sha256']))
  copies.append(cp(mf,R/E/dest/mn,pin))
 cpplan=R/E/'Goal_probe_terminal/nonweight_copy_plan.json';assert h(cpplan)=='32bf312ac0baa15f851836fedfb0efaf277724eaa859736e56b22f6c7d96f9f9'
 plan=json.loads(cpplan.read_bytes());assert plan['files_count']==len(plan['files'])==8
 for row in plan['files']:
  src=Path(row['source']);dst=Path(row['destination']);assert src.is_relative_to(P) and dst.is_relative_to(R) and src.stat().st_size==row['bytes'];copies.append(cp(src,dst,row['sha256']))
 summary=R/E/'Goal_probe_terminal/terminal_summary.json';assert h(summary)=='b5a8b094d523bb671945109b5a44b63d63c1d5b1f6b35c140f4dfb89926eddf4'
 x=json.loads(summary.read_bytes());assert x['external_queries']==12 and x['dummy_control_actions']==120 and x['policy_control_actions']==0 and not x['original_mismatch_reproduced'] and x['original200_HOLD_unchanged'] and x['allocated_GPU_seconds']==354
 assert h(R/'results/experiment_supervisor/state.json')==before
 out=R/B/'dispatch_and_probe_terminal_delivery.json'
 with out.open('x') as f:json.dump(dict(status='exact_nonweight_sources_archived',copies=copies,probe=ref(summary),probe_cause='undetermined',scientific_release=False,raw_NPZ_remain_P_with_exact_manifest=True,state_unchanged=True,new_GPU_jobs=0),f,ensure_ascii=False,sort_keys=True,indent=2);f.write(chr(10))
 print(json.dumps(dict(receipt=ref(out),files=len(copies),probe_scientific_release=False)),flush=True)
