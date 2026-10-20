from pathlib import Path
import copy,hashlib,importlib.util,json,sys,time
from unittest.mock import patch
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/integration_candidate_20261020T1530';P=D/'integrate_1530_v2.py'
assert hashlib.sha256(P.read_bytes()).hexdigest()=='c05d049e4d56d82708a64e05802ca9281f91f191d3e510ccbbc54550a8d25219'
sp=importlib.util.spec_from_file_location('integration1530test',P);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
checks=[];started=time.perf_counter()
def ok(label,test):
 assert test,label;checks.append(label)
def reject(label,fn):
 try:fn()
 except (ValueError,AssertionError,KeyError):checks.append(label);return
 raise AssertionError('failed to reject '+label)
base='.local/integration_candidate_20261020T1530/preview_95f917f55464'
s=m.rd(base+'/state_before.json');before=m.sha(m.path(base+'/state_before.json'));pre=m.rd(base+'/'+m.SUMMARY)
d=m.inputs();m.precondition(s);checks.append('all exact canonical root and independent pins plus173 source hashes reverified')
obs=pre['scheduler'];cap=pre['capacity'];after,summary,outputs=m.prepare(s,before,d,obs,cap,'CPU_SELFTEST_NOT_APPLIED');f=after['formal_main_progress']
ok('exact66 root and independent arms plus331000 reviewed updates',f['root_and_independent_completed_arms']==66 and f['root_and_independent_reviewed_arm_updates']==331000)
ok('exact600 accepted current4400 raw5612 compatible5000',f['current_action_development_trial_count']==4400 and f['completed_development_trials']==5612 and summary['compatible_current_and_explicit_legacy_trials']==5000)
ok('400 unique initial states,100 per suite retained',f['current_action_development_unique_initial_states']==400 and set(f['current_action_development_unique_initial_states_by_suite'].values())=={100})
ok('machine68 and330000 preserved',f['trained_arms']==s['formal_main_progress']['trained_arms']==68 and f['machine_and_prior_verified_arm_updates']==330000)
ok('target original machine evidence preserved',all(f['completed_training_pairs'][m.PAIR][k]==v for k,v in s['formal_main_progress']['completed_training_pairs'][m.PAIR].items()))
ok('other33 completed machine/prior pairs untouched',all(f['completed_training_pairs'][k]==v for k,v in s['formal_main_progress']['completed_training_pairs'].items() if k!=m.PAIR))
ok('automatic machine proofs unchanged',f['automatic_machine_verified_pairs']==s['formal_main_progress']['automatic_machine_verified_pairs'])
ok('pending reservation owner registry unchanged',all(after[k]==s[k] for k in ['autonomous_training_v1','registered_jobs','pending_submission']))
ok('heldGoal200 not counted or edited','3049679' not in f['new_action_development_verified_by_job'] and f['nonLong_development_submissions_1317']==s['formal_main_progress']['nonLong_development_submissions_1317'])
ok('Object bridge no scientific admission and original blockers untouched',not summary['Object256seed23_bridge_scientifically_admitted'] and f['downstream_blockers_20261020T1418']==s['formal_main_progress']['downstream_blockers_20261020T1418'])
ok('old accepted development records exact',all(f['new_action_development_verified_by_job'][k]==v for k,v in s['formal_main_progress']['new_action_development_verified_by_job'].items()))
ok('acceptance cost added zero times',after['current_round_cost']['allocated_gpu_seconds']==pre['allocated_GPU_seconds'] and summary['acceptance_allocation_seconds_not_added_again']==60721+6678)
ok('original negative results and partial seed panel retained',d['statistics']['suites']['libero_spatial']['per_seed'][1]['B_minus_A_pp']==-2 and d['statistics']['suites']['libero_object']['missing_seeds']==[23] and not d['statistics']['suites']['libero_object']['bootstrap_computed'])
ok('sealed final untouched',f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'])
ok('no new job submission by integration',summary['new_GPU_jobs_by_integration']==0 and summary['new_dispatches_created']==0 and summary['new_dispatch_trials_accepted']==0)
for name,edit in [
 ('already accepted counts',lambda x:x['formal_main_progress'].update(current_action_development_trial_count=4400)),
 ('already applied marker',lambda x:x['formal_main_progress'].update(integration_20261020T1530_accepted={})),
 ('training review counter changed',lambda x:x['formal_main_progress'].update(root_and_independent_completed_arms=66)),
 ('test opened',lambda x:x['formal_main_progress'].update(test_opened=True)),
 ('final released',lambda x:x['formal_main_progress'].update(global_release_created=True)),
 ('duplicate target independent acceptance',lambda x:x['formal_main_progress']['completed_training_pairs'][m.PAIR].update(independent_review='fake')),
 ('heldGoal accepted',lambda x:x['formal_main_progress']['new_action_development_verified_by_job'].update({'3049679':{}})),
 ('duplicate developer acceptance',lambda x:x['formal_main_progress']['new_action_development_verified_by_job'].update({'3050192':{}})),
 ('missing pending terminal',lambda x:x['formal_main_progress'].update(nonLong_development_submissions_1418=[])),
 ('controller identity changed',lambda x:x['autonomous_training_v1'].update(controller_job_id='different'))]:
 x=copy.deepcopy(s);edit(x);reject('reject '+name,lambda:m.precondition(x))
for name,edit in [
 ('terminal still running',lambda x:x['rows']['3050192'].update(status='RUNNING')),
 ('terminal nonzero exit',lambda x:x['rows']['3050205'].update(exit_code='1:0')),
 ('training terminal wrong seconds',lambda x:x['rows']['3043762'].update(elapsed_seconds=60720)),
 ('missing registered accounting',lambda x:x['rows'].pop('3050224')),
 ('controller down',lambda x:x['rows']['3034538'].update(status='FAILED'))]:
 x=copy.deepcopy(obs);edit(x);reject('reject '+name,lambda:m.prepare(s,before,d,x,cap,'test'))
x=copy.deepcopy(cap);x['occupied']=list(range(9));reject('reject ninth GPU',lambda:m.prepare(s,before,d,obs,x,'test'))
x=copy.deepcopy(cap);x['unknown']=['unknown'];reject('reject uncertain allocation',lambda:m.prepare(s,before,d,obs,x,'test'))
x=copy.deepcopy(s);x['registered_jobs'].append(copy.deepcopy(x['registered_jobs'][0]));reject('reject duplicate allocation costs',lambda:m.prepare(x,before,d,obs,cap,'test'))
x=copy.deepcopy(s);x['current_round_cost']['allocated_gpu_seconds']=pre['allocated_GPU_seconds']+1;reject('reject regressed cost',lambda:m.prepare(x,before,d,obs,cap,'test'))
x=copy.deepcopy(d);x['training_independent']['arms']['A']['sample_uses']=39999;reject('reject wrong training cursor/use count',lambda:m.verify_training(x))
x=copy.deepcopy(d);x['selected_server']['checks'][0]['sha256']='0'*64;reject('reject selected checkpoint substitution',lambda:m.verify_training(x))
x=copy.deepcopy(d);x['training_independent']['arms']['B']['validation'].pop();reject('reject missing validation node',lambda:m.verify_training(x))
x=copy.deepcopy(d);x['training_independent']['machine_status_not_claimed_as_independence']=False;reject('reject machine status offered as independent review',lambda:m.verify_training(x))
# Future submissions are deliberately independent from this completed-evidence transaction.
x=copy.deepcopy(s);x['pending_submission']={'status':'pending_exact_ACK_reconciliation','job_id':'CPU_SYNTHETIC'};x['autonomous_training_v1']['reserved_GPU_slots']=1;x['autonomous_training_v1']['root_submission_hold']={'reason':'CPU fixture only'};x['formal_main_progress']['future_development_dispatch_CPU_fixture']={'accepted':0};x['formal_main_progress']['trained_arms']=72
future,_,_=m.prepare(x,before,d,obs,cap,'CPU_SYNTHETIC')
ok('pending held ACK, reservation, submission hold all preserved',all(future[k]==x[k] for k in ['pending_submission','autonomous_training_v1','registered_jobs']))
ok('later machine count and future dispatch preserved',future['formal_main_progress']['trained_arms']==72 and future['formal_main_progress']['future_development_dispatch_CPU_fixture']=={'accepted':0})
for name,edit in [
 ('controller',lambda x:x['autonomous_training_v1'].update(reserved_GPU_slots=99)),
 ('registry',lambda x:x['registered_jobs'].pop()),
 ('machine count',lambda x:x['formal_main_progress'].update(trained_arms=0)),
 ('old hold',lambda x:x['formal_main_progress']['nonLong_development_submissions_1317'].clear()),
 ('machine receipt',lambda x:x['formal_main_progress']['completed_training_pairs'][m.PAIR].update(machine_verification={})),
 ('other pair',lambda x:x['formal_main_progress']['completed_training_pairs']['libero_10_k128_seed17'].update(seed=99))]:
 x=copy.deepcopy(after);edit(x);reject('preservation guard rejects '+name,lambda:m.preserve_unrelated(s,x))
reject('reject wrong evidence raw SHA',lambda:m.rd(*[m.PINS['training_root'][0],'0'*64]))
reject('reject parent traversal',lambda:m.path('../state.json'));reject('reject absolute path',lambda:m.path('/etc/passwd'))
doc_before={p:m.sha(m.path(p)) for p in ['docs/'+n+'.md' for n in m.DOCS]};docs,pins=m.documents(d,summary,'CPU_SELFTEST_ONLY')
for p in pins:ok('preserve full historical body '+p,docs[p].endswith(m.path(p).read_bytes().partition(b'\n')[2]))
ok('six existing docs plus one new complete Spatial table',len(docs)==7)
ok('correct 100-cluster uncertainty and no O2A claim','100个唯一初态不能当作300个' in docs['docs/正式Spatial轻度剪枝开发结果.md'].decode() and '−0.667,+1.333' in docs['docs/正式Spatial轻度剪枝开发结果.md'].decode())
ok('Goal engineering described as registered pending review, not unrun','Goal工程诊断已登记、待终审' in docs['docs/实验进度.md'].decode())
m.assert_transaction_available(outputs,docs,pins);checks.append('canonical intention and completion absent before any apply')
real_path=m.path
with patch.object(m,'path',side_effect=lambda rel,*a,**kw: P if rel==m.INTENT else real_path(rel,*a,**kw)):
 reject('prior intent blocks non-reentrant apply',lambda:m.assert_transaction_available(outputs,docs,pins))
ok('no canonical docs written',all(m.sha(m.path(p))==v for p,v in doc_before.items()))
report=dict(schema='formal_main_v2',kind='completed_evidence_integration_CPU_selfcheck',status='passed',checks=checks,count=len(checks),source=m.ref(str(P.relative_to(R))),private_synthetic_fixtures=True,canonical_mutations=False,new_GPU_jobs=0,Slurm_mutations=False,Git_mutations=False,exact_preview_state_sha256=before,controller_may_advance_independently=True,elapsed_CPU_wall_seconds=time.perf_counter()-started)
p=D/'cpu_selfcheck_v1.json'
with p.open('xb') as f:f.write(m.rawjson(report))
print(json.dumps({'status':'passed','checks':len(checks),'report':m.ref(str(p.relative_to(R)))},ensure_ascii=False))
