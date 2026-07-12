#!/usr/bin/env bash
# Aprovisiona el collector de funding en el VPS (reutiliza usuario/venv de
# polymarket-bot, ya creados por polymarket-bot/deploy/setup_vps.sh).
# Ejecutar como root DESPUES de haber copiado /opt/merakia/funding-bot.
set -euo pipefail

echo "== usuario y permisos (reutiliza merakia si ya existe) =="
id -u merakia &>/dev/null || useradd -m -s /bin/bash merakia
chown -R merakia:merakia /opt/merakia/funding-bot

echo "== venv (reutiliza /opt/merakia/venv si ya existe; collector.py es stdlib pura) =="
[ -d /opt/merakia/venv ] || sudo -u merakia python3 -m venv /opt/merakia/venv

echo "== backfill inicial del historico de funding =="
sudo -u merakia /opt/merakia/venv/bin/python /opt/merakia/funding-bot/collector.py --backfill

echo "== servicio systemd =="
cp /opt/merakia/funding-bot/deploy/funding-collector.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now funding-collector

sleep 3
echo "== estado =="
systemctl is-active funding-collector
echo "OK — collector de funding corriendo (snapshots cada 5 min). BD en /opt/merakia/funding-bot/funding.db"
