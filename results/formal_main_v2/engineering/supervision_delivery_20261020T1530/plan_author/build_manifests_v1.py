"""Read-only source/complete-pair checks and original factory for four dev-only candidates."""
import contextlib,hashlib,importlib.util,io,json,os,sys,traceback
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/nonLong64_development_plans_20261020T1530'
STATE='.local/nonLong64_development_plans_20261020T1530/state_source.json';STATE_SHA='86d2c2ad011cbb52c7367cc93703f67ad6449bb74548fd9a98955244c7658355'
HELPER='scripts/formal_execution_manifests.py';HELPER_SHA='614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89'
GROUPS=[('libero_spatial', 64, 17, '3034616', 'ac7fbc4642ae077b0fa7f251aabdedbe880a4b6ef15b31b8be17d8587f3be10a', 'results/formal_main_v2/engineering/completed_pairs_independent_0547/libero_spatial_k64_seed17_independent.json', 'fcb1399cdb1c1caf24ae99186110b0bcae2f58290c8c87f9a478e7e7f100197f'), ('libero_spatial', 64, 41, '3034689', '613b0245d29ce9b2349063bc9ca32ef3fde6f21c05c8a9f9380de41617ab1cc4', 'results/formal_main_v2/engineering/completed_pairs_independent_0547/libero_spatial_k64_seed41_independent.json', '6ef35840966f673c6c8f6a6789f32b848ed2eca5bec2b0b2411f12cc4bde3e77'), ('libero_object', 64, 17, '3037054', 'b7e528439916fd881668ca2d2960735a8aa751b05e198fff6e15cccb68ec1756', 'results/formal_main_v2/libero_object/k64/seed17/training/segment_reviews/3037054_independent.json', 'f14b26c65a7a337dd629d2ae87ca10d94e9ad31d96dffcfb0e6cbf39188fefd7'), ('libero_object', 64, 41, '3037535', 'd2836fab19c5c11cd1baba1a102ec7e677ebab781091f2b2bcb103f35825ddf8', 'results/formal_main_v2/libero_object/k64/seed41/training/segment_reviews/3037535_independent.json', 'a1643466dd8bbe032261c195c8ebef6ef214c373d82ab4ede6829450a1623301')]
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No subprocess/network/GPU')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   assert not any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts),'no forbidden data'
   assert not set(p.suffixes)&{'.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init'},'no weights'
   wr=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC)))
   if wr:assert D in p.parents,'private output only'
sys.addaudithook(guard)
def shab(b):return hashlib.sha256(b).hexdigest()
def read(rel,pin=None):
 b=(R/rel).read_bytes();assert pin is None or shab(b)==pin,'SHA drift '+rel;return b
def ref(rel):
 b=read(rel);return dict(path=rel,sha256=shab(b),bytes=len(b))
def out(name,obj):
 b=obj if isinstance(obj,bytes) else (json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
 with (D/name).open('xb') as f:f.write(b)
 return ref(str((D/name).relative_to(R)))
def main():
 sb=read(STATE,STATE_SHA);s=json.loads(sb);out('state_at_planning.json',sb);assert s.get('pending_submission') is None
 b=read(HELPER,HELPER_SHA);spec=importlib.util.spec_from_file_location('nonLong6420261020T1530_factory',R/HELPER);h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;exec(compile(b,str(R/HELPER),'exec'),h.__dict__)
 plans=[];checks=[];skipped=[]
 for suite,budget,seed,jid,rsha,irpath,isha in GROUPS:
  pair=f'{suite}_k{budget}_seed{seed}';methods=[f'A{budget}_seed{seed}',f'B{budget}_seed{seed}'];base=f'results/formal_main_v2/{suite}/k{budget}/seed{seed}/training';summary=json.loads(read(base+'/training_summary.json'))
  rr=json.loads(read(base+'/segment_reviews/'+jid+'.json',rsha));ir=json.loads(read(irpath,isha))
  assert summary['job_id']==jid and summary['status']=='completed' and summary['pair_complete'] is True
  assert rr['status']=='passed' and rr['completed_by_arm']=={'A':5000,'B':5000}
  assert ir['status'] in ('passed','passed_complete_training_only') and str(ir['job_id'])==jid
  assert s['autonomous_training_v1']['completed_pairs'][pair]['completed_by_arm']=={'A':5000,'B':5000}
  complete_pair=s['formal_main_progress']['completed_training_pairs'][pair]
  root_adoption=complete_pair.get('terminal_root_and_independent_review')
  if root_adoption:
   assert root_adoption['completed_by_arm']=={'A':5000,'B':5000}
   assert root_adoption['independent_review']=={'path':irpath,'sha256':isha}
   rr2=json.loads(read(root_adoption['root_review']['path'],root_adoption['root_review']['sha256']))
   assert rr2['status'] in ('passed','accepted_training_integrity_not_scientific_efficacy','passed_complete_training_only')
  matches=[j for j in s['registered_jobs'] if j.get('suite')==suite and j.get('mode')=='development' and set(j.get('method_ids',[]))&set(methods)]
  artifacts=[]
  for scanroot in (R,Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')):
   for candidate in (scanroot/f'results/formal_main_v2/{suite}/downstream/development').glob('*/attempt*/config.json'):
    prior=json.loads(candidate.read_bytes());ids={m['identity']['method_id'] for m in prior['manifest']['methods']}
    if ids&set(methods):artifacts.append({'path':str(candidate),'sha256':shab(candidate.read_bytes())})
  if matches or artifacts:
   skipped.append({'pair':pair,'registered_job_ids':[str(j['job_id']) for j in matches],'existing_artifacts':artifacts,'reason':'Never duplicate any registered or existing development method output.'});continue
  arms={}
  for arm in ('A','B'):
   a=summary['arms'][arm];ev=a['evaluations'];assert [e['update'] for e in ev]==list(range(0,5001,500))
   best=min(ev,key=lambda e:(e['validation_metric'],e['update']));assert best['update']==a['best_update'] and best['validation_metric']==a['best_validation_metric']
   assert a['training_updates_completed']==5000 and a['committed_samples']==40000
   receipt=json.loads(read(base+'/'+arm+'/deployment_receipt.json'));assert receipt['checkpoint_sha256']==a['best_checkpoint_sha256']
   arms[arm]={k:a[k] for k in ('best_update','best_checkpoint_sha256','best_validation_metric','training_updates_completed','committed_samples')}
  name=f'{pair}_development.json';args=['--project-root',str(R),'development','--suite',suite,'--methods',*methods,'--source-inventory','results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','--output',str((D/name).relative_to(R))]
  capture=io.StringIO()
  with contextlib.redirect_stdout(capture):rc=h.main(args)
  out(pair+'_manifest_factory_call.json',dict(argv=args,returncode=rc,stdout=capture.getvalue(),helper=ref(HELPER)))
  assert rc==0,'original factory rejected '+pair
  mr=ref(str((D/name).relative_to(R)));er=ref(str((D/(name+'.evidence.json')).relative_to(R)));m=json.loads(read(mr['path']));assert [x['identity']['method_id'] for x in m['methods']]==methods
  plans.append(dict(suite=suite,budget=budget,seed=seed,method_ids=methods,expected_trials=200,candidate=mr,evidence=er,canonical_path='results/formal_main_v2/execution/nonLong_action_v1_20261020T1530/'+name))
  checks.append(dict(suite=suite,budget=budget,seed=seed,root_review=ref(base+'/segment_reviews/'+jid+'.json'),independent_review=ref(irpath),training_summary=ref(base+'/training_summary.json'),completed_arms=arms,terminal_root_adoption=root_adoption,existing_development_method_matches=[],existing_R_P_development_artifacts=[],actual_weight_bytes_read=False))
 out('training_and_duplicate_checks.json',dict(status='source_metadata_checks_passed_not_development_readiness',state=ref(str((D/'state_at_planning.json').relative_to(R))),pairs=checks,skipped=skipped))
 index=out('execution_manifest_candidates.json',dict(schema='formal_main_v2',status='candidate_pending_root_publication',plans=plans,total_trials=200*len(plans),skipped=skipped,final_enabled=False,production_modified=False))
 print(json.dumps({'status':'candidates_ready_for_root_publication','index':index,'plans':plans}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  out('factory_failure_v1.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc()));raise
