from pathlib import Path
import ast,hashlib,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_independent_20261020T2358'
H=lambda b:hashlib.sha256(b).hexdigest();checks=[];refs=[]
def ck(x,n):
 assert x,n
 checks.append({'check':n,'passed':True})
def text(p,w):
 b=(R/p).read_bytes();ck(H(b)==w,'pin:'+p);ast.parse(b);refs.append({'path':p,'sha256':w,'bytes':len(b)});return b.decode()
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('Read-only static source review')
 if event=='open':
  p,m,f=args
  if isinstance(p,(str,bytes)) and ((m and any(c in m for c in 'wax+')) or (isinstance(f,int) and f&(1|2|64|512|1024))):assert Path(p).resolve().is_relative_to(D)
sys.addaudithook(guard)
prior=R/'.local/delivery_independent_20261020T2358/static_review_v6.json';ck(H(prior.read_bytes())=='bc6988f3a4053fa4066ee4dd761ca8b13e98292d502a4ab1b71ef7d21a07ae3b','prior72_static_checks_exact')
s4=text('.local/final_snapshot_20261020T2358_v4.py','0bf4af47d39b94fb4bccce5f54a58d46d34f1bd1f748e2ee93f63cef067d1609')
s5=text('.local/final_snapshot_20261020T2358_v5.py','23f00b8ca94f92fcf5b34a5c13be9c66ab26c0c707ea6a444ab2d429d84b0b45')
i1=text('.local/prepare_inputs_20261020T2358_v1.py','1a880c44c17347945f9b8b09468c2826b8424341defd5dcc4236918f6e32ac13')
i2=text('.local/prepare_inputs_20261020T2358_v2.py','06d92eacbd722df3619731b9643e8f4687bb4631bc702c9a63e7489e3644a2ca')
d4=text('.local/deliver_20261020T2358_v4.py','c843e21b112b743263df195754753a22728b25ae81ff599755ec41843acf6c23')
d5=text('.local/deliver_20261020T2358_v5.py','7b3ddbf5a83d692567d282da3e2f4e681f72cb5a1a9f742a974d3feef0ccd4da')
want=s4.replace("summary['Spatial588']['last_observed_completed_raw_trials']=204;","summary['Spatial588']['last_observed_completed_raw_trials']=None;summary['Spatial588']['live_raw_progress_not_archived']=True;").replace('原始报告204/600，尚未终验','运行中报告进度未归档为可重建证据，完整终态尚未验收')
ck(s5==want,'snapshot_v5_only_withdraws_unarchived_progress_value')
ck(i2==i1.replace('原报告204/600、RUNNING；原12 legacy','其Slurm状态为RUNNING；运行中raw报告计数未单独归档，不能由live_observation重建，本轮不引用该未归档计数。原12 legacy'),'inputs_v2_only_withdraws_unarchived_progress_value')
want=d4.replace("'.local/deliver_20261020T2358_v4.py'","'.local/deliver_20261020T2358_v4.py','.local/deliver_20261020T2358_v5.py'").replace("'.local/final_snapshot_20261020T2358_v4.py'","'.local/final_snapshot_20261020T2358_v4.py','.local/final_snapshot_20261020T2358_v5.py','.local/prepare_inputs_20261020T2358_v1.py','.local/prepare_inputs_20261020T2358_v2.py'")
ck(d5==want,'delivery_v5_only_adds_four_source_versions_to_exact_archive')
for label,v in [('snapshot',s5),('inputs',i2),('delivery',d5)]:
 ck('204/600' not in v,'no_unarchived_raw_count_claim:'+label)
 ck('sbatch' not in v and 'squeue' not in v and 'sacct' not in v,'no_new_Slurm_calls:'+label)
 ck("with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):" in v,'same_shared_lock:'+label)
out=D/'static_review_v7.json';assert not out.exists()
report={'schema':'formal_main_v2','kind':'root_final_delivery_static_delta_independent_review','status':'passed_static_review_actual_snapshot_pending','blockers':[],'prior_static_review':{'path':str(prior.relative_to(R)),'sha256':H(prior.read_bytes()),'check_count':72},'source_refs':refs,'check_count':len(checks),'checks':tuple(checks),'scope':'Exact append-only v5/v2 deltas to previously reviewed helpers; unarchived 204/600 claim withdrawn, existing Slurm evidence preserved, no new polling. Actual state/inputs/summary and future Git are not yet verified.','actual_snapshot_verified':False,'future_Git_verified':False,'new_GPU_submissions':0}
b=(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
with out.open('xb') as f:f.write(b)
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(b),'check_count':len(checks)}))
