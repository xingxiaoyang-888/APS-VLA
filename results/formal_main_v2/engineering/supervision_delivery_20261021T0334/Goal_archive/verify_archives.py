"""Read-only integrity verifier for the exact Goal3054717 nonweight archive set."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, re, tarfile
EXPECTED_INVENTORY='db4d8a05cd7f21af5aac0687d2190297cd571eb1a6ffc83eb74d235d53eb7ac1'
LIMIT=90*1024*1024
def require(ok,message):
    if not ok: raise ValueError(message)
def digest_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def strict_json(raw):
    def pairs(items):
        d={}
        for k,v in items:
            require(k not in d,'duplicate JSON key');d[k]=v
        return d
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def safe_relative(s):
    require(type(s)is str,'path type')
    p=PurePosixPath(s)
    require(s and not p.is_absolute() and '..' not in p.parts and '\\' not in s and p.as_posix()==s,'unsafe relative path')
    return p
def exact_regular(root,relative):
    q=root/str(safe_relative(relative))
    require(q.resolve()==q and q.is_file() and not any(p.is_symlink() for p in (q,*q.parents)),'non-regular/symlink member')
    return q
def verify_volume(p,part,members):
    require(p.stat().st_size==part['bytes'] and p.stat().st_size<LIMIT,'part bytes')
    require(digest_file(p)==part['sha256'],'part SHA')
    indices=part['member_indices']
    require(type(indices)is list and all(type(i)is int and 0<=i<len(members) for i in indices),'indices type/bounds')
    require(len(indices)==part['member_count'] and len(set(indices))==len(indices),'part member count/duplicates')
    require(sum(members[i]['bytes'] for i in indices)==part['raw_bytes'],'part raw bytes')
    restored=0
    with tarfile.open(p,mode='r|gz') as tf:
        for entry in tf:
            require(restored<len(indices),'extra tar member')
            m=members[indices[restored]];safe_relative(entry.name)
            require(entry.name==m['archive_path'] and entry.isfile() and not entry.issym() and not entry.islnk(),'tar path/type')
            require(entry.size==m['bytes'] and entry.uid==0 and entry.gid==0 and entry.mode==0o600 and entry.mtime==0,'tar metadata')
            stream=tf.extractfile(entry);require(stream is not None,'missing file stream')
            h=hashlib.sha256();size=0
            for b in iter(lambda:stream.read(1024*1024),b''):size+=len(b);h.update(b)
            require(size==m['bytes'] and h.hexdigest()==m['sha256'],'decompressed bytes/SHA')
            restored+=1
    require(restored==len(indices),'missing tar member')
    return {'path':part['path'],'verified_members':restored,'verified_raw_bytes':part['raw_bytes'],'part_sha256':part['sha256']}
def verify(directory,manifest_sha256):
    root=Path(directory).absolute()
    require(root.resolve()==root and not any(p.is_symlink() for p in (root,*root.parents)),'archive root symlink')
    require(re.fullmatch('[a-f0-9]{64}',manifest_sha256),'manifest SHA format')
    mp=exact_regular(root,'archive_manifest.json')
    require(digest_file(mp)==manifest_sha256,'manifest SHA')
    manifest=strict_json(mp.read_bytes())
    require(manifest['schema']=='formal_main_v2' and manifest['kind']=='Goal3054717_exact_nonweight_content_addressed_archives','archive schema/kind')
    require(manifest['status']=='archived_and_byte_restoration_verified' and manifest['job_id']=='3054717','archive status/scope')
    require(manifest['inventory']=={'path':'inventory.json','sha256':EXPECTED_INVENTORY},'inventory reference')
    ip=exact_regular(root,'inventory.json');require(digest_file(ip)==EXPECTED_INVENTORY,'inventory bytes')
    inv=strict_json(ip.read_bytes())
    require(inv['status']=='exact_event_allowlist_and_original_read_blob_verified' and inv['job_id']=='3054717','inventory status/scope')
    members=inv['members']
    require(len(members)==35076 and sum(m['bytes'] for m in members)==1680131983,'exact inventory totals')
    require(manifest['source_member_count']==len(members) and manifest['source_raw_bytes']==1680131983,'manifest source totals')
    require(manifest['volume_compressed_size_limit_exclusive']==LIMIT,'volume limit')
    require(manifest['scientific_admission'] is False and manifest['new_trials']==0 and manifest['new_GPU_jobs']==0,'no new science')
    seen_names=set()
    for m in members:
        safe_relative(m['archive_path']);safe_relative(m['restore_relative'])
        require(m['archive_path'] not in seen_names,'duplicate inventory member');seen_names.add(m['archive_path'])
        require(m['restore_root'] in ('R','P'),'restore namespace')
    parts=manifest['parts'];require(len(parts)==manifest['volume_count'],'volume count')
    all_indices=[];part_paths=set();reports=[]
    for part in parts:
        require(part['path'] not in part_paths,'duplicate part');part_paths.add(part['path'])
        require(PurePosixPath(part['path']).parts[0]=='volumes','volume directory')
        p=exact_regular(root,part['path'])
        reports.append(verify_volume(p,part,members));all_indices.extend(part['member_indices'])
    require(sorted(all_indices)==list(range(len(members))),'archive set is not exact partition')
    require(sum(p['bytes'] for p in parts)==manifest['compressed_bytes'],'compressed total')
    on_disk=set()
    for p in (root/'volumes').iterdir():
        require(p.is_file() and not p.is_symlink(),'unknown volume directory or symlink')
        on_disk.add(p.relative_to(root).as_posix())
    require(on_disk==part_paths,'unknown or missing volume')
    return {'schema':'formal_main_v2','kind':'Goal3054717_read_only_archive_reverification','status':'passed','archive_manifest_sha256':manifest_sha256,'inventory_sha256':EXPECTED_INVENTORY,'verified_members':len(members),'verified_raw_bytes':1680131983,'volume_count':len(parts),'compressed_bytes':manifest['compressed_bytes'],'volumes':reports,'extraction_performed':False,'scientific_admission':False,'new_trials':0,'new_GPU_jobs':0}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--directory',required=True);ap.add_argument('--manifest-sha256',required=True)
    args=ap.parse_args();print(json.dumps(verify(args.directory,args.manifest_sha256),ensure_ascii=False,sort_keys=True))
