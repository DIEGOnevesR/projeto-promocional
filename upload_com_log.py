#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import glob
import sys
from pathlib import Path
import cloudinary
import cloudinary.uploader

# Forçar output UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

cloudinary.config(
    cloud_name='divlmyzig',
    api_key='573712429865238',
    api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w'
)

def log_print(msg):
    print(msg, flush=True)
    with open('upload_log.txt', 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

# Limpar log anterior
if os.path.exists('upload_log.txt'):
    os.remove('upload_log.txt')

log_print('=' * 60)
log_print('🚀 UPLOAD PARA CLOUDINARY')
log_print('=' * 60)
log_print(f'Diretório: {os.getcwd()}')
log_print('=' * 60)
log_print('')

uploaded = 0
errors = 0

# Imagens
log_print('📤 Imagens padrão...')
imagens_list = ['Base do Produto.png', 'Call Action.png', 'Fundo.png', 'Logo.png', 'Logo Inferior.png', 'logo ofertas.png']
for img in imagens_list:
    path = os.path.join('Imagens', img)
    if os.path.exists(path):
        try:
            log_print(f'  📤 Enviando: {img}...')
            cloudinary.uploader.upload(path, folder='imagens', public_id=Path(img).stem, overwrite=True)
            log_print(f' ✅ OK')
            uploaded += 1
        except Exception as e:
            log_print(f' ❌ ERRO: {str(e)}')
            errors += 1
    else:
        log_print(f'  ⚠️ Não encontrado: {img}')

# Bandeiras
log_print('\n📤 Bandeiras...')
if os.path.exists('Bandeira'):
    bandeiras = glob.glob('Bandeira/*.png')
    for b in bandeiras:
        try:
            nome = os.path.basename(b)
            log_print(f'  📤 Enviando: {nome}...')
            cloudinary.uploader.upload(b, folder='bandeiras', public_id=Path(b).stem, overwrite=True)
            log_print(f' ✅ OK')
            uploaded += 1
        except Exception as e:
            log_print(f' ❌ ERRO: {str(e)}')
            errors += 1
else:
    log_print('  ⚠️ Pasta Bandeira não encontrada')

# Fontes
log_print('\n📤 Fontes...')
if os.path.exists('Fontes'):
    fontes = glob.glob('Fontes/*.ttf')
    for f in fontes:
        try:
            nome = os.path.basename(f)
            log_print(f'  📤 Enviando: {nome}...')
            cloudinary.uploader.upload(f, folder='fontes', public_id=Path(f).stem, resource_type='raw', overwrite=True)
            log_print(f' ✅ OK')
            uploaded += 1
        except Exception as e:
            log_print(f' ❌ ERRO: {str(e)}')
            errors += 1
else:
    log_print('  ⚠️ Pasta Fontes não encontrada')

# Tabelas
log_print('\n📤 Tabelas...')
tabelas_list = ['Tabela de Preço.csv', 'Unidades.xlsx']
for t in tabelas_list:
    if os.path.exists(t):
        try:
            log_print(f'  📤 Enviando: {t}...')
            cloudinary.uploader.upload(t, folder='tabelas', public_id=Path(t).stem, resource_type='raw', overwrite=True)
            log_print(f' ✅ OK')
            uploaded += 1
        except Exception as e:
            log_print(f' ❌ ERRO: {str(e)}')
            errors += 1
    else:
        log_print(f'  ⚠️ Não encontrado: {t}')

log_print('')
log_print('=' * 60)
log_print(f'✅ Sucesso: {uploaded} arquivos')
if errors > 0:
    log_print(f'❌ Erros: {errors} arquivos')
log_print('=' * 60)
log_print('')
log_print('📄 Log salvo em: upload_log.txt')
log_print('')

