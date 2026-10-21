from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,types,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/object_terminal_independent_20261021T0334';B='results/formal_main_v2/preflight/heartbeat_20261021T1134'
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'scripts/ops/formal_object_single_error_v1'),str(S/'src')]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pinned(n,pin):p=R/n;assert h(p)==pin;return p.read_bytes()
def save(n,v):(D/n).open('x',encoding='utf-8').write(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
pinned('scripts/ops/formal_object_single_error_v1/reviewer.py','c0aa1fc3d7c1607032897d7eede009bb989753daf58911d2b3351b4df7a030a2')
pinned(B+'/Object_original_terminal_review_failure.json','c9e652dcb68bb2def299bbe9c2dbb48bedaf8c5c94df7d75fcf172436c4e2fdd')
projection=json.loads(pinned(B+'/terminal_analysis_supervisor_projection.json','28972a53a01b3bf21e7c2194fe8b7fd31106fd49ed47290beb1a4f871d363513'))
pull='results/formal_main_v2/pulls/terminal_object_20261021T0334/receipt.json';pinned(pull,'1ab834c09cc562f4fce9224bf98bc6c80d31dbaadcb6a3381c877c1395aad710')
state_before=h(R/'results/experiment_supervisor/state.json')
from cti_vla.evaluation import formal_trials as M
assert Path(M.__file__).resolve()==S/'src/cti_vla/evaluation/formal_trials.py'
import reviewer as Q
import fixed as F
import iterator as I
source=(S/F.LOOP).read_bytes();assert hashlib.sha256(source).hexdigest()==F.LOOP_SHA and source==(R/F.LOOP).read_bytes()
actual=json.loads((P/'results/formal_main_v2/object_single_error_invocations/3054409/iterator_events.jsonl').read_bytes().splitlines()[0])['derivation']
proofs={}
for label,base in [('R',R),('S',S)]:
 name='_independent_Object_'+label+'_source_origin';module=types.ModuleType(name);module.__file__=str(base/F.LOOP);sys.modules[name]=module
 exec(compile(source,str(base/F.LOOP),'exec',dont_inherit=True),module.__dict__)
 proofs[label]=I.derive_loop(module,source)[2]
_,_,loaded=I.derive_loop(M,source)
differences={k:{'actual':actual[k],'R_expected':proofs['R'][k],'S_expected':proofs['S'][k]} for k in actual if actual[k]!=proofs['R'][k]}
assert set(differences)=={'original_code_sha256','derived_code_sha256'}
assert proofs['S']==loaded==actual and proofs['R']!=actual
origin=dict(schema='formal_main_v2',kind='Object3054409_original_reviewer_source_origin_diagnosis',status='exact_cause_reproduced_for_review_environment_only',actual_scientific_module_path=str(Path(M.__file__).resolve()),actual_co_filename=M.evaluate_formal_trials.__code__.co_filename,source_raw_identical=True,source_sha256=F.LOOP_SHA,actual_derivation=actual,R_compilation_derivation=proofs['R'],S_compilation_derivation=proofs['S'],differences=differences,explanation='marshal.dumps(code,2) includes co_filename; R-loaded and exact S-executed functions have equal AST/source but different two code signatures. Explicitly preload S/src before review to reconstruct the actually executed filename identity; no source guard needs removal.',canonical_source_modified=False,scientific_runtime_issue_inferred=False,new_GPU_submissions=0,new_Slurm_queries=0)
save('source_origin_diagnosis.json',origin)
try:
 result=Q.review('3054409',pull,project=R,state=projection)
 consumed=Q.consume(result,job_id='3054409',pull_receipt=pull,project=R,state=projection)
 assert consumed==result
 save('canonical_review_S_reconstruction.json',result)
 outcome=dict(status='passed_original_review_and_consume',reconstruction_sha256=h(D/'canonical_review_S_reconstruction.json'))
except BaseException as e:
 outcome=dict(status='original_review_still_blocked',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),scientific_acceptance=False)
 assert isinstance(e,ValueError) and str(e)=='consumed actual runtime/raw file absent from complete terminal pull'
 # Independently check the exact retained four files are present in the full pull,
 # but excluded by the unchanged original scheduler required-set projection.
 receipt=json.loads((R/pull).read_bytes());rows={r['relative']:r for r in receipt['files']};jid='3054409';run=F.OUT
 original_required={n for n,r in rows.items() if n.startswith(run+'/') and jid in r['job_ids']}|{'results/formal_main_v2/job_receipts/'+jid+'.json',*[f'results/slurm/cti_object_linked_t8s49d1_{jid}.{ext}' for ext in ('out','err')]}
 journals=['results/formal_main_v2/object_single_error_invocations/3054409/'+name for name in ['identity.json','completion.json','action_events.jsonl','iterator_events.jsonl']]
 assert len(rows)==13 and len(original_required)==9 and set(rows)-original_required==set(journals)
 facts=[]
 for n in journals:
  r=rows[n];a=(R/n).read_bytes();b=(P/n).read_bytes();assert a==b and hashlib.sha256(a).hexdigest()==r['sha256'] and len(a)==r['bytes'] and r['path']==str(P/n) and r['job_ids']==[jid]
  facts.append(dict(path=n,sha256=r['sha256'],bytes=r['bytes'],present_in_complete_pull=True,excluded_by_legacy_candidate_required_set=True))
 outcome.update(terminal_pull_real_file_count=13,legacy_candidate_verified_files=9,exact_missing_typed_journal_members=facts,bounded_fix_recommendation='Retain original pulled_candidate and all its full600/source/adapter/accounting guards. Add an explicit typed Object3054409 journal supplement consuming exactly these four already terminal-pulled rows against before/after inventory, job_ids, path, bytes, R/P SHA and identity/completion pin relationships. Do not accept arbitrary extra paths or a caller passed flag. Canonical source remains unchanged until root separately reviews a new precise metadata-only consumer bridge; no GPU rerun.')
assert state_before==h(R/'results/experiment_supervisor/state.json')
outcome.update(schema='formal_main_v2',kind='Object3054409_S_preload_original_full_review_attempt',reviewed_by='independent',job_id='3054409',reviewer_sha256=h(Path(Q.__file__)),source_origin_diagnosis_sha256=h(D/'source_origin_diagnosis.json'),pull_receipt=pull,pull_sha256=h(R/pull),analysis_projection_sha256=h(R/B/'terminal_analysis_supervisor_projection.json'),state_before=state_before,state_after=state_before,new_GPU_submissions=0,new_Slurm_queries=0,canonical_modified=False,utc=datetime.now(timezone.utc).isoformat())
save('canonical_review_S_attempt.json',outcome)
print(json.dumps(dict(status=outcome['status'],error=outcome.get('error'),origin_sha256=h(D/'source_origin_diagnosis.json'),attempt_sha256=h(D/'canonical_review_S_attempt.json'))))
