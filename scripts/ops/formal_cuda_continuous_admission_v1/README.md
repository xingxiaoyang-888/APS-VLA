# 已恢复 CUDA pair 的一次连续续跑入口

仅适用于 Object256 seed23、原失败3028460与恢复3039258。固定500步真实断点，目标5000、软时限169200秒、48小时分配；11次验证和全部科学源保持原字节。默认只读；实际提交需两个显式标志及完整实时门。

授权：configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json。来源与独审、实际 canonical preflight 在 results/formal_main_v2/preflight/heartbeat_20261019T1911。保留6596 GPU秒历史；两份resume仅先验SHA复核，实际恢复由原训练器完整加载optimizer/RNG/cursor。

正常控制器不接管该失败历史；入口只执行一次，保留blocked与Spatial预留槽。不确定提交保留全局pending，不可删除或重试。若软时限后仍未完成或异常，root重新核验；最终5000须root与独审后显式继承完成身份。不能靠清空blocked重新进入正常控制器。
