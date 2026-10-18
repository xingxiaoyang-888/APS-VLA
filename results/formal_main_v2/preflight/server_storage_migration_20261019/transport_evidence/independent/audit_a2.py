from __future__ import annotations
import ast,hashlib,importlib.util,json,os,shlex,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;H=OUT.parent.parent;C=OUT.parent/'server_transport_v1';R=H/'control_repo'
start=time.monotonic();checks=[];evidence={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,v):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def passed(name):checks.append(name)
def reject(function,*args,**kw):
 try:function(*args,**kw)
 except (ValueError,FileNotFoundError):return
 raise AssertionError('expected rejection: '+str(args))
author=read(C/'candidate_review.json');assert sha(C/'candidate_review.json')=='8b10bb30f8703b4e613e8a064bf96c04de6b79b38e95f6597dcea9051e698aef'
for name,h in author['read_evidence_sha256'].items():
 p=Path(name);assert H in p.parents or Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA') in p.parents;assert sha(p)==h,name;evidence[name]=h
for name in ('candidate_review.json','README.md','test_server_transport.py','tests_a1.xml','tests_a1.json','tests_a1.log'):
 evidence[str(C/name)]=sha(C/name)
t=load(C/'server_transport.py','independent_server_transport');manifest_sha=sha(C/'bundle_manifest.json')
t.verify_bundle(manifest_sha);frozen=t.verify_frozen();assert len(frozen)==173
passed('actual_bundle_and_173_R_S_SHA_before')
xml=ET.parse(C/'tests_a1.xml').getroot();assert xml.attrib['tests']=='20' and xml.attrib['failures']==xml.attrib['errors']==xml.attrib['skipped']=='0'
tests=read(C/'tests_a1.json');assert tests['tests']==20 and tests['status']=='passed_CPU_only';passed('author20_raw_XML_and_log_bindings')
f=load(R/'scripts/formal_supervisor.py','independent_frozen_supervisor');expected=['ssh','-o','BatchMode=yes','tongji-cvpr'];assert f.SSH==expected
parent_environment=dict(os.environ)
# New copy tests use only this independent output area, no real R/P writes.
a=OUT/'binary_source.jsonl';a.write_bytes(bytes(range(256))*13);b=OUT/'binary_copy.jsonl';d=OUT/'binary_back.jsonl'
x=t.copy_single(str(a),str(b));y=t.copy_single(str(b),str(d));assert a.read_bytes()==b.read_bytes()==d.read_bytes() and x['action']==y['action']=='copied_exclusive'
before=b.stat();z=t.copy_single(str(a),str(b));assert z['action']=='same_bytes_no_write' and (b.stat().st_ino,b.stat().st_mtime_ns)==(before.st_ino,before.st_mtime_ns)
passed('single_regular_file_binary_roundtrip_and_identical_no_write')
a.write_bytes(b'different');reject(t.copy_single,str(a),str(b));assert b.read_bytes()==d.read_bytes();passed('different_destination_preserved')
assert t.parse_scp(['-q',str(a),'tongji-cvpr:'+str(b)])==[str(a),str(b)]
for args in (['-r',str(a),'tongji-cvpr:'+str(b)],['-q',str(a),'other:'+str(b)],['-q','tongji-cvpr:'+str(a),'tongji-cvpr:'+str(b)],['-q',str(a),str(b)],['-q',str(a),'tongji-cvpr:'+str(b),'extra']):reject(t.parse_scp,args)
passed('SCP_one_known_endpoint_exact_shape')
old_no_links=t.no_links
def fs_forbidden(*a,**k):raise AssertionError('I/O reached for forbidden path')
t.no_links=fs_forbidden
try:
 for p in (H/'weights/x.json',H/'checkpoints/x.json',H/'results/sealed_final.json',H/'results/init_states_test.json',H/'results/final_registry.json',H/'results/panel.json',H/'results/x.pt.partial',Path('/etc/passwd')):reject(t.project_path,str(p))
 reject(t.project_path,str(t.S/'src/new.py'),copy_target=True)
finally:t.no_links=old_no_links
passed('weights_states_snapshot_and_external_paths_rejected_before_I_O')
link=OUT/'source_alias.jsonl';link.symlink_to(a);reject(t.copy_single,str(link),str(OUT/'alias_dest.jsonl'));passed('symlink_source_rejected')
for args in ([],['-o','BatchMode=no','tongji-cvpr','true'],['-o','BatchMode=yes','other','true'],['-o','BatchMode=yes','tongji-cvpr','true','extra']):reject(t.run_ssh,args)
reject(t.scope);passed('SSH_shape_and_inactive_scope_rejection')
# Execute the original run_ssh function and bash with an independent journal.
# Only scope() is replaced so this audit does not create a journal inside R.
journal=OUT/'function_calls.jsonl';journal.write_bytes(b'')
child='import importlib.util,os,sys\nfrom pathlib import Path\np=Path('+repr(str(C/'server_transport.py'))+')\ns=importlib.util.spec_from_file_location("child_transport",p);t=importlib.util.module_from_spec(s);s.loader.exec_module(t)\nt.verify_bundle('+repr(manifest_sha)+')\nt.scope=lambda:Path('+repr(str(journal))+')\nraise SystemExit(t.run_ssh(["-o","BatchMode=yes","tongji-cvpr",sys.argv[1]]))\n'
env=dict(os.environ);env['CTI_SERVER_CONTROL_ROOT']=str(R);env['CTI_SERVER_CONTROL_BIN']=str(C/'bin');env['PYTHONDONTWRITEBYTECODE']='1'
command=shlex.quote(sys.executable)+' -B -c '+shlex.quote('import subprocess,sys; subprocess.run([sys.executable,"-B","-c","import sys;sys.stdout.buffer.write(sys.stdin.buffer.read()[::-1]);sys.stderr.write(\"independent_err\");raise SystemExit(7)"],check=False);raise SystemExit(7)')
run=subprocess.run([sys.executable,'-B','-c',child,command],input=b'abc\x00xyz',capture_output=True,cwd=R,env=env,timeout=30)
(OUT/'ssh.stdout.bin').write_bytes(run.stdout);(OUT/'ssh.stderr.log').write_bytes(run.stderr)
assert run.returncode==7 and run.stdout==b'zyx\x00cba' and run.stderr==b'independent_err'
write(OUT/'function_execution.json',dict(returncode=run.returncode,stdout_sha256=sha(OUT/'ssh.stdout.bin'),stderr_sha256=sha(OUT/'ssh.stderr.log'),command=command,scope_journal_only_stub=True))
rows=[json.loads(x)for x in journal.read_bytes().splitlines()];assert [x['event']for x in rows]==['ssh_start','ssh_end'];assert rows[0]['original_argv'][:4]==expected and rows[1]['returncode']==7
passed('actual_run_ssh_bash_binary_stdin_stdout_stderr_exit_and_grandchild')
# Reverify original actual PATH-shim integration evidence without copying or rerunning its fixture.
base=C/'tests_work_a1/H/control_repo/results/formal_main_v2/control_transport'
rows=[json.loads(x)for x in (base/'actual_f_inheritance.jsonl').read_bytes().splitlines()]
starts=[x for x in rows if x['event']=='ssh_start'];ends=[x for x in rows if x['event']=='ssh_end']
assert len(starts)==len(ends)==4 and {x['call_id']for x in starts}=={x['call_id']for x in ends}
assert all(x['original_argv'][:4]==expected for x in starts) and any('grandchild_ok'in x['original_argv'][-1]for x in starts)
assert any(x['returncode']==7 for x in ends) and rows[-1]['source173_and_entrypoint_unchanged'] is True
scp=[json.loads(x)for x in (base/'actual_scp.jsonl').read_bytes().splitlines()];copies=[x for x in scp if x['event']=='scp_end'];assert len(copies)==3 and [x['action']for x in copies]==['copied_exclusive','copied_exclusive','same_bytes_no_write']
passed('author_actual_scoped_PATH_SSH_f_grandchild_and_SCP_raw_journals_reconstructed')
# Relocation is __file__ relative; inspect an in-memory relocated module rather than publishing it.
relocated=R/'scripts/ops/server_control_transport_v1';ns={'__name__':'relocated_transport','__file__':str(relocated/'server_transport.py')}
exec(compile((C/'server_transport.py').read_bytes(),ns['__file__'],'exec'),ns)
assert ns['BUNDLE']==relocated and ns['R']==R and ns['P']==t.P
assert str(C) not in (C/'server_transport.py').read_text() and str(C) not in (C/'run_server_control.py').read_text()
for p in (C/'bin/ssh',C/'bin/scp'):
 assert '__file__'in p.read_text() and 'parent.parent / "server_transport.py"'in p.read_text() and os.access(p,os.X_OK)
passed('whole_bundle_relocation_no_C_literal_dependency')
assert dict(os.environ)==parent_environment and f.SSH==expected;t.verify_bundle(manifest_sha);t.verify_frozen()
for p,h in evidence.items():assert sha(p)==h,p
passed('parent_PATH_f_SSH_bundle_and_173_R_S_unchanged_after')
for p in OUT.iterdir():
 if p.is_file() and not p.is_symlink() and p.name not in ('audit.log','independent_review.json'):evidence[str(p)]=sha(p)
evidence[str(OUT/'audit.log')]=sha(OUT/'audit.log')
receipt=dict(independent_harness_initial_failure='Initial path assertion allowed H only and rejected actual P snapshot reference before candidate execution; original audit.py/audit.log retained. Only allowlisted P root added in audit_a2.py.',schema='formal_main_v2',kind='server_control_transport_independent_CPU_review',version='server-control-transport-independent-v1',status='passed_finite_CPU_review_pending_root_integration',utc=datetime.now(timezone.utc).isoformat(),candidate_root=str(C),candidate_review_sha256=sha(C/'candidate_review.json'),bundle_manifest_sha256=manifest_sha,independent_checks=checks,checks_passed=len(checks),author_tests_verified=20,
 scope=dict(new_outputs_only_under=str(OUT),local_files_written=0,real_R_or_P_writes=0,Slurm_submissions=0,GPU_seconds=0,sealed_values_read=False,weight_values_read=False,real173_R_S_SHA_verified_before_after=True),
 limitations=['Independent run_ssh used the original function and bash; only scope() was replaced to direct its audit journal outside read-only R.','The fully scoped original runner/PATH/f.SSH/shim/grandchild integration is independently reconstructed from the SHA-bound author raw journals, not rerun or relabelled as a new test.','No actual refresh/pull/review/Slurm operation was run. Different destination bytes are intentionally rejected; callers must use fresh staging locations.','Only exact one-command tongji-cvpr SSH and quiet single-file SCP are supported; Git transport must stay outside the scope.','Historical F:/ helper paths require separate checked repair; this transport does not rewrite them.'],
 relocation=dict(can_move_whole_bundle_to=str(relocated),hardcoded_candidate_C_dependency=False,requirements=['Preserve server_transport.py,run_server_control.py,bin/ssh,bin/scp,bundle_manifest.json together.','Retain executable permission on both bin shims; reverify exact bundle hash.','Authorize entrypoint by exact R-relative path/SHA and use a fresh audit-relative path.','Keep root capacity/pending/scientific guards intact; this transport grants no submission authorization.']),blockers=[],wall_seconds=time.monotonic()-start,read_evidence_sha256=dict(sorted(evidence.items())))
write(OUT/'independent_review.json',receipt)
print(json.dumps(dict(receipt=str(OUT/'independent_review.json'),sha256=sha(OUT/'independent_review.json'),checks=len(checks),status=receipt['status'],evidence=len(evidence),wall_seconds=receipt['wall_seconds'])))
