from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent
PINS={'admission.py': '187e5393e6ffcdc8f042bfcdb032860048e6f36282160825dbb928f3a83ad46f', 'gateway.py': '4f552abcc05d72ff84975e360ea28a624a4744febb8518e2fc71839fe47d5864', 'prepare.py': 'f5951e7fbd4de3ce4d828023118aed3a00843425712f650550b4096bd5098619', 'document_binding.json': '37123f887b53931016d6a5ef85984b5c76d9b055b632d4b171298ffe2faea019', 'test_doc_binding.py': 'b52597c3ff47b506c01ce3d076308b6e2028f9221614e454a84b419b68e6c247'}
for name,pin in PINS.items():
 if hashlib.sha256((C/name).read_bytes()).hexdigest()!=pin:raise ValueError('candidate source changed: '+name)
import pytest
raise SystemExit(pytest.main([str(C/'test_doc_binding.py'),'-q','-p','no:cacheprovider','--basetemp='+str(C/'pytest_a1'),'--junitxml='+str(C/'tests_a1.xml')]))
