@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title Verificador e Instalador de Dependencias

echo ========================================
echo   VERIFICADOR E INSTALADOR DE DEPENDENCIAS
echo ========================================
echo.
echo Este script verifica e instala automaticamente
echo todas as dependencias necessarias para o projeto.
echo.
echo ========================================
echo.

REM ========================================
REM 1. VERIFICAR PYTHON
REM ========================================
echo [1/8] Verificando Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERRO: Python nao encontrado!
    echo.
    echo Por favor, instale o Python 3.8 ou superior:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Marque a opcao "Add Python to PATH" durante a instalacao!
    echo.
    pause
    exit /b 1
)

REM Verificar versao do Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python encontrado: !PYTHON_VERSION!
echo.

REM ========================================
REM 2. VERIFICAR PIP
REM ========================================
echo [2/8] Verificando pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERRO: pip nao encontrado!
    echo.
    echo Tentando instalar pip...
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo.
        echo ❌ Falha ao instalar pip!
        echo Por favor, reinstale o Python com pip incluido.
        echo.
        pause
        exit /b 1
    )
)
echo ✓ pip encontrado
echo.

REM ========================================
REM 3. VERIFICAR E INSTALAR DEPENDENCIAS PYTHON
REM ========================================
echo [3/8] Verificando dependencias Python...
echo.

REM Atualizar pip primeiro
echo Atualizando pip...
python -m pip install --upgrade pip --quiet
echo.

REM Verificar se requirements.txt existe
if not exist "requirements.txt" (
    echo ⚠️  AVISO: Arquivo requirements.txt nao encontrado!
    echo.
    echo Instalando dependencias manualmente...
    echo.
    
    REM Instalar dependencias principais
    echo Instalando dependencias Python...
    python -m pip install pandas playwright requests openpyxl rembg Pillow numpy onnxruntime --quiet --upgrade
    python -m pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client --quiet --upgrade
    python -m pip install flask flask-cors --quiet --upgrade
    
    if %errorlevel% neq 0 (
        echo.
        echo ❌ ERRO ao instalar algumas dependencias!
        echo    Tente instalar manualmente: pip install -r requirements.txt
        echo.
    ) else (
        echo.
        echo ✓ Dependencias Python instaladas
    )
) else (
    echo Instalando dependencias do requirements.txt...
    echo    Isso pode demorar alguns minutos...
    echo.
    
    REM Instalar todas as dependencias do requirements.txt
    python -m pip install -r requirements.txt --quiet --upgrade
    
    if %errorlevel% neq 0 (
        echo.
        echo ❌ ERRO ao instalar dependencias do requirements.txt!
        echo    Tente executar manualmente: pip install -r requirements.txt
        echo.
    ) else (
        echo.
        echo ✓ Dependencias Python instaladas do requirements.txt
    )
    
    REM Verificar dependencias criticas individualmente
    echo.
    echo Verificando dependencias criticas...
    echo.
    
    REM Verificar dependencias criticas individualmente
    python -c "import pandas" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   ❌ pandas nao esta instalado
        python -m pip install pandas --quiet --upgrade
    ) else (
        echo   ✓ pandas OK
    )
    
    python -c "import flask" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   ❌ flask nao esta instalado
        python -m pip install flask --quiet --upgrade
    ) else (
        echo   ✓ flask OK
    )
    
    python -c "import flask_cors" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   ❌ flask-cors nao esta instalado
        python -m pip install flask-cors --quiet --upgrade
    ) else (
        echo   ✓ flask-cors OK
    )
    
    python -c "import requests" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   ❌ requests nao esta instalado
        python -m pip install requests --quiet --upgrade
    ) else (
        echo   ✓ requests OK
    )
    
    python -c "import openpyxl" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   ❌ openpyxl nao esta instalado
        python -m pip install openpyxl --quiet --upgrade
    ) else (
        echo   ✓ openpyxl OK
    )
    
    python -c "from PIL import Image" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   ❌ Pillow nao esta instalado
        python -m pip install Pillow --quiet --upgrade
    ) else (
        echo   ✓ Pillow OK
    )
)

echo.
echo ✓ Dependencias Python verificadas/instaladas
echo.

REM ========================================
REM 4. INSTALAR NAVEGADORES DO PLAYWRIGHT
REM ========================================
echo [4/8] Verificando navegadores do Playwright...
python -c "import playwright" >nul 2>&1
if %errorlevel% equ 0 (
    echo Verificando se os navegadores estao instalados...
    python -m playwright install --help >nul 2>&1
    if %errorlevel% equ 0 (
        echo Instalando navegadores do Playwright (pode demorar alguns minutos)...
        python -m playwright install chromium
        if %errorlevel% neq 0 (
            echo ⚠️  Aviso: Falha ao instalar navegadores do Playwright
            echo    Voce pode instalar manualmente depois com: python -m playwright install
        ) else (
            echo ✓ Navegadores do Playwright instalados
        )
    )
)
echo.

REM ========================================
REM 5. VERIFICAR NODE.JS
REM ========================================
echo [5/8] Verificando Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  AVISO: Node.js nao encontrado!
    echo.
    echo O servidor WhatsApp nao funcionara sem Node.js.
    echo Se precisar usar o servidor WhatsApp, instale Node.js:
    echo https://nodejs.org/
    echo.
    echo Continuando sem Node.js...
    set NODEJS_INSTALLED=0
) else (
    for /f "tokens=1" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
    echo ✓ Node.js encontrado: !NODE_VERSION!
    set NODEJS_INSTALLED=1
)
echo.

REM ========================================
REM 6. VERIFICAR NPM
REM ========================================
if !NODEJS_INSTALLED! equ 1 (
    echo [6/8] Verificando npm...
    where npm >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⚠️  AVISO: npm nao encontrado!
        echo    Isso pode causar problemas com o servidor WhatsApp.
    ) else (
        for /f "tokens=1" %%i in ('npm --version 2^>^&1') do set NPM_VERSION=%%i
        echo ✓ npm encontrado: !NPM_VERSION!
    )
    echo.
) else (
    echo [6/8] Pulando verificacao npm (Node.js nao instalado)
    echo.
)

REM ========================================
REM 7. VERIFICAR E INSTALAR DEPENDENCIAS NODE.JS
REM ========================================
if !NODEJS_INSTALLED! equ 1 (
    echo [7/8] Verificando dependencias Node.js...
    echo.
    
    if not exist "package.json" (
        echo ⚠️  AVISO: Arquivo package.json nao encontrado!
        echo    Dependencias Node.js nao serao instaladas.
    ) else (
        if not exist "node_modules" (
            echo 📦 Instalando dependencias Node.js...
            echo    Isso pode demorar alguns minutos...
            echo.
            npm install
            if %errorlevel% neq 0 (
                echo.
                echo ❌ ERRO ao instalar dependencias Node.js!
                echo    Tente executar manualmente: npm install
                echo.
            ) else (
                echo.
                echo ✓ Dependencias Node.js instaladas
            )
        ) else (
            echo Verificando dependencias Node.js...
            REM Verificar se as dependencias principais estao instaladas
            if not exist "node_modules\whatsapp-web.js" (
                echo   → whatsapp-web.js nao encontrado, instalando...
                npm install whatsapp-web.js
            )
            if not exist "node_modules\qrcode-terminal" (
                echo   → qrcode-terminal nao encontrado, instalando...
                npm install qrcode-terminal
            )
            if not exist "node_modules\express" (
                echo   → express nao encontrado, instalando...
                npm install express
            )
            echo ✓ Dependencias Node.js verificadas
        )
    )
    echo.
) else (
    echo [7/8] Pulando instalacao de dependencias Node.js (Node.js nao instalado)
    echo.
)

REM ========================================
REM 8. VERIFICAR ARQUIVOS E PASTAS NECESSARIAS
REM ========================================
echo [8/8] Verificando arquivos e pastas necessarias...
echo.

REM Verificar arquivos Python principais
set MISSING_FILES=0

if not exist "main.py" (
    echo ❌ Arquivo main.py nao encontrado!
    set MISSING_FILES=1
) else (
    echo ✓ main.py encontrado
)

if not exist "server.py" (
    echo ❌ Arquivo server.py nao encontrado!
    set MISSING_FILES=1
) else (
    echo ✓ server.py encontrado
)

if not exist "template_editor.html" (
    echo ⚠️  Arquivo template_editor.html nao encontrado!
    echo    A interface web pode nao funcionar corretamente.
) else (
    echo ✓ template_editor.html encontrado
)

REM Verificar arquivos Node.js (se Node.js estiver instalado)
if !NODEJS_INSTALLED! equ 1 (
    if not exist "whatsapp-sender.js" (
        echo ⚠️  Arquivo whatsapp-sender.js nao encontrado!
        echo    O servidor WhatsApp nao funcionara.
    ) else (
        echo ✓ whatsapp-sender.js encontrado
    )
)

REM Verificar arquivos Gmail (opcionais)
if not exist "gmail_service.py" (
    echo ⚠️  Arquivo gmail_service.py nao encontrado (opcional)
) else (
    echo ✓ gmail_service.py encontrado
)

if not exist "gmail-monitor-api.py" (
    echo ⚠️  Arquivo gmail-monitor-api.py nao encontrado (opcional)
) else (
    echo ✓ gmail-monitor-api.py encontrado
)

REM Verificar pastas necessarias
if not exist "Imagens" (
    echo ⚠️  Pasta Imagens nao encontrada (sera criada se necessario)
    mkdir "Imagens" >nul 2>&1
) else (
    echo ✓ Pasta Imagens encontrada
)

if not exist "banners" (
    echo ⚠️  Pasta banners nao encontrada (sera criada se necessario)
    mkdir "banners" >nul 2>&1
) else (
    echo ✓ Pasta banners encontrada
)

if not exist "uploads" (
    echo ⚠️  Pasta uploads nao encontrada (sera criada se necessario)
    mkdir "uploads" >nul 2>&1
) else (
    echo ✓ Pasta uploads encontrada
)

if not exist "cache_imagens_processadas" (
    echo ⚠️  Pasta cache_imagens_processadas nao encontrada (sera criada se necessario)
    mkdir "cache_imagens_processadas" >nul 2>&1
) else (
    echo ✓ Pasta cache_imagens_processadas encontrada
)

echo.

REM ========================================
REM RESUMO FINAL
REM ========================================
echo ========================================
echo   RESUMO DA VERIFICACAO
echo ========================================
echo.

if %MISSING_FILES% equ 1 (
    echo ❌ ALGUNS ARQUIVOS ESSENCIAIS ESTAO FALTANDO!
    echo    Verifique os erros acima.
    echo.
) else (
    echo ✓ Todos os arquivos essenciais encontrados
    echo.
)

echo ✓ Python: !PYTHON_VERSION!
if !NODEJS_INSTALLED! equ 1 (
    echo ✓ Node.js: !NODE_VERSION!
    echo ✓ npm: !NPM_VERSION!
) else (
    echo ⚠️  Node.js: NAO INSTALADO (opcional para servidor WhatsApp)
)

echo.
echo ========================================
echo   VERIFICACAO CONCLUIDA!
echo ========================================
echo.

REM Verificar se precisa baixar modelo rembg
echo Verificando modelo rembg...
python -c "from rembg import remove" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Biblioteca rembg instalada
    echo   (O modelo sera baixado automaticamente na primeira execucao)
) else (
    echo ⚠️  Biblioteca rembg nao instalada
    echo   Execute: python baixar-modelo-rembg.py
)

echo.
echo ========================================
echo   PROXIMOS PASSOS
echo ========================================
echo.
echo 1. Se o Node.js nao estiver instalado e voce precisar do servidor WhatsApp:
echo    → Instale Node.js de: https://nodejs.org/
echo    → Execute este script novamente
echo.
echo 2. Para usar o Gmail Monitor:
echo    → Configure o arquivo credentials.json (veja README_GMAIL_MONITOR.md)
echo.
echo 3. Para iniciar o projeto:
echo    → Execute: iniciar-servidor.bat
echo.
echo 4. Para baixar o modelo rembg (se ainda nao foi feito):
echo    → Execute: baixar-modelo-rembg.bat
echo.
echo ========================================
echo.

pause

