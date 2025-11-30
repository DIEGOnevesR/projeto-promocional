#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar conexão Gmail
"""
import os
import sys

print("=" * 50)
print("TESTE DE CONEXÃO GMAIL")
print("=" * 50)
print()

# 1. Verificar se credentials.json existe
print("[1/4] Verificando credentials.json...")
if os.path.exists('credentials.json'):
    print("✅ Arquivo credentials.json encontrado")
    try:
        import json
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
            if 'installed' in creds or 'web' in creds:
                print("✅ Formato do arquivo parece correto")
            else:
                print("⚠️ Formato do arquivo pode estar incorreto")
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
else:
    print("❌ Arquivo credentials.json NÃO encontrado!")
    print("   Por favor, baixe o arquivo do Google Cloud Console")
    sys.exit(1)

print()

# 2. Verificar dependências
print("[2/4] Verificando dependências Python...")
try:
    import google.auth
    import google.auth.oauthlib
    import googleapiclient.discovery
    print("✅ Todas as dependências estão instaladas")
except ImportError as e:
    print(f"❌ Dependência faltando: {e}")
    print("   Execute: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

print()

# 3. Testar importação do módulo
print("[3/4] Testando importação do módulo gmail_service...")
try:
    from gmail_service import GmailService
    print("✅ Módulo gmail_service importado com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar módulo: {e}")
    sys.exit(1)

print()

# 4. Testar autenticação (sem realmente autenticar)
print("[4/4] Testando inicialização do serviço...")
try:
    gmail_service = GmailService()
    print("✅ Serviço Gmail inicializado")
    print()
    print("=" * 50)
    print("TUDO PRONTO PARA AUTENTICAR!")
    print("=" * 50)
    print()
    print("Agora você pode:")
    print("1. Iniciar o servidor: python gmail-monitor-api.py")
    print("2. Abrir template_editor.html no navegador")
    print("3. Clicar em 'Conectar Gmail' na aba Gmail Monitor")
    print()
    print("NOTA: Uma janela do navegador será aberta para autorização OAuth2")
except Exception as e:
    print(f"❌ Erro ao inicializar serviço: {e}")
    sys.exit(1)










