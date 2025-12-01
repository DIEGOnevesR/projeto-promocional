#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servidor Flask para executar o gerador de banners promocionais
"""
import os
import sys
import json
import threading
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

app = Flask(__name__)
CORS(app)

# Estado global da execução
execution_state = {
    'status': 'idle',  # idle, running, completed, error, stopped
    'progress': 0,
    'task': '',
    'logs': [],
    'error': None,
    'details': {},  # Detalhes adicionais do progresso
    'stats': {  # Estatísticas da execução
        'total_unidades': 0,
        'unidade_atual': 0,
        'unidade_nome': '',
        'total_banners': 0,
        'banners_gerados': 0,
        'banner_atual': 0,
        'itens_processados': 0,
        'itens_total': 0
    }
}

# Lock para thread safety
execution_lock = threading.Lock()
execution_thread = None

def log_message(message):
    """Adiciona uma mensagem aos logs"""
    with execution_lock:
        execution_state['logs'].append(message)
        # Limitar logs a 1000 mensagens
        if len(execution_state['logs']) > 1000:
            execution_state['logs'] = execution_state['logs'][-1000:]

def progress_callback(opcao, progresso, tarefa, detalhes):
    """Callback para atualizar progresso durante a geração"""
    global execution_state
    
    with execution_lock:
        execution_state['progress'] = min(100, max(0, int(progresso)))
        execution_state['task'] = tarefa
        execution_state['details'] = detalhes
        
        # Atualizar estatísticas baseado na opção
        if opcao == 'read_csv' and detalhes:
            if 'total_unidades' in detalhes:
                execution_state['stats']['total_unidades'] = detalhes.get('total_unidades', 0)
            if 'total_registros' in detalhes:
                execution_state['stats']['itens_total'] = detalhes.get('total_registros', 0)
        elif opcao == 'process_unit' and detalhes:
            execution_state['stats']['unidade_atual'] = detalhes.get('unidade_atual', 0)
            execution_state['stats']['unidade_nome'] = detalhes.get('unidade', '')
        elif opcao == 'process_banner' and detalhes:
            execution_state['stats']['banner_atual'] = detalhes.get('banner_sequencia', 0)
            if 'total_banners_gerados' in detalhes:
                execution_state['stats']['banners_gerados'] = detalhes.get('total_banners_gerados', 0)
        elif opcao == 'complete' and detalhes:
            execution_state['stats']['total_banners'] = detalhes.get('total_banners_gerados', 0)
            execution_state['stats']['itens_processados'] = detalhes.get('total_itens_gerados', 0)

def run_generator():
    """Executa o gerador de banners em uma thread separada"""
    global execution_state, execution_thread
    
    try:
        with execution_lock:
            execution_state['status'] = 'running'
            execution_state['progress'] = 0
            execution_state['task'] = 'Iniciando geração...'
            execution_state['error'] = None
            execution_state['details'] = {}
            execution_state['stats'] = {
                'total_unidades': 0,
                'unidade_atual': 0,
                'unidade_nome': '',
                'total_banners': 0,
                'banners_gerados': 0,
                'banner_atual': 0,
                'itens_processados': 0,
                'itens_total': 0
            }
        
        log_message('🚀 Iniciando geração de banners...')
        
        # Importar main aqui para evitar erros de importação
        try:
            from main import BannerGenerator
        except ImportError:
            log_message('❌ Erro: Arquivo main.py não encontrado!')
            with execution_lock:
                execution_state['status'] = 'error'
                execution_state['error'] = 'Arquivo main.py não encontrado'
            return
        
        log_message('✓ Módulo main.py carregado com sucesso')
        
        # Garantir que estamos no diretório correto
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if os.getcwd() != script_dir:
            log_message(f'⚠ Diretório de trabalho: {os.getcwd()}')
            log_message(f'✓ Mudando para diretório do script: {script_dir}')
            os.chdir(script_dir)
            log_message(f'✓ Diretório de trabalho atual: {os.getcwd()}')
        
        # Criar instância do gerador
        try:
            generator = BannerGenerator()
            log_message('✓ Gerador de banners criado')
        except Exception as e:
            log_message(f'❌ Erro ao criar gerador: {str(e)}')
            import traceback
            log_message(f'Detalhes: {traceback.format_exc()}')
            with execution_lock:
                execution_state['status'] = 'error'
                execution_state['error'] = str(e)
            return
        
        # Verificar se há template salvo
        template_file = 'banner-template.json'
        if os.path.exists(template_file):
            log_message(f'✓ Template encontrado: {template_file}')
        else:
            log_message('⚠ Template não encontrado, usando valores padrão')
        
        # Executar geração com callback de progresso
        try:
            with execution_lock:
                execution_state['progress'] = 5
                execution_state['task'] = 'Lendo planilha CSV...'
            
            log_message('📊 Lendo planilha de preços...')
            generator.generate_banners(progress_callback=progress_callback)
            
            with execution_lock:
                execution_state['progress'] = 100
                execution_state['task'] = 'Geração concluída!'
                execution_state['status'] = 'completed'
            
            log_message('✅ Geração concluída com sucesso!')
            
        except Exception as e:
            log_message(f'❌ Erro durante a geração: {str(e)}')
            import traceback
            log_message(f'Detalhes: {traceback.format_exc()}')
            with execution_lock:
                execution_state['status'] = 'error'
                execution_state['error'] = str(e)
                
    except Exception as e:
        log_message(f'❌ Erro fatal: {str(e)}')
        import traceback
        log_message(f'Detalhes: {traceback.format_exc()}')
        with execution_lock:
            execution_state['status'] = 'error'
            execution_state['error'] = str(e)
    finally:
        execution_thread = None

@app.route('/save-template', methods=['POST'])
def save_template():
    """Salva o template JSON no servidor"""
    try:
        template_data = request.get_json()
        
        # Salvar no arquivo banner-template.json
        with open('banner-template.json', 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({'status': 'success', 'message': 'Template salvo com sucesso'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/execute', methods=['POST'])
def execute():
    """Inicia a execução do gerador de banners"""
    global execution_thread, execution_state
    
    with execution_lock:
        if execution_state['status'] == 'running':
            return jsonify({'status': 'error', 'error': 'Execução já está em andamento'}), 400
        
        # Resetar estado
        execution_state['status'] = 'idle'
        execution_state['progress'] = 0
        execution_state['task'] = ''
        execution_state['logs'] = []
        execution_state['error'] = None
    
    # Iniciar thread de execução
    execution_thread = threading.Thread(target=run_generator, daemon=True)
    execution_thread.start()
    
    return jsonify({'status': 'started', 'message': 'Execução iniciada'})

@app.route('/status', methods=['GET'])
def status():
    """Retorna o status atual da execução"""
    with execution_lock:
        return jsonify({
            'status': execution_state['status'],
            'progress': execution_state['progress'],
            'task': execution_state['task'],
            'logs': execution_state['logs'],
            'error': execution_state['error'],
            'details': execution_state.get('details', {}),
            'stats': execution_state.get('stats', {})
        })

@app.route('/stop', methods=['POST'])
def stop():
    """Para a execução do gerador"""
    global execution_state
    
    with execution_lock:
        if execution_state['status'] == 'running':
            execution_state['status'] = 'stopped'
            execution_state['task'] = 'Parando execução...'
            log_message('⚠ Execução interrompida pelo usuário')
            return jsonify({'status': 'stopped', 'message': 'Execução interrompida'})
        else:
            return jsonify({'status': 'error', 'error': 'Nenhuma execução em andamento'}), 400

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({'status': 'ok', 'message': 'Servidor funcionando'})

@app.route('/', methods=['GET'])
@app.route('/index.html', methods=['GET'])
def index():
    """Serve o template_editor.html"""
    return send_from_directory('.', 'template_editor.html')

@app.route('/preprocess-images', methods=['POST'])
def preprocess_images():
    """Pré-processa todas as imagens da tabela de preços"""
    try:
        from main import BannerGenerator
        
        generator = BannerGenerator()
        resultado = generator.preprocess_all_images()
        
        if resultado:
            return jsonify({
                'status': 'success',
                'message': 'Pré-processamento concluído',
                'resultado': resultado
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'Erro no pré-processamento'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/get-product-image/<int:codigo>', methods=['GET'])
def get_product_image(codigo):
    """Retorna imagem do produto com fundo removido e normalizada"""
    try:
        from main import BannerGenerator
        
        generator = BannerGenerator()
        imagem_url = generator.get_product_image_with_background_removed(codigo)
        
        if imagem_url:
            return jsonify({
                'status': 'success',
                'data': imagem_url
            })
        else:
            return jsonify({
                'status': 'error',
                'error': f'Imagem não encontrada para código {codigo}'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/get-image/<image_name>', methods=['GET'])
def get_image(image_name):
    """Retorna uma imagem do Cloudinary (pasta imagens) como base64"""
    try:
        # Tentar importar cloudinary_storage
        try:
            from cloudinary_storage import get_image_base64_from_cloudinary
        except ImportError:
            # Fallback: tentar carregar do arquivo local se Cloudinary não disponível
            import base64
            images_folder = 'Imagens'
            
            # Mapear nomes de imagem solicitados para nomes reais
            image_mapping = {
                'base-produto': 'Base do Produto',
                'call-action': 'Call Action',
                'fundo': 'Fundo',
                'logo-inferior': 'Logo Inferior',
                'logo-ofertas': 'logo ofertas',
                'logo-superior': 'Logo',
            }
            
            # Verificar se há um mapeamento
            base_name = image_mapping.get(image_name, image_name)
            possible_names = [
                base_name + '.png',
                base_name + '.jpg',
                base_name + '.jpeg',
                base_name + '.PNG',
                base_name + '.JPG',
                base_name + '.JPEG',
            ]
            
            # Tentar encontrar o arquivo local
            for name in possible_names:
                image_path = os.path.join(images_folder, name)
                if os.path.exists(image_path):
                    try:
                        with open(image_path, 'rb') as f:
                            image_data = base64.b64encode(f.read()).decode('utf-8')
                        
                        # Determinar MIME type
                        mime_type = 'image/png'
                        if name.lower().endswith('.jpg') or name.lower().endswith('.jpeg'):
                            mime_type = 'image/jpeg'
                        
                        return jsonify({
                            'status': 'success',
                            'data': f'data:{mime_type};base64,{image_data}',
                            'mime_type': mime_type
                        })
                    except Exception as e:
                        return jsonify({'status': 'error', 'error': str(e)}), 500
            
            return jsonify({'status': 'error', 'error': f'Imagem não encontrada: {image_name}'}), 404
        
        # Mapear nomes de imagem solicitados para nomes reais no Cloudinary
        image_mapping = {
            'base-produto': 'Base do Produto',
            'call-action': 'Call Action',
            'fundo': 'Fundo',
            'logo-inferior': 'Logo Inferior',
            'logo-ofertas': 'logo ofertas',
            'logo-superior': 'Logo',
        }
        
        # Obter nome real da imagem
        base_name = image_mapping.get(image_name, image_name)
        
        # Buscar imagem do Cloudinary
        try:
            image_data = get_image_base64_from_cloudinary(base_name, folder='imagens')
            
            if image_data:
                # Determinar MIME type (assumir PNG por padrão, mas Cloudinary pode retornar qualquer formato)
                mime_type = 'image/png'
                # Tentar detectar pelo nome
                if 'jpg' in base_name.lower() or 'jpeg' in base_name.lower():
                    mime_type = 'image/jpeg'
                
                return jsonify({
                    'status': 'success',
                    'data': f'data:{mime_type};base64,{image_data}',
                    'mime_type': mime_type
                })
            else:
                # Se Cloudinary falhou, tentar fallback local
                import base64
                images_folder = 'Imagens'
                possible_names = [
                    base_name + '.png',
                    base_name + '.jpg',
                    base_name + '.jpeg',
                    base_name + '.PNG',
                    base_name + '.JPG',
                    base_name + '.JPEG',
                ]
                
                for name in possible_names:
                    image_path = os.path.join(images_folder, name)
                    if os.path.exists(image_path):
                        try:
                            with open(image_path, 'rb') as f:
                                image_data = base64.b64encode(f.read()).decode('utf-8')
                            
                            mime_type = 'image/png'
                            if name.lower().endswith('.jpg') or name.lower().endswith('.jpeg'):
                                mime_type = 'image/jpeg'
                            
                            return jsonify({
                                'status': 'success',
                                'data': f'data:{mime_type};base64,{image_data}',
                                'mime_type': mime_type
                            })
                        except Exception as e:
                            pass
                
                return jsonify({'status': 'error', 'error': f'Imagem não encontrada no Cloudinary nem localmente: {image_name} (procurando: {base_name})'}), 404
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f'❌ Erro ao buscar imagem do Cloudinary: {e}')
            print(f'Detalhes: {error_details}')
            return jsonify({'status': 'error', 'error': f'Erro ao buscar imagem: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/upload-image', methods=['POST'])
def upload_image():
    """Faz upload de uma imagem e retorna o caminho"""
    try:
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'error': 'Nenhuma imagem fornecida'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'status': 'error', 'error': 'Nome de arquivo vazio'}), 400
        
        # Verificar extensão
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'status': 'error', 'error': f'Extensão não permitida: {file_ext}'}), 400
        
        # Criar pasta de uploads se não existir
        upload_folder = os.path.join('uploads', datetime.now().strftime('%Y-%m-%d'))
        os.makedirs(upload_folder, exist_ok=True)
        
        # Gerar nome único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f'{timestamp}_{filename}'
        file_path = os.path.join(upload_folder, safe_filename)
        
        # Salvar arquivo
        file.save(file_path)
        
        # Retornar caminho absoluto
        abs_path = os.path.abspath(file_path)
        
        return jsonify({
            'status': 'success',
            'message': 'Imagem enviada com sucesso',
            'path': abs_path,
            'filename': safe_filename
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/load-unidades', methods=['GET'])
def load_unidades():
    """Carrega mapeamento de unidades para grupos do arquivo Unidades.xlsx"""
    try:
        import pandas as pd
        
        unidades_file = 'Unidades.xlsx'
        
        if not os.path.exists(unidades_file):
            return jsonify({
                'success': False,
                'error': f'Arquivo {unidades_file} não encontrado'
            }), 404
        
        # Ler arquivo Excel
        df_unidades = pd.read_excel(unidades_file, engine='openpyxl')
        df_unidades.columns = df_unidades.columns.str.strip()
        
        # Verificar colunas necessárias
        if 'Unidade' not in df_unidades.columns or 'id_grupo' not in df_unidades.columns:
            return jsonify({
                'success': False,
                'error': 'Arquivo não contém colunas "Unidade" e "id_grupo"'
            }), 400
        
        # Criar mapeamento
        mapping = {}
        for _, row in df_unidades.iterrows():
            unidade = str(row['Unidade']).strip()
            id_grupo = str(row['id_grupo']).strip()
            
            if unidade and id_grupo and id_grupo.lower() != 'nan':
                mapping[unidade] = id_grupo
        
        return jsonify({
            'success': True,
            'mapping': mapping,
            'count': len(mapping)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def preprocess_on_startup():
    """Pré-processa imagens ao iniciar o servidor (em background)"""
    import threading
    
    def preprocess():
        try:
            time.sleep(2)  # Aguardar servidor iniciar
            from main import BannerGenerator
            generator = BannerGenerator()
            print('\n🔄 Iniciando pré-processamento de imagens em background...')
            generator.preprocess_all_images()
            print('✅ Pré-processamento concluído!\n')
        except Exception as e:
            print(f'⚠ Erro no pré-processamento: {e}')
    
    # Iniciar em thread separada para não bloquear o servidor
    thread = threading.Thread(target=preprocess, daemon=True)
    thread.start()

if __name__ == '__main__':
    # Configuração para produção vs desenvolvimento
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = '0.0.0.0' if not debug else '127.0.0.1'
    
    print('🚀 Iniciando servidor Flask...')
    print(f'📡 Servidor disponível em: http://{host}:{port}')
    print('💡 Abra o template_editor.html no navegador e use o botão "Executar Gerador"')
    print('⚠ Para parar o servidor, pressione Ctrl+C')
    
    # Iniciar pré-processamento em background apenas em desenvolvimento
    if debug:
        preprocess_on_startup()
    
    app.run(host=host, port=port, debug=debug)
