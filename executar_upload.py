import os, glob, sys
from pathlib import Path
import cloudinary.uploader
import cloudinary

cloudinary.config(cloud_name='divlmyzig', api_key='573712429865238', api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w')

print('='*60)
print('UPLOAD CLOUDINARY')
print('='*60)

uploaded = 0
errors = 0

# Imagens
print('\nImagens:')
for img in ['Base do Produto.png', 'Call Action.png', 'Fundo.png', 'Logo.png', 'Logo Inferior.png', 'logo ofertas.png']:
    p = os.path.join('Imagens', img)
    if os.path.exists(p):
        try:
            cloudinary.uploader.upload(p, folder='imagens', public_id=Path(img).stem, overwrite=True)
            print(f'  OK: {img}')
            uploaded += 1
        except Exception as e:
            print(f'  ERRO: {img} - {e}')
            errors += 1

# Bandeiras
print('\nBandeiras:')
for b in glob.glob('Bandeira/*.png'):
    try:
        cloudinary.uploader.upload(b, folder='bandeiras', public_id=Path(b).stem, overwrite=True)
        print(f'  OK: {os.path.basename(b)}')
        uploaded += 1
    except Exception as e:
        print(f'  ERRO: {os.path.basename(b)} - {e}')
        errors += 1

# Fontes
print('\nFontes:')
for f in glob.glob('Fontes/*.ttf'):
    try:
        cloudinary.uploader.upload(f, folder='fontes', public_id=Path(f).stem, resource_type='raw', overwrite=True)
        print(f'  OK: {os.path.basename(f)}')
        uploaded += 1
    except Exception as e:
        print(f'  ERRO: {os.path.basename(f)} - {e}')
        errors += 1

# Tabelas
print('\nTabelas:')
for t in ['Tabela de Preço.csv', 'Unidades.xlsx']:
    if os.path.exists(t):
        try:
            cloudinary.uploader.upload(t, folder='tabelas', public_id=Path(t).stem, resource_type='raw', overwrite=True)
            print(f'  OK: {t}')
            uploaded += 1
        except Exception as e:
            print(f'  ERRO: {t} - {e}')
            errors += 1

print(f'\nTotal: {uploaded} OK, {errors} erros')


