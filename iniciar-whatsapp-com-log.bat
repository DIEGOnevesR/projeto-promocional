@echo off
chcp 65001 >nul
echo ========================================
echo    Servidor WhatsApp - Modo Debug
echo ========================================
echo.
echo Este script vai iniciar o servidor e mostrar
echo todos os erros em uma janela que nao fecha.
echo.
echo Pressione Ctrl+C para parar o servidor.
echo.
pause

cd /d "%~dp0"

echo.
echo Iniciando servidor...
echo.

node whatsapp-sender.js

echo.
echo ========================================
echo    SERVIDOR FINALIZADO
echo ========================================
echo.
echo Pressione qualquer tecla para fechar...
pause

