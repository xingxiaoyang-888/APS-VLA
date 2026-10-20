"""Read-only source/complete-pair checks and original factory for three dev-only candidates."""
import contextlib,hashlib,importlib.util,io,json,os,sys,traceback
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/nonLong_development_plans_1220'
STATE='results/formal_main_v2/preflight/heartbeat_20261020T2020/state_before.json';STATE_SHA='a32924884da6a900f98aea682642c70047c2b48df51d4d5524a7b4318f5e89b8'
HELPER='scripts/formal_execution_manifests.py';HELPER_SHA='614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89'
GROUPS=[('libero_spatial',41,'3023249','5749480011fdf58282d4f99eaa298236764a2956bfd4950d7516a08a621c4a08','8e88afc34766cd36562e33159ca7b612796a4cecc4593b2ac61c2798df8bdc47'),('libero_object',41,'3036313','5271261a84b6ad1bcbfd924788c31e1143b2183aa3fadcab0360930f058f8dd9','046b6e9b7001ad314920563d42b25ed565dab39496407d8514ee566c17272338'),('libero_goal',23,'3039981','e742b9453c814788b3772768817a65a35da5e52bafc9ecdcc65688fb86c0273c','6126c326b153586b2ce863e0f3d134d4d27c1274c4eb3a4d6712d4f58676cf75')]
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
 b=read(HELPER,HELPER_SHA);spec=importlib.util.spec_from_file_location('nonLong1220_factory',R/HELPER);h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;exec(compile(b,str(R/HELPER),'exec'),h.__dict__)
 plans=[];checks=[]
 for suite,seed,jid,rsha,isha in GROUPS:
  pair=f'{suite}_k128_seed{seed}';methods=[f'A128_seed{seed}',f'B128_seed{seed}'];base=f'results/formal_main_v2/{suite}/k128/seed{seed}/training';summary=json.loads(read(base+'/training_summary.json'))
  rr=json.loads(read(base+'/segment_reviews/'+jid+'.json',rsha));ir=json.loads(read(base+'/segment_reviews/'+jid+'_independent.json',isha))
  assert summary['job_id']==jid and summary['status']=='completed' and summary['pair_complete'] is True
  assert rr['status']=='passed' and rr['completed_by_arm']=={'A':5000,'B':5000}
  assert ir['status'] in ('passed','passed_complete_training_only') and str(ir['job_id'])==jid
  assert s['autonomous_training_v1']['completed_pairs'][pair]['completed_by_arm']=={'A':5000,'B':5000}
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
  plans.append(dict(suite=suite,seed=seed,method_ids=methods,expected_trials=200,candidate=mr,evidence=er,canonical_path='results/formal_main_v2/execution/nonLong_action_v1_1220/'+name))
  checks.append(dict(suite=suite,seed=seed,root_review=ref(base+'/segment_reviews/'+jid+'.json'),independent_review=ref(base+'/segment_reviews/'+jid+'_independent.json'),training_summary=ref(base+'/training_summary.json'),completed_arms=arms,existing_development_method_matches=[],actual_weight_bytes_read=False))
 out('training_and_duplicate_checks.json',dict(status='source_metadata_checks_passed_not_development_readiness',state=ref(str((D/'state_at_planning.json').relative_to(R))),pairs=checks))
 index=out('execution_manifest_candidates.json',dict(schema='formal_main_v2',status='candidate_pending_root_publication',plans=plans,total_trials=600,final_enabled=False,production_modified=False))
 print(json.dumps({'status':'candidates_ready_for_root_publication','index':index,'plans':plans}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  out('factory_failure_v1.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc()));raise
