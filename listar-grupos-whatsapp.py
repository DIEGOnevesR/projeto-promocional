#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para listar e salvar grupos do WhatsApp
"""
import requests
import json
import os
from datetime import datetime

WHATSAPP_API_URL = 'http://localhost:3001'
GROUPS_FILE = 'whatsapp-groups.json'

def print_header(text):
    print('\n' + '=' * 60)
    print(f'  {text}')
    print('=' * 60 + '\n')

def print_success(text):
    print(f'✅ {text}')

def print_error(text):
    print(f'❌ {text}')

def print_info(text):
    print(f'ℹ️  {text}')

def check_server():
    """Verifica se o servidor está rodando e pronto"""
    try:
        response = requests.get(f'{WHATSAPP_API_URL}/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ready':
                return True
            else:
                print_error(f'Servidor não está pronto: {data.get("message")}')
                return False
        else:
            print_error(f'Servidor respondeu com código {response.status_code}')
            return False
    except requests.exceptions.ConnectionError:
        print_error('Não foi possível conectar ao servidor!')
        print_info('Certifique-se de que o servidor está rodando: start-whatsapp-server.bat')
        return False
    except Exception as e:
        print_error(f'Erro ao verificar servidor: {e}')
        return False

def list_groups():
    """Lista os grupos do WhatsApp"""
    try:
        print_info('Buscando grupos do WhatsApp...')
        response = requests.get(f'{WHATSAPP_API_URL}/list-groups', timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('groups', [])
            else:
                print_error(f'Erro ao listar grupos: {data.get("error")}')
                return None
        else:
            print_error(f'Erro HTTP {response.status_code}: {response.text}')
            return None
    except Exception as e:
        print_error(f'Erro ao listar grupos: {e}')
        return None

def save_groups():
    """Salva os grupos em arquivo via API"""
    try:
        print_info('Salvando grupos em arquivo...')
        response = requests.get(f'{WHATSAPP_API_URL}/save-groups', timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data
            else:
                print_error(f'Erro ao salvar grupos: {data.get("error")}')
                return None
        else:
            print_error(f'Erro HTTP {response.status_code}: {response.text}')
            return None
    except Exception as e:
        print_error(f'Erro ao salvar grupos: {e}')
        return None

def display_groups(groups):
    """Exibe os grupos encontrados"""
    if not groups:
        print_info('Nenhum grupo encontrado.')
        return
    
    print(f'\n📋 {len(groups)} grupo(s) encontrado(s):\n')
    print('-' * 60)
    print(f'{"Nome do Grupo":<40} {"ID":<30} {"Participantes":<10}')
    print('-' * 60)
    
    for group in groups:
        name = group.get('name', 'Sem nome')[:38]
        group_id = group.get('id', 'N/A')[:28]
        participants = group.get('participants', 0)
        print(f'{name:<40} {group_id:<30} {participants:<10}')
    
    print('-' * 60)

def load_saved_groups():
    """Carrega grupos salvos do arquivo"""
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print_error(f'Erro ao carregar arquivo: {e}')
            return None
    return None

def main():
    print_header('LISTAR GRUPOS DO WHATSAPP')
    
    # Verificar servidor
    if not check_server():
        print('\n💡 Solução:')
        print('   1. Execute: start-whatsapp-server.bat')
        print('   2. Aguarde aparecer "✅ Cliente WhatsApp pronto!"')
        print('   3. Execute este script novamente')
        return
    
    print_success('Servidor está pronto!')
    
    # Salvar grupos
    result = save_groups()
    if result:
        print_success(f'{result.get("count", 0)} grupo(s) salvos em {GROUPS_FILE}')
        groups = result.get('groups', [])
        display_groups(groups)
        
        # Carregar e exibir informações do arquivo
        saved_data = load_saved_groups()
        if saved_data:
            last_update = saved_data.get('lastUpdate', 'N/A')
            print(f'\n📅 Última atualização: {last_update}')
            print(f'📁 Arquivo: {os.path.abspath(GROUPS_FILE)}')
    else:
        print_error('Não foi possível salvar os grupos')
        # Tentar apenas listar
        groups = list_groups()
        if groups:
            display_groups(groups)
    
    print_header('INSTRUÇÕES')
    print('Para enviar mensagens para um grupo:')
    print('   1. Abra o arquivo whatsapp-groups.json')
    print('   2. Copie o ID do grupo desejado')
    print('   3. Use o ID para enviar mensagens (em desenvolvimento)')
    print(f'\n📁 Arquivo salvo em: {os.path.abspath(GROUPS_FILE)}')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n⚠️  Operação cancelada pelo usuário')
    except Exception as e:
        print(f'\n\n❌ Erro inesperado: {e}')
        import traceback
        traceback.print_exc()

