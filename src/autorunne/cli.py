from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from autorunne.commands import adopt as adopt_cmd
from autorunne.commands import checkpoint as checkpoint_cmd
from autorunne.commands import completion as completion_cmd
from autorunne.commands import daemon as daemon_cmd
from autorunne.commands import doctor as doctor_cmd
from autorunne.commands import export as export_cmd
from autorunne.commands import finish as finish_cmd
from autorunne.commands import hermes_task as hermes_task_cmd
from autorunne.commands import history as history_cmd
from autorunne.commands import hooks as hooks_cmd
from autorunne.commands import init as init_cmd
from autorunne.commands import integrate as integrate_cmd
from autorunne.commands import migrate as migrate_cmd
from autorunne.commands import open as open_cmd
from autorunne.commands import record as record_cmd
from autorunne.commands import render as render_cmd
from autorunne.commands import release as release_cmd
from autorunne.commands import show as show_cmd
from autorunne.commands import start as start_cmd
from autorunne.commands import status as status_cmd
from autorunne.commands import sync as sync_cmd
from autorunne.commands import task as task_cmd
from autorunne.commands import trace as trace_cmd
from autorunne.commands import vscode as vscode_cmd
from autorunne.commands import watch as watch_cmd

app = typer.Typer(help="Turn any git repository into an Autorunne workspace.")
task_app = typer.Typer(help="Manage explicit task state inside the Autorunne workspace.")
app.add_typer(task_app, name="task")
console = Console()


def _target(path: str | None) -> Path:
    return Path(path).expanduser().resolve() if path else Path.cwd()


@app.command()
def init(
    path: str | None = typer.Option(None, help="Target repository path"),
    with_vscode: bool = typer.Option(False, "--with-vscode", help="Also create VS Code auto-sync integration."),
):
    """Initialize Autorunne files in a git repository."""
    result = init_cmd.run(_target(path), with_vscode=with_vscode)
    console.print(f"Initialized Autorunne in [bold]{result['repo_root']}[/bold]")
    console.print(f"Local git exclude updated: {result['exclude_path']}")
    console.print(f"Next action: {result['scan']['next_action']}")
    console.print(f"Open in Claude Code / Codex / Cursor / Copilot / Gemini / Hermes: {result['start_here_path']}")
    if result.get("vscode"):
        console.print(f"VS Code integration ready: {result['vscode']['tasks_path']}")


@app.command()
def adopt(
    path: str | None = typer.Option(None, help="Target repository path"),
    with_vscode: bool = typer.Option(False, "--with-vscode", help="Also create VS Code auto-sync integration."),
):
    """Adopt an existing repository into Autorunne."""
    result = adopt_cmd.run(_target(path), with_vscode=with_vscode)
    console.print(f"Adopted repository: [bold]{result['repo_root']}[/bold]")
    console.print(f"Detected stack: {', '.join(result['scan']['stack'])}")
    console.print(f"Detected framework: {', '.join(result['scan']['framework'])}")
    console.print(f"Next action: {result['scan']['next_action']}")
    console.print(f"Open in Claude Code / Codex / Cursor / Copilot / Gemini / Hermes: {result['start_here_path']}")
    if result.get("vscode"):
        console.print(f"VS Code integration ready: {result['vscode']['tasks_path']}")


@app.command()
def open(
    path: str | None = typer.Option(None, help="Target repository path"),
    with_vscode: bool = typer.Option(False, "--with-vscode", help="Also install VS Code folder-open automation."),
):
    """Auto-bootstrap or resume a repo so the agent enters a working state immediately."""
    result = open_cmd.run(_target(path), with_vscode=with_vscode)
    console.print(f"Autorunne {result['action']}: [bold]{result['repo_root']}[/bold]")
    console.print(f"Detected stack: {', '.join(result['scan']['stack'])}")
    console.print(f"Project phase: {result['scan']['project_phase']}")
    console.print(f"Resume hint: {result['scan']['resume_hint']}")
    console.print(f"Next action: {result['scan']['next_action']}")
    console.print(f"Open now: {result['start_here_path']}")
    if result.get("vscode"):
        console.print(f"VS Code integration ready: {result['vscode']['tasks_path']}")


@app.command()
def migrate(
    path: str | None = typer.Option(None, help="Target repository path"),
    note: str | None = typer.Option(None, help="Optional migration note to append"),
):
    """Convert a legacy markdown-only workspace into a state-backed workspace."""
    result = migrate_cmd.run(_target(path), note=note)
    if result["migrated"]:
        console.print(f"Migrated Autorunne workspace in [bold]{result['repo_root']}[/bold]")
        console.print(f"Next action: {result['next_action']}")
        console.print(f"Open now: {result['start_here_path']}")
    else:
        console.print(f"Autorunne state workspace already active in [bold]{result['repo_root']}[/bold]")


@app.command()
def render(path: str | None = typer.Option(None, help="Target repository path")):
    """Rebuild rendered views from `.autorunne/state/*`."""
    result = render_cmd.run(_target(path))
    console.print(f"Rendered views for [bold]{result['repo_root']}[/bold]")


@app.command()
def integrate(
    path: str | None = typer.Option(None, help="Target repository path"),
    tool: str = typer.Option("all", help="codex, claude, hermes, or all"),
    scope: str = typer.Option("repo", help="repo or user"),
):
    """Install repo/user integration files and wrappers."""
    result = integrate_cmd.run(_target(path), tool=tool, scope=scope)
    console.print(f"Installed integrations ({result['scope']}): {', '.join(result['tools'])}")
    if result.get("wrappers"):
        console.print(f"Wrappers: {', '.join(result['wrappers'])}")


@app.command()
def show(
    path: str | None = typer.Option(None, help="Target repository path"),
    section: str = typer.Option("all", help="current, tasks, decisions, sessions, events, or all"),
):
    """Show a structured slice of Autorunne state."""
    result = show_cmd.run(_target(path), section=section)
    console.print(result["data"])


@app.command()
def history(
    path: str | None = typer.Option(None, help="Target repository path"),
    limit: int = typer.Option(20, min=1, help="How many session entries to show."),
):
    """Show recent session history from state."""
    result = history_cmd.run(_target(path), limit=limit)
    console.print(result["items"])


@app.command()
def trace(
    path: str | None = typer.Option(None, help="Target repository path"),
    limit: int = typer.Option(20, min=1, help="How many events to show."),
    event_type: str | None = typer.Option(None, "--event-type", help="Optional event type filter."),
):
    """Show recent state events."""
    result = trace_cmd.run(_target(path), limit=limit, event_type=event_type)
    console.print(result["items"])


@app.command()
def record(
    summary: str = typer.Option(..., help="Short durable note to add to state history."),
    next: str | None = typer.Option(None, "--next", help="Optional next action override."),
    task: str | None = typer.Option(None, "--task", help="Optional task to insert into next-up."),
    decision: str | None = typer.Option(None, "--decision", help="Optional durable decision to append."),
    event_type: str = typer.Option("manual_recorded", help="Custom event type for the record entry."),
    path: str | None = typer.Option(None, help="Target repository path"),
):
    """Record a manual state note without running a sync or finish."""
    result = record_cmd.run(_target(path), summary=summary, next_action=next, task=task, decision=decision, event_type=event_type)
    console.print(f"Recorded: {result['summary']}")
    console.print(f"Next action: {result['next_action']}")
    if result.get("decision"):
        console.print(f"Decision captured: {result['decision']}")


@task_app.command("add")
def task_add(
    text: str = typer.Option(..., "--text", help="Task text to add."),
    section: str = typer.Option("next-up", "--section", help="next-up, known-unknowns, in-progress, or completed"),
    path: str | None = typer.Option(None, help="Target repository path"),
):
    """Add an explicit task item to the state workspace."""
    result = task_cmd.add(_target(path), text=text, section=section)
    console.print(f"Added task: {result['text']}")
    console.print(f"Section: {result['section']}")


@task_app.command("done")
def task_done(
    match: str = typer.Option(..., "--match", help="Substring used to find the task to complete."),
    section: str = typer.Option("next-up", "--section", help="Preferred section to search first."),
    path: str | None = typer.Option(None, help="Target repository path"),
):
    """Mark a task as completed and move it into completed state."""
    result = task_cmd.done(_target(path), match=match, section=section)
    console.print(f"Completed task: {result['matched']}")
    console.print(f"From section: {result.get('from_section', section)}")


@task_app.command("remove")
def task_remove(
    match: str = typer.Option(..., "--match", help="Substring used to find the task to remove."),
    section: str = typer.Option("next-up", "--section", help="Section to search."),
    path: str | None = typer.Option(None, help="Target repository path"),
):
    """Remove a task from the chosen state section."""
    result = task_cmd.remove(_target(path), match=match, section=section)
    console.print(f"Removed task: {result['matched']}")
    console.print(f"From section: {result.get('from_section', section)}")


@app.command()
def sync(
    path: str | None = typer.Option(None, help="Target repository path"),
    note: str | None = typer.Option(None, help="Optional session note to append"),
):
    """Refresh Autorunne state."""
    result = sync_cmd.run(_target(path), note=note)
    console.print(f"Synced Autorunne in [bold]{result['repo_root']}[/bold]")
    console.print(f"Next action: {result['scan']['next_action']}")


@app.command()
def start(
    task: str = typer.Option(..., help="Task to start and place into TASKS.md."),
    next: str | None = typer.Option(None, "--next", help="Optional next action to write immediately."),
    path: str | None = typer.Option(None, help="Target repository path"),
):
    """Start a new focused task slice."""
    result = start_cmd.run(_target(path), task=task, next_action=next)
    console.print(f"Started: {result['task']}")
    console.print(f"Next action: {result['next_action']}")


@app.command()
def checkpoint(
    summary: str = typer.Option(..., help="Short progress note for the current task."),
    next: str | None = typer.Option(None, "--next", help="Optional next action to update immediately."),
    validate: str | None = typer.Option(None, "--validate", help="Optional validation command to run before checkpoint succeeds."),
    no_validate: bool = typer.Option(False, "--no-validate", help="Skip automatic validation for this checkpoint call."),
    path: str | None = typer.Option(None, help="Target repository path"),
):
    """Save progress without closing the current task."""
    try:
        result = checkpoint_cmd.run(
            _target(path),
            summary=summary,
            next_action=next,
            validation_command=validate,
            skip_validation=no_validate,
        )
    except checkpoint_cmd.FinishValidationError as exc:
        console.print(f"Validation failed: {exc.command}")
        if exc.output:
            console.print(exc.output)
        raise typer.Exit(1)
    console.print(f"Checkpoint: {result['summary']}")
    console.print(f"Next action: {result['next_action']}")
    if result.get("validation"):
        console.print(f"Validation: {result['validation']['status']} ({result['validation']['command']})")


@app.command()
def finish(
    summary: str = typer.Option(..., help="Concise summary of what was completed."),
    next: str | None = typer.Option(None, "--next", help="Concrete next step to write into NEXT_ACTION.md."),
    task: str | None = typer.Option(None, "--task", help="Optional open task text to close inside TASKS.md."),
    decision: str | None = typer.Option(None, "--decision", help="Optional durable decision to append to DECISIONS.md."),
    validate: str | None = typer.Option(None, "--validate", help="Optional validation command to run before finish succeeds."),
    no_validate: bool = typer.Option(False, "--no-validate", help="Skip automatic validation for this finish call."),
    path: str | None = typer.Option(None, help="Target repository path"),
):
    """Record a finished slice and set the next action."""
    try:
        result = finish_cmd.run(
            _target(path),
            summary=summary,
            next_action=next,
            task_match=task,
            decision=decision,
            validation_command=validate,
            skip_validation=no_validate,
        )
    except finish_cmd.FinishValidationError as exc:
        console.print(f"Validation failed: {exc.command}")
        if exc.output:
            console.print(exc.output)
        raise typer.Exit(1)
    console.print(f"Finished: {result['summary']}")
    console.print(f"Next action: {result['next_action']}")
    if result.get("matched_task"):
        console.print(f"Matched task: {result['matched_task']}")
    if result.get("decision"):
        console.print(f"Decision captured: {result['decision']}")
    if result.get("changed_files"):
        console.print(f"Files changed: {', '.join(result['changed_files'])}")
    if result.get("validation"):
        console.print(f"Validation: {result['validation']['status']} ({result['validation']['command']})")


@app.command()
def watch(
    path: str | None = typer.Option(None, help="Target repository path"),
    duration: float = typer.Option(30.0, help="How long to watch for changes in seconds."),
    interval: float = typer.Option(1.0, help="Polling interval in seconds."),
):
    """Watch the repo for local file changes and auto-record Autorunne progress."""
    result = watch_cmd.run(_target(path), duration=duration, interval=interval)
    if result["changes_detected"]:
        console.print(f"Detected change(s): {result['changes_detected']}")
        console.print(f"Last sync repo: {result['last_sync']}")
        console.print(f"Auto-records: {result.get('auto_records', 0)}")
        if result.get("last_auto_summary"):
            console.print(f"Last auto-record: {result['last_auto_summary']}")
    else:
        console.print("No file changes detected during watch window.")


@app.command()
def daemon(
    path: str | None = typer.Option(None, help="Target repository path"),
    duration: float = typer.Option(30.0, help="How long to keep the daemon loop alive in seconds."),
    interval: float = typer.Option(1.0, help="Polling interval in seconds."),
    max_syncs: int = typer.Option(0, min=0, help="Stop after this many auto-syncs. Use 0 to keep the loop only time-bound."),
):
    """Run an open-first background loop that bootstraps/resumes then auto-records changes."""
    result = daemon_cmd.run(_target(path), duration=duration, interval=interval, max_syncs=max_syncs or None)
    console.print(f"Autorunne daemon started from: {result['action']}")
    console.print(f"Ticks: {result['ticks']}")
    console.print(f"Auto-syncs: {result['syncs']}")
    console.print(f"Auto-records: {result.get('auto_records', 0)}")
    if result.get("last_changed_files"):
        console.print(f"Last changed files: {', '.join(result['last_changed_files'])}")
    if result.get("last_auto_summary"):
        console.print(f"Last auto-record: {result['last_auto_summary']}")
    console.print(f"Next action: {result['next_action']}")


@app.command("hermes-task")
def hermes_task(
    task: str = typer.Option(..., help="Task text coming from a Hermes chat entry."),
    next: str | None = typer.Option(None, "--next", help="Concrete next action to write immediately."),
    context: str | None = typer.Option(None, help="Optional user request or extra Hermes context."),
    decision: str | None = typer.Option(None, help="Optional durable decision to append immediately."),
    path: str | None = typer.Option(None, help="Target repository path"),
):
    """Bridge a Hermes chat task into local Autorunne workflow files."""
    result = hermes_task_cmd.run(_target(path), task=task, next_action=next, context=context, decision=decision)
    console.print(f"Hermes task captured: {result['task']}")
    console.print(f"Workspace action: {result['workspace_action']}")
    console.print(f"Next action: {result['next_action']}")
    if result.get("decision"):
        console.print(f"Decision captured: {result['decision']}")


@app.command()
def status(path: str | None = typer.Option(None, help="Target repository path")):
    """Show Autorunne health and next action."""
    result = status_cmd.run(_target(path))
    table = Table(title="Autorunne Status")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Repo", result["repo"])
    table.add_row("Autorunne root", result["workflow_root"])
    table.add_row("Workflow mode", result.get("workflow_mode", "scan"))
    table.add_row("Stack", ", ".join(result["stack"]))
    table.add_row("Framework", ", ".join(result["framework"]))
    table.add_row("Project phase", result["project_phase"])
    table.add_row("Resume hint", result["resume_hint"])
    table.add_row("Active task", result.get("active_task") or "none")
    table.add_row("Last action", result.get("last_action") or "none")
    table.add_row("Updated at", result.get("updated_at") or "unknown")
    task_counts = result.get("task_counts", {})
    table.add_row(
        "Task counts",
        f"completed={task_counts.get('completed', 0)}, in_progress={task_counts.get('in_progress', 0)}, next_up={task_counts.get('next_up', 0)}, archived={task_counts.get('archived', 0)}, known_unknowns={task_counts.get('known_unknowns', 0)}",
    )
    table.add_row("Sessions / events", f"{result.get('session_count', 0)} / {result.get('event_count', 0)}")
    repo_integrations = result.get("repo_integrations", {})
    tools = ", ".join(repo_integrations.get("tools", [])) or "none"
    wrappers = ", ".join(repo_integrations.get("wrappers", [])) or "none"
    table.add_row("Repo integrations", tools)
    table.add_row("Repo wrappers", wrappers)
    table.add_row("Missing files", ", ".join(result["missing"]) or "none")
    table.add_row("Next action", result["next_action"])
    table.add_row("Tracked by git", str(result["workflow_tracked"]))
    console.print(table)
    if result.get("legacy_workspace"):
        console.print("Legacy workspace detected. Run `autorunne migrate` to convert markdown memory into `.autorunne/state/*`.")


@app.command()
def doctor(path: str | None = typer.Option(None, help="Target repository path")):
    """Validate Autorunne structure and git isolation."""
    result = doctor_cmd.run(_target(path))
    table = Table(title="Autorunne Doctor")
    table.add_column("Check")
    table.add_column("Status")
    for name, status in result["checks"].items():
        table.add_row(name, status)
    console.print(table)
    if result["missing"]:
        console.print({"missing": result["missing"]})
    if result["warnings"]:
        console.print({"warnings": result["warnings"]})
    raise typer.Exit(1 if result["warnings"] or result["missing"] else 0)


@app.command("export")
def export_command(
    path: str | None = typer.Option(None, help="Target repository path"),
    output_name: str | None = typer.Option(None, help="Optional export directory name"),
):
    """Create a clean release copy without Autorunne files."""
    result = export_cmd.run(_target(path), output_name=output_name)
    console.print(f"Exported clean copy to [bold]{result['exported_path']}[/bold]")


@app.command()
def release(
    version: str = typer.Option(..., help="Release version, e.g. 0.6.3 or v0.6.3"),
    path: str | None = typer.Option(None, help="Target repository path"),
    skip_build: bool = typer.Option(False, help="Skip building wheel/sdist assets."),
):
    """Create a formal release bundle with a clean export and release notes."""
    result = release_cmd.run(_target(path), version=version, skip_build=skip_build)
    console.print(f"Release bundle created: [bold]{result['release_dir']}[/bold]")
    console.print(f"Release notes: {result['notes_path']}")
    console.print(f"Manifest: {result['manifest_path']}")
    if result['assets']:
        console.print({"assets": result['assets']})


@app.command()
def hooks(
    path: str | None = typer.Option(None, help="Target repository path"),
    with_pre_commit: bool = typer.Option(False, "--with-pre-commit", help="Also install a pre-commit hook and config."),
):
    """Install lightweight git hooks that auto-sync on checkout/merge."""
    result = hooks_cmd.run(_target(path), with_pre_commit=with_pre_commit)
    for hook in result["hooks"]:
        console.print(f"Installed hook: {hook}")
    if result.get("precommit_config"):
        console.print(f"Pre-commit config: {result['precommit_config']}")


@app.command("vscode")
def vscode_command(path: str | None = typer.Option(None, help="Target repository path")):
    """Create VS Code integration that auto-syncs on folder open."""
    result = vscode_cmd.run(_target(path))
    console.print(f"VS Code tasks: {result['tasks_path']}")
    console.print(f"VS Code settings: {result['settings_path']}")


@app.command()
def completion(shell: str = typer.Argument(..., help="Shell: bash, zsh, or fish")):
    """Print shell completion setup instructions."""
    result = completion_cmd.run(shell)
    console.print(result["script"], end="")


if __name__ == "__main__":
    app()
