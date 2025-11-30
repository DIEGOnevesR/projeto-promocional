import os, glob, sys
from pathlib import Path
import cloudinary.uploader
import cloudinary

cloudinary.config(cloud_name='divlmyzig', api_key='573712429865238', api_secret='m_yHXjNUHkm8N2S05Jt3mkgig5w')

print('='*70)
print('UPLOAD COMPLETO PARA CLOUDINARY')
print('='*70)
print()

uploaded = 0
errors = 0
total = 0

# 1. Imagens
print('SEÇÃO 1: Imagens Padrão')
print('-'*70)
imagens = ['Base do Produto.png', 'Call Action.png', 'Fundo.png', 'Logo.png', 'Logo Inferior.png', 'logo ofertas.png']
for img in imagens:
    p = os.path.join('Imagens', img)
    if os.path.exists(p):
        total += 1
        try:
            print(f'[{total}] {img}...', end=' ')
            cloudinary.uploader.upload(p, folder='imagens', public_id=Path(img).stem, overwrite=True)
            print('OK')
            uploaded += 1
        except Exception as e:
            print(f'ERRO: {e}')
            errors += 1

# 2. Bandeiras
print()
print('SEÇÃO 2: Bandeiras')
print('-'*70)
if os.path.exists('Bandeira'):
    for b in sorted(glob.glob('Bandeira/*.png')):
        total += 1
        nome = os.path.basename(b)
        try:
            print(f'[{total}] {nome}...', end=' ')
            cloudinary.uploader.upload(b, folder='bandeiras', public_id=Path(b).stem, overwrite=True)
            print('OK')
            uploaded += 1
        except Exception as e:
            print(f'ERRO: {e}')
            errors += 1

# 3. Fontes
print()
print('SEÇÃO 3: Fontes')
print('-'*70)
if os.path.exists('Fontes'):
    for f in sorted(glob.glob('Fontes/*.ttf')):
        total += 1
        nome = os.path.basename(f)
        try:
            print(f'[{total}] {nome}...', end=' ')
            cloudinary.uploader.upload(f, folder='fontes', public_id=Path(f).stem, resource_type='raw', overwrite=True)
            print('OK')
            uploaded += 1
        except Exception as e:
            print(f'ERRO: {e}')
            errors += 1

# 4. Tabelas
print()
print('SEÇÃO 4: Tabelas')
print('-'*70)
for t in ['Tabela de Preço.csv', 'Unidades.xlsx']:
    if os.path.exists(t):
        total += 1
        try:
            print(f'[{total}] {t}...', end=' ')
            cloudinary.uploader.upload(t, folder='tabelas', public_id=Path(t).stem, resource_type='raw', overwrite=True)
            print('OK')
            uploaded += 1
        except Exception as e:
            print(f'ERRO: {e}')
            errors += 1

print()
print('='*70)
print(f'RESUMO: {uploaded}/{total} arquivos enviados com sucesso')
if errors > 0:
    print(f'ERROS: {errors} arquivos falharam')
print('='*70)


