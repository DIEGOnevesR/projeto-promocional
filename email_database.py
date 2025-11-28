#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerenciamento de Banco de Dados SQLite para E-mails Processados
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime

DB_PATH = Path('emails_sent.db')

class EmailDatabase:
    def __init__(self, db_path=None):
        """
        Inicializa o banco de dados
        
        Args:
            db_path: Caminho do arquivo SQLite (padrão: emails_sent.db)
        """
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.init_database()
    
    def init_database(self):
        """Cria as tabelas se não existirem"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de e-mails processados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                thread_id TEXT,
                subject TEXT,
                from_email TEXT,
                date_received TEXT,
                email_body TEXT,
                vendedor_nome TEXT,
                vendedor_primeiro_nome TEXT,
                name TEXT,
                code TEXT,
                phone TEXT,
                empresa TEXT,
                cnpj TEXT,
                telefone_vendedor TEXT,
                whatsapp_message TEXT,
                authorization_link TEXT,
                enviado_whatsapp INTEGER DEFAULT 0,
                data_envio TEXT,
                tentativas INTEGER DEFAULT 0,
                erro TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para melhor performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_id ON emails(message_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_enviado ON emails(enviado_whatsapp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_received ON emails(date_received)')
        # Índice composto para verificação de duplicatas por cliente (code + phone - telefone do cliente)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_phone_date ON emails(code, phone, date_received, enviado_whatsapp)')
        
        conn.commit()
        conn.close()
    
    def save_email(self, message_id, thread_id, subject, from_email, date_received, 
                   email_body, extracted_info, whatsapp_message, authorization_link):
        """
        Salva um e-mail no banco de dados
        
        Args:
            message_id: ID único da mensagem do Gmail
            thread_id: ID da thread/conversa
            subject: Assunto do e-mail
            from_email: Remetente
            date_received: Data de recebimento
            email_body: Corpo do e-mail
            extracted_info: Dicionário com informações extraídas
            whatsapp_message: Mensagem formatada para WhatsApp
            authorization_link: Link de autorização gerado
            
        Returns:
            int: ID do registro inserido
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO emails (
                    message_id, thread_id, subject, from_email, date_received,
                    email_body, vendedor_nome, vendedor_primeiro_nome,
                    name, code, phone, empresa, cnpj, telefone_vendedor,
                    whatsapp_message, authorization_link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id, thread_id, subject, from_email, date_received,
                email_body, 
                extracted_info.get('vendedor_nome_completo', ''),
                extracted_info.get('vendedor_primeiro_nome', ''),
                extracted_info.get('name', ''),
                extracted_info.get('code', ''),
                extracted_info.get('phone', ''),
                extracted_info.get('empresa', ''),
                extracted_info.get('cnpj', ''),
                extracted_info.get('telefone_vendedor', ''),
                whatsapp_message,
                authorization_link
            ))
            
            conn.commit()
            email_id = cursor.lastrowid
            
            # Se não inseriu (já existe), buscar o ID existente
            if email_id == 0:
                cursor.execute('SELECT id FROM emails WHERE message_id = ?', (message_id,))
                result = cursor.fetchone()
                email_id = result[0] if result else None
            
            return email_id
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Erro ao salvar e-mail: {e}")
        finally:
            conn.close()
    
    def mark_as_sent(self, message_id, success=True, error=None):
        """
        Marca um e-mail como enviado
        
        IMPORTANTE: Esta função faz commit imediato para garantir que a marcação
        seja persistida antes de qualquer outra operação.
        
        Args:
            message_id: ID da mensagem
            success: Se foi enviado com sucesso
            error: Mensagem de erro (se houver)
            
        Returns:
            bool: True se atualizado com sucesso, False caso contrário
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if success:
                cursor.execute('''
                    UPDATE emails 
                    SET enviado_whatsapp = 1,
                        data_envio = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE message_id = ?
                ''', (datetime.now().isoformat(), message_id))
                
                # Verificar se realmente atualizou
                rows_updated = cursor.rowcount
                if rows_updated == 0:
                    print(f"⚠️ ATENÇÃO: Nenhuma linha atualizada para message_id={message_id}")
                    print(f"   O e-mail pode não existir no banco de dados")
                    conn.rollback()
                    return False
            else:
                cursor.execute('''
                    UPDATE emails 
                    SET tentativas = tentativas + 1,
                        erro = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE message_id = ?
                ''', (error, message_id))
            
            # COMMIT IMEDIATO para garantir persistência
            conn.commit()
            
            # Verificar se o commit foi bem-sucedido
            if success:
                # Fazer uma verificação adicional para confirmar
                cursor.execute('SELECT enviado_whatsapp FROM emails WHERE message_id = ?', (message_id,))
                result = cursor.fetchone()
                if result and result[0] == 1:
                    print(f"✅ E-mail marcado como enviado no banco: message_id={message_id}")
                    return True
                else:
                    print(f"⚠️ ATENÇÃO: E-mail não foi marcado corretamente: message_id={message_id}, result={result}")
                    return False
            
            return True
        except sqlite3.Error as e:
            conn.rollback()
            print(f"❌ Erro ao atualizar e-mail no banco: {e}")
            import traceback
            print(traceback.format_exc())
            raise Exception(f"Erro ao atualizar e-mail: {e}")
        finally:
            conn.close()
    
    def mark_as_processing(self, message_id):
        """
        Marca um e-mail como sendo processado (atualiza updated_at para indicar processamento recente)
        Isso ajuda a identificar e-mails que estão sendo processados simultaneamente
        
        Args:
            message_id: ID da mensagem
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE emails 
                SET updated_at = CURRENT_TIMESTAMP
                WHERE message_id = ?
            ''', (message_id,))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            # Não levantar exceção aqui, apenas logar
            print(f"⚠️ Erro ao marcar e-mail como processando: {e}")
        finally:
            conn.close()
    
    def get_pending_emails(self):
        """
        Retorna lista de e-mails pendentes (não enviados)
        
        Returns:
            list: Lista de dicionários com e-mails pendentes
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM emails 
            WHERE enviado_whatsapp = 0
            ORDER BY date_received ASC
        ''')
        
        rows = cursor.fetchall()
        emails = [dict(row) for row in rows]
        
        conn.close()
        return emails
    
    def get_email_by_message_id(self, message_id):
        """
        Busca um e-mail pelo message_id
        
        Args:
            message_id: ID da mensagem
            
        Returns:
            dict: Dados do e-mail ou None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM emails WHERE message_id = ?', (message_id,))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None
    
    def get_all_emails(self, limit=100, offset=0):
        """
        Retorna todos os e-mails (com paginação)
        
        Args:
            limit: Número máximo de registros
            offset: Offset para paginação
            
        Returns:
            list: Lista de dicionários com e-mails
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM emails 
            ORDER BY date_received DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        emails = [dict(row) for row in rows]
        
        conn.close()
        return emails
    
    def delete_email(self, message_id):
        """
        Deleta um e-mail do banco de dados
        
        Args:
            message_id: ID da mensagem a deletar
            
        Returns:
            bool: True se deletado com sucesso
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM emails WHERE message_id = ?', (message_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            return deleted
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Erro ao deletar e-mail: {e}")
        finally:
            conn.close()
    
    def delete_multiple_emails(self, message_ids):
        """
        Deleta múltiplos e-mails do banco de dados
        
        Args:
            message_ids: Lista de IDs de mensagens a deletar
            
        Returns:
            int: Número de e-mails deletados
        """
        if not message_ids:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join(['?'] * len(message_ids))
            cursor.execute(f'DELETE FROM emails WHERE message_id IN ({placeholders})', message_ids)
            conn.commit()
            deleted_count = cursor.rowcount
            return deleted_count
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Erro ao deletar e-mails: {e}")
        finally:
            conn.close()
    
    def get_statistics(self):
        """
        Retorna estatísticas do banco de dados
        
        Returns:
            dict: Estatísticas (total, enviados, pendentes)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM emails')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM emails WHERE enviado_whatsapp = 1')
        enviados = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM emails WHERE enviado_whatsapp = 0')
        pendentes = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'enviados': enviados,
            'pendentes': pendentes
        }
    
    def delete_all_pending_emails(self):
        """
        Deleta todos os e-mails pendentes (não enviados) do banco de dados
        
        Returns:
            int: Número de e-mails deletados
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Contar quantos serão deletados
            cursor.execute('SELECT COUNT(*) FROM emails WHERE enviado_whatsapp = 0')
            count = cursor.fetchone()[0]
            
            # Deletar todos os e-mails pendentes
            cursor.execute('DELETE FROM emails WHERE enviado_whatsapp = 0')
            conn.commit()
            
            deleted_count = cursor.rowcount
            return deleted_count
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Erro ao deletar e-mails pendentes: {e}")
        finally:
            conn.close()
    
    def check_already_sent_by_client_and_phone(self, code, phone, exclude_message_id=None):
        """
        Verifica se já foi enviado um e-mail para o mesmo cliente (code + phone - telefone do cliente)
        que foi entregue com sucesso (enviado_whatsapp = 1) NO MESMO DIA.
        
        IMPORTANTE: 
        - A validação é válida apenas para o mesmo dia (data atual)
        - Se foi enviado hoje, não envia novamente hoje
        - Se for amanhã, pode enviar novamente
        - Também verifica e-mails que estão sendo processados/enviados (updated_at recente)
        
        Args:
            code: Código do cliente
            phone: Telefone do cliente (formato: DDD + número, ex: 8897797542)
            exclude_message_id: Message ID a excluir da verificação (para não considerar o próprio e-mail)
            
        Returns:
            dict: Dados do e-mail já enviado com sucesso ou em processamento, ou None se não encontrado
        """
        if not code or not phone:
            return None
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Obter data atual (apenas dia, sem hora)
            today = datetime.now().date()
            today_str = today.strftime('%Y-%m-%d')
            
            base_params = [code, phone]
            
            # Excluir o próprio e-mail se fornecido
            exclude_clause = ''
            if exclude_message_id:
                exclude_clause = ' AND message_id != ?'
                base_params.append(exclude_message_id)
            
            # PRIORIDADE 1: Verificar e-mails já enviados com sucesso (enviado_whatsapp = 1) NO MESMO DIA
            # Comparar apenas a data, ignorando a hora
            # date_received pode estar em diferentes formatos:
            # - ISO format: "2025-11-27T16:49:26"
            # - RFC 2822: "Thu, 27 Nov 2025 16:49:26 -0300"
            # - Outros formatos
            # Vamos usar uma função auxiliar para extrair a data
            query_sent = f'''
                SELECT * FROM emails 
                WHERE code = ? 
                  AND phone = ?
                  AND enviado_whatsapp = 1
                  {exclude_clause}
                ORDER BY date_received DESC
            '''
            
            cursor.execute(query_sent, base_params)
            rows = cursor.fetchall()
            
            # Verificar cada resultado para ver se foi enviado no mesmo dia
            for row in rows:
                result = dict(row)
                date_received_str = result.get('date_received', '')
                
                if not date_received_str:
                    continue
                
                # Tentar extrair a data do date_received
                email_date = None
                try:
                    # Tentar formato ISO (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)
                    if 'T' in date_received_str:
                        email_date = datetime.fromisoformat(date_received_str.replace('Z', '+00:00')).date()
                    elif date_received_str.startswith('20'):  # Provavelmente formato ISO
                        email_date = datetime.strptime(date_received_str[:10], '%Y-%m-%d').date()
                    else:
                        # Tentar parsear formato RFC 2822 (Thu, 27 Nov 2025 16:49:26 -0300)
                        try:
                            email_date = parsedate_to_datetime(date_received_str).date()
                        except:
                            # Se falhar, tentar outros formatos
                            try:
                                email_date = datetime.strptime(date_received_str[:19], '%a, %d %b %Y %H:%M:%S').date()
                            except:
                                pass
                except Exception as e:
                    print(f"⚠️ Erro ao parsear data: {date_received_str}, erro: {e}")
                    continue
                
                # Se conseguiu extrair a data e é o mesmo dia, retornar como duplicata
                if email_date and email_date == today:
                    print(f"🔍 DUPLICATA ENCONTRADA (JÁ ENVIADO HOJE): code={code}, phone={phone} (telefone do cliente)")
                    print(f"   E-mail já enviado HOJE: message_id={result.get('message_id')}, date={date_received_str}")
                    print(f"   Data extraída: {email_date}, Data atual: {today}")
                    print(f"   Status: enviado_whatsapp={result.get('enviado_whatsapp')} (confirmado)")
                    return result
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                print(f"🔍 DUPLICATA ENCONTRADA (JÁ ENVIADO HOJE): code={code}, phone={phone} (telefone do cliente)")
                print(f"   E-mail já enviado HOJE: message_id={result.get('message_id')}, date={result.get('date_received')}")
                print(f"   Status: enviado_whatsapp={result.get('enviado_whatsapp')} (confirmado)")
                return result
            
            # PRIORIDADE 2: Verificar e-mails que estão sendo processados/enviados (updated_at recente)
            # Isso evita que dois e-mails sejam enviados simultaneamente
            # Considerar apenas e-mails atualizados nos últimos 10 minutos (tempo suficiente para envio + ACK)
            recent_threshold = datetime.now() - timedelta(minutes=10)
            recent_threshold_str = recent_threshold.strftime('%Y-%m-%d %H:%M:%S')
            
            query_processing = f'''
                SELECT * FROM emails 
                WHERE code = ? 
                  AND phone = ?
                  AND enviado_whatsapp = 0
                  AND updated_at >= ?
                  {exclude_clause}
                ORDER BY date_received DESC LIMIT 1
            '''
            
            processing_params = [code, phone, recent_threshold_str]
            if exclude_message_id:
                processing_params.append(exclude_message_id)
            
            cursor.execute(query_processing, processing_params)
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                print(f"🔍 DUPLICATA ENCONTRADA (EM PROCESSAMENTO): code={code}, phone={phone} (telefone do cliente)")
                print(f"   E-mail em processamento: message_id={result.get('message_id')}, updated_at={result.get('updated_at')}")
                print(f"   ⚠️ Este e-mail está sendo processado/enviado, ignorando novo e-mail para evitar duplicata")
                return result
            
            return None
        except Exception as e:
            print(f"⚠️ Erro ao verificar e-mail já enviado: {e}")
            import traceback
            print(traceback.format_exc())
            return None
        finally:
            conn.close()

