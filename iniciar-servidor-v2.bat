@echo off
chcp 65001 >nul 2>&1
cls
echo ========================================
echo    Iniciando Servidores
echo ========================================
echo.

REM Verificar Python
echo [1/3] Verificando Python...
where python >nul 2>&1
if not %errorlevel%==0 (
    echo ERRO: Python nao encontrado!
    echo Instale o Python de: https://www.python.org/
    pause
    exit /b 1
)
echo OK: Python encontrado
echo.

REM Verificar Node.js
echo [2/3] Verificando Node.js...
where node >nul 2>&1
if not %errorlevel%==0 (
    echo AVISO: Node.js nao encontrado - WhatsApp desabilitado
) else (
    echo OK: Node.js encontrado
)
echo.

REM Verificar server.py
echo [3/3] Verificando server.py...
if not exist "%~dp0server.py" (
    echo ERRO: Arquivo server.py nao encontrado!
    pause
    exit /b 1
)
echo OK: server.py encontrado
echo.

REM Verificar Flask
echo Verificando Flask...
python -c "import flask" >nul 2>&1
if not %errorlevel%==0 (
    echo ERRO: Flask nao instalado!
    echo Execute: pip install flask flask-cors
    pause
    exit /b 1
)
echo OK: Flask encontrado
echo.

REM Iniciar servidor Flask
echo Iniciando servidor Flask...
cd /d "%~dp0"
start "Servidor Flask" cmd /k "cd /d %~dp0 && python server.py && pause"

REM Iniciar WhatsApp se disponivel
where node >nul 2>&1
if %errorlevel%==0 (
    if exist "%~dp0start-whatsapp-server.bat" (
        echo Iniciando servidor WhatsApp...
        start "" "%~dp0start-whatsapp-server.bat"
    )
)

echo.
echo Aguardando servidores iniciarem...
timeout /t 5 /nobreak >nul

echo.
echo Abrindo template editor...
start "" "%~dp0template_editor.html"

echo.
echo ========================================
echo    Pronto!
echo ========================================
echo.
pause









