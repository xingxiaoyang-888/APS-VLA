"""Read-only exact dependency preview for four originally planned development batches."""
from pathlib import Path
import hashlib,types,json,copy,time
from types import SimpleNamespace
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/nonLong_development_plans_1317';P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
p=D/'prepare_four_plans_v1.py';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='d5b9f1b6629db68971390108741615ce7e6ed62f76f25807b2d52b88e13868ca'
a=types.ModuleType('exact_nonLong_author_preview');a.__file__=str(p);exec(compile(raw,str(p),'exec'),a.__dict__)
t0=time.perf_counter();h=a.load('scripts/formal_execution_manifests.py');planner=a.load('scripts/ops/formal_downstream_supervisor.py');runtime=a.load(a.PRE+'runtime_scope.py');state=a.js(D/'state_at_planning.json');missing={};outputs=[]
for suite,budget,seed,name,msha,methods in a.GROUPS:
 args=dict(stage='development',source_inventory=a.INV,execution_manifest=a.DEST+'/'+name,output_relative=None,freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,resume=False,stop_after=None)
 science=planner.plan(SimpleNamespace(**args),copy.deepcopy(state),project=R,helper=h)
 a.require(science['invocation']['method_ids']==methods and science['invocation']['prior_job_ids']==[],'scope')
 out=a.write(f'dependency_preview_v1/{suite}_k{budget}_seed{seed}_scientific_plan.json',science);outputs.append(out)
 inv=science['invocation'];needed={**inv['watched_files'],**{str(P/n):v for n,v in inv['support_files'].items()}}
 scope=runtime.make_contract(project_root=R,source_root=a.S,suite=suite,stage='development');runtime.validate_contract(scope,project_root=R,source_root=a.S)
 for rel,pin in scope['dependencies'].items():needed[str(P/rel)]=pin
 for role,ref in scope['engineering_acceptance'].items():needed[str(P/ref['path'])]=ref['sha256']
 for path,pin in needed.items():
  target=Path(path);a.require(P in target.parents and target.resolve()==target,'P only');rel=target.relative_to(P).as_posix()
  if target.is_file():a.read(target,pin)
  else:
   src=R/rel;a.read(src,pin);row={'canonical_path':rel,'candidate_path':rel,'sha256':pin,'bytes':src.stat().st_size,'reason':'original unchanged P wrapper or runtime required exact file absent','group_keys':[]}
   if rel not in missing:missing[rel]=row
   missing[rel]['group_keys'].append(f'{suite}_k{budget}_seed{seed}')
report=dict(schema='formal_main_v2',kind='nonLong_exact_original_dependency_copy_requirements',status='root_publication_required',source_entry_sha256='d5b9f1b6629db68971390108741615ce7e6ed62f76f25807b2d52b88e13868ca',state_at_planning={'path':str((D/'state_at_planning.json').relative_to(R)),'sha256':a.sha(D/'state_at_planning.json')},files=list(missing.values()),plans=outputs,production_files_changed=False,GPU_calls=0,CPU_wall_seconds=time.perf_counter()-t0)
r=a.write('dependency_preview_v1/required_P_copies.json',report);print(json.dumps({'report':r,'missing_files':report['files'],'plans':outputs}))
