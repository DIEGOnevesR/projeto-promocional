#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para enviar imagens para grupos do WhatsApp
"""
import requests
import json
import os
import sys
from pathlib import Path

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

def load_groups():
    """Carrega grupos do arquivo JSON"""
    if not os.path.exists(GROUPS_FILE):
        print_error(f'Arquivo {GROUPS_FILE} não encontrado!')
        print_info('Execute primeiro: listar-grupos.bat')
        return None
    
    try:
        with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('groups', [])
    except Exception as e:
        print_error(f'Erro ao carregar grupos: {e}')
        return None

def display_groups(groups):
    """Exibe grupos disponíveis"""
    if not groups:
        print_info('Nenhum grupo encontrado no arquivo.')
        return
    
    print(f'\n📋 {len(groups)} grupo(s) disponível(s):\n')
    for i, group in enumerate(groups, 1):
        print(f'{i}. {group.get("name", "Sem nome")} ({group.get("participants", 0)} participantes)')
        print(f'   ID: {group.get("id", "N/A")}\n')

def send_to_group(image_path, group_id):
    """Envia imagem para um grupo"""
    if not os.path.exists(image_path):
        print_error(f'Imagem não encontrada: {image_path}')
        return False
    
    try:
        abs_path = os.path.abspath(image_path)
        caption = f'Compre no WhatsApp - wa.me/551151944697?text=oi'
        
        print_info(f'Enviando {os.path.basename(image_path)} para grupo...')
        response = requests.post(
            f'{WHATSAPP_API_URL}/send-image-to-group',
            json={
                'groupId': group_id,
                'imagePath': abs_path,
                'caption': caption
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                group_name = result.get('groupName', 'Grupo')
                print_success(f'Enviado ao grupo "{group_name}" com sucesso!')
                return True
            else:
                print_error(f'Erro: {result.get("error")}')
                return False
        else:
            print_error(f'Erro HTTP {response.status_code}: {response.text}')
            return False
    except Exception as e:
        print_error(f'Erro ao enviar: {e}')
        return False

def main():
    print_header('ENVIAR IMAGEM PARA GRUPOS DO WHATSAPP')
    
    # Verificar servidor
    try:
        response = requests.get(f'{WHATSAPP_API_URL}/health', timeout=5)
        if response.status_code != 200 or response.json().get('status') != 'ready':
            print_error('Servidor WhatsApp não está pronto!')
            print_info('Execute: start-whatsapp-server.bat')
            return
    except:
        print_error('Servidor WhatsApp não está rodando!')
        print_info('Execute: start-whatsapp-server.bat')
        return
    
    # Carregar grupos
    groups = load_groups()
    if not groups:
        return
    
    # Exibir grupos
    display_groups(groups)
    
    # Solicitar imagem
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Procurar imagem mais recente
        banners_dir = Path('banners')
        if banners_dir.exists():
            jpg_files = list(banners_dir.glob('**/*.jpg'))
            if jpg_files:
                jpg_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                image_path = str(jpg_files[0])
                print_info(f'Usando imagem mais recente: {image_path}')
            else:
                print_error('Nenhuma imagem encontrada na pasta banners/')
                image_path = input('Digite o caminho da imagem: ').strip()
        else:
            image_path = input('Digite o caminho da imagem: ').strip()
    
    if not os.path.exists(image_path):
        print_error(f'Imagem não encontrada: {image_path}')
        return
    
    # Escolher grupos
    print('\nEscolha os grupos para enviar:')
    print('  - Digite os números separados por vírgula (ex: 1,2,3)')
    print('  - Ou digite "todos" para enviar para todos os grupos')
    print('  - Ou digite "sair" para cancelar')
    
    choice = input('\nOpção: ').strip().lower()
    
    if choice == 'sair':
        print_info('Operação cancelada.')
        return
    
    selected_groups = []
    if choice == 'todos':
        selected_groups = groups
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected_groups = [groups[i] for i in indices if 0 <= i < len(groups)]
        except:
            print_error('Opção inválida!')
            return
    
    if not selected_groups:
        print_error('Nenhum grupo selecionado!')
        return
    
    # Confirmar envio
    print(f'\n📤 Enviando para {len(selected_groups)} grupo(s)...')
    confirm = input('Continuar? (s/n): ').strip().lower()
    if confirm != 's':
        print_info('Operação cancelada.')
        return
    
    # Enviar para cada grupo
    success_count = 0
    for group in selected_groups:
        group_id = group.get('id')
        group_name = group.get('name', 'Grupo')
        print(f'\n📤 Enviando para: {group_name}...')
        if send_to_group(image_path, group_id):
            success_count += 1
    
    # Resumo
    print_header('RESUMO')
    print_success(f'{success_count} de {len(selected_groups)} grupo(s) receberam a imagem!')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n⚠️  Operação cancelada pelo usuário')
    except Exception as e:
        print(f'\n\n❌ Erro inesperado: {e}')
        import traceback
        traceback.print_exc()

