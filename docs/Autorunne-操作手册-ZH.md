# Autorunne 安装与使用操作手册

这是一份给真实用户直接照着做的说明。

目标很简单：
- 先把 Autorunne 装好
- 让 VS Code 自动接管仓库
- 然后直接在仓库里启动 Codex / Claude Code 开发

---

## 一、你到底要不要每次先启动 Autorunne？

**不用。**

正确理解是：

- **Autorunne 是仓库工作流底座**
- **Codex / Claude Code 是实际开发执行者**

所以正常流程不是：
- 先开一个 Autorunne 聊天窗口
- 再开一个 Codex 窗口

而是：

1. **Autorunne 安装一次**
2. **每个仓库第一次接管一次**
3. 后面你就正常打开 VS Code
4. 然后直接在仓库终端里启动 Codex / Claude Code

如果你只是正常通过 `ar-codex / ar-claude / ar-hermes` 进入仓库，这些 wrapper 现在会自动拉起后台 daemon；只有你想单独保温一个仓库时，才需要手动运行 `autorunne daemon`。

---

## 二、安装方式

### 方式 A：最推荐，直接从 PyPI 安装

```bash
pipx install autorunne
```

适合：
- 你想用最标准的一键安装方式
- 你希望以后更新也直接走 pipx

---

### 方式 B：一键安装脚本

```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | bash
```

适合：
- 想最快装好
- 准备直接在自己机器上用
- 主要用 VS Code + Codex / Claude Code

---

### 方式 C：固定安装某个公开版本

比如安装 0.6.10：

```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | AUTORUNNE_INSTALL_SOURCE=release-wheel AUTORUNNE_VERSION=v0.6.10 bash
```

适合：
- 你想锁定版本
- 你不想直接跟随 main 最新代码

---

### 方式 D：开发者本地安装

```bash
git clone https://github.com/keguihua/autorunne.git
cd autorunne
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

适合：
- 你准备改 Autorunne 自己的代码
- 你想参与二次开发

---

## 三、每个仓库第一次怎么接入

进入你的项目仓库，执行：

```bash
autorunne open --with-vscode
```

这个命令会做几件事：

- 如果仓库还没有 `.autorunne/`，就自动创建
- 如果仓库已经有 `.autorunne/state/*`，就自动恢复
- 如果仓库里是旧的 markdown-only `.autorunne/*.md`，可以后续执行 `autorunne migrate` 升级进 state workspace
- 自动生成 VS Code 工作区任务
- 让 VS Code 以后打开这个仓库时自动执行 `autorunne open`

也就是说：

**这一步每个仓库通常只要做一次。**

后面同一个仓库你再次打开时：
- VS Code 会自动触发 `autorunne open`
- `.autorunne/` 里的记忆、任务、下一步状态会自动 refresh
- 你直接开 Codex / Claude Code 就能接着做

---

## 四、之后日常怎么用

### 最省事的日常流程

1. 打开 VS Code 到你的项目目录
2. VS Code 自动触发 Autorunne
3. 打开终端
4. 直接启动 Codex / Claude Code
5. 开发

你不用每次单独再开一个 Autorunne 窗口。

---

## 五、如果你用 Codex，实际怎么走

推荐顺序：

1. 先保证这个仓库已经执行过：

```bash
autorunne open --with-vscode
```

2. 然后以后每次直接：
- 打开 VS Code
- 打开这个仓库的终端
- 启动 Codex

3. 让 Codex 从这里开始：

- `.autorunne/views/START_HERE.md`
- `.autorunne/views/NEXT_ACTION.md`
- `.autorunne/views/TASKS.md`
- 或者直接用 `./.autorunne/bin/ar-codex`

如果 Codex 能读项目文件，它就能直接接着干。

---

## 六、如果你用 Claude Code，怎么走

和 Codex 基本一样：

1. 仓库先接入一次 Autorunne
2. 打开 VS Code 或普通终端进入仓库
3. 启动 Claude Code
4. 让它从 `.autorunne/views/START_HERE.md` 开始，或者直接用 `./.autorunne/bin/ar-claude`

---

## 七、什么时候要手动运行 Autorunne

### 情况 1：你没配 VS Code 自动接入

那你每次进仓库手动跑一下：

```bash
autorunne open
```

### 情况 2：你想让仓库在一个工作时段里持续自动记录

这时运行：

```bash
autorunne daemon --duration 300 --interval 2
```

如果你只想检测到第一次有效改动并自动记录后就退出：

```bash
autorunne daemon --duration 300 --interval 2 --max-syncs 1
```

现在 daemon 会显示：
- 自动记录了几次
- 最后一次涉及哪些文件

---

## 八、升级 AutoRunne

推荐用 `pipx` 直接升级，并强制走官方 PyPI、跳过本地缓存：

```bash
pipx upgrade autorunne --pip-args="--no-cache-dir -i https://pypi.org/simple"
```

验证当前安装版本，推荐看 pipx 管理的包版本：

```bash
pipx runpip autorunne show autorunne
```

也可以使用 CLI 内置版本命令：

```bash
autorunne version
autorunne --version
```

注意：旧版 CLI 可能没有 `autorunne --version` 参数，所以排查旧环境时，优先使用：

```bash
pipx runpip autorunne show autorunne
```

如果你执行普通升级时看到：

```text
autorunne is already at latest version 0.6.6
```

但 PyPI 实际已经有新版，通常是 pipx 缓存、pip 镜像源或旧索引缓存导致。不要先卸载，先执行：

```bash
pipx upgrade autorunne --pip-args="--no-cache-dir -i https://pypi.org/simple"
```

或者使用 Autorunne 提供的安全升级入口：

```bash
autorunne self-upgrade
```

这个命令等价于优先执行上面的 pipx 安全升级方式，只升级 CLI 本身，不会删除或重建任何项目里的 `.autorunne/` 目录。

最后 fallback 才是卸载重装：

```bash
pipx uninstall autorunne
pipx install --pip-args="--no-cache-dir -i https://pypi.org/simple" autorunne
```

升级后进入项目执行：

```bash
autorunne sync
autorunne open --with-vscode
```

如果项目里的 `.autorunne/config.json` 版本较旧，Autorunne 会安全迁移到当前包版本；它只补齐/更新配置字段，不会删除你的任务、报告、状态、runtime、skills 或历史记录。

---

## 九、常用命令表

### 接管 / 恢复仓库

```bash
autorunne open
autorunne open --with-vscode
```

### 新仓库初始化

```bash
autorunne init
autorunne init --with-vscode
```

### 手动同步 / 渲染 / 看状态

```bash
autorunne sync
autorunne sync --note "今天修完登录问题，下一步做订单页"
autorunne record --summary "补一条项目说明" --next "继续梳理 trace"
autorunne render
autorunne show --section current
autorunne history --limit 5
autorunne trace --limit 10
```

### 开始一个任务

```bash
autorunne start --task "实现支付回调" --next "先补 webhook 合约测试"
```

### 记录中途进度

```bash
autorunne checkpoint --summary "已理清 webhook payload" --next "开始接 handler wiring"
```

### 收尾一个切片

```bash
autorunne finish --summary "修完登录问题" --task "检查登录逻辑" --next "开始做订单页筛选"
```

### 从 Hermes 直接写任务进仓库

```bash
autorunne hermes-task \
  --task "继续支付回调" \
  --next "先补 webhook 合约测试" \
  --context "用户在 Hermes 里要求继续做支付回调"
```

### 健康检查

```bash
autorunne doctor
```

### 正式导出版本

```bash
autorunne export
autorunne release --version 0.6.8
```

---

## 十、最推荐你的真实工作流

如果你主要是：
- VS Code
- Codex / Claude Code
- 做真实项目开发

那最推荐就是：

### 第一步：安装一次

```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | bash
```

### 第二步：每个仓库第一次接入一次

```bash
autorunne open --with-vscode
```

### 第三步：以后直接开发
### 第三步：以后正常开发
- 打开 VS Code
- 打开仓库
- 直接开 Codex / Claude Code
- 不需要额外再开一个 Autorunne 窗口

也就是说，你要的效果就是：
- **每个新仓库第一次手动接入一次**
- **后面再开同一个仓库基本自动恢复**
- **你直接开始开发就行**

---

## 十一、一句话总结

**Autorunne 负责让仓库“进入可续做状态”，Codex / Claude Code 负责真正继续开发。**

所以它更像：
- 开发底座
- 项目本地记忆层
- 进入仓库后的自动工作流入口

而不是一个每次都必须单独先打开的聊天软件。
