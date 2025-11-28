@echo off
chcp 65001 >nul
echo ========================================
echo    TESTE - Node.js e Dependencias
echo ========================================
echo.

echo [1] Verificando Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js nao encontrado!
    pause
    exit /b 1
)
echo ✓ Node.js encontrado
node --version
echo.

echo [2] Verificando npm...
where npm >nul 2>&1
if errorlevel 1 (
    echo ❌ npm nao encontrado!
    pause
    exit /b 1
)
echo ✓ npm encontrado
npm --version
echo.

echo [3] Verificando arquivo whatsapp-sender.js...
if not exist "whatsapp-sender.js" (
    echo ❌ Arquivo nao encontrado!
    pause
    exit /b 1
)
echo ✓ Arquivo encontrado
echo.

echo [4] Verificando node_modules...
if not exist "node_modules" (
    echo ⚠️  node_modules nao existe
    echo    Execute: npm install
) else (
    echo ✓ node_modules existe
)
echo.

echo [5] Verificando dependencias...
if exist "node_modules\whatsapp-web.js" (
    echo ✓ whatsapp-web.js instalado
) else (
    echo ❌ whatsapp-web.js nao instalado
    echo    Execute: npm install
)
if exist "node_modules\express" (
    echo ✓ express instalado
) else (
    echo ❌ express nao instalado
    echo    Execute: npm install
)
if exist "node_modules\qrcode-terminal" (
    echo ✓ qrcode-terminal instalado
) else (
    echo ❌ qrcode-terminal nao instalado
    echo    Execute: npm install
)
echo.

echo [6] Testando sintaxe do JavaScript...
node -c whatsapp-sender.js
if errorlevel 1 (
    echo ❌ Erro de sintaxe no arquivo!
    pause
    exit /b 1
)
echo ✓ Sintaxe OK
echo.

echo ========================================
echo    TESTE CONCLUIDO
echo ========================================
echo.
pause

