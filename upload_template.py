#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para fazer upload do banner-template.json para Cloudinary
"""
import os
import json
import sys
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name='divlmyzig',
    api_key='573712429865238',
    api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w'
)

template_file = 'banner-template.json'

if not os.path.exists(template_file):
    print(f'Arquivo {template_file} nao encontrado!')
    sys.exit(1)

print('='*70)
print('UPLOAD DO TEMPLATE PARA CLOUDINARY')
print('='*70)
print()

try:
    # Ler template
    with open(template_file, 'r', encoding='utf-8') as f:
        template_data = json.load(f)
    
    print(f'Template carregado: {len(template_data)} propriedades')
    print('Enviando para Cloudinary...', end=' ', flush=True)
    
    # Upload
    result = cloudinary.uploader.upload(
        template_file,
        folder='templates',
        public_id='banner-template',
        resource_type='raw',
        overwrite=True
    )
    
    url = result.get('secure_url') or result.get('url')
    print('OK')
    print(f'URL: {url}')
    print('='*70)
    
except Exception as e:
    print(f'ERRO: {e}')
    sys.exit(1)


