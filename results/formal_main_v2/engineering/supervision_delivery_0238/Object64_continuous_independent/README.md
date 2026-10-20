Object64 seed23 连续入口独审通过；本收据不是 root 提交授权。

候选 admission.py 6598fa7311b076bdff079e0f09ed58216650eb35b7b6f532a7960c3673c5616f；gateway.py 2aaed25efd1d8783ace9ace93a5212f67b52f1d1a6fde1072349d8d8a830f54a。可按同字节复制到 scripts/ops/formal_object64_cuda_continuous_admission_v1/。

15 项独立检查通过。真实原 reviewer 重建、211 项 P/S 非权重元数据、两份 resume 文件稳定 SHA/bytes 均通过；未反序列化 tensor、未恢复优化器或 RNG、未跑 GPU。作者55项CPU与其metadata prepare单独引用，未冒称其读取checkpoint。

保留原失败3028468的69秒与恢复3044017的5141秒，总5210 GPU秒；A/B从500/cursor4000续到5000。Object metadata wrapper、冻结173科学源、损失/种子/11验证节点、锁/owner/lease/CAS/pending/容量门不变。replay=0 检查保留，并补 unique_samples=4000 和原冷启动False。

post-ACK accounting缺行、预约占满、CAS漂移等测试仅在 isolated/ 的明确 synthetic fixture执行；无真实Slurm调用。原脚本首次执行前修正一处fixture，使queue保留、仅sacct延迟；旧脚本原件保留。

root仍须签新精确授权，未来空槽运行原fresh gate。旧失败和blocked历史保留，异常不自动重发。交付 archive_closure.json 顶层文件；isolated/仅可重建测试副本，不进入Git。
