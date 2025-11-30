@echo off
chcp 65001 >nul
cls
title Upload Cloudinary
echo ========================================
echo   UPLOAD DE ASSETS PARA CLOUDINARY
echo ========================================
echo.

cd /d "%~dp0"

if exist "upload_com_log.py" (
    echo Executando upload_com_log.py...
    python upload_com_log.py
    echo.
    echo Log salvo em: upload_log.txt
    type upload_log.txt
) else if exist "C:\Users\diegoribeiro-itr\.cursor\worktrees\Projeto_Promocional\acr\upload_com_log.py" (
    cd "C:\Users\diegoribeiro-itr\.cursor\worktrees\Projeto_Promocional\acr"
    echo Executando upload_com_log.py...
    python upload_com_log.py
    echo.
    echo Log salvo em: upload_log.txt
    type upload_log.txt
) else (
    echo ERRO: upload_com_log.py nao encontrado!
    echo.
    echo Copie este arquivo .bat para o mesmo diretorio do upload_com_log.py
    pause
    exit /b 1
)

