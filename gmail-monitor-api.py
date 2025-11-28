#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Flask para Monitoramento de E-mails Gmail
"""
import os
import re
import threading
import time
import random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from gmail_service import GmailService
from email_processor import extract_email_info, format_whatsapp_message, generate_authorization_link, validate_extracted_info
from email_database import EmailDatabase
import requests

app = Flask(__name__)
CORS(app)

# Tratamento de erros global
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint não encontrado',
        'path': request.path
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Erro interno do servidor',
        'message': str(error) if str(error) else 'Erro desconhecido'
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        'success': False,
        'error': 'Erro inesperado',
        'message': str(e)
    }), 500

# Configurações
WHATSAPP_API_URL = 'http://localhost:3001'
GMAIL_MONITOR_PORT = 5001  # Porta do servidor Gmail Monitor
CHECK_INTERVAL = 60  # 1 minuto em segundos

# Configurações de Simulação Humana (mesmas do Mensager)
HUMAN_DELAY_FIRST_MIN = 25  # Segundos - primeira mensagem
HUMAN_DELAY_FIRST_MAX = 35  # Segundos - primeira mensagem
HUMAN_DELAY_SUBSEQUENT_MIN = 30  # Segundos - mensagens subsequentes
HUMAN_DELAY_SUBSEQUENT_MAX = 45  # Segundos - mensagens subsequentes

# Instâncias globais
gmail_service = GmailService()
email_db = EmailDatabase()
monitor_thread = None
monitor_running = False
last_check_time = None
email_send_count = 0  # Contador para simulação humana (primeira vs subsequentes)

# Lock e set para evitar processamento simultâneo do mesmo e-mail
processing_lock = threading.Lock()
emails_being_processed = set()  # Set de message_ids sendo processados

def get_human_delay(is_first_message=False):
    """
    Gera um delay aleatório para simulação humana
    
    Args:
        is_first_message: Se é a primeira mensagem da sessão
        
    Returns:
        int: Delay em segundos
    """
    if is_first_message:
        delay = random.uniform(HUMAN_DELAY_FIRST_MIN, HUMAN_DELAY_FIRST_MAX)
    else:
        delay = random.uniform(HUMAN_DELAY_SUBSEQUENT_MIN, HUMAN_DELAY_SUBSEQUENT_MAX)
    
    return int(delay)

def prepare_whatsapp_contact(contact_id):
    """
    Prepara contato no WhatsApp (cria LID se necessário)
    
    Args:
        contact_id: ID do contato (formato: 55XXXXXXXXXXX)
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        # Remover @c.us se existir
        clean_number = contact_id.replace('@c.us', '').replace('@g.us', '')
        
        response = requests.post(
            f"{WHATSAPP_API_URL}/prepare-contacts",
            json={
                'numbers': [clean_number]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                prepared = result.get('results', {}).get('prepared', [])
                if prepared:
                    return True, None
                else:
                    failed = result.get('results', {}).get('failed', [])
                    error_msg = failed[0].get('error', 'Falha ao preparar contato') if failed else 'Contato não preparado'
                    return False, error_msg
            return False, result.get('error', 'Falha ao preparar contato')
        else:
            error_msg = response.json().get('error', 'Erro desconhecido')
            return False, error_msg
    except requests.exceptions.RequestException as e:
        return False, str(e)

def normalize_phone_number(phone_text):
    """
    Normaliza número de telefone extraído do e-mail
    Extrai DDD e número, montando base: 55 + DDD + número
    
    Args:
        phone_text: Número no formato do e-mail (ex: "(34) 99780-4675" ou "34997804675")
        
    Returns:
        tuple: (base_number, ddd, rest) onde:
            - base_number: 55 + DDD + número completo (ex: "5534997804675")
            - ddd: DDD extraído (ex: "34")
            - rest: Número após o DDD (ex: "997804675")
    """
    # Remover todos os caracteres não numéricos
    digits_only = re.sub(r'[^\d]', '', phone_text)
    
    # Se começar com 55, remover
    if digits_only.startswith('55'):
        digits_only = digits_only[2:]
    
    # Extrair DDD (2 primeiros dígitos)
    if len(digits_only) >= 2:
        ddd = digits_only[:2]
        rest = digits_only[2:]
        base_number = f"55{ddd}{rest}"
        return base_number, ddd, rest
    
    return None, None, None

def generate_phone_candidates(base_number, ddd, rest):
    """
    Gera candidatos de número (com e sem 9 após o DDD)
    
    Args:
        base_number: Número base (55 + DDD + número completo)
        ddd: DDD (2 dígitos)
        rest: Número após o DDD
        
    Returns:
        list: Lista de candidatos [(número_com_9, número_sem_9), ...]
              Prioriza o número original (que veio do e-mail)
    """
    candidates = []
    
    # Verificar se é celular (9 dígitos após DDD, começando com 9)
    # ou fixo (8 dígitos após DDD, não começando com 9)
    if len(rest) == 9 and rest.startswith('9'):
        # É celular com 9
        # Candidato 1: Sem 9 (prioridade - mais comum funcionar)
        candidate_without_9 = f"55{ddd}{rest[1:]}"  # 55 + DDD + 8 dígitos (remove o 9)
        # Candidato 2: Com 9 (original do e-mail)
        candidate_with_9 = base_number  # 55 + DDD + 9 + 8 dígitos
        
        # Priorizar SEM 9 primeiro (mais comum funcionar)
        candidates = [
            (candidate_without_9, 'sem_9'),  # Prioridade 1
            (candidate_with_9, 'com_9')  # Prioridade 2
        ]
    elif len(rest) == 8:
        # É fixo (8 dígitos) ou celular sem 9
        # Candidato 1: Sem 9 (original)
        candidate_without_9 = base_number  # 55 + DDD + 8 dígitos
        # Candidato 2: Com 9 (adicionar 9)
        candidate_with_9 = f"55{ddd}9{rest}"  # 55 + DDD + 9 + 8 dígitos
        
        # Priorizar o que veio do e-mail (sem 9)
        candidates = [
            (candidate_without_9, 'sem_9'),  # Prioridade 1
            (candidate_with_9, 'com_9')  # Prioridade 2
        ]
    else:
        # Formato não reconhecido, usar apenas o original
        candidates = [(base_number, 'original')]
    
    return candidates

def validate_phone_with_whatsapp(phone_text):
    """
    Valida número de telefone com WhatsApp usando getNumberId
    Gera candidatos (com e sem 9) e verifica qual é válido
    
    Args:
        phone_text: Número no formato do e-mail (ex: "(34) 99780-4675")
        
    Returns:
        tuple: (valid_number, validation_info) onde:
            - valid_number: Número válido encontrado (ou None se nenhum)
            - validation_info: Dict com informações da validação
    """
    # Normalizar número
    base_number, ddd, rest = normalize_phone_number(phone_text)
    
    if not base_number:
        return None, {
            'error': 'Não foi possível normalizar o número',
            'original': phone_text
        }
    
    # Gerar candidatos
    candidates = generate_phone_candidates(base_number, ddd, rest)
    
    validation_info = {
        'original': phone_text,
        'normalized': base_number,
        'ddd': ddd,
        'rest': rest,
        'candidates': [],
        'valid': None,
        'method': None
    }
    
    # Testar cada candidato usando /prepare-contacts
    for candidate_number, candidate_type in candidates:
        try:
            print(f"🔍 Validando candidato {candidate_type}: {candidate_number}")
            
            # Chamar /prepare-contacts para validar
            response = requests.post(
                f"{WHATSAPP_API_URL}/prepare-contacts",
                json={
                    'numbers': [candidate_number]
                },
                timeout=30
            )
            
            candidate_info = {
                'number': candidate_number,
                'type': candidate_type,
                'valid': False,
                'error': None
            }
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    prepared = result.get('results', {}).get('prepared', [])
                    failed = result.get('results', {}).get('failed', [])
                    
                    # Verificar se foi preparado com sucesso
                    if prepared:
                        prepared_info = prepared[0]
                        candidate_info['valid'] = True
                        candidate_info['chatId'] = prepared_info.get('chatId')
                        candidate_info['method'] = prepared_info.get('method')
                        
                        validation_info['candidates'].append(candidate_info)
                        
                        # Se encontrou um válido, usar esse (prioridade ao primeiro válido)
                        if validation_info['valid'] is None:
                            validation_info['valid'] = candidate_number
                            validation_info['method'] = candidate_type
                            print(f"✅ Número válido encontrado: {candidate_number} ({candidate_type})")
                            # Não retornar ainda - testar todos para ter informações completas
                    else:
                        # Nenhum preparado, verificar se falhou
                        if failed:
                            error_msg = failed[0].get('error', 'Falha ao preparar')
                            candidate_info['error'] = error_msg
                            print(f"❌ Candidato {candidate_type} inválido: {error_msg}")
                        else:
                            candidate_info['error'] = 'Número não encontrado no WhatsApp'
                            print(f"❌ Candidato {candidate_type} não encontrado no WhatsApp")
                        
                        validation_info['candidates'].append(candidate_info)
                else:
                    error_msg = result.get('error', 'Erro desconhecido')
                    candidate_info['error'] = error_msg
                    validation_info['candidates'].append(candidate_info)
                    print(f"❌ Erro ao validar candidato {candidate_type}: {error_msg}")
            else:
                error_msg = response.json().get('error', 'Erro HTTP')
                candidate_info['error'] = error_msg
                validation_info['candidates'].append(candidate_info)
                print(f"❌ Erro HTTP ao validar candidato {candidate_type}: {error_msg}")
        
        except requests.exceptions.RequestException as e:
            candidate_info = {
                'number': candidate_number,
                'type': candidate_type,
                'valid': False,
                'error': str(e)
            }
            validation_info['candidates'].append(candidate_info)
            print(f"❌ Exceção ao validar candidato {candidate_type}: {e}")
    
    # Coletar todos os candidatos válidos, mantendo a ordem original dos candidatos
    # Criar um dicionário para mapear número -> info
    candidates_map = {c['number']: c for c in validation_info['candidates'] if c.get('valid', False)}
    
    # Ordenar candidatos válidos pela ordem original (primeiro o original do e-mail)
    valid_candidates = []
    for candidate_number, candidate_type in candidates:
        if candidate_number in candidates_map:
            valid_candidates.append(candidates_map[candidate_number])
    
    # Retornar informações de validação com lista de candidatos válidos
    if valid_candidates:
        # Se houver apenas um válido, usar esse
        if len(valid_candidates) == 1:
            validation_info['valid'] = valid_candidates[0]['number']
            validation_info['method'] = valid_candidates[0]['type']
            print(f"✅ Apenas um candidato válido: {validation_info['valid']} ({validation_info['method']})")
        else:
            # Se houver múltiplos válidos, retornar lista ordenada (original primeiro)
            validation_info['valid'] = valid_candidates[0]['number']  # Primeiro como padrão
            validation_info['method'] = valid_candidates[0]['type']
            validation_info['all_valid'] = [c['number'] for c in valid_candidates]  # Já ordenado pela ordem original
            print(f"✅ Múltiplos candidatos válidos encontrados: {[c['number'] for c in valid_candidates]}")
            print(f"   Ordem de tentativa: 1º {valid_candidates[0]['number']} ({valid_candidates[0]['type']}), 2º {valid_candidates[1]['number']} ({valid_candidates[1]['type']})")
            print(f"   Testando ambos no envio na ordem acima...")
        
        return validation_info['valid'], validation_info
    else:
        # Se nenhum for válido, retornar o primeiro candidato (original) para tentar mesmo assim
        print(f"⚠️ Nenhum candidato válido encontrado, usando o original: {candidates[0][0]}")
        validation_info['valid'] = candidates[0][0]
        validation_info['method'] = 'fallback_original'
        return candidates[0][0], validation_info

def send_to_whatsapp(contact_id, message):
    """
    Envia mensagem para WhatsApp via API existente
    Usa validação prévia para identificar o número correto (com ou sem 9 após DDD)
    
    Args:
        contact_id: ID do contato (formato: 55XXXXXXXXXXX ou texto do e-mail)
        message: Mensagem a enviar
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        # Remover @c.us se existir
        clean_number = contact_id.replace('@c.us', '').replace('@g.us', '')
        
        # Validar número com WhatsApp (gera candidatos e testa qual é válido)
        print(f"🔍 Validando número de telefone: {clean_number}")
        valid_number, validation_info = validate_phone_with_whatsapp(clean_number)
        
        if not valid_number:
            error_msg = validation_info.get('error', 'Número inválido')
            print(f"❌ Não foi possível validar o número: {error_msg}")
            return False, f"Número inválido: {error_msg}"
        
        # Se houver múltiplos candidatos válidos, tentar todos
        all_valid_numbers = validation_info.get('all_valid', [valid_number])
        
        print(f"✅ Número(s) válido(s) identificado(s): {all_valid_numbers}")
        print(f"   Método principal: {validation_info.get('method', 'unknown')}")
        
        # Tentar enviar com cada candidato válido (na ordem de prioridade)
        last_error = None
        for idx, candidate_number in enumerate(all_valid_numbers):
            try:
                print(f"\n{'='*60}")
                print(f"🔧 Tentativa {idx + 1}/{len(all_valid_numbers)}: número {candidate_number}")
                print(f"{'='*60}")
                
                # Preparar o contato (criar LID se necessário)
                print(f"🔧 Preparando contato {candidate_number}...")
                prepare_success, prepare_error = prepare_whatsapp_contact(candidate_number)
                
                if not prepare_success:
                    # Se falhar ao preparar, tentar enviar mesmo assim (pode já ter LID)
                    print(f"⚠️ Aviso ao preparar contato: {prepare_error}. Tentando enviar mesmo assim...")
                
                # Formatar ID do contato (adicionar @c.us)
                contact_id_formatted = f"{candidate_number}@c.us"
                
                # Enviar mensagem
                print(f"📤 Enviando mensagem para {contact_id_formatted}...")
                response = requests.post(
                    f"{WHATSAPP_API_URL}/send-text-to-contact",
                    json={
                        'contactId': contact_id_formatted,
                        'text': message
                    },
                    timeout=45  # Aumentado para dar tempo de esperar ACK (20s wait + margem)
                )
                
                if response.status_code == 200:
                    result = response.json()
                    success = result.get('success', False)
                    delivered = result.get('delivered', None)
                    ack = result.get('ack', None)
                    
                    print(f"📨 Retorno WhatsApp: success={success}, delivered={delivered}, ack={ack}")
                    
                    # Verificar se foi realmente entregue (dois ticks)
                    # IMPORTANTE: ACK 1 = servidor (um tick), ACK 2 = entregue (dois ticks)
                    # Por isso, verificamos ack >= 2 para garantir que foi realmente entregue
                    is_delivered = False
                    
                    # Só considerar entregue se:
                    # 1. delivered é explicitamente True (não None, não False)
                    # 2. E ack >= 2 (ACK 2 = entregue/dois ticks, ACK 3 = lido)
                    if delivered is True:
                        # Se delivered é True, verificar também o ack para garantir
                        if isinstance(ack, int) and ack >= 2:
                            is_delivered = True
                        else:
                            # delivered=True mas ack < 2 - pode ser falso positivo (ack=1 é apenas um tick)
                            print(f"⚠️ delivered=True mas ack={ack} não confirma entrega (ack=1 é apenas um tick, precisa ack>=2)")
                            is_delivered = False
                    elif delivered is False:
                        # delivered=False explicitamente - não entregue
                        is_delivered = False
                    elif delivered is None:
                        # delivered=None - não sabemos, verificar ack
                        if isinstance(ack, int) and ack >= 2:
                            # Se ack >= 2 mas delivered=None, pode ser que ainda não atualizou
                            # Mas vamos considerar como não entregue para ser mais seguro
                            print(f"⚠️ delivered=None mas ack={ack} - aguardando confirmação explícita")
                            is_delivered = False
                        else:
                            is_delivered = False
                    
                    # Consideramos OK apenas se entregue confirmado
                    if success and is_delivered:
                        print(f"✅ Mensagem ENTREGUE (dois ticks) para {candidate_number} (ack={ack}, delivered={delivered})")
                        return True, None
                    
                    # Se não foi entregue, tentar próximo candidato ou retry
                    if not success:
                        # Se success for False, houve erro no envio
                        error_msg = result.get('error', 'Erro desconhecido')
                        print(f"❌ Erro ao enviar mensagem para {candidate_number}: {error_msg}")
                        last_error = error_msg
                        
                        # Se ainda der erro de LID, tentar preparar novamente
                        if 'LID' in error_msg or 'No LID' in error_msg:
                            print(f"🔄 Erro de LID, tentando preparar novamente...")
                            prepare_success, _ = prepare_whatsapp_contact(candidate_number)
                            if prepare_success:
                                retry_response = requests.post(
                                    f"{WHATSAPP_API_URL}/send-text-to-contact",
                                    json={
                                        'contactId': contact_id_formatted,
                                        'text': message
                                    },
                                    timeout=45
                                )
                                if retry_response.status_code == 200:
                                    retry_result = retry_response.json()
                                    retry_delivered = retry_result.get('delivered', None)
                                    retry_ack = retry_result.get('ack', None)
                                    
                                    retry_is_delivered = False
                                    if retry_delivered is True:
                                        # Se delivered=True, verificar também ack >= 2
                                        if isinstance(retry_ack, int) and retry_ack >= 2:
                                            retry_is_delivered = True
                                        else:
                                            retry_is_delivered = False
                                    elif isinstance(retry_ack, int) and retry_ack >= 2:
                                        # ACK >= 2 = entregue (dois ticks)
                                        retry_is_delivered = True
                                    
                                    if retry_result.get('success', False) and retry_is_delivered:
                                        print(f"✅ Mensagem entregue após retry de preparação para {candidate_number}")
                                        return True, None
                    
                    # Se chegou aqui, não foi entregue (success pode ser True mas delivered=False/None ou ack < 1)
                    error_msg = result.get('error', 'Mensagem não confirmada como entregue')
                    last_error = f"Mensagem não entregue: delivered={delivered}, ack={ack}"
                    print(f"⚠️ Mensagem NÃO entregue para {candidate_number}")
                    print(f"   Detalhes: delivered={delivered}, ack={ack}, success={success}")
                    
                    # SEMPRE tentar próximo candidato se houver
                    if idx < len(all_valid_numbers) - 1:
                        next_candidate = all_valid_numbers[idx + 1]
                        print(f"🔄 Tentativa {idx + 1} não entregue, tentando próximo candidato: {next_candidate}")
                        time.sleep(1)
                        continue
                    else:
                        # Último candidato, não há mais opções
                        print(f"❌ Último candidato testado e não entregue")
                        break
                else:
                    error_msg = response.json().get('error', 'Erro desconhecido')
                    print(f"❌ Erro HTTP ao enviar mensagem para {candidate_number}: {error_msg}")
                    last_error = error_msg
                    
                    # Se houver mais candidatos, continuar tentando
                    if idx < len(all_valid_numbers) - 1:
                        print(f"🔄 Erro HTTP na primeira tentativa, tentando próximo candidato...")
                        time.sleep(1)  # Pequeno delay entre tentativas
                        continue
                    else:
                        # Último candidato, não há mais opções
                        break
            
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                print(f"❌ Exceção ao enviar para {candidate_number}: {error_msg}")
                last_error = error_msg
                
                # Se houver mais candidatos, continuar tentando
                if idx < len(all_valid_numbers) - 1:
                    print(f"🔄 Exceção na primeira tentativa, tentando próximo candidato...")
                    time.sleep(1)  # Pequeno delay entre tentativas
                    continue
                else:
                    # Último candidato, não há mais opções
                    break
        
        # Se chegou aqui, nenhum candidato funcionou
        print(f"\n{'='*60}")
        print(f"❌ FALHA: Nenhum candidato foi entregue com sucesso")
        print(f"   Candidatos testados: {len(all_valid_numbers)}")
        print(f"   Último erro: {last_error}")
        print(f"{'='*60}\n")
        return False, last_error or 'Falha ao enviar para todos os candidatos válidos'
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        print(f"❌ Exceção ao enviar mensagem: {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erro inesperado ao enviar mensagem: {error_msg}")
        return False, error_msg

def process_email(message):
    """
    Processa um e-mail: extrai informações, formata mensagem e salva no banco
    
    Args:
        message: Objeto de mensagem do Gmail API
        
    Returns:
        dict: Informações processadas
    """
    # Extrair metadados
    metadata = gmail_service.get_message_metadata(message)
    email_body = gmail_service.get_message_body(message)
    
    # Extrair informações do e-mail
    extracted_info = extract_email_info(email_body)
    
    # Log de debug para verificar extração
    print(f"📧 Informações extraídas: name={extracted_info.get('name')}, code={extracted_info.get('code')}, phone={extracted_info.get('phone')}, empresa={extracted_info.get('empresa')}, telefone_vendedor={extracted_info.get('telefone_vendedor')}")
    
    # Validar informações
    is_valid, missing = validate_extracted_info(extracted_info)
    if not is_valid:
        print(f"⚠️ E-mail inválido - campos faltando: {missing}")
        print(f"📧 Corpo do e-mail (primeiros 500 caracteres): {email_body[:500]}")
        return None
    
    # Formatar mensagem WhatsApp
    whatsapp_message = format_whatsapp_message(email_body, extracted_info)
    authorization_link = generate_authorization_link(extracted_info)
    
    # Salvar no banco de dados
    email_id = email_db.save_email(
        message_id=metadata.get('id'),
        thread_id=metadata.get('threadId'),
        subject=metadata.get('subject', ''),
        from_email=metadata.get('from', ''),
        date_received=metadata.get('date', datetime.now().isoformat()),
        email_body=email_body,
        extracted_info=extracted_info,
        whatsapp_message=whatsapp_message,
        authorization_link=authorization_link
    )
    
    return {
        'email_id': email_id,
        'message_id': metadata.get('id'),
        'extracted_info': extracted_info,
        'whatsapp_message': whatsapp_message,
        'authorization_link': authorization_link
    }

def monitor_emails():
    """
    Loop principal de monitoramento de e-mails
    """
    global monitor_running, last_check_time
    
    print("📧 Monitor de e-mails iniciado")
    
    while monitor_running:
        try:
            if not gmail_service.is_authenticated():
                print("⚠️ Gmail não autenticado. Aguardando autenticação...")
                time.sleep(60)
                continue
            
            # Atualizar timestamp ANTES de buscar (para evitar processar o mesmo e-mail duas vezes)
            current_check_time = datetime.now()
            
            # Buscar apenas e-mails novos desde a última verificação
            if last_check_time:
                print(f"🔍 Buscando e-mails desde: {last_check_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"🔍 Primeira verificação - buscando e-mails dos últimos 7 dias")
            
            new_messages = gmail_service.get_new_messages(last_check_time)
            
            # FILTRAR e-mails que já foram processados e enviados
            # Isso evita processar novamente e-mails que já foram enviados
            filtered_messages = []
            skipped_count = 0
            for msg in new_messages:
                msg_metadata = gmail_service.get_message_metadata(msg)
                msg_id = msg_metadata.get('id')
                
                # Verificar se já foi processado e enviado
                existing = email_db.get_email_by_message_id(msg_id)
                if existing and existing.get('enviado_whatsapp') == 1:
                    skipped_count += 1
                    continue
                
                filtered_messages.append(msg)
            
            new_messages = filtered_messages
            
            if new_messages:
                print(f"📬 {len(new_messages)} nova(s) mensagem(ns) encontrada(s) (após filtrar {skipped_count} já enviado(s))")
                print(f"⏱️ Simulação humana ativada:")
                print(f"   • Primeira mensagem: {HUMAN_DELAY_FIRST_MIN}-{HUMAN_DELAY_FIRST_MAX}s")
                print(f"   • Mensagens subsequentes: {HUMAN_DELAY_SUBSEQUENT_MIN}-{HUMAN_DELAY_SUBSEQUENT_MAX}s")
            else:
                if skipped_count > 0:
                    print(f"✅ Nenhum e-mail novo encontrado (todos os {skipped_count} e-mail(s) já foram enviados)")
                else:
                    print(f"✅ Nenhum e-mail novo encontrado")
            
            # Resetar contador de envios para esta verificação
            global email_send_count
            email_send_count = 0
            
            for message in new_messages:
                try:
                    # Obter metadata para verificar assunto e message_id
                    metadata = gmail_service.get_message_metadata(message)
                    message_id = metadata.get('id')
                    subject = metadata.get('subject', '').strip()
                    
                    # VERIFICAÇÃO INICIAL CRÍTICA: Verificar por message_id ANTES de qualquer processamento
                    # Isso evita processar o mesmo e-mail múltiplas vezes
                    existing_check = email_db.get_email_by_message_id(message_id)
                    if existing_check and existing_check.get('enviado_whatsapp') == 1:
                        print(f"⏭️ E-mail já enviado (verificação inicial) - ignorando: {message_id}")
                        print(f"   Assunto: {subject[:50]}...")
                        print(f"   Status no banco: enviado_whatsapp={existing_check.get('enviado_whatsapp')}, data_envio={existing_check.get('data_envio')}")
                        continue
                    
                    # Verificar se o assunto contém "Erro de Login Whatsapp"
                    if 'Erro de Login Whatsapp' not in subject:
                        print(f"⏭️ E-mail ignorado - assunto não corresponde: {subject[:50]}...")
                        continue
                    
                    # Usar lock para evitar processamento simultâneo
                    with processing_lock:
                        # Verificar se já está sendo processado
                        if message_id in emails_being_processed:
                            print(f"⏭️ E-mail já está sendo processado - ignorando: {message_id}")
                            continue
                        
                        # Verificar se o e-mail já foi processado e enviado
                        existing_email = email_db.get_email_by_message_id(message_id)
                        if existing_email:
                            if existing_email.get('enviado_whatsapp') == 1:
                                print(f"⏭️ E-mail já enviado anteriormente - ignorando: {message_id} (Assunto: {subject[:50]}...)")
                                continue
                        
                        # VERIFICAÇÃO PRINCIPAL: Extrair code e phone (telefone do cliente) para verificar duplicatas
                        # Chave de validação: code + phone (telefone do cliente)
                        email_body_preview = gmail_service.get_message_body(message)
                        extracted_info_preview = extract_email_info(email_body_preview)
                        code_preview = extracted_info_preview.get('code', '')
                        phone_preview = extracted_info_preview.get('phone', '')  # Telefone do cliente
                        
                        print(f"🔍 Verificando duplicata: code={code_preview}, phone={phone_preview} (telefone do cliente)")
                        
                        # Verificar se já foi enviado para este cliente + telefone do cliente
                        if code_preview and phone_preview:
                            already_sent = email_db.check_already_sent_by_client_and_phone(
                                code=code_preview,
                                phone=phone_preview,
                                exclude_message_id=message_id
                            )
                            
                            if already_sent:
                                print(f"⏭️ DUPLICATA: E-mail já enviado para code={code_preview}, phone={phone_preview} (telefone do cliente)")
                                print(f"   E-mail anterior: message_id={already_sent.get('message_id')}, data={already_sent.get('date_received')}")
                                continue
                            else:
                                print(f"✅ Nenhum e-mail duplicado encontrado para code={code_preview}, phone={phone_preview}")
                        else:
                            if not code_preview:
                                print(f"⚠️ Code não encontrado no e-mail, pulando verificação de duplicata")
                            if not phone_preview:
                                print(f"⚠️ Telefone do cliente não encontrado no e-mail, pulando verificação de duplicata")
                        
                        # Marcar como sendo processado
                        emails_being_processed.add(message_id)
                    
                    try:
                        # Verificar novamente ANTES de processar (double-check)
                        existing_email = email_db.get_email_by_message_id(message_id)
                        if existing_email and existing_email.get('enviado_whatsapp') == 1:
                            print(f"⏭️ E-mail foi enviado enquanto estava na fila - ignorando: {message_id}")
                            emails_being_processed.discard(message_id)
                            continue
                        
                        # Se já existe mas não foi enviado, verificar se outro e-mail do mesmo cliente + telefone do cliente já foi enviado
                        if existing_email:
                            existing_code = existing_email.get('code', '')
                            existing_phone = existing_email.get('phone', '')  # Telefone do cliente
                            
                            # VERIFICAÇÃO CRÍTICA: Verificar se está sendo processado/enviado (updated_at recente)
                            # Se o updated_at foi atualizado recentemente (últimos 5 minutos), significa que está sendo processado
                            if existing_email.get('updated_at'):
                                try:
                                    updated_at_str = existing_email.get('updated_at')
                                    if isinstance(updated_at_str, str):
                                        # Tentar parsear a data
                                        try:
                                            if 'T' in updated_at_str:
                                                updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                                            else:
                                                updated_at = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
                                        except:
                                            updated_at = None
                                    else:
                                        updated_at = None
                                    
                                    if updated_at:
                                        # Remover timezone se existir para comparação
                                        if updated_at.tzinfo:
                                            updated_at = updated_at.replace(tzinfo=None)
                                        
                                        time_diff = (datetime.now() - updated_at).total_seconds()
                                        if time_diff < 300:  # 5 minutos
                                            print(f"⏭️ E-mail está sendo processado/enviado (updated_at há {int(time_diff)}s) - ignorando: {message_id}")
                                            emails_being_processed.discard(message_id)
                                            continue
                                except Exception as e:
                                    print(f"⚠️ Erro ao verificar updated_at: {e}")
                            
                            if existing_code and existing_phone:
                                already_sent_existing = email_db.check_already_sent_by_client_and_phone(
                                    code=existing_code,
                                    phone=existing_phone,
                                    exclude_message_id=message_id
                                )
                                
                                if already_sent_existing:
                                    print(f"⏭️ DUPLICATA: E-mail já enviado para code={existing_code}, phone={existing_phone} (telefone do cliente)")
                                    print(f"   E-mail anterior: message_id={already_sent_existing.get('message_id')}")
                                    emails_being_processed.discard(message_id)
                                    continue
                            
                            # VERIFICAÇÃO CRÍTICA: Verificar se está sendo processado/enviado (updated_at recente)
                            # Se o updated_at foi atualizado recentemente (últimos 5 minutos), significa que está sendo processado
                            should_skip = False
                            if existing_email.get('updated_at'):
                                try:
                                    updated_at_str = existing_email.get('updated_at')
                                    if isinstance(updated_at_str, str):
                                        # Tentar parsear a data
                                        try:
                                            if 'T' in updated_at_str:
                                                updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                                            else:
                                                updated_at = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
                                        except:
                                            updated_at = None
                                    else:
                                        updated_at = None
                                    
                                    if updated_at:
                                        # Remover timezone se existir para comparação
                                        if updated_at.tzinfo:
                                            updated_at = updated_at.replace(tzinfo=None)
                                        
                                        time_diff = (datetime.now() - updated_at).total_seconds()
                                        if time_diff < 300:  # 5 minutos
                                            print(f"⏭️ E-mail está sendo processado/enviado (updated_at há {int(time_diff)}s) - ignorando: {message_id}")
                                            emails_being_processed.discard(message_id)
                                            should_skip = True
                                except Exception as e:
                                    print(f"⚠️ Erro ao verificar updated_at: {e}")
                            
                            if should_skip:
                                continue
                            
                            print(f"🔄 E-mail já processado mas não enviado - tentando enviar novamente: {message_id}")
                            contact_id = existing_email.get('telefone_vendedor')
                            whatsapp_msg = existing_email.get('whatsapp_message')
                            
                            if contact_id and whatsapp_msg:
                                # Marcar como "enviando" no banco ANTES de qualquer verificação (para evitar envios simultâneos)
                                # Isso cria uma "reserva" no banco indicando que este e-mail está sendo enviado
                                email_db.mark_as_processing(message_id)
                                
                                # VERIFICAÇÃO ULTRA-RIGOROSA: Verificar UMA ÚLTIMA VEZ por code + phone ANTES de enviar
                                existing_code_final = existing_email.get('code', '')
                                existing_phone_final = existing_email.get('phone', '')  # Telefone do cliente
                                
                                if existing_code_final and existing_phone_final:
                                    ultra_final_check = email_db.check_already_sent_by_client_and_phone(
                                        code=existing_code_final,
                                        phone=existing_phone_final,
                                        exclude_message_id=message_id
                                    )
                                    
                                    if ultra_final_check:
                                        print(f"⏭️ DUPLICATA (verificação ultra-final): E-mail já enviado para code={existing_code_final}, phone={existing_phone_final}")
                                        emails_being_processed.discard(message_id)
                                        continue
                                
                                # Aplicar delay de simulação humana (apenas para mensagens subsequentes)
                                if email_send_count > 0:
                                    delay = get_human_delay(is_first_message=False)
                                    print(f"⏳ Aguardando {delay}s (simulação humana - mensagem subsequente)...")
                                    time.sleep(delay)
                                
                                print(f"📤 Enviando para WhatsApp: {contact_id}")
                                success, error = send_to_whatsapp(contact_id, whatsapp_msg)
                                email_send_count += 1
                                
                                if success:
                                    # Marcar como enviado IMEDIATAMENTE após sucesso
                                    email_db.mark_as_sent(message_id, success=True)
                                    
                                    # VERIFICAÇÃO FINAL: Confirmar que foi marcado como enviado
                                    verification = email_db.get_email_by_message_id(message_id)
                                    if verification and verification.get('enviado_whatsapp') == 1:
                                        print(f"✅ E-mail enviado com sucesso para {contact_id}")
                                        print(f"   ✅ Confirmado no banco: message_id={message_id}, enviado_whatsapp={verification.get('enviado_whatsapp')}")
                                    else:
                                        print(f"⚠️ ATENÇÃO: E-mail enviado mas não confirmado no banco!")
                                        print(f"   message_id={message_id}, verification={verification}")
                                else:
                                    email_db.mark_as_sent(message_id, success=False, error=error)
                                    print(f"❌ Erro ao enviar: {error}")
                            else:
                                print(f"⚠️ E-mail existente sem dados completos - reprocessando...")
                                # Reprocessar se não tiver dados completos
                                processed = process_email(message)
                                if processed:
                                    # Verificar se já foi enviado para este cliente + telefone do cliente ANTES de enviar
                                    reprocessed_code = processed['extracted_info'].get('code', '')
                                    reprocessed_phone = processed['extracted_info'].get('phone', '')  # Telefone do cliente
                                    
                                    if reprocessed_code and reprocessed_phone:
                                        already_sent_reprocessed = email_db.check_already_sent_by_client_and_phone(
                                            code=reprocessed_code,
                                            phone=reprocessed_phone,
                                            exclude_message_id=processed['message_id']
                                        )
                                        
                                        if already_sent_reprocessed:
                                            print(f"⏭️ DUPLICATA (reprocessamento): E-mail já enviado para code={reprocessed_code}, phone={reprocessed_phone} (telefone do cliente)")
                                            print(f"   E-mail anterior: message_id={already_sent_reprocessed.get('message_id')}")
                                            emails_being_processed.discard(message_id)
                                            continue
                                    
                                    # VERIFICAÇÃO ULTRA-RIGOROSA: Verificar UMA ÚLTIMA VEZ por code + phone ANTES de enviar
                                    if reprocessed_code and reprocessed_phone:
                                        ultra_final_reprocessed = email_db.check_already_sent_by_client_and_phone(
                                            code=reprocessed_code,
                                            phone=reprocessed_phone,
                                            exclude_message_id=processed['message_id']
                                        )
                                        
                                        if ultra_final_reprocessed:
                                            print(f"⏭️ DUPLICATA (verificação ultra-final - reprocessamento): E-mail já enviado para code={reprocessed_code}, phone={reprocessed_phone}")
                                            emails_being_processed.discard(message_id)
                                            continue
                                    
                                    # Marcar como "enviando" no banco ANTES de enviar
                                    email_db.mark_as_processing(processed['message_id'])
                                    
                                    contact_id = processed['extracted_info'].get('telefone_vendedor')
                                    whatsapp_msg = processed['whatsapp_message']
                                    
                                    # Aplicar delay de simulação humana (apenas para mensagens subsequentes)
                                    if email_send_count > 0:
                                        delay = get_human_delay(is_first_message=False)
                                        print(f"⏳ Aguardando {delay}s (simulação humana - mensagem subsequente)...")
                                        time.sleep(delay)
                                    
                                    print(f"📤 Enviando para WhatsApp: {contact_id}")
                                    success, error = send_to_whatsapp(contact_id, whatsapp_msg)
                                    email_send_count += 1
                                    
                                    if success:
                                        # Marcar como enviado IMEDIATAMENTE após sucesso
                                        email_db.mark_as_sent(processed['message_id'], success=True)
                                        
                                        # VERIFICAÇÃO FINAL: Confirmar que foi marcado como enviado
                                        verification = email_db.get_email_by_message_id(processed['message_id'])
                                        if verification and verification.get('enviado_whatsapp') == 1:
                                            print(f"✅ E-mail enviado com sucesso para {contact_id}")
                                            print(f"   ✅ Confirmado no banco: message_id={processed['message_id']}, enviado_whatsapp={verification.get('enviado_whatsapp')}")
                                        else:
                                            print(f"⚠️ ATENÇÃO: E-mail enviado mas não confirmado no banco!")
                                            print(f"   message_id={processed['message_id']}, verification={verification}")
                                    else:
                                        email_db.mark_as_sent(processed['message_id'], success=False, error=error)
                                        print(f"❌ Erro ao enviar: {error}")
                        else:
                            # Processar e-mail novo
                            processed = process_email(message)
                            
                            if processed:
                                # Marcar como processando IMEDIATAMENTE após salvar no banco
                                # Isso ajuda outras threads a identificar que este e-mail está sendo processado
                                email_db.mark_as_processing(processed['message_id'])
                                
                                # Verificar NOVAMENTE antes de enviar (triple-check por message_id)
                                final_check = email_db.get_email_by_message_id(processed['message_id'])
                                if final_check and final_check.get('enviado_whatsapp') == 1:
                                    print(f"⏭️ E-mail foi enviado durante o processamento - ignorando: {processed['message_id']}")
                                    emails_being_processed.discard(message_id)
                                    continue
                                
                                # VERIFICAÇÃO CRÍTICA: Verificar por code + phone (telefone do cliente) ANTES de enviar
                                processed_code = processed['extracted_info'].get('code', '')
                                processed_phone = processed['extracted_info'].get('phone', '')  # Telefone do cliente
                                
                                if processed_code and processed_phone:
                                    already_sent_client = email_db.check_already_sent_by_client_and_phone(
                                        code=processed_code,
                                        phone=processed_phone,
                                        exclude_message_id=processed['message_id']
                                    )
                                    
                                    if already_sent_client:
                                        print(f"⏭️ DUPLICATA: E-mail já enviado para code={processed_code}, phone={processed_phone} (telefone do cliente)")
                                        print(f"   E-mail anterior: message_id={already_sent_client.get('message_id')}")
                                        emails_being_processed.discard(message_id)
                                        continue
                                
                                # VERIFICAÇÃO FINAL: Verificar novamente por code + phone ANTES de enviar
                                # (pode ter sido salvo enquanto estava processando)
                                if processed_code and processed_phone:
                                    final_client_check = email_db.check_already_sent_by_client_and_phone(
                                        code=processed_code,
                                        phone=processed_phone,
                                        exclude_message_id=processed['message_id']
                                    )
                                    
                                    if final_client_check:
                                        print(f"⏭️ DUPLICATA (verificação final): E-mail já enviado para code={processed_code}, phone={processed_phone} (telefone do cliente)")
                                        print(f"   E-mail anterior: message_id={final_client_check.get('message_id')}")
                                        emails_being_processed.discard(message_id)
                                        continue
                                
                                # VERIFICAÇÃO ULTRA-RIGOROSA: Verificar UMA ÚLTIMA VEZ por code + phone ANTES de enviar
                                # Isso evita que dois e-mails sejam enviados simultaneamente
                                if processed_code and processed_phone:
                                    ultra_final_check = email_db.check_already_sent_by_client_and_phone(
                                        code=processed_code,
                                        phone=processed_phone,
                                        exclude_message_id=processed['message_id']
                                    )
                                    
                                    if ultra_final_check:
                                        print(f"⏭️ DUPLICATA (verificação ultra-final): E-mail já enviado para code={processed_code}, phone={processed_phone}")
                                        print(f"   E-mail anterior: message_id={ultra_final_check.get('message_id')}")
                                        emails_being_processed.discard(message_id)
                                        continue
                                
                                # Marcar como "enviando" no banco ANTES de enviar (para evitar envios simultâneos)
                                # Isso cria uma "reserva" no banco indicando que este e-mail está sendo enviado
                                email_db.mark_as_processing(processed['message_id'])
                                
                                # Enviar para WhatsApp
                                contact_id = processed['extracted_info'].get('telefone_vendedor')
                                whatsapp_msg = processed['whatsapp_message']
                                
                                # Aplicar delay de simulação humana (apenas para mensagens subsequentes)
                                if email_send_count > 0:
                                    delay = get_human_delay(is_first_message=False)
                                    print(f"⏳ Aguardando {delay}s (simulação humana - mensagem subsequente)...")
                                    time.sleep(delay)
                                else:
                                    print(f"📤 Primeira mensagem - sem delay (simulação humana)")
                                
                                print(f"📤 Enviando para WhatsApp: {contact_id}")
                                success, error = send_to_whatsapp(contact_id, whatsapp_msg)
                                email_send_count += 1
                                
                                if success:
                                    # Marcar como enviado IMEDIATAMENTE após sucesso
                                    email_db.mark_as_sent(processed['message_id'], success=True)
                                    
                                    # VERIFICAÇÃO FINAL: Confirmar que foi marcado como enviado
                                    verification = email_db.get_email_by_message_id(processed['message_id'])
                                    if verification and verification.get('enviado_whatsapp') == 1:
                                        print(f"✅ E-mail enviado com sucesso para {contact_id}")
                                        print(f"   ✅ Confirmado no banco: message_id={processed['message_id']}, enviado_whatsapp={verification.get('enviado_whatsapp')}")
                                    else:
                                        print(f"⚠️ ATENÇÃO: E-mail enviado mas não confirmado no banco!")
                                        print(f"   message_id={processed['message_id']}, verification={verification}")
                                else:
                                    email_db.mark_as_sent(processed['message_id'], success=False, error=error)
                                    print(f"❌ Erro ao enviar: {error}")
                    finally:
                        # Sempre remover do set de processamento, mesmo em caso de erro
                        emails_being_processed.discard(message_id)
                
                except Exception as e:
                    print(f"❌ Erro ao processar e-mail: {e}")
                    # Garantir que remove do set mesmo em caso de erro
                    try:
                        metadata = gmail_service.get_message_metadata(message)
                        message_id = metadata.get('id')
                        emails_being_processed.discard(message_id)
                    except:
                        pass
                    continue
            
            # Atualizar timestamp da última verificação
            last_check_time = current_check_time
            print(f"✅ Verificação concluída. Próxima verificação em {CHECK_INTERVAL} segundos...")
            
            # Aguardar antes da próxima verificação
            time.sleep(CHECK_INTERVAL)
        
        except Exception as e:
            print(f"❌ Erro no monitor: {e}")
            time.sleep(60)

@app.route('/gmail/connect', methods=['POST'])
def connect_gmail():
    """Inicia processo de autenticação Gmail"""
    try:
        # Verificar se credentials.json existe
        if not os.path.exists('credentials.json'):
            return jsonify({
                'success': False,
                'error': 'Arquivo credentials.json não encontrado. Por favor, baixe o arquivo do Google Cloud Console e salve como credentials.json na raiz do projeto. Veja README_GMAIL_MONITOR.md para instruções detalhadas.'
            }), 404
        
        print("Iniciando autenticação Gmail...")
        success = gmail_service.authenticate()
        
        if success:
            print("Autenticação bem-sucedida, obtendo perfil...")
            profile = gmail_service.get_profile()
            email = profile.get('emailAddress', '') if profile else ''
            
            print(f"Gmail conectado: {email}")
            return jsonify({
                'success': True,
                'message': 'Gmail conectado com sucesso',
                'email': email
            })
        else:
            print("Falha na autenticação")
            return jsonify({
                'success': False,
                'error': 'Falha na autenticação. Verifique se o arquivo credentials.json está correto e se a Gmail API está habilitada no Google Cloud Console.'
            }), 500
    except FileNotFoundError as e:
        error_msg = str(e)
        print(f"Erro FileNotFoundError: {error_msg}")
        return jsonify({
            'success': False,
            'error': f'Arquivo não encontrado: {error_msg}'
        }), 404
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = str(e)
        print(f"Erro ao conectar Gmail:")
        print(error_details)
        return jsonify({
            'success': False,
            'error': f'Erro ao conectar: {error_msg}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'ok',
        'service': 'Gmail Monitor API',
        'port': GMAIL_MONITOR_PORT
    })

@app.route('/gmail/status', methods=['GET'])
def gmail_status():
    """Retorna status da conexão Gmail"""
    is_authenticated = gmail_service.is_authenticated()
    email = None
    
    if is_authenticated:
        profile = gmail_service.get_profile()
        email = profile.get('emailAddress', '') if profile else ''
    
    return jsonify({
        'authenticated': is_authenticated,
        'email': email
    })

@app.route('/gmail/start-monitor', methods=['POST'])
def start_monitor():
    """Inicia monitoramento de e-mails"""
    global monitor_thread, monitor_running
    
    if not gmail_service.is_authenticated():
        return jsonify({
            'success': False,
            'error': 'Gmail não está autenticado'
        }), 400
    
    if monitor_running:
        return jsonify({
            'success': False,
            'error': 'Monitor já está em execução'
        })
    
    # Obter intervalo do request (se fornecido)
    data = request.get_json() or {}
    interval = data.get('interval', CHECK_INTERVAL)
    
    monitor_running = True
    monitor_thread = threading.Thread(target=monitor_emails, daemon=True)
    monitor_thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Monitor iniciado',
        'interval': interval
    })

@app.route('/gmail/stop-monitor', methods=['POST'])
def stop_monitor():
    """Para monitoramento de e-mails"""
    global monitor_running
    
    monitor_running = False
    
    return jsonify({
        'success': True,
        'message': 'Monitor parado'
    })

@app.route('/gmail/monitor-status', methods=['GET'])
def monitor_status():
    """Retorna status do monitor"""
    global last_check_time
    
    stats = email_db.get_statistics()
    
    return jsonify({
        'running': monitor_running,
        'last_check': last_check_time.isoformat() if last_check_time else None,
        'statistics': stats
    })

@app.route('/gmail/pending-emails', methods=['GET'])
def get_pending_emails():
    """Retorna lista de e-mails pendentes"""
    pending = email_db.get_pending_emails()
    
    # Converter para formato JSON serializável
    for email in pending:
        for key, value in email.items():
            if isinstance(value, (int, float)) and value is None:
                email[key] = None
    
    return jsonify({
        'success': True,
        'count': len(pending),
        'emails': pending
    })

@app.route('/gmail/process-pending', methods=['POST'])
def process_pending():
    """Processa e-mails pendentes"""
    pending = email_db.get_pending_emails()
    
    results = {
        'success': [],
        'failed': [],
        'total': len(pending)
    }
    
    for email in pending:
        try:
            contact_id = email.get('telefone_vendedor')
            whatsapp_msg = email.get('whatsapp_message')
            
            if not contact_id or not whatsapp_msg:
                results['failed'].append({
                    'message_id': email.get('message_id'),
                    'error': 'Dados incompletos'
                })
                continue
            
            # Enviar para WhatsApp
            success, error = send_to_whatsapp(contact_id, whatsapp_msg)
            
            if success:
                email_db.mark_as_sent(email.get('message_id'), success=True)
                results['success'].append({
                    'message_id': email.get('message_id'),
                    'contact_id': contact_id
                })
            else:
                email_db.mark_as_sent(email.get('message_id'), success=False, error=error)
                results['failed'].append({
                    'message_id': email.get('message_id'),
                    'error': error
                })
        
        except Exception as e:
            results['failed'].append({
                'message_id': email.get('message_id'),
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'results': results
    })

@app.route('/gmail/clean-pending', methods=['POST'])
def clean_pending_emails():
    """Limpa e-mails pendentes que não existem mais no Gmail"""
    if not gmail_service.is_authenticated():
        return jsonify({
            'success': False,
            'error': 'Gmail não está autenticado'
        }), 400
    
    pending = email_db.get_pending_emails()
    
    results = {
        'checked': 0,
        'removed': 0,
        'exists': 0,
        'errors': 0,
        'removed_ids': []
    }
    
    print(f"🔍 Verificando {len(pending)} e-mail(s) pendente(s)...")
    
    for email in pending:
        try:
            message_id = email.get('message_id')
            if not message_id:
                continue
            
            results['checked'] += 1
            
            # Verificar se o e-mail ainda existe no Gmail
            message = gmail_service.get_message(message_id)
            
            if message is None:
                # E-mail não existe mais no Gmail, remover do banco
                deleted = email_db.delete_email(message_id)
                if deleted:
                    results['removed'] += 1
                    results['removed_ids'].append(message_id)
                    print(f"🗑️ E-mail removido (não existe no Gmail): {message_id}")
            else:
                # E-mail ainda existe
                results['exists'] += 1
        
        except Exception as e:
            results['errors'] += 1
            print(f"❌ Erro ao verificar e-mail {email.get('message_id', 'unknown')}: {e}")
            continue
    
    print(f"✅ Limpeza concluída: {results['removed']} removido(s), {results['exists']} ainda existe(m)")
    
    return jsonify({
        'success': True,
        'message': f'Limpeza concluída: {results["removed"]} e-mail(s) removido(s)',
        'results': results
    })

@app.route('/gmail/delete-all-pending', methods=['POST'])
def delete_all_pending():
    """Deleta todos os e-mails pendentes do banco de dados"""
    try:
        deleted_count = email_db.delete_all_pending_emails()
        
        print(f"🗑️ Limpeza de e-mails pendentes: {deleted_count} e-mail(s) deletado(s)")
        
        return jsonify({
            'success': True,
            'message': f'{deleted_count} e-mail(s) pendente(s) deletado(s) com sucesso',
            'deleted_count': deleted_count
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = str(e)
        print(f"❌ Erro ao deletar e-mails pendentes:")
        print(error_details)
        return jsonify({
            'success': False,
            'error': f'Erro ao deletar e-mails pendentes: {error_msg}'
        }), 500

@app.route('/gmail/history', methods=['GET'])
def get_history():
    """Retorna histórico de e-mails"""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    emails = email_db.get_all_emails(limit=limit, offset=offset)
    
    # Converter para formato JSON serializável
    for email in emails:
        for key, value in email.items():
            if isinstance(value, (int, float)) and value is None:
                email[key] = None
    
    return jsonify({
        'success': True,
        'count': len(emails),
        'emails': emails
    })

@app.route('/gmail/test-email', methods=['POST'])
def test_email():
    """Testa processamento de e-mail com texto fornecido"""
    data = request.get_json()
    email_body = data.get('email_body', '')
    
    if not email_body:
        return jsonify({
            'success': False,
            'error': 'Corpo do e-mail não fornecido'
        }), 400
    
    # Extrair informações
    extracted_info = extract_email_info(email_body)
    whatsapp_message = format_whatsapp_message(email_body, extracted_info)
    authorization_link = generate_authorization_link(extracted_info)
    
    return jsonify({
        'success': True,
        'extracted_info': extracted_info,
        'whatsapp_message': whatsapp_message,
        'authorization_link': authorization_link
    })

def auto_connect_and_start():
    """
    Conecta automaticamente ao Gmail e inicia o monitoramento
    """
    print("\n" + "="*60)
    print("🔐 Tentando conectar automaticamente ao Gmail...")
    print("="*60)
    
    # Tentar autenticar se já tiver token
    if os.path.exists('token.json'):
        try:
            authenticated = gmail_service.authenticate()
            if authenticated:
                print("✅ Gmail conectado automaticamente!")
                
                # Iniciar monitoramento automaticamente
                global monitor_thread, monitor_running
                if not monitor_running:
                    print("📧 Iniciando monitoramento automaticamente...")
                    monitor_running = True
                    monitor_thread = threading.Thread(target=monitor_emails, daemon=True)
                    monitor_thread.start()
                    print("✅ Monitoramento iniciado automaticamente!")
                else:
                    print("ℹ️ Monitoramento já está em execução")
            else:
                print("⚠️ Não foi possível conectar automaticamente. Use o botão 'Conectar Gmail' na interface.")
        except Exception as e:
            print(f"⚠️ Erro ao conectar automaticamente: {e}")
            print("ℹ️ Use o botão 'Conectar Gmail' na interface para autenticar.")
    else:
        print("ℹ️ Token não encontrado. Use o botão 'Conectar Gmail' na interface para autenticar pela primeira vez.")
    
    print("="*60 + "\n")

if __name__ == '__main__':
    print("🚀 Iniciando servidor Gmail Monitor API...")
    print(f"📧 Porta: {GMAIL_MONITOR_PORT}")
    print(f"📱 WhatsApp API: {WHATSAPP_API_URL}")
    print(f"🌐 URL: http://localhost:{GMAIL_MONITOR_PORT}")
    
    # Tentar conectar automaticamente e iniciar monitoramento
    auto_connect_and_start()
    
    app.run(host='0.0.0.0', port=GMAIL_MONITOR_PORT, debug=True)

