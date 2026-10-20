from pathlib import Path
import ast,copy,datetime,hashlib,json,os,sys,time,traceback,types
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');O=R/'.local/Long_legacy6_consumer_code_audit_1032'
D='.local/Long_legacy6_consumer_candidate_1032';SRC=D+'/legacy_proof_api_v3.py';PIN='7bf7fe93e9eb219273799aed7c2dfe35e23dad91e063db145ac80f1f7b60342d'
MAN=D+'/manifest.json';MPIN='5fbdf3c85d730867f204dd6d298e2d257fcc5a09b68aafab116c7c1447745e5a'
START=time.perf_counter();CPU=time.process_time();CHECKS=[];REFS={};READS=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('No process/network in CPU code audit')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or set(s.lower() for s in p.suffixes)&{'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'} or p.name.lower()=='init_states_test.json' or (p.name=='panel.json' and 'final' in p.parts):raise RuntimeError('Forbidden model/sealed value read')
  mode,flags=args[1:3];write=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if write and p.parent!=O:raise RuntimeError('Private audit outputs only')
  if not write:READS.append(str(p))
sys.dont_write_bytecode=True;sys.addaudithook(guard)
def read(rel,pin=None):
 p=R/rel;b=p.read_bytes();h=sha(b)
 if pin is not None:assert h==pin,(rel,h,pin)
 REFS[rel]={'path':rel,'sha256':h,'bytes':len(b)};return b

def write(name,obj):
 p=O/name
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}

def reject(name,fn,no_io=False):
 before=len(READS)
 try:fn()
 except (m.Rejected,TypeError,ValueError) as e:
  if no_io:assert len(READS)==before,name+' unexpectedly performed IO'
  CHECKS.append({'case':name,'rejected':True,'reason':str(e),'before_IO_verified':no_io})
 else:raise AssertionError(name+' accepted')
try:
 manifest=json.loads(read(MAN,MPIN));assert len(manifest['files'])==18
 for row in manifest['files']:
  b=read(row['path'],row['sha256']);assert len(b)==row['bytes']
 source=read(SRC,PIN);text=source.decode();tree=ast.parse(text)
 m=types.ModuleType('_independent_legacy600_code_v3');m.__file__=str(R/SRC);sys.modules[m.__name__]=m
 exec(compile(source,str(R/SRC),'exec',dont_inherit=True),m.__dict__)
 for rel,pin in m.SOURCE_SHA.items():read(rel,pin)
 contract=json.loads(read(D+'/API_contract.json','7b5b3eef24c508f2939b5ca408b37f308c6456abbbe2563328c3d80c48871f0a'))
 assert contract['source']=={'path':SRC,'sha256':PIN} and contract['real_positive_path_run'] is False
 def fixture_ref(tag):return {'path':'results/formal_main_v2/engineering/IN_MEMORY_CODE_AUDIT_ONLY/'+tag,'sha256':sha(tag.encode())}
 ar,rr,ir=fixture_ref('identity.json'),fixture_ref('root.json'),fixture_ref('independent.json')
 common={'schema':'formal_main_v2','status':'passed','synthetic':True,'map_ref':m.MAP,'legacy_root_ref':m.ROOT,'target_action_semantics_sha256':m.SEM,'same_controller_environment':True,'old_instance_hash_claimed':False,'old_full_RNG_dump_required':False,'final_release':False}
 identity={**common,'kind':'formal_legacy_controller_environment_identity_assessment','version':'long-legacy6-identity-v1','review_role':'independent','original_condition':'controller and environment were identical','decision':'sufficient_historical_source_chain','historical_provenance_ref':m.PRIOR,'supporting_evidence_refs':[m.IDENTITY_SUPPORT],'reviewer_source_ref':fixture_ref('identity_reviewer.py')}
 def adoption(role):return {**common,'kind':'formal_legacy_development_equivalence_adoption','version':'long-legacy6-adoption-v1','review_role':role,'identity_assessment_ref':ar,'independent_adoption_ref':ir if role=='root' else None,'reviewer_source_ref':fixture_ref(role+'_reviewer.py')}
 root,ind=adoption('root'),adoption('independent');kw={'assessment_ref':ar,'root_ref':rr,'independent_ref':ir}
 x=m.validate_synthetic_adoption_fixture(assessment=identity,root=root,independent=ind,**kw)
 assert x['synthetic'] is True and x['real_proof_returned'] is False and x['production_reuse_authorized'] is False
 CHECKS.append({'case':'valid_in_memory_synthetic_is_structure_only','passed':True,'real_proof_returned':False})
 reject('synthetic_documents_block_real_gate',lambda:m._documents(identity,root,ind,synthetic=False,**kw),True)
 mutations=[
 ('root_null',1,None),('independent_null',2,None),('assessment_null',0,None),
 ('draft_root',1,{'status':'draft'}),('negative_independent',2,{'status':'failed'}),('pending_identity',0,{'status':'pending'}),
 ('wrong_root_role',1,{'review_role':'independent'}),('wrong_independent_role',2,{'review_role':'root'}),
 ('negative_same_environment',0,{'same_controller_environment':False}),('truthy_string_environment',2,{'same_controller_environment':'true'}),
 ('missing_exact_inode_evidence',0,{'supporting_evidence_refs':[]}),('duplicate_inode_evidence',0,{'supporting_evidence_refs':[m.IDENTITY_SUPPORT,m.IDENTITY_SUPPORT]}),
 ('wrong_historical_chain',0,{'historical_provenance_ref':fixture_ref('wrong_history.json')}),
 ('changed_map',1,{'map_ref':fixture_ref('other_map.json')}),('changed_legacy_root',2,{'legacy_root_ref':fixture_ref('other_legacy_root.json')}),
 ('changed_target_semantics',0,{'target_action_semantics_sha256':'0'*64}),
 ('different_assessment_ref',2,{'identity_assessment_ref':fixture_ref('other_identity.json')}),
 ('root_unbound_independent',1,{'independent_adoption_ref':None}),('independent_self_bind',2,{'independent_adoption_ref':ir}),
 ('same_review_source_refs',1,{'reviewer_source_ref':ind['reviewer_source_ref']}),
 ('invented_instance_hash',0,{'old_instance_hash_claimed':True}),('invented_RNG_requirement',1,{'old_full_RNG_dump_required':True}),
 ('final_claim',2,{'final_release':True}),('private_reviewer_source',0,{'reviewer_source_ref':{'path':'.local/fake.py','sha256':'0'*64}}),
 ('wrong_identity_decision',0,{'decision':'insufficient'}),('wrong_identity_condition',0,{'original_condition':'unknown'}),
 ('unexpected_field',1,{'extra':'not_allowed'}),('nonsynthetic_in_synthetic_gate',2,{'synthetic':False})]
 for name,idx,patch in mutations:
  docs=copy.deepcopy([identity,root,ind]);docs[idx]=None if patch is None else {**docs[idx],**patch}
  reject(name,lambda docs=docs:m._documents(*docs,synthetic=True,**kw),True)
 reject('missing_typed_field',lambda:m._documents(identity,{k:v for k,v in root.items() if k!='status'},ind,synthetic=True,**kw),True)
 reject('aliased_document_paths',lambda:m._documents(identity,root,ind,synthetic=True,assessment_ref=ar,root_ref=rr,independent_ref=rr),True)
 public={'legacy_root_ref':m.ROOT,'equivalence_map_ref':m.MAP,'root_adoption_ref':None,'independent_adoption_ref':None,'identity_assessment_ref':None,'suite':'libero_10','stage':'development','target_action_semantics_sha256':m.SEM}
 reject('public_missing_adoptions',lambda:m.consume_legacy_development_proof(**public),True)
 for name,change in [('public_final',{'stage':'final'}),('public_other_suite',{'suite':'libero_goal'}),('public_wrong_semantics',{'target_action_semantics_sha256':'0'*64}),('public_changed_map',{'equivalence_map_ref':fixture_ref('changed.json')}),('public_private_receipt',{'root_adoption_ref':{'path':'.local/private_receipt.json','sha256':'0'*64}})]:
  reject(name,lambda change=change:m.consume_legacy_development_proof(**{**public,**change}),True)
 reject('public_no_synthetic_override',lambda:m.consume_legacy_development_proof(**public,synthetic=True),True)
 reject('public_no_forged_evidence_provider',lambda:m.consume_legacy_development_proof(**public,evidence=object()),True)
 for name,path in [('path_traversal','results/formal_main_v2/../escape'),('absolute','/tmp/receipt.json'),('windows_absolute','F:/receipt.json'),('backslash','results\\bad.json')]:
  reject(name,lambda path=path:m.valid_ref({'path':path,'sha256':'0'*64},receipt=True),True)
 reject('duplicate_JSON_keys',lambda:m.decode(b'{"a":1,"a":2}'),True)
 reject('nonfinite_JSON_constant',lambda:m.decode(b'{"a":NaN}'),True)
 reject('f64_wrong_width',lambda:m._f64([[0]*6]),True)
 reject('f64_boolean_action',lambda:m._f64([[False]*7]),True)
 reject('f64_nan_action',lambda:m._f64([[float('nan')]*7]),True)
 # Static original consumer chain and complete raw proof invariants, without redoing another agent's evidence audit.
 needed=[
 "old=consumer.review_downstream_output(ev,legacy_root_ref,expected_stage='development',suite='libero_10')",
 "old.get('execution_version',OLD)==OLD and old['scientific_complete'] is True and old['completed_trials']==600",
 "schema.validate_candidate(mapping,records)","list(identities)==METHODS",
 "reviewer.semantic_identity(target)==SEM","seen==set(bytrial)",
 "totals==Counter(trials=600,chunks=23179,actions=183676)",
 "len(states)==100 and all(s['methods']==set(METHODS) for s in states.values())",
 "clip==0 and len(r['chunks'])==r['policy_calls']==math.ceil(r['control_steps']/8)",
 "actual==_f64(queue[:r['control_steps']])",
 "digest(actual)==a['old_CPU_replay_executed_sha256']==a['new_CPU_replay_executed_sha256']",
 "old['cost']['all_attempt_gpu_seconds']==10531 and [a['job_id'] for a in old['cost']['allocations']]==JOBS",
 "require(eh.hexdigest()==checksum,'external evidence changed while auditing')",
 "ev.unchanged()","_documents(assessment,root,ind,assessment_ref=identity_assessment_ref,root_ref=root_adoption_ref,independent_ref=independent_adoption_ref,synthetic=False)",
 "'compatibility_class':'legacy_equivalent_not_new_wrapper_execution'","'actual_new_wrapper_trials_added':0",
 "'original_invocations_ran_new_wrapper':False","'production_activation_inferred':False"]
 for q in needed:assert q in text,q
 functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
 api=functions['consume_legacy_development_proof'];assert not api.args.args and api.args.kwarg is None
 assert [a.arg for a in api.args.kwonlyargs]==contract['required_keyword_arguments']
 consumer=read(m.CONSUMER,m.SOURCE_SHA[m.CONSUMER]).decode();helper=read(m.HELPER,m.SOURCE_SHA[m.HELPER]).decode()
 assert 'return original.review_downstream_output(evidence, reference' in consumer
 for q in ['scheduler.require_root_review(evidence, reference["path"], jobs, expected_stage=expected_stage)','rebuilt = reviewer.review(saved["job_id"], saved["pull_receipt"]','if path == MUTABLE_STATE:','evidence.unchanged()']:assert q in helper,q
 # Exactly five private dependencies have existing byte-exact tracked archive mappings.
 mapping=json.loads(read(m.MAP['path'],m.MAP['sha256']))
 e=json.loads(read(mapping['evidence']['path'],mapping['evidence']['sha256']))
 needed_local={m.MAP['path'],mapping['trial_records']['path'],mapping['evidence']['path'],*[x for x in m.SOURCE_SHA if x.startswith('.local/')],*[x for x in e if x.startswith('.local/')]}
 delivery_rel='results/formal_main_v2/preflight/heartbeat_20261020T1727/Long_legacy6_typed_bridge_delivery.json'
 delivery=json.loads(read(delivery_rel,'43356935006e9f17d43e967955e14407d8602cc2e5e3d4c251dc8db2acf15c3d'))
 bysrc={x['source']['path']:x for x in delivery['copies']};assert needed_local<=set(bysrc) and len(needed_local)==5
 restore=[]
 for rel in sorted(needed_local):
  item=bysrc[rel];a=read(rel,item['source']['sha256']);b=read(item['archive']['path'],item['archive']['sha256'])
  assert a==b and len(a)==item['source']['bytes']
  restore.append({'source_private_path':rel,'archive':REFS[item['archive']['path']],'required_sha256':sha(a),'bytes':len(a),'byte_identical_now':True})
 repro=write('reproduction_map.json',{'status':'five_private_dependencies_have_exact_archive_mapping','files':restore,
 'restore_required_in_fresh_checkout':True,'restoration_performed':False,
 'rule':'Restore original bytes to these exact private paths after verifying archived SHA/bytes; do not rewrite hard-coded source refs or weaken gates.',
 'absolute_runtime_source_dependencies':sum(Path(k).is_absolute() for k in e),
 'runtime_source_dependency_identity_reviewed_here':False,
 'Git_checkout_alone_sufficient':False,
 'limitation':'Existing retained H/P runtime snapshot and package/source evidence remains required. Independent scientific identity assessment covers that chain.'})
 tests=write('tests.json',{'status':'passed','tests':CHECKS,'count':len(CHECKS),'all_fixtures_in_memory_only':True,'real_receipts_created':0,'real_positive_API_called':False,'whole_chain_reconstruction_rerun_here':False,'new_GPU_seconds':0})
 report={'schema':'formal_main_v2','kind':'independent_legacy600_proof_API_code_audit','status':'passed','reviewer':'/root/long128s41_terminal_0530',
 'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script':{'path':SRC,'sha256':PIN},'candidate_manifest':REFS[MAN],
 'API_contract':REFS[D+'/API_contract.json'],'tests':tests,'reproduction':repro,'blockers':[],
 'original_chain_static_trace':['explicit consume_legacy_development_proof real three-receipt gate','_raw_rebuild exact pinned action consumer.review_downstream_output','unchanged legacy helper.review_downstream_output','original scheduler.require_root_review and original reviewer.review over immutable terminal snapshot','full saved-vs-rebuilt root equality excluding review timestamp','full600 typed-map/raw-action/hash/cost closure'],
 'checked_invariants':{'six_methods':m.METHODS,'same_unique_initial_states':100,'legacy_trials':600,'all_emitted_chunks':23179,'executed_actions':183676,'historical_GPU_seconds':10531,'original_job_ids':m.JOBS,'old_execution_version':m.OLD,'original_invocations_ran_new_wrapper':False,'new_wrapper_trials_added_by_proof':0,'new_independent_states':0,'new_GPU_seconds':0,'no_outcome_filtering':True,'legacy_receipts_not_rewritten':True,'final_release_authorized':False},
 'trust_boundary':'Root-adopted exact fixed evidence consumption. A reviewer_source SHA proves byte identity, not independent judgment. Genuine independent assessment/adoption and root adoption must be separately issued and pinned before real API use; author tests/code review do not supply them.',
 'real_identity_assessment_performed_by_this_agent':False,'actual600_or1350_evidence_audit_repeated_here':False,
 'real_positive_public_API_executed_here':False,'author_CPU_review_not_substituted_for_independent_science':True,
 'suitable_for_minimal_nonfrozen_CPU_proof_application_after_real_receipts':True,
 'production_hook_integrated':False,'Long22_assembler_implemented':False,'full_O2A_or_global_final_release_inferred':False,
 'legacy600_remains_separate_from_existing_actual_new_wrapper1600':True,
 'limitations':['This code audit does not itself admit legacy600 or increase scientific trial counts.','A real positive call with the actual independent identity/adoption and root adoption remains required.','All88 identities/four-suite/global freeze and timing gates remain unchanged; this candidate does not implement their integration.','Exact archive restoration preserves private dependency paths, while retained absolute runtime source evidence is still needed.'],
 'source_refs':list(REFS.values()),'reviewer_Git_state_Slurm_or_production_modified':False,
 'CPU_wall_seconds':time.perf_counter()-START,'CPU_process_seconds':time.process_time()-CPU}
 rr=write('code_audit_review.json',report)
 files=[]
 for p in sorted(O.iterdir()):
  if p.is_file():files.append({'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size})
 mr=write('manifest.json',{'schema':'formal_main_v2','kind':'independent_code_audit_files','status':'passed','reviewed_script':report['script'],'files':files,'transport_closure_separate':True})
 print(json.dumps({'status':'passed','review':rr,'manifest':mr,'tests':len(CHECKS),'private_dependencies':len(needed_local),'real_positive_API_called':False,'new_GPU_seconds':0}))
except BaseException as exc:
 write('failure_v1.json',{'status':'failed','error':str(exc),'traceback':traceback.format_exc(),'completed_tests':CHECKS,'production_mutated':False,'new_GPU_seconds':0})
 raise
