from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/k64_spatial_reconcile_independent_20261020T1949';B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0349';S=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p.relative_to(R)),'sha256':h(p),'bytes':p.stat().st_size}
def put(n,x):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
assert not (D/'delivery_manifest.json').exists()
reports={'helper_source_independent_review.json':'0a48a04d8a1b7f6023399ddf18e1df5355bd5898c2a4d9da61e4cde7d2f5500e','post_reconciliation_independent_review.json':'5cd70fa199b34cd5877be4f512f21aca07c9c4bf2bb782d85934844a1d971521','Object3053894/helper_source_independent_review.json':'31a0ae9d7807c2b87603f3281dcc5f97ae392c9af569e580f2f4af1989bcc490','Object3053894/post_reconciliation_independent_review.json':'d741a75ae623a69afb2d052848c345c4fafd364ad082759e32c57dc93d7e0428'}
for name,pin in reports.items():assert h(D/name)==pin and j(D/name)['status']=='passed' and j(D/name)['blockers']==[]
source_manifest=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';assert h(source_manifest)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926';source=j(source_manifest)['files'];assert len(source)==173
for name,pin in source.items():assert h(R/name)==h(S/name)==pin
copied=[]
def copy(src,rel):
 dst=D/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 assert not src.is_symlink()
 with dst.open('xb') as f:f.write(src.read_bytes())
 assert h(dst)==h(src);copied.append({'source':ref(src),'copy':ref(dst)})
for suite,jid,auth in [('Spatial','3053875','79d22ee8370f95551c259894ad7deccffa7bebc4a1ffecab1c9d567d393cf855'),('Object','3053894','36b24fd96344e48b5241a5253b807e4f8f6e65a997713c796d8f471f8c2f2b74')]:
 T=R/'results/formal_main_v2/downstream_gateway'/auth
 for n in ['failed_transaction.json','sbatch_result.json','preflight.json','root_reconciled_submission_observation.json','committed.json']:
  copy(T/n,'actual_root_records/'+jid+'/'+n)
 for n in [suite+'64s23_pending_reconciliation.json',suite+'64s23_dispatch/completion.json']:
  copy(B/n,'actual_root_records/'+jid+'/'+Path(n).name)
 copy(R/('results/formal_main_v2/submissions/'+jid+'.json'),'actual_root_records/'+jid+'/immutable_job_registration.json')
for n in ['final_summary.json','state_update_receipt.json']:copy(B/n,'actual_root_records/final_refresh/'+n)
for name,rc in [('k64_spatial_reconcile_independent_20261020T1949_v1.jsonl',0),('k64_spatial_reconcile_post_20261020T1949_v1.jsonl',0),('k64_object_reconcile_independent_20261020T1949_v1.jsonl',0),('k64_object_reconcile_post_20261020T1949_v1.jsonl',1),('k64_object_reconcile_post_20261020T1949_v2.jsonl',0)]:
 p=R/'results/formal_main_v2/control_transport'/name;rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()];last=rows[-1];assert last['event']=='control_end' and last['returncode']==rc and last['source173_and_entrypoint_unchanged'] is True
 copy(p,'transport/'+name)
put('copied_root_records_and_transports.json',copied)
hand=put('handoff.json',{'schema':'formal_main_v2','kind':'two_k64s23_exact_ACK_reconciliation_independent_delivery','status':'passed','job_ids':['3053875','3053894'],'exact_original_ACKs_only':True,'reports':{n:ref(D/n) for n in reports},'real_submission_calls_by_auditor':0,'root_reconciliation_submission_calls':0,'scientific_trials_added':0,'GPU_results_read':False,'production_state_or_Git_writes':False,'source173_R_and_S_unchanged':True,'two_entire_committed_states_reconstructed_and_SHA_equal':True,'state_freshness':'Object post additionally binds exact final_summary32f395cb and state_update_receipt0f415ca four-part before/after chain; only five recorded scheduler fields may differ from immutable job records. Spatial post was before that root refresh.','preserved_failure':'Object post v1 rejected current full registry byte equality after root operational refresh; v2 retains exact committed state digest and binds five observed fields to exact root snapshot. No science/source/identity guard removed. Original post-submit accounting failures and all ACK proofs retained.','all_prior_failed_allocation_costs_preserved':True,'blockers':[],'created_utc':datetime.now(timezone.utc).isoformat()})
files=[]
for p in sorted(D.rglob('*')):
 assert not p.is_symlink()
 if not p.is_file():continue
 assert p.suffix.lower() not in ('.pt','.pth','.bin','.ckpt','.safetensors','.pyc') and p.stat().st_size<100*1024*1024
 files.append(ref(p))
r=put('delivery_manifest.json',{'schema':'formal_main_v2','kind':'independent_delivery_manifest','status':'sealed','source_prefix':str(D.relative_to(R)),'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'handoff':hand,'manifest_self_excluded':True,'external_in_progress_seal_transport':'results/formal_main_v2/control_transport/k64_reconcile_independent_delivery_seal_20261020T1949_v1.jsonl','external_seal_transport_archive_after_control_end_only':True,'contains_no_weights_or_sealed_states':True,'created_utc':datetime.now(timezone.utc).isoformat()})
print(json.dumps({'manifest':r,'handoff':hand,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files)}))
