@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\gestion-camiones.exe" (
    echo No se encontro el ejecutable local de la app.
    echo Verifica que exista .venv\Scripts\gestion-camiones.exe
    pause
    exit /b 1
)

start "" ".venv\Scripts\gestion-camiones.exe"
