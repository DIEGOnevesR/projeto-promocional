import cloudinary.api
import cloudinary

cloudinary.config(cloud_name='divlmyzig', api_key='573712429865238', api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w')

print('Verificando arquivos no Cloudinary...')
print()

# Imagens
try:
    r = cloudinary.api.resources(type='upload', prefix='imagens', max_results=100)
    print(f'Imagens: {len(r.get("resources", []))} arquivos')
except:
    print('Erro ao verificar imagens')

# Bandeiras
try:
    r = cloudinary.api.resources(type='upload', prefix='bandeiras', max_results=100)
    print(f'Bandeiras: {len(r.get("resources", []))} arquivos')
except:
    print('Erro ao verificar bandeiras')

# Fontes
try:
    r = cloudinary.api.resources(type='upload', prefix='fontes', resource_type='raw', max_results=100)
    print(f'Fontes: {len(r.get("resources", []))} arquivos')
except:
    print('Erro ao verificar fontes')

# Tabelas
try:
    r = cloudinary.api.resources(type='upload', prefix='tabelas', resource_type='raw', max_results=100)
    print(f'Tabelas: {len(r.get("resources", []))} arquivos')
except:
    print('Erro ao verificar tabelas')


