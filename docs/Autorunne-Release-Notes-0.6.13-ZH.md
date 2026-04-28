# Autorunne 0.6.13 发布说明

## 一句话总结
0.6.13 重点修复真实开发中的多包项目识别问题：根目录没有 `package.json`，但存在 `frontend/package.json`、`backend/package.json`、`contracts/package.json` 时，`autorunne sync` 不再把项目误判为 `generic`。

## 主要变化
- 支持扫描 `frontend/`、`backend/`、`contracts/`、`sdk/`、`integrations/`、`apps/*`、`packages/*` 下的 `package.json`
- 自动识别 Vite 前端、Node.js 后端、Hardhat 合约项目
- 自动把子项目提升为顶层摘要：`multi-package Node/TypeScript`
- 自动从子项目 scripts 派生命令，例如：
  - `frontend:build -> cd frontend && npm run build`
  - `backend:test -> cd backend && npm test`
  - `contracts:compile -> cd contracts && npm run compile`
  - `contracts:test -> cd contracts && npm test`
- START_HERE / PROJECT_CONTEXT / COMMANDS 不再因为根目录缺少 `package.json` 显示 generic
- 对旧状态做了渲染兜底：如果已有 `packages`，即使顶层摘要还是 generic，也会从 packages 派生真实视图

## 适合谁升级
如果你的项目类似：

```text
frontend/
backend/
contracts/
```

并且根目录没有 `package.json`，建议直接升级到 0.6.13。

## 升级命令
```bash
pipx upgrade autorunne --pip-args '--no-cache-dir -i https://pypi.org/simple'
```

验证：

```bash
autorunne version
```

期望输出：

```text
AutoRunne 0.6.13
```

## 验证结果
- 全量测试通过：`72 passed`
- GitHub Actions 通过
- GitHub Release 发布成功
- PyPI `autorunne==0.6.13` 发布并安装验证成功
- 临时 haopay 风格项目 smoke 验证通过
