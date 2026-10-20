独立 CPU 审查通过；不授权提交。

15 项独立检查全部通过，包括真实 Git 旧/新 bytes、唯一 717 字节操作说明增补、精确历史 proof/path/SHA 负例、当前文档/绑定漂移拒绝、v1 授权拒绝，以及原 reviewer + NativeIO 真实只读重建。R/S 173 科学源一致，P/S 213 项元数据与两份 resume 文件哈希通过；未加载 checkpoint tensor、未恢复优化器或 RNG。

候选反变换可逐字节还原 v1 admission/gateway。只桥接指定独审收据中指定文档旧 SHA；其他证据和当前文档仍严格校验。历史失败、root/独审原件、11958 GPU 秒及其中失败 73 秒保留。

源码可以按 publication_map 原字节发布；仍需 root 的新 v2 授权和实际提交前现成全量门槛。没有调用 Slurm，没有修改生产 state/源码/Git/P，没有发布 invocation，不代表 GPU 恢复成功或当前容量可用。

交付 archive_closure.json 所列顶层文件及独立 transport 日志。isolated/ 仅负例测试隔离副本，不归档至 Git。完整命令在 run_a1_command.json；原 stdout/stderr 未改。
