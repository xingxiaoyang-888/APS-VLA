from pathlib import Path
import hashlib,json,ast,difflib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/object64_recovery_independent_0238'
template='results/formal_main_v2/engineering/terminal_delivery_0943/independent/audit_3039258_v2.py'
pin='029dac536286154f200a6dbd2543241eb7d95fb0e8c81ae36210e2c00ad5eab7'
original=(R/template).read_bytes();assert hashlib.sha256(original).hexdigest()==pin
s=original.decode();changes=[]
def replace(a,b):
 global s
 n=s.count(a);assert n>0,repr(a)
 s=s.replace(a,b);changes.append({'from':a,'to':b,'occurrences':n})
for a,b in [
("D=R/'.local/cuda_recovery_independent_0943'","D=R/'.local/object64_recovery_independent_0238'"),
('3039258','3044017'),('3028460','3028468'),('/k256/seed23','/k64/seed23'),('_k256_seed23','_k64_seed23'),
("root['visual_tokens']==256","root['visual_tokens']==64"),("'visual_tokens':256","'visual_tokens':64"),
("config['tokens_per_camera']==128","config['tokens_per_camera']==32"),('f01_k256.json','f01_k64.json'),
('len(ix)==256','len(ix)==64'),('sum(i<256 for i in ix)==128','sum(i<256 for i in ix)==32'),('hard256 sorted packing','hard64 sorted packing'),
('6596','5210'),('6512','5141'),("('FAILED','1:0',84,1)","('FAILED','1:0',69,1)"),("('FAILED','1:0',84)","('FAILED','1:0',69)"),
("'retained_FAILED_GPU_seconds':84","'retained_FAILED_GPU_seconds':69"),("'gpu4010'","'gpu4017'"),
('2399d0f5b92b7ffe1d007d1df6fb1914b2c9765099bb8948bc9027873c6041ec','0f8c1eab2e196c544bbf1302d440085abf052bc0bbc32a6dc3d9377bcdb0aec0'),
("failuremod=load('.local/cuda_startup_recovery_0840/startup_failure_evidence.py')","failuremod=load('scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py')"),
("'cuda-recovery-independent-0943-v1'","'cuda-recovery-independent-0238-v1'"),
("and cur in [0,500] and r['windows']==204","and cur in [0,500] and cur not in seenval and r['windows']==204"),
]:replace(a,b)
insert=""" raw('SERVER_WORKSPACE.md','fe43ae998a45bc749b3de1acbb8841d5b413962b59b05f62284e3f503a9baf62')
 raw('docs/服务器工作区与GitHub同步.md','d7f0455ef4febb536df199653fd323a1cef98ad66732e5b2ea8edfdf06b75343')
 raw('scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py','c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480')
 raw('scripts/formal_cuda_terminal_review_v1/review_formal_segment_startup.py','ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4')
 raw('results/formal_main_v2/engineering/terminal_delivery_0943/independent/audit_3039258_v2.py','029dac536286154f200a6dbd2543241eb7d95fb0e8c81ae36210e2c00ad5eab7')
 need(args.root_review_sha256=='2bffb9a9194b4c1b434b0c79491d165ce6f14d12305f3ebe9b6f4843af288d84','exact canonical root')
 need(args.pull=='results/formal_main_v2/pulls/20261020T024610Z_89cee566247b/receipt.json' and args.pull_sha256=='aa509e9edbe2bb52ae1832501b7a4785c43fa579215e67a17f47d80e284ec53b','exact terminal pull')
"""
replace(" rootrel=REL+'/segment_reviews/3044017.json'",insert+" rootrel=REL+'/segment_reviews/3044017.json'")
replace(" need(root['source_sha256']==SOURCE and root['pair_allocated_gpu_seconds']==5210,'root source/cost')"," need(root['source_sha256']==SOURCE and root['pair_allocated_gpu_seconds']==5210,'root source/cost')\n need(root['allowed_next_segment_end']==1000 and root['resume_required'] is True,'only next registered boundary, no continuous admission')")
replace(" need(auth['original_target']==500 and auth['maximum_new_attempts']==1 and auth['resume'] is True,'target scope')"," need(auth['kind']=='cuda_startup_single_recovery_authorization' and auth['status']=='approved_for_exactly_one_original_target_recovery' and auth['original_target']==500 and auth['maximum_new_attempts']==1 and auth['resume'] is True,'target scope')")
replace(" for item in ['--no-requeue','--time=04:00:00','--exclude=gpu4020']:"," for item in ['--no-requeue','--time=04:00:00','--exclude=gpu4020','--comment=cti-cuda-recovery-v1:'+PIN]:")
replace("for key in ['canonical_publication','root_reservation'","for key in ['canonical_failure_review','canonical_publication','root_reservation'")
modelchecks=""" need(gate['job_id']=='3012482' and gate['runtime_compatibility']==job['runtime_compatibility'],'own Object accepted metadata runtime')
 need(all('component_compatibility' not in v for v in [original,current,job,oldj]),'Object uses metadata only, no Goal component adapter')
 registration=read('configs/experiments/formal_main_v2.json',inv['files']['configs/experiments/formal_main_v2.json'])
 suite=registration['suites']['libero_object'];pair=next(x for x in registration['pairs'] if x['suite']=='libero_object' and x['visual_tokens']==64 and x['seed']==23)
 model=read(suite['model_manifest'],suite['model_manifest_sha256'])
 need(model['repository']=='moojink/openvla-7b-oft-finetuned-libero-object' and model['revision']==config['model_revision']==suite['model_revision'],'own official Object base')
 expected=['--config',str(S/pair['path']),'--protocol',str(P/suite['protocol']),'--windows',str(P/suite['windows']),'--checkpoint',suite['model_root_server'],'--asset-manifest',str(S/suite['model_manifest']),'--data-directory',suite['data_root_server'],'--cache-directory',str(P/'.local/formal-hf-libero_object'),'--feature-cache',suite['cache_root_server'],'--training-checkpoints',pair['checkpoint_root_server'],'--input-acceptance-report',str(P/gate['output_relative']/'input_acceptance.json'),'--acceptance-report',str(P/gate['output_relative']/'f01_k64.json'),'--output',str(P/REL),'--arm','both','--stop-after-updates','500','--max-wall-seconds','12600','--resume']
 need(current['argv']==expected,'complete original scientific argv retained')
 official_components=[]
 for name in ['action_head--150000_checkpoint.pt','proprio_projector--150000_checkpoint.pt']:
  spec=next(x for x in model['files'] if x['path']==name)
  actual=shafile(Path(suite['model_root_server'])/name)
  need(actual['sha256']==spec['sha256'] and actual['bytes']==spec['size'],'official Object component actual bytes')
  official_components.append(actual)
"""
replace(" for name,sha in gate['files'].items():raw(gate['output_relative']+'/'+name,sha)",modelchecks+" for name,sha in gate['files'].items():raw(gate['output_relative']+'/'+name,sha)")
replace(" reports={};initial_rows={};summaries={};resumechecks=[]"," reports={};initial_rows={};summaries={};resumechecks=[];candidatechecks=[]\n trainer=raw('src/cti_vla/training/formal_future.py').decode()\n need('optimizer.load_state_dict(saved[\"optimizer\"])' in trainer and 'restore_rng(saved[\"rng\"])' in trainer,'unchanged optimizer/RNG restore path')")
replace("  initial_rows[arm]=", """  need([e['update'] for e in evaluations]==[0,500],'exact raw validation nodes once')
  for ev in report['evaluations']:
   candidate=H/'checkpoints/formal_main_v2/libero_object/k64/seed23'/arm/'candidates'/(attempt+'_update'+str(ev['update']).zfill(5)+'.pt')
   need(ev['candidate_path']==str(candidate),'exact candidate path')
   actual=shafile(candidate);need(actual['sha256']==ev['candidate_sha256'],'candidate raw byte identity')
   candidatechecks.append(dict(arm=arm,update=ev['update'],**actual))
  initial_rows[arm]=""")
mirrorchecks=""" mirror_ref='results/formal_main_v2/preflight/heartbeat_20261020T1038/3044017_slurm_log_server_mirror.json'
 mirror=read(mirror_ref,'28bdb6e7469097b97c0da658cd230bd5a39de6eaad93bb7991fefc9db0b9df33')
 need(mirror['job_id']=='3044017' and mirror['terminal'] is True and mirror['raw_bytes_changed'] is False and mirror['slurm_wrapper']=={'path':'scripts/server/formal_asset_main.slurm','sha256':'9d54e0486a078a8358c8443bb92db8c8096d9ac3988eff693fa69b250d97c36a'},'exact raw stdout/stderr origin correction')
 need(len(mirror['mirrored'])==2,'two logs only')
 for row in mirror['mirrored']:
  rel=Path(row['source']).relative_to(R).as_posix()
  need(rel in ['results/slurm/cti-formal_3044017.out','results/slurm/cti-formal_3044017.err'] and row['destination']==str(P/rel) and row['source_retained'] is True,'log mirror exact scope')
  data=raw(rel,row['sha256']);need(len(data)==row['bytes'] and shafile(P/rel)['sha256']==row['sha256'],'same original logs R/P')
"""
replace(" for rel,sha in root['files'].items():raw(rel,sha)",mirrorchecks+" for rel,sha in root['files'].items():raw(rel,sha)")
acceptancechecks=""" gatejob=gate['job_at_review'];gateinv=read(gatejob['invocation'],gatejob['invocation_sha256'])
 gatereceipt=read('results/formal_main_v2/job_receipts/'+gatejob['job_id']+'.json')
 gatepull=gate['runtime_compatibility_review']['pull_receipt'];raw(gatepull['path'],gatepull['sha256'])
 ge=shared.Evidence(R)
 gm=shared.review_runtime_compatibility(ge,job=gatejob,invocation=gateinv,receipt=gatereceipt,inventory=inv,pull_receipt=gatepull['path'])
 need(gm==gate['runtime_compatibility_review'],'own original Object acceptance metadata proof reconstructed')
 ge.unchanged()
 for rel,sha in ge.hashes.items():raw(rel,sha)
"""
replace(" for rel,sha in list(readmap.items()):",acceptancechecks+" for rel,sha in list(readmap.items()):")
replace("'actual_server_resume_checks':resumechecks,","'actual_server_resume_checks':resumechecks,'actual_server_candidate_checks':candidatechecks,'official_Object_components':official_components,'acceptance_metadata_reconstruction':gm,'recovery_metadata_reconstruction':rebuilt,'log_mirror':{'path':mirror_ref,'sha256':readmap[mirror_ref]},'completed_by_arm':{'A':500,'B':500},'allowed_next_segment_end':1000,'reviewed_arm_updates_added':1000,")
ast.parse(s)
stripped=s.replace(template,'')
for bad in ['k256','3039258','3028460','6512','6596','gpu4010']:assert bad not in stripped,bad
entry=D/'audit_3044017.py'
with entry.open('x') as f:f.write(s)
sh=hashlib.sha256(entry.read_bytes()).hexdigest()
with (D/'adaptation.json').open('x') as f:json.dump({'schema':'formal_main_v2','kind':'exact_original_target_recovery_audit_adaptation','template':{'path':template,'sha256':pin},'script':{'path':entry.relative_to(R).as_posix(),'sha256':sh},'scope':'Exact Object64 seed23 original0->500 recovery. Original predicates retained with actual identities; explicit own Object component/acceptance and candidate-byte checks; no optimizer deserialization, production review publication or submission.','changes':changes},f,sort_keys=True,indent=2);f.write('\n')
with (D/'audit.diff').open('x') as f:f.write(''.join(difflib.unified_diff(original.decode().splitlines(keepends=True),s.splitlines(keepends=True),fromfile=template,tofile=entry.relative_to(R).as_posix())))
print(json.dumps({'prepared_entry':entry.relative_to(R).as_posix(),'sha256':sh,'bytes':entry.stat().st_size,'AST':'valid','executed':False}))
