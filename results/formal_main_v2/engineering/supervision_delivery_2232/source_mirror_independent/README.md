# 源镜像交付独审

精确helper SHA36c6981e…通过13项隔离CPU检查。173份canonical源共1664859字节完整复原，重复恢复及verify-only不改已有文件；错误inventory/source/target、源或目标symlink和父目录symlink、路径逃逸均拒绝。既有错误目标没有被覆盖。

仅写本目录隔离fixture与报告，真实源/镜像/入口/state/Git/Slurm未改，未读权重或封存值。重建器是原canonical字节的复原，不冒称重新取得服务器原始证据。

调用范围为正常python -B（非-O、无PYTHONOPTIMIZE）；代码的assert检查依赖__debug__。这不是对敌对并发文件系统改写的隔离保证。

交付只取archive_closure列出的顶层文件；isolated/及foreign/是测试副本，禁止随Git归档。真实canonical源码、原映射和helper由root正常交付。
