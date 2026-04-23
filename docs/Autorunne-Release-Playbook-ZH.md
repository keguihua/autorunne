# Autorunne 发布与合并策略（公开售卖版）

## 1. 推荐分支策略
### `main`
始终保持：
- 可安装
- 可演示
- README 与安装命令可直接复制
- `scripts/install.sh` 可直接从 `main` 下载使用

### 功能分支
例如：
- `feat/...`
- `fix/...`
- `docs/...`

所有新功能先走 PR，再合并到 `main`。

## 2. 合并策略
建议使用：
- **squash merge**

原因：
- 保持主分支历史干净
- 适合快速迭代的小而硬产品
- 方便以后按版本整理 changelog

## 3. 对外公开前检查清单
每次准备让外部用户直接安装前，先确认：

### 基础质量
- `pytest -q` 通过
- `python -m build` 通过
- wheel 安装烟测通过
- `scripts/install.sh` 一键安装烟测通过

### 产品体验
- README 顶部安装命令可直接复制
- `autorunne open --with-vscode` 路径正常
- `.autorunne/views/START_HERE.md` 能被 Claude Code / Codex / Gemini 正常使用
- `start / checkpoint / finish` 工作流能走通

### 发布面
- `main` 已包含最新稳定功能
## 4. tag 发布动作
```bash
git tag v0.6.7
git push origin v0.6.7
```

如果已经在 PyPI 侧配置好 trusted publisher，那么推送版本 tag 后会同时触发：
- GitHub Release 资产上传
- PyPI 发布

也就是说未来的标准对外发布动作可以收敛成：
1. 合并到 `main`
2. 本地确认测试 / build 通过
3. `git tag vX.Y.Z`
4. `git push origin vX.Y.Z`
- GitHub Release workflow 会自动构建并上传 wheel / sdist

## 4. 推荐发布节奏
### 小版本（建议）
- `0.4.1`
- `0.4.2`
- `0.6.7`

适合 Autorunne 这种快速产品化节奏：
- 小步快跑
- 每次只补一个高价值动作
- 不堆大而全功能

## 5. 当前建议操作
如果当前 PR 已本地验证通过：
1. 合并到 `main`
2. 确认 `main` 分支安装命令可用：
```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | bash
```
3. 再决定是否打 tag 发 release

## 6. 对外售卖建议
先卖“可立即使用的稳定版”，不要等“完美版”。

更合适的节奏是：
- `main` 保持可安装可演示
- 持续修小问题
- 每个版本只强调 1~3 个最强改进点

这样最符合 Autorunne 的产品气质：
- 轻
- 稳
- 快
- 真能用
