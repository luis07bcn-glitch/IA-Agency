# ============================================================================
#  DESPLEGAR_CLIENTE.PS1
#  Script interactivo para desplegar un cliente nuevo desde Windows.
#  Conecta al servidor por SSH y hace todo automáticamente.
#
#  Uso:
#    1. Clic derecho → "Ejecutar con PowerShell"
#    2. Sigue las preguntas en pantalla
# ============================================================================

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "MerakIA — Desplegar cliente"

Clear-Host
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        MerakIA — Asistente de despliegue            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Datos del servidor ────────────────────────────────────────────────────────
Write-Host "── SERVIDOR ──────────────────────────────────────────" -ForegroundColor Yellow
$SERVER_IP   = Read-Host "  IP del servidor (ej: 95.217.1.100)"
$SERVER_USER = Read-Host "  Usuario SSH     [root]"
if (-not $SERVER_USER) { $SERVER_USER = "root" }

Write-Host ""
Write-Host "── CLIENTE NUEVO ─────────────────────────────────────" -ForegroundColor Yellow
$NOMBRE = Read-Host "  Nombre del negocio (ej: Restaurante Mar)"

# Generar slug automáticamente
$SLUG = $NOMBRE.ToLower() `
  -replace '[áàä]','a' -replace '[éèë]','e' `
  -replace '[íìï]','i' -replace '[óòö]','o' `
  -replace '[úùü]','u' -replace 'ñ','n' `
  -replace '[^a-z0-9]+','-' -replace '^-|-$',''

Write-Host "  Identificador  : $SLUG" -ForegroundColor Gray

$DOMINIO = Read-Host "  Dominio (ej: crm.restaurantemar.com) [opcional, Enter para omitir]"

Write-Host ""
Write-Host "── AGENTE DE IA ──────────────────────────────────────" -ForegroundColor Yellow
Write-Host "  API key de Anthropic para el agente IA." -ForegroundColor Gray
$API_KEY = Read-Host "  API key (sk-ant-...) [opcional, se puede añadir después]"

Write-Host ""
Write-Host "── WHATSAPP (YCloud) ─────────────────────────────────" -ForegroundColor Yellow
Write-Host "  El cliente debe tener cuenta en ycloud.com con un número" -ForegroundColor Gray
Write-Host "  de WhatsApp Business registrado. Si no lo tiene aún, deja" -ForegroundColor Gray
Write-Host "  en blanco y añádelo después editando el .env del servidor." -ForegroundColor Gray
Write-Host ""
$YCLOUD_API_KEY       = Read-Host "  YCloud API key         [opcional]"
$YCLOUD_WH_SECRET     = Read-Host "  YCloud Webhook secret  [opcional]"
$YCLOUD_WA_NUMBER     = Read-Host "  Número WhatsApp Business (ej: +34600000000) [opcional]"

Write-Host ""
Write-Host "── VOZ (Twilio) ──────────────────────────────────────" -ForegroundColor Yellow
Write-Host "  Solo si el cliente contrata el canal de voz (llamadas)." -ForegroundColor Gray
Write-Host "  Requiere cuenta en twilio.com con un número de teléfono." -ForegroundColor Gray
Write-Host ""
$TWILIO_SID    = Read-Host "  Twilio Account SID    [opcional]"
$TWILIO_TOKEN  = Read-Host "  Twilio Auth Token     [opcional]"
$TWILIO_NUMBER = Read-Host "  Número Twilio (ej: +34900000000) [opcional]"

# ── Calcular puertos ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ Conectando al servidor para calcular puertos disponibles..." -ForegroundColor Cyan

$REGISTRY_JSON = ssh "${SERVER_USER}@${SERVER_IP}" "cat /opt/merakia-clients/registro.json 2>/dev/null || echo '{""clientes"":[]}" 2>/dev/null

try {
    $registry = $REGISTRY_JSON | ConvertFrom-Json
    $numClientes = $registry.clientes.Count
} catch {
    $numClientes = 0
}

$WEB_PORT = 3100 + ($numClientes * 100)
$API_PORT = $WEB_PORT + 1

Write-Host "  Puerto web asignado : $WEB_PORT" -ForegroundColor Gray
Write-Host "  Puerto API asignado : $API_PORT" -ForegroundColor Gray

# URL pública (para webhook de Twilio/YCloud)
if ($DOMINIO) {
    $PUBLIC_URL = "https://$DOMINIO"
} else {
    $PUBLIC_URL = "http://${SERVER_IP}:${API_PORT}"
}

# ── Resumen ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Resumen del despliegue:" -ForegroundColor Cyan
Write-Host "    Servidor   : ${SERVER_USER}@${SERVER_IP}" -ForegroundColor White
Write-Host "    Cliente    : $NOMBRE ($SLUG)" -ForegroundColor White
if ($DOMINIO) {
Write-Host "    Dominio    : $DOMINIO" -ForegroundColor White
} else {
Write-Host "    Acceso     : http://${SERVER_IP}:${WEB_PORT}" -ForegroundColor White
}
Write-Host "    API key IA : $(if ($API_KEY) { '✓' } else { '(añadir después)' })" -ForegroundColor White
Write-Host "    WhatsApp   : $(if ($YCLOUD_API_KEY) { "✓ $YCLOUD_WA_NUMBER" } else { '(añadir después)' })" -ForegroundColor White
Write-Host "    Voz        : $(if ($TWILIO_SID) { "✓ $TWILIO_NUMBER" } else { '(no contratado / añadir después)' })" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$confirm = Read-Host "¿Continuar? (s/n)"
if ($confirm -notin @('s','S','si','Si','SI','y','Y')) {
    Write-Host "Cancelado." -ForegroundColor Red
    exit 0
}

# ── Paso 1: preparar el servidor si es la primera vez ───────────────────────
Write-Host ""
Write-Host "▶ Paso 1/3: Preparando el servidor (primera vez tarda ~1 min)..." -ForegroundColor Cyan

$SETUP_SCRIPT = Get-Content "$PSScriptRoot\deploy\setup_servidor.sh" -Raw
echo $SETUP_SCRIPT | ssh "${SERVER_USER}@${SERVER_IP}" "sudo bash -s" 2>&1

# ── Paso 2: desplegar cliente ────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ Paso 2/3: Desplegando cliente (puede tardar 2-3 min)..." -ForegroundColor Cyan

$DEPLOY_SCRIPT = Get-Content "$PSScriptRoot\deploy\nuevo_cliente.sh" -Raw

$ENV_VARS = "CLIENTE_SLUG='$SLUG' CLIENTE_NOMBRE='$NOMBRE' WEB_PORT='$WEB_PORT' API_PORT='$API_PORT' PUBLIC_URL='$PUBLIC_URL'"
if ($DOMINIO)          { $ENV_VARS += " DOMINIO='$DOMINIO'" }
if ($API_KEY)          { $ENV_VARS += " ANTHROPIC_KEY='$API_KEY'" }
if ($YCLOUD_API_KEY)   { $ENV_VARS += " YCLOUD_API_KEY='$YCLOUD_API_KEY'" }
if ($YCLOUD_WH_SECRET) { $ENV_VARS += " YCLOUD_WEBHOOK_SECRET='$YCLOUD_WH_SECRET'" }
if ($YCLOUD_WA_NUMBER) { $ENV_VARS += " YCLOUD_WHATSAPP_NUMBER='$YCLOUD_WA_NUMBER'" }
if ($TWILIO_SID)       { $ENV_VARS += " TWILIO_ACCOUNT_SID='$TWILIO_SID'" }
if ($TWILIO_TOKEN)     { $ENV_VARS += " TWILIO_AUTH_TOKEN='$TWILIO_TOKEN'" }
if ($TWILIO_NUMBER)    { $ENV_VARS += " TWILIO_PHONE_NUMBER='$TWILIO_NUMBER'" }

echo $DEPLOY_SCRIPT | ssh "${SERVER_USER}@${SERVER_IP}" "sudo $ENV_VARS bash -s"

# ── Paso 3: verificar ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ Paso 3/3: Verificando..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

$STATUS = ssh "${SERVER_USER}@${SERVER_IP}" "docker ps --filter 'name=${SLUG}' --format 'table {{.Names}}\t{{.Status}}'" 2>/dev/null

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║        ✅ Cliente desplegado con éxito              ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Cliente   : $NOMBRE" -ForegroundColor White

if ($DOMINIO) {
Write-Host "  Panel     : https://$DOMINIO" -ForegroundColor White
} else {
Write-Host "  Panel     : http://${SERVER_IP}:${WEB_PORT}" -ForegroundColor White
}

Write-Host ""
Write-Host "  Canales configurados:" -ForegroundColor Cyan
if ($YCLOUD_API_KEY) {
Write-Host "  💬 WhatsApp : ✅ Conectado ($YCLOUD_WA_NUMBER)" -ForegroundColor Green
Write-Host "     Webhook YCloud → POST ${PUBLIC_URL}/api/webhooks/ycloud" -ForegroundColor Gray
} else {
Write-Host "  💬 WhatsApp : ⏳ Pendiente — añadir credenciales de YCloud al .env" -ForegroundColor Yellow
}
if ($TWILIO_SID) {
Write-Host "  📞 Voz      : ✅ Conectado ($TWILIO_NUMBER)" -ForegroundColor Green
Write-Host "     Webhook Twilio  → POST ${PUBLIC_URL}/api/voice/incoming" -ForegroundColor Gray
} else {
Write-Host "  📞 Voz      : ⏳ Pendiente — añadir credenciales de Twilio al .env" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Contenedores activos:" -ForegroundColor Gray
Write-Host $STATUS -ForegroundColor Gray
Write-Host ""
Write-Host "  Siguientes pasos:" -ForegroundColor Cyan
Write-Host "    1. Abre el panel y configura nombre, servicios y horarios en 'Agente'" -ForegroundColor White
Write-Host "    2. Sube el PDF del centro en 'Agente' → Base de conocimiento" -ForegroundColor White
if (-not $YCLOUD_API_KEY) {
Write-Host "    3. Cuando tengas las credenciales de YCloud, edita:" -ForegroundColor White
Write-Host "       /opt/merakia-clients/$SLUG/.env  y reinicia con:" -ForegroundColor Gray
Write-Host "       docker compose -f /opt/merakia-clients/$SLUG/docker-compose.prod.yml restart" -ForegroundColor Gray
}
if ($YCLOUD_API_KEY) {
Write-Host "    3. En YCloud configura el webhook apuntando a la URL de arriba" -ForegroundColor White
}
Write-Host ""

Read-Host "Pulsa Enter para cerrar"
