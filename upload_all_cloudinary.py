#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import glob
import sys
from pathlib import Path
import cloudinary
import cloudinary.uploader

# Configuração
cloudinary.config(
    cloud_name='divlmyzig',
    api_key='573712429865238',
    api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w'
)

print('=' * 60)
print('🚀 UPLOAD DE ASSETS PARA CLOUDINARY')
print('=' * 60)
print(f'Cloud Name: divlmyzig')
print(f'Diretório: {os.getcwd()}')
print('=' * 60)
print()

def upload_file(file_path, folder, public_id=None):
    try:
        if not os.path.exists(file_path):
            print(f'⚠️ Não encontrado: {file_path}', file=sys.stderr)
            return None
        
        if public_id is None:
            public_id = Path(file_path).stem
        
        ext = Path(file_path).suffix.lower()
        resource_type = 'raw' if ext in ['.csv', '.xlsx', '.xls', '.json', '.ttf', '.otf'] else 'image'
        
        print(f'📤 Enviando: {os.path.basename(file_path)}...', end=' ', flush=True)
        
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=True
        )
        
        url = result.get('secure_url') or result.get('url')
        print(f'✅ OK')
        return url
    except Exception as e:
        print(f'❌ ERRO: {str(e)}')
        return None

uploaded = []
total = 0
errors = []

# 1. Imagens padrão
print('📤 Upload imagens padrão...', flush=True)
imagens_folder = 'Imagens'
if os.path.exists(imagens_folder):
    imagens = ['Base do Produto.png', 'Call Action.png', 'Fundo.png', 'Logo.png', 'Logo Inferior.png', 'logo ofertas.png']
    for img in imagens:
        path = os.path.join(imagens_folder, img)
        if os.path.exists(path):
            total += 1
            url = upload_file(path, 'imagens', Path(img).stem)
            if url:
                uploaded.append(img)
            else:
                errors.append(img)

# 2. Bandeiras
print('\n📤 Upload bandeiras...', flush=True)
if os.path.exists('Bandeira'):
    bandeiras = glob.glob('Bandeira/*.png')
    for bandeira in bandeiras:
        total += 1
        url = upload_file(bandeira, 'bandeiras', Path(bandeira).stem)
        if url:
            uploaded.append(os.path.basename(bandeira))

# 3. Fontes
print('\n📤 Upload fontes...', flush=True)
if os.path.exists('Fontes'):
    fontes = glob.glob('Fontes/*.ttf')
    for fonte in fontes:
        total += 1
        url = upload_file(fonte, 'fontes', Path(fonte).stem)
        if url:
            uploaded.append(os.path.basename(fonte))

# 4. Tabelas
print('\n📤 Upload tabelas...', flush=True)
for arquivo in ['Tabela de Preço.csv', 'Unidades.xlsx']:
    if os.path.exists(arquivo):
        total += 1
        url = upload_file(arquivo, 'tabelas', Path(arquivo).stem)
        if url:
            uploaded.append(arquivo)
        else:
            errors.append(arquivo)

print()
print('=' * 60)
print('📊 RESUMO DO UPLOAD')
print('=' * 60)
print(f'✅ Sucesso: {len(uploaded)}/{total} arquivos')
if errors:
    print(f'❌ Erros: {len(errors)} arquivos')
    print('\nArquivos com erro:')
    for err in errors:
        print(f'  - {err}')
print('=' * 60)
print()
if len(uploaded) == total:
    print('🎉 Todos os arquivos foram enviados com sucesso!')
else:
    print(f'⚠️ {len(errors)} arquivo(s) falharam. Verifique os erros acima.')
print()

