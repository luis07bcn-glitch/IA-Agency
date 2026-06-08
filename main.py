import typer
from rich.console import Console

app = typer.Typer(help="IA-Agency — Multi-agent AI system")
console = Console()


@app.command()
def run(task: str = typer.Argument(..., help="Task to execute")):
    """Run a task through the agent pipeline."""
    console.print(f"[bold green]Running:[/bold green] {task}")
    # TODO: wire up agent workflow here


@app.command()
def list_agents():
    """List all available agents."""
    console.print("[bold]Available agents:[/bold]")
    # TODO: auto-discover agents


if __name__ == "__main__":
    app()
