"""CPU fault injection against the exact helpers used in the raw terminal audit."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/Goal64s41_independent_20261020T1644'
p=D/'audit_3043877_v2.py';pin='6a158d05bad33edda60260afb7375916892303a3b60fda51b85bb3496bb01e46'
assert hashlib.sha256(p.read_bytes()).hexdigest()==pin
spec=importlib.util.spec_from_file_location('Goal41CPU1644',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
rr=D/'3043877_independent_review.json';rrsha='1b1dd348efcc5b0857bcefde44d4f9b97243952d4bc15ee5383f46b1aea3d064'
assert hashlib.sha256(rr.read_bytes()).hexdigest()==rrsha
review=json.loads(rr.read_bytes());row=review['arms']['A']['validation'][0]
vp=R/row['path'];assert hashlib.sha256(vp.read_bytes()).hexdigest()==row['sha256'];v=json.loads(vp.read_bytes())
original=v['observations'][0];ref={'episode_id':original['episode_id'],'task_id':original['task_id']}
passed=[]
def case(name,action,reject=False):
 try:action()
 except (ValueError,AssertionError) as ex:
  assert reject,(name,str(ex));passed.append({'name':name,'expected':'reject','observed':'rejected','reason':str(ex)})
 else:
  assert not reject,name;passed.append({'name':name,'expected':'accept','observed':'accepted'})
def change(key,value):
 x=copy.deepcopy(original);x[key]=value;return lambda:m.validate_hard64_observation(x,ref)
case('actual original observation accepted',lambda:m.validate_hard64_observation(original,ref))
ids=original['retained_indices']
case('missing token rejected',change('retained_indices',ids[:-1]),True)
case('duplicate token rejected',change('retained_indices',ids[:-1]+[ids[-2]]),True)
case('reordered token rejected',change('retained_indices',list(reversed(ids))),True)
case('out of range token rejected',change('retained_indices',ids[:-1]+[512]),True)
case('floating token rejected',change('retained_indices',[float(ids[0])]+ids[1:]),True)
case('boolean token rejected',change('retained_indices',[True]+ids[1:]),True)
case('unequal camera quotas rejected',change('retained_indices',list(range(33))+list(range(256,287))),True)
case('wrong episode rejected',change('episode_id','not-the-original-episode'),True)
case('wrong task rejected',change('task_id',999),True)
case('seven step action chunk rejected',change('normalized_actions',original['normalized_actions'][:-1]),True)
xs=copy.deepcopy(original['normalized_actions']);xs[0]=xs[0][:-1]
case('six dimension action rejected',change('normalized_actions',xs),True)
for label,value in [('NaN',float('nan')),('Inf',float('inf'))]:
 xs=copy.deepcopy(original['normalized_actions']);xs[0][0]=value
 case(label+' action rejected',change('normalized_actions',xs),True)
for metric in ['teacher_l1','demonstration_l1']:
 for label,value in [('negative',-0.1),('NaN',float('nan')),('Inf',float('inf'))]:case(label+' '+metric+' rejected',change(metric,value),True)
vals={x['update']:copy.deepcopy(x) for x in review['arms']['A']['validation']}
case('all actual validation nodes choose actual3500',lambda: m.need(m.select_validation(vals)['update']==3500,'actual selection'))
missing=copy.deepcopy(vals);del missing[2500]
case('missing scheduled validation rejected',lambda:m.select_validation(missing),True)
extra=copy.deepcopy(vals);extra[125]={'update':125,'teacher_l1':0}
case('extra unscheduled validation rejected',lambda:m.select_validation(extra),True)
nonn=copy.deepcopy(vals);nonn[1500]['teacher_l1']=float('nan')
case('nonfinite selection metric rejected',lambda:m.select_validation(nonn),True)
wrong=copy.deepcopy(vals);wrong[500]['update']=1000
case('mismatched update identity rejected',lambda:m.select_validation(wrong),True)
tie=copy.deepcopy(vals)
for x in tie.values():x['teacher_l1']=1.0
tie[500]['teacher_l1']=tie[3000]['teacher_l1']=0.0
case('equal minimum chooses earlier500',lambda:m.need(m.select_validation(tie)['update']==500,'early tie'))
# Schema constants are audited: catches the original adapter's 173-to-413 typo.
case('exact173 source cardinality restored',lambda:m.need('len(inventory["files"])==173' in p.read_text() and 'len(inventory["files"])==413' not in p.read_text(),'source173 typo regression'))
out={'status':'passed','kind':'independent_audit_CPU_fault_injection','entrypoint':{'path':str(p.relative_to(R)),'sha256':pin},'raw_validation':{'path':row['path'],'sha256':row['sha256']},'training_review':{'path':str(rr.relative_to(R)),'sha256':rrsha},'checks':passed,'passed_count':len(passed),'failed_count':0,'GPU_seconds':0,'audit_main_reexecuted':False,'scientific_data_mutated':False,'state_Git_Slurm_written':False}
dest=D/'cpu_selfcheck.json'
with dest.open('x') as f:json.dump(out,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({'path':str(dest.relative_to(R)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'passed':len(passed),'failed':0}))
