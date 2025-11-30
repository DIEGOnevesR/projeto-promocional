#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Keep-Alive para manter serviços Render ativos
Este script faz ping periódico nos endpoints /health dos serviços
"""
import requests
import time
import sys
from datetime import datetime

# URLs dos serviços Render
SERVICES = {
    'Backend Principal': 'https://projeto-promocional.onrender.com/health',
    'WhatsApp Sender': 'https://whatsapp-sender-weq8.onrender.com/health',
    'Gmail Monitor': 'https://gmail-monitor-pfts.onrender.com/health'
}

# Intervalo entre pings (em segundos)
# 10 minutos = 600 segundos (mantém dentro do limite do Render)
INTERVAL = 600  # 10 minutos

def ping_service(name, url):
    """Faz ping em um serviço"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return True, 'OK'
        else:
            return False, f'Status {response.status_code}'
    except requests.exceptions.Timeout:
        return False, 'Timeout'
    except requests.exceptions.ConnectionError:
        return False, 'Connection Error'
    except Exception as e:
        return False, str(e)

def main():
    """Loop principal de keep-alive"""
    print('🔄 Script de Keep-Alive para Render')
    print('=' * 50)
    print(f'📡 Monitorando {len(SERVICES)} serviço(s)')
    print(f'⏱️  Intervalo: {INTERVAL // 60} minutos')
    print('=' * 50)
    print('💡 Pressione Ctrl+C para parar\n')
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'\n[{timestamp}] Iteração #{iteration}')
            print('-' * 50)
            
            results = {}
            for name, url in SERVICES.items():
                success, message = ping_service(name, url)
                status = '✅' if success else '❌'
                results[name] = success
                print(f'{status} {name}: {message}')
            
            # Resumo
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            print(f'\n📊 Resumo: {success_count}/{total_count} serviço(s) respondendo')
            
            # Aguardar próximo intervalo
            if iteration < 1000:  # Evitar loop infinito muito longo
                print(f'⏳ Aguardando {INTERVAL // 60} minutos até próximo ping...')
                time.sleep(INTERVAL)
            else:
                print('\n⚠️  Limite de iterações atingido. Reinicie o script se necessário.')
                break
                
    except KeyboardInterrupt:
        print('\n\n🛑 Script interrompido pelo usuário')
        print('👋 Até logo!')
        sys.exit(0)
    except Exception as e:
        print(f'\n❌ Erro fatal: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()

