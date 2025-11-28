# 🚀 Guia de Deploy - Gerador de Banners Promocionais

Este guia explica como publicar o projeto em nuvem.

## 📋 Pré-requisitos

- Conta no GitHub/GitLab (para versionamento)
- Conta em uma plataforma de deploy (Render, Railway, Heroku, etc.)
- Python 3.11 instalado localmente (para testes)

## 🌐 Opções de Plataformas

### 1. Render.com (Recomendado - Gratuito)

**Vantagens:**
- Plano gratuito disponível
- Deploy automático via Git
- SSL automático
- Fácil configuração

**Passos:**

1. **Criar conta no Render.com**
   - Acesse: https://render.com
   - Faça login com GitHub/GitLab

2. **Preparar repositório Git**
   ```bash
   git init
   git add .
   git commit -m "Preparar para deploy"
   git remote add origin SEU_REPOSITORIO_GIT
   git push -u origin main
   ```

3. **Criar novo Web Service no Render**
   - Clique em "New +" → "Web Service"
   - Conecte seu repositório Git
   - Configure:
     - **Name:** banner-generator
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn server:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 300`
     - **Instance Type:** Free (ou Starter para mais recursos)

4. **Configurar Variáveis de Ambiente**
   - No painel do Render, vá em "Environment"
   - Adicione:
     ```
     FLASK_ENV=production
     FLASK_DEBUG=False
     ```

5. **Deploy**
   - Render fará deploy automático
   - Aguarde alguns minutos
   - Anote a URL gerada (ex: `https://banner-generator.onrender.com`)

### 2. Railway.app

**Passos:**

1. Criar conta em https://railway.app
2. Conectar repositório Git
3. Railway detecta automaticamente Python
4. Configure:
   - **Start Command:** `gunicorn server:app --bind 0.0.0.0:$PORT`
   - Adicione variáveis de ambiente no painel

### 3. Heroku

**Passos:**

1. Instalar Heroku CLI
2. Login: `heroku login`
3. Criar app: `heroku create seu-app-nome`
4. Deploy: `git push heroku main`
5. Configurar variáveis: `heroku config:set FLASK_ENV=production`

## 🔧 Configuração do Frontend

Após fazer deploy do backend, você precisa atualizar o `template_editor.html`:

1. **Opção 1: Editar manualmente**
   - Abra `template_editor.html`
   - Procure por `getApiUrl()` na linha ~1866
   - Substitua a URL hardcoded pela URL do seu backend

2. **Opção 2: Usar detecção automática**
   - O arquivo já foi ajustado para detectar automaticamente
   - Se estiver rodando localmente, usa `localhost:5000`
   - Se estiver em produção, usa a URL atual da página

## 📁 Estrutura de Arquivos

```
.
├── server.py              # Servidor Flask (backend)
├── main.py                # Lógica de geração de banners
├── template_editor.html   # Interface web (frontend)
├── requirements.txt       # Dependências Python
├── Procfile              # Configuração para Heroku/Render
├── runtime.txt           # Versão Python
├── render.yaml           # Configuração Render.com
└── .env.example          # Exemplo de variáveis de ambiente
```

## 🔐 Variáveis de Ambiente

Crie um arquivo `.env` (não commitar no Git) com:

```env
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000
```

**Importante:** Nunca commite arquivos com credenciais:
- `token.json`
- `credentials.json`
- `.env`

## 📦 Arquivos Estáticos

O projeto usa vários arquivos estáticos:
- **Imagens:** `Imagens/`, `Bandeira/`
- **Fontes:** `Fontes/`
- **Cache:** `cache_imagens_processadas/`

**Opções para produção:**

1. **Incluir no deploy** (mais simples)
   - Render/Railway incluem todos os arquivos
   - Limite de tamanho pode ser um problema

2. **Armazenamento em nuvem** (recomendado para produção)
   - AWS S3
   - Cloudinary
   - Google Cloud Storage

## 🚨 Limitações do Plano Gratuito

- **Timeout:** Processos longos podem ser interrompidos (30-60s)
- **Memória:** Limitada (512MB-1GB)
- **CPU:** Compartilhada
- **Sleep:** Render coloca apps gratuitos em sleep após inatividade

**Soluções:**
- Para processamento pesado, considere filas (Celery + Redis)
- Ou use plano pago para mais recursos

## 🔍 Verificar Deploy

Após o deploy, teste:

1. **Health Check:**
   ```
   GET https://seu-app.onrender.com/health
   ```

2. **Status:**
   ```
   GET https://seu-app.onrender.com/status
   ```

3. **Abrir template_editor.html:**
   - Faça upload do HTML para Netlify/Vercel
   - Ou sirva localmente apontando para o backend em nuvem

## 📝 Deploy do Frontend (HTML)

O `template_editor.html` pode ser publicado separadamente:

### Netlify (Recomendado)

1. Acesse https://netlify.com
2. Arraste a pasta ou conecte Git
3. Configure:
   - **Build command:** (deixe vazio)
   - **Publish directory:** (raiz do projeto)
4. Adicione variável de ambiente:
   - `VITE_BACKEND_URL=https://seu-backend.onrender.com`

### Vercel

1. Acesse https://vercel.com
2. Importe projeto
3. Configure variáveis de ambiente

## 🐛 Troubleshooting

### Erro: "Module not found"
- Verifique se `requirements.txt` está completo
- Execute `pip install -r requirements.txt` localmente para testar

### Erro: "Port already in use"
- Render/Railway definem `$PORT` automaticamente
- Não precisa configurar manualmente

### Timeout durante processamento
- Processamento de imagens pode demorar
- Considere aumentar timeout no `Procfile`
- Ou implementar processamento assíncrono

### Imagens não carregam
- Verifique caminhos relativos
- Certifique-se que pastas estão incluídas no deploy
- Use caminhos absolutos ou CDN

## 📞 Suporte

Para problemas específicos:
- Render: https://render.com/docs
- Railway: https://docs.railway.app
- Heroku: https://devcenter.heroku.com

---

**Boa sorte com o deploy! 🎉**

