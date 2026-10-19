"""Read-only CPU counterexample of the exact O2A join after upstream reconstruction.
No production proof is generated. Upstream artifacts here are explicitly synthetic.
"""
from pathlib import Path
from types import SimpleNamespace
import copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
path=R/'scripts/ops/formal_action_deployment_v1/consumer.py'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'
spec=importlib.util.spec_from_file_location('mixed_prefix_readonly_counterexample',path)
c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
def require(condition,message):
 if not condition:raise ValueError(message)
# Stub only inputs already reconstructed by the upstream raw-review chain. Test
# the published require_matching_o2a function unchanged, not model/Slurm/source.
c._reviewer=lambda evidence:SimpleNamespace(require=require)
base=dict(execution_version=c.VERSION,action_semantics_sha256='a'*64,execution_manifest_sha256='b'*64,
 observations=30,methods=22,attempted_policy_forwards=14300,scientific_complete=True)
def run(case):
 reports={'development':copy.deepcopy(base),'full':copy.deepcopy(base),'components':copy.deepcopy(base)}
 reports['development']['historical_transition']=dict(from_version='formal-downstream-root-v1',
  preserved_prefix_bytes=592887,preserved_prefix_sha256='3a175dbc5dd7a23cd2c3c8385cb6ff3c525f09d4e607ff32a69a10869672a2f9',historical_terminal_outcomes_replaced=False)
 # No registered equivalence mapping is included.
 if case=='top_level_old_control':reports['development']['execution_version']='formal-downstream-root-v1'
 if case=='different_semantics_control':reports['development']['action_semantics_sha256']='c'*64
 c.review_downstream_output=lambda evidence,reference,**kwargs:reports[reference]
 try:
  value=c.require_matching_o2a(None,['development'],'full','components',suite='libero_spatial')
  return dict(case=case,accepted=True,returned_status=value['status'],final_release=value['final_release'],input_reports=reports)
 except ValueError as error:return dict(case=case,accepted=False,error=str(error),input_reports=reports)
if __name__=='__main__':print(json.dumps([run(x) for x in ['mixed_old_prefix_no_equivalence','top_level_old_control','different_semantics_control']],sort_keys=True))
