# Autorunne 0.6.8 Release Notes

## 这版是什么
0.6.8 不是换方向的一版，
而是把 0.6.7 已经修好的 repo 入口，再往前推进一步：

> 不只是“别报错”，
> 而是要让用户在 Codex 窗口里直接发自然语言任务后，
> Autorunne 能更干净地记录过程，并且在小任务结束后自动收口。

## 这版重点解决什么
### 1. 自动记录里会混进很多接入噪音
之前真实 dogfood 时，Autorunne 会把这些也记进自动 checkpoint：

- `.codex`
- `.agents`
- `.claude`
- `.cursor`
- `.github/copilot-instructions.md`
- `AGENTS.md`

这会导致日志看起来像“系统在自说自话”，
不够聚焦用户真正改的项目文件。

现在：
- 自动记录默认忽略这些接入噪音路径
- daemon / auto-record 更聚焦真实改动
- `SESSION_LOG.md` 和任务记录更像真正的开发过程，而不是接入脚手架变化

### 2. 任务做完后不会自动 finish
之前虽然能做到：
- Hermes 自然语言任务进入 `.autorunne`
- `ar-codex` 真正改文件
- daemon 自动写 checkpoint

但任务完成后通常还停在：
- `In progress`
- 没有自动 finish
- 用户还得自己补一遍 `autorunne finish`

现在：
- repo wrapper 在成功结束 agent 会话后，会尝试自动执行 `autorunne auto-finish`
- 对于这种极小、明确、自然语言驱动的单文件任务，可以自动收口
- `TASKS.md` 会把任务移到 completed
- `NEXT_ACTION.md` 会切到一个新的通用下一步，而不是停留在旧任务提示

## 这版具体改了什么
- `src/autorunne/core/auto_record.py`
  - 新增噪音路径过滤
  - 增加自动 finish 的核心逻辑
  - 文档类单文件任务可以跳过整仓测试，避免为了一个 `.md` 改动强行跑完整验证
- `src/autorunne/commands/daemon.py`
  - 只在检测到“有意义的真实改动”时才自动 sync / checkpoint
- `src/autorunne/commands/auto_finish.py`
  - 新增 wrapper 可调用的自动收口命令
- `src/autorunne/core/integrations.py`
  - 生成的 `ar-codex` / `ar-claude` / `ar-hermes` wrapper 在成功执行后会尝试自动 finish
- `src/autorunne/models/config.py`
  - 增加 `auto_record_ignored_paths`

## 真实验证
这版已验证：

```bash
python -m pytest -q
python -m build
```

另外还做了真实 temp repo dogfood：

1. `autorunne open`
2. `autorunne hermes-task`
3. `./.autorunne/bin/ar-codex exec --full-auto '自然语言任务'`
4. 检查：
   - `TASKS.md`
   - `NEXT_ACTION.md`
   - `SESSION_LOG.md`

实际观察到：
- 真实目标文件被创建
- daemon 写入 checkpoint
- wrapper 自动 finish
- 任务被移到 completed
- finish 记录里只保留有意义的目标文件，不再混入 `.codex` / `.agents` 这类接入噪音

## 安装 0.6.8
### 推荐
```bash
pipx install autorunne
```

### 固定安装 0.6.8
```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | AUTORUNNE_INSTALL_SOURCE=release-wheel AUTORUNNE_VERSION=v0.6.8 bash
```

## 版本结论
0.6.8 的价值不是加很多新命令，
而是把用户真正关心的体验往前推了一步：

- 用户发自然语言任务
- Codex 真改文件
- Autorunne 自动记录过程
- 小任务可以自动收口
- 日志更干净，不再被接入噪音淹没
