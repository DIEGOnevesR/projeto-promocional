#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Serviço de Integração com Gmail API
"""
import os
import base64
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Escopos necessários para acessar Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """
        Inicializa o serviço Gmail
        
        Args:
            credentials_file: Arquivo de credenciais OAuth2
            token_file: Arquivo para salvar token de acesso
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.creds = None
        
        # Criar credentials.json a partir de variáveis de ambiente se não existir
        self._create_credentials_from_env()
    
    def authenticate(self):
        """
        Autentica e obtém credenciais do Gmail
        
        Returns:
            bool: True se autenticado com sucesso
        """
        # Verificar se já existe token salvo
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        elif os.environ.get('GMAIL_REFRESH_TOKEN'):
            # Criar credenciais a partir de refresh token em variável de ambiente
            try:
                client_id = os.environ.get('GMAIL_CLIENT_ID')
                client_secret = os.environ.get('GMAIL_CLIENT_SECRET')
                refresh_token = os.environ.get('GMAIL_REFRESH_TOKEN')
                
                if client_id and client_secret and refresh_token:
                    self.creds = Credentials(
                        token=None,
                        refresh_token=refresh_token,
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=client_id,
                        client_secret=client_secret,
                        scopes=SCOPES
                    )
                    # Tentar obter novo token
                    try:
                        self.creds.refresh(Request())
                    except Exception as e:
                        print(f"Erro ao renovar token inicial: {e}")
            except Exception as e:
                print(f"Erro ao criar credenciais a partir de variáveis de ambiente: {e}")
        
        # Se não há credenciais válidas, solicitar autorização
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Renovar token expirado
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Erro ao renovar token: {e}")
                    return False
            else:
                # Fazer fluxo de autenticação OAuth2
                if not os.path.exists(self.credentials_file):
                    # Tentar criar novamente a partir de variáveis de ambiente
                    self._create_credentials_from_env()
                    
                    if not os.path.exists(self.credentials_file):
                        raise FileNotFoundError(
                            f"Arquivo de credenciais não encontrado: {self.credentials_file}\n"
                            "Por favor, configure as variáveis de ambiente GMAIL_CLIENT_ID e GMAIL_CLIENT_SECRET\n"
                            "ou baixe o arquivo credentials.json do Google Cloud Console"
                        )
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    
                    # Em produção (Render), usar run_console em vez de run_local_server
                    if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER'):
                        # Em produção, retornar URL de autorização
                        auth_url, _ = flow.authorization_url(prompt='consent')
                        raise Exception(
                            f"Autenticação OAuth2 necessária. "
                            f"Por favor, visite esta URL para autorizar: {auth_url}\n"
                            f"Depois, configure o token via variável de ambiente GMAIL_REFRESH_TOKEN"
                        )
                    else:
                        # Em desenvolvimento, usar servidor local
                        self.creds = flow.run_local_server(
                            port=0,
                            open_browser=True,
                            authorization_prompt_message='Por favor, visite esta URL para autorizar o acesso:',
                            success_message='Autenticação bem-sucedida! Você pode fechar esta janela.'
                        )
                except Exception as e:
                    print(f"Erro durante autenticação OAuth2: {e}")
                    raise Exception(f"Erro na autenticação OAuth2: {str(e)}. Certifique-se de que o arquivo credentials.json está correto e que a Gmail API está habilitada no Google Cloud Console.")
            
            # Salvar credenciais para próxima vez
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
        
        # Construir serviço Gmail
        try:
            self.service = build('gmail', 'v1', credentials=self.creds)
            return True
        except HttpError as error:
            print(f'Erro ao construir serviço Gmail: {error}')
            return False
    
    def _create_credentials_from_env(self):
        """Cria credentials.json a partir de variáveis de ambiente se não existir"""
        if os.path.exists(self.credentials_file):
            return  # Arquivo já existe
        
        # Tentar criar a partir de variáveis de ambiente
        client_id = os.environ.get('GMAIL_CLIENT_ID')
        client_secret = os.environ.get('GMAIL_CLIENT_SECRET')
        project_id = os.environ.get('GMAIL_PROJECT_ID', 'gmail-monitor')
        
        if client_id and client_secret:
            credentials_data = {
                "installed": {
                    "client_id": client_id,
                    "project_id": project_id,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": client_secret,
                    "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"]
                }
            }
            
            try:
                with open(self.credentials_file, 'w') as f:
                    json.dump(credentials_data, f, indent=2)
                print(f"✓ Arquivo credentials.json criado a partir de variáveis de ambiente")
            except Exception as e:
                print(f"⚠ Erro ao criar credentials.json: {e}")
    
    def is_authenticated(self):
        """Verifica se está autenticado"""
        return self.service is not None and self.creds is not None
    
    def get_profile(self):
        """
        Obtém informações do perfil do Gmail
        
        Returns:
            dict: Informações do perfil (email, etc)
        """
        if not self.is_authenticated():
            return None
        
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile
        except HttpError as error:
            print(f'Erro ao obter perfil: {error}')
            return None
    
    def list_messages(self, query='', max_results=10, after_date=None):
        """
        Lista mensagens do Gmail
        
        Args:
            query: Query de busca (ex: 'from:example@gmail.com')
            max_results: Número máximo de resultados
            after_date: Data mínima (datetime object)
            
        Returns:
            list: Lista de IDs de mensagens
        """
        if not self.is_authenticated():
            return []
        
        try:
            # Construir query
            search_query = query
            if after_date:
                # Usar after com data no formato YYYY/MM/DD
                # O Gmail API filtra e-mails recebidos após esta data
                date_str = after_date.strftime('%Y/%m/%d')
                if search_query:
                    search_query += f' after:{date_str}'
                else:
                    search_query = f'after:{date_str}'
            
            # Buscar mensagens
            results = self.service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            return [msg['id'] for msg in messages]
        except HttpError as error:
            print(f'Erro ao listar mensagens: {error}')
            return []
    
    def get_message(self, message_id):
        """
        Obtém uma mensagem completa pelo ID
        
        Args:
            message_id: ID da mensagem
            
        Returns:
            dict: Dados da mensagem (id, threadId, snippet, payload, etc)
        """
        if not self.is_authenticated():
            return None
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return message
        except HttpError as error:
            print(f'Erro ao obter mensagem: {error}')
            return None
    
    def get_message_body(self, message):
        """
        Extrai o corpo do e-mail da mensagem
        
        Args:
            message: Objeto de mensagem do Gmail API
            
        Returns:
            str: Corpo do e-mail decodificado
        """
        if not message or 'payload' not in message:
            return ''
        
        payload = message['payload']
        body = ''
        
        # Função recursiva para extrair texto
        def extract_text(part):
            text = ''
            if part.get('parts'):
                for subpart in part['parts']:
                    text += extract_text(subpart)
            else:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data')
                    if data:
                        try:
                            text = base64.urlsafe_b64decode(data).decode('utf-8')
                        except:
                            try:
                                text = base64.urlsafe_b64decode(data).decode('latin-1')
                            except:
                                pass
            return text
        
        body = extract_text(payload)
        return body
    
    def get_message_metadata(self, message):
        """
        Extrai metadados da mensagem
        
        Args:
            message: Objeto de mensagem do Gmail API
            
        Returns:
            dict: Metadados (subject, from, date, etc)
        """
        if not message or 'payload' not in message:
            return {}
        
        headers = message['payload'].get('headers', [])
        metadata = {}
        
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            
            if name == 'subject':
                metadata['subject'] = value
            elif name == 'from':
                metadata['from'] = value
            elif name == 'date':
                metadata['date'] = value
            elif name == 'to':
                metadata['to'] = value
        
        metadata['id'] = message.get('id')
        metadata['threadId'] = message.get('threadId')
        metadata['snippet'] = message.get('snippet', '')
        
        return metadata
    
    def get_new_messages(self, last_check_date=None):
        """
        Obtém novas mensagens desde a última verificação
        
        Args:
            last_check_date: Data da última verificação (datetime)
            
        Returns:
            list: Lista de mensagens completas
        """
        if not self.is_authenticated():
            return []
        
        # Se não há data, buscar mensagens dos últimos 7 dias
        if not last_check_date:
            last_check_date = datetime.now() - timedelta(days=7)
        
        # Filtrar apenas e-mails com o assunto "Erro de Login Whatsapp"
        message_ids = self.list_messages(
            query='subject:"Erro de Login Whatsapp" (is:unread OR in:inbox)',
            max_results=50,
            after_date=last_check_date
        )
        
        messages = []
        for msg_id in message_ids:
            message = self.get_message(msg_id)
            if message:
                messages.append(message)
        
        return messages

