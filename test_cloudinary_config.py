#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar configuração do Cloudinary e descobrir cloud_name correto
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Tentar diferentes variações do cloud_name
api_key = '573712429865238'
api_secret = 'm_yHXjNUHkm8N2S05Jt3mkgig5w'

# Possíveis cloud_names
possible_names = ['Root', 'root', 'ROOT', 'dxyqjqjqj']

print('🔍 Testando configurações do Cloudinary...\n')

for cloud_name in possible_names:
    try:
        print(f'Tentando cloud_name: {cloud_name}')
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Tentar fazer uma chamada simples para verificar
        result = cloudinary.api.ping()
        print(f'✅ SUCESSO! cloud_name correto: {cloud_name}')
        print(f'   Resultado: {result}')
        break
        
    except Exception as e:
        print(f'   ❌ Erro: {e}')
        continue

print('\n💡 Se nenhum funcionou, verifique o cloud_name no dashboard do Cloudinary:')
print('   https://console.cloudinary.com/settings/account')


