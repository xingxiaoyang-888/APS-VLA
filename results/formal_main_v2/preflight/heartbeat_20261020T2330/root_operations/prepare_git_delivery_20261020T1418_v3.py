from pathlib import Path
import json,hashlib,importlib.util,sys,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n))
def checked(ref0):assert h(R/ref0['path'])==ref0['sha256'];return rd(ref0['path'])
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('preparegit1418v2ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)
 I=checked(dict(path=B+'/git_delivery_inputs.json',sha256='c3860085f66de157af7eee1c59b653d2ec4aee1faed1446ec38c9c58cf9a1e45'))
 a=checked(dict(path=B+'/Goal3043762_archive_inputs.json',sha256='8514cfc84a32bafee5af954a1b638c3a6cd2a85d5076d669a1bf1a6e967b434e'))
 pull=checked(a['pull']);assert pull['status']=='verified_nonweight_snapshot' and [str(j['job_id']) for j in pull['selected_jobs']]==['3043762']
 extra=set(I['extra_exact']);extra.update(row['relative'] for row in pull['files'])
 p=Path(a['pull']['path']).parent
 extra.update((p/n).as_posix() for n in ['receipt.json','inventory_before.json','inventory_after.json'])
 snap=checked(a['snapshot']);extra.update([a['snapshot']['path'],snap['request']['path']])
 for row in snap['provenance']:checked(row);extra.add(row['path'])
 for row in snap['files']:
  obj=checked(row['manifest']);extra.add(row['manifest']['path'])
  for part in obj['chunks']:
   assert h(R/part['path'])==part['compressed_sha256']
   extra.add(part['path'])
 I['extra_exact']=sorted(extra);I['additional_pulls']=[a['pull']]
 I['archive_scope_note']='Goal3043762 machine-pulled nonweights archived only; root plus independent scientific terminal acceptance remains pending.'
 excluded=['results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out',
 'results/formal_main_v2/control_transport/heartbeat_20261020T1418_prepare_git_inputs_v3.jsonl',
 'results/formal_main_v2/control_transport/heartbeat_20261020T1418_delivery_v3.jsonl',
 'results/formal_main_v2/control_transport/heartbeat_20261020T1418_github_push.jsonl']
 I['allowed_live_exclusions']=excluded
 pins={}
 status=subprocess.check_output(['git','--no-optional-locks','status','--porcelain=v1','--untracked-files=all','-z'],cwd=R).decode()
 for row in status.split('\0'):
  if not row:continue
  name=row[3:]
  if not name.startswith('results/formal_main_v2/control_transport/') or name in excluded:continue
  raw=(R/name).read_bytes();events=[json.loads(x) for x in raw.splitlines()]
  assert events[0]['event']=='control_start' and events[-1]['event']=='control_end',name
  pins[name]=h(R/name)
 I['transport_pins']=pins
 own=Path(__file__).relative_to(R).as_posix();I['additional_root_sources'].append(dict(**ref(own),not_yet_executed=False))
 out=R/B/'git_delivery_inputs_v3.json'
 with out.open('x') as fp:json.dump(I,fp,ensure_ascii=False,sort_keys=True,indent=2);fp.write('\n')
 print(json.dumps(dict(path=out.relative_to(R).as_posix(),sha256=h(out),closed_transport=len(pins),extra_exact=len(extra))))
