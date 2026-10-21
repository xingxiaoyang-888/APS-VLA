from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261021T1134';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0334'
BASE='328e3b918379a985ef299cee4891138a55874827'
STATE='results/experiment_supervisor/state.json'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json'
SSHA='1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def rd(n,pin=None):
 if pin:assert h(R/n)==pin,n
 return json.loads((R/n).read_bytes())
def save(n,v):
 p=R/n;assert not p.exists(),n;p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write((json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode());return ref(n)
def cp(src,dst):
 p=R/src;q=R/dst;assert p.resolve()==p and q.resolve()==q and not p.is_symlink() and not q.exists();q.parent.mkdir(parents=True,exist_ok=True);q.open('xb').write(p.read_bytes());return ref(dst)
def module(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def git(*args,data=None,check=True):
 return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,input=data,check=check)
def package(private,pin,dest):
 mp=private+'/delivery_manifest.json';v=rd(mp,pin);seen=set();rows=[]
 for x in v['files']:
  n=x['path'];n=Path(n).relative_to(private).as_posix() if n.startswith(private+'/') else n
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and n not in seen;seen.add(n)
  src=private+'/'+n;assert h(R/src)==x['sha256'] and (R/src).stat().st_size==x['bytes']
  rows.append(dict(source=src,**cp(src,dest+'/'+n)))
 cp(mp,dest+'/delivery_manifest_original.json');save(dest+'/root_publication_mapping.json',dict(source_manifest=ref(mp),files=rows))
ap=argparse.ArgumentParser();ap.add_argument('--state-sha256',required=True);ap.add_argument('--summary-sha256',required=True);ap.add_argument('--preaudit-manifest-sha256',required=True);ap.add_argument('--preaudit-report-sha256',required=True);a=ap.parse_args()
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
ctl=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','stage0334ctl')
guard=module('scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6','stage0334guard')
with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==BASE
 assert not git('diff','--cached','--name-only').stdout
 assert h(R/STATE)==a.state_sha256
 s=rd(B+'/final_summary.json',a.summary_sha256);assert s['compatible_development_trials']==7800 and s['current_action_development_trials']==6589 and s['final_sealed'] and not s['new_GPU_jobs']
 q=rd(B+'/root_integration_receipt.json');assert q['state_after']==ref(STATE) and q['summary']==ref(B+'/final_summary.json')
 pr='.local/delivery_independent_20261021T0334'
 pre=rd(pr+'/preintegration_review.json',a.preaudit_report_sha256);assert pre['status']=='passed_bounded_preintegration' and not pre['blockers']
 package(pr,a.preaudit_manifest_sha256,E+'/Delivery_preintegration')
 package('.local/goal_remaining5_design_20261021T0334','83b17715c073995fb0ca87efd1151e7bf9b6438ffe2f2a135478d9a12ff93ea3',E+'/Goal_remaining5_design')
 doc='docs/正式下游阻塞登记_20261021T0334.md';old=(R/doc).read_bytes()
 addition='\n## Goal 剩余五配对的发布缺口\n\nCPU设计逐项核对原训练双审、10份选中checkpoint身份和原100开发初态；256 seed23/41、64 seed17/23/41各200条均未发现开发提交。五份P配置及各自execution manifest、scientific plan、invocation尚未发布，不能复用3054717的专用入口或收据。原缺P检查与跨套件同名method误拒均保留。详见[CPU证据与下一轮门槛](../'+E+'/Goal_remaining5_design/README.md)。设计不是生产准入；本轮不提交这五组。\n'
 (R/doc).write_bytes(old+addition.encode())
 save(B+'/remaining5_design_publication.json',dict(status='CPU_design_only_HOLD',source_manifest=ref(E+'/Goal_remaining5_design/delivery_manifest_original.json'),design=ref(E+'/Goal_remaining5_design/design.json'),preintegration_audit=ref(E+'/Delivery_preintegration/preintegration_review.json'),document=dict(path=doc,before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=h(R/doc)),new_GPU_jobs=0,new_trials=0,production_ready=False))
 names=['observe_20261021T0334.py','observe_20261021T0334_v2.py','pull_object_terminal_20261021T0334.py','pull_goal_terminal_20261021T0334.py','review_object_terminal_20261021T0334.py','review_terminal_pair_20261021T0334.py','integrate_goal_archive_20261021T0334.py','integrate_terminals_20261021T0334.py','integrate_terminals_20261021T0334_v2.py','integrate_terminals_20261021T0334_v3.py','stage_delivery_20261021T0334.py',Path(__file__).name]
 for n in names:cp('.local/'+n,B+'/root_operations/'+n)
 selected=set()
 for root in [B,E]:
  for p in (R/root).rglob('*'):
   if p.is_file():assert not p.is_symlink();selected.add(p.relative_to(R).as_posix())
 for n in [STATE,'scripts/ops/formal_object_terminal_pull_bridge_v1/bridge.py',doc,'docs/正式主实验规划.md','docs/完整实验计划.md','docs/实验进度.md','docs/正式主实验阶段结论.md','docs/正式非Long开发结果.md','docs/正式Goal主预算开发结果.md']:selected.add(n)
 pull_paths=['results/formal_main_v2/pulls/terminal_object_20261021T0334/receipt.json','results/formal_main_v2/pulls/terminal_goal_20261021T0334/receipt.json']
 exact_pulled=[];loose_blob_exclusions=[]
 for n in pull_paths:
  v=rd(n);selected.add(n)
  for x in v['files']:
   rel=x['relative'];assert str(R/rel)==x['local_path']
   if rel.endswith('.bin'):
    assert n==pull_paths[1] and '/attempt01/observer/blobs/' in rel
    loose_blob_exclusions.append(rel);continue
   assert ref(rel)==dict(path=rel,sha256=x['sha256'],bytes=x['bytes']);selected.add(rel);exact_pulled.append(ref(rel))
 assert len(exact_pulled)==26 and len(loose_blob_exclusions)==15522
 traces=[]
 for p in sorted((R/'results/formal_main_v2/control_transport').glob('*20261021T0334*.jsonl')):
  ev=[json.loads(x) for x in p.read_bytes().splitlines()];assert ev and ev[0]['event']=='control_start'
  if ev[-1]['event']!='control_end':
   assert p.name=='stage_delivery_20261021T0334_v2.jsonl',p.name;continue
  n=p.relative_to(R).as_posix();selected.add(n);traces.append(ref(n))
 manifest=rd(E+'/Goal_archive/archive_manifest.json','18c61e6a89047e7c4a0cdab7e6111f73a36db0421a3c2b1627a2f01944cf4d21')
 volumes=manifest['parts'];assert len(volumes)==24
 archive_files=[]
 for x in volumes:
  n=E+'/Goal_archive/'+x['path'];r=ref(n);assert r['sha256']==x['sha256'] and r['bytes']<90*(1<<20)
  archive_files.append(r);assert n in selected
 fixtures=[ref(n) for n in sorted(selected) if '/Goal_archive/verifier_fixtures/' in n]
 assert len(fixtures)==9
 allow=B+'/git_external_nonweight_allowlist_v1.json'
 save(allow,dict(schema='formal_main_v2',kind='exact_terminal_nonweight_Git_allowlist',pull_receipts=[ref(x) for x in pull_paths],pulled_nonweight_files=exact_pulled,archived_Goal_real_volumes=archive_files,archived_Goal_test_fixtures=fixtures,archive_inventory=ref(E+'/Goal_archive/inventory.json'),archive_root_verification=ref(B+'/Goal_archive_root_verification.json'),loose_P_passive_blobs_excluded=15522,R_raw_observation_payloads_only_archived=True,source_goal_observation_blob_count=19540,no_weights_or_final_values=True));selected.add(allow)
 trace_meta=B+'/root_transport_manifest.json';save(trace_meta,dict(files=traces,current_stage_transport_deferred_until_finished=True));selected.add(trace_meta)
 assert len({n.casefold() for n in selected})==len(selected)
 for n in selected:
  guard.lexical(n)
  assert 0<=(R/n).stat().st_size<100*(1<<20)
  assert '/raw_runtime/' not in n and '/observer/blobs/' not in n
  if n.endswith('.tar.gz'):assert n in {x['path'] for x in archive_files+fixtures},n
 ignored=[]
 for n in sorted(selected):
  z=git('check-ignore','-q','--',n,check=False)
  assert z.returncode in [0,1]
  if z.returncode==0:ignored.append(ref(n))
 ign=B+'/git_ignored_allowlist_v1.json';save(ign,dict(kind='exact_nonweight_paths_only',files=ignored,reason='Only individually hashed observed development metadata, validated nonweight archive members and audit evidence. No weights, loose blobs or sealed final values.'));selected.add(ign)
 required=B+'/git_required_files_v1.json';rows=[ref(n) for n in sorted(selected)]
 save(required,dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=rows))
 ignored_set={x['path'] for x in ignored}
 for n in sorted(selected|{required}):
  git('add',*(['-f'] if n in ignored_set else []),'--',n)
  assert git('show',':'+n).stdout==(R/n).read_bytes()
 raw=[x['path'] for x in rd(SNAP)['files']]
 checked=guard.check(R,SNAP,SSHA,raw,required)
 assert checked['status']=='verified_index_archive_delivery' and checked['frozen_files_verified_in_worktree_and_index']==173
 save(B+'/git_index_guard_v1.json',checked)
 diag=git('diff','--cached','--check',check=False)
 save(B+'/git_whitespace_diagnostic_v1.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 for n in [B+'/git_index_guard_v1.json',B+'/git_whitespace_diagnostic_v1.json']:git('add','--',n)
 assert h(R/STATE)==a.state_sha256 and h(R/B/'final_summary.json')==a.summary_sha256
 assert not diag.returncode,diag.stdout.decode()
 print(json.dumps(dict(status='staged_not_committed',required=ref(required),state_sha256=a.state_sha256,summary_sha256=a.summary_sha256,index_sha256=h(R/'.git/index'),staged_count=len(git('diff','--cached','--name-only').stdout.decode().splitlines()),independent_delivery_next=True)))
