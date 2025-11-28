# 🚀 Guia de Deploy para Nuvem

Este guia explica como publicar o projeto em diferentes plataformas de nuvem.

## 📋 Pré-requisitos

1. Conta em uma plataforma de deploy (Render, Railway, Heroku, etc.)
2. Repositório Git (GitHub, GitLab, Bitbucket)
3. Todos os arquivos de configuração já foram criados

## 🌐 Opção 1: Render.com (Recomendado)

### Passo a Passo:

1. **Criar conta no Render.com**
   - Acesse: https://render.com
   - Faça login com GitHub/GitLab

2. **Conectar Repositório**
   - No dashboard, clique em "New +" → "Web Service"
   - Conecte seu repositório Git

3. **Configurar o Serviço**
   - **Name**: `banner-generator` (ou o nome que preferir)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn server:app`
   - **Plan**: Escolha o plano (Starter tem plano gratuito)

4. **Variáveis de Ambiente**
   - Adicione as variáveis necessárias na seção "Environment Variables"
   - Consulte `.env.example` para referência

5. **Deploy**
   - Clique em "Create Web Service"
   - Aguarde o build e deploy

6. **Configurar Frontend**
   - Após o deploy, você receberá uma URL (ex: `https://banner-generator.onrender.com`)
   - Edite `template_editor.html` e substitua `http://localhost:5000` pela URL do seu backend

## 🚂 Opção 2: Railway.app

### Passo a Passo:

1. **Criar conta no Railway**
   - Acesse: https://railway.app
   - Faça login com GitHub

2. **Novo Projeto**
   - Clique em "New Project"
   - Selecione "Deploy from GitHub repo"
   - Escolha seu repositório

3. **Configuração Automática**
   - Railway detecta automaticamente que é um projeto Python
   - O `Procfile` será usado automaticamente

4. **Variáveis de Ambiente**
   - Vá em "Variables" e adicione as variáveis necessárias

5. **Deploy**
   - O deploy acontece automaticamente após o push

## 🟣 Opção 3: Heroku

### Passo a Passo:

1. **Instalar Heroku CLI**
   ```bash
   # Windows
   # Baixe de: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login no Heroku**
   ```bash
   heroku login
   ```

3. **Criar App**
   ```bash
   heroku create seu-app-banner-generator
   ```

4. **Configurar Variáveis de Ambiente**
   ```bash
   heroku config:set FLASK_DEBUG=false
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

## 📄 Publicar Frontend HTML

O arquivo `template_editor.html` pode ser publicado como site estático:

### Opção A: Netlify

1. Acesse https://netlify.com
2. Arraste a pasta do projeto ou conecte via Git
3. Configure:
   - **Build command**: (deixe vazio)
   - **Publish directory**: (raiz do projeto)
4. **Importante**: Edite o HTML para apontar para a URL do seu backend

### Opção B: Vercel

1. Acesse https://vercel.com
2. Conecte seu repositório Git
3. Configure como site estático
4. Edite o HTML para usar a URL do backend

### Opção C: GitHub Pages

1. No repositório GitHub, vá em Settings → Pages
2. Selecione a branch `main`
3. O site ficará em: `https://seu-usuario.github.io/seu-repo`

## ⚙️ Configurações Importantes

### 1. Atualizar URLs no Frontend

Após fazer deploy do backend, você precisa atualizar o `template_editor.html`:

```javascript
// Antes (desenvolvimento local):
const API_URL = 'http://localhost:5000';

// Depois (produção):
const API_URL = 'https://seu-app.onrender.com';
```

### 2. Variáveis de Ambiente

Configure estas variáveis na plataforma de deploy:

- `FLASK_DEBUG=false` (produção)
- `PORT` (geralmente definido automaticamente)
- Credenciais do Gmail (se usar)
- Credenciais do WhatsApp (se usar)

### 3. Arquivos Estáticos

Os seguintes arquivos precisam estar acessíveis:
- `Imagens/` - Imagens base dos banners
- `Fontes/` - Fontes customizadas
- `Bandeira/` - Bandeiras dos países
- `Tabela de Preço.csv` - Planilha de preços
- `Unidades.xlsx` - Mapeamento de unidades

**Dica**: Considere usar armazenamento em nuvem (S3, Cloudinary) para arquivos grandes.

### 4. Limites de Memória

O processamento de imagens pode consumir muita memória. Considere:
- Usar um plano com mais memória
- Otimizar o processamento de imagens
- Usar cache agressivo

### 5. Timeout

Processos longos podem dar timeout. Soluções:
- Usar filas (Celery + Redis)
- Processar em chunks menores
- Usar webhooks para notificar conclusão

## 🔍 Verificação Pós-Deploy

1. **Teste o Health Check**
   ```
   GET https://seu-app.onrender.com/health
   ```

2. **Teste o Frontend**
   - Abra o HTML publicado
   - Verifique se consegue se conectar ao backend

3. **Teste a Geração de Banners**
   - Faça uma geração de teste
   - Verifique se os banners são gerados corretamente

## 🐛 Troubleshooting

### Erro: "Module not found"
- Verifique se todas as dependências estão no `requirements.txt`
- Execute `pip install -r requirements.txt` localmente para testar

### Erro: "Port already in use"
- A plataforma define a porta automaticamente via variável `PORT`
- Não hardcode a porta no código

### Erro: "Timeout"
- Processos muito longos podem dar timeout
- Considere processar em background com filas

### Erro: "Memory limit exceeded"
- Upgrade do plano
- Otimize o processamento de imagens
- Use cache mais agressivo

## 📞 Suporte

Para problemas específicos, consulte a documentação da plataforma escolhida:
- Render: https://render.com/docs
- Railway: https://docs.railway.app
- Heroku: https://devcenter.heroku.com

