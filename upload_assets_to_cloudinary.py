#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para fazer upload de todos os assets para Cloudinary
Execute este script uma vez para fazer upload inicial
"""
import os
import glob
from pathlib import Path
from cloudinary_storage import upload_image_to_cloudinary, upload_file_to_cloudinary

def upload_imagens_padrao():
    """Upload imagens padrão da pasta imagens/"""
    print('\n📤 Fazendo upload de imagens padrão...')
    print('=' * 60)
    
    imagens_folder = 'imagens'
    if not os.path.exists(imagens_folder):
        print(f'❌ Pasta {imagens_folder} não encontrada!')
        return []
    
    imagens = [
        'Base do Produto.png',
        'Call Action.png',
        'Fundo.png',
        'Fundo.jpg',
        'Logo.png',
        'Logo Inferior.png',
        'Logo Inferior.jpg',
        'logo inferior.png',
        'logo inferior.jpg',
        'logo ofertas.png'
    ]
    
    uploaded = []
    for img in imagens:
        path = os.path.join(imagens_folder, img)
        if os.path.exists(path):
            # Remover extensão para public_id
            public_id = Path(img).stem
            url = upload_image_to_cloudinary(path, folder='imagens', public_id=public_id)
            if url:
                uploaded.append({'nome': img, 'url': url, 'public_id': f'imagens/{public_id}'})
        else:
            print(f'⚠️ Arquivo não encontrado: {img}')
    
    print(f'\n✅ {len(uploaded)} imagem(ns) padrão enviada(s)')
    return uploaded

def upload_bandeiras():
    """Upload bandeiras da pasta Bandeira/"""
    print('\n📤 Fazendo upload de bandeiras...')
    print('=' * 60)
    
    bandeira_folder = 'Bandeira'
    if not os.path.exists(bandeira_folder):
        print(f'⚠️ Pasta {bandeira_folder} não encontrada (opcional)')
        return []
    
    # Buscar todos os arquivos PNG na pasta Bandeira
    bandeiras = glob.glob(os.path.join(bandeira_folder, '*.png'))
    bandeiras.extend(glob.glob(os.path.join(bandeira_folder, '*.PNG')))
    
    uploaded = []
    for bandeira_path in bandeiras:
        nome = os.path.basename(bandeira_path)
        public_id = Path(nome).stem  # Nome sem extensão
        url = upload_image_to_cloudinary(bandeira_path, folder='bandeiras', public_id=public_id)
        if url:
            uploaded.append({'nome': nome, 'url': url, 'public_id': f'bandeiras/{public_id}'})
    
    print(f'\n✅ {len(uploaded)} bandeira(s) enviada(s)')
    return uploaded

def upload_fontes():
    """Upload fontes da pasta Fontes/"""
    print('\n📤 Fazendo upload de fontes...')
    print('=' * 60)
    
    fonts_folder = 'Fontes'
    if not os.path.exists(fonts_folder):
        print(f'⚠️ Pasta {fonts_folder} não encontrada (opcional)')
        return []
    
    # Buscar todos os arquivos TTF
    fontes = glob.glob(os.path.join(fonts_folder, '*.ttf'))
    fontes.extend(glob.glob(os.path.join(fonts_folder, '*.TTF')))
    
    uploaded = []
    for fonte_path in fontes:
        nome = os.path.basename(fonte_path)
        public_id = Path(nome).stem
        # Upload como 'raw' para fontes
        url = upload_file_to_cloudinary(fonte_path, folder='fontes', public_id=public_id)
        if url:
            uploaded.append({'nome': nome, 'url': url, 'public_id': f'fontes/{public_id}'})
    
    print(f'\n✅ {len(uploaded)} fonte(s) enviada(s)')
    return uploaded

def upload_tabelas():
    """Upload tabelas de preços e unidades"""
    print('\n📤 Fazendo upload de tabelas...')
    print('=' * 60)
    
    arquivos = [
        ('Tabela de Preço.csv', 'tabelas'),
        ('Unidades.xlsx', 'tabelas')
    ]
    
    uploaded = []
    for arquivo, folder in arquivos:
        if os.path.exists(arquivo):
            public_id = Path(arquivo).stem
            url = upload_file_to_cloudinary(arquivo, folder=folder, public_id=public_id)
            if url:
                uploaded.append({'nome': arquivo, 'url': url, 'public_id': f'{folder}/{public_id}'})
        else:
            print(f'⚠️ Arquivo não encontrado: {arquivo}')
    
    print(f'\n✅ {len(uploaded)} tabela(s) enviada(s)')
    return uploaded

def main():
    """Executa upload de todos os assets"""
    print('🚀 Iniciando upload de assets para Cloudinary...')
    print('=' * 60)
    
    all_uploaded = []
    
    # Upload imagens padrão
    imagens = upload_imagens_padrao()
    all_uploaded.extend(imagens)
    
    # Upload bandeiras
    bandeiras = upload_bandeiras()
    all_uploaded.extend(bandeiras)
    
    # Upload fontes
    fontes = upload_fontes()
    all_uploaded.extend(fontes)
    
    # Upload tabelas
    tabelas = upload_tabelas()
    all_uploaded.extend(tabelas)
    
    # Resumo
    print('\n' + '=' * 60)
    print('📊 RESUMO DO UPLOAD')
    print('=' * 60)
    print(f'Total de arquivos enviados: {len(all_uploaded)}')
    print('\nArquivos enviados:')
    for item in all_uploaded:
        print(f'  ✅ {item["public_id"]}: {item["url"]}')
    
    # Salvar mapeamento em arquivo JSON
    import json
    with open('cloudinary_assets_map.json', 'w', encoding='utf-8') as f:
        json.dump(all_uploaded, f, indent=2, ensure_ascii=False)
    
    print('\n✅ Mapeamento salvo em: cloudinary_assets_map.json')
    print('\n🎉 Upload concluído!')

if __name__ == '__main__':
    main()


