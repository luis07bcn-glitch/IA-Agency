# GestorIA — el copiloto del despacho

Software para gestorías y asesorías españolas. La tesis: una gestoría no
necesita "IA", necesita **horas**. Cada módulo ataca un ladrón de horas
concreto del despacho y es demostrable en 20 minutos con datos reales.

## Lanzar el panel

```
venv\Scripts\streamlit.exe run gestorias/app_gestoria.py --server.port 8509
```

CLI del radar (para cron/tarea programada diaria):

```
venv\Scripts\python.exe gestorias\run_radar.py --dias 7            # ingesta + clasificación
venv\Scripts\python.exe gestorias\run_radar.py --dias 7 --boletin  # + boletín para clientes
```

## Módulos construidos (v0.1)

| Módulo | Qué hace | Ladrón de horas que ataca |
|---|---|---|
| 📡 **Radar normativo** | Ingesta el BOE diario (API datos abiertos), prefiltro por keywords (descarta ~80% gratis), clasificación con Claude: relevancia, impacto, área, a quién afecta y qué hacer | "Estar al día de normativa robando horas facturables" |
| 📬 **Boletín para clientes** | Redacta con IA un boletín semanal en lenguaje llano listo para reenviar con la marca del despacho | El despacho queda como "el que siempre avisa" sin dedicarle una tarde |
| 📅 **Calendario fiscal** | Vencimientos de los modelos habituales (111, 115, 130/131, 303, 349, 390, 347, 100, 200, 202, 720, cuentas anuales), con ajuste de fin de semana | Control de plazos sin Excel artesanal |
| 📥 **Correo** | Lee la bandeja (IMAP solo-lectura o .eml), clasifica cada correo (factura / requerimiento / documentación / consulta / comercial), prioriza lo urgente y pasa las facturas adjuntas por el extractor. **Cartera de clientes**: identifica de qué negocio es cada factura (email del remitente → CIF leído en la factura) y guarda todo en `salida/<periodo>/<Cliente>/` con su CSV — "en la carpeta Meraki están sus facturas, en la de Loli las suyas" | "Infinidad de correos con facturas para el trimestre" (verbatim de prospectos) + requerimientos AEAT/TGSS enterrados en la bandeja |
| 🧾 **Extractor de facturas** | Visión con Claude: factura (PNG/JPG/PDF) → campos estructurados → CSV para A3/Sage/Holded. La "demo asesina" del playbook | Picar datos a mano: 30-50% del tiempo del equipo admin |

Datos: `gestorias/data/radar.db` (SQLite; contenido público del BOE, no sensible).
Coste API: prefiltro descarta la mayoría sin tokens; clasificación con Haiku
(barata, solo títulos); el boletín con Sonnet (texto de cara al cliente).
Modelos configurables vía `RADAR_CLASSIFY_MODEL` / `RADAR_DIGEST_MODEL`.

## Roadmap — la visión completa

El objetivo a largo plazo es el mejor software de despacho del mercado. Pero
**cada fase se desbloquea vendiendo, no construyendo**
(ver `docs/prospeccion_gestorias_playbook.md`):

- **Fase 1 (AHORA)** — Radar + boletín + calendario + extractor. Sirve para la
  demo del diagnóstico de 490 € y como asset de outreach (enviar el boletín
  semanal a los 40 prospectos = valor por adelantado).
  *Gate: 1 diagnóstico pagado en 4 semanas.*
- **Fase 2** — Piloto IDP con cliente real: extracción en lote desde email/
  WhatsApp, validación humana en el panel, export al software del despacho
  (A3/Sage/Holded). Seguimiento de expedientes y avisos a clientes.
  *Gate: piloto de 2.500–4.500 € vendido.*
- **Fase 3** — Asistentes de campaña: Renta (checklist por cliente, borradores
  de requerimientos, simulaciones IRPF), Impuesto de Sociedades (ajustes al
  resultado contable, deducciones), IVA (cuadre 303↔390↔347).
  Importante: NO presentamos impuestos; preparamos el trabajo para que el
  gestor presente. La presentación exige certificados/colaboración social AEAT
  y responsabilidad que se queda en el despacho.
  *Gate: 2-3 despachos en iguala mensual.*
- **Fase 4** — Multi-despacho (SaaS): fuentes autonómicas (DOGC, BOPs),
  convenios por sector del cliente, alertas personalizadas por cartera
  ("tienes 12 clientes en el convenio del metal de Barcelona → esto les
  afecta"), Verifactu. Aquí es donde se convierte en producto.

## Arquitectura

```
gestorias/
├── radar/
│   ├── boe.py          # cliente API datos abiertos BOE (secciones 1 y 3)
│   ├── classifier.py   # prefiltro keywords → clasificación Claude en lotes
│   ├── digest.py       # boletín para clientes (markdown)
│   ├── calendario.py   # vencimientos fiscales deterministas
│   └── store.py        # SQLite (items + boletines)
├── clientes.py         # cartera: negocio ↔ emails/CIF ↔ carpeta (tabla en SQLite)
├── correo/
│   ├── fuentes.py      # IMAP solo-lectura + carpeta .eml (demo/export Outlook)
│   ├── clasificador.py # Claude Haiku en lotes + fallback keywords
│   ├── pipeline.py     # bandeja → clasificación → extracción → cliente → carpetas
│   └── _generar_demo.py# demo: 4 negocios, 10 .eml, 15 facturas adjuntas
├── salida/             # <periodo>/<Cliente>/facturas + CSV (gitignored)
├── run_radar.py        # CLI de ingesta (cron diario)
├── app_gestoria.py     # panel Streamlit (puerto 8509)
└── extractor_facturas.py  # visión: factura → JSON/CSV
```

Fuentes futuras enchufables en `radar/`: DOGC/BOPs (Fase 4), consultas
vinculantes DGT, novedades AEAT (sus RSS antiguos ya no existen; habrá que
scrapear la sede o esperar API).
