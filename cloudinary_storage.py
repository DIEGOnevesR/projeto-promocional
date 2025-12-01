"""
Módulo para gerenciar armazenamento de arquivos no Cloudinary
"""
import os
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import requests
import base64
from pathlib import Path

# Configurar Cloudinary
# Credenciais padrão (podem ser sobrescritas por variáveis de ambiente)
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', 'divlmyzig')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '573712429865238')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', 'm_yHXjNUHkm8N2S05Jt3mkgig5w')

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

def upload_image_to_cloudinary(file_path, folder='imagens', public_id=None, resource_type='image'):
    """
    Upload imagem para Cloudinary
    
    Args:
        file_path: Caminho do arquivo local
        folder: Pasta no Cloudinary (ex: 'imagens', 'bandeiras', 'banners')
        public_id: ID público (nome do arquivo sem extensão). Se None, usa nome do arquivo
        resource_type: Tipo de recurso ('image', 'raw' para outros arquivos)
    
    Returns:
        URL pública da imagem ou None se erro
    """
    try:
        if not os.path.exists(file_path):
            print(f'⚠️ Arquivo não encontrado: {file_path}')
            return None
        
        # Se public_id não fornecido, usar nome do arquivo sem extensão
        if public_id is None:
            public_id = Path(file_path).stem
        
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=True  # Sobrescrever se já existir
        )
        
        url = result.get('secure_url') or result.get('url')
        print(f'✅ Upload: {file_path} → {url}')
        return url
        
    except Exception as e:
        print(f'❌ Erro ao fazer upload de {file_path}: {e}')
        return None

def upload_file_to_cloudinary(file_path, folder='files', public_id=None):
    """
    Upload arquivo genérico (CSV, Excel, JSON) para Cloudinary como 'raw'
    
    Args:
        file_path: Caminho do arquivo local
        folder: Pasta no Cloudinary
        public_id: ID público (nome do arquivo sem extensão)
    
    Returns:
        URL pública do arquivo ou None se erro
    """
    try:
        if not os.path.exists(file_path):
            print(f'⚠️ Arquivo não encontrado: {file_path}')
            return None
        
        if public_id is None:
            public_id = Path(file_path).stem
        
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            public_id=public_id,
            resource_type='raw',
            overwrite=True
        )
        
        url = result.get('secure_url') or result.get('url')
        print(f'✅ Upload: {file_path} → {url}')
        return url
        
    except Exception as e:
        print(f'❌ Erro ao fazer upload de {file_path}: {e}')
        return None

def get_image_base64_from_cloudinary(public_id, folder='imagens', format='auto'):
    """
    Busca imagem do Cloudinary e retorna base64 - VERSÃO TESTADA E FUNCIONAL
    
    Args:
        public_id: ID público da imagem (nome sem extensão, ex: "Logo")
        folder: Pasta no Cloudinary (padrão: 'imagens')
        format: Formato desejado ('auto', 'png', 'jpg', etc)
    
    Returns:
        String base64 da imagem ou None se erro
    """
    try:
        # Garantir configuração
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )
        
        # Construir public_id completo (formato: "imagens/Logo")
        full_public_id = f'{folder}/{public_id}'
        
        # Método 1: Usar cloudinary.api.resource (testado e funciona)
        try:
            resource = cloudinary.api.resource(full_public_id)
            url = resource.get('secure_url') or resource.get('url')
            
            if url:
                # Fazer download da imagem
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    # Converter para base64
                    return base64.b64encode(response.content).decode('utf-8')
        except:
            # Se api.resource falhar, tentar método alternativo
            pass
        
        # Método 2: Usar cloudinary_url como fallback (também testado e funciona)
        try:
            url, _ = cloudinary_url(full_public_id, secure=True)
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
        except:
            pass
        
        return None
            
    except Exception as e:
        return None

def get_image_url_from_cloudinary(public_id, folder='imagens', format='auto', transformations=None):
    """
    Retorna URL pública da imagem no Cloudinary
    
    Args:
        public_id: ID público da imagem
        folder: Pasta no Cloudinary
        format: Formato desejado
        transformations: Transformações opcionais (ex: {'width': 800, 'height': 600})
    
    Returns:
        URL pública da imagem
    """
    try:
        url, options = cloudinary_url(
            f'{folder}/{public_id}',
            format=format,
            secure=True,
            transformation=transformations
        )
        return url
    except Exception as e:
        print(f'❌ Erro ao gerar URL: {e}')
        return None

def upload_banner_to_cloudinary(banner_path, unidade, data_atual, sequencia):
    """
    Upload banner gerado para Cloudinary
    
    Args:
        banner_path: Caminho local do banner
        unidade: Nome da unidade
        data_atual: Data no formato DD-MM-YYYY
        sequencia: Número sequencial do banner
    
    Returns:
        URL pública do banner ou None se erro
    """
    public_id = f'{unidade}-{data_atual}-{sequencia:03d}'
    return upload_image_to_cloudinary(
        banner_path,
        folder='banners',
        public_id=public_id
    )

def download_file_from_cloudinary(public_id, folder='files', save_path=None):
    """
    Download arquivo do Cloudinary (raw files como CSV, Excel, etc)
    
    Args:
        public_id: ID público do arquivo (pode incluir extensão)
        folder: Pasta no Cloudinary
        save_path: Caminho local para salvar (opcional)
    
    Returns:
        Conteúdo do arquivo (bytes) ou None se erro
    """
    try:
        # Construir public_id completo
        full_public_id = f'{folder}/{public_id}'
        
        # Buscar via API (método mais confiável - retorna URL com versão correta)
        try:
            resource = cloudinary.api.resource(full_public_id, resource_type='raw')
            url = resource.get('secure_url') or resource.get('url')
            if not url:
                return None
        except Exception as api_error:
            # Se falhar, tentar usar cloudinary_url como fallback
            try:
                url, _ = cloudinary_url(full_public_id, resource_type='raw', secure=True)
            except:
                print(f'⚠️ Erro ao buscar arquivo via API: {api_error}')
                return None
        
        if not url:
            return None
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            content = response.content
            
            if save_path:
                os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(content)
                print(f'✅ Arquivo salvo: {save_path}')
            
            return content
        else:
            print(f'⚠️ Erro ao baixar arquivo: HTTP {response.status_code}')
            return None
            
    except Exception as e:
        print(f'❌ Erro ao baixar arquivo: {e}')
        import traceback
        traceback.print_exc()
        return None

def get_csv_from_cloudinary(public_id='Tabela de Preço', folder='files', encoding='utf-8-sig'):
    """
    Busca CSV do Cloudinary e retorna como string
    
    Args:
        public_id: ID público do arquivo CSV (pode ser com ou sem extensão)
        folder: Pasta no Cloudinary (padrão: 'files')
        encoding: Encoding do arquivo (padrão: 'utf-8-sig')
    
    Returns:
        String com conteúdo do CSV ou None se erro
    """
    try:
        # Lista de variações para tentar (priorizar com extensão .csv)
        variations = []
        
        # Se não tem extensão, adicionar .csv primeiro (mais comum)
        if not public_id.endswith('.csv'):
            variations.append(f'{public_id}.csv')
            variations.append(public_id)  # Tentar sem extensão também
        else:
            # Se já tem extensão, tentar primeiro com extensão
            variations.append(public_id)
            variations.append(public_id[:-4])  # Tentar sem extensão
        
        # Tentar cada variação
        for variant in variations:
            try:
                content = download_file_from_cloudinary(variant, folder=folder)
                if content:
                    return content.decode(encoding)
            except Exception as e:
                # Continuar tentando outras variações
                continue
        
        return None
    except Exception as e:
        print(f'❌ Erro ao ler CSV do Cloudinary: {e}')
        import traceback
        traceback.print_exc()
        return None

def upload_csv_to_cloudinary(file_path, public_id='Tabela de Preço', folder='files'):
    """
    Upload CSV para Cloudinary
    
    Args:
        file_path: Caminho do arquivo CSV local
        public_id: ID público no Cloudinary (padrão: 'Tabela de Preço')
        folder: Pasta no Cloudinary (padrão: 'files')
    
    Returns:
        URL pública do arquivo ou None se erro
    """
    return upload_file_to_cloudinary(file_path, folder=folder, public_id=public_id)

def delete_from_cloudinary(public_id, folder='imagens', resource_type='image'):
    """
    Deleta arquivo do Cloudinary
    
    Args:
        public_id: ID público do arquivo
        folder: Pasta no Cloudinary
        resource_type: Tipo de recurso ('image', 'raw')
    
    Returns:
        True se deletado com sucesso, False caso contrário
    """
    try:
        full_public_id = f'{folder}/{public_id}'
        result = cloudinary.uploader.destroy(
            full_public_id,
            resource_type=resource_type
        )
        
        if result.get('result') == 'ok':
            print(f'✅ Deletado: {full_public_id}')
            return True
        else:
            print(f'⚠️ Não foi possível deletar: {full_public_id}')
            return False
            
    except Exception as e:
        print(f'❌ Erro ao deletar: {e}')
        return False

def upload_cache_image_to_cloudinary(codigo, image_bytes):
    """
    Upload imagem de cache processada para Cloudinary
    
    Args:
        codigo: Código do produto
        image_bytes: Bytes da imagem (PNG)
    
    Returns:
        URL pública da imagem ou None se erro
    """
    try:
        import io
        import tempfile
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Upload para Cloudinary
            result = cloudinary.uploader.upload(
                tmp_path,
                folder='cache',
                public_id=str(codigo),
                resource_type='image',
                overwrite=True
            )
            url = result.get('secure_url') or result.get('url')
            return url
        finally:
            # Limpar arquivo temporário
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        print(f'❌ Erro ao fazer upload de cache para Cloudinary: {e}')
        return None

def get_cache_image_from_cloudinary(codigo):
    """
    Busca imagem de cache do Cloudinary e retorna base64
    
    Args:
        codigo: Código do produto
    
    Returns:
        String base64 da imagem (data URI) ou None se erro
    """
    try:
        url, _ = cloudinary_url(
            f'cache/{codigo}',
            format='png',
            secure=True
        )
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            import base64
            img_base64 = base64.b64encode(response.content).decode('utf-8')
            return f'data:image/png;base64,{img_base64}'
        else:
            return None
            
    except Exception as e:
        return None

def save_template_to_cloudinary(template_data):
    """
    Salva template JSON no Cloudinary
    
    Args:
        template_data: Dicionário com dados do template
    
    Returns:
        URL pública do arquivo ou None se erro
    """
    try:
        import json
        import tempfile
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_file:
            json.dump(template_data, tmp_file, indent=2, ensure_ascii=False)
            tmp_path = tmp_file.name
        
        try:
            # Upload para Cloudinary
            result = cloudinary.uploader.upload(
                tmp_path,
                folder='templates',
                public_id='banner-template',
                resource_type='raw',
                overwrite=True
            )
            url = result.get('secure_url') or result.get('url')
            return url
        finally:
            # Limpar arquivo temporário
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        print(f'❌ Erro ao salvar template no Cloudinary: {e}')
        return None

def load_template_from_cloudinary():
    """
    Carrega template JSON do Cloudinary
    
    Returns:
        Dicionário com dados do template ou None se erro
    """
    try:
        import json
        
        url, _ = cloudinary_url(
            'templates/banner-template',
            format='json',
            secure=True,
            resource_type='raw'
        )
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            template_data = json.loads(response.text)
            return template_data
        else:
            return None
            
    except Exception as e:
        return None

