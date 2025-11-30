#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simplificado para fazer upload de assets para Cloudinary
Execute: python upload_to_cloudinary.py
"""
import os
import glob
from pathlib import Path

# IMPORTANTE: Substitua 'SEU_CLOUD_NAME' pelo cloud_name correto do seu Cloudinary
# Você encontra isso em: https://console.cloudinary.com/settings/api-keys
CLOUD_NAME = 'divlmyzig'  # ✅ Cloud_name encontrado
API_KEY = '573712429865238'
API_SECRET = 'm_yHXjNUHkm8N2S05Jt3mkgig5w'

try:
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(
        cloud_name=CLOUD_NAME,
        api_key=API_KEY,
        api_secret=API_SECRET
    )
except ImportError:
    print('❌ Instale o cloudinary: pip install cloudinary')
    exit(1)

def upload_file(file_path, folder, public_id=None):
    """Upload arquivo para Cloudinary"""
    try:
        if not os.path.exists(file_path):
            print(f'⚠️ Arquivo não encontrado: {file_path}')
            return None
        
        if public_id is None:
            public_id = Path(file_path).stem
        
        # Determinar resource_type
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
        print(f'✅ {file_path} → {url}')
        return url
        
    except Exception as e:
        print(f'❌ Erro ao fazer upload de {file_path}: {e}')
        return None

def main():
    if CLOUD_NAME == 'SEU_CLOUD_NAME':
        print('❌ ERRO: Configure o CLOUD_NAME no arquivo antes de executar!')
        print('   Encontre o cloud_name em: https://console.cloudinary.com/settings/api-keys')
        return
    
    print('🚀 Iniciando upload para Cloudinary...\n')
    
    # Testar conexão primeiro
    try:
        cloudinary.api.ping()
        print('✅ Conexão com Cloudinary OK!\n')
    except Exception as e:
        print(f'❌ Erro ao conectar: {e}')
        print('   Verifique se o CLOUD_NAME está correto!')
        return
    
    uploaded = []
    
    # 1. Imagens padrão
    print('📤 Upload imagens padrão...')
    imagens_folder = 'Imagens'
    if os.path.exists(imagens_folder):
        imagens = [
            'Base do Produto.png',
            'Call Action.png',
            'Fundo.png',
            'Logo.png',
            'Logo Inferior.png',
            'logo ofertas.png'
        ]
        for img in imagens:
            path = os.path.join(imagens_folder, img)
            if os.path.exists(path):
                url = upload_file(path, 'imagens', Path(img).stem)
                if url:
                    uploaded.append({'tipo': 'imagem', 'nome': img, 'url': url})
    
    # 2. Bandeiras
    print('\n📤 Upload bandeiras...')
    bandeira_folder = 'Bandeira'
    if os.path.exists(bandeira_folder):
        for bandeira in glob.glob(os.path.join(bandeira_folder, '*.png')):
            nome = os.path.basename(bandeira)
            url = upload_file(bandeira, 'bandeiras', Path(nome).stem)
            if url:
                uploaded.append({'tipo': 'bandeira', 'nome': nome, 'url': url})
    
    # 3. Fontes
    print('\n📤 Upload fontes...')
    fonts_folder = 'Fontes'
    if os.path.exists(fonts_folder):
        for fonte in glob.glob(os.path.join(fonts_folder, '*.ttf')):
            nome = os.path.basename(fonte)
            url = upload_file(fonte, 'fontes', Path(nome).stem)
            if url:
                uploaded.append({'tipo': 'fonte', 'nome': nome, 'url': url})
    
    # 4. Tabelas
    print('\n📤 Upload tabelas...')
    tabelas = [
        ('Tabela de Preço.csv', 'tabelas'),
        ('Unidades.xlsx', 'tabelas')
    ]
    for arquivo, folder in tabelas:
        if os.path.exists(arquivo):
            url = upload_file(arquivo, folder, Path(arquivo).stem)
            if url:
                uploaded.append({'tipo': 'tabela', 'nome': arquivo, 'url': url})
    
    # Resumo
    print('\n' + '=' * 60)
    print(f'✅ Upload concluído! Total: {len(uploaded)} arquivos')
    print('=' * 60)

if __name__ == '__main__':
    main()

