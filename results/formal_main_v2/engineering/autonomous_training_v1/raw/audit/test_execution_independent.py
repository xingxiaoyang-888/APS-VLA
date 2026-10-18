"""Independent boundary tests. Synthetic upstream reviewer; no GPU or real state."""
import copy, importlib.util, json
from pathlib import Path
import pytest
AUTHOR=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/autonomous_training_v1/train/test_execution.py')
spec=importlib.util.spec_from_file_location('author_execution_fixtures',AUTHOR)
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
m=t.m
project=t.project

def no_b(project,args):
    root=project['root'];rp=root/args['review_ref']['path'];review=json.loads(rp.read_bytes())
    out=review['output_relative'];result_path=out+'/training_progress.json'
    result=json.loads((root/result_path).read_bytes());result['arms']['B']={'status':'not_started'}
    t.write(root,result_path,result);review['files'][result_path]=m.sha(root/result_path)
    review['files']={n:s for n,s in review['files'].items() if not n.startswith(out+'/B/')}
    for collection in (review['server_resume_checks'],args['actual_resume_checks']):
        row=next(x for x in collection if x['arm']=='B');row.update(exists=False);row.pop('sha256',None);row.pop('bytes',None)
    row=next(x for x in review['server_resume_checklist'] if x['arm']=='B');row.update(must_exist=False,sha256=None)
    t.write(root,args['review_ref']['path'],review);args['review_ref']=t.ref(root,args['review_ref']['path']);args['rebuilt_review']=copy.deepcopy(review)
    return args

@pytest.mark.parametrize('a',[735,5000])
def test_fresh_softwall_b_not_started_resumes_without_reset(project,a):
    args=t.terminal(project,completed={'A':a,'B':0},autonomous=True,previous=False,skip_b=True)
    inv=t.m.Evidence(project['root']).read(args['job']['invocation'])
    inv['autonomous_execution']['completed_before']={'A':0,'B':0}
    t.write(project['root'],args['job']['invocation'],inv)
    args['job']['invocation_sha256']=m.sha(project['root']/args['job']['invocation'])
    args['job']['autonomous_execution']=copy.deepcopy(inv['autonomous_execution'])
    def update(r):
        r['registered_pair_jobs_at_review']=[copy.deepcopy(args['job'])];r['invocation_sha256']=args['job']['invocation_sha256']
    t.rewrite_review(project,args,update)
    value=t.classify(project,no_b(project,args))
    assert value['decision']=='ready' and value['completed_by_arm']=={'A':a,'B':0}
    assert next(x for x in value['server_resume_checks'] if x['arm']=='B')['exists'] is False

@pytest.mark.parametrize('a',[501,735])
def test_nonboundary_legacy_clean_softwall_migrates_to5000(project,a):
    args=t.terminal(project,completed={'A':a,'B':500},target=1000,skip_b=True)
    root=project['root'];review=args['rebuilt_review'];out=review['output_relative'];name=out+'/A/progress_report.json'
    report=json.loads((root/name).read_bytes());report['stop_reason']='engineering_wall_limit_after_complete_update';t.write(root,name,report)
    pair=json.loads((root/(out+'/training_progress.json')).read_bytes());pair['arms']['A']=report;t.write(root,out+'/training_progress.json',pair)
    t.rewrite_review(project,args,lambda r:r['files'].update({name:m.sha(root/name),out+'/training_progress.json':m.sha(root/(out+'/training_progress.json'))}))
    assert t.classify(project,args)['next_target']==5000

@pytest.mark.parametrize('change',['wall_under_limit','negative_progress','registered_contract','actual_bytes','missing_cost_input'])
def test_additional_invalid_admission_fails_closed(project,change):
    args=t.terminal(project,completed={'A':5000,'B':500},autonomous=True,skip_b=True)
    root=project['root']
    if change=='wall_under_limit':
        name='results/formal_main_v2/job_receipts/201.json';t.write(root,name,{'wall_seconds':169199})
        t.rewrite_review(project,args,lambda r:r['files'].update({name:m.sha(root/name)}))
    elif change=='negative_progress':
        inv=json.loads((root/args['job']['invocation']).read_bytes());inv['autonomous_execution']['completed_before']['B']=501
        t.write(root,args['job']['invocation'],inv);args['job']['invocation_sha256']=m.sha(root/args['job']['invocation']);args['job']['autonomous_execution']=copy.deepcopy(inv['autonomous_execution'])
        def update(r):
            r['registered_pair_jobs_at_review'][-1]=copy.deepcopy(args['job']);r['invocation_sha256']=args['job']['invocation_sha256']
        t.rewrite_review(project,args,update)
    elif change=='registered_contract':
        args['job']['allocation_time']='04:00:00'
        t.rewrite_review(project,args,lambda r:r['registered_pair_jobs_at_review'].__setitem__(-1,copy.deepcopy(args['job'])))
    elif change=='actual_bytes':args['actual_resume_checks'][0]['bytes']+=1
    else:t.rewrite_review(project,args,lambda r:r.update(pair_allocated_gpu_seconds=100))
    with pytest.raises(ValueError):t.classify(project,args)

def test_base_and_execution_are_observationally_read_only(project):
    root=project['root'];before={str(p.relative_to(root)):m.sha(p) for p in root.rglob('*') if p.is_file()}
    plan=t.base(project,key='libero_goal_k256_seed41');result=m.build_execution(root,plan,adapter_ref=project['adapter'])
    after={str(p.relative_to(root)):m.sha(p) for p in root.rglob('*') if p.is_file()}
    assert before==after and result['invocation']['watched_files']==plan['invocation']['watched_files']
