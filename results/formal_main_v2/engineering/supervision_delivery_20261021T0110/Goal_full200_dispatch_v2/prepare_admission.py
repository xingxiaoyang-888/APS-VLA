"""Root-only admission JSON builder; prints bytes, never writes state or submits."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
DISPATCH=R/'scripts/ops/formal_goal_full200_dispatch_v1/dispatch.py'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--dispatch-sha256',required=True)
 p.add_argument('--runtime-review',required=True)
 p.add_argument('--dispatch-review',required=True)
 p.add_argument('--actual-P-verification',dest='capture',required=True)
 p.add_argument('--root-reviewed',action='store_true')
 a=p.parse_args()
 if not a.root_reviewed or Path.cwd().resolve()!=R:raise ValueError('explicit root review and canonical cwd required')
 raw=DISPATCH.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=a.dispatch_sha256:raise ValueError('dispatch source SHA differs')
 s=importlib.util.spec_from_file_location('_goal_dispatch_build_root',DISPATCH);g=importlib.util.module_from_spec(s);sys.modules[s.name]=g
 exec(compile(raw,str(DISPATCH),'exec'),g.__dict__)
 package=g.runtime_package(g.P);g.require(g.runtime_package(R)==package,'exact R/P runtime source closure')
 for path,pin in g.source_map().items():g.raw(g.P/path,pin)
 scope=g.read(R/g.BASE/'scope.json',g.SCOPE_SHA)
 g.require(scope['runtime_files']==package['files'],'scope runtime closure differs')
 runtime_ref=g.ref(R,g.relative(a.runtime_review));runtime=g.archive_ref(runtime_ref)
 dispatch_ref=g.ref(R,g.relative(a.dispatch_review));dispatch=g.archive_ref(dispatch_ref)
 g.require(str(runtime.get('status','')).startswith('passed') and runtime.get('package_manifest_sha256')==g.RUNTIME_MANIFEST_SHA
  and runtime.get('package_files')==package['files'] and runtime.get('blockers')==[] and runtime.get('reviewed_by') not in (None,'root'),'runtime independent source proof required')
 g.require(dispatch.get('kind')=='Goal_full200_atomic_dispatch_independent_review' and dispatch.get('status')=='passed'
  and dispatch.get('dispatch_files')==g.source_map() and dispatch.get('package_manifest_sha256')==g.RUNTIME_MANIFEST_SHA
  and dispatch.get('runtime_files')==package['files'] and dispatch.get('blockers')==[]
  and dispatch.get('review_scope')=='source_and_CPU_only' and dispatch.get('GPU_execution_authorized') is False,'exact dispatcher independent proof required')
 auth=g.read(R/g.AUTH);g.require(g.raw(g.P/g.AUTH)==g.raw(R/g.AUTH),'R/P auth differ')
 e=g.load(g.P/g.PROD/'entry.py',package['files'][g.PROD+'/entry.py'],'_goal_root_build_metadata')
 e.validate_authorization(auth,package['files'][g.PROD+'/config.json'],g.RUNTIME_MANIFEST_SHA,package['files'][g.PROD+'/entry.py'])
 for role in ('root','independent'):
  rr=auth[role+'_review'];rel=g.relative(str(Path(rr['path']).relative_to(g.P)))
  g.require(g.raw(g.P/rel,rr['sha256'])==g.raw(R/rel,rr['sha256']),'R/P readiness differ')
  e.check_review(g.read(g.P/rel),role,g.RUNTIME_MANIFEST_SHA,package['files'][g.PROD+'/config.json'])
 capref=g.ref(R,g.relative(a.capture));capture=g.read_ref(R,capref)
 argv=[str(g.H/'venv/bin/python'),'-B',str(g.P/g.PROD/'entry.py'),'--verify','--package-manifest-sha256',g.RUNTIME_MANIFEST_SHA]
 g.require(capture.get('kind')=='Goal_full200_actual_P_verification_capture' and capture.get('argv')==argv
  and capture.get('returncode')==0 and capture.get('runtime_files')==package['files'],'actual P original captured process required')
 prior=g.runtime_output(json.loads(capture['stdout']),package)
 current=g.runtime_output(e.verify_published(g.RUNTIME_MANIFEST_SHA),package)
 g.require(prior['identity']==current['identity'],'actual full200 identity changed')
 result=g.admission_fixed()
 result.update(dispatch_files=g.source_map(),runtime_files=package['files'],authorization=g.ref(R,g.AUTH),
  runtime_independent_review=runtime_ref,dispatch_independent_review=dispatch_ref,actual_P_verification=capref,prepared_utc=g.utc())
 g.check_admission_fields(result)
 sys.stdout.buffer.write(g.canonical(result)+b'\n')
if __name__=='__main__':main()
