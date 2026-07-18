#!/usr/bin/env bash
# Aprovisiona el sensor de order flow en el VPS (reutiliza usuario/venv de
# polymarket-bot). Ejecutar como root DESPUES de copiar /opt/merakia/orderflow-sensor.
set -euo pipefail

echo "== usuario y permisos (reutiliza merakia si ya existe) =="
id -u merakia &>/dev/null || useradd -m -s /bin/bash merakia
chown -R merakia:merakia /opt/merakia/orderflow-sensor

echo "== venv + websockets (unica dependencia del collector) =="
[ -d /opt/merakia/venv ] || sudo -u merakia python3 -m venv /opt/merakia/venv
sudo -u merakia /opt/merakia/venv/bin/pip install --quiet "websockets>=12"

echo "== servicio systemd =="
cp /opt/merakia/orderflow-sensor/deploy/orderflow-collector.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now orderflow-collector

sleep 3
echo "== estado =="
systemctl is-active orderflow-collector
echo "OK — sensor de order flow corriendo 24/7. BD en /opt/merakia/orderflow-sensor/orderflow.db"
echo "El analisis se hace en local: scp de la BD (ver README.md)."
