#!/bin/bash
# ============================================================================
#  NUEVO_CLIENTE.SH
#  Despliega una instancia nueva del CRM para un cliente.
#  Se ejecuta EN EL SERVIDOR (lo lanza desplegar_cliente.ps1 por SSH).
#
#  Variables de entorno requeridas:
#    CLIENTE_SLUG      — identificador corto sin espacios (ej: restaurante-mar)
#    CLIENTE_NOMBRE    — nombre completo (ej: "Restaurante Mar")
#    WEB_PORT          — puerto web (asignado automáticamente)
#    API_PORT          — puerto API (asignado automáticamente)
#    DOMINIO           — dominio del cliente (opcional, ej: crm.restaurantemar.com)
#    ANTHROPIC_KEY          — API key de Anthropic (opcional)
#    YCLOUD_API_KEY         — API key de YCloud (opcional)
#    YCLOUD_WEBHOOK_SECRET  — Webhook secret de YCloud (opcional)
#    YCLOUD_WHATSAPP_NUMBER — Número WhatsApp Business en E.164 (opcional)
#    TWILIO_ACCOUNT_SID     — Account SID de Twilio (opcional)
#    TWILIO_AUTH_TOKEN      — Auth token de Twilio (opcional)
#    TWILIO_PHONE_NUMBER    — Número de teléfono Twilio en E.164 (opcional)
#    PUBLIC_URL             — URL pública del servidor (para webhooks)
#    REPO_URL               — URL del repositorio git
# ============================================================================
set -e

CLIENTE_SLUG="${CLIENTE_SLUG:?Falta CLIENTE_SLUG}"
WEB_PORT="${WEB_PORT:?Falta WEB_PORT}"
API_PORT="${API_PORT:?Falta API_PORT}"
REPO_URL="${REPO_URL:-https://github.com/luis07bcn-glitch/agente-whatsapp-citas.git}"
DIR="/opt/merakia-clients/${CLIENTE_SLUG}"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  MerakIA — Desplegando cliente               ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  Cliente : ${CLIENTE_NOMBRE:-$CLIENTE_SLUG}"
echo "  Carpeta : $DIR"
echo "  Web     : puerto $WEB_PORT"
echo "  API     : puerto $API_PORT"
if [ -n "$DOMINIO" ]; then
echo "  Dominio : $DOMINIO"
fi
echo ""

# ── Clonar o actualizar el código ───────────────────────────────────────────
if [ -d "$DIR/.git" ]; then
  echo "▶ Actualizando código existente..."
  git -C "$DIR" pull --ff-only
else
  echo "▶ Clonando repositorio..."
  git clone "$REPO_URL" "$DIR"
fi

# ── Generar contraseña aleatoria para la BD ──────────────────────────────────
DB_PASS=$(openssl rand -hex 16)

# Preservar contraseña existente si el cliente ya existía
if [ -f "$DIR/.env" ]; then
  EXISTING_PASS=$(grep POSTGRES_PASSWORD "$DIR/.env" | cut -d= -f2)
  if [ -n "$EXISTING_PASS" ]; then
    DB_PASS="$EXISTING_PASS"
    echo "  ↺ Contraseña de BD existente conservada."
  fi
fi

# ── Crear archivo .env del cliente ───────────────────────────────────────────
cat > "$DIR/.env" <<ENV
# === Cliente: ${CLIENTE_NOMBRE:-$CLIENTE_SLUG} ===
# Generado automáticamente el $(date '+%Y-%m-%d')

POSTGRES_USER=citas
POSTGRES_PASSWORD=${DB_PASS}
POSTGRES_DB=citas
DATABASE_URL=postgres://citas:${DB_PASS}@db:5432/citas

OPENROUTER_API_KEY=${ANTHROPIC_KEY:-}
AGENT_MODEL=claude-sonnet-4-6

# WhatsApp (YCloud)
YCLOUD_API_KEY=${YCLOUD_API_KEY:-}
YCLOUD_WEBHOOK_SECRET=${YCLOUD_WEBHOOK_SECRET:-}
YCLOUD_WHATSAPP_NUMBER=${YCLOUD_WHATSAPP_NUMBER:-}

# Voz (Twilio)
TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID:-}
TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN:-}
TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER:-}

# URL pública (para webhooks de YCloud y Twilio)
PUBLIC_URL=${PUBLIC_URL:-}

SEED_DEMO_DATA=true

API_HOST_PORT=${API_PORT}
WEB_HOST_PORT=${WEB_PORT}
WEB_ORIGIN=${PUBLIC_URL:-http://localhost:${WEB_PORT}}
NEXT_PUBLIC_API_URL=${PUBLIC_URL:-http://localhost:${API_PORT}}

TZ=Europe/Madrid
ENV

echo "✓ Archivo .env creado."

# ── Construir y arrancar con Docker Compose ──────────────────────────────────
echo "▶ Construyendo y arrancando contenedores (puede tardar 2-3 min la primera vez)..."
cd "$DIR"
docker compose -f docker-compose.prod.yml up -d --build

echo "✓ Contenedores arrancados."

# ── Configurar Caddy si hay dominio ─────────────────────────────────────────
if [ -n "$DOMINIO" ]; then
  # Eliminar bloque anterior del mismo cliente si existía
  CADDY_FILE="/etc/caddy/Caddyfile.merakia"
  if grep -q "# CLIENTE:${CLIENTE_SLUG}" "$CADDY_FILE" 2>/dev/null; then
    # Borrar el bloque anterior (entre las líneas marcadas)
    sed -i "/# CLIENTE:${CLIENTE_SLUG}/,/# FIN:${CLIENTE_SLUG}/d" "$CADDY_FILE"
  fi

  # Añadir nuevo bloque
  cat >> "$CADDY_FILE" <<CADDY

# CLIENTE:${CLIENTE_SLUG}
${DOMINIO} {
    # Panel CRM — protegido con contraseña básica
    basicauth /* {
        admin $(echo -n "merakia2024" | caddy hash-password --plaintext "merakia2024" 2>/dev/null || echo '$2a$14$PLACEHOLDER')
    }
    # Solo el webhook de WhatsApp queda sin contraseña
    @webhook path /api/webhooks/*
    handle @webhook {
        reverse_proxy localhost:${API_PORT}
    }
    reverse_proxy localhost:${WEB_PORT}
}
# FIN:${CLIENTE_SLUG}
CADDY

  systemctl reload caddy
  echo "✓ Caddy configurado para $DOMINIO."
fi

# ── Registrar el cliente ──────────────────────────────────────────────────────
REGISTRO="/opt/merakia-clients/registro.json"
python3 - <<PYTHON
import json, datetime

with open('$REGISTRO', 'r') as f:
    data = json.load(f)

# Eliminar si ya existía
data['clientes'] = [c for c in data['clientes'] if c['slug'] != '$CLIENTE_SLUG']

data['clientes'].append({
    'slug': '$CLIENTE_SLUG',
    'nombre': '${CLIENTE_NOMBRE:-$CLIENTE_SLUG}',
    'webPort': $WEB_PORT,
    'apiPort': $API_PORT,
    'dominio': '${DOMINIO:-}',
    'creado': datetime.date.today().isoformat()
})

with open('$REGISTRO', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('✓ Cliente registrado.')
PYTHON

# ── Resumen final ────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ Cliente desplegado correctamente"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  Nombre  : ${CLIENTE_NOMBRE:-$CLIENTE_SLUG}"
if [ -n "$DOMINIO" ]; then
echo "  URL     : https://$DOMINIO"
echo "  Usuario : admin"
echo "  Clave   : merakia2024  ← cámbiala desde Caddy"
else
echo "  URL web : http://IP-DEL-SERVIDOR:${WEB_PORT}"
echo "  URL API : http://IP-DEL-SERVIDOR:${API_PORT}/api"
fi
echo ""
if [ -n "${YCLOUD_API_KEY}" ]; then
  echo "  WhatsApp : configurado (${YCLOUD_WHATSAPP_NUMBER})"
  echo "             Webhook YCloud → POST ${PUBLIC_URL}/api/webhooks/ycloud"
else
  echo "  WhatsApp : pendiente — anadir YCLOUD_* en $DIR/.env"
fi
if [ -n "${TWILIO_ACCOUNT_SID}" ]; then
  echo "  Voz      : configurado (${TWILIO_PHONE_NUMBER})"
  echo "             Webhook Twilio → POST ${PUBLIC_URL}/api/voice/incoming"
else
  echo "  Voz      : pendiente — anadir TWILIO_* en $DIR/.env"
fi
echo ""
echo "  Para actualizar credenciales despues del despliegue:"
echo "    nano $DIR/.env"
echo "    docker compose -f $DIR/docker-compose.prod.yml restart api"
echo ""
