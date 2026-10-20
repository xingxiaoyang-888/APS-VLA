# Goal t0 异常取证（只读，未启动新实验）

原3049679的200条继续HOLD。probe3050711未复现原A的97bfd36f…，原因未定；不能部署修复、放宽hash门槛或补认原结果。

- 原异常A/B是第57/58条。此前56条累计916次策略query、7124个策略控制动作、560等待动作。原入口和探针均每条重设seed、新建并关闭环境；不能归因为环境复用。
- 原t0 hash在predict_chunk返回后、第一策略动作前记录。没有原prequery和逐数组原件，不能判定差异来自reset/等待/query，更不能由此断言模型改了输入。
- 探针12query/120dummy/0policy，所有pre/post均5967f63a…，与原B相同；未重演前56条历史。AB/BA只平衡query/reset顺序，加载顺序仍A后B。
- 同arm比较：原B和6次probeB首chunk完全一致；原A和6次probeA的token、全部metadata相同，但归一化动作最大差0.00390625、环境动作最大差0.0035470145716998136。token相同不等于输入/动作相同，不用于成功率判断。
- 两次配置同seed17/envseed0、256相机、wait10/chunk8、相同checkpoint；OMP/BLAS/MKL/TF配置相同。原gpu4025、探针gpu4023不同仅为事实，不证明节点原因。原实际线程数、reset内部重试未记录。共同reset源码的finally:continue不能证明原来发生了重试。

下一步仅建议：一次1GPU、最长30分钟、固定前58条（29个已用开发初态、原顺序，含异常A/B），计入8槽，不自动重试。沿原闭环策略实际产生动作，不强制历史动作或终止结果；是同源入口和顺序的前缀重执行，不能称为实际轨迹逐动作重放。记录首个历史偏离以及reset/set_init/等待/t0query前后五数组、sim/RNG和身份。observer经CPU/AST及GPU被动性检查，不新增render/step/query/随机调用，仍须承认时间扰动；不把该运行用于测速。

pre一致而post变化才支持输入修改方向；pre已不同先定位reset/等待。图像单独变化也不可视为无害。未复现/超时/证据不足均继续HOLD，无自动科学重跑。具体草案见proposed_single_attempt_registration.json，尚未授权或执行。原200不会因为probe通过而补认。

836项CPU证据检查通过，含173文件R/S前后核验；新GPU成本0。原2034秒及probe354秒已计成本，不重复累计。来源SHA见pinned_inputs.json，原前缀见original_prefix58.json。未读取封存值/权重，未改变状态、canonical、Git或Slurm。
