# Autorunne 产品说明书

## 一句话定义
Autorunne 是一个 **本地优先的 AI 开发工作流系统**，把任意 Git 仓库变成可持续推进、可恢复上下文、可多模型共享的开发工作区。

## 核心价值
- 让 Claude Code、Codex、Hermes、Cursor 等代理共享同一套项目记忆
- 把开发过程中的上下文、任务、决策、下一步动作落到 `.autorunne/`
- 保持正式发布版本干净，不把内部工作流文件混进交付物
- 让“今天做一半、明天继续、换模型继续、换人继续”真正可行

## 适用对象
- 独立开发者
- AI 编程工作流重度用户
- 同时使用多个 coding agent 的团队
- 需要接手老项目 / 半成品项目的人
- 需要把开发态和交付态严格分开的服务商

## 产品结构
### 1. CLI 命令
- `autorunne init`
- `autorunne adopt`
- `autorunne sync`
- `autorunne watch`
- `autorunne status`
- `autorunne doctor`
- `autorunne export`
- `autorunne release`
- `autorunne hooks`
- `autorunne vscode`
- `autorunne completion`

### 2. 项目本地目录
```text
.autorunne/
├── PROJECT_CONTEXT.md
├── TASKS.md
├── DECISIONS.md
├── SESSION_LOG.md
├── RULES.md
├── NEXT_ACTION.md
├── agents/
└── snapshots/
```

### 3. 多模型共享层
- Hermes：聊天入口 / 执行入口
- Claude Code：高质量工程实现
- Codex：快速编码与验证
- Cursor：编辑器入口

## 典型工作流
1. 在项目里运行 `autorunne init` 或 `autorunne adopt`
2. 生成 `.autorunne/` 共享工作区
3. 让任意 coding agent 先读取 `.autorunne/`
4. 开发过程中持续执行 `autorunne sync`
5. 需要正式交付时执行 `autorunne export` 或 `autorunne release`

## 当前版本定位
当前版本已经属于 **可在真实项目里开始使用的 Alpha 产品**：
- 已有基本命令集
- 已能构建可安装包
- 已有 pytest 验证
- 已支持本地开发安装和 wheel 构建

## 当前边界
还未完成：
- PyPI 正式发布
- 更强的自动会话总结
- 更强的项目扫描 / adopt 推理
- 更细的商业版功能分层

## 推荐使用场景
- 先在自己的真实项目中连续使用 1~2 周
- 再把沉淀下来的最佳实践做成对外版本
