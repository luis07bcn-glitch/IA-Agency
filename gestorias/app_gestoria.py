# -*- coding: utf-8 -*-
"""
GestorIA — panel para gestorías (Streamlit).

    venv\\Scripts\\streamlit.exe run gestorias/app_gestoria.py --server.port 8509

Módulos:
- Radar normativo: BOE clasificado por IA (qué cambia, a quién afecta, qué hacer)
- Boletín clientes: resumen en llano listo para reenviar con la marca del despacho
- Calendario fiscal: próximos vencimientos de los modelos habituales
- Extractor de facturas: la demo asesina del playbook (módulo ya existente)
"""
import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gestorias.radar import boe, calendario, classifier, digest, store  # noqa: E402

st.set_page_config(page_title="GestorIA — MerakIA", page_icon="📋", layout="wide")

AREA_LABELS = {
    "fiscal": "Fiscal", "laboral": "Laboral", "seguridad_social": "Seg. Social",
    "mercantil": "Mercantil", "subvenciones": "Subvenciones",
    "contable": "Contable", "otros": "Otros",
}
IMPACTO_BADGE = {"alto": "🔴 Alto", "medio": "🟠 Medio", "bajo": "🟢 Bajo"}


@st.cache_resource
def _conn():
    return store.get_conn()


conn = _conn()

st.title("📋 GestorIA")
st.caption("El copiloto normativo del despacho — MerakIA")

tab_radar, tab_boletin, tab_cal, tab_correo, tab_facturas = st.tabs(
    ["📡 Radar normativo", "📬 Boletín para clientes", "📅 Calendario fiscal",
     "📥 Correo", "🧾 Extractor de facturas"]
)

# ---------------------------------------------------------------- Radar
with tab_radar:
    col_a, col_b = st.columns([3, 1])
    with col_b:
        dias_actualizar = st.number_input("Días a actualizar", 1, 30, 7)
        if st.button("🔄 Actualizar BOE", use_container_width=True):
            hoy = dt.date.today()
            desde = hoy - dt.timedelta(days=int(dias_actualizar) - 1)
            with st.spinner(f"Descargando BOE {desde} → {hoy}..."):
                items = boe.sumarios_rango(desde, hoy)
                nuevos = store.upsert_items(conn, [it.as_dict() for it in items])
            with st.spinner("Clasificando con IA..."):
                stats = classifier.clasificar_pendientes(conn, log=lambda m: None)
            st.success(f"{nuevos} items nuevos · {stats['relevantes']} relevantes detectados")

    with col_a:
        f1, f2, f3, f4 = st.columns(4)
        rango_dias = f1.selectbox("Periodo", [7, 14, 30, 60, 90], index=2,
                                  format_func=lambda d: f"Últimos {d} días")
        area_sel = f2.selectbox("Área", ["todas"] + list(AREA_LABELS),
                                format_func=lambda a: AREA_LABELS.get(a, "Todas"))
        impacto_sel = f3.selectbox("Impacto", ["todos", "alto", "medio", "bajo"])
        buscar = f4.text_input("Buscar", placeholder="verifactu, convenio metal...")

    hoy = dt.date.today()
    desde_iso = (hoy - dt.timedelta(days=rango_dias)).isoformat()
    items = store.items_relevantes(conn, desde_iso, hoy.isoformat())

    if area_sel != "todas":
        items = [i for i in items if area_sel in i["areas"]]
    if impacto_sel != "todos":
        items = [i for i in items if i["impacto"] == impacto_sel]
    if buscar:
        q = buscar.lower()
        items = [i for i in items if q in (i["titulo"] + (i["resumen"] or "")).lower()]

    st.markdown(f"**{len(items)} novedades relevantes**")
    if not items:
        st.info("Sin datos en este rango. Pulsa **Actualizar BOE** para ingerir los últimos días.")

    for it in items:
        badges = " ".join(f"`{AREA_LABELS.get(a, a)}`" for a in it["areas"])
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{it['resumen'] or it['titulo'][:200]}**")
            c2.markdown(IMPACTO_BADGE.get(it["impacto"], it["impacto"] or "—"))
            if it["afecta"]:
                c1.markdown(f"👥 *Afecta a:* {it['afecta']}")
            if it["accion"] and "informativo" not in it["accion"].lower():
                c1.markdown(f"✅ *Qué hacer:* {it['accion']}")
            c1.markdown(
                f"{badges} · {it['fecha']} · [{it['identificador']}]({it['url_html']})"
            )
            with c1.expander("Título oficial"):
                st.write(it["titulo"])

# ---------------------------------------------------------------- Boletín
with tab_boletin:
    st.markdown(
        "Boletín en lenguaje llano para **reenviar a los clientes del despacho** "
        "(email, WhatsApp o PDF con vuestra marca). Lo redacta la IA solo con lo "
        "clasificado como relevante; siempre con revisión humana antes de enviar."
    )
    c1, c2, c3 = st.columns([1, 1, 2])
    b_desde = c1.date_input("Desde", dt.date.today() - dt.timedelta(days=7))
    b_hasta = c2.date_input("Hasta", dt.date.today())
    if c3.button("✍️ Generar boletín", use_container_width=True):
        with st.spinner("Redactando boletín..."):
            try:
                md = digest.generar_boletin(conn, b_desde.isoformat(), b_hasta.isoformat())
                if not md:
                    st.warning("No hay novedades relevantes en ese rango.")
            except Exception as e:
                st.error(f"Error generando el boletín: {e}")

    ultimo = store.ultimo_boletin(conn)
    if ultimo:
        st.divider()
        st.caption(
            f"Último boletín · {ultimo['fecha_desde']} → {ultimo['fecha_hasta']} "
            f"(generado {ultimo['creado_en']})"
        )
        st.markdown(ultimo["contenido_md"])
        st.download_button(
            "⬇️ Descargar markdown", ultimo["contenido_md"],
            file_name=f"boletin_{ultimo['fecha_hasta']}.md",
        )

# ---------------------------------------------------------------- Calendario
with tab_cal:
    dias_cal = st.slider("Horizonte (días)", 15, 180, 60, step=15)
    vencs = calendario.proximos_vencimientos(dias=dias_cal)
    if vencs:
        df = pd.DataFrame([{
            "Fecha límite": v.fecha.strftime("%d/%m/%Y"),
            "Días": (v.fecha - dt.date.today()).days,
            "Modelo": v.modelo,
            "Qué es": v.descripcion,
            "Periodo": v.periodo,
            "Quién": v.colectivo,
        } for v in vencs])
        st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(
        "Reglas generales del calendario del contribuyente (ajuste automático de "
        "fines de semana; festivos no incluidos). Las domiciliaciones cierran "
        "~5 días antes. Verificar siempre fechas exactas en sede de la AEAT."
    )

# ---------------------------------------------------------------- Correo
with tab_correo:
    st.markdown(
        "La bandeja del despacho, **ordenada sola**: clasifica cada correo "
        "(facturas / requerimientos / documentación / consultas / comercial), "
        "prioriza lo urgente y **extrae automáticamente las facturas adjuntas** "
        "→ CSV listo para A3/Sage/Holded."
    )

    from gestorias import clientes as cartera_mod

    with st.expander("👥 Cartera de clientes (quién es quién en la bandeja)"):
        st.caption("Cada negocio con su(s) email(s) y su carpeta. La identificación "
                   "usa el remitente y, si no, el CIF leído en la propia factura. "
                   "Varios emails separados por `;`.")
        conn_cli = cartera_mod.get_conn()
        df_cartera = pd.DataFrame([{
            "nombre": c.nombre, "cif": c.cif,
            "emails": "; ".join(c.emails), "carpeta": c.carpeta,
        } for c in cartera_mod.listar(conn_cli)] or [{"nombre": "", "cif": "", "emails": "", "carpeta": ""}])
        df_editada = st.data_editor(df_cartera, num_rows="dynamic",
                                    use_container_width=True, key="editor_cartera")
        if st.button("💾 Guardar cartera"):
            cartera_mod.reemplazar_cartera(conn_cli, df_editada.to_dict("records"))
            st.success("Cartera guardada")

    fuente = st.radio("Fuente", ["Bandeja demo (.eml)", "Buzón IMAP real"],
                      horizontal=True, label_visibility="collapsed")
    imap_cfg = None
    if fuente == "Buzón IMAP real":
        with st.expander("Conexión IMAP (solo lectura)", expanded=True):
            c1, c2 = st.columns(2)
            imap_host = c1.text_input("Servidor", placeholder="imap.gmail.com / outlook.office365.com")
            imap_dias = c2.number_input("Días hacia atrás", 1, 365, 92)
            imap_user = c1.text_input("Usuario", placeholder="despacho@...")
            imap_pass = c2.text_input("Contraseña de aplicación", type="password")
            st.caption("Gmail/Outlook: usar contraseña de aplicación, no la de la cuenta. "
                       "No se marca ni se mueve ningún correo.")
            imap_cfg = (imap_host, imap_user, imap_pass, int(imap_dias))

    if st.button("📥 Procesar bandeja", use_container_width=True):
        from gestorias.correo import fuentes as correo_fuentes
        from gestorias.correo.pipeline import procesar_bandeja

        try:
            with st.spinner("Leyendo correos..."):
                if imap_cfg:
                    host, user, pwd, dias = imap_cfg
                    correos = correo_fuentes.leer_imap(host, user, pwd, dias=dias)
                else:
                    correos = correo_fuentes.leer_carpeta_eml()
            with st.spinner(f"Clasificando {len(correos)} correos y extrayendo facturas..."):
                st.session_state["bandeja"] = procesar_bandeja(correos, log=lambda m: None)
        except Exception as e:
            st.error(f"Error procesando la bandeja: {e}")

    r = st.session_state.get("bandeja")
    if r:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Correos", len(r.correos))
        m2.metric("🔴 Urgentes", r.urgentes)
        m3.metric("🧾 Facturas extraídas", len(r.facturas))
        m4.metric("Categorías", len(r.por_categoria))

        PRIO = {"alta": "🔴 Alta", "media": "🟠 Media", "baja": "🟢 Baja"}
        CAT = {"factura": "🧾 Factura", "requerimiento": "⚠️ Requerimiento",
               "documentacion": "📎 Documentación", "consulta": "💬 Consulta",
               "comercial": "🗑️ Comercial", "otro": "Otro"}
        por_uid = {c.uid: c for c in r.correos}
        orden = {"alta": 0, "media": 1, "baja": 2}
        df_correos = pd.DataFrame([{
            "Prioridad": PRIO.get(c.prioridad, c.prioridad),
            "Categoría": CAT.get(c.categoria, c.categoria),
            "De": por_uid[c.uid].de,
            "Asunto": por_uid[c.uid].asunto,
            "Resumen": c.resumen,
            "Siguiente paso": c.accion,
        } for c in sorted(r.clasificaciones, key=lambda c: orden.get(c.prioridad, 3))])
        st.dataframe(df_correos, use_container_width=True, hide_index=True)

        if r.facturas:
            st.subheader("🗂️ Facturas por negocio")
            cols = ["_archivo", "emisor_nombre", "numero_factura", "fecha",
                    "base_imponible", "tipo_iva", "cuota_iva", "retencion_irpf", "total"]
            for nombre_cli, filas in r.facturas_por_cliente.items():
                suma = sum(f.get("total") or 0 for f in filas)
                titulo = f"{nombre_cli} — {len(filas)} facturas · {suma:,.2f} €"
                with st.expander(titulo, expanded=nombre_cli.startswith("⚠")):
                    df_cli = pd.DataFrame(filas)
                    st.dataframe(df_cli[[c for c in cols if c in df_cli.columns]],
                                 use_container_width=True, hide_index=True)
                    if nombre_cli.startswith("⚠"):
                        st.info("Remitente no registrado: dale de alta en la "
                                "**Cartera de clientes** (arriba) y reprocesa.")

            st.divider()
            from gestorias.correo.pipeline import guardar_en_carpetas, periodo_por_defecto
            c1, c2 = st.columns([1, 2])
            periodo = c1.text_input("Periodo", periodo_por_defecto())
            if c2.button("🗂️ Guardar en carpetas por cliente", use_container_width=True):
                resumen = guardar_en_carpetas(r, periodo)
                st.success(f"Guardado en `gestorias/salida/{periodo}/` — "
                           + " · ".join(f"{c.split('(')[0].strip()}: {i['n']}"
                                        for c, i in resumen.items()))

            df_todas = pd.DataFrame([{k: v for k, v in f.items() if k != "_adjunto_bytes"}
                                     for f in r.facturas])
            st.download_button(
                "⬇️ Descargar CSV global para el software del despacho",
                df_todas.to_csv(index=False).encode("utf-8-sig"),
                file_name="facturas_bandeja.csv", mime="text/csv",
            )
        if r.errores_extraccion:
            st.warning("Adjuntos no procesados: " + "; ".join(r.errores_extraccion))
    else:
        st.info("Pulsa **Procesar bandeja** para ver la demo con 8 correos reales "
                "(facturas del trimestre, notificación AEAT, consultas, spam).")

# ---------------------------------------------------------------- Facturas
with tab_facturas:
    st.markdown(
        """La **demo asesina** del playbook: extracción estructurada de facturas
con visión (Claude) lista para volcar a A3/Sage/Holded.

Módulo CLI ya operativo:
```
venv\\Scripts\\python.exe gestorias\\extractor_facturas.py ruta\\a\\factura.png
```
"""
    )
    subido = st.file_uploader("Probar con una factura (PNG/JPG/PDF)",
                              type=["png", "jpg", "jpeg", "webp", "pdf"])
    if subido is not None:
        with st.spinner("Extrayendo campos..."):
            try:
                from gestorias.extractor_facturas import extraer_factura_bytes
                resultado = extraer_factura_bytes(subido.getvalue(), subido.name)
                st.json(resultado)
            except Exception as e:
                st.error(f"Error en la extracción: {e}")
