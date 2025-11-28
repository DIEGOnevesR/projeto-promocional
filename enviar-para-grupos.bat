@echo off
chcp 65001 >nul
echo ========================================
echo    ENVIAR IMAGEM PARA GRUPOS
echo ========================================
echo.

python enviar-para-grupos.py %*

echo.
pause

