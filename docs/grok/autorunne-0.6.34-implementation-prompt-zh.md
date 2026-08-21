# 给 Grok 的 Autorunne 0.6.34 实施提示词

把下面整段提示词原样交给 Grok。不要把“候选完成”理解为允许发布。

---

你现在负责实现 Autorunne 0.6.34 的状态可靠性补丁。

## 仓库和起点

- 仓库：/Users/huafire777/Desktop/program/autorunne
- GitHub：HUAFIRE777/autorunne
- 已审查基线：f1828d4（main / origin/main 的 0.6.33 基线）
- 目标分支：grok/autorunne-0.6.34-reliability
- 语言：Python 3.11+
- 当前本地 .venv 是用户环境，不得提交、删除或重建。
- 如果当前 HEAD 已经前进，先报告实际基线并确认它包含 f1828d4；不得回退或覆盖用户提交。

## 第一步必须做

1. 读取 AGENTS.md。
2. 读取 .autorunne/views/START_HERE.md、PROJECT_CONTEXT.md、TASKS.md、DECISIONS.md、NEXT_ACTION.md。
3. 读取并严格执行：
   - docs/superpowers/specs/2026-08-22-autorunne-0.6.34-state-reliability-design.md
   - docs/superpowers/plans/2026-08-22-autorunne-0.6.34-state-reliability.md
4. 使用 Autorunne CLI 记录任务；绝对不要直接编辑 .autorunne/state/*：

       AUTORUNNE_DISABLE_UPDATE_CHECK=1 .venv/bin/autorunne ingest \
         --source grok \
         --task "Implement the approved Autorunne 0.6.34 state reliability patch using TDD" \
         --next "Execute Task 1 red tests from the approved implementation plan"

5. 检查 git status，保留所有不属于你的改动。不得提交 .venv、.autorunne、dist、缓存或用户文件。
6. 在独立 branch/worktree 中工作。如果无法安全建立 worktree，停止并以 BLOCKED 报告，不要在 main 上直接大改。

## 产品目标

Autorunne 现有价值不变：AI 进入项目后能立即知道项目做到哪里、当前任务和下一步。0.6.34 只修底层长期可靠性：

- 多线程、多进程状态写入串行化；
- JSON 同目录原子替换；
- 最近一次有效备份和安全自动恢复；
- 主文件、备份都坏时明确失败，绝不静默清空；
- events.jsonl 追加持久化和安全尾部修复；
- 同月 compact 只追加，不覆盖；
- 相同压缩批次崩溃重试不重复；
- 版本统一为 0.6.34；
- 测试不能再把 9.9.9 更新缓存写入真实 checkout。

## 严格范围

只允许修改实施计划 File map 中列出的产品、测试和文档文件，以及最终 CODEX_REVIEW_HANDOFF.md。

明确禁止：

- 修改 daemon 时长、轮询、扫描器或 node_modules 行为；
- 修改 Git worktree adopt 支持；
- 改成 SQLite、数据库、云同步或远程锁；
- 改 CLI 命令名称、handoff 视图结构或默认 compact 阈值；
- 删除或重建用户 .autorunne；
- 直接编辑 .autorunne/state/*；
- 顺手重构无关模块；
- merge main、push GitHub、打 tag、创建 Release、上传 PyPI、发 Discussion；
- 把“测试通过”写成“已经发布”。

遇到范围外问题，记录在 CODEX_REVIEW_HANDOFF.md 的 Known limitations，不要修。

## 开发方法

严格按计划 Task 1 到 Task 7 顺序执行。每一个行为都使用 TDD：

1. 写一个最小失败测试；
2. 运行并确认失败原因正确；
3. 写最小实现；
4. 运行 focused test 确认通过；
5. 运行相关回归；
6. 做一个范围清楚的小提交。

不要先写完整实现再补测试。不要删除或放宽已有断言来获得绿色结果。

锁必须覆盖完整 read-modify-write-render 事务，不是只锁 write_text。锁要支持同线程嵌套，避免 finish_task -> save_workspace_state -> append_event -> render_views 自己死锁。

所有恢复必须 fail closed：

- primary 坏、backup 好：恢复 backup；
- primary 和 backup 都坏：退出非零，保留原文件，明确告诉用户 Autorunne 没有 reset state；
- 不允许用空 dict、空列表或 seed state 覆盖损坏历史。

归档必须包含确定性 SHA-256 batch marker。已有无 marker 的旧归档内容必须原样保留。

## 必须真实运行的验证

所有 pytest 命令带 AUTORUNNE_DISABLE_UPDATE_CHECK=1。

Focused：

    AUTORUNNE_DISABLE_UPDATE_CHECK=1 .venv/bin/python -m pytest \
      tests/test_persistence.py tests/test_state_engine.py \
      tests/test_memory_commands.py tests/test_update_check.py -q

Full：

    AUTORUNNE_DISABLE_UPDATE_CHECK=1 .venv/bin/python -m pytest -q

Build：

    .venv/bin/python -m build

Metadata：

    unzip -p dist/autorunne-0.6.34-py3-none-any.whl \
      'autorunne-0.6.34.dist-info/METADATA' | sed -n '1,20p'

Hygiene：

    git diff --check
    git status --short
    git diff --name-only f1828d4 HEAD
    test "$(sed -n 's/^version: //p' .agents/skills/autorunne-workflow/SKILL.md)" = \
      "$(sed -n 's/^version: //p' .claude/skills/autorunne-workflow/SKILL.md)"

两个 Skill 只要求 version 行一致；必须保留 Codex/Claude 各自不同的 source、wrapper 和用户入口文字。

还必须实际证明：

- 40 个并发 task add 全部退出 0，40 个唯一任务全部保留；
- 主 sessions.json 损坏、backup 有效时 open 和 doctor 可继续；
- 主文件和 backup 都损坏时 open/doctor 明确失败且不覆盖；
- 同月两次 compact 保留两批记录；
- 同一批次模拟中断后重跑不重复；
- events.jsonl 末尾半行可安全修复，中间坏行明确失败；
- wheel metadata 是 0.6.34。

如果任何测试失败，不得写 COMPLETE。先判断是否属于批准范围；属于则修复并添加回归测试，不属于则写 PARTIAL 或 BLOCKED。

## 文档要求

新增 docs/Autorunne-Release-Notes-0.6.34-ZH.md，更新 README.md 和 CHANGELOG.md，但必须称为 release candidate，除非外部发布真的由用户另行批准并成功完成。本任务没有发布授权。

## 强制交接文件

在仓库根目录创建 CODEX_REVIEW_HANDOFF.md，必须包含：

1. Status：只能是 COMPLETE、PARTIAL、BLOCKED 之一；
2. 实际 cwd、branch、base SHA、head SHA；
3. changed files 和每个文件的目的；
4. spec acceptance criteria 对照矩阵；
5. 每条验证命令、真实 exit code、关键输出；
6. 并发、损坏恢复、fail-closed、归档追加、归档幂等、版本 metadata 的证据；
7. Known limitations；
8. 明确写 GitHub push/tag/release = NOT PERFORMED，PyPI = NOT PERFORMED；
9. 请求 Codex 独立检查 diff、重跑 focused/full/build/metadata/scope。

不得伪造结果，不得把计划中的 expected output 当成真实运行结果。

## Autorunne 收口

验证成功后通过 CLI 记录，不要直接改状态：

    AUTORUNNE_DISABLE_UPDATE_CHECK=1 .venv/bin/autorunne finish \
      --summary "Implemented and verified the bounded Autorunne 0.6.34 state reliability patch" \
      --next "Codex independently reviews CODEX_REVIEW_HANDOFF.md and reruns reliability verification" \
      --validate "AUTORUNNE_DISABLE_UPDATE_CHECK=1 .venv/bin/python -m pytest -q"

最后提交候选文档和 CODEX_REVIEW_HANDOFF.md，然后停止。

## 最终回复格式

第一行只写 COMPLETE、PARTIAL 或 BLOCKED。

随后提供：

- branch 和 head SHA；
- 完成了什么；
- focused/full/build/metadata 的真实结果；
- 未完成或风险；
- CODEX_REVIEW_HANDOFF.md 路径；
- 明确说明没有 merge、push、tag、GitHub Release 或 PyPI publish。

完成后等待 Codex 独立验收。不要继续发布。
