from pathlib import Path
import hashlib,json,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0530';A='results/formal_main_v2/engineering/supervision_delivery_2130'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cp(n,out,pin):
 p=R/n;q=R/out;assert h(p)==pin and not p.is_symlink();q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as f:f.write(p.read_bytes())
 assert h(q)==pin;return dict(source=n,path=out,sha256=pin,bytes=q.stat().st_size)
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archive2130ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 man='.local/downstream_pending_reconcile_2130/archive_closure.json';assert h(R/man)=='2c42f6c111ea2df5edadf6d158e0a4b26826536a9412c58fb55738cfe40ae73a';v=json.loads((R/man).read_text());rows=[]
 assert v['file_count']==11 and v['new_sbatch_calls']==0 and v['original_failure_retained_exact']
 for row in v['files']:
  name=row['path'];assert Path(name).name==name and '/' not in name and '\\' not in name
  src='.local/downstream_pending_reconcile_2130/'+name;assert (R/src).stat().st_size==row['bytes']
  rows.append(cp(src,A+'/known_ack_reconciliation/'+name,row['sha256']))
 rows.append(cp(man,A+'/known_ack_reconciliation/archive_closure.json',h(R/man)))
 for row in v['external_root_transaction_evidence']:
  assert h(R/row['path'])==row['sha256'] and (R/row['path']).stat().st_size==row['bytes']
 src='.local/cuda_terminal_independent_2130/independent_review.json';pin='6cfde8e029ab7b31f748175dfd052f75b1b5b3f457229a6abf689f8936afea5e'
 assert h(R/src)==pin;ind=json.loads((R/src).read_text())
 assert ind['status']=='passed_original_target_recovery_only' and ind['completed_by_arm']=={'A':1500,'B':1500} and ind['cost']['all_pair_allocated_GPU_seconds']==11958
 target='results/formal_main_v2/libero_spatial/k64/seed23/training/segment_reviews/3043399_independent.json'
 rows.append(cp(src,target,pin))
 with (R/B/'initial_engineering_archive_map.json').open('x') as f:json.dump(dict(schema='formal_main_v2',files=rows,originals_retained=True,weights_copied=False),f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(status='reconciliation_and_terminal_receipts_archived',files=len(rows),canonical_independent=target,sha256=pin)))
