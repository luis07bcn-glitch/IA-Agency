import sys
import io
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box

# Fix Windows terminal encoding for Unicode/emoji output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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
#  SUBTITLE — karaoke word-by-word
# ─────────────────────────────────────────
@app.command()
def subtitle(
    video_file: str  = typer.Argument(..., help="MP4 del EditorAgent (outputs/final/.../video_final.mp4)"),
    audio_file: str  = typer.Argument(..., help="MP3 narrado (outputs/audio/.../full_audio.mp3)"),
    output_dir: str  = typer.Option(None,      "--output-dir", "-o"),
    language: str    = typer.Option("es",       "--lang", "-l", help="es | en | auto"),
    model: str       = typer.Option("small",    "--model", "-m", help="tiny|base|small|medium"),
    words: int       = typer.Option(4,          "--words", "-w", help="Palabras por línea (3-5)"),
    font_size: int   = typer.Option(22,         "--font-size", help="Tamaño de fuente"),
    style: str       = typer.Option("tiktok",   "--style", "-s", help="tiktok | youtube"),
):
    """[bold cyan]SubtitleAgent — transcribe con Whisper y quema karaoke en el video.[/bold cyan]

    Ejemplos:
      python main.py subtitle outputs/final/guion_sueno/video_final.mp4 outputs/audio/guion_sueno/full_audio.mp3
      python main.py subtitle ... --model medium --words 3 --style tiktok
    """
    from agents.specialists.video.subtitle_agent import SubtitleAgent
    from pathlib import Path
    import json as _json

    for p in (video_file, audio_file):
        if not Path(p).exists():
            console.print(f"[red]No se encuentra: {p}[/red]")
            raise typer.Exit(1)

    if not output_dir:
        output_dir = str(Path(video_file).parent)

    console.print(Panel(
        f"[bold]Video:[/bold]    {video_file}\n"
        f"[bold]Audio:[/bold]    {audio_file}\n"
        f"[bold]Modelo:[/bold]   Whisper {model}  ·  [bold]Idioma:[/bold] {language}  ·  [bold]Estilo:[/bold] {style}",
        title="[bold cyan]IA-Agency · SubtitleAgent[/bold cyan]",
        border_style="cyan",
    ))

    console.print(f"\n[dim]Descargando modelo Whisper '{model}' si no está en caché...[/dim]")

    with console.status(f"[dim]Transcribiendo audio con Whisper {model}...[/dim]"):
        result = SubtitleAgent(whisper_model=model).run(
            video_file=video_file,
            audio_file=audio_file,
            output_dir=output_dir,
            language=language if language != "auto" else None,
            words_per_line=words,
            font_size=font_size,
            style=style,
        )

    mins, secs = divmod(int(result.duration_seconds), 60)
    size_mb = round(Path(result.video_with_subs).stat().st_size / 1_048_576, 1) if Path(result.video_with_subs).exists() else 0

    console.print()
    console.print(Panel(
        f"[bold yellow]{Path(result.video_with_subs).name}[/bold yellow]\n\n"
        f"[dim]Idioma detectado:[/dim] [green]{result.language_detected}[/green]  ·  "
        f"[dim]Palabras transcritas:[/dim] [green]{result.total_words}[/green]\n"
        f"[dim]Duración:[/dim] {mins}m {secs:02d}s  ·  "
        f"[dim]Tamaño:[/dim] {size_mb} MB\n"
        f"[dim]ASS:[/dim] {result.ass_file}\n"
        f"[dim]Video:[/dim] {result.video_with_subs}",
        title="[bold green]Subtítulos quemados[/bold green]",
        border_style="green",
    ))

    meta = str(Path(output_dir) / "subtitle_output.json")
    with open(meta, "w", encoding="utf-8") as f:
        _json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    console.print(f"[dim]Metadatos en {meta}[/dim]")


# ─────────────────────────────────────────
#  EDIT — ensambla el video final
# ─────────────────────────────────────────
@app.command()
def edit(
    script_file: str  = typer.Argument(..., help="JSON del ScriptAgent"),
    voice_file: str   = typer.Argument(..., help="JSON del VoiceAgent (voice_output.json)"),
    media_file: str   = typer.Argument(..., help="JSON del MediaAgent (media_output.json)"),
    output_dir: str   = typer.Option(None,       "--output-dir", "-o"),
    orientation: str  = typer.Option("portrait", "--orientation", help="portrait | landscape"),
    bgm: str          = typer.Option(None,        "--bgm", "-b", help="Ruta a MP3 de música (por defecto: aleatorio MPT)"),
    bgm_vol: float    = typer.Option(0.08,        "--bgm-vol", help="Volumen BGM 0.0-1.0 (defecto 0.08)"),
):
    """[bold cyan]EditorAgent — ensambla clips + audio en el MP4 final.[/bold cyan]

    Ejemplos:
      python main.py edit outputs/guion_sueno.json outputs/audio/guion_sueno/voice_output.json outputs/media/guion_sueno/media_output.json
      python main.py edit ... --orientation landscape --bgm-vol 0.05
    """
    from agents.specialists.video.editor_agent import EditorAgent
    from pathlib import Path
    import json as _json

    for p in (script_file, voice_file, media_file):
        if not Path(p).exists():
            console.print(f"[red]No se encuentra: {p}[/red]")
            raise typer.Exit(1)

    if not output_dir:
        output_dir = str(Path("outputs") / "final" / Path(script_file).stem)

    console.print(Panel(
        f"[bold]Guión:[/bold]   {script_file}\n"
        f"[bold]Audio:[/bold]   {voice_file}\n"
        f"[bold]Media:[/bold]   {media_file}\n"
        f"[bold]Salida:[/bold]  {output_dir}  ·  [bold]Orientación:[/bold] {orientation}  ·  [bold]BGM vol:[/bold] {bgm_vol}",
        title="[bold cyan]IA-Agency · EditorAgent[/bold cyan]",
        border_style="cyan",
    ))

    with console.status("[dim]Ensamblando video (puede tardar varios minutos)...[/dim]"):
        result = EditorAgent().run_from_files(
            script_json=script_file,
            voice_json=voice_file,
            media_json=media_file,
            output_dir=output_dir,
            orientation=orientation,
            bgm_file=bgm,
            bgm_volume=bgm_vol,
        )

    mins, secs = divmod(int(result.duration_seconds), 60)
    console.print()
    console.print(Panel(
        f"[bold yellow]{Path(result.video_file).name}[/bold yellow]\n\n"
        f"[dim]Resolución:[/dim]  {result.width}×{result.height}  ·  "
        f"[dim]Duración:[/dim] [green]{mins}m {secs:02d}s[/green]  ·  "
        f"[dim]Tamaño:[/dim] [green]{result.file_size_mb} MB[/green]\n"
        f"[dim]Secciones:[/dim]   {result.sections_processed}  ·  "
        f"[dim]Ruta:[/dim] {result.video_file}",
        title="[bold green]Video ensamblado[/bold green]",
        border_style="green",
    ))


# ─────────────────────────────────────────
#  MEDIA — descarga clips de Pexels
# ─────────────────────────────────────────
@app.command()
def media(
    script_file: str = typer.Argument(..., help="JSON del ScriptAgent (outputs/guion.json)"),
    voice_file: str = typer.Argument(..., help="JSON del VoiceAgent (outputs/audio/xxx/voice_output.json)"),
    output_dir: str = typer.Option(None, "--output-dir", "-o", help="Carpeta de salida (por defecto: outputs/media/<nombre>)"),
    orientation: str = typer.Option("portrait", "--orientation", help="portrait (9:16 TikTok) | landscape (16:9 YouTube)"),
    clips: int = typer.Option(4, "--clips", "-c", help="Clips distintos a descargar por sección"),
    pexels_key: str = typer.Option("", "--key", "-k", help="Pexels API key (o configura PEXELS_API_KEY en .env)"),
):
    """[bold cyan]MediaAgent — descarga clips de Pexels para cada sección del video.[/bold cyan]

    Ejemplos:
      python main.py media outputs/guion_sueno.json outputs/audio/guion_sueno/voice_output.json
      python main.py media outputs/guion.json outputs/audio/guion/voice_output.json --orientation landscape
      python main.py media outputs/guion.json outputs/audio/guion/voice_output.json --clips 6
    """
    from agents.specialists.video.media_agent import MediaAgent
    from rich.table import Table
    from rich import box as rbox
    from pathlib import Path
    import json as _json

    script_path = Path(script_file)
    voice_path = Path(voice_file)

    for p in (script_path, voice_path):
        if not p.exists():
            console.print(f"[red]No se encuentra: {p}[/red]")
            raise typer.Exit(1)

    if not output_dir:
        output_dir = str(Path("outputs") / "media" / script_path.stem)

    console.print(Panel(
        f"[bold]Guión:[/bold] {script_file}\n"
        f"[bold]Audio:[/bold] {voice_file}\n"
        f"[bold]Orientación:[/bold] {orientation}  ·  [bold]Clips/sección:[/bold] {clips}  ·  [bold]Salida:[/bold] {output_dir}",
        title="[bold cyan]IA-Agency · MediaAgent[/bold cyan]",
        border_style="cyan",
    ))

    agent = MediaAgent(pexels_api_key=pexels_key)

    with console.status("[dim]Buscando y descargando clips de Pexels...[/dim]"):
        result = agent.run_from_files(
            script_json=script_file,
            voice_json=voice_file,
            output_dir=output_dir,
            orientation=orientation,
            clips_per_section=clips,
        )

    # ── Resumen ──
    total_clips = sum(len(s.clips) for s in result.sections)
    total_video = sum(s.total_clip_duration for s in result.sections)
    total_audio = sum(s.target_duration for s in result.sections)
    mins_v, secs_v = divmod(int(total_video), 60)
    mins_a, secs_a = divmod(int(total_audio), 60)

    console.print()
    console.print(Panel(
        f"[dim]Clips descargados:[/dim] [green]{total_clips}[/green]  ·  "
        f"[dim]Video total:[/dim] [green]{mins_v}m {secs_v:02d}s[/green]  ·  "
        f"[dim]Audio a cubrir:[/dim] {mins_a}m {secs_a:02d}s\n"
        f"[dim]Guardado en:[/dim] {output_dir}",
        title="[bold green]Media descargada[/bold green]",
        border_style="green",
    ))

    # ── Tabla de secciones ──
    table = Table(title="Clips por sección", border_style="cyan", box=rbox.ROUNDED)
    table.add_column("#", style="dim", width=5)
    table.add_column("Clips", justify="right", style="yellow", width=6)
    table.add_column("Video", justify="right", style="green", width=8)
    table.add_column("Audio", justify="right", style="dim", width=8)
    table.add_column("Cobertura", style="cyan", width=10)

    for s in result.sections:
        label = "hook" if s.section_id == 0 else "outro" if s.section_id == 999 else str(s.section_id)
        pct = int(s.total_clip_duration / s.target_duration * 100) if s.target_duration else 0
        mv, sv = divmod(int(s.total_clip_duration), 60)
        ma, sa = divmod(int(s.target_duration), 60)
        bar = ("█" * (pct // 10)) + ("░" * (10 - pct // 10))
        table.add_row(label, str(len(s.clips)), f"{mv}m{sv:02d}s", f"{ma}m{sa:02d}s", bar)

    console.print()
    console.print(table)

    # Guardar metadatos
    meta_file = Path(output_dir) / "media_output.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        _json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    console.print(f"\n[dim]Metadatos guardados en {meta_file}[/dim]")


# ─────────────────────────────────────────
#  VOICE — TTS con timestamps
# ─────────────────────────────────────────
@app.command()
def voice(
    script_file: str = typer.Argument(..., help="Ruta al JSON generado por 'script' (ej: outputs/guion.json)"),
    output_dir: str = typer.Option(None, "--output-dir", "-o", help="Carpeta de salida (por defecto: outputs/audio/<nombre>)"),
    provider: str = typer.Option("edge", "--provider", "-p", help="edge (gratis) | elevenlabs (premium)"),
    language: str = typer.Option("es", "--lang", "-l", help="es | en"),
    voice_name: str = typer.Option(None, "--voice", "-v", help="Forzar voz específica (ej: es-ES-AlvaroNeural)"),
    el_key: str = typer.Option("", "--el-key", help="API key de ElevenLabs (o configura ELEVENLABS_API_KEY en .env)"),
    list_voices_flag: bool = typer.Option(False, "--list-voices", help="Lista voces disponibles y termina"),
):
    """[bold cyan]VoiceAgent — convierte el guión JSON en audio MP3 con timestamps.[/bold cyan]

    Ejemplos:
      python main.py voice outputs/guion_sueno.json
      python main.py voice outputs/guion.json --provider elevenlabs --el-key sk-xxx
      python main.py voice outputs/guion.json --voice es-MX-JorgeNeural
      python main.py voice outputs/guion.json --list-voices
    """
    from agents.specialists.video.voice_agent import VoiceAgent
    import json as _json
    from pathlib import Path

    agent = VoiceAgent(elevenlabs_api_key=el_key)

    if list_voices_flag:
        voices = VoiceAgent.list_voices(language)
        console.print(f"\n[bold cyan]Voces Edge TTS ({language}*):[/bold cyan]")
        for v in voices:
            console.print(f"  [yellow]{v}[/yellow]")
        return

    script_path = Path(script_file)
    if not script_path.exists():
        console.print(f"[red]No se encuentra: {script_file}[/red]")
        raise typer.Exit(1)

    # Directorio de salida automático
    if not output_dir:
        stem = script_path.stem
        output_dir = str(Path("outputs") / "audio" / stem)

    console.print(Panel(
        f"[bold]Guión:[/bold] {script_file}\n"
        f"[bold]Proveedor:[/bold] {provider}  ·  [bold]Idioma:[/bold] {language}  ·  [bold]Salida:[/bold] {output_dir}",
        title="[bold cyan]IA-Agency · VoiceAgent[/bold cyan]",
        border_style="cyan",
    ))

    with console.status(f"[dim]Sintetizando audio con {provider}...[/dim]"):
        result = agent.run_from_file(
            script_json_path=script_file,
            output_dir=output_dir,
            language=language,
            provider=provider,
            voice_override=voice_name if voice_name else None,
        )

    # ── Resumen ──
    mins, secs = divmod(int(result.total_duration_seconds), 60)
    total_words = sum(len(s.word_timestamps) for s in result.sections)

    console.print()
    console.print(Panel(
        f"[bold yellow]{result.voice_name}[/bold yellow] ({result.provider})\n\n"
        f"[dim]Duración total:[/dim] [green]{mins}m {secs:02d}s[/green]  ·  "
        f"[dim]Palabras con timestamp:[/dim] {total_words}\n"
        f"[dim]Audio completo:[/dim] {result.full_audio_file}",
        title="[bold green]Audio generado[/bold green]",
        border_style="green",
    ))

    # ── Tabla de secciones ──
    from rich.table import Table
    from rich import box as rbox
    table = Table(title="Secciones de audio", border_style="cyan", box=rbox.ROUNDED)
    table.add_column("#", style="dim", width=4)
    table.add_column("Archivo", style="dim")
    table.add_column("Duración", justify="right", style="yellow", width=9)
    table.add_column("Palabras", justify="right", style="dim", width=9)

    for s in result.sections:
        label = "hook" if s.section_id == 0 else "outro" if s.section_id == 999 else str(s.section_id)
        m2, s2 = divmod(int(s.duration_seconds), 60)
        table.add_row(label, Path(s.audio_file).name, f"{m2}m {s2:02d}s", str(len(s.word_timestamps)))
    console.print()
    console.print(table)

    # Guardar metadatos
    meta_file = Path(output_dir) / "voice_output.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        _json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    console.print(f"\n[dim]Metadatos guardados en {meta_file}[/dim]")


# ─────────────────────────────────────────
#  VIDEO SCRIPT — guión para YouTube/TikTok
# ─────────────────────────────────────────
@app.command()
def script(
    topic: str = typer.Argument(..., help='Tema del video, ej: "Los 5 hacks de sueño de los CEOs"'),
    niche: str = typer.Option("biohacking", "--niche", "-n", help="biohacking | finanzas | motivacion | tecnologia | curiosidades"),
    duration: int = typer.Option(10, "--duration", "-d", help="Duración en minutos (1-20)"),
    platform: str = typer.Option("both", "--platform", "-p", help="youtube | tiktok | both"),
    language: str = typer.Option("es", "--lang", "-l", help="Idioma: es | en"),
    output: str = typer.Option(None, "--output", "-o", help="Guardar en outputs/<archivo>.json"),
    show_narration: bool = typer.Option(False, "--narration", help="Mostrar texto completo del guión"),
):
    """[bold cyan]ScriptAgent — genera guiones estructurados para YouTube y TikTok.[/bold cyan]

    Ejemplos:
      python main.py script "Los 5 hacks de sueño que usan los CEOs" --niche biohacking
      python main.py script "Cómo invertir 100€ al mes" --niche finanzas --duration 15
      python main.py script "El truco mental que duplica tu productividad" --niche motivacion -d 3 -p tiktok
    """
    from agents.specialists.video.script_agent import ScriptAgent
    from tools.file_tool import save_to_file
    from rich.table import Table
    from rich import box as rbox

    console.print(Panel(
        f"[bold]Tema:[/bold] {topic}\n"
        f"[bold]Nicho:[/bold] {niche}  ·  [bold]Duración:[/bold] {duration} min  ·  [bold]Plataforma:[/bold] {platform}",
        title="[bold cyan]IA-Agency · ScriptAgent[/bold cyan]",
        border_style="cyan",
    ))

    with console.status("[dim]Generando guión con IA...[/dim]"):
        video_script = ScriptAgent().run(
            topic=topic,
            niche=niche,
            duration_minutes=duration,
            platform=platform,
            language=language,
        )

    # ── Resumen ──
    mins, secs = divmod(video_script.total_duration_seconds, 60)
    console.print()
    console.print(Panel(
        f"[bold yellow]{video_script.youtube_title}[/bold yellow]\n\n"
        f"[dim]Audiencia:[/dim] {video_script.target_audience}\n"
        f"[dim]CPM estimado:[/dim] [green]{video_script.estimated_cpm_range}[/green]\n"
        f"[dim]Duración total:[/dim] {mins}m {secs}s  ·  "
        f"[dim]Palabras:[/dim] ~{video_script.total_words()}  ·  "
        f"[dim]Secciones:[/dim] {len(video_script.sections)}",
        title="[bold green]Guión generado[/bold green]",
        border_style="green",
    ))

    # ── Tabla de secciones ──
    table = Table(title="Estructura del guión", border_style="cyan", box=rbox.ROUNDED)
    table.add_column("#", style="dim", width=3)
    table.add_column("Sección", style="bold white", min_width=28)
    table.add_column("Duración", justify="right", style="yellow", width=9)
    table.add_column("Keywords visuales", style="dim", min_width=30)

    for s in video_script.sections:
        m, sc = divmod(s.duration_seconds, 60)
        table.add_row(
            str(s.section_id),
            s.title,
            f"{m}m {sc:02d}s",
            ", ".join(s.visual_keywords[:4]),
        )
    console.print()
    console.print(table)

    # ── Thumbnail & TikTok ──
    console.print()
    console.print(f"[bold]Thumbnail:[/bold] [dim]{video_script.thumbnail_concept}[/dim]")
    console.print(f"[bold]TikTok caption:[/bold] [dim]{video_script.tiktok_caption}[/dim]")
    console.print(f"[bold]Tags YouTube:[/bold] [dim]{', '.join(video_script.youtube_tags[:8])}...[/dim]")

    # ── Narración completa opcional ──
    if show_narration:
        _panel("Guión completo", video_script.full_narration(), "magenta")

    # ── Guardar ──
    if output:
        import json
        content = json.dumps(video_script.to_dict(), ensure_ascii=False, indent=2)
        fname = output if output.endswith(".json") else output + ".json"
        info = save_to_file(fname, content)
        console.print(f"\n[dim]Guión guardado en {info['saved']}[/dim]")
    else:
        console.print("\n[dim]Tip: usa [bold]--output guion.json[/bold] para guardar · [bold]--narration[/bold] para ver el texto completo[/dim]")


# ─────────────────────────────────────────
#  PIPELINE — todo en uno
# ─────────────────────────────────────────
@app.command()
def pipeline(
    topic: str        = typer.Argument(..., help='Tema del video, ej: "Los 5 hacks de sueño de los CEOs"'),
    niche: str        = typer.Option("biohacking", "--niche",       "-n", help="biohacking | finanzas | motivacion | tecnologia | curiosidades"),
    duration: int     = typer.Option(10,           "--duration",    "-d", help="Duración en minutos (1-20)"),
    platform: str     = typer.Option("both",       "--platform",    "-p", help="youtube | tiktok | both"),
    language: str     = typer.Option("es",         "--lang",        "-l", help="es | en"),
    orientation: str  = typer.Option("portrait",   "--orientation",       help="portrait (TikTok 9:16) | landscape (YouTube 16:9)"),
    tts: str          = typer.Option("edge",       "--tts",               help="edge (gratis) | elevenlabs (premium)"),
    clips: int        = typer.Option(4,            "--clips",       "-c", help="Clips Pexels por sección"),
    bgm_vol: float    = typer.Option(0.08,         "--bgm-vol",           help="Volumen música de fondo 0.0-1.0"),
    whisper: str      = typer.Option("small",      "--whisper",     "-w", help="Modelo Whisper: tiny|base|small|medium"),
    output_base: str  = typer.Option("outputs",    "--output-base",       help="Carpeta raíz de salida"),
    skip_subtitle: bool = typer.Option(False,      "--no-subtitle",       help="Omitir subtítulos (más rápido)"),
    publish_to: str   = typer.Option("",           "--publish",           help="Subir a: youtube | tiktok | youtube,tiktok (requiere --yt-secrets / --tt-token)"),
    yt_secrets: str   = typer.Option("",           "--yt-secrets",        help="client_secrets.json de Google Cloud"),
    yt_privacy: str   = typer.Option("private",    "--yt-privacy",        help="private | unlisted | public"),
    tt_token: str     = typer.Option("",           "--tt-token",          help="TikTok access_token"),
):
    """[bold cyan]PIPELINE completo — de tema a video listo en un solo comando.[/bold cyan]

    Ejecuta en orden: ScriptAgent → VoiceAgent → MediaAgent → EditorAgent → SubtitleAgent → (PublishAgent)

    Ejemplos:
      python main.py pipeline "Los 5 hacks de sueño de los CEOs" --niche biohacking
      python main.py pipeline "Cómo invertir 100€" --niche finanzas --duration 15 --orientation landscape
      python main.py pipeline "Tema" --niche motivacion --no-subtitle
      python main.py pipeline "Tema" --niche biohacking --publish youtube --yt-secrets client_secrets.json --yt-privacy public
    """
    from pathlib import Path
    import json as _json
    import time

    from agents.specialists.video.script_agent  import ScriptAgent
    from agents.specialists.video.voice_agent   import VoiceAgent
    from agents.specialists.video.media_agent   import MediaAgent
    from agents.specialists.video.editor_agent  import EditorAgent
    from agents.specialists.video.subtitle_agent import SubtitleAgent

    # ── Slug para carpetas ───────────────────────────────────────────────────
    slug = topic[:40].lower()
    slug = "".join(c if c.isalnum() or c in " _" else "" for c in slug).strip().replace(" ", "_")
    base = Path(output_base)

    script_dir = base
    audio_dir  = base / "audio"  / slug
    media_dir  = base / "media"  / slug
    final_dir  = base / "final"  / slug

    script_json = base / f"{slug}.json"

    def _step(n: int, total: int, name: str) -> None:
        console.rule(f"[bold cyan]Paso {n}/{total} — {name}[/bold cyan]")

    total_steps = 5 if not skip_subtitle else 4
    if publish_to:
        total_steps += 1

    t0 = time.time()

    # ── 1. ScriptAgent ───────────────────────────────────────────────────────
    _step(1, total_steps, "ScriptAgent — generando guión")
    with console.status("[dim]Escribiendo guión con IA...[/dim]"):
        video_script = ScriptAgent().run(
            topic=topic, niche=niche,
            duration_minutes=duration,
            platform=platform, language=language,
        )
    script_data = video_script.to_dict()
    script_json.parent.mkdir(parents=True, exist_ok=True)
    with open(script_json, "w", encoding="utf-8") as f:
        _json.dump(script_data, f, ensure_ascii=False, indent=2)
    mins, secs = divmod(video_script.total_duration_seconds, 60)
    console.print(f"  [green]OK[/green] {video_script.youtube_title[:70]}  ({mins}m {secs:.0f}s · {len(video_script.sections)} secciones)")

    # ── 2. VoiceAgent ────────────────────────────────────────────────────────
    _step(2, total_steps, "VoiceAgent — sintetizando audio")
    with console.status(f"[dim]TTS con {tts}...[/dim]"):
        voice_output = VoiceAgent().run(
            script_data=script_data,
            output_dir=str(audio_dir),
            language=language,
            provider=tts,
        )
    voice_data = voice_output.to_dict()
    voice_json = audio_dir / "voice_output.json"
    with open(voice_json, "w", encoding="utf-8") as f:
        _json.dump(voice_data, f, ensure_ascii=False, indent=2)
    total_mins, total_secs = divmod(voice_output.total_duration_seconds, 60)
    console.print(f"  [green]OK[/green] {voice_output.voice_name}  ({total_mins}m {total_secs:.0f}s)")

    # ── 3. MediaAgent ────────────────────────────────────────────────────────
    _step(3, total_steps, "MediaAgent — descargando clips Pexels")
    with console.status("[dim]Buscando y descargando clips...[/dim]"):
        media_output = MediaAgent().run(
            script_data=script_data,
            voice_data=voice_data,
            output_dir=str(media_dir),
            orientation=orientation,
            clips_per_section=clips,
        )
    media_data = media_output.to_dict()
    media_json = media_dir / "media_output.json"
    with open(media_json, "w", encoding="utf-8") as f:
        _json.dump(media_data, f, ensure_ascii=False, indent=2)
    total_clips = sum(len(s.clips) for s in media_output.sections)
    console.print(f"  [green]OK[/green] {total_clips} clips descargados en {len(media_output.sections)} secciones")

    # ── 4. EditorAgent ───────────────────────────────────────────────────────
    _step(4, total_steps, "EditorAgent — ensamblando video")
    with console.status("[dim]Ensamblando video (puede tardar varios minutos)...[/dim]"):
        editor_output = EditorAgent().run(
            script_data=script_data,
            voice_data=voice_data,
            media_data=media_data,
            output_dir=str(final_dir),
            orientation=orientation,
            bgm_volume=bgm_vol,
        )
    emins, esecs = divmod(int(editor_output.duration_seconds), 60)
    console.print(f"  [green]OK[/green] {editor_output.width}×{editor_output.height} · {emins}m {esecs:02d}s · {editor_output.file_size_mb} MB")

    # ── 5. SubtitleAgent ─────────────────────────────────────────────────────
    final_video = editor_output.video_file

    if not skip_subtitle:
        _step(5, total_steps, "SubtitleAgent — transcribiendo y quemando karaoke")
        console.print(f"  [dim]Modelo Whisper: {whisper}  (puede tardar 10-20 min en CPU)[/dim]")
        with console.status("[dim]Transcribiendo y quemando subtítulos...[/dim]"):
            sub_output = SubtitleAgent(whisper_model=whisper).run(
                video_file=editor_output.video_file,
                audio_file=voice_output.full_audio_file,
                output_dir=str(final_dir),
                language=language if language != "auto" else None,
            )
        smins, ssecs = divmod(int(sub_output.duration_seconds), 60)
        sub_mb = round(Path(sub_output.video_with_subs).stat().st_size / 1_048_576, 1) if Path(sub_output.video_with_subs).exists() else 0
        console.print(f"  [green]OK[/green] {sub_output.total_words} palabras · {smins}m {ssecs:02d}s · {sub_mb} MB")
        final_video = sub_output.video_with_subs

    # ── 6. PublishAgent (opcional) ───────────────────────────────────────────
    if publish_to:
        from agents.specialists.video.publish_agent import PublishAgent
        _step(total_steps, total_steps, "PublishAgent — subiendo video")
        platform_list = [p.strip() for p in publish_to.split(",") if p.strip()]
        with console.status("[dim]Subiendo...[/dim]"):
            pub_output = PublishAgent(
                youtube_secrets_file=yt_secrets,
                tiktok_access_token=tt_token,
            ).run(
                video_file=final_video,
                script_data=script_data,
                platforms=platform_list,
                youtube_privacy=yt_privacy,
            )
        for r in pub_output.results:
            if r.success:
                console.print(f"  [green]OK[/green] {r.platform}: {r.url}")
            else:
                console.print(f"  [red]FAIL[/red] {r.platform}: {r.error}")

    # ── Resumen final ────────────────────────────────────────────────────────
    elapsed = int(time.time() - t0)
    emins2, esecs2 = divmod(elapsed, 60)
    console.print()
    console.print(Panel(
        f"[bold yellow]{video_script.youtube_title[:80]}[/bold yellow]\n\n"
        f"[dim]Video final:[/dim]  [green]{final_video}[/green]\n"
        f"[dim]Guión JSON:[/dim]   {script_json}\n"
        f"[dim]Tiempo total:[/dim] {emins2}m {esecs2:02d}s",
        title="[bold green]Pipeline completado[/bold green]",
        border_style="green",
    ))


# ─────────────────────────────────────────
#  PUBLISH — sube a YouTube y/o TikTok
# ─────────────────────────────────────────
@app.command()
def publish(
    video_file: str  = typer.Argument(..., help="MP4 final (con subtítulos) a subir"),
    script_file: str = typer.Argument(..., help="JSON del ScriptAgent (para título, descripción, tags)"),
    platforms: str   = typer.Option("youtube", "--platforms", "-p", help="youtube | tiktok | youtube,tiktok"),
    yt_secrets: str  = typer.Option("", "--yt-secrets", help="Ruta a client_secrets.json de Google Cloud"),
    yt_token: str    = typer.Option("youtube_token.json", "--yt-token", help="Archivo de token OAuth2 YouTube (se crea automáticamente)"),
    yt_privacy: str  = typer.Option("private", "--yt-privacy", help="private | unlisted | public"),
    tt_token: str    = typer.Option("", "--tt-token", help="TikTok access_token"),
    tt_privacy: str  = typer.Option("SELF_ONLY", "--tt-privacy", help="SELF_ONLY | MUTUAL_FOLLOW_FRIENDS | PUBLIC_TO_EVERYONE"),
    schedule: str    = typer.Option(None, "--schedule", help="Programar publicación ISO8601 (ej: 2025-06-15T18:00:00Z)"),
):
    """[bold cyan]PublishAgent — sube el video final a YouTube y/o TikTok.[/bold cyan]

    Requisitos YouTube:
      1. Google Cloud Console → activar YouTube Data API v3
      2. Crear credenciales OAuth2 Desktop → descargar client_secrets.json
      3. Primera vez: se abrirá el navegador para autorizar

    Requisitos TikTok:
      1. developers.tiktok.com → crear app → obtener access_token

    Ejemplos:
      python main.py publish outputs/final/guion/video_final_subtitled.mp4 outputs/guion.json --yt-secrets client_secrets.json
      python main.py publish video.mp4 guion.json --platforms youtube,tiktok --yt-privacy public --tt-token xxxxx
      python main.py publish video.mp4 guion.json --yt-privacy private --schedule 2025-06-15T18:00:00Z
    """
    from agents.specialists.video.publish_agent import PublishAgent
    from pathlib import Path
    import json as _json

    for p in (video_file, script_file):
        if not Path(p).exists():
            console.print(f"[red]No se encuentra: {p}[/red]")
            raise typer.Exit(1)

    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]

    console.print(Panel(
        f"[bold]Video:[/bold]      {video_file}\n"
        f"[bold]Guión:[/bold]      {script_file}\n"
        f"[bold]Plataformas:[/bold] {', '.join(platform_list)}  ·  [bold]Privacidad YT:[/bold] {yt_privacy}",
        title="[bold cyan]IA-Agency · PublishAgent[/bold cyan]",
        border_style="cyan",
    ))

    agent = PublishAgent(
        youtube_secrets_file=yt_secrets,
        youtube_token_file=yt_token,
        tiktok_access_token=tt_token,
    )

    with console.status("[dim]Subiendo video...[/dim]"):
        result = agent.run_from_files(
            video_file=video_file,
            script_json=script_file,
            platforms=platform_list,
            schedule_time=schedule,
            youtube_privacy=yt_privacy,
            tiktok_privacy=tt_privacy,
        )

    console.print()
    for r in result.results:
        if r.success:
            console.print(Panel(
                f"[green]Video ID:[/green] {r.video_id}\n"
                f"[green]URL:[/green]      {r.url}",
                title=f"[bold green]{r.platform.upper()} — Subida exitosa[/bold green]",
                border_style="green",
            ))
        else:
            console.print(Panel(
                f"[red]{r.error}[/red]",
                title=f"[bold red]{r.platform.upper()} — Error[/bold red]",
                border_style="red",
            ))

    meta = Path(video_file).parent / "publish_output.json"
    with open(meta, "w", encoding="utf-8") as f:
        _json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    console.print(f"[dim]Resultado en {meta}[/dim]")


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
        ("pipeline <topic>",    "Pipeline completo",       "Script→Voz→Media→Video→Subtítulos→Publish en un solo comando"),
        ("script <topic>",      "ScriptAgent",             "Guiones 1-20 min para YouTube & TikTok (biohacking, finanzas…)"),
        ("voice <json>",        "VoiceAgent",              "TTS con timestamps: Edge TTS (gratis) o ElevenLabs (premium)"),
        ("media <s> <v>",       "MediaAgent",              "Descarga clips Pexels por sección según visual_keywords"),
        ("edit <s> <v> <m>",    "EditorAgent",             "Ensambla clips + narración + BGM en el MP4 final"),
        ("subtitle <v> <a>",    "SubtitleAgent",           "Whisper + karaoke ASS quemado en el video"),
        ("publish <v> <s>",     "PublishAgent",            "Sube a YouTube (OAuth2) y/o TikTok (Content API)"),
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
