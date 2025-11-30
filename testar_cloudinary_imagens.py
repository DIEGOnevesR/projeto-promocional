#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar se as imagens estão no Cloudinary com os nomes corretos
"""
import os
import cloudinary
import cloudinary.api

# Configurar Cloudinary
cloudinary.config(
    cloud_name='divlmyzig',
    api_key='573712429865238',
    api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w'
)

# Mapeamento de nomes
image_mapping = {
    'base-produto': 'Base do Produto',
    'call-action': 'Call Action',
    'fundo': 'Fundo',
    'logo-inferior': 'Logo Inferior',
    'logo-ofertas': 'logo ofertas',
    'logo-superior': 'Logo',
}

print('='*70)
print('VERIFICANDO IMAGENS NO CLOUDINARY')
print('='*70)
print()

# Listar todas as imagens na pasta 'imagens'
try:
    result = cloudinary.api.resources(
        type='upload',
        prefix='imagens/',
        max_results=100
    )
    
    resources = result.get('resources', [])
    print(f'Total de imagens encontradas na pasta "imagens/": {len(resources)}')
    print()
    
    # Mostrar todas as imagens encontradas
    if resources:
        print('Imagens encontradas:')
        for resource in resources:
            public_id = resource.get('public_id', '')
            print(f'  - {public_id}')
        print()
    
    # Verificar cada imagem do mapeamento
    print('Verificando imagens necessárias:')
    print('-'*70)
    
    for key, name in image_mapping.items():
        expected_public_id = f'imagens/{name}'
        found = False
        
        for resource in resources:
            if resource.get('public_id') == expected_public_id:
                found = True
                print(f'✅ {key} → {name} (ENCONTRADO)')
                break
        
        if not found:
            print(f'❌ {key} → {name} (NÃO ENCONTRADO)')
            print(f'   Procurando por: {expected_public_id}')
    
    print()
    print('='*70)
    
except Exception as e:
    print(f'❌ Erro ao buscar imagens: {e}')
    import traceback
    traceback.print_exc()


