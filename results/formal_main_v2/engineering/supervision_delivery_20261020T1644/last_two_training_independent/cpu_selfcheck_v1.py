from pathlib import Path
import copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/last_two_training_independent_20261020T1644'
assert len(sys.argv)==5,'suite sourceSHA reviewSHA outputname'
suite,source_sha,review_sha,outname=sys.argv[1:]
assert suite in ('goal','object') and '/' not in outname and outname.endswith('.json')
job='3043813' if suite=='goal' else '3044844'
p=D/suite/f'audit_{job}_v2.py';assert hashlib.sha256(p.read_bytes()).hexdigest()==source_sha
sp=importlib.util.spec_from_file_location('last_two_cpu_'+suite,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
rr=D/suite/('3043813_independent_review.json' if suite=='goal' else 'independent_review.json');assert hashlib.sha256(rr.read_bytes()).hexdigest()==review_sha
review=json.loads(rr.read_text());row=review['arms']['A']['validation'][0]
vp=R/row['path'];assert hashlib.sha256(vp.read_bytes()).hexdigest()==row['sha256'];v=json.loads(vp.read_bytes())
original=v['observations'][0];ref={k:original[k] for k in ('episode_id','task_id')};passed=[]
def case(name,fn,reject=False):
 try:fn()
 except (ValueError,AssertionError) as ex:
  assert reject,(name,str(ex));passed.append({'name':name,'expected':'reject','observed':'rejected','reason':str(ex)})
 else:
  assert not reject,name;passed.append({'name':name,'expected':'accept','observed':'accepted'})
def mutate(key,value):
 x=copy.deepcopy(original);x[key]=value;return lambda:m.validate_hard64_observation(x,ref)
case('actual hard64 validation observation accepted',lambda:m.validate_hard64_observation(original,ref))
ids=original['retained_indices']
for name,value in [('missing',ids[:-1]),('duplicate',ids[:-1]+[ids[-2]]),('reordered',list(reversed(ids))),('outofrange',ids[:-1]+[512]),('float',[float(ids[0])]+ids[1:]),('bool',[True]+ids[1:]),('unequalcamera',list(range(33))+list(range(256,287)))]:case(name+' tokens rejected',mutate('retained_indices',value),True)
case('wrong episode rejected',mutate('episode_id','wrong-original-episode'),True)
case('wrong task rejected',mutate('task_id',999),True)
case('seven-step actions rejected',mutate('normalized_actions',original['normalized_actions'][:-1]),True)
xs=copy.deepcopy(original['normalized_actions']);xs[0]=xs[0][:-1];case('six-dim action rejected',mutate('normalized_actions',xs),True)
for name,value in [('NaN',float('nan')),('Inf',float('inf'))]:
 xs=copy.deepcopy(original['normalized_actions']);xs[0][0]=value;case(name+' action rejected',mutate('normalized_actions',xs),True)
for metric in ('teacher_l1','demonstration_l1'):
 for name,value in [('negative',-.1),('NaN',float('nan')),('Inf',float('inf'))]:case(name+' '+metric+' rejected',mutate(metric,value),True)
vals={x['update']:copy.deepcopy(x) for x in review['arms']['A']['validation']}
case('actual selected earliest minimum retained',lambda:m.need(m.select_validation(vals)['update']==review['arms']['A']['earliest_selected_update'],'actual selection'))
missing=copy.deepcopy(vals);del missing[2500];case('missing500node rejected',lambda:m.select_validation(missing),True)
extra=copy.deepcopy(vals);extra[125]={'update':125,'teacher_l1':0};case('off-schedule node rejected',lambda:m.select_validation(extra),True)
nonn=copy.deepcopy(vals);nonn[1500]['teacher_l1']=float('nan');case('NaN selection rejected',lambda:m.select_validation(nonn),True)
wrong=copy.deepcopy(vals);wrong[500]['update']=1000;case('wrong node identity rejected',lambda:m.select_validation(wrong),True)
tie=copy.deepcopy(vals)
for x in tie.values():x['teacher_l1']=1.0
tie[500]['teacher_l1']=tie[3000]['teacher_l1']=0.;case('equal minimum chooses earlier500',lambda:m.need(m.select_validation(tie)['update']==500,'earlier tie'))
case('source173 retained',lambda:m.need('len(inventory["files"])==173' in p.read_text(),'exact173 source'))
case('sample reconstruction fixed seed23',lambda:m.need('random.Random(23)' in p.read_text(),'seed23'))
case('archive publication not falsely claimed',lambda:m.need(review['archive_reconstruction']['status']=='not_claimed_here','root archive separate'))
if suite=='object':
 root=m.refread(review['root_review']);j=next(x for x in root['registered_pair_jobs_at_review'] if str(x['job_id'])=='3028468')
 failuremod=m.io.load('scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py')
 case('exact original failed startup reconstructs',lambda:m.need(failuremod.require_saved(m.io.Evidence(),job=j)['elapsed_seconds']==69,'failedGPU retained'))
 for key,value in [('elapsed_seconds',0),('exit_code','0:0'),('invocation_sha256','0'*64)]:
  q=copy.deepcopy(j);q[key]=value;case('corrupt failed '+key+' rejected',lambda q=q:failuremod.require_saved(m.io.Evidence(),job=q),True)
out={'schema':'formal_main_v2','kind':'independent_terminal_audit_cpu_fault_injection','status':'passed','suite':suite,'job_id':job,'entrypoint':{'path':str(p.relative_to(R)),'sha256':source_sha},'review':{'path':str(rr.relative_to(R)),'sha256':review_sha},'original_validation':{'path':row['path'],'sha256':row['sha256']},'passed':len(passed),'failed':0,'checks':passed,'GPU_seconds':0,'state_Git_Slurm_mutations':False,'checkpoint_tensor_loads':0,'scientific_data_mutations':False}
dest=D/suite/outname
with dest.open('x') as f:json.dump(out,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({'path':str(dest.relative_to(R)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'passed':len(passed),'failed':0}))
