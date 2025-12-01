#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para fazer upload de TODAS as imagens de cache processadas para Cloudinary
"""
import os
import glob
import sys
from pathlib import Path
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name='divlmyzig',
    api_key='573712429865238',
    api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w'
)

print('='*70)
print('UPLOAD DE CACHE DE IMAGENS PROCESSADAS PARA CLOUDINARY')
print('='*70)
print()

cache_folder = r'C:\Users\diegoribeiro-itr\Documents\Projeto Promocional\cache_imagens_processadas'

if not os.path.exists(cache_folder):
    print(f'ERRO: Pasta {cache_folder} nao encontrada!')
    sys.exit(1)

cache_files = glob.glob(os.path.join(cache_folder, '*.png'))
print(f'Total de arquivos de cache encontrados: {len(cache_files)}')
print()
print('Iniciando upload...')
print('='*70)
print()

uploaded = 0
errors = 0
total = len(cache_files)

for i, cache_file in enumerate(sorted(cache_files), 1):
    codigo = Path(cache_file).stem
    try:
        print(f'[{i}/{total}] {codigo}.png...', end=' ', flush=True)
        result = cloudinary.uploader.upload(
            cache_file,
            folder='cache',
            public_id=codigo,
            resource_type='image',
            overwrite=True
        )
        print('OK')
        uploaded += 1
        
        # Mostrar progresso a cada 50 arquivos
        if i % 50 == 0:
            print(f'  Progresso: {i}/{total} ({uploaded} OK, {errors} erros)')
            
    except Exception as e:
        print(f'ERRO: {str(e)[:50]}')
        errors += 1

print()
print('='*70)
print('RESUMO FINAL')
print('='*70)
print(f'Total processado: {total} arquivos')
print(f'Sucesso: {uploaded} arquivos')
if errors > 0:
    print(f'Erros: {errors} arquivos')
print('='*70)
print()

if uploaded == total:
    print('TODOS OS ARQUIVOS FORAM ENVIADOS COM SUCESSO!')
else:
    print(f'{errors} arquivo(s) falharam. Voce pode executar novamente.')

print()


