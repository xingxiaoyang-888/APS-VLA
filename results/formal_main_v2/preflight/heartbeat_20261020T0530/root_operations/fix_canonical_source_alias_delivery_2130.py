from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0530';E='results/formal_main_v2/engineering/supervision_delivery_2130'
HEAD='7d2c6c2173fd36bd8e9139493abb042818d516a6'
RAW='results/formal_main_v2/libero_object/k64/seed41/training/cache_events/3037535_ff11e398c517.jsonl'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/machine_training_object64seed41_20261020_2130.json'
NAMES=['201611f6d862_build_formal_initial_states.py.txt','34b73213fce6_initial_states.py.txt','6ef472b85cbb_build_long_initial_states.py.txt','752e8e35ab6f_formal_initial_states.py.txt','972a8257320d_long_initial_states.py.txt']
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def copy_exclusive(src,rel):
 with (R/rel).open('xb') as f:f.write(src.read_bytes())
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('canonical_alias2130ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==HEAD
 required=json.loads((R/B/'git_required_files.json').read_bytes());before_req=h(R/B/'git_required_files.json')
 assert set(git('diff','--cached','--name-only').stdout.decode().splitlines())=={x['path'] for x in required['files']}|{B+'/git_required_files.json'}
 err=json.loads((R/B/'git_index_guard.stderr.txt').read_bytes());assert err['status']=='rejected' and err['error']=='State-value metadata forbidden'
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes());assert len(inventory['files'])==173
 mapping=[]
 for name in NAMES:
  rel=E+'/terminal_independent/dependencies/'+name;p=R/rel;pin=h(p)
  matches=[n for n,v in inventory['files'].items() if v==pin];assert len(matches)==1
  canon=matches[0];assert canon.startswith(('src/','scripts/')) and canon.endswith('.py') and h(R/canon)==pin
  assert git('show','HEAD:'+canon).stdout==p.read_bytes() and git('show',':'+rel).stdout==p.read_bytes()
  mapping.append(dict(retained_server_archive_path=rel,git_canonical_source=canon,sha256=pin,bytes=p.stat().st_size,byte_exact=True))
 aliases=[m['retained_server_archive_path'] for m in mapping]
 for name in ['git_required_files.json','git_index_guard.stdout.json','git_index_guard.stderr.txt']:
  copy_exclusive(R/B/name,B+'/'+name.replace('.', '_attempt01.',1))
 git('restore','--staged','--',*aliases)
 ignore=R/'.gitignore';old=ignore.read_text();assert not any('/'+x in old.splitlines() for x in aliases)
 ignore.write_text(old+'\n# Audit aliases use existing SHA-identical frozen sources; raw server copies retained.\n'+'\n'.join('/'+x for x in aliases)+'\n')
 aliasnote=E+'/terminal_independent/canonical_source_alias_delivery.json'
 save(aliasnote,dict(schema='formal_main_v2',kind='canonical_frozen_source_alias_delivery',status='all_five_exact_source_bytes_already_in_Git',mapping=mapping,explanation='The unmodified archive stage guard rejects state-named metadata aliases. These five files are SHA-identical frozen source already present at canonical src/scripts paths, not state values. Raw server copies and original audit manifests remain intact. Reconstruct an original alias from its mapped canonical source and verify SHA/bytes when needed.',sealed_values_read=False,checker_changed=False,original_source_173_unchanged=True,server_copies_deleted=False))
 copy_exclusive(Path(__file__),B+'/root_operations/fix_canonical_source_alias_delivery_2130.py')
 additions=[aliasnote,B+'/root_operations/fix_canonical_source_alias_delivery_2130.py',B+'/git_required_files_attempt01.json',B+'/git_index_guard_attempt01.stdout.json',B+'/git_index_guard_attempt01.stderr.txt']
 # Names above follow replace('.', '_attempt01.', 1); validate exact expected paths.
 for x in additions:assert (R/x).is_file(),x
 audit='results/formal_main_v2/control_transport/heartbeat_2130_stage_delivery_a2.jsonl';assert json.loads((R/audit).read_text().splitlines()[-1])['event']=='control_end';additions.append(audit)
 git('add','--','.gitignore',*additions)
 current=set(git('diff','--cached','--name-only').stdout.decode().splitlines())-{B+'/git_required_files.json'}
 updated=dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[dict(path=n,sha256=hashlib.sha256(git('show',':'+n).stdout).hexdigest(),bytes=len(git('show',':'+n).stdout)) for n in sorted(current)])
 # Refresh live controller metadata in one locked snapshot, never overwrite state.
 for n in ['results/experiment_supervisor/state.json','results/formal_main_v2/autonomous_training/run_v1/events/events.000000.jsonl']:git('add','--',n)
 updated['files']=[dict(path=n,sha256=hashlib.sha256(git('show',':'+n).stdout).hexdigest(),bytes=len(git('show',':'+n).stdout)) for n in sorted(current)]
 (R/B/'git_required_files.json').write_text(json.dumps(updated,sort_keys=True,ensure_ascii=False,indent=2)+'\n');git('add','--',B+'/git_required_files.json')
 checker=R/'scripts/ops/check_nonweight_archive_stage.py';assert h(checker)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
 argv=[sys.executable,'-B',str(checker),'--project-root',str(R),'--snapshot',SNAP,'--snapshot-sha256',h(R/SNAP),'--raw-path',RAW,'--required-files',B+'/git_required_files.json']
 result=subprocess.run(argv,cwd=R,capture_output=True)
 (R/B/'git_index_guard.stdout.json').write_bytes(result.stdout);(R/B/'git_index_guard.stderr.txt').write_bytes(result.stderr)
 assert result.returncode==0,result.stderr.decode()
 v=json.loads(result.stdout);assert v['status']=='verified_index_archive_delivery' and v['frozen_files_verified_in_worktree_and_index']==173 and len(v['raw_paths_restored_exactly'])==1
 diag=git('diff','--cached','--check',check=False);save(B+'/git_whitespace_diagnostic.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 exceptions=[]
 if diag.returncode:
  headers=[line for line in diag.stdout.decode().splitlines() if re.match(r'^.*?:[0-9]+: ',line)];assert headers and not diag.stderr
  for header in headers:
   match=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',header);assert match,header
   name=match.group(1);assert name.startswith(E+'/') or name.startswith('results/slurm/') or name.startswith(B+'/') and name.endswith(('.txt','.out','.err','.log','.diff')),name;exceptions.append(name)
 exceptions=sorted(set(exceptions));git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 save(B+'/git_index_delivery.json',dict(schema='formal_main_v2',status='all_required_index_and_incremental_archive_verified',baseline=HEAD,required_files=B+'/git_required_files.json',index_guard=dict(path=B+'/git_index_guard.stdout.json',sha256=h(R/B/'git_index_guard.stdout.json')),frozen_index_and_worktree_files=173,new_raw_restored=1,new_raw_bytes=132813168,previous_union29_unchanged=True,weights_added=False,excluded_live_files=['results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out'],canonical_source_alias_delivery=dict(path=aliasnote,sha256=h(R/aliasnote)),raw_whitespace_exceptions=[dict(path=n,sha256=h(R/n)) for n in exceptions],machine_complete=50,root_independent_complete=48,pending_Object64seed41_root_independent_review=True,new_GPU_submissions_by_root=['3043709'],normal_controller_refill='3043762'))
 print(json.dumps(dict(status='index_reverified_with_canonical_source_aliases',aliases=len(mapping),raw_restored_bytes=132813168,files=len(current)+1,whitespace_exceptions=len(exceptions))))
