# Autorunne 商业计划书（简版）

## 1. 项目名称
Autorunne

## 2. 项目定位
Autorunne 不是普通的 AI 聊天壳，也不是单一模型插件。
它是一个 **面向真实开发项目的 AI 工作流基础设施**：

> 把任意 Git 项目变成可恢复、可协作、可多模型接力推进的 AI 开发工作区。
> Hermes 记住用户和跨项目经验，Autorunne 记住这个 repo 的项目状态。

## 3. 市场痛点
当前 AI 编程工具普遍存在：
- 会写代码，但不擅长长期连续推进项目
- 换会话、换模型、换人后上下文断裂
- 开发态与交付态容易混在一起
- 大多数工具绑定某个编辑器或某个模型，迁移成本高

## 4. Autorunne 的解决方案
Autorunne 提供：
- 本地项目记忆层 `.autorunne/`
- 标准化任务/决策/下一步恢复机制
- 多模型共享工作流
- frontend/backend/contracts 等多包项目自动识别与命令派生
- 开发态与正式交付态分离
- 命令行优先，编辑器只是入口，不是核心

## 5. 目标用户
### 第一阶段
- AI 编程重度用户
- 独立开发者
- 接外包/交付项目的人
- 用 Hermes/Claude/Codex 混合开发的人

### 第二阶段
- 小型开发团队
- AI 开发流程顾问/培训者
- 想把 AI 编程流程标准化的服务商

## 6. 产品形态
### 免费开源层（0.6.15 已覆盖）
- state-first CLI
- `.autorunne/state/*` + `.autorunne/views/*`
- 基础命令：open/migrate/start/checkpoint/finish/record/status/show/history/trace/doctor/export/release
- repo 级 skill / wrapper / VS Code 接入
- direct agent 任务入口：`autorunne ingest`
- 多包 Node/TypeScript 项目识别：`frontend/`、`backend/`、`contracts/`、`apps/*`、`packages/*`
- 轻量 Python 教学/demo 项目识别：无 package manager 也能给出 `python app.py`、`python -m pytest -q`
- Codex / Claude / Hermes / Cursor / Copilot repo 入口统一指向 Autorunne workflow

### 未来商业层
- 团队协作版模板
- 行业化工作流包
- 可视化仪表盘
- 私有部署 / 企业版
- 配套培训与咨询服务
- 面向交付团队的标准化流程资产包

## 7. 收入模式
- 开源 + 高级版订阅
- 企业部署/顾问服务
- AI 开发流程培训课程
- 行业解决方案模板包
- 与 Hermes / 业务文档 / 教学体系联动销售
- 面向“AI 编程交付训练营”的项目工作流工具包

## 8. 核心竞争力
- 不依赖单一模型
- 不依赖单一编辑器
- 强调“项目连续推进”而不是一次性问答
- 适合中国用户的真实交付场景
- 可与 Hermes 聊天入口天然联动
- 与 Hermes 记忆系统互补：Hermes 管用户记忆，Autorunne 管 repo 本地项目记忆

## 9. 当前阶段判断
当前已经具备：
- state-first CLI 主路径
- 旧 `.autorunne/*.md` 到 state workspace 的迁移能力
- 可安装包构建、GitHub Release 与 PyPI 发布链路
- 显式 task 操作、状态观测与 doctor 检查
- direct agent 工作流说明
- 0.6.13 多包项目识别与 sync 渲染修复，能支撑真实 frontend/backend/contracts 项目演示
- 0.6.14/0.6.15 轻量 Python demo 识别与全 agent 入口补齐，能支撑课程开发项目演示
- 初步对外说明文档、产品说明书、中文操作手册、商业稳定性说明

当前更准确的阶段是：
### **可在真实项目里持续使用、可做对外演示和早期成交的商业验证版 Beta 产品**
还不是最终成熟企业版，但 GitHub Release、PyPI、服务器本机运行环境和真实课程开发 demo 都已验证，已经适合进入“教学 + 交付 + 顾问服务”组合验证。

## 10. 接下来的关键里程碑
### M1：真实项目连续跑状态工作流
- 用 `open → sync → ingest/start → finish → show/history/trace` 连续跑多个真实项目
- 优先覆盖 AI 教学、全栈开发、frontend/backend/contracts 项目
- 验证恢复体验、多模型协作体验、legacy migration 体验

### M2：产品化补强
- JSON 输出模式
- 更复杂 monorepo 的包关系图谱
- 更强的 release / changelog / publish 自动化
- 更顺的团队协作接入

### M3：商业化包装
- 官网 / 演示视频 / 对外宣传页
- 标准版产品说明书
- 成交页 / 商业介绍 / 行业方案
- 课程 / 咨询 / 交付流程服务包

## 11. 一句话商业结论
Autorunne 最有机会成为：

> **AI 时代的软件项目“持续开发操作层”**

不是替代模型，而是让不同模型真正能接力把项目做完。
