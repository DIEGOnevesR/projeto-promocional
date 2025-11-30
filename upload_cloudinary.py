#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import glob
from pathlib import Path
import cloudinary
import cloudinary.uploader

# Configuração
cloudinary.config(
    cloud_name='divlmyzig',
    api_key='573712429865238',
    api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w'
)

def upload_file(file_path, folder, public_id=None):
    try:
        if not os.path.exists(file_path):
            print(f'⚠️ Não encontrado: {file_path}')
            return None
        
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
        
        url = result.get('secure_url') or result.get('url')
        print(f'✅ {os.path.basename(file_path)} → {url}')
        return url
    except Exception as e:
        print(f'❌ Erro: {file_path} - {e}')
        return None

print('🚀 Iniciando upload para Cloudinary (cloud_name: divlmyzig)...\n')

uploaded = []

# 1. Imagens padrão
print('📤 Upload imagens padrão...')
imagens_folder = 'Imagens'
if os.path.exists(imagens_folder):
    imagens = ['Base do Produto.png', 'Call Action.png', 'Fundo.png', 'Logo.png', 'Logo Inferior.png', 'logo ofertas.png']
    for img in imagens:
        path = os.path.join(imagens_folder, img)
        if os.path.exists(path):
            url = upload_file(path, 'imagens', Path(img).stem)
            if url:
                uploaded.append(img)

# 2. Bandeiras
print('\n📤 Upload bandeiras...')
if os.path.exists('Bandeira'):
    for bandeira in glob.glob('Bandeira/*.png'):
        url = upload_file(bandeira, 'bandeiras', Path(bandeira).stem)
        if url:
            uploaded.append(os.path.basename(bandeira))

# 3. Fontes
print('\n📤 Upload fontes...')
if os.path.exists('Fontes'):
    for fonte in glob.glob('Fontes/*.ttf'):
        url = upload_file(fonte, 'fontes', Path(fonte).stem)
        if url:
            uploaded.append(os.path.basename(fonte))

# 4. Tabelas
print('\n📤 Upload tabelas...')
for arquivo in ['Tabela de Preço.csv', 'Unidades.xlsx']:
    if os.path.exists(arquivo):
        url = upload_file(arquivo, 'tabelas', Path(arquivo).stem)
        if url:
            uploaded.append(arquivo)

print(f'\n✅ Upload concluído! Total: {len(uploaded)} arquivos')


