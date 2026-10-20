from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261021T0349'
M='.local/collect_terminal_20261020T1949/development_gateway/source_publication_candidate.json';PIN='306a447c76ea0e0e3337e35fadfa51cd30fef2a49536ebe8e8b76ad6f6c12914'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def record(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('pubnewdev1949ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 st=R/'results/experiment_supervisor/state.json';before=h(st);s=read(st);assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 assert h(R/M)==PIN;m=read(R/M);assert len(m['files'])==1 and m['actual_runtime_readiness'] is False and m['root_authorization_created'] is False
 v=m['files'][0];assert v['path']=='scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py' and v['source']=='.local/collect_terminal_20261020T1949/development_gateway/revision01/gateway.py' and v['sha256']=='873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb' and v['publish_R'] is True and v['publish_P'] is False
 src=R/v['source'];dst=R/v['path'];assert src.resolve()==src and dst.resolve()==dst and not any(x.is_symlink() for x in [src,*src.parents,dst,*dst.parents]);assert h(src)==v['sha256'] and src.stat().st_size==v['bytes'];compile(src.read_bytes(),str(src),'exec')
 frozen=read(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json')['files'];assert len(frozen)==173 and v['path'] not in frozen
 for n,pin in frozen.items():assert h(R/n)==h(P/'snapshots/formal_main_v2_run_564be0995e'/n)==pin
 old='scripts/ops/formal_action_deployment_posttraining_v1/gateway.py';assert h(R/old)=='4a11a62e817cd96523cd8f06aa0c3c71e12208f1b3a6b487799160915e59ec83'
 existed=dst.exists()
 if existed:assert dst.read_bytes()==src.read_bytes()
 record(R/B/'k64_gateway_source_publication_intent.json',{'manifest':{'path':M,'sha256':PIN},'state_before':before,'GPU_authority':False})
 dst.parent.mkdir(parents=True,exist_ok=True)
 if not existed:dst.open('xb').write(src.read_bytes())
 assert h(dst)==v['sha256'] and h(st)==before
 record(R/B/'k64_gateway_source_publication.json',{'status':'exact_source_only_published','source':v,'already_exact':existed,'state_unchanged':True,'frozen173_unchanged':True,'old_collect_gateway_unchanged':True,'runtime_admitted':False,'new_jobs':0})
 print(json.dumps({'status':'source_only_published','receipt':B+'/k64_gateway_source_publication.json','sha256':h(R/B/'k64_gateway_source_publication.json'),'new_jobs':0}))
