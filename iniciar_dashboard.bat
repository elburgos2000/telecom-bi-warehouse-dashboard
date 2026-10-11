@echo off
title Servidor Enterprise Telecom BI Analytics
echo ========================================================
echo   INICIANDO ENTERPRISE TELECOM BI ANALYTICS DASHBOARD
echo   Autor: Brayan Burgos Palomino
echo ========================================================
echo.
cd /d "%~dp0"
start http://localhost:8085
python server.py
pause
