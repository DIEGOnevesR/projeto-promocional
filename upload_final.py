#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import glob
import sys
from pathlib import Path

# Forçar output imediato
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

try:
    import cloudinary
    import cloudinary.uploader
except ImportError:
    print("ERRO: cloudinary nao instalado. Execute: pip install cloudinary")
    sys.exit(1)

cloudinary.config(
    cloud_name='divlmyzig',
    api_key='573712429865238',
    api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w'
)

print('='*70)
print('UPLOAD PARA CLOUDINARY')
print('='*70)
print(f'Diretorio: {os.getcwd()}')
print('='*70)
print()
sys.stdout.flush()

uploaded = 0
errors = 0
total = 0

def upload_file(file_path, folder, public_id=None, resource_type='image'):
    global total, uploaded, errors
    total += 1
    nome = os.path.basename(file_path)
    
    try:
        print(f'[{total}] Enviando: {nome}...', end=' ', flush=True)
        
        if public_id is None:
            public_id = Path(file_path).stem
        
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=True
        )
        
        print('OK')
        uploaded += 1
        return True
        
    except Exception as e:
        print(f'ERRO: {str(e)}')
        errors += 1
        return False

# 1. Imagens
print('SEÇÃO 1: Imagens Padrão')
print('-'*70)
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
        upload_file(path, 'imagens', Path(img).stem)
    else:
        print(f'  Nao encontrado: {img}')

# 2. Bandeiras
print()
print('SEÇÃO 2: Bandeiras')
print('-'*70)
sys.stdout.flush()

if os.path.exists('Bandeira'):
    bandeiras = sorted(glob.glob('Bandeira/*.png'))
    for b in bandeiras:
        upload_file(b, 'bandeiras', Path(b).stem)
else:
    print('  Pasta Bandeira nao encontrada')

# 3. Fontes
print()
print('SEÇÃO 3: Fontes')
print('-'*70)
sys.stdout.flush()

if os.path.exists('Fontes'):
    fontes = sorted(glob.glob('Fontes/*.ttf'))
    for f in fontes:
        upload_file(f, 'fontes', Path(f).stem, resource_type='raw')
else:
    print('  Pasta Fontes nao encontrada')

# 4. Tabelas
print()
print('SEÇÃO 4: Tabelas')
print('-'*70)
sys.stdout.flush()

tabelas_list = ['Tabela de Preço.csv', 'Unidades.xlsx']
for t in tabelas_list:
    if os.path.exists(t):
        upload_file(t, 'tabelas', Path(t).stem, resource_type='raw')
    else:
        print(f'  Nao encontrado: {t}')

# Resumo
print()
print('='*70)
print('RESUMO')
print('='*70)
print(f'Sucesso: {uploaded}/{total} arquivos')
if errors > 0:
    print(f'Erros: {errors} arquivos')
print('='*70)
sys.stdout.flush()

if uploaded == total:
    print()
    print('TODOS OS ARQUIVOS FORAM ENVIADOS COM SUCESSO!')
else:
    print()
    print(f'{errors} arquivo(s) falharam.')

print()


