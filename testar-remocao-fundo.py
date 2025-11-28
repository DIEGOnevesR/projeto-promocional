#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se a remoção de fundo está funcionando
"""
import sys
import os

# Adicionar o diretório atual ao path para importar main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import BannerGenerator
    
    print('=' * 60)
    print('TESTE DE REMOÇÃO DE FUNDO')
    print('=' * 60)
    print()
    
    # Criar instância do gerador
    generator = BannerGenerator()
    
    # Testar com um código de produto (use um código que você sabe que existe)
    codigo_teste = 2  # Código do exemplo: https://fdvmtz.jbs.com.br/static/erp/img/2.jpg
    
    print(f'Testando remoção de fundo para produto código: {codigo_teste}')
    print('-' * 60)
    
    # Testar a função
    resultado = generator.get_product_image_with_background_removed(codigo_teste)
    
    print()
    print('-' * 60)
    print('RESULTADO:')
    print('-' * 60)
    
    if resultado:
        if resultado.startswith('data:image'):
            print('✅ SUCESSO! Imagem com fundo removido (base64)')
            print(f'   Tamanho do base64: {len(resultado)} caracteres')
            print(f'   Primeiros 50 caracteres: {resultado[:50]}...')
        else:
            print('⚠️  AVISO: Retornou URL original (remoção pode ter falhado)')
            print(f'   URL: {resultado}')
    else:
        print('❌ ERRO: Nenhum resultado retornado')
    
    print()
    print('=' * 60)
    
except Exception as e:
    print(f'❌ Erro ao executar teste: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)










