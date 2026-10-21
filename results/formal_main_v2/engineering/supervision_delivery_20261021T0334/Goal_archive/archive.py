from pathlib import Path, PurePosixPath
import argparse, gzip, hashlib, io, json, math, os, re, stat, tarfile, time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_terminal_archive_20261021T0334'
INV_SHA='db4d8a05cd7f21af5aac0687d2190297cd571eb1a6ffc83eb74d235d53eb7ac1'
LIMIT=90*1024*1024
BUDGET=80*1024*1024
ORIGINAL_CONSUMER='c12a6a5b99c4e34ff19f535a4725fecd9fcabc70ba1f37dc2c6c32c979ad3c4b'
def require(ok,msg):
    if not ok: raise RuntimeError(msg)
def sha(b): return hashlib.sha256(b).hexdigest()
def digest_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def strict_json(b):
    def pairs(xs):
        d={}
        for k,v in xs:
            require(k not in d,'duplicate JSON key');d[k]=v
        return d
    return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def write_json(p,v):
    with p.open('x',encoding='utf-8') as f:
        json.dump(v,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')
def signature(p):
    s=p.stat()
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def safe(p):
    require(p.is_absolute() and p.resolve()==p,'noncanonical source path')
    require(not any(x.is_symlink() for x in (p,*p.parents)),'source symlink')
    require(p.is_file(),'not a regular source file')
def valid_name(s):
    q=PurePosixPath(s)
    require(not q.is_absolute() and '..' not in q.parts and '\\' not in s and q.as_posix()==s,'unsafe archive path')
def load_inventory():
    raw=(D/'inventory.json').read_bytes();require(sha(raw)==INV_SHA,'inventory pin')
    inv=strict_json(raw)
    require(inv['status']=='exact_event_allowlist_and_original_read_blob_verified','inventory status')
    require(inv['job_id']=='3054717' and inv['scientific_admission'] is False,'scope')
    require(inv['source_consumer']['sha256']==ORIGINAL_CONSUMER,'consumer pin')
    require(inv['member_count']==35076 and inv['member_bytes']==1680131983,'inventory count/bytes')
    seen=set()
    for m in inv['members']:
        valid_name(m['archive_path']);require(m['archive_path'] not in seen,'duplicate member');seen.add(m['archive_path'])
        require(m['restore_root'] in ('R','P'),'restore root')
        valid_name(m['restore_relative'])
        require(type(m['bytes'])is int and m['bytes']>=0 and re.fullmatch('[a-f0-9]{64}',m['sha256']),'member metadata')
        require(m['namespace'] in ('R_observations','P_passive','P_attempt_metadata','R_observation_metadata'),'namespace')
        if m['namespace'] in ('R_observations','P_passive'):
            require(m['original_consumer_read_blob_verified'] is True,'blob original verification')
    return inv
def groups(members):
    result=[]
    for namespace in ('R_observations','R_observation_metadata','P_passive','P_attempt_metadata'):
        current=[];cost=10240
        for idx,m in enumerate(members):
            if m['namespace']!=namespace: continue
            item=4096+((m['bytes']+511)//512)*512
            require(item+10240<BUDGET,'individual member cannot fit bounded volume')
            if current and cost+item>BUDGET:
                result.append((namespace,current,cost));current=[];cost=10240
            current.append(idx);cost+=item
        if current: result.append((namespace,current,cost))
    require(sorted(i for _,ii,_ in result for i in ii)==list(range(len(members))),'exact groups partition')
    return result
def verify_part(p,part,members):
    safe(p);require(p.stat().st_size==part['bytes'] and p.stat().st_size<LIMIT,'part size')
    require(digest_file(p)==part['sha256'],'part SHA')
    expect=part['member_indices'];seen=[]
    with tarfile.open(p,mode='r|gz') as tf:
        for member in tf:
            require(len(seen)<len(expect),'extra archive member')
            idx=expect[len(seen)];m=members[idx]
            require(member.name==m['archive_path'] and member.isfile() and not member.issym() and not member.islnk(),'archive member path/type')
            require(member.size==m['bytes'] and member.uid==0 and member.gid==0 and member.mode==0o600 and member.mtime==0,'archive member bytes/mode')
            f=tf.extractfile(member);require(f is not None,'archive member absent')
            h=hashlib.sha256();size=0
            for b in iter(lambda:f.read(1024*1024),b''):size+=len(b);h.update(b)
            require(size==m['bytes'] and h.hexdigest()==m['sha256'],'restored member differs')
            seen.append(idx)
    require(seen==expect,'missing archive member')
    return {'part':part['path'],'sha256':part['sha256'],'restored_member_count':len(seen),'restored_bytes':sum(members[i]['bytes'] for i in seen),'exact_member_order':True,'all_decompressed_bytes_verified':True}
def archive():
    inv=load_inventory();members=inv['members'];plans=groups(members);V=D/'volumes';V.mkdir(exist_ok=False)
    parts=[];checks=[]
    for n,(namespace,indices,bound) in enumerate(plans,1):
        p=V/('%02d_%s.tar.gz'%(n,namespace))
        before={}
        with p.open('xb') as out:
            with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0,compresslevel=6) as gz:
                with tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as tf:
                    for idx in indices:
                        m=members[idx];q=Path(m['source']);safe(q);sig=signature(q);raw=q.read_bytes()
                        require(signature(q)==sig and len(raw)==m['bytes'] and sha(raw)==m['sha256'],'source changed since inventory')
                        ti=tarfile.TarInfo(m['archive_path']);ti.size=len(raw);ti.mode=0o600;ti.uid=ti.gid=0;ti.mtime=0;ti.uname=ti.gname=''
                        tf.addfile(ti,io.BytesIO(raw))
                        require(signature(q)==sig,'source changed during archive')
        require(p.stat().st_size<LIMIT,'compressed volume exceeds 90 MiB')
        part={'path':p.relative_to(D).as_posix(),'namespace':namespace,'sha256':digest_file(p),'bytes':p.stat().st_size,'member_indices':indices,'member_count':len(indices),'raw_bytes':sum(members[i]['bytes'] for i in indices),'conservative_tar_bytes_budget':bound}
        parts.append(part);checks.append(verify_part(p,part,members))
        print(json.dumps({'volume':n,'of':len(plans),'path':part['path'],'compressed_bytes':part['bytes'],'restored_members':len(indices)}),flush=True)
    require(sha((D/'inventory.json').read_bytes())==INV_SHA,'inventory changed')
    manifest={'schema':'formal_main_v2','kind':'Goal3054717_exact_nonweight_content_addressed_archives','status':'archived_and_byte_restoration_verified','job_id':'3054717','inventory':{'path':'inventory.json','sha256':INV_SHA},'original_consumer_sha256':ORIGINAL_CONSUMER,'archive_format':'gzip tar PAX','gzip_mtime':0,'gzip_level':6,'volume_compressed_size_limit_exclusive':LIMIT,'source_member_count':len(members),'source_raw_bytes':sum(m['bytes'] for m in members),'volume_count':len(parts),'compressed_bytes':sum(p['bytes'] for p in parts),'parts':parts,'source_files_unchanged':True,'weights_or_final_values':False,'scientific_admission':False,'new_trials':0,'new_GPU_jobs':0,'restoration':'Exact inventory restore_root and restore_relative mapping; validate each member before writing. No extraction performed by this archival job.'}
    write_json(D/'archive_manifest.json',manifest)
    report={'schema':'formal_main_v2','kind':'Goal3054717_nonweight_archive_restoration_verification','status':'passed','archive_manifest_sha256':sha((D/'archive_manifest.json').read_bytes()),'inventory_sha256':INV_SHA,'all_members_verified':len(members),'all_raw_bytes_verified':sum(m['bytes'] for m in members),'volume_count':len(parts),'volumes':checks,'scientific_admission':False,'new_trials':0,'new_GPU_jobs':0}
    write_json(D/'restoration_verification.json',report)
    print(json.dumps({'status':'passed','volume_count':len(parts),'raw_bytes':manifest['source_raw_bytes'],'compressed_bytes':manifest['compressed_bytes'],'manifest_sha256':sha((D/'archive_manifest.json').read_bytes()),'restoration_report_sha256':sha((D/'restoration_verification.json').read_bytes())}),flush=True)
if __name__=='__main__':
    try: archive()
    except BaseException as e:
        p=D/('archive_failure_%s.json'%time.time_ns())
        write_json(p,{'status':'failed','exception_type':type(e).__name__,'message':str(e),'scientific_admission':False})
        raise
