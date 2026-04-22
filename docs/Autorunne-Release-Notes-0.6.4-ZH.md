# Autorunne 0.6.4 Release Notes

发布日期：2026-04-21

## 这版是什么
0.6.4 是 Autorunne 第一版真正意义上更完整的**状态工作流 CLI**。

它不是只会生成几份 markdown，而是已经能把：
- 项目状态
- 任务推进
- 恢复入口
- 迁移旧工作区
- 检查与发布前验证

真正收敛到一条可持续使用的 CLI 主路径里。

## 这一版最重要的升级

### 1. 旧工作区可以正式迁移
新增：
```bash
autorunne migrate
```

现在如果你的仓库里原来只有旧的 `.autorunne/*.md`，可以直接迁移到：
- `.autorunne/state/*`
- `.autorunne/views/*`

不需要手工重建整套工作流。

---

### 2. `status` 终于读真实状态了
以前很多工具都会有一个问题：
“看起来在汇报项目状态，其实只是临时扫一遍 repo。”

0.6.4 里：
```bash
autorunne status
```
会优先读取真实 state，直接展示：
- active task
- last action
- task counts
- integrations
- wrappers
- next action

这样你一进项目，看到的是**真实工作流状态**，不是临时猜测。

---

### 3. 任务现在可以显式管理
新增：
```bash
autorunne task add --text "确认发布清单" --section next-up
autorunne task done --match "确认发布清单"
autorunne task remove --match "过期事项" --section known-unknowns
```

这意味着 Autorunne 不再只是记录 start/checkpoint/finish，
还可以更直接地维护 backlog、known unknowns 和完成项。

---

### 4. 老项目接入体验更顺
现在：
- `show / history / trace` 遇到旧 markdown-only workspace，会明确提示先 `autorunne migrate`
- scanner 会自动降低 `.vscode/` 这类编辑器噪音对恢复建议的干扰
- `doctor` 会明确检查 legacy workspace 是否还没迁移

所以它对真实老项目更友好了，不容易一上来就被噪音路径带偏。

---

## 推荐主路径
现在推荐的使用主路径已经比较清楚：

### 第一次接管一个仓库
```bash
autorunne open --with-vscode
```

### 如果仓库是旧 workspace
```bash
autorunne migrate
```

### 进入一个开发切片
```bash
autorunne start --task "实现支付回调" --next "先补 webhook 合约测试"
```

### 中途落检查点
```bash
autorunne checkpoint --summary "已理清 webhook payload" --next "开始接 handler wiring"
```

### 收尾
```bash
autorunne finish --summary "修完登录问题" --next "开始做订单页筛选"
```

### 查看状态
```bash
autorunne status
autorunne show --section current
autorunne history --limit 5
autorunne trace --limit 10
```

---

## 这版已经验证过什么
我已经实际验证：
- `pytest -q` 通过
- `python -m build` 通过
- GitHub Release 已生成
- PyPI 已更新到 `0.6.4`
- 在 `autorunne` 自己这个真实项目仓库里，完整跑过：
  - `status`
  - `migrate`
  - `open --with-vscode`
  - `start`
  - `checkpoint`
  - `finish`
  - `show`
  - `history`
  - `trace`
  - `doctor`

---

## 安装 / 升级

### 新安装
```bash
pipx install autorunne
```

### 升级到最新版
```bash
pipx upgrade autorunne
```

### 固定安装 0.6.4
```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | AUTORUNNE_INSTALL_SOURCE=release-wheel AUTORUNNE_VERSION=v0.6.4 bash
```

---

## 版本结论
0.6.4 不是“理论上更先进”，而是：

> **已经能在真实项目里直接拿来跑完整状态工作流的一版。**

如果你想要的是一个能让 Codex、Claude Code、Hermes 等工具在同一个项目里持续接力推进，而不是每次重新解释项目，这一版已经可以开始稳定用了。
