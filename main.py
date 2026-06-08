import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box

app = typer.Typer(
    name="ia-agency",
    help="IA-Agency — Plataforma multi-agente de Inteligencia Artificial",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
agents_app = typer.Typer(help="Gestión de agentes", no_args_is_help=True)
app.add_typer(agents_app, name="agents")

console = Console()


def _panel(title: str, content: str, color: str = "green") -> None:
    console.print()
    console.print(Panel(
        Markdown(content),
        title=f"[bold {color}]{title}[/bold {color}]",
        border_style=color,
        padding=(1, 2),
    ))


# ─────────────────────────────────────────
#  PROJECT — orquestador principal
# ─────────────────────────────────────────
@app.command()
def project(
    request: str = typer.Argument(..., help='Requisitos del cliente, ej: "Crear chatbot para restaurante"'),
    output: str = typer.Option(None, "--output", "-o", help="Guardar entrega en outputs/<archivo>"),
    verbose: bool = typer.Option(True, "--verbose/--quiet", help="Mostrar progreso por agente"),
):
    """[bold cyan]Lanza el Project Manager Agent para ejecutar un proyecto completo.[/bold cyan]

    Ejemplos:
      python main.py project "Crear chatbot para mi restaurante El Bulli"
      python main.py project "Landing page para academia de yoga" --output landing.md
    """
    from agents.pm_agent import ProjectManagerAgent
    from tools.file_tool import save_to_file

    console.print(Panel(
        f"[bold]Solicitud:[/bold] {request}",
        title="[bold cyan]IA-Agency · Project Manager[/bold cyan]",
        border_style="cyan",
    ))

    pm = ProjectManagerAgent()

    if verbose:
        console.print("\n[dim]Analizando requisitos y asignando tareas...[/dim]")

    with console.status("[dim]El equipo está trabajando...[/dim]"):
        result = pm.run(request, verbose=False)

    # Show plan
    if result["plan"]:
        plan = result["plan"]
        table = Table(title="Plan del Proyecto", border_style="cyan", box=box.ROUNDED)
        table.add_column("Agente", style="bold yellow")
        table.add_column("Tarea", style="dim")
        for item in plan.get("tasks", []):
            table.add_row(item["agent"], item["task"][:80] + "..." if len(item["task"]) > 80 else item["task"])
        if plan.get("timeline"):
            table.caption = f"Estimación: {plan['timeline']}"
        console.print()
        console.print(table)

    # Show delivery
    _panel("Entrega Final al Cliente", result["final_delivery"], "green")

    if output:
        content = f"# {result['plan']['project_title'] if result['plan'] else 'Proyecto'}\n\n"
        content += result["final_delivery"]
        info = save_to_file(output, content)
        console.print(f"\n[dim]Guardado en {info['saved']}[/dim]")


# ─────────────────────────────────────────
#  CHAT — chatbot interactivo
# ─────────────────────────────────────────
@app.command()
def chat(
    name: str = typer.Option("Asistente IA-Agency", "--name", "-n", help="Nombre del chatbot"),
    system: str = typer.Option(None, "--system", "-s", help="System prompt personalizado"),
):
    """[bold cyan]Inicia una sesión de chat interactiva.[/bold cyan]

    Comandos especiales durante el chat:
      reset  → borra el historial de conversación
      exit   → finaliza la sesión
    """
    from agents.chatbot_agent import ChatbotAgent

    bot = ChatbotAgent(name=name, system_prompt=system)
    console.print(Panel(
        f"[bold]Chatbot:[/bold] {name}\n"
        "[dim]Escribe [bold]exit[/bold] para salir · [bold]reset[/bold] para borrar historial[/dim]",
        title="[bold cyan]IA-Agency · Chat[/bold cyan]",
        border_style="cyan",
    ))

    while True:
        try:
            user_input = console.input("\n[bold yellow]Tú:[/bold yellow] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Sesión finalizada.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "salir", "quit"):
            console.print("[dim]Hasta pronto.[/dim]")
            break
        if user_input.lower() == "reset":
            bot.reset()
            console.print("[dim]Historial borrado.[/dim]")
            continue

        with console.status("[dim]Pensando...[/dim]"):
            reply = bot.chat(user_input)
        console.print(f"\n[bold green]{name}:[/bold green] {reply}")


# ─────────────────────────────────────────
#  CHATBOT — diseñar chatbot para cliente
# ─────────────────────────────────────────
@app.command()
def chatbot(
    brief: str = typer.Argument(..., help='Brief del chatbot, ej: "Chatbot para clínica dental"'),
    output: str = typer.Option(None, "--output", "-o", help="Guardar resultado en outputs/<archivo>"),
):
    """[bold cyan]Chatbot Specialist — diseña un chatbot personalizado para un negocio.[/bold cyan]"""
    from agents.specialists.chatbot_specialist import ChatbotSpecialist
    from tools.file_tool import save_to_file

    with console.status("[dim]Diseñando chatbot...[/dim]"):
        result = ChatbotSpecialist().run(brief)

    _panel("Chatbot Specialist", result, "cyan")

    if output:
        info = save_to_file(output, result)
        console.print(f"[dim]Guardado en {info['saved']}[/dim]")


# ─────────────────────────────────────────
#  WEBDEV — generar código web
# ─────────────────────────────────────────
@app.command()
def webdev(
    task: str = typer.Argument(..., help='Descripción, ej: "Landing page para gym moderno"'),
    output: str = typer.Option(None, "--output", "-o", help="Guardar en outputs/<archivo>"),
):
    """[bold cyan]Web Developer Agent — crea landing pages y código web listo para producción.[/bold cyan]"""
    from agents.specialists.web_developer import WebDeveloperAgent
    from tools.file_tool import save_to_file

    with console.status("[dim]Desarrollando...[/dim]"):
        result = WebDeveloperAgent().run(task)

    _panel("Web Developer", result, "blue")

    if output:
        info = save_to_file(output, result)
        console.print(f"[dim]Guardado en {info['saved']}[/dim]")


# ─────────────────────────────────────────
#  CONTENT — generar contenido y copy
# ─────────────────────────────────────────
@app.command()
def content(
    brief: str = typer.Argument(..., help='Brief de contenido, ej: "5 posts Instagram para cafetería"'),
    output: str = typer.Option(None, "--output", "-o", help="Guardar en outputs/<archivo>"),
):
    """[bold cyan]Content & Marketing Agent — genera copy y contenido para todos los canales.[/bold cyan]"""
    from agents.specialists.content_marketing import ContentMarketingAgent
    from tools.file_tool import save_to_file

    with console.status("[dim]Creando contenido...[/dim]"):
        result = ContentMarketingAgent().run(brief)

    _panel("Content & Marketing", result, "magenta")

    if output:
        info = save_to_file(output, result)
        console.print(f"[dim]Guardado en {info['saved']}[/dim]")


# ─────────────────────────────────────────
#  AUTONOMOUS — agente autónomo con tools
# ─────────────────────────────────────────
@app.command()
def autonomous(
    task: str = typer.Argument(..., help="Tarea a ejecutar de forma autónoma"),
    output: str = typer.Option(None, "--output", "-o", help="Guardar en outputs/<archivo>"),
):
    """[bold cyan]Autonomous Agent — ejecuta tareas complejas usando herramientas.[/bold cyan]

    Herramientas disponibles: get_current_datetime, calculate, save_to_file, read_from_file

    Ejemplo:
      python main.py autonomous "¿Qué día es hoy? Calcula el 21% de IVA de 1250€ y guárdalo en iva.txt"
    """
    from agents.autonomous_agent import AutonomousAgent
    from tools.file_tool import save_to_file

    console.print("[dim]Herramientas: datetime · calculator · file I/O[/dim]")
    with console.status("[dim]Ejecutando tarea autónoma...[/dim]"):
        result = AutonomousAgent().run(task)

    _panel("Autonomous Agent", result, "yellow")

    if output:
        info = save_to_file(output, result)
        console.print(f"[dim]Guardado en {info['saved']}[/dim]")


# ─────────────────────────────────────────
#  AGENTS LIST
# ─────────────────────────────────────────
@agents_app.command("list")
def agents_list():
    """[bold cyan]Lista todos los agentes y comandos disponibles.[/bold cyan]"""
    table = Table(
        title="IA-Agency — Agentes & Servicios",
        border_style="cyan",
        box=box.ROUNDED,
        show_header=True,
    )
    table.add_column("Comando", style="bold yellow", min_width=20)
    table.add_column("Agente", style="bold white", min_width=22)
    table.add_column("Descripción", style="dim")

    rows = [
        ("project <brief>",     "ProjectManagerAgent",    "Orquesta todo el equipo para proyectos completos"),
        ("chat",                "ChatbotAgent",            "Chat interactivo con memoria de sesión"),
        ("chatbot <brief>",     "ChatbotSpecialist",       "Diseña chatbots personalizados para negocios"),
        ("webdev <task>",       "WebDeveloperAgent",       "Crea landing pages y código web"),
        ("content <brief>",     "ContentMarketingAgent",   "Copy, posts, emails y contenido de marketing"),
        ("autonomous <task>",   "AutonomousAgent",         "Tareas complejas con uso de herramientas"),
    ]

    for cmd, agent, desc in rows:
        table.add_row(cmd, agent, desc)

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Uso: [bold]python main.py <comando> --help[/bold] para más opciones[/dim]")
    console.print("[dim]Todos los comandos aceptan [bold]--output <archivo>[/bold] para guardar el resultado[/dim]")


if __name__ == "__main__":
    app()
