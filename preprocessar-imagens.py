#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para pré-processar todas as imagens da tabela de preços
Execute este script para processar todas as imagens antecipadamente
"""
import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import BannerGenerator
    
    print('=' * 60)
    print('🔄 PRÉ-PROCESSAMENTO DE IMAGENS')
    print('=' * 60)
    print()
    print('Este script vai processar todas as imagens da tabela de preços')
    print('e salvar no cache para acelerar a geração de banners.')
    print()
    input('Pressione ENTER para continuar...')
    print()
    
    # Criar gerador
    generator = BannerGenerator()
    
    # Pré-processar
    resultado = generator.preprocess_all_images()
    
    if resultado:
        print()
        print('=' * 60)
        print('✅ PRÉ-PROCESSAMENTO CONCLUÍDO COM SUCESSO!')
        print('=' * 60)
        print(f'✓ {resultado["processadas"]} imagens processadas agora')
        print(f'✓ {resultado["em_cache"]} imagens já estavam em cache')
        print(f'⚠ {resultado["erros"]} erros')
        print(f'📊 Total: {resultado["total"]} imagens')
        print()
        print('💡 Agora os banners serão gerados muito mais rápido!')
        print('=' * 60)
    else:
        print('❌ Erro no pré-processamento')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ Erro: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)










