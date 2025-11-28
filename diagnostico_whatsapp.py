#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Diagnóstico - WhatsApp
Verifica o status do servidor e testa o envio
"""
import requests
import os
from pathlib import Path

WHATSAPP_API_URL = 'http://localhost:3001'

def print_header(text):
    print('\n' + '=' * 60)
    print(f'  {text}')
    print('=' * 60)

def print_status(ok, message):
    symbol = '✅' if ok else '❌'
    print(f'{symbol} {message}')

print_header('DIAGNÓSTICO DO SERVIDOR WHATSAPP')

# 1. Verificar se o servidor está rodando
print('\n1. Verificando conexão com o servidor...')
try:
    response = requests.get(f'{WHATSAPP_API_URL}/health', timeout=5)
    if response.status_code == 200:
        data = response.json()
        print_status(True, f'Servidor está respondendo (código {response.status_code})')
        print(f'   Status: {data.get("status", "unknown")}')
        print(f'   Mensagem: {data.get("message", "N/A")}')
        print(f'   Número: {data.get("number", "N/A")}')
        
        if data.get('status') == 'ready':
            print_status(True, 'WhatsApp está pronto para enviar mensagens!')
        else:
            print_status(False, 'WhatsApp NÃO está pronto')
            print('   💡 Escaneie o QR Code no servidor WhatsApp')
    else:
        print_status(False, f'Servidor respondeu com código {response.status_code}')
        print(f'   Resposta: {response.text}')
except requests.exceptions.ConnectionError:
    print_status(False, 'Não foi possível conectar ao servidor!')
    print('   💡 Certifique-se de que o servidor está rodando:')
    print('      Execute: start-whatsapp-server.bat')
except Exception as e:
    print_status(False, f'Erro ao verificar servidor: {e}')

# 2. Procurar uma imagem de teste
print('\n2. Procurando imagem de teste...')
banners_dir = Path('banners')
test_image = None
if banners_dir.exists():
    jpg_files = list(banners_dir.glob('**/*.jpg'))
    if jpg_files:
        jpg_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        test_image = jpg_files[0]
        print_status(True, f'Imagem encontrada: {test_image}')
        print(f'   Tamanho: {test_image.stat().st_size / 1024:.2f} KB')
    else:
        print_status(False, 'Nenhuma imagem JPG encontrada na pasta banners/')
else:
    print_status(False, 'Pasta banners/ não existe')

# 3. Testar envio (se servidor estiver pronto e imagem encontrada)
if test_image and os.path.exists(test_image):
    print('\n3. Testando envio de imagem...')
    try:
        abs_path = os.path.abspath(test_image)
        print(f'   Caminho absoluto: {abs_path}')
        print(f'   Arquivo existe: {os.path.exists(abs_path)}')
        
        response = requests.post(
            f'{WHATSAPP_API_URL}/send-image',
            json={
                'imagePath': abs_path,
                'caption': 'Compre no WhatsApp - wa.me/551151944697?text=oi'
            },
            timeout=30
        )
        
        print(f'   Status HTTP: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print_status(True, 'Imagem enviada com sucesso!')
                print('   📱 Verifique seu WhatsApp')
            else:
                print_status(False, f'Erro no envio: {result.get("error", "Erro desconhecido")}')
        else:
            print_status(False, f'Erro HTTP {response.status_code}')
            print(f'   Resposta: {response.text[:300]}')
            
    except requests.exceptions.Timeout:
        print_status(False, 'Timeout ao enviar (servidor pode estar ocupado)')
    except requests.exceptions.ConnectionError:
        print_status(False, 'Erro de conexão ao enviar')
    except Exception as e:
        print_status(False, f'Erro inesperado: {e}')
        import traceback
        traceback.print_exc()
else:
    print('\n3. Pulando teste de envio (servidor não pronto ou imagem não encontrada)')

# 4. Resumo
print_header('RESUMO DO DIAGNÓSTICO')
print('\nVerifique:')
print('  [ ] Servidor WhatsApp está rodando (start-whatsapp-server.bat)')
print('  [ ] QR Code foi escaneado')
print('  [ ] Status do servidor é "ready"')
print('  [ ] Há imagens na pasta banners/')
print('  [ ] O número está correto no whatsapp-sender.js (5534999499430)')
print('\nPara mais informações, verifique os logs do servidor WhatsApp.')

print('\n' + '=' * 60)

