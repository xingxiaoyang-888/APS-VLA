from pathlib import Path
import copy, gzip, hashlib, io, json, tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_terminal_archive_20261021T0334'
vp=D/'verify_archives.py';vraw=vp.read_bytes()
assert hashlib.sha256(vraw).hexdigest()=='e466661b2899ce289947867c2b44eeb280fd34a2ee15f48c7bb20721a3fea2d3'
V={'__name__':'goal_nonweight_archive_verifier','__file__':str(vp)}
exec(compile(vraw,str(vp),'exec'),V)
inv=json.loads((D/'inventory.json').read_bytes());members=copy.deepcopy([m for m in inv['members'] if m['namespace']=='P_passive'][:2])
F=D/'verifier_fixtures';F.mkdir(exist_ok=False);checks=[]
raws=[]
for m in members:
    b=Path(m['source']).read_bytes();assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256'];raws.append(b)
def make(name,indices=(0,1),alter=None):
    p=F/(name+'.tar.gz')
    with p.open('xb') as out:
        with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as tf:
                for position,i in enumerate(indices):
                    m=members[i];ti=tarfile.TarInfo(m['archive_path']);ti.size=len(raws[i]);ti.mode=0o600;ti.uid=ti.gid=0;ti.mtime=0
                    if alter: alter(ti,position)
                    tf.addfile(ti,io.BytesIO(raws[i]) if ti.isfile() else None)
    return p
def part(p):
    return {'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'member_indices':[0,1],'member_count':2,'raw_bytes':sum(m['bytes'] for m in members)}
p=make('valid');par=part(p)
V['verify_volume'](p,par,members);checks.append({'name':'valid_two_real_passive_blob_bytes','expected':'pass','passed':True})
def reject(name,fn):
    try: fn()
    except (ValueError,RuntimeError,tarfile.TarError,EOFError,OSError) as exc:
        checks.append({'name':name,'expected':'reject','passed':True,'exception_type':type(exc).__name__});return
    raise AssertionError('accepted '+name)
for name,key,value in [('wrong_part_sha','sha256','0'*64),('wrong_part_bytes','bytes',par['bytes']+1),('duplicate_indices','member_indices',[0,0]),('out_of_range','member_indices',[0,2]),('wrong_count','member_count',1),('wrong_raw_total','raw_bytes',par['raw_bytes']+1),('bool_index','member_indices',[False,1])]:
    bad=copy.deepcopy(par);bad[key]=value;reject(name,lambda bad=bad:V['verify_volume'](p,bad,members))
bad=copy.deepcopy(members);bad[0]['sha256']='0'*64;reject('wrong_restored_sha',lambda:V['verify_volume'](p,par,bad))
bad=copy.deepcopy(members);bad[0]['bytes']+=1;badpar=copy.deepcopy(par);badpar['raw_bytes']+=1;reject('wrong_restored_bytes',lambda:V['verify_volume'](p,badpar,bad))
for name,indices,alter in [
 ('extra_entry',(0,1,0),None),('missing_entry',(0,),None),('swapped_order',(1,0),None),
 ('tar_symlink',(0,1),lambda ti,pos:(setattr(ti,'type',tarfile.SYMTYPE),setattr(ti,'linkname','forbidden')) if pos==0 else None),
 ('wrong_mode',(0,1),lambda ti,pos:setattr(ti,'mode',0o644) if pos==0 else None),
 ('wrong_mtime',(0,1),lambda ti,pos:setattr(ti,'mtime',1) if pos==0 else None),
 ('traversal_member',(0,1),lambda ti,pos:setattr(ti,'name','../escape') if pos==0 else None)]:
    q=make(name,indices,alter);badpart=part(q);reject(name,lambda q=q,badpart=badpart:V['verify_volume'](q,badpart,members))
q=F/'corrupt.tar.gz';q.write_bytes(b'not a gzip archive');badpart=part(q);reject('corrupt_gzip',lambda:V['verify_volume'](q,badpart,members))
for name,s in [('absolute','/escape'),('parent','a/../escape'),('backslash','a\\escape'),('empty',''),('dot','./a')]:
    reject('unsafe_path_'+name,lambda s=s:V['safe_relative'](s))
report={'schema':'formal_main_v2','kind':'Goal3054717_archive_integrity_verifier_CPU_tests','status':'passed','source_sha256':hashlib.sha256(vraw).hexdigest(),'positive_count':sum(c['expected']=='pass' for c in checks),'negative_count':sum(c['expected']=='reject' for c in checks),'checks':checks,'fixtures':'Two already-recorded passive development blobs; tar structural/corruption tests only, no simulator/model/inference.','scientific_admission':False,'new_trials':0,'new_GPU_jobs':0}
with (D/'verifier_CPU_tests.json').open('x') as f:json.dump(report,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:report[k] for k in ('status','positive_count','negative_count','source_sha256')}))
