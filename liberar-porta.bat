@echo off
chcp 65001 >nul
echo ========================================
echo    LIBERAR PORTA 3001
echo ========================================
echo.

echo Procurando processos na porta 3001...
echo.

REM Usar PowerShell para uma solução mais robusta
powershell -Command "$processes = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; if ($processes) { foreach ($pid in $processes) { Write-Host 'Finalizando processo:' $pid; Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } } else { Write-Host 'Nenhum processo encontrado na porta 3001' }"

echo.
echo Aguardando 2 segundos...
timeout /t 2 /nobreak >nul

echo.
echo Verificando se a porta esta livre...
netstat -ano | findstr :3001 | findstr LISTENING >nul
if errorlevel 1 (
    echo ✅ Porta 3001 esta livre agora!
) else (
    echo ⚠️  Porta 3001 ainda esta em uso
    echo    Tente executar como Administrador
)

echo.
pause

