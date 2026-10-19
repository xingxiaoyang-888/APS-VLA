from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261019T2318'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('resume1518',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';before=h(statepath);s=json.loads(statepath.read_text());j=next(x for x in s['registered_jobs'] if str(x['job_id'])=='3042627');assert s['pending_submission'] is None
 run=P/'results/formal_main_v2/libero_object/k256/seed23/training';p=run/'A/attempts/20261019T154719_f82c43afe6e5/cost_events.jsonl';buf=[];rows=[]
 with p.open('rb') as f:
  for line in f:
   assert line.endswith(b'\n');v=json.loads(line);buf.append(line);rows.append(v)
   if v['event']=='update_end':break
   assert len(buf)<100
 raw=b''.join(buf);assert rows[0]['event']=='attempt_start' and rows[0]['resumed'] is True and rows[0]['completed_update']==500 and rows[0]['next_sample_cursor']==4000
 assert all(x['job_id']=='3042627' for x in rows) and rows[-1]['event']=='update_end' and rows[-1]['update']==501 and rows[-1]['forward_backward_samples']==8 and rows[-1]['grad_norm']>0
 orderpath=run/'A/training_order.json';order=json.loads(orderpath.read_text());assert order['seed']==23 and len(order['samples'])==40000
 assert rows[1]['event']=='update_start' and rows[1]['update']==501 and rows[1]['window_ids']==order['samples'][4000:4008]
 assert (run/'B/training_order.json').read_bytes()==orderpath.read_bytes()
 with p.open('rb') as f:assert f.read(len(raw))==raw
 target=R/B/'CUDA3042627_A_first_update_prefix.jsonl'
 with target.open('xb') as f:f.write(raw)
 receipt=dict(schema='formal_main_v2',kind='bounded_first_actual_resume_observation',status='A_resume500_cursor4000_and_update501_match_original_order',utc=datetime.now(timezone.utc).isoformat(),job_id='3042627',arm='A',source_journal=str(p),source_prefix_bytes=len(raw),source_prefix_rows=len(rows),source_prefix_sha256=h(target),source_may_continue_appending=True,training_order=dict(path=str(orderpath),sha256=h(orderpath),order_sha256=order['order_sha256']),AB_order_bytes_identical=True,initial_scorer_sha256=order['initial_scorer_sha256'],invocation=dict(path=j['invocation'],sha256=j['invocation_sha256']),resume_completed_update=500,next_sample_cursor=4000,first_update=rows[-1],checkpoint_tensors_read_by_this_probe=False,optimizer_rng_recovery_enforced_by_frozen_trainer=True,B_resume_not_yet_observed=True,completed_training_claimed=False,state_unchanged=True,continued_polling=False)
 assert h(statepath)==before
 out=R/B/'CUDA3042627_first_actual_resume.json'
 with out.open('x') as f:json.dump(receipt,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(status=receipt['status'],receipt=out.relative_to(R).as_posix(),sha256=h(out),first_update=501,scope='A_first_update_only_not_B_or5000_completion')))
