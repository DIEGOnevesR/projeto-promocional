@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Script de Keep-Alive para Render
echo ========================================
echo.
echo Este script mantém seus serviços Render ativos
echo fazendo ping periódico nos endpoints /health
echo.
echo Pressione Ctrl+C para parar
echo.
pause

python keep-alive.py

pause

