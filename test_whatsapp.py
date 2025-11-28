#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Teste para Envio de Imagens via WhatsApp
Testa a conexão e envio de imagens para o WhatsApp
"""
import os
import sys
import requests
import time
from pathlib import Path

# Configuração
WHATSAPP_API_URL = 'http://localhost:3001'
WHATSAPP_LINK = 'wa.me/551151944697?text=oi'

def print_header(text):
    """Imprime cabeçalho formatado"""
    print('\n' + '=' * 60)
    print(f'  {text}')
    print('=' * 60 + '\n')

def print_step(step_num, text):
    """Imprime passo do teste"""
    print(f'\n📋 PASSO {step_num}: {text}')
    print('-' * 60)

def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f'✅ {text}')

def print_error(text):
    """Imprime mensagem de erro"""
    print(f'❌ {text}')

def print_warning(text):
    """Imprime mensagem de aviso"""
    print(f'⚠️  {text}')

def print_info(text):
    """Imprime informação"""
    print(f'ℹ️  {text}')

def wait_user():
    """Aguarda o usuário pressionar Enter"""
    input('\n⏸️  Pressione ENTER para continuar...')

def check_server():
    """Verifica se o servidor WhatsApp está rodando"""
    print_step(1, 'Verificando se o servidor WhatsApp está rodando')
    
    try:
        print_info(f'Tentando conectar em: {WHATSAPP_API_URL}')
        response = requests.get(f'{WHATSAPP_API_URL}/health', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            message = data.get('message', '')
            number = data.get('number', 'unknown')
            
            if status == 'ready':
                print_success('Servidor WhatsApp está rodando e pronto!')
                print_info(f'Número configurado: {number}')
                return True
            else:
                print_warning(f'Servidor está rodando mas não está pronto: {message}')
                print_info('Aguarde a autenticação do WhatsApp (escaneie o QR Code)')
                return False
        else:
            print_error(f'Servidor respondeu com código: {response.status_code}')
            return False
            
    except requests.exceptions.ConnectionError:
        print_error('Não foi possível conectar ao servidor WhatsApp!')
        print_info('Certifique-se de que o servidor está rodando:')
        print('   1. Execute: start-whatsapp-server.bat')
        print('   2. Ou execute: npm start')
        print('   3. Aguarde aparecer "✅ Cliente WhatsApp pronto!"')
        return False
    except Exception as e:
        print_error(f'Erro ao verificar servidor: {e}')
        return False

def find_test_image():
    """Procura uma imagem de teste na pasta de banners"""
    print_step(2, 'Procurando imagem de teste')
    
    # Procurar na pasta de banners
    banners_dir = Path('banners')
    if banners_dir.exists():
        # Procurar por arquivos JPG mais recentes
        jpg_files = list(banners_dir.glob('**/*.jpg'))
        if jpg_files:
            # Ordenar por data de modificação (mais recente primeiro)
            jpg_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            test_image = jpg_files[0]
            print_success(f'Imagem de teste encontrada: {test_image}')
            print_info(f'Tamanho: {test_image.stat().st_size / 1024:.2f} KB')
            return str(test_image.absolute())
    
    print_warning('Nenhuma imagem encontrada na pasta banners/')
    print_info('Você pode:')
    print('   1. Gerar um banner primeiro (python main.py)')
    print('   2. Ou colocar uma imagem de teste na pasta banners/')
    return None

def send_test_image(image_path):
    """Envia imagem de teste para o WhatsApp"""
    print_step(3, 'Enviando imagem de teste para o WhatsApp')
    
    if not os.path.exists(image_path):
        print_error(f'Imagem não encontrada: {image_path}')
        return False
    
    filename = os.path.basename(image_path)
    abs_path = os.path.abspath(image_path)
    
    print_info(f'Arquivo: {filename}')
    print_info(f'Caminho completo: {abs_path}')
    print_info(f'Legenda: Compre no WhatsApp - {WHATSAPP_LINK}')
    
    try:
        print_info('Enviando requisição para o servidor...')
        response = requests.post(
            f'{WHATSAPP_API_URL}/send-image',
            json={
                'imagePath': abs_path,
                'caption': f'Compre no WhatsApp - {WHATSAPP_LINK}'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print_success('Imagem enviada com sucesso para o WhatsApp!')
                print_info('Verifique seu WhatsApp para confirmar o recebimento')
                return True
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                print_error(f'Erro ao enviar imagem: {error_msg}')
                return False
        else:
            print_error(f'Erro HTTP {response.status_code}: {response.text}')
            return False
            
    except requests.exceptions.Timeout:
        print_error('Tempo de espera excedido. O servidor pode estar ocupado.')
        return False
    except Exception as e:
        print_error(f'Erro ao enviar imagem: {e}')
        return False

def main():
    """Função principal do teste"""
    print_header('TESTE GUIADO - ENVIO DE IMAGENS VIA WHATSAPP')
    
    print('Este script irá testar o envio de imagens para o WhatsApp.')
    print('Certifique-se de que:')
    print('   1. O servidor WhatsApp está rodando (start-whatsapp-server.bat)')
    print('   2. O WhatsApp está autenticado (QR Code escaneado)')
    print('   3. Você tem pelo menos uma imagem na pasta banners/')
    
    wait_user()
    
    # Passo 1: Verificar servidor
    if not check_server():
        print('\n❌ TESTE INTERROMPIDO: Servidor WhatsApp não está disponível')
        print('\n💡 SOLUÇÃO:')
        print('   1. Abra um novo terminal')
        print('   2. Execute: start-whatsapp-server.bat')
        print('   3. Aguarde aparecer "✅ Cliente WhatsApp pronto!"')
        print('   4. Execute este teste novamente')
        wait_user()
        return
    
    wait_user()
    
    # Passo 2: Encontrar imagem de teste
    test_image = find_test_image()
    if not test_image:
        print('\n❌ TESTE INTERROMPIDO: Nenhuma imagem de teste encontrada')
        print('\n💡 SOLUÇÃO:')
        print('   1. Gere um banner primeiro: python main.py')
        print('   2. Ou coloque uma imagem JPG na pasta banners/')
        print('   3. Execute este teste novamente')
        wait_user()
        return
    
    wait_user()
    
    # Passo 3: Enviar imagem
    print_info('Agora vamos enviar a imagem para o WhatsApp...')
    print_info('Verifique seu WhatsApp após o envio!')
    wait_user()
    
    success = send_test_image(test_image)
    
    # Resultado final
    print_header('RESULTADO DO TESTE')
    
    if success:
        print_success('✅ TESTE CONCLUÍDO COM SUCESSO!')
        print('\n📱 Verifique seu WhatsApp:')
        print('   - Você deve ter recebido a imagem')
        print('   - A legenda deve conter o link de compra')
        print('   - O número deve ser: 5534999499430')
        print('\n🎉 O sistema está funcionando corretamente!')
        print('   Agora você pode gerar banners e eles serão enviados automaticamente.')
    else:
        print_error('❌ TESTE FALHOU')
        print('\n🔍 POSSÍVEIS CAUSAS:')
        print('   1. WhatsApp não está autenticado (escaneie o QR Code)')
        print('   2. Número incorreto (verifique whatsapp-sender.js)')
        print('   3. Servidor WhatsApp não está pronto')
        print('   4. Problema de conexão com a internet')
        print('\n💡 SOLUÇÃO:')
        print('   1. Verifique os logs do servidor WhatsApp')
        print('   2. Confirme que o QR Code foi escaneado')
        print('   3. Verifique o número no arquivo whatsapp-sender.js')
        print('   4. Tente executar o teste novamente')
    
    wait_user()
    
    print_header('INFORMAÇÕES ÚTEIS')
    print('📚 Documentação: README_WHATSAPP.md')
    print('🔗 API Health: http://localhost:3001/health')
    print('📞 Número configurado: 5534999499430')
    print('🔗 Link de compra: wa.me/551151944697?text=oi')
    print('\n✅ Teste finalizado!')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n⚠️  Teste interrompido pelo usuário')
        sys.exit(0)
    except Exception as e:
        print(f'\n\n❌ Erro inesperado: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

