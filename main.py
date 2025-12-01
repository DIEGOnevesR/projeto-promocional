#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerador de Banners Promocionais
Lê tabela de preços (CSV), identifica produtos com maior desconto e gera banners em JPEG
"""
import os
import sys
import json
import base64
import time
import queue
import threading
import pandas as pd
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
import subprocess
from html import escape
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Importar Cloudinary
try:
    from cloudinary_storage import (
        get_image_base64_from_cloudinary,
        get_image_url_from_cloudinary,
        download_file_from_cloudinary,
        upload_banner_to_cloudinary,
        upload_cache_image_to_cloudinary,
        get_cache_image_from_cloudinary,
        save_template_to_cloudinary,
        load_template_from_cloudinary
    )
    USE_CLOUDINARY = os.getenv('USE_CLOUDINARY', 'true').lower() == 'true'
except ImportError:
    USE_CLOUDINARY = False
    print('⚠️ cloudinary_storage não encontrado. Usando arquivos locais.')

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    try:
        import codecs
        # Verificar se stdout tem buffer antes de tentar usar
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, TypeError):
        # Se não conseguir configurar, apenas ignorar (pode estar em ambiente que já gerencia encoding)
        pass

# Constantes
CSV_FILE = 'Tabela de Preço.csv'
UNIDADES_FILE = 'Unidades.xlsx'
TEMPLATE_FILE = 'banner-template.json'
IMAGES_FOLDER = 'imagens'
CACHE_FOLDER = 'cache_imagens_processadas'  # Cache de imagens com fundo removido
BANNER_WIDTH = 1080
BANNER_HEIGHT = 1920
BASE_IMAGE_URL = 'https://fdvmtz.jbs.com.br/static/erp/img/{codigo}.jpg'

TELEGRAM_BOT_TOKEN = '8589089694:AAGtUGhoMDg_zd-BvU47UTA3kP4OV8sX70w'
TELEGRAM_CHAT_ID = 'fboi_images_bot'
TELEGRAM_API_BASE = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}' if TELEGRAM_BOT_TOKEN else None

# Configuração WhatsApp
WHATSAPP_API_URL = 'http://localhost:3001'
WHATSAPP_ENABLED = True
WHATSAPP_LINK = 'wa.me/551151944697?text=oi'


class BannerGenerator:
    """Gerador de banners promocionais"""
    
    def __init__(self):
        """Inicializa o gerador"""
        # Carregar template PRIMEIRO - obrigatório
        self.template_config = {}
        self._force_reload_template()
        
        self.images_folder = IMAGES_FOLDER
        
        if not os.path.exists(self.images_folder):
            print(f'⚠ Pasta {self.images_folder} não encontrada!')
        
        if not os.path.exists(CSV_FILE):
            raise FileNotFoundError(f'Arquivo CSV não encontrado: {CSV_FILE}')
        
        # Criar pasta de cache se não existir
        self.cache_folder = CACHE_FOLDER
        os.makedirs(self.cache_folder, exist_ok=True)
        
        # Carregar mapeamento de unidades para grupos
        self.unidade_to_group = self.load_unidades_grupos()
        
        # Otimizações de performance
        self.playwright = None
        self.browser = None
        self.image_existence_cache = {}  # Cache de verificação de imagens
        self.local_images_cache = {}  # Cache de imagens locais convertidas para base64
        self.whatsapp_session = None  # Sessão HTTP persistente para WhatsApp
        
        # Fila e thread para envio paralelo ao WhatsApp
        self.whatsapp_queue = queue.Queue()
        self.whatsapp_thread = None
        self.whatsapp_thread_stop = threading.Event()
        self.whatsapp_thread_running = False
    
    def load_template(self, silent=False):
        """Carrega configuração do template se existir - suporta Cloudinary"""
        # Tentar Cloudinary primeiro se habilitado
        if USE_CLOUDINARY:
            try:
                template_data = load_template_from_cloudinary()
                if template_data and isinstance(template_data, dict) and len(template_data) > 0:
                    if not silent:
                        print(f'✓ Template carregado do Cloudinary: {len(template_data)} propriedades')
                    # Normalizar valores (mesmo código de normalização)
                    for key, value in template_data.items():
                        if key in ['desconto-badge-shape', 'footer-rotation'] or key.endswith('-font-family') or key.endswith('-font-weight') or key.endswith('-font-style') or key.endswith('-color') or key.endswith('-bg-color'):
                            continue
                        if isinstance(value, str) and value.strip() == '0':
                            template_data[key] = 0
                        elif isinstance(value, str):
                            try:
                                if '.' not in value.strip():
                                    template_data[key] = int(float(value.strip()))
                                else:
                                    template_data[key] = float(value.strip())
                            except (ValueError, TypeError):
                                pass
                    return template_data
            except Exception as e:
                if not silent:
                    print(f'⚠ Erro ao carregar template do Cloudinary: {e}. Tentando local...')
        
        # Fallback para arquivo local
        # Usar caminho absoluto para garantir que encontre o arquivo
        template_path = os.path.abspath(TEMPLATE_FILE)
        
        if not silent:
            print(f'🔍 Buscando template em: {template_path}')
            print(f'   Diretório de trabalho: {os.getcwd()}')
        
        if os.path.exists(template_path):
            try:
                if not silent:
                    print(f'✓ Arquivo encontrado, lendo...')
                
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not silent:
                        print(f'   Tamanho do arquivo: {len(content)} bytes')
                    
                    config = json.loads(content)
                    
                    # Verificar se config é None ou não é dict
                    if config is None:
                        if not silent:
                            print(f'⚠ Template carregado mas JSON retornou None')
                        return {}
                    
                    if not isinstance(config, dict):
                        if not silent:
                            print(f'⚠ Template carregado mas não é um dicionário: {type(config)}')
                        return {}
                    
                    if len(config) == 0:
                        if not silent:
                            print(f'⚠ Template carregado mas está vazio (0 propriedades)')
                        return {}
                    
                    # Normalizar valores "0" (string) para 0 (número) para consistência
                    # MAS manter valores como números quando possível
                    for key, value in config.items():
                        # Campos que devem permanecer strings
                        if key in ['desconto-badge-shape', 'footer-rotation'] or key.endswith('-font-family') or key.endswith('-font-weight') or key.endswith('-font-style') or key.endswith('-color') or key.endswith('-bg-color'):
                            continue
                        
                        # Se for string "0", converter para número 0
                        if isinstance(value, str) and value.strip() == '0':
                                config[key] = 0
                        # Se for string numérica, tentar converter para número
                        elif isinstance(value, str):
                            try:
                                # Tentar converter para int se for inteiro
                                if '.' not in value.strip():
                                    config[key] = int(float(value.strip()))
                                else:
                                    config[key] = float(value.strip())
                            except (ValueError, TypeError):
                                # Se não conseguir converter, manter como string
                                pass
                    
                    if not silent:
                        print(f'✓ Template carregado com sucesso: {len(config)} propriedades encontradas')
                        print(f'   Primeiras 5 chaves: {list(config.keys())[:5]}')
                    return config
            except json.JSONDecodeError as je:
                if not silent:
                    print(f'❌ Erro de JSON no template: {je}')
                    print(f'   Linha: {je.lineno}, Coluna: {je.colno}')
                    import traceback
                    print(f'  Detalhes: {traceback.format_exc()}')
                return {}
            except Exception as e:
                if not silent:
                    print(f'❌ Erro ao carregar template: {e}')
                    import traceback
                    print(f'  Detalhes: {traceback.format_exc()}')
                return {}
        else:
            # Tentar também caminho relativo (por compatibilidade) - evitar recursão
            rel_path = TEMPLATE_FILE
            if os.path.exists(rel_path) and os.path.abspath(rel_path) != template_path:
                if not silent:
                    print(f'⚠ Arquivo encontrado apenas com caminho relativo, usando caminho relativo...')
                try:
                    with open(rel_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        config = json.loads(content)
                        # Normalizar valores (mesmo código de normalização)
                        for key, value in config.items():
                            if key in ['desconto-badge-shape', 'footer-rotation'] or key.endswith('-font-family') or key.endswith('-font-weight') or key.endswith('-font-style') or key.endswith('-color') or key.endswith('-bg-color'):
                                continue
                            if isinstance(value, str) and value.strip() == '0':
                                config[key] = 0
                            elif isinstance(value, str):
                                try:
                                    if '.' not in value.strip():
                                        config[key] = int(float(value.strip()))
                                    else:
                                        config[key] = float(value.strip())
                                except (ValueError, TypeError):
                                    pass
                        if not silent:
                            print(f'✓ Template carregado (relativo): {len(config)} propriedades')
                        return config
                except Exception as e:
                    if not silent:
                        print(f'❌ Erro ao carregar template relativo: {e}')
            # Se não encontrou em nenhum lugar (arquivo relativo não existe ou não é diferente do absoluto)
            else:
                if not silent:
                    print(f'❌ Template não encontrado:')
                    print(f'   Caminho absoluto testado: {template_path}')
                    print(f'   Caminho relativo testado: {rel_path}')
                    print(f'   Diretório de trabalho atual: {os.getcwd()}')
                    print(f'   Existe (absoluto)? {os.path.exists(template_path)}')
                    print(f'   Existe (relativo)? {os.path.exists(rel_path)}')
        return {}
    
    def _force_reload_template(self):
        """Força recarregamento do template - usado na inicialização"""
        print(f'\n🔄 FORÇANDO CARREGAMENTO DO TEMPLATE NA INICIALIZAÇÃO...')
        print(f'   Diretório de trabalho: {os.getcwd()}')
        print(f'   Caminho do arquivo: {os.path.abspath(TEMPLATE_FILE)}')
        
        self.template_config = self.load_template(silent=False)
        
        if not self.template_config or len(self.template_config) == 0:
            print(f'\n⚠⚠⚠ AVISO CRÍTICO: Template não foi carregado ou está vazio na inicialização!')
            print(f'   Arquivo esperado: {TEMPLATE_FILE}')
            print(f'   Caminho absoluto: {os.path.abspath(TEMPLATE_FILE)}')
            print(f'   Arquivo existe? {os.path.exists(TEMPLATE_FILE)}')
            print(f'   Arquivo existe (abs)? {os.path.exists(os.path.abspath(TEMPLATE_FILE))}')
            
            if os.path.exists(TEMPLATE_FILE):
                print(f'   Tentando ler novamente...')
                try:
                    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f'   Tamanho do arquivo: {len(content)} bytes')
                        if len(content) > 0:
                            import json
                            test_config = json.loads(content)
                            print(f'   JSON válido com {len(test_config)} chaves')
                            print(f'   ⚠ PORÉM, load_template() retornou vazio! Problema no método!')
                            # Tentar usar o config direto
                            self.template_config = test_config
                            print(f'   ✓ Template carregado diretamente: {len(self.template_config)} propriedades')
                except Exception as e:
                    print(f'   ❌ Erro ao ler template: {e}')
                    import traceback
                    print(f'   Detalhes: {traceback.format_exc()}')
            else:
                print(f'   💡 Crie o arquivo {TEMPLATE_FILE} através do editor de templates')
        else:
            print(f'✓✓✓ Template carregado com sucesso na inicialização: {len(self.template_config)} propriedades')
            print(f'   Tipo: {type(self.template_config)}')
            print(f'   É dict? {isinstance(self.template_config, dict)}')
    
    def reload_template(self):
        """Recarrega o template do arquivo"""
        print(f'\n🔄 RECARREGANDO TEMPLATE...')
        print(f'   Diretório de trabalho: {os.getcwd()}')
        print(f'   Caminho do arquivo: {os.path.abspath(TEMPLATE_FILE)}')
        
        old_count = len(self.template_config) if self.template_config else 0
        template_antes = self.template_config.copy() if isinstance(self.template_config, dict) and self.template_config else {}
        
        # Verificar se arquivo existe antes de tentar carregar
        template_path = os.path.abspath(TEMPLATE_FILE)
        if not os.path.exists(template_path):
            print(f'❌ Arquivo não encontrado no caminho absoluto: {template_path}')
            if os.path.exists(TEMPLATE_FILE):
                print(f'   Mas encontrado no caminho relativo: {TEMPLATE_FILE}')
                template_path = TEMPLATE_FILE
            else:
                print(f'   ❌ Não encontrado nem no caminho relativo!')
        
        # Forçar recarregamento (sem silent para ver todos os logs)
        loaded_config = self.load_template(silent=False)
        
        # Se não carregou, tentar fallback direto
        if not loaded_config or len(loaded_config) == 0:
            print(f'   ⚠ load_template() retornou vazio, tentando carregar diretamente...')
            try:
                template_path_fallback = os.path.abspath(TEMPLATE_FILE)
                if not os.path.exists(template_path_fallback):
                    template_path_fallback = TEMPLATE_FILE
                
                if os.path.exists(template_path_fallback):
                    print(f'   Tentando ler diretamente de: {template_path_fallback}')
                    with open(template_path_fallback, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f'   Tamanho: {len(content)} bytes')
                        if len(content) > 0:
                            import json
                            loaded_config = json.loads(content)
                            print(f'   ✓ Carregado diretamente: {len(loaded_config)} propriedades')
                            # Aplicar normalização
                            for key, value in loaded_config.items():
                                if key in ['desconto-badge-shape', 'footer-rotation'] or key.endswith('-font-family') or key.endswith('-font-weight') or key.endswith('-font-style') or key.endswith('-color') or key.endswith('-bg-color'):
                                    continue
                                if isinstance(value, str) and value.strip() == '0':
                                    loaded_config[key] = 0
                                elif isinstance(value, str):
                                    try:
                                        if '.' not in value.strip():
                                            loaded_config[key] = int(float(value.strip()))
                                        else:
                                            loaded_config[key] = float(value.strip())
                                    except (ValueError, TypeError):
                                        pass
            except Exception as e:
                print(f'   ❌ Erro no fallback: {e}')
                import traceback
                print(f'   Detalhes: {traceback.format_exc()}')
        
        self.template_config = loaded_config if loaded_config and isinstance(loaded_config, dict) and len(loaded_config) > 0 else {}
        
        new_count = len(self.template_config) if self.template_config else 0
        
        print(f'   Template antes: {old_count} propriedades')
        print(f'   Template depois: {new_count} propriedades')
        print(f'   Tipo retornado: {type(loaded_config)}')
        print(f'   É dict? {isinstance(loaded_config, dict)}')
        print(f'   loaded_config é None? {loaded_config is None}')
        empty_dict = {}
        print(f'   loaded_config é vazio? {loaded_config == empty_dict}')
        
        if new_count > 0:
            print(f'✓ Template recarregado: {new_count} propriedades encontradas')
            # Debug: mostrar algumas propriedades chave
            print(f'  📋 Exemplos de valores carregados:')
            sample_keys = ['produto-container-padding', 'desconto-badge-shape', 'produto-nome-font-size', 'logo-ofertas-top', 'produto-container-bg-color']
            for key in sample_keys:
                if key in self.template_config:
                    valor_antes = template_antes.get(key, 'N/A') if template_antes else 'N/A'
                    valor_agora = self.template_config[key]
                    print(f'    • {key}: {valor_agora} (antes: {valor_antes})')
            
            # Verificar se realmente mudou
            if old_count == new_count and template_antes == self.template_config:
                print(f'  ⚠ Atenção: Template recarregado mas valores são idênticos aos anteriores')
            else:
                print(f'  ✓ Template atualizado (tinha {old_count}, agora tem {new_count} propriedades)')
        else:
            print(f'❌❌❌ ERRO CRÍTICO: Template vazio ou não encontrado após recarregar!')
            print(f'   Template retornado: {loaded_config}')
            print(f'   Tipo: {type(loaded_config)}')
            print(f'   Verifique o arquivo {TEMPLATE_FILE}')
            print(f'   Caminho absoluto: {template_path}')
    
    def get_template_value(self, key, default):
        """Obtém valor do template ou retorna padrão"""
        if not self.template_config:
            return default
        value = self.template_config.get(key, default)
        # Se o valor não foi encontrado explicitamente, usar o padrão
        if key not in self.template_config:
            return default
        # Se o valor for None mas a chave existe, retornar None (pode ser válido)
        return value
    
    def load_unidades_grupos(self):
        """Carrega mapeamento de unidades para grupos do WhatsApp"""
        unidade_to_group = {}
        
        if not os.path.exists(UNIDADES_FILE):
            print(f'⚠ Arquivo {UNIDADES_FILE} não encontrado. Envio para grupos desabilitado.')
            return unidade_to_group
        
        try:
            # Tentar ler como Excel
            df_unidades = pd.read_excel(UNIDADES_FILE, engine='openpyxl')
            df_unidades.columns = df_unidades.columns.str.strip()
            
            # Verificar se tem as colunas necessárias
            if 'Unidade' not in df_unidades.columns or 'id_grupo' not in df_unidades.columns:
                print(f'⚠ Arquivo {UNIDADES_FILE} não contém colunas "Unidade" e "id_grupo". Envio para grupos desabilitado.')
                return unidade_to_group
            
            # Criar mapeamento
            for _, row in df_unidades.iterrows():
                unidade = str(row['Unidade']).strip()
                id_grupo = str(row['id_grupo']).strip()
                
                if unidade and id_grupo and id_grupo.lower() != 'nan':
                    unidade_to_group[unidade] = id_grupo
            
            print(f'✓ Mapeamento de unidades carregado: {len(unidade_to_group)} unidade(s) com grupo(s)')
            if unidade_to_group:
                print(f'  Grupos configurados: {", ".join(unidade_to_group.keys())}')
            
        except Exception as e:
            print(f'⚠ Erro ao carregar {UNIDADES_FILE}: {e}')
            print('  Envio para grupos desabilitado.')
        
        return unidade_to_group
    
    def get_imagem_container_bg_color(self):
        """Obtém cor de fundo do container de imagem do produto com opacidade"""
        bg_color_hex = self.get_template_value('produto-imagem-container-bg-color', '#FFFFFF')
        bg_opacity_raw = self.get_template_value('produto-imagem-container-bg-opacity', 80)
        
        # Converter opacidade para 0-1 se necessário
        if isinstance(bg_opacity_raw, (int, float)):
            bg_opacity = bg_opacity_raw / 100.0 if bg_opacity_raw > 1 else bg_opacity_raw
        else:
            try:
                bg_opacity_val = float(bg_opacity_raw)
                bg_opacity = bg_opacity_val / 100.0 if bg_opacity_val > 1 else bg_opacity_val
            except:
                bg_opacity = 0.8
        
        # Se a opacidade for 0, retornar transparente
        if bg_opacity == 0:
            return 'transparent'
        
        # Converter cor hex para RGB
        bg_color_hex = bg_color_hex.lstrip('#')
        if len(bg_color_hex) == 6:
            r = int(bg_color_hex[0:2], 16)
            g = int(bg_color_hex[2:4], 16)
            b = int(bg_color_hex[4:6], 16)
            return f'rgba({r}, {g}, {b}, {bg_opacity})'
        else:
            return f'rgba(255, 255, 255, {bg_opacity})'
    
    def generate_goldplay_fonts_css(self):
        """Gera @font-face declarations para as fontes Goldplay locais"""
        fonts_dir = 'Fontes'
        font_faces = []
        
        # Goldplay Regular e variações
        goldplay_weights = {
            'Thin': '100',
            'Light': '300',
            'Regular': '400',
            'Medium': '500',
            'SemiBold': '600',
            'Bold': '700',
            'Black': '900'
        }
        
        for weight_name, weight_value in goldplay_weights.items():
            regular_path = os.path.join(fonts_dir, f'Goldplay-{weight_name}.ttf')
            italic_path = os.path.join(fonts_dir, f'Goldplay-{weight_name}It.ttf')
            
            if os.path.exists(regular_path):
                try:
                    with open(regular_path, 'rb') as f:
                        font_data = f.read()
                        font_base64 = base64.b64encode(font_data).decode('utf-8')
                        font_faces.append(f'''
@font-face {{
    font-family: 'Goldplay';
    src: url(data:font/truetype;charset=utf-8;base64,{font_base64}) format('truetype');
    font-weight: {weight_value};
    font-style: normal;
    font-display: swap;
}}''')
                except Exception as e:
                    print(f'⚠ Erro ao carregar fonte Goldplay-{weight_name}.ttf: {e}')
            
            if os.path.exists(italic_path):
                try:
                    with open(italic_path, 'rb') as f:
                        font_data = f.read()
                        font_base64 = base64.b64encode(font_data).decode('utf-8')
                        font_faces.append(f'''
@font-face {{
    font-family: 'Goldplay';
    src: url(data:font/truetype;charset=utf-8;base64,{font_base64}) format('truetype');
    font-weight: {weight_value};
    font-style: italic;
    font-display: swap;
}}''')
                except Exception as e:
                    print(f'⚠ Erro ao carregar fonte Goldplay-{weight_name}It.ttf: {e}')
        
        # GoldplayAlt Regular e variações
        for weight_name, weight_value in goldplay_weights.items():
            regular_path = os.path.join(fonts_dir, f'GoldplayAlt-{weight_name}.ttf')
            italic_path = os.path.join(fonts_dir, f'GoldplayAlt-{weight_name}It.ttf')
            
            if os.path.exists(regular_path):
                try:
                    with open(regular_path, 'rb') as f:
                        font_data = f.read()
                        font_base64 = base64.b64encode(font_data).decode('utf-8')
                        font_faces.append(f'''
@font-face {{
    font-family: 'GoldplayAlt';
    src: url(data:font/truetype;charset=utf-8;base64,{font_base64}) format('truetype');
    font-weight: {weight_value};
    font-style: normal;
    font-display: swap;
}}''')
                except Exception as e:
                    print(f'⚠ Erro ao carregar fonte GoldplayAlt-{weight_name}.ttf: {e}')
            
            if os.path.exists(italic_path):
                try:
                    with open(italic_path, 'rb') as f:
                        font_data = f.read()
                        font_base64 = base64.b64encode(font_data).decode('utf-8')
                        font_faces.append(f'''
@font-face {{
    font-family: 'GoldplayAlt';
    src: url(data:font/truetype;charset=utf-8;base64,{font_base64}) format('truetype');
    font-weight: {weight_value};
    font-style: italic;
    font-display: swap;
}}''')
                except Exception as e:
                    print(f'⚠ Erro ao carregar fonte GoldplayAlt-{weight_name}It.ttf: {e}')
        
        return '\n'.join(font_faces)
    
    def format_css_value(self, key, value):
        """Formata valor para CSS - deve corresponder exatamente à lógica do getValue() no template_editor.html"""
        # Se já for uma string com unidade (px, %, auto), retornar como está
        if isinstance(value, str):
            value_stripped = value.strip()
            if value_stripped.endswith(('px', '%', 'auto')):
                return value_stripped
            # Converter string vazia ou "0" para 0 numérico
            if value_stripped == '' or value_stripped == '0':
                value = 0
            else:
                # Tentar converter para número
                try:
                    value = float(value_stripped)
                except ValueError:
                    return value_stripped
        
        # Agora value deve ser numérico
        if isinstance(value, (int, float)):
            # Opacidades: converter para 0-1 se vier como 0-100
            if key in ['base-produto-opacity', 'produto-container-bg-opacity', 'produto-imagem-container-bg-opacity']:
                if value > 1:
                    value = value / 100.0
                return str(value)
            
            # Valores que devem ser percentuais (left)
            percent_left_keys = {'produto-imagem-left', 'base-produto-left', 'call-action-left', 'logo-inferior-left', 'footer-left'}
            if key in percent_left_keys:
                return f'{value}%'
            
            # Valores que devem ser percentuais (width)
            if key in ['base-produto-width', 'produto-imagem-width']:
                return f'{value}%'
            
            # Valores que retornam 'auto' quando são 0
            auto_when_zero_keys = [
                'produto-imagem-height', 
                'base-produto-height', 
                'desconto-badge-width', 
                'desconto-badge-height', 
                'logo-superior-height', 
                'call-action-top', 
                'footer-top',
                'desconto-badge-left',
                'desconto-badge-bottom',
                'footer-bottom',
                'call-action-bottom'
            ]
            if key in auto_when_zero_keys and value == 0:
                return 'auto'
            
            # Todos os outros valores devem ser pixels
            return f'{value}px'
        
        # Se não for numérico, retornar como string
        return str(value)
    
    def image_to_base64(self, image_path):
        """Converte imagem para base64 (com cache) - suporta Cloudinary e local"""
        # Verificar cache primeiro
        abs_path = os.path.abspath(image_path) if not USE_CLOUDINARY else image_path
        if abs_path in self.local_images_cache:
            return self.local_images_cache[abs_path]
        
        # Tentar Cloudinary primeiro se habilitado
        if USE_CLOUDINARY:
            try:
                # Extrair nome do arquivo sem extensão
                filename = Path(image_path).stem
                # Determinar pasta baseado no caminho
                if 'imagens' in image_path.lower() or 'Imagens' in image_path:
                    folder = 'imagens'
                elif 'bandeira' in image_path.lower() or 'Bandeira' in image_path:
                    folder = 'bandeiras'
                else:
                    folder = 'imagens'  # default
                
                result = get_image_base64_from_cloudinary(filename, folder=folder)
                if result:
                    self.local_images_cache[abs_path] = result
                    return result
            except Exception as e:
                print(f'⚠ Erro ao buscar do Cloudinary: {e}. Tentando local...')
        
        # Fallback para arquivo local
        if not os.path.exists(image_path):
            return None
        
        try:
            with open(image_path, 'rb') as f:
                result = base64.b64encode(f.read()).decode('utf-8')
                # Armazenar no cache
                self.local_images_cache[abs_path] = result
                return result
        except Exception as e:
            print(f'⚠ Erro ao converter {image_path} para base64: {e}')
            return None
    
    def check_image_exists(self, codigo):
        """Verifica se a imagem do produto existe no servidor (com cache)"""
        # Verificar cache primeiro
        if codigo in self.image_existence_cache:
            return self.image_existence_cache[codigo]
        
        url = BASE_IMAGE_URL.format(codigo=codigo)
        result = None
        try:
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    result = url
        except:
            pass
        
        # Armazenar no cache (mesmo que None)
        self.image_existence_cache[codigo] = result
        return result
    
    def get_product_image_url(self, codigo):
        """Obtém URL da imagem do produto ou retorna placeholder"""
        url = self.check_image_exists(codigo)
        if url:
            return url
        return f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='180'%3E%3Crect fill='%23ddd' width='200' height='180'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999'%3EProduto {codigo}%3C/text%3E%3C/svg%3E"
    
    def get_cache_path(self, codigo):
        """Retorna o caminho do arquivo de cache para um código"""
        return os.path.join(self.cache_folder, f'{codigo}.png')
    
    def load_from_cache(self, codigo):
        """Carrega imagem processada do cache e normaliza se necessário - suporta Cloudinary"""
        # Tentar Cloudinary primeiro se habilitado
        if USE_CLOUDINARY:
            try:
                cached_data = get_cache_image_from_cloudinary(codigo)
                if cached_data:
                    print(f'  ✓ Imagem carregada do cache Cloudinary (produto {codigo})')
                    return cached_data
            except Exception as e:
                print(f'  ⚠ Erro ao buscar cache do Cloudinary: {e}. Tentando local...')
        
        # Fallback para cache local
        cache_path = self.get_cache_path(codigo)
        if os.path.exists(cache_path):
            try:
                import io
                from PIL import Image
                
                # Verificar se a imagem no cache já está normalizada
                img = Image.open(cache_path)
                
                # Verificar se já está normalizada (1000x1000)
                if img.size != (1000, 1000):
                    # Normalizar se não estiver
                    img = self.normalize_product_size(img, target_size=1000, padding_percent=5)
                    # Salvar versão normalizada de volta no cache
                    img.save(cache_path, format="PNG")
                
                # Converter para base64
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                return f'data:image/png;base64,{img_base64}'
            except Exception as e:
                print(f'  ⚠ Erro ao carregar cache: {e}')
                return None
        return None
    
    def save_to_cache(self, codigo, image_bytes):
        """Salva imagem processada no cache - suporta Cloudinary"""
        # Salvar localmente primeiro
        cache_path = self.get_cache_path(codigo)
        try:
            with open(cache_path, 'wb') as f:
                f.write(image_bytes)
        except Exception as e:
            print(f'  ⚠ Erro ao salvar cache local: {e}')
        
        # Upload para Cloudinary se habilitado
        if USE_CLOUDINARY:
            try:
                url = upload_cache_image_to_cloudinary(codigo, image_bytes)
                if url:
                    print(f'  ✓ Cache enviado para Cloudinary (produto {codigo})')
                    return True
            except Exception as e:
                print(f'  ⚠ Erro ao enviar cache para Cloudinary: {e}')
        
        return True
    
    def normalize_product_size(self, img, target_size=1000, padding_percent=5):
        """
        Normaliza o tamanho do produto em um canvas quadrado
        O produto fica alinhado na parte inferior (como se estivesse apoiado no chão)
        
        Args:
            img: PIL Image com fundo transparente
            target_size: Tamanho do canvas quadrado (padrão: 1000x1000)
            padding_percent: Percentual de padding ao redor do produto (padrão: 5%)
        
        Returns:
            PIL Image normalizada em canvas quadrado
        """
        import numpy as np
        from PIL import Image
        
        # Converter para array numpy para detectar bounding box
        img_array = np.array(img)
        
        # Encontrar pixels não transparentes (alpha > 0)
        if img_array.shape[2] == 4:  # RGBA
            alpha_channel = img_array[:, :, 3]
            coords = np.column_stack(np.where(alpha_channel > 0))
        else:
            # Se não tiver alpha, usar toda a imagem
            coords = np.column_stack(np.where(np.any(img_array[:, :, :3] > 0, axis=2)))
        
        if len(coords) == 0:
            # Se não encontrar pixels, retornar imagem original
            return img
        
        # Calcular bounding box
        min_y, min_x = coords.min(axis=0)
        max_y, max_x = coords.max(axis=0)
        
        # Cortar imagem para o bounding box
        cropped = img.crop((min_x, min_y, max_x + 1, max_y + 1))
        
        # Calcular tamanho com padding
        padding = int(target_size * (padding_percent / 100))
        max_size = target_size - (padding * 2)
        
        # Calcular escala mantendo proporção
        width, height = cropped.size
        scale = min(max_size / width, max_size / height)
        
        # Redimensionar mantendo proporção
        new_width = int(width * scale)
        new_height = int(height * scale)
        # Usar LANCZOS (compatível com versões antigas e novas do Pillow)
        try:
            resized = cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except AttributeError:
            # Fallback para versões antigas do Pillow
            resized = cropped.resize((new_width, new_height), Image.LANCZOS)
        
        # Criar canvas quadrado transparente
        canvas = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
        
        # Calcular posição: centralizado horizontalmente, alinhado na parte inferior
        x_offset = (target_size - new_width) // 2  # Centralizado horizontalmente
        y_offset = target_size - new_height - padding  # Alinhado na parte inferior com padding
        
        # Colar produto no canvas (alinhado na base)
        canvas.paste(resized, (x_offset, y_offset), resized)
        
        return canvas
    
    def remove_background(self, image_url, codigo=None, use_cache=True):
        """Remove o fundo da imagem do produto usando rembg"""
        # Verificar cache primeiro
        if use_cache and codigo:
            cached = self.load_from_cache(codigo)
            if cached:
                print(f'  ✓ Imagem carregada do cache (produto {codigo})')
                return cached
        
        try:
            from rembg import remove
            from PIL import Image
            import io
            
            if codigo:
                print(f'🔄 Processando remoção de fundo para produto {codigo}: {image_url}')
            else:
                print(f'🔄 Processando remoção de fundo para: {image_url}')
            
            # Baixar imagem
            print(f'  📥 Baixando imagem...')
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                print(f'  ⚠ Erro ao baixar imagem (status {response.status_code}): {image_url}')
                return None
            
            print(f'  ✓ Imagem baixada ({len(response.content)} bytes)')
            
            # Processar com rembg
            print(f'  🎨 Processando com rembg...')
            input_image = response.content
            output_image = remove(input_image)
            print(f'  ✓ Processamento concluído')
            
            # Converter para PIL Image para garantir formato PNG com transparência
            img = Image.open(io.BytesIO(output_image))
            
            # Normalizar tamanho - produto alinhado na parte inferior
            print(f'  📐 Normalizando tamanho do produto...')
            img = self.normalize_product_size(img, target_size=1000, padding_percent=5)
            print(f'  ✓ Produto normalizado (1000x1000px, alinhado na base)')
            
            # Converter de volta para bytes para salvar no cache
            buffered_temp = io.BytesIO()
            img.save(buffered_temp, format="PNG")
            output_image = buffered_temp.getvalue()
            
            # Salvar no cache se tiver código
            if codigo:
                self.save_to_cache(codigo, output_image)
                print(f'  ✓ Imagem salva no cache (normalizada)')
            
            # Converter para base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            print(f'  ✓ Imagem convertida para base64')
            return f'data:image/png;base64,{img_base64}'
            
        except ImportError as e:
            print(f'⚠ Erro: Biblioteca rembg não instalada: {e}')
            print('💡 Execute: pip install rembg Pillow numpy onnxruntime')
            return None
        except Exception as e:
            print(f'⚠ Erro ao remover fundo: {e}')
            import traceback
            print('📋 Detalhes do erro:')
            traceback.print_exc()
            return None
    
    def get_product_image_with_background_removed(self, codigo, use_cache=True):
        """Obtém imagem do produto com fundo removido"""
        # Verificar cache primeiro - se tiver imagem processada, retornar diretamente
        cached = self.load_from_cache(codigo)
        if cached:
            return cached
        
        # Se não tiver no cache, retornar URL original (pode processar depois se necessário)
        url = self.check_image_exists(codigo)
        if url:
            return url
        
        # Se não existir, retornar placeholder
        return self.get_product_image_url(codigo)
    
    def process_images_in_parallel(self, produtos_validos, max_workers=4):
        """Processa imagens de produtos em paralelo (otimização de performance)"""
        results = {}
        
        def process_single_image(produto):
            """Processa imagem de um único produto"""
            codigo = int(produto['Código'])
            try:
                imagem_url = self.get_product_image_with_background_removed(codigo, use_cache=True)
                return codigo, imagem_url
            except Exception as e:
                print(f'  ⚠ Erro ao processar imagem do produto {codigo}: {e}')
                # Retornar placeholder em caso de erro
                return codigo, self.get_product_image_url(codigo)
        
        # Processar em paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_single_image, produto): produto 
                for produto in produtos_validos
            }
            
            for future in as_completed(futures):
                try:
                    codigo, imagem_url = future.result()
                    results[codigo] = imagem_url
                except Exception as e:
                    produto = futures[future]
                    codigo = int(produto['Código'])
                    print(f'  ⚠ Erro ao processar imagem do produto {codigo}: {e}')
                    results[codigo] = self.get_product_image_url(codigo)
        
        return results
    
    def preprocess_all_images(self, progress_callback=None):
        """Pré-processa todas as imagens da tabela de preços"""
        print('\n' + '='*60)
        print('🔄 PRÉ-PROCESSAMENTO DE IMAGENS')
        print('='*60)
        
        # Ler CSV (usar mesma lógica de generate_banners)
        try:
            df = None
            sep_configs = [
                {'sep': ',', 'decimal': '.'},
                {'sep': ';', 'decimal': ','},
                {'sep': ';', 'decimal': '.'},
                {'sep': ',', 'decimal': ','},
                {'sep': '\t', 'decimal': ','}
            ]
            for encoding in ('utf-8-sig', 'utf-8', 'latin1'):
                for config in sep_configs:
                    try:
                        read_kwargs = {
                            'sep': config['sep'],
                            'encoding': encoding,
                            'engine': 'python'
                        }
                        if config.get('decimal') is not None:
                            read_kwargs['decimal'] = config['decimal']
                        candidate_df = pd.read_csv(CSV_FILE, **read_kwargs)
                        candidate_df.columns = candidate_df.columns.str.strip()
                        if 'Código' in candidate_df.columns:
                            df = candidate_df
                            break
                    except:
                        continue
                if df is not None:
                    break
            
            if df is None:
                raise Exception('Não foi possível ler o CSV')
            
            df.columns = df.columns.str.strip()
            
            # Obter códigos únicos
            codigos = df['Código'].dropna().unique()
            codigos = [int(float(str(c).strip())) for c in codigos if str(c).strip() and str(c).strip() != 'nan']
            
            print(f'📊 Total de produtos únicos: {len(codigos)}')
            
            # Filtrar apenas códigos que têm imagem no servidor
            codigos_com_imagem = []
            for codigo in codigos:
                if self.check_image_exists(codigo):
                    codigos_com_imagem.append(codigo)
            
            print(f'✓ Produtos com imagem disponível: {len(codigos_com_imagem)}')
            
            # Processar cada imagem
            processadas = 0
            em_cache = 0
            erros = 0
            
            for idx, codigo in enumerate(codigos_com_imagem, 1):
                # Verificar se já está em cache
                if os.path.exists(self.get_cache_path(codigo)):
                    em_cache += 1
                    if progress_callback:
                        progress_callback(idx, len(codigos_com_imagem), f'Cache: {codigo}')
                    continue
                
                # Processar
                if progress_callback:
                    progress_callback(idx, len(codigos_com_imagem), f'Processando: {codigo}')
                
                url = self.check_image_exists(codigo)
                if url:
                    resultado = self.remove_background(url, codigo=codigo, use_cache=False)
                    if resultado:
                        processadas += 1
                    else:
                        erros += 1
                else:
                    erros += 1
            
            print('\n' + '='*60)
            print('✅ PRÉ-PROCESSAMENTO CONCLUÍDO')
            print('='*60)
            print(f'✓ Imagens processadas agora: {processadas}')
            print(f'✓ Imagens já em cache: {em_cache}')
            print(f'⚠ Erros: {erros}')
            print(f'📊 Total: {len(codigos_com_imagem)}')
            print('='*60 + '\n')
            
            return {
                'processadas': processadas,
                'em_cache': em_cache,
                'erros': erros,
                'total': len(codigos_com_imagem)
            }
            
        except Exception as e:
            print(f'❌ Erro no pré-processamento: {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def calculate_discount_percentage(self, preco_comercial, preco_promocional):
        """Calcula percentual de desconto"""
        if preco_comercial <= 0:
            return 0
        return ((preco_comercial - preco_promocional) / preco_comercial) * 100
    
    def generate_starburst_clip_path(self):
        """Gera clip-path de círculo serrilhado (estrela) - equivalente à função JavaScript"""
        import math
        num_rays = 24  # Número de raios
        outer_radius = 50  # Raio externo em % (50% = borda do elemento)
        inner_radius = 44  # Raio interno em % (cria os vales entre os raios)
        center_x = 50  # Centro X em %
        center_y = 50  # Centro Y em %
        angle_step = (360.0 / num_rays) * (math.pi / 180.0)  # Passo angular em radianos
        
        points = []
        
        # Calcular pontos alternando entre raio externo e interno
        for i in range(num_rays * 2):
            angle = i * angle_step / 2  # Cada raio tem 2 pontos (externo e interno)
            is_outer_point = (i % 2) == 0  # Pontos pares são externos, ímpares são internos
            radius = outer_radius if is_outer_point else inner_radius
            
            # Calcular coordenadas usando trigonometria
            # Cos e Sin no SVG são medidos a partir do topo (0° = topo)
            x = center_x + radius * math.sin(angle)
            y = center_y - radius * math.cos(angle)
            
            points.append(f'{x:.2f}% {y:.2f}%')
        
        return f'polygon({", ".join(points)})'
    
    def generate_html_banner(self, produtos, unidade, nome_empresa=None, data_inicio='', data_fim=''):
        """Gera HTML do banner para os 3 produtos"""
        # Carregar imagens locais
        logo_ofertas_b64 = self.image_to_base64(os.path.join(self.images_folder, 'logo ofertas.png'))
        call_action_b64 = self.image_to_base64(os.path.join(self.images_folder, 'Call Action.png'))
        # Tentar carregar logo inferior (pode ser .png ou .jpg)
        logo_inferior_b64 = None
        logo_inferior_mime = 'image/png'
        logo_inferior_paths = [
            os.path.join(self.images_folder, 'Logo Inferior.png'),
            os.path.join(self.images_folder, 'Logo Inferior.jpg'),
            os.path.join(self.images_folder, 'logo inferior.png'),
            os.path.join(self.images_folder, 'logo inferior.jpg')
        ]
        logo_inferior_loaded_path = None
        for path in logo_inferior_paths:
            if os.path.exists(path):
                logo_inferior_b64 = self.image_to_base64(path)
                if logo_inferior_b64:
                    logo_inferior_loaded_path = path
                    if path.lower().endswith('.jpg') or path.lower().endswith('.jpeg'):
                        logo_inferior_mime = 'image/jpeg'
                    break
        if logo_inferior_b64:
            print(f'✓ Logo Inferior carregada: {logo_inferior_loaded_path}')
        else:
            print(f'⚠ Logo Inferior não encontrada na pasta {self.images_folder}')
        logo_superior_b64 = self.image_to_base64(os.path.join(self.images_folder, 'Logo.png'))
        base_produto_b64 = self.image_to_base64(os.path.join(self.images_folder, 'Base do Produto.png'))
        
        # Tentar carregar imagem de fundo (pode ser .png ou .jpg)
        fundo_b64 = self.image_to_base64(os.path.join(self.images_folder, 'Fundo.png'))
        if not fundo_b64:
            fundo_b64 = self.image_to_base64(os.path.join(self.images_folder, 'Fundo.jpg'))
        if not fundo_b64:
            fundo_b64 = self.image_to_base64(os.path.join(self.images_folder, 'fundo.png'))
        if not fundo_b64:
            fundo_b64 = self.image_to_base64(os.path.join(self.images_folder, 'fundo.jpg'))
        
        # Gerar HTML dos produtos
        # Função para gerar HTML do separador
        def generate_separador_html(position_percent):
            """Gera HTML do separador entre produtos"""
            separador_color = self.get_template_value('separador-color', '#CCCCCC')
            separador_width_raw = self.get_template_value('separador-width', 2)
            separador_width_value = self._safe_int_convert(separador_width_raw, 2)
            separador_width = f'{separador_width_value}px'
            
            separador_height_raw = self.get_template_value('separador-height', 100)
            separador_height_value = self._safe_int_convert(separador_height_raw, 100)
            separador_height = f'{separador_height_value}px'
            
            separador_top_raw = self.get_template_value('separador-top', 0)
            separador_top_value = self._safe_int_convert(separador_top_raw, 0)
            separador_top = f'{separador_top_value}px'
            
            separador_left_raw = self.get_template_value('separador-left', 0)
            separador_left_value = self._safe_int_convert(separador_left_raw, 0)
            
            # Calcular posição left baseada na porcentagem + ajuste
            left_calc = f'calc({position_percent}% + {separador_left_value}px)'
            
            return f'<div class="separador-produto" style="position: absolute; width: {separador_width}; height: {separador_height}; background-color: {separador_color}; top: {separador_top}; left: {left_calc}; transform: translateX(-50%); z-index: 15;"></div>'
        
        produtos_html = ''
        produto_index = 0
        for produto in produtos:
            codigo = int(produto['Código'])
            nome = produto['Nome']
            preco_comercial = float(produto['Preço Comercial'])
            preco_promocional = float(produto['Preço Promocional'])
            desconto_pct = self.calculate_discount_percentage(preco_comercial, preco_promocional)
            
            # Ler colunas opcionais: Unidade de Medida e Bandeira
            unidade_medida = produto.get('Unidade de Medida', '').strip() if 'Unidade de Medida' in produto else ''
            bandeira = produto.get('Bandeira', '').strip() if 'Bandeira' in produto else ''
            # Usar imagem processada se disponível (processamento paralelo), senão processar normalmente
            if '_imagem_url_processada' in produto:
                imagem_url = produto['_imagem_url_processada']
            else:
                imagem_url = self.get_product_image_with_background_removed(codigo)
            
            # Obter valores do template
            padding = self.format_css_value('produto-container-padding', self.get_template_value('produto-container-padding', 15))
            bg_color_hex = self.get_template_value('produto-container-bg-color', '#FFFFFF')
            bg_opacity_raw = self.get_template_value('produto-container-bg-opacity', 90)
            # Converter opacidade para 0-1 se necessário
            if isinstance(bg_opacity_raw, (int, float)):
                bg_opacity = bg_opacity_raw / 100.0 if bg_opacity_raw > 1 else bg_opacity_raw
            else:
                try:
                    bg_opacity_val = float(bg_opacity_raw)
                    bg_opacity = bg_opacity_val / 100.0 if bg_opacity_val > 1 else bg_opacity_val
                except:
                    bg_opacity = 0.9
            # Converter cor hex para RGB
            bg_color_hex = bg_color_hex.lstrip('#')
            # Se a opacidade for 0, retornar transparente
            if bg_opacity == 0:
                bg_color = 'transparent'
            elif len(bg_color_hex) == 6:
                r = int(bg_color_hex[0:2], 16)
                g = int(bg_color_hex[2:4], 16)
                b = int(bg_color_hex[4:6], 16)
                bg_color = f'rgba({r}, {g}, {b}, {bg_opacity})'
            else:
                bg_color = f'rgba(255, 255, 255, {bg_opacity})'
            border_radius = self.format_css_value('produto-container-border-radius', self.get_template_value('produto-container-border-radius', 15))
            
            # Se opacidade for 0, remover box-shadow e border
            container_shadow = 'none' if bg_opacity == 0 else '0 2px 8px rgba(0,0,0,0.1)'
            
            # Obter valores da base do produto
            base_bottom_raw = self.get_template_value('base-produto-bottom', -100)
            # Se for string "0", converter para 0
            if isinstance(base_bottom_raw, str) and base_bottom_raw.strip() == '0':
                base_bottom_raw = 0
            base_bottom = self.format_css_value('base-produto-bottom', base_bottom_raw)
            base_left = self.format_css_value('base-produto-left', self.get_template_value('base-produto-left', 50))
            base_width = self.format_css_value('base-produto-width', self.get_template_value('base-produto-width', 200))
            base_max_width = self.format_css_value('base-produto-max-width', self.get_template_value('base-produto-max-width', 500))
            base_height = self.format_css_value('base-produto-height', self.get_template_value('base-produto-height', 0))
            base_opacity_raw = self.get_template_value('base-produto-opacity', 90)
            # Converter opacidade para 0-1 se necessário
            if isinstance(base_opacity_raw, (int, float)):
                base_opacity = base_opacity_raw / 100.0 if base_opacity_raw > 1 else base_opacity_raw
            else:
                try:
                    base_opacity_val = float(base_opacity_raw)
                    base_opacity = base_opacity_val / 100.0 if base_opacity_val > 1 else base_opacity_val
                except:
                    base_opacity = 0.9
            base_opacity = str(base_opacity)
            
            base_produto_img = f'<img class="base-produto" src="data:image/png;base64,{base_produto_b64}" alt="Base" style="position: absolute; bottom: {base_bottom}; left: {base_left}; transform: translateX(-50%); width: {base_width}; max-width: {base_max_width}; height: {base_height}; opacity: {base_opacity}; object-fit: contain; z-index: 1;" />' if base_produto_b64 else ''
            
            # Obter max-width do container de produto
            produto_item_max_width = self.format_css_value('produto-item-max-width', self.get_template_value('produto-item-max-width', 320))
            
            desconto_badge_top = self.format_css_value('desconto-badge-top', self.get_template_value('desconto-badge-top', 8))
            desconto_badge_right = self.format_css_value('desconto-badge-right', self.get_template_value('desconto-badge-right', 8))
            
            # Usar format_css_value diretamente - ele já trata valores 0 retornando 'auto'
            badge_bottom = self.format_css_value('desconto-badge-bottom', self.get_template_value('desconto-badge-bottom', 0))
            badge_left = self.format_css_value('desconto-badge-left', self.get_template_value('desconto-badge-left', 0))
            
            badge_shape = str(self.get_template_value('desconto-badge-shape', 'pill')).lower()
            if badge_shape == 'circle':
                badge_radius = '50%'
                badge_clip_path = None
            elif badge_shape == 'starburst':
                badge_radius = '0'
                badge_clip_path = self.generate_starburst_clip_path()
            else:
                badge_radius = '18px'
                badge_clip_path = None
            
            badge_border_width_raw = self.get_template_value('desconto-badge-border-width', 0)
            try:
                badge_border_width_int = int(float(str(badge_border_width_raw).strip().lower().replace('px', '').replace(',', '.')))
            except (ValueError, TypeError):
                badge_border_width_int = 0
            badge_border_color = self.get_template_value('desconto-badge-border-color', '#FFFFFF')
            badge_border = f'{badge_border_width_int}px solid {badge_border_color}' if badge_border_width_int > 0 else 'none'
            
            badge_width = self.format_css_value('desconto-badge-width', self.get_template_value('desconto-badge-width', 0))
            badge_height = self.format_css_value('desconto-badge-height', self.get_template_value('desconto-badge-height', 0))
            badge_font_size = self.format_css_value('desconto-badge-font-size', self.get_template_value('desconto-badge-font-size', 16))
            badge_bg_color = self.get_template_value('desconto-badge-bg-color', '#FF0000')
            badge_text_color = self.get_template_value('desconto-badge-color', '#FFFFFF')
            
            badge_style_parts = [
                'position: absolute',
                f'background-color: {badge_bg_color}',
                f'color: {badge_text_color}',
                'padding: 8px 16px',
                f'font-size: {badge_font_size}',
                'font-weight: bold',
                f'width: {badge_width}',
                f'height: {badge_height}',
                'display: flex',
                'flex-direction: column',
                'align-items: center',
                'justify-content: center',
                'text-align: center',
                'white-space: normal',
                'pointer-events: none',
                'box-sizing: border-box',
                'min-width: fit-content',
                'box-shadow: 0 4px 12px rgba(0,0,0,0.25)',
                'z-index: 60',
                f'border-radius: {badge_radius}'
            ]
            
            # Adicionar clip-path se for formato estrela
            if badge_clip_path:
                badge_style_parts.append(f'clip-path: {badge_clip_path}')
            
            # Lógica de posicionamento do badge - deve corresponder exatamente ao JavaScript
            if badge_bottom == 'auto' and desconto_badge_top != 'auto':
                badge_style_parts.append(f'top: {desconto_badge_top}')
            if badge_left == 'auto' and desconto_badge_right != 'auto':
                badge_style_parts.append(f'right: {desconto_badge_right}')
            if badge_bottom != 'auto':
                badge_style_parts.append(f'bottom: {badge_bottom}')
            if badge_left != 'auto':
                badge_style_parts.append(f'left: {badge_left}')
            
            if badge_border != 'none':
                badge_style_parts.append(f'border: {badge_border}')
            else:
                badge_style_parts.append('border: none')
            
            badge_style = '; '.join(badge_style_parts) + ';'

            produto_nome_font_size = self.format_css_value('produto-nome-font-size', self.get_template_value('produto-nome-font-size', 16))
            produto_nome_color = self.get_template_value('produto-nome-color', '#1a1a1a')
            produto_nome_font_family = self.get_template_value('produto-nome-font-family', "'Montserrat', sans-serif")
            # Garantir que a fonte está no formato correto (remover aspas extras se necessário)
            if produto_nome_font_family and not produto_nome_font_family.startswith("'"):
                # Se não começa com aspas simples, adicionar
                if 'Goldplay' in produto_nome_font_family or 'GoldplayAlt' in produto_nome_font_family:
                    produto_nome_font_family = f"'{produto_nome_font_family.split(',')[0]}', sans-serif" if ',' not in produto_nome_font_family else produto_nome_font_family
            produto_nome_font_weight = self.get_template_value('produto-nome-font-weight', 'bold')
            produto_nome_font_style = self.get_template_value('produto-nome-font-style', 'normal')

            produto_codigo_font_size = self.format_css_value('produto-codigo-font-size', self.get_template_value('produto-codigo-font-size', 14))
            produto_codigo_color = self.get_template_value('produto-codigo-color', '#666666')
            produto_codigo_font_family = self.get_template_value('produto-codigo-font-family', "'Roboto', sans-serif")
            # Garantir que a fonte está no formato correto
            if produto_codigo_font_family and not produto_codigo_font_family.startswith("'"):
                if 'Goldplay' in produto_codigo_font_family or 'GoldplayAlt' in produto_codigo_font_family:
                    produto_codigo_font_family = f"'{produto_codigo_font_family.split(',')[0]}', sans-serif" if ',' not in produto_codigo_font_family else produto_codigo_font_family
            produto_codigo_font_weight = self.get_template_value('produto-codigo-font-weight', 'normal')
            produto_codigo_font_style = self.get_template_value('produto-codigo-font-style', 'normal')
            
            # Extrair valor numérico do font-size do código do produto
            produto_codigo_font_size_num = 14  # padrão
            if isinstance(produto_codigo_font_size, str):
                produto_codigo_font_size_num = float(produto_codigo_font_size.replace('px', '').replace('em', '').replace('%', '').strip() or '14')
            elif isinstance(produto_codigo_font_size, (int, float)):
                produto_codigo_font_size_num = float(produto_codigo_font_size)
            
            # Posicionamento
            produto_nome_top = self._safe_int_convert(self.get_template_value('produto-nome-top', 0), 0)
            produto_nome_left = self._safe_int_convert(self.get_template_value('produto-nome-left', 0), 0)
            
            # Calcular altura máxima para 3 linhas (baseado no font-size)
            # Extrair valor numérico do font-size
            produto_nome_font_size_num = 16  # padrão
            if isinstance(produto_nome_font_size, str):
                produto_nome_font_size_num = float(produto_nome_font_size.replace('px', '').replace('em', '').replace('%', '').strip() or '16')
            elif isinstance(produto_nome_font_size, (int, float)):
                produto_nome_font_size_num = float(produto_nome_font_size)
            # Altura máxima = line-height (1.2) * font-size * 3 linhas
            produto_nome_max_height = produto_nome_font_size_num * 1.2 * 3
            
            # Extrair largura numérica do container de produto para o container do nome
            produto_item_max_width_num = 320  # padrão
            if isinstance(produto_item_max_width, str):
                produto_item_max_width_num = float(produto_item_max_width.replace('px', '').replace('em', '').replace('%', '').strip() or '320')
            elif isinstance(produto_item_max_width, (int, float)):
                produto_item_max_width_num = float(produto_item_max_width)
            # Largura do container do nome = largura do item - padding lateral (40px)
            produto_nome_container_width = produto_item_max_width_num - 40
            
            produto_codigo_top = self._safe_int_convert(self.get_template_value('produto-codigo-top', 0), 0)
            produto_codigo_left = self._safe_int_convert(self.get_template_value('produto-codigo-left', 0), 0)
            preco_de_top = self._safe_int_convert(self.get_template_value('preco-de-top', 0), 0)
            preco_de_left = self._safe_int_convert(self.get_template_value('preco-de-left', 0), 0)
            preco_comercial_top = self._safe_int_convert(self.get_template_value('preco-comercial-top', 0), 0)
            preco_comercial_left = self._safe_int_convert(self.get_template_value('preco-comercial-left', 0), 0)
            preco_por_top = self._safe_int_convert(self.get_template_value('preco-por-top', 0), 0)
            preco_por_left = self._safe_int_convert(self.get_template_value('preco-por-left', 0), 0)
            preco_promocional_top = self._safe_int_convert(self.get_template_value('preco-promocional-top', 0), 0)
            preco_promocional_left = self._safe_int_convert(self.get_template_value('preco-promocional-left', 0), 0)

            preco_comercial_font_size = self.format_css_value('preco-comercial-font-size', self.get_template_value('preco-comercial-font-size', 14))
            preco_comercial_color = self.get_template_value('preco-comercial-color', '#e53935')
            preco_comercial_font_family = self.get_template_value('preco-comercial-font-family', "'Roboto', sans-serif")
            # Garantir que a fonte está no formato correto
            if preco_comercial_font_family and not preco_comercial_font_family.startswith("'"):
                if 'Goldplay' in preco_comercial_font_family or 'GoldplayAlt' in preco_comercial_font_family:
                    preco_comercial_font_family = f"'{preco_comercial_font_family.split(',')[0]}', sans-serif" if ',' not in preco_comercial_font_family else preco_comercial_font_family
            preco_comercial_font_weight = self.get_template_value('preco-comercial-font-weight', 'normal')
            preco_comercial_font_style = self.get_template_value('preco-comercial-font-style', 'normal')

            preco_promocional_font_size = self.format_css_value('preco-promocional-font-size', self.get_template_value('preco-promocional-font-size', 28))
            preco_promocional_color = self.get_template_value('preco-promocional-color', '#FF6B00')
            preco_promocional_font_family = self.get_template_value('preco-promocional-font-family', "'Montserrat', sans-serif")
            # Garantir que a fonte está no formato correto
            if preco_promocional_font_family and not preco_promocional_font_family.startswith("'"):
                if 'Goldplay' in preco_promocional_font_family or 'GoldplayAlt' in preco_promocional_font_family:
                    preco_promocional_font_family = f"'{preco_promocional_font_family.split(',')[0]}', sans-serif" if ',' not in preco_promocional_font_family else preco_promocional_font_family
            preco_promocional_font_weight = self.get_template_value('preco-promocional-font-weight', 'bold')
            preco_promocional_font_style = self.get_template_value('preco-promocional-font-style', 'normal')
            
            # Configurações para labels DE e POR (podem ter tamanhos de fonte independentes)
            # Se não existir no template, usar o valor numérico de produto_nome_font_size como padrão
            produto_nome_font_size_num_for_default = 16
            if isinstance(produto_nome_font_size, str):
                produto_nome_font_size_num_for_default = float(produto_nome_font_size.replace('px', '').replace('em', '').replace('%', '').strip() or '16')
            elif isinstance(produto_nome_font_size, (int, float)):
                produto_nome_font_size_num_for_default = float(produto_nome_font_size)
            
            preco_de_font_size_default = self.get_template_value('preco-de-font-size', produto_nome_font_size_num_for_default)
            preco_de_font_size = self.format_css_value('preco-de-font-size', preco_de_font_size_default)
            
            preco_por_font_size_default = self.get_template_value('preco-por-font-size', produto_nome_font_size_num_for_default)
            preco_por_font_size = self.format_css_value('preco-por-font-size', preco_por_font_size_default)
            
            # Configurações para label "POR [Unidade]" (similar às labels DE e POR)
            preco_por_unidade_font_size_default = self.get_template_value('preco-por-unidade-font-size', produto_nome_font_size_num_for_default)
            preco_por_unidade_font_size = self.format_css_value('preco-por-unidade-font-size', preco_por_unidade_font_size_default)
            preco_por_unidade_top = self._safe_int_convert(self.get_template_value('preco-por-unidade-top', 0), 0)
            preco_por_unidade_left = self._safe_int_convert(self.get_template_value('preco-por-unidade-left', 0), 0)
            
            # Carregar imagem da bandeira se existir
            bandeira_b64 = None
            bandeira_mime = 'image/png'
            if bandeira:
                # Tentar Cloudinary primeiro se habilitado
                if USE_CLOUDINARY:
                    try:
                        bandeira_b64 = get_image_base64_from_cloudinary(bandeira, folder='bandeiras')
                        if bandeira_b64:
                            print(f'  ✓ Bandeira carregada do Cloudinary: {bandeira}')
                    except Exception as e:
                        print(f'  ⚠ Erro ao buscar bandeira do Cloudinary: {e}. Tentando local...')
                
                # Fallback para arquivo local
                if not bandeira_b64:
                    bandeira_folder = 'Bandeira'
                    # Tentar diferentes extensões
                    for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                        bandeira_path = os.path.join(bandeira_folder, f'{bandeira}{ext}')
                        if os.path.exists(bandeira_path):
                            bandeira_b64 = self.image_to_base64(bandeira_path)
                            if bandeira_b64:
                                if ext.lower() in ['.jpg', '.jpeg']:
                                    bandeira_mime = 'image/jpeg'
                                break
            
            # Configurações para imagem da bandeira
            # Verificar se há valores definidos nos controles, senão usar do badge
            bandeira_width_raw = self.get_template_value('bandeira-width', 0)
            bandeira_height_raw = self.get_template_value('bandeira-height', 0)
            bandeira_top_raw = self.get_template_value('bandeira-top', 'auto')
            bandeira_right_raw = self.get_template_value('bandeira-right', 'auto')
            bandeira_bottom_raw = self.get_template_value('bandeira-bottom', 0)
            bandeira_left_raw = self.get_template_value('bandeira-left', 'auto')
            
            # Se width/height não estiver definido (0 ou auto), usar do badge
            if bandeira_width_raw == 0 or bandeira_width_raw == '0' or (isinstance(bandeira_width_raw, str) and bandeira_width_raw.lower() == 'auto'):
                bandeira_width = badge_width
            else:
                bandeira_width = self.format_css_value('bandeira-width', bandeira_width_raw)
            
            if bandeira_height_raw == 0 or bandeira_height_raw == '0' or (isinstance(bandeira_height_raw, str) and bandeira_height_raw.lower() == 'auto'):
                bandeira_height = badge_height
            else:
                bandeira_height = self.format_css_value('bandeira-height', bandeira_height_raw)
            
            # Extrair valores numéricos do badge para cálculo de posição (quando necessário)
            badge_top_value = 8  # padrão
            badge_right_value = 8  # padrão
            badge_bottom_value = 0
            badge_left_value = 0
            badge_height_value = 60  # altura padrão estimada
            
            if desconto_badge_top != 'auto':
                try:
                    badge_top_value = int(float(str(desconto_badge_top).replace('px', '')))
                except:
                    badge_top_value = 8
            if desconto_badge_right != 'auto':
                try:
                    badge_right_value = int(float(str(desconto_badge_right).replace('px', '')))
                except:
                    badge_right_value = 8
            if badge_height != 'auto':
                try:
                    badge_height_value = int(float(str(badge_height).replace('px', '').replace('%', '')))
                except:
                    badge_height_value = 60
            else:
                # Se badge_height é auto, tentar estimar pela font-size + padding
                try:
                    font_size_val = int(float(str(badge_font_size).replace('px', '')))
                    badge_height_value = font_size_val * 2 + 16  # font-size * 2 linhas + padding
                except:
                    badge_height_value = 60
            
            # Calcular altura da bandeira para posicionamento
            if bandeira_height != 'auto':
                try:
                    bandeira_height_value = int(float(str(bandeira_height).replace('px', '').replace('%', '')))
                except:
                    bandeira_height_value = badge_height_value
            else:
                bandeira_height_value = badge_height_value
            
            # Posicionamento horizontal: usar valores dos controles se definidos, senão usar do badge
            if bandeira_right_raw == 'auto' or bandeira_right_raw == 0 or bandeira_right_raw == '0':
                bandeira_right = desconto_badge_right  # Usar do badge
            else:
                bandeira_right = self.format_css_value('bandeira-right', bandeira_right_raw)
            
            if bandeira_left_raw == 'auto' or bandeira_left_raw == 0 or bandeira_left_raw == '0':
                bandeira_left = badge_left  # Usar do badge
            else:
                bandeira_left = self.format_css_value('bandeira-left', bandeira_left_raw)
            
            # SEMPRE calcular posição ABAIXO do badge, independente dos controles
            # Isso garante que a bandeira nunca fique sobreposta ao badge
            if badge_bottom == 'auto' and desconto_badge_top != 'auto':
                # Badge está posicionado por TOP, bandeira vai ABAIXO (top maior)
                bandeira_top_calculated = badge_top_value + badge_height_value + 5  # 5px de espaçamento
                # Se os controles estão definidos, verificar se estão abaixo do mínimo necessário
                if bandeira_top_raw != 'auto' and bandeira_top_raw != 0 and bandeira_top_raw != '0':
                    try:
                        bandeira_top_num = int(float(str(bandeira_top_raw).replace('px', '')))
                        if bandeira_top_num < bandeira_top_calculated:
                            # Valor definido está acima do mínimo, usar o mínimo
                            bandeira_top = f'{bandeira_top_calculated}px'
                        else:
                            # Valor definido está OK, usar ele
                            bandeira_top = f'{bandeira_top_num}px'
                    except:
                        bandeira_top = f'{bandeira_top_calculated}px'
                else:
                    bandeira_top = f'{bandeira_top_calculated}px'
                bandeira_bottom = 'auto'
            elif badge_bottom != 'auto':
                # Badge está posicionado por BOTTOM, calcular top da bandeira para ficar ABAIXO
                try:
                    badge_bottom_num = int(float(str(badge_bottom).replace('px', '')))
                    # Obter altura do container de imagem para calcular posição
                    imagem_container_height_raw = self.get_template_value('produto-imagem-container-height', 420)
                    try:
                        imagem_container_height = int(float(str(imagem_container_height_raw).replace('px', '')))
                    except:
                        imagem_container_height = 420
                    # Top do badge = altura_container - bottom_badge - altura_badge
                    # Top da bandeira = top_badge + altura_badge + espaçamento (para ficar ABAIXO)
                    badge_top_from_bottom = imagem_container_height - badge_bottom_num - badge_height_value
                    bandeira_top_calculated = badge_top_from_bottom + badge_height_value + 5
                    
                    # Validar que está dentro do container
                    if bandeira_top_calculated > 0 and bandeira_top_calculated < imagem_container_height:
                        # Se os controles estão definidos, verificar se estão abaixo do mínimo necessário
                        if bandeira_top_raw != 'auto' and bandeira_top_raw != 0 and bandeira_top_raw != '0':
                            try:
                                bandeira_top_num = int(float(str(bandeira_top_raw).replace('px', '')))
                                if bandeira_top_num < bandeira_top_calculated:
                                    # Valor definido está acima do mínimo, usar o mínimo
                                    bandeira_top = f'{bandeira_top_calculated}px'
                                else:
                                    # Valor definido está OK, usar ele
                                    bandeira_top = f'{bandeira_top_num}px'
                            except:
                                bandeira_top = f'{bandeira_top_calculated}px'
                        elif bandeira_bottom_raw != 0 and bandeira_bottom_raw != '0' and bandeira_bottom_raw != 'auto':
                            # Usando bottom, converter para top e validar
                            try:
                                bandeira_bottom_num = int(float(str(bandeira_bottom_raw).replace('px', '')))
                                bandeira_top_equivalent = imagem_container_height - bandeira_bottom_num - bandeira_height_value
                                if bandeira_top_equivalent < bandeira_top_calculated:
                                    # Posição está acima do mínimo, usar top calculado
                                    bandeira_top = f'{bandeira_top_calculated}px'
                                    bandeira_bottom = 'auto'
                                else:
                                    # Posição está OK, usar bottom original
                                    bandeira_bottom = self.format_css_value('bandeira-bottom', bandeira_bottom_raw)
                                    bandeira_top = 'auto'
                            except:
                                bandeira_top = f'{bandeira_top_calculated}px'
                                bandeira_bottom = 'auto'
                        else:
                            bandeira_top = f'{bandeira_top_calculated}px'
                            bandeira_bottom = 'auto'
                    else:
                        # Se deu fora do container, usar top simples baseado no badge
                        bandeira_top_calculated = badge_top_value + badge_height_value + 5
                        bandeira_top = f'{bandeira_top_calculated}px'
                        bandeira_bottom = 'auto'
                except:
                    # Fallback: calcular por top
                    bandeira_top_calculated = badge_top_value + badge_height_value + 5
                    bandeira_top = f'{bandeira_top_calculated}px'
                    bandeira_bottom = 'auto'
            else:
                # Fallback: calcular por top
                bandeira_top_calculated = badge_top_value + badge_height_value + 5
                # Se os controles estão definidos, validar
                if bandeira_top_raw != 'auto' and bandeira_top_raw != 0 and bandeira_top_raw != '0':
                    try:
                        bandeira_top_num = int(float(str(bandeira_top_raw).replace('px', '')))
                        if bandeira_top_num < bandeira_top_calculated:
                            bandeira_top = f'{bandeira_top_calculated}px'
                        else:
                            bandeira_top = f'{bandeira_top_num}px'
                    except:
                        bandeira_top = f'{bandeira_top_calculated}px'
                else:
                    bandeira_top = f'{bandeira_top_calculated}px'
                bandeira_bottom = 'auto'
            
            # Construir estilo da bandeira (mesmas dimensões, logo abaixo)
            # z-index menor que o badge para garantir que a bandeira fique ABAIXO e visível
            bandeira_style_parts = [
                'position: absolute',
                f'width: {bandeira_width}',
                f'height: {bandeira_height}',
                'object-fit: cover',
                'object-position: center',
                'z-index: 2'
            ]
            
            # Posicionamento: mesma lógica horizontal do badge, vertical logo abaixo
            if bandeira_bottom == 'auto' and bandeira_top != 'auto':
                bandeira_style_parts.append(f'top: {bandeira_top}')
            if bandeira_left == 'auto' and bandeira_right != 'auto':
                bandeira_style_parts.append(f'right: {bandeira_right}')
            if bandeira_bottom != 'auto':
                bandeira_style_parts.append(f'bottom: {bandeira_bottom}')
            if bandeira_left != 'auto':
                bandeira_style_parts.append(f'left: {bandeira_left}')
            
            bandeira_style = '; '.join(bandeira_style_parts) + ';'
            
            # Configurações separadas para R$ e parte decimal
            preco_rs_color = self.get_template_value('preco-rs-color', '#FF6B00')
            preco_rs_font_size_raw = self.get_template_value('preco-rs-font-size', 0.5)
            preco_rs_font_size = f"{float(preco_rs_font_size_raw)}em" if isinstance(preco_rs_font_size_raw, (int, float)) else str(preco_rs_font_size_raw) if isinstance(preco_rs_font_size_raw, str) and 'em' in preco_rs_font_size_raw else f"{float(str(preco_rs_font_size_raw).replace('em', ''))}em"
            preco_rs_vertical_align = self.get_template_value('preco-rs-vertical-align', 'center')
            
            preco_decimal_color = self.get_template_value('preco-decimal-color', '#FF6B00')
            preco_decimal_font_size_raw = self.get_template_value('preco-decimal-font-size', 0.65)
            preco_decimal_font_size = f"{float(preco_decimal_font_size_raw)}em" if isinstance(preco_decimal_font_size_raw, (int, float)) else str(preco_decimal_font_size_raw) if isinstance(preco_decimal_font_size_raw, str) and 'em' in preco_decimal_font_size_raw else f"{float(str(preco_decimal_font_size_raw).replace('em', ''))}em"
            preco_decimal_vertical_align = self.get_template_value('preco-decimal-vertical-align', 'top')
            
            # Formatar preço promocional com tamanhos diferentes: R$ (menor), valor antes vírgula (maior), centavos (menor)
            def format_price_promocional(price):
                price_str = f"{price:.2f}"
                parts = price_str.split('.')
                integer_part = parts[0]
                decimal_part = parts[1] if len(parts) > 1 else "00"
                return f'<span class="preco-rs" style="font-size: {preco_rs_font_size}; color: {preco_rs_color}; align-self: {preco_rs_vertical_align}; margin-right: 5px;">R$</span><span class="preco-inteiro">{integer_part}</span><span class="preco-virgula" style="font-size: {preco_decimal_font_size}; color: {preco_decimal_color}; vertical-align: {preco_decimal_vertical_align};">,</span><span class="preco-decimal" style="font-size: {preco_decimal_font_size}; color: {preco_decimal_color}; vertical-align: {preco_decimal_vertical_align};">{decimal_part}</span>'
            
            # Formatar preço comercial (mantém formato simples)
            def format_price_comercial(price):
                price_str = f"{price:.2f}"
                parts = price_str.split('.')
                integer_part = parts[0]
                decimal_part = parts[1] if len(parts) > 1 else "00"
                return f'<span class="preco-comercial-rs">R$</span><span class="preco-comercial-valor-num">{integer_part},{decimal_part}</span>'
            
            # Verificar opacidade do container de imagem para remover sombras quando transparente
            imagem_container_bg = self.get_imagem_container_bg_color()
            imagem_container_shadow = 'none' if imagem_container_bg == 'transparent' else 'none'
            
            produtos_html += f'''
            <div class="produto-item" style="padding: 15px 12px 35px 12px; overflow: visible; max-width: {produto_item_max_width};">
                <div class="produto-container" style="padding: {padding}; background: {bg_color}; border-radius: {border_radius}; box-shadow: {container_shadow}; border: none;">
                    <div class="produto-imagem-container" style="position: relative; background: {imagem_container_bg}; border-radius: 15px; padding: 25px 20px; margin-bottom: {self.format_css_value('produto-imagem-container-margin-bottom', self.get_template_value('produto-imagem-container-margin-bottom', 30))}; height: {self.format_css_value('produto-imagem-container-height', self.get_template_value('produto-imagem-container-height', 420))}; display: flex; align-items: flex-start; justify-content: center; box-shadow: {imagem_container_shadow}; border: none;">
                        <img class="produto-imagem" src="{imagem_url}" alt="{nome}" style="position: absolute; top: {self.format_css_value('produto-imagem-top', self.get_template_value('produto-imagem-top', 20))}; left: {self.format_css_value('produto-imagem-left', self.get_template_value('produto-imagem-left', 50))}; transform: translateX(-50%); width: {self.format_css_value('produto-imagem-width', self.get_template_value('produto-imagem-width', 80))}; max-width: {self.format_css_value('produto-imagem-max-width', self.get_template_value('produto-imagem-max-width', 200))}; height: {self.format_css_value('produto-imagem-height', self.get_template_value('produto-imagem-height', 0))}; max-height: {self.format_css_value('produto-imagem-max-height', self.get_template_value('produto-imagem-max-height', 240))}; object-fit: contain; z-index: 2;">
                        {f'<div class="desconto-badge" style="{badge_style}"><div style="line-height: 1; font-weight: bold;">{desconto_pct:.0f}%</div><div style="line-height: 1; font-size: 0.65em; font-weight: normal; margin-top: 2px;">OFF</div></div>' if desconto_pct > 5 else ''}
                        {f'<img class="bandeira-imagem" src="data:image/{bandeira_mime};base64,{bandeira_b64}" alt="Bandeira {bandeira}" style="{bandeira_style}" />' if bandeira_b64 else ''}
                        {base_produto_img}
                    </div>
                    <div class="produto-info" style="padding: 10px 5px; position: relative;">
                        <div class="produto-nome-container" style="position: absolute; top: {produto_nome_top}px; left: {produto_nome_left}px; width: {produto_nome_container_width}px; height: {produto_nome_max_height}px; overflow: hidden; display: flex; align-items: center; justify-content: center; z-index: 1;">
                            <div class="produto-nome" data-original-font-size="{produto_nome_font_size_num}" style="font-size: {produto_nome_font_size}; color: {produto_nome_color}; font-family: {produto_nome_font_family}; font-weight: {produto_nome_font_weight}; font-style: {produto_nome_font_style}; text-align: center; padding: 0 5px; width: 100%; max-height: {produto_nome_max_height}px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; word-wrap: break-word; word-break: break-word; box-sizing: border-box;">{nome}</div>
                        </div>
                        <div class="produto-codigo" style="font-size: {produto_codigo_font_size}; color: {produto_codigo_color}; font-family: {produto_codigo_font_family}; font-weight: {produto_codigo_font_weight}; font-style: {produto_codigo_font_style}; margin-bottom: 8px; position: relative; top: {produto_codigo_top}px; left: {produto_codigo_left}px; text-align: center; display: inline-block;">COD. {codigo}</div>
                        <div class="precos" style="text-align: center; margin-bottom: 8px; display: flex; flex-direction: column; align-items: center; gap: 6px;">
                            <div class="preco-linhas" style="display: flex; gap: 16px; align-items: baseline; justify-content: center; flex-wrap: wrap; position: relative;">
                                <span class="preco-label preco-label-de" style="font-family: {produto_nome_font_family}; font-weight: {produto_nome_font_weight}; font-style: {produto_nome_font_style}; color: {produto_nome_color}; font-size: {preco_de_font_size}; position: relative; top: {preco_de_top}px; left: {preco_de_left}px; display: inline-block; pointer-events: auto;">DE</span>
                                <span class="preco-comercial-valor" style="font-family: {preco_comercial_font_family}; font-weight: {preco_comercial_font_weight}; font-style: {preco_comercial_font_style}; font-size: {preco_comercial_font_size}; color: {preco_comercial_color}; display: inline-flex; align-items: baseline; position: relative; top: {preco_comercial_top}px; left: {preco_comercial_left}px; pointer-events: auto;">{format_price_comercial(preco_comercial)}</span>
                                <span class="preco-label preco-label-por" style="font-family: {produto_nome_font_family}; font-weight: {produto_nome_font_weight}; font-style: {produto_nome_font_style}; color: {produto_nome_color}; font-size: {preco_por_font_size}; position: relative; top: {preco_por_top}px; left: {preco_por_left}px; display: inline-block; pointer-events: auto;">POR</span>
                            </div>
                            <div class="preco-linha-promocional" style="display: flex; gap: 8px; align-items: baseline; justify-content: center; position: relative; width: 100%; margin-top: {preco_promocional_top}px;">
                                <span class="preco-promocional" style="font-size: {preco_promocional_font_size}; color: {preco_promocional_color}; font-family: {preco_promocional_font_family}; font-weight: {preco_promocional_font_weight}; font-style: {preco_promocional_font_style}; display: inline-flex; align-items: flex-start; line-height: 1; position: relative; left: {preco_promocional_left}px; pointer-events: auto;">{format_price_promocional(preco_promocional)}</span>
                            </div>
                            {f'<div class="preco-linha-por-unidade" style="display: flex; gap: 8px; align-items: baseline; justify-content: center; position: relative; width: 100%; margin-top: {preco_por_unidade_top}px;"><span class="preco-label preco-label-por-unidade" style="font-family: {produto_nome_font_family}; font-weight: {produto_nome_font_weight}; font-style: {produto_nome_font_style}; color: {produto_nome_color}; font-size: {preco_por_unidade_font_size}; position: relative; left: {preco_por_unidade_left}px; display: inline-block; pointer-events: auto;">POR {unidade_medida}</span></div>' if unidade_medida else ''}
                        </div>
                    </div>
                </div>
            </div>
            '''
            
            # Adicionar separador após o produto (exceto o último)
            produto_index += 1
            # Se houver mais produtos, adicionar separador
            # Para 3 produtos: separador após produto 1 (33.333%) e após produto 2 (66.666%)
            # Para 2 produtos: separador após produto 1 (50%)
            if produto_index < len(produtos):
                # Calcular posição baseada na quantidade de produtos
                if len(produtos) == 3:
                    # 3 produtos: separador em 33.333% e 66.666%
                    position_percent = 33.333 * produto_index
                elif len(produtos) == 2:
                    # 2 produtos: separador em 50%
                    position_percent = 50.0
                else:
                    # Mais de 3 produtos: distribuir igualmente
                    position_percent = (100.0 / len(produtos)) * produto_index
                produtos_html += generate_separador_html(position_percent)
        
        # Obter valores das logos do template
        logo_superior_top = self.format_css_value('logo-superior-top', self.get_template_value('logo-superior-top', 20))
        logo_superior_right = self.format_css_value('logo-superior-right', self.get_template_value('logo-superior-right', 20))
        logo_superior_width = self.format_css_value('logo-superior-width', self.get_template_value('logo-superior-width', 150))
        logo_superior_height = self.format_css_value('logo-superior-height', self.get_template_value('logo-superior-height', 0))
        
        # Obter valores da logo inferior e tratar string "0" se necessário
        logo_inferior_bottom_raw = self.get_template_value('logo-inferior-bottom', 20)
        if isinstance(logo_inferior_bottom_raw, str) and logo_inferior_bottom_raw.strip() == '0':
            logo_inferior_bottom_raw = 0
        logo_inferior_bottom = self.format_css_value('logo-inferior-bottom', logo_inferior_bottom_raw)
        logo_inferior_left = self.format_css_value('logo-inferior-left', self.get_template_value('logo-inferior-left', 50))
        logo_inferior_width = self.format_css_value('logo-inferior-width', self.get_template_value('logo-inferior-width', 350))
        logo_inferior_height = self.format_css_value('logo-inferior-height', self.get_template_value('logo-inferior-height', 80))
        
        # Obter valores da logo ofertas
        logo_ofertas_top = self.format_css_value('logo-ofertas-top', self.get_template_value('logo-ofertas-top', 50))
        logo_ofertas_width = self.format_css_value('logo-ofertas-width', self.get_template_value('logo-ofertas-width', 450))
        logo_ofertas_height = self.format_css_value('logo-ofertas-height', self.get_template_value('logo-ofertas-height', 450))
        
        # Obter valores da call action
        call_action_top_raw = self.get_template_value('call-action-top', 0)
        if isinstance(call_action_top_raw, str) and call_action_top_raw.strip() == '0':
            call_action_top_raw = 0
        call_action_top = self.format_css_value('call-action-top', call_action_top_raw)
        call_action_bottom_raw = self.get_template_value('call-action-bottom', 120)
        if isinstance(call_action_bottom_raw, str) and call_action_bottom_raw.strip() == '0':
            call_action_bottom_raw = 0
        call_action_bottom = self.format_css_value('call-action-bottom', call_action_bottom_raw)
        call_action_left = self.format_css_value('call-action-left', self.get_template_value('call-action-left', 50))
        call_action_width = self.format_css_value('call-action-width', self.get_template_value('call-action-width', 500))
        call_action_height = self.format_css_value('call-action-height', self.get_template_value('call-action-height', 100))
        
        # Montar estilo da call action (top ou bottom, dependendo do que foi definido)
        call_action_style_parts = []
        if call_action_top != 'auto':
            call_action_style_parts.append(f'top: {call_action_top}')
        if call_action_bottom != 'auto':
            call_action_style_parts.append(f'bottom: {call_action_bottom}')
        call_action_style_parts.append(f'left: {call_action_left}')
        call_action_style_parts.append(f'transform: translateX(-50%)')
        call_action_style_parts.append(f'width: {call_action_width}')
        call_action_style_parts.append(f'height: {call_action_height}')
        call_action_style_parts.append(f'z-index: 20')
        call_action_style_parts.append(f'object-fit: contain')
        call_action_style = '; '.join(call_action_style_parts) + ';'

        nome_empresa_display = (nome_empresa or '').strip()
        if not nome_empresa_display:
            nome_empresa_display = unidade

        periodo_part = ''
        if data_inicio and data_fim:
            periodo_part = f'de {data_inicio} a {data_fim}'
        elif data_inicio:
            periodo_part = f'a partir de {data_inicio}'
        elif data_fim:
            periodo_part = f'até {data_fim}'

        line1 = f'Promoção válida apenas para a unidade de {nome_empresa_display}'
        if periodo_part:
            line1 += f', {periodo_part}'
        line1 += ' ou enquanto durarem os estoques.'
        line2 = '*Promoção não acumulativa com outros itens promocionais. Condições não estendidas a clientes com acordos comerciais.'

        line1_html = escape(line1)
        line2_html = escape(line2)
        footer_text_html = f"{line1_html} {line2_html}" if line2_html else line1_html

        footer_font_size_raw = self.get_template_value('footer-font-size', 26)
        footer_font_size = self.format_css_value('footer-font-size', footer_font_size_raw)
        footer_color = self.get_template_value('footer-color', '#FFFFFF')
        footer_width = self.format_css_value('footer-width', self.get_template_value('footer-width', 900))
        footer_left = self.format_css_value('footer-left', self.get_template_value('footer-left', 50))

        footer_top_raw = self.get_template_value('footer-top', 0)
        if isinstance(footer_top_raw, str) and footer_top_raw.strip() == '0':
            footer_top_raw = 0
        footer_top = self.format_css_value('footer-top', footer_top_raw)

        footer_bottom_raw = self.get_template_value('footer-bottom', 5)
        if isinstance(footer_bottom_raw, str) and footer_bottom_raw.strip() == '0':
            footer_bottom_raw = 0
        footer_bottom = self.format_css_value('footer-bottom', footer_bottom_raw)

        footer_rotation = str(self.get_template_value('footer-rotation', 'horizontal')).lower()

        def parse_css_number(value, default):
            try:
                s = str(value).strip()
                if s.endswith('px'):
                    s = s[:-2]
                return float(s.replace(',', '.'))
            except Exception:
                return default

        footer_font_size_numeric = parse_css_number(footer_font_size, 26.0)

        footer_transform = 'translateX(-50%)'
        if footer_rotation == 'vertical':
            footer_transform = 'translate(-50%, 0) rotate(-90deg)'

        footer_position_parts = []
        if footer_bottom != 'auto':
            footer_position_parts.append(f'bottom: {footer_bottom};')
        if footer_top != 'auto':
            footer_position_parts.append(f'top: {footer_top};')
        footer_position_css = ' '.join(footer_position_parts)
        if footer_position_css and not footer_position_css.endswith(' '):
            footer_position_css += ' '
        if not footer_position_css:
            footer_position_css = 'bottom: 0px; '

        # Calcular estilos da frase de impulsionamento para o CSS da classe
        impulsionamento_css_parts = []
        impulsionamento_text = self.get_template_value('impulsionamento-text', '')
        if impulsionamento_text:
            import re
            text_without_tags = re.sub(r'<[^>]+>', '', impulsionamento_text).strip()
            if text_without_tags and text_without_tags != '' and 'Digite sua frase' not in text_without_tags:
                # Obter valores (mesma lógica da função _generate_impulsionamento_html)
                impulsionamento_font_family = self.get_template_value('impulsionamento-font-family', "'Bebas Neue', sans-serif")
                impulsionamento_font_size_raw = self.get_template_value('impulsionamento-font-size', 32)
                impulsionamento_font_size_value = self._safe_int_convert(impulsionamento_font_size_raw, 32)
                impulsionamento_font_size = f'{impulsionamento_font_size_value}px'
                
                impulsionamento_color = self.get_template_value('impulsionamento-color', '#FFFFFF')
                impulsionamento_width_raw = self.get_template_value('impulsionamento-width', 800)
                impulsionamento_width_value = self._safe_int_convert(impulsionamento_width_raw, 800)
                impulsionamento_width = f'{impulsionamento_width_value}px'
                
                impulsionamento_height_raw = self.get_template_value('impulsionamento-height', 0)
                impulsionamento_height_value = self._safe_int_convert(impulsionamento_height_raw, 0)
                impulsionamento_height_css = 'auto' if impulsionamento_height_value == 0 else f'{impulsionamento_height_value}px'
                
                # Posicionamento
                impulsionamento_top_raw = self.get_template_value('impulsionamento-top', 0)
                impulsionamento_top_value = self._safe_int_convert(impulsionamento_top_raw, 0)
                
                impulsionamento_bottom_raw = self.get_template_value('impulsionamento-bottom', 0)
                impulsionamento_bottom_value = self._safe_int_convert(impulsionamento_bottom_raw, 0)
                
                impulsionamento_left_raw = self.get_template_value('impulsionamento-left', 540)
                impulsionamento_left_value = self._safe_int_convert(impulsionamento_left_raw, 540)
                
                impulsionamento_right_raw = self.get_template_value('impulsionamento-right', 0)
                impulsionamento_right_value = self._safe_int_convert(impulsionamento_right_raw, 0)
                
                # Montar CSS de posicionamento
                if impulsionamento_bottom_value > 0:
                    impulsionamento_css_parts.append(f'bottom: {impulsionamento_bottom_value}px')
                else:
                    impulsionamento_css_parts.append(f'top: {impulsionamento_top_value}px')
                
                if impulsionamento_right_value > 0:
                    impulsionamento_css_parts.append(f'right: {impulsionamento_right_value}px')
                else:
                    impulsionamento_css_parts.append(f'left: {impulsionamento_left_value}px')
                
                # Adicionar outros estilos
                impulsionamento_css_parts.append(f'width: {impulsionamento_width}')
                if impulsionamento_height_css != 'auto':
                    impulsionamento_css_parts.append(f'height: {impulsionamento_height_css}')
                impulsionamento_css_parts.append(f'font-family: {impulsionamento_font_family}')
                impulsionamento_css_parts.append(f'font-size: {impulsionamento_font_size}')
                impulsionamento_css_parts.append(f'color: {impulsionamento_color}')
                
                # Debug: confirmar font-size no CSS da classe
                print(f'  ✅ CSS Classe - Font-size aplicado: {impulsionamento_font_size}')
        
        impulsionamento_css = '; '.join(impulsionamento_css_parts) + ('; ' if impulsionamento_css_parts else '')

        # Definir background do banner (imagem de fundo ou gradiente padrão)
        if fundo_b64:
            background_style = f'background-image: url(data:image/png;base64,{fundo_b64}); background-size: cover; background-position: center; background-repeat: no-repeat;'
        else:
            background_style = 'background: linear-gradient(180deg, #0a1628 0%, #1a3a5a 50%, #2d5a7a 100%);'
        
        # Gerar CSS das fontes Goldplay locais
        goldplay_fonts_css = self.generate_goldplay_fonts_css()
        
        # HTML completo
        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<!-- Google Fonts - Fontes para banners promocionais -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Anton&family=Impact&family=Raleway:wght@400;600;700;800;900&family=Nunito:wght@400;600;700;800;900&family=Montserrat:wght@400;500;600;700;800;900&family=Roboto:wght@400;500;700;900&family=Poppins:wght@400;500;600;700;800;900&family=Open+Sans:wght@400;600;700;800&family=Lato:wght@400;700;900&family=Oswald:wght@400;500;600;700&family=Playfair+Display:wght@400;700;900&display=swap" rel="stylesheet">
<style>
/* Fontes Goldplay locais */
{goldplay_fonts_css}
body {{ margin: 0; padding: 0; width: {BANNER_WIDTH}px; height: {BANNER_HEIGHT}px; overflow: hidden; }}
.banner-container {{ width: {BANNER_WIDTH}px; height: {BANNER_HEIGHT}px; position: relative; {background_style} overflow: hidden; }}
.logo-ofertas {{ position: absolute; left: 50%; transform: translateX(-50%); top: {self.format_css_value('logo-ofertas-top', self.get_template_value('logo-ofertas-top', 50))}; width: 450px; height: 450px; z-index: 10; }}
.produtos-container {{ position: absolute; left: 50%; transform: translateX(-50%); top: {self.format_css_value('produtos-container-top', self.get_template_value('produtos-container-top', 650))}; width: 100%; display: flex; flex-direction: row; justify-content: center; align-items: flex-start; gap: {self.format_css_value('produtos-container-gap', self.get_template_value('produtos-container-gap', 20))}; padding: 0 20px; }}
.produto-item {{ flex: 1; max-width: {self.format_css_value('produto-item-max-width', self.get_template_value('produto-item-max-width', 320))}; }}
.produto-container {{ }}
.produto-imagem-container {{ position: relative; background: {self.get_imagem_container_bg_color()}; border-radius: 15px; }}
.produto-imagem {{ position: absolute; object-fit: contain; z-index: 2; }}
.base-produto {{ position: absolute; object-fit: contain; z-index: 1; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)); }}
.desconto-badge {{ position: absolute; z-index: 3; }}
.produto-nome-container {{ position: absolute; overflow: hidden; display: flex; align-items: center; justify-content: center; }}
.produto-nome {{ text-align: center; font-family: {produto_nome_font_family}; font-weight: {produto_nome_font_weight}; font-style: {produto_nome_font_style}; color: {produto_nome_color}; font-size: {produto_nome_font_size}; line-height: 1.2; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; word-wrap: break-word; word-break: break-word; width: 100%; max-height: {produto_nome_max_height}px; box-sizing: border-box; }}
.produto-codigo {{ text-align: center; font-family: {produto_codigo_font_family}; font-weight: {produto_codigo_font_weight}; font-style: {produto_codigo_font_style}; color: {produto_codigo_color}; font-size: {produto_codigo_font_size}; }}
.preco-label {{ font-family: {produto_nome_font_family}; font-weight: {produto_nome_font_weight}; font-style: {produto_nome_font_style}; color: {produto_nome_color}; }}
.preco-label-de {{ font-size: {preco_de_font_size}; }}
.preco-label-por {{ font-size: {preco_por_font_size}; }}
.precos {{ text-align: center; display: flex; flex-direction: column; align-items: center; gap: 6px; }}
.preco-linhas {{ display: flex; gap: 16px; align-items: baseline; justify-content: center; flex-wrap: wrap; }}
.preco-label {{ font-family: {produto_nome_font_family}; font-weight: {produto_nome_font_weight}; font-style: {produto_nome_font_style}; color: {produto_nome_color}; font-size: {produto_nome_font_size}; }}
.preco-comercial-valor {{ font-family: {preco_comercial_font_family}; font-weight: {preco_comercial_font_weight}; font-style: {preco_comercial_font_style}; font-size: {preco_comercial_font_size}; color: {preco_comercial_color}; display: inline-flex; align-items: baseline; }}
.preco-comercial-rs {{ font-size: 0.6em; vertical-align: baseline; }}
.preco-comercial-valor-num {{ }}
.preco-promocional {{ font-family: {preco_promocional_font_family}; font-weight: {preco_promocional_font_weight}; font-style: {preco_promocional_font_style}; color: {preco_promocional_color}; display: inline-flex; align-items: flex-start; line-height: 1; }}
.preco-rs {{ font-size: {preco_rs_font_size}; margin-right: 5px; color: {preco_rs_color}; align-self: {preco_rs_vertical_align}; }}
.preco-inteiro {{ font-size: 1em; vertical-align: baseline; }}
.preco-virgula {{ font-size: {preco_decimal_font_size}; color: {preco_decimal_color}; vertical-align: {preco_decimal_vertical_align}; }}
.preco-decimal {{ font-size: {preco_decimal_font_size}; color: {preco_decimal_color}; vertical-align: {preco_decimal_vertical_align}; }}
.unidade-text {{ position: absolute; top: 30px; left: 40px; color: #FFFFFF; font-size: 42px; font-family: 'Montserrat', sans-serif; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; text-shadow: 0 3px 6px rgba(0,0,0,0.45); z-index: 30; }}
.impulsionamento-text {{ position: absolute; {impulsionamento_css} z-index: 40; text-align: center; white-space: normal; word-wrap: break-word; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }}
.separador-produto {{ position: absolute; z-index: 15; }}
.footer-text {{ position: absolute; left: {footer_left}; width: {footer_width}; {footer_position_css} color: {footer_color}; font-size: {footer_font_size}; transform: {footer_transform}; transform-origin: center; font-family: 'Montserrat', sans-serif; z-index: 25; line-height: 1.2; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.6); white-space: normal; font-weight: 500; }}
.call-action {{ position: absolute; left: 50%; transform: translateX(-50%); z-index: 10; border-radius: 20px; box-shadow: none; border: none; }}
.logo-inferior {{ position: absolute; left: 50%; transform: translateX(-50%); z-index: 10; }}
.logo-superior {{ position: absolute; z-index: 10; }}
</style>
</head>
<body>
<div class="banner-container">
{'<img src="data:image/png;base64,' + logo_superior_b64 + '" alt="Logo Superior" class="logo-superior" style="position: absolute; top: ' + logo_superior_top + '; right: ' + logo_superior_right + '; width: ' + logo_superior_width + '; height: ' + logo_superior_height + '; z-index: 10; object-fit: contain;" />' if logo_superior_b64 else ''}
{'<img src="data:image/png;base64,' + logo_ofertas_b64 + '" alt="Ofertas da Semana" class="logo-ofertas" style="position: absolute; left: 50%; transform: translateX(-50%); top: ' + logo_ofertas_top + '; width: ' + logo_ofertas_width + '; height: ' + logo_ofertas_height + '; z-index: 10; object-fit: contain;" />' if logo_ofertas_b64 else ''}
<div class="produtos-container" style="position: relative;">
{produtos_html}
</div>
{'<div class="unidade-text">' + escape(unidade) + '</div>'}
{self._generate_impulsionamento_html()}
{'<img src="data:image/png;base64,' + call_action_b64 + '" alt="Call Action" class="call-action" style="position: absolute; ' + call_action_style + '" />' if call_action_b64 else ''}
{'<img src="data:' + logo_inferior_mime + ';base64,' + logo_inferior_b64 + '" alt="Logo Inferior" class="logo-inferior" style="position: absolute; left: ' + logo_inferior_left + '; bottom: ' + logo_inferior_bottom + '; transform: translateX(-50%); width: ' + logo_inferior_width + '; height: ' + logo_inferior_height + '; z-index: 10; object-fit: contain;" />' if logo_inferior_b64 else ''}
{f'<div class="footer-text">{footer_text_html}</div>'}
</div>
<script>
(function() {{
    // Ajustar tamanho da fonte do produto-nome se necessário
    const produtoNomes = document.querySelectorAll('.produto-nome');
    produtoNomes.forEach(function(nomeEl) {{
        const originalFontSize = parseFloat(nomeEl.getAttribute('data-original-font-size')) || 16;
        const maxHeight = originalFontSize * 1.2 * 3; // 3 linhas
        let currentFontSize = originalFontSize;
        const minFontSize = originalFontSize * 0.6; // Não reduzir mais que 40%
        
        // Verificar se o texto está excedendo a altura máxima
        function checkAndAdjust() {{
            nomeEl.style.fontSize = currentFontSize + 'px';
            nomeEl.style.display = '-webkit-box';
            nomeEl.style.webkitLineClamp = '3';
            nomeEl.style.webkitBoxOrient = 'vertical';
            
            // Forçar reflow
            void nomeEl.offsetHeight;
            
            // Se o conteúdo ainda está excedendo, reduzir fonte
            if (nomeEl.scrollHeight > maxHeight && currentFontSize > minFontSize) {{
                currentFontSize = Math.max(minFontSize, currentFontSize - 1);
                checkAndAdjust();
            }}
        }}
        
        checkAndAdjust();
    }});
}})();
</script>
</body>
</html>'''
        return html
    
    def _safe_int_convert(self, value, default=0):
        """Função auxiliar para converter valor para int (trata string "0" e número 0)"""
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            stripped = value.strip().replace('px', '').replace('auto', '0').replace('"', '').replace("'", '')
            if not stripped or stripped == '':
                return default
            try:
                return int(float(stripped))
            except:
                return default
        return default
    
    def _generate_impulsionamento_html(self):
        """Gera HTML da frase de impulsionamento"""
        impulsionamento_text = self.get_template_value('impulsionamento-text', '')
        # Verificar se o texto está vazio ou é apenas o placeholder
        if not impulsionamento_text:
            return ''
        
        # Remover tags HTML para verificar se há conteúdo real
        import re
        text_without_tags = re.sub(r'<[^>]+>', '', impulsionamento_text).strip()
        if not text_without_tags or text_without_tags == '' or 'Digite sua frase' in text_without_tags:
            # Debug: verificar se o template tem a chave
            if 'impulsionamento-text' in self.template_config:
                print(f'  ⚠ Frase de impulsionamento encontrada no template mas está vazia ou é placeholder')
            return ''
        
        # Debug: confirmar que a frase será gerada
        print(f'  ✓ Gerando frase de impulsionamento: {text_without_tags[:50]}...')
        
        # Obter valores do template (usar valores diretos como no template_editor.html)
        impulsionamento_font_family = self.get_template_value('impulsionamento-font-family', "'Bebas Neue', sans-serif")
        
        # Font size: ler valor e converter para número, depois adicionar 'px'
        impulsionamento_font_size_raw = self.get_template_value('impulsionamento-font-size', 32)
        impulsionamento_font_size_value = self._safe_int_convert(impulsionamento_font_size_raw, 32)
        impulsionamento_font_size = f'{impulsionamento_font_size_value}px'
        
        # Debug: confirmar font-size
        print(f'  📊 Font-size: raw={impulsionamento_font_size_raw}, converted={impulsionamento_font_size_value}, final={impulsionamento_font_size}')
        
        impulsionamento_color = self.get_template_value('impulsionamento-color', '#FFFFFF')
        
        # Width: ler valor e converter para número, depois adicionar 'px'
        impulsionamento_width_raw = self.get_template_value('impulsionamento-width', 800)
        impulsionamento_width_value = self._safe_int_convert(impulsionamento_width_raw, 800)
        impulsionamento_width = f'{impulsionamento_width_value}px'
        
        # Height: ler valor e converter para número, depois adicionar 'px' ou 'auto'
        impulsionamento_height_raw = self.get_template_value('impulsionamento-height', 0)
        impulsionamento_height_value = self._safe_int_convert(impulsionamento_height_raw, 0)
        impulsionamento_height = 'auto' if impulsionamento_height_value == 0 else f'{impulsionamento_height_value}px'
        
        # Obter valores de posicionamento (usar valores diretos como no template_editor.html)
        # Top: sempre em pixels, 0px é válido
        impulsionamento_top_raw = self.get_template_value('impulsionamento-top', 0)
        impulsionamento_top_value = self._safe_int_convert(impulsionamento_top_raw, 0)
        
        # Bottom: 0 = auto, senão em pixels
        impulsionamento_bottom_raw = self.get_template_value('impulsionamento-bottom', 0)
        impulsionamento_bottom_value = self._safe_int_convert(impulsionamento_bottom_raw, 0)
        
        # Left: sempre em pixels, 0px é válido
        impulsionamento_left_raw = self.get_template_value('impulsionamento-left', 540)
        impulsionamento_left_value = self._safe_int_convert(impulsionamento_left_raw, 540)
        
        # Right: 0 = auto, senão em pixels
        impulsionamento_right_raw = self.get_template_value('impulsionamento-right', 0)
        impulsionamento_right_value = self._safe_int_convert(impulsionamento_right_raw, 0)
        
        # Montar estilo de posicionamento (simplificado como no template_editor.html)
        impulsionamento_style_parts = [
            'position: absolute',
            f'font-family: {impulsionamento_font_family}',
            f'font-size: {impulsionamento_font_size}',
            f'color: {impulsionamento_color}',
            f'width: {impulsionamento_width}',
            'z-index: 40',
            'text-align: center',
            'white-space: normal',
            'word-wrap: break-word',
            'text-shadow: 0 2px 4px rgba(0,0,0,0.5)'
        ]
        
        if impulsionamento_height != 'auto':
            impulsionamento_style_parts.append(f'height: {impulsionamento_height}')
        
        # Lógica simplificada: sempre usar top quando bottom for 0
        if impulsionamento_bottom_value > 0:
            impulsionamento_style_parts.append(f'bottom: {impulsionamento_bottom_value}px')
        else:
            # Sempre usar top quando bottom for 0 (mesmo que top seja 0px)
            impulsionamento_style_parts.append(f'top: {impulsionamento_top_value}px')
        
        # Left/Right: sempre usar left se right for 0, senão usar right
        if impulsionamento_right_value > 0:
            impulsionamento_style_parts.append(f'right: {impulsionamento_right_value}px')
        else:
            impulsionamento_style_parts.append(f'left: {impulsionamento_left_value}px')
        
        impulsionamento_style = '; '.join(impulsionamento_style_parts) + ';'
        
        # Debug: mostrar estilo final aplicado
        print(f'  🎨 Estilo aplicado: {impulsionamento_style[:200]}...')
        print(f'  📍 Posição final: top={impulsionamento_top_value}px, left={impulsionamento_left_value}px, width={impulsionamento_width}, font-size={impulsionamento_font_size}')
        print(f'  ✅ CONFIRMAÇÃO FONT-SIZE: {impulsionamento_font_size} (valor original: {impulsionamento_font_size_raw}, convertido: {impulsionamento_font_size_value})')
        
        # O texto já vem com HTML (formatação inline preservada)
        return f'<div class="impulsionamento-text" style="{impulsionamento_style}">{impulsionamento_text}</div>'
    
    def initialize_browser(self):
        """Inicializa navegador Playwright uma única vez (otimização de performance)"""
        if self.browser is None or not self.browser.is_connected():
            try:
                if self.playwright is None:
                    self.playwright = sync_playwright().start()
                self.browser = self.playwright.chromium.launch(headless=True)
                print('  ✓ Navegador Playwright inicializado')
            except Exception as e:
                if 'Executable' in str(e) or 'chromium' in str(e).lower():
                    print('⚠ Tentando reinstalar Chromium...')
                    try:
                        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], 
                                      check=True, capture_output=True)
                        if self.playwright is None:
                            self.playwright = sync_playwright().start()
                        self.browser = self.playwright.chromium.launch(headless=True)
                        print('  ✓ Navegador Playwright inicializado após reinstalação')
                    except Exception as e2:
                        raise Exception(f'Erro ao inicializar navegador: {e2}')
                else:
                    raise Exception(f'Erro ao inicializar navegador: {e}')
    
    def close_browser(self):
        """Fecha navegador Playwright"""
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
        except:
            pass
    
    def html_to_image(self, html_content, output_path):
        """Converte HTML para imagem JPEG usando Playwright (otimizado - reutiliza navegador)"""
        # Garantir que navegador está inicializado
        self.initialize_browser()
        
        try:
            # Criar nova página (navegador já está aberto)
            page = self.browser.new_page(viewport={'width': BANNER_WIDTH, 'height': BANNER_HEIGHT})
            # Usar 'domcontentloaded' ao invés de 'networkidle' para ser mais rápido
            page.set_content(html_content, wait_until='domcontentloaded')
            # Reduzir timeout de 2000ms para 500ms
            page.wait_for_timeout(500)
            page.screenshot(path=output_path, type='jpeg', quality=90)
            page.close()  # Fecha apenas a página, não o navegador
        except Exception as e:
            # Se navegador desconectou, tentar reinicializar e tentar novamente
            if 'Target closed' in str(e) or 'Browser closed' in str(e):
                print('  ⚠ Navegador desconectado, reinicializando...')
                self.close_browser()
                self.initialize_browser()
                page = self.browser.new_page(viewport={'width': BANNER_WIDTH, 'height': BANNER_HEIGHT})
                page.set_content(html_content, wait_until='domcontentloaded')
                page.wait_for_timeout(500)
                page.screenshot(path=output_path, type='jpeg', quality=90)
                page.close()
            else:
                raise Exception(f'Erro ao converter HTML para imagem: {e}')
    
    def send_to_telegram(self, image_paths):
        if not TELEGRAM_API_BASE or not TELEGRAM_CHAT_ID:
            print('⚠ Integração com Telegram não configurada. Pulando envio.')
            return
        if not image_paths:
            print('⚠ Nenhuma imagem para enviar ao Telegram.')
            return
        for image_path in image_paths:
            try:
                print(f'  🔄 Enviando {image_path} ao Telegram...')
                with open(image_path, 'rb') as photo_file:
                    response = requests.post(
                        f"{TELEGRAM_API_BASE}/sendPhoto",
                        data={'chat_id': TELEGRAM_CHAT_ID, 'caption': os.path.basename(image_path)},
                        files={'photo': photo_file}
                    )
                if response.status_code == 200:
                    resp_json = response.json()
                    if resp_json.get('ok'):
                        print(f'  📤 Enviado ao Telegram: {image_path}')
                    else:
                        print(f"  ⚠ Telegram retornou erro para {image_path}: {resp_json}")
                else:
                    print(f"  ⚠ Falha HTTP {response.status_code} ao enviar {image_path}: {response.text}")
            except Exception as exc:
                print(f'  ⚠ Erro ao enviar {image_path} ao Telegram: {exc}')

    def worker_thread_whatsapp(self):
        """Thread worker que processa a fila de envios ao WhatsApp"""
        print('📤 Thread de envio WhatsApp iniciada (processamento paralelo)')
        
        while not self.whatsapp_thread_stop.is_set():
            try:
                # Pegar item da fila com timeout para verificar periodicamente se deve parar
                try:
                    item = self.whatsapp_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # None é o sinal de parada
                if item is None:
                    break
                
                image_path, group_id = item
                
                # Enviar ao WhatsApp
                if self.send_to_whatsapp_group_direct(image_path, group_id):
                    print(f'  ✅ Banner enviado (thread): {os.path.basename(image_path)}')
                else:
                    print(f'  ⚠ Falha ao enviar (thread): {os.path.basename(image_path)}')
                
                # Marcar tarefa como concluída
                self.whatsapp_queue.task_done()
                
            except Exception as e:
                print(f'  ⚠ Erro na thread de envio WhatsApp: {e}')
                import traceback
                traceback.print_exc()
                try:
                    self.whatsapp_queue.task_done()
                except:
                    pass
        
        print('📤 Thread de envio WhatsApp finalizada')
        self.whatsapp_thread_running = False
    
    def start_whatsapp_thread(self):
        """Inicia a thread de envio ao WhatsApp"""
        if self.whatsapp_thread_running:
            return
        
        self.whatsapp_thread_stop.clear()
        self.whatsapp_thread_running = True
        self.whatsapp_thread = threading.Thread(target=self.worker_thread_whatsapp, daemon=True)
        self.whatsapp_thread.start()
        print('✓ Thread de envio WhatsApp iniciada')
    
    def stop_whatsapp_thread(self):
        """Para a thread de envio ao WhatsApp"""
        if not self.whatsapp_thread_running:
            return
        
        print('⏳ Finalizando thread de envio WhatsApp...')
        self.whatsapp_thread_stop.set()
        # Enviar sinal de parada na fila
        try:
            self.whatsapp_queue.put(None)
        except:
            pass
        
        # Aguardar thread terminar (com timeout)
        if self.whatsapp_thread and self.whatsapp_thread.is_alive():
            self.whatsapp_thread.join(timeout=10)
        
        # Aguardar fila esvaziar
        try:
            self.whatsapp_queue.join()
        except:
            pass
        
        self.whatsapp_thread_running = False
        print('✓ Thread de envio WhatsApp finalizada')
    
    def cleanup(self):
        """Limpa recursos ao finalizar (fecha navegador e para thread WhatsApp)"""
        self.close_browser()
        self.stop_whatsapp_thread()
    
    def enqueue_whatsapp_send(self, image_path, group_id):
        """Adiciona um banner à fila de envio ao WhatsApp"""
        if not WHATSAPP_ENABLED:
            return False
        
        try:
            self.whatsapp_queue.put((image_path, group_id))
            return True
        except Exception as e:
            print(f'  ⚠ Erro ao adicionar à fila WhatsApp: {e}')
            return False
    
    def send_to_whatsapp_group_direct(self, image_path, group_id):
        """Envia uma imagem para um grupo do WhatsApp via servidor Node.js (chamada direta)"""
        if not WHATSAPP_ENABLED:
            return False
        
        # Verificar se o arquivo existe
        if not os.path.exists(image_path):
            print(f'  ⚠ Arquivo não encontrado: {image_path}')
            return False
        
        try:
            # Verificar servidor
            server_ready = False
            if hasattr(self, '_whatsapp_ready') and self._whatsapp_ready:
                server_ready = True
            else:
                try:
                    response = requests.get(f'{WHATSAPP_API_URL}/health', timeout=5)
                    if response.status_code == 200:
                        health_data = response.json()
                        if health_data.get('status') == 'ready':
                            server_ready = True
                            self._whatsapp_ready = True
                        else:
                            self._whatsapp_ready = False
                    else:
                        self._whatsapp_ready = False
                except Exception as e:
                    self._whatsapp_ready = False
            
            if not server_ready:
                return False

            # Preparar caminho absoluto
            abs_path = os.path.abspath(image_path)
            
            # Obter legenda do template ou usar padrão
            caption_text = self.get_template_value('banner-caption', '').strip()
            if not caption_text:
                caption_text = f'Compre no WhatsApp - {WHATSAPP_LINK}'
            
            # Enviar para grupo
            response = requests.post(
                f'{WHATSAPP_API_URL}/send-image-to-group',
                json={
                    'groupId': group_id,
                    'imagePath': abs_path,
                    'caption': caption_text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    group_name = result.get('groupName', 'Grupo')
                    print(f'  ✅ Enviado ao grupo "{group_name}": {os.path.basename(image_path)}')
                    return True
                else:
                    return False
            else:
                return False
                
        except Exception as exc:
            return False
    
    def send_to_whatsapp_group(self, image_path, group_id):
        """Envia uma imagem para um grupo do WhatsApp via servidor Node.js (compatibilidade)"""
        # Redireciona para método direto para manter compatibilidade
        return self.send_to_whatsapp_group_direct(image_path, group_id)

    def send_to_whatsapp(self, image_path):
        """Envia uma imagem para o WhatsApp via servidor Node.js com legenda simples"""
        if not WHATSAPP_ENABLED:
            print('  ⚠ WhatsApp desabilitado. Pulando envio.')
            return False
        
        # Verificar se o arquivo existe
        if not os.path.exists(image_path):
            print(f'  ⚠ Arquivo não encontrado: {image_path}')
            return False
        
        try:
            # Verificar servidor a cada tentativa (mas cachear o resultado se estiver OK)
            server_ready = False
            if hasattr(self, '_whatsapp_ready') and self._whatsapp_ready:
                server_ready = True
            else:
                try:
                    response = requests.get(f'{WHATSAPP_API_URL}/health', timeout=5)
                    if response.status_code == 200:
                        health_data = response.json()
                        if health_data.get('status') == 'ready':
                            server_ready = True
                            self._whatsapp_ready = True
                        else:
                            print(f'  ⚠ Servidor WhatsApp não está pronto: {health_data.get("message")}')
                            print('  💡 Aguarde a autenticação do WhatsApp (escaneie o QR Code)')
                            self._whatsapp_ready = False
                    else:
                        print(f'  ⚠ Servidor WhatsApp respondeu com código: {response.status_code}')
                        self._whatsapp_ready = False
                except requests.exceptions.ConnectionError:
                    print('  ⚠ Não foi possível conectar ao servidor WhatsApp!')
                    print('  💡 Certifique-se de que o servidor está rodando: start-whatsapp-server.bat')
                    self._whatsapp_ready = False
                except Exception as e:
                    print(f'  ⚠ Erro ao verificar servidor WhatsApp: {e}')
                    self._whatsapp_ready = False
            
            if not server_ready:
                return False

            # Preparar caminho absoluto
            abs_path = os.path.abspath(image_path)
            
            # Verificar novamente se o arquivo existe (com caminho absoluto)
            if not os.path.exists(abs_path):
                print(f'  ⚠ Arquivo não encontrado (absoluto): {abs_path}')
                return False
            
            # Obter legenda do template ou usar padrão
            caption_text = self.get_template_value('banner-caption', '').strip()
            if not caption_text:
                caption_text = f'Compre no WhatsApp - {WHATSAPP_LINK}'
            
            # Enviar imagem
            print(f'  🔄 Enviando {os.path.basename(image_path)} ao WhatsApp...')
            try:
                response = requests.post(
                    f'{WHATSAPP_API_URL}/send-image',
                    json={
                        'imagePath': abs_path,
                        'caption': caption_text
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f'  ✅ Enviado ao WhatsApp com sucesso: {os.path.basename(image_path)}')
                        return True
                    else:
                        error_msg = result.get('error', 'Erro desconhecido')
                        print(f'  ⚠ Erro ao enviar ao WhatsApp: {error_msg}')
                        # Se houver erro, marcar servidor como não pronto para próxima verificação
                        self._whatsapp_ready = False
                        return False
                else:
                    print(f'  ⚠ Falha HTTP {response.status_code} ao enviar ao WhatsApp')
                    print(f'  📄 Resposta: {response.text[:200]}')
                    self._whatsapp_ready = False
                    return False
            except requests.exceptions.Timeout:
                print('  ⚠ Timeout ao enviar ao WhatsApp (servidor pode estar ocupado)')
                return False
            except requests.exceptions.ConnectionError:
                print('  ⚠ Erro de conexão ao enviar ao WhatsApp')
                self._whatsapp_ready = False
                return False
                
        except Exception as exc:
            print(f'  ⚠ Erro inesperado ao enviar ao WhatsApp: {exc}')
            import traceback
            traceback.print_exc()
            return False

    def save_csv_with_format(self, df, file_path, sep, encoding):
        """Salva o DataFrame mantendo o formato original do CSV"""
        try:
            # Remover colunas internas que não devem ser salvas
            df_to_save = df.copy()
            colunas_para_remover = ['_imagem_url', 'Desconto %']
            for col in colunas_para_remover:
                if col in df_to_save.columns:
                    df_to_save = df_to_save.drop(columns=[col])
            
            # Salvar CSV mantendo o formato
            df_to_save.to_csv(file_path, sep=sep, encoding=encoding, index=False, lineterminator='\n')
            return True
        except Exception as e:
            print(f'⚠ Erro ao salvar CSV: {e}')
            import traceback
            traceback.print_exc()
            return False

    def generate_banners(self, progress_callback=None):
        """Gera banners para todas as unidades, marcando itens processados no CSV
        
        Args:
            progress_callback: Função callback(opcao, progresso, tarefa, detalhes) para atualizar progresso
                              opcao: 'init', 'read_csv', 'process_unit', 'process_banner', 'process_images', 'save', 'complete'
                              progresso: 0-100
                              tarefa: string descritiva
                              detalhes: dict com informações adicionais
        """
        def update_progress(opcao, progresso, tarefa, detalhes=None):
            """Helper para atualizar progresso"""
            if progress_callback:
                try:
                    progress_callback(opcao, progresso, tarefa, detalhes or {})
                except:
                    pass  # Ignorar erros no callback
        
        # CRÍTICO: Recarregar template antes de gerar para garantir que está atualizado
        print('\n' + '='*60)
        print('🔧 RECARREGANDO TEMPLATE ANTES DA GERAÇÃO')
        print('='*60)
        
        # Forçar recarregamento do template
        template_antes = self.template_config.copy() if isinstance(self.template_config, dict) and self.template_config else {}
        self.reload_template()
        
        # Verificar se template foi realmente carregado após reload
        if not isinstance(self.template_config, dict):
            print(f'⚠ Template config não é dict após reload: {type(self.template_config)}')
            self.template_config = {}
        if not self.template_config:
            print(f'⚠ Template config está None após reload')
            self.template_config = {}
        
        # VERIFICAÇÃO CRÍTICA: Template DEVE estar carregado antes de continuar
        if not self.template_config or len(self.template_config) == 0:
            print('\n' + '='*60)
            print('❌❌❌ ERRO CRÍTICO: TEMPLATE NÃO FOI CARREGADO!')
            print('='*60)
            print(f'   Arquivo esperado: {TEMPLATE_FILE}')
            print(f'   Arquivo existe? {os.path.exists(TEMPLATE_FILE)}')
            
            # Tentar diagnosticar o problema
            if os.path.exists(TEMPLATE_FILE):
                try:
                    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f'   Tamanho do arquivo: {len(content)} bytes')
                        if len(content) == 0:
                            print('   ❌ Arquivo está vazio!')
                        else:
                            try:
                                import json
                                test_config = json.loads(content)
                                print(f'   ⚠ JSON válido com {len(test_config)} chaves, mas não foi carregado!')
                                print(f'   Isso indica um problema no método load_template()')
                            except json.JSONDecodeError as je:
                                print(f'   ❌ JSON inválido: {je}')
                            except Exception as e:
                                print(f'   ❌ Erro ao ler JSON: {e}')
                except Exception as e:
                    print(f'   ❌ Erro ao acessar arquivo: {e}')
            else:
                print(f'   💡 O arquivo {TEMPLATE_FILE} não existe!')
                print(f'   Crie o template através do editor em template_editor.html')
            
            print('='*60)
            print('🚫 GERAÇÃO INTERROMPIDA: Não é possível gerar banners sem template!')
            print('='*60 + '\n')
            raise Exception(f'Template não carregado! Arquivo {TEMPLATE_FILE} não existe ou está vazio/inválido.')
        else:
            print(f'✓✓✓ Template confirmado: {len(self.template_config)} propriedades carregadas')
            # Mostrar algumas propriedades para confirmar que foram carregadas
            print('  📋 Propriedades do template verificadas:')
            check_keys = ['produto-container-padding', 'desconto-badge-shape', 'produto-nome-font-size', 'logo-ofertas-top', 'produto-container-bg-color']
            for key in check_keys:
                valor = self.template_config.get(key, 'NÃO ENCONTRADO')
                valor_antes = template_antes.get(key, 'N/A') if template_antes else 'N/A'
                status = '✓' if key in self.template_config else '✗'
                print(f'    {status} {key}: {valor} (antes: {valor_antes})')
            print('='*60 + '\n')
        
        update_progress('init', 0, 'Inicializando geração de banners...', {})
        print('📊 Lendo tabela de preços (CSV)...')
        df = None
        read_error = None
        csv_sep = ','
        csv_encoding = 'utf-8-sig'
        required_columns = ['Unidade', 'Início', 'Fim', 'Código', 'Nome', 'Preço Comercial', 'Preço Promocional']
        sep_configs = [
            {'sep': ',', 'decimal': '.'},
            {'sep': ';', 'decimal': ','},
            {'sep': ';', 'decimal': '.'},
            {'sep': ',', 'decimal': ','},
            {'sep': '\t', 'decimal': ','}
        ]
        for encoding in ('utf-8-sig', 'utf-8', 'latin1'):
            for config in sep_configs:
                try:
                    read_kwargs = {
                        'sep': config['sep'],
                        'encoding': encoding,
                        'engine': 'python'
                    }
                    if config.get('decimal') is not None:
                        read_kwargs['decimal'] = config['decimal']
                    candidate_df = pd.read_csv(CSV_FILE, **read_kwargs)
                    candidate_df.columns = candidate_df.columns.str.strip()
                    if set(required_columns).issubset(set(candidate_df.columns)):
                        df = candidate_df
                        csv_sep = config['sep']
                        csv_encoding = encoding
                        print(f"✓ CSV lido com separador '{config['sep']}' (encoding {encoding})")
                        break
                    else:
                        print(f"⚠ Separador '{config['sep']}' com encoding {encoding} não contém colunas esperadas: {list(candidate_df.columns)}")
                except Exception as exc:
                    read_error = exc
                    df = None
            if df is not None:
                break
        if df is None:
            raise Exception(f'Erro ao ler CSV ({CSV_FILE}): {read_error}')

        update_progress('read_csv', 5, 'CSV lido com sucesso', {'total_registros': len(df) if df is not None else 0})

        df.columns = df.columns.str.strip()

        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()

        required_columns = ['Unidade', 'Início', 'Fim', 'Código', 'Nome', 'Preço Comercial', 'Preço Promocional']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print('⚠ Cabeçalho encontrado no CSV:', list(df.columns))
            try:
                with open(CSV_FILE, 'r', encoding='utf-8-sig') as raw_file:
                    raw_lines = raw_file.readlines()[:10]
                print('⚠ Primeiras linhas do CSV (UTF-8):')
                for line in raw_lines:
                    print(line.strip())
            except Exception as raw_exc:
                print(f'⚠ Não foi possível ler CSV em UTF-8: {raw_exc}')
            raise Exception(f'❌ Colunas faltando no CSV: {", ".join(missing_columns)}')

        # Adicionar coluna "Gerado" se não existir
        if 'Gerado' not in df.columns:
            df['Gerado'] = 'Não'
            print('✓ Coluna "Gerado" adicionada ao CSV')

        # Resetar índice para garantir índices sequenciais
        df = df.reset_index(drop=True)

        def parse_number(value):
            if pd.isna(value):
                return None
            s = str(value).strip()
            if not s:
                return None
            s = s.replace('R$', '').replace(' ', '')
            if ',' in s:
                if '.' in s and s.find('.') < s.rfind(','):
                    s = s.replace('.', '')
                s = s.replace(',', '.')
            return s

        for col in ['Preço Comercial', 'Preço Promocional']:
            df[col] = df[col].apply(parse_number)
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df['Código'] = pd.to_numeric(df['Código'].apply(lambda x: str(x).strip()), errors='coerce')

        df = df.dropna(subset=['Unidade', 'Nome', 'Código', 'Preço Comercial', 'Preço Promocional'])
        df['Código'] = df['Código'].astype(int)
        df['Unidade'] = df['Unidade'].astype(str).str.strip()
        df['Nome'] = df['Nome'].astype(str).str.strip()

        # Normalizar coluna Gerado
        df['Gerado'] = df['Gerado'].astype(str).str.strip()
        df['Gerado'] = df['Gerado'].apply(lambda x: 'Sim' if str(x).lower() in ('sim', 'yes', '1', 'true', 'x', '✓', 's') else 'Não')

        print(f'✓ Tabela lida: {len(df)} registros encontrados')
        itens_nao_gerados = len(df[df['Gerado'] == 'Não'])
        itens_gerados = len(df[df['Gerado'] == 'Sim'])
        print(f'  📊 Itens não gerados: {itens_nao_gerados}')
        print(f'  📊 Itens já gerados: {itens_gerados}')

        df['Desconto %'] = df.apply(lambda row: self.calculate_discount_percentage(row['Preço Comercial'], row['Preço Promocional']), axis=1)

        unidades = df['Unidade'].unique()
        print(f'✓ {len(unidades)} unidades encontradas')
        
        update_progress('read_csv', 10, f'CSV processado: {len(df)} registros, {len(unidades)} unidades', {
            'total_registros': len(df),
            'total_unidades': len(unidades),
            'itens_nao_gerados': itens_nao_gerados,
            'itens_gerados': itens_gerados
        })

        generated_paths = []
        data_atual = datetime.now().strftime('%d-%m-%Y')
        output_dir = os.path.join('banners', data_atual)
        os.makedirs(output_dir, exist_ok=True)
        
        total_unidades = len(unidades)
        unidade_atual = 0
        
        # Iniciar thread de envio WhatsApp para processamento paralelo
        if WHATSAPP_ENABLED:
            print('🚀 Iniciando thread de envio WhatsApp (processamento paralelo)...')
            self.start_whatsapp_thread()

        def format_date_display(value):
            if pd.isna(value):
                return ''
            value_str = str(value).strip()
            if not value_str:
                return ''
            try:
                dt = pd.to_datetime(value_str, dayfirst=True, errors='coerce')
                if pd.isna(dt):
                    return value_str
                return dt.strftime('%d/%m/%Y')
            except Exception:
                return value_str

        for unidade in unidades:
            unidade_atual += 1
            progresso_base = 10 + (unidade_atual - 1) * (85 / total_unidades) if total_unidades > 0 else 10
            
            print(f'\n📦 Processando unidade: {unidade}')
            update_progress('process_unit', progresso_base, f'Processando unidade: {unidade} ({unidade_atual}/{total_unidades})', {
                'unidade': unidade,
                'unidade_atual': unidade_atual,
                'total_unidades': total_unidades
            })
            
            df_unidade = df[(df['Unidade'] == unidade) & (df['Gerado'] == 'Não')].copy()
            
            if len(df_unidade) == 0:
                print(f'  ⚠ Unidade {unidade}: todos os itens já foram gerados. Pulando...')
                continue

            df_unidade = df_unidade.sort_values('Desconto %', ascending=False)
            
            total_itens_unidade = len(df_unidade)
            banner_sequencia = 1
            total_banners_gerados = 0
            unidade_banners = []  # Lista para armazenar banners desta unidade

            # Primeiro, marcar produtos sem imagem como gerados para evitar loop infinito
            produtos_sem_imagem = []
            for idx, row in df_unidade.iterrows():
                codigo_val = int(row['Código'])
                imagem_url = self.check_image_exists(codigo_val)
                if not imagem_url:
                    produtos_sem_imagem.append(idx)
            
            if produtos_sem_imagem:
                print(f'  ⚠ {len(produtos_sem_imagem)} produto(s) sem imagem serão marcados como gerados.')
                for idx in produtos_sem_imagem:
                    df.loc[idx, 'Gerado'] = 'Sim'
                # Salvar CSV após marcar produtos sem imagem
                self.save_csv_with_format(df, CSV_FILE, csv_sep, csv_encoding)
                # Atualizar df_unidade
                df_unidade = df[(df['Unidade'] == unidade) & (df['Gerado'] == 'Não')].copy()
                df_unidade = df_unidade.sort_values('Desconto %', ascending=False)

            # Loop para gerar múltiplos banners até esgotar os itens
            while len(df_unidade) > 0:
                itens_restantes = len(df_unidade)
                progresso_banner = progresso_base + ((total_itens_unidade - itens_restantes) / total_itens_unidade) * (85 / total_unidades) if total_itens_unidade > 0 else progresso_base
                
                produtos_validos = []
                indices_para_marcar = []

                # Selecionar até 3 produtos com imagem válida
                update_progress('process_banner', progresso_banner, f'Selecionando produtos para banner #{banner_sequencia} (Unidade: {unidade})', {
                    'unidade': unidade,
                    'banner_sequencia': banner_sequencia,
                    'itens_restantes': itens_restantes
                })
                
                for idx, row in df_unidade.iterrows():
                    codigo_val = int(row['Código'])
                    imagem_url = self.check_image_exists(codigo_val)
                    if not imagem_url:
                        # Se por algum motivo ainda houver produto sem imagem, marcar e continuar
                        df.loc[idx, 'Gerado'] = 'Sim'
                        continue
                    
                    registro = row.to_dict()
                    # NÃO salvar _imagem_url aqui - deixar a função get_product_image_with_background_removed processar
                    # registro['_imagem_url'] = imagem_url  # REMOVIDO - sempre processar com remoção de fundo
                    produtos_validos.append(registro)
                    indices_para_marcar.append(idx)
                    
                    if len(produtos_validos) == 3:
                        break

                if not produtos_validos:
                    print(f'  ⚠ Unidade {unidade}: nenhum produto restante com imagem válida. Finalizando unidade.')
                    break

                if len(produtos_validos) < 3:
                    print(f'  ℹ Unidade {unidade}: banner #{banner_sequencia} com {len(produtos_validos)} produto(s) (últimos disponíveis).')

                # Obter dados do primeiro produto para o banner
                primeiro_produto = produtos_validos[0]
                nome_empresa_val = primeiro_produto.get('Nome Empresa', '')
                if pd.isna(nome_empresa_val) or str(nome_empresa_val).strip() == 'nan':
                    nome_empresa_val = ''
                nome_empresa_val = str(nome_empresa_val).strip()

                data_inicio = format_date_display(primeiro_produto.get('Início'))
                data_fim = format_date_display(primeiro_produto.get('Fim'))

                # Gerar nome do arquivo com sequência e hora
                hora_atual = datetime.now().strftime('%H-%M-%S')
                filename = f'{unidade}-{data_atual}-{banner_sequencia:03d}-{hora_atual}.jpg'
                output_path = os.path.join(output_dir, filename)

                print(f'  🎨 Gerando banner #{banner_sequencia}...')
                update_progress('process_banner', progresso_banner + 1, f'Gerando banner #{banner_sequencia} (Unidade: {unidade})', {
                    'unidade': unidade,
                    'banner_sequencia': banner_sequencia,
                    'total_produtos': len(produtos_validos)
                })
                
                # Processar imagens em paralelo (otimização)
                print(f'  🖼️ Processando {len(produtos_validos)} imagem(ns) de produto(s) em paralelo...')
                update_progress('process_images', progresso_banner + 2, f'Processando {len(produtos_validos)} imagem(ns) em paralelo...', {
                    'total_imagens': len(produtos_validos),
                    'banner_sequencia': banner_sequencia
                })
                imagens_processadas = self.process_images_in_parallel(produtos_validos, max_workers=3)
                
                # Substituir URLs de imagens nos produtos
                for produto in produtos_validos:
                    codigo = int(produto['Código'])
                    if codigo in imagens_processadas:
                        produto['_imagem_url_processada'] = imagens_processadas[codigo]
                
                update_progress('process_banner', progresso_banner + 3, f'Gerando HTML do banner #{banner_sequencia}...', {
                    'banner_sequencia': banner_sequencia
                })
                html = self.generate_html_banner(produtos_validos, unidade, nome_empresa_val, data_inicio, data_fim)

                print(f'  📸 Convertendo para JPEG: {filename}')
                update_progress('process_banner', progresso_banner + 4, f'Convertendo banner #{banner_sequencia} para imagem...', {
                    'banner_sequencia': banner_sequencia,
                    'filename': filename
                })
                self.html_to_image(html, output_path)
                print(f'  ✅ Banner salvo: {output_path}')
                generated_paths.append(output_path)
                
                # Upload para Cloudinary se habilitado
                if USE_CLOUDINARY:
                    try:
                        banner_url = upload_banner_to_cloudinary(output_path, unidade, data_atual, banner_sequencia)
                        if banner_url:
                            print(f'  ✅ Banner enviado para Cloudinary: {banner_url}')
                    except Exception as e:
                        print(f'  ⚠ Erro ao enviar banner para Cloudinary: {e}')
                unidade_banners.append(output_path)  # Adicionar à lista da unidade
                total_banners_gerados += 1

                update_progress('process_banner', progresso_banner + 5, f'Banner #{banner_sequencia} concluído!', {
                    'banner_sequencia': banner_sequencia,
                    'total_banners_gerados': total_banners_gerados,
                    'banners_gerados_unidade': total_banners_gerados
                })

                # Marcar produtos como gerados no DataFrame principal
                for idx in indices_para_marcar:
                    df.loc[idx, 'Gerado'] = 'Sim'

                # Salvar CSV em lotes (otimização - a cada 5 banners ou no final da unidade)
                banners_gerados_lote = banner_sequencia % 5
                if banners_gerados_lote == 0 or len(df_unidade) - len(indices_para_marcar) <= 0:
                    update_progress('save', progresso_banner + 5, f'Salvando progresso no CSV...', {
                        'itens_marcados': len(indices_para_marcar)
                    })
                if self.save_csv_with_format(df, CSV_FILE, csv_sep, csv_encoding):
                        print(f'  💾 CSV atualizado (lote): {len(indices_para_marcar)} item(ns) marcado(s) como gerado(s)')
                else:
                    print(f'  ⚠ Aviso: não foi possível salvar CSV após banner #{banner_sequencia}')

                # Atualizar df_unidade removendo itens já processados
                df_unidade = df[(df['Unidade'] == unidade) & (df['Gerado'] == 'Não')].copy()
                df_unidade = df_unidade.sort_values('Desconto %', ascending=False)
                
                banner_sequencia += 1

            print(f'  ✅ Unidade {unidade}: {total_banners_gerados} banner(ns) gerado(s)')
            update_progress('process_unit', progresso_base + (85 / total_unidades), f'Unidade {unidade} concluída: {total_banners_gerados} banner(s)', {
                'unidade': unidade,
                'banners_gerados': total_banners_gerados
            })
            
            # Adicionar banners à fila de envio WhatsApp (processamento paralelo)
            if unidade in self.unidade_to_group:
                group_id = self.unidade_to_group[unidade]
                
                if unidade_banners:
                    print(f'\n  📱 Adicionando {len(unidade_banners)} banner(s) à fila de envio para o grupo da unidade {unidade}...')
                    enqueued_count = 0
                    for banner_path in unidade_banners:
                        if self.enqueue_whatsapp_send(banner_path, group_id):
                            enqueued_count += 1
                    
                    if enqueued_count > 0:
                        print(f'  ✅ {enqueued_count} banner(s) adicionado(s) à fila de envio (processamento paralelo)')
                    else:
                        print(f'  ⚠ Não foi possível adicionar banners à fila de envio.')
                else:
                    print(f'  ℹ Nenhum banner gerado para a unidade {unidade} nesta execução.')
            else:
                print(f'  ℹ Unidade {unidade} não tem grupo configurado. Pulando envio para grupos.')
            
            # Salvar CSV final da unidade (garantir que está salvo)
            if total_banners_gerados > 0:
                self.save_csv_with_format(df, CSV_FILE, csv_sep, csv_encoding)

        # Fechar navegador ao final de tudo (otimização - liberar recursos)
        update_progress('complete', 93, 'Finalizando geração e aguardando envios WhatsApp...', {})
        self.close_browser()
        print('  ✓ Navegador Playwright fechado')
        
        # Aguardar fila de envio WhatsApp esvaziar
        if WHATSAPP_ENABLED and self.whatsapp_thread_running:
            print(f'\n⏳ Aguardando envio de banners ao WhatsApp ({self.whatsapp_queue.qsize()} banner(s) na fila)...')
            update_progress('complete', 95, f'Aguardando envio WhatsApp ({self.whatsapp_queue.qsize()} banner(s) na fila)...', {})
            
            # Aguardar fila esvaziar (com timeout máximo)
            try:
                # Aguardar até a fila esvaziar ou timeout de 5 minutos
                timeout_count = 0
                max_timeout = 300  # 5 minutos
                while not self.whatsapp_queue.empty() and timeout_count < max_timeout:
                    time.sleep(1)
                    timeout_count += 1
                    if timeout_count % 10 == 0:
                        queue_size = self.whatsapp_queue.qsize()
                        print(f'  ⏳ Aguardando... {queue_size} banner(s) ainda na fila...')
                        update_progress('complete', 95, f'Aguardando envio WhatsApp ({queue_size} banner(s) restantes)...', {})
                
                if self.whatsapp_queue.empty():
                    print(f'  ✅ Todos os banners foram processados pela fila de envio!')
                else:
                    print(f'  ⚠ Timeout: ainda há {self.whatsapp_queue.qsize()} banner(s) na fila')
            except Exception as e:
                print(f'  ⚠ Erro ao aguardar fila WhatsApp: {e}')
            
            # Parar thread de envio
            self.stop_whatsapp_thread()

        if generated_paths:
            update_progress('complete', 97, f'Enviando {len(generated_paths)} banner(s) ao Telegram...', {
                'total_banners': len(generated_paths)
            })
            print(f'\n📨 Enviando {len(generated_paths)} banner(s) ao Telegram...')
            self.send_to_telegram(generated_paths)
        else:
            print('\n⚠ Nenhum banner gerado, envio ao Telegram não realizado.')

        total_gerados = len(df[df['Gerado'] == 'Sim'])
        total_nao_gerados = len(df[df['Gerado'] == 'Não'])
        print(f'\n✅ Geração concluída!')
        print(f'  📊 Total de banners gerados nesta execução: {len(generated_paths)}')
        print(f'  📊 Itens marcados como gerados: {total_gerados}')
        print(f'  📊 Itens ainda não gerados: {total_nao_gerados}')
        
        update_progress('complete', 100, 'Geração concluída com sucesso!', {
            'total_banners_gerados': len(generated_paths),
            'total_itens_gerados': total_gerados,
            'total_itens_nao_gerados': total_nao_gerados
        })


if __name__ == '__main__':
    try:
        generator = BannerGenerator()
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == '--send-test':
            if len(sys.argv) > 2:
                test_path = sys.argv[2]
            else:
                banners_dir = Path('banners')
                candidates = sorted(banners_dir.glob('**/*.jpg'), key=lambda p: p.stat().st_mtime, reverse=True)
                test_path = str(candidates[0]) if candidates else None
            if not test_path:
                print('❌ Nenhum arquivo para enviar no teste.')
                sys.exit(1)
            if not os.path.exists(test_path):
                print(f"❌ Arquivo não encontrado: {test_path}")
                sys.exit(1)
            print(f"🔍 Enviando teste para o Telegram: {test_path}")
            generator.send_to_telegram([test_path])
            sys.exit(0)
        generator.generate_banners()
    except KeyboardInterrupt:
        print('\n⚠ Geração interrompida pelo usuário')
        generator.cleanup()  # Garantir fechamento do navegador e parar thread WhatsApp
        sys.exit(0)
    except Exception as e:
        print(f'❌ Erro: {e}')
        generator.cleanup()  # Garantir fechamento do navegador e parar thread WhatsApp
        import traceback
        traceback.print_exc()
        sys.exit(1)

