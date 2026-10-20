"""Exact single-doc bridge CPU checks; no production mutation or Slurm."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
import pytest
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('doc_binding_gateway',C/'gateway.py')
g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g);a=g.a

@pytest.fixture
def box(tmp_path):
 doc=tmp_path/a.DOCUMENT;doc.parent.mkdir(parents=True);doc.write_bytes((C/'current_document.md').read_bytes())
 binding=tmp_path/'binding.json';binding.write_bytes((C/'document_binding.json').read_bytes())
 return a.Evidence(tmp_path),{'path':'binding.json','sha256':a.DOCUMENT_BINDING_SHA}

def test_exact_historical_entry_and_both_content_versions(box):
 e,r=box
 with pytest.raises(ValueError,match='SHA'):e.watch(a.DOCUMENT,a.DOCUMENT_OLD_SHA)
 a.watch_review_evidence(e,a.DOCUMENT_HISTORICAL_REVIEW,a.DOCUMENT,a.DOCUMENT_OLD_SHA,r)
 assert e.hashes=={r['path']:a.DOCUMENT_BINDING_SHA,a.DOCUMENT:a.DOCUMENT_NEW_SHA}
 v=json.loads((e.root/r['path']).read_bytes())
 assert a.digest(v['historical']['utf8'].encode())==a.DOCUMENT_OLD_SHA
 assert a.digest(v['current']['utf8'].encode())==a.DOCUMENT_NEW_SHA
 e.unchanged()

@pytest.mark.parametrize('change',['review_sha','review_path','document_path','old_sha'])
def test_only_exact_signed_independent_map_entry_has_bridge(box,change):
 e,r=box;review=copy.deepcopy(a.DOCUMENT_HISTORICAL_REVIEW);path=a.DOCUMENT;pin=a.DOCUMENT_OLD_SHA
 if change=='review_sha':review['sha256']='0'*64
 if change=='review_path':review['path']=a.ROOT_PATH
 if change=='document_path':
  path='docs/another.md';(e.root/path).write_bytes((C/'current_document.md').read_bytes())
 if change=='old_sha':pin='0'*64
 with pytest.raises(ValueError,match='SHA'):a.watch_review_evidence(e,review,path,pin,r)

@pytest.mark.parametrize('raw',[(C/'historical_document.md').read_bytes(),(C/'current_document.md').read_bytes()+bytes([10])])
def test_current_doc_exact_new_version_not_restored_old(box,raw):
 e,r=box;(e.root/a.DOCUMENT).write_bytes(raw)
 with pytest.raises(ValueError,match='SHA'):a.verify_document_binding(e,r)

@pytest.mark.parametrize('change',['old_content','current_content','git_commit','scope'])
def test_binding_bytes_not_self_authorizing(box,change):
 e,r=box;v=json.loads((e.root/r['path']).read_bytes())
 if change=='old_content':v['historical']['utf8']+='changed'
 if change=='current_content':v['current']['utf8']+='changed'
 if change=='git_commit':v['historical']['git_commit']='0'*40
 if change=='scope':v['document']='docs/another.md'
 (e.root/r['path']).write_bytes(a.canonical(v))
 with pytest.raises(ValueError,match='SHA'):a.verify_document_binding(e,r)
 r['sha256']=a.digest((e.root/r['path']).read_bytes())
 with pytest.raises(ValueError,match='exact document binding'):a.verify_document_binding(e,r)

def test_missing_binding_ref_rejected(box):
 e,r=box
 with pytest.raises(ValueError,match='exact document binding'):a.verify_document_binding(e,None)

def test_other_raw_tamper_is_not_covered(box):
 e,r=box;p=e.root/'results/raw.json';p.parent.mkdir();p.write_bytes(b'original');pin=a.digest(p.read_bytes())
 a.watch_review_evidence(e,a.DOCUMENT_HISTORICAL_REVIEW,'results/raw.json',pin,r)
 p.write_bytes(b'changed')
 with pytest.raises(ValueError,match='SHA'):a.watch_review_evidence(e,a.DOCUMENT_HISTORICAL_REVIEW,'results/raw.json',pin,r)

def test_watched_current_and_binding_fail_drift(box):
 e,r=box;a.verify_document_binding(e,r);(e.root/r['path']).write_bytes(b'{}')
 with pytest.raises(ValueError,match='SHA'):e.unchanged()

def test_old_signed_auth_cannot_authorize_v2(tmp_path):
 rel='configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v1.json'
 p=tmp_path/'old.json';p.write_bytes((a.R/rel).read_bytes())
 with pytest.raises(ValueError,match='typed'):g.validate_authorization(tmp_path,{'path':'old.json','sha256':a.digest(p.read_bytes())})

def node(path,name):
 return next(x for x in ast.parse(path.read_text()).body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name)
@pytest.mark.parametrize('module,name',[
 ('admission.py','Evidence'),('admission.py','history'),('admission.py','compare_reconstruction'),
 ('admission.py','retained_finalizations'),('admission.py','NativeIO'),
 ('gateway.py','controller_owner'),('gateway.py','capacity_gate'),('gateway.py','sbatch_argv'),
 ('gateway.py','parse_ack'),('gateway.py','Gateway')])
def test_raw_native_transaction_primitives_unchanged(module,name):
 assert ast.dump(node(C/module,name))==ast.dump(node(C/'baseline'/module,name))
