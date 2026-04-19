from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from awf.commands import adopt as adopt_cmd
from awf.commands import doctor as doctor_cmd
from awf.commands import export as export_cmd
from awf.commands import hooks as hooks_cmd
from awf.commands import init as init_cmd
from awf.commands import status as status_cmd
from awf.commands import sync as sync_cmd
from awf.commands import vscode as vscode_cmd

app = typer.Typer(help="Attach a local-only AI workflow layer to any git repository.")
console = Console()


def _target(path: str | None) -> Path:
    return Path(path).expanduser().resolve() if path else Path.cwd()


@app.command()
def init(
    path: str | None = typer.Option(None, help="Target repository path"),
    with_vscode: bool = typer.Option(False, "--with-vscode", help="Also create VS Code auto-sync integration."),
):
    """Initialize workflow files in a git repository."""
    result = init_cmd.run(_target(path), with_vscode=with_vscode)
    console.print(f"Initialized AI workflow in [bold]{result['repo_root']}[/bold]")
    console.print(f"Local git exclude updated: {result['exclude_path']}")
    if result.get("vscode"):
        console.print(f"VS Code integration ready: {result['vscode']['tasks_path']}")


@app.command()
def adopt(
    path: str | None = typer.Option(None, help="Target repository path"),
    with_vscode: bool = typer.Option(False, "--with-vscode", help="Also create VS Code auto-sync integration."),
):
    """Adopt an existing repository into the workflow."""
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
    """Refresh workflow state."""
    result = sync_cmd.run(_target(path), note=note)
    console.print(f"Synced workflow in [bold]{result['repo_root']}[/bold]")
    console.print(f"Next action: {result['scan']['next_action']}")


@app.command()
def status(path: str | None = typer.Option(None, help="Target repository path")):
    """Show workflow health and next action."""
    result = status_cmd.run(_target(path))
    table = Table(title="AI Workflow Status")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Repo", result["repo"])
    table.add_row("Workflow root", result["workflow_root"])
    table.add_row("Stack", ", ".join(result["stack"]))
    table.add_row("Framework", ", ".join(result["framework"]))
    table.add_row("Missing files", ", ".join(result["missing"]) or "none")
    table.add_row("Next action", result["next_action"])
    table.add_row("Tracked by git", str(result["workflow_tracked"]))
    console.print(table)


@app.command()
def doctor(path: str | None = typer.Option(None, help="Target repository path")):
    """Validate workflow structure and git isolation."""
    result = doctor_cmd.run(_target(path))
    console.print(result)
    raise typer.Exit(1 if result["warnings"] or result["missing"] else 0)


@app.command("export")
def export_command(
    path: str | None = typer.Option(None, help="Target repository path"),
    output_name: str | None = typer.Option(None, help="Optional export directory name"),
):
    """Create a clean release copy without AI workflow files."""
    result = export_cmd.run(_target(path), output_name=output_name)
    console.print(f"Exported clean copy to [bold]{result['exported_path']}[/bold]")


@app.command()
def hooks(path: str | None = typer.Option(None, help="Target repository path")):
    """Install lightweight git hooks that auto-sync on checkout/merge."""
    result = hooks_cmd.run(_target(path))
    for hook in result["hooks"]:
        console.print(f"Installed hook: {hook}")


@app.command("vscode")
def vscode_command(path: str | None = typer.Option(None, help="Target repository path")):
    """Create VS Code integration that auto-syncs on folder open."""
    result = vscode_cmd.run(_target(path))
    console.print(f"VS Code tasks: {result['tasks_path']}")
    console.print(f"VS Code settings: {result['settings_path']}")


if __name__ == "__main__":
    app()
