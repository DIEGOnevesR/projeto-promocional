@echo off
chcp 65001 >nul
echo ========================================
echo    LIBERAR PORTA 3001
echo ========================================
echo.

echo Verificando processos usando a porta 3001...
echo.

REM Usar PowerShell para encontrar e finalizar processos
powershell -NoProfile -Command "^
$port = 3001; ^
$connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; ^
if ($connections) { ^
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique; ^
    Write-Host \"Encontrado(s) $($pids.Count) processo(s) usando a porta $port\"; ^
    Write-Host \"\"; ^
    foreach ($pid in $pids) { ^
        try { ^
            $process = Get-Process -Id $pid -ErrorAction Stop; ^
            Write-Host \"Finalizando processo: $pid ($($process.ProcessName))\"; ^
            Stop-Process -Id $pid -Force -ErrorAction Stop; ^
            Write-Host \"✅ Processo $pid finalizado com sucesso!\"; ^
        } catch { ^
            Write-Host \"⚠️  Erro ao finalizar processo $pid: $_\"; ^
        } ^
        Write-Host \"\"; ^
    } ^
    Write-Host \"Aguardando 2 segundos...\"; ^
    Start-Sleep -Seconds 2; ^
    $stillInUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; ^
    if ($stillInUse) { ^
        Write-Host \"⚠️  Porta ainda esta em uso. Tente executar como Administrador.\"; ^
    } else { ^
        Write-Host \"✅ Porta $port liberada com sucesso!\"; ^
    } ^
} else { ^
    Write-Host \"✅ Nenhum processo encontrado. Porta $port esta livre!\"; ^
}
"

echo.
pause

