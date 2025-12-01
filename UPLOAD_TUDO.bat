@echo off
chcp 65001 >nul
cls
title Upload Completo Cloudinary
echo ========================================
echo   UPLOAD COMPLETO PARA CLOUDINARY
echo ========================================
echo.

cd /d "%~dp0"
if exist "C:\Users\diegoribeiro-itr\.cursor\worktrees\Projeto_Promocional\acr" (
    cd "C:\Users\diegoribeiro-itr\.cursor\worktrees\Projeto_Promocional\acr"
)

echo 1. Upload de assets principais...
python upload_completo.py
echo.

echo 2. Upload do template...
if exist "banner-template.json" (
    python upload_template.py
) else (
    echo banner-template.json nao encontrado
)
echo.

echo 3. Upload de cache existente...
if exist "cache_imagens_processadas" (
    python upload_cache_existente.py
) else (
    echo Pasta cache_imagens_processadas nao encontrada
)
echo.

echo ========================================
echo Upload completo finalizado!
echo ========================================
pause


