@echo off
echo ========================================
echo   Verificando Servidor Gmail Monitor
echo ========================================
echo.

REM Verificar se a porta 5001 está em uso
echo Verificando porta 5001...
netstat -ano | findstr ":5001" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Porta 5001 esta em uso (servidor provavelmente rodando)
    echo.
    echo Testando conexao...
    curl -s http://localhost:5001/health >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Servidor esta respondendo!
    ) else (
        echo [AVISO] Porta em uso mas servidor nao esta respondendo
    )
) else (
    echo [ERRO] Porta 5001 nao esta em uso
    echo.
    echo O servidor Gmail Monitor nao esta rodando!
    echo.
    echo Para iniciar:
    echo   1. Execute: python gmail-monitor-api.py
    echo   2. Ou use: iniciar-servidor.bat
    echo.
)

echo.
echo ========================================
pause

