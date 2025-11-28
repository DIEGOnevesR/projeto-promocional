@echo off
echo ========================================
echo  Limpar Cache de Imagens Processadas
echo ========================================
echo.
echo Este script vai limpar o cache de imagens
echo para que todas sejam reprocessadas com
echo a nova normalizacao de tamanho.
echo.
pause

if exist "cache_imagens_processadas" (
    echo Removendo cache antigo...
    rmdir /s /q "cache_imagens_processadas"
    echo Cache removido!
) else (
    echo Pasta de cache nao encontrada.
)

echo.
echo Pronto! Agora execute o preprocessamento
echo novamente para processar as imagens com
echo a normalizacao de tamanho.
echo.
pause










