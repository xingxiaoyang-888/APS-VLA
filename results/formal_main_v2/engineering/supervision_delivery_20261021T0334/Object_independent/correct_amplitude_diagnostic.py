from pathlib import Path
import ast,hashlib,json
import numpy as np
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/object_terminal_independent_20261021T0334'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'src/cti_vla/evaluation/libero_runtime.py';assert h(source)=='2fc1bacbd1268a36f2e31451c70a650be4f8d0c8f6803e7c8b2a3d45f701c781'
tree=ast.parse(source.read_bytes());loop=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_episode')
branches=[n for n in ast.walk(loop) if isinstance(n,ast.If) and len(n.body)==1 and isinstance(n.body[0],ast.Raise) and isinstance(n.body[0].exc,ast.Call) and n.body[0].exc.args and isinstance(n.body[0].exc.args[0],ast.Constant) and n.body[0].exc.args[0].value=='environment action outside normalized controller [-1, 1] range']
assert len(branches)==1
compares=[n for n in ast.walk(branches[0].test) if isinstance(n,ast.Compare)];assert len(compares)==1
threshold=compares[0].comparators[0].value;assert threshold==1.00001
raw=P/'results/formal_main_v2/libero_object/downstream/linked_policy_error_correction/task08_state0049_dense/attempt01/trials.jsonl';assert h(raw)=='ec9feefaa0bcdc2ea7514e9f5bea2bb01f828a1a2003ac7f20422f46cd663ece'
r=json.loads(raw.read_bytes().splitlines()[-1]);exceed=[]
for i,c in enumerate(r['chunks']):
 a=np.asarray(c['environment_actions'],dtype='<f8');where=np.argwhere(np.abs(a)>threshold)
 if len(where):exceed.append(dict(query_index=i,call_ordinal=i+1,control_step=c['control_step'],count=len(where),positions=[dict(chunk_row=int(row),component=int(col),value=float(a[row,col])) for row,col in where],max_abs=float(np.max(np.abs(a)))))
assert exceed and exceed[0]['query_index']==7
original=D/'logical_view_diagnostics.json';value=json.loads(original.read_bytes());oldsha=h(original)
value['new_current_amplitude_over_old_threshold']=exceed;value['old_amplitude_threshold_from_exact_source']=threshold
value['diagnostic_correction']=dict(original_sha256=oldsha,original_threshold_in_private_precheck=1.05,corrected_threshold=threshold,original_source_sha256=h(source),source_branch=ast.unparse(branches[0]),retained_first7_unchanged=True,old_rejected_query8_payload_remains_unknown=True,terminal_or_scientific_conclusion_changed=False,explanation='Corrected only optional private magnitude diagnostic; original action queue/finite/typed evidence reconstruction and all raw bytes are unchanged. New eighth call exceeds the historical range guard; original unrecorded eighth payload is not inferred.')
p=D/'logical_view_diagnostics_v2.json';p.open('x',encoding='utf-8').write(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(status='private_optional_threshold_diagnostic_corrected_original_retained',threshold=threshold,exceeding_chunks=exceed,path=p.name,sha256=h(p)),ensure_ascii=False))
