from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0758'
DOC='docs/正式下游阻塞登记_20261020T2358.md'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=True)
def save(n,v):
 with (R/n).open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('git_format_repair_ctl',p);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()=='456014638158b5495df0aa358a55f1c25a4f521c'
 assert h(R/'results/experiment_supervisor/state.json')=='40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a'
 req=B+'/git_required_files.json';assert h(R/req)=='e52831510cbbc626612880054e4f151dd4d6c568eeebfe90a55e4e91979987ea'
 assert h(R/(B+'/git_index_guard.json'))=='5129c715ea72a2a49125fb2660f52b059860438e670f9af9888272b60ed57fe7'
 rows=json.loads((R/req).read_bytes())['files'];expected={x['path']:x for x in rows}
 assert len(expected)==len(rows)
 expected[req]={'path':req,'sha256':h(R/req),'bytes':(R/req).stat().st_size}
 staged=git('diff','--cached','--name-only','-z').stdout.decode().split(chr(0));staged=[x for x in staged if x]
 assert len(staged)==224 and set(staged)==set(expected)
 for n,v in expected.items():
  raw=git('show',':'+n).stdout;assert hashlib.sha256(raw).hexdigest()==v['sha256'] and len(raw)==v['bytes'] and raw==(R/n).read_bytes()
 raw=(R/DOC).read_bytes();assert h(R/DOC)=='d11864b253cdd9b4560db42e2c8d1c090846eddd4622182fc16c82a22ed66aa6' and raw.endswith(b'\n\n') and not raw.endswith(b'\n\n\n')
 check=subprocess.run(['git','-c','core.quotepath=false','diff','--cached','--check'],cwd=R,capture_output=True)
 assert check.returncode==2 and not check.stderr and check.stdout.decode()==DOC+':36: new blank line at EOF.\n'
 save(B+'/git_v5_precommit_failure.json',{'status':'failed_before_commit_preserved','utc':datetime.now(timezone.utc).isoformat(),'error':check.stdout.decode(),'exact_staged_files':[expected[n] for n in sorted(expected)],'original_doc_utf8':raw.decode(),'repair_scope':'remove final one LF only and unstage exact 224 previously validated project paths; no worktree removal','state_unchanged':True,'GPU_jobs_added':0})
 for i in range(0,len(staged),60):git('restore','--staged','--',*staged[i:i+60])
 assert git('diff','--cached','--name-only').stdout==b''
 for n,v in expected.items():assert h(R/n)==v['sha256'] and (R/n).stat().st_size==v['bytes']
 (R/DOC).write_bytes(raw[:-1]);assert (R/DOC).read_bytes()+b'\n'==raw
 assert h(R/'results/experiment_supervisor/state.json')=='40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a'
 value={'status':'single_LF_corrected_exact_index_restored_empty','utc':datetime.now(timezone.utc).isoformat(),'document':DOC,'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':h(R/DOC),'bytes_removed':1,'unstaged_exact_paths':224,'worktree_files_deleted':0,'state_unchanged':True,'GPU_jobs_added':0,'prior_failure_receipt':B+'/git_v5_precommit_failure.json'}
 save(B+'/git_format_repair.json',value);print(json.dumps(value))
