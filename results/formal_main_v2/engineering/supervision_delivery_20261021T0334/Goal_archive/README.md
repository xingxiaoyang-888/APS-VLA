# Goal3054717 非权重终态精确归档

仅准备和验证归档；不做科学终验、成功率统计或新试验。复用 root 已保存的 COMPLETED 0:0 / 2205 GPU 秒证据，不另查 Slurm，不写 state/Git/P 或冻结源。

- inventory.json 是不可变事件引用清单，SHA db4d8a05cd7f21af5aac0687d2190297cd571eb1a6ffc83eb74d235d53eb7ac1。逐唯一 blob 实际调用原 consumer.read_blob，核文件名内容地址、bytes、SHA、无 symlink；事件所有引用与两个源目录精确相等。
- R 五组件开发观测：19,540 blob / 1,544,833,664 B；R claim.json：360 B。它们本来已在 R，不需 P→R 再复制。
- P 被动模拟器/RNG：15,522 blob / 4,014,813 B；P 原始元数据：13 项 / 131,283,146 B（含两零字节锁）。P_terminal_pull_allowlist.json 给出每项 P-relative / attempt-relative / bytes / SHA。root 拉取可显式排除两锁；归档保留用于完整还原。
- 全部 35,076 项 / 1,680,131,983 原始字节。volumes/ 共 24 卷，压缩总 573716185 B，最大 29237053 B；每卷严格小于 90 MiB。
- archive_manifest.json SHA 18c61e6a89047e7c4a0cdab7e6111f73a36db0421a3c2b1627a2f01944cf4d21。各卷成员索引精确引用 inventory，不通过 glob 把未知 .bin 加入 Git。R observations、P passive、P metadata 和 R metadata 分开归档。
- 归档采用 gzip + tar PAX（mtime=0，uid/gid=0，mode=0600）。创建后逐卷流式解压检验全部成员顺序/type/bytes/SHA，再由独立只读入口完整复核一次，均通过。原始文件未修改。
- CPU 容器测试 1 正例 / 22 拒绝，用两份已记录真实被动 blob 仅构造 tar 容器，拒绝损坏、错 SHA/size、重复/漏/额外成员、乱序、symlink、路径穿越。不是模拟器重跑或新科学结果。

## 精确恢复和审核

inventory.members[*].restore_root 只能是 R 或 P，restore_relative 是原文件相对根路径；archive_path 是卷内名字。恢复时先跑只读完整验证，再由 root 决定唯一目标；不得覆盖不同内容或从 tar 自行接受额外路径。本任务只流式验证，未向原路径解压。

可在原私有包或 root 发布后的完整目录运行只读检查（正常项目执行仍通过已审 transport，固定脚本 SHA e466661b2899ce289947867c2b44eeb280fd34a2ee15f48c7bb20721a3fea2d3）：

    python -B verify_archives.py --directory <完整归档包目录> --manifest-sha256 18c61e6a89047e7c4a0cdab7e6111f73a36db0421a3c2b1627a2f01944cf4d21

所有成员、卷、清单、脚本和恢复报告按 delivery_manifest.json 逐项 SHA 发布；不要把未压缩原始 .bin 直接加入 Git。provenance/ 保留原 58 条归档实现、当前 frozen consumer/observer/package、原保存 Slurm 观察及本次 transport 原日志。

本包不采纳 200 条科学结果，不改原失败/尝试历史，不开放 sealed final，不重复计 GPU 成本。科学终验由 root 和独立审核另行完成。
