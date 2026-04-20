from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from autorunne.commands import adopt as adopt_cmd
from autorunne.commands import completion as completion_cmd
from autorunne.commands import doctor as doctor_cmd
from autorunne.commands import export as export_cmd
from autorunne.commands import hooks as hooks_cmd
from autorunne.commands import init as init_cmd
from autorunne.commands import release as release_cmd
from autorunne.commands import status as status_cmd
from autorunne.commands import sync as sync_cmd
from autorunne.commands import vscode as vscode_cmd
from autorunne.commands import watch as watch_cmd

app = typer.Typer(help="Turn any git repository into an Autorunne workspace.")
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
    if result.get("vscode"):
        console.print(f"VS Code integration ready: {result['vscode']['tasks_path']}")


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
def watch(
    path: str | None = typer.Option(None, help="Target repository path"),
    duration: float = typer.Option(30.0, help="How long to watch for changes in seconds."),
    interval: float = typer.Option(1.0, help="Polling interval in seconds."),
):
    """Watch the repo for local file changes and auto-sync Autorunne."""
    result = watch_cmd.run(_target(path), duration=duration, interval=interval)
    if result["changes_detected"]:
        console.print(f"Detected change(s): {result['changes_detected']}")
        console.print(f"Last sync repo: {result['last_sync']}")
    else:
        console.print("No file changes detected during watch window.")


@app.command()
def status(path: str | None = typer.Option(None, help="Target repository path")):
    """Show Autorunne health and next action."""
    result = status_cmd.run(_target(path))
    table = Table(title="Autorunne Status")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Repo", result["repo"])
    table.add_row("Autorunne root", result["workflow_root"])
    table.add_row("Stack", ", ".join(result["stack"]))
    table.add_row("Framework", ", ".join(result["framework"]))
    table.add_row("Missing files", ", ".join(result["missing"]) or "none")
    table.add_row("Next action", result["next_action"])
    table.add_row("Tracked by git", str(result["workflow_tracked"]))
    console.print(table)


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
    version: str = typer.Option(..., help="Release version, e.g. 0.4.0 or v0.4.0"),
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
