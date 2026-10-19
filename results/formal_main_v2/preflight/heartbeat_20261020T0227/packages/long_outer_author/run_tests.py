import hashlib,importlib.util,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(HERE/"prepare.py")=="87b998c474ed548d31d79f8bcc47e5d6fcc17eaebd0e43b824658595cd851a11"
assert sha(HERE/"test_outer.py")=="5e63d437ba0b125209e1f139d0150ab2ac7ad115d6125b54cb8ee899436962fc"
spec=importlib.util.spec_from_file_location("outer1827_guard",HERE/"prepare.py")
p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
old,c,runtime=p.modules();before=p.protected(old)
import pytest
rc=pytest.main(["-q","-p","no:cacheprovider",str(HERE/"test_outer.py"),"--basetemp="+str(HERE/"pytest_a1"),"--junitxml="+str(HERE/"author_tests_a1.xml")])
assert p.protected(old)==before
raise SystemExit(rc)
