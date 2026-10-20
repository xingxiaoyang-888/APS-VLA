from pathlib import Path
import importlib.util,hashlib,json,sys,ast
D=Path(__file__).parent;R=D.parents[1]
p=D/'ast_gate_v1.py';spec=importlib.util.spec_from_file_location('candidate_generation_only',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Static AST construction only; no loop or simulator execution. This temporary
# derivation callback is not a verification pass and is absent from final source.
m.base.assert_projection=lambda a,b:{}
a,b,_=m.derive_run((R/'src/cti_vla/evaluation/libero_runtime.py').read_bytes())
pin=hashlib.sha256(m.base.text(b).encode()).hexdigest()
text=p.read_text();assert text.count('REPLACE_DERIVED_SHA')==1
out=D/'ast_gate_v2.py';out.open('x').write(text.replace('REPLACE_DERIVED_SHA',pin))
with (D/'source_generation.json').open('x') as f:json.dump({'kind':'source_only_AST_layout_freeze_not_test_acceptance','derived_AST_sha256':pin,'final_source_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'GPU_launches':0,'scientific_trials_added':0},f,sort_keys=True,indent=2)
print(pin)
