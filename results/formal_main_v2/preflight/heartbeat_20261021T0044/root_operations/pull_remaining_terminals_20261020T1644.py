from pathlib import Path
import hashlib,importlib.util,json,sys,shutil
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert sha(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def write(rel,v):
 p=R/rel
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return ref(p)
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','cti_lastpull_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=sha(state);s=json.loads(state.read_text())
 a=s['autonomous_training_v1'];assert a.get('pending_submission') is None
 src=R/'.local/reconcile_object_3052166_20261020T1644.py';assert sha(src)=='b173bc9ac02a24a2eb3a3873cfbaba9b577a20ead75b531b9f48e1ca17ff6c3f'
 dst=R/B/'root_operations/reconcile_libero_object_k256_seed23_3052166_20261020T1644.py';dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert sha(dst)==sha(src)
 else:shutil.copyfile(src,dst)
 repair=write(B+'/3052166_postcommit_archive_only_repair.json',{'status':'executed_source_archived_only','source':ref(src),'archive':ref(dst),'reconciliation_not_reexecuted':True,'new_submission':False,'state_unchanged':True})
 puller=load('scripts/pull_formal_results.py','b1b141ddb75fd8641d6f5e7f68dbfea462e1fe907ced2f2a98338a1145d77061','cti_lastpull_original')
 report,path=puller.pull(['3044844','3050870','3050890','3050901','3050916'],timeout=180)
 assert report['status']=='verified_nonweight_snapshot' and report['final_evidence'] and not report['weights_copied'] and not report['sealed_initial_states_copied']
 assert {str(x['job_id']) for x in report['selected_jobs']}=={'3044844','3050870','3050890','3050901','3050916'}
 assert sha(state)==before
 result=write(B+'/remaining_terminal_canonical_pull.json',{'status':'verified_nonweight_snapshot','receipt':ref(path),'files':len(report['files']),'selected_job_ids':[x['job_id'] for x in report['selected_jobs']],'state_unchanged':True,'postcommit_archive_only_repair':repair})
 print(json.dumps({'status':report['status'],'receipt':ref(path),'root_record':result,'files':len(report['files'])}))
