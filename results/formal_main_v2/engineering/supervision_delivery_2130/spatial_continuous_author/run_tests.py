from pathlib import Path
import sys,hashlib
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent
PINS={'admission.py': '0e5d2bbdca27640c4784393b3ea6a17969a7c6235bdeeb10b61c4a8ab7546b74', 'gateway.py': '71af9cf0bce935d00934db8c8198f7f9624fd7194f570e36efd95f77da0634c6', 'prepare.py': 'cf259a2d105456675e0b9cf4d23dc6825a5483df3932a68e50fa9627cf6cb3ac', 'test_continuation.py': 'a684c5c449246e66511537ae684fff5cdf5b12e4c5303bb88bab2bc3864a3d7b'}
for name,pin in PINS.items():
 if hashlib.sha256((C/name).read_bytes()).hexdigest()!=pin:raise ValueError('candidate drift: '+name)
import pytest
raise SystemExit(pytest.main([str(C/'test_continuation.py'),'-q','-p','no:cacheprovider','--basetemp='+str(C/'pytest_a1'),'--junitxml='+str(C/'author_tests_a1.xml')]))
