from pathlib import Path
import ast,copy,hashlib,json,os,sys,traceback,types
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/object_single_error_production_20261020T2358';O=R/'.local/object_single_error_production_independent_20261020T2358'
os.environ['CUDA_VISIBLE_DEVICES']='';sys.dont_write_bytecode=True
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];rejections=[];boundaries=[]
def save(n,v):
 with (O/n).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def ok(value,name):
 if not value:raise AssertionError(name)
 checks.append({'check':name,'passed':True})
def reject(fn,name):
 try:fn()
 except (ValueError,RuntimeError,TypeError,KeyError,AssertionError,AttributeError) as e:
  rejections.append({'check':name,'type':type(e).__name__,'reason':str(e)});return
 raise AssertionError('accepted forbidden case: '+name)
def encode(v):return b''.join((json.dumps(x,sort_keys=True,allow_nan=True)+'\n').encode() for x in v)
def main():
 manifest=json.loads((D/'delivery_manifest.json').read_bytes())
 ok(H(D/'delivery_manifest.json')=='c7e40a9cb8474862da58fe0b4cc822d2b32f3cfcbbbfcd2d920e634eddf12485','author manifest pin')
 ok(manifest['file_count']==len(manifest['files'])==30,'30 immutable author files')
 for row in manifest['files']:
  p=R/row['path'];ok(p.is_relative_to(D) and not p.is_symlink() and H(p)==row['sha256'] and p.stat().st_size==row['bytes'],'author bytes '+row['path'])
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_bytes())
 ok(len(inventory['files'])==173,'source inventory173')
 for path,pin in inventory['files'].items():
  for root in (R,S):ok(H(root/path)==pin,'frozen source '+str(root/path))
 state_before=H(R/'results/experiment_supervisor/state.json')
 sys.path[:0]=[str(D),str(S/'src')]
 import fixed as F,constants as C,adoption as A,execution as E,wrapper as W,gateway_contract as G,reviewer as V,iterator as I
 from cti_vla.evaluation import formal_trials as M
 inputs=F.load_inputs(M)
 adoption=A.rebuild(inputs);A.require_independent(R,C.ref(R,C.ADOPTION_INDEPENDENT),adoption)
 ok(adoption['legacy_equivalent_trials']==599 and adoption['original_GPU_seconds']==6713 and adoption['current_generated_trials']==0,'599 actual references and all original6713 seconds')
 # Independently parse the preserved failed row under an explicitly CPU-only envelope.
 rows=[dict(event='invocation',created_utc='INDEPENDENT_CPU_ONLY_NOT_NEW_JOB',slurm_job_id='9900991',run_signature=F.sig(inputs['config'])),json.loads(inputs['raw'][F.START['byte_offset']:F.START['byte_offset']+F.START['bytes']]),copy.deepcopy(inputs['results'][F.CELL])]
 def parse(rr,panel=None,manifest=None):return V.parse_raw(encode(rr),config=inputs['config'],panel=panel or inputs['panel'],manifest=manifest or inputs['manifest'],job_id='9900991',inputs=inputs)
 proof=parse(rows);ok(proof['result']['success'] is False and proof['result']['status']=='policy_error' and proof['result']['control_steps']==56 and len(proof['result']['chunks'])==7,'original failed row remains failed without fabricated query8')
 for field,val in [('task_id',99),('source_state_index',50),('runtime_seed',41),('method','B128_seed17'),('trial_id','forged')]:
  bad=copy.deepcopy(rows);bad[1][field]=val;reject(lambda bad=bad:parse(bad),'start identity '+field)
 for i in range(3):
  bad=copy.deepcopy(rows);bad[i]['run_signature']='0'*64;reject(lambda bad=bad:parse(bad),'mixed run signature '+str(i))
 bad=copy.deepcopy(rows);bad[0]['invented_prior_completions']=599;reject(lambda:parse(bad),'extra invocation key')
 bad=copy.deepcopy(rows);bad[-1]['success']=True;reject(lambda:parse(bad),'failed result cannot become success')
 bad=copy.deepcopy(rows);bad[-1]['chunks'][0]['control_step']=8;reject(lambda:parse(bad),'changed query cadence')
 bad=copy.deepcopy(rows);bad[-1]['executed_actions'][0][0]=float('nan');reject(lambda:parse(bad),'nonfinite actual command')
 bad=copy.deepcopy(rows);bad[-1]['control_steps']=57;reject(lambda:parse(bad),'control step action mismatch')
 bad=copy.deepcopy(rows);bad[1]['event']='result';reject(lambda:parse(bad),'result cannot replace start')
 bad=copy.deepcopy(inputs['panel']);bad['states'][0],bad['states'][1]=bad['states'][1],bad['states'][0];reject(lambda:parse(rows,panel=bad),'changed full panel order')
 bad=copy.deepcopy(inputs['manifest']);bad['methods']=bad['methods'][:-1];reject(lambda:parse(rows,manifest=bad),'dropped full manifest method')
 original,derived,ip=I.derive_loop(M,F.read(S,F.LOOP,F.LOOP_SHA))
 ok(ip['inserted_node_count']==1 and ip['allowlist']==[F.CELL] and ip['fake_legacy_completions_written'] is False,'one AST allowlist insertion without legacy ledger')
 for key in ('_identity','validate_trial_identities','expected_method_ids'):
  fn=getattr(M,key)
  try:
   setattr(M,key,lambda *args,**kwargs:None);reject(lambda:I.derive_loop(M,F.read(S,F.LOOP,F.LOOP_SHA)),'live original loop helper '+key)
  finally:setattr(M,key,fn)
 defaults=original.__kwdefaults__
 try:
  original.__kwdefaults__={**defaults,'policy_watchdog_seconds':61.};reject(lambda:I.derive_loop(M,F.read(S,F.LOOP,F.LOOP_SHA)),'live default watchdog changed')
 finally:original.__kwdefaults__=defaults
 # The code-claim expected map is recomputed from exact immutable source, not read from a passed flag.
 execute=E.compiled_function(F.read(S,'scripts/eval_formal_selector_libero.py',inventory['files']['scripts/eval_formal_selector_libero.py']),S/'scripts/eval_formal_selector_libero.py','execute')
 adapter=E.compiled_function(F.read(P,C.LEGACY,C.LEGACY_SHA),P/C.LEGACY,'run')
 install=E.compiled_function((D/'execution.py').read_bytes(),P/C.BASE/'execution.py','install')
 source='src/cti_vla/evaluation/formal_runtime.py';token='src/cti_vla/models/openvla_oft_policy.py'
 expected={'original_execute_code_sha256':I.codesig(execute),'original_adapter_run_code_sha256':I.codesig(adapter),'guard_code_sha256':I.codesig(I.nested(I.nested(install,'bindings'),'guarded')),'original_execute_callbacks':{n:I.codesig(I.nested(execute,n)) for n in ('factory','reseed','on_result')},'policy_methods_code_sha256':{n:I.codesig(v) for n,v in E.class_codes(F.read(S,source,inventory['files'][source]),S/source,'FormalRolloutPolicy').items() if n!='<lambda>'},'source_sha256':inventory['files'][source],'token_policy_methods_code_sha256':{n:I.codesig(v) for n,v in E.class_codes(F.read(S,token,inventory['files'][token]),S/token,'OpenVLAOFTTokenPolicy').items() if n!='<lambda>'},'token_policy_source_sha256':inventory['files'][token]}
 first={k:expected[k] for k in ('original_execute_code_sha256','original_adapter_run_code_sha256','guard_code_sha256')}
 second={'original_execute_callbacks':expected['original_execute_callbacks'],'policy_closure':{**{k:expected[k] for k in ('policy_methods_code_sha256','source_sha256','token_policy_methods_code_sha256','token_policy_source_sha256')},'opaque_callbacks_allowed':False}}
 journal=[first,second];V.validate_code_claims(journal,expected);ok(True,'all expected original and projected code bytes independently compiled; not actual P execution')
 for key in first:
  bad=copy.deepcopy(journal);bad[0].pop(key);reject(lambda bad=bad:V.validate_code_claims(bad,expected),'missing code field '+key)
 for key in expected['token_policy_methods_code_sha256']:
  bad=copy.deepcopy(journal);bad[1]['policy_closure']['token_policy_methods_code_sha256'][key]='f'*64;reject(lambda bad=bad:V.validate_code_claims(bad,expected),'changed token policy method '+key)
 for k in ('synthetic','synthetic_fixture'):
  reject(lambda k=k:V.reject_synthetic({'synthetic_input':False},[],[{k:True}]),'typed iterator explicit '+k)
 reject(lambda:V.reject_synthetic({},[{}],[{}]),'missing synthetic_input disposition')
 # Duplicate classifiers must remain strict even for incomplete terminal records.
 cases=[{'mode':G.MODE},{'logical_trial_id':F.CELL},{'stage_key':C.STAGE_KEY},{'linked_failure_sha256':F.RESULT['sha256']},{'run_root':str(P/F.OUT)},{'job_name':G.NAME},{'slurm_comment':'cti-object-single-error:old-ack'}]
 for idx,row in enumerate(cases):ok(G.duplicate(row),'partial prior attempt classification '+str(idx))
 reject(lambda:G.submit(),'no native submission implementation')
 reject(lambda:G.bound_registration({'submission_token':'not-a-real-token'},{'registered_jobs':[{'job_id':'9900991','invocation_sha256':'0'*64}]},job_id='9900991',invocation_sha256='1'*64),'bound registration rejects changed actual invocation bytes before plan read')
 # Canonical absence is a boundary, never an invitation to install from this audit.
 locations=[P/C.BASE,P/C.PLAN,P/C.INVOCATION,P/F.OUT]
 absent={str(p):not p.exists() for p in locations}
 ok(all(absent.values()),'new canonical P runtime/plan/invocation/output absent; actual P unverified')
 entry_tree=ast.parse((D/'entry.py').read_bytes());stmt=entry_tree.body
 boot=[i for i,n in enumerate(stmt) if isinstance(n,ast.If) and any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='bootstrap' for x in ast.walk(n))]
 first_import=next(i for i,n in enumerate(stmt) if isinstance(n,ast.Import) and any(a.name=='fixed' for a in n.names))
 ok(len(boot)==1 and boot[0]<first_import,'stdlib bootstrap validates P and complete source before project imports')
 # Record, do not mistake, the pure projection limitation for an actual live gate.
 boundaries.extend(['Atomic gateway is intentionally absent; submit always raises HOLD.','Registered projections and lease are not actual capacity evidence until future native gateway reconstructs state and live Slurm under writer lock/CAS.','No canonical P package, actual new plan or actual-P verification.','No new GPU raw evidence; full linked terminal path has not executed. Old original600 actual consumer validation is history only.'])
 ok(H(R/'results/experiment_supervisor/state.json')==state_before,'supervisor state unchanged')
 for row in manifest['files']:ok(H(R/row['path'])==row['sha256'],'immutable after independent checks '+row['path'])
 for path,pin in inventory['files'].items():
  for root in (R,S):ok(H(root/path)==pin,'frozen after '+str(root/path))
 save('supplementary_independent_CPU_checks.json',{'schema':'formal_main_v2','status':'passed_CPU_checks_only','checks':checks,'check_count':len(checks),'negative':rejections,'negative_count':len(rejections),'known_production_blockers':boundaries,'scope':'No model/simulator inference; only explicit CPU envelopes and source reconstruction. No entry.main or entry.run.','new_GPU_seconds':0,'new_scientific_trials':0,'actual_P_verified':False,'state_sha256_unchanged':state_before,'actual_P_absence':absent,'original_failed_trial_preserved':True,'source173_R_S_verified':True})
 print(json.dumps({'status':'passed_CPU_checks_only','checks':len(checks),'negative':len(rejections)}))
try:main()
except BaseException as error:
 save('supplementary_failure_01.json',{'error_type':type(error).__name__,'error':str(error),'traceback':traceback.format_exc(),'completed_checks':checks,'completed_rejections':rejections,'new_GPU_seconds':0});raise
