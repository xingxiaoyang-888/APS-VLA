from pathlib import Path
import ast,hashlib,json
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/goal_remaining5_runtime_20261021T0449');p=D/'package/entry.py'
b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='c2677e03c5475563e822fbbdadd3457b1b71c059e0a7982d31ca107dc8cff8fa'
with (D/'package/entry.py.pre_ACK_and_encoding_v4').open('xb') as f:f.write(b)
s=b.decode()
old="""        require(len(events) < 1024 and len(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()) <= 65536, 'outer event storage bound exceeded; fail closed without truncation')
        with eventpath.open('a', encoding='utf-8') as f:
            json.dump(row, f, sort_keys=True, ensure_ascii=False, allow_nan=False)
            f.write('\\n')
            f.flush()
            os.fsync(f.fileno())"""
new="""        if len(events) >= 1024:raise MetadataBoundAbort('outer event count exceeds bound; prefix retained')
        raw = bounded_json_bytes(row,65536)
        with eventpath.open('ab') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())"""
assert s.count(old)==1;s=s.replace(old,new)
old="""        require(len(json.dumps(complete,sort_keys=True,ensure_ascii=False,allow_nan=False).encode())<=8*1024*1024,'terminal completion metadata exceeds bound; raw prefix retained')
        with (outer / 'completion.json').open('x', encoding='utf-8') as f:
            json.dump(complete, f, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\\n')"""
new="""        complete_raw=bounded_json_bytes(complete,8*1024*1024,indent=2)
        with (outer / 'completion.json').open('xb') as f:f.write(complete_raw)"""
assert s.count(old)==1;s=s.replace(old,new)
old="""        require(len(json.dumps(parent,sort_keys=True,ensure_ascii=False,allow_nan=False).encode())<=8*1024*1024,'typed parent metadata exceeds bound; raw prefix retained')
        with (outer / 'typed_parent.json').open('x', encoding='utf8') as f:
            json.dump(parent, f, sort_keys=True, ensure_ascii=False, indent=2)
            f.write('\\n')"""
new="""        parent_raw=bounded_json_bytes(parent,8*1024*1024,indent=2)
        with (outer / 'typed_parent.json').open('xb') as f:f.write(parent_raw)"""
assert s.count(old)==1;s=s.replace(old,new)
old=""" storage=load(P/PKG/'storage.py','goal_r5_verify_storage',package['files'][PKG+'/storage.py'])
 capacity=storage.verify_storage(ctx,must_be_fresh=must_be_fresh,aggregate_pair_keys=scope.KEYS)"""
new=""" if must_be_fresh:
  storage=load(P/PKG/'storage.py','goal_r5_verify_storage',package['files'][PKG+'/storage.py'])
  capacity=storage.verify_storage(ctx,must_be_fresh=True,aggregate_pair_keys=scope.KEYS)
 else:
  capacity={'status':'not_rechecked_existing_ACK_source_identity_only','fresh_submission_capacity_verified':False,'new_storage_paths_created':False,'new_submission_authorized':False}
"""
assert s.count(old)==1;s=s.replace(old,new)
needle='def redirect_runtime_output(ctx):'
addition="""def bounded_json_bytes(value,limit,*,indent=None):
 try:raw=(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=indent)+'\\n').encode('utf-8')
 except BaseException as error:raise MetadataBoundAbort('metadata serialization failed; original prefix retained') from error
 if len(raw)>limit:raise MetadataBoundAbort('exact serialized metadata exceeds bound; original prefix retained')
 return raw

"""
assert s.count(needle)==1;s=s.replace(needle,addition+needle)
ast.parse(s);p.write_text(s)
report={'status':'bounded_pre_freeze_correction_complete','before_sha256':hashlib.sha256(b).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'fresh_submit_all_five_capacity_unchanged':True,'existing_ACK_only_no_new_capacity_or_claim':True,'exact_written_encoding_guard_includes_indent_and_newline':True,'original_loop_or_actions_changed':False,'production_writes':0}
with (D/'ACK_and_encoding_v4_result.json').open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(report))
