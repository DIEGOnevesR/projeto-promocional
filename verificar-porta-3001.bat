@echo off
chcp 65001 >nul
echo ========================================
echo    VERIFICAR PORTA 3001
echo ========================================
echo.

echo Verificando processos usando a porta 3001...
echo.

netstat -aon | findstr :3001 | findstr LISTENING >nul
if errorlevel 1 (
    echo ✅ Porta 3001 esta livre!
    echo    Nenhum processo encontrado usando esta porta.
) else (
    echo ⚠️  Porta 3001 esta em uso!
    echo.
    echo Processos usando a porta 3001:
    echo.
    netstat -aon | findstr :3001 | findstr LISTENING
    echo.
    echo Para liberar a porta, execute: liberar-porta-3001.bat
)

echo.
pause

