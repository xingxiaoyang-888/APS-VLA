LIBERO-Long 使用自己的输入预验收和 F01，不借用 Spatial G0 或 Spatial 选择器。此规范不预写验收成功。

固定模型为 `moojink/openvla-7b-oft-finetuned-libero-10@95220f9a3421a7ff12d4218e73d09ade830fa9a3`；suite=`libero_10`，stats key=`libero_10_no_noops`。配置为 `configs/experiments/g1_future_long_v1.json`，数据仅从独立 `long_future_v1/protocol.json`、`windows.json` 读取。

预验收在冻结 windows 中按官方 task IDs 0/3/5 各取一个 train window：通过 protocol 的 task_catalog 映射到 instruction，再按 `(episode_id,start_step,window_id)` 取最小。只用元数据确定样本，不看图像或结果、不补采 episode、不打开 test。每条仅检查当前帧及该窗口既有的 8 个示范动作。

每帧比较固定 OFT 官方纯函数与共享入口的双视角 JPEG/Lanczos/crop、prompt/token/mask、Long proprio bounds 归一化；像素和 token 必须完全相等，proprio 最大误差≤1e-6。另将 RLDS 已旋转图像翻转回原相机布局，验证 raw-camera 路径与已旋转 RLDS 路径一致；这是 RLDS 派生的相机方向探针，不冒称新采集的模拟器观测。示范动作使用 Long checkpoint 统计，核查原生 gripper 变换、mask、常量维和 bounds 逆变换。

同一输入下执行官方 public `vla.predict_action` 与共享 dense token policy；从官方返回 action hidden states 捕获 normalized actions，并核对原生 physical actions。normalized 最大差≤0.002；共享与官方动作后处理一致、两路径夹爪一致。固定共 3 帧、6 次动作策略前向、6 次双视角视觉骨干前向；动作头重读不额外计作完整 VLA 前向。

独立阶段名为 `G1-F00-input-parity`，不产生或伪造 G0。源码、官方 reference 文件、配置、协议、窗口、模型清单及实际统计文件身份均记录；开始和结束校验基础权重，全部完成且权重不变后才写 passed。逐次模型调用先写 durable start，完成同步后写 complete；失败/未知尝试保留，结果目录不可覆盖。完整 Slurm 占用另计，计时不当作部署延迟。

Long F01 必须读取上述原始 receipt，并精确匹配当前源码、配置、窗口、协议及资产；F01 再验证真实冻结 VLA 的动作/未来梯度、参数字节不变、dense/hard128 packing。后续训练必须读取 Long 自己 finalized F01，不能用 Spatial 报告或单个布尔字段放行。A/B 均从共同 seed17 初始化重新训练；保持 100 updates、90 train/60 validation、h8、λ=0.1、每相机64，不扩额外闭环验收。
