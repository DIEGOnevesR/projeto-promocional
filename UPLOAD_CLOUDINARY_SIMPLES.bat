@echo off
chcp 65001 >nul
cls
echo ========================================
echo   UPLOAD DE ASSETS PARA CLOUDINARY
echo ========================================
echo.

REM Mudar para o diretório do script
cd /d "%~dp0"

REM Tentar encontrar o diretório do projeto
if exist "upload_all_cloudinary.py" (
    echo Diretório encontrado: %CD%
) else if exist "C:\Users\diegoribeiro-itr\.cursor\worktrees\Projeto_Promocional\acr\upload_all_cloudinary.py" (
    cd "C:\Users\diegoribeiro-itr\.cursor\worktrees\Projeto_Promocional\acr"
    echo Diretório encontrado: %CD%
) else (
    echo.
    echo ERRO: Arquivo upload_all_cloudinary.py não encontrado!
    echo.
    echo Por favor, execute este arquivo .bat no mesmo diretório onde está
    echo o arquivo upload_all_cloudinary.py
    echo.
    pause
    exit /b 1
)

echo.
echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python não encontrado!
    echo Por favor, instale Python ou adicione ao PATH
    pause
    exit /b 1
)

echo Python OK!
echo.
echo Instalando cloudinary se necessário...
python -m pip install cloudinary --quiet --disable-pip-version-check
echo.

echo ========================================
echo Iniciando upload...
echo ========================================
echo.

python upload_all_cloudinary.py

echo.
echo ========================================
echo Processo concluído!
echo ========================================
echo.
pause


