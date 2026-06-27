#!/bin/bash
# ============================================================================
#  SETUP_SERVIDOR.SH
#  Ejecutar UNA SOLA VEZ en un VPS Ubuntu/Debian recién creado.
#  Instala Docker, Caddy (proxy con HTTPS automático) y prepara las carpetas.
#
#  Uso:
#    chmod +x setup_servidor.sh && sudo bash setup_servidor.sh
# ============================================================================
set -e

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  MerakIA — Preparación del servidor          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Docker ─────────────────────────────────────────────────────────────────
if command -v docker &>/dev/null; then
  echo "✓ Docker ya está instalado."
else
  echo "▶ Instalando Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
  echo "✓ Docker instalado."
fi

# ── Caddy (proxy inverso con HTTPS automático) ──────────────────────────────
if command -v caddy &>/dev/null; then
  echo "✓ Caddy ya está instalado."
else
  echo "▶ Instalando Caddy..."
  apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl 2>/dev/null
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    | tee /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq
  apt-get install -y caddy
  systemctl enable caddy
  echo "✓ Caddy instalado."
fi

# ── Carpeta de clientes ──────────────────────────────────────────────────────
mkdir -p /opt/merakia-clients
echo '{"clientes":[]}' > /opt/merakia-clients/registro.json 2>/dev/null || true
chmod 700 /opt/merakia-clients

# ── Caddyfile base ──────────────────────────────────────────────────────────
if [ ! -f /etc/caddy/Caddyfile.merakia ]; then
  cat > /etc/caddy/Caddyfile.merakia <<'EOF'
# Dominios de clientes MerakIA — generado automáticamente
# (este archivo se actualiza cada vez que añades un cliente con dominio)
EOF
  # Incluir nuestro archivo en el Caddyfile principal si no está ya
  if ! grep -q "Caddyfile.merakia" /etc/caddy/Caddyfile; then
    echo "" >> /etc/caddy/Caddyfile
    echo "import /etc/caddy/Caddyfile.merakia" >> /etc/caddy/Caddyfile
  fi
  systemctl reload caddy 2>/dev/null || true
fi

# ── Git (para clonar el código en cada cliente) ─────────────────────────────
if ! command -v git &>/dev/null; then
  apt-get install -y git
fi

echo ""
echo "✅ Servidor listo para recibir clientes MerakIA."
echo ""
echo "   Próximo paso: ejecuta 'desplegar_cliente.ps1' desde tu ordenador"
echo "   para añadir el primer cliente."
echo ""
