#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Processador de E-mails - Extrai informações do corpo do e-mail
"""
import re
from urllib.parse import quote

def extract_email_info(email_body):
    """
    Extrai informações do corpo do e-mail e formata para WhatsApp
    
    Args:
        email_body: Texto completo do corpo do e-mail
        
    Returns:
        dict: Dicionário com informações extraídas
    """
    result = {
        'vendedor_nome_completo': '',
        'vendedor_primeiro_nome': '',
        'name': '',  # Patiocanoagrill
        'code': '',  # 3051288
        'phone': '',  # 8897797542
        'empresa': '',  # PATIO GRILL
        'cnpj': '',  # 27.765.542/0001-01
        'telefone_formatado': '',  # (88) 9779-7542
        'telefone_vendedor': ''  # Telefone do vendedor para envio WhatsApp
    }
    
    # 1. Extrair nome do vendedor (primeira linha após "Prezado,")
    vendedor_match = re.search(r'Prezado,\s*([A-ZÁÉÍÓÚÇÃÕÂÊÔ\s]+)', email_body, re.IGNORECASE)
    if vendedor_match:
        nome_completo = vendedor_match.group(1).strip()
        result['vendedor_nome_completo'] = nome_completo
        # Pegar apenas o primeiro nome
        primeiro_nome = nome_completo.split()[0] if nome_completo.split() else nome_completo
        result['vendedor_primeiro_nome'] = primeiro_nome
    
    # 2. Extrair "name" (Patiocanoagrill) - vem de "O(A) Patiocanoagrill Cliente:"
    # Capturar tudo que está entre "O(A)" e "Cliente:"
    name_match = re.search(r'O\(A\)\s+(.*?)\s+Cliente:', email_body, re.IGNORECASE | re.DOTALL)
    
    if name_match:
        extracted_name = name_match.group(1).strip()
        # Se estiver vazio ou contiver apenas espaços, usar "-"
        if not extracted_name or extracted_name == '':
            result['name'] = '-'
        else:
            # Limitar tamanho e remover quebras de linha
            extracted_name = extracted_name.replace('\n', ' ').replace('\r', ' ').strip()
            if len(extracted_name) > 100:
                extracted_name = extracted_name[:100]
            result['name'] = extracted_name
    else:
        # Se não encontrar o padrão, usar "-"
        result['name'] = '-'
    
    # 3. Extrair "empresa" (PATIO GRILL) - vem de "Cliente: PATIO GRILL"
    empresa_match = re.search(r'Cliente:\s*([^-]+?)\s*-\s*CNPJ:', email_body, re.IGNORECASE)
    if empresa_match:
        result['empresa'] = empresa_match.group(1).strip()
    
    # 4. Extrair CNPJ
    cnpj_match = re.search(r'CNPJ:\s*([0-9./-]+)', email_body)
    if cnpj_match:
        result['cnpj'] = cnpj_match.group(1).strip()
    
    # 5. Extrair "code" (código do cliente) - vem de "Cod Cliente: 3051288"
    code_match = re.search(r'Cod\s+Cliente:\s*(\d+)', email_body, re.IGNORECASE)
    if code_match:
        result['code'] = code_match.group(1).strip()
    
    # 6. Extrair telefone utilizado - vem de "Telefone utilizado: (88) 9779-7542"
    telefone_match = re.search(r'Telefone\s+utilizado:\s*\(?(\d{2})\)?\s*(\d{4,5})-?(\d{4})', email_body, re.IGNORECASE)
    if telefone_match:
        ddd = telefone_match.group(1)
        parte1 = telefone_match.group(2)
        parte2 = telefone_match.group(3)
        # Formatar telefone completo (sem espaços, parênteses, hífens)
        result['phone'] = f"{ddd}{parte1}{parte2}"
        # Telefone formatado para exibição
        result['telefone_formatado'] = f"({ddd}) {parte1}-{parte2}"
    
    # 7. Extrair telefone do vendedor - vem de "Telefone do Vendedor: (85) 98162-2927"
    telefone_vendedor_match = re.search(r'Telefone\s+do\s+Vendedor:\s*\(?(\d{2})\)?\s*(\d{4,5})-?(\d{4})', email_body, re.IGNORECASE)
    if telefone_vendedor_match:
        ddd_v = telefone_vendedor_match.group(1)
        parte1_v = telefone_vendedor_match.group(2)
        parte2_v = telefone_vendedor_match.group(3)
        # Formatar para WhatsApp: 55 + DDD + número (sem formatação)
        result['telefone_vendedor'] = f"55{ddd_v}{parte1_v}{parte2_v}"
    
    return result

def format_whatsapp_message(email_body, extracted_info):
    """
    Formata a mensagem para WhatsApp
    
    Args:
        email_body: Texto original do e-mail
        extracted_info: Dicionário com informações extraídas
        
    Returns:
        str: Mensagem formatada para WhatsApp
    """
    vendedor = extracted_info.get('vendedor_primeiro_nome', '')
    name = extracted_info.get('name', '-')
    code = extracted_info.get('code', '')
    empresa = extracted_info.get('empresa', '')
    cnpj = extracted_info.get('cnpj', '')
    telefone = extracted_info.get('telefone_formatado', '')
    
    # Se name for "-", formatar mensagem sem mencionar o name
    if name == '-':
        mensagem = f"""Prezado, {vendedor}

Tentou acessar a conta do Cliente: {code} - {empresa} - CNPJ: {cnpj} na Assistente Virtual WhatsApp com o telefone {telefone} porém esse telefone não está cadastrado no sistema.

Clique no Link Abaixo para autorizar ou recusar o Acesso desse cliente com esse número.

{generate_authorization_link(extracted_info)}"""
    else:
        mensagem = f"""Prezado, {vendedor}

O(A) {name}, tentou acessar a conta do Cliente: {code} - {empresa} - CNPJ: {cnpj} na Assistente Virtual WhatsApp com o telefone {telefone} porém esse telefone não está cadastrado no sistema.

Clique no Link Abaixo para autorizar ou recusar o Acesso desse cliente com esse número.

{generate_authorization_link(extracted_info)}"""
    
    return mensagem

def generate_authorization_link(extracted_info):
    """
    Gera o link de autorização com as variáveis formatadas
    
    Args:
        extracted_info: Dicionário com informações extraídas
        
    Returns:
        str: Link de autorização formatado
    """
    base_url = "https://script.google.com/macros/s/AKfycbzeo4Q6HwuzOfAYQZfUoYBlFxH1CqKQrvi3LAysYrO5gusBu4w1LoPzopxj71L210Sn/exec"
    
    # Formatar variáveis
    name = extracted_info.get('name', '-')
    # Se name estiver vazio, usar "-"
    if not name or name == '':
        name = '-'
    name_encoded = quote(name)  # URL encode (espaços viram %20)
    code = extracted_info.get('code', '')
    phone = extracted_info.get('phone', '')  # Já está sem formatação
    empresa = quote(extracted_info.get('empresa', ''))  # URL encode
    
    link = f"{base_url}?name={name_encoded}&code={code}&phone={phone}&empresa={empresa}"
    
    return link

def validate_extracted_info(info):
    """
    Valida se todas as informações necessárias foram extraídas
    
    Args:
        info: Dicionário com informações extraídas
        
    Returns:
        tuple: (bool, list) - (é válido, lista de campos faltando)
    """
    # Campos obrigatórios para envio (name é opcional - terá valor padrão)
    required_fields = ['code', 'phone', 'empresa', 'telefone_vendedor']
    missing = [field for field in required_fields if not info.get(field)]
    
    # Se 'name' não foi encontrado ou está vazio, usar "-"
    if not info.get('name') or info.get('name') == '':
        info['name'] = '-'  # Valor padrão
    
    if missing:
        return False, missing
    
    return True, []

def clean_phone_number(phone_text):
    """
    Remove todos os caracteres não numéricos do telefone
    
    Args:
        phone_text: Texto com telefone formatado
        
    Returns:
        str: Telefone apenas com números
    """
    return re.sub(r'[^\d]', '', phone_text)

