"""MerakIA — Panel de control web (Streamlit)."""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("PYTHONUTF8", "1")

import streamlit as st

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MerakIA · Panel de Agentes",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Gradient header */
  .merakia-header {
    background: linear-gradient(135deg, #7C3AED, #A855F7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -0.5px;
  }
  /* Agent result box */
  .result-box {
    background: #1E293B;
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-top: 0.8rem;
  }
  /* Metric cards */
  div[data-testid="metric-container"] {
    background: #1E293B;
    border: 1px solid rgba(124,58,237,0.25);
    border-radius: 10px;
    padding: 0.8rem 1rem;
  }
  /* Sidebar title */
  .sidebar-brand {
    font-size: 1.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7C3AED, #A855F7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
  }
  /* Hide Streamlit branding */
  #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">🤖 MerakIA</div>', unsafe_allow_html=True)
    st.caption("Agencia de Inteligencia Artificial")
    st.divider()

    page = st.radio(
        "Navegación",
        options=["🏠 Dashboard", "💬 Chat", "📋 Project Manager", "🌐 Web Developer",
                 "📣 Contenido & Marketing", "🤖 Chatbot Specialist", "⚡ Agente Autónomo",
                 "🎬 VideoStudio", "🚀 Pipeline Completo", "🎯 ProspectorIA",
                 "📊 Base de Datos"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("v1.0 · Claude Sonnet 4.6")


# ─── Helper ───────────────────────────────────────────────────────────────────
def stream_write(text: str, container=None) -> None:
    """Simula efecto de escritura progresiva."""
    target = container or st
    words = text.split(" ")
    result = ""
    placeholder = target.empty()
    for word in words:
        result += word + " "
        placeholder.markdown(result + "▌")
        time.sleep(0.008)
    placeholder.markdown(result.strip())


def download_button(content: str, filename: str) -> None:
    st.download_button(
        label=f"⬇️ Descargar {filename}",
        data=content.encode("utf-8"),
        file_name=filename,
        mime="text/plain",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGES
# ══════════════════════════════════════════════════════════════════════════════

# ─── Dashboard ────────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.markdown('<div class="merakia-header">MerakIA · Panel de Agentes IA</div>',
                unsafe_allow_html=True)
    st.markdown("**Inteligencia Artificial que impulsa tu negocio**")
    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Agentes activos", "11")
    col2.metric("Workflows", "3")
    col3.metric("Herramientas", "4")
    col4.metric("Modelo", "Sonnet 4.6")

    st.divider()
    st.subheader("🚀 Agentes disponibles")

    agents_info = [
        ("🎯", "ProspectorIA", "Busca negocios, analiza sus dolores y genera ofertas irresistibles"),
        ("💬", "Chat", "Asistente conversacional con memoria de sesión"),
        ("📋", "Project Manager", "Orquesta el equipo completo para proyectos de cliente"),
        ("🌐", "Web Developer", "Genera landing pages y código web listo para producción"),
        ("📣", "Contenido & Marketing", "Copy, posts, emails y estrategia de contenidos"),
        ("🤖", "Chatbot Specialist", "Diseña chatbots personalizados para negocios"),
        ("⚡", "Autónomo", "Ejecuta tareas complejas con herramientas (calc, fecha, archivos)"),
        ("🎬", "VideoStudio", "Guión + Voz + Clips + Edición + Subtítulos karaoke"),
        ("📤", "PublishAgent", "Sube videos a YouTube y TikTok con metadata optimizada"),
        ("🚀", "Pipeline Completo", "Tema → video listo en un solo paso automático"),
    ]

    cols = st.columns(3)
    for i, (icon, name, desc) in enumerate(agents_info):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="result-box">
              <b>{icon} {name}</b><br>
              <small style="color:#94A3B8">{desc}</small>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.info("👈 Selecciona un agente en el menú lateral para empezar.", icon="ℹ️")


# ─── Chat ─────────────────────────────────────────────────────────────────────
elif page == "💬 Chat":
    st.subheader("💬 Chat con IA")

    # Config
    with st.expander("⚙️ Configuración del chatbot", expanded=False):
        bot_name = st.text_input("Nombre del asistente", value="Asistente MerakIA")
        system_prompt = st.text_area(
            "System prompt",
            value="Eres un asistente de IA profesional de MerakIA. Eres útil, preciso y conciso.",
            height=80,
        )
        if st.button("🔄 Reiniciar conversación"):
            st.session_state.chat_history = []
            st.session_state.chat_agent = None
            st.rerun()

    # Init agent & history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_agent" not in st.session_state:
        st.session_state.chat_agent = None

    # Display history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Escribe tu mensaje..."):
        # Lazy-load agent
        if st.session_state.chat_agent is None:
            from agents.chatbot_agent import ChatbotAgent
            st.session_state.chat_agent = ChatbotAgent(
                name=bot_name, system_prompt=system_prompt
            )

        # Show user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        # Get response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Pensando..."):
                reply = st.session_state.chat_agent.chat(prompt)
            st.markdown(reply)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})


# ─── Project Manager ──────────────────────────────────────────────────────────
elif page == "📋 Project Manager":
    st.subheader("📋 Project Manager Agent")
    st.caption("Describe el proyecto del cliente — el PM analiza, asigna tareas y entrega el resultado.")

    request = st.text_area(
        "Solicitud del cliente",
        placeholder='Ej: "Quiero un chatbot para mi restaurante italiano en Barcelona que gestione reservas y responda preguntas sobre la carta"',
        height=120,
    )

    if st.button("🚀 Ejecutar proyecto", type="primary", disabled=not request.strip()):
        from agents.pm_agent import ProjectManagerAgent

        pm = ProjectManagerAgent()
        progress = st.progress(0, text="Analizando requisitos...")

        with st.spinner("El equipo está trabajando..."):
            progress.progress(20, text="PM analizando y planificando...")
            result = pm.run(request, verbose=False)
            progress.progress(100, text="¡Completado!")

        # Plan table
        if result["plan"] and result["plan"].get("tasks"):
            st.divider()
            st.markdown("**📊 Plan del proyecto**")
            plan = result["plan"]
            if plan.get("timeline"):
                st.caption(f"⏱️ Estimación: {plan['timeline']}")

            cols = st.columns([1, 3])
            cols[0].markdown("**Agente**")
            cols[1].markdown("**Tarea**")
            for task in plan["tasks"]:
                c1, c2 = st.columns([1, 3])
                c1.markdown(f"`{task['agent']}`")
                c2.markdown(task["task"][:120] + ("..." if len(task["task"]) > 120 else ""))

        # Delivery
        st.divider()
        st.markdown("**📄 Entrega final al cliente**")
        st.markdown(result["final_delivery"])
        st.divider()
        download_button(result["final_delivery"], "entrega_cliente.md")


# ─── Web Developer ────────────────────────────────────────────────────────────
elif page == "🌐 Web Developer":
    st.subheader("🌐 Web Developer Agent")
    st.caption("Genera código web listo para producción — landing pages, componentes, APIs.")

    task = st.text_area(
        "¿Qué necesitas desarrollar?",
        placeholder='Ej: "Landing page moderna para academia de yoga online con sección hero, servicios y formulario de contacto"',
        height=120,
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        output_file = st.text_input("Nombre de archivo (opcional)", placeholder="landing.html")
    with col2:
        max_tokens = st.selectbox("Tamaño output", [8000, 16000, 32000], index=1)

    if st.button("⚡ Generar código", type="primary", disabled=not task.strip()):
        from agents.specialists.web_developer import WebDeveloperAgent
        from tools.file_tool import save_to_file

        with st.spinner("Desarrollando... puede tardar 30-60s para páginas completas"):
            result = WebDeveloperAgent().run(task, max_tokens=max_tokens)

        # Strip markdown fences if present
        if result.strip().startswith("```"):
            lines = result.splitlines()
            result = "\n".join(l for l in lines if not l.strip().startswith("```"))

        st.success("✅ Código generado")

        tab1, tab2 = st.tabs(["📄 Código", "👁️ Preview"])
        with tab1:
            st.code(result, language="html" if "html" in task.lower() else "text")
        with tab2:
            if "html" in result.lower()[:50]:
                st.components.v1.html(result, height=600, scrolling=True)
            else:
                st.info("Preview disponible solo para HTML completo.")

        if output_file:
            info = save_to_file(output_file, result)
            st.caption(f"💾 Guardado en `{info['saved']}`")

        download_button(result, output_file or "output.html")


# ─── Content & Marketing ──────────────────────────────────────────────────────
elif page == "📣 Contenido & Marketing":
    st.subheader("📣 Content & Marketing Agent")
    st.caption("Copy, posts, emails, artículos SEO y estrategia de contenidos.")

    content_type = st.selectbox(
        "Tipo de contenido",
        ["Post Instagram", "Post LinkedIn", "Email marketing", "Blog post SEO",
         "Copy para anuncio", "Guión para vídeo", "Descripción de producto", "Otro"],
    )

    brief = st.text_area(
        "Brief del contenido",
        placeholder='Ej: "3 posts de Instagram para una cafetería de especialidad en Madrid, tono cercano y moderno, enfocados en el proceso del café"',
        height=120,
    )

    tone = st.select_slider(
        "Tono",
        options=["Muy formal", "Formal", "Neutro", "Cercano", "Muy cercano/divertido"],
        value="Cercano",
    )

    if st.button("✍️ Generar contenido", type="primary", disabled=not brief.strip()):
        from agents.specialists.content_marketing import ContentMarketingAgent

        full_brief = f"Tipo: {content_type}. Tono: {tone}. {brief}"
        with st.spinner("Creando contenido..."):
            result = ContentMarketingAgent().run(full_brief)

        st.divider()
        st.markdown(result)
        st.divider()
        download_button(result, "contenido.md")


# ─── Chatbot Specialist ───────────────────────────────────────────────────────
elif page == "🤖 Chatbot Specialist":
    st.subheader("🤖 Chatbot Specialist Agent")
    st.caption("Diseña chatbots personalizados para cualquier negocio o sector.")

    col1, col2 = st.columns(2)
    with col1:
        business_name = st.text_input("Nombre del negocio", placeholder="La Dolce Vita")
        sector = st.selectbox(
            "Sector",
            ["Restaurante / Bar", "E-commerce", "Salud / Clínica", "Inmobiliaria",
             "Educación", "Servicios profesionales", "Hotel / Turismo", "Otro"],
        )
    with col2:
        objectives = st.multiselect(
            "Objetivos del chatbot",
            ["Gestión de reservas", "Atención al cliente", "FAQ / Información",
             "Generación de leads", "Soporte técnico", "Ventas", "Seguimiento de pedidos"],
            default=["Atención al cliente", "FAQ / Información"],
        )
        tone_bot = st.select_slider(
            "Personalidad del bot",
            options=["Muy formal", "Profesional", "Amigable", "Cercano", "Divertido"],
            value="Amigable",
        )

    extra = st.text_area("Contexto adicional (opcional)",
                         placeholder="Horarios, servicios especiales, información relevante...",
                         height=80)

    if st.button("🤖 Diseñar chatbot", type="primary", disabled=not business_name.strip()):
        from agents.specialists.chatbot_specialist import ChatbotSpecialist

        brief = (
            f"Negocio: {business_name} | Sector: {sector} | "
            f"Objetivos: {', '.join(objectives)} | Personalidad: {tone_bot}. "
            f"{extra}"
        )
        with st.spinner("Diseñando chatbot..."):
            result = ChatbotSpecialist().run(brief)

        st.divider()
        st.markdown(result)
        st.divider()
        download_button(result, f"chatbot_{business_name.lower().replace(' ', '_')}.md")


# ─── Autonomous Agent ─────────────────────────────────────────────────────────
elif page == "⚡ Agente Autónomo":
    st.subheader("⚡ Agente Autónomo")
    st.caption("Ejecuta tareas complejas de forma independiente usando herramientas.")

    with st.expander("🛠️ Herramientas disponibles"):
        t1, t2, t3, t4 = st.columns(4)
        t1.info("📅 **get_current_datetime**\nFecha y hora actual")
        t2.info("🔢 **calculate**\nOperaciones matemáticas")
        t3.info("💾 **save_to_file**\nGuardar en outputs/")
        t4.info("📂 **read_from_file**\nLeer de outputs/")

    task = st.text_area(
        "Tarea para el agente",
        placeholder='Ej: "¿Qué día es hoy? Calcula el 21% de IVA de 3500€ y guarda el resultado en iva_calculo.txt"',
        height=100,
    )

    if st.button("🚀 Ejecutar tarea", type="primary", disabled=not task.strip()):
        from agents.autonomous_agent import AutonomousAgent

        with st.spinner("Agente trabajando..."):
            result = AutonomousAgent().run(task)

        st.divider()
        st.markdown("**Resultado:**")
        st.markdown(result)
        st.divider()
        download_button(result, "resultado_autonomo.txt")


# ─── VideoStudio ──────────────────────────────────────────────────────────────
elif page == "🎬 VideoStudio":
    st.subheader("🎬 VideoStudio — Agentes de Vídeo")
    st.caption("Ejecuta cada agente por separado o usa el Pipeline completo.")

    tab_script, tab_voice, tab_media, tab_edit, tab_sub, tab_pub = st.tabs(
        ["📝 Guión", "🎙️ Voz", "🎞️ Media", "✂️ Edición", "💬 Subtítulos", "📤 Publicar"]
    )

    # ── Tab: Guión ────────────────────────────────────────────────────────────
    with tab_script:
        st.markdown("**ScriptAgent** — genera guiones optimizados para YouTube y TikTok")
        col1, col2, col3 = st.columns(3)
        with col1:
            topic = st.text_input("Tema del vídeo", placeholder="Los 5 hacks de sueño de los CEOs")
            niche = st.selectbox("Nicho", ["biohacking", "finanzas", "motivacion", "tecnologia", "curiosidades"])
        with col2:
            duration = st.slider("Duración (min)", 1, 20, 10)
            platform = st.selectbox("Plataforma", ["both", "youtube", "tiktok"])
        with col3:
            language = st.selectbox("Idioma", ["es", "en"])
            show_narration = st.checkbox("Ver narración completa")

        if st.button("📝 Generar guión", type="primary", disabled=not topic.strip(), key="btn_script"):
            from agents.specialists.video.script_agent import ScriptAgent
            import json

            with st.spinner("Generando guión con IA..."):
                vs = ScriptAgent().run(topic=topic, niche=niche,
                                      duration_minutes=duration, platform=platform, language=language)

            st.success(f"✅ {vs.youtube_title}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Duración", f"{int(vs.total_duration_seconds//60)}m {int(vs.total_duration_seconds%60)}s")
            c2.metric("Secciones", len(vs.sections))
            c3.metric("CPM estimado", vs.estimated_cpm_range)

            st.divider()
            st.markdown(f"**Thumbnail:** {vs.thumbnail_concept}")
            st.markdown(f"**TikTok caption:** {vs.tiktok_caption}")
            st.markdown(f"**Tags:** {', '.join(vs.youtube_tags[:10])}...")

            # Tabla de secciones
            import pandas as pd
            rows = [{"#": s.section_id, "Sección": s.title,
                     "Duración": f"{int(s.duration_seconds//60)}m{int(s.duration_seconds%60):02d}s",
                     "Keywords": ", ".join(s.visual_keywords[:3])} for s in vs.sections]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if show_narration:
                st.text_area("Narración completa", vs.full_narration(), height=400)

            # Guardar y descargar
            script_dict = vs.to_dict()
            script_json = json.dumps(script_dict, ensure_ascii=False, indent=2)
            st.session_state["script_data"] = script_dict
            st.session_state["script_json"] = script_json
            st.download_button("⬇️ Descargar guión JSON", script_json,
                               file_name=f"guion_{niche}.json", mime="application/json")

    # ── Tab: Voz ──────────────────────────────────────────────────────────────
    with tab_voice:
        st.markdown("**VoiceAgent** — sintetiza el guión en audio MP3 con timestamps")
        st.info("Carga un guión JSON generado por ScriptAgent o usa el de la sesión actual.", icon="ℹ️")

        uploaded_script = st.file_uploader("Guión JSON (opcional si ya generaste uno arriba)", type="json", key="vu_script")
        tts_provider = st.selectbox("Proveedor TTS", ["edge (gratis)", "elevenlabs (premium)"])
        output_audio_dir = st.text_input("Carpeta de salida", value="outputs/audio/video")

        if st.button("🎙️ Sintetizar audio", type="primary", key="btn_voice"):
            import json, tempfile
            from pathlib import Path
            from agents.specialists.video.voice_agent import VoiceAgent

            if uploaded_script:
                script_data = json.load(uploaded_script)
            elif "script_data" in st.session_state:
                script_data = st.session_state["script_data"]
            else:
                st.error("Primero genera un guión en la pestaña 'Guión'.")
                st.stop()

            provider = "edge" if "edge" in tts_provider else "elevenlabs"
            with st.spinner("Sintetizando audio... (puede tardar 1-2 min)"):
                vo = VoiceAgent().run(script_data=script_data, output_dir=output_audio_dir,
                                     language=script_data.get("language", "es"), provider=provider)

            st.success(f"✅ {vo.voice_name} · {int(vo.total_duration_seconds//60)}m {int(vo.total_duration_seconds%60)}s")
            st.markdown(f"**Audio completo:** `{vo.full_audio_file}`")

            # Guardar en session
            voice_dict = vo.to_dict()
            st.session_state["voice_data"] = voice_dict
            voice_json = json.dumps(voice_dict, ensure_ascii=False, indent=2)
            st.download_button("⬇️ Descargar voice_output.json", voice_json,
                               file_name="voice_output.json", mime="application/json")

    # ── Tab: Media ────────────────────────────────────────────────────────────
    with tab_media:
        st.markdown("**MediaAgent** — descarga clips de Pexels por sección")
        col1, col2 = st.columns(2)
        with col1:
            orientation = st.selectbox("Orientación", ["portrait (9:16)", "landscape (16:9)"])
            clips_per_section = st.slider("Clips por sección", 2, 8, 4)
        with col2:
            output_media_dir = st.text_input("Carpeta de salida", value="outputs/media/video", key="media_out")

        if st.button("🎞️ Descargar clips", type="primary", key="btn_media"):
            import json
            from agents.specialists.video.media_agent import MediaAgent

            script_data = st.session_state.get("script_data")
            voice_data  = st.session_state.get("voice_data")
            if not script_data or not voice_data:
                st.error("Necesitas generar el guión y el audio primero.")
                st.stop()

            orient = "portrait" if "portrait" in orientation else "landscape"
            with st.spinner("Buscando y descargando clips de Pexels..."):
                mo = MediaAgent().run(script_data=script_data, voice_data=voice_data,
                                     output_dir=output_media_dir, orientation=orient,
                                     clips_per_section=clips_per_section)

            total_clips = sum(len(s.clips) for s in mo.sections)
            st.success(f"✅ {total_clips} clips descargados en {len(mo.sections)} secciones")

            media_dict = mo.to_dict()
            st.session_state["media_data"] = media_dict
            st.download_button("⬇️ Descargar media_output.json",
                               json.dumps(media_dict, ensure_ascii=False, indent=2),
                               file_name="media_output.json", mime="application/json")

    # ── Tab: Edición ──────────────────────────────────────────────────────────
    with tab_edit:
        st.markdown("**EditorAgent** — ensambla clips + narración + BGM en el MP4 final")
        col1, col2 = st.columns(2)
        with col1:
            output_final_dir = st.text_input("Carpeta de salida", value="outputs/final/video", key="edit_out")
        with col2:
            bgm_vol = st.slider("Volumen BGM", 0.0, 0.3, 0.08, step=0.01)

        if st.button("✂️ Ensamblar vídeo", type="primary", key="btn_edit"):
            from agents.specialists.video.editor_agent import EditorAgent

            script_data = st.session_state.get("script_data")
            voice_data  = st.session_state.get("voice_data")
            media_data  = st.session_state.get("media_data")
            if not all([script_data, voice_data, media_data]):
                st.error("Completa guión, audio y media primero.")
                st.stop()

            with st.spinner("Ensamblando vídeo... puede tardar varios minutos"):
                eo = EditorAgent().run(script_data=script_data, voice_data=voice_data,
                                      media_data=media_data, output_dir=output_final_dir,
                                      bgm_volume=bgm_vol)

            mins, secs = divmod(int(eo.duration_seconds), 60)
            st.success(f"✅ {eo.width}×{eo.height} · {mins}m {secs:02d}s · {eo.file_size_mb} MB")
            st.markdown(f"**Ruta:** `{eo.video_file}`")
            st.session_state["editor_output"] = eo.to_dict()
            st.session_state["final_video"] = eo.video_file

    # ── Tab: Subtítulos ───────────────────────────────────────────────────────
    with tab_sub:
        st.markdown("**SubtitleAgent** — transcribe con Whisper y quema karaoke")
        col1, col2 = st.columns(2)
        with col1:
            whisper_model = st.selectbox("Modelo Whisper", ["tiny", "base", "small", "medium"], index=2)
        with col2:
            words_per_line = st.slider("Palabras por línea", 2, 6, 4)

        if st.button("💬 Quemar subtítulos", type="primary", key="btn_sub"):
            from agents.specialists.video.subtitle_agent import SubtitleAgent
            from pathlib import Path

            eo = st.session_state.get("editor_output")
            vo = st.session_state.get("voice_data")
            if not eo or not vo:
                st.error("Ensambla el vídeo primero.")
                st.stop()

            video_file = eo["video_file"]
            audio_file = vo["full_audio_file"]
            out_dir    = str(Path(video_file).parent)

            st.info(f"Modelo: {whisper_model} — puede tardar 10-20 min en CPU", icon="⏱️")
            with st.spinner("Transcribiendo y quemando subtítulos..."):
                so = SubtitleAgent(whisper_model=whisper_model).run(
                    video_file=video_file, audio_file=audio_file,
                    output_dir=out_dir, words_per_line=words_per_line,
                )

            mins, secs = divmod(int(so.duration_seconds), 60)
            st.success(f"✅ {so.total_words} palabras · {mins}m {secs:02d}s")
            st.markdown(f"**Video final:** `{so.video_with_subs}`")
            st.session_state["final_video"] = so.video_with_subs

    # ── Tab: Publicar ─────────────────────────────────────────────────────────
    with tab_pub:
        st.markdown("**PublishAgent** — sube a YouTube y/o TikTok")

        platforms = st.multiselect("Plataformas", ["youtube", "tiktok"], default=["youtube"])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**YouTube**")
            yt_secrets = st.text_input("Ruta a client_secrets.json", placeholder="client_secrets.json")
            yt_privacy  = st.selectbox("Privacidad", ["private", "unlisted", "public"])
        with col2:
            st.markdown("**TikTok**")
            tt_token   = st.text_input("TikTok access_token", type="password")
            tt_privacy = st.selectbox("Privacidad TikTok", ["SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS", "PUBLIC_TO_EVERYONE"])

        final_video = st.session_state.get("final_video", "")
        script_data  = st.session_state.get("script_data", {})

        if final_video:
            st.info(f"Video listo: `{final_video}`", icon="🎬")
        else:
            st.warning("Completa el pipeline primero (Guión → Voz → Media → Edición → Subtítulos)", icon="⚠️")

        if st.button("📤 Subir vídeo", type="primary",
                     disabled=not final_video or not platforms, key="btn_pub"):
            from agents.specialists.video.publish_agent import PublishAgent
            from pathlib import Path

            agent = PublishAgent(
                youtube_secrets_file=yt_secrets,
                tiktok_access_token=tt_token,
            )
            with st.spinner("Subiendo vídeo..."):
                result = agent.run(
                    video_file=final_video,
                    script_data=script_data,
                    platforms=platforms,
                    youtube_privacy=yt_privacy,
                    tiktok_privacy=tt_privacy,
                )

            for r in result.results:
                if r.success:
                    st.success(f"✅ {r.platform.upper()}: [{r.url}]({r.url})")
                else:
                    st.error(f"❌ {r.platform.upper()}: {r.error}")


# ─── Pipeline Completo ────────────────────────────────────────────────────────
elif page == "🚀 Pipeline Completo":
    st.subheader("🚀 Pipeline Completo — Tema → Vídeo listo")
    st.caption("Ejecuta todos los agentes en secuencia: Guión → Voz → Media → Edición → Subtítulos → (Publicar)")

    col1, col2, col3 = st.columns(3)
    with col1:
        topic    = st.text_input("Tema del vídeo", placeholder="Los 5 hacks de sueño de los CEOs", key="pl_topic")
        niche    = st.selectbox("Nicho", ["biohacking", "finanzas", "motivacion", "tecnologia", "curiosidades"], key="pl_niche")
        duration = st.slider("Duración (min)", 1, 20, 10, key="pl_dur")
    with col2:
        orientation = st.selectbox("Orientación", ["portrait (TikTok 9:16)", "landscape (YouTube 16:9)"], key="pl_orient")
        tts_prov    = st.selectbox("TTS", ["edge (gratis)", "elevenlabs (premium)"], key="pl_tts")
        whisper_m   = st.selectbox("Whisper", ["tiny", "base", "small", "medium"], index=2, key="pl_whisper")
    with col3:
        skip_sub    = st.checkbox("Omitir subtítulos (más rápido)", key="pl_nosub")
        bgm_v       = st.slider("Volumen BGM", 0.0, 0.3, 0.08, step=0.01, key="pl_bgm")
        output_slug = st.text_input("Nombre carpeta", placeholder="mi_video", key="pl_slug")

    st.divider()
    st.markdown("**Publicar al terminar (opcional)**")
    pub_platforms = st.multiselect("Plataformas", ["youtube", "tiktok"], key="pl_platforms")
    col4, col5 = st.columns(2)
    with col4:
        pl_yt_secrets = st.text_input("client_secrets.json", key="pl_yt_sec")
        pl_yt_privacy = st.selectbox("Privacidad YT", ["private", "unlisted", "public"], key="pl_yt_priv")
    with col5:
        pl_tt_token   = st.text_input("TikTok token", type="password", key="pl_tt")

    st.divider()

    if st.button("🚀 Iniciar pipeline completo", type="primary",
                 disabled=not topic.strip(), key="btn_pipeline"):
        import json
        from pathlib import Path
        from agents.specialists.video.script_agent   import ScriptAgent
        from agents.specialists.video.voice_agent    import VoiceAgent
        from agents.specialists.video.media_agent    import MediaAgent
        from agents.specialists.video.editor_agent   import EditorAgent
        from agents.specialists.video.subtitle_agent import SubtitleAgent

        slug = output_slug.strip() or topic[:30].lower().replace(" ", "_")
        slug = "".join(c for c in slug if c.isalnum() or c == "_")
        orient = "portrait" if "portrait" in orientation else "landscape"
        provider = "edge" if "edge" in tts_prov else "elevenlabs"
        base = Path("outputs")

        progress = st.progress(0)
        status   = st.empty()

        # 1. Script
        status.info("📝 Paso 1/5 — Generando guión...")
        progress.progress(5)
        vs = ScriptAgent().run(topic=topic, niche=niche, duration_minutes=duration,
                               platform="both", language="es")
        script_data = vs.to_dict()
        (base / f"{slug}.json").parent.mkdir(parents=True, exist_ok=True)
        with open(base / f"{slug}.json", "w", encoding="utf-8") as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        progress.progress(15)
        st.success(f"✅ Guión: {vs.youtube_title[:60]}")

        # 2. Voice
        status.info("🎙️ Paso 2/5 — Sintetizando audio...")
        audio_dir = str(base / "audio" / slug)
        vo = VoiceAgent().run(script_data=script_data, output_dir=audio_dir,
                              language="es", provider=provider)
        voice_data = vo.to_dict()
        with open(Path(audio_dir) / "voice_output.json", "w", encoding="utf-8") as f:
            json.dump(voice_data, f, ensure_ascii=False, indent=2)
        progress.progress(30)
        mins_v = int(vo.total_duration_seconds // 60)
        st.success(f"✅ Audio: {vo.voice_name} · {mins_v}m")

        # 3. Media
        status.info("🎞️ Paso 3/5 — Descargando clips Pexels...")
        media_dir = str(base / "media" / slug)
        mo = MediaAgent().run(script_data=script_data, voice_data=voice_data,
                              output_dir=media_dir, orientation=orient, clips_per_section=4)
        media_data = mo.to_dict()
        with open(Path(media_dir) / "media_output.json", "w", encoding="utf-8") as f:
            json.dump(media_data, f, ensure_ascii=False, indent=2)
        total_clips = sum(len(s.clips) for s in mo.sections)
        progress.progress(50)
        st.success(f"✅ Media: {total_clips} clips descargados")

        # 4. Editor
        status.info("✂️ Paso 4/5 — Ensamblando vídeo...")
        final_dir = str(base / "final" / slug)
        eo = EditorAgent().run(script_data=script_data, voice_data=voice_data,
                               media_data=media_data, output_dir=final_dir,
                               orientation=orient, bgm_volume=bgm_v)
        mins_e, secs_e = divmod(int(eo.duration_seconds), 60)
        progress.progress(70)
        st.success(f"✅ Vídeo: {eo.width}×{eo.height} · {mins_e}m {secs_e:02d}s · {eo.file_size_mb} MB")

        # 5. Subtítulos
        final_video = eo.video_file
        if not skip_sub:
            status.info(f"💬 Paso 5/5 — Subtítulos Whisper {whisper_m} (puede tardar 10-20 min)...")
            so = SubtitleAgent(whisper_model=whisper_m).run(
                video_file=eo.video_file,
                audio_file=vo.full_audio_file,
                output_dir=final_dir,
            )
            sub_mb = round(Path(so.video_with_subs).stat().st_size / 1_048_576, 1) if Path(so.video_with_subs).exists() else 0
            progress.progress(90)
            st.success(f"✅ Subtítulos: {so.total_words} palabras · {sub_mb} MB")
            final_video = so.video_with_subs

        # Publicar
        if pub_platforms:
            from agents.specialists.video.publish_agent import PublishAgent
            status.info("📤 Publicando...")
            pub = PublishAgent(youtube_secrets_file=pl_yt_secrets, tiktok_access_token=pl_tt_token)
            pr  = pub.run(video_file=final_video, script_data=script_data,
                          platforms=pub_platforms, youtube_privacy=pl_yt_privacy)
            for r in pr.results:
                if r.success:
                    st.success(f"✅ {r.platform.upper()}: {r.url}")
                else:
                    st.error(f"❌ {r.platform.upper()}: {r.error}")

        progress.progress(100)
        status.empty()
        st.balloons()
        st.success(f"🎉 Pipeline completado — {final_video}")


# ─── ProspectorIA ─────────────────────────────────────────────────────────────
elif page == "🎯 ProspectorIA":
    import pandas as pd
    from agents.specialists.prospector import ProspectorAgent, CRM, ESTADOS, ESTADO_COLORS
    from agents.specialists.prospector.models import ProspectorResult
    from config.settings import settings

    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown("""<style>
    .step-header {
        display:flex; align-items:center; gap:10px;
        padding:10px 14px; border-radius:10px; margin-bottom:6px;
    }
    .step-active  { background:rgba(124,58,237,0.12); border:1px solid rgba(124,58,237,0.4); }
    .step-done    { background:rgba(16,185,129,0.10); border:1px solid rgba(16,185,129,0.35); }
    .step-locked  { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); opacity:.5; }
    .step-num     { width:28px;height:28px;border-radius:50%;display:flex;align-items:center;
                    justify-content:center;font-weight:800;font-size:13px;flex-shrink:0; }
    .num-active   { background:#7C3AED; color:#fff; }
    .num-done     { background:#10b981; color:#fff; }
    .num-locked   { background:rgba(255,255,255,0.1); color:#64748b; }
    .step-title   { font-weight:700; font-size:15px; }
    .chip { display:inline-block;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:700;margin:2px; }
    .chip-alta  { background:rgba(239,68,68,.15);color:#ef4444;border:1px solid #ef4444; }
    .chip-media { background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid #f59e0b; }
    .chip-baja  { background:rgba(16,185,129,.15);color:#10b981;border:1px solid #10b981; }
    </style>""", unsafe_allow_html=True)

    # ── Session state ─────────────────────────────────────────────────────────
    for k, v in [
        ("ps_paso", 1),
        ("ps_tipo", ""), ("ps_ciudad", ""), ("ps_agencia", "MerakIA"),
        ("ps_negocios", []), ("ps_resultados", []), ("ps_sel_idx", 0),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    paso = st.session_state.ps_paso

    # ── Barra de progreso superior ────────────────────────────────────────────
    PASOS = [
        (1, "Nicho & Ciudad"),
        (2, "Negocios"),
        (3, "Análisis"),
        (4, "Dolores"),
        (5, "Pricing & ROI"),
        (6, "Arsenal de venta"),
        (7, "CRM"),
    ]

    st.markdown('<div class="merakia-header">🎯 ProspectorIA</div>', unsafe_allow_html=True)
    st.caption("Plataforma de venta: nicho → análisis → dolor → precio → propuesta → cierre")
    st.divider()

    # Progress chips
    cols_p = st.columns(len(PASOS))
    for i, (n, label) in enumerate(PASOS):
        with cols_p[i]:
            if n < paso:
                st.markdown(f'<div style="text-align:center"><span class="chip chip-baja">✓ {n}</span><br><small style="color:#64748b">{label}</small></div>', unsafe_allow_html=True)
            elif n == paso:
                st.markdown(f'<div style="text-align:center"><span class="chip chip-alta">● {n}</span><br><small style="color:#fff;font-weight:600">{label}</small></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="text-align:center"><span class="chip" style="background:rgba(255,255,255,.05);color:#475569;border:1px solid rgba(255,255,255,.1)">{n}</span><br><small style="color:#475569">{label}</small></div>', unsafe_allow_html=True)

    st.divider()

    # ── Configuración (sidebar colapsable) ───────────────────────────────────
    with st.expander("⚙️ Configuración — API Keys y agencia", expanded=(paso == 1)):
        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            gkey = st.text_input(
                "Google Places API Key",
                value=settings.google_places_api_key,
                type="password",
                help="console.cloud.google.com — gratis hasta $200/mes",
            )
            if gkey:
                settings.google_places_api_key = gkey
        with col_cfg2:
            agencia_input = st.text_input("Nombre de tu agencia", value=st.session_state.ps_agencia)
            st.session_state.ps_agencia = agencia_input

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 1 — Seleccionar nicho y ciudad  /  o entrar un negocio concreto
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 1:
        with st.container():
            st.markdown("### 1️⃣ ¿Cómo quieres empezar?")

            tab_nicho, tab_manual = st.tabs(["🔍 Buscar por nicho", "✏️ Negocio específico"])

            # ── Tab A: búsqueda por nicho (flujo original) ──────────────────
            with tab_nicho:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    NICHOS = [
                        "clínica dental", "clínica estética", "fisioterapia", "veterinaria",
                        "restaurante", "bar", "cafetería", "gimnasio", "peluquería",
                        "inmobiliaria", "taller mecánico", "farmacia", "óptica",
                        "academia de idiomas", "otro",
                    ]
                    tipo_sel = st.selectbox("Tipo de negocio", NICHOS, key="ps_tipo_sel")
                    tipo = st.text_input(
                        "O escribe el nicho libre",
                        value=tipo_sel if tipo_sel != "otro" else "",
                        placeholder="Ej: clínica de podología",
                        key="ps_tipo_libre",
                    )
                    tipo = tipo.strip() or tipo_sel

                with col2:
                    ciudad = st.text_input(
                        "Ciudad o localidad",
                        placeholder="Barcelona, Vilanova i la Geltrú, Madrid...",
                        key="ps_ciudad_input",
                    )

                with col3:
                    limite = st.number_input("Resultados", 5, 50, 15, 5, key="ps_limite")

                btn_buscar = st.button(
                    "🔍 Buscar negocios →",
                    type="primary",
                    disabled=not (tipo and ciudad),
                    key="ps_btn_buscar",
                )

                if btn_buscar:
                    try:
                        with st.spinner(f"Buscando '{tipo}' en {ciudad}..."):
                            agent = ProspectorAgent(nombre_agencia=st.session_state.ps_agencia)
                            negocios = agent.buscar_negocios(tipo=tipo, ciudad=ciudad, limite=limite)
                        st.session_state.ps_negocios = negocios
                        st.session_state.ps_resultados = []
                        st.session_state.ps_tipo = tipo
                        st.session_state.ps_ciudad = ciudad
                        st.session_state.ps_paso = 2
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")

            # ── Tab B: negocio específico (entrada manual) ───────────────────
            with tab_manual:
                st.caption("Introduce un negocio concreto. Buscaremos su ficha en Google Places para traer rating y reseñas; si no lo encontramos, usamos los datos que pongas aquí.")

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    m_nombre = st.text_input(
                        "Nombre del negocio *",
                        placeholder="Ej: Clínica Dental Sorriso",
                        key="ps_m_nombre",
                    )
                    m_ciudad = st.text_input(
                        "Ciudad *",
                        placeholder="Ej: Vilanova i la Geltrú",
                        key="ps_m_ciudad",
                    )
                with col_m2:
                    m_tipo = st.text_input(
                        "Tipo / sector",
                        placeholder="Ej: clínica dental",
                        key="ps_m_tipo",
                    )
                    m_url = st.text_input(
                        "URL de la web (opcional)",
                        placeholder="https://www.clinicasorriso.com",
                        key="ps_m_url",
                    )

                btn_manual = st.button(
                    "🎯 Analizar este negocio →",
                    type="primary",
                    disabled=not (m_nombre and m_ciudad),
                    key="ps_btn_manual",
                )

                if btn_manual:
                    from agents.specialists.prospector.scraper import GooglePlacesScraper
                    from agents.specialists.prospector.models import Business as BizModel
                    import uuid

                    tipo_m = m_tipo.strip() or "negocio local"
                    url_limpia = m_url.strip() or None

                    biz = None
                    # Intentar encontrarlo en Places por nombre + ciudad
                    if settings.google_places_api_key:
                        try:
                            with st.spinner(f"Buscando '{m_nombre}' en Google Places..."):
                                scraper = GooglePlacesScraper(settings.google_places_api_key)
                                candidatos = scraper.buscar_negocios(
                                    tipo=m_nombre, ciudad=m_ciudad, limite=5
                                )
                            # Buscar el que más se parezca al nombre
                            nombre_lower = m_nombre.lower()
                            for c in candidatos:
                                if nombre_lower in c.nombre.lower() or c.nombre.lower() in nombre_lower:
                                    biz = c
                                    break
                            if biz is None and candidatos:
                                biz = candidatos[0]  # el más relevante según Places
                            if biz:
                                # Si el usuario dio URL, tiene prioridad
                                if url_limpia:
                                    biz.web = url_limpia
                                    biz.tiene_web = True
                                biz.tipo = tipo_m
                                st.success(f"✅ Encontrado en Google Places: **{biz.nombre}** · {biz.rating}⭐ · {biz.total_resenas} reseñas")
                        except Exception as e:
                            st.warning(f"No se pudo buscar en Places ({e}). Continuando con datos manuales.")

                    # Si Places no devolvió nada, crear el objeto a mano
                    if biz is None:
                        biz = BizModel(
                            place_id=f"manual_{uuid.uuid4().hex[:8]}",
                            nombre=m_nombre,
                            tipo=tipo_m,
                            ciudad=m_ciudad,
                            direccion=m_ciudad,
                            web=url_limpia,
                            tiene_web=bool(url_limpia),
                        )
                        st.info("No encontrado en Google Places — se analizará solo la web.")

                    # Saltar directamente al análisis (paso 3), sin pasar por el listado
                    st.session_state.ps_negocios = [biz]
                    st.session_state.ps_negocios_analizar = [biz]
                    st.session_state.ps_resultados = []
                    st.session_state.ps_tipo = tipo_m
                    st.session_state.ps_ciudad = m_ciudad
                    st.session_state.ps_paso = 3
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 2 — Negocios encontrados
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 2 and st.session_state.ps_negocios:
        st.divider()
        negocios = st.session_state.ps_negocios
        tipo_act = st.session_state.ps_tipo
        ciudad_act = st.session_state.ps_ciudad

        st.markdown(f"### 2️⃣ {len(negocios)} negocios encontrados — *{tipo_act}* en **{ciudad_act}**")
        st.caption("Marca los que quieres analizar (por defecto los 3 primeros) y pulsa el botón.")

        df_neg = pd.DataFrame([{
            "✓": i < 3,
            "#": i + 1,
            "Nombre": n.nombre,
            "Dirección": n.direccion[:55] + "…" if len(n.direccion) > 55 else n.direccion,
            "Rating": f"{n.rating} ⭐" if n.rating else "—",
            "Reseñas": n.total_resenas or 0,
        } for i, n in enumerate(negocios)])

        edited = st.data_editor(
            df_neg,
            use_container_width=True,
            hide_index=True,
            column_config={
                "✓": st.column_config.CheckboxColumn("Analizar", width="small"),
                "#": st.column_config.NumberColumn("#", width="small"),
            },
            disabled=["#", "Nombre", "Dirección", "Rating", "Reseñas"],
            key="ps_neg_editor",
        )

        seleccionados_idx = [i for i, row in edited.iterrows() if row["✓"]]
        n_sel = len(seleccionados_idx)

        col_b1, col_b2 = st.columns([1, 3])
        if col_b1.button("← Nueva búsqueda", key="ps_back1"):
            st.session_state.ps_paso = 1
            st.rerun()

        btn_label = (
            f"📊 Analizar {n_sel} seleccionado{'s' if n_sel != 1 else ''} →"
            if n_sel > 0 else "Selecciona al menos uno"
        )
        if col_b2.button(btn_label, type="primary", key="ps_btn_analizar", disabled=(n_sel == 0)):
            # guardar solo los negocios marcados para el análisis
            st.session_state.ps_negocios_analizar = [negocios[i] for i in seleccionados_idx]
            st.session_state.ps_paso = 3
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 3 — Análisis masivo (web + reseñas + score)
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 3:
        st.divider()
        # usar solo los negocios seleccionados en el paso 2 (o todos si no hay selección guardada)
        negocios = st.session_state.get("ps_negocios_analizar") or st.session_state.ps_negocios
        resultados = st.session_state.ps_resultados

        st.markdown("### 3️⃣ Análisis web + reseñas + score de oportunidad")

        if not resultados:
            st.info(
                f"Se analizarán {len(negocios)} negocio{'s' if len(negocios) != 1 else ''}: "
                "web (15 puntos), reseñas Google, velocidad de carga y señales de dolor.",
                icon="🔬",
            )
            if st.button("⚡ Iniciar análisis masivo", type="primary", key="ps_btn_run_analisis"):
                agent = ProspectorAgent(nombre_agencia=st.session_state.ps_agencia)
                pb = st.progress(0)
                st_status = st.empty()
                results_tmp = []
                for i, neg in enumerate(negocios):
                    st_status.markdown(
                        f"🔬 Analizando **{neg.nombre}** ({i+1}/{len(negocios)})…"
                    )
                    pb.progress((i + 1) / len(negocios))
                    try:
                        r = agent.analizar_negocio(neg, generar_outreach=False)
                        results_tmp.append(r)
                    except Exception as e:
                        results_tmp.append(
                            ProspectorResult(business=neg, resumen_oportunidad=f"Error: {e}")
                        )
                results_tmp.sort(key=lambda r: r.score_oportunidad, reverse=True)
                st.session_state.ps_resultados = results_tmp
                pb.empty()
                st_status.empty()
                st.session_state.ps_paso = 4
                st.rerun()
        else:
            # Ya analizado — mostrar tabla resumen
            COLOR_OPT = {"alta": "🔴", "media": "🟡", "baja": "🟢"}
            rows_df = []
            for r in resultados:
                b = r.business
                cl = r.web_checklist
                nivel = cl.oportunidad() if cl else ("alta" if not b.tiene_web else "media")
                rows_df.append({
                    "Score": r.score_oportunidad,
                    "Oportunidad": COLOR_OPT.get(nivel, "⚪") + " " + nivel.upper(),
                    "Nombre": b.nombre,
                    "Web": "❌ Sin web" if not b.tiene_web else f"✅ {cl.score()}/15",
                    "Rating": f"{b.rating} ⭐" if b.rating else "—",
                    "Reseñas neg.": sum(1 for rv in r.resenas if rv.rating <= 3),
                    "Dolor principal": r.pains[0].descripcion[:60] + "…" if r.pains else "—",
                })
            st.dataframe(pd.DataFrame(rows_df), use_container_width=True, hide_index=True)
            st.caption(f"✅ {len(resultados)} negocios analizados, ordenados de mayor a menor oportunidad")

            if st.button("← Volver a resultados de búsqueda", key="ps_back3"):
                st.session_state.ps_paso = 2
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 4 — Seleccionar negocio y ver dolores detectados
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 4 and st.session_state.ps_resultados:
        st.divider()
        resultados = st.session_state.ps_resultados
        st.markdown("### 4️⃣ Selecciona un negocio y examina sus dolores")

        # Selector con score visible
        opciones = [
            f"[{r.score_oportunidad}] {r.business.nombre}"
            for r in resultados
        ]
        sel_label = st.selectbox(
            "Negocio (ordenados de mayor oportunidad a menor)",
            opciones,
            index=st.session_state.ps_sel_idx,
            key="ps_sel_negocio",
        )
        st.session_state.ps_sel_idx = opciones.index(sel_label)
        sel = resultados[st.session_state.ps_sel_idx]
        b = sel.business
        cl = sel.web_checklist
        nivel = cl.oportunidad() if cl else ("alta" if not b.tiene_web else "media")
        COLOR_OPT = {"alta": "🔴", "media": "🟡", "baja": "🟢"}

        # ── Cabecera del negocio ───────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score oportunidad", f"{sel.score_oportunidad}/100")
        c2.metric("Rating Google", f"{b.rating} ⭐" if b.rating else "—")
        c3.metric("Análisis web", f"{cl.score()}/15" if cl else "Sin web")
        c4.metric("Nivel", COLOR_OPT.get(nivel, "") + " " + nivel.upper())

        info_cols = st.columns(3)
        info_cols[0].markdown(f"📍 {b.direccion}")
        if b.telefono:
            info_cols[1].markdown(f"📞 {b.telefono}")
        if b.web:
            info_cols[2].markdown(f"🌐 [{b.web}]({b.web})")

        if b.nombre_propietario:
            st.success(f"👤 Propietario detectado: **{b.nombre_propietario}** — el email irá personalizado")

        if sel.resumen_oportunidad:
            st.info(f"💡 {sel.resumen_oportunidad}")

        st.divider()

        # ── Dos columnas: análisis web | reseñas ──────────────────────────
        col_web, col_rev = st.columns(2)

        with col_web:
            st.markdown("**🌐 Análisis de la web**")
            if not b.tiene_web:
                st.error("❌ SIN SITIO WEB — Lead Tier 1 (máxima oportunidad)")
            elif cl:
                if sel.tiempo_carga and sel.tiempo_carga < 99:
                    color_t = "🟢" if sel.tiempo_carga < 3 else "🔴"
                    st.caption(f"⏱️ Carga: {color_t} {sel.tiempo_carga:.1f}s")
                items_web = [
                    ("Formulario de contacto", cl.tiene_formulario),
                    ("Chat / WhatsApp widget", cl.tiene_chat_whatsapp),
                    ("Carga rápida <3s", cl.carga_rapida),
                    ("Mobile responsive", cl.es_mobile_responsive),
                    ("HTTPS activo", cl.tiene_https),
                    ("CTA de reserva claro", cl.tiene_cta_reserva),
                    ("Reserva online", cl.tiene_reserva_online),
                    ("Testimonios visibles", cl.tiene_testimonios),
                    ("Vídeo presentación", cl.tiene_video),
                    ("Blog / contenido SEO", cl.tiene_blog),
                    ("Píxel de remarketing", cl.tiene_pixel_tracking),
                    ("Captura de emails", cl.tiene_captura_email),
                ]
                for label, ok in items_web:
                    st.markdown(f"{'✅' if ok else '❌'} {label}")

        with col_rev:
            st.markdown("**⭐ Reseñas Google**")
            if not sel.resenas:
                st.caption("No hay reseñas disponibles en este análisis.")
            else:
                negs = [r for r in sel.resenas if r.rating <= 3]
                poss = [r for r in sel.resenas if r.rating >= 4]
                st.caption(f"🟢 {len(poss)} positivas   🔴 {len(negs)} negativas")
                for r in sorted(sel.resenas, key=lambda x: x.rating)[:5]:
                    stars = "⭐" * r.rating
                    cat = f"  `{r.categoria_dolor}`" if r.categoria_dolor else ""
                    with st.expander(f"{stars} {r.autor}{cat}", expanded=(r.rating <= 2)):
                        st.write(r.texto or "_Sin texto_")

        st.divider()

        # ── Dolores priorizados ────────────────────────────────────────────
        st.markdown("**💊 Dolores detectados — ordenados de mayor a menor impacto en ventas**")
        if not sel.pains:
            st.info("Sin dolores críticos detectados para este negocio.")
        else:
            for i, pain in enumerate(sel.pains):
                urg_ico = "🔴" if pain.urgencia >= 8 else "🟡" if pain.urgencia >= 5 else "🟢"
                with st.expander(
                    f"{urg_ico} #{i+1}  {pain.descripcion[:75]}…  — urgencia {pain.urgencia}/10",
                    expanded=(i == 0),
                ):
                    st.markdown(f"**Servicio recomendado:** {pain.servicio}")
                    st.markdown(f"**Evidencia encontrada:** _{pain.evidencia}_")

        col_b4a, col_b4b = st.columns(2)
        if col_b4a.button("← Volver al análisis masivo", key="ps_back4"):
            st.session_state.ps_paso = 3
            st.rerun()
        if col_b4b.button("💰 Calcular precios & ROI →", type="primary", key="ps_goto5"):
            st.session_state.ps_paso = 5
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 5 — Pricing & ROI (motor de ventas)
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 5 and st.session_state.ps_resultados:
        from agents.specialists.prospector import PricingCalculator
        st.divider()
        resultados = st.session_state.ps_resultados
        sel = resultados[st.session_state.ps_sel_idx]
        b = sel.business
        pc = PricingCalculator()

        st.markdown(f"### 5️⃣ Pricing & ROI — **{b.nombre}**")
        st.caption("Qué venderle, a qué precio, y cuánto ganará el cliente. Ajusta los valores y todo se recalcula al instante.")

        # Valores de partida (sugeridos por nicho, editables)
        ticket_def = sel.ticket_promedio or pc.ticket_sugerido(b.tipo)
        leads_def = sel.leads_mensuales or 200
        conv_def = sel.conversion_actual or 25.0

        col_p1, col_p2, col_p3 = st.columns(3)
        ticket = col_p1.number_input(
            "💶 Ticket medio por cliente (€)", min_value=10, max_value=10000,
            value=int(ticket_def), step=10, key="ps_ticket",
            help="Cuánto factura el negocio por cada cliente/venta. Pre-rellenado según el nicho.",
        )
        leads = col_p2.number_input(
            "📥 Leads/contactos al mes", min_value=10, max_value=10000,
            value=int(leads_def), step=10, key="ps_leads",
            help="Cuántas personas contactan o entran al mes (estimación).",
        )
        conv = col_p3.number_input(
            "🎯 Conversión actual (%)", min_value=1.0, max_value=100.0,
            value=float(conv_def), step=1.0, key="ps_conv",
            help="Qué % de esos contactos acaba comprando.",
        )

        # Guardar en el resultado
        sel.ticket_promedio = float(ticket)
        sel.leads_mensuales = int(leads)
        sel.conversion_actual = float(conv)

        # Recomendación de servicios + precios
        recs = pc.recomendar(sel, float(ticket))

        st.markdown("#### 🛠️ Servicios recomendados (según sus dolores reales)")
        st.caption("Marca los que quieras incluir en la propuesta. El ROI se recalcula con tu selección.")

        seleccionados = []
        for i, r in enumerate(recs):
            cols = st.columns([0.5, 4, 2, 3])
            incluir = cols[0].checkbox("", value=(i < 3), key=f"ps_svc_{i}",
                                       label_visibility="collapsed")
            cols[1].markdown(f"**{r.servicio.nombre}**  \n<small style='color:#94a3b8'>{r.motivo}</small>", unsafe_allow_html=True)
            precio_txt = f"{r.setup:.0f}€ setup"
            if r.mensual > 0:
                precio_txt += f" + {r.mensual:.0f}€/mes"
            cols[2].markdown(f"<div style='text-align:right'><b>{precio_txt}</b></div>", unsafe_allow_html=True)
            cols[3].markdown(f"<small style='color:#10b981'>📈 {r.servicio.kpi}</small>", unsafe_allow_html=True)
            if incluir:
                seleccionados.append(r)

        if not seleccionados:
            st.warning("Selecciona al menos un servicio para calcular el ROI.")
        else:
            roi = pc.proyectar_roi(float(leads), float(conv), float(ticket), seleccionados)

            # Guardar para la propuesta
            sel.servicios_recomendados = [{
                "nombre": s.servicio.nombre, "setup": s.setup,
                "mensual": s.mensual, "kpi": s.servicio.kpi, "motivo": s.motivo,
            } for s in seleccionados]
            sel.roi_data = roi.to_dict()

            st.markdown("#### 💰 Lo que tú cobras")
            tot_setup = sum(s.setup for s in seleccionados)
            tot_mensual = sum(s.mensual for s in seleccionados)
            cc1, cc2, cc3 = st.columns(3)
            cc1.metric("Setup inicial", f"{tot_setup:,.0f} €".replace(",", "."))
            cc2.metric("Recurrente", f"{tot_mensual:,.0f} €/mes".replace(",", "."))
            cc3.metric("Primer año", f"{tot_setup + tot_mensual * 12:,.0f} €".replace(",", "."))

            st.markdown("#### 📊 Lo que gana el cliente — Sin vs Con automatización")
            df_roi = pd.DataFrame({
                "Métrica": ["Leads/mes", "Conversión", "Ventas/mes", "Ingresos/mes"],
                "❌ Ahora": [
                    f"{roi.leads_mes:.0f}",
                    f"{roi.conversion_actual:.0f}%",
                    f"{roi.ventas_actual:.0f}",
                    f"{roi.ingresos_actual:,.0f} €".replace(",", "."),
                ],
                "✅ Con MerakIA": [
                    f"{roi.leads_nuevo:.0f}",
                    f"{roi.conversion_nueva:.0f}%",
                    f"{roi.ventas_nuevo:.0f}",
                    f"{roi.ingresos_nuevo:,.0f} €".replace(",", "."),
                ],
            })
            st.dataframe(df_roi, use_container_width=True, hide_index=True)

            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("💸 Ingreso extra", f"+{roi.ingreso_extra_mes:,.0f} €/mes".replace(",", "."))
            payback_txt = f"{roi.payback_meses:.1f} meses" if roi.payback_meses < 99 else "—"
            rc2.metric("⏱️ Recuperación", payback_txt)
            rc3.metric("📈 ROI 6 meses", f"{roi.roi_6m:.0f}%")
            rc4.metric("📈 ROI 12 meses", f"{roi.roi_12m:.0f}%")

            if roi.ingreso_extra_mes > tot_mensual:
                st.success(
                    f"💎 Argumento de cierre: por **{tot_mensual:.0f}€/mes** el cliente "
                    f"gana **{roi.ingreso_extra_mes:,.0f}€/mes** extra".replace(",", ".") +
                    f" — se paga solo en {payback_txt}.",
                )

        st.divider()
        col_b5a, col_b5b = st.columns(2)
        if col_b5a.button("← Volver a dolores", key="ps_back5"):
            st.session_state.ps_paso = 4
            st.rerun()
        if col_b5b.button("📣 Generar arsenal de venta →", type="primary", key="ps_goto6"):
            st.session_state.ps_paso = 6
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 6 — Arsenal de venta (outreach + assets)
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 6 and st.session_state.ps_resultados:
        st.divider()
        resultados = st.session_state.ps_resultados
        sel = resultados[st.session_state.ps_sel_idx]
        b = sel.business

        st.markdown(f"### 6️⃣ Arsenal de venta — **{b.nombre}**")
        st.caption("Todo personalizado con los datos reales del negocio y el ROI calculado.")

        negativas = [r for r in sel.resenas if r.rating <= 3 and r.texto]

        # Resumen del ROI para alimentar propuesta/presentación
        roi_resumen = ""
        if sel.roi_data:
            rd = sel.roi_data
            roi_resumen = (
                f"Inversión {rd['inversion_setup']:.0f}€ setup + {rd['inversion_mensual']:.0f}€/mes; "
                f"ingreso extra estimado +{rd['ingreso_extra_mes']:.0f}€/mes; "
                f"recuperación en {rd['payback_meses']:.1f} meses; ROI 12m {rd['roi_12m']:.0f}%."
            )

        col_cfg_o1, col_cfg_o2 = st.columns(2)
        nombre_agencia_o = col_cfg_o1.text_input(
            "Tu agencia", value=st.session_state.ps_agencia, key="ps_agencia_o"
        )
        nombre_dest = col_cfg_o2.text_input(
            "Nombre propietario",
            value=b.nombre_propietario or "",
            placeholder="Si lo conoces, el email irá personalizado",
            key="ps_dest_nombre",
        )

        (tab_email, tab_wa, tab_llamada, tab_propuesta,
         tab_demo, tab_landing, tab_present) = st.tabs(
            ["📧 Email", "💬 WhatsApp", "📞 Script", "📄 Propuesta",
             "🎁 Demo", "🖥️ Landing", "📊 Presentación"]
        )

        def _agent_o():
            return ProspectorAgent(nombre_agencia=nombre_agencia_o)

        # ── Email ─────────────────────────────────────────────────────────
        with tab_email:
            if not sel.email_asunto:
                st.info(
                    "El email citará reseñas reales, cuantificará el coste del dolor "
                    "y terminará con un CTA de 15 minutos.", icon="✍️"
                )
                if st.button("📧 Generar email emocional", type="primary", key="ps_gen_email"):
                    with st.spinner("Redactando con framework PAS (Problem → Agitate → Solution)…"):
                        ag = _agent_o()
                        asunto, cuerpo = ag.offer_gen.generar_email(
                            b, sel.pains, negativas, nombre_dest or None
                        )
                    sel.email_asunto = asunto
                    sel.email_cuerpo = cuerpo
                    ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.markdown(f"**Asunto:** `{sel.email_asunto}`")
                st.text_area("Cuerpo", value=sel.email_cuerpo or "", height=320, key="ps_email_txt")
                col_dl, col_regen = st.columns(2)
                col_dl.download_button(
                    "⬇️ Descargar .txt",
                    data=f"ASUNTO: {sel.email_asunto}\n\n{sel.email_cuerpo}",
                    file_name=f"email_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regen.button("🔄 Regenerar", key="ps_regen_email"):
                    sel.email_asunto = None
                    sel.email_cuerpo = None
                    st.rerun()

        # ── WhatsApp ──────────────────────────────────────────────────────
        with tab_wa:
            if not sel.whatsapp_mensaje:
                st.info("Mensaje directo de 5-6 líneas, hook específico, dolor en euros.", icon="💬")
                if st.button("💬 Generar WhatsApp", type="primary", key="ps_gen_wa"):
                    with st.spinner("Escribiendo…"):
                        ag = _agent_o()
                        sel.whatsapp_mensaje = ag.offer_gen.generar_whatsapp(
                            b, sel.pains, negativas
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Mensaje", value=sel.whatsapp_mensaje, height=200, key="ps_wa_txt")
                col_dl2, col_regen2 = st.columns(2)
                col_dl2.download_button(
                    "⬇️ Descargar .txt",
                    data=sel.whatsapp_mensaje,
                    file_name=f"wa_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regen2.button("🔄 Regenerar", key="ps_regen_wa"):
                    sel.whatsapp_mensaje = None
                    st.rerun()

        # ── Script llamada ────────────────────────────────────────────────
        with tab_llamada:
            if not sel.script_llamada:
                st.info("Guión completo: apertura + gancho + cualificación + propuesta + cierre + objeciones.", icon="📞")
                if st.button("📞 Generar guión cold call", type="primary", key="ps_gen_script"):
                    with st.spinner("Construyendo guión…"):
                        ag = _agent_o()
                        sel.script_llamada = ag.offer_gen.generar_script_llamada(
                            b, sel.pains, negativas
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Guión", value=sel.script_llamada, height=450, key="ps_script_txt")
                col_dl3, col_regen3 = st.columns(2)
                col_dl3.download_button(
                    "⬇️ Descargar .txt",
                    data=sel.script_llamada,
                    file_name=f"guion_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regen3.button("🔄 Regenerar", key="ps_regen_script"):
                    sel.script_llamada = None
                    st.rerun()

        # ── Propuesta completa ────────────────────────────────────────────
        with tab_propuesta:
            if not sel.propuesta_texto:
                st.info(
                    "Documento estructurado: diagnóstico · soluciones · cómo trabajamos · "
                    "inversión y ROI (los del paso 5) · siguiente paso.",
                    icon="📄",
                )
                if st.button("📄 Generar propuesta completa", type="primary", key="ps_gen_propuesta"):
                    with st.spinner("Redactando propuesta…"):
                        ag = _agent_o()
                        resumen = sel.resumen_oportunidad
                        if roi_resumen:
                            resumen = f"{resumen}\n\nNúmeros para la propuesta: {roi_resumen}"
                        sel.propuesta_texto = ag.offer_gen.generar_propuesta_texto(
                            b, sel.pains, resumen
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Propuesta", value=sel.propuesta_texto, height=480, key="ps_propuesta_txt")
                col_dlp, col_regp = st.columns(2)
                col_dlp.download_button(
                    "⬇️ Descargar propuesta .txt",
                    data=sel.propuesta_texto,
                    file_name=f"propuesta_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regp.button("🔄 Regenerar", key="ps_regen_propuesta"):
                    sel.propuesta_texto = None
                    st.rerun()

        # ── Demo (caballo de Troya) ────────────────────────────────────────
        with tab_demo:
            st.caption("Genera el prompt para montar un agente DEMO que atienda como si fuera este negocio. Llegar a la reunión con la demo viva es lo que más cierra.")
            col_d1, col_d2 = st.columns(2)
            tipo_demo = col_d1.selectbox("Canal de la demo", ["WhatsApp", "Voz (llamada)", "Chat web"], key="ps_demo_canal")
            objetivo_demo = col_d2.selectbox(
                "Objetivo del agente",
                ["agendar citas", "responder y cualificar leads", "reservar mesa/servicio", "dar información y captar contacto"],
                key="ps_demo_obj",
            )
            if not sel.demo_prompt:
                if st.button("🎁 Generar prompt de demo", type="primary", key="ps_gen_demo"):
                    with st.spinner("Construyendo el agente demo…"):
                        ag = _agent_o()
                        sel.demo_prompt = ag.offer_gen.generar_demo_prompt(
                            b, sel.pains, tipo_demo, objetivo_demo
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Prompt del agente demo", value=sel.demo_prompt, height=420, key="ps_demo_txt")
                col_dld, col_regd = st.columns(2)
                col_dld.download_button(
                    "⬇️ Descargar prompt .txt",
                    data=sel.demo_prompt,
                    file_name=f"demo_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regd.button("🔄 Regenerar", key="ps_regen_demo"):
                    sel.demo_prompt = None
                    st.rerun()

        # ── Landing ────────────────────────────────────────────────────────
        with tab_landing:
            st.caption("Prompt listo para Base44 / Framer / Lovable / v0: estructura, copy y diseño de una landing de alta conversión para este negocio.")
            if not sel.landing_prompt:
                if st.button("🖥️ Generar prompt de landing", type="primary", key="ps_gen_landing"):
                    with st.spinner("Diseñando la landing…"):
                        ag = _agent_o()
                        sel.landing_prompt = ag.offer_gen.generar_landing_prompt(
                            b, sel.pains, sel.resumen_oportunidad
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Prompt de landing", value=sel.landing_prompt, height=420, key="ps_landing_txt")
                col_dll, col_regl = st.columns(2)
                col_dll.download_button(
                    "⬇️ Descargar prompt .txt",
                    data=sel.landing_prompt,
                    file_name=f"landing_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regl.button("🔄 Regenerar", key="ps_regen_landing"):
                    sel.landing_prompt = None
                    st.rerun()

        # ── Presentación (Gamma) ───────────────────────────────────────────
        with tab_present:
            st.caption("Prompt para Gamma que crea la presentación de la reunión: diagnóstico, dolor en euros, solución y ROI.")
            if not sel.presentacion_prompt:
                if st.button("📊 Generar prompt de presentación", type="primary", key="ps_gen_present"):
                    with st.spinner("Preparando la presentación…"):
                        ag = _agent_o()
                        sel.presentacion_prompt = ag.offer_gen.generar_presentacion_prompt(
                            b, sel.pains, sel.resumen_oportunidad, roi_resumen
                        )
                        ag.crm.guardar(sel)
                    st.rerun()
            else:
                st.text_area("Prompt para Gamma", value=sel.presentacion_prompt, height=420, key="ps_present_txt")
                col_dlpr, col_regpr = st.columns(2)
                col_dlpr.download_button(
                    "⬇️ Descargar prompt .txt",
                    data=sel.presentacion_prompt,
                    file_name=f"presentacion_{b.nombre[:25].replace(' ','_')}.txt",
                )
                if col_regpr.button("🔄 Regenerar", key="ps_regen_present"):
                    sel.presentacion_prompt = None
                    st.rerun()

        st.divider()
        col_b6a, col_b6b = st.columns(2)
        if col_b6a.button("← Volver a Pricing & ROI", key="ps_back6"):
            st.session_state.ps_paso = 5
            st.rerun()
        if col_b6b.button("📋 Registrar en CRM →", type="primary", key="ps_goto7"):
            st.session_state.ps_paso = 7
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 7 — CRM & Seguimiento
    # ══════════════════════════════════════════════════════════════════════════
    if paso >= 7:
        st.divider()
        st.markdown("### 7️⃣ CRM — Registra el estado y haz el seguimiento")

        crm = CRM()

        # ── Estado del negocio actual ──────────────────────────────────────
        if st.session_state.ps_resultados:
            sel = st.session_state.ps_resultados[st.session_state.ps_sel_idx]
            b = sel.business
            st.markdown(f"**Negocio activo:** {b.nombre}")

            col_s1, col_s2 = st.columns([1, 2])
            nuevo_estado = col_s1.selectbox(
                "Estado",
                ESTADOS,
                index=ESTADOS.index(sel.estado) if sel.estado in ESTADOS else 0,
                format_func=lambda e: f"{ESTADO_COLORS.get(e,'')} {e.upper()}",
                key="ps_crm_estado",
            )
            nuevas_notas = col_s2.text_area(
                "Notas", value=sel.notas or "", height=80, key="ps_crm_notas"
            )
            if st.button("💾 Guardar estado", key="ps_crm_save"):
                crm.actualizar_estado(b.place_id, nuevo_estado, nuevas_notas)
                sel.estado = nuevo_estado
                sel.notas = nuevas_notas
                st.success(f"✅ {ESTADO_COLORS.get(nuevo_estado,'')} {nuevo_estado.upper()} guardado")

            if st.button("✉️ Analizar otro negocio", key="ps_otro_negocio"):
                st.session_state.ps_paso = 4
                st.rerun()

        st.divider()

        # ── Tabla CRM completa ─────────────────────────────────────────────
        st.markdown("**Todos los prospectos en el CRM**")

        col_f1, col_f2, col_f3 = st.columns(3)
        filtro_ciudad_crm = col_f1.text_input("Ciudad", key="crm2_ciudad")
        filtro_estado_crm = col_f2.selectbox(
            "Estado", ["todos"] + ESTADOS, key="crm2_estado",
            format_func=lambda e: "Todos" if e == "todos" else f"{ESTADO_COLORS.get(e,'')} {e.upper()}",
        )
        filtro_opt_crm = col_f3.selectbox("Oportunidad", ["todas", "alta", "media", "baja"], key="crm2_opt")

        rows_crm = crm.listar(
            ciudad=filtro_ciudad_crm or None,
            estado=filtro_estado_crm if filtro_estado_crm != "todos" else None,
            oportunidad=filtro_opt_crm if filtro_opt_crm != "todas" else None,
        )

        stats = crm.stats()
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Total", stats["total"])
        mc2.metric("Alta oportunidad", stats["alta_oportunidad"])
        mc3.metric("Clientes", stats["por_estado"].get("cliente", 0))
        mc4.metric("Propuestas", stats["por_estado"].get("propuesta", 0))

        if rows_crm:
            COLOR_OPT_C = {"alta": "🔴", "media": "🟡", "baja": "🟢"}
            df_crm = pd.DataFrame([{
                "Score": r["score_oportunidad"] or 0,
                "Oportunidad": COLOR_OPT_C.get(r["oportunidad_nivel"] or "", "⚪") + " " + (r["oportunidad_nivel"] or "").upper(),
                "Estado": ESTADO_COLORS.get(r["estado"], "") + " " + (r["estado"] or "").upper(),
                "Nombre": r["nombre"],
                "Ciudad": r["ciudad"],
                "Web": "❌" if not r["tiene_web"] else "✅",
                "Rating": f"{r['rating']} ⭐" if r["rating"] else "—",
                "Teléfono": r["telefono"] or "—",
                "Contactado": (r["fecha_contacto"] or "")[:10],
            } for r in rows_crm])
            st.dataframe(df_crm, use_container_width=True, hide_index=True)

            csv_data = crm.exportar_csv()
            if csv_data:
                st.download_button(
                    "⬇️ Exportar todo el CRM a CSV",
                    data=csv_data.encode("utf-8"),
                    file_name="prospectos_crm.csv",
                    mime="text/csv",
                )
        else:
            st.info("Sin prospectos en el CRM todavía.", icon="ℹ️")

        if st.button("🔄 Empezar nueva búsqueda", key="ps_nueva_busqueda"):
            for k in ["ps_paso", "ps_negocios", "ps_resultados", "ps_sel_idx", "ps_tipo", "ps_ciudad"]:
                if k == "ps_paso":
                    st.session_state[k] = 1
                elif k in ["ps_negocios", "ps_resultados"]:
                    st.session_state[k] = []
                elif k == "ps_sel_idx":
                    st.session_state[k] = 0
                else:
                    st.session_state[k] = ""
            st.rerun()


# ─── Base de Datos ─────────────────────────────────────────────────────────────
elif page == "📊 Base de Datos":
    import pandas as pd
    from agents.specialists.prospector import CRM, ESTADOS, ESTADO_COLORS
    import json as _json

    st.title("📊 Base de Datos de Negocios")
    st.caption("Todos los prospectos analizados con ProspectorIA. Filtra, edita y exporta.")

    crm_db = CRM()
    stats_db = crm_db.stats()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total negocios", stats_db["total"])
    k2.metric("Alta oportunidad 🔴", stats_db["alta_oportunidad"])
    k3.metric("Clientes 🟢", stats_db["por_estado"].get("cliente", 0))
    k4.metric("Propuestas 🟣", stats_db["por_estado"].get("propuesta", 0))
    k5.metric("Reuniones 🟠", stats_db["por_estado"].get("reunion", 0))

    st.divider()

    # ── Filtros ───────────────────────────────────────────────────────────────
    with st.expander("🔎 Filtros", expanded=True):
        fc1, fc2, fc3, fc4 = st.columns(4)
        f_nombre = fc1.text_input("Buscar nombre", placeholder="Ej: Dental", key="db_f_nombre")
        f_ciudad = fc2.text_input("Ciudad", placeholder="Ej: Barcelona", key="db_f_ciudad")
        f_estado = fc3.selectbox(
            "Estado", ["todos"] + ESTADOS, key="db_f_estado",
            format_func=lambda e: "Todos" if e == "todos" else f"{ESTADO_COLORS.get(e,'')} {e.upper()}",
        )
        f_opt = fc4.selectbox("Oportunidad", ["todas", "alta", "media", "baja"], key="db_f_opt")

    rows_db = crm_db.listar(
        ciudad=f_ciudad or None,
        estado=f_estado if f_estado != "todos" else None,
        oportunidad=f_opt if f_opt != "todas" else None,
    )

    # Filtro por nombre (en memoria)
    if f_nombre:
        rows_db = [r for r in rows_db if f_nombre.lower() in (r["nombre"] or "").lower()]

    if not rows_db:
        st.info("No hay negocios que coincidan con los filtros.", icon="ℹ️")
    else:
        COLOR_OPT_DB = {"alta": "🔴", "media": "🟡", "baja": "🟢"}

        st.caption(f"{len(rows_db)} negocio{'s' if len(rows_db) != 1 else ''} encontrado{'s' if len(rows_db) != 1 else ''}")

        # ── Tabla resumen ──────────────────────────────────────────────────
        df_db = pd.DataFrame([{
            "Score": r["score_oportunidad"] or 0,
            "Oport.": COLOR_OPT_DB.get(r["oportunidad_nivel"] or "", "⚪"),
            "Estado": ESTADO_COLORS.get(r["estado"], "") + " " + (r["estado"] or "").upper(),
            "Nombre": r["nombre"],
            "Ciudad": r["ciudad"] or "—",
            "Tipo": r["tipo"] or "—",
            "Web": "✅" if r["tiene_web"] else "❌",
            "Rating": f"{r['rating']} ⭐" if r["rating"] else "—",
            "Reseñas": r["total_resenas"] or 0,
            "Tel.": r["telefono"] or "—",
            "Guardado": (r["fecha_creacion"] or "")[:10],
        } for r in rows_db])

        st.dataframe(df_db, use_container_width=True, hide_index=True)

        # ── Exportar ───────────────────────────────────────────────────────
        csv_db = crm_db.exportar_csv()
        if csv_db:
            st.download_button(
                "⬇️ Exportar CSV completo",
                data=csv_db.encode("utf-8"),
                file_name="negocios_merakia.csv",
                mime="text/csv",
            )

        st.divider()

        # ── Detalle expandible por negocio ─────────────────────────────────
        st.markdown("#### Ver / editar detalle")

        nombres_lista = [f"{ESTADO_COLORS.get(r['estado'],'')} {r['nombre']} · {r['ciudad'] or ''}" for r in rows_db]
        sel_db_idx = st.selectbox("Selecciona un negocio", range(len(rows_db)),
                                  format_func=lambda i: nombres_lista[i], key="db_sel")
        rec = rows_db[sel_db_idx]

        col_d1, col_d2 = st.columns([2, 1])

        with col_d1:
            st.markdown(f"### {rec['nombre']}")
            st.markdown(f"**Tipo:** {rec['tipo'] or '—'} &nbsp;|&nbsp; **Ciudad:** {rec['ciudad'] or '—'}")
            if rec["web"]:
                st.markdown(f"**Web:** [{rec['web']}]({rec['web']})")
            if rec["telefono"]:
                st.markdown(f"**Teléfono:** {rec['telefono']}")
            st.markdown(f"**Rating:** {rec['rating']} ⭐ ({rec['total_resenas']} reseñas)" if rec["rating"] else "**Rating:** —")
            st.markdown(f"**Score web:** {rec['score_web']}/15 &nbsp;|&nbsp; **Score oportunidad:** {rec['score_oportunidad']}/100")
            if rec["resumen"]:
                st.info(rec["resumen"], icon="💡")

        with col_d2:
            st.markdown("**Gestión del pipeline**")
            nuevo_estado_db = st.selectbox(
                "Estado",
                ESTADOS,
                index=ESTADOS.index(rec["estado"]) if rec["estado"] in ESTADOS else 0,
                format_func=lambda e: f"{ESTADO_COLORS.get(e,'')} {e.upper()}",
                key="db_edit_estado",
            )
            nuevas_notas_db = st.text_area("Notas", value=rec["notas"] or "", height=100, key="db_edit_notas")
            if st.button("💾 Guardar cambios", key="db_save_estado", type="primary"):
                crm_db.actualizar_estado(rec["id"], nuevo_estado_db, nuevas_notas_db)
                st.success("✅ Guardado")
                st.rerun()

        # ── Dolores detectados ─────────────────────────────────────────────
        if rec.get("pains_json"):
            pains_db = _json.loads(rec["pains_json"])
            if pains_db:
                st.markdown("**Dolores detectados**")
                for p in sorted(pains_db, key=lambda x: x.get("urgencia", 0), reverse=True):
                    urg = p.get("urgencia", 0)
                    color = "#ef4444" if urg >= 7 else "#f59e0b" if urg >= 4 else "#6b7280"
                    st.markdown(
                        f'<span style="color:{color};font-weight:600">[{urg}/10]</span> '
                        f'**{p.get("categoria","").replace("_"," ").title()}** — {p.get("descripcion","")}',
                        unsafe_allow_html=True,
                    )

        # ── Email generado ─────────────────────────────────────────────────
        if rec.get("email_cuerpo"):
            with st.expander("✉️ Email generado"):
                st.markdown(f"**Asunto:** {rec.get('email_asunto','')}")
                st.text_area("Cuerpo", value=rec["email_cuerpo"], height=200,
                             key="db_email_body", disabled=True)

        # ── WhatsApp / Script ──────────────────────────────────────────────
        col_wa, col_sc = st.columns(2)
        if rec.get("whatsapp_mensaje"):
            with col_wa.expander("💬 WhatsApp"):
                st.text_area("Mensaje", value=rec["whatsapp_mensaje"], height=150,
                             key="db_wa", disabled=True)
        if rec.get("script_llamada"):
            with col_sc.expander("📞 Script llamada"):
                st.text_area("Script", value=rec["script_llamada"], height=150,
                             key="db_script", disabled=True)
