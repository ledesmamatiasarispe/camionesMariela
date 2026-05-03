@echo off
setlocal

cd /d "%~dp0"
set "ROOT=%CD%"
set "PYTHONPATH=%ROOT%\src"
set "VENV_PY=%ROOT%\.venv\Scripts\python.exe"

echo Iniciando Gestion Camiones en modo desarrollo...
echo Repo: %ROOT%

if not exist "%VENV_PY%" (
    echo.
    echo No existe .venv. Creando entorno virtual...
    call :create_venv
    if errorlevel 1 goto :error
)

echo.
echo Verificando dependencias...
"%VENV_PY%" -c "import PySide6, certifi, openpyxl, reportlab" >nul 2>nul
if errorlevel 1 (
    echo Instalando dependencias de desarrollo...
    "%VENV_PY%" -m pip install --upgrade pip
    if errorlevel 1 goto :error
    "%VENV_PY%" -m pip install -r "%ROOT%\requirements-dev.txt"
    if errorlevel 1 goto :error
    "%VENV_PY%" -m pip install -e "%ROOT%"
    if errorlevel 1 goto :error
)

echo.
echo Abriendo app desde src...
"%VENV_PY%" -m gestion_camiones.main
if errorlevel 1 goto :error
exit /b 0

:create_venv
where py >nul 2>nul
if not errorlevel 1 (
    py -3.11 -m venv "%ROOT%\.venv"
    exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    python -m venv "%ROOT%\.venv"
    exit /b 0
)

echo No se encontro Python para crear .venv.
echo Instalar Python 3.11 o superior y volver a ejecutar este launcher.
exit /b 1

:error
echo.
echo No se pudo abrir la app en modo desarrollo.
echo La ventana queda abierta para leer el error.
pause
exit /b 1
