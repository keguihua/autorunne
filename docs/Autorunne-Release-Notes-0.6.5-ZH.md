# Autorunne 0.6.5 Release Notes

## 这版是什么
0.6.5 是把 Autorunne 从“能记任务”继续打磨成“真实项目里更不容易越用越乱”的一版。

这一版重点不是再加一堆新命令，而是把真实开发时最容易积灰的两个地方补强：

1. `in-progress` 只保留当前活跃任务
2. 旧版本 release backlog 自动归档到历史区块

## 这版解决了什么真实问题
### 1. 旧的 next action / in-progress 会越积越多
现在：
- 当前活跃任务只保留在 `In progress`
- 旧的未完成项会自动回落到 `Next up`
- 不会继续冒充“正在做”

### 2. 老版本发布遗留会污染当前路线
现在：
- 像 `Tag v0.6.3`、`publish 0.6.3` 这类已经过期的 release backlog
- 会自动移到 `Archived / historical`
- `Next up` 更聚焦当前版本和当前产品路线

## 这版具体新增/增强
- `TASKS.md` 新增 `Archived / historical` 区块
- 自动识别旧版本 release backlog 并归档
- `start / checkpoint / finish / sync` 自动重排 `in-progress` 与 `next-up`
- `task add --section in-progress` 会真正设置 active task
- `task done / task remove` 后会自动重新整理焦点分层
- `status` 现在会显示 archived 计数

## 真实验证
这版不是只跑单测，我还在 `autorunne` 自己这个真实仓库里跑过：

```bash
autorunne task add --text "Audit lingering release backlog" --section in-progress
autorunne start --task "在真实 autorunne 仓库验证 in-progress 与 next-up 分层规则" --next "检查旧 in-progress 是否被自动降级到 next-up，再跑一次 checkpoint/finish"
autorunne checkpoint --summary "真实仓库中已验证 start 会把旧 in-progress 降级为 next-up，并保持当前 active task 单一聚焦" --next "跑完整 pytest 并 finish 收口这轮真实验证" --validate "python -m pytest -q"
autorunne finish --summary "完成真实仓库分层规则验证：旧 in-progress 已自动降级，新 active task 与 next-up 分层正常" --task "在真实 autorunne 仓库验证 in-progress 与 next-up 分层规则" --next "下一步可以继续打磨 release backlog 的归档策略" --decision "in-progress 应只承载当前活跃任务，历史未完成项应自动回落到 next-up" --validate "python -m pytest -q"
autorunne task remove --match "Audit lingering release backlog" --section next-up
```

并且全量测试通过：

```bash
python -m pytest -q
```

## 安装 0.6.5
### 推荐
```bash
pipx install autorunne
```

### 固定安装 0.6.5
```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | AUTORUNNE_INSTALL_SOURCE=release-wheel AUTORUNNE_VERSION=v0.6.5 bash
```

## 版本结论
0.6.5 的价值不是“看起来更高级”，而是：

- 当前任务更聚焦
- backlog 更干净
- 历史发布遗留有地方放
- 真正在长期项目里更容易持续帮到开发
