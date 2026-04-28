from __future__ import annotations

from typing import Any

WORKFLOW_FLOW = "open/sync → start/ingest → checkpoint → finish/validate"


def _latest_validation_status(sessions: dict[str, Any]) -> str:
    for session in reversed(sessions.get("items", [])):
        for line in session.get("lines", []):
            if line.startswith("Validation result:"):
                raw = line.split(":", 1)[1].strip().lower()
                if raw == "passed":
                    return "通过"
                if raw == "failed":
                    return "失败"
                return raw or "未记录"
    return "未记录"


def build_user_summary(state: dict[str, Any], *, missing: list[str] | None = None) -> dict[str, str]:
    """Return a plain-language status snapshot for non-technical users."""
    current = state.get("current", {})
    sessions = state.get("sessions", {})
    active_task = (current.get("active_task") or "").strip()
    last_action = (current.get("last_action") or "").strip()
    missing_files = [item for item in (missing or []) if item]

    if missing_files:
        project_state = "需要补齐上下文入口"
    elif active_task:
        project_state = "正在开发中"
    elif last_action == "task_finished":
        project_state = "可继续开发"
    else:
        project_state = "已准备，可开始任务"

    context_entry = "已准备好" if not missing_files else f"缺少 {len(missing_files)} 个入口文件"
    validation_status = _latest_validation_status(sessions)
    next_action = current.get("next_action") or "确认下一个具体任务"

    return {
        "project_state": project_state,
        "validation_status": validation_status,
        "next_action": next_action,
        "context_entry": context_entry,
        "workflow_flow": WORKFLOW_FLOW,
        "one_line": f"当前项目状态：{project_state}；上次验证：{validation_status}；下一步：{next_action}；上下文入口：{context_entry}",
    }
