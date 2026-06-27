@echo off
REM ============================================================
REM   MerakIA - Lanzador en un clic
REM   Doble clic en este archivo para abrir la plataforma.
REM ============================================================
cd /d "%~dp0"
echo.
echo   Iniciando MerakIA...
echo   El navegador se abrira automaticamente en unos segundos.
echo.
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0iniciar_merakia.ps1"
