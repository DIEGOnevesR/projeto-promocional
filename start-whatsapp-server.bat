@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title Servidor WhatsApp

echo ========================================
echo    Servidor WhatsApp - Iniciando
echo ========================================
echo.

REM Verificar Node.js
echo [1/4] Verificando Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERRO: Node.js nao encontrado!
    echo.
    echo Instale o Node.js de: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
echo ✓ Node.js encontrado
node --version
echo.

REM Verificar dependencias
echo [2/4] Verificando dependencias...
if not exist "node_modules" (
    echo 📦 Instalando dependencias...
    npm install
    if errorlevel 1 (
        echo.
        echo ❌ ERRO ao instalar dependencias!
        echo.
        pause
        exit /b 1
    )
)
echo ✓ Dependencias OK
echo.

REM Verificar arquivo
echo [3/4] Verificando arquivos...
if not exist "whatsapp-sender.js" (
    echo.
    echo ❌ ERRO: whatsapp-sender.js nao encontrado!
    echo.
    pause
    exit /b 1
)
echo ✓ Arquivos OK
echo.

REM Verificar porta
echo [4/4] Verificando porta 3001...
netstat -ano | findstr :3001 | findstr LISTENING >nul
if not errorlevel 1 (
    echo ⚠️  Porta em uso! Tentando liberar...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)
echo ✓ Porta OK
echo.

echo ========================================
echo    Iniciando Servidor...
echo ========================================
echo.
echo ⚠️  IMPORTANTE: Escaneie o QR Code
echo.
echo 💡 Para parar: Pressione Ctrl+C
echo.
echo ========================================
echo.

REM Executar Node.js
node whatsapp-sender.js

REM Se chegou aqui, o servidor foi fechado
echo.
echo ========================================
echo    Servidor Finalizado
echo ========================================
echo.
pause
