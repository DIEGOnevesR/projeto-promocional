# 🚀 Deploy dos Serviços Adicionais (WhatsApp e Gmail)

Este guia explica como fazer deploy dos serviços WhatsApp e Gmail no Render.

## 📋 Pré-requisitos

- ✅ Conta no Render.com
- ✅ Código já no GitHub
- ✅ Serviço principal (banner-generator) já deployado

---

## 📱 PASSO 1: Deploy do Servidor WhatsApp

### 1.1 - Criar novo Web Service no Render

1. Acesse: https://dashboard.render.com
2. Clique em "New +" → "Web Service"
3. Conecte o mesmo repositório: `DIEGOnevesR/projeto-promocional`

### 1.2 - Configurar o Serviço WhatsApp

**Informações Básicas:**
- **Name:** `whatsapp-sender` (ou outro nome)
- **Region:** Mesma região do serviço principal
- **Branch:** `master`

**Configurações:**
- **Runtime:** `Node`
- **Build Command:** `npm install`
- **Start Command:** `node whatsapp-sender.js`
- **Instance Type:** `Free` (ou `Starter`)

**Variáveis de Ambiente:**
- `NODE_ENV` = `production`
- `PORT` = `3001` (opcional, Render define automaticamente)

### 1.3 - Criar o Serviço

1. Clique em "Create Web Service"
2. Aguarde o deploy (5-10 minutos)
3. Anote a URL gerada (ex: `https://whatsapp-sender-xxxx.onrender.com`)

---

## 📧 PASSO 2: Deploy do Monitor Gmail

### 2.1 - Criar novo Web Service no Render

1. No dashboard do Render, clique em "New +" → "Web Service"
2. Conecte o mesmo repositório: `DIEGOnevesR/projeto-promocional`

### 2.2 - Configurar o Serviço Gmail

**Informações Básicas:**
- **Name:** `gmail-monitor` (ou outro nome)
- **Region:** Mesma região do serviço principal
- **Branch:** `master`

**Configurações:**
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python gmail-monitor-api.py`
- **Instance Type:** `Free` (ou `Starter`)

**Variáveis de Ambiente:**
- `FLASK_ENV` = `production`
- `FLASK_DEBUG` = `False`
- `WHATSAPP_API_URL` = URL do serviço WhatsApp (ex: `https://whatsapp-sender-xxxx.onrender.com`)

### 2.3 - Criar o Serviço

1. Clique em "Create Web Service"
2. Aguarde o deploy (5-10 minutos)
3. Anote a URL gerada (ex: `https://gmail-monitor-xxxx.onrender.com`)

---

## 🔗 PASSO 3: Configurar URLs no Frontend

Depois que ambos os serviços estiverem deployados, atualize o `template_editor.html`:

1. Abra o arquivo `template_editor.html`
2. No `<head>`, adicione/atualize as meta tags:

```html
<meta name="backend-url" content="https://projeto-promocional.onrender.com">
<meta name="whatsapp-url" content="https://whatsapp-sender-xxxx.onrender.com">
<meta name="gmail-url" content="https://gmail-monitor-xxxx.onrender.com">
```

3. Faça commit e push:
```bash
git add template_editor.html
git commit -m "Configurar URLs dos serviços WhatsApp e Gmail"
git push
```

---

## ⚠️ IMPORTANTE: Limitações do Plano Gratuito

### WhatsApp:
- **QR Code:** Precisa escanear o QR Code para autenticar
- **Sessão:** Pode expirar se o serviço entrar em sleep
- **Solução:** Use plano pago ou mantenha serviço sempre ativo

### Gmail:
- **Credenciais:** Precisa configurar credenciais do Gmail
- **Token:** Precisa fazer autenticação OAuth inicial
- **Solução:** Configure as credenciais via variáveis de ambiente

---

## 🔐 Configuração de Credenciais

### Gmail - Variáveis de Ambiente:

No painel do Render, adicione no serviço Gmail:

```
GMAIL_CLIENT_ID=seu_client_id
GMAIL_CLIENT_SECRET=seu_client_secret
GMAIL_REFRESH_TOKEN=seu_refresh_token
```

**Como obter:**
1. Acesse: https://console.cloud.google.com
2. Crie um projeto
3. Ative Gmail API
4. Crie credenciais OAuth 2.0
5. Configure redirect URI
6. Obtenha tokens

---

## ✅ Verificar se Funcionou

### WhatsApp:
```
https://whatsapp-sender-xxxx.onrender.com/health
```

### Gmail:
```
https://gmail-monitor-xxxx.onrender.com/health
```

Ambos devem retornar status OK.

---

## 🎉 Pronto!

Agora todos os serviços estão no ar:
- ✅ Gerador de Banners: `https://projeto-promocional.onrender.com`
- ✅ WhatsApp: `https://whatsapp-sender-xxxx.onrender.com`
- ✅ Gmail Monitor: `https://gmail-monitor-xxxx.onrender.com`

---

**Dúvidas?** Consulte os logs no Render para diagnosticar problemas.






