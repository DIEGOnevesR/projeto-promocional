#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para fazer upload de imagens de cache já processadas para Cloudinary
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
print('UPLOAD DE CACHE DE IMAGENS PROCESSADAS')
print('='*70)
print()

cache_folder = 'cache_imagens_processadas'
if not os.path.exists(cache_folder):
    print(f'Pasta {cache_folder} nao encontrada!')
    sys.exit(1)

cache_files = glob.glob(os.path.join(cache_folder, '*.png'))
print(f'Total de arquivos de cache: {len(cache_files)}')
print()

uploaded = 0
errors = 0

for i, cache_file in enumerate(sorted(cache_files), 1):
    codigo = Path(cache_file).stem
    try:
        print(f'[{i}/{len(cache_files)}] {codigo}.png...', end=' ', flush=True)
        result = cloudinary.uploader.upload(
            cache_file,
            folder='cache',
            public_id=codigo,
            resource_type='image',
            overwrite=True
        )
        print('OK')
        uploaded += 1
    except Exception as e:
        print(f'ERRO: {e}')
        errors += 1

print()
print('='*70)
print(f'RESUMO: {uploaded}/{len(cache_files)} arquivos enviados')
if errors > 0:
    print(f'ERROS: {errors} arquivos')
print('='*70)


