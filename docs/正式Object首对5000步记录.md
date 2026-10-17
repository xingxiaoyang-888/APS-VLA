# Object首对正式5000步验收

2026-10-18，北京时间。`formal_main_v2` 的 Object、总128 tokens、seed17，A/B均完成5000更新；十段原始训练、11次完整验证、独立审计及服务器实际选中权重SHA均通过。正式累计完成4/72组；本记录只确认训练完成，不代表未来监督取得闭环或延迟收益。

| 方法 | 按预定验证规则选中更新 | 任务等权硬teacher L1 | best.pt SHA256 |
|---|---:|---:|---|
| A | 2500 | 0.024357639637494842 | `bc390e912c760480309a8591d3d7d11a1b1a596851bbba5c934a7d9d7b989a43` |
| B | 4500 | 0.02449570353150309 | `926fa0d35d69dad26ce95ce1fe0142d7ccda176bdf86c29e3f034e4f16543ce4` |

每臂40000次窗口使用、40000个唯一窗口；完整合法训练池44068个，实际遍历量0.907688次。A/B初始化和完整样本顺序相同，恢复游标均40000，无训练失败或恢复重放。验证固定11×204个窗口，选模按任务等权硬teacher L1，平分取更早更新；没有依据结果改方法或增加训练。

十个Slurm分配合计41618 GPU秒（11.560556小时），包含加载、缓存、前反向、验证及保存；最后一段3021103为4226秒，已包含在总数中，不另加。峰值CUDA allocated显存A为18222259712字节、B为18231945216字节；这不是推理显存或完整成本替代值。

权重仅在服务器：`/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_object/k128/seed17/{A,B}/best.pt`。终态不再续训至5500；下一步按固定开发初态进行接口及闭环评测。全部最终初态继续封存，须满足全局72选择器、16参考和四套件开发门槛后再开放。

证据：[根审计](../results/formal_main_v2/libero_object/k128/seed17/training/segment_reviews/3021103.json)、[独立审计](../results/formal_main_v2/libero_object/k128/seed17/training/segment_reviews/3021103_independent.json)、[实际服务器best SHA](../results/formal_main_v2/libero_object/k128/seed17/training/segment_reviews/3021103_selected_server.json)、[稳定回存](../results/formal_main_v2/pulls/20261017T225221Z_33861bca4729/receipt.json)。
