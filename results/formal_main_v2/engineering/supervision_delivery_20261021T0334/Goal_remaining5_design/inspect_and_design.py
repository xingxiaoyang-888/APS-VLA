from pathlib import Path
import collections, datetime, hashlib, json, re, time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/goal_remaining5_design_20261021T0334'
TARGETS=[(256,23),(256,41),(64,17),(64,23),(64,41)]
checks=[]
def require(ok,msg):
    checks.append({'name':msg,'passed':bool(ok)})
    if not ok:raise RuntimeError(msg)
def h(raw):return hashlib.sha256(raw).hexdigest()
def hashfile(p):
    before=p.stat();x=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):x.update(b)
    require(before==p.stat(),'stable bytes '+str(p))
    return x.hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p),'bytes':p.stat().st_size,'sha256':hashfile(p)}
def save(name,v):
    with (D/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
def check_ref(x):
    p=R/x['path'];require(hashfile(p)==x['sha256'],'exact evidence '+x['path']);return read(p)
def main():
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    state_raw=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(state_raw);fp=state['formal_main_progress'];jobs=state['registered_jobs']
    with (D/'state_snapshot.json').open('xb') as f:f.write(state_raw)
    source_rel='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';source=read(R/source_rel)
    require(source['source_sha256']=='dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e' and len(source['files'])==173,'frozen173 inventory')
    source_checks=[]
    for rel,pin in source['files'].items():
        require(hashfile(R/rel)==pin and hashfile(S/rel)==pin,'frozen R/S '+rel);source_checks.append({'path':rel,'sha256':pin,'R_and_S_verified':True})
    panel_rel='configs/manifests/formal_main_v2/libero_goal/initial_states/development.json';panel=read(R/panel_rel)
    require(hashfile(R/panel_rel)=='ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9' and hashfile(P/panel_rel)==hashfile(R/panel_rel),'exact development panel R/P')
    require(panel['split']=='development' and panel['suite']=='libero_goal' and len(panel['states'])==100 and panel['environment_seed']==0,'Goal100 development only')
    require(collections.Counter(x['task_id'] for x in panel['states'])==dict.fromkeys(range(10),10),'ten fixed states each task')
    state_order=[{k:s[k] for k in ('trial_id','task_id','task_name','source_state_index','initial_state_sha256','source_file')} for s in panel['states']]
    common={
      'registration':ref(R/'configs/experiments/formal_main_v2.json'),'source_inventory':ref(R/source_rel),'source_sha256':source['source_sha256'],'source_root':str(S),'source173_R_and_S_verified':True,
      'development_panel':ref(R/panel_rel),'development_content_signature':panel['content_signature'],'development_order_sha256':h(json.dumps(state_order,sort_keys=True,separators=(',',':')).encode()),'development_states':state_order,
      'protocol':ref(R/'configs/manifests/formal_main_v2/libero_goal/protocol.json'),'windows':ref(R/'configs/manifests/formal_main_v2/libero_goal/windows.json'),
      'official_asset_manifest':ref(R/'configs/assets/openvla_oft_libero_goal.json'),'strict_asset_manifest':ref(R/'configs/assets/formal_main_v2_strict/libero_goal.json'),
      'input_acceptance':ref(R/'results/formal_main_v2/libero_goal/acceptance/attempt03/input_acceptance.json'),
      'environment':{'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':300},
      'fixed_training':{'updates_per_arm':5000,'batch':8,'horizon':8,'lambda_B':0.1,'budgets':[256,128,64],'seeds':[17,23,41],'arms':['A','B'],'search':False},
      'base_model_revision':'c2d0f9fbbd82674683b397ff923168a12f6a307b','base_model_frozen_sha256':'85703124930f24771cd4d04a4e88309710fcfc230e4891a1e6578d7ec14a45a2',
      'base_weight_files_not_rehashed':'Base identity inherits original input acceptance and root training terminal evidence; no base model weight bytes copied or reloaded.'}
    accepted=[]
    for job_id,n,kseed in [('3048609',600,17),('3049191',200,23),('3049622',200,41)]:
        accepted_row=fp['new_action_development_verified_by_job'][job_id]
        require(accepted_row['suite']=='libero_goal' and accepted_row['completed_trials']==n,'registered accepted Goal128 '+job_id)
        root_review=check_ref(accepted_row['root_review']);ind=check_ref(accepted_row['independent_review'])
        require(root_review['job_id']==job_id and root_review['suite']=='libero_goal' and root_review['completed_trials']==n and root_review['scientific_complete'] is True,'actual original root review '+job_id)
        require(job_id in json.dumps(ind),'independent report contains exact job '+job_id)
        j=next(j for j in jobs if j['job_id']==job_id);inv=check_ref({'path':j['invocation'],'sha256':j['invocation_sha256']})
        require(inv['stage']=='development' and inv['suite']=='libero_goal' and inv['method_ids']==j['method_ids'],'accepted exact invocation '+job_id)
        accepted.append({'job_id':job_id,'budget':128,'seed':kseed,'completed_trials':n,'methods':j['method_ids'],'root_review':accepted_row['root_review'],'independent_review':accepted_row['independent_review'],'invocation':{'path':j['invocation'],'sha256':j['invocation_sha256']},'root_status':root_review['status'],'does_not_authorize_other_pair':True})
    require(sum(x['completed_trials'] for x in accepted)==1000,'Goal128 accepted1000')
    # Bounded published development search, no final registry/state values.
    published={}
    for label,root in [('R',R),('P',P)]:
        invs=[]
        for p in sorted((root/'results/formal_main_v2/invocations').glob('libero_goal_development_*.json')):
            x=read(p);require(x['suite']=='libero_goal' and x['stage']=='development','published development invocation scope')
            invs.append({'path':p.relative_to(root).as_posix(),'sha256':hashfile(p),'methods':x['method_ids'],'stage_key':x['stage_key'],'run_root':x['run_root']})
        manifests=[]
        for p in sorted((root/'results/formal_main_v2/execution').rglob('*libero_goal*development.json')):
            x=read(p);require(x['suite']=='libero_goal' and x['split']=='development','published manifest development scope')
            manifests.append({'path':p.relative_to(root).as_posix(),'sha256':hashfile(p),'methods':[m['identity']['method_id'] for m in x['methods']]})
        published[label]={'invocations':invs,'execution_manifests':manifests,'run_directories':sorted(p.name for p in (root/'results/formal_main_v2/libero_goal/downstream/development').iterdir())}
    require(published['R']==published['P'],'R/P published Goal development inventories exact')
    require(len(published['R']['invocations'])==4 and len(published['R']['execution_manifests'])==4 and len(published['R']['run_directories'])==4,'known four historical Goal development runs')
    matrix=[]
    for budget,seed in TARGETS:
        key=f'libero_goal_k{budget}_seed{seed}';pair_rel=f'configs/experiments/formal_main_v2/{key}.json';cfg=read(R/pair_rel)
        require(cfg['suite']=='libero_goal' and cfg['seed']==seed and cfg['tokens_per_camera']*2==budget and cfg['training']['updates']==5000 and cfg['training']['effective_batch']==8 and cfg['future']['horizon']==8 and cfg['future']['weight_B']==0.1,'frozen pair scientific settings '+key)
        require(hashfile(R/pair_rel)==source['files'][pair_rel] and hashfile(P/pair_rel)==source['files'][pair_rel],'pair config original bytes R/P/S '+key)
        base=f'results/formal_main_v2/libero_goal/k{budget}/seed{seed}/training';summary=read(R/base/'training_summary.json');completion=fp['completed_training_pairs'][key]
        require(summary['pair_complete'] is True and summary['planned_updates_per_arm']==5000 and summary['status']=='completed' and summary['test_opened'] is False,'pair completed train '+key)
        completion_refs={}
        for role in ('root_review','independent_review','selected_server_review'):
            if role in completion:
                x={'path':completion[role],'sha256':completion[role+'_sha256']};check_ref(x);completion_refs[role]=x
        arms=[];pair_ids=set()
        for arm in ('A','B'):
            path=R/base/arm/'deployment_receipt.json';receipt=read(path);meta=receipt['metadata'];summ=summary['arms'][arm]
            require(receipt['training_complete'] is True and receipt['completed_updates']==receipt['planned_updates']==5000 and receipt['base_frozen'] is True and receipt['checkpoint_unchanged'] is True,'full deployment receipt '+key+arm)
            require(receipt['pair_config']==cfg and meta['suite']=='libero_goal' and meta['arm']==arm and meta['seed']==seed and meta['visual_tokens']==budget and meta['per_camera_budgets']==[budget//2]*2,'exact pair receipt '+key+arm)
            require(meta['model_revision']==common['base_model_revision'] and meta['frozen_model_sha256']==common['base_model_frozen_sha256'] and meta['data_protocol_sha256']==common['protocol']['sha256'] and meta['window_manifest_sha256']==common['windows']['sha256'] and meta['input_acceptance_sha256']==common['input_acceptance']['sha256'],'common assets/data/input identity '+key+arm)
            require([x['update'] for x in receipt['evaluations']]==list(range(0,5001,500)),'all11 validation nodes '+key+arm)
            selected=min(receipt['evaluations'],key=lambda e:(e['validation_metric'],e['update']))
            require(selected['update']==meta['update']==summ['best_update'],'earliest minimum selection retained '+key+arm)
            cp=Path(summ['best_checkpoint']);selected_state=next(x for x in completion['selected_checkpoints'] if x['arm']==arm)
            require(str(cp)==selected_state['path'] and hashfile(cp)==summ['best_checkpoint_sha256']==receipt['checkpoint_sha256']==selected_state['expected_sha256'],'selected checkpoint bytes actual server '+key+arm)
            require(hashfile(P/base/arm/'deployment_receipt.json')==hashfile(path),'receipt exact R/P '+key+arm)
            for rel,pin in meta['training_source_files'].items():require(hashfile(S/rel)==pin,'training source '+key+arm+' '+rel)
            pair_ids.add(meta['pair_id'])
            arms.append({'arm':arm,'method_id':f'{arm}{budget}_seed{seed}','selected_update':meta['update'],'checkpoint':{'path':str(cp),'bytes':cp.stat().st_size,'sha256':receipt['checkpoint_sha256'],'actual_server_bytes_verified':True},'deployment_receipt':ref(path),'deployment_metadata_sha256':receipt['metadata_sha256'],'training_config_sha256':meta['config_sha256'],'training_source_sha256':meta['training_source_sha256'],'selection_protocol_sha256':meta['selection_protocol_sha256'],'f01_report_sha256':receipt['f01_report_sha256'],'input_version':meta['input_version'],'packing_version':meta['packing_version']})
        require(len(pair_ids)==1,'same A/B pair id '+key);pair_id=next(iter(pair_ids));methods=[f'A{budget}_seed{seed}',f'B{budget}_seed{seed}']
        matches=[{k:j.get(k) for k in ['job_id','mode','status','stage_key','method_ids','pair_id','invocation','invocation_sha256']} for j in jobs if j.get('mode') in ('development','engineering','collect','profile','full_profile','component_profile') and (j.get('pair_id')==pair_id or bool(set(j.get('method_ids') or [])&set(methods)) or (j.get('suite')=='libero_goal' and j.get('visual_tokens')==budget and j.get('training_seed')==seed))]
        invmatches=[x for x in published['R']['invocations'] if bool(set(x['methods'])&set(methods))]
        manmatches=[x for x in published['R']['execution_manifests'] if bool(set(x['methods'])&set(methods))]
        require(not matches and not invmatches and not manmatches,'no registered/published prior development for '+key)
        matrix.append({'pair_key':key,'budget':budget,'seed':seed,'pair_id':pair_id,'method_ids':methods,'expected_trials':200,'unique_development_states':100,'planned_scientific_matrix_source':ref(R/pair_rel),'training_summary':ref(R/base/'training_summary.json'),'training_terminal_job_id':completion['job_id'],'training_terminal_evidence':completion_refs,'arms':arms,'registered_development_jobs':matches,'published_invocations':invmatches,'published_execution_manifests':manmatches,'per_pair_execution_plan_already_frozen':False,'current_state':'IDENTITIES_VERIFIED_EXECUTION_HOLD','missing':['new exact per-pair development execution manifest and original-planner scientific plan','new per-pair prospective observer/gate/consumer binding and full source closure','root + independent source/CPU review and actual-P metadata/source/capacity verification','fresh all-mode scheduler/pending/owner and storage admission, unique held ACK transaction'],'maximum_attempts_proposed':1,'max_total_control_steps':60000,'max_total_policy_queries':7600,'new_execution_authorized':False})
        print(json.dumps({'pair':key,'selected_updates':[a['selected_update'] for a in arms],'checkpoint_sha256':[a['checkpoint']['sha256'] for a in arms],'existing_development_jobs':matches}),flush=True)
    current_job=next(j for j in jobs if j['job_id']=='3054717');obs_ref={'path':'results/formal_main_v2/preflight/heartbeat_20261021T1134/initial_observation.json','sha256':'0c0520630396e633c5b417a401da18bd100974e79d5f962308cf892bd945ac41'};check_ref(obs_ref)
    pending200={'job_id':'3054717','budget':256,'seed':17,'expected_trials':200,'unique_development_states':100,'registry_status_snapshot':current_job['status'],'known_saved_terminal':'COMPLETED 0:0 / 2205 GPU seconds','saved_observation':obs_ref,'scientific_admission_by_this_design':False,'root_terminal_acceptance_pending_separate_process':True,'historical_original200_job_id':'3049679','historical_original200_remains_HOLD':True,'authorization':{'path':current_job['invocation'],'sha256':current_job['invocation_sha256']},'runtime_package_manifest':ref(R/'scripts/ops/formal_goal_full200_gate_v1/package_manifest.json'),'dispatch_scope':ref(R/'scripts/ops/formal_goal_full200_dispatch_v1/scope.json'),'must_not_reuse_original_ACK_or_authorization_for_other_pair':True}
    runtime_files=read(R/'scripts/ops/formal_goal_full200_gate_v1/package_manifest.json')['files'];bindings={}
    for rel,pin in runtime_files.items():
        require(hashfile(R/rel)==pin and hashfile(P/rel)==pin,'current exact runtime R/P '+rel)
        txt=(R/rel).read_text();bindings[rel]={'sha256':pin,'operational_literals_present':[x for x in ('goal_full200_20261021T0110','A256_seed17','B256_seed17','k256/seed17','ORIGINAL','STAGE','RAW=') if x in txt]}
    report={'schema':'formal_main_v2','kind':'Goal_remaining_five_pair_CPU_design','status':'bounded_identity_design_complete_execution_HOLD','observed_utc':started,'state_snapshot_sha256':h(state_raw),'accepted_Goal128_trials':1000,'accepted_Goal128_AB_trials':600,'accepted_shared_reference_trials':400,'accepted_Goal128':accepted,'new256seed17_terminal_pending_separate_acceptance':pending200,'remaining_pair_count':5,'remaining_expected_trials':1000,'remaining_pairs':matrix,'common':common,'published_evidence_search':published,'pending_submission_snapshot':state.get('pending_submission'),'autonomous_pending_submission_snapshot':state.get('autonomous_training_v1',{}).get('pending_submission'),'source173_R_S':source_checks,'current_full200_binding_scan':bindings,'fresh_scheduler_observation_performed':False,'limitations':['No new selected-model inference or environment run.','No existing execution plans for the five pairs were found in the exact R/P published Goal development namespaces; frozen scientific pair configs/selected training receipts exist.','Absence of registered/published attempts is scoped to saved state and bounded R/P metadata inventory; a fresh full-mode scheduler/ACK check is mandatory before submission.','3054717 terminal science remains a separate root+independent decision; this design does not pre-admit its200 or reuse its authorization.'],'new_trials':0,'new_GPU_jobs':0,'production_ready':False,'sealed_final_values_read':False}
    save('design.json',report);save('verification_checks.json',{'status':'passed','count':len(checks),'checks':checks,'scope':'CPU identity and saved evidence only; not actual-P new runtime admission'})
    lines=['# Goal 剩余五 pair：CPU 证据矩阵与下一轮最小集成门槛','','这是设计和身份核对，不是提交授权。已冻结归档包和已有 runtime/dispatch 均未修改。','',f"状态快照 SHA：{h(state_raw)}。已验收 Goal128 三 seed 共 1,000 条，其中 A/B 为 600、四参考为 400。3054717 新256seed17 200条虽已有已保存 COMPLETED 0:0 / 2205 GPU秒，仍由 root 与独审另行准入；旧3049679 200条不转为已接纳。",'','|剩余 pair|A选中更新|B选中更新|原开发提交|待执行数|','|---|---:|---:|---|---:|']
    for x in matrix:lines.append(f"|Goal {x['budget']} / seed{x['seed']}|{x['arms'][0]['selected_update']}|{x['arms'][1]['selected_update']}|登记与 R/P 精确发布目录均未发现|200|")
    lines+=['','五 pair 的冻结 pair config、5000训练双终验、部署收据、全部11验证节点与原最早平分选模均核对；10份 best.pt 在服务器流式复算 SHA，与原 root/独审登记及 receipt 一致，不复制权重。R/S 的173份冻结源逐字节通过。完整开发100初态的原文件、顺序、10任务每任务10初态身份一致；不读 final 值。','',
'## 缺少的计划，不补造',
'目前 R/P 正式 execution/invocations 下只有 Goal128 三个开发计划及 Goal256seed17 旧计划，其他五 pair 尚没有独立 execution manifest / scientific plan / invocation / ACK。design.json 里的 planned_scientific_matrix_source 指向原冻结训练科学配置，不冒充已发布的下游计划。下一轮应先用原已审 planner、原 deployment identity builder 为每个固定 A/B pair + 同100初态构建各200条明确清单，再冻结其原始字节与执行身份。',
'',
'## 操作性绑定须新增，原入口保持专用',
'现 formal_goal_full200_gate_v1 和 dispatch_v1 专属 3054717。entry/config/specification/paired_input_gate/consumer/storage/run.slurm、dispatch scope/prepare admission 各自包含 stage、method IDs、seed、budget、pair_id、原 invocation、checkpoint、raw/output 路径、授权/审计/容量收据和唯一 comment/token 绑定。必须在新受审包逐项绑定五个精确目标，不能运行时替换全局常量或改旧包。原五 pair 没有历史开发 invocation，不能复用 c07489c5... 伪作各 pair 的原调用。',
'两个 AST 转换器当前无 seed/budget 字符串，仅可在源码/代码对象/回调闭包独审后原字节继承；observer 与 five-component gate 的方法映射、全输入采集和相应限额也须测试新 pair，不能因为函数名相同就继承 GPU 验收结论。原控制循环、动作/clip、预处理、packing、action slice、环境/RNG调用规则及300步/chunk8保持不变。',
'',
'## 每 pair 最小门槛',
'1. 根与独立终验先结束3054717原200的准入；为剩余五 pair 明确新受审 scope 和保留所有既往失败/成本，不据结果改 checkpoint、初态、方法或预算。',
'2. 科学输入：固定本 pair A/B100状态各一次；原开发面板 SHA、官方Goal基座、原 selected checkpoint SHA、F01、训练/数据/来源桥完整核对；没有 source bridge 就 HOLD，不能套别 pair。source173原字节不改。',
'3. 执行：保留完整原执行 manifest 与原 parser/scientific guard；每 pair 独立 fresh reset / ledger，不普通恢复3054717或58工程。每 pair 最大200 trial、60000控制步、7600 query、一次尝试；新结果不能触发重试。历史动作不注入，异常立即停止并保留。',
'4. AST/运行期闭包：核 original / derived loop、adapter.run、policy 方法、回调函数与 source code SHA。强制预调用与调用后五组件完整输入、sim/RNG记录及t0跨A/B门控；非t0空数组、缺一组件、错类型/shape、错内容地址、synthetic标志、额外/漏事件一律拒绝。',
'5. 终态：原 consumer 完整执行模型/config/checkpoint/data/轨迹和ledger核验，再typed observer/gate逐条重建。新增消费者实际接受 mode=development、run_root=<attempt>/original_run 的真实登记；必须做 registration→consumer.validate_job 跨入口CPU测试，不能终验临时修改 job 或信布尔通过。',
'6. 发布：完整新 source closure、root/独审源码CPU收据、精确 R/P 安装映射、实际P --verify、不可变 readiness 和 root authorization 齐全后才能提交；旧已通过 receipt 只证明其旧范围。',
'7. 容量：提交与计算节点两次实际检查 R 五组件与 P 元数据/被动blob空间；每pair独占内容地址 claim，无未来去重信用。按5个新attempt的并行 worst-case 预算核全量容量，不能按3054717短轨迹实测放宽每pair上限。',
'8. 提交：共享 writer.lock + CAS，root pending 与 autonomous pending 双拒绝；控制器生命周期lease、全部模式GPU合计最多8及Goal pair占用校验。新唯一token/output、held sbatch→持久原ACK→精确sacct/comment/name/account/output/原argv核验→同锁登记→唯一release；不确定提交/release只能精确原ACK对账，不能清pending重发。不同pair不共享ACK或授权。',
'9. 验收与成本：每pair完整原始P→R allowlist、五组件/被动blob内容地址可恢复归档、root+不同agent终验齐后仅新增200。保存每个失败/工程/加载与全部Slurm分配并且只计一次；未完成/失败或缺证据不得记成功率分母。',
'10. 最终和测速：五pair完成也不自动开放 final 或 O2A。仍需72checkpoint、16参考、四套件开发收据和最终清单全局冻结与root release；本设计不读取封存值、不泛化到其他套件/预算/种子/方法。',
'',
'精确源、路径、原始SHA、checkpoint SHA、pair_id、已验收收据和缺失项见 design.json。verification_checks.json 只证明此次CPU身份核验。fresh Slurm查询、实际P的新入口验证和任何GPU运行均未执行。']
    with (D/'README.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    files=[]
    for p in sorted(D.iterdir()):
        if p.is_file() and p.name!='delivery_manifest.json':files.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashfile(p)})
    save('delivery_manifest.json',{'schema':'formal_main_v2','kind':'Goal_remaining5_CPU_design_delivery','root':D.relative_to(R).as_posix(),'file_count':len(files),'files':files,'production_ready':False,'new_trials':0,'new_GPU_jobs':0})
    print(json.dumps({'status':report['status'],'checks':len(checks),'design_sha256':hashfile(D/'design.json'),'manifest_sha256':hashfile(D/'delivery_manifest.json'),'file_count':len(files)}),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:
        save('failure_'+str(time.time_ns())+'.json',{'status':'failed','exception_type':type(e).__name__,'message':str(e),'checks':checks,'new_GPU_jobs':0});raise
