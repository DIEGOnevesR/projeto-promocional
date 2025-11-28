# 🚀 Deploy Rápido - Passo a Passo

## Opção 1: Render.com (Mais Fácil - Gratuito)

### Passo 1: Preparar o Código
```bash
# Certifique-se de que todos os arquivos estão commitados
git add .
git commit -m "Preparar para deploy"
```

### Passo 2: Criar Conta no Render
1. Acesse https://render.com
2. Faça login com GitHub/GitLab
3. Clique em "New +" → "Web Service"

### Passo 3: Conectar Repositório
1. Conecte seu repositório Git
2. Render detectará automaticamente que é Python

### Passo 4: Configurar Deploy
- **Name:** `banner-generator` (ou o nome que preferir)
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn server:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 300`
- **Instance Type:** `Free` (ou `Starter` para mais recursos)

### Passo 5: Variáveis de Ambiente
No painel do Render, vá em "Environment" e adicione:
```
FLASK_ENV=production
FLASK_DEBUG=False
```

### Passo 6: Deploy
- Render fará deploy automático
- Aguarde 5-10 minutos
- Anote a URL gerada (ex: `https://banner-generator.onrender.com`)

### Passo 7: Configurar Frontend
1. Abra `template_editor.html`
2. Adicione no `<head>` (antes de `</head>`):
```html
<meta name="backend-url" content="https://seu-app.onrender.com">
```

3. Publique o HTML:
   - **Netlify:** Arraste a pasta ou conecte Git
   - **Vercel:** Importe projeto
   - **GitHub Pages:** Ative no Settings → Pages

## Opção 2: Railway.app

### Passo 1: Criar Conta
1. Acesse https://railway.app
2. Faça login com GitHub

### Passo 2: Novo Projeto
1. Clique em "New Project"
2. Selecione "Deploy from GitHub repo"
3. Escolha seu repositório

### Passo 3: Configurar
- Railway detecta automaticamente Python
- Configure variáveis de ambiente:
  ```
  FLASK_ENV=production
  FLASK_DEBUG=False
  ```

### Passo 4: Deploy
- Railway faz deploy automático
- Anote a URL gerada

## ⚙️ Configuração do Frontend

### Opção A: Meta Tags no HTML
Adicione no `<head>` do `template_editor.html`:

```html
<!-- URLs dos serviços (ajuste conforme necessário) -->
<meta name="backend-url" content="https://seu-backend.onrender.com">
<meta name="whatsapp-url" content="https://seu-whatsapp.onrender.com">
<meta name="gmail-url" content="https://seu-gmail.onrender.com">
```

### Opção B: Detecção Automática
O código já detecta automaticamente:
- Se estiver em `localhost` → usa `localhost:5000`
- Se estiver em produção → usa a mesma origem da página

## ✅ Verificar se Funcionou

1. **Teste o Backend:**
   ```
   https://seu-app.onrender.com/health
   ```
   Deve retornar: `{"status": "ok", "message": "Servidor funcionando"}`

2. **Teste o Status:**
   ```
   https://seu-app.onrender.com/status
   ```

3. **Abra o template_editor.html:**
   - Se estiver em Netlify/Vercel, abra a URL
   - Se estiver local, abra o arquivo e ele detectará o backend automaticamente

## 🐛 Problemas Comuns

### Erro: "Module not found"
- Verifique se `requirements.txt` está completo
- Execute `pip install -r requirements.txt` localmente para testar

### Timeout
- Processamento de imagens pode demorar
- Considere aumentar timeout no `Procfile`
- Ou use plano pago para mais recursos

### App entra em sleep (Render Free)
- Render coloca apps gratuitos em sleep após 15min de inatividade
- Primeira requisição após sleep pode demorar ~30s
- Solução: Use plano pago ou configure "Always On"

### Imagens não carregam
- Verifique caminhos relativos
- Certifique-se que pastas estão incluídas no deploy
- Use armazenamento em nuvem (S3, Cloudinary) para produção

## 📝 Checklist Final

- [ ] Código commitado no Git
- [ ] Conta criada na plataforma (Render/Railway)
- [ ] Repositório conectado
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy realizado com sucesso
- [ ] URL do backend anotada
- [ ] Frontend configurado com URL do backend
- [ ] Testes realizados

## 🎉 Pronto!

Seu projeto está no ar! Compartilhe a URL com quem precisar usar.

---

**Dúvidas?** Consulte `README_DEPLOY.md` para mais detalhes.

