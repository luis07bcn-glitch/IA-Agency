# Sube el collector de funding a /opt/merakia/funding-bot en el VPS y lo deja
# corriendo como servicio systemd (snapshots cada 5 min, 24/7).
# Uso:  .\deploy_to_vps.ps1 -ServerIp X.X.X.X
# Requiere: misma clave SSH que polymarket-bot (ver polymarket-bot/deploy/README_DEPLOY.md).
param([Parameter(Mandatory = $true)][string]$ServerIp)

$key = "$env:USERPROFILE\.ssh\ionos_merakia"
$src = Split-Path -Parent $PSScriptRoot   # ...\funding-bot
$dst = "root@${ServerIp}:/opt/merakia/funding-bot"

Write-Host "== 1/3 Creando carpeta remota =="
ssh -i $key -o StrictHostKeyChecking=accept-new root@$ServerIp "mkdir -p /opt/merakia/funding-bot"

Write-Host "== 2/3 Copiando codigo (sin BD: el backfill la genera en el VPS) =="
scp -i $key "$src\collector.py" "$src\backtest.py" "$src\README.md" $dst/
scp -i $key -r "$src\deploy" $dst/

Write-Host "== 3/3 Aprovisionando y arrancando el servicio =="
ssh -i $key root@$ServerIp "bash /opt/merakia/funding-bot/deploy/setup_vps.sh"

Write-Host ""
Write-Host "LISTO. Comandos utiles:"
Write-Host "  estado:    ssh -i `"$key`" root@$ServerIp 'systemctl status funding-collector'"
Write-Host "  log vivo:  ssh -i `"$key`" root@$ServerIp 'journalctl -u funding-collector -f'"
Write-Host "  backtest:  ssh -i `"$key`" root@$ServerIp '/opt/merakia/venv/bin/python /opt/merakia/funding-bot/backtest.py'"
