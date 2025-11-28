@echo off
echo ========================================
echo   GMAIL MONITOR - Iniciando Servidor
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python 3.7 ou superior.
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Verificar se requirements estão instalados
echo Verificando dependencias...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Dependencias nao encontradas. Instalando...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias!
        pause
        exit /b 1
    )
)

echo [OK] Dependencias verificadas
echo.

REM Verificar se credentials.json existe
if not exist "credentials.json" (
    echo [AVISO] Arquivo credentials.json nao encontrado!
    echo.
    echo Por favor:
    echo 1. Acesse o Google Cloud Console
    echo 2. Crie um projeto e ative a Gmail API
    echo 3. Crie credenciais OAuth 2.0
    echo 4. Baixe o arquivo JSON e salve como credentials.json
    echo.
    echo Veja README_GMAIL_MONITOR.md para mais detalhes.
    echo.
    pause
    exit /b 1
)

echo [OK] Arquivo credentials.json encontrado
echo.

REM Verificar se servidor WhatsApp está rodando
echo Verificando servidor WhatsApp (porta 3001)...
curl -s http://localhost:3001/health >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Servidor WhatsApp nao esta rodando na porta 3001!
    echo.
    echo Por favor, inicie o servidor WhatsApp primeiro:
    echo   npm start
    echo   ou
    echo   node whatsapp-sender.js
    echo.
    echo Pressione qualquer tecla para continuar mesmo assim...
    pause >nul
)

echo.
echo ========================================
echo   Iniciando servidor Gmail Monitor...
echo   Porta: 5000
echo ========================================
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

python gmail-monitor-api.py

pause





