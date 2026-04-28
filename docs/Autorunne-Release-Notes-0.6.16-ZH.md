# Autorunne 0.6.16 发布说明

0.6.16 是一个“安心感和可视化”版本，重点不是让用户多学命令，而是让项目负责人一眼看懂 Autorunne 是否已经把项目上下文、验证结果和下一步记录好。

## 核心变化

### 1. `autorunne status` 增加用户摘要

现在 `autorunne status` 除了技术字段，还会显示：

```text
用户摘要：
当前项目状态：可继续开发
上次验证：通过
下一步：开发下一个小功能
上下文入口：已准备好
记录流程：open/sync → start/ingest → checkpoint → finish/validate
```

这对应用户真正关心的问题：

- 当前任务有没有做完？
- 上次验证有没有通过？
- 下一步是什么？
- 下次换 agent 或隔天继续时，上下文入口是否准备好了？

### 2. 新增 `.autorunne/views/STATUS.md`

每个已初始化的 repo 会渲染一份给人看的状态页：

```text
.autorunne/views/STATUS.md
.autorunne/STATUS.md
```

它用中文总结：

- 当前项目状态
- 上次验证
- 下一步
- 上下文入口是否准备好
- Autorunne 的记录流程

这样课程学员、客户、项目负责人不需要读 `current.json` 或 `SESSION_LOG.md`，也能判断项目是否可以继续派任务。

### 3. 工作流程更可视化

0.6.16 把 Autorunne 的后台工作解释成一条固定流程：

```text
open/sync → start/ingest → checkpoint → finish/validate
```

这条流程对应：

1. 打开/刷新项目上下文；
2. 记录用户交代的新任务；
3. 中途写回进展；
4. 验证通过后收尾，并留下总结和下一步。

## 为什么这版重要

0.6.15 解决的是“多 agent 入口都能回到 Autorunne workflow”。

0.6.16 解决的是“用户能不能看懂 Autorunne 到底有没有让项目更可靠”。

对外可以这样说：

> Autorunne 0.6.16 让 AI 项目不只保存上下文，还把项目是否可继续、上次是否验证、下一步是什么，用用户能看懂的方式显示出来。

## 推荐升级

```bash
pipx upgrade autorunne --pip-args "--no-cache-dir -i https://pypi.org/simple"
autorunne version
```

或固定安装：

```bash
pip install autorunne==0.6.16
```

## 验证摘要

- 本地测试：`python -m pytest -q`
- 本地构建：`python -m build`
- 课程 demo smoke test：`autorunne open/sync/start/finish` + `python -m pytest -q`
- GitHub Release：`v0.6.16`
- PyPI：`autorunne==0.6.16`

## 商业稳定性判断

0.6.16 仍然应定位为“可商用验证的 Beta 工作流层”。

它适合：

- AI 编程课程演示；
- 早期客户项目交付；
- 多 agent 协作开发流程标准化；
- 让用户只管派任务，而不是反复解释项目上下文。

不建议夸成“完全自动替代开发者”或“最终企业级研发平台”。
