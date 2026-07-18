# Sube el sensor de order flow a /opt/merakia/orderflow-sensor en el VPS y lo
# deja corriendo como servicio systemd (snapshots 1s + trades, 24/7).
# Uso:  .\deploy_to_vps.ps1 -ServerIp 93.93.112.48
# Requiere: misma clave SSH que polymarket-bot (ver polymarket-bot/deploy/README_DEPLOY.md).
param([Parameter(Mandatory = $true)][string]$ServerIp)

$key = "$env:USERPROFILE\.ssh\ionos_merakia"
$src = Split-Path -Parent $PSScriptRoot   # ...\orderflow-sensor
$dst = "root@${ServerIp}:/opt/merakia/orderflow-sensor"

Write-Host "== 1/3 Creando carpeta remota =="
ssh -i $key -o StrictHostKeyChecking=accept-new root@$ServerIp "mkdir -p /opt/merakia/orderflow-sensor"

Write-Host "== 2/3 Copiando codigo (sin BD: el collector la crea en el VPS) =="
scp -i $key "$src\collector.py" "$src\analyze.py" "$src\README.md" $dst/
scp -i $key -r "$src\deploy" $dst/

Write-Host "== 3/3 Aprovisionando y arrancando el servicio =="
ssh -i $key root@$ServerIp "bash /opt/merakia/orderflow-sensor/deploy/setup_vps.sh"

Write-Host ""
Write-Host "LISTO. Comandos utiles:"
Write-Host "  estado:   ssh -i `"$key`" root@$ServerIp 'systemctl status orderflow-collector'"
Write-Host "  log vivo: ssh -i `"$key`" root@$ServerIp 'journalctl -u orderflow-collector -f'"
Write-Host "  traer BD: scp -i `"$key`" root@${ServerIp}:/opt/merakia/orderflow-sensor/orderflow.db orderflow-sensor\orderflow.db"
