# 📧 Como Configurar Gmail no Render

Este guia explica como configurar as credenciais do Gmail para funcionar no Render.

## 🔐 Opção 1: Usar Variáveis de Ambiente (Recomendado)

### Passo 1: Obter Credenciais do Google Cloud Console

1. Acesse: https://console.cloud.google.com
2. Crie um projeto (ou selecione um existente)
3. Ative a **Gmail API**:
   - Vá em "APIs & Services" → "Library"
   - Procure por "Gmail API"
   - Clique em "Enable"

4. Crie credenciais OAuth 2.0:
   - Vá em "APIs & Services" → "Credentials"
   - Clique em "Create Credentials" → "OAuth client ID"
   - Tipo: "Desktop app" ou "Web application"
   - Dê um nome (ex: "Gmail Monitor")
   - Clique em "Create"
   - **Anote o Client ID e Client Secret**

5. Configure Redirect URIs:
   - No OAuth client criado, adicione:
     - `http://localhost` (para desenvolvimento)
     - `https://gmail-monitor-pfts.onrender.com` (sua URL do Render)

### Passo 2: Obter Refresh Token (Primeira Vez)

**IMPORTANTE:** Você precisa fazer isso **uma vez** no seu computador local:

1. No seu computador, crie um arquivo `credentials.json` com:
```json
{
  "installed": {
    "client_id": "SEU_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "seu-projeto-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "SEU_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

2. Execute localmente:
```bash
python -c "from gmail_service import GmailService; s = GmailService(); s.authenticate()"
```

3. Isso abrirá o navegador para autorizar
4. Depois da autorização, um arquivo `token.json` será criado
5. Abra o `token.json` e copie o valor de `"refresh_token"`

### Passo 3: Configurar no Render

No painel do Render, no serviço **gmail-monitor**, adicione estas variáveis de ambiente:

1. **GMAIL_CLIENT_ID** = `seu-client-id.apps.googleusercontent.com`
2. **GMAIL_CLIENT_SECRET** = `seu-client-secret`
3. **GMAIL_REFRESH_TOKEN** = `refresh-token-copiado-do-token.json`
4. **GMAIL_PROJECT_ID** = `seu-projeto-id` (opcional)
5. **WHATSAPP_API_URL** = `https://whatsapp-sender-weq8.onrender.com`

### Passo 4: Testar

Depois de configurar, o serviço criará automaticamente o `credentials.json` a partir das variáveis de ambiente e usará o refresh token para autenticar.

---

## 🔐 Opção 2: Fazer Upload do credentials.json

Se preferir, você pode fazer upload do arquivo `credentials.json`:

1. No Render, vá no serviço **gmail-monitor**
2. Vá em "Settings" → "Build & Deploy"
3. Use "Build Command" para copiar o arquivo (não recomendado)
4. Ou use variáveis de ambiente (Opção 1 - mais seguro)

---

## ⚠️ Importante

- **Nunca commite** `credentials.json` ou `token.json` no Git
- Use sempre variáveis de ambiente em produção
- O refresh token não expira (a menos que você revogue)
- Mantenha as credenciais seguras

---

## 🐛 Troubleshooting

### Erro: "credentials.json não encontrado"
- Verifique se as variáveis de ambiente estão configuradas
- Verifique se os nomes estão corretos (GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET)

### Erro: "Invalid refresh token"
- Gere um novo refresh token seguindo o Passo 2
- Certifique-se de que o Client ID e Secret estão corretos

### Erro: "Access denied"
- Verifique se a Gmail API está habilitada no Google Cloud Console
- Verifique se os redirect URIs estão configurados corretamente

---

**Dúvidas?** Consulte os logs no Render para mais detalhes.






