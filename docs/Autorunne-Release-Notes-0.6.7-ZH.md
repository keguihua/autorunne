# Autorunne 0.6.7 Release Notes

## 这版是什么
0.6.7 是一个很聚焦的修正版：

> 把 repo 里自动生成给各个 agent 用的接入文件格式修干净，
> 让 Codex / Claude / Cursor 这些入口不要一进项目就先报格式警告。

这版不是去改产品方向，
而是把 0.6.6 已经打通的自动记录链路继续打磨到更稳的可用状态。

## 这版解决了什么真实问题
### 1. `ar-codex` 进 repo 时会提示 skill 文件格式不合法
典型报错是：

```text
missing YAML frontmatter delimited by ---
```

根因不是 Autorunne 没跑，
而是自动生成的 `.agents/skills/autorunne-workflow/SKILL.md` / `.claude/.../SKILL.md`
没有带合法的 YAML frontmatter。

现在：
- 生成出来的 skill 文件会自带标准 frontmatter
- Codex / Claude 这类入口能更正常加载 repo skill
- 不会再一进 repo 就先看到无效 `SKILL.md` 警告

### 2. Cursor rule 的 frontmatter 不够干净
之前生成的 Cursor rule 带了一个空的 `globs:` 键。
虽然不一定每次都炸，但格式不够稳。

现在：
- 改成更干净的 frontmatter
- 避免这种“看起来没事，但其实不规范”的 metadata 输出

## 这版具体改了什么
- `src/autorunne/core/integrations.py`
  - 生成给 Codex / Claude 用的 `SKILL.md` 时，补上合法 YAML frontmatter
  - Cursor rule 的 frontmatter 改干净
- 测试补强
  - 新增检查生成后的 `.agents/.../SKILL.md` / `.claude/.../SKILL.md` 是否真的以 `---` 开头
  - 检查 Cursor rule 是否包含正确 frontmatter，且不再输出空 `globs:`

## 验证
这一版已验证：

```bash
python -m pytest tests/test_integrations.py -q
python -m pytest tests/test_cli.py tests/test_install_script.py -q
python -m pytest -q
```

另外还做了真实生成检查：
- fresh repo + `autorunne init`
- 检查：
  - `.agents/skills/autorunne-workflow/SKILL.md`
  - `.claude/skills/autorunne-workflow/SKILL.md`
  - `.cursor/rules/autorunne-workflow.mdc`
  - `.github/copilot-instructions.md`

## 安装 0.6.7
### 推荐
```bash
pipx install autorunne
```

### 固定安装 0.6.7
```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | AUTORUNNE_INSTALL_SOURCE=release-wheel AUTORUNNE_VERSION=v0.6.7 bash
```

## 版本结论
0.6.7 的价值不是“功能更多”，而是：

- 让多 agent 接入层更干净
- 让 `ar-codex` 这类入口更像真正可直接用的产品入口
- 把 0.6.6 的自动记录能力建立在更稳的文件格式基础上
