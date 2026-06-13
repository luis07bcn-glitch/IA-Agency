import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import json
import io
import anthropic
import streamlit as st
from database import (
    init_db, get_platos, add_plato, update_plato, delete_plato,
    get_despensa, add_despensa, delete_despensa,
    save_menu, get_menus_guardados, bulk_add_platos,
)
from ai_generator import generar_menu, analizar_escandallo, importar_platos_desde_texto, importar_platos_desde_pdf, analizar_foto_despensa, modo_escandalo

init_db()

st.set_page_config(
    page_title="ChefMenu AI",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container { padding-top: 1.5rem; }
.plato-card {
    background: #1a1f2e;
    border-left: 3px solid #4CAF50;
    padding: 10px 14px;
    border-radius: 6px;
    margin: 4px 0;
}
.alerta {
    background: #2d1f1f;
    border-left: 3px solid #f44336;
    padding: 8px 12px;
    border-radius: 6px;
}
.chip {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    margin: 2px;
}
.chip-verde { background: #1b4332; color: #52b788; }
.chip-naranja { background: #3d2700; color: #ff9800; }
.chip-azul { background: #0d2137; color: #64b5f6; }
</style>
""", unsafe_allow_html=True)

st.sidebar.image("https://img.icons8.com/emoji/96/fork-and-knife-with-plate.png", width=60)
st.sidebar.title("ChefMenu AI")
st.sidebar.markdown("*Menús inteligentes para tu restaurante*")
st.sidebar.divider()

pagina = st.sidebar.radio(
    "Navegación",
    ["🍽️ Generar Menú", "📋 Mis Platos", "📥 Importar Platos", "🛒 Despensa", "📊 Escandallo", "♻️ Escándalo Mode", "📁 Menús Guardados"],
    label_visibility="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — GENERAR MENÚ
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "🍽️ Generar Menú":
    st.title("🍽️ Generar Menú del Día")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("⚙️ Configuración")
        precio = st.number_input("Precio del menú (€)", min_value=5.0, max_value=100.0, value=12.0, step=0.5)
        st.divider()

        modo = st.radio(
            "Modo de estructura",
            ["📏 Simple (sliders)", "✍️ Plantilla libre"],
            help="Simple: elige cuántos platos de cada categoría. Plantilla libre: describe exactamente qué quieres.",
        )

        n_primeros = n_segundos = n_postres = 0
        plantilla_libre = ""

        if modo == "📏 Simple (sliders)":
            n_primeros = st.slider("Opciones de primero", 1, 8, 3)
            n_segundos = st.slider("Opciones de segundo", 1, 8, 3)
            n_postres = st.slider("Opciones de postre", 1, 4, 2)
        else:
            st.markdown("Describe la estructura exacta del menú:")
            plantilla_libre = st.text_area(
                "Plantilla",
                height=140,
                placeholder=(
                    "Ej: Es verano, quiero un menú fresco.\n"
                    "Primeros: 4 ensaladas diferentes, 1 gazpacho, 1 vichyssoise\n"
                    "Segundos: 2 platos de pescado, 1 carne a la plancha, 1 arroz\n"
                    "Postres: 2 opciones de fruta o postre frío"
                ),
                label_visibility="collapsed",
            )
            # Extraer conteos aproximados para el generador
            n_primeros = 4
            n_segundos = 3
            n_postres = 2

        st.divider()
        reglas_extra = st.text_area(
            "Reglas extra (opcional)",
            placeholder="Ej: Esta semana tenemos mucho bacalao. Sin cerdo.",
            height=70,
        )
        usar_despensa = st.checkbox("Considerar despensa", value=True)
        usar_rotacion = st.checkbox("🔄 Rotación inteligente (evitar repetir últimas semanas)", value=True)
        generar = st.button("✨ Generar menú con IA", type="primary", use_container_width=True)

    with col2:
        if generar:
            platos = get_platos()
            despensa = get_despensa() if usar_despensa else []
            historial = get_menus_guardados()[:6] if usar_rotacion else []

            primeros_bd = [p for p in platos if p["categoria"] == "primero"]
            segundos_bd = [p for p in platos if p["categoria"] == "segundo"]

            if not plantilla_libre and len(primeros_bd) < n_primeros:
                st.error(f"No hay suficientes primeros en la BD (tienes {len(primeros_bd)}, necesitas {n_primeros}).")
            elif not plantilla_libre and len(segundos_bd) < n_segundos:
                st.error(f"No hay suficientes segundos en la BD (tienes {len(segundos_bd)}, necesitas {n_segundos}).")
            elif plantilla_libre and not platos:
                st.error("No hay platos en la BD. Añade platos o importa desde un documento.")
            else:
                with st.spinner("La IA está componiendo el mejor menú..."):
                    try:
                        resultado = generar_menu(
                            platos, despensa, precio,
                            n_primeros, n_segundos, n_postres,
                            reglas_extra, plantilla_libre,
                            historial=historial,
                        )
                        st.session_state["ultimo_menu"] = resultado
                        st.session_state["ultimo_precio"] = precio
                    except Exception as e:
                        st.error(f"Error al generar: {e}")
                        resultado = None

        resultado = st.session_state.get("ultimo_menu")
        precio_actual = st.session_state.get("ultimo_precio", precio)

        if resultado:
            k1, k2, k3 = st.columns(3)
            coste = resultado.get("coste_medio_estimado", 0)
            food_cost_pct = (coste / precio_actual * 100) if precio_actual else 0
            margen = resultado.get("margen_estimado", 0)
            k1.metric("Coste medio/comensal", f"{coste:.2f}€")
            k2.metric("Food cost", f"{food_cost_pct:.1f}%", delta="✓ OK" if food_cost_pct <= 35 else "⚠ Alto", delta_color="off")
            k3.metric("Margen estimado", f"{margen:.1f}%")
            st.divider()

            c1, c2, c3 = st.columns(3)

            def render_platos(col, titulo, lista):
                col.markdown(f"**{titulo}**")
                for p in lista:
                    dietas = p.get("dietas", [])
                    chips = ""
                    if "vegano" in dietas: chips += '<span class="chip chip-verde">Vegano</span>'
                    if "sin_gluten" in dietas: chips += '<span class="chip chip-verde">Sin gluten</span>'
                    if "vegetariano" in dietas: chips += '<span class="chip chip-verde">Veg</span>'
                    subtipo = p.get("subtipo", "")
                    subtipo_html = f'<span class="chip chip-azul">{subtipo}</span>' if subtipo else ""
                    col.markdown(f"""<div class="plato-card">
                        <b>{p['nombre']}</b>{subtipo_html}<br>
                        <small>{p['coste']:.2f}€/ración</small><br>{chips}
                    </div>""", unsafe_allow_html=True)

            render_platos(c1, "🥗 Primeros", resultado.get("primeros", []))
            render_platos(c2, "🥩 Segundos", resultado.get("segundos", []))
            render_platos(c3, "🍮 Postres", resultado.get("postres", []))

            st.divider()
            st.markdown(f"**💬 Notas del chef:** {resultado.get('notas_chef', '')}")
            for alerta in resultado.get("alertas", []):
                st.markdown(f'<div class="alerta">⚠️ {alerta}</div>', unsafe_allow_html=True)

            st.divider()
            with st.form("guardar_menu_form"):
                ca, cb = st.columns(2)
                nombre_menu = ca.text_input("Nombre del menú", value="Menú semana")
                fecha_menu = cb.date_input("Fecha")
                if st.form_submit_button("💾 Guardar este menú", use_container_width=True):
                    save_menu(nombre_menu, str(fecha_menu), precio_actual, resultado)
                    st.success("Menú guardado.")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — MIS PLATOS
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📋 Mis Platos":
    st.title("📋 Base de Datos de Platos")

    tab1, tab2 = st.tabs(["Ver platos", "Añadir plato"])

    with tab1:
        filtro_cat = st.selectbox("Filtrar por categoría", ["Todos", "primero", "segundo", "postre"])
        cat = None if filtro_cat == "Todos" else filtro_cat
        platos = get_platos(categoria=cat)
        st.caption(f"{len(platos)} platos encontrados")

        if not platos:
            st.info("No hay platos. Añádelos manualmente o impórtalos desde un documento.")
        else:
            for p in platos:
                with st.expander(f"**{p['nombre']}** — {p['categoria'].upper()} {('· ' + p['subtipo']) if p.get('subtipo') else ''} | {p['coste_racion']:.2f}€"):
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Proteína:** {p.get('proteina', '—')}")
                    c2.markdown(f"**Tiempo prep:** {p.get('tiempo_prep', '—')} min")
                    c3.markdown(f"**Coste ración:** {p['coste_racion']:.2f}€")
                    alergenos = json.loads(p.get("alergenos", "[]"))
                    dietas = json.loads(p.get("dietas", "[]"))
                    st.markdown(f"**Alérgenos:** {', '.join(alergenos) if alergenos and alergenos[0] != 'ninguno' else 'Ninguno'}")
                    st.markdown(f"**Dietas:** {', '.join(dietas) if dietas else 'Ninguna'}")
                    if p.get("descripcion"):
                        st.markdown(f"*{p['descripcion']}*")
                    if st.button("🗑️ Eliminar", key=f"del_{p['id']}"):
                        delete_plato(p["id"])
                        st.rerun()

    with tab2:
        st.subheader("Añadir nuevo plato")
        SUBTIPOS = {
            "primero": ["", "ensalada", "pasta", "crema", "sopa", "verdura", "legumbres", "arroz", "huevo", "otro"],
            "segundo": ["", "plancha", "frito", "guiso", "horno", "arroz", "pasta", "otro"],
            "postre": ["", "postre_frio", "postre_caliente", "fruta", "lacteo", "pasteleria", "otro"],
        }
        with st.form("form_nuevo_plato"):
            nombre = st.text_input("Nombre del plato *")
            col1, col2, col3 = st.columns(3)
            categoria = col1.selectbox("Categoría *", ["primero", "segundo", "postre"])
            proteina = col2.selectbox("Proteína principal", ["ninguna", "pollo", "cerdo", "ternera", "cordero", "pescado", "marisco", "huevo", "vegetal"])
            subtipo = col3.text_input("Subtipo", placeholder="ensalada, pasta, crema…")
            col4, col5 = st.columns(2)
            coste = col4.number_input("Coste por ración (€) *", min_value=0.10, max_value=50.0, value=2.0, step=0.10)
            tiempo = col5.number_input("Tiempo prep (min)", min_value=1, max_value=300, value=20)
            descripcion = st.text_area("Descripción / ingredientes", height=60)

            st.markdown("**Alérgenos:**")
            cols_a = st.columns(4)
            tiene_gluten = cols_a[0].checkbox("Gluten")
            tiene_lactosa = cols_a[1].checkbox("Lácteos")
            tiene_huevo = cols_a[2].checkbox("Huevo")
            tiene_pescado = cols_a[3].checkbox("Pescado")
            cols_a2 = st.columns(4)
            tiene_marisco = cols_a2[0].checkbox("Marisco")
            tiene_fn = cols_a2[1].checkbox("Frutos secos")
            tiene_soja = cols_a2[2].checkbox("Soja")
            tiene_apio = cols_a2[3].checkbox("Apio")

            st.markdown("**Apto para:**")
            cols_d = st.columns(4)
            es_vegano = cols_d[0].checkbox("Vegano")
            es_veg = cols_d[1].checkbox("Vegetariano")
            es_sg = cols_d[2].checkbox("Sin gluten")
            es_sl = cols_d[3].checkbox("Sin lactosa")

            if st.form_submit_button("➕ Añadir plato", type="primary"):
                if not nombre:
                    st.error("El nombre es obligatorio.")
                else:
                    alergenos = [a for a, ok in [
                        ("gluten", tiene_gluten), ("lactosa", tiene_lactosa), ("huevo", tiene_huevo),
                        ("pescado", tiene_pescado), ("marisco", tiene_marisco), ("frutos_secos", tiene_fn),
                        ("soja", tiene_soja), ("apio", tiene_apio),
                    ] if ok] or ["ninguno"]
                    dietas = [d for d, ok in [
                        ("vegano", es_vegano), ("vegetariano", es_veg),
                        ("sin_gluten", es_sg), ("sin_lactosa", es_sl),
                    ] if ok]
                    add_plato(nombre, categoria, proteina, coste, tiempo, alergenos, dietas, descripcion, subtipo)
                    st.success(f"✅ '{nombre}' añadido.")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — IMPORTAR PLATOS
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📥 Importar Platos":
    st.title("📥 Importar Platos desde Documento")
    st.markdown(
        "Sube tu carta, lista de platos o recetario en PDF o TXT. "
        "La IA extraerá todos los platos automáticamente para que los revises antes de guardarlos."
    )

    archivo = st.file_uploader(
        "Selecciona un archivo",
        type=["pdf", "txt"],
        help="Se aceptan cartas en PDF, listas en TXT o cualquier documento de texto con nombres de platos.",
    )

    if archivo:
        st.info(f"Archivo subido: **{archivo.name}** ({archivo.size // 1024} KB)")
        if st.button("🔍 Extraer platos con IA", type="primary"):
            with st.spinner("La IA está leyendo el documento y extrayendo platos..."):
                try:
                    contenido = archivo.read()
                    if archivo.name.lower().endswith(".pdf"):
                        platos_extraidos = importar_platos_desde_pdf(contenido)
                    else:
                        texto = contenido.decode("utf-8", errors="ignore")
                        platos_extraidos = importar_platos_desde_texto(texto)
                    st.session_state["platos_importados"] = platos_extraidos
                except Exception as e:
                    st.error(f"Error al procesar el documento: {e}")

    platos_importados = st.session_state.get("platos_importados")

    if platos_importados:
        st.success(f"✅ Se han extraído **{len(platos_importados)} platos**. Revísalos antes de guardar.")
        st.divider()

        # Mostrar tabla editable
        seleccionados = []
        for i, p in enumerate(platos_importados):
            with st.expander(
                f"**{p.get('nombre', '?')}** — {p.get('categoria', '?').upper()} "
                f"{'· ' + p['subtipo'] if p.get('subtipo') else ''} | {p.get('coste_racion', 0):.2f}€",
                expanded=False,
            ):
                cols = st.columns([2, 1, 1, 1])
                p["nombre"] = cols[0].text_input("Nombre", value=p.get("nombre", ""), key=f"imp_nom_{i}")
                p["categoria"] = cols[1].selectbox("Categoría", ["primero", "segundo", "postre"],
                    index=["primero", "segundo", "postre"].index(p.get("categoria", "primero")),
                    key=f"imp_cat_{i}")
                p["subtipo"] = cols[2].text_input("Subtipo", value=p.get("subtipo", ""), key=f"imp_sub_{i}")
                p["coste_racion"] = cols[3].number_input("Coste (€)", value=float(p.get("coste_racion", 1.0)),
                    min_value=0.1, step=0.1, key=f"imp_cos_{i}")

                c2a, c2b = st.columns(2)
                p["proteina"] = c2a.selectbox("Proteína", ["ninguna","pollo","cerdo","ternera","cordero","pescado","marisco","huevo","vegetal"],
                    index=["ninguna","pollo","cerdo","ternera","cordero","pescado","marisco","huevo","vegetal"].index(p.get("proteina","ninguna"))
                    if p.get("proteina","ninguna") in ["ninguna","pollo","cerdo","ternera","cordero","pescado","marisco","huevo","vegetal"] else 0,
                    key=f"imp_pro_{i}")
                p["descripcion"] = c2b.text_input("Descripción", value=p.get("descripcion", ""), key=f"imp_des_{i}")

                alergenos_actuales = p.get("alergenos", ["ninguno"])
                dietas_actuales = p.get("dietas", [])
                st.caption(f"Alérgenos detectados: {', '.join(alergenos_actuales)} | Dietas: {', '.join(dietas_actuales) if dietas_actuales else 'ninguna'}")

                incluir = st.checkbox("✅ Incluir este plato", value=True, key=f"imp_inc_{i}")
                if incluir:
                    seleccionados.append(p)

        st.divider()
        col_a, col_b = st.columns(2)
        col_a.markdown(f"**{len(seleccionados)} de {len(platos_importados)} platos seleccionados**")
        if col_b.button("💾 Guardar platos seleccionados", type="primary", use_container_width=True):
            if seleccionados:
                bulk_add_platos(seleccionados)
                st.success(f"✅ {len(seleccionados)} platos añadidos a tu base de datos.")
                del st.session_state["platos_importados"]
                st.balloons()
            else:
                st.warning("No has seleccionado ningún plato.")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — DESPENSA (con multimodal)
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🛒 Despensa":
    st.title("🛒 Despensa de la Semana")
    st.markdown("**Nueva función:** Sube una foto y Claude detecta automáticamente los ingredientes.")

    tab1, tab2 = st.tabs(["📸 Análisis por Foto (Recomendado)", "✍️ Añadir Manual"])

    # === TAB 1: FOTO ===
    with tab1:
        st.subheader("📷 Toma o sube foto del frigorífico / despensa")
        foto = st.camera_input("Usar cámara") or st.file_uploader("Subir foto", type=["jpg", "jpeg", "png"])

        if foto:
            st.image(foto, caption="Foto subida", width=500)

            if st.button("🔍 Analizar foto con Claude", type="primary", use_container_width=True):
                with st.spinner("Claude está analizando la despensa..."):
                    if isinstance(foto, st.runtime.uploaded_file_manager.UploadedFile):
                        bytes_data = foto.getvalue()
                    else:
                        bytes_data = foto.read()

                    resultado = analizar_foto_despensa(bytes_data)

                    if resultado.get("ingredientes"):
                        st.success(f"✅ Detectados **{len(resultado['ingredientes'])}** ingredientes")
                        for i, ing in enumerate(resultado["ingredientes"]):
                            with st.expander(f"🍅 {ing.get('ingrediente', 'Ingrediente')}"):
                                col1, col2 = st.columns(2)
                                cantidad = col1.text_input("Cantidad", ing.get("cantidad", ""), key=f"cant_{i}")
                                nota = col2.text_input("Nota / Caducidad", ing.get("nota", ""), key=f"nota_{i}")
                                if st.button("➕ Añadir a despensa", key=f"addphoto_{i}"):
                                    add_despensa(
                                        ing.get("ingrediente", ""),
                                        cantidad,
                                        "",
                                        "",
                                        nota
                                    )
                                    st.success(f"✅ {ing.get('ingrediente')} añadido")
                                    st.rerun()
                    else:
                        st.warning("No se detectaron ingredientes claros. Probá con otra foto.")

    # === TAB 2: MANUAL ===
    with tab2:
        st.subheader("Añadir ingrediente manualmente")
        with st.form("form_despensa"):
            ingrediente = st.text_input("Ingrediente *", placeholder="Ej: Queso manchego")
            c1, c2 = st.columns(2)
            cantidad = c1.text_input("Cantidad", placeholder="2")
            unidad = c2.selectbox("Unidad", ["kg", "g", "litros", "unidades", "raciones", "bandejas", "—"])
            caducidad = st.date_input("Caduca el (opcional)", value=None)
            nota = st.text_area("Nota", placeholder="De oferta / hay que gastar antes del viernes", height=60)
            if st.form_submit_button("➕ Añadir", type="primary", use_container_width=True):
                if ingrediente:
                    add_despensa(ingrediente, cantidad, unidad if unidad != "—" else "", str(caducidad) if caducidad else "", nota)
                    st.success(f"'{ingrediente}' añadido.")
                    st.rerun()

    # Lista actual
    st.subheader("📋 Ingredientes actuales en despensa")
    despensa = get_despensa()
    if not despensa:
        st.info("La despensa está vacía.")
    else:
        for item in despensa:
            c1, c2 = st.columns([5, 1])
            txt = f"**{item['ingrediente']}**"
            if item.get("cantidad"):
                txt += f" — {item['cantidad']} {item.get('unidad', '')}"
            if item.get("caducidad") and item["caducidad"] != "None":
                txt += f" | 📅 {item['caducidad']}"
            if item.get("nota"):
                txt += f"\n*{item['nota']}*"
            c1.markdown(txt)
            if c2.button("✕", key=f"del_d_{item['id']}"):
                delete_despensa(item["id"])
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 5 — ESCANDALLO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📊 Escandallo":
    st.title("📊 Calculadora de Escandallo")
    st.markdown("Introduce ingredientes con cantidades y precios. La IA calcula si encaja en el food cost del menú.")

    col1, col2 = st.columns([1, 1])

    with col1:
        nombre_plato = st.text_input("Nombre del plato", placeholder="Ej: Pollo al curry")
        precio_menu_esc = st.number_input("Precio del menú (€)", min_value=5.0, value=12.0, step=0.5)
        ingredientes_txt = st.text_area(
            "Ingredientes (cantidad + precio aproximado)",
            height=200,
            placeholder="- Pechuga de pollo: 200g, 5€/kg → ~1.00€\n- Cebolla: 50g, 0.80€/kg → ~0.04€\n- Nata: 100ml, 2€/litro → ~0.20€",
        )
        if st.button("🔍 Analizar escandallo", type="primary", use_container_width=True):
            if nombre_plato and ingredientes_txt:
                with st.spinner("Calculando..."):
                    try:
                        resultado = analizar_escandallo(nombre_plato, ingredientes_txt, precio_menu_esc)
                        st.session_state["ultimo_escandallo"] = resultado
                        st.session_state["esc_precio"] = precio_menu_esc
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.error("Rellena el nombre y los ingredientes.")

    with col2:
        esc = st.session_state.get("ultimo_escandallo")
        if esc:
            encaja = esc.get("encaja_en_menu", False)
            color = "#1b4332" if encaja else "#2d1f1f"
            icono = "✅" if encaja else "❌"
            max_fc = st.session_state.get("esc_precio", 12) * 0.35
            st.markdown(f"""<div style="background:{color}; padding:16px; border-radius:10px; margin-bottom:12px;">
                <h3>{icono} {'Encaja en el menú' if encaja else 'No encaja — coste elevado'}</h3>
                <b>Coste estimado:</b> {esc.get('coste_estimado', 0):.2f}€ / ración<br>
                <b>Margen:</b> {esc.get('margen', '—')}<br>
                <b>Food cost máximo:</b> {max_fc:.2f}€
            </div>""", unsafe_allow_html=True)
            if esc.get("sugerencias"):
                st.info(f"💡 {esc['sugerencias']}")
            if esc.get("desglose"):
                st.subheader("Desglose")
                for ing in esc["desglose"]:
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(ing["ingrediente"])
                    c2.markdown(f"**{ing['coste_estimado']:.2f}€**")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 6 — ESCÁNDALO MODE
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "♻️ Escándalo Mode":
    st.title("♻️ Escándalo Mode")
    st.markdown(
        "¿Te sobró de ayer? ¿Tienes ingredientes a punto de caducar? "
        "Dile a la IA qué tienes y te arma **platos de aprovechamiento épicos** — "
        "presentables, rentables y con nombre de carta."
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("¿Qué tienes para aprovechar?")

        # Opción de importar desde despensa
        despensa_actual = get_despensa()
        if despensa_actual:
            if st.button("📥 Importar todo de la despensa", use_container_width=True):
                st.session_state["sobras_escandalo"] = [
                    {"ingrediente": d["ingrediente"], "cantidad": d.get("cantidad", ""), "nota": d.get("nota", "")}
                    for d in despensa_actual
                ]

        st.markdown("**O añade manualmente:**")
        if "sobras_escandalo" not in st.session_state:
            st.session_state["sobras_escandalo"] = []

        with st.form("form_sobra"):
            c1, c2 = st.columns(2)
            sobra_nombre = c1.text_input("Ingrediente", placeholder="Ej: Bacalao al pil-pil")
            sobra_cantidad = c2.text_input("Cantidad", placeholder="Ej: 3 raciones")
            sobra_nota = st.text_input("Nota", placeholder="Ej: Sobró de ayer, hay que gastarlo hoy")
            if st.form_submit_button("➕ Añadir"):
                if sobra_nombre:
                    st.session_state["sobras_escandalo"].append({
                        "ingrediente": sobra_nombre,
                        "cantidad": sobra_cantidad,
                        "nota": sobra_nota,
                    })

        # Lista actual de sobras
        sobras = st.session_state.get("sobras_escandalo", [])
        if sobras:
            st.markdown(f"**{len(sobras)} ingredientes para aprovechar:**")
            for i, s in enumerate(sobras):
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"🔸 **{s['ingrediente']}** {s.get('cantidad', '')} {('— ' + s['nota']) if s.get('nota') else ''}")
                if c2.button("✕", key=f"del_s_{i}"):
                    st.session_state["sobras_escandalo"].pop(i)
                    st.rerun()

        st.divider()
        st.subheader("Configurar generación")
        precio_esc = st.number_input("Precio menú objetivo (€)", min_value=5.0, value=12.0, step=0.5)
        num_platos_esc = st.slider("Número de platos a crear", 1, 6, 3)
        estilo_esc = st.selectbox(
            "Estilo de cocina",
            ["libre", "tapas", "fusion", "tradicional"],
            format_func=lambda x: {
                "libre": "🎨 Libre — máxima creatividad",
                "tapas": "🍢 Tapas y platillos",
                "fusion": "🌏 Fusión atrevida",
                "tradicional": "🫕 Tradicional española",
            }[x],
        )

        generar_esc = st.button("🔥 ¡Armar platos épicos!", type="primary", use_container_width=True)

    with col2:
        if generar_esc:
            sobras = st.session_state.get("sobras_escandalo", [])
            if not sobras:
                st.error("Añade al menos un ingrediente para aprovechar.")
            else:
                with st.spinner("El chef está convirtiendo sobras en obras maestras..."):
                    try:
                        resultado_esc = modo_escandalo(sobras, precio_esc, num_platos_esc, estilo_esc)
                        st.session_state["resultado_escandalo"] = resultado_esc
                    except Exception as e:
                        st.error(f"Error: {e}")

        resultado_esc = st.session_state.get("resultado_escandalo")
        if resultado_esc:
            ahorro = resultado_esc.get("ahorro_estimado", "")
            consejo = resultado_esc.get("consejo_chef", "")

            if ahorro:
                st.info(f"💰 **Ahorro estimado:** {ahorro}")

            for plato in resultado_esc.get("platos", []):
                with st.container():
                    st.markdown(f"""<div style="background:#1a2035; border-left:4px solid #ff9800;
                        padding:16px; border-radius:8px; margin:8px 0;">
                        <h3 style="margin:0; color:#ff9800;">🍴 {plato['nombre']}</h3>
                        <p style="margin:6px 0;">{plato['descripcion']}</p>
                        <p><b>Categoría:</b> {plato['categoria'].upper()} &nbsp;|&nbsp;
                        <b>Coste:</b> {plato['coste_estimado']:.2f}€ &nbsp;|&nbsp;
                        <b>Tiempo:</b> {plato['tiempo_prep']} min</p>
                        <p><b>Ingredientes de sobras usados:</b> {', '.join(plato.get('ingredientes_usados', []))}</p>
                        <p><b>Añadir:</b> {', '.join(plato.get('ingredientes_extra', [])) or 'Nada extra'}</p>
                        <p style="color:#aed581;">✨ <i>{plato.get('wow_factor', '')}</i></p>
                    </div>""", unsafe_allow_html=True)

            if consejo:
                st.markdown(f"**💬 Consejo del chef:** {consejo}")

            st.divider()
            # Botón para añadir platos aprovechamiento a la BD
            if st.button("💾 Guardar estos platos en mi BD", use_container_width=True):
                from database import add_plato
                for plato in resultado_esc.get("platos", []):
                    add_plato(
                        nombre=plato["nombre"],
                        categoria=plato["categoria"],
                        proteina="ninguna",
                        coste_racion=plato["coste_estimado"],
                        tiempo_prep=plato["tiempo_prep"],
                        alergenos=["ninguno"],
                        dietas=[],
                        descripcion=plato["descripcion"],
                        subtipo="aprovechamiento",
                    )
                st.success(f"✅ {len(resultado_esc.get('platos', []))} platos añadidos a tu BD de platos.")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 7 — MENÚS GUARDADOS
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📁 Menús Guardados":
    st.title("📁 Historial de Menús")

    menus = get_menus_guardados()
    if not menus:
        st.info("Todavía no has guardado ningún menú.")
    else:
        for m in menus:
            with st.expander(f"**{m['nombre']}** — {m['fecha']} | {m['precio_menu']}€"):
                contenido = m["contenido"]
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("**Primeros**")
                    for p in contenido.get("primeros", []):
                        st.markdown(f"- {p['nombre']} ({p['coste']:.2f}€)")
                with c2:
                    st.markdown("**Segundos**")
                    for p in contenido.get("segundos", []):
                        st.markdown(f"- {p['nombre']} ({p['coste']:.2f}€)")
                with c3:
                    st.markdown("**Postres**")
                    for p in contenido.get("postres", []):
                        st.markdown(f"- {p['nombre']} ({p['coste']:.2f}€)")
                if contenido.get("notas_chef"):
                    st.markdown(f"*{contenido['notas_chef']}*")
                st.caption(f"Coste medio: {contenido.get('coste_medio_estimado', '—')}€ | Guardado: {m['created_at']}")
