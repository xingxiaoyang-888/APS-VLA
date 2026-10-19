# Spatial64 seed23 连续入口独审

结论：最终两份候选通过有限 CPU 独审，可由 root 原字节发布后签署一次性准入。尚未提交或执行1500→5000。

- 14项独立定向 CPU 检查通过；作者45项仅作为继承证据。正交易使用隔离 synthetic fixture，不能当作真实作业。
- 实际调用原 Science/reviewer 和 NativeIO：487项来源、213项P/S输入、两个resume实际SHA通过。未反序列化checkpoint，未恢复optimizer/RNG。
- 四次分配11958 GPU秒完整保留（含失败73秒）；A/B均1500、cursor12000。5000调度、每500验证和每50恢复点不变，使用原Spatial Slurm wrapper。
- 两个早期finalization仅以精确路径/SHA/bytes、原failure archive和唯一pull ownership补入严格清单；未扩大目录豁免。
- 实际unsigned draft仍拒绝。现存controller、blocked记录和其他预约保留；未来提交需root新签授权及空闲非预约槽的完整实时复核。
- accounting传播延迟会保留known pending并拒绝再次提交，需对账原作业，不能重发。
- 一次独审runner引号语法失败原件保留，未运行候选；只修runner后14项和实际桥接通过。
- 本目录不含state/P/Slurm修改、封存值或权重副本。所有pytest隔离副本不进入交付包；仅归档顶层代码、原日志、XML、收据。
