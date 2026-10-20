"""Read-only original source-consumer probes; private candidate files only, no Slurm/network."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,os,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/remaining_development_inventory_20261020T1825'
HELPER='scripts/formal_execution_manifests.py';PIN='614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No child process/network/Slurm allowed')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in a.lower() or a.lower() in ('weights','checkpoints') for a in p.parts) or set(p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'}:raise RuntimeError('Forbidden payload read')
   writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
   if writing and D not in p.parents:raise RuntimeError('Private output only: '+str(p))
sys.addaudithook(guard)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def out(name,x):
 p=D/name
 with p.open('x') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
raw=(R/HELPER).read_bytes();assert hashlib.sha256(raw).hexdigest()==PIN
spec=importlib.util.spec_from_file_location('inventory1825_frozen_factory',R/HELPER);h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;exec(compile(raw,str(R/HELPER),'exec'),h.__dict__)
results=[]
for suite,methods,label in [('libero_spatial',['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'],'spatial_first6'),('libero_object',['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'],'object_first6'),('libero_spatial',['A64_seed23','B64_seed23'],'spatial64seed23'),('libero_object',['A64_seed23','B64_seed23'],'object64seed23')]:
 args=['--project-root',str(R),'development','--suite',suite,'--methods',*methods,'--source-inventory',INV,'--output',(D/(label+'_metadata_manifest.json')).relative_to(R).as_posix()]
 cap=io.StringIO();t=time.perf_counter()
 with contextlib.redirect_stdout(cap):rc=h.main(args)
 row=dict(label=label,suite=suite,methods=methods,returncode=rc,stdout=cap.getvalue(),factory={'path':HELPER,'sha256':PIN},argv=args,CPU_wall_seconds=time.perf_counter()-t,new_GPU_seconds=0,new_trials=0,readiness_claimed=False)
 row['output_ref']=out(label+'_original_factory_call.json',row)
 results.append(row)
assert results[0]['returncode']==results[1]['returncode']==0
assert results[2]['returncode']==results[3]['returncode']==2
print(json.dumps(out('original_source_consumer_probe_summary.json',dict(status='completed_expected_success_and_fail_closed',results=results,no_checkpoint_payloads_read=True,no_GPU_no_Slurm=True,scientific_admission=False)),ensure_ascii=False))
