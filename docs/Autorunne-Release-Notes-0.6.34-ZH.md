# Autorunne 0.6.34 发布说明

**状态：release candidate**

0.6.34 是状态可靠性补丁，不是产品重写。AI 进入仓库后，仍然能立刻看到项目做到哪里、当前任务和下一步；`.autorunne/views/*` 交接文件和现有命令保持不变。

在 GitHub tag、GitHub Release 和 PyPI 实际上传成功之前，这一版只能称为 **release candidate**。GitHub Release / PyPI 尚未发布。

## 这一版修了什么

- **并发写入串行化**：同一工作区的多线程、多进程状态读写会抢 `.autorunne/runtime/state.lock`。锁覆盖完整的 read-modify-write-render，不是只锁最后一次写文件。`timeout` 同时约束同进程线程等待和跨进程 OS 锁。同线程嵌套调用不会死锁。
- **JSON 原子替换和最近一次有效备份**：状态 JSON 先写同目录临时文件，再 `os.replace()`。只有当前主文件能解析时，才会把它的精确字节复制到 `*.bak`。损坏的主文件不会覆盖有效备份。
- **安全自动恢复**：主文件坏、备份好时，`open` 和 `doctor` 会把备份原子恢复回主文件，然后继续。
- **无有效备份时 fail closed**：主文件和备份都坏时，命令以非零退出，明确写出 `Autorunne state is corrupt` 和 `did not reset state`，并保留原文件字节。Autorunne 不会用空 dict、空列表或 seed state 覆盖损坏历史。
- **events.jsonl 安全追加**：追加时持锁，写完一行后 flush + fsync。只有没有换行符的末尾半行才视为中断写入并修复；已经换行结束的坏记录、中间坏行都会 fail closed，不改文件。
- **同月归档只追加、批次幂等**：`.autorunne/archive/YYYY-MM.md` 不再被第二次 compact 覆盖。每个压缩批次带确定性 SHA-256 marker。compact 会先把原始批次写入 `.autorunne/runtime/pending-compaction.json`，崩溃重试识别原始批次，而不是按已裁剪状态重算。已有无 marker 的旧归档内容原样保留。
- **版本一致**：`autorunne.__version__`、`pyproject.toml`、`WorkflowConfig.version` 和仓库 skill 的 version 行统一为 `0.6.34`。
- **测试隔离**：update-check 的 `9.9.9` 缓存只写到测试用的 `tmp_path`，不再污染真实 checkout。

## 明确不做

0.6.34 不处理：

- daemon 时长、轮询、扫描器或 `node_modules` 行为；
- Git worktree adopt / `.git` 文件支持；
- SQLite、数据库、云同步或远程锁；
- CLI 命令名称、handoff 视图结构或默认 compact 阈值；
- GitHub push、tag、Release、PyPI 上传或 Discussions。

这些留给 0.6.35 或用户另行授权的发布流程。

## 兼容性

- 现有状态文件仍然有效。
- `.bak` 文件在第一次成功替换后惰性出现。
- 旧的同月归档没有 batch marker 时保持不动；第一次 0.6.34 compact 会在旧内容下面追加带 marker 的新批次。
- 用户看到的命令和视图结构不变，只是锁超时和损坏恢复会给出可执行的错误说明。

## 验证（候选构建，不是已发布）

本候选在独立分支上实际跑过：

- 40 个并发 `autorunne task add` 全部退出 0，40 个唯一任务都还在；
- 主 `sessions.json` 损坏、backup 有效时，`open` 和 `doctor --handoff` 可继续；
- 主文件和 backup 都损坏时，`open` / `doctor` 明确失败且不覆盖原文件；
- 同月两次 compact 保留两批记录；
- 同一批次在 archive 后、sessions 保存后或 events 重写前崩溃，重跑都不重复；
- `events.jsonl` 没有换行的末尾半行可安全修复；已换行的坏末条和中间坏行明确失败且不改字节；
- 同进程线程锁等待会按 timeout 抛错，不会无限阻塞；
- 新的临时虚拟环境安装 wheel 后 `autorunne --version` 为 `AutoRunne 0.6.34`；
- wheel metadata 为 `Name: autorunne`、`Version: 0.6.34`。

以上只是候选构建证据，不代表外部发布已经完成。
