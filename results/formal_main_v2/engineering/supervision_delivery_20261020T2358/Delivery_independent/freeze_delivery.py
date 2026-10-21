from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_independent_20261020T2358';H=lambda b:hashlib.sha256(b).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--review-sha256',required=True);a=ap.parse_args()
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('No execution or network during private manifest freeze')
 if event=='open':
  p,m,f=args
  if isinstance(p,(str,bytes)) and ((m and any(c in m for c in 'wax+')) or (isinstance(f,int) and f&(1|2|64|512|1024))):assert Path(p).resolve().is_relative_to(D)
sys.addaudithook(guard)
def put(name,b):
 p=D/name;assert p.parent==D and not p.exists()
 with p.open('xb') as f:f.write(b)
 return {'path':str(p.relative_to(R)),'sha256':H(b),'bytes':len(b)}
def jout(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
p=D/'final_independent_review.json';b=p.read_bytes();assert H(b)==a.review_sha256
review=json.loads(b);assert review['status']=='passed_final_delivery_review' and review['blockers']==[] and review['source173_verified'] and review['final_sealed']
assert review['check_count']==len(review['checks'])
assert H((R/'results/experiment_supervisor/state.json').read_bytes())==review['state_sha256']
closed=[];open_journals=[]
for p in sorted((R/'results/formal_main_v2/control_transport').glob('delivery_independent_*_20261020T2358.jsonl')):
 b=p.read_bytes();lines=[json.loads(x) for x in b.splitlines()];assert lines and lines[0]['event']=='control_start'
 assert lines[0]['entrypoint'].startswith(D.relative_to(R).as_posix()+'/')
 if lines[-1]['event']!='control_end':
  open_journals.append(str(p.relative_to(R)));continue
 src={'path':str(p.relative_to(R)),'sha256':H(b),'bytes':len(b)}
 closed.append({'source':src,'archive':put(p.name,b),'events':[x['event'] for x in lines]})
readme=f"""# 20261020T2358 root delivery independent review

Status: passed_final_delivery_review, tied to state SHA {review['state_sha256']}.
Final report SHA {a.review_sha256}; immutable checks list length {len(review['checks'])}.
Scope: actual final state/doc snapshot and exact nonweight evidence archive; Git helper source audit only, before commit and push.

- 72 arms / 36 pairs / 360000 updates remain complete. Original training validation and root/independent evidence are preserved; this audit does not rehash weights or rerun training.
- 5800 current rows, 6400 accepted complete-batch rows, 7012 historical rows, 400 unique states remain unchanged.
- Object599 are separately adopted legacy references, with 520 successes and all 79 ordinary task failures retained. Original policy_error and all 6713 GPU seconds remain; whole600 and a new correction trial are not admitted.
- Goal fixed one full200 prospective design only: 200 trials / 60000 control steps / 7600 queries. Old200 and additional1000 stay HOLD. No causal repair claim or new runtime/output/token/GPU authority.
- One preserved UTC2026-10-21T00:03:34 observation, 271 unique allocations, 1987496 GPU seconds as lower bound, Spatial3054201 RUNNING2194sec. No new Slurm queries. The unarchived raw-progress count was withdrawn in root snapshot v5 / input v2; former unexecuted helpers remain as history.
- Source173 verified at canonical R, frozen S, and R mirror; final sealed0/35200, no O2A/global release.
- Root must consume the exact independent report SHA with matching state before its separately guarded Git commit. Actual commit/push and remote HEAD are still pending and are not asserted by this package.

Earlier static scripts v4/v5 failed because of auditor literal-matching mistakes; original scripts and closed failed transport journals are retained. They did not execute root delivery helpers or change scientific evidence. Unexecuted actual-audit v1/v2 scripts preserve preparation history; v3 adds parsing of the already archived raw_sacct without polling.
All writes here are confined to this private server audit directory, plus the approved transport's own journals. No production state, Git, P, canonical or Slurm modifications.
"""
put('README.md',readme.encode())
files=[]
for p in sorted(D.rglob('*')):
 if not p.is_file():continue
 assert p.resolve()==p and not any(q.is_symlink() for q in [p,*p.parents])
 assert p.suffix.lower() in {'.py','.json','.jsonl','.md'} and p.stat().st_size<100*(1<<20)
 assert p.name!='delivery_manifest.json'
 b=p.read_bytes();files.append({'path':str(p.relative_to(R)),'bytes':len(b),'sha256':H(b)})
manifest={'schema':'formal_main_v2','kind':'root_final_delivery_independent_manifest','status':'passed_final_delivery_review','root':str(D.relative_to(R)),'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'files':files,'final_review':{'path':str((D/'final_independent_review.json').relative_to(R)),'sha256':a.review_sha256},'check_count':len(review['checks']),'state_sha256':review['state_sha256'],'blockers':[],'source173_verified':True,'final_sealed':True,'final_release':False,'Git_commit_and_push_pending':True,'new_GPU_submissions':0,'new_scientific_trials':0,'additional_Slurm_queries':0,'no_state_Git_P_canonical_writes':True,'closed_transport_journals':closed,'open_transport_journals_excluded':open_journals,'utc':datetime.now(timezone.utc).isoformat()}
m=put('delivery_manifest.json',jout(manifest))
print(json.dumps({'manifest':m,'file_count':len(files),'total_bytes':manifest['total_bytes'],'final_review':manifest['final_review'],'state_sha256':review['state_sha256'],'status':manifest['status']}))
