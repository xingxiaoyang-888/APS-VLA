from pathlib import Path
import argparse,hashlib,json,importlib.util,sys,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
D='results/formal_main_v2/execution/nonLong_action_v1_20261020T1418/'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def git(*a):return subprocess.check_output(['git','--no-optional-locks',*a],cwd=R)
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('preparegit1418ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=rd('results/experiment_supervisor/state.json');f=state['formal_main_progress']
 key='supervision_integrity_review_20261020T1418'
 assert f[key]['status']=='passed' and state['pending_submission'] is None
 dispatch=rd(B+'/dispatch_root_report.json');assert [x['job_id'] for x in dispatch['submissions']]==['3050192','3050205','3050224']
 pullref=dict(path='results/formal_main_v2/pulls/20261020T142621Z_02800e667ffb/receipt.json',sha256='20139adbe331ea4d217e7011f22b4e3d6e008f6c59e87ff1d00a0735ef290493')
 assert h(R/pullref['path'])==pullref['sha256'];pull=rd(pullref['path'])
 extra=set(x['relative'] for x in pull['files'])
 extra.update('results/formal_main_v2/downstream_reviews/'+j+'.json' for j in ['3049132','3049172','3049622','3049632','3049657'])
 docs=['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式非Long开发结果','正式Goal主预算开发结果','正式下游阻塞登记_20261020T1418']
 extra.update('docs/'+d+'.md' for d in docs)
 prefixes=[D,'results/formal_main_v2/pulls/20261020T142621Z_02800e667ffb/','results/formal_main_v2/autonomous_training/run_v1/reviews/']
 for row in dispatch['submissions']:
  extra.update([row['invocation']['path'],row['submission']['path']])
  prefixes.append('results/formal_main_v2/downstream_gateway/'+row['authorization']['sha256']+'/')
 excluded=['results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out',
 'results/formal_main_v2/control_transport/heartbeat_20261020T1418_prepare_git_inputs.jsonl',
 'results/formal_main_v2/control_transport/heartbeat_20261020T1418_delivery.jsonl',
 'results/formal_main_v2/control_transport/heartbeat_20261020T1418_github_push.jsonl']
 pins={}
 for row in git('status','--porcelain=v1','--untracked-files=all','-z').decode().split('\0'):
  if not row:continue
  name=row[3:]
  if not name.startswith('results/formal_main_v2/control_transport/'):continue
  if name in excluded:continue
  raw=(R/name).read_bytes();lines=[json.loads(x) for x in raw.splitlines()]
  assert lines[0]['event']=='control_start' and lines[-1]['event']=='control_end',name
  pins[name]=hashlib.sha256(raw).hexdigest()
 push='.local/github_push_20261020T1418.py';assert h(R/push)=='ecaaaf2ce1c5c4c8a4fb6be9005ce1d82d082038f2e77b3c9adad8481de4860b'
 own=Path(__file__).relative_to(R).as_posix()
 inputs=dict(schema='formal_main_v2',baseline='e79204d66ecc25b3d9927499d01e2f4dd34a0fbb',
  new_job_ids=['3050192','3050205','3050224'],summary=state['last_root_supervision_snapshot'],
  independent_final_review=f[key]['independent_review'],root_integrity_status_path=key,
  transport_pins=pins,extra_exact=sorted(extra),extra_prefixes=prefixes,allowed_live_exclusions=excluded,pull=pullref,
  additional_root_sources=[dict(**ref(push),not_yet_executed=True),dict(**ref(own),not_yet_executed=False)])
 out=R/B/'git_delivery_inputs.json'
 with out.open('x') as fp:json.dump(inputs,fp,ensure_ascii=False,sort_keys=True,indent=2);fp.write('\n')
 print(json.dumps(dict(path=out.relative_to(R).as_posix(),sha256=h(out),closed_transport=len(pins),extra_exact=len(extra))))
