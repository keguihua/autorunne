# Autorunne 0.6.6 Release Notes

## 这版是什么
0.6.6 是把 Autorunne 从“能记状态”继续推进到“只要开始改代码，就会自己把记录接上”的一版。

这一版最重要的不是再让用户多学几个命令，
而是把“有变更就自动记录”真正落到 runtime 行为里：

1. watcher / daemon 检测到真实文件变更后，会自动写回 Autorunne
2. `ar-codex / ar-claude / ar-hermes` 这些 repo wrapper 会自动拉起后台 daemon
3. 用户只需要继续做任务，不需要自己判断什么时候 `start / checkpoint`

## 这版解决了什么真实问题
### 1. 代码已经改了，但 `.autorunne/` 还是停在旧状态
现在：
- watcher / daemon 一旦看到真实文件变更
- 会自动把这轮变更写回 `.autorunne/state/*`
- 不再完全依赖模型自己记得去补记录

### 2. wrapper 只是把 agent 带进 repo，但不会持续跟踪
现在：
- `ar-codex / ar-claude / ar-hermes` 不只是先 `open`
- 还会在背后自动拉起后台 daemon
- 正常 coding session 里的本地改动也会被自动续写

### 3. 用户还得自己判断什么时候 start / checkpoint
现在：
- 第一次检测到有效变更时，会自动补一条聚焦中的 task
- 后续变更会继续追加 checkpoint 风格记录
- 用户只管发任务、继续开发

## 这版具体新增/增强
- 新增 `src/autorunne/core/auto_record.py`
- 新增默认配置：`auto_record_on_change = true`
- `autorunne watch`
  - 不只是看变化
  - 还会自动写回 progress 记录
- `autorunne daemon`
  - 不只是 auto-sync
  - 还会把变更写成自动记录
  - CLI 输出会显示自动记录次数和最后一次摘要
- repo wrapper
  - 自动拉起后台 daemon
  - 命令退出时自动清理 daemon
  - 保留原始 agent 命令退出码

## 验证
这一版已验证：

```bash
python -m pytest tests/test_cli.py -q
python -m pytest tests/test_install_script.py -q
python -m build
```

并且新增覆盖了：
- `open` 生成的 wrapper 确实包含 daemon 启动逻辑
- `watch` 检测到文件变化后会自动记录
- `daemon` 检测到文件变化后会自动记录

## 安装 0.6.6
### 推荐
```bash
pipx install autorunne
```

### 固定安装 0.6.6
```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | AUTORUNNE_INSTALL_SOURCE=release-wheel AUTORUNNE_VERSION=v0.6.6 bash
```

## 版本结论
0.6.6 的价值不是“命令更多了”，而是：

- 用户不用再管 workflow 细节
- 只要发生真实代码变更，Autorunne 就会自动接住
- wrapper / daemon / watcher 终于开始像真正的自动执行层
- 更接近“用户只发任务，系统自己把过程记全”的产品方向
