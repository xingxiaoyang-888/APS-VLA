from pathlib import Path
import json,hashlib,sys,subprocess,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T2330';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530';D='results/formal_main_v2/execution/nonLong_action_v1_20261020T1530/'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n))
def checked(r):assert h(R/r['path'])==r['sha256'];return rd(r['path'])
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('prepareGit1530ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()=='6968b7a8bb134ef3b5f9076470c826ab462156ee'
 assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)
 s=rd('results/experiment_supervisor/state.json');f=s['formal_main_progress'];key='supervision_integrity_review_20261020T1530'
 assert f[key]['status']=='passed' and s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 assert f['root_and_independent_completed_arms']==66 and f['current_action_development_trial_count']==4400
 assert s['last_root_supervision_snapshot']==dict(path=B+'/summary_after_dispatch.json',sha256='3bced1812b1002f276f6327674c37779d8747ecbb9e368d8073e7cd9bc32b216')
 dispatch=checked(dict(path=B+'/dispatch_root_report.json',sha256='82a65bd598a35cbaa49afeca1259c8b2ca39f20ca237fd282dd534c13546f8bf'))
 assert [r['job_id'] for r in dispatch['submissions']]==['3050870','3050890','3050901','3050916']
 pr=dict(path='results/formal_main_v2/pulls/20261020T153411Z_ee5de4901f52/receipt.json',sha256='d2e3853021dc69de491ac500b88492c1f062ee84dd910bc39ebae51b39599d0f')
 primary=checked(pr);assert primary['status']=='verified_nonweight_snapshot'
 extra={r['relative'] for r in primary['files']}
 prefixes=[D,str(Path(pr['path']).parent)+'/', 'results/formal_main_v2/autonomous_training/run_v1/reviews/',
 'results/formal_main_v2/engineering/goal_t0_probe_20261020T1418/',
 'results/formal_main_v2/execution/object256seed23_source_bridge_v1_20261020T1530/']
 for e in dispatch['submissions']:
  extra.update([e['invocation']['path'],e['submission']['path']]);prefixes.append('results/formal_main_v2/downstream_gateway/'+e['authorization']['sha256']+'/')
 extra.update('results/formal_main_v2/downstream_reviews/'+jid+'.json' for jid in ['3050192','3050205','3050224'])
 extra.update('results/formal_main_v2/libero_goal/k64/seed17/training/segment_reviews/'+fn for fn in ['3043762.json','3043762_independent.json'])
 docs=['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式非Long开发结果','正式Spatial轻度剪枝开发结果','正式下游阻塞登记_20261020T1530']
 extra.update('docs/'+n+'.md' for n in docs)
 a=rd(B+'/Goal3043877_archive_inputs.json');apull=checked(a['pull']);assert apull['status']=='verified_nonweight_snapshot' and [str(j['job_id']) for j in apull['selected_jobs']]==['3043877']
 extra.update(r['relative'] for r in apull['files']);p=Path(a['pull']['path']).parent
 extra.update((p/n).as_posix() for n in ['receipt.json','inventory_before.json','inventory_after.json'])
 snap=checked(a['snapshot']);extra.update([a['snapshot']['path'],snap['request']['path']])
 for row in snap['provenance']:checked(row);extra.add(row['path'])
 for row in snap['files']:
  obj=checked(row['manifest']);extra.add(row['manifest']['path'])
  for part in obj['chunks']:assert h(R/part['path'])==part['compressed_sha256'];extra.add(part['path'])
 probeplan=checked(dict(path=E+'/Goal_probe_terminal/nonweight_copy_plan.json',sha256='32bf312ac0baa15f851836fedfb0efaf277724eaa859736e56b22f6c7d96f9f9'))
 for row in probeplan['files']:
  path=Path(row['destination']);assert path.is_relative_to(R) and h(path)==row['sha256'];extra.add(path.relative_to(R).as_posix())
 excluded=['results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out',
 'results/formal_main_v2/control_transport/heartbeat_20261020T1530_prepare_git_inputs.jsonl',
 'results/formal_main_v2/control_transport/heartbeat_20261020T1530_delivery.jsonl',
 'results/formal_main_v2/control_transport/heartbeat_20261020T1530_github_push.jsonl']
 pins={}
 output=subprocess.check_output(['git','--no-optional-locks','-c','core.quotepath=false','status','--porcelain=v1','--untracked-files=all','-z'],cwd=R).decode()
 for row in output.split(chr(0)):
  if not row:continue
  name=row[3:]
  if not name.startswith('results/formal_main_v2/control_transport/') or name in excluded:continue
  lines=[json.loads(v) for v in (R/name).read_bytes().splitlines()]
  assert lines[0]['event']=='control_start' and lines[-1]['event']=='control_end',name;pins[name]=h(R/name)
 extra_sources=[]
 for rel,pin,unused in [('.local/github_push_20261020T1530.py','1e29638cafdf7e73fa8a76f8417ea80f949014ff0da8ec72469558a47811053e',True),('.local/archive_reviews_20261020T1530.py','719046015902e0256d34f9ddb55481ae39561b0cb5e4005d892ae7253d79cc8f',True)]:
  assert h(R/rel)==pin;extra_sources.append(dict(path=rel,sha256=pin,not_yet_executed=unused))
 extra_sources.append(dict(**ref(Path(__file__).relative_to(R).as_posix()),not_yet_executed=False))
 array_ref=dict(path=B+'/Goal_probe_arrays_delivery.json',sha256='8d7e66ebb6f5dfc61958d27f25007d837ed5a4a713e4c802db5dd87e9f1d0775')
 ar=checked(array_ref);assert ar['root_verified_members']==288 and ar['root_verified_original_and_restored_SHA'] and not ar['scientific_release']
 assert h(R/ar['archive']['path'])==ar['archive']['sha256']=='97a41e3248b708ec0906b46bd8417ba023935482b8274910fdff6954efb8174b'
 for row in ar['copies']:assert h(R/row['archive']['path'])==row['archive']['sha256'];extra.add(row['archive']['path'])
 for rel,pin in [('.local/prepare_git_delivery_20261020T1530.py','01b2a84fd6e6aec3c908d40affcc09f64458c4fff035040eb7341a9851a84021'),('.local/deliver_20261020T1530.py','6eccff9218e8d4e79024a3f4cae9980e8c073a9ebc9ed307f176006c49846189')]:
  assert h(R/rel)==pin;extra_sources.append(dict(path=rel,sha256=pin,not_yet_executed=True))
 I=dict(schema='formal_main_v2',baseline='6968b7a8bb134ef3b5f9076470c826ab462156ee',new_job_ids=['3050870','3050890','3050901','3050916'],new_engineering_job_ids=['3050711'],
 summary=s['last_root_supervision_snapshot'],independent_final_review=f[key]['independent_review'],root_integrity_status_path=key,transport_pins=pins,extra_exact=sorted(extra),extra_prefixes=prefixes,allowed_live_exclusions=excluded,pull=pr,additional_pulls=[a['pull']],additional_root_sources=extra_sources,
 array_delivery=array_ref,archive_scope_note='Goal3043877 machine-pulled nonweights archived only; root plus independent scientific terminal acceptance remains pending. Probe raw 288 NPZ remain in P; their complete lossless archive and per-member provenance are delivered in R and GitHub.')
 out=R/B/'git_delivery_inputs.json'
 with out.open('x') as fp:json.dump(I,fp,ensure_ascii=False,sort_keys=True,indent=2);fp.write(chr(10))
 print(json.dumps(dict(receipt=ref(out.relative_to(R).as_posix()),closed_transport=len(pins),exact_files=len(extra))),flush=True)
