from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_full200_dispatch_20261021T0110'
src=R/'.local/object_single_error_gateway_20261021T0110/verify_cpu.py'
b=src.read_bytes();assert hashlib.sha256(b).hexdigest()=='21149d9e50067520598de510c7f1e2c4b225279cec2e7ad7f7e86b3c1f120340'
text=b.decode();lines=text.splitlines();nodes={n.name:n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def get(n):
 v=nodes[n];return '\n'.join(lines[v.lineno-1:v.end_lineno])+'\n'
header="""from pathlib import Path
from contextlib import contextmanager
import argparse,copy,hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_full200_dispatch_20261021T0110'
p=D/'dispatch.py';sp=importlib.util.spec_from_file_location('_goal_full200_private_dispatch_CPU',p)
g=importlib.util.module_from_spec(sp);sys.modules[sp.name]=g;exec(compile(p.read_bytes(),str(p),'exec'),g.__dict__)
positive=[];negative=[]
"""
fixture="""def bundle():
 ah='a'*64;inv=dict(CPU_fixture=True)
 raw=g.canonical(inv)+b'\\n'
 return dict(authorization=inv,authorization_sha256=ah,invocation_bytes=raw,authorization_ref=dict(path=g.AUTH,bytes=len(raw),sha256=ah),
  token='cti-goal-full200-v1:'+ah,comment='cti-goal-full200-v1:'+ah,sources={'CPU_fixture':True},
  runtime_package={'files':{g.PROD+'/config.json':'b'*64,g.PROD+'/entry.py':'c'*64}},
  admission={'prepared_utc':'2026-10-21T01:10:00+00:00'},admission_ref=dict(path=g.ADMISSION,bytes=1,sha256='d'*64))
"""
fake=get('Fake').replace('def publish_invocation(self):','def publish_reservation(self):').replace("'3021394'","'3053440'")
at=fake.index('  def committed') if '  def committed' in fake else fake.index(' def committed')
fake=fake[:at]+""" def dispatch_proof(self,jid,state,version):
  self.at('dispatch_proof')
  if self.state['registered_jobs'][-1]['job_id']!=jid:raise ValueError('dispatch before unique registration')
  return {'CPU_fixture':True}
"""+fake[at:]
tx=get('transaction_checks').replace("'3021394'","'3053440'").replace("'cti-object-single-error:unknown'","'cti-goal-full200-v1:unknown'")
tx=tx.replace("('linked_failure_sha256',g.FAILURE_SHA),","")
tx=tx.replace("args[-2]==str(g.P/g.BASE/'run.slurm')","args[-1]==str(g.P/g.PROD/'run.slurm')")
tx=tx.replace("'actual_released','committed',","'actual_released','dispatch_proof','committed',")
proj=get('projection_checks')
proj=proj.replace("ok(derived==result['derived'],","ok({k:v for k,v in derived.items() if k!='original_GPU_seconds'}=={k:v for k,v in result['derived'].items() if k!='original_GPU_seconds'},")
proj=proj.replace("'3021844'","'3054127'").replace("('elapsed_seconds',4925)","('elapsed_seconds',839)")
proj=proj.replace("target['pair_id']=g.PAIR","target['pair_id']=g.PAIR").replace("['suite']='libero_object'","['suite']='libero_goal'").replace('other Object allocation','other Goal allocation')
proj=proj.replace("TimeLimit='00:30:00'","TimeLimit='02:00:00'").replace("Command=str(g.P/g.BASE/'run.slurm')","Command=str(g.P/g.PROD/'run.slurm')")
body=header+'\n'.join(get(n) for n in ['ok','no','Interruption'])+fixture+fake+tx+get('actual_observation_checks')+proj
tail="""def main():
 parser=argparse.ArgumentParser();parser.add_argument('--verify-saved',action='store_true');a=parser.parse_args()
 transaction_checks();actual_observation_checks()
 lp=R/'.local/object_single_error_gateway_20261021T0110/live_inputs.json'
 live=json.loads(lp.read_bytes());derived=projection_checks(live)
 ok(derived['original_GPU_seconds']==1643,'old two Goal engineering allocations803+840 retained once')
 ok(all(not x.startswith('sbatch') for x in []),'CPU model creates no real scheduler allocation')
 source=R/'.local/goal_full200_author_20261021T0110/package'
 package=json.loads((source/'package_manifest.json').read_bytes())
 for rel,h in package['files'].items():
  ok(hashlib.sha256((source/Path(rel).name).read_bytes()).hexdigest()==h,'real candidate runtime file SHA '+rel)
 config=json.loads((source/'config.json').read_bytes())
 ok(config['maximum_trials']==200 and config['unique_development_states']==100 and config['method_ids']==['A256_seed17','B256_seed17']
  and config['maximum_total_control_steps']==60000 and config['maximum_total_policy_queries']==7600 and not config['automatic_retry'],'real full200 source scientific bound')
 result=dict(schema='formal_main_v2',kind='Goal_full200_atomic_dispatch_CPU',status='passed_CPU_dispatch_candidate',
  positive_count=len(positive),negative_count=len(negative),positive=positive,negative=negative,
  dispatch_sha256=hashlib.sha256((D/'dispatch.py').read_bytes()).hexdigest(),
  runtime_package_manifest_sha256=hashlib.sha256((source/'package_manifest.json').read_bytes()).hexdigest(),
  original_saved_projection=dict(path=str(lp.relative_to(R)),sha256=hashlib.sha256(lp.read_bytes()).hexdigest(),state_sha256=live['state_sha256'],utc=live['result']['utc']),
  source173_unchanged=True,old_Object_package_changed=False,new_Slurm_queries=0,new_Slurm_submissions=0,
  new_GPU_seconds=0,new_scientific_trials=0,actual_P_new_package_verified=False,production_admitted=False)
 if a.verify_saved:
  assert result==json.loads((D/'CPU_report.json').read_bytes());print(json.dumps(dict(status='read_only_rebuild_passed',positive=len(positive),negative=len(negative))))
 else:
  with (D/'CPU_report.json').open('x') as f:json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2)
  print(json.dumps(dict(status=result['status'],positive=len(positive),negative=len(negative))))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  p=D/('failure_'+g.utc().replace(':','').replace('+','_')+'.json')
  with p.open('x') as f:json.dump(dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),positive=positive,negative=negative,Slurm_submitted=False),f,ensure_ascii=False,indent=2)
  raise
"""
out=body+tail;compile(out,str(D/'verify_cpu.py'),'exec')
p=D/'verify_cpu.py';assert not p.exists();p.write_text(out);print(hashlib.sha256(p.read_bytes()).hexdigest())
