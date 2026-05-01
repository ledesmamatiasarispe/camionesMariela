@echo off
setlocal

cd /d "%~dp0"

if exist "dist\GestionCamiones\GestionCamiones.exe" (
    start "" "dist\GestionCamiones\GestionCamiones.exe"
    exit /b 0
)

if exist ".venv\Scripts\gestion-camiones.exe" (
    start "" ".venv\Scripts\gestion-camiones.exe"
    exit /b 0
)

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" -m gestion_camiones.main
    exit /b 0
)

if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" -m gestion_camiones.main
    exit /b 0
)

echo No se encontro un ejecutable para abrir la app.
echo Opciones esperadas:
echo - dist\GestionCamiones\GestionCamiones.exe
echo - .venv\Scripts\gestion-camiones.exe
echo - .venv\Scripts\pythonw.exe
pause
exit /b 1
