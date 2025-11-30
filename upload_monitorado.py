#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import glob
import sys
from pathlib import Path
import time

# Configurar output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

import cloudinary
import cloudinary.uploader

print('=' * 70)
print('🚀 UPLOAD DE ASSETS PARA CLOUDINARY - MONITORADO')
print('=' * 70)
print(f'Cloud Name: divlmyzig')
print(f'Diretório: {os.getcwd()}')
print('=' * 70)
print()
sys.stdout.flush()

cloudinary.config(
    cloud_name='divlmyzig',
    api_key='573712429865238',
    api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w'
)

uploaded = []
errors = []
total = 0

def upload_arquivo(file_path, folder, public_id=None):
    global total
    total += 1
    nome = os.path.basename(file_path)
    
    try:
        print(f'[{total}] 📤 {nome}...', end=' ', flush=True)
        
        if public_id is None:
            public_id = Path(file_path).stem
        
        ext = Path(file_path).suffix.lower()
        resource_type = 'raw' if ext in ['.csv', '.xlsx', '.xls', '.json', '.ttf', '.otf'] else 'image'
        
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=True
        )
        
        url = result.get('secure_url', 'OK')
        print(f'✅ OK')
        uploaded.append(nome)
        return True
        
    except Exception as e:
        print(f'❌ ERRO: {str(e)}')
        errors.append((nome, str(e)))
        return False

# 1. Imagens padrão
print('📤 SEÇÃO 1: Imagens Padrão')
print('-' * 70)
sys.stdout.flush()

imagens_list = [
    'Base do Produto.png',
    'Call Action.png',
    'Fundo.png',
    'Logo.png',
    'Logo Inferior.png',
    'logo ofertas.png'
]

for img in imagens_list:
    path = os.path.join('Imagens', img)
    if os.path.exists(path):
        upload_arquivo(path, 'imagens', Path(img).stem)
        time.sleep(0.5)  # Pequeno delay para não sobrecarregar
    else:
        print(f'⚠️ Não encontrado: {img}')

# 2. Bandeiras
print()
print('📤 SEÇÃO 2: Bandeiras')
print('-' * 70)
sys.stdout.flush()

if os.path.exists('Bandeira'):
    bandeiras = sorted(glob.glob('Bandeira/*.png'))
    for b in bandeiras:
        upload_arquivo(b, 'bandeiras', Path(b).stem)
        time.sleep(0.5)
else:
    print('⚠️ Pasta Bandeira não encontrada')

# 3. Fontes
print()
print('📤 SEÇÃO 3: Fontes')
print('-' * 70)
sys.stdout.flush()

if os.path.exists('Fontes'):
    fontes = sorted(glob.glob('Fontes/*.ttf'))
    for f in fontes:
        upload_arquivo(f, 'fontes', Path(f).stem)
        time.sleep(0.5)
else:
    print('⚠️ Pasta Fontes não encontrada')

# 4. Tabelas
print()
print('📤 SEÇÃO 4: Tabelas')
print('-' * 70)
sys.stdout.flush()

tabelas_list = ['Tabela de Preço.csv', 'Unidades.xlsx']
for t in tabelas_list:
    if os.path.exists(t):
        upload_arquivo(t, 'tabelas', Path(t).stem)
        time.sleep(0.5)
    else:
        print(f'⚠️ Não encontrado: {t}')

# Resumo
print()
print('=' * 70)
print('📊 RESUMO FINAL')
print('=' * 70)
print(f'✅ Sucesso: {len(uploaded)}/{total} arquivos')
print(f'❌ Erros: {len(errors)} arquivos')
print('=' * 70)

if errors:
    print()
    print('Arquivos com erro:')
    for nome, erro in errors:
        print(f'  - {nome}: {erro}')

if len(uploaded) == total:
    print()
    print('🎉 TODOS OS ARQUIVOS FORAM ENVIADOS COM SUCESSO!')
else:
    print()
    print(f'⚠️ {len(errors)} arquivo(s) falharam. Execute novamente para tentar novamente.')

print()
print('=' * 70)
sys.stdout.flush()


