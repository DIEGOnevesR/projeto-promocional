@echo off
chcp 65001 >nul
cls
title Upload Cache Cloudinary
echo ========================================
echo   UPLOAD DE CACHE DE IMAGENS PROCESSADAS
echo ========================================
echo.

cd "C:\Users\diegoribeiro-itr\Documents\Projeto Promocional"

if exist "upload_cache_376.py" (
    echo Executando upload de 376 arquivos de cache...
    python upload_cache_376.py
) else (
    echo ERRO: upload_cache_376.py nao encontrado!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Processo concluido!
echo ========================================
pause


