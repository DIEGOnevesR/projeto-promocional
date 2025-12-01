#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import glob
import sys
from pathlib import Path

# Forçar output
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
sys.stderr.reconfigure(encoding='utf-8') if hasattr(sys.stderr, 'reconfigure') else None

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
print(f'Diretório: {os.getcwd()}')
print('=' * 60)
print()
sys.stdout.flush()

uploaded = 0
errors = 0
total = 0

# 1. Imagens padrão
print('📤 Imagens padrão...')
sys.stdout.flush()
imagens_list = ['Base do Produto.png', 'Call Action.png', 'Fundo.png', 'Logo.png', 'Logo Inferior.png', 'logo ofertas.png']
for img in imagens_list:
    path = os.path.join('Imagens', img)
    if os.path.exists(path):
        total += 1
        try:
            print(f'  📤 {img}...', end=' ', flush=True)
            cloudinary.uploader.upload(path, folder='imagens', public_id=Path(img).stem, overwrite=True)
            print('✅')
            uploaded += 1
        except Exception as e:
            print(f'❌ {str(e)}')
            errors += 1
            sys.stdout.flush()
    else:
        print(f'  ⚠️ Não encontrado: {img}')

# 2. Bandeiras
print('\n📤 Bandeiras...')
sys.stdout.flush()
if os.path.exists('Bandeira'):
    bandeiras = glob.glob('Bandeira/*.png')
    for b in bandeiras:
        total += 1
        nome = os.path.basename(b)
        try:
            print(f'  📤 {nome}...', end=' ', flush=True)
            cloudinary.uploader.upload(b, folder='bandeiras', public_id=Path(b).stem, overwrite=True)
            print('✅')
            uploaded += 1
        except Exception as e:
            print(f'❌ {str(e)}')
            errors += 1
            sys.stdout.flush()
else:
    print('  ⚠️ Pasta Bandeira não encontrada')

# 3. Fontes
print('\n📤 Fontes...')
sys.stdout.flush()
if os.path.exists('Fontes'):
    fontes = glob.glob('Fontes/*.ttf')
    for f in fontes:
        total += 1
        nome = os.path.basename(f)
        try:
            print(f'  📤 {nome}...', end=' ', flush=True)
            cloudinary.uploader.upload(f, folder='fontes', public_id=Path(f).stem, resource_type='raw', overwrite=True)
            print('✅')
            uploaded += 1
        except Exception as e:
            print(f'❌ {str(e)}')
            errors += 1
            sys.stdout.flush()
else:
    print('  ⚠️ Pasta Fontes não encontrada')

# 4. Tabelas
print('\n📤 Tabelas...')
sys.stdout.flush()
tabelas_list = ['Tabela de Preço.csv', 'Unidades.xlsx']
for t in tabelas_list:
    if os.path.exists(t):
        total += 1
        try:
            print(f'  📤 {t}...', end=' ', flush=True)
            cloudinary.uploader.upload(t, folder='tabelas', public_id=Path(t).stem, resource_type='raw', overwrite=True)
            print('✅')
            uploaded += 1
        except Exception as e:
            print(f'❌ {str(e)}')
            errors += 1
            sys.stdout.flush()
    else:
        print(f'  ⚠️ Não encontrado: {t}')

print()
print('=' * 60)
print(f'✅ Sucesso: {uploaded}/{total} arquivos')
if errors > 0:
    print(f'❌ Erros: {errors} arquivos')
print('=' * 60)
sys.stdout.flush()


