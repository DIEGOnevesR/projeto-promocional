@echo off
chcp 65001 >nul 2>&1
cls
echo ========================================
echo    Iniciando Servidores
echo ========================================
echo.
echo Aguarde enquanto os servidores iniciam...
echo.

REM Verificar se Python esta instalado
echo [1/3] Verificando Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo.
    echo Instale o Python de: https://www.python.org/
    echo.
    pause
    exit /b 1
)
echo OK: Python encontrado
echo.

REM Verificar se Node.js esta instalado
echo [2/3] Verificando Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo AVISO: Node.js nao encontrado!
    echo.
    echo O servidor WhatsApp nao sera iniciado.
    echo Instale o Node.js de: https://nodejs.org/ se precisar usar o Mensager.
    echo.
    timeout /t 3 /nobreak >nul
) else (
    echo OK: Node.js encontrado
)
echo.

REM Iniciar o servidor Flask em uma nova janela
echo [3/3] Iniciando Servidor Flask...
REM Verificar se server.py existe
if not exist "%~dp0server.py" (
    echo ERRO: Arquivo server.py nao encontrado!
    echo.
    echo Verifique se o arquivo server.py existe na pasta do projeto.
    echo.
    pause
    exit /b 1
)

REM Verificar dependencias Python antes de iniciar
echo Verificando dependencias Python...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Flask nao esta instalado!
    echo.
    echo Instale com: pip install flask flask-cors
    echo.
    pause
    exit /b 1
)
python -c "import flask_cors" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Flask-CORS nao esta instalado!
    echo.
    echo Instale com: pip install flask-cors
    echo.
    pause
    exit /b 1
)
echo OK: Dependencias Python verificadas
echo.

REM Verificar dependencias Gmail Monitor
echo Verificando dependencias Gmail Monitor...
python -c "import google.auth" >nul 2>&1
if %errorlevel% neq 0 (
    echo AVISO: Dependencias Gmail nao encontradas!
    echo.
    echo Instalando dependencias Gmail...
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERRO: Falha ao instalar dependencias Gmail!
        echo.
        echo Instale manualmente com: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
        echo.
    ) else (
        echo OK: Dependencias Gmail instaladas
    )
) else (
    echo OK: Dependencias Gmail verificadas
)
echo.

REM Tentar iniciar o servidor e capturar erros
cd /d "%~dp0"
start "Servidor Flask - Gerador de Banners" cmd /k "cd /d %~dp0 && python server.py && pause"

REM Iniciar o servidor WhatsApp em uma nova janela (se Node.js estiver disponivel)
where node >nul 2>&1
if %errorlevel% equ 0 (
    echo Iniciando Servidor WhatsApp...
    start "" "%~dp0start-whatsapp-server.bat"
)

REM Iniciar o servidor Gmail Monitor em uma nova janela (se gmail-monitor-api.py existir)
if exist "%~dp0gmail-monitor-api.py" (
    echo Iniciando Servidor Gmail Monitor...
    start "Servidor Gmail Monitor" cmd /k "cd /d %~dp0 && python gmail-monitor-api.py && pause"
)

echo.
echo Servidores iniciando em novas janelas...
echo Aguardando servidores iniciarem...

REM Aguardar 5 segundos para os servidores iniciarem
timeout /t 5 /nobreak >nul

echo.
echo Abrindo template editor no navegador...
echo.

REM Abrir o template_editor.html no navegador padrao
start "" "%~dp0template_editor.html"

echo ========================================
echo    Configuracao concluida!
echo ========================================
echo.
echo OK: Servidor Flask iniciado em nova janela
if exist "%~dp0whatsapp-sender.js" (
    echo OK: Servidor WhatsApp iniciado em nova janela
)
if exist "%~dp0gmail-monitor-api.py" (
    echo OK: Servidor Gmail Monitor iniciado em nova janela
)
echo OK: Template Editor aberto no navegador
echo.
echo Para parar os servidores, feche as janelas dos servidores
echo ou pressione Ctrl+C nas janelas dos servidores
echo.
echo IMPORTANTE: Se o servidor WhatsApp pedir QR Code,
echo            escaneie-o na janela do servidor WhatsApp
echo.
echo IMPORTANTE: Para usar o Gmail Monitor, configure o arquivo
echo            credentials.json (veja README_GMAIL_MONITOR.md)
echo.
pause
