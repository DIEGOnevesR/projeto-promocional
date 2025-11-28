#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para baixar o modelo do rembg antecipadamente
Execute este script uma vez para baixar o modelo antes de usar o gerador de banners
"""
import sys
import io
from PIL import Image

print('🔄 Iniciando download do modelo rembg...')
print('⏳ Isso pode levar alguns minutos na primeira vez...\n')

try:
    from rembg import remove
    
    # Criar uma imagem de teste pequena (1x1 pixel) para forçar o download do modelo
    print('📦 Criando imagem de teste...')
    test_image = Image.new('RGB', (100, 100), color='white')
    
    # Converter para bytes
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    print('⬇️  Baixando modelo do rembg (isso pode demorar ~2-5 minutos)...')
    print('💡 O modelo tem aproximadamente 176MB\n')
    
    # Processar a imagem - isso vai forçar o download do modelo
    output = remove(img_bytes.getvalue())
    
    print('✅ Modelo baixado com sucesso!')
    print('✓ O modelo está agora em cache e não precisará ser baixado novamente.')
    print('✓ Você pode usar o gerador de banners normalmente agora.\n')
    
except ImportError:
    print('❌ Erro: Biblioteca rembg não encontrada!')
    print('💡 Execute: pip install rembg Pillow numpy onnxruntime')
    sys.exit(1)
except Exception as e:
    print(f'❌ Erro ao baixar modelo: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)










