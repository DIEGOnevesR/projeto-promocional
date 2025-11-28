@echo off
chcp 65001 >nul
echo ========================================
echo    MENU DE INSTRUCOES - WHATSAPP
echo ========================================
echo.
echo Selecione qual arquivo deseja abrir:
echo.
echo 1. INICIO_RAPIDO.txt - Guia rapido para comecar
echo 2. TESTE_RAPIDO.txt - Guia de teste rapido
echo 3. GUIA_TESTE_WHATSAPP.txt - Guia completo de teste
echo 4. README_WHATSAPP.txt - Documentacao completa
echo 5. Abrir todos os arquivos
echo 6. Sair
echo.
set /p opcao="Digite o numero da opcao: "

if "%opcao%"=="1" (
    echo.
    echo Abrindo INICIO_RAPIDO.txt...
    notepad INICIO_RAPIDO.txt
    goto :fim
)

if "%opcao%"=="2" (
    echo.
    echo Abrindo TESTE_RAPIDO.txt...
    notepad TESTE_RAPIDO.txt
    goto :fim
)

if "%opcao%"=="3" (
    echo.
    echo Abrindo GUIA_TESTE_WHATSAPP.txt...
    notepad GUIA_TESTE_WHATSAPP.txt
    goto :fim
)

if "%opcao%"=="4" (
    echo.
    echo Abrindo README_WHATSAPP.txt...
    notepad README_WHATSAPP.txt
    goto :fim
)

if "%opcao%"=="5" (
    echo.
    echo Abrindo todos os arquivos...
    start notepad INICIO_RAPIDO.txt
    timeout /t 1 /nobreak >nul
    start notepad TESTE_RAPIDO.txt
    timeout /t 1 /nobreak >nul
    start notepad GUIA_TESTE_WHATSAPP.txt
    timeout /t 1 /nobreak >nul
    start notepad README_WHATSAPP.txt
    goto :fim
)

if "%opcao%"=="6" (
    echo.
    echo Saindo...
    goto :fim
)

echo.
echo Opcao invalida!
pause
goto :fim

:fim
echo.
echo ========================================
echo.

