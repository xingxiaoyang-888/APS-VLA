from pathlib import Path
import hashlib,json,ast,difflib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=Path(__file__).resolve().parent
REL=D.relative_to(R).as_posix()
TEMPLATE='.local/audit_training_segment_3025581.py'
TEMPLATE_SHA='6058096035cbc29d39b5bb73faf02a29272d0b8b7f9aef1c395e875fd1a6f011'
PULL='results/formal_main_v2/pulls/20261018T164114Z_d2a1355175b5/receipt.json'
PULL_SHA='7b1d8e836749c48300912c5aec00de28d3767f729d825778a89b353d4192db3f'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
 with p.open('xb') as f:f.write(b)
assert sha((R/TEMPLATE).read_bytes())==TEMPLATE_SHA
assert sha((R/PULL).read_bytes())==PULL_SHA
original=(R/TEMPLATE).read_text()
pull=json.loads((R/PULL).read_text())
byrel={row['relative']:row for row in pull['files']}
cases={
 '3028452':dict(seed=41,budget=64,jobs=['3025080','3028452'],target=1000,total=9431,latest=4311),
 '3028457':dict(seed=23,budget=256,jobs=['3023656','3025196','3028457'],target=1500,total=14153,latest=4428),
 '3030091':dict(seed=17,budget=256,jobs=['3023005','3023875','3025581','3030091'],target=2000,total=16766,latest=4047),
 '3030099':dict(seed=17,budget=64,jobs=['3023228','3024981','3025841','3030099'],target=2000,total=13942,latest=4030),
 '3030166':dict(seed=41,budget=256,jobs=['3025845','3030166'],target=1000,total=6586,latest=3173)}
inputs={TEMPLATE:TEMPLATE_SHA,PULL:PULL_SHA}
for jid,c in cases.items():
 c.update(suite='libero_spatial',pool=34703,val=189,gate='attempt01',stats='3f8b7854c8634ea6ccfd6ef6b8f983e3b30b067c2cdaf690b152c0899d5d9282')
 c['resume']={}
 for arm in ['A','B']:
  rel=f"results/formal_main_v2/libero_spatial/k{c['budget']}/seed{c['seed']}/training/{arm}/progress_report.json"
  b=(R/rel).read_bytes();assert sha(b)==byrel[rel]['sha256']; inputs[rel]=sha(b)
  value=json.loads(b);assert value['training_updates_completed']==c['target'] and value['next_sample_cursor']==c['target']*8 and value['job_ids']==c['jobs']
  c['resume'][arm]=value['resume_sha256']
prep={'schema':'formal_main_v2','kind':'independent_audit_preparation','status':'prepared_not_audited','pull':PULL,'pull_sha256':PULL_SHA,'template':TEMPLATE,'template_sha256':TEMPLATE_SHA,'cases':cases,'evidence_sha256':inputs,'scope':'Only current successful Spatial partial segments; no state, weights, sealed values or GPU. Pending root operation SHA is mandatory at execution.'}
prep_rel=REL+'/input_preparation.json';prep_bytes=(json.dumps(prep,sort_keys=True,indent=2)+'\n').encode();put(R/prep_rel,prep_bytes)
prep_sha=sha(prep_bytes)
outputs={}
for jid,c in cases.items():
 s=original
 def rep(a,b,n=1):
  global s
  assert s.count(a)==n,(jid,a[:100],s.count(a),n)
  s=s.replace(a,b)
 rep("args.add_argument('--case', choices=['spatial17'], required=True)","args.add_argument('--case', choices=['spatial'], required=True)\nargs.add_argument('--operation-sha', required=True)")
 start=s.index('CASES={\n');end=s.index("T=CASES[opts.case]")
 s=s[:start]+"CASES={'spatial':"+repr(c)+"}\n"+s[end:]
 rep("ROOT=Path('F:/CTI-VLA')",f'ROOT=Path({str(R)!r})')
 rep("BASE=f'results/formal_main_v2/{SUITE}/k256/seed{SEED}/training'",f"BUDGET={c['budget']};PER_CAMERA=BUDGET//2\nBASE=f'results/formal_main_v2/{{SUITE}}/k{{BUDGET}}/seed{{SEED}}/training'")
 rep("OUT=BASE+f'/segment_reviews/{JOBS[-1]}_independent.json'",f"OUT={REL+'/'+jid+'_independent.json'!r}")
 rep("    path = Path(rel)\n    if path.is_absolute():", "    text = str(rel).replace('\\\\','/')\n    if text.startswith('F:/CTI-VLA/'):\n        text = text[len('F:/CTI-VLA/'):]\n    path = Path(text)\n    if path.is_absolute():")
 rep("AUDIT_LOG='.local/audit_training_segment_3025581.log'",f"AUDIT_LOG={REL+'/audit_training_segment_'+jid+'.log'!r}")
 rep("raw(audit_self_relative)","raw(audit_self_relative)\nverify("+repr(TEMPLATE)+","+repr(TEMPLATE_SHA)+")\nverify("+repr(prep_rel)+","+repr(prep_sha)+")\nraw("+repr(REL+'/prepare_spatial_audits.py')+")\ncheck(PULL=="+repr(PULL)+" and opts.pull_sha=="+repr(PULL_SHA)+",'fixed stable joint pull')")
 start=s.index("verify('.local/root_pull_review_2250_3025581.json'");end=s.index('review = read(ROOT_REVIEW)',start)
 block="""OPERATION=OPERATION_LITERAL
verify(OPERATION,opts.operation_sha)
operation=read(OPERATION)
check(operation['status']=='passed' and operation['job_id']==JOBS[-1] and operation['root_review']==ROOT_REVIEW
      and operation['root_sha256']==opts.root_sha and operation['pull']==PULL and operation['pull_sha256']==opts.pull_sha
      and operation['histories']==JOBS and operation['boundary']==TARGET and operation['allowed_next']==TARGET+500
      and operation['suite']==SUITE and operation['budget']==BUDGET and operation['seed']==SEED
      and operation['pair_gpu_seconds']==T['total'] and operation['latest_gpu_seconds']==T['latest'], 'root operation binding')
command=operation['command']
check(command[command.index('--entrypoint')+1]=='scripts/review_formal_segment.py'
      and command[command.index('--job-id')+1]==JOBS[-1] and '--verify-server-resume' in command
      and command[command.index('--pull-receipt')+1]==PULL,'actual root review entry/remote hash probe request')
verify('scripts/review_formal_segment.py',command[command.index('--entrypoint-sha256')+1])
raw(command[command.index('--audit-relative')+1])
""".replace('OPERATION_LITERAL',repr(f'results/formal_main_v2/preflight/heartbeat_20261019T0037/operation_{jid}.json'))
 s=s[:start]+block+s[end:]
 rep("check(review['status'] == 'passed' and review['job_id'] == JOBS[-1], 'wrong root review')", "check(review['status'] == 'passed' and review['job_id'] == JOBS[-1], 'wrong root review')\ncheck(review['evidence_sha256'].get(PULL)==opts.pull_sha,'root review exact joint pull binding')")
 rep("T['total']=review['pair_allocated_gpu_seconds']\ncheck(T['total']==12719, 'expected three-job total differs')\nT['latest']=jobs[JOBS[-1]]['elapsed_seconds']\ncheck(T['latest']==4475, 'latest allocation cost')", "check(review['pair_allocated_gpu_seconds']==T['total'],'expected full pair total differs')\ncheck(jobs[JOBS[-1]]['elapsed_seconds']==T['latest'],'latest allocation cost')")
 rep("check(review['allowed_next_segment_end']==2000 and review['completed_by_arm']=={'A':1500,'B':1500} and review['requested_segment_end']==1500", "check(review['allowed_next_segment_end']==TARGET+500 and review['completed_by_arm']=={'A':TARGET,'B':TARGET} and review['requested_segment_end']==TARGET")
 rep("T['resume']={row['arm']:row['sha256'] for row in review['server_resume_checks']}","root_resume={row['arm']:row['sha256'] for row in review['server_resume_checks']}")
 rep("check(T['resume']=={'A':'2ece04eeff2dd6a9d14e3ca69a5713c0b84d7323490175fe3b0ecd3f12ec26b1','B':'1cdaad86ba028f700bdebaa84a497db388d1d16daa332150a9ba1fdc8d364f3f'},'latest actual server hashes')","check(root_resume==T['resume'],'latest root actual server hashes match pinned progress')")
 rep('(SUITE, 256, SEED)','(SUITE, BUDGET, SEED)')
 rep("f'{SUITE}_train_k256_seed{SEED}'","f'{SUITE}_train_k{BUDGET}_seed{SEED}'")
 s=s.replace('f01_k256.json',f"f01_k{c['budget']}.json")
 rep("f01['visual_tokens'] == 256 and f01['per_camera_budgets'] == [128, 128]", "f01['visual_tokens'] == BUDGET and f01['per_camera_budgets'] == [PER_CAMERA, PER_CAMERA]")
 rep('tokens_per_camera=128','tokens_per_camera=PER_CAMERA')
 rep('len(inds)==256','len(inds)==BUDGET')
 rep('sum(i<256 for i in inds)==128', 'sum(i<256 for i in inds)==PER_CAMERA')
 rep("reviewer='profile_long'", "reviewer='deploy64'")
 rep('seed=SEED,visual_tokens=256','seed=SEED,visual_tokens=BUDGET')
 rep('per_camera_budgets=[128,128]','per_camera_budgets=[PER_CAMERA,PER_CAMERA]')
 rep('weights_copied=False,ssh_used=False,new_gpu_seconds=0',"weights_copied=False,ssh_used=True,ssh_scope='memory-stream transport to R only; no independent checkpoint probe',new_gpu_seconds=0")
 rep("'A/B share fresh initialization and complete seeded40000 order; all three500-update segments commit12000 uses per arm without replay, restoring update500/cursor4000 and update1000/cursor8000. The next segment must restore the verified1500/cursor12000 boundary.'", "f'A/B share fresh initialization and complete seeded40000 order; all {len(JOBS)} registered500-update segments commit{SAMPLES} uses per arm without replay. Every intermediate resume update/cursor matches the preceding original raw commit; next restores {TARGET}/{SAMPLES}.'")
 rep("'Hard validation256 tokens ordered uniquely,128 per camera; task-macro teacher L1 and earliest best-so-far recomputed.'", "f'Hard validation{BUDGET} tokens ordered uniquely,{PER_CAMERA} per camera; task-macro teacher L1 and earliest best-so-far recomputed.'")
 rep("'Spatial acceptance and all three training allocations contain no Object/Goal compatibility contracts; no compatibility runner was used.'", "f'Spatial acceptance and all {len(JOBS)} training allocations contain no Object/Goal compatibility contracts; no compatibility runner was used.'")
 start=s.index('    audit_implementation=dict(');end=s.index('\nif opts.write:',start)
 s=s[:start]+"    audit_implementation=dict(path=audit_self_relative,sha256=READ[audit_self_relative],local_dependencies=[audit_self_relative,AUDIT_LOG,OPERATION,"+repr(REL+'/prepare_spatial_audits.py')+','+repr(prep_rel)+','+repr(TEMPLATE)+"],adaptation_references=["+repr(TEMPLATE)+"],adaptation='Server control ROOT/output and exact job/budget pins only; raw validation algorithm retained; old F metadata locations map exact relative suffix into R and retain SHA checks.'))"+s[end:]
 ast.parse(s)
 assert "F:/CTI-VLA" not in s.replace("text.startswith('F:/CTI-VLA/')",'').replace("text[len('F:/CTI-VLA/'):]",'')
 path=D/f'audit_training_segment_{jid}.py';put(path,s.encode())
 diff=''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile=TEMPLATE,tofile=path.relative_to(R).as_posix()))
 dp=D/f'audit_training_segment_{jid}.diff';put(dp,diff.encode())
 outputs[path.relative_to(R).as_posix()]=sha(s.encode());outputs[dp.relative_to(R).as_posix()]=sha(diff.encode())
receipt={'schema':'formal_main_v2','kind':'independent_audit_preparation','status':'prepared_not_executed','template':TEMPLATE,'template_sha256':TEMPLATE_SHA,'inputs':prep_rel,'inputs_sha256':prep_sha,'generator':Path(__file__).relative_to(R).as_posix(),'generator_sha256':sha(Path(__file__).read_bytes()),'outputs':outputs,'notes':['No root pass inferred. Each audit requires fixed current root SHA and operation SHA.','Only server audit output paths permitted. No GPU, Slurm, shared state or scientific source changes.']}
put(D/'preparation.json',(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(receipt,sort_keys=True))
