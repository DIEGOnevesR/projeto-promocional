#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import glob
from pathlib import Path
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name='divlmyzig',
    api_key='573712429865238',
    api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w'
)

print('=' * 60)
print('🚀 UPLOAD PARA CLOUDINARY')
print('=' * 60)
print()

uploaded = 0
errors = 0

# Imagens
print('📤 Imagens padrão...')
for img in ['Base do Produto.png', 'Call Action.png', 'Fundo.png', 'Logo.png', 'Logo Inferior.png', 'logo ofertas.png']:
    path = os.path.join('Imagens', img)
    if os.path.exists(path):
        try:
            cloudinary.uploader.upload(path, folder='imagens', public_id=Path(img).stem, overwrite=True)
            print(f'  ✅ {img}')
            uploaded += 1
        except Exception as e:
            print(f'  ❌ {img}: {e}')
            errors += 1

# Bandeiras
print('\n📤 Bandeiras...')
if os.path.exists('Bandeira'):
    for b in glob.glob('Bandeira/*.png'):
        try:
            cloudinary.uploader.upload(b, folder='bandeiras', public_id=Path(b).stem, overwrite=True)
            print(f'  ✅ {os.path.basename(b)}')
            uploaded += 1
        except Exception as e:
            print(f'  ❌ {os.path.basename(b)}: {e}')
            errors += 1

# Fontes
print('\n📤 Fontes...')
if os.path.exists('Fontes'):
    for f in glob.glob('Fontes/*.ttf'):
        try:
            cloudinary.uploader.upload(f, folder='fontes', public_id=Path(f).stem, resource_type='raw', overwrite=True)
            print(f'  ✅ {os.path.basename(f)}')
            uploaded += 1
        except Exception as e:
            print(f'  ❌ {os.path.basename(f)}: {e}')
            errors += 1

# Tabelas
print('\n📤 Tabelas...')
for t in ['Tabela de Preço.csv', 'Unidades.xlsx']:
    if os.path.exists(t):
        try:
            cloudinary.uploader.upload(t, folder='tabelas', public_id=Path(t).stem, resource_type='raw', overwrite=True)
            print(f'  ✅ {t}')
            uploaded += 1
        except Exception as e:
            print(f'  ❌ {t}: {e}')
            errors += 1

print()
print('=' * 60)
print(f'✅ Sucesso: {uploaded} arquivos')
if errors > 0:
    print(f'❌ Erros: {errors} arquivos')
print('=' * 60)
input('\nPressione ENTER para sair...')


