@echo off
chcp 65001 >nul
echo ========================================
echo    TESTE GUIADO - ENVIO WHATSAPP
echo ========================================
echo.

REM Verificar se Python está instalado
where python >nul 2>&1
if errorlevel 1 (
    set "PYTHON_CMD=py"
    where %PYTHON_CMD% >nul 2>&1
    if errorlevel 1 (
        echo ❌ Erro: Python nao encontrado!
        echo.
        echo Por favor, instale o Python de https://www.python.org/
        echo.
        pause
        exit /b 1
    )
) else (
    set "PYTHON_CMD=python"
)

echo ✓ Python encontrado!
echo.
echo ========================================
echo    Iniciando Teste Guiado
echo ========================================
echo.
echo IMPORTANTE: Certifique-se de que o servidor WhatsApp
echo            esta rodando antes de executar este teste!
echo.
echo Se o servidor nao estiver rodando:
echo   1. Abra um novo terminal
echo   2. Execute: start-whatsapp-server.bat
echo   3. Aguarde aparecer "✅ Cliente WhatsApp pronto!"
echo   4. Execute este teste novamente
echo.
echo ========================================
echo.

pause

%PYTHON_CMD% test_whatsapp.py

pause

