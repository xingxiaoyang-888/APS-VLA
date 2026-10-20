"""Read-only source/complete-pair checks and original factory for four dev-only candidates."""
import contextlib,hashlib,importlib.util,io,json,os,sys,traceback
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/nonLong_development_plans_20261020T1418'
STATE='.local/nonLong_development_plans_20261020T1418/state_source.json';STATE_SHA='1859a623537af884c7f7d41ad9965497b6d73f5288dbe7258d49eac4b3aeb80f'
HELPER='scripts/formal_execution_manifests.py';HELPER_SHA='614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89'
GROUPS=[('libero_spatial', 256, 23, '3034604', '809bd0e648ece4a335431f5e8314649c8b7b5ca36b179231f4c8702af68d5c98', 'results/formal_main_v2/engineering/completed_pairs_independent_0547/libero_spatial_k256_seed23_independent.json', '9276d3727c0702ac8358a1404c7fc45b37d62c5c27358841239313c33eb7e6c8'), ('libero_object', 256, 23, '3042627', 'ef4fa5c45dd73db1fef8f68a18d563959b408337cd3a1992613d673e15540e0a', 'results/formal_main_v2/libero_object/k256/seed23/training/segment_reviews/3042627_independent.json', 'e87a594516432526e718b80bd284146c164eac1c42f864c5bc349a3c42a83c98'), ('libero_goal', 256, 23, '3037821', '11a239df861d502bfc65befb74c1a991ade37cf5cd3f89cba786ce749aef6b46', 'results/formal_main_v2/libero_goal/k256/seed23/training/segment_reviews/3037821_independent.json', 'ed9d27395bc21f697150f26fa8a70ea9bcc86fc262239c09ec49c5b91fbc79ac'), ('libero_spatial', 256, 41, '3034611', 'aeeb152272e355a91f3419121a52a38343cfe5a2e79923eefc2cecec10772835', 'results/formal_main_v2/engineering/completed_pairs_independent_0547/libero_spatial_k256_seed41_independent.json', '1743fc2a975cedecdfad4a591d611464ec1a24ba3f1c97ee3e3e7a7aba70445d')]
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
 b=read(HELPER,HELPER_SHA);spec=importlib.util.spec_from_file_location('nonLong20261020T1418_factory',R/HELPER);h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;exec(compile(b,str(R/HELPER),'exec'),h.__dict__)
 plans=[];checks=[]
 for suite,budget,seed,jid,rsha,irpath,isha in GROUPS:
  pair=f'{suite}_k{budget}_seed{seed}';methods=[f'A{budget}_seed{seed}',f'B{budget}_seed{seed}'];base=f'results/formal_main_v2/{suite}/k{budget}/seed{seed}/training';summary=json.loads(read(base+'/training_summary.json'))
  rr=json.loads(read(base+'/segment_reviews/'+jid+'.json',rsha));ir=json.loads(read(irpath,isha))
  assert summary['job_id']==jid and summary['status']=='completed' and summary['pair_complete'] is True
  assert rr['status']=='passed' and rr['completed_by_arm']=={'A':5000,'B':5000}
  assert ir['status'] in ('passed','passed_complete_training_only') and str(ir['job_id'])==jid
  complete_pair=s['formal_main_progress']['completed_training_pairs'][pair]
  assert complete_pair['completed_by_arm']=={'A':5000,'B':5000}
  if pair in s['autonomous_training_v1']['completed_pairs']:
   assert s['autonomous_training_v1']['completed_pairs'][pair]['completed_by_arm']=={'A':5000,'B':5000}
  else:
   assert pair=='libero_object_k256_seed23' and complete_pair['root_review']==base+'/segment_reviews/'+jid+'.json' and complete_pair['root_review_sha256']==rsha
   assert complete_pair['independent_review']==irpath and complete_pair['independent_review_sha256']==isha and complete_pair['verification_kind']=='root_startup_consumer_and_independent_raw_reconstruction'
  root_adoption=complete_pair.get('terminal_root_and_independent_review')
  if root_adoption:
   assert root_adoption['completed_by_arm']=={'A':5000,'B':5000}
   assert root_adoption['independent_review']=={'path':irpath,'sha256':isha}
   rr2=json.loads(read(root_adoption['root_review']['path'],root_adoption['root_review']['sha256']))
   assert rr2['status'] in ('passed','accepted_training_integrity_not_scientific_efficacy','passed_complete_training_only')
  matches=[j for j in s['registered_jobs'] if j.get('suite')==suite and j.get('mode')=='development' and set(j.get('method_ids',[]))&set(methods)]
  assert not matches,'Already registered development methods '+str(matches)
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
  plans.append(dict(suite=suite,budget=budget,seed=seed,method_ids=methods,expected_trials=200,candidate=mr,evidence=er,canonical_path='results/formal_main_v2/execution/nonLong_action_v1_20261020T1418/'+name))
  checks.append(dict(suite=suite,budget=budget,seed=seed,root_review=ref(base+'/segment_reviews/'+jid+'.json'),independent_review=ref(irpath),training_summary=ref(base+'/training_summary.json'),completed_arms=arms,terminal_root_adoption=root_adoption,existing_development_method_matches=[],actual_weight_bytes_read=False))
 out('training_and_duplicate_checks.json',dict(status='source_metadata_checks_passed_not_development_readiness',state=ref(str((D/'state_at_planning.json').relative_to(R))),pairs=checks))
 index=out('execution_manifest_candidates.json',dict(schema='formal_main_v2',status='candidate_pending_root_publication',plans=plans,total_trials=800,final_enabled=False,production_modified=False))
 print(json.dumps({'status':'candidates_ready_for_root_publication','index':index,'plans':plans}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  out('factory_failure_v1.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc()));raise
