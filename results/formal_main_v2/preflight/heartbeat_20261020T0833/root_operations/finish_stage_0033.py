from pathlib import Path
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T0833';E='results/formal_main_v2/engineering/supervision_delivery_0033'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):return json.loads((R/rel).read_bytes())
def save(rel,v):
 p=R/rel
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def git(*a):return subprocess.run(['git','-c','core.quotepath=false',*a],cwd=R,capture_output=True,check=True)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('finishstage0033',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()=='532ec5c0696c7613f45a52a9389c0d1a25a6cd60'
 required=read(B+'/git_required_files.json')
 assert set(git('diff','--cached','--name-only').stdout.decode().splitlines())=={x['path'] for x in required['files']}|{B+'/git_required_files.json'}
 for row in required['files']:
  raw=git('show',':'+row['path']).stdout;assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 guard=read(B+'/git_index_guard.stdout.json');assert guard['status']=='verified_index_archive_delivery' and guard['frozen_files_verified_in_worktree_and_index']==173
 assert len(guard['raw_paths_restored_exactly'])==3 and sum(x['bytes'] for x in guard['raw_paths_restored_exactly'])==178950489
 raw_scontrol=B+'/Object64_3044017_scontrol.txt';assert h(R/raw_scontrol)=='8e7083ee4c1906fe8c715fefb84f1711b93e7153717247d502dc8db1e8436f7d'
 diagnostic=read(B+'/git_whitespace_diagnostic.json');assert diagnostic['returncode']==2 and not diagnostic['stderr']
 exceptions=[]
 for line in diagnostic['stdout'].splitlines():
  if not re.match(r'^.*?:[0-9]+: ',line):continue
  m=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',line);assert m,line
  name=m.group(1);assert name.startswith(E+'/') and name.endswith(('.diff','.log','.txt')) or name==raw_scontrol,name
  exceptions.append(name)
 exceptions=sorted(set(exceptions));assert len(exceptions)==4
 git('diff','--cached','--check','--','.',*[':(exclude)'+x for x in exceptions])
 save(B+'/git_index_delivery.json',dict(schema='formal_main_v2',status='all_required_index_and_incremental_archive_verified',baseline='532ec5c0696c7613f45a52a9389c0d1a25a6cd60',required_files=B+'/git_required_files.json',index_guard=dict(path=B+'/git_index_guard.stdout.json',sha256=h(R/B/'git_index_guard.stdout.json')),frozen_index_and_worktree_files=173,new_raw_restored=3,new_raw_bytes=178950489,previous_archives_unchanged=True,weights_added=False,excluded_live_files=['results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out','results/slurm/cti-formal_3044017.out','results/slurm/cti-formal_3044017.err'],raw_whitespace_exceptions=[dict(path=n,sha256=h(R/n)) for n in exceptions],root_independent_complete=54,new_GPU_submissions_by_root=['3044017'],new_development_trials=0))
 source=B+'/root_operations/finish_stage_0033.py'
 with (R/source).open('xb') as f:f.write(Path(__file__).read_bytes())
 save(B+'/git_stage_raw_whitespace_resolution.json',dict(status='exact_raw_observation_whitespace_preserved',initial_failure_transport=dict(path='results/formal_main_v2/control_transport/heartbeat_0033_stage_delivery.jsonl',sha256=h(R/'results/formal_main_v2/control_transport/heartbeat_0033_stage_delivery.jsonl')),reason='Original Slurm scontrol output ends with space; preserve exact raw bytes. Existing archive and all173 index checks passed. Only this exact immutable raw observation added to allowed diagnostics.',exact_raw=dict(path=raw_scontrol,sha256=h(R/raw_scontrol)),source=dict(path=source,sha256=h(R/source)),index_modified=False,source_or_science_changed=False))
 print(json.dumps(dict(status='index_verified_exact_raw_whitespace_retained',frozen=173,raw_archive_bytes=178950489,exceptions=exceptions)))
